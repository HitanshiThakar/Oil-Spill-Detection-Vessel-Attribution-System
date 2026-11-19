# OCEANUS Project Journal

This journal documents the current state of the OCEANUS project for Smart India Hackathon challenge PS26143: "Leveraging satellite imagery to determine Oil spills at sea along with AIS data correlations to identify vessel responsible".

This record is intentionally grounded in the repository as it exists today. It preserves useful historical context from the earlier technical baseline while making clear that the active project identity is OCEANUS and that the current implementation is an evidence-based analysis workflow rather than a legal attribution engine.

---

## 1. Project identity and scope

The repository is the OCEANUS project, not a continuation of the older TideTrace branding. The project is organized around a maritime oil-spill investigation workflow that combines SAR scene analysis, drift estimation, AIS correlation, and analyst-facing reporting.

The current app structure shows a clear product flow:

- app/main.py: FastAPI entry point and browser shell
- app/pipeline.py: orchestrated detection and analysis workflow
- app/config.py: runtime configuration and local data settings
- app/api/: detection, drift, health, pipeline, and report APIs
- app/drift/: advection and environmental analysis
- app/geo/: geospatial and raster helper code
- app/ais/: AIS ingestion and scoring
- app/ml/: detection model and inference flow
- app/static/: dashboard front end

The implemented workflow is designed to support investigation and candidate attribution. It is not a legal proof engine and it is not marketed as field-validated causality in the sense of a court-admissible finding.

---

## 2. Historical baseline and proper framing

An earlier maritime oil-spill analysis codebase was reviewed as a technical baseline before OCEANUS was finalized around the SIH PS26143 requirements. That baseline was valuable for understanding patterns in:

- SAR preprocessing and dark-patch detection
- drift backtracking and origin-zone estimation
- AIS reconstruction and ranking logic
- analyst dashboard structure and report design

Those ideas were selectively adapted into the current repository. The historical baseline remains relevant as engineering context, but it is not the same as the active OCEANUS implementation.

The distinction matters because the current project is evidence-based support software, not a direct continuation of a legacy product name or brand.

---

## 3. Problem statement as implemented

The challenge asks for a system that can:

1. detect oil-like signatures in satellite imagery,
2. distinguish oil from look-alikes where possible,
3. estimate drift and likely origin zone,
4. correlate the result with AIS vessel activity,
5. rank candidate vessels with explainable reasons.

The current repository aligns with that flow and keeps its outputs scoped as candidate evidence. The system is designed as an analyst workflow to support a human review decision rather than to make an automatic legal attribution.

---

## 4. Repository evidence of the current project state

The repo contains the current OCEANUS implementation and supporting assets:

- app/ml/model.py and app/ml/infer.py: model loader and inference path
- models/oil_unet_best.pt: current checkpoint asset
- models/oil_unet_best.report.json: checkpoint summary including validation metrics
- app/pipeline.py: end-to-end execution orchestration
- app/drift/: advection and origin-zone logic
- app/api/: analyst and operator endpoints
- tests/: automated validation for pipeline behavior and UI contract

The code and assets clearly indicate an implemented product, not a speculative design document. At the same time, the repository still treats scientific validation and software validation as separate concerns.

---

## 5. Detection and model status

The current model path is implemented around a U-Net-style segmentation architecture. The checkpoint metadata records the following values:

- IoU sea: 0.9822
- IoU oil: 0.8891
- mIoU: 0.9356
- pixel accuracy: 0.9844
- water_false_oil: 0.0106

These values are repository-verified checkpoint metrics from the project assets. They are not field-level proof of correct spill detection in all real-world scenes. The repository keeps an explicit distinction between:

- model metrics from local validation data, and
- operational performance in actual maritime incidents.

The project also includes a baseline fallback path when the trained model is unavailable. This fallback is intentionally important because it supports local, offline operation and keeps a reproducible non-model path in the system.

---

## 6. Scene processing and geospatial analysis

The codebase processes SAR scenes, handles georeferencing, and extracts polygon-level geometry from dark features that may correspond to oil slicks. The geometry layer computes scene-level features such as area, perimeter, length, width, orientation, compactness, and local contrast.

