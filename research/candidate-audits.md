# Shortlisted Ascend project source audits

本报告固定于 2026-07-17（Asia/Shanghai），审计四个 Task 4 shortlist 项目。只读取固定源码、官方文档、提交元数据与项目自产测试材料；没有下载权重或数据，没有 clone/vendor 候选仓库，也没有运行 CUDA、Ascend 910B、训练、推理、转换或评测。状态统一为：**已证实**（固定源码或官方材料直接支持）、**项目声明**（作者记录但本研究未复现）、**分析推断**（针对 Qwen3-TTS 的迁移判断）、**待真机验证**（包括所有 CANN 8.5.2 行为）。README 与项目 ST 不自动升级为独立复现。

## Candidate: Ascend/MindSpeed-MM (CAND-001)

### 1. Identity, canonical URL, fixed SHA, license, and maintenance status

- Canonical entry 是 `https://gitcode.com/Ascend/MindSpeed-MM`；审计源码固定为 Ascend 官方 GitHub mirror 的 `0edd553e0ac9c912fe422c42cc9f42db9255ddcf`，提交时间 `2026-07-16T06:53:03Z`。固定树近期活跃，但该提交是 Qwen3.5 prefetch 修复，不是 Qwen3-TTS 训练变更。[已证实；SRC-018, SRC-019, SRC-048]
- 2026-07-17 检索时 GitCode `master` 已指向 `de997c4db38da6eb6cca90571df23a89eff33105`，而本审计固定 GitHub snapshot 仍为 `0edd553...`。因此 **moving canonical ref 与 fixed mirror ref 已分叉**；这只证明 ref 不同，不证明两棵对象树等价或形成独立代码 fork，也不得把审计 SHA 静默移动到 canonical HEAD。[已证实；SRC-019, SRC-065]
- 固定 recursive tree 为完整返回且没有 Git submodule entry。[已证实；SRC-066]
- 根许可证是 BSD-3-Clause-style、Apache-2.0、MIT 与文件级 notices 的聚合边界，故 CSV 保守记为 `Other (aggregate BSD-3-Clause-style notices)`。本任务不批准整仓 vendor；以后复制文件必须逐文件核查 header、attribution 与第三方资产来源。[已证实/分析推断；SRC-024, SRC-071]

### 2. Claimed scope versus code-confirmed scope

固定树直接包含 Qwen3-TTS 12/25Hz 模型/processor/tokenizer 源码、12Hz speaker SFT 数据链、FSDP2 训练、NPU launcher 与 DCP 转换；guide 固定 upstream Qwen3-TTS revision `022e286...`。[已证实；SRC-019, SRC-020]

公开 exact route 只建立 1.7B Base 的 speaker SFT，不建立 Qwen3-TTS S1/S2/S3 预训练、DPO、GSPO、tokenizer training 或完整质量评测。8 卡来自 launcher/config 与项目 ST 组合，多机只有参数入口，均不能写成独立复现。[已证实/项目声明；SRC-020, SRC-021, SRC-023, SRC-043]

### 3. Repository tree and training entry points

```text
MindSpeed-MM@0edd553...
├── examples/qwen3tts/{README.md,process_data.py,prepare_data.py,
│   finetune_qwen3tts.sh,qwen3tts_config.yaml}
├── mindspeed_mm/fsdp/train/{trainer.py,train_engine.py}
├── mindspeed_mm/fsdp/data/datasets/qwen3tts/qwen3tts_dataset.py
├── mindspeed_mm/fsdp/models/qwen3tts/{core,inference,npu_patch.py}
├── mindspeed_mm/fsdp/{distributed,optimizer,checkpoint}/
├── checkpoint/fsdp/custom_model_converter/qwen3tts.py
└── tests/st/{run_configs,baseline_results}/finetune_qwen3tts*
```

训练控制流是 `finetune_qwen3tts.sh` → `torchrun` → FSDP `trainer.py` → `TrainEngine` → forward/loss/backward → clip/optimizer/scheduler/zero-grad → interval/final checkpoint。[已证实；SRC-021, SRC-022, SRC-043]

### 4. Ascend device initialization and torch-npu integration

launcher 加载 Ascend toolkit 环境，默认 8 个进程并暴露 rendezvous 参数。device abstraction 导入 `torch_npu`、选择 `npu`/`hccl`，训练入口按 local rank 设置设备并初始化 process group。[已证实；SRC-021, SRC-074]

Qwen3-TTS NPU patch 提供 RoPE 与 RMSNorm 替换面；固定源码存在不等于补丁调用边已完整证明，更不等于 CANN 8.5.2 数值/性能正确。[已证实/待真机验证；SRC-069]

### 5. MindSpeed/MindSpeed-LLM integration

guide 要求外部 clone/copy moving MindSpeed package，训练框架引用 `mindspeed.fsdp.*`。该依赖没有固定 SHA，形成复现漂移风险。exact launcher 设置 `NON_MEGATRON=true`，没有 `mindspeed_llm` route；应称为 **MindSpeed FSDP integration**，不能称为 MindSpeed-LLM/Megatron TP/PP pretraining。[已证实；SRC-020, SRC-021, SRC-022]

### 6. Operator, mixed-precision, and custom-extension handling

exact config 使用 BF16 参数、FP32 reduction、eager attention、`allow_hf32: false`；FSDP2 提供 mixed-precision policy 和 prefetch。RoPE/RMSNorm 走 torch-npu fused surface，小 shape RoPE 有 PyTorch fallback；未发现 exact route 的 GradScaler/autocast 或项目自有 Qwen3-TTS C++/AscendC extension。[已证实；SRC-043, SRC-068, SRC-069]

