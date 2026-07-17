# Ascend training candidate landscape

本报告记录截至 2026-07-17（Asia/Shanghai）的公开广度检索。事实只回指 `research/source-ledger.csv` 中的官方仓库、固定 commit、官方模型卡或官方生态入口；调查 handoff 和搜索结果只用于发现，不作为候选能力证据。没有下载权重或数据、clone/vendor 候选源码，也没有进行 CUDA/Ascend 真机验证。所有分数均为进入 Task 5 源码级深审前的 **preliminary** 分数。

## Search coverage

`research/search-log.csv` 保留原 Task 3 的 QRY-001–011，并新增 QRY-012–038。新增的 27 行均记录原样 query、实际入口、精确带时区时间、工具当次可见结果数、接纳 ID 与筛选边界；通用 Web 的 `result_count` 是返回材料中唯一可数的结果项，不是搜索引擎估算总命中数。GitHub API 的 1/0/0 是 API `total_count`，QRY-038 的 HTTP 401 失败以可见结果数 0 保留且不计入饱和轮次。

| 必需 query family | Query ID | 可见结果 | 本轮接纳 | 结论边界 |
| --- | --- | ---: | --- | --- |
| `Qwen3-TTS Ascend 910B training` | QRY-012 | 28 | CAND-001, CAND-006 | exact SFT 与 inference-only 线索均保留 |
| `Qwen TTS MindSpeed training Ascend` | QRY-013 | 24 | CAND-001 | exact public training 命中 CAND-001 |
| `speech generation TTS Ascend 910B training` | QRY-014 | 28 | CAND-006 | 910B 声明经核验只建立 inference 边界 |
| `audio tokenizer codec Ascend training` | QRY-015 | 23 | CAND-003, CAND-007, CAND-008, CAND-015 | architecture 线索入池；无训练链者明确拒绝，不推导 Ascend |
| `Qwen3 MindSpeed multi-node training` | QRY-016 | 20 | CAND-002 | 建立 text-Qwen3 scale satellite |
| `PyTorch TTS torch-npu distributed training` | QRY-017 | 26 | — | 无新增 eligible canonical repo |
| `Qwen 语音 合成 昇腾 训练` | QRY-018 | 25 | — | API、部署及二手材料不合格 |
| `Qwen3-TTS 昇腾 910B 训练` | QRY-019 | 26 | — | 已知候选与推理重复项 |
| `MindSpeed 语音生成 多机训练` | QRY-020 | 16 | — | MindSpeed-RL/非语音材料不补本轮角色 |

| 必需渠道 | Query ID | 覆盖内容 | 结果 |
| --- | --- | --- | --- |
| 华为官方 GitCode / hiascend | QRY-021, QRY-022, QRY-028, QRY-029, QRY-031 | exact Qwen3-TTS、环境、pretrain、speech ports | CAND-001 canonical；CAND-011 inference-only；8.5.2 仍无精确矩阵 |
| GitHub Web / API / fixed source | QRY-023, QRY-027, QRY-032, QRY-035–038 | 仓库、源码、零结果与失败 | 1/0/0 API 计数；401 失败保留；无新 eligible repo |
| Gitee | QRY-024 | Ascend 组织中文微调检索 | 旧生态/推理镜像；无新 eligible repo |
| ModelScope | QRY-025, QRY-030, QRY-033 | exact TTS、FSDP2、codec-scale | 模型卡不替代训练源码；无新 eligible repo |
| Hugging Face | QRY-026, QRY-034 | exact TTS Ascend、TTS FSDP2 | DSTK 进入拒绝表；无独立训练实现 |
| 通用中英文 Web | QRY-012–020 | 九个要求的 query families | 候选发现与跨渠道去重 |
| 源码、配置、测试、许可与提交 | SRC-019–046 | 固定树、launcher、optimizer/backward、config、checkpoint、baseline、license | 只用于资格初筛；Task 5 仍需完整源码级审计 |

未逐条重放的 handoff 历史检索没有伪造进 CSV；它们只作为调查过程背景。公开 Web 不能覆盖私有、删除、未索引或受限项目，因此“全网”只表示上述多渠道、可复查的系统检索。

