"""Orchestrator: 把抓取、保存原始、调用 DeepSeek 处理并保存结果串成链路"""
from pathlib import Path
from typing import Optional, Dict, Any
from utils import setup_logger
from .fetcher import WeiboHotSearchFetcher
from .api_client import DeepSeekClient
from .classifier import TitleClassifier
from .data_processor import DataProcessor
from config.settings import DEFAULT_DELAY


def fetch_and_process(
    start_date: str,
    end_date: str,
    raw_path: str | Path,
    output_path: str | Path,
    with_history: bool = False,
    workers: int = 10,
    model: Optional[str] = None,
    enhanced: bool = False,
    delay: Optional[float] = None,
    client: Optional[DeepSeekClient] = None,
    logger=None,
) -> Dict[str, Any]:
    logger = logger or setup_logger("orchestrator")
    raw_path = Path(raw_path)
    output_path = Path(output_path)
    delay = DEFAULT_DELAY if delay is None else delay

    logger.info(f"开始抓取: {start_date} -> {end_date} (with_history={with_history})")
    fetcher = WeiboHotSearchFetcher()
    all_data = fetcher.fetch_date_range(start_date, end_date, max_workers=workers, with_history=with_history)

    if not all_data:
        logger.error("未抓取到任何数据")
        raise RuntimeError("empty result from fetcher")

    # 保存原始数据
    saved = fetcher.save_data(all_data, filename=str(raw_path), with_history=with_history)
    if not saved:
        logger.error("保存原始数据失败")
        raise RuntimeError("failed to save raw data")

    logger.info("初始化 DeepSeek 客户端并开始处理")
    client = client or DeepSeekClient()
    classifier = TitleClassifier(client.get_client(), model=model)
    processor = DataProcessor()

    filtered_records, total, kept = processor.process_file(
        input_path=raw_path,
        classifier=classifier,
        delay=delay,
        enhance_model=enhanced,
    )

    records, container_key, original_data = processor.load_json_file(raw_path)
    processor.save_filtered_data(filtered_records, original_data, container_key, output_path)

    logger.info("抓取并处理完成")

    return {
        "total": total,
        "kept": kept,
        "filtered": total - kept if total is not None else None,
        "output_path": str(output_path)
    }
