import pathlib, re
p = pathlib.Path("/XYFS02/HDD_POOL/paratera_xy/pxy1289/HaocunYe/Research/BlindGain/src/eval/layer1_blind.py")
s = p.read_text(encoding="utf-8")
orig = s

# 1. imports
s = s.replace("import math\nimport string\n", "import math\nimport re\nimport string\n", 1)
s = s.replace(
    "from scripts.postprocess_vlmeval_predictions import _choice_payload, score_mcq_prediction, score_open_prediction",
    "from scripts.postprocess_vlmeval_predictions import (\n"
    "    _choice_payload,\n"
    "    _not_missing,\n"
    "    score_mcq_prediction,\n"
    "    score_open_prediction,\n"
    ")",
    1,
)

# 2. dispatch table + mmmu builder
old_dispatch = '''def build_text_prompt(row: dict[str, Any], dataset_type: str) -> str:
    if dataset_type == "mmstar":
        return mmstar_text_prompt(row)
    if dataset_type == "mathvista":
        return mathvista_text_prompt(row)
    raise ValueError(f"unsupported blind Layer-1 dataset type: {dataset_type}")'''
new_dispatch = '''# Each blind builder mirrors the VLMEvalKit class that produced the paired
# with-image column, so the blind prompt is that prompt minus the image
# messages and nothing else:
#   ImageMCQDataset.build_prompt  -> "Question:" + "Options:" block + select
#     instruction. Used by MMStar_VLMEVAL, BLINK_LOCAL, MMVP_LOCAL_V2.
#   ImageBaseDataset.build_prompt -> question text verbatim. Used by
#     ImageYORNDataset (HallusionBench_LOCAL_V2) and MathVerse (MathVerse_LOCAL),
#     both of which carry any options inside the question text itself.
#   MMMUDataset.build_prompt      -> ImageMCQDataset.build_prompt followed by
#     split_MMMU, which *consumes* the "<image N>" markers as it interleaves the
#     real images. The blind mirror therefore deletes those markers. Note this
#     differs from MMStar/BLINK/MMVP on purpose: plain ImageMCQDataset leaves a
#     literal "<image N>" in its text, so those builders keep it verbatim.
_MCQ_OPTION_BLOCK_TYPES = frozenset({"mmstar", "blink", "mmvp"})
_QUESTION_VERBATIM_TYPES = frozenset({"mathvista", "hallusionbench", "mathverse"})
_MMMU_IMAGE_MARKER = re.compile(r"<image\\s+\\d+>")


def mmmu_text_prompt(row: dict[str, Any]) -> str:
    return _MMMU_IMAGE_MARKER.sub("", mmstar_text_prompt(row))


def build_text_prompt(row: dict[str, Any], dataset_type: str) -> str:
    if dataset_type in _MCQ_OPTION_BLOCK_TYPES:
        return mmstar_text_prompt(row)
    if dataset_type in _QUESTION_VERBATIM_TYPES:
        return mathvista_text_prompt(row)
    if dataset_type == "mmmu":
        return mmmu_text_prompt(row)
    raise ValueError(f"unsupported blind Layer-1 dataset type: {dataset_type}")'''
assert old_dispatch in s
s = s.replace(old_dispatch, new_dispatch, 1)

# 3. category selection mirrors the with-image postprocessor (category, then task)
old_cat = '''            category = str(row.get("task", "unknown"))'''
new_cat = '''            category = row.get("category")
            if not _not_missing(category):
                category = row.get("task", "unknown")
            category = str(category)'''
assert old_cat in s
s = s.replace(old_cat, new_cat, 1)

assert s != orig
p.write_text(s, encoding="utf-8")
print("patched layer1_blind.py")
