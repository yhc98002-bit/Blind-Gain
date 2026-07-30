# E1c: blind columns for the five benchmarks that had none

- Schema: `blind-gains.e1c-blind-columns.v1`
- Generated: 2026-07-30T13:29:58Z
- Source of truth: `reports/e1c_blind_columns_v1.json`

Complete the F0 visual-necessity audit by supplying the blind (image-removed) column for the five benchmarks that reports/chance_corrected_retention_v1.json listed as having no image-removed run anywhere.

This takes the F0 visual-necessity audit from 2 benchmarks (MMStar, MathVista) to 7.

## Method

- naive retention = `mean(blind) / mean(with_image)`
- corrected retention = `(mean(blind) - mean(null)) / (mean(with_image) - mean(null))`
- null rule (unchanged from `reports/chance_corrected_retention_v1.json`):
  - multiple_choice: 1/k using that item's own k (count of option labels presented)
  - multiple_choice_gold_label_absent: 0 (gold label is not among presented labels)
  - free_form: 0 (no correction)
- null aggregation: per-item null averaged over the subset; recomputed inside every bootstrap replicate
- bootstrap: 10000 reps, seed 20260729, unit=item, paired=same item ids in both conditions, CI=percentile 2.5 / 97.5
- MathVerse and MMMU are split by answer format; no single global null is applied to a mixed benchmark (I18).
- Where mean(with_image) equals mean(null) the corrected denominator is 0 (guarded at |d| <= 1e-12 against floating point residue); corrected retention and its CI are reported as null with corrected_retention_undefined=true.
- Subsets with n < 30 carry underpowered_subset=true. Their intervals are reported for completeness but are not interpretable; MMMU k=6 (n=6), k=7 (n=2) and k=9 (n=5) are the affected cells.

**Blind integrity.** Every cell ran scripts/eval_layer1_blind.py, which raises if the chat template inserts <|vision_start|> or <|image_pad|> for any row, and src.eval.layer1_blind.load_rows, which raises if a built prompt retains an image token. metrics.json image_removed=true was verified per cell.

## HallusionBench null: which rule was applied

