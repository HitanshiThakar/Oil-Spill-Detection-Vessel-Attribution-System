"""Tests for dynamic real-data SAR STAC search, acquisition screening, and indexing."""
from __future__ import annotations

import pytest

from app import scenes as scenes_mod
from app.sar import stac as sar_stac


def test_stac_search_queries_planetary_computer():
    """Verify STAC search returns valid Sentinel-1 features from Planetary Computer."""
    # Gulf of Mexico MC20 coordinates
    items = sar_stac.search_sentinel1(lat=28.938, lon=-88.970, t_start="2023-09-01", t_end="2023-10-01", limit=5)
    assert isinstance(items, list)
    assert len(items) > 0
    first = items[0]
    assert first["id"].startswith("S1")
    assert "assets" in first
    assert "vv" in first["assets"]


def test_stac_search_endpoint_via_fastapi_testclient():
    """Verify POST /api/scenes/search endpoint."""
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        res = client.post("/api/scenes/search", json={
            "lat": 28.938,
            "lon": -88.970,
            "t_start": "2023-09-01",
            "t_end": "2023-10-01",
        })
        assert res.status_code == 200
        doc = res.json()
        assert doc["count"] > 0
        assert len(doc["items"]) > 0
        assert doc["items"][0]["has_vv"] is True


def test_auto_disk_scanner_discovers_unindexed_geotiffs():
    """Verify scan_disk picks up raw GeoTIFFs placed in data/sar."""
    import shutil
    from pathlib import Path

    target_dir = Path(scenes_mod.config.SAR_DIR)
    src = target_dir / "gom_mc20_chronic_slick.tif"
    if src.exists():
        dst = target_dir / "custom_disc_temp.tif"
        shutil.copy(src, dst)
        try:
            found = scenes_mod.scan_disk()
            assert any(s.id == "custom_disc_temp" for s in found), f"found: {[s.id for s in found]}"
        finally:
            dst.unlink(missing_ok=True)







