"""
抓取微博热搜并使用 DeepSeek 完成筛选的整合脚本
用法示例:
  python scripts/fetch_and_filter.py --start 2025-12-20 --end 2025-12-24 --output data/filtered.json --raw data/raw.json --with-history
"""
import argparse
import sys
from pathlib import Path
# 确保项目根目录可导入
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
from datetime import datetime
from utils import setup_logger
from core import DeepSeekClient, TitleClassifier, DataProcessor, WeiboHotSearchFetcher
# Orchestrator import
from core.orchestrator import fetch_and_process

"""解析命令行参数"""
def parse_args():
    p = argparse.ArgumentParser(description="抓取微博热搜并调用 DeepSeek 进行筛选")
    p.add_argument("--start", required=True, help="开始日期 YYYY-MM-DD")
    p.add_argument("--end", required=True, help="结束日期 YYYY-MM-DD")
    p.add_argument("--raw", default="data/weibo_raw.json", help="抓取并保存的原始文件路径")
    p.add_argument("--output", default="data/weibo_filtered.json", help="过滤后输出文件路径")
    p.add_argument("--with-history", action="store_true", help="抓取关键词历史（较慢）")
    p.add_argument("--workers", type=int, default=10, help="并发线程数（含历史时建议小些）")
    p.add_argument("--model", type=str, default=None, help="DeepSeek 模型名称（可选）")
    p.add_argument("--enhanced", action="store_true", help="启用增强模式（关联明星推断）")
    return p.parse_args()


"""验证日期格式是否正确"""
def validate_date(s: str) -> bool:
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return True
    except Exception:
        return False


def main():
    logger = setup_logger("fetch_and_filter")
    args = parse_args()

    # 校验日期
    if not validate_date(args.start) or not validate_date(args.end):
        logger.error("开始/结束日期格式必须为 YYYY-MM-DD")
        raise SystemExit(1)
    start_date = args.start
    end_date = args.end

    # 创建抓取器
    fetcher = WeiboHotSearchFetcher()

    # 使用 orchestrator 完成抓取并处理（抓取 -> 保存原始 -> DeepSeek 处理 -> 保存输出）
    try:
        result = fetch_and_process(
            start_date=start_date,
            end_date=end_date,
            raw_path=args.raw,
            output_path=args.output,
            with_history=args.with_history,
            workers=args.workers,
            model=args.model,
            enhanced=args.enhanced,
            delay=None,
        )
        logger.info(f"处理完成: {result}")
    except Exception as e:
        logger.exception(f"处理过程中发生错误: {e}")
        raise SystemExit(1)


if __name__ == '__main__':
    main()
