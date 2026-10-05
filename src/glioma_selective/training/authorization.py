"""Seven ordered checks required before a Phase 06 training run (T06.8)."""

from __future__ import annotations

import errno
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import warnings
from contextlib import AbstractContextManager, nullcontext
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast

import torch

from glioma_selective.models.segresnet import IDHNet, ModelConfig, build_model
from glioma_selective.training.checkpoint import (
    load_checkpoint,
)
from glioma_selective.training.determinism import deterministic_mode
from glioma_selective.training.loop import TrainConfig, fit, make_optimizer
from glioma_selective.training.losses import joint_loss
from glioma_selective.utils import paths

__all__ = [
    "HARNESS_VERSION",
    "STEP_NAMES",
    "HarnessReport",
    "StepResult",
    "assert_authorized",
    "run_harness",
    "step_cpu_unit_tests",
    "step_data_sample",
    "step_tiny_forward",
    "step_tiny_overfit",
    "step_gpu_memory",
    "step_checkpoint_equivalence",
    "base_config_sha256",
    "step_deterministic_logging",
    "write_harness_report",
]

HARNESS_VERSION = "1.0.0"
STEP_NAMES = (
    "CPU unit tests",
    "one-sample data test",
    "tiny-batch forward pass",
    "tiny overfit",
    "GPU memory test",
    "checkpoint save/resume equivalence",
    "deterministic/config logging",
)
StepStatus = Literal["passed", "failed", "not_run"]


@dataclass(frozen=True)
class StepResult:
    """One harness outcome. Details must never include patient identifiers."""

    name: str
    status: StepStatus
    detail: str
    seconds: float


@dataclass(frozen=True)
class HarnessReport:
    """Serializable evidence for one authorization attempt."""

    results: tuple[StepResult, ...]
    authorized: bool
    device: str
    git_sha: str
    git_dirty: bool
    config_sha256: str
    frozen_hashes: dict[str, str]
    timestamp_utc: str
    harness_version: str
    authorization_run_id: str
    synthetic: bool = False


@dataclass(frozen=True)
class _Inputs:
    model_config: ModelConfig
    training_config: TrainConfig
    model_mapping: dict[str, Any]
    training_mapping: dict[str, Any]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _git(*args: str) -> str:
    completed = subprocess.run(
        ("git", *args), cwd=_repo_root(), check=True, capture_output=True, text=True
    )
    return completed.stdout.strip()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sidecar_digest(path: Path) -> str:
    sidecar = path.with_name(path.name + ".sha256")
    try:
        expected = sidecar.read_text(encoding="ascii").split()[0].lower()
    except (OSError, UnicodeError, IndexError) as exc:
        raise ValueError(
            f"missing or invalid frozen hash sidecar for {path.name}"
        ) from exc
    actual = _sha256(path)
    if not re.fullmatch(r"[0-9a-f]{64}", expected) or actual != expected:
        raise ValueError(f"frozen hash verification failed for {path.name}")
    return actual