## Search saturation

停止条件已满足，但不表示穷尽互联网：所有方法论必需渠道已有正式 query row，随后两轮 query-family pass 连续没有新增符合 inclusion rules 的 canonical repository。

| Pass | Query ID | 研究轴 | 可见结果数 | 新增 eligible canonical repo |
| --- | --- | --- | ---: | ---: |
| 1 | QRY-027 | CAND-001 optimizer/backward 源码增强 | 17 | 0 |
| 1 | QRY-028 | CANN 8.5.2 / PyTorch 2.7.1 精确兼容 | 16 | 0 |
| 1 | QRY-029 | exact Qwen3-TTS pretraining | 12 | 0 |
| 1 | QRY-030 | ModelScope exact FSDP2 | 12 | 0 |
| 2 | QRY-031 | GitCode CosyVoice3/MOSS-TTS ports | 3 | 0 |
| 2 | QRY-032 | GitHub MOSS-TTS `torch_npu` | 12 | 0 |
| 2 | QRY-033 | ModelScope codec + MindSpeed scale | 15 | 0 |
| 2 | QRY-034 | Hugging Face TTS + Ascend FSDP2 | 17 | 0 |

Pass 1 只增强 CAND-001 的已知路径并维持环境 unknown；Pass 2 只返回 CAND-001 内已有 ports、CAND-003 upstream、模型卡或研究轴不匹配材料。CAND-001 内的 MOSS-TTS/CosyVoice3 ports 是同一 canonical repo 的路径，不建立新候选，也不把 Ascend 分数重复授予 upstream CAND-003/CAND-004。QRY-038 因认证失败不参与任何 pass。

## Candidate categories

### Direct match

**CAND-001 — Ascend/MindSpeed-MM，shortlisted，90/100。** canonical 为 Ascend GitCode，官方 GitHub mirror 固定到 `0edd553e0ac9c912fe422c42cc9f42db9255ddcf`。exact Qwen3-TTS speaker SFT 训练链为 `finetune_qwen3tts.sh` → `torchrun`/HCCL/NPU → `trainer.py`/`TrainEngine` → forward/loss/`backward()` → AdamW/clip/step/scheduler/zero-grad；YAML 提供 FSDP、迭代和保存配置，DCP checkpoint 可转 HF，项目还记录了 ST loss/time/memory baseline。默认单机 8 NPU，脚本暴露 `NNODES`、`NODE_RANK`、`MASTER_ADDR`；这些只证明配置/框架能力，exact Qwen3-TTS 多机实跑仍是 unknown。[SRC-018][SRC-019][SRC-020][SRC-021][SRC-022][SRC-023][SRC-043]

CAND-001 只建立 **Qwen3-TTS SFT**，不建立 exact pretraining。文档的默认环境含 PyTorch/torch-npu 2.7.1 与 CANN 8.5.0；目标 CANN 8.5.2 是未证 patch 差异。根 LICENSE 含 BSD-3-Clause-style 条款与多上游 notices，但平台 SPDX 为 `NOASSERTION`，因此 CSV 保守写 `Other (aggregate...)`；若后续 vendor 源码，这是 major license risk，本阶段只保留元数据和链接。[SRC-020][SRC-024][SRC-028]

### Ascend-training-mature

**CAND-002 — Ascend/MindSpeed-LLM，shortlisted，82/100。** canonical 为 Ascend GitCode，mirror 固定到 `434baff794bd5594ebc9ed8a5b399110da9a44f0`。Qwen3 8B launcher 与 `pretrain_gpt.py`、训练 lifecycle、checkpoint lifecycle 共同建立 launch/config → forward/loss → backward/optimizer/scheduler → save/load/resume 链；脚本和固定树覆盖多种 dense/MoE Qwen3 规模、每节点 8 NPU 及多机参数。它补 pretraining、8 卡与多机工程，不是 Qwen3-TTS 或 speech/codec 直接支持。[SRC-025][SRC-026][SRC-027][SRC-044][SRC-045][SRC-046]