custom op 的 ABI、shape coverage、fallback 数值和 patch 调用必须在 910B + CANN 8.5.2 上验证。[待真机验证]

### 7. Data pipeline and audio-specific coverage

`prepare_data.py` 在 NPU 上物化 12Hz codec codes，但整文件读写、无 sharding/resume；dataset 构造 ChatML、24 kHz/128-bin mel、双通道 text/codec 输入、16 codebooks、mask/labels，并 all-reduce 全局最大长度后 padding。[已证实；SRC-067, SRC-073]

数据示例绑定 KAN-TTS/single-speaker 形态，未建立许可过滤、去重、验证集、长音频 bucketing、多语种/多说话人或中断恢复。[已证实；SRC-020, SRC-073]

### 8. DDP, TP, PP, CP, ZeRO, single-node, and multi-node coverage

| Mode | Fixed evidence | Audit state |
| --- | --- | --- |
| DDP | framework 在 FSDP size=1 时可用 | 已证实 generic；exact config 未走 DDP [SRC-068] |
| FSDP2 | `fully_shard`、BF16/FP32、prefetch、DCP | 已证实 exact config [SRC-043, SRC-068] |
| TP | generic device mesh；exact value 1 | generic only [SRC-068] |
| PP | exact route 无 stage/config | unknown |
| CP | generic ring/Ulysses；exact sizes 1 | generic only [SRC-019, SRC-043] |
| ZeRO | 无 DeepSpeed ZeRO route | absent |
| Single-node 8 NPU | launcher defaults 8；ST 是项目记录 | 配置已证实/项目声明 [SRC-021, SRC-023] |
| Multi-node | launcher 暴露 node/rendezvous 参数 | 配置已证实；模型实跑待真机 [SRC-021] |

### 9. Checkpoint, conversion, resume, inference, and evaluation

DCP 保存/恢复 model、optimizer、scheduler、dataloader、RNG 与 consumed samples；可同步/异步保存。custom converter 实现 DCP→HF、speaker id 3000 注入和 speaker encoder 权重删除，但 `hf_to_dcp()` 未实现。[已证实；SRC-070, SRC-072]

固定 exact example 没有合成音频 inference/eval launcher、converted-checkpoint smoke、WER/CER/SIM 或音质流水线；ST 只记录短训练 loss/time/memory。[已证实/项目声明；SRC-023]

### 10. Environment and version matrix

| Layer | Fixed evidence | Target comparison | State |
| --- | --- | --- | --- |
| Python | `>=3.10` | baseline 未另定 | 已证实 [SRC-071] |
| PyTorch | 2.7.1 | 2.7.1 | aligned [SRC-020, SRC-071] |
| torch-npu | guide-level paired route | 2.7.1 target family | packaging incomplete [SRC-020] |
| CANN | guide route 8.5.0 | **8.5.2** | **unknown; 不从 8.5.0 外推** [SRC-020] |
| Transformers | root 4.57.0；guide 4.57.3 | target varies | internal conflict [SRC-020, SRC-071] |
| MindSpeed | moving clone/copy | fixed dependency required | unknown SHA [SRC-020] |
| Device | NPU/HCCL path | Ascend 910B | exact SKU/log absent [SRC-021, SRC-074] |

### 11. Reproduction evidence and missing evidence

项目 ST JSON 记录 5 个 loss 点、迭代时间与内存，paired YAML 限制 5 iterations/50 samples；这是 **项目记录**，不是本研究复现。[项目声明；SRC-023, SRC-043]

缺失项包括 exact hardware SKU/count/topology、driver/CANN/torch-npu/MindSpeed SHA、完整 command/log/tolerance、checkpoint checksum、converted-model inference、audio quality、multi-node artifact。没有本研究运行材料。[待真机验证]

### 12. Score rationale for all five dimensions

| Dimension | Audited score | Source IDs and conservative rationale |
| --- | ---: | --- |
| Ascend completeness /30 | **27** | SRC-021, SRC-022, SRC-043, SRC-069, SRC-074：exact NPU/HCCL/FSDP2 SFT chain；扣 independent run、patch invocation/inference smoke、8.5.2 unknown。 |
| Architecture proximity /25 | **24** | SRC-019, SRC-020, SRC-067：exact 12/25Hz tree、16-codebook data 与 speaker SFT；扣公开 pretrain/DPO/GSPO/tokenizer training。 |
| Scale maturity /20 | **13** | SRC-021, SRC-043, SRC-068：8-process/FSDP2 与 generic TP/CP；扣 exact TP/CP>1、PP/ZeRO、模型多机实跑。 |
| Reproducibility /15 | **11** | SRC-019, SRC-020, SRC-023, SRC-065, SRC-071：fixed tree/guide/ST；扣 canonical/mirror ref 分叉、dependency/pin conflict、硬件与多机 artifact。 |
| Docs/license /10 | **6** | SRC-020, SRC-024, SRC-071：文档可用但 aggregate/file-level license、无统一 SPDX 与整仓 vendor 禁止。 |
| **Total** | **81/100** | preliminary 90 被源码级保守审计下调 9 分。 |

### 13. Reusable knowledge for Qwen3-TTS

| Target module | Reusable evidence | Transfer boundary |
| --- | --- | --- |
| Talker RoPE/RMSNorm | torch-npu replacement surface [SRC-069] | 需测 shape/dtype/numerics 与实际调用 |
| Speaker SFT | mel→speaker encoder→codec embedding [SRC-067] | KAN-TTS/single-speaker 边界 |
| 16-codebook collate | dual tracks/masks/codec-0 labels [SRC-067] | 与 target baseline 做逐字段一致性测试 |
| Variable length | distributed max-length padding [SRC-067] | 仍需 bucketing/sharding |
| BF16/FSDP2 | BF16 params + FP32 reduction [SRC-043, SRC-068] | 不是 AMP 全覆盖证据 |
| Checkpoint | full DCP state + DCP→HF [SRC-070, SRC-072] | HF→DCP 缺失；需 inference smoke |
| Speech breadth | same-repo MOSS/CosyVoice ports [SRC-019] | **只计 CAND-001，不回填 CAND-003/004** |

