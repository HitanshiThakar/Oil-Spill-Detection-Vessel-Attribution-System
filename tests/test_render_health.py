from __future__ import annotations


def test_health_is_lightweight_and_does_not_load_model(monkeypatch):
    from app.api import health as health_mod

    def boom():
        raise AssertionError("health route should not load the inference model")

    monkeypatch.setattr(health_mod.infer, "get_model", boom)
    monkeypatch.setattr(
        health_mod.model_mod,
        "status",
        lambda: {
            "torch": False,
            "smp": False,
            "cuda": False,
            "device": "cpu",
            "checkpoint_path": "models/oil_unet_best.pt",
            "checkpoint_present": False,
            "checkpoint_mb": None,
        },
    )

    payload = health_mod.health()

    assert payload.ok is True
    assert payload.model_loaded is False
    assert payload.detector == "sigma0_threshold_baseline"
    assert "baseline" in payload.warnings[0].lower()
