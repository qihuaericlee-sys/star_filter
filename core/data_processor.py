import json
import logging
from typing import Any, Dict, List, Tuple, Optional
from pathlib import Path
from .classifier import TitleClassifier
from .related_classifier import RelatedCelebrityClassifier
from tqdm import tqdm
import time

logger = logging.getLogger(__name__)


class DataProcessor:
    """数据处理类，负责JSON文件的读取、处理和保存"""
    
    @staticmethod
    def extract_title_from_item(item: Dict[str, Any]) -> Optional[str]:
        """
        从数据项中提取标题
        
        优先规则：
        - 如果有 `keyword` 字段，使用它（Weibo fetcher 带历史模式使用此字段）
        - 如果有 `raw_data` 且为列表，则使用第一个元素作为标题
        - 否则按常见字段名查找

        Args:
            item: 数据项字典
            
        Returns:
            Optional[str]: 提取到的标题，如果未找到则返回None
        """
        if not isinstance(item, dict):
            return None

        # 优先 Weibo 格式的字段
        if "keyword" in item and item.get("keyword"):
            return str(item.get("keyword"))

        raw = item.get("raw_data")
        if isinstance(raw, list) and raw:
            # raw_data 的第一个元素通常是关键词文本
            first = raw[0]
            if isinstance(first, str) and first:
                return first

        # 可能的标题字段名
        title_fields = ["title", "Title", "name", "text", "headline", "topic"]

        for key in title_fields:
            if key in item and item[key]:
                return str(item[key])

        return None
    
    @staticmethod
    def load_json_file(file_path: Path) -> Tuple[Optional[List], Optional[str], Dict]:
        """
        加载JSON文件并提取记录列表

        支持格式：
        - 顶层是列表
        - 顶层是字典且包含常见的容器键（如 items）
        - 顶层是按日期索引的字典（例如 {"2025-12-20": {"items": [...]}, ...}），此时会展开为扁平记录列表，并在每条记录中加入 `_source_date` 字段以便回写

        Args:
            file_path: JSON文件路径

        Returns:
            Tuple[Optional[List], Optional[str], Dict]: 
                (记录列表, 容器键名 or 'by_date' 表示按日期展开, 原始数据)

        Raises:
            ValueError: 文件结构不支持
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"无法解析JSON文件 {file_path}: {e}")
            raise

        # 如果顶层是列表，直接返回
        if isinstance(data, list):
            return data, None, data

        # 顶层是字典，可能为按日期索引的结构
        if isinstance(data, dict):
            # 检查是否为日期索引（每个值是 dict 或 list 包含 items）
            # 如果发现 date-like 结构，则展开
            expanded = []
            found_date_structure = False

            for key, value in data.items():
                # 忽略非日期和元数据项（例如：metadata 等）——但我们只要能找到 items/list 就处理
                if isinstance(value, dict) and 'items' in value and isinstance(value['items'], list):
                    for it in value['items']:
                        if isinstance(it, dict):
                            new_item = dict(it)
                        else:
                            new_item = {'raw_data': it}
                        new_item['_source_date'] = key
                        expanded.append(new_item)
                    found_date_structure = True
                elif isinstance(value, list):
                    for it in value:
                        if isinstance(it, dict):
                            new_item = dict(it)
                        else:
                            new_item = {'raw_data': it}
                        new_item['_source_date'] = key
                        expanded.append(new_item)
                    found_date_structure = True

            if found_date_structure:
                return expanded, 'by_date', data

            # 否则按原有逻辑查找常见键名
            container_keys = ["items", "data", "rows", "trends", "results", "records"]
            for key in container_keys:
                if key in data and isinstance(data[key], list):
                    return data[key], key, data

            # 回退：查找第一个列表值
            for key, value in data.items():
                if isinstance(value, list):
                    logger.warning(f"使用非标准键名 '{key}' 作为容器")
                    return value, key, data

            raise ValueError("无法在JSON中找到列表记录结构")

        raise ValueError("不支持的JSON顶层结构")
    
    def process_file(
        self,
        input_path: Path,
        classifier,
        delay: float = 0.5,
        enhance_model = False
    ) -> Tuple[List, int, int]:
        """
        处理文件，过滤包含明星的条目
        
        Args:
            input_path: 输入文件路径
            classifier: 分类器实例
            delay: API请求之间的延迟
            
        Returns:
            Tuple[List, int, int]: (过滤后的记录, 总记录数, 保留记录数)
        """
        # 加载数据
        records, container_key, original_data = self.load_json_file(input_path)
        filtered = []
        total = len(records)

        # 使用传入的分类器作为直接分类器
        direct_classifier = classifier
        related_classifier = None
        if enhance_model:
            # RelatedCelebrityClassifier 需要底层 client（如 OpenAI 客户端），使用 classifier.client
            related_classifier = RelatedCelebrityClassifier(getattr(classifier, 'client', None))
        
        # 创建tqdm进度条迭代器
        progress_bar = tqdm(records, desc="正在过滤", unit="条", ncols=80)

        for item in progress_bar:
            title = self.extract_title_from_item(item)
            if not title:
                progress_bar.set_postfix_str('跳过: 无标题', refresh=False)
                continue

            output_item = None
            current_reason = ""

            # --- 阶段一：直接明星判断 ---
            is_celeb, _ = direct_classifier.classify_title(title)
            if is_celeb:
                output_item = dict(item)  # 创建副本
                output_item["filter_reason"] = "direct_celebrity"
                current_reason = f"直接明星: {title[:15]}..."

            # --- 阶段二：关联明星推断 ---
            elif enhance_model and related_classifier:
                related_result = related_classifier.infer_related_celebrity(title)
                if related_result and related_result.get("name"):
                    # 成功推断出关联明星，创建新条目
                    output_item = dict(item)
                    output_item["original_title"] = title  # 保留原始标题
                    output_item["title"] = related_result["name"]  # 替换为关联明星
                    output_item["filter_reason"] = "inferred_celebrity"
                    output_item["inference_reasoning"] = related_result.get("reasoning", "")
                    current_reason = f"推断为: {related_result['name'][:15]}..."
                else:
                    # 无法推断，丢弃
                    current_reason = "丢弃: 无关联明星"
            else:
                # 非增强模式，且非直接明星 -> 丢弃
                current_reason = "丢弃: 非明星主题"

            # 4. 更新进度条信息并收集结果
            progress_bar.set_postfix_str(current_reason, refresh=False)
            if output_item:
                filtered.append(output_item)
                # 可选：添加微小延迟，使进度条更平滑（对API延迟影响可忽略）
                # time.sleep(delay * 0.05)

        progress_bar.close()

        # 处理每个记录
        # for idx, item in enumerate(records, 1):
        #     title = self.extract_title_from_item(item)
        #     if not title:
        #         logger.warning(f"记录 {idx} 未找到标题字段，跳过")
        #         continue
            
        #     is_celeb, resp = classifier.classify_title(title)
        #     if is_celeb:
        #         filtered.append(item)
            
        #     logger.info(f"[{idx}/{total}] {'KEEP' if is_celeb else 'DROP'} - {title[:100]}")
            
        #     # 添加延迟
        #     if idx < total and delay > 0:
        #         import time
        #         time.sleep(delay)
        
        return filtered, total, len(filtered)
    
    def save_filtered_data(
        self,
        filtered_records: List,
        original_data: Dict,
        container_key: Optional[str],
        output_path: Path
    ):
        """
        保存过滤后的数据

        兼容多种输入结构：
        - 如果是按日期展开（container_key == 'by_date'），则把结果分配回对应日期下的 `items` 或列表中
        - 如果是普通容器键，则直接替换
        - 如果没有容器键（顶层列表），直接保存列表
        """
        # 构建输出数据结构
        if container_key == 'by_date' and isinstance(original_data, dict):
            out_data = dict(original_data)

            # 初始化每个日期的目标容器
            for date_key, value in out_data.items():
                if isinstance(value, dict) and 'items' in value and isinstance(value['items'], list):
                    out_data[date_key]['items'] = []
                elif isinstance(value, list):
                    out_data[date_key] = []
                else:
                    # 保持原样，如果需要可创建 items
                    out_data[date_key] = value

            # 分配每个过滤后的记录
            for item in filtered_records:
                src_date = item.pop('_source_date', None)
                if not src_date:
                    # 如果没有来源日期，追加到顶层（不常见）
                    continue

                if src_date not in out_data:
                    # 新的日期键，创建并放入 items
                    out_data[src_date] = {'items': [item]}
                    continue

                if isinstance(out_data[src_date], dict) and 'items' in out_data[src_date] and isinstance(out_data[src_date]['items'], list):
                    out_data[src_date]['items'].append(item)
                elif isinstance(out_data[src_date], list):
                    out_data[src_date].append(item)
                else:
                    # 回退：将其覆盖为列表
                    out_data[src_date] = [item]

        elif container_key:
            out_data = dict(original_data)
            out_data[container_key] = filtered_records
        else:
            out_data = filtered_records

        # 保存文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(out_data, f, ensure_ascii=False, indent=2)

        logger.info(f"已保存过滤后的数据到: {output_path}")