CAND-002 当前 release notes 已前移到 CANN 9.x，并列出部分 8.5.0 兼容组合，但没有 CANN 8.5.2 精确行；任何 8.5.2 兼容、多机稳定性、性能或精度结论均保持 unknown/待真机验证。根许可同样保守写 aggregate/Other，vendoring 风险与 CAND-001 相同。[SRC-028][SRC-029]

**CAND-005 — Ascend/ModelZoo-PyTorch speech recipes，discovered，47/100。** 固定官方 mirror 含 Tacotron2/FastPitch/WaveGlow/DeepSpeech 等历史 1p/8p recipes，能证明旧代 Ascend speech training 线索，但仓库迁移、子项目许可、依赖与 meaningful maintenance 需要逐目录复核；老版本/老架构与 PyTorch 2.7.1、CANN 8.5.2 差距过大，故不进入短名单。[SRC-034]

### Architecture-near

**CAND-003 — OpenMOSS/MOSS-TTS，shortlisted，60/100。** fixed revision `ad99ec5f26debf1d6c1a4dc8461b2bcb787ec9af` 含 Delay/Local/Realtime 的 SFT 与分布式配置；直接 SFT 文件建立 optimizer/backward/checkpoint 训练链，Apache-2.0 清晰。upstream 没有 Ascend 证据；CAND-001 内的 MOSS-TTS FSDP2 port 归 CAND-001，CAND-003 的 Ascend 完整度必须为 0。[SRC-030][SRC-031]

**CAND-010 — QwenLM/Qwen3-TTS target baseline，discovered，50/100。** fixed revision `022e286b98fbec7e1e916cb940cdf532cd9f488e` 是 exact architecture baseline，公开训练代码仅覆盖 CUDA-oriented 12Hz Base 单说话人 SFT；pretraining、DPO、GSPO、tokenizer training、单机 8 卡与多机均未公开建立。它不作为 Ascend 参考，只用于目标模块对齐。[SRC-001][SRC-002]

### Speech-specialist

**CAND-004 — FunAudioLLM/CosyVoice，shortlisted，51/100。** fixed revision `074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc` 的 `cosyvoice/bin/train.py` 建立 optimizer/backward/scheduler/checkpoint 与 distributed training 入口，Apache-2.0 清晰；upstream 自身无 Ascend 证据。CAND-001 的 CosyVoice3 port 只归 CAND-001，故 CAND-004 Ascend 分数为 0。[SRC-032][SRC-033]

**CAND-007 — jishengpeng/WavTokenizer，discovered，43/100；CAND-008 — ESPnet/espnet (ESPnet-Codec)，discovered，48/100。** 两者分别固定为 `5cf440d91ac420ca338f117b7003a77450d64730` 与 `6ed85c0c2be18e2699818b6c042b33ffb7adfa4d`，具有 codec/speech training 与许可价值，但无 Ascend 训练证据；CAND-007 最新可见 commit 停在 2025-03，CAND-008 过于宽泛，均不优于 CAND-003/CAND-004 的目标模块覆盖。[SRC-036][SRC-037]

### Rejected

CAND-006、009、011、012、013、014、015 均保留在 `candidates.csv`，避免后续重复发现。910B、NPU patch、export 或模型卡声明均不替代 optimizer/backward/launch/config/checkpoint 链。

## Qualification screening