HallusionBench stores no option labels on any of its 1129 rows (k=0 everywhere), and the with-image column scored it with the open_final_span contract. DECISION: it is treated as FREE-FORM with null=0 for the primary row -- no option labels were synthesised and no options were extracted. Because its gold vocabulary is in fact binary ({Yes: 484, No: 645}) while only 170 of 1129 question texts say 'yes or no', a second row applies null=0.5 and is labelled a sensitivity, not the primary. The free-form primary is the conservative choice under the existing null rule ('1/k using that item's own k (count of option labels presented)'): zero labels are presented.

**Prompt mirroring.** The blind prompt is the with-image prompt minus the image messages:
- `blink / mmvp`: VLMEvalKit ImageMCQDataset.build_prompt text: 'Question:' + 'Options:' block + select instruction (identical builder to MMStar).
- `hallusionbench`: VLMEvalKit ImageYORNDataset inherits ImageBaseDataset.build_prompt: question text verbatim.
- `mathverse`: VLMEvalKit MathVerse.build_prompt: question text verbatim (the option list is already inside the question text).
- `mmmu`: VLMEvalKit MMMUDataset.build_prompt = ImageMCQDataset.build_prompt then split_MMMU, which consumes the '<image N>' markers while interleaving images; the blind mirror deletes those markers. This differs from MMStar/BLINK/MMVP on purpose, because plain ImageMCQDataset leaves a literal '<image N>' in its text.

## Format composition of each benchmark

| Benchmark | Model | Format counts |
| --- | --- | --- |
| BLINK | Qwen2.5-VL-3B | `MC|k=2`=924, `MC|k=3`=134, `MC|k=4`=843 |
| BLINK | Qwen2.5-VL-7B | `MC|k=2`=924, `MC|k=3`=134, `MC|k=4`=843 |
| HallusionBench | Qwen2.5-VL-3B | `free_form|k=0`=1129 |
| HallusionBench | Qwen2.5-VL-7B | `free_form|k=0`=1129 |
| MMVP | Qwen2.5-VL-3B | `MC|k=2`=300 |
| MMVP | Qwen2.5-VL-7B | `MC|k=2`=300 |
| MathVerse | Qwen2.5-VL-3B | `MC|k=2`=105, `MC|k=3`=60, `MC|k=4`=1835, `MC|k=5`=150, `MC|k=6`=30, `free_form|k=0`=1760 |
| MathVerse | Qwen2.5-VL-7B | `MC|k=2`=105, `MC|k=3`=60, `MC|k=4`=1835, `MC|k=5`=150, `MC|k=6`=30, `free_form|k=0`=1760 |
| MMMU dev+validation | Qwen2.5-VL-3B | `MC|k=2`=35, `MC|k=3`=133, `MC|k=4`=699, `MC|k=5`=108, `MC|k=6`=6, `MC|k=7`=2, `MC|k=9`=5, `free_form|k=0`=62 |
| MMMU dev+validation | Qwen2.5-VL-7B | `MC|k=2`=35, `MC|k=3`=133, `MC|k=4`=699, `MC|k=5`=108, `MC|k=6`=6, `MC|k=7`=2, `MC|k=9`=5, `free_form|k=0`=62 |

## Whole-benchmark naive retention (null ignored)

| Benchmark | Model | n | with-image acc_final | blind acc_final | naive retention (95% CI) |
| --- | --- | --- | --- | --- | --- |
| BLINK | Qwen2.5-VL-3B | 1901 | 0.4929 | 0.4087 | 0.8292 [0.7815, 0.8794] |
| BLINK | Qwen2.5-VL-7B | 1901 | 0.5565 | 0.3872 | 0.6957 [0.6504, 0.7427] |
| HallusionBench | Qwen2.5-VL-3B | 1129 | 0.5979 | 0.4748 | 0.7941 [0.7478, 0.8429] |
| HallusionBench | Qwen2.5-VL-7B | 1129 | 0.6829 | 0.5686 | 0.8327 [0.7895, 0.8773] |
| MMVP | Qwen2.5-VL-3B | 300 | 0.6600 | 0.5000 | 0.7576 [0.6683, 0.8535] |
| MMVP | Qwen2.5-VL-7B | 300 | 0.7433 | 0.5000 | 0.6726 [0.5931, 0.7560] |
| MathVerse | Qwen2.5-VL-3B | 3940 | 0.2817 | 0.2264 | 0.8036 [0.7655, 0.8423] |
| MathVerse | Qwen2.5-VL-7B | 3940 | 0.3406 | 0.2421 | 0.7109 [0.6774, 0.7455] |
| MMMU dev+validation | Qwen2.5-VL-3B | 1050 | 0.4819 | 0.3914 | 0.8123 [0.7578, 0.8681] |
| MMMU dev+validation | Qwen2.5-VL-7B | 1050 | 0.5133 | 0.4152 | 0.8089 [0.7570, 0.8632] |

## Format-split rows (lenient, `acc_final`)

| Benchmark | Model | Subset | k | n | null | with-image | blind | naive retention (95% CI) | corrected retention (95% CI) | denom<=0 frac |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BLINK | Qwen2.5-VL-3B | MC k=2 | 2 | 924 | 0.5000 | 0.6147 | 0.5043 | 0.8204 [0.7607, 0.8845] | 0.0377 [-0.2680, 0.3204] | 0.000 |
| BLINK | Qwen2.5-VL-3B | MC k=3 | 3 | 134 | 0.3333 | 0.4328 | 0.4254 | 0.9828 [0.9200, 1.0385] | 0.9250 [0.4749, 1.2727] | 0.009 |
| BLINK | Qwen2.5-VL-3B | MC k=4 | 4 | 843 | 0.2500 | 0.3689 | 0.3013 | 0.8167 [0.7270, 0.9138] | 0.4314 [0.1798, 0.7046] | 0.000 |
| BLINK | Qwen2.5-VL-3B | all items (MC pooled, item-level null) | mixed | 1901 | 0.3774 | 0.4929 | 0.4087 | 0.8292 [0.7815, 0.8794] | 0.2713 [0.0889, 0.4541] | 0.000 |
| BLINK | Qwen2.5-VL-7B | MC k=2 | 2 | 924 | 0.5000 | 0.7175 | 0.4968 | 0.6923 [0.6401, 0.7465] | -0.0149 [-0.1684, 0.1337] | 0.000 |
| BLINK | Qwen2.5-VL-7B | MC k=3 | 3 | 134 | 0.3333 | 0.4328 | 0.2687 | 0.6207 [0.3939, 0.9216] | -0.6500 [-2.0000, 0.2500] | 0.008 |
| BLINK | Qwen2.5-VL-7B | MC k=4 | 4 | 843 | 0.2500 | 0.3998 | 0.2859 | 0.7151 [0.6311, 0.8075] | 0.2396 [0.0382, 0.4508] | 0.000 |
| BLINK | Qwen2.5-VL-7B | all items (MC pooled, item-level null) | mixed | 1901 | 0.3774 | 0.5565 | 0.3872 | 0.6957 [0.6504, 0.7427] | 0.0546 [-0.0622, 0.1747] | 0.000 |
| HallusionBench | Qwen2.5-VL-3B | all items (free-form null=0, primary) | 0 | 1129 | 0.0000 | 0.5979 | 0.4748 | 0.7941 [0.7478, 0.8429] | 0.7941 [0.7478, 0.8429] | 0.000 |
| HallusionBench | Qwen2.5-VL-3B | all items (binary Yes/No null=0.5, sensitivity) | 2 | 1129 | 0.5000 | 0.5979 | 0.4748 | 0.7941 [0.7478, 0.8429] | -0.2579 [-0.6727, 0.0390] | 0.000 |
| HallusionBench | Qwen2.5-VL-3B | real-image rows only (free-form null=0) | 0 | 951 | 0.0000 | 0.6151 | 0.4679 | 0.7607 [0.7081, 0.8148] | 0.7607 [0.7081, 0.8148] | 0.000 |
| HallusionBench | Qwen2.5-VL-3B | text-only rows, blank placeholder image (free-form null=0) | 0 | 178 | 0.0000 | 0.5056 | 0.5112 | 1.0111 [0.9419, 1.0886] | 1.0111 [0.9419, 1.0886] | 0.000 |
| HallusionBench | Qwen2.5-VL-7B | all items (free-form null=0, primary) | 0 | 1129 | 0.0000 | 0.6829 | 0.5686 | 0.8327 [0.7895, 0.8773] | 0.8327 [0.7895, 0.8773] | 0.000 |
| HallusionBench | Qwen2.5-VL-7B | all items (binary Yes/No null=0.5, sensitivity) | 2 | 1129 | 0.5000 | 0.6829 | 0.5686 | 0.8327 [0.7895, 0.8773] | 0.3753 [0.2203, 0.5236] | 0.000 |
| HallusionBench | Qwen2.5-VL-7B | real-image rows only (free-form null=0) | 0 | 951 | 0.0000 | 0.6909 | 0.5552 | 0.8037 [0.7549, 0.8543] | 0.8037 [0.7549, 0.8543] | 0.000 |
| HallusionBench | Qwen2.5-VL-7B | text-only rows, blank placeholder image (free-form null=0) | 0 | 178 | 0.0000 | 0.6404 | 0.6404 | 1.0000 [0.9304, 1.0755] | 1.0000 [0.9304, 1.0755] | 0.000 |
| MMVP | Qwen2.5-VL-3B | MC k=2 | 2 | 300 | 0.5000 | 0.6600 | 0.5000 | 0.7576 [0.6683, 0.8535] | 0.0000 [-0.4167, 0.3421] | 0.000 |
| MMVP | Qwen2.5-VL-3B | all items (MC pooled, item-level null) | mixed | 300 | 0.5000 | 0.6600 | 0.5000 | 0.7576 [0.6683, 0.8535] | 0.0000 [-0.4167, 0.3421] | 0.000 |
| MMVP | Qwen2.5-VL-7B | MC k=2 | 2 | 300 | 0.5000 | 0.7433 | 0.5000 | 0.6726 [0.5931, 0.7560] | 0.0000 [-0.2468, 0.2279] | 0.000 |
| MMVP | Qwen2.5-VL-7B | all items (MC pooled, item-level null) | mixed | 300 | 0.5000 | 0.7433 | 0.5000 | 0.6726 [0.5931, 0.7560] | 0.0000 [-0.2468, 0.2279] | 0.000 |
| MathVerse | Qwen2.5-VL-3B | free-form (gold-consistent, primary) | 0 | 1755 | 0.0000 | 0.0553 | 0.0188 | 0.3402 [0.2400, 0.4580] | 0.3402 [0.2400, 0.4580] | 0.000 |
| MathVerse | Qwen2.5-VL-3B | free-form (all items, sensitivity) | 0 | 1760 | 0.0000 | 0.0551 | 0.0187 | 0.3402 [0.2391, 0.4516] | 0.3402 [0.2391, 0.4516] | 0.000 |
| MathVerse | Qwen2.5-VL-3B | MC k=2 | 2 | 105 | 0.5000 | 0.6381 | 0.5905 | 0.9254 [0.7973, 1.0678] | 0.6552 [-0.0526, 1.5333] | 0.002 |
| MathVerse | Qwen2.5-VL-3B | MC k=3 | 3 | 60 | 0.3333 | 0.4667 | 0.4167 | 0.8929 [0.6875, 1.1481] | 0.6250 [-0.6000, 2.0000] | 0.012 |
| MathVerse | Qwen2.5-VL-3B | MC k=4 | 4 | 1835 | 0.2500 | 0.4703 | 0.4016 | 0.8540 [0.8099, 0.8977] | 0.6883 [0.6012, 0.7776] | 0.000 |
| MathVerse | Qwen2.5-VL-3B | MC k=5 | 5 | 150 | 0.2000 | 0.3333 | 0.2333 | 0.7000 [0.5192, 0.9149] | 0.2500 [-0.3529, 0.7500] | 0.000 |
| MathVerse | Qwen2.5-VL-3B | MC k=6 | 6 | 30 | 0.1667 | 0.1667 | 0.0000 | 0.0000 [0.0000, 0.0000] | n/a | 0.608 |
| MathVerse | Qwen2.5-VL-3B | MC pooled (item-level null) | mixed | 2180 | 0.2597 | 0.4647 | 0.3940 | 0.8480 [0.8073, 0.8888] | 0.6553 [0.5683, 0.7431] | 0.000 |
| MathVerse | Qwen2.5-VL-7B | free-form (gold-consistent, primary) | 0 | 1755 | 0.0000 | 0.0872 | 0.0313 | 0.3595 [0.2800, 0.4430] | 0.3595 [0.2800, 0.4430] | 0.000 |
| MathVerse | Qwen2.5-VL-7B | free-form (all items, sensitivity) | 0 | 1760 | 0.0000 | 0.0869 | 0.0312 | 0.3595 [0.2814, 0.4410] | 0.3595 [0.2814, 0.4410] | 0.000 |
| MathVerse | Qwen2.5-VL-7B | MC k=2 | 2 | 105 | 0.5000 | 0.8857 | 0.5524 | 0.6237 [0.5222, 0.7204] | 0.1358 [-0.1200, 0.3626] | 0.000 |
| MathVerse | Qwen2.5-VL-7B | MC k=3 | 3 | 60 | 0.3333 | 0.5333 | 0.3500 | 0.6562 [0.4516, 0.8966] | 0.0833 [-0.8571, 0.6667] | 0.000 |
| MathVerse | Qwen2.5-VL-7B | MC k=4 | 4 | 1835 | 0.2500 | 0.5433 | 0.4104 | 0.7553 [0.7157, 0.7968] | 0.5467 [0.4769, 0.6190] | 0.000 |
| MathVerse | Qwen2.5-VL-7B | MC k=5 | 5 | 150 | 0.2000 | 0.3867 | 0.4067 | 1.0517 [0.8500, 1.3061] | 1.1071 [0.7143, 1.7826] | 0.000 |
| MathVerse | Qwen2.5-VL-7B | MC k=6 | 6 | 30 | 0.1667 | 0.3000 | 0.2000 | 0.6667 [0.2000, 1.8000] | 0.2500 [-1.5000, 3.0000] | 0.077 |
| MathVerse | Qwen2.5-VL-7B | MC pooled (item-level null) | mixed | 2180 | 0.2597 | 0.5454 | 0.4124 | 0.7561 [0.7207, 0.7927] | 0.5343 [0.4695, 0.6010] | 0.000 |
| MMMU dev+validation | Qwen2.5-VL-3B | free-form | 0 | 62 | 0.0000 | 0.0968 | 0.0484 | 0.5000 [0.0000, 1.0000] | 0.5000 [0.0000, 1.0000] | 0.001 |
| MMMU dev+validation | Qwen2.5-VL-3B | MC k=2 | 2 | 35 | 0.5000 | 0.6286 | 0.6000 | 0.9545 [0.7143, 1.2632] | 0.7778 [-2.3333, 5.0000] | 0.058 |
| MMMU dev+validation | Qwen2.5-VL-3B | MC k=3 | 3 | 133 | 0.3308 | 0.4436 | 0.4436 | 1.0000 [0.8475, 1.1800] | 1.0000 [0.3636, 2.5000] | 0.004 |
| MMMU dev+validation | Qwen2.5-VL-3B | MC k=4 | 4 | 699 | 0.2500 | 0.5193 | 0.4034 | 0.7769 [0.7115, 0.8435] | 0.5697 [0.4499, 0.6915] | 0.000 |
| MMMU dev+validation | Qwen2.5-VL-3B | MC k=5 | 5 | 108 | 0.2000 | 0.4815 | 0.3889 | 0.8077 [0.6545, 0.9773] | 0.6711 [0.4079, 0.9554] | 0.000 |
| MMMU dev+validation | Qwen2.5-VL-3B | MC k=6 **(underpowered)** | 6 | 6 | 0.1667 | 0.3333 | 0.5000 | 1.5000 [1.0000, 4.0000] | 2.0000 [-1.0000, 3.0000] | 0.353 |
| MMMU dev+validation | Qwen2.5-VL-3B | MC k=7 **(underpowered)** | 7 | 2 | 0.1429 | 0.5000 | 0.0000 | 0.0000 [0.0000, 0.0000] | -0.4000 [-0.4000, 1.0000] | 0.247 |
| MMMU dev+validation | Qwen2.5-VL-3B | MC k=9 **(underpowered)** | 9 | 5 | 0.1111 | 0.2000 | 0.2000 | 1.0000 [1.0000, 1.0000] | 1.0000 [1.0000, 1.0000] | 0.325 |
| MMMU dev+validation | Qwen2.5-VL-3B | MC pooled (item-level null) | mixed | 988 | 0.2628 | 0.5061 | 0.4130 | 0.8160 [0.7636, 0.8728] | 0.6172 [0.5117, 0.7288] | 0.000 |
| MMMU dev+validation | Qwen2.5-VL-7B | free-form | 0 | 62 | 0.0000 | 0.1290 | 0.0484 | 0.3750 [0.0000, 1.0000] | 0.3750 [0.0000, 1.0000] | 0.000 |
| MMMU dev+validation | Qwen2.5-VL-7B | MC k=2 | 2 | 35 | 0.5000 | 0.6000 | 0.5429 | 0.9048 [0.6500, 1.2353] | 0.4286 [-5.0000, 5.0000] | 0.120 |
| MMMU dev+validation | Qwen2.5-VL-7B | MC k=3 | 3 | 133 | 0.3308 | 0.4436 | 0.3609 | 0.8136 [0.6452, 1.0182] | 0.2667 [-0.8677, 1.0882] | 0.004 |
| MMMU dev+validation | Qwen2.5-VL-7B | MC k=4 | 4 | 699 | 0.2500 | 0.5608 | 0.4478 | 0.7985 [0.7401, 0.8571] | 0.6364 [0.5339, 0.7398] | 0.000 |
| MMMU dev+validation | Qwen2.5-VL-7B | MC k=5 | 5 | 108 | 0.2000 | 0.5093 | 0.4815 | 0.9455 [0.7692, 1.1569] | 0.9102 [0.6328, 1.2817] | 0.000 |
| MMMU dev+validation | Qwen2.5-VL-7B | MC k=6 **(underpowered)** | 6 | 6 | 0.1667 | 0.1667 | 0.0000 | 0.0000 [0.0000, 0.0000] | n/a | 0.739 |
| MMMU dev+validation | Qwen2.5-VL-7B | MC k=7 **(underpowered)** | 7 | 2 | 0.1429 | 0.5000 | 0.0000 | 0.0000 [0.0000, 0.0000] | -0.4000 [-0.4000, 1.0000] | 0.247 |
| MMMU dev+validation | Qwen2.5-VL-7B | MC k=9 **(underpowered)** | 9 | 5 | 0.1111 | 0.4000 | 0.2000 | 0.5000 [0.0000, 1.0000] | 0.3077 [-1.2500, 1.0000] | 0.078 |
| MMMU dev+validation | Qwen2.5-VL-7B | MC pooled (item-level null) | mixed | 988 | 0.2628 | 0.5374 | 0.4383 | 0.8154 [0.7638, 0.8701] | 0.6388 [0.5414, 0.7403] | 0.000 |

## Format-split rows (strict, `acc_strict`)

The same answer-format null (1/k) is applied to acc_strict. acc_strict additionally requires the <answer> wrapper, so where with-image acc_strict is below the null the denominator is negative; such rows carry denominator_crosses_zero=true and boot_denominator_nonpositive_frac.

| Benchmark | Model | Subset | n | null | with-image | blind | naive retention (95% CI) | corrected retention (95% CI) | denom crosses zero |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BLINK | Qwen2.5-VL-3B | MC k=2 | 924 | 0.5000 | 0.0000 | 0.0000 | n/a | 1.0000 [1.0000, 1.0000] | true |
| BLINK | Qwen2.5-VL-3B | MC k=3 | 134 | 0.3333 | 0.0000 | 0.0000 | n/a | 1.0000 [1.0000, 1.0000] | true |
| BLINK | Qwen2.5-VL-3B | MC k=4 | 843 | 0.2500 | 0.0000 | 0.1127 | n/a | 0.5492 [0.4638, 0.6346] | true |
| BLINK | Qwen2.5-VL-3B | all items (MC pooled, item-level null) | 1901 | 0.3774 | 0.0000 | 0.0500 | n/a | 0.8676 [0.8404, 0.8930] | true |
| BLINK | Qwen2.5-VL-7B | MC k=2 | 924 | 0.5000 | 0.0000 | 0.2922 | n/a | 0.4156 [0.3571, 0.4762] | true |
| BLINK | Qwen2.5-VL-7B | MC k=3 | 134 | 0.3333 | 0.0000 | 0.2687 | n/a | 0.1940 [-0.0299, 0.4179] | true |
| BLINK | Qwen2.5-VL-7B | MC k=4 | 843 | 0.2500 | 0.0000 | 0.2800 | n/a | -0.1198 [-0.2386, -0.0012] | true |
| BLINK | Qwen2.5-VL-7B | all items (MC pooled, item-level null) | 1901 | 0.3774 | 0.0000 | 0.2851 | n/a | 0.2445 [0.1886, 0.2985] | true |
| HallusionBench | Qwen2.5-VL-3B | all items (free-form null=0, primary) | 1129 | 0.0000 | 0.3880 | 0.3552 | 0.9155 [0.8535, 0.9829] | 0.9155 [0.8535, 0.9829] | false |
| HallusionBench | Qwen2.5-VL-3B | all items (binary Yes/No null=0.5, sensitivity) | 1129 | 0.5000 | 0.3880 | 0.3552 | 0.9155 [0.8535, 0.9829] | 1.2925 [1.0511, 1.6359] | true |
| HallusionBench | Qwen2.5-VL-3B | real-image rows only (free-form null=0) | 951 | 0.0000 | 0.3659 | 0.3260 | 0.8908 [0.8141, 0.9732] | 0.8908 [0.8141, 0.9732] | false |
| HallusionBench | Qwen2.5-VL-3B | text-only rows, blank placeholder image (free-form null=0) | 178 | 0.0000 | 0.5056 | 0.5112 | 1.0111 [0.9419, 1.0886] | 1.0111 [0.9419, 1.0886] | false |
| HallusionBench | Qwen2.5-VL-7B | all items (free-form null=0, primary) | 1129 | 0.0000 | 0.3729 | 0.4482 | 1.2019 [1.0973, 1.3162] | 1.2019 [1.0973, 1.3162] | false |
| HallusionBench | Qwen2.5-VL-7B | all items (binary Yes/No null=0.5, sensitivity) | 1129 | 0.5000 | 0.3729 | 0.4482 | 1.2019 [1.0973, 1.3162] | 0.4077 [0.1802, 0.6627] | true |
| HallusionBench | Qwen2.5-VL-7B | real-image rows only (free-form null=0) | 951 | 0.0000 | 0.3239 | 0.4132 | 1.2760 [1.1382, 1.4348] | 1.2760 [1.1382, 1.4348] | false |
| HallusionBench | Qwen2.5-VL-7B | text-only rows, blank placeholder image (free-form null=0) | 178 | 0.0000 | 0.6348 | 0.6348 | 1.0000 [0.9256, 1.0811] | 1.0000 [0.9256, 1.0811] | false |
| MMVP | Qwen2.5-VL-3B | MC k=2 | 300 | 0.5000 | 0.0000 | 0.0000 | n/a | 1.0000 [1.0000, 1.0000] | true |
| MMVP | Qwen2.5-VL-3B | all items (MC pooled, item-level null) | 300 | 0.5000 | 0.0000 | 0.0000 | n/a | 1.0000 [1.0000, 1.0000] | true |
| MMVP | Qwen2.5-VL-7B | MC k=2 | 300 | 0.5000 | 0.0000 | 0.2667 | n/a | 0.4667 [0.3667, 0.5667] | true |
| MMVP | Qwen2.5-VL-7B | all items (MC pooled, item-level null) | 300 | 0.5000 | 0.0000 | 0.2667 | n/a | 0.4667 [0.3667, 0.5667] | true |
| MathVerse | Qwen2.5-VL-3B | free-form (gold-consistent, primary) | 1755 | 0.0000 | 0.0387 | 0.0182 | 0.4706 [0.3333, 0.6429] | 0.4706 [0.3333, 0.6429] | false |
| MathVerse | Qwen2.5-VL-3B | free-form (all items, sensitivity) | 1760 | 0.0000 | 0.0386 | 0.0182 | 0.4706 [0.3289, 0.6308] | 0.4706 [0.3289, 0.6308] | false |
| MathVerse | Qwen2.5-VL-3B | MC k=2 | 105 | 0.5000 | 0.0000 | 0.0952 | n/a | 0.8095 [0.6952, 0.9048] | true |
| MathVerse | Qwen2.5-VL-3B | MC k=3 | 60 | 0.3333 | 0.0000 | 0.1000 | n/a | 0.7000 [0.4500, 0.9000] | true |
| MathVerse | Qwen2.5-VL-3B | MC k=4 | 1835 | 0.2500 | 0.0000 | 0.0610 | n/a | 0.7559 [0.7123, 0.7995] | true |
| MathVerse | Qwen2.5-VL-3B | MC k=5 | 150 | 0.2000 | 0.0000 | 0.0600 | n/a | 0.7000 [0.5000, 0.8667] | true |
| MathVerse | Qwen2.5-VL-3B | MC k=6 | 30 | 0.1667 | 0.0000 | 0.0000 | n/a | 1.0000 [1.0000, 1.0000] | true |
| MathVerse | Qwen2.5-VL-3B | MC pooled (item-level null) | 2180 | 0.2597 | 0.0000 | 0.0628 | n/a | 0.7581 [0.7178, 0.7961] | true |
| MathVerse | Qwen2.5-VL-7B | free-form (gold-consistent, primary) | 1755 | 0.0000 | 0.0843 | 0.0313 | 0.3716 [0.2901, 0.4576] | 0.3716 [0.2901, 0.4576] | false |
| MathVerse | Qwen2.5-VL-7B | free-form (all items, sensitivity) | 1760 | 0.0000 | 0.0841 | 0.0312 | 0.3716 [0.2917, 0.4552] | 0.3716 [0.2917, 0.4552] | false |
| MathVerse | Qwen2.5-VL-7B | MC k=2 | 105 | 0.5000 | 0.0000 | 0.0000 | n/a | 1.0000 [1.0000, 1.0000] | true |
| MathVerse | Qwen2.5-VL-7B | MC k=3 | 60 | 0.3333 | 0.0000 | 0.0000 | n/a | 1.0000 [1.0000, 1.0000] | true |
| MathVerse | Qwen2.5-VL-7B | MC k=4 | 1835 | 0.2500 | 0.0545 | 0.0518 | 0.9500 [0.7287, 1.2353] | 1.0139 [0.9444, 1.0879] | true |
| MathVerse | Qwen2.5-VL-7B | MC k=5 | 150 | 0.2000 | 0.0067 | 0.0600 | 9.0000 [1.7500, 14.0000] | 0.7241 [0.5168, 0.9259] | true |
| MathVerse | Qwen2.5-VL-7B | MC k=6 | 30 | 0.1667 | 0.0000 | 0.0667 | n/a | 0.6000 [0.0000, 1.0000] | true |
| MathVerse | Qwen2.5-VL-7B | MC pooled (item-level null) | 2180 | 0.2597 | 0.0463 | 0.0486 | 1.0495 [0.8113, 1.3542] | 0.9893 [0.9347, 1.0481] | true |
| MMMU dev+validation | Qwen2.5-VL-3B | free-form | 62 | 0.0000 | 0.0806 | 0.0484 | 0.6000 [0.0000, 1.6667] | 0.6000 [0.0000, 1.6667] | true |
| MMMU dev+validation | Qwen2.5-VL-3B | MC k=2 | 35 | 0.5000 | 0.0000 | 0.0000 | n/a | 1.0000 [1.0000, 1.0000] | true |
| MMMU dev+validation | Qwen2.5-VL-3B | MC k=3 | 133 | 0.3308 | 0.0000 | 0.0301 | n/a | 0.9091 [0.8168, 0.9774] | true |
| MMMU dev+validation | Qwen2.5-VL-3B | MC k=4 | 699 | 0.2500 | 0.0029 | 0.0215 | 7.5000 [2.6000, 20.0000] | 0.9247 [0.8784, 0.9653] | true |
| MMMU dev+validation | Qwen2.5-VL-3B | MC k=5 | 108 | 0.2000 | 0.0000 | 0.0185 | n/a | 0.9074 [0.7685, 1.0000] | true |
| MMMU dev+validation | Qwen2.5-VL-3B | MC k=6 **(underpowered)** | 6 | 0.1667 | 0.0000 | 0.0000 | n/a | 1.0000 [1.0000, 1.0000] | true |
| MMMU dev+validation | Qwen2.5-VL-3B | MC k=7 **(underpowered)** | 2 | 0.1429 | 0.0000 | 0.0000 | n/a | 1.0000 [1.0000, 1.0000] | true |
| MMMU dev+validation | Qwen2.5-VL-3B | MC k=9 **(underpowered)** | 5 | 0.1111 | 0.0000 | 0.2000 | n/a | -0.8000 [-4.4000, 1.0000] | true |
| MMMU dev+validation | Qwen2.5-VL-3B | MC pooled (item-level null) | 988 | 0.2628 | 0.0020 | 0.0223 | 11.0000 [4.0000, 28.0000] | 0.9224 [0.8860, 0.9566] | true |
| MMMU dev+validation | Qwen2.5-VL-7B | free-form | 62 | 0.0000 | 0.1290 | 0.0484 | 0.3750 [0.0000, 1.0000] | 0.3750 [0.0000, 1.0000] | false |
| MMMU dev+validation | Qwen2.5-VL-7B | MC k=2 | 35 | 0.5000 | 0.1143 | 0.2571 | 2.2500 [1.0000, 8.0000] | 0.6296 [0.2593, 1.0000] | true |
| MMMU dev+validation | Qwen2.5-VL-7B | MC k=3 | 133 | 0.3308 | 0.2857 | 0.3383 | 1.1842 [0.9038, 1.5833] | -0.1667 [-6.6339, 6.0000] | true |
| MMMU dev+validation | Qwen2.5-VL-7B | MC k=4 | 699 | 0.2500 | 0.2275 | 0.4249 | 1.8679 [1.6286, 2.1597] | -7.7619 [-70.4286, 65.9000] | true |
| MMMU dev+validation | Qwen2.5-VL-7B | MC k=5 | 108 | 0.2000 | 0.1019 | 0.3796 | 3.7273 [2.2500, 7.8000] | -1.8302 [-5.0876, -0.7647] | true |
| MMMU dev+validation | Qwen2.5-VL-7B | MC k=6 **(underpowered)** | 6 | 0.1667 | 0.0000 | 0.0000 | n/a | 1.0000 [1.0000, 1.0000] | true |
| MMMU dev+validation | Qwen2.5-VL-7B | MC k=7 **(underpowered)** | 2 | 0.1429 | 0.0000 | 0.0000 | n/a | 1.0000 [1.0000, 1.0000] | true |
| MMMU dev+validation | Qwen2.5-VL-7B | MC k=9 **(underpowered)** | 5 | 0.1111 | 0.4000 | 0.2000 | 0.5000 [0.0000, 1.0000] | 0.3077 [-1.2500, 1.0000] | true |
| MMMU dev+validation | Qwen2.5-VL-7B | MC pooled (item-level null) | 988 | 0.2628 | 0.2166 | 0.3978 | 1.8364 [1.6320, 2.0794] | -2.9176 [-7.3466, -1.6049] | true |

## Not computed

- **HallusionBench / Qwen2.5-VL-3B / text-only rows (n=178) as evidence of visual necessity** (n=178): HallusionBench_LOCAL_V2.metadata.json records text_only_rows_use_deterministic_blank_image=178: these rows carried a deterministic blank image in the with-image condition, so removing the image removes no visual information and their retention is not evidence about visual necessity. They are reported as their own subset and are the reason the all-items HallusionBench row is a ceiling on retention.
- **HallusionBench / Qwen2.5-VL-7B / text-only rows (n=178) as evidence of visual necessity** (n=178): HallusionBench_LOCAL_V2.metadata.json records text_only_rows_use_deterministic_blank_image=178: these rows carried a deterministic blank image in the with-image condition, so removing the image removes no visual information and their retention is not evidence about visual necessity. They are reported as their own subset and are the reason the all-items HallusionBench row is a ceiling on retention.
- **MathVerse / Qwen2.5-VL-3B / free-form items mathverse_2956..2960** (n=5): The with-image artifact stores gold '0' where the pinned TSV stores '=\frac{7}{4}': VLMEvalKit wrote the xlsx and Excel coerced the leading '=' into a formula. The two conditions therefore do not share a gold on these 5 items, so they are excluded from the paired primary and reported as a sensitivity row instead.
- **MathVerse / Qwen2.5-VL-3B / whole benchmark (single global null)**: Mixed benchmark: 2180 MC items and 1760 free-form items. Per the null rule a single global null is not permitted, so no whole-benchmark corrected retention is reported.
- **MathVerse / Qwen2.5-VL-7B / free-form items mathverse_2956..2960** (n=5): The with-image artifact stores gold '0' where the pinned TSV stores '=\frac{7}{4}': VLMEvalKit wrote the xlsx and Excel coerced the leading '=' into a formula. The two conditions therefore do not share a gold on these 5 items, so they are excluded from the paired primary and reported as a sensitivity row instead.
- **MathVerse / Qwen2.5-VL-7B / whole benchmark (single global null)**: Mixed benchmark: 2180 MC items and 1760 free-form items. Per the null rule a single global null is not permitted, so no whole-benchmark corrected retention is reported.
- **MMMU dev+validation / Qwen2.5-VL-3B / whole benchmark (single global null)**: Mixed benchmark: 988 MC items and 62 free-form items. Per the null rule a single global null is not permitted, so no whole-benchmark corrected retention is reported.
- **MMMU dev+validation / Qwen2.5-VL-7B / whole benchmark (single global null)**: Mixed benchmark: 988 MC items and 62 free-form items. Per the null rule a single global null is not permitted, so no whole-benchmark corrected retention is reported.

## Provenance

| Benchmark | Model | Blind run id | Blind config | with-image run (source of the paired column) |
| --- | --- | --- | --- | --- |
| BLINK | Qwen2.5-VL-3B | `layer1_blind_e1c_blink3b_an29_20260730T131949Z` | `configs/eval/layer1_blind_blink_3b.json` | `experiments/runs/vlmevalkit_postprocess_l10_blink3b_canonicalv2_final_20260711T132325Z` |
| BLINK | Qwen2.5-VL-7B | `layer1_blind_e1c_blink7b_an29_20260730T132024Z` | `configs/eval/layer1_blind_blink_7b.json` | `experiments/runs/vlmevalkit_postprocess_l10_blink7b_canonicalv2_final_20260711T132325Z` |
| HallusionBench | Qwen2.5-VL-3B | `layer1_blind_e1c_hallusion3b_an29_20260730T131755Z` | `configs/eval/layer1_blind_hallusion_3b.json` | `experiments/runs/vlmevalkit_postprocess_l10_hallusion3b_canonicalv2_final_20260711T132325Z` |
| HallusionBench | Qwen2.5-VL-7B | `layer1_blind_e1c_hallusion7b_an29_20260730T131811Z` | `configs/eval/layer1_blind_hallusion_7b.json` | `experiments/runs/vlmevalkit_postprocess_l10_hallusion7b_canonicalv2_final_20260711T132325Z` |
| MMVP | Qwen2.5-VL-3B | `layer1_blind_e1c_mmvp3b_an29_20260730T131650Z` | `configs/eval/layer1_blind_mmvp_3b.json` | `experiments/runs/vlmevalkit_postprocess_l10_mmvp3b_canonicalv2_final_20260711T132326Z` |
| MMVP | Qwen2.5-VL-7B | `layer1_blind_e1c_mmvp7b_an29_20260730T131650Z` | `configs/eval/layer1_blind_mmvp_7b.json` | `experiments/runs/vlmevalkit_postprocess_l10_mmvp7b_canonicalv2_final_20260711T132326Z` |
| MathVerse | Qwen2.5-VL-3B | `layer1_blind_e1c_mathverse3b_an29_20260730T132052Z` | `configs/eval/layer1_blind_mathverse_3b.json` | `experiments/runs/vlmevalkit_postprocess_l10_mathverse3b_canonicalv2_v2_20260711T143923Z` |
| MathVerse | Qwen2.5-VL-7B | `layer1_blind_e1c_mathverse7b_an29_20260730T132138Z` | `configs/eval/layer1_blind_mathverse_7b.json` | `experiments/runs/vlmevalkit_postprocess_l10_mathverse7b_canonicalv2_v2_20260711T143943Z` |
| MMMU dev+validation | Qwen2.5-VL-3B | `layer1_blind_e1c_mmmu3b_an29_20260730T131851Z` | `configs/eval/layer1_blind_mmmu_3b.json` | `experiments/runs/vlmevalkit_postprocess_l10_mmmu3b_v2_canonicalv2_20260711T145554Z` |
| MMMU dev+validation | Qwen2.5-VL-7B | `layer1_blind_e1c_mmmu7b_an29_20260730T131915Z` | `configs/eval/layer1_blind_mmmu_7b.json` | `experiments/runs/vlmevalkit_postprocess_l10_mmmu7b_v2_canonicalv2_20260711T145711Z` |

All blind cells: node/GPU, seed, git hash, config hash, data manifest hash, exit code, and `image_removed` flag are recorded per cell in the `provenance` block of the json, and in each run's `run_manifest.json`.

### Input artifact digests

| Artifact | sha256 | bytes |
| --- | --- | --- |
| `experiments/runs/layer1_blind_e1c_blink3b_an29_20260730T131949Z/predictions.jsonl` | `1603f1df124b7a9c...` | 1649892 |
| `experiments/runs/vlmevalkit_postprocess_l10_blink3b_canonicalv2_final_20260711T132325Z/rows.jsonl` | `331aaa7cbfce8506...` | 1766564 |
| `experiments/runs/layer1_blind_e1c_blink7b_an29_20260730T132024Z/predictions.jsonl` | `9911d4ba2fd481b3...` | 1667150 |
| `experiments/runs/vlmevalkit_postprocess_l10_blink7b_canonicalv2_final_20260711T132325Z/rows.jsonl` | `604bc57f26a0f466...` | 1770523 |
| `experiments/runs/layer1_blind_e1c_hallusion3b_an29_20260730T131755Z/predictions.jsonl` | `585d71ccb5edae45...` | 899948 |
| `experiments/runs/vlmevalkit_postprocess_l10_hallusion3b_canonicalv2_final_20260711T132325Z/rows.jsonl` | `bb8911236f06d8d9...` | 957225 |
| `experiments/runs/layer1_blind_e1c_hallusion7b_an29_20260730T131811Z/predictions.jsonl` | `386c2dd6f754fad7...` | 902311 |
| `experiments/runs/vlmevalkit_postprocess_l10_hallusion7b_canonicalv2_final_20260711T132325Z/rows.jsonl` | `b0f67f655eb02965...` | 959109 |
| `experiments/runs/layer1_blind_e1c_mmvp3b_an29_20260730T131650Z/predictions.jsonl` | `5ab0753a3d2ad9b0...` | 244286 |
| `experiments/runs/vlmevalkit_postprocess_l10_mmvp3b_canonicalv2_final_20260711T132326Z/rows.jsonl` | `5d34202e77f6522d...` | 263204 |
| `experiments/runs/layer1_blind_e1c_mmvp7b_an29_20260730T131650Z/predictions.jsonl` | `6f15ee043be5b820...` | 245902 |
| `experiments/runs/vlmevalkit_postprocess_l10_mmvp7b_canonicalv2_final_20260711T132326Z/rows.jsonl` | `cdf7558b4091f0ef...` | 263323 |
| `experiments/runs/layer1_blind_e1c_mathverse3b_an29_20260730T132052Z/predictions.jsonl` | `d112fb48b79275bd...` | 3311808 |
| `experiments/runs/vlmevalkit_postprocess_l10_mathverse3b_canonicalv2_v2_20260711T143923Z/rows.jsonl` | `513641a5a9425311...` | 3578184 |
| `experiments/runs/layer1_blind_e1c_mathverse7b_an29_20260730T132138Z/predictions.jsonl` | `4bb5971b35943c2b...` | 3329834 |
| `experiments/runs/vlmevalkit_postprocess_l10_mathverse7b_canonicalv2_v2_20260711T143943Z/rows.jsonl` | `b92c3e89bead0379...` | 3592732 |
| `experiments/runs/layer1_blind_e1c_mmmu3b_an29_20260730T131851Z/predictions.jsonl` | `3254c1a42beccc73...` | 930469 |
| `experiments/runs/vlmevalkit_postprocess_l10_mmmu3b_v2_canonicalv2_20260711T145554Z/rows.jsonl` | `3b80a6a8464c2026...` | 1009577 |
| `experiments/runs/layer1_blind_e1c_mmmu7b_an29_20260730T131915Z/predictions.jsonl` | `8076498a4c46565a...` | 951050 |
| `experiments/runs/vlmevalkit_postprocess_l10_mmmu7b_v2_canonicalv2_20260711T145711Z/rows.jsonl` | `64321526f1ff7c83...` | 1022789 |

