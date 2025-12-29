import os
from typing import Optional
from openai import OpenAI
from config.settings import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL


class DeepSeekClient:
    """DeepSeek API客户端封装类"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        初始化DeepSeek客户端
        
        Args:
            api_key: API密钥，如果为None则从环境变量或配置文件读取
            base_url: API基础URL
        """
        self.api_key = api_key or DEEPSEEK_API_KEY
        self.base_url = base_url or DEEPSEEK_BASE_URL
        
        if not self.api_key:
            raise ValueError(
                "DeepSeek API密钥未提供。请设置环境变量DEEPSEEK_API_KEY "
                "或在调用时提供api_key参数"
            )
        
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
    
    def get_client(self) -> OpenAI:
        """获取OpenAI客户端实例"""
        return self.client