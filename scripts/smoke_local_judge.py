#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import time
from pathlib import Path

import requests


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir")
    parser.add_argument("--timeout-seconds", type=float, default=600.0)
    args = parser.parse_args()
    run_dir = Path(args.run_dir)
    manifest_path = run_dir / "run_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    endpoint = manifest["endpoint"].rstrip("/")
    deadline = time.monotonic() + args.timeout_seconds
    last_error = "server did not become ready"
    while time.monotonic() < deadline:
        try:
            response = requests.get(f"{endpoint}/models", timeout=10)
            response.raise_for_status()
            break
        except requests.RequestException as error:
            last_error = str(error)
            time.sleep(5)
    else:
        raise SystemExit(last_error)

    payload = {
        "model": manifest["served_model_name"],
        "messages": [
            {
                "role": "user",
                "content": "What is 2 + 2? Reply only with <answer>4</answer>.",
            }
        ],
        "temperature": 0.0,
        "top_p": 1.0,
        "max_tokens": 32,
    }
    response = requests.post(f"{endpoint}/chat/completions", json=payload, timeout=120)
    response.raise_for_status()
    result = response.json()
    content = result["choices"][0]["message"]["content"].strip()
    if "<answer>4</answer>" not in content:
        raise SystemExit(f"unexpected judge smoke response: {content!r}")
    artifact = run_dir / "smoke_response.json"
    artifact.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest.update(
        {
            "ready_time_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "serving",
            "smoke_response": str(artifact),
            "smoke_response_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
            "decoding_smoke": {"temperature": 0.0, "top_p": 1.0, "max_tokens": 32},
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(content)


if __name__ == "__main__":
    main()