| ID | Canonical / fixed revision | Owner | Training chain | Ascend evidence | Model / scale | License / docs | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CAND-001 | GitCode + `0edd553…` mirror | Ascend | exact Qwen3-TTS SFT complete | direct NPU/HCCL/FSDP2 | 1.7B; 8p config; multi-node run unknown | Other aggregate; strong docs | shortlist main |
| CAND-002 | GitCode + `434baff…` mirror | Ascend | Qwen3 pretrain/SFT complete | direct NPU/MindSpeed | dense/MoE; multi-node config/project claims | Other aggregate; strong docs | shortlist scale |
| CAND-003 | GitHub `ad99ec5…` | OpenMOSS | speech SFT complete | none upstream | 8-GPU configs | Apache-2.0; good docs | shortlist codec |
| CAND-004 | GitHub `074ca6d…` | FunAudioLLM | speech training complete | none upstream | distributed entry | Apache-2.0; good docs | shortlist speech |
| CAND-005 | GitHub `6a2804a…` mirror | Ascend | historical recipes; per-path deep audit pending | direct but stale | some 1p/8p | per-project license/freshness gap | discovered |
| CAND-006 | HF moving card | DiscreteSpeech | no public full chain found | 910B inference only | no training scale | Apache-2.0 card | rejected |
| CAND-007 | GitHub `5cf440d…` | jishengpeng | codec train/config | none | scale weak | MIT; stale | discovered |
| CAND-008 | GitHub `6ed85c0…` | ESPnet | mature speech/codec recipes | none | GPU distributed | Apache-2.0; broad | discovered |
| CAND-009 | GitHub `be517db…` | vLLM Project | serving only for this role | NPU inference | not training scale | Apache-2.0 | rejected |
| CAND-010 | GitHub `022e286…` | QwenLM | narrow single-speaker SFT | none | 8p/multi-node unknown | Apache-2.0; target docs | target baseline |
| CAND-011 | GitCode moving entry | Ascend | no full chain found | inference entry | not training scale | UNKNOWN | rejected |
| CAND-012 | Gitee moving entry | MindSpore | export/inference only | device inference | not training scale | Apache-2.0 repo | rejected |
| CAND-013 | Gitee moving entry | DeepSpark | no Qwen3-TTS training chain | inference inventory | text-Qwen training elsewhere | UNKNOWN | rejected |
| CAND-014 | ModelScope moving card | OpenBMB | QAT project claim; canonical tree unresolved | 910B/MindSpeed claim | non-speech | UNKNOWN | rejected |
| CAND-015 | GitHub `8c50ac4…` | OpenMOSS | public training chain absent | none | codec modeling/inference | Apache-2.0 | rejected |

对未进入 shortlist 的 moving-only rejected entries，本轮没有伪造 commit；其 revision 留空并在报告/CSV 明示边界。进入 shortlist 的四项均固定完整 commit。

## Preliminary score

分数用于广度排序，不等于 Task 5 审计结论。每个非零分数均通过 `evidence_ids` 回指至少一个 ledger 来源；CAND-003/CAND-004/CAND-007/CAND-008/CAND-010/CAND-015 的 Ascend 维度为 0，CAND-001 内 ports 不重复计分给 upstream。

| ID | Candidate | Ascend /30 | Architecture /25 | Scale /20 | Repro /15 | Docs/license /10 | Total | Evidence |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| CAND-001 | MindSpeed-MM | 29 | 25 | 15 | 14 | 7 | 90 | SRC-018–024, SRC-043 |
| CAND-002 | MindSpeed-LLM | 29 | 12 | 20 | 14 | 7 | 82 | SRC-025–029, SRC-044–046 |
| CAND-003 | MOSS-TTS | 0 | 23 | 13 | 14 | 10 | 60 | SRC-030–031 |
| CAND-004 | CosyVoice | 0 | 19 | 8 | 14 | 10 | 51 | SRC-032–033 |
| CAND-010 | Qwen3-TTS target | 0 | 25 | 1 | 14 | 10 | 50 | SRC-001–002 |
| CAND-008 | ESPnet/ESPnet-Codec | 0 | 18 | 7 | 14 | 9 | 48 | SRC-037 |
| CAND-005 | ModelZoo-PyTorch speech | 18 | 8 | 8 | 8 | 5 | 47 | SRC-034 |
| CAND-006 | DSTK | 8 | 20 | 2 | 8 | 8 | 46 | SRC-035 |
| CAND-007 | WavTokenizer | 0 | 21 | 5 | 10 | 7 | 43 | SRC-036 |
| CAND-015 | MOSS-Audio-Tokenizer | 0 | 18 | 0 | 8 | 10 | 36 | SRC-047 |
| CAND-009 | vLLM-Omni | 0 | 16 | 0 | 8 | 8 | 32 | SRC-038 |
| CAND-014 | BitCPM-CANN | 10 | 3 | 8 | 5 | 3 | 29 | SRC-042 |
| CAND-011 | Ascend-SACT | 0 | 16 | 0 | 5 | 3 | 24 | SRC-039 |
| CAND-012 | MindSpore Lite example | 0 | 10 | 0 | 4 | 7 | 21 | SRC-040 |
| CAND-013 | DeepSparkHub Qwen3-TTS | 0 | 12 | 0 | 4 | 3 | 19 | SRC-041 |

