# ModelScope 72B Route Probe

Status:
- Qwen2.5-VL-72B-Instruct is public and available from ModelScope.
- The direct ModelScope route failed during this probe; the approved international-proxy fallback succeeds from both login and `an29` through an SSH reverse tunnel.
- No model weights were downloaded by this probe.

Evidence:
- Model ID: `Qwen/Qwen2.5-VL-72B-Instruct`.
- Source: `https://modelscope.cn/models/Qwen/Qwen2.5-VL-72B-Instruct`.
- ModelScope inventory: 51 files totaling 146,833,336,607 bytes.
- Direct-route failure: ModelScope API connection failed with `Device or resource busy` on 2026-07-11.
- Proxy fallback: `127.0.0.1:7890` returned public model metadata successfully.
- Compute-node route: one foreground `ssh -R 17890:127.0.0.1:7890 an29 ... ms info ...` probe succeeded, proving the tunnel remains available for the lifetime of the download SSH process.
- License was downloaded separately as a 6.96 kB probe artifact to `/tmp/blindgain_qwen25vl72b_license_probe/LICENSE`.
- License: Qwen License Agreement, release date 2024-09-19. Research use is allowed; redistribution is allowed with the agreement, modification notices, and required Qwen attribution. The greater-than-100-million-MAU commercial restriction is not relevant to this research run.
- First mass-download launch attempt: `experiments/runs/modelscope_ephemeral_qwen25vl72b_l9_an29_20260711T160104Z`. The login wrapper exited before a remote worker or local checkout appeared; the attempt is preserved `fail` with exit 70.
- Second launch attempt: `experiments/runs/modelscope_ephemeral_qwen25vl72b_l9_retry_an29_20260711T160334Z`. It reproduced the pre-worker exit with empty bootstrap and SSH logs. A foreground harmless-manifest fixture then proved the wrapper and reverse tunnel themselves work. The defect was process-session detachment: unlike established long-running login jobs, the wrapper had not started a new session. The launcher now uses `nohup setsid` and retains bootstrap stderr.
- Active download: `experiments/runs/modelscope_ephemeral_qwen25vl72b_l9_session_an29_20260711T160604Z`, git `4e10a90`, CPU/network only on `an29`. The supervisor has its own session, the remote guard passed, and ModelScope began transferring the 38 BF16 weight shards into `/dev/shm`.

Problems:
- Compute nodes cannot resolve external hosts directly.
- The 146.8 GB checkout cannot transit shared storage without violating project policy and consuming scarce quota.

Decision:
- Download directly into `/dev/shm/blind-gains/models/Qwen2.5-VL-72B-Instruct` on the eventual serving node.
- Use `scripts/launch_modelscope_ephemeral_download.sh`, which keeps the reverse tunnel and remote download in one supervised process, records a run manifest, invokes the Tier-T guard with memory-filesystem authorization, and writes a persistent checkout hash manifest.
- Use TP4 for serving; this 72B model is not eligible for the <=7B independent-TP1 launcher.
- Delete the ephemeral checkout after both R19 and R20 caption stores are committed and record the deletion in `reports/strong_caption_stress.md`.

Next actions:
- Commit and test the dedicated downloader and TP4 caption runner.
- Launch the download only on a node with at least 146,833,336,607 bytes plus the 40 GiB guard floor available in `/dev/shm`.
