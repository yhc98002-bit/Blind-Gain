#!/usr/bin/env python3
"""
blindgain_cleanup_20260727.py — scoped, manifest-first cleanup.

Written for the 2026-07-27 cross-path storage cleanup. Design goal: make a
scope escape structurally impossible. The 2026-07-26 incident deleted an entire
archive tree far beyond its six authorized paths; this tool cannot do that.

Every target must pass ALL of:
  1. absolute, normalized, and strictly deeper than an allowlisted root
  2. not equal to, inside, or an ANCESTOR of any protected (deny) path
  3. owned by the invoking uid (lstat, symlinks not followed)
  4. not held open by any live process (/proc fd + maps + cwd + exe scan)
  5. realpath still satisfies (1) and (2) after symlink resolution

Dry-run is the default. --execute is required to remove anything.

Usage:
  python3 blindgain_cleanup_20260727.py --targets t.json --manifest m.json
  python3 blindgain_cleanup_20260727.py --targets t.json --manifest m.json --execute
"""

import argparse
import hashlib
import json
import os
import socket
import stat
import sys
import time

ALLOWED_ROOTS = [
    "/tmp",
    "/var/tmp",
    "/dev/shm",
    "/HOME/paratera_xy/pxy1289",
    "/XYFS02/HDD_POOL/paratera_xy/pxy1289",
    # ln206 exposes /HOME as a symlink into /XYFS01/HOME, ln207 as a direct
    # mount. Same bytes, two spellings; realpath() yields this form on ln206.
    "/XYFS01/HOME/paratera_xy/pxy1289",
]

BG = "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain"

# Never delete these, and never delete anything that CONTAINS them.
DENY = [
    # live job / heartbeats
    "/tmp/tmux-22847",
    "/dev/shm/blind-gains",
    # an12: live Ray session for m5_anchor_longhorizon segment 300->350, and the
    # two PSM3 segments created 7 min after it (probable live libfabric transport)
    "/dev/shm/bg-ray-868dafa61268",
    "/dev/shm/psm_1f3190a1",
    "/dev/shm/psm_8ccaca16",
    # an29: today's launcher attempts; a retry loop was firing every ~20 min
    "/dev/shm/bg-ray-4e8ce3f9d111",
    "/dev/shm/bg-ray-3f22b6806569",
    # /HOME protected
    "/HOME/paratera_xy/pxy1289/.triton",
    "/HOME/paratera_xy/pxy1289/.codex",
    "/HOME/paratera_xy/pxy1289/.conda",
    "/HOME/paratera_xy/pxy1289/cuda",
    "/HOME/paratera_xy/pxy1289/.local",
    "/HOME/paratera_xy/pxy1289/.cache/modelscope",
    "/HOME/paratera_xy/pxy1289/.cache/huggingface",
    "/HOME/paratera_xy/pxy1289/.cache/clap",
    "/HOME/paratera_xy/pxy1289/.cache/vllm",
    # other people / sibling projects on shared Lustre (ruling 1)
    "/XYFS02/HDD_POOL/paratera_xy/pxy1289/zhaotong",
    "/XYFS02/HDD_POOL/paratera_xy/pxy1289/blindgain_archive",
    "/XYFS02/HDD_POOL/paratera_xy/pxy1289/.uv_cache",
    "/XYFS02/HDD_POOL/paratera_xy/pxy1289/source",
    "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/AudioDiffusion",
    "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/AudioDiffusion_envs",
    "/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/benchmark_v2_runtime",
    "/HOME/paratera_xy/pxy1289/sa3_foundation_runtime/repository",
    "/HOME/paratera_xy/pxy1289/sa3_foundation_runtime/env",
    "/HOME/paratera_xy/pxy1289/sa3_foundation_runtime/models",
    # BlindGain record surface + all experimental assets (ruling 2)
    BG + "/checkpoints",
    BG + "/reports",
    BG + "/configs",
    BG + "/docs",
    BG + "/experiments",
    BG + "/scripts",
    BG + "/src",
    BG + "/tests",
    BG + "/.git",
    BG + "/logs",
    BG + "/artifacts/models",
    BG + "/artifacts/repos",
    BG + "/artifacts/envs",
    BG + "/.venv",
    BG + "/.venv-m11",
    BG + "/.venv-ocr",
    BG + "/data/virl39k",
    BG + "/data/mini_a5_train_v1",
    BG + "/data/geometry3k_caption_images",
]

