"""GET /api/health and GET /api/config."""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter

from .. import config, scenes as scenes_mod
from ..ais import ingest as ais_ingest, score as ais_score
from ..drift import fields as fields_mod
from ..jobs import store as job_store
from ..ml import infer, model as model_mod
from ..schemas import HealthResponse

router = APIRouter()


@router.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Lightweight readiness check for Render and local startup.

    This endpoint must not trigger checkpoint loading or scan the full data
    store. A health check should confirm that the process is alive and the app
    can serve requests, while the heavier model and dataset validation belongs to
    dedicated pipeline calls.
    """
    warnings: List[str] = []

    status = model_mod.status()
    cache = getattr(infer, "_CACHE", {})
    model_loaded = bool(cache.get("done") and cache.get("loaded") is not None)
    detector = "unet" if model_loaded else "sigma0_threshold_baseline"

    if not model_loaded:
        reason = infer.model_error() or "checkpoint not loaded yet"
        warnings.append(
            "Detection is running on the sigma0_threshold_baseline because the "
            "U-Net checkpoint has not been loaded on this process (%s). This is a "
            "startup health check, not a model validation run." % reason
        )

    if not status.get("checkpoint_present"):
        warnings.append(
            "No model checkpoint was found at %s. The app is serving the lightweight "
            "baseline path until a model is mounted or trained." % status.get("checkpoint_path")
        )

    storage = {
        "data_dir": str(config.DATA_DIR),
        "jobs_dir": str(config.JOBS_DIR),
        "cache_dir": str(config.CACHE_DIR),
        "sar_dir": str(config.SAR_DIR),
        "metocean_dir": str(config.METOCEAN_DIR),
    }

    return HealthResponse(
        ok=True,
        mode="offline" if config.OFFLINE else "online",
        cuda=bool(status["cuda"]),
        model_loaded=model_loaded,
        detector=detector,
        ais_rows=0,
        ais_vessels=0,
        metocean_scenes=0,
        scenes=0,
        version=config.VERSION,
        warnings=warnings,
        model_detail=status,
        storage=storage,
        config=config.as_dict(),
    )


@router.get("/api/config")
def get_config() -> Dict[str, Any]:
    return {
        "config": config.as_dict(),
        "scoring": ais_score.explain_weights(),
        "ui_title": config.UI_TITLE,
        "codename": config.PROJECT_CODENAME,
        "sih_id": config.SIH_ID,
    }


@router.get("/api/metocean")
def metocean() -> Dict[str, Any]:
    return {"cached": fields_mod.list_cached()}


@router.get("/api/ais/stats")
def ais_stats() -> Dict[str, Any]:
    return ais_ingest.stats().to_dict()
