# Network Probe

Status:
- Login node `ln207` can access domestic and international routes.
- Compute nodes cannot resolve external hostnames directly.
- `127.0.0.1:7890` is active on the login node only.
- `127.0.0.1:3138` is not listening on login or compute nodes during this probe.

Evidence:
- Login probe: `reports/network_probe_login.md`
- `an12` direct DNS failed for `pypi.tuna.tsinghua.edu.cn` and `www.modelscope.cn`.
- `an12` localhost `3138` and `7890` were connection refused before reverse forwarding.
- Foreground SSH reverse forward `-R 7891:127.0.0.1:7890` was verified once on `an12`, but detached reverse tunnels exited, so they are not reliable for long package installs.

Problems:
- Compute-node external download commands should not be assumed reliable.
- Domestic `3138` service location is not discoverable from the current environment.

Decision:
- Run downloads and package installation on `ln207` into the shared project path.
- Use explicit proxy variables only for international routes or fallback downloads:
  `http_proxy=http://127.0.0.1:7890 https_proxy=http://127.0.0.1:7890`.
- Do not set global proxy variables in shell profiles.

Next actions:
- Keep using `scripts/net_probe.sh` before any new bulk route.
- Ask PI/admin for canonical `3138` endpoint if domestic ModelScope downloads become slow or blocked.