### 14. Non-transferable assumptions and risks

1. CANN 8.5.0 不能代表目标 8.5.2；所有融合算子 ABI、精度与性能保持 unknown。
2. `NON_MEGATRON=true` FSDP SFT 不建立 MindSpeed-LLM pretraining、TP/PP 或集群 scale-out。
3. KAN-TTS/single-speaker 数据不覆盖目标预训练、DPO、GSPO、tokenizer training、多语种与长上下文。
4. exposed multi-node variables 和项目 ST 不等于模型多机实跑。
5. DCP→HF 的 config/state mutation 需要 checksum 与 inference-equivalence 验证。
6. aggregate/file-level license 是重大合规风险；不得整仓 vendor。

### 15. Source index and claim-state summary

主要固定证据：identity/tree `SRC-018, SRC-019, SRC-048, SRC-065, SRC-066`；guide/launch/config/train `SRC-020, SRC-021, SRC-022, SRC-023, SRC-043`；data/device/FSDP/op/checkpoint `SRC-067, SRC-068, SRC-069, SRC-070, SRC-071, SRC-072, SRC-073, SRC-074`；license `SRC-024, SRC-071`。

| Claim state | Summary |
| --- | --- |
| 已证实 | fixed source chain、NPU/HCCL/FSDP2/DCP 接口、数据映射、8-process default |
| 项目声明 | ST loss/time/memory 与 guide 的运行成功含义 |
| 分析推断 | 对 target 模块的复用映射与 selective-copy 合规路线 |
| 待真机验证 | CANN 8.5.2、patch invocation/numerics、硬件 SKU、multi-node、conversion inference、质量与完整训练阶段 |

## Candidate: Ascend/MindSpeed-LLM (CAND-002)

### 1. Identity, canonical URL, fixed SHA, license, and maintenance status

- Canonical entry 是 `https://gitcode.com/Ascend/MindSpeed-LLM`；审计源码固定为官方 GitHub mirror `434baff794bd5594ebc9ed8a5b399110da9a44f0`，提交时间 `2026-07-16T09:26:04Z`，是 docs-only 变更。[已证实；SRC-025, SRC-026, SRC-049]
- 2026-07-17 检索时 canonical `master` 为 `2a545dd5dafba21d97b951af818b1646f538d247`，与 fixed mirror `434baff...` 不同；正式维护 refs 也需单独 pin。即 **canonical/mirror refs 已分叉**，不得声称 fixed snapshot 等于当前 canonical/formal branch HEAD。[已证实；SRC-026, SRC-075]
- fixed recursive tree 完整、无 Git submodule；安装依赖外部 moving MindSpeed、Megatron-LM 与 FSDPTurbo，并非 self-contained。[已证实；SRC-076, SRC-087]
- 根 LICENSE 与 third-party notice 是 aggregate/file-level 边界，CSV 保守记 `Other`；不批准 clone/vendor/整仓复制。[已证实/分析推断；SRC-029, SRC-086]

### 2. Claimed scope versus code-confirmed scope

固定树直接确认 text Qwen3 dense/MoE 的 pretrain、full SFT、LoRA、DPO、generation、text evaluation、data preprocessing、HF↔MCore conversion，以及独立 FSDP2 recipes。[已证实；SRC-077, SRC-078, SRC-080, SRC-081]

固定树没有 Qwen3-TTS、audio/codec/tokenizer、waveform/mel、speaker encoder 或 speech metric。它只能是 **text-Qwen3 scale satellite**；text Qwen scale 不得冒充 TTS direct support 或 speech pretraining。[已证实/分析边界；SRC-026, SRC-077, SRC-078]

### 3. Repository tree and training entry points

```text
MindSpeed-LLM@434baff...
├── pretrain_gpt.py / posttrain_gpt.py
├── inference.py / evaluation.py / convert_ckpt.py
├── examples/mcore/qwen3/{pretrain,tune,data,generate,evaluate,convert}*.sh
├── examples/mcore/qwen3_moe/{pretrain,tune,dpo,data,eval,convert}*.sh
├── examples/fsdp2/qwen3*/{*.sh,*.yaml}
└── mindspeed_llm/
    ├── training/{training,checkpointing}.py
    ├── tasks/{models,posttrain,evaluation}/
    ├── core/{tensor_parallel,pipeline_parallel,context_parallel,optimizer}/
    └── fsdp2/{models,data,train,checkpoint,inference}/
```

MCore launchers 通过 `torchrun` 进入 `pretrain_gpt.py`/`posttrain_gpt.py`，再接入 training/checkpoint lifecycle；FSDP2 是独立 shell/YAML/entry stack。入口和配置存在不等于每个规模在 fixed revision 已成功运行。[已证实；SRC-027, SRC-044, SRC-045, SRC-046, SRC-081, SRC-083]

### 4. Ascend device initialization and torch-npu integration

Qwen3 launcher 设置 HCCL/NPU allocator/ASD/task queue，默认每节点 8 NPU；MCore surface 保留 `nccl` 字面量。adaptor 实际导入 `torch_npu.contrib.transfer_to_npu` 并应用 MindSpeed patches，FSDP2 entry 在 NPU 路径显式选 `torch.npu`/`hccl`。[已证实；SRC-027, SRC-082, SRC-083]

这建立 NPU integration surface，不建立 CANN 8.5.2 可运行性或数值正确。[待真机验证]

