"""Real-time Sentinel-1 STAC API search, screening, and windowed COG acquisition.

Queries Microsoft Planetary Computer STAC (sentinel-1-rtc), screens candidate
acquisitions for dark-slick contrast, streams windowed COGs on-the-fly, and
dynamically indexes new scenes without relying on hardcoded presets.
"""
from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .. import config, scenes as scenes_mod

STAC_SEARCH = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
SAS_TOKEN_URL = "https://planetarycomputer.microsoft.com/api/sas/v1/token/%s"
COLLECTION = "sentinel-1-rtc"
LICENSE = ("Contains modified Copernicus Sentinel data. Sentinel-1 RTC hosted by "
           "Microsoft Planetary Computer, CC BY 4.0.")


def get_sas_token(collection: str = COLLECTION) -> str:
    """Fetch an anonymous SAS token for Planetary Computer blob access."""
    req = urllib.request.Request(SAS_TOKEN_URL % collection)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))["token"]


def search_sentinel1(
    lat: float,
    lon: float,
    t_start: Optional[str] = None,
    t_end: Optional[str] = None,
    pad_deg: float = 0.15,
    limit: int = 15,
) -> List[Dict[str, Any]]:
    """Query Microsoft Planetary Computer STAC for real Sentinel-1 acquisitions."""
    if not t_end:
        t_end = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if not t_start:
        # Default to 6 months window
        t_start = "2023-01-01"

    bbox = [lon - pad_deg, lat - pad_deg, lon + pad_deg, lat + pad_deg]
    body = {
        "collections": [COLLECTION],
        "bbox": bbox,
        "datetime": "%sT00:00:00Z/%sT23:59:59Z" % (t_start[:10], t_end[:10]),
        "limit": limit,
    }

    req = urllib.request.Request(
        STAC_SEARCH,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "TideTrace/1.5"},
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("features", [])


def cut_windowed_chip(
    item: Dict[str, Any],
    lat: float,
    lon: float,
    size_km: float = 22.0,
    token: Optional[str] = None,
    max_side: int = 2048,
) -> Dict[str, Any]:
    """Windowed stream of VV/VH bands around a lat/lon point into a dB stack."""
    import rasterio
    from rasterio.warp import transform_bounds
    from rasterio.windows import from_bounds

    os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
    os.environ.setdefault("CPL_VSIL_CURL_ALLOWED_EXTENSIONS", ".tif,.tiff")

    if not token:
        token = get_sas_token()

    from ..geo.crs import meters_per_degree

    m_lon, m_lat = meters_per_degree(lat)
    half = size_km * 1000.0 / 2.0
    wgs = (lon - half / m_lon, lat - half / m_lat, lon + half / m_lon, lat + half / m_lat)

    bands: List[np.ndarray] = []
    transform = None
    crs = None

    for pol in ("vv", "vh"):
        asset = item["assets"].get(pol)
        if asset is None:
            continue
        href = "/vsicurl/%s?%s" % (asset["href"], token)
        with rasterio.open(href) as ds:
            bounds = transform_bounds("EPSG:4326", ds.crs, *wgs)
            win = from_bounds(*bounds, transform=ds.transform).round_offsets().round_lengths()
            if win.width < 64 or win.height < 64:
                raise RuntimeError("requested window falls outside this scene")
            out_h = min(int(win.height), max_side)
            out_w = min(int(win.width), max_side)
            arr = ds.read(1, window=win, out_shape=(out_h, out_w), boundless=True, fill_value=float("nan"))
            if transform is None:
                t = ds.window_transform(win)
                sx = float(win.width) / out_w
                sy = float(win.height) / out_h
                transform = (t.a * sx, t.b, t.c, t.d, t.e * sy, t.f)
                crs = ds.crs.to_string()
        arr = np.asarray(arr, dtype=np.float32)
        arr[arr <= 0] = np.nan
        arr[arr < 1e-6] = np.nan
        bands.append(10.0 * np.log10(arr))

    if not bands:
        raise RuntimeError("STAC item has no VV or VH polarization asset")
    if len(bands) == 1:
        bands.append(bands[0].copy())

    stack = np.stack(bands, axis=0).astype(np.float32)
    coverage = float(np.isfinite(stack).mean())
    return {
        "array": stack,
        "transform": transform,
        "crs": crs,
        "coverage": coverage,
        "t_sat": item["properties"]["datetime"],
        "item_id": item["id"],
        "shape": list(stack.shape),
    }


