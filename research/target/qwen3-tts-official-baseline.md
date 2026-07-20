# Qwen3-TTS official target baseline

本基线截至 2026-07-17（Asia/Shanghai），只使用 Qwen/Alibaba 官方源码与发布页、官方模型托管元数据及 Qwen Team 技术报告建立目标侧事实；没有下载权重或数据，也没有运行模型、训练、评测或任何 CUDA/Ascend 真机实验。文中“已证实”只表示固定公开材料直接支持，“项目声明”不表示独立复现，“分析推断”不表示项目能力，“待真机验证”保持 unknown。[SRC-001][SRC-003][SRC-004][SRC-005]

## 1. Official artifacts and fixed revisions

canonical 源码仓库为 `QwenLM/Qwen3-TTS`，默认分支 `main` 在本次审计固定为完整 commit `022e286b98fbec7e1e916cb940cdf532cd9f488e`；该提交的 author/committer 时间为 `2026-03-17T14:38:41+08:00`，主题为 `fix finetuning bug`。固定树与 `pyproject.toml` 声明 Apache-2.0；技术报告固定为 arXiv `2601.15621v1`，页面标注 CC BY 4.0，论文许可不外推为代码或权重许可。[SRC-001][SRC-002][SRC-003]

官方 Hugging Face 与 ModelScope collection 用于确认五个 12Hz TTS 模型和一个 12Hz Tokenizer 的发布清单，但 moving collection 不作为固定 revision 证明。下表的 Hugging Face SHA 分别回指官方 immutable commit URL；ModelScope UI 没有已核实的稳定 commit permalink，因此每个 ModelScope SHA 都由只读 `git ls-remote` 对对应官方 asset remote 的 `HEAD` 验证。SHA 只用于重放资产元数据，不代表本研究下载或执行了相应权重。[SRC-004][SRC-005][SRC-006][SRC-007][SRC-008][SRC-009][SRC-010][SRC-011][SRC-012][SRC-013][SRC-014][SRC-015][SRC-016][SRC-017]

