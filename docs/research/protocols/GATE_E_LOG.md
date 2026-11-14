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
| — | — | — | — | No entry: Gate E has not been passed. The flag is 0. |
