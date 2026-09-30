import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "research/article5/refresh_ct_s1_statcast.py"
SPEC = importlib.util.spec_from_file_location("article5_ct_s1_refresh", MODULE_PATH)
refresh = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = refresh
SPEC.loader.exec_module(refresh)


def test_refresh_is_limited_to_frozen_final_day():
    url = refresh.final_day_url()
    assert "game_date_gt=2026-09-27" in url
    assert "game_date_lt=2026-09-27" in url
    assert "hfGT=R%7C" in url