# Mirror every /HOME protection under the /XYFS01/HOME spelling, so a protected
# path stays protected after symlink resolution on ln206.
DENY += [d.replace("/HOME/", "/XYFS01/HOME/", 1) for d in DENY if d.startswith("/HOME/")]


def norm(p):
    return os.path.normpath(p)


def is_under(child, parent):
    """True if child == parent or child is inside parent."""
    child, parent = norm(child), norm(parent)
    return child == parent or child.startswith(parent.rstrip("/") + "/")


def live_open_paths():
    """Absolute paths currently held open by any readable process.

    Scans fd symlinks, memory maps, cwd and exe. Deliberately best-effort:
    unreadable pids are skipped, but our own processes are always readable,
    and we only ever delete our own files.
    """
    seen = set()
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        base = "/proc/" + pid
        for link in ("cwd", "exe"):
            try:
                seen.add(os.readlink(base + "/" + link))
            except OSError:
                pass
        try:
            for fd in os.listdir(base + "/fd"):
                try:
                    seen.add(os.readlink(base + "/fd/" + fd))
                except OSError:
                    pass
        except OSError:
            pass
        try:
            with open(base + "/maps") as fh:
                for line in fh:
                    parts = line.rstrip("\n").split(" ", 5)
                    if len(parts) == 6:
                        path = parts[5].strip()
                        if path.startswith("/"):
                            seen.add(path)
        except OSError:
            pass
    # Strip kernel's " (deleted)" suffix so unlinked-but-mapped files still match.
    out = set()
    for p in seen:
        out.add(p[: -len(" (deleted)")] if p.endswith(" (deleted)") else p)
    return out


def tree_stats(path):
    """(apparent_bytes, file_count) without following symlinks out of the tree."""
    st = os.lstat(path)
    if not stat.S_ISDIR(st.st_mode):
        return st.st_size, 1
    total, count = 0, 0
    for root, dirs, files in os.walk(path, followlinks=False):
        for name in files + dirs:
            try:
                s = os.lstat(os.path.join(root, name))
            except OSError:
                continue
            if not stat.S_ISDIR(s.st_mode):
                total += s.st_size
                count += 1
    return total, count