def _atomic_json_once(path: Path, payload: str, *, prefix: str) -> Path:
    """Atomically publish JSON once, including filesystems without hard links."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=prefix, suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            raise FileExistsError(f"file already exists: {path}") from None
        except OSError as exc:
            unsupported_link = {errno.ENOTSUP, errno.EOPNOTSUPP, errno.EXDEV}
            if exc.errno not in unsupported_link:
                raise
            lock = path.with_name(f".{path.name}.authorization-lock")
            lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            try:
                if path.exists():
                    raise FileExistsError(f"file already exists: {path}")
                os.replace(temporary, path)
                directory_fd = os.open(path.parent, os.O_RDONLY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            finally:
                os.close(lock_fd)
                lock.unlink(missing_ok=True)
        temporary.unlink(missing_ok=True)
    finally:
        temporary.unlink(missing_ok=True)
    return path


def _frozen_hashes() -> dict[str, str]:
    manifests = paths.manifests_dir()
    return {
        "splits.json": _sidecar_digest(manifests / "splits.json"),
        "normalization_stats.json": _sidecar_digest(
            manifests / "normalization_stats.json"
        ),
    }


def _load_real_dataset(
    count: int | None = None,
    *,
    augment: bool = False,
    zero_channels: tuple[int, ...] = (),
    sorted_ids: bool = False,
) -> Any:
    from glioma_selective.data.dataset import IDHDataset, load_split_patient_ids
    from glioma_selective.preprocessing.normalize import load_normalization_stats

    manifests = paths.manifests_dir()
    stats_path = manifests / "normalization_stats.json"
    stats_digest = _sidecar_digest(stats_path)
    split_digest = _sidecar_digest(manifests / "splits.json")
    stats = load_normalization_stats(stats_path, expected_sha256=stats_digest)
    if stats.split_manifest_sha256 != split_digest:
        raise ValueError("normalization statistics refer to a different frozen split")
    patient_ids = load_split_patient_ids("train")
    if sorted_ids:
        patient_ids.sort()
    if count is not None:
        patient_ids = patient_ids[:count]
    return IDHDataset(
        patient_ids,
        stats=stats,
        seed=0,
        augment=augment,
        zero_channels=zero_channels,
        storage=paths.processed_data_dir(),
    )


def _synthetic_batch() -> dict[str, torch.Tensor]:
    """Small separable four-patient fixture matching test_training_loop.py."""
    generator = torch.Generator().manual_seed(1)
    labels = torch.tensor([0.0, 1.0, 0.0, 1.0])
    images = torch.randn(4, 4, 8, 8, 8, generator=generator) * 0.1
    images += (labels * 2.0 - 1.0).view(4, 1, 1, 1, 1)
    seg = torch.zeros(4, 3, 8, 8, 8)
    seg[:, 0, 2:6, 2:6, 2:6] = 1.0
    return {
        "image": images,
        "seg": seg,
        "has_seg": torch.ones(4, dtype=torch.bool),
        "label": labels,
    }


def _small_model_config() -> ModelConfig:
    return ModelConfig(
        init_filters=8,
        blocks_down=(1, 1, 1, 1),
        head_hidden=8,
        head_dropout=0.0,
    )


def _inputs(synthetic: bool, *, seed: int = 0) -> _Inputs:
    model_config = _small_model_config() if synthetic else ModelConfig()
    model_mapping = asdict(model_config)
    training_config = TrainConfig(seed=seed)
    training_mapping = asdict(training_config)
    return _Inputs(model_config, training_config, model_mapping, training_mapping)


def _config_sha256(inputs: _Inputs) -> str:
    payload = {"model": inputs.model_mapping, "training": inputs.training_mapping}
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def base_config_sha256() -> str:
    """Digest of the base model and training configs an authorization report covers."""
    return _config_sha256(_inputs(False))


def _result(name: str, status: StepStatus, detail: str, started: float) -> StepResult:
    safe_detail = re.sub(
        r"\bUTSW[-_ ]?[A-Za-z0-9-]+\b", "[patient id redacted]", detail
    )
    return StepResult(name, status, safe_detail, time.monotonic() - started)


def _failed(name: str, started: float, error: BaseException) -> StepResult:
    return _result(name, "failed", f"{type(error).__name__}: {error}", started)


def step_cpu_unit_tests() -> StepResult:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            (sys.executable, "-m", "pytest", "tests/unit", "-q"),
            cwd=_repo_root(),
            check=False,
            capture_output=True,
            text=True,
        )
        summary = (completed.stdout + "\n" + completed.stderr).strip()
        match = re.search(r"(?:^|\s)(\d+) passed(?:[,\s]|$)", summary)
        count = int(match.group(1)) if match else None
        if completed.returncode == 0:
            detail = (
                f"{count} passed"
                if count is not None
                else "exit 0; passed count unavailable"
            )
            return _result(STEP_NAMES[0], "passed", detail, started)
        tail = " | ".join(line.strip() for line in summary.splitlines()[-5:])
        return _result(
            STEP_NAMES[0], "failed", f"exit {completed.returncode}; {tail}", started
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return _failed(STEP_NAMES[0], started, exc)


def step_data_sample() -> StepResult:
    started = time.monotonic()
    try:
        dataset = _load_real_dataset(1, augment=True)
        sample = dataset[0]
        image, seg, label = sample["image"], sample["seg"], sample["label"]
        if image.shape != (4, 96, 96, 96) or image.dtype != torch.float32:
            raise AssertionError("image must be float32 [4,96,96,96]")
        if not torch.isfinite(image).all():
            raise AssertionError("image contains non-finite values")
        if seg.shape != (3, 96, 96, 96) or not torch.all((seg == 0) | (seg == 1)):
            raise AssertionError("segmentation must be binary [3,96,96,96]")
        if label.item() not in (0.0, 1.0):
            raise AssertionError("IDH label must be binary")
        background = image.eq(0).all(dim=0)
        if torch.count_nonzero(image[:, background]):
            raise AssertionError("image background is not exactly zero")
        zeroed = _load_real_dataset(1, augment=False, zero_channels=(2,))[0]
        if torch.count_nonzero(zeroed["image"][2]):
            raise AssertionError("zero_channels=(2,) did not zero channel 2")
        dataset.set_epoch(4)
        first = dataset[0]
        dataset.set_epoch(4)
        second = dataset[0]
        for key in ("image", "seg", "label", "has_seg"):
            if first[key].numpy().tobytes() != second[key].numpy().tobytes():
                raise AssertionError(
                    "fixed seed and epoch augmentation is not byte-identical"
                )
        return _result(
            STEP_NAMES[1],
            "passed",
            "1 sample; data, zero-channel and augmentation checks passed",
            started,
        )
    except Exception as exc:
        return _failed(STEP_NAMES[1], started, exc)


def _device(value: str | torch.device) -> torch.device:
    if isinstance(value, torch.device):
        selected = value
    elif value == "auto":
        selected = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        selected = torch.device(value)
    return selected


def _select_labeled_patients(count: int, *, balanced: bool) -> Any:
    dataset = _load_real_dataset(None, augment=False, sorted_ids=balanced)
    if not balanced:
        indices = [0]
        for index, label in enumerate(dataset._labels[:10]):
            if label != dataset._labels[0]:
                indices.append(index)
                break
        if len(indices) < 2:
            for index, label in enumerate(dataset._labels[10:], start=10):
                if label != dataset._labels[0]:
                    indices.append(index)
                    break
        if len(indices) < 2:
            indices = list(range(min(count, len(dataset))))
    else:
        mutants = [i for i, label in enumerate(dataset._labels) if label == 1.0][:2]
        wildtypes = [i for i, label in enumerate(dataset._labels) if label == 0.0][:2]
        if len(mutants) < 2 or len(wildtypes) < 2:
            raise ValueError(
                "frozen train split does not contain two patients per IDH class"
            )
        indices = sorted([*mutants, *wildtypes])
    selected = [dataset[index] for index in indices[:count]]
    return {
        "image": torch.stack([item["image"] for item in selected]),
        "seg": torch.stack([item["seg"] for item in selected]),
        "has_seg": torch.stack([item["has_seg"] for item in selected]),
        "label": torch.stack([item["label"] for item in selected]),
    }


def _forward_batch(
    synthetic: bool, *, count: int, balanced: bool = False
) -> dict[str, torch.Tensor]:
    if synthetic:
        batch = _synthetic_batch()
        return {key: value[:count] for key, value in batch.items()}
    return cast(
        dict[str, torch.Tensor], _select_labeled_patients(count, balanced=balanced)
    )


def step_tiny_forward(
    device: str | torch.device, *, synthetic: bool = False
) -> StepResult:
    started = time.monotonic()
    try:
        selected_device = _device(device)
        batch = _forward_batch(synthetic, count=2)
        model = build_model(_small_model_config() if synthetic else ModelConfig()).to(
            selected_device
        )
        model.eval()
        image = batch["image"].to(selected_device)
        with torch.no_grad():
            output = model(image)
            zeroed = image.clone()
            zeroed[:, 2] = 0
            zero_output = model(zeroed)
        if output.logit.shape != (2,) or not torch.isfinite(output.logit).all():
            raise AssertionError("classification logits must be finite with shape [2]")
        expected = (2, 3, *image.shape[2:])
        if output.seg_logits is None or tuple(output.seg_logits.shape) != expected:
            raise AssertionError(f"segmentation logits must have shape {expected}")
        if (
            not torch.isfinite(output.seg_logits).all()
            or not torch.isfinite(zero_output.logit).all()
        ):
            raise AssertionError("forward pass with a zeroed channel is non-finite")
        return _result(
            STEP_NAMES[2],
            "passed",
            f"batch=2; device={selected_device}; logits finite with zeroed channel",
            started,
        )
    except Exception as exc:
        return _failed(STEP_NAMES[2], started, exc)


def _overfit(
    batch: dict[str, torch.Tensor],
    *,
    model_config: ModelConfig,
    device: torch.device,
    max_steps: int,
    threshold: float,
    learning_rate: float,
) -> tuple[StepStatus, int, float, list[float]]:
    torch.manual_seed(0)
    model = build_model(model_config).to(device)
    model.train()
    config = TrainConfig(
        seed=0,
        max_epochs=1,
        batch_size=2,
        accumulation_steps=1,
        learning_rate=learning_rate,
        weight_decay=0.0,
        grad_clip_norm=1.0,
        amp="off",
        seg_weight=1.0,
    )
    optimizer = make_optimizer(model, config)
    tensors = {key: value.to(device) for key, value in batch.items()}
    history: list[float] = []
    used = 0
    for step in range(1, max_steps + 1):
        optimizer.zero_grad(set_to_none=True)
        for start in (0, 2):
            part = {key: value[start : start + 2] for key, value in tensors.items()}
            output = model(part["image"])
            losses = joint_loss(
                output.logit.float(),
                None if output.seg_logits is None else output.seg_logits.float(),
                part["label"],
                part["seg"],
                part["has_seg"],
                pos_weight=1.0,
                seg_weight=config.seg_weight,
                dice_smooth=config.dice_smooth,
            )
            (losses.total / 2).backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), config.grad_clip_norm)
        optimizer.step()
        model.eval()
        with torch.no_grad():
            output = model(tensors["image"])
            losses = joint_loss(
                output.logit.float(),
                None if output.seg_logits is None else output.seg_logits.float(),
                tensors["label"],
                tensors["seg"],
                tensors["has_seg"],
                pos_weight=1.0,
                seg_weight=0.0,
                dice_smooth=config.dice_smooth,
            )
        loss = float(losses.classification)
        history.append(loss)
        used = step
        if loss < threshold:
            return "passed", used, loss, history
        model.train()
    return "failed", used, history[-1], history


def step_tiny_overfit(
    device: str | torch.device,
    *,
    max_steps: int = 150,
    overfit_threshold: float = 0.05,
    synthetic: bool = False,
    learning_rate: float = 3.0e-4,
) -> StepResult:
    started = time.monotonic()
    if not synthetic:
        try:
            selected = _device(device)
        except Exception as exc:
            return _failed(STEP_NAMES[3], started, exc)
        if selected.type != "cuda":
            return _result(
                STEP_NAMES[3],
                "not_run",
                "real 4-patient overfit is pending a CUDA GPU",
                started,
            )
    try:
        selected = _device(device)
        batch = (
            _synthetic_batch()
            if synthetic
            else _forward_batch(False, count=4, balanced=True)
        )
        model_config = _small_model_config() if synthetic else ModelConfig()
        status, steps, loss, curve = _overfit(
            batch,
            model_config=model_config,
            device=selected,
            max_steps=max_steps,
            threshold=overfit_threshold,
            learning_rate=learning_rate,
        )
        summary = (
            f"steps={steps}; final_loss={loss:.8g}; "
            f"curve_start={curve[0]:.8g}; curve_min={min(curve):.8g}; "
            f"curve_end={curve[-1]:.8g}"
        )
        return _result(STEP_NAMES[3], status, summary, started)
    except Exception as exc:
        return _failed(STEP_NAMES[3], started, exc)


def step_gpu_memory(*, synthetic: bool = False) -> StepResult:
    started = time.monotonic()
    if synthetic:
        return _result(
            STEP_NAMES[4],
            "not_run",
            "synthetic wiring mode does not measure the target 96^3 GPU workload",
            started,
        )
    if not torch.cuda.is_available():
        return _result(STEP_NAMES[4], "not_run", "no CUDA device", started)
    try:
        device = torch.device("cuda")
        config = TrainConfig()
        batch = (
            _synthetic_batch()
            if synthetic
            else _forward_batch(False, count=config.batch_size)
        )
        model = build_model(_small_model_config() if synthetic else ModelConfig()).to(
            device
        )
        tensors = {key: value.to(device) for key, value in batch.items()}
        torch.cuda.reset_peak_memory_stats(device)
        amp_context: AbstractContextManager[Any] = nullcontext()
        if config.amp != "off":
            dtype = torch.bfloat16 if config.amp == "bf16" else torch.float16
            amp_context = torch.autocast(device_type="cuda", dtype=dtype)
        with amp_context:
            output = model(tensors["image"])
        losses = joint_loss(
            output.logit.float(),
            None if output.seg_logits is None else output.seg_logits.float(),
            tensors["label"],
            tensors["seg"],
            tensors["has_seg"],
            pos_weight=1.0,
            seg_weight=config.seg_weight,
            dice_smooth=config.dice_smooth,
        )
        losses.total.backward()
        peak = torch.cuda.max_memory_allocated(device)
        total = torch.cuda.get_device_properties(device).total_memory
        name = torch.cuda.get_device_name(device)
        detail = (
            f"device={name}; peak_bytes={peak}; total_bytes={total}; "
            f"fraction={peak / total:.6f}"
        )
        if peak >= 0.9 * total:
            return _result(
                STEP_NAMES[4],
                "failed",
                detail + "; exceeds 90%; follow D-005/R-H04 accommodation ladder",
                started,
            )
        return _result(STEP_NAMES[4], "passed", detail, started)
    except torch.cuda.OutOfMemoryError as exc:
        torch.cuda.empty_cache()
        return _result(
            STEP_NAMES[4],
            "failed",
            f"CUDA OOM; follow the D-005/R-H04 accommodation ladder; {exc}",
            started,
        )
    except Exception as exc:
        return _failed(STEP_NAMES[4], started, exc)


class _TensorDataset:
    def __init__(self, tensors: dict[str, torch.Tensor]) -> None:
        self.tensors = tensors
        self.epoch = 0

    def set_epoch(self, epoch: int) -> None:
        self.epoch = epoch


class _TensorLoader:
    def __init__(self, dataset: _TensorDataset) -> None:
        self.dataset = dataset

    def __iter__(self):  # type: ignore[no-untyped-def]
        for start in range(0, len(self.dataset.tensors["label"]), 2):
            yield {
                key: value[start : start + 2]
                for key, value in self.dataset.tensors.items()
            }


def _parameter_difference(left: IDHNet, right: IDHNet) -> float:
    differences = [
        (a.detach() - b.detach()).abs().max().item()
        for a, b in zip(left.parameters(), right.parameters(), strict=True)
    ]
    return max(differences, default=0.0)


def step_checkpoint_equivalence(
    device: str | torch.device, *, synthetic: bool = False
) -> StepResult:
    """Resume must reproduce an uninterrupted run exactly, on CPU and on CUDA."""
    started = time.monotonic()
    with deterministic_mode():
        return _checkpoint_equivalence(device, synthetic=synthetic, started=started)


def _checkpoint_equivalence(
    device: str | torch.device, *, synthetic: bool, started: float
) -> StepResult:
    try:
        selected = _device(device)
        batch = (
            _synthetic_batch()
            if synthetic
            else _forward_batch(False, count=4, balanced=True)
        )
        config_model = _small_model_config() if synthetic else ModelConfig()
        config_train = TrainConfig(
            max_epochs=4,
            batch_size=2,
            accumulation_steps=1,
            learning_rate=1e-3,
            weight_decay=0.0,
            amp="off",
            early_stopping_patience=10,
        )
        dataset = _TensorDataset(batch)
        train_loader = _TensorLoader(dataset)
        calibration_loader = _TensorLoader(dataset)
        torch.manual_seed(909)
        straight = build_model(config_model)
        fit(
            straight,
            train_loader,
            calibration_loader,
            config_train,
            pos_weight=1.0,
            checkpoint_dir=Path(tempfile.mkdtemp()) / "straight",
            device=selected,
            resume=False,
            stop_after_steps=3,
        )
        straight_dir = Path(tempfile.mkdtemp()) / "resumed"
        torch.manual_seed(909)
        partial = build_model(config_model)
        first = fit(
            partial,
            train_loader,
            calibration_loader,
            config_train,
            pos_weight=1.0,
            checkpoint_dir=straight_dir,
            device=selected,
            resume=False,
            stop_after_steps=1,
        )
        if not first.interrupted:
            raise AssertionError("mid-epoch run did not stop at the requested step")
        resumed = build_model(config_model)
        second = fit(
            resumed,
            train_loader,
            calibration_loader,
            config_train,
            pos_weight=1.0,
            checkpoint_dir=straight_dir,
            device=selected,
            resume=True,
            stop_after_steps=3,
        )
        if not second.interrupted:
            raise AssertionError("resumed run did not reach the requested step")
        difference = _parameter_difference(straight, resumed)
        if not all(
            torch.equal(a, b)
            for a, b in zip(straight.parameters(), resumed.parameters(), strict=True)
        ):
            raise AssertionError(
                f"resumed parameters differ on {selected.type}; "
                f"max_abs={difference:.8g}"
            )

        checkpoint_path = straight_dir / "last.pt"
        checkpoint_model = build_model(config_model).to(selected)
        optimizer = make_optimizer(checkpoint_model, config_train)
        state = load_checkpoint(
            checkpoint_path, model=checkpoint_model, optimizer=optimizer, scaler=None
        )
        del state
        probe = batch["image"][:2].to(selected)
        straight.eval()
        checkpoint_model.eval()
        with torch.no_grad():
            expected = straight(probe)
            actual = checkpoint_model(probe)
        if not torch.equal(expected.logit, actual.logit):
            raise AssertionError(
                "save/load/forward output is not numerically identical"
            )
        if (
            expected.seg_logits is not None
            and actual.seg_logits is not None
            and not torch.equal(expected.seg_logits, actual.seg_logits)
        ):
            raise AssertionError(
                "save/load segmentation forward output is not numerically identical"
            )
        return _result(
            STEP_NAMES[5],
            "passed",
            f"N=3; resumed_max_abs={difference:.8g}; checkpoint forward identical",
            started,
        )
    except Exception as exc:
        return _failed(STEP_NAMES[5], started, exc)


def step_deterministic_logging(
    inputs: _Inputs,
    *,
    authorization_run_id: str,
    synthetic: bool,
    device: torch.device,
) -> StepResult:
    started = time.monotonic()
    try:
        frozen = _frozen_hashes()
        from glioma_selective.tracking.run_record import (
            assert_launch_ready,
            build_run_record,
            write_run_record,
        )

        manifests = paths.manifests_dir()
        preprocessing_outputs = manifests / "preprocessing_outputs.json"
        exclusions = manifests / "exclusion_manifest_post_qc.json"
        if not preprocessing_outputs.is_file() or not exclusions.is_file():
            raise ValueError("UTSW preprocessing and exclusion manifests are required")
        config = {"model": inputs.model_mapping, "training": inputs.training_mapping}
        record = build_run_record(
            dataset_manifest_hash=_sha256(preprocessing_outputs),
            exclusion_list_hash=_sha256(exclusions),
            config=config,
            seed=inputs.training_config.seed,
            preprocessing_version="phase06-frozen-zscore-and-2mm-whole-brain",
            parameter_hash=hashlib.sha256(
                json.dumps(config, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
            normalization_stats_sha256=frozen["normalization_stats.json"],
            repo_root=_repo_root(),
        )
        record = replace(record, run_id=authorization_run_id)
        assert_launch_ready(record)
        hard_link_fallback = False
        try:
            write_run_record(record)
        except OSError as exc:
            if exc.errno not in {errno.ENOTSUP, errno.EOPNOTSUPP, errno.EXDEV}:
                raise
            record_path = paths.experiments_dir() / authorization_run_id / "record.json"
            _atomic_json_once(
                record_path,
                json.dumps(asdict(record), indent=2, sort_keys=True) + "\n",
                prefix=".record-",
            )
            hard_link_fallback = True
        deterministic_ops: list[str] = []
        was_deterministic = torch.are_deterministic_algorithms_enabled()
        was_warn_only = torch.is_deterministic_algorithms_warn_only_enabled()
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                torch.use_deterministic_algorithms(True, warn_only=True)
                batch = (
                    _synthetic_batch() if synthetic else _forward_batch(False, count=2)
                )
                probe = build_model(inputs.model_config).to(device)
                tensors = {key: value.to(device) for key, value in batch.items()}
                output = probe(tensors["image"])
                losses = joint_loss(
                    output.logit.float(),
                    None if output.seg_logits is None else output.seg_logits.float(),
                    tensors["label"],
                    tensors["seg"],
                    tensors["has_seg"],
                    pos_weight=1.0,
                    seg_weight=inputs.training_config.seg_weight,
                    dice_smooth=inputs.training_config.dice_smooth,
                )
                losses.total.backward()
                deterministic_ops.append(
                    "torch.use_deterministic_algorithms(True, warn_only=True)"
                )
            deterministic_ops.extend(
                f"non-deterministic operation warning: {item.message}"
                for item in caught
            )
            if not caught:
                deterministic_ops.append(
                    "no non-deterministic operation warnings in the logging probe"
                )
        finally:
            torch.use_deterministic_algorithms(
                was_deterministic, warn_only=was_warn_only
            )
        detail = "launch record accepted; clean checkout; " + "; ".join(
            deterministic_ops
        )
        if hard_link_fallback:
            detail += "; atomic rename used because hard links are unsupported"
        if synthetic:
            detail += "; synthetic run is never authorized"
        return _result(STEP_NAMES[6], "passed", detail, started)
    except Exception as exc:
        return _failed(STEP_NAMES[6], started, exc)


def run_harness(
    *,
    device: str = "auto",
    max_steps: int = 150,
    overfit_threshold: float = 0.05,
    synthetic: bool = False,
    run_cpu_tests: bool = True,
) -> HarnessReport:
    """Run all seven steps in order; failed steps stop later checks."""
    if max_steps < 1:
        raise ValueError("max_steps must be at least one")
    selected = _device(device)
    inputs = _inputs(synthetic)
    config_sha = _config_sha256(inputs)
    try:
        git_sha = _git("rev-parse", "HEAD")
        git_dirty = bool(_git("status", "--porcelain"))
    except (OSError, subprocess.SubprocessError):
        git_sha, git_dirty = "unavailable", True
    try:
        frozen = _frozen_hashes()
    except (OSError, ValueError, paths.PathResolutionError):
        frozen = {}
    from glioma_selective.tracking.run_record import generate_run_id

    run_id = generate_run_id()
    results: list[StepResult] = []
    if run_cpu_tests:
        results.append(step_cpu_unit_tests())
        if results[-1].status == "failed":
            return _make_report(
                results,
                selected,
                git_sha,
                git_dirty,
                config_sha,
                frozen,
                run_id,
                synthetic,
            )
    else:
        results.append(StepResult(STEP_NAMES[0], "not_run", "disabled by caller", 0.0))

    if synthetic:
        results.append(
            StepResult(
                STEP_NAMES[1],
                "not_run",
                "synthetic wiring mode has no real UTSW sample",
                0.0,
            )
        )
    else:
        results.append(step_data_sample())
        if results[-1].status == "failed":
            return _make_report(
                results,
                selected,
                git_sha,
                git_dirty,
                config_sha,
                frozen,
                run_id,
                synthetic,
            )

    results.append(step_tiny_forward(selected, synthetic=synthetic))
    if results[-1].status == "failed":
        return _make_report(
            results, selected, git_sha, git_dirty, config_sha, frozen, run_id, synthetic
        )
    results.append(
        step_tiny_overfit(
            selected,
            max_steps=max_steps,
            overfit_threshold=overfit_threshold,
            synthetic=synthetic,
        )
    )
    if results[-1].status == "failed":
        return _make_report(
            results, selected, git_sha, git_dirty, config_sha, frozen, run_id, synthetic
        )
    results.append(step_gpu_memory(synthetic=synthetic))
    if results[-1].status == "failed":
        return _make_report(
            results, selected, git_sha, git_dirty, config_sha, frozen, run_id, synthetic
        )
    results.append(step_checkpoint_equivalence(selected, synthetic=synthetic))
    if results[-1].status == "failed":
        return _make_report(
            results, selected, git_sha, git_dirty, config_sha, frozen, run_id, synthetic
        )
    result = step_deterministic_logging(
        inputs,
        authorization_run_id=run_id,
        synthetic=synthetic,
        device=selected,
    )
    results.append(result)
    return _make_report(
        results, selected, git_sha, git_dirty, config_sha, frozen, run_id, synthetic
    )


def _make_report(
    results: list[StepResult],
    device: torch.device,
    git_sha: str,
    git_dirty: bool,
    config_sha: str,
    frozen: dict[str, str],
    run_id: str,
    synthetic: bool,
) -> HarnessReport:
    completed_names = {result.name for result in results}
    failed_name = next(
        (result.name for result in results if result.status == "failed"), None
    )
    if failed_name is not None:
        stopped = False
        padded: list[StepResult] = []
        for name in STEP_NAMES:
            if name == failed_name:
                stopped = True
            if name in completed_names:
                padded.append(next(result for result in results if result.name == name))
            elif stopped:
                padded.append(
                    StepResult(
                        name,
                        "not_run",
                        f"not run after {failed_name} failed",
                        0.0,
                    )
                )
        results = padded
    authorized = (
        not synthetic
        and len(results) == len(STEP_NAMES)
        and all(result.status == "passed" for result in results)
    )
    if synthetic and results:
        last = results[-1]
        results[-1] = replace(
            last,
            detail=last.detail + "; synthetic mode always forces authorized=false",
        )
    return HarnessReport(
        results=tuple(results),
        authorized=authorized,
        device=str(device),
        git_sha=git_sha,
        git_dirty=git_dirty,
        config_sha256=config_sha,
        frozen_hashes=frozen,
        timestamp_utc=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        harness_version=HARNESS_VERSION,
        authorization_run_id=run_id,
        synthetic=synthetic,
    )


def write_harness_report(report: HarnessReport, report_path: Path) -> Path:
    """Atomically create one report, refusing to overwrite any existing file."""
    payload = json.dumps(asdict(report), indent=2, sort_keys=True) + "\n"
    return _atomic_json_once(report_path, payload, prefix=".authorization-")


def assert_authorized(
    report_path: str | Path, *, git_sha: str, config_sha256: str
) -> None:
    """Reject missing, synthetic, stale, CPU-only, or incomplete authorization."""
    try:
        report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("could not read authorization report") from exc
    if not isinstance(report, dict) or report.get("authorized") is not True:
        raise ValueError("training authorization report is not authorized")
    if report.get("synthetic") is True:
        raise ValueError("synthetic authorization reports cannot authorize training")
    results = report.get("results")
    if (
        not isinstance(results, list)
        or tuple(item.get("name") for item in results if isinstance(item, dict))
        != STEP_NAMES
        or any(
            not isinstance(item, dict) or item.get("status") != "passed"
            for item in results
        )
    ):
        raise ValueError("authorization report does not contain seven passed steps")
    if not str(report.get("device", "")).startswith("cuda"):
        raise ValueError("authorization report was not produced on CUDA")
    if report.get("git_sha") != git_sha:
        raise ValueError("authorization report git SHA does not match current commit")
    if report.get("config_sha256") != config_sha256:
        raise ValueError(
            "authorization report config hash does not match resolved config"
        )
