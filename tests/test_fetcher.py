from pathlib import Path
import json

def test_save_data_creates_files(tmp_path):
    from core.fetcher import WeiboHotSearchFetcher

    f = WeiboHotSearchFetcher()
    data = {
        "2025-12-24": {
            "date": "2025-12-24",
            "items": [
                {"rank": 1, "keyword": "A", "history": {"max_hotness": 100}},
                {"rank": 2, "keyword": "B", "history": {"max_hotness": 50}}
            ]
        }
    }

    out = tmp_path / 'raw.json'
    ok = f.save_data(data, filename=str(out), with_history=True)
    assert ok
    assert out.exists()

    # Test simplified version when with_history=False
    out2 = tmp_path / 'raw2.json'
    ok2 = f.save_data(data, filename=str(out2), with_history=False)
    assert ok2
    simplified = out2.with_name(out2.stem + '_simplified.json')
    assert simplified.exists()
    with open(simplified, 'r', encoding='utf-8') as g:
        s = json.load(g)
    assert '2025-12-24' in s
    assert isinstance(s['2025-12-24'], list)
    assert s['2025-12-24'][0]['title'] == 'A'
