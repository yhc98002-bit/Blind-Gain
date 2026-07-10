---
language:
- en
license: mit
task_categories:
- question-answering
- image-text-to-text
tags:
- training
- Reinforcement Learning
---

# 1. Overview of ViRL39K

**ViRL39K** (pronounced as "viral") provides a curated collection of 38,870 verifiable QAs for **Vi**sion-Language **RL** training. 
It is built on top of newly collected problems and existing datasets (
[Llava-OneVision](https://huggingface.co/datasets/lmms-lab/LLaVA-OneVision-Data), 
[R1-OneVision](https://huggingface.co/datasets/Fancy-MLLM/R1-Onevision),
[MM-Eureka](https://huggingface.co/datasets/FanqingM/MMK12),
[MM-Math](https://huggingface.co/datasets/THU-KEG/MM_Math),
[M3CoT](https://huggingface.co/datasets/LightChen2333/M3CoT),
[DeepScaleR](https://huggingface.co/datasets/agentica-org/DeepScaleR-Preview-Dataset),
[MV-Math](https://huggingface.co/datasets/PeijieWang/MV-MATH))
through cleaning, reformatting, rephrasing and verification.

**ViRL39K** lays the foundation for SoTA Vision-Language Reasoning Model [VL-Rethinker](https://tiger-ai-lab.github.io/VL-Rethinker/). It has the following merits:
- **high-quality** and **verifiable**: the QAs undergo rigorous filtering and quality control, removing problematic queries or ones that cannot be verified by rules.
- covering **comprehensive** topics and categories: from grade school problems to broader STEM and Social topics; reasoning with charts, diagrams, tables, documents, spatial relationships, etc. 
- with fine-grained **model-capability annotations**: it tells you what queries to use when training models at different scales.

Explore more about **VL-Rethinker**:
- [**Project Page**](https://tiger-ai-lab.github.io/VL-Rethinker/) 
- [**Github**](https://github.com/TIGER-AI-Lab/VL-Rethinker) 
- [**Paper**](https://arxiv.org/abs/2504.08837) 
- [**Models**](https://huggingface.co/collections/TIGER-Lab/vl-rethinker-67fdc54de07c90e9c6c69d09)


# 2. Dataset Statistics
## 2.1 **ViRL39K** covers **eight** major categories:
![image/png](https://cdn-uploads.huggingface.co/production/uploads/65bf52f0259bc6caeb74f8bf/JYKhUrEbKQOP8p0nkdNmc.png)

## 2.2 **ViRL39K** covers different difficulty levels for different model scales.
![image/png](https://cdn-uploads.huggingface.co/production/uploads/65bf52f0259bc6caeb74f8bf/fUtM10BsllV7axEblwKxQ.png)

We associate each query with a PassRate annotation that reflects **model-capability** affinity. 

You can use this annotation to select the proper queries to train models at different scales.

# 3. Dataset Keys
- answer: all answers are with \\boxed{}.

For answer extractions, we recommend using the `math-verify` library. 

It can handle partial match where the answer has text in it, such as : `predicted = \\boxed{17}, answer = \\boxed{17^\circ}`.

You can refer to our [**Github**](https://github.com/TIGER-AI-Lab/VL-Rethinker)  for reference of extraction and matching functions.

- PassRate:
  
we provide all PassRate for 32BTrained, <u>but provide only partial PassRate for 7BUntrained</u>, to save compute.

Specifically, we only label PassRate on 7BUntrained with 50\% queries in the dataset. These selected queries are easy for 32BTrained, which has `PassRate==1.0`. 

The remaining queries are somewhat challenging for 32BTrained (`PassRate<1.0`), so we assume they will also be challenging for 7BUntrained. 

**Note**: For 7BUntrained PassRate annotations, if they are not tested because `PassRate_32BTrained<1.0`, they are labeled `PassRate_7BUntrained=-1.0`.

- Category:
  
you can choose queries of interest based on the category.


## Citation

If you find ViRL39K useful, please give us a free cit:
```bibtex
@article{vl-rethinker,
      title={VL-Rethinker: Incentivizing Self-Reflection of Vision-Language Models with Reinforcement Learning},
      author = {Wang, Haozhe and Qu, Chao and Huang, Zuming and Chu, Wei and Lin,Fangzhen and Chen, Wenhu},
      journal={arXiv preprint arXiv:2504.08837},
      year={2025}
}
```

