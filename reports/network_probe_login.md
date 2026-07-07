# Network Probe

- Timestamp: 2026-07-07T13:22:16-07:00
- Host: ln207
- PROXY_URL: `http://127.0.0.1:7890`
- DOMESTIC_PROXY: `none`

| Route | URL | curl rc | HTTP | seconds | bytes | bytes/s |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| ModelScope direct | `https://www.modelscope.cn/api/v1/models` | 1 | 404 | 0.398794 | 18 | 45 |
| GitHub proxy | `https://github.com/` | 1 | 200 | 1.777712 | 576399 | 324236 |
| HuggingFace proxy | `https://huggingface.co/` | 1 | 200 | 1.347252 | 173236 | 128584 |
| PyPI mirror direct | `https://pypi.tuna.tsinghua.edu.cn/simple` | 1 | 200 | 1.938302 | 43028540 | 22199089 |
| ModelScope small file | `https://modelscope.cn/api/v1/datasets/modelscope/hellaswag/repo/files?Revision=master&Recursive=false` | 1 | 405 | 0.293087 | 160 | 545 |
| HF small file proxy | `https://huggingface.co/bert-base-uncased/raw/main/config.json` | 1 | 200 | 1.169311 | 570 | 487 |