### 5. MindSpeed/MindSpeed-LLM integration

Qwen3 recipe 使用仓内 Qwen3 layer spec、MCore model、MindSpeed fusion、distributed optimizer、gradient/parameter overlap 与 CoC；training/checkpoint lifecycle 在仓内实现。[已证实；SRC-027, SRC-044, SRC-045, SRC-046]

官方 install guide 另取 moving external repositories，fixed tree 没有用 submodule 固定这些依赖，因此实施前必须选 formal branch/revision 并重新审计依赖组合。[已证实/分析推断；SRC-076, SRC-087]

### 6. Operator, mixed-precision, and custom-extension handling

8B recipe 使用 BF16、loss scale、flash attention、fused RoPE/SwiGLU/RMSNorm、distributed optimizer 与 overlap。能力主要来自外部 MindSpeed/torch-npu 与 Python patch；fixed tree 的 setup 编译路径不提供一套可独立确认的完整 NPU custom-kernel 源码。[已证实；SRC-027, SRC-076, SRC-082]

fusion build、fallback、numerics 与性能均未在本研究运行，保持待真机验证。

### 7. Data pipeline and audio-specific coverage

Qwen3 pretraining 使用 text indexed dataset，SFT 使用 instruction/chat text，DPO 使用 pairwise text。没有 audio decode/resample、mel、codec codes、speaker prompt、speech length bucketing、waveform loss 或 TTS evaluation。[已证实；SRC-077, SRC-078]

可迁移的是离线 preprocess→indexed/packed dataset→distributed sampler/batch 的工程模式，不可复用其 text schema/loss 作为 TTS 数据实现。[分析推断]

### 8. DDP, TP, PP, CP, ZeRO, single-node, and multi-node coverage

| Mode | Fixed evidence | Audit state |
| --- | --- | --- |
| DDP | framework/FSDP2 可提供 data parallel | generic source-confirmed [SRC-081, SRC-083] |
| TP/PP/CP | MCore launchers显式暴露 | text-Qwen source-confirmed [SRC-027, SRC-079] |
| EP | MoE launcher配置 EP | text-MoE source-confirmed [SRC-078, SRC-079] |
| Distributed optimizer | MCore sharding/overlap | source-confirmed；不叫 DeepSpeed ZeRO [SRC-027] |
| ZeRO | 无证据将其标成 DeepSpeed ZeRO | terminology boundary |
| FSDP2 | 独立 Qwen3 route | source-confirmed [SRC-081, SRC-083] |
| Single-node 8 NPU | launcher default | 配置已证实；本研究未跑 [SRC-027] |
| Multi-node | 30B launcher为 2 nodes × 8 NPU | 配置已证实；项目运行结果未独立复现 [SRC-079] |

### 9. Checkpoint, conversion, resume, inference, and evaluation

固定树有 MCore checkpoint save/load、text Qwen HF↔MCore conversion、generation 与 CEval/MMLU 等 text evaluation；FSDP2 trainer/checkpoint manager 实现 model/optimizer/global-step/scheduler/RNG 与 DCP sync/async save/load。[已证实；SRC-046, SRC-077, SRC-084, SRC-085]

部分 MCore examples 使用 `--no-load-optim --no-load-rng`，因此示例 load 不等于 full-state fault-resume。所有 conversion/inference/eval 都是 text LLM，不是 TTS waveform 或 WER/CER/SIM。[已证实/分析边界；SRC-027, SRC-077]

### 10. Environment and version matrix

| Route | PyTorch | CANN | State |
| --- | --- | --- | --- |
| fixed master | 2.7.1 family | docs span 9.x/compatibility rows | development snapshot [SRC-028, SRC-087] |
| formal 26.0.0 | 2.7.1 | 9.0.0 | official project row [SRC-028] |
| formal 26.1.0 | 2.7.1 | 9.1.0 | official project row [SRC-028] |
| older compatibility | 2.7.1 family | includes 8.5.0 | project compatibility claim [SRC-028] |
| target | 2.7.1 | **8.5.2** | **no exact official row; unknown** [SRC-028] |

任何 8.5.0→8.5.2 patch compatibility 外推均被禁止。

### 11. Reproduction evidence and missing evidence

已有 fixed revision、launch/config、training/checkpoint/data/conversion/inference/eval entry 与项目 ST/performance 材料。缺失本研究的 910B single-node 8-card、multi-node、resume、conversion、precision、performance 与稳定性运行；没有权重/数据下载。[已证实边界；SRC-026, SRC-027, SRC-028, SRC-044, SRC-045, SRC-046]

尤其所有规模证据属于 text Qwen，不是 Qwen3-TTS。[分析边界]

### 12. Score rationale for all five dimensions

| Dimension | Audited score | Source IDs and conservative rationale |
| --- | ---: | --- |
| Ascend completeness /30 | **29** | SRC-027, SRC-044, SRC-045, SRC-046, SRC-082, SRC-083, SRC-084, SRC-085：NPU patch surface、fusion、BF16、optimizer/checkpoint 完整；扣无本研究真机。 |
| Architecture proximity /25 | **10** | SRC-077, SRC-078, SRC-080：Qwen3 transformer 与训练阶段邻近；**没有任何 audio/codec/speech direct coverage**。 |
| Scale maturity /20 | **20** | SRC-027, SRC-079, SRC-081, SRC-083, SRC-084, SRC-085：TP/PP/CP/EP、distributed optimizer、FSDP2、8p/2-node configs；此满分不表示 TTS scale 已跑。 |
| Reproducibility /15 | **14** | SRC-026, SRC-027, SRC-028, SRC-044, SRC-045, SRC-046, SRC-075, SRC-076, SRC-077, SRC-078, SRC-079, SRC-080, SRC-081, SRC-082, SRC-083, SRC-084, SRC-085, SRC-086, SRC-087：fixed entries/docs/lifecycle 广；扣 canonical/mirror drift、moving externals 与无独立运行。 |
| Docs/license /10 | **7** | SRC-028, SRC-029, SRC-086, SRC-087：文档强；aggregate/file-level license 和 dependency drift 限制复用。 |
| **Total** | **80/100** | preliminary 82 下调 2；角色保持 text-Qwen scale satellite。 |