## Rejection table

| ID | Project | Explicit exclusion | Evidence |
| --- | --- | --- | --- |
| CAND-006 | DiscreteSpeech/DSTK | 项目卡声明 Ascend 910B 实验并给出 inference 环境，但未发现公开 optimizer/backward/launch/config/checkpoint 训练链 | SRC-035 |
| CAND-009 | vLLM-Omni | Qwen3-TTS NPU 路径属于 serving/inference；模型 patch 不等于训练 | SRC-038 |
| CAND-011 | Ascend-SACT Qwen3-TTS | 官方生态入口为 inference，未建立训练链；moving-only revision 不用于能力加分 | SRC-039 |
| CAND-012 | MindSpore Lite Qwen3-TTS | export/端侧推理示例，没有目标训练 lifecycle | SRC-040 |
| CAND-013 | DeepSparkHub Qwen3-TTS | inventory 将 Qwen3-TTS 放在 inference；训练条目是 text-only Qwen3 | SRC-041 |
| CAND-014 | BitCPM-CANN | 非 speech/codec 的 910B QAT 模型卡，canonical code tree 未解析；不优于 CAND-002 scale route | SRC-042 |
| CAND-015 | MOSS-Audio-Tokenizer | fixed public tree 只有 modeling、demo、ONNX/TensorRT export/inference；项目训练声明没有对应公开 optimizer/backward/launch/config/checkpoint 链 | SRC-047 |

二手 CSDN 部署文章、Qwen Cloud speech API、当前用户研究仓和无实质差异 mirrors 不是 canonical code candidates，因此不另分配候选 ID；其排除规则已由 QRY-018、QRY-019、QRY-035 的 notes 保留。

## Shortlist

1. **CAND-001 Ascend/MindSpeed-MM — main reference candidate。** 唯一发现且核实的 exact Qwen3-TTS + Ascend public training project；边界是 SFT，不是 exact pretraining。
2. **CAND-002 Ascend/MindSpeed-LLM — scale satellite。** 补 Qwen3 pretraining、MindSpeed、单机 8 卡与多机配置/lifecycle；不得宣称直接支持 Qwen3-TTS。
3. **CAND-003 OpenMOSS/MOSS-TTS — speech/codec architecture satellite。** 补 discrete-token TTS、多 codebook 与 speech SFT；Ascend 实现证据只归 CAND-001。
4. **CAND-004 FunAudioLLM/CosyVoice — speech specialist satellite。** 补语音数据预处理和训练对照；Ascend 实现证据只归 CAND-001。

Task 5 应完整审计 CAND-001/CAND-002；CAND-003/CAND-004 只审与 Qwen3-TTS target-module checklist 直接相关的 speech/codec 路径，避免重复审计 CAND-001 的 FSDP2/NPU 基础设施。

## Coverage gaps

