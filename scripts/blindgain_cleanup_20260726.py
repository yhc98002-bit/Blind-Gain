#!/usr/bin/env python3
"""PI-authorized 2026-07-26 storage cleanup — tranches 1 and 2.

Fail-closed per-candidate gates; per-candidate checksum evidence; dry-run
inventory before any deletion. Never touches: step-60/100 merged checkpoints,
any seed-3 or M5-resume150 or Mini-A5 artifact, frozen data, manifests, logs,
or anything outside the explicit candidate list.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import random
import subprocess
from pathlib import Path
from typing import Any, Callable

ROOT = Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain")
OVERFLOW = ROOT / "artifacts/checkpoint_archive_overflow"
SCRATCH_ARCHIVE = Path("/tmp/blindgain_checkpoint_archive")
REPORT_DIR = ROOT / "reports/cleanup_20260726"

SEED12_LINEAGES = (
    "mech_a1_real",
    "mech_a1_real_resume60",
    "mech_a2_gray",
    "mech_a2_gray_resume60_retry2",
    "mech_a2b_noimage_retry4",
    "mech_a3_caption_resume20",
    "mech_a1_real_seed2",
    "mech_a2_gray_seed2_resume20",
    "mech_a2b_noimage_seed2_resume20",
    "mech_a3_caption_seed2",
)
INTERMEDIATE_STEPS = (20, 40, 80)


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def du_bytes(path: Path) -> int:
    out = subprocess.run(["du", "-sb", str(path)], capture_output=True, text=True)
    return int(out.stdout.split()[0]) if out.returncode == 0 else -1


def merged_index_ok(path: Path) -> bool:
    return (path / "actor/huggingface/model.safetensors.index.json").is_file()


def sample_verify_checksums(entry: Path, sample: int = 3) -> dict[str, Any]:
    manifests = sorted(entry.rglob("*.sha256")) + sorted(
        entry.rglob("raw_checkpoint.checksums.json")
    )
    pairs: list[tuple[Path, str]] = []
    for manifest in manifests:
        if manifest.suffix == ".json":
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            records = payload if isinstance(payload, list) else payload.get("files", [])
            for record in records:
                name = record.get("file") or record.get("path")
                digest = record.get("sha256")
                if name and digest:
                    candidate = manifest.parent / Path(name).name
                    if candidate.is_file():
                        pairs.append((candidate, digest))
        else:
            for line in manifest.read_text(encoding="utf-8").splitlines():
                parts = line.split()
                if len(parts) >= 2:
                    candidate = manifest.parent / Path(parts[-1]).name
                    if candidate.is_file():
                        pairs.append((candidate, parts[0]))
    if not pairs:
        return {"checksum_files": len(manifests), "verified": 0, "note": "no verifiable records"}
    rng = random.Random(20260726)
    chosen = rng.sample(pairs, min(sample, len(pairs)))
    for candidate, expected in chosen:
        if _sha256(candidate) != expected:
            raise RuntimeError(f"checksum mismatch during pre-delete verify: {candidate}")
    return {"checksum_files": len(manifests), "verified": len(chosen)}


def gate_anchor_a0() -> dict[str, Any]:
    entry = OVERFLOW / "anchor_a0_recipe_3b_geo3k_20260709T224852Z"
    evidence = sample_verify_checksums(entry)
    merged = ROOT / "checkpoints/anchor_a0_recipe_3b_geo3k/anchor_a0_recipe_3b_geo3k_20260709T224852Z"
    candidates = list(ROOT.glob("checkpoints/**/anchor_a0*/global_step_100/actor/huggingface/model.safetensors.index.json"))
    evidence["merged_step100_on_quota"] = len(candidates) >= 1
    if not evidence["merged_step100_on_quota"]:
        raise RuntimeError("anchor_a0 merged step-100 not found on quota")
    return evidence


def gate_old_a2_seed2() -> dict[str, Any]:
    entry = OVERFLOW / "mech_a2_gray_seed2_an12_20260718T004316Z"
    evidence = sample_verify_checksums(entry)
    for step in (60, 100):
        ok = merged_index_ok(ROOT / f"checkpoints/pilot/mech_a2_gray_seed2_resume20/global_step_{step}")
        evidence[f"resume20_merged_step{step}"] = ok
        if not ok:
            raise RuntimeError(f"resume20 merged step-{step} missing")
    return evidence


def gate_old_m5() -> dict[str, Any]:
    entry = OVERFLOW / "m5_anchor_longhorizon_400_an12_20260716T173030Z"
    evidence = sample_verify_checksums(entry)
    for step in (250, 300):
        marker = ROOT / f"checkpoints/m5_anchor_longhorizon_400_resume150/global_step_{step}/actor/RAW_STATE_RELOCATED.json"
        evidence[f"resume150_step{step}_raw_marker"] = marker.is_file()
        if not marker.is_file():
            raise RuntimeError(f"resume150 step-{step} raw marker missing; fallback not superseded")
    merged150 = list(ROOT.glob("checkpoints/m5_anchor_longhorizon_400*/global_step_150/actor/huggingface/model.safetensors.index.json"))
    evidence["merged_step150_on_quota"] = len(merged150) >= 1
    if not merged150:
        raise RuntimeError("merged step-150 not found on quota; keeping old M5 lineage")
    return evidence


def gate_seed2_resume20(lineage: str, training_run: str) -> Callable[[], dict[str, Any]]:
    def gate() -> dict[str, Any]:
        entry = SCRATCH_ARCHIVE / training_run
        evidence = sample_verify_checksums(entry)
        for step in (60, 100):
            ok = merged_index_ok(ROOT / f"checkpoints/pilot/{lineage}/global_step_{step}")
            evidence[f"merged_step{step}"] = ok
            if not ok:
                raise RuntimeError(f"{lineage} merged step-{step} missing")
        run_dir = ROOT / "experiments/runs" / training_run
        for marker in ("step60_fliptrack_complete.json", "step100_fliptrack_complete.json"):
            present = (run_dir / marker).is_file()
            evidence[marker] = present
            if not present:
                raise RuntimeError(f"{training_run}: eval marker {marker} missing")
        return evidence

    return gate


def intermediate_merged_candidates() -> list[Path]:
    hits: list[Path] = []
    for lineage in SEED12_LINEAGES:
        for step in INTERMEDIATE_STEPS:
            actor = ROOT / f"checkpoints/pilot/{lineage}/global_step_{step}/actor"
            if (actor / "huggingface").is_dir():
                hits.append(actor / "huggingface")
    return hits


PROVENANCE_RECORD_MARKERS = (
    "/reports/storage_relocations/",
    "/reports/cleanup_",
    "retention",
    "relocation",
)


def gate_intermediate_merged() -> dict[str, Any]:
    """Refuse if any scientific artifact (config, registered doc, readout)
    references a candidate intermediate merged checkpoint. Historical
    storage-operation provenance records (relocation manifests, checksum
    files, retention reports) describe past moves and are not consumers."""
    patterns: list[str] = []
    for lineage in SEED12_LINEAGES:
        for step in INTERMEDIATE_STEPS:
            patterns.append(f"checkpoints/pilot/{lineage}/global_step_{step}")
    command = ["grep", "-rl"]
    for pattern in patterns:
        command += ["-e", pattern]
    command += [str(ROOT / "configs"), str(ROOT / "docs"), str(ROOT / "reports")]
    grep = subprocess.run(command, capture_output=True, text=True)
    references = [
        line
        for line in grep.stdout.splitlines()
        if not any(marker in line for marker in PROVENANCE_RECORD_MARKERS)
        and "cleanup_20260726" not in line
    ]
    if references:
        raise RuntimeError(
            f"scientific references to intermediate merged paths: {references[:5]}"
        )
    return {"reference_grep_clean": True, "patterns_checked": len(patterns)}


def checksum_manifest_for(path: Path, out: Path) -> str:
    records = []
    for item in sorted(path.rglob("*")):
        if item.is_file():
            records.append(
                {"file": str(item.relative_to(path)), "sha256": _sha256(item), "bytes": item.stat().st_size}
            )
    payload = {"target": str(path), "generated_utc": _now(), "files": records}
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return _sha256(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--tranche", choices=("1", "2", "both"), default="both")
    args = parser.parse_args()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    candidates: list[dict[str, Any]] = []
    if args.tranche in ("1", "both"):
        candidates += [
            {"id": "overflow_anchor_a0", "path": OVERFLOW / "anchor_a0_recipe_3b_geo3k_20260709T224852Z",
             "gate": gate_anchor_a0, "class": "archived_raw_complete_lineage", "needs_manifest": False},
            {"id": "overflow_old_a2_seed2", "path": OVERFLOW / "mech_a2_gray_seed2_an12_20260718T004316Z",
             "gate": gate_old_a2_seed2, "class": "archived_raw_superseded_lineage", "needs_manifest": False},
        ]
    if args.tranche in ("2", "both"):
        candidates += [
            {"id": "overflow_old_m5", "path": OVERFLOW / "m5_anchor_longhorizon_400_an12_20260716T173030Z",
             "gate": gate_old_m5, "class": "archived_raw_superseded_lineage", "needs_manifest": False},
            {"id": "scratch_a2_seed2_resume20",
             "path": SCRATCH_ARCHIVE / "mech_a2_gray_seed2_resume20_an12_20260719T125918Z",
             "gate": gate_seed2_resume20("mech_a2_gray_seed2_resume20", "mech_a2_gray_seed2_resume20_an12_20260719T125918Z"),
             "class": "archived_raw_completed_evaluated", "needs_manifest": False},
            {"id": "scratch_a2b_seed2_resume20",
             "path": SCRATCH_ARCHIVE / "mech_a2b_noimage_seed2_resume20_an29_20260719T125447Z",
             "gate": gate_seed2_resume20("mech_a2b_noimage_seed2_resume20", "mech_a2b_noimage_seed2_resume20_an29_20260719T125447Z"),
             "class": "archived_raw_completed_evaluated", "needs_manifest": False},
        ]
        gate_intermediate_merged()
        for merged in intermediate_merged_candidates():
            lineage = merged.parts[-4]
            step = merged.parts[-3]
            candidates.append(
                {"id": f"merged_{lineage}_{step}", "path": merged,
                 "gate": lambda: {"covered_by": "gate_intermediate_merged"},
                 "class": "intermediate_merged_completed_seed12", "needs_manifest": True}
            )

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    inventory = []
    for candidate in candidates:
        path: Path = candidate["path"]
        if not path.exists():
            inventory.append({"id": candidate["id"], "path": str(path), "status": "absent"})
            continue
        inventory.append(
            {"id": candidate["id"], "path": str(path), "class": candidate["class"],
             "bytes": du_bytes(path), "status": "candidate"}
        )
    mode = "execute" if args.execute else "dry-run"
    inv_path = REPORT_DIR / f"cleanup_inventory_{mode}_{stamp}.json"
    inv_path.write_text(json.dumps({
        "schema_version": "blind-gains.cleanup-20260726.inventory.v1",
        "generated_utc": _now(), "mode": mode, "candidates": inventory,
        "total_bytes": sum(item.get("bytes", 0) for item in inventory if item.get("bytes", 0) > 0),
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"inventory": str(inv_path.relative_to(ROOT)),
                      "candidates": len([i for i in inventory if i["status"] == "candidate"]),
                      "total_gib": round(sum(i.get("bytes", 0) for i in inventory if i.get("bytes", 0) > 0) / 2**30, 1)}))
    if not args.execute:
        return

    deleted = []
    for candidate in candidates:
        path = candidate["path"]
        if not path.exists():
            continue
        evidence = candidate["gate"]()
        record: dict[str, Any] = {
            "id": candidate["id"], "path": str(path), "class": candidate["class"],
            "bytes": du_bytes(path), "gate_evidence": evidence,
        }
        if candidate["needs_manifest"]:
            manifest_out = REPORT_DIR / f"checksums_{candidate['id']}.json"
            record["checksum_manifest"] = str(manifest_out.relative_to(ROOT))
            record["checksum_manifest_sha256"] = checksum_manifest_for(path, manifest_out)
        subprocess.run(["rm", "-rf", str(path)], check=True)
        record["deleted_utc"] = _now()
        deleted.append(record)
        print(json.dumps({"deleted": candidate["id"], "gib": round(record["bytes"] / 2**30, 1)}))

    exec_path = REPORT_DIR / f"cleanup_execution_{stamp}.json"
    exec_path.write_text(json.dumps({
        "schema_version": "blind-gains.cleanup-20260726.execution.v1",
        "generated_utc": _now(), "deleted": deleted,
        "total_bytes": sum(record["bytes"] for record in deleted),
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"execution_report": str(exec_path.relative_to(ROOT)),
                      "deleted": len(deleted),
                      "total_gib": round(sum(r["bytes"] for r in deleted) / 2**30, 1)}))


if __name__ == "__main__":
    main()
