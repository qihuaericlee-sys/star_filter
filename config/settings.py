import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 项目根目录
# TODO: 修改此路径以适应你的项目结构
BASE_DIR = Path(__file__).resolve().parent.parent

#爬取数据的密钥
SECRET_KEY = os.getenv("SECRET_KEY", "")

# API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# 分类器配置
CLASSIFIER_SYSTEM_PROMPT = """你是一个严格的分类器。判断给定标题是否包含明星（人名/艺名）信息。只回答大写的 YES 或 NO，不要添加额外说明。"""

# 处理配置
DEFAULT_DELAY = 0.5  # API请求之间的默认延迟（秒）

# 文件路径配置
DEFAULT_INPUT_FILE = "trends_export.json"
DEFAULT_OUTPUT_FILE = "trends_export_filtered.json"

# 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = BASE_DIR / "logs" / "star_filter.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 创建必要的目录
for dir_path in [BASE_DIR / "logs", BASE_DIR / "data"]:
    dir_path.mkdir(exist_ok=True)