- **环境冲突：** CAND-001 默认 CANN 8.5.0，CAND-002 当前正式路线已到 CANN 9.x；没有找到 CANN **8.5.2** + PyTorch 2.7.1 的精确官方 compatibility row。8.5.2 patch compatibility 保持 unknown，不从 8.5.0 外推。[SRC-020][SRC-028]
- **规模证据：** CAND-001 exact Qwen3-TTS 脚本有多机参数，但没有本轮可核实的模型专属多机实跑日志；CAND-002 的多机/性能属于源码配置与项目材料，不是本研究复现。两者的多机实跑均保持 unknown/待真机验证。[SRC-021][SRC-023][SRC-026][SRC-027]
- **训练阶段：** 公开 exact Qwen3-TTS pretraining、DPO、GSPO 和 tokenizer training 仍未找到；CAND-002 只能提供 text-Qwen3 scale 工程。不能把 architecture-near 迁移推断写成 speech pretraining 已证实。[SRC-001][SRC-020][SRC-027]
- **许可证：** CAND-001/CAND-002 均保守记录为 `Other` aggregate license，且含 file-level/third-party notices。若选中后要 clone/vendor 源码，必须单独升级合规决策；本阶段不 clone/vendor。[SRC-024][SRC-029]
- **移动或不可固定材料：** CAND-006、011–014 的公开入口未全部提供本轮可核实的 stable commit permalink；这些项目不进入 shortlist，revision 留空而不是猜测。GitHub code search QRY-038 因 HTTP 401 失败也明确保留。
- **维护差距：** CAND-005 的历史 speech recipes、CAND-007 的旧提交和 CAND-008 的宽仓范围需要更细粒度审计；本轮不以“曾有 8p”推导当前 CANN/PyTorch 可用。[SRC-034][SRC-036][SRC-037]
- **未做运行验证：** 没有真机训练、推理、精度、吞吐、稳定性或 checkpoint restore 复现；项目 baseline 与 performance 表都只按项目声明/源码材料处理。

关键冲突的保守结论是：公开证据改变了“没有 exact Ascend 项目”的先验——CAND-001 已提供 exact Qwen3-TTS SFT；但它没有消除 exact pretraining、CANN 8.5.2 或多机实跑缺口。

## Source index

完整字段、访问日和用途以 `research/source-ledger.csv` 为准；下表是 Task 4 使用的直接证据索引。

| Source ID | Direct official/fixed evidence | Primary use |
| --- | --- | --- |
| SRC-001–002 | QwenLM/Qwen3-TTS fixed tree/commit `022e286…` | target architecture and public-SFT boundary |
| SRC-018 | Ascend/MindSpeed-MM canonical GitCode | canonical owner |
| SRC-019 | MindSpeed-MM fixed tree `0edd553…` | immutable source boundary |
| SRC-020–023 | exact Qwen3-TTS guide, launcher, train engine, ST baseline | SFT and launch/backward/checkpoint evidence |
| SRC-024 | MindSpeed-MM fixed LICENSE | aggregate/Other license risk |
| SRC-025 | Ascend/MindSpeed-LLM canonical GitCode | canonical owner |
| SRC-026–029 | fixed tree, Qwen3 launcher, release notes, LICENSE | scale, environment and license boundaries |
| SRC-030–031 | MOSS-TTS fixed tree/SFT | speech/codec architecture and training |
| SRC-032–033 | CosyVoice fixed tree/train entry | speech specialist training |
| SRC-034 | ModelZoo-PyTorch fixed mirror | historical Ascend speech recipes |
| SRC-035 | DSTK official Hugging Face card | 910B inference-only exclusion |
| SRC-036 | WavTokenizer fixed tree | codec architecture and maintenance |
| SRC-037 | ESPnet fixed tree | codec/speech recipe maturity |
| SRC-038 | vLLM-Omni fixed tree | serving/inference exclusion |
| SRC-039 | Ascend-SACT canonical GitCode | inference-only exclusion |
| SRC-040 | MindSpore Lite canonical Gitee | export/inference exclusion |
| SRC-041 | DeepSparkHub canonical Gitee | inference inventory exclusion |
| SRC-042 | BitCPM-CANN official ModelScope card | non-speech scale exclusion |
| SRC-043 | MindSpeed-MM exact Qwen3-TTS YAML | optimizer/config/FSDP/checkpoint settings |
| SRC-044–046 | MindSpeed-LLM pretrain entry, training lifecycle, checkpoint lifecycle | forward/backward/optimizer/launch/checkpoint chain |
| SRC-047 | MOSS-Audio-Tokenizer fixed tree `8c50ac4…` | public-training-chain absence and inference/export rejection |