def sha256_of(path, limit=512 * 1024 * 1024):
    st = os.lstat(path)
    if not stat.S_ISREG(st.st_mode) or st.st_size > limit:
        return None
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(4 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def vet(target, uid, open_paths):
    """Return (ok, reason). Reason is the rejection cause when not ok."""
    if not target.startswith("/"):
        return False, "not an absolute path"
    t = norm(target)
    root = next((r for r in ALLOWED_ROOTS if is_under(t, r)), None)
    if root is None:
        return False, "outside every allowlisted root"
    if norm(t) == norm(root):
        return False, "is an allowlisted root itself"
    # require at least one component below the root
    rel = os.path.relpath(t, root)
    if rel in (".", "..") or rel.startswith(".." + os.sep):
        return False, "escapes its root"

    for d in DENY:
        if is_under(t, d):
            return False, "inside protected path %s" % d
        if is_under(d, t):
            return False, "would contain protected path %s" % d

    try:
        st = os.lstat(t)
    except FileNotFoundError:
        return False, "does not exist"
    except OSError as exc:
        return False, "lstat failed: %s" % exc

    if st.st_uid != uid:
        return False, "owned by uid %d, not %d" % (st.st_uid, uid)

    # symlink resolution must not escape the vetted region
    real = os.path.realpath(t)
    if real != t:
        if not any(is_under(real, r) for r in ALLOWED_ROOTS):
            return False, "symlink resolves outside allowlist: %s" % real
        for d in DENY:
            if is_under(real, d):
                return False, "symlink resolves into protected path %s" % d

    # live-handle check: the target itself, or anything inside it
    for op in open_paths:
        if is_under(op, t):
            return False, "held open by a live process: %s" % op

    return True, None


def remove(path):
    st = os.lstat(path)
    if stat.S_ISDIR(st.st_mode) and not stat.S_ISLNK(st.st_mode):
        # manual walk so a failure on one entry does not abort the rest
        errors = []
        for root, dirs, files in os.walk(path, topdown=False, followlinks=False):
            for name in files:
                try:
                    os.unlink(os.path.join(root, name))
                except OSError as exc:
                    errors.append(str(exc))
            for name in dirs:
                p = os.path.join(root, name)
                try:
                    if os.path.islink(p):
                        os.unlink(p)
                    else:
                        os.rmdir(p)
                except OSError as exc:
                    errors.append(str(exc))
        try:
            os.rmdir(path)
        except OSError as exc:
            errors.append(str(exc))
        return errors
    os.unlink(path)
    return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--targets", required=True, help="JSON file: list of absolute paths")
    ap.add_argument("--manifest", required=True, help="where to write the manifest JSON")
    ap.add_argument("--execute", action="store_true", help="actually delete (default: dry run)")
    ap.add_argument("--sha256", action="store_true", help="hash regular-file targets <=512MB")
    ap.add_argument("--tier", default="unnamed")
    args = ap.parse_args()

    uid = os.getuid()
    with open(args.targets) as fh:
        targets = json.load(fh)
    if not isinstance(targets, list):
        sys.exit("targets file must contain a JSON list")

    print("scanning live process handles ...", flush=True)
    open_paths = live_open_paths()
    print("  %d open paths seen" % len(open_paths), flush=True)

    accepted, rejected = [], []
    for raw in targets:
        t = norm(raw)
        ok, reason = vet(t, uid, open_paths)
        if not ok:
            rejected.append({"path": t, "reason": reason})
            continue
        size, count = tree_stats(t)
        entry = {
            "path": t,
            "bytes": size,
            "file_count": count,
            "mtime_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(os.lstat(t).st_mtime)),
            "is_dir": stat.S_ISDIR(os.lstat(t).st_mode),
        }
        if args.sha256:
            digest = sha256_of(t)
            if digest:
                entry["sha256"] = digest
        accepted.append(entry)

    total = sum(e["bytes"] for e in accepted)
    manifest = {
        "schema_version": "blind-gains.cleanup-manifest.v1",
        "tier": args.tier,
        "node": socket.gethostname(),
        "uid": uid,
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mode": "execute" if args.execute else "dry_run",
        "accepted_count": len(accepted),
        "accepted_bytes": total,
        "accepted_gib": round(total / 1024**3, 3),
        "rejected_count": len(rejected),
        "accepted": accepted,
        "rejected": rejected,
    }

    print("\n=== %s on %s ===" % (args.tier, manifest["node"]))
    for e in sorted(accepted, key=lambda x: -x["bytes"]):
        print("  DELETE %10.3f GiB  %6d files  %s" % (e["bytes"] / 1024**3, e["file_count"], e["path"]))
    for r in rejected:
        print("  SKIP   %s  <- %s" % (r["path"], r["reason"]))
    print("\n  accepted: %d paths, %.3f GiB" % (len(accepted), total / 1024**3))
    print("  rejected: %d paths" % len(rejected))

    if args.execute:
        print("\nexecuting ...", flush=True)
        # Re-scan live handles now: minutes may have passed since the dry-run
        # scan, and a new job could have opened one of these paths.
        fresh_open = live_open_paths()
        print("  re-scanned: %d open paths" % len(fresh_open), flush=True)
        done, failed = 0, []
        for e in accepted:
            # re-vet immediately before removal; state may have changed
            ok, reason = vet(e["path"], uid, fresh_open)
            if not ok:
                failed.append({"path": e["path"], "error": "re-vet failed: %s" % reason})
                continue
            try:
                errs = remove(e["path"])
                if errs:
                    failed.append({"path": e["path"], "error": "; ".join(errs[:5])})
                else:
                    done += 1
                    e["removed"] = True
            except OSError as exc:
                failed.append({"path": e["path"], "error": str(exc)})
        manifest["removed_count"] = done
        manifest["failures"] = failed
        print("  removed %d/%d paths, %d failures" % (done, len(accepted), len(failed)))
        for f in failed:
            print("  FAIL %s: %s" % (f["path"], f["error"]))

    os.makedirs(os.path.dirname(os.path.abspath(args.manifest)), exist_ok=True)
    with open(args.manifest, "w") as fh:
        json.dump(manifest, fh, indent=2, sort_keys=True)
        fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())
    print("\nmanifest -> %s" % args.manifest)


if __name__ == "__main__":
    main()