### 13. Reusable knowledge for Qwen3-TTS

可迁移：rank/env/torchrun 模板、TP/PP/CP、distributed optimizer/overlap、checkpoint/resume 框架、HF↔MCore conversion 方法、BF16/fusion gating、Qwen3 Talker 主干映射、ST baseline 组织。[分析推断；SRC-027, SRC-044, SRC-045, SRC-046, SRC-077, SRC-079]

迁移前必须重证：dual-track text/codec、16-codebook MTP loss、speaker encoder、codec masks、audio length 与 checkpoint mapping 在 pipeline/CP/fusion 下的语义和数值。[待真机验证]

### 14. Non-transferable assumptions and risks

1. text causal-LM dataset/loss 不可替代 speech/codec/speaker path；MMLU/CEval 不可替代 TTS quality。
2. text Qwen conversion mapping 不可直接套 Talker/MTP/tokenizer/speaker encoder state dict。
3. text 8B/30B/235B/480B 配置或项目结果不证明 0.6B/1.7B Qwen3-TTS scale-out。
4. Megatron distributed optimizer 不能无条件改名为 DeepSpeed ZeRO；MCore/FSDP2 semantics 不同。
5. mirror/canonical refs 已分叉；实施必须重新 pin formal branch/revision。
6. aggregate license 禁止未经逐文件复核的 vendor；CANN 8.5.2、fusion 与多机均 unknown。

### 15. Source index and claim-state summary

主要固定证据：identity/ref/tree `SRC-025, SRC-026, SRC-049, SRC-075, SRC-076`；launch/lifecycle `SRC-027, SRC-044, SRC-045, SRC-046, SRC-077, SRC-078, SRC-079, SRC-080, SRC-081, SRC-082, SRC-083, SRC-084, SRC-085`；environment/install `SRC-028, SRC-087`；license `SRC-029, SRC-086`。

| Claim state | Summary |
| --- | --- |
| 已证实 | text Qwen entries、NPU integration、parallel configs、training/checkpoint code、aggregate notices |
| 项目声明 | ST/performance/scale run outcomes 与 compatibility operation |
| 分析推断 | 可迁移 scale framework、Qwen backbone mapping；不是 speech support |
| 待真机验证 | CANN 8.5.2、fusion numerics、single-node/multi-node stability、resume/conversion 与全部 TTS adaptation |

## Candidate: OpenMOSS/MOSS-TTS (CAND-003)

### 1. Identity, canonical URL, fixed SHA, license, and maintenance status

Canonical/fixed source 为 `OpenMOSS/MOSS-TTS@ad99ec5f26debf1d6c1a4dc8461b2bcb787ec9af`，提交时间 `2026-06-22T11:51:50Z`，主题为 local v1.5 fine-tuning，维护近期且与训练相关；根许可 Apache-2.0。[已证实；SRC-030, SRC-050]

固定 `.gitmodules` 声明 MOSS-Audio-Tokenizer submodule，但本研究没有独立恢复 gitlink 完整 SHA 或 release tags；submodule 保持独立固定/许可边界。[已证实/限制；SRC-088]

### 2. Claimed scope versus code-confirmed scope

固定源码包含 Delay/Local/Realtime speech generation 与直接 SFT；Delay 是 Qwen backbone、主 text head + 32 RVQ heads、24 kHz/12.5Hz、多 codebook Delay pattern 和 reference conditioning。[已证实；SRC-030, SRC-090, SRC-093]

长语音、WER/CER/SIM 与音质是项目声明；upstream 无 Ascend training code。[项目声明/已证实边界；SRC-030, SRC-090]

### 3. Repository tree and training entry points

目标路径是 `moss_tts_delay/{configuration,modeling,processing,inference_utils}.py` 与 `finetuning/{prepare_data,dataset,sft}.py`，配套 Accelerate DDP/FSDP/ZeRO-3 configs 和 launcher。`accelerate launch .../sft.py` 构造 AdamW/scheduler，执行 prepare→forward/loss→backward/clip/step/zero-grad→epoch save。[已证实；SRC-030, SRC-031, SRC-091, SRC-092, SRC-093]

### 4. Ascend device initialization and torch-npu integration

upstream 没有 torch-npu/CANN/HCCL/device patch，Ascend dimension 固定为 0。MindSpeed-MM 的 `examples/moss_tts` port 属于 **CAND-001**，不能回填或双计给 CAND-003。[已证实 attribution boundary；SRC-019, SRC-030, SRC-031]

### 5. MindSpeed/MindSpeed-LLM integration

upstream 无 MindSpeed/MindSpeed-LLM integration。MindSpeed-MM port 绑定另一 upstream revision `fd7dac7`，与本候选 `ad99ec5...` 不是同一固定树能力，只能作为 CAND-001 的迁移对照。[已证实；SRC-019, SRC-030]

### 6. Operator, mixed-precision, and custom-extension handling

runtime 以 CUDA wheel、FlashAttention 2 与 `torch.backends.cuda` 为主；训练支持 BF16/FP16、gradient checkpointing、Accelerate mixed precision，但无 NPU custom op/fallback。[已证实；SRC-089, SRC-090, SRC-091]

