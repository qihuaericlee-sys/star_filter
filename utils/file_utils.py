import json
from pathlib import Path
from typing import Any, Dict
import logging


logger = logging.getLogger(__name__)


def validate_file_path(file_path: Path, must_exist: bool = True) -> bool:
    """
    验证文件路径
    
    Args:
        file_path: 文件路径
        must_exist: 文件是否必须存在
        
    Returns:
        bool: 路径是否有效
    """
    if not file_path:
        logger.error("文件路径不能为空")
        return False
    
    if must_exist and not file_path.exists():
        logger.error(f"文件不存在: {file_path}")
        return False
    
    if must_exist and not file_path.is_file():
        logger.error(f"路径不是文件: {file_path}")
        return False
    
    # 检查文件扩展名
    if file_path.suffix.lower() != '.json':
        logger.warning(f"文件扩展名不是.json: {file_path}")
    
    return True


def backup_file(file_path: Path, backup_suffix: str = '.bak') -> Path:
    """
    创建文件备份
    
    Args:
        file_path: 要备份的文件路径
        backup_suffix: 备份文件后缀
        
    Returns:
        Path: 备份文件路径
    """
    backup_path = file_path.with_suffix(file_path.suffix + backup_suffix)
    
    try:
        if file_path.exists():
            import shutil
            shutil.copy2(file_path, backup_path)
            logger.info(f"已创建备份: {backup_path}")
    except Exception as e:
        logger.error(f"创建备份失败: {e}")
    
    return backup_path


def read_json_safely(file_path: Path) -> Any:
    """
    安全读取JSON文件
    
    Args:
        file_path: JSON文件路径
        
    Returns:
        Any: 解析后的JSON数据
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析错误: {e}")
        raise
    except Exception as e:
        logger.error(f"读取文件失败: {e}")
        raise


def save_json_safely(data: Any, file_path: Path, indent: int = 2) -> bool:
    """
    安全保存JSON数据到文件
    
    Args:
        data: 要保存的数据
        file_path: 输出文件路径
        indent: 缩进空格数
        
    Returns:
        bool: 是否保存成功
    """
    try:
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
        
        logger.info(f"数据已保存到: {file_path}")
        return True
    except Exception as e:
        logger.error(f"保存文件失败: {e}")
        return False