def score_slick_contrast(chip: Dict[str, Any]) -> Dict[str, Any]:
    """Screen an acquisition for ocean backscatter contrast and dark slick blobs."""
    from ..geo import geometry
    from ..ml import fallback

    vv = chip["array"][0]
    out = fallback.detect(vv, min_pixels=48)
    mask = out["mask"]
    dark_px = int((mask > 0).sum())
    oil_px = int((mask == 2).sum())

    finite = vv[np.isfinite(vv)]
    if finite.size == 0:
        return {"score": -1.0, "oil_px": 0, "dark_px": 0, "contrast_db": 0.0}
    sea = float(np.median(finite))
    p1 = float(np.percentile(finite, 1.0))
    contrast = sea - p1

    _labels, n = geometry.label_components(mask == 2)
    largest = 0
    if n:
        largest = int(max((int((_labels == k).sum()) for k in range(1, n + 1)), default=0))

    score = largest / 1000.0 + oil_px / 20000.0 + max(0.0, contrast - 2.0)
    return {
        "score": float(score),
        "oil_px": oil_px,
        "dark_px": dark_px,
        "largest_blob_px": largest,
        "sea_db": round(sea, 2),
        "contrast_db": round(contrast, 2),
    }


def fetch_stac_scene(
    lat: float,
    lon: float,
    scene_id: Optional[str] = None,
    title: Optional[str] = None,
    t_start: Optional[str] = None,
    t_end: Optional[str] = None,
    size_km: float = 22.0,
    auto_screen: bool = True,
    max_candidates: int = 6,
) -> scenes_mod.Scene:
    """Dynamically query STAC, download windowed COG, and auto-index the scene."""
    from ..geo import raster as raster_mod

    items = search_sentinel1(lat, lon, t_start=t_start, t_end=t_end, limit=max(10, max_candidates))
    if not items:
        raise RuntimeError("No Sentinel-1 acquisitions found for lat=%.4f lon=%.4f" % (lat, lon))

    token = get_sas_token()
    selected_item = items[0]

    if auto_screen and len(items) > 1:
        scored = []
        for item in items[:max_candidates]:
            try:
                small = cut_windowed_chip(item, lat, lon, size_km, token, max_side=640)
                if small["coverage"] >= 0.70:
                    sc = score_slick_contrast(small)
                    scored.append((sc["score"], item))
            except Exception:
                continue
        if scored:
            scored.sort(key=lambda x: -x[0])
            selected_item = scored[0][1]

    chip = cut_windowed_chip(selected_item, lat, lon, size_km, token)
    scene_id = scene_id or "stac_s1_%s" % datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    title = title or "Sentinel-1 STAC Granule (%s)" % selected_item["id"][:28]

    out_path = Path(config.SAR_DIR) / ("%s.tif" % scene_id)
    raster_mod.write_geotiff(out_path, chip["array"], chip["transform"], chip["crs"])

    scene = scenes_mod.describe_geotiff(
        out_path,
        scene_id=scene_id,
        title=title,
        t_sat=chip["t_sat"],
        source="Sentinel-1 RTC via Microsoft Planetary Computer STAC (%s)" % chip["item_id"],
        license_=LICENSE,
        notes="Dynamically fetched real Sentinel-1 imagery",
    )
    scenes_mod.upsert([scene])
    return scene
