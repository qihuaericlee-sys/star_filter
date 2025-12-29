import logging
import sys
from pathlib import Path
from config.settings import LOG_LEVEL, LOG_FILE, LOG_FORMAT


def setup_logger(name: str = None, log_to_file: bool = True) -> logging.Logger:
    """
    设置并返回配置好的日志记录器
    
    Args:
        name: 日志记录器名称
        log_to_file: 是否记录到文件
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    logger = logging.getLogger(name or __name__)
    logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # 清除现有的处理器
    logger.handlers.clear()
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, LOG_LEVEL))
    console_formatter = logging.Formatter(LOG_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    if log_to_file:
        # 确保日志目录存在
        LOG_FILE.parent.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setLevel(getattr(logging, LOG_LEVEL))
        file_formatter = logging.Formatter(LOG_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger