# Ascend training candidate landscape

本报告记录截至 2026-07-17（Asia/Shanghai）的公开广度检索。事实只回指 `research/source-ledger.csv` 中的官方仓库、固定 commit、官方模型卡或官方生态入口；调查 handoff 和搜索结果只用于发现，不作为候选能力证据。没有下载权重或数据、clone/vendor 候选源码，也没有进行 CUDA/Ascend 真机验证。所有分数均为进入 Task 5 源码级深审前的 **preliminary** 分数。

## Search coverage

`research/search-log.csv` 保留 QRY-001–038 的全部历史，并在审阅修复中追加至 QRY-121。QRY-012–020 是九个 family 的 general-Web 原始行；QRY-039–083 补齐其余五个渠道的 45 个矩阵单元。每行保存原样 query、实际入口、精确带时区时间、可观察结果数和限制。filtered-Web `result_count` 是唯一可数的 tool-visible item 数，不是平台/搜索引擎总量；GitHub QRY-075–083、092–093、095–121 使用 native repository Search API 的精确 `total_count`。

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

### Complete query-family × channel matrix

| Family | General Web | Huawei official | GitHub native API | Gitee | ModelScope | Hugging Face |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen3-TTS Ascend 910B training | QRY-012 | QRY-039 | QRY-075 | QRY-048 | QRY-057 | QRY-066 |
| Qwen TTS MindSpeed training Ascend | QRY-013 | QRY-040 | QRY-076 | QRY-049 | QRY-058 | QRY-067 |
| speech generation TTS Ascend 910B training | QRY-014 | QRY-041 | QRY-077 | QRY-050 | QRY-059 | QRY-068 |
| audio tokenizer codec Ascend training | QRY-015 | QRY-042 | QRY-078 | QRY-051 | QRY-060 | QRY-069 |
| Qwen3 MindSpeed multi-node training | QRY-016 | QRY-043 | QRY-079 | QRY-052 | QRY-061 | QRY-070 |
| PyTorch TTS torch-npu distributed training | QRY-017 | QRY-044 | QRY-080 | QRY-053 | QRY-062 | QRY-071 |
| Qwen 语音 合成 昇腾 训练 | QRY-018 | QRY-045 | QRY-081 | QRY-054 | QRY-063 | QRY-072 |
| Qwen3-TTS 昇腾 910B 训练 | QRY-019 | QRY-046 | QRY-082 | QRY-055 | QRY-064 | QRY-073 |
| MindSpeed 语音生成 多机训练 | QRY-020 | QRY-047 | QRY-083 | QRY-056 | QRY-065 | QRY-074 |

矩阵共 9×6=54 个实际查询单元。华为、Gitee、ModelScope、Hugging Face 没有本任务可用的稳定 native search contract，因此采用 exact domain-filtered fallback 并逐行注明限制；GitHub 使用 native API。QRY-039–047 的零值是该 fallback 的零个 tool-visible items，不宣称平台全局零命中。

### Candidate discovery provenance repair

| Candidate | Replay query | Observable count | accepted_ids |
| --- | --- | ---: | --- |
| CAND-004 CosyVoice | QRY-084 | 18 tool-visible | CAND-004 |
| CAND-005 ModelZoo-PyTorch | QRY-085 | 15 tool-visible | CAND-005 |
| CAND-009 vLLM-Omni | QRY-086 | 17 tool-visible | CAND-009 |
| CAND-012 MindSpore Lite | QRY-087 | 14 tool-visible | CAND-012 |
| CAND-013 DeepSparkHub | QRY-088 | 15 tool-visible | CAND-013 |
| CAND-014 BitCPM-CANN | QRY-089 | 15 tool-visible | CAND-014 |

这些是独立的 discovery-provenance replay，不把 coverage 单元静默改写成候选发现历史。历史 QRY-001–083 原样保留。

### Remediation discovery reset

完成 54 单元矩阵、canonical 和 maintenance 初审后，QRY-090–094 对新线索做了可复查回放。QRY-092 接纳 CAND-016 Inworld TTS：其固定树包含 SpeechLM/codec pretrain、SFT、RLHF、DDP/DeepSpeed/FSDP、optimizer 与 checkpoint 生命周期，但仅验证 CUDA。QRY-093 接纳 CAND-017 Alibaba unified-audio：其固定树包含 audio-tokenizer/codec 配置与 UniSE 训练入口，但无 Ascend 训练证据。两项新增使此前连续零新增计数归零。[SRC-057][SRC-058][SRC-059][SRC-060]

QRY-094 同时筛查了社区 `gcw_coj3XaOd/GLM-TTS`：项目自身把 910B 改造限定为端到端推理，并将 tokenizer/vocoder 回退 CPU；未建立独立 optimizer/backward/checkpoint 训练链，故按 inclusion rules 不接纳为训练候选。QRY-090–091 的 filtered-Web 回放未直接返回目标 canonical，保留为带限制的探索记录，不计入饱和证据。

未逐条重放且没有精确可观察计数的 handoff 历史检索没有伪造进 CSV；它们只作为调查过程背景。公开 Web 不能覆盖私有、删除、未索引或受限项目，因此“全网”只表示上述多渠道、可复查的系统检索。

## Search saturation

QRY-027–034 是原 Task 4 的历史两轮记录。审阅修复后的重跑先发现 CAND-016/CAND-017，又在 QRY-097 发现 CAND-018，因此历史零新增结论和 QRY-095–103 attempt 都不能作为新停止条件。新的两轮 9-family saturation pass 将在 18 项候选 canonical/maintenance 审计完成后执行；只有成功返回并完成去重的查询才可计零新增。

18-candidate 基线完成 canonical/maintenance 审计后，两轮新的 pass 已连续完成且零新增：QRY-104–112 和 QRY-113–121 各覆盖全部九个 family，18 个查询均为成功的 GitHub native repository API 响应，`incomplete_results=false`；没有失败或 auth-gated query 被计为零新增。

| New pass | Query IDs | Family cells | API-visible results | New eligible canonical repos |
| --- | --- | ---: | ---: | ---: |
| 1 | QRY-104–112 | 9/9 | 0 | 0 |
| 2 | QRY-113–121 | 9/9 | 12 | 0 |

pass 2 的 12 个结果由 10 个 awesome-list/index/unrelated repositories 和两个已筛过的 LMSV text-Qwen copies 构成；它们不新增 speech、Ascend training 或独立 scale 角色。停止结论因此是：在已记录的 54-cell 多渠道矩阵、18-candidate canonical/maintenance 基线和两轮新 GitHub native query-family pass 下达到公开检索饱和，不表示穷尽私有、删除、未索引或受限项目。

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

历史 Pass 1 只增强 CAND-001 的已知路径并维持环境 unknown；历史 Pass 2 只返回当时已知 ports/upstream/模型卡。CAND-001 内的 MOSS-TTS/CosyVoice3 ports 是同一 canonical repo 的路径，不建立新候选，也不把 Ascend 分数重复授予 upstream CAND-003/CAND-004。QRY-038 因认证失败不参与任何 pass；QRY-092–093 和 QRY-097 的新增候选均将连续零新增计数归零。

## Candidate categories

### Direct match

**CAND-001 — Ascend/MindSpeed-MM，shortlisted，90/100。** canonical 为 Ascend GitCode，官方 GitHub mirror 固定到 `0edd553e0ac9c912fe422c42cc9f42db9255ddcf`。exact Qwen3-TTS speaker SFT 训练链为 `finetune_qwen3tts.sh` → `torchrun`/HCCL/NPU → `trainer.py`/`TrainEngine` → forward/loss/`backward()` → AdamW/clip/step/scheduler/zero-grad；YAML 提供 FSDP、迭代和保存配置，DCP checkpoint 可转 HF，项目还记录了 ST loss/time/memory baseline。默认单机 8 NPU，脚本暴露 `NNODES`、`NODE_RANK`、`MASTER_ADDR`；这些只证明配置/框架能力，exact Qwen3-TTS 多机实跑仍是 unknown。[SRC-018][SRC-019][SRC-020][SRC-021][SRC-022][SRC-023][SRC-043]

CAND-001 只建立 **Qwen3-TTS SFT**，不建立 exact pretraining。文档的默认环境含 PyTorch/torch-npu 2.7.1 与 CANN 8.5.0；目标 CANN 8.5.2 是未证 patch 差异。根 LICENSE 含 BSD-3-Clause-style 条款与多上游 notices，但平台 SPDX 为 `NOASSERTION`，因此 CSV 保守写 `Other (aggregate...)`；若后续 vendor 源码，这是 major license risk，本阶段只保留元数据和链接。[SRC-020][SRC-024][SRC-028]

### Ascend-training-mature

**CAND-002 — Ascend/MindSpeed-LLM，shortlisted，82/100。** canonical 为 Ascend GitCode，mirror 固定到 `434baff794bd5594ebc9ed8a5b399110da9a44f0`。Qwen3 8B launcher 与 `pretrain_gpt.py`、训练 lifecycle、checkpoint lifecycle 共同建立 launch/config → forward/loss → backward/optimizer/scheduler → save/load/resume 链；脚本和固定树覆盖多种 dense/MoE Qwen3 规模、每节点 8 NPU 及多机参数。它补 pretraining、8 卡与多机工程，不是 Qwen3-TTS 或 speech/codec 直接支持。[SRC-025][SRC-026][SRC-027][SRC-044][SRC-045][SRC-046]

CAND-002 当前 release notes 已前移到 CANN 9.x，并列出部分 8.5.0 兼容组合，但没有 CANN 8.5.2 精确行；任何 8.5.2 兼容、多机稳定性、性能或精度结论均保持 unknown/待真机验证。根许可同样保守写 aggregate/Other，vendoring 风险与 CAND-001 相同。[SRC-028][SRC-029]

**CAND-005 — Ascend/ModelZoo-PyTorch speech recipes，discovered，47/100。** authoritative upstream 已修正为 GitCode，当前 HEAD `c9d4e7dc8a951fb9365e5ebe42601b0101d34ba3`；GitHub `6a2804a358a5b18e3dac1ab902f41f88e240b00f` 只保留为固定 mirror，两个 HEAD 不同且不假设 commit 等价。mirror 含 Tacotron2/FastPitch/WaveGlow/DeepSpeech 等历史 1p/8p recipes；canonical 当前仍活跃，但最新变更是非 speech 的 ICAA，因此 speech recipe maintenance 仍偏旧。根规则是 Apache-2.0 default、模型目录可覆盖，故不进入短名单。[SRC-034][SRC-052]

### Architecture-near

**CAND-003 — OpenMOSS/MOSS-TTS，shortlisted，60/100。** fixed revision `ad99ec5f26debf1d6c1a4dc8461b2bcb787ec9af` 含 Delay/Local/Realtime 的 SFT 与分布式配置；直接 SFT 文件建立 optimizer/backward/checkpoint 训练链，Apache-2.0 清晰。upstream 没有 Ascend 证据；CAND-001 内的 MOSS-TTS FSDP2 port 归 CAND-001，CAND-003 的 Ascend 完整度必须为 0。[SRC-030][SRC-031]

**CAND-010 — QwenLM/Qwen3-TTS target baseline，discovered，50/100。** fixed revision `022e286b98fbec7e1e916cb940cdf532cd9f488e` 是 exact architecture baseline，公开训练代码仅覆盖 CUDA-oriented 12Hz Base 单说话人 SFT；pretraining、DPO、GSPO、tokenizer training、单机 8 卡与多机均未公开建立。它不作为 Ascend 参考，只用于目标模块对齐。[SRC-001][SRC-002]

**CAND-018 — zai-org/GLM-TTS，discovered，57/100。** official fixed HEAD `4b944f4be7b6c55454751715081f4dc83992897a` 含 DeepSpeed GRPO optimizer/checkpoint/distributed training entry 和 CANN 8.5.1/910B NPU setup，但训练脚本硬编码 CUDA device/AMP，故只给 Ascend inference 证据，不推导 NPU training。`prchbzy/glmtts-910b` 的固定派生树补充 OM/NPU inference 修复，但没有独立 NPU training lifecycle，因此作为 secondary source 合并，不重复计候选。[SRC-061][SRC-062][SRC-063][SRC-064]

### Speech-specialist

**CAND-004 — FunAudioLLM/CosyVoice，shortlisted，51/100。** fixed revision `074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc` 的 `cosyvoice/bin/train.py` 建立 optimizer/backward/scheduler/checkpoint 与 distributed training 入口，Apache-2.0 清晰；upstream 自身无 Ascend 证据。CAND-001 的 CosyVoice3 port 只归 CAND-001，故 CAND-004 Ascend 分数为 0。[SRC-032][SRC-033]

**CAND-007 — jishengpeng/WavTokenizer，discovered，43/100；CAND-008 — ESPnet/espnet (ESPnet-Codec)，discovered，48/100。** 两者分别固定为 `5cf440d91ac420ca338f117b7003a77450d64730` 与 `6ed85c0c2be18e2699818b6c042b33ffb7adfa4d`，具有 codec/speech training 与许可价值，但无 Ascend 训练证据；CAND-007 最新可见 commit 停在 2025-03，CAND-008 过于宽泛，均不优于 CAND-003/CAND-004 的目标模块覆盖。[SRC-036][SRC-037]

**CAND-016 — inworld-ai/tts，discovered，58/100；CAND-017 — alibaba/unified-audio，discovered，45/100。** CAND-016 的固定树提供 SpeechLM/1D codec pretrain、SFT、RLHF、DDP/DeepSpeed/FSDP 与 checkpoint 生命周期，但环境明确是 CUDA；CAND-017 的固定树提供 audio-tokenizer/codec 配置与 UniSE `train.py`，同样没有 Ascend 训练证据。两者在审阅修复检索中新增，保留作 architecture/lifecycle 对照；CAND-003/CAND-004 仍因与已知 MindSpeed-MM ports/目标模块映射更直接而维持当前 shortlist。[SRC-057][SRC-058][SRC-059][SRC-060]

### Rejected

CAND-006、009、011、012、013、014、015 均保留在 `candidates.csv`，避免后续重复发现。910B、NPU patch、export 或模型卡声明均不替代 optimizer/backward/launch/config/checkpoint 链。

## Qualification screening

| ID | Canonical / fixed revision | Owner | Training chain | Ascend evidence | Model / scale | License / docs | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CAND-001 | GitCode + `0edd553…` mirror | Ascend | exact Qwen3-TTS SFT complete | direct NPU/HCCL/FSDP2 | 1.7B; 8p config; multi-node run unknown | Other aggregate; strong docs | shortlist main |
| CAND-002 | GitCode + `434baff…` mirror | Ascend | Qwen3 pretrain/SFT complete | direct NPU/MindSpeed | dense/MoE; multi-node config/project claims | Other aggregate; strong docs | shortlist scale |
| CAND-003 | GitHub `ad99ec5…` | OpenMOSS | speech SFT complete | none upstream | 8-GPU configs | Apache-2.0; good docs | shortlist codec |
| CAND-004 | GitHub `074ca6d…` | FunAudioLLM | speech training complete | none upstream | distributed entry | Apache-2.0; good docs | shortlist speech |
| CAND-005 | GitCode `c9d4e7d…` + GitHub `6a2804a…` mirror | Ascend | historical recipes; per-path deep audit pending | direct but stale | some 1p/8p | Apache-2.0 default; per-model override | discovered |
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
| CAND-016 | GitHub `a8556e4…` | Inworld AI | SpeechLM/codec pretrain, SFT and RLHF | none; CUDA-only | DDP/DeepSpeed/FSDP | MIT; strong docs | discovered |
| CAND-017 | GitHub `c4004e2…` | Alibaba | UniSE training; codec configs | none | scale evidence limited | Apache-2.0; good docs | discovered |
| CAND-018 | GitHub `4b944f4…` + derivative `9735802…` | Z.ai | GRPO/DeepSpeed optimizer and checkpoint chain | 910B inference only; training hardcodes CUDA | distributed RL entry | Apache-2.0; strong docs | discovered |

