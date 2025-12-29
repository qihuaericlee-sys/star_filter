# 导出核心模块
from .api_client import DeepSeekClient
from .classifier import TitleClassifier
from .data_processor import DataProcessor

__version__ = "1.0.0"
__all__ = ['DeepSeekClient', 'TitleClassifier', 'DataProcessor']