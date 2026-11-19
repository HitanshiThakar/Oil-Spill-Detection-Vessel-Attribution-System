# Render deployment: first single-service deployment

This repository is prepared for a single Render Web Service running the FastAPI app and the existing static dashboard together. The deployment intentionally does not add Vercel, Docker, Redis, Celery, or a separate database.

## Verified runtime

- App entry point: `app.main:app`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/api/health`
- Build command: `pip install -r requirements.txt`
- Render service type: `Web Service`
- Root directory: blank / repository root
- Runtime: Python 3
- Python version: 3.11

## Why this is the correct app object

The actual FastAPI application is created in `app/main.py` as `app = FastAPI(...)` and is mounted with the static dashboard and `/data` asset endpoint. The repository was validated by importing the module and confirming the app title and version from Python.

## Required Render config

- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/api/health`
- Environment variables:
  - `TIDETRACE_DATA=/var/data`
  - `TIDETRACE_MODELS=/var/data/models` (optional, if the project is intended to keep model files on the persistent disk)

## Persistent disk

Render should mount a persistent disk at `/var/data`. The application already uses `TIDETRACE_DATA` as its primary runtime root and creates runtime folders centrally in `app/config.py`.

Required runtime directories under `/var/data`:

- `ais/`
- `sar/`
- `metocean/`
- `jobs/`
- `cache/`
- `land/`
- `optical/`
- `basemap/`
- `uploads/`
- `reports/`
- `tmp/`

At startup these directories are created automatically when they do not exist.

## Runtime assets that must be seeded on the disk

The app can start from a fresh empty `/var/data` directory, but the following runtime assets should be copied or regenerated there before production use:

- AIS database: `data/ais/ais.sqlite`
- SAR scenes and index data: `data/sar/`
- metocean cache: `data/metocean/`
- job JSON and overlay PNG files: `data/jobs/`, `data/cache/`
- land mask assets: `data/land/`
- optional optical corroboration assets: `data/optical/`
- uploaded SAR inputs: `data/uploads/`
- generated reports and GeoJSON: `data/reports/`

The repository also ships a checkpoint in `models/oil_unet_best.pt`, which may be mounted or copied as part of the deployment if model inference is desired. The app is designed to run in a lightweight baseline mode if the checkpoint is absent, but that is not the same as a trained detector being active.

## Detector and model status

- Default detector: U-Net model path defined in `app/ml/model.py`
- Fallback detector: sigma0 threshold baseline in `app/ml/fallback.py`
- Current startup behavior: the app does not require PyTorch for startup or health checks
- Current rendering/Render deployment recommendation: keep the lightweight baseline path unless a later phase explicitly adds model deployment and checkpoint hosting
- Model checkpoint is optional for the first deployment; it must be handled as a separate deployment decision if the team wants active ML inference on Render

## Data / Git guidance

The repository tracks code and some small assets. Large generated data and unbundled runtime files must not be committed to Git. The `.gitignore` covers generated runtime artifacts in `data/` and temporary outputs, while the persistent disk is the correct place for runtime data on Render.

## Render filesystem and one-instance guidance

This first deployment is intentionally a single Render instance with one worker because the app is file-backed and process-local in important ways:

- job progress is process-local
- generated files are stored on disk
- AIS data and local caches are not shared across multiple instances
- multiple instances would create divergence in live state and files

Do not add Redis, Celery, PostgreSQL, or object storage for the first deployment unless the application already requires them by design. That would be a separate architecture decision.

## Security and CORS notes

- This deployment is not Vercel-specific and does not add a separate frontend domain
- CORS is currently permissive at the FastAPI layer for local/dashboard compatibility and is not authentication
- This is not a replacement for access control
- Secrets should not be placed in frontend JavaScript or committed to source control

## Future Vercel split

A later Vercel frontend split should keep the API on Render and move only the static UI to a separate frontend host if desired. That would be a separate phase after the single-service deployment is stable.

## Recommended later phases

- Add explicit model deployment configuration and checkpoint hosting
- Add Render environment validation for model and cache readiness
- Consider a dedicated web app split for Vercel or a separate static frontend when product requirements demand it
- Add stronger monitoring and alerting for data directory exhaustion or checkpoint failures

## Manual Render steps

1. Create a new Render Web Service from this repository.
2. Select Python runtime, not Docker.
3. Use repository root as the root directory.
4. Set the build command to `pip install -r requirements.txt`.
5. Set the start command to `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
6. Add a health check route `/api/health`.
7. Mount a persistent disk at `/var/data`.
8. Add the environment variable `TIDETRACE_DATA=/var/data`.
9. Optionally add `TIDETRACE_MODELS=/var/data/models` if the model is stored on the disk.
10. Deploy and confirm the service starts.

## Deployment caveat

This repository is now locally verified for startup and health-route behavior. It is not claimed to be a production-validated model deployment. The model path remains a later-phase architecture decision unless a separate deployment step is intentionally added for trained inference.