对 moving-only rejected entries，本轮没有伪造 commit；其 revision 留空并在报告/CSV 明示边界。进入 shortlist 的四项和 CAND-005 canonical 均固定完整 commit。

## Canonical and mirror audit

| ID | Authoritative project URL | Mirror/secondary URL | Resolution |
| --- | --- | --- | --- |
| CAND-001 | `gitcode.com/Ascend/MindSpeed-MM` | GitHub fixed mirror `0edd553…` | canonical GitCode; mirror only for immutable source evidence [SRC-018][SRC-019] |
| CAND-002 | `gitcode.com/Ascend/MindSpeed-LLM` | GitHub fixed mirror `434baff…` | canonical GitCode; mirror only for immutable source evidence [SRC-025][SRC-026] |
| CAND-003 | `github.com/OpenMOSS/MOSS-TTS` | none recorded | canonical owner repository [SRC-030] |
| CAND-004 | `github.com/FunAudioLLM/CosyVoice` | none recorded | canonical owner repository [SRC-032] |
| CAND-005 | `gitcode.com/Ascend/ModelZoo-PyTorch` | GitHub mirror `6a2804a358a5b18e3dac1ab902f41f88e240b00f` | canonical corrected; GitCode `c9d4e7dc8a951fb9365e5ebe42601b0101d34ba3` and mirror SHA differ, so equivalence is unknown [SRC-034][SRC-052] |
| CAND-006 | `huggingface.co/DiscreteSpeech/DSTK` | none recorded | canonical model-card repository for the exclusion [SRC-035] |
| CAND-007 | `github.com/jishengpeng/WavTokenizer` | none recorded | canonical owner repository [SRC-036] |
| CAND-008 | `github.com/espnet/espnet` | none recorded | canonical organization repository; ESPnet-Codec is a path/family, not a second candidate [SRC-037] |
| CAND-009 | `github.com/vllm-project/vllm-omni` | none recorded | canonical organization repository [SRC-038] |
| CAND-010 | `github.com/QwenLM/Qwen3-TTS` | official HF/ModelScope assets are not source mirrors | canonical source repository [SRC-001][SRC-002] |
| CAND-011 | `gitcode.com/Ascend/Ascend-SACT` | none fixed | canonical official entry; revision remains unknown [SRC-039] |
| CAND-012 | `gitee.com/mindspore/mindspore-lite` | none fixed | canonical official entry used for exclusion; exact example revision unknown [SRC-040] |
| CAND-013 | `gitee.com/deep-spark/deepsparkhub` | none fixed | canonical official entry used for exclusion; exact Qwen3-TTS revision unknown [SRC-041] |
| CAND-014 | `modelscope.cn/models/OpenBMB/BitCPM-CANN` | no canonical code tree resolved | canonical model-card entry only; code upstream unknown [SRC-042] |
| CAND-015 | `github.com/OpenMOSS/MOSS-Audio-Tokenizer` | none recorded | canonical owner repository [SRC-047] |
| CAND-016 | `github.com/inworld-ai/tts` | none recorded | canonical organization repository [SRC-057][SRC-058] |
| CAND-017 | `github.com/alibaba/unified-audio` | none recorded | canonical organization repository [SRC-059][SRC-060] |
| CAND-018 | `github.com/zai-org/GLM-TTS` | derivative `github.com/prchbzy/glmtts-910b` at `9735802…` | canonical owner repository; derivative adds inference/OM fixes but no independent NPU training and is merged as secondary evidence [SRC-061–064] |

## Latest meaningful commit and maintenance screening

`fixed/latest meaningful` 是本轮用于维护判断的可追溯 revision；对 fixed tree 使用其 commit 元数据，对 moving/inaccessible exclusion entry 明确保持 unknown。它不表示本研究运行了该 revision。

| ID | Canonical project | Fixed/latest meaningful SHA | Commit date (UTC) | Subject / release context | Maintenance judgment | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CAND-001 | Ascend/MindSpeed-MM | `0edd553e0ac9c912fe422c42cc9f42db9255ddcf` | 2026-07-16T06:53:03Z | optimize qwen3.5 execution/prefetch | active; fixed HEAD is not Qwen3-TTS-specific, exact SFT added earlier | SRC-048 |
| CAND-002 | Ascend/MindSpeed-LLM | `434baff794bd5594ebc9ed8a5b399110da9a44f0` | 2026-07-16T09:26:04Z | `docs(torch): mla doc update` | active; fixed HEAD is docs-only, Qwen3 lifecycle remains in fixed tree | SRC-049 |
| CAND-003 | OpenMOSS/MOSS-TTS | `ad99ec5f26debf1d6c1a4dc8461b2bcb787ec9af` | 2026-06-22T11:51:50Z | add Local v1.5 finetuning | active and directly training-relevant | SRC-050 |
| CAND-004 | FunAudioLLM/CosyVoice | `074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc` | 2026-05-25T18:15:40Z | add FunAudioLLM ecosystem links | active; latest fixed commit is not a training change | SRC-051 |
| CAND-005 | Ascend/ModelZoo-PyTorch | `c9d4e7dc8a951fb9365e5ebe42601b0101d34ba3` | 2026-07-14T08:10:57Z | add ICAA PyTorch support | canonical active; speech subtrees are historical, mirror equivalence unknown | SRC-052 |
| CAND-006 | DiscreteSpeech/DSTK | unknown | unknown | HF model API and Git endpoint timed out during remediation; moving card remains accessible | maintenance unknown; sufficient only for inference exclusion | SRC-035 |
| CAND-007 | jishengpeng/WavTokenizer | `5cf440d91ac420ca338f117b7003a77450d64730` | 2025-03-02T03:53:58Z | Update README.md | stale for a fast-moving codec stack | SRC-053 |
| CAND-008 | ESPnet/espnet | `6ed85c0c2be18e2699818b6c042b33ffb7adfa4d` | 2026-07-10T22:04:30Z | merge OpenBEATs training | active broad speech repository; not Ascend evidence | SRC-054 |
| CAND-009 | vLLM-Omni | `be517db18a68fb8983ce72a4a5f5312f5324b26e` | 2026-07-17T03:26:35Z | video-DiT replica-DP recipe/benchmark | active, but latest change is unrelated to TTS training | SRC-055 |
| CAND-010 | QwenLM/Qwen3-TTS | `022e286b98fbec7e1e916cb940cdf532cd9f488e` | 2026-03-17T06:38:41Z | fix finetuning bug | active/relevant target baseline; public lifecycle remains narrow | SRC-002 |
| CAND-011 | Ascend/Ascend-SACT | unknown | unknown | moving GitCode inference entry; no fixed commit metadata established | maintenance unknown; only inference exclusion is claimed | SRC-039 |
| CAND-012 | MindSpore Lite | unknown | unknown | moving Gitee umbrella entry; exact Qwen3-TTS example revision not fixed | maintenance unknown for this example; export/inference role only | SRC-040 |
| CAND-013 | DeepSparkHub | unknown | unknown | moving Gitee inventory; exact Qwen3-TTS revision not fixed | maintenance unknown for this entry; inference classification only | SRC-041 |
| CAND-014 | OpenBMB/BitCPM-CANN | unknown | unknown | moving ModelScope card; canonical code tree unresolved | maintenance unknown; non-speech exclusion only | SRC-042 |
| CAND-015 | OpenMOSS/MOSS-Audio-Tokenizer | `8c50ac4c5d7287d2ed6ea20a08c90ca439887d23` | 2026-06-16T12:50:45Z | `feat: update readme` | active release-facing repository; public training code absent | SRC-056 |
| CAND-016 | Inworld TTS | `a8556e420a2e6e0b18f506f369aae9efa65d2c78` | 2025-09-19T02:51:53Z | Update prompting format | fixed default HEAD is old despite later repository metadata activity; training tree remains inspectable | SRC-057 |
| CAND-017 | Alibaba unified-audio | `c4004e217ddf7c514f72ea22f2d0fbf43f02ae90` | 2026-07-07T05:42:57Z | Upload project info | active release-facing audio project; latest commit is metadata-oriented | SRC-059 |
| CAND-018 | Z.ai GLM-TTS | `4b944f4be7b6c55454751715081f4dc83992897a` | 2026-04-10T08:50:23Z | Merge PR 53: Support Ascend NPU | active relevant maintenance; NPU change establishes inference setup while GRPO training remains CUDA-hardcoded | SRC-061 |

