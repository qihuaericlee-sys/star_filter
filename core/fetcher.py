import base64
import json
import hashlib
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad, pad
from tqdm import tqdm

from config.settings import SECRET_KEY


class WeiboHotSearchFetcher:
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or SECRET_KEY or "tSdGtmwh49BcR1irt18mxG41dGsBuGKS"
        sha1_hash = hashlib.sha1(self.secret_key.encode('utf-8')).hexdigest()
        key_hex = sha1_hash[:32]
        try:
            self.aes_key = bytes.fromhex(key_hex)
        except Exception:
            self.aes_key = b"\x00" * 16
        self.lock = Lock()

    def create_session(self):
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'DNT': '1',
            'Origin': 'https://www.weibotop.cn',
            'Referer': 'https://www.weibotop.cn/',
        })
        return session

    def decrypt_data(self, encrypted_data: str) -> Optional[Any]:
        try:
            encrypted_bytes = base64.b64decode(encrypted_data)
            cipher = AES.new(self.aes_key, AES.MODE_ECB)
            decrypted = cipher.decrypt(encrypted_bytes)
            decrypted = unpad(decrypted, AES.block_size)
            result = decrypted.decode('utf-8')
            return json.loads(result)
        except Exception:
            return None

    def encrypt(self, plaintext: Optional[str]) -> Optional[str]:
        if plaintext is None:
            return None
        cipher = AES.new(self.aes_key, AES.MODE_ECB)
        padded_data = pad(plaintext.encode('utf-8'), AES.block_size)
        encrypted = cipher.encrypt(padded_data)
        return base64.b64encode(encrypted).decode('utf-8')

    def get_timeid_for_date(self, session: requests.Session, date_str: str) -> Tuple[Optional[str], Optional[str]]:
        try:
            timestamp = f"{date_str} 00:00:00"
            encrypted_timestamp = self.encrypt(timestamp)

            response = session.get(
                "https://api.weibotop.cn/getclosesttime",
                params={"timestamp": encrypted_timestamp},
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                return data[0], data[1]
            else:
                return None, None
        except Exception:
            return None, None

    def fetch_keyword_history(self, session: requests.Session, keyword: str, date_str: str) -> Optional[Dict[str, Any]]:
        try:
            encrypted_keyword = self.encrypt(keyword)

            response = session.get(
                "https://api.weibotop.cn/getrankhistory",
                params={"name": encrypted_keyword},
                timeout=10
            )

            if response.status_code != 200:
                return None

            if "Invalid" in response.text or "Code:DCE" in response.text:
                return None

            history_data = self.decrypt_data(response.text)
            if not history_data or not isinstance(history_data, list) or len(history_data) != 3:
                return None

            timestamps, ranks, hotness = history_data
            daily_history = []
            for i, ts in enumerate(timestamps):
                if ts.startswith(date_str):
                    daily_history.append({
                        "time": ts,
                        "rank": int(ranks[i]),
                        "hotness": int(hotness[i])
                    })

            if not daily_history:
                return None

            return {
                "total_points": len(daily_history),
                "min_rank": min(d["rank"] for d in daily_history),
                "max_rank": max(d["rank"] for d in daily_history),
                "min_hotness": min(d["hotness"] for d in daily_history),
                "max_hotness": max(d["hotness"] for d in daily_history),
                "first_time": daily_history[0]["time"],
                "last_time": daily_history[-1]["time"],
                "details": daily_history
            }
        except Exception:
            return None

    def fetch_data_for_date(self, date_str: str, with_history: bool = False, max_retries: int = 3) -> Tuple[Optional[Any], str]:
        for retry in range(max_retries):
            session = self.create_session()
            try:
                timeid, actual_time = self.get_timeid_for_date(session, date_str)
                if timeid is None:
                    if retry < max_retries - 1:
                        time.sleep(1)
                        continue
                    return None, "无法获取timeid"

                encrypted_timeid = self.encrypt(str(timeid))
                if not encrypted_timeid:
                    if retry < max_retries - 1:
                        time.sleep(1)
                        continue
                    return None, "加密失败"

                timeid_param = quote(encrypted_timeid)
                url = f"https://api.weibotop.cn/currentitems?timeid={timeid_param}"
                response = session.get(url, timeout=15)
                response.raise_for_status()

                if "Invalid" in response.text:
                    if retry < max_retries - 1:
                        time.sleep(1)
                        continue
                    return None, f"API返回错误"

                data = self.decrypt_data(response.text)
                if not data:
                    if retry < max_retries - 1:
                        time.sleep(1)
                        continue
                    return None, "解密失败"

                if not isinstance(data, list):
                    if retry < max_retries - 1:
                        time.sleep(1)
                        continue
                    return None, "数据格式错误"

                if with_history:
                    enriched_data = []
                    for rank, item in enumerate(tqdm(data, desc=f"{date_str} 关键词", leave=False), 1):
                        keyword = item[0] if isinstance(item, list) else item
                        history = self.fetch_keyword_history(session, keyword, date_str)
                        enriched_item = {
                            "rank": rank,
                            "keyword": keyword,
                            "raw_data": item,
                            "history": history
                        }
                        enriched_data.append(enriched_item)
                        time.sleep(0.1)

                    result = {
                        "date": date_str,
                        "timeid": timeid,
                        "actual_time": actual_time,
                        "total_items": len(enriched_data),
                        "items": enriched_data
                    }
                    return result, f"成功 ({len(data)} 条，含历史数据)"
                else:
                    return data, f"成功 ({len(data)} 条)"
            except Exception as e:
                if retry < max_retries - 1:
                    time.sleep(1)
                    continue
                return None, str(e)
            finally:
                session.close()
        return None, "重试失败"

    def fetch_date_range(self, start_date: str, end_date: str, max_workers: int = 10, with_history: bool = False) -> Dict[str, Any]:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        date_list = []
        current = start
        while current <= end:
            date_list.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)

        all_data = {}
        success_count = 0
        fail_count = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_date = {
                executor.submit(self.fetch_data_for_date, date, with_history): date
                for date in date_list
            }

            for future in as_completed(future_to_date):
                date = future_to_date[future]
                try:
                    data, status = future.result()
                    with self.lock:
                        if data:
                            all_data[date] = data
                            success_count += 1
                        else:
                            fail_count += 1
                except Exception:
                    with self.lock:
                        fail_count += 1

        return all_data

    def save_data(self, data: Dict[str, Any], filename: str = "weibo_hotsearch.json", with_history: bool = False) -> bool:
        """保存抓取的数据为 JSON 文件并可选生成简化版。

        Args:
            data: 按日期字典的数据
            filename: 输出完整数据文件路径
            with_history: 是否为带历史的输出（如果 False，将生成简化版文件）

        Returns:
            bool: 是否保存成功
        """
        try:
            from pathlib import Path
            from utils.file_utils import save_json_safely

            out_path = Path(filename)
            # 保存完整数据
            saved = save_json_safely(data, out_path)
            if not saved:
                return False

            if not with_history:
                simplified = {}
                for date, day in data.items():
                    if isinstance(day, dict) and 'items' in day and isinstance(day['items'], list):
                        simplified[date] = [
                            {
                                'rank': it.get('rank', i + 1),
                                'title': it.get('keyword', it.get('word', it.get('title', ''))),
                                'hot_value': (it.get('history', {}).get('max_hotness') if isinstance(it, dict) else 0) or it.get('num', 0),
                                'url': it.get('url', '') if isinstance(it, dict) else ''
                            }
                            for i, it in enumerate(day['items'])
                        ]
                simplified_path = out_path.with_name(out_path.stem + '_simplified.json')
                save_json_safely(simplified, simplified_path)

            return True
        except Exception:
            return False