`channelwise_loss_weight` 可对 text 与 32 audio heads 分配权重；这可做实验设计参考，但不能替代 Qwen3-TTS codec-0 + residual MTP loss。[已证实/分析推断；SRC-030, SRC-093]

### 7. Data pipeline and audio-specific coverage

data preparation 用 Accelerate rank 信息分片，离线编码 target/reference audio codes 并输出 rank-suffixed JSONL；dataset 校验 `n_vq`，支持 reference codes/path/None、多说话人 teacher forcing、loss mask 与 padded labels。[已证实；SRC-092, SRC-093]

未见显式 audio-length bucketing/dynamic batching、数据许可过滤或 codec/tokenizer training lifecycle。[已证实边界；SRC-091, SRC-092, SRC-093]

### 8. DDP, TP, PP, CP, ZeRO, single-node, and multi-node coverage

固定材料覆盖 single GPU、8-GPU DDP、FSDP、DeepSpeed ZeRO-3，并文档化 Accelerate multi-machine 参数。没有 TP/PP/CP/MindSpeed；8-GPU 与 multi-node 是配置/项目能力说明，本研究无固定 run log。[已证实/项目声明；SRC-030, SRC-091]

### 9. Checkpoint, conversion, resume, inference, and evaluation

SFT 每 epoch 保存 safetensors 与 runtime/tokenizer/processor metadata，可用于 inference；没有 `resume`/optimizer restore，`global_step` 从 0 开始，故不是 fault-resume checkpoint。[已证实；SRC-031]

固定树有 Transformers inference 与部署路径；质量表缺少本研究可重放 raw outputs/eval pipeline，保持项目声明。[已证实/项目声明；SRC-030, SRC-090]

### 10. Environment and version matrix

`pyproject` 要求 Python `>=3.10`；项目材料推荐 Python 3.12、CUDA 12.8、PyTorch/Torchaudio 2.9.1、Transformers 5.0.0 与 Accelerate/DeepSpeed/FlashAttention。目标是 PyTorch 2.7.1 + CANN 8.5.2，device/runtime 有实质错位；CANN 8.5.2 行为 unknown。[已证实/分析推断；SRC-089, SRC-090, SRC-091]

### 11. Reproduction evidence and missing evidence

已有 fixed source、SFT guide、pins、single/DDP/FSDP/ZeRO-3 configs、launcher 与可加载 checkpoint layout。缺失 upstream Ascend/910B/torch-npu/HCCL、独立 run、raw logs/eval outputs、完整 resume 与 submodule full SHA；未下载权重/数据。[已证实边界；SRC-030, SRC-031, SRC-088, SRC-089, SRC-090, SRC-091, SRC-092, SRC-093]

### 12. Score rationale for all five dimensions

| Dimension | Audited score | Source IDs and conservative rationale |
| --- | ---: | --- |
| Ascend completeness /30 | **0** | SRC-019, SRC-030, SRC-031：upstream 无 NPU；MindSpeed-MM port 只归 CAND-001。 |
| Architecture proximity /25 | **23** | SRC-030, SRC-090, SRC-093：Qwen/discrete audio/32-codebook Delay/reference/SFT 接近；生成 topology 不同。 |
| Scale maturity /20 | **13** | SRC-031, SRC-091：DDP/FSDP/ZeRO-3、8-GPU/multi-machine configs；无 TP/PP/CP/MindSpeed/run log。 |
| Reproducibility /15 | **13** | SRC-030, SRC-031, SRC-050, SRC-088, SRC-089, SRC-090, SRC-091, SRC-092, SRC-093：fixed code/pins/data/checkpoint 强；扣 no resume、submodule full SHA、raw run/eval。 |
| Docs/license /10 | **10** | SRC-030, SRC-088, SRC-089, SRC-090, SRC-091：Apache-2.0 与文档强；submodule 仍保持单独许可边界。 |
| **Total** | **59/100** | preliminary 60 下调 1：full resume/raw evidence 不足。 |

### 13. Reusable knowledge for Qwen3-TTS

可迁移：rank-sharded codec materialization、reference/None conditioning、multi-head/channel loss、Delay pattern 对照、Accelerate DDP/FSDP/ZeRO-3 wrapping、self-contained inference assets。[分析推断；SRC-031, SRC-092, SRC-093]

不可直接迁移：32-head same-step topology、Qwen-8B-scale config、CUDA attention、无 resume 保存策略。

### 14. Non-transferable assumptions and risks

MOSS 的 32 RVQ heads/12.5Hz Delay 与 Qwen3-TTS 16 codebooks、codec-0 Talker + residual MTP 不等价；prompt/schema/weights/loss/sampling/decoder 不可互换。CUDA 2.9.1/FlashAttention/DeepSpeed configs 不证明 PyTorch 2.7.1/CANN 8.5.2 可用。upstream 无 Ascend training，MindSpeed-MM port 不双计。[分析推断/待真机验证]

### 15. Source index and claim-state summary

主要固定证据：tree/commit `SRC-030, SRC-050`；SFT/data `SRC-031, SRC-091, SRC-092, SRC-093`；dependency/submodule `SRC-088, SRC-089`；model guide `SRC-090`。

| Claim state | Summary |
| --- | --- |
| 已证实 | speech SFT/data/checkpoint/config 源码、Apache-2.0、submodule declaration |
| 项目声明 | long-form/quality metrics 与 multi-machine operation |
| 分析推断 | Delay/multi-head/reference 迁移价值 |
| 待真机验证 | 全部 Ascend/CANN 8.5.2 行为、distributed run、quality 与完整 resume |

## Candidate: FunAudioLLM/CosyVoice (CAND-004)

### 1. Identity, canonical URL, fixed SHA, license, and maintenance status