## Preliminary score

分数用于广度排序，不等于 Task 5 审计结论。每个非零分数均通过 `evidence_ids` 回指至少一个 ledger 来源；CAND-003/CAND-004/CAND-007/CAND-008/CAND-010/CAND-015/CAND-016/CAND-017 的 Ascend 维度为 0，CAND-018 的 Ascend 分只来自 inference setup，CAND-001 内 ports 不重复计分给 upstream。

| ID | Candidate | Ascend /30 | Architecture /25 | Scale /20 | Repro /15 | Docs/license /10 | Total | Evidence |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| CAND-001 | MindSpeed-MM | 29 | 25 | 15 | 14 | 7 | 90 | SRC-018–024, SRC-043 |
| CAND-002 | MindSpeed-LLM | 29 | 12 | 20 | 14 | 7 | 82 | SRC-025–029, SRC-044–046 |
| CAND-003 | MOSS-TTS | 0 | 23 | 13 | 14 | 10 | 60 | SRC-030–031 |
| CAND-016 | Inworld TTS | 0 | 20 | 15 | 13 | 10 | 58 | SRC-057–058 |
| CAND-018 | GLM-TTS | 8 | 22 | 5 | 12 | 10 | 57 | SRC-061–064 |
| CAND-004 | CosyVoice | 0 | 19 | 8 | 14 | 10 | 51 | SRC-032–033 |
| CAND-010 | Qwen3-TTS target | 0 | 25 | 1 | 14 | 10 | 50 | SRC-001–002 |
| CAND-008 | ESPnet/ESPnet-Codec | 0 | 18 | 7 | 14 | 9 | 48 | SRC-037 |
| CAND-005 | ModelZoo-PyTorch speech | 18 | 8 | 8 | 8 | 5 | 47 | SRC-034 |
| CAND-006 | DSTK | 8 | 20 | 2 | 8 | 8 | 46 | SRC-035 |
| CAND-017 | Alibaba unified-audio | 0 | 20 | 6 | 9 | 10 | 45 | SRC-059–060 |
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
- **新增 speech 参考边界：** CAND-016/CAND-017/CAND-018 补充 SpeechLM/codec/GRPO 训练比较，但均未建立 Ascend training；CAND-018 的 official/derivative NPU 材料只支撑 inference，固定 GRPO entry 仍硬编码 CUDA。[SRC-057–064]
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
| SRC-048–056 | fixed commit metadata for CAND-001–005, 007–009 and 015 | maintenance screening |
| SRC-057–060 | Inworld TTS and Alibaba unified-audio fixed commits/training trees | remediation-added speech/codec candidates |
| SRC-061–064 | GLM-TTS fixed commit, CUDA GRPO, official NPU guide and derivative tree | NPU-inference versus training boundary and deduplication |