This is a meaningful part of the workflow because detection is not reduced to a binary mask alone. The project turns the mask into inspectable geometry that can be ranked, checked for look-alikes, and examined for drift behaviour.

The repository also includes logic for land and false-positive suppression, which is essential in coastal and near-shore regions where radar-dark features are not necessarily oil.

---

## 7. Drift and origin estimation

The drift modules in the project estimate likely origin zones and time windows using metocean fields and advection logic. The workflow is designed to backtrack a suspected slick to a plausible source area and also create a forward-looking forecast cone.

This is implemented as investigative support rather than absolute proof. The origin estimate is useful because it narrows the search space for AIS correlation and candidate review, but it does not by itself establish a discharge event or legal responsibility.

The repository also treats data coverage as a real limitation. Missing or incomplete current fields are surfaced in the run output instead of silently treated as valid drift input.

---

## 8. AIS integration and candidate ranking

The AIS pipeline is a core part of the challenge and is implemented in the current codebase. It covers:

- local AIS ingestion
- time-window and spatial filtering
- track reconstruction and gap handling
- vessel candidate search near the suspected origin
- scoring using distance, speed, vessel type, and behaviour patterns

Candidate ranking is explainable and transparent: the system can report why a vessel scored highly and which weight components contributed to the result. This design is appropriate for analyst review work.

The project keeps the causal language honest: a ranked vessel is a candidate vessel, not a proven culprit.

---

## 9. Analyst-facing reporting and dashboard

The app exposes a browser dashboard and API surface for running the analysis and reviewing outputs. The front end is built around the SAR scene, spill overlays, drift cones, AIS tracks, and a ranked candidate leaderboard.

The API and dashboard support:

- health checks
- detection runs
- drift analysis
- report generation
- job and trace output

This shows the project is structured as an operational analyst tool rather than an opaque model wrapper.

---

## 10. Testing status and what it proves

The repository test suite was run and verified in the current environment:

- 113 passed
- 2 skipped
- 0 failed

This is evidence of healthy software-level validation. It is not evidence that all detection or attribution claims are scientifically complete or legally binding.

The correct inference is: the code is functioning as a coherent project with a stable test baseline, while still requiring domain review and scientific caution in the actual maritime application context.

---

## 11. Development decisions captured from repository reality

The current project is intentionally built around a set of practical engineering decisions that are observable in the code:

- local data + offline-ready execution paths are supported
- optional external preparation steps are separated from the core app
- fallback logic is kept available when model assets are absent
- drift and AIS evidence are kept explainable and reviewable
- the repository avoids pretending that candidate ranking equals legal attribution

These decisions are aligned with the challenge requirement and with the repository's actual architecture.

---

## 12. Production claims and caution

The project should not claim operational certainty beyond the evidence available in the repo.

Important guardrails:

- checkpoint metrics are not field validation
- candidate ranking is not legal responsibility
- drift estimates are support for investigation, not proof
- the dashboard is an analyst console, not a certified enforcement interface
- Docker/configuration files are operational packaging and should not be mistaken for proven production deployment

The repository is therefore best understood as a robust decision-support prototype with explicit uncertainty boundaries, not as an unqualified final authority on real spill attribution.

---

## 13. Current status summary

At the current state of the repo:

- OCEANUS is the active project identity.
- The project addresses the PS26143 challenge through SAR, drift, and AIS integrated analysis.
- The codebase is functional and test-validated at the software level.
- Candidate vessel attribution is implemented and explainable.
- Scientific and legal certainty remain separate concerns from software correctness.

This journal therefore records an honest engineering baseline: the repository is a real implemented OCEANUS solution for the challenge, but it is still a decision-support system with clear methodological limits and no claim of final legal adjudication.

---

## 14. Final project note

The central lesson of this journal is simple: the repository should be described as a practical OCEANUS investigation tool that is backed by code, tested behavior, and structured evidence, while staying explicit that its outputs are support for human review rather than final proof of culpability.

The challenge is addressed through engineering discipline, transparent limitations, and evidence-first interpretation. That is the appropriate boundary for the current state of the project.
