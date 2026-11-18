# Gate E log

The dated record of the one action that lets external labels and performance be read:
flipping `GLIOMA_EXTERNAL_EVAL_AUTHORIZED` to `1` (EXTERNAL_VALIDATION_PROTOCOL.md section 2
and 3). **Research Lead only; not delegable.** An entry is written before the flag flips,
after the freeze manifest is signed and hashed, and it names the manifest SHA-256.

`src/glioma_selective/evaluation/firewall.py` refuses every external label or performance
access until both the flag and a signed manifest at `experiments/gate_e/freeze_manifest.json`
(with a matching `.sha256` sidecar) exist.

| Date (UTC) | Event | Freeze manifest SHA-256 | Signed by | Notes |
|---|---|---|---|---|
| 2026-11-18, about 10:21 UTC (15:51 server time) | Freeze manifest signed and sealed; GLIOMA_EXTERNAL_EVAL_AUTHORIZED=1 set for one command to run the Phase 12 external evaluation (UCSF-PDGM, run id ucsf_pdgm_gate_e_20261118) on the home PC | 2af464b078c3229e2d2a5839fe42577fefd3c2b90d70c33f9d14d57c5086263d | Aniket Saha | Entry written after the flip, not before as this log requires. Manifest pins code commit 2fd951314439fcd216c7e95f87fd0316d8df3a5c. EGD is deferred (D-057). Gate D was not yet signed when the flag was set. |
