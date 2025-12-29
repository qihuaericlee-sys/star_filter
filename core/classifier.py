import logging
from typing import Tuple
from openai import OpenAI
from config.settings import DEEPSEEK_MODEL, CLASSIFIER_SYSTEM_PROMPT


logger = logging.getLogger(__name__)


class TitleClassifier:
    """标题分类器，用于判断标题是否包含明星信息"""
    
    def __init__(self, client: OpenAI, model: str = None):
        """
        初始化分类器
        
        Args:
            client: OpenAI客户端实例
            model: 使用的模型名称
        """
        self.client = client
        self.model = model or DEEPSEEK_MODEL
    
    def classify_title(self, title: str) -> Tuple[bool, str]:
        """
        判断标题是否包含明星信息
        
        Args:
            title: 要判断的标题
            
        Returns:
            Tuple[bool, str]: (是否包含明星, 原始响应)
        """
        messages = [
            {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
            {"role": "user", "content": title},
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model, 
                messages=messages, 
                stream=False
            )
            text = response.choices[0].message.content.strip().upper()
            
            # 解析响应
            if text.startswith("YES"):
                return True, text
            if text.startswith("NO"):
                return False, text
            
            # 回退处理
            return ("YES" in text), text
            
        except Exception as e:
            error_msg = f"API调用失败: {e}"
            logger.error(error_msg)
            return False, f"ERROR: {e}"
    
    def batch_classify(self, titles: list, delay: float = 0.5) -> list:
        """
        批量分类多个标题
        
        Args:
            titles: 标题列表
            delay: 每次请求之间的延迟（秒）
            
        Returns:
            list: 分类结果列表，每个元素为(标题, 是否包含明星, 原始响应)
        """
        import time
        results = []
        
        for i, title in enumerate(titles, 1):
            logger.info(f"正在处理第 {i}/{len(titles)} 个标题: {title[:50]}...")
            is_celeb, resp = self.classify_title(title)
            results.append((title, is_celeb, resp))
            
            if i < len(titles) and delay > 0:
                time.sleep(delay)
        
        return results