Canonical/fixed source 为 `FunAudioLLM/CosyVoice@074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc`，提交时间 `2026-05-25T18:15:40Z`，主题为 ecosystem links；仓库活跃但该 fixed HEAD 不是训练变更。根许可 Apache-2.0。[已证实；SRC-032, SRC-051]

`.gitmodules` 声明 Matcha-TTS submodule；本研究没有独立解析其 full SHA。根许可证不自动覆盖 submodule/资产，故 docs/license 保守扣 1。[已证实/分析边界；SRC-094]

### 2. Claimed scope versus code-confirmed scope

固定源码直接包含 LLM→discrete speech token、flow acoustic model、HiFT/HiFiGAN waveform path，以及 DDP/DeepSpeed、SFT/DPO、checkpoint/scheduler/data/export 入口。README 的 CER/WER/SIM 排名是项目声明；upstream 无 Ascend training evidence。[已证实/项目声明；SRC-032, SRC-033, SRC-096, SRC-097, SRC-098, SRC-099]

### 3. Repository tree and training entry points

目标路径为 `cosyvoice/bin/train.py`、`cosyvoice/dataset/{dataset,processor}.py`、`cosyvoice/llm/llm.py`、`cosyvoice/{flow,hifigan}` 与 `examples/libritts/cosyvoice3/{run.sh,conf}`。staged recipe 展开 manifest→embedding/token→parquet→torchrun train→checkpoint average→JIT/ONNX export。[已证实；SRC-033, SRC-096, SRC-097, SRC-098, SRC-099]

### 4. Ascend device initialization and torch-npu integration

upstream 无 torch-npu/CANN/HCCL/NPU patch，Ascend dimension 固定 0。MindSpeed-MM `examples/cosyvoice3` 是 CAND-001 的 FSDP2/NPU port，不归因、不得双计给 CAND-004。[已证实 attribution boundary；SRC-019, SRC-032, SRC-033]

### 5. MindSpeed/MindSpeed-LLM integration

upstream 没有 MindSpeed/MindSpeed-LLM integration；MindSpeed-MM port 只能作为独立迁移对照，不回填本候选 capability 或 score。[已证实；SRC-019, SRC-032]

### 6. Operator, mixed-precision, and custom-extension handling

train entry 默认 `nccl`、CUDA model wrapper 与 CUDA GradScaler；requirements 固定 CUDA wheels、onnxruntime-gpu/TensorRT。AMP 与 DeepSpeed stage 2 可选，但无 NPU fallback/custom op。[已证实；SRC-033, SRC-095]

LLM 使用 discrete speech-token CE/accuracy 并有 DPO path；flow/HiFiGAN 是不同目标，不能外推为 Qwen3-TTS 的统一多-codebook loss。[已证实/分析边界；SRC-099]

### 7. Data pipeline and audio-specific coverage

recipe 生成 Kaldi manifests，离线抽取 speaker embedding 与 ONNX speech tokens，以 parquet 分片；dataset 按 rank/world-size/worker partition，processor 提供 frame-budget dynamic batch、length sort/pad、Whisper features、speaker embeddings 与 tokens。[已证实；SRC-096, SRC-097, SRC-098]

prompt text/speech/embedding 与 mix-ratio 是 reference-conditioning 对照；speech tokenizer 作为预训练 extractor 使用，没有 tokenizer/codec training lifecycle。[已证实/分析推断；SRC-032, SRC-096, SRC-099]

### 8. DDP, TP, PP, CP, ZeRO, single-node, and multi-node coverage

fixed entry 支持 DDP 与 DeepSpeed stage 2、rank sampler、AMP/NCCL/torchrun；recipe 默认 `CUDA_VISIBLE_DEVICES=0`、`nnodes=1`。没有 FSDP、ZeRO-3、TP/PP/CP/MindSpeed 或固定 8-GPU/multi-node log，因此规模分只承认 distributed code surface。[已证实边界；SRC-033, SRC-096]

### 9. Checkpoint, conversion, resume, inference, and evaluation

train entry 可加载 model checkpoint 并恢复 step/epoch/scheduler；DDP path 未建立 optimizer restore，DeepSpeed 可保存 model+optimizer。recipe 包含 best-checkpoint averaging 与 JIT/ONNX export。[已证实；SRC-033, SRC-096]

recipe 文本称仅支持 LLM training，但脚本又循环 llm/flow/hifigan，存在文档/脚本张力；不能无运行证据声称三阶段均跑通。质量表没有本研究 raw outputs/eval replay。[已证实/项目声明；SRC-032, SRC-096]

### 10. Environment and version matrix

fixed requirements 使用 CUDA 12.1 index，pins PyTorch/Torchaudio 2.3.1、Transformers 4.51.3、DeepSpeed 0.15.1、ONNX Runtime GPU 与 TensorRT。它与 PyTorch 2.7.1/CANN 8.5.2 有实质 device/version 差异，所有 target compatibility 均 unknown。[已证实/待真机验证；SRC-095]

### 11. Reproduction evidence and missing evidence

已有 fixed source、LibriTTS staged recipe、CUDA pins、DDP/DeepSpeed args、dynamic batching、checkpoint average/export 与公开质量表。缺失 upstream Ascend/910B/torch-npu/HCCL、8-GPU/multi-node logs、完整 DDP optimizer resume、raw eval outputs、本研究独立运行与 submodule full SHA。未下载权重/数据。[已证实边界；SRC-032, SRC-033, SRC-094, SRC-095, SRC-096, SRC-097, SRC-098, SRC-099]

### 12. Score rationale for all five dimensions

| Dimension | Audited score | Source IDs and conservative rationale |
| --- | ---: | --- |
| Ascend completeness /30 | **0** | SRC-019, SRC-032, SRC-033：upstream 无 NPU；MindSpeed-MM port 只归 CAND-001。 |
| Architecture proximity /25 | **19** | SRC-032, SRC-097, SRC-098, SRC-099：discrete speech token、prompt/reference、flow/vocoder/data；无 Qwen3-TTS 16-codebook MTP 同构。 |
| Scale maturity /20 | **8** | SRC-033, SRC-096, SRC-098：DDP/DeepSpeed stage 2/rank sampler；无 8-GPU/multi-node/FSDP/TP/PP/CP/MindSpeed evidence。 |
| Reproducibility /15 | **13** | SRC-032, SRC-033, SRC-051, SRC-095, SRC-096, SRC-097, SRC-098, SRC-099：fixed staged recipe/pins/checkpoint/export；扣 partial resume、default 1 GPU、raw logs 与 recipe 张力。 |
| Docs/license /10 | **9** | SRC-032, SRC-094, SRC-095, SRC-096：根 Apache-2.0 与文档强；submodule/assets 仍需独立许可核查。 |
| **Total** | **49/100** | preliminary 51 下调 2：resume 与 license/reproduction 证据比初审更弱。 |

### 13. Reusable knowledge for Qwen3-TTS

可迁移：Kaldi→embedding/token→parquet stages、rank/worker partition、frame-budget dynamic batching、prompt text/speech/embedding、discrete-token CE/DPO lifecycle、checkpoint averaging/export 与 CER/WER/SIM 评估设计。[分析推断；SRC-096, SRC-097, SRC-098, SRC-099]

不可直接迁移：单 speech-token vocabulary、flow/HiFT/HiFiGAN decoder、CUDA AMP/NCCL/DeepSpeed assumptions 与预训练 tokenizer assets。

### 14. Non-transferable assumptions and risks

CosyVoice 的 tokenizer、single-token LM/flow/vocoder、mix-ratio prompt 与 Qwen3-TTS Talker/MTP/16-codebook causal tokenizer 不等价。DDP partial resume、DeepSpeed stage 2、CUDA 2.3.1 stack 均不能证明目标 FSDP2/MindSpeed/CANN 8.5.2 行为。MindSpeed-MM CosyVoice port 不双计。[分析推断/待真机验证]

### 15. Source index and claim-state summary

主要固定证据：tree/commit `SRC-032, SRC-051`；train/data/model `SRC-033, SRC-096, SRC-097, SRC-098, SRC-099`；dependency/submodule `SRC-094, SRC-095`。

| Claim state | Summary |
| --- | --- |
| 已证实 | staged data/train/checkpoint/export source、DDP/DeepSpeed surface、Apache-2.0/submodule declaration |
| 项目声明 | quality tables、multi-stage success 与运行结果 |
| 分析推断 | dynamic batching/prompt/eval 对 target 的迁移价值 |
| 待真机验证 | 全部 Ascend/CANN 8.5.2 行为、8-card/multi-node、resume、quality 与 TTS semantic adaptation |

# Cross-candidate target-module comparison and Task 6 decision

审计总分排序是 CAND-001 **81**、CAND-002 **80**、CAND-003 **59**、CAND-004 **49**。CAND-001 与 CAND-002 只差 1 分，却代表实质不同路线：前者是 exact Qwen3-TTS Ascend/FSDP SFT，后者是 text-Qwen3 MindSpeed/MCore scale engineering。按 methodology，这不是可由总分静默解决的 tie，而是 **Task 6 major decision**；Task 5 不推荐最终主/卫星组合。[SRC-019, SRC-020, SRC-026, SRC-027]

| Qwen3-TTS target checklist group | CAND-001 | CAND-002 | CAND-003 | CAND-004 | Remaining gap |
| --- | --- | --- | --- | --- | --- |
| Talker/Qwen3/RoPE/attention | exact model + NPU patch | text-Qwen scale/fusion | Qwen-style Delay contrast | discrete-token LLM contrast | CANN 8.5.2 numerics/perf |
| codec-0 + residual MTP / 16 codebooks | exact data/model tree | none | 32-head Delay comparison | single-token comparison | exact distributed MTP tests |
| speaker encoder/reference paths | exact SFT mel path | none | reference/None conditioning | prompt text/speech/embedding | multi-speaker/pretrain coverage |
| offline codec/data/collate | exact materialization + masks but no resume/shard | text indexed-data pattern only | rank-sharded codes | parquet + dynamic batching | licensed data/bucketing/resume |
| BF16/operator abstraction | exact FSDP2 BF16 + torch-npu surfaces | mature fusion framework | CUDA mixed precision | CUDA AMP | 910B fallback/numerical matrix |
| checkpoint/conversion/resume | full DCP + one-way HF export | mature text lifecycle | inference-ready save no resume | partial resume + export | TTS conversion smoke/fault restore |
| single-node 8-card/multi-node | 8p default; multi-node params only | mature text configs | GPU configs only | default 1 GPU | exact Qwen3-TTS run artifacts |
| pretrain/DPO/GSPO/tokenizer training | absent exact | text pretrain/DPO only | SFT only | speech-token DPO contrast | all exact public stages absent |
| eval WER/CER/SIM/tokenizer quality | ST loss only | text metrics only | project tables | project tables/design | executable fixed eval + raw outputs |

因此 Task 6 必须显式选择学习路线：以 CAND-001 为 exact implementation anchor 并用 CAND-002 补 scale，或以 CAND-002 的 MCore scale architecture 为主工程并承担更大的 TTS semantic port。无论选择哪条路线，CANN 8.5.2、exact multi-node、完整训练阶段与许可处理仍是 hard gaps；MOSS/CosyVoice 的 MindSpeed-MM ports 只计 CAND-001，不能双计为 upstream Ascend 能力。
