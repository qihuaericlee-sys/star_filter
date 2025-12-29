#!/usr/bin/env python3
"""
DeepSeek明星趋势过滤器主脚本
"""
import argparse
from pathlib import Path
import sys

# 添加项目根目录到Python路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config.settings import (
    DEFAULT_INPUT_FILE, 
    DEFAULT_OUTPUT_FILE, 
    DEFAULT_DELAY
)
from core import DeepSeekClient, TitleClassifier, DataProcessor, RelatedCelebrityClassifier
from utils import setup_logger


def main():
    """主函数"""
    # 设置日志
    logger = setup_logger("star_filter")
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(
        description="使用 Deepseek 对 trends JSON 的 title 字段进行明星筛选"
    )
    
    parser.add_argument(
        "input", 
        nargs="?", 
        default=DEFAULT_INPUT_FILE,
        help=f"输入 JSON 文件，默认 {DEFAULT_INPUT_FILE}"
    )
    
    parser.add_argument(
        "-o", "--output", 
        default=DEFAULT_OUTPUT_FILE,
        help=f"输出过滤后 JSON 文件，默认 {DEFAULT_OUTPUT_FILE}"
    )
    
    parser.add_argument(
        "--delay", 
        type=float, 
        default=DEFAULT_DELAY,
        help=f"每次请求之间的延迟（秒），默认 {DEFAULT_DELAY}"
    )
    
    parser.add_argument(
        "--model", 
        type=str,
        help=f"使用的DeepSeek模型"
    )
    
    parser.add_argument(
        "--no-delay", 
        action="store_true",
        help="禁用请求延迟（不推荐，可能导致API限制）"
    )

    parser.add_argument(
        "--enhanced",
        action="store_true",  # 启用时设为True
        help="启用增强模式，对非直接明星标题进行关联明星推断"
    )
    
    args = parser.parse_args()
    
    # 处理延迟参数
    delay = 0 if args.no_delay else args.delay
    
    try:
        # 初始化客户端和处理器
        logger.info("初始化DeepSeek客户端...")
        client = DeepSeekClient()
        
        logger.info("初始化分类器...")
        classifier = TitleClassifier(client.get_client(), model=args.model)
        
        processor = DataProcessor()
        
        # 处理文件
        input_path = Path(args.input)
        output_path = Path(args.output)
        
        logger.info(f"开始处理文件: {input_path}")
        
        # 加载数据
        records, container_key, original_data = processor.load_json_file(input_path)
        
        # 处理数据
        filtered_records, total, kept = processor.process_file(
            input_path=Path(args.input),
            classifier=classifier,
            delay=delay,
            enhance_model=args.enhanced
        )
        
        # 保存结果
        processor.save_filtered_data(
            filtered_records, 
            original_data, 
            container_key, 
            output_path
        )
        
        # 输出统计信息
        logger.info("=" * 50)
        logger.info(f"处理完成!")
        logger.info(f"总记录数: {total}")
        logger.info(f"保留记录数: {kept}")
        logger.info(f"过滤记录数: {total - kept}")
        logger.info(f"保留比例: {kept/total*100:.1f}%" if total > 0 else "N/A")
        logger.info(f"输出文件: {output_path}")
        logger.info("=" * 50)
        
    except ValueError as e:
        logger.error(f"参数错误: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        logger.error(f"文件错误: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("用户中断处理")
        sys.exit(0)
    except Exception as e:
        logger.error(f"处理过程中发生错误: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()