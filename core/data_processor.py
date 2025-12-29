import json
import logging
from typing import Any, Dict, List, Tuple, Optional
from pathlib import Path


logger = logging.getLogger(__name__)


class DataProcessor:
    """数据处理类，负责JSON文件的读取、处理和保存"""
    
    @staticmethod
    def extract_title_from_item(item: Dict[str, Any]) -> Optional[str]:
        """
        从数据项中提取标题
        
        Args:
            item: 数据项字典
            
        Returns:
            Optional[str]: 提取到的标题，如果未找到则返回None
        """
        if not isinstance(item, dict):
            return None
        
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
        
        Args:
            file_path: JSON文件路径
            
        Returns:
            Tuple[Optional[List], Optional[str], Dict]: 
                (记录列表, 容器键名, 原始数据)
                
        Raises:
            ValueError: 文件结构不支持
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"无法解析JSON文件 {file_path}: {e}")
            raise
        
        # 假设顶层是列表
        if isinstance(data, list):
            return data, None, data
        
        # 如果是字典，尝试找到包含列表的键
        elif isinstance(data, dict):
            # 尝试常见的键名
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
        
        else:
            raise ValueError("不支持的JSON顶层结构")
    
    def process_file(
        self,
        input_path: Path,
        classifier,
        delay: float = 0.5
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
        
        # 处理每个记录
        for idx, item in enumerate(records, 1):
            title = self.extract_title_from_item(item)
            if not title:
                logger.warning(f"记录 {idx} 未找到标题字段，跳过")
                continue
            
            is_celeb, resp = classifier.classify_title(title)
            if is_celeb:
                filtered.append(item)
            
            logger.info(f"[{idx}/{total}] {'KEEP' if is_celeb else 'DROP'} - {title[:100]}")
            
            # 添加延迟
            if idx < total and delay > 0:
                import time
                time.sleep(delay)
        
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
        
        Args:
            filtered_records: 过滤后的记录列表
            original_data: 原始数据
            container_key: 容器键名（如果是嵌套结构）
            output_path: 输出文件路径
        """
        # 构建输出数据结构
        if container_key:
            out_data = dict(original_data)
            out_data[container_key] = filtered_records
        else:
            out_data = filtered_records
        
        # 保存文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(out_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"已保存过滤后的数据到: {output_path}")