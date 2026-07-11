from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping


ANSWER_FORMAT_CONTRACT = (
    "Give your final answer inside <answer> and </answer> tags. "
    "Keep the tagged span to the shortest answer that resolves the question."
)
PROMPT_CONTRACT_SCHEMA_VERSION = "blind-gains.prompt-contract.v1"


@dataclass(frozen=True)
class PromptContract:
    contract_id: str
    instruction: str
    response_format: str
    schema_version: str = PROMPT_CONTRACT_SCHEMA_VERSION

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @property
    def sha256(self) -> str:
        encoded = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


DEFAULT_PROMPT_CONTRACT = PromptContract(
    contract_id="answer-tags-v1",
    instruction=ANSWER_FORMAT_CONTRACT,
    response_format="single_final_answer_tag",
)

PromptContractLike = PromptContract | Mapping[str, Any] | None


def resolve_prompt_contract(value: PromptContractLike = None) -> PromptContract:
    if value is None:
        return DEFAULT_PROMPT_CONTRACT
    if isinstance(value, PromptContract):
        return value
    required = {"contract_id", "instruction", "response_format", "schema_version"}
    missing = required - set(value)
    extra = set(value) - required
    if missing or extra:
        raise ValueError(f"prompt contract fields mismatch: missing={sorted(missing)}, extra={sorted(extra)}")
    contract = PromptContract(**{key: str(value[key]) for key in required})
    if contract.schema_version != PROMPT_CONTRACT_SCHEMA_VERSION:
        raise ValueError(f"unsupported prompt contract schema: {contract.schema_version}")
    return contract


def prompt_contract_metadata(value: PromptContractLike = None) -> dict[str, str]:
    contract = resolve_prompt_contract(value)
    return {
        "prompt_contract_id": contract.contract_id,
        "prompt_contract_sha256": contract.sha256,
    }


def response_satisfies_contract(response: Any, value: PromptContractLike = None) -> bool:
    contract = resolve_prompt_contract(value)
    text = str(response).strip()
    if contract.response_format != "single_final_answer_tag":
        raise ValueError(f"unsupported response format: {contract.response_format}")
    if len(re.findall(r"<answer\b", text, re.IGNORECASE)) != 1:
        return False
    if len(re.findall(r"</answer\s*>", text, re.IGNORECASE)) != 1:
        return False
    match = re.fullmatch(r"(?s).*<answer>\s*(.*?)\s*</answer>", text, re.IGNORECASE)
    return bool(match and match.group(1).strip())


def load_prompt_contract_from_run_manifest(path: str | Path) -> PromptContract:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    contract = payload.get("prompt_contract")
    if not isinstance(contract, dict):
        raise ValueError(f"run manifest has no prompt_contract mapping: {path}")
    resolved = resolve_prompt_contract(contract)
    recorded_hash = payload.get("prompt_contract_sha256")
    if recorded_hash != resolved.sha256:
        raise ValueError(
            f"run manifest prompt contract hash mismatch: expected {resolved.sha256}, found {recorded_hash}"
        )
    return resolved


def format_question(question: str, contract: PromptContractLike = None) -> str:
    resolved = resolve_prompt_contract(contract)
    return f"{question.strip()}\n\n{resolved.instruction}"