| Asset | Hugging Face `main` full SHA | ModelScope `master` full SHA | Evidence |
| --- | --- | --- | --- |
| `Qwen3-TTS-Tokenizer-12Hz` | [`7dd38ad4e9bad454aae9cd937d0cd577604fe229`](https://huggingface.co/Qwen/Qwen3-TTS-Tokenizer-12Hz/commit/7dd38ad4e9bad454aae9cd937d0cd577604fe229) | [`d1d2fe2dbcbdc294f6962e5aa47ba394dc0cab07`](https://www.modelscope.cn/Qwen/Qwen3-TTS-Tokenizer-12Hz.git) | SRC-006, SRC-012 |
| `Qwen3-TTS-12Hz-1.7B-CustomVoice` | [`0c0e3051f131929182e2c023b9537f8b1c68adfe`](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice/commit/0c0e3051f131929182e2c023b9537f8b1c68adfe) | [`54dfa57e196341bfa4994c97ad1f0f874964eeab`](https://www.modelscope.cn/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice.git) | SRC-007, SRC-013 |
| `Qwen3-TTS-12Hz-1.7B-VoiceDesign` | [`5ecdb67327fd37bb2e042aab12ff7391903235d3`](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign/commit/5ecdb67327fd37bb2e042aab12ff7391903235d3) | [`8dd530dbed7fda907a15ac48d7f78742cc90a065`](https://www.modelscope.cn/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign.git) | SRC-008, SRC-014 |
| `Qwen3-TTS-12Hz-1.7B-Base` | [`fd4b254389122332181a7c3db7f27e918eec64e3`](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base/commit/fd4b254389122332181a7c3db7f27e918eec64e3) | [`dfb4a462f62f8f831ff0ffabf31189fc9d4344fd`](https://www.modelscope.cn/Qwen/Qwen3-TTS-12Hz-1.7B-Base.git) | SRC-009, SRC-015 |
| `Qwen3-TTS-12Hz-0.6B-CustomVoice` | [`85e237c12c027371202489a0ec509ded67b5e4b5`](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice/commit/85e237c12c027371202489a0ec509ded67b5e4b5) | [`70b274883e68023af521a9199603192d58ccdd3f`](https://www.modelscope.cn/Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice.git) | SRC-010, SRC-016 |
| `Qwen3-TTS-12Hz-0.6B-Base` | [`5d83992436eae1d760afd27aff78a71d676296fc`](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base/commit/5d83992436eae1d760afd27aff78a71d676296fc) | [`fda1995a3162ad0488393cc366b82ca59c91c08e`](https://www.modelscope.cn/Qwen/Qwen3-TTS-12Hz-0.6B-Base.git) | SRC-011, SRC-017 |

## 2. Released model variants and training-related claims

已证实的官方公开资产范围是 `1.7B-Base`、`1.7B-VoiceDesign`、`1.7B-CustomVoice`、`0.6B-Base`、`0.6B-CustomVoice` 五个 12Hz 模型和 `Qwen3-TTS-Tokenizer-12Hz`。固定 README 将 Base 描述为可用于 fine-tuning，将 VoiceDesign 描述为自然语言声音设计，将 CustomVoice 描述为预置音色；功能、质量与 streaming 效果仍属于项目声明而非本研究实测。[SRC-001][SRC-004][SRC-005]

技术报告 Table 1 另列出五个 25Hz 条目：`1.7B-Base`、`1.7B-VoiceEditing`、`1.7B-CustomVoice`、`0.6B-Base`、`0.6B-CustomVoice`。固定 README 明确“技术报告中的其他模型未来发布”，官方 collection 未列这些 25Hz 权重，因此本基线只确认报告描述了十项 family，不把 25Hz 权重视为已公开资产。[SRC-001][SRC-003][SRC-004][SRC-005]

报告声称预训练使用超过 500 万小时多语言语音，并分为 S1 通用阶段、S2 高质量持续预训练和 S3 长上下文阶段；S3 将最大 token length 从 8192 提高到 32768。报告还声称后训练依次使用 DPO、规则奖励驱动的 GSPO 和轻量 speaker fine-tuning；这些是项目方方法声明，公开仓库没有相应复现入口、数据管线、集群配置或完整超参数。[SRC-001][SRC-003]

## 3. Repository map and whether training code is public

固定源码树的研究相关入口如下；这是一棵源码/文档树，不包含本研究下载的任何权重或数据。[SRC-001]

```text
Qwen3-TTS@022e286b98fbec7e1e916cb940cdf532cd9f488e
├── README.md
├── pyproject.toml
├── examples/
│   ├── test_model_12hz_base.py
│   ├── test_model_12hz_custom_voice.py
│   ├── test_model_12hz_voice_design.py
│   └── test_tokenizer_12hz.py
├── finetuning/
│   ├── README.md
│   ├── prepare_data.py
│   ├── dataset.py
│   └── sft_12hz.py
└── qwen_tts/
    ├── cli/demo.py
    ├── inference/qwen3_tts_model.py
    ├── inference/qwen3_tts_tokenizer.py
    └── core/
        ├── models/{configuration,modeling,processing}_qwen3_tts.py
        ├── tokenizer_12hz/{configuration,modeling}_qwen3_tts_tokenizer_v2.py
        └── tokenizer_25hz/{configuration,modeling}_qwen3_tts_tokenizer_v1.py
```

公开训练代码的准确边界是：**只有 12Hz 0.6B/1.7B Base 到单说话人 CustomVoice 的 SFT 示例公开**。`finetuning/README.md` 明确写 single-speaker，并把 multi-speaker 与其他高级 fine-tuning 留给未来版本；不能将这一目录概括成完整训练代码公开。[SRC-001]

在固定 revision 的完整 tracked tree 中，没有 Qwen3-TTS pretraining、DPO、GSPO、Tokenizer training 或可执行 benchmark/eval pipeline 的入口，也没有官方 multi-node launcher、NCCL 配置、`torchrun`/DeepSpeed/FSDP 启动示例。该结论严格限定于本次固定树审计，不表示相关内部代码永远不存在。[SRC-001]

## 4. End-to-end data and control flow

推理加载链由 `Qwen3TTSModel.from_pretrained` 注册 Qwen3-TTS config/model/processor，再通过 Transformers 加载模型与 processor。文本经 Qwen tokenizer/processor 编码；Base voice clone 还从 reference audio 提取 speech codes 与 speaker embedding，ICL 模式同时携带 reference transcript；VoiceDesign 加入自然语言 instruction；CustomVoice 选择预置 speaker embedding。[SRC-001]

12Hz 生成链使用 dual-track text/codec 表示：Talker 的主干自回归预测第 0 个 codec codebook，code predictor/MTP 再按帧预测其余 15 个 residual codebooks。最终多码本 codes 交给 12Hz speech tokenizer 的因果解码路径还原 waveform；这一代码路径可审查，但本研究没有对音质、延迟或 streaming 行为做运行验证。[SRC-001][SRC-003]

SFT 数据链从每行包含 `audio`、`text`、`ref_audio` 的 JSONL 开始；`prepare_data.py` 使用 12Hz tokenizer 离线生成 `audio_codes`。`TTSDataset` 将文本包装为 ChatML assistant 序列，要求 reference audio 为 24 kHz，计算 128-bin mel，并在 collate 时构造双通道 text/codec 输入、16 码本、attention mask、codec mask 与第 0 码本 labels。[SRC-001]

`sft_12hz.py` 用 speaker encoder 生成并 detach reference speaker embedding，将其注入 codec embedding；Talker 计算第 0 码本 LM loss，sub-talker/code predictor 计算剩余码本 loss，总损失为 `main_loss + 0.3 * sub_talker_loss`。AdamW 更新模型参数；每个 epoch 由主进程复制初始 checkpoint 目录、改写为 custom-voice 配置、写入 speaker id 3000、移除 `speaker_encoder*` state keys 并保存 `model.safetensors`。[SRC-001]

## 5. Text and audio tokenization or codec path

文本路径使用 Qwen tokenizer 与 ChatML；公开 `Qwen3TTSProcessor` 只包装 text tokenizer。12Hz SFT 的音频预处理把目标音频先物化为 codec codes，并对 reference audio 计算 24 kHz、128-bin mel 供 speaker encoder 使用。[SRC-001]

技术报告把 12Hz tokenizer 描述为 12.5 FPS、16 个 2048-entry codebooks：第 0 层在 WavLM teacher 引导下承载语义，后 15 层 RVQ 逐步表示声学细节；encoder/decoder 为完全因果、无 look-ahead，波形恢复采用轻量 causal ConvNet。公开仓库含 12Hz encoder/RVQ/Transformer/causal decoder 的推理实现，但没有报告所述 GAN、discriminator、多尺度 mel loss或 WavLM-teacher tokenizer-training 入口。[SRC-001][SRC-003]

技术报告把 25Hz tokenizer 描述为 32768-entry 单码本和两阶段训练：Qwen2-Audio 路径产生 tokens，flow-matching DiT 将 code 转为 mel，modified BigVGAN 再生成 waveform；chunked streaming 使用当前块、3-block lookback 与 1-block lookahead。固定仓库含 25Hz tokenizer modeling/inference 源码，但官方公开资产清单未提供 25Hz tokenizer checkpoint，因此其公开可执行性在本基线中保持 unknown。[SRC-001][SRC-003][SRC-004][SRC-005]

## 6. Model components and generation stages

- `Qwen3TTSSpeakerEncoder`：ECAPA-TDNN 风格 speaker encoder，接收 128-bin mel 并产生 speaker embedding；公开配置默认 `enc_dim=1024`。[SRC-001]
- `Qwen3TTSTalkerModel` / `Qwen3TTSTalkerForConditionalGeneration`：Qwen3-style decoder backbone，组合 text projection 与 codec embedding，LM head 预测第 0 码本。[SRC-001][SRC-003]
- `Qwen3TTSTalkerCodePredictor*`：MTP/sub-talker，基于 Talker hidden state 与已知码本顺序生成剩余 residual codebooks。[SRC-001][SRC-003]
- `Qwen3TTSTokenizerV2Model`：12Hz 多码本 tokenizer 路径，包含 encoder、split/RVQ 与轻量因果 waveform decoder。[SRC-001][SRC-003]
- `Qwen3TTSTokenizerV1Model`：25Hz tokenizer 路径，包含 Qwen2-Audio-derived encoder/VQ、DiT mel decoder 与 BigVGAN waveform decoder。[SRC-001][SRC-003]
- Base 支持 speaker-embedding-only 与 text/audio ICL 两条 voice-clone prompt 路径；VoiceDesign 使用自然语言 instruction；CustomVoice 通过 speaker id/embedding 注入预置音色。[SRC-001][SRC-003]

12Hz 的生成阶段可以压缩为 `text/prompt encoding -> dual-track Talker -> codec-0 autoregression -> per-frame MTP residual codebooks -> 12Hz causal tokenizer decode -> waveform`。这是一份源码与报告的结构映射，不是吞吐、时延、数值一致性或真机稳定性的验证结果。[SRC-001][SRC-003]

## 7. Pretraining, SFT, inference, and evaluation entry points

| Stage | Public entry point | Evidence state | Publicly unknowable details | Evidence |
| --- | --- | --- | --- | --- |
| Pretraining S1/S2/S3 | None in fixed tree | Project claim only | Data construction and sampling; optimizer/scheduler; global batch; parallelism; checkpoint/resume/fault handling | SRC-001, SRC-003 |
| Post-training DPO | None in fixed tree | Project claim only | Preference schema; reference policy; objective implementation; hyperparameters; parallelism | SRC-001, SRC-003 |
| Post-training GSPO | None in fixed tree | Project claim only | Rule rewards; rollout/group construction; objective implementation; hyperparameters; parallelism | SRC-001, SRC-003 |
| 12Hz single-speaker SFT | `finetuning/prepare_data.py`; `dataset.py`; `sft_12hz.py` | Source-confirmed example | Validation split/metrics; scheduler; resume; distributed launch and tested scale | SRC-001 |
| Inference | `examples/test_model_12hz_*.py`; `examples/test_tokenizer_12hz.py`; wrapper APIs; `qwen-tts-demo` | Source-confirmed interfaces | Hardware performance and output quality remain unverified here | SRC-001 |
| Evaluation | README/report tables and method descriptions only | Project claim only | Official executable pipeline; exact dataset preparation; metric code/revisions; raw outputs; distributed evaluation | SRC-001, SRC-003 |

公开材料因此不足以复现完整 training-to-evaluation lifecycle；后续参考项目选择必须由其他有证据的训练/分布式路线补足，而不能从 Qwen3-TTS 的项目声明推导出缺失入口。[SRC-001][SRC-003]

## 8. CUDA, NCCL, fused-kernel, mixed-precision, and custom-extension dependencies

| Topic | Fixed public evidence and boundary | State | Evidence |
| --- | --- | --- | --- |
| CUDA | README examples and `prepare_data.py` use `cuda:0`; this is an NVIDIA-oriented interface rather than a run performed here | Source-confirmed interface; not independently run | SRC-001 |
| FlashAttention 2 | README recommends it for memory reduction and limits it to fp16/bf16; SFT requests `flash_attention_2` | Source-confirmed dependency choice; not benchmarked | SRC-001 |
| BF16 / AMP | SFT builds `Accelerator(... mixed_precision="bf16")` and loads BF16; README evaluation claims BF16 | Source-confirmed code and project evaluation claim | SRC-001 |
| FP16 | README describes FlashAttention compatibility; official SFT path itself selects BF16 | Compatibility claim only for this baseline | SRC-001 |
| NCCL | No NCCL configuration or training usage is present in the fixed tracked tree | Unknown / not publicly established | SRC-001 |
| DDP/FSDP/DeepSpeed/torchrun | `Accelerator.prepare` is used, but there is no project launcher/config/example or scale claim; two generic FSDP compatibility comments do not prove support | Analysis boundary; tested support unknown | SRC-001 |
| Fused/custom extensions | No project-owned `.cu`, `.cuh`, C/C++, or Triton source exists in the fixed tree; FlashAttention is an optional third-party backend | No public project-owned extension found | SRC-001 |
| `torch.compile` / CUDA Graph | Report says these optimize tokenizer decode in an internal vLLM V0 inference benchmark on one typical resource | Project claim for internal inference only; not training evidence | SRC-003 |

本基线没有运行 CUDA、FlashAttention、NCCL、mixed precision 或任何 kernel；表中“source-confirmed”仅表示参数、依赖或代码路径存在，不能解释为设备兼容性、性能或数值正确性已验证。[SRC-001][SRC-003]

## 9. Single-node and multi-node assumptions

官方 SFT README 只给出 `python sft_12hz.py`，数据预处理示例固定 `cuda:0`；仓库没有 `accelerate launch` 配置、process count、node rank、master address、hostfile、SLURM、NCCL 环境、`torchrun`、单机 8 卡或 multi-node 示例。`Accelerator.prepare` 与 `is_main_process` 只能说明脚本具备框架包装点，不能证明多进程正确性或可扩展性。[SRC-001]

因此可确认的是单 CUDA device 的公开接口和单说话人 SFT 实现，而不是一次成功的单卡训练；单机 8 卡、多机多卡、global-batch accounting、sampler sharding、collective topology、checkpoint 并发安全、吞吐、确定性与容错全部保持 unknown / 待真机验证。[SRC-001]

报告效率表中的 concurrency 1/3/6 来自单一“typical computational resource”上的内部 vLLM 推理测量；它既不是 node/GPU 数量，也不是训练规模证据，不能用于填补单机 8 卡或多机多卡缺口。[SRC-003]

## 10. Confirmed facts, project claims, analysis inferences, and unknowns

### Confirmed facts

- canonical repo、默认分支、完整 fixed commit、提交时间/主题与代码 Apache-2.0 许可已由官方 Git 元数据和固定树确认。[SRC-001][SRC-002]
- 固定树公开推理与两代 tokenizer modeling 源码，以及范围明确的 12Hz Base 单说话人 SFT 示例。[SRC-001]
- 官方 Hugging Face 与 ModelScope collection 列出五个 12Hz 模型和一个 12Hz Tokenizer；collections 只证明发布清单，不证明固定 revision。[SRC-004][SRC-005]
- 六个 Hugging Face asset revision 分别由官方 immutable commit URL 证明；六个 ModelScope asset revision 分别由对应官方 remote 的只读 `git ls-remote` 证明，且没有构造未经核实的 ModelScope commit permalink。[SRC-006][SRC-007][SRC-008][SRC-009][SRC-010][SRC-011][SRC-012][SRC-013][SRC-014][SRC-015][SRC-016][SRC-017]
- SFT 的 JSONL 字段、离线 codec 准备、BF16、FlashAttention 2、gradient accumulation 4、AdamW、clip norm 1.0、组合 loss 与按 epoch safetensors 保存可由源码直接审查。[SRC-001]

### Project claims

- 超过 500 万小时、十种语言、S1/S2/S3、DPO、GSPO、speaker fine-tuning 与 ChatML 数据格式均来自 Qwen Team 报告，没有由本研究运行复现。[SRC-003]
- 97 ms first-packet、长语音稳定性、SOTA 与各 benchmark 数值是官方项目声明，不是真机或独立评测结论。[SRC-001][SRC-003]
- 25Hz family、两类 tokenizer 的训练方法以及内部 vLLM/CUDA Graph 效率数据是报告声明；公开资产与代码入口不能完整复现这些结果。[SRC-001][SRC-003][SRC-004][SRC-005]

### Analysis inferences

- `Accelerator.prepare` 可能允许外部配置多进程，但缺少项目 launcher、配置、日志和规模证据，故不得标记为已支持 distributed training。[SRC-001]
- 迁移优先级应落在已发布 12Hz 路线的 Talker attention/MLP/KV cache、MTP 内循环、speaker encoder、16-codebook RVQ、causal decoder、离线 audio-code preparation 与 HF generation glue；25Hz DiT/BigVGAN 暂作为次级映射。[SRC-001][SRC-003][SRC-004][SRC-005]

### Unknowns / pending hardware validation

- Pretraining、DPO、GSPO、Tokenizer training 的源码、数据与完整超参数，以及官方数据许可/过滤/去重/sampling 明细均未公开。[SRC-001][SRC-003]
- 官方 executable eval pipeline、metric implementation/revisions、raw predictions 与 distributed evaluation 未公开。[SRC-001][SRC-003]
- NCCL、single-node 8-GPU、multi-node multi-GPU、TP/PP/CP/EP、ZeRO/FSDP、resume、fault tolerance 与 checkpoint ownership 未建立公开项目证据。[SRC-001]
- CANN、torch-npu、MindSpeed、Ascend 910B kernel/precision/performance behavior 以及所有 CUDA-to-Ascend 替换都必须后续实现并真机验证。[SRC-001]

## 11. Target-module checklist for future migration mapping

- [ ] Qwen text tokenizer、ChatML processor 与输入模板。[SRC-001][SRC-003]
- [ ] `Qwen3TTSTalkerModel` 的 text projection、codec embedding、Qwen3 decoder layers、RoPE、attention 与 KV cache。[SRC-001]
- [ ] Talker codec-0 LM head、generation logits processors 与 sampling。[SRC-001]
- [ ] `Qwen3TTSTalkerCodePredictor*` 的 per-frame MTP/residual-codebook 顺序生成。[SRC-001][SRC-003]
- [ ] `Qwen3TTSSpeakerEncoder` 与 24 kHz/128-bin mel frontend。[SRC-001]
- [ ] Base 的 x-vector-only 和 ICL reference text/audio prompt 路径。[SRC-001][SRC-003]
- [ ] VoiceDesign instruction prefix 与 CustomVoice speaker-id/embedding 注入路径。[SRC-001][SRC-003]
- [ ] 12Hz tokenizer encoder、16-codebook split/RVQ encode/decode。[SRC-001][SRC-003]
- [ ] 12Hz Transformer + causal ConvNet/ConvNeXt waveform decoder 与 chunked decode。[SRC-001][SRC-003]
- [ ] librosa、torchaudio、soundfile、sox 等 audio preprocessing/resampling 依赖。[SRC-001]
- [ ] `prepare_data.py` 离线 audio-code materialization 与可恢复数据分片。[SRC-001]
- [ ] `TTSDataset.collate_fn` 双通道 masks、codec labels 与 distributed sampler 改造。[SRC-001]
- [ ] SFT main loss + `0.3 * sub_talker_loss` 的数值一致性。[SRC-001]
- [ ] Accelerate BF16、gradient accumulation、gradient clipping 与 optimizer 集成。[SRC-001]
- [ ] checkpoint copy/config mutation/safetensors save，以及缺失的 resume/ownership 设计。[SRC-001]
- [ ] Transformers `generate()` 兼容、FlashAttention abstraction 与 eager/SDPA/Ascend fallback。[SRC-001]
- [ ] single-node 8-card global-batch accounting、sampler、collectives 与 checkpoint ownership。[SRC-001]
- [ ] multi-node rendezvous、collectives、topology、fault handling 与恢复。[SRC-001]
- [ ] eval reproducibility：datasets、ASR WER/CER、speaker SIM、tokenizer PESQ/STOI/UTMOS。[SRC-001][SRC-003]
- [ ] 25Hz tokenizer/DiT/BigVGAN 仅作次级映射，直到官方 25Hz checkpoint 与可复现入口公开。[SRC-001][SRC-003][SRC-004][SRC-005]

## 12. Source index using `SRC-*` identifiers

| Source ID | Grade | Official artifact and fixed boundary | Purpose |
| --- | --- | --- | --- |
| SRC-001 | S | [QwenLM/Qwen3-TTS tree at `022e286b98fbec7e1e916cb940cdf532cd9f488e`](https://github.com/QwenLM/Qwen3-TTS/tree/022e286b98fbec7e1e916cb940cdf532cd9f488e) | Repository map; architecture implementation; SFT/data flow; dependency and absence audit |
| SRC-002 | S | [Commit `022e286b98fbec7e1e916cb940cdf532cd9f488e`](https://github.com/QwenLM/Qwen3-TTS/commit/022e286b98fbec7e1e916cb940cdf532cd9f488e) | Immutable revision provenance and commit metadata |
| SRC-003 | S | [Qwen3-TTS Technical Report `arXiv:2601.15621v1`](https://arxiv.org/abs/2601.15621v1) | Official architecture; tokenizer; training; efficiency and evaluation claims |
| SRC-004 | S | [Qwen official Hugging Face collection](https://huggingface.co/collections/Qwen/qwen3-tts) | Released inventory only; not fixed revision proof |
| SRC-005 | S | [Qwen official ModelScope collection](https://modelscope.cn/collections/Qwen/Qwen3-TTS) | Released inventory only; not fixed revision proof |
| SRC-006 | S | [Tokenizer 12Hz HF commit `7dd38ad4e9bad454aae9cd937d0cd577604fe229`](https://huggingface.co/Qwen/Qwen3-TTS-Tokenizer-12Hz/commit/7dd38ad4e9bad454aae9cd937d0cd577604fe229) | Immutable Hugging Face asset revision |
| SRC-007 | S | [1.7B CustomVoice HF commit `0c0e3051f131929182e2c023b9537f8b1c68adfe`](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice/commit/0c0e3051f131929182e2c023b9537f8b1c68adfe) | Immutable Hugging Face asset revision |
| SRC-008 | S | [1.7B VoiceDesign HF commit `5ecdb67327fd37bb2e042aab12ff7391903235d3`](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign/commit/5ecdb67327fd37bb2e042aab12ff7391903235d3) | Immutable Hugging Face asset revision |
| SRC-009 | S | [1.7B Base HF commit `fd4b254389122332181a7c3db7f27e918eec64e3`](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-Base/commit/fd4b254389122332181a7c3db7f27e918eec64e3) | Immutable Hugging Face asset revision |
| SRC-010 | S | [0.6B CustomVoice HF commit `85e237c12c027371202489a0ec509ded67b5e4b5`](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice/commit/85e237c12c027371202489a0ec509ded67b5e4b5) | Immutable Hugging Face asset revision |
| SRC-011 | S | [0.6B Base HF commit `5d83992436eae1d760afd27aff78a71d676296fc`](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base/commit/5d83992436eae1d760afd27aff78a71d676296fc) | Immutable Hugging Face asset revision |
| SRC-012 | S | [Tokenizer 12Hz official ModelScope Git remote](https://www.modelscope.cn/Qwen/Qwen3-TTS-Tokenizer-12Hz.git) | `HEAD=d1d2fe2dbcbdc294f6962e5aa47ba394dc0cab07` by read-only `git ls-remote`; no stable commit permalink exposed |
| SRC-013 | S | [1.7B CustomVoice official ModelScope Git remote](https://www.modelscope.cn/Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice.git) | `HEAD=54dfa57e196341bfa4994c97ad1f0f874964eeab` by read-only `git ls-remote`; no stable commit permalink exposed |
| SRC-014 | S | [1.7B VoiceDesign official ModelScope Git remote](https://www.modelscope.cn/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign.git) | `HEAD=8dd530dbed7fda907a15ac48d7f78742cc90a065` by read-only `git ls-remote`; no stable commit permalink exposed |
| SRC-015 | S | [1.7B Base official ModelScope Git remote](https://www.modelscope.cn/Qwen/Qwen3-TTS-12Hz-1.7B-Base.git) | `HEAD=dfb4a462f62f8f831ff0ffabf31189fc9d4344fd` by read-only `git ls-remote`; no stable commit permalink exposed |
| SRC-016 | S | [0.6B CustomVoice official ModelScope Git remote](https://www.modelscope.cn/Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice.git) | `HEAD=70b274883e68023af521a9199603192d58ccdd3f` by read-only `git ls-remote`; no stable commit permalink exposed |
| SRC-017 | S | [0.6B Base official ModelScope Git remote](https://www.modelscope.cn/Qwen/Qwen3-TTS-12Hz-0.6B-Base.git) | `HEAD=fda1995a3162ad0488393cc366b82ca59c91c08e` by read-only `git ls-remote`; no stable commit permalink exposed |

所有架构事实优先回指固定源码树或 versioned official report；移动 collection 只用于发布清单交叉核对，逐资产 SHA 则回指 immutable Hugging Face commit URL 或经只读 `git ls-remote` 验证的 ModelScope official remote。搜索结果、社区教程、讨论区与本任务调查 handoff 均未作为本报告的事实来源。[SRC-001][SRC-002][SRC-003][SRC-004][SRC-005][SRC-006][SRC-007][SRC-008][SRC-009][SRC-010][SRC-011][SRC-012][SRC-013][SRC-014][SRC-015][SRC-016][SRC-017]
