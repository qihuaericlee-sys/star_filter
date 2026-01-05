"""兼容层：请从 `core.fetcher` 导入 `WeiboHotSearchFetcher`。

原始脚本已搬入 `core/fetcher.py`，直接使用该实现可以避免同步问题。
"""
from core.fetcher import WeiboHotSearchFetcher
from datetime import datetime

# 保持向后兼容：当被直接运行时，可像原来一样通过 core.fetcher 使用
if __name__ == '__main__':
    print("请改为使用：from core.fetcher import WeiboHotSearchFetcher")
    print("或者使用脚本：python scripts/fetch_and_filter.py --start YYYY-MM-DD --end YYYY-MM-DD")
    fetcher = WeiboHotSearchFetcher()
    # 简单演示：抓取最近一天（仅示例）
    today = datetime.now().strftime("%Y-%m-%d")
    data = fetcher.fetch_date_range(today, today, with_history=False)
    fetcher.save_data(data, filename=f"weibo_hotsearch_{today}.json", with_history=False)
