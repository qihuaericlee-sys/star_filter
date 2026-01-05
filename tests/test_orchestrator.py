import json
from pathlib import Path


def test_fetch_and_process_monkeypatch(monkeypatch, tmp_path):
    # 准备假数据和假 fetcher
    fake_data = {
        "2025-12-24": {
            "date": "2025-12-24",
            "items": [{"keyword": "A"}, {"keyword": "B"}],
        }
    }

    class DummyFetcher:
        def fetch_date_range(self, start, end, max_workers, with_history):
            assert start == '2025-12-24'
            assert end == '2025-12-24'
            return fake_data

        def save_data(self, data, filename, with_history=False):
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
            return True

    monkeypatch.setattr('core.orchestrator.WeiboHotSearchFetcher', lambda *a, **k: DummyFetcher())

    # 模拟 DeepSeek client / TitleClassifier
    class DummyClassifier:
        def classify_title(self, title):
            if 'A' in title:
                return True, 'YES'
            return False, 'NO'

    monkeypatch.setattr('core.orchestrator.DeepSeekClient', lambda *a, **k: None)
    monkeypatch.setattr('core.orchestrator.TitleClassifier', lambda *a, **k: DummyClassifier())

    raw_path = tmp_path / 'raw.json'
    out_path = tmp_path / 'out.json'

    from core.orchestrator import fetch_and_process
    res = fetch_and_process('2025-12-24', '2025-12-24', raw_path, out_path, with_history=True, workers=1)

    assert res['total'] == 2
    assert res['kept'] == 1
    assert out_path.exists()

    with open(out_path, 'r', encoding='utf-8') as f:
        out = json.load(f)

    assert '2025-12-24' in out
    assert len(out['2025-12-24']['items']) == 1
