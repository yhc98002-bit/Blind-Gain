import json

import torch
import transformers
import qwen_vl_utils  # noqa: F401
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration  # noqa: F401

from src.eval.fliptrack_metrics import pair_score  # noqa: F401
from src.eval.image_conditions import materialize_image  # noqa: F401
from src.eval.prompt_contract import DEFAULT_PROMPT_CONTRACT

print(
    json.dumps(
        {
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "cuda_device_count_visible": torch.cuda.device_count(),
            "prompt_contract_sha256": DEFAULT_PROMPT_CONTRACT.sha256,
            "imports_ok": True,
        },
        sort_keys=True,
    )
)
