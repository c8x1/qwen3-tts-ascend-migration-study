# Qwen3-TTS Ascend reference selection proposal

本提案截至 2026-07-17（Asia/Shanghai），记录 Phase 1 的参考项目组合与后续取材方式。评分和选型只综合既有固定源码审计、官方文档和项目自产材料；它们不代表本研究已运行 CUDA、Ascend 910B、训练、推理、转换或评测，也不授权下载权重或数据。分数来自可复算的已审计 CSV，而不是一次运行排名。[SRC-001][SRC-019][SRC-026][SRC-030][SRC-032]

## Approved selection

用户于 **2026-07-17（Asia/Shanghai）** 明确批准默认路线和 acquisition mode，**没有要求修改路线**。固定选型如下：

| Approved role | Candidate | Canonical URL | Fixed revision | License |
| --- | --- | --- | --- | --- |
| main implementation anchor | CAND-001 Ascend/MindSpeed-MM | `https://gitcode.com/Ascend/MindSpeed-MM` | `0edd553e0ac9c912fe422c42cc9f42db9255ddcf` | `Other (aggregate BSD-3-Clause-style notices)` |
| scale satellite | CAND-002 Ascend/MindSpeed-LLM | `https://gitcode.com/Ascend/MindSpeed-LLM` | `434baff794bd5594ebc9ed8a5b399110da9a44f0` | `Other (aggregate BSD-3-Clause-style notices)` |
| speech/codec satellite | CAND-003 OpenMOSS/MOSS-TTS | `https://github.com/OpenMOSS/MOSS-TTS` | `ad99ec5f26debf1d6c1a4dc8461b2bcb787ec9af` | `Apache-2.0` |

CAND-004 仍为已审计的 optional comparison，未被选入固定清单。用户同时授权对上述三个固定 revision 进行**仓库外部或 `.superpowers/` 下 git-ignored、read-only、source-only 的本地获取**。`research/selected-revisions.csv` 中的 `acquisition_policy=clone` 是获取授权策略：它表示允许在这一外部/ignored 边界内获取固定源码，**不代表 Git clone 传输成功，不表示源码被 vendor 或追踪**。授权不包含公开仓库提交、公开再分发、submodule 添加、权重、数据集、checkpoint 或其他模型资产。

授权策略与实际传输结果分开记录：CAND-001 和 CAND-002 在 smart-HTTP 失败后实际使用了 exact-SHA codeload archive fallback，**不是 clone**；本批准记录不据此断言 CAND-003 的实际获取方式或最终 checkout 状态，这些仍由独立 acquisition handoff/remediation 验证。因此，此处不声称三个源码获取全部完成。

## 1. Executive recommendation

**用户已于 2026-07-17 批准默认的 exact-TTS-led 组合：**以 **CAND-001 Ascend/MindSpeed-MM** 的固定官方 GitHub mirror 快照 `0edd553e0ac9c912fe422c42cc9f42db9255ddcf`（**81/100**）为 main implementation anchor；以 **CAND-002 Ascend/MindSpeed-LLM** 的固定快照 `434baff794bd5594ebc9ed8a5b399110da9a44f0`（**79/100**）为 training-scale satellite；以 **CAND-003 OpenMOSS/MOSS-TTS** `ad99ec5f26debf1d6c1a4dc8461b2bcb787ec9af`（**59/100**）为 speech/codec satellite。**CAND-004 CosyVoice** `074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc`（**49/100**）只作可选的 data/training/eval/export 次级对照，不是必须获取或 vendor 的主卫星。[SRC-019][SRC-026][SRC-030][SRC-032]

精确结论是：**存在 exact public Qwen3-TTS→Ascend 的 12Hz Base speaker-SFT 参考，即 MindSpeed-MM；但没有可验证的 exact full-lifecycle 项目同时覆盖 Qwen3-TTS S1/S2/S3 pretrain、tokenizer training、DPO/GSPO、fixed executable eval、CANN 8.5.2、candidate-specific multi-node run/resume。**官方 Qwen3-TTS 固定树本身只公开 12Hz Base 到单说话人 CustomVoice 的 SFT 示例；MindSpeed-MM 补上 exact NPU/FSDP2 训练链，却仍没有上述完整阶段和目标环境运行证据。因此，这个组合是当前公开证据下最接近、可辩护且缺口可见的参考；它既不等于“完全没有 exact 项目”，也不等于“已有完整迁移”。[SRC-001][SRC-003][SRC-019][SRC-020][SRC-021][SRC-022][SRC-043][SRC-066]

**DEC-002 route selection** 和 **DEC-001 acquisition mode** 均已于 2026-07-17 由用户明确批准，并固化为上述组合和授权边界。此批准只允许 source-only acquisition 与后续计划准备，不自动授权建立站点内容、实施迁移或运行模型。

## 2. Ranked audited candidates and final scores

| Rank | Candidate and fixed revision | Ascend /30 | Architecture /25 | Scale /20 | Repro /15 | Docs/license /10 | Final | Approved role |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | CAND-001 MindSpeed-MM `0edd553e0ac9c912fe422c42cc9f42db9255ddcf` | 27 | 24 | 13 | 11 | 6 | **81** | main implementation anchor |
| 2 | CAND-002 MindSpeed-LLM `434baff794bd5594ebc9ed8a5b399110da9a44f0` | 29 | 10 | 19 | 14 | 7 | **79** | training-scale satellite |
| 3 | CAND-003 MOSS-TTS `ad99ec5f26debf1d6c1a4dc8461b2bcb787ec9af` | 0 | 23 | 13 | 13 | 10 | **59** | speech/codec satellite |
| 4 | CAND-004 CosyVoice `074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc` | 0 | 19 | 8 | 13 | 9 | **49** | optional secondary comparison |

分数的含义是证据覆盖度，而非候选间可互换性。源码级审计把 preliminary 分数保守下调为 81、79、59、49；尤其 CAND-001/CAND-002 只差 2 分，却分别代表 exact TTS semantics 和 text-Qwen scale architecture，不能用总分自动消除重大路线选择。[SRC-019][SRC-020][SRC-023][SRC-026][SRC-027][SRC-030][SRC-031][SRC-032][SRC-033]

## 3. Recommended main project

**推荐主项目：CAND-001 Ascend/MindSpeed-MM，固定审计快照 `0edd553e0ac9c912fe422c42cc9f42db9255ddcf`，81/100。** canonical owner entry 是 Ascend GitCode；本提案引用的是同 owner 官方 GitHub mirror 的 immutable fixed tree。审计日 canonical `master` 观察为 `de997c4db38da6eb6cca90571df23a89eff33105`，与固定快照不同；这只证明 moving ref 已移动，不能把两者写成 current equality，也不能断言对象树等价或 fork。[SRC-018][SRC-019][SRC-048][SRC-065][SRC-100]

选择它主导的决定性证据是：

- `examples/qwen3tts/finetune_qwen3tts.sh` 明确进入 `torchrun`/HCCL/NPU 路线并暴露 8-process 默认值和多节点参数；配置固定 AdamW、BF16/FSDP、累积、裁剪、迭代与 checkpoint 选项。[已证实；SRC-021][SRC-043]
- FSDP engine 固定源码覆盖 forward/loss、`backward()`、optimizer/scheduler、gradient clip 与 zero-grad；DCP checkpointer 覆盖 model、optimizer、scheduler、dataloader 和 RNG save/load。[已证实；SRC-022][SRC-072]
- exact dataset/prepare path 覆盖 24 kHz mel、12Hz 离线 codec materialization、双轨 masks/labels；Qwen3-TTS patch 暴露 RoPE/RMSNorm torch-npu replacement surface；converter 只有 DCP→HF，HF→DCP 方向未实现。[已证实；SRC-067][SRC-069][SRC-070][SRC-073]
- 项目 ST JSON 记录 loss/time/memory，只是项目自产基线，不是本研究独立运行；exact patch invocation edge、音质、转换后推理、多机与 CANN 8.5.2 都不因此变成已验证。[项目声明/待真机验证；SRC-023][SRC-066][SRC-069]

主项目边界：它是 **12Hz Base speaker-SFT implementation anchor**，不是 S1/S2/S3 pretraining、tokenizer training、DPO/GSPO 或 fixed eval 的完整替代品；默认 8-process 配置与 multi-node 参数也不是 exact multi-node run artifact。[SRC-001][SRC-003][SRC-020][SRC-021]

## 4. Recommended training-scale satellite project

**推荐规模卫星：CAND-002 Ascend/MindSpeed-LLM，固定审计快照 `434baff794bd5594ebc9ed8a5b399110da9a44f0`，79/100。**它只提供 text-Qwen/MCore/FSDP2 scale engineering：Qwen3 pretrain/SFT/DPO inventory、TP/PP/CP/EP、distributed optimizer、8-NPU/2-node 配置、训练 lifecycle 与同步/异步 DCP checkpoint；这些证据不能回填为 TTS/audio、16-codebook MTP、speaker encoder 或 waveform eval 能力。[已证实/分析边界；SRC-026][SRC-027][SRC-044][SRC-045][SRC-046][SRC-077][SRC-078][SRC-079][SRC-081][SRC-083][SRC-084][SRC-085]

canonical GitCode `master` 在审计日先后出现不同 HEAD，且与固定 GitHub 快照不同。因此教学和映射继续绑定 `434baff...`，不把 moving `master` 冒充 immutable current equality；若后续实施选 formal release/ref，必须重新 pin source 和外部 MindSpeed/Megatron/FSDPTurbo 依赖。[SRC-025][SRC-049][SRC-075][SRC-076][SRC-087][SRC-101]

它的角色严格限定为回答“规模框架如何组织”，而不是回答“Qwen3-TTS 语义怎样实现”。下一阶段只从中学习 rank/env/launcher、parallel topology、global-batch accounting、fusion gating、checkpoint/resume 与 conversion 组织；任何 text dataset/loss、text eval 或 text state mapping 都不得直接套用到 TTS。[SRC-027][SRC-046][SRC-077][SRC-079][SRC-084][SRC-085]

## 5. Recommended speech or codec satellite project

**推荐 speech/codec 卫星：CAND-003 OpenMOSS/MOSS-TTS `ad99ec5f26debf1d6c1a4dc8461b2bcb787ec9af`，59/100。**它补的是 CAND-001/002 之外的结构与数据比较：Qwen-style Delay、32 RVQ heads、reference/None conditioning、rank-sharded target/reference codec materialization、multi-codebook teacher forcing、channel loss、DDP/FSDP/ZeRO-3 配置和直接 SFT lifecycle。[已证实；SRC-030][SRC-031][SRC-090][SRC-091][SRC-092][SRC-093]

这些价值是**对照知识**：MOSS 的 32-head same-step/Delay topology 与 Qwen3-TTS 的 16-codebook codec-0 Talker + residual MTP 不同；其 upstream 是 CUDA/PyTorch 2.9.1 路线，没有 torch-npu/CANN/HCCL。MindSpeed-MM 内的 MOSS port 只能归因给 CAND-001，不能把 CAND-003 的 Ascend 分数从 0 补高。[分析推断/已证实边界；SRC-019][SRC-030][SRC-031][SRC-089][SRC-093]

**CAND-004 CosyVoice `074ca6...`，49/100，只作为可选次级对照。**它的 Kaldi→embedding/token→parquet、frame-budget dynamic batching、rank/worker partition、checkpoint averaging、JIT/ONNX export 与 CER/WER/SIM 设计值得按需比较；但 single-token LLM + flow/HiFT/HiFiGAN 路径与 target 更远，上游也没有 Ascend training，因此默认不把它列为必须 acquisition/vendor 的卫星。[SRC-032][SRC-033][SRC-095][SRC-096][SRC-097][SRC-098][SRC-099]

## 6. Qwen3-TTS target-module coverage matrix

下表逐项对照官方 target module checklist；“覆盖”仅指固定源码可用于阅读或映射，不代表目标环境已运行。[SRC-001][SRC-003]

| Target checklist item | Main: CAND-001 | Scale: CAND-002 | Speech: CAND-003 | Optional: CAND-004 | Residual decision/validation gap |
| --- | --- | --- | --- | --- | --- |
| text tokenizer / ChatML processor / templates | exact SFT path | text-Qwen templates only | Qwen-style contrast | text/speech prompt contrast | target preprocessing parity [SRC-001][SRC-019][SRC-077] |
| Talker projection / codec embedding / Qwen3 decoder / RoPE / attention / KV cache | exact model + NPU patch surface | text-Qwen scale/fusion pattern | Qwen-style Delay contrast | discrete-token LLM contrast | patch invocation and 8.5.2 numerics [SRC-019][SRC-069][SRC-077] |
| codec-0 LM head / logits / sampling | exact tree | no audio head | text + audio-head contrast | single-token CE contrast | generation parity tests [SRC-019][SRC-093][SRC-099] |
| residual MTP / 16 codebooks | exact model/data structures | none | 32-head Delay comparison | none equivalent | distributed MTP loss/numerics [SRC-019][SRC-067][SRC-093] |
| speaker encoder / 24 kHz / 128-bin mel | exact SFT mel path | none | reference-code contrast | embedding/features contrast | multi-speaker and encoder numerics [SRC-067][SRC-092][SRC-097] |
| x-vector-only and ICL reference text/audio | exact upstream-derived path | none | reference/None conditioning | prompt text/speech/embedding | prompt and sampling parity [SRC-001][SRC-019][SRC-093][SRC-099] |
| VoiceDesign / CustomVoice injection | only Base speaker-SFT scope | none | architecture comparison only | prompt comparison only | exact VoiceDesign/multi-speaker training absent [SRC-001][SRC-020] |
| 12Hz encoder / 16-codebook RVQ | codec materialization/use, not tokenizer training | none | 32-codebook contrast | pretrained token extractor | tokenizer training lifecycle absent [SRC-003][SRC-073][SRC-092][SRC-096] |
| 12Hz causal waveform decoder / chunking | target dependency path | none | speech generation contrast | flow/vocoder contrast | 910B decode quality/performance [SRC-001][SRC-030][SRC-032] |
| audio libraries / resampling | exact data path surface | none | CUDA audio path | staged audio path | package/operator audit on NPU [SRC-001][SRC-073][SRC-096] |
| offline codec materialization / recoverable sharding | materialization, no resume/shard | generic text preprocessing only | rank-sharded materialization | parquet staging | exact resumable/sharded preparation [SRC-073][SRC-092][SRC-096] |
| collate masks / labels / distributed sampler | exact masks/labels and max-length sync | sampler/accounting pattern only | multi-codebook masks | rank/worker partition + batching | target sampler/bucketing correctness [SRC-067][SRC-079][SRC-093][SRC-097][SRC-098] |
| main + `0.3 * sub_talker_loss` parity | exact target loss shape | generic distributed loss plumbing | channel-loss contrast | discrete CE/DPO contrast | BF16/FP32 reduction numerical tolerance [SRC-001][SRC-022][SRC-093][SRC-099] |
| BF16 / accumulation / clipping / optimizer | exact config/engine | mature text framework pattern | CUDA mixed precision | CUDA AMP | 910B fallback and precision matrix [SRC-022][SRC-043][SRC-084] |
| checkpoint copy/config/save/resume ownership | DCP full-state + one-way HF export | mature text lifecycle | inference-ready save, no resume | partial resume + export | target fault restore and HF→DCP [SRC-070][SRC-072][SRC-085][SRC-031][SRC-033] |
| Transformers generation / attention fallback | exact integration surface | fusion-gating pattern only | CUDA/FA2 contrast | CUDA path | eager/SDPA/NPU parity [SRC-001][SRC-069][SRC-082] |
| single-node 8-card | default 8-process config, no independent run | mature text config | GPU config only | default 1 GPU | candidate-specific 910B run artifact [SRC-021][SRC-027][SRC-096] |
| multi-node rendezvous / topology / recovery | parameters only | 2-node text config/framework | documented GPU parameters | no fixed multi-node evidence | exact TTS run/resume artifact [SRC-021][SRC-079][SRC-091] |
| executable WER/CER/SIM/tokenizer eval | ST loss only | text metrics only | project quality tables | design/project tables | fixed code, data revisions, raw outputs [SRC-023][SRC-090][SRC-096] |
| 25Hz DiT/BigVGAN secondary mapping | not primary selection scope | none | none equivalent | flow/vocoder contrast | defer until official assets/entry mature [SRC-001][SRC-003][SRC-032] |

## 7. What the combination covers and does not cover

**组合覆盖：**exact Qwen3-TTS 12Hz Base speaker-SFT 的 NPU launcher/config/data/model/engine/checkpoint/export 阅读面；torch-npu/HCCL/FSDP2 device abstraction；text-Qwen 的 TP/PP/CP/EP、distributed optimizer、多节点配置和 checkpoint/resume 组织；speech 侧的 multi-codebook/Delay/reference conditioning/rank-sharded codec data/SFT 对照；按需补充 dynamic batching、eval/export 设计。[已证实；SRC-019][SRC-021][SRC-022][SRC-026][SRC-027][SRC-046][SRC-067][SRC-068][SRC-070][SRC-072][SRC-077][SRC-079][SRC-092][SRC-093][SRC-096][SRC-097]

**组合不覆盖：**exact Qwen3-TTS S1/S2/S3 pretraining、tokenizer training、DPO/GSPO、VoiceDesign 或 multi-speaker 完整训练、fixed executable eval 与 raw outputs；CANN 8.5.2 官方精确兼容行；候选专属的 910B single-node 8-card、多节点训练、断点恢复、数值/精度/性能/音质结果；完整数据和资产许可；HF→DCP target converter。[SRC-001][SRC-003][SRC-028][SRC-066][SRC-069][SRC-070][SRC-076]

组合也不允许把卫星能力相加成虚假的单一项目能力：MindSpeed-LLM 的 text scale 不是 TTS scale，MOSS/CosyVoice upstream 没有 Ascend training，MindSpeed-MM 内部 ports 只归 CAND-001，project config/ST/README 也不是独立运行。[SRC-019][SRC-023][SRC-026][SRC-030][SRC-032]

## 8. Environment compatibility summary

推荐采用**双环境、双阶段**，避免把复现与目标验证混成一次未经证实的升级：

| Lane | Purpose | Version policy | Evidence state / consequence |
| --- | --- | --- | --- |
| A. project-native reproducibility lane | 优先理解和重放 MindSpeed-MM documented route | 尽量匹配 PyTorch/torch-npu **2.7.1** + CANN **8.5.0**，同时 pin fixed source 和全部外部依赖 | 版本路线有文档/源码支持，但本研究未运行；仍需记录 driver、固件、MindSpeed SHA 和硬件拓扑 [SRC-020][SRC-071][SRC-074] |
| B. target validation lane | 在用户已有目标栈检查迁移适配 | PyTorch/torch-npu **2.7.1** + CANN **8.5.2** | exact compatibility **unknown**；必须后续做 910B smoke、numerical、operator fallback、checkpoint、single-node 和 distributed validation，不能从 8.5.0 patch 外推 [SRC-020][SRC-028][SRC-069] |

MindSpeed-LLM 26.x 文档中的 PyTorch 2.7.1 + CANN 9.0/9.1 路线只作为 scale-engineering 学习材料；旧兼容信息含 8.5.0，但没有 8.5.2 精确行。它不要求主环境升级到 9.x，也不能替主项目证明 8.5.2；只有后续实验或官方精确矩阵可以改变 unknown。[SRC-028][SRC-087]

MOSS-TTS 推荐 Python 3.12/CUDA 12.8/PyTorch 2.9.1，CosyVoice 固定 CUDA 12.1/PyTorch 2.3.1；二者与 target lane 显著错位，默认只做 source reading，不把 CUDA 环境合并进 NPU 主环境。[SRC-089][SRC-091][SRC-095]

## 9. License and local-source acquisition implications

| Candidate | Fixed-source license record | Current permission boundary | If source is copied/redistributed |
| --- | --- | --- | --- |
| CAND-001 MindSpeed-MM | `Other (aggregate BSD-3-Clause-style notices)` | 已授权外部/ignored read-only source-only 获取 | 公开复制/再分发前仍须逐文件 license/notice 审计和二次确认 [SRC-024][SRC-071] |
| CAND-002 MindSpeed-LLM | `Other (aggregate BSD-3-Clause-style notices)` | 已授权外部/ignored read-only source-only 获取 | 同上，并保留 third-party notices [SRC-029][SRC-086] |
| CAND-003 MOSS-TTS | root Apache-2.0；fixed `moss_audio_tokenizer@56776e...` 也为 Apache-2.0 | 已授权外部/ignored read-only source-only 获取 | parent 不 blanket-cover submodule；权重/数据/资产另审 [SRC-030][SRC-088][SRC-103][SRC-104] |
| CAND-004 CosyVoice | root Apache-2.0；fixed `Matcha-TTS@dd9105...` 为 MIT | 仅按需作为次级对照 | parent/submodule 分别保留 notice；预训练、导出资产另审 [SRC-032][SRC-094][SRC-106][SRC-107] |

**DEC-001 acquisition mode（approved 2026-07-17）：**采用仓库外部或 `.superpowers/` 下 git-ignored 的 read-only source-only acquisition，固定 revisions，**不提交到公共仓**；所有讲解页面只使用必要的短引用和 immutable links。若要把源码复制进 `references/` 或公开再分发，先做逐文件 license/notice 与 asset provenance 审计，然后再次取得明确确认。CSV 的 `clone` 值表示此本地获取授权，不证明 Git clone 成功；当前仍不授权 vendor、submodule 添加、权重/数据/模型资产下载或公开再分发。

## 10. Verified facts, project claims, inferences, and 910B validation gaps

| Claim state | This proposal may say | This proposal must not imply |
| --- | --- | --- |
| **已证实** | fixed trees 中存在 exact Qwen3-TTS NPU speaker-SFT launcher/config/engine/data/checkpoint surface；MindSpeed-LLM 有 text-Qwen scale framework；MOSS/CosyVoice 有各自 speech training/data surface [SRC-019][SRC-021][SRC-022][SRC-026][SRC-030][SRC-032] | 源码存在等于在目标机器运行成功 |
| **项目声明** | MindSpeed-MM ST loss/time/memory，MOSS/CosyVoice quality tables，MindSpeed-LLM scale/performance材料由项目方给出 [SRC-023][SRC-079][SRC-090][SRC-096] | 本研究独立复现了性能、质量或稳定性 |
| **分析推断** | exact-TTS-led 组合能以较小语义偏差学习迁移；text scale 和 speech satellites 可补工程/结构知识 [SRC-019][SRC-026][SRC-030] | 卫星能力可以合并成一个完整实现，或 text scale 自动适用于 TTS |
| **待真机验证** | 下列 910B gaps 保持 unknown | 8.5.0→8.5.2、CUDA→NPU、config→successful run 的无证据外推 |

910B validation gaps 至少包括：CANN 8.5.2 import/device smoke；RoPE/RMSNorm/attention/fallback 的 shape、dtype、forward/backward 与 tolerance；BF16/FP32 reduction loss parity；audio preprocessing 与 codec materialization；DCP save/load、HF export、转换后 inference；单机 8 卡 sampler/global batch/collective/checkpoint ownership；多节点 rendezvous/topology/throughput/fault restore；quality/eval pipeline 和 raw outputs。所有候选还缺本研究的 candidate-specific multi-node run/resume 证据。[SRC-021][SRC-023][SRC-066][SRC-067][SRC-069][SRC-070][SRC-072][SRC-079]

## 11. Alternatives and consequences

### Alternative A — scale-led MindSpeed-LLM main

以 CAND-002 为主、CAND-001 为 exact TTS satellite。好处是先按 MCore/FSDP2、TP/PP/CP/EP 和成熟 checkpoint 结构建立规模教学；代价是主干没有 audio/codec/speaker direct coverage，必须把 dual-track、16-codebook MTP、speaker encoder、codec masks、audio length 和 checkpoint mapping 移植进 text-oriented framework，**TTS semantic port 风险显著更高**。适合用户把“先学超大规模框架”置于“先保持 exact model semantics”之上；本提案不推荐为默认。[SRC-026][SRC-027][SRC-077][SRC-079][SRC-084][SRC-085]

### Alternative B — minimal exact-only MindSpeed-MM

只选择 CAND-001，暂不获取 CAND-002/003/004。好处是 acquisition/许可/内容范围最小，所有分析围绕 exact speaker-SFT；代价是 TP/PP/CP/EP、多节点 resume/global-batch 等规模知识，以及 multi-codebook/reference/data pipeline 的外部对照缺口更大，容易把单个项目配置误读成成熟完整生命周期。适合用户只要 narrow 12Hz speaker-SFT 源码导读；不适合声称完整 N→D 迁移参考。[SRC-019][SRC-021][SRC-066][SRC-067]

### Alternative C — speech-led architecture study

以 MOSS-TTS 为结构学习主线，辅以 MindSpeed-MM。它对 Delay/multi-codebook/reference conditioning/data/SFT 的讲解更丰富，但 MOSS upstream 没有 Ascend training，CUDA/PyTorch 2.9.1 与 target 栈错位，且 topology 并非 Qwen3-TTS 16-codebook residual MTP。这个路线适合纯 architecture survey，**不推荐**作为 Ascend 主训练链。[SRC-030][SRC-031][SRC-089][SRC-092][SRC-093]

## 12. Exact next-stage scope under the approval

用户已同时批准 **DEC-002 route selection** 和 **DEC-001 acquisition mode**；下一阶段仅可执行以下 scope：

1. 只获取用户许可的 **source-only fixed revisions**，默认放在外部或 ignored read-only checkout；不下载权重、数据或模型资产。
2. 对获批 revisions 建立源码索引：entry points、训练/data/device/operator/checkpoint/conversion/eval 路径与固定链接。
3. 建立 Qwen3-TTS target checklist→主项目→satellite 的调用链、缺口和 N→D 迁移映射，持续使用四态证据标签。
4. 设计多页 HTML **内容架构**与页面清单，所有代码展示只用短引用和 immutable source links；是否实际生成页面由后续任务另行授权。

明确排除：不实施实际 NVIDIA/CUDA→Ascend/NPU 迁移代码，不修改候选源码，不运行训练/推理/eval，不执行 910B smoke，不下载权重/数据，不把仓库 vendor 进 `references/`，也不把 CANN 8.5.2 标记为兼容。第 11 节的替代路线及后果保留为历史决策记录，本次批准没有要求转向它们。

## 13. Source index

以下是本决策直接依赖的正式 `SRC-*` 组；完整字段、grade、retrieval date 与 URL 以 `research/source-ledger.csv` 为准。

| Evidence group | Source IDs | Decision use |
| --- | --- | --- |
| Official Qwen3-TTS target | SRC-001, SRC-002, SRC-003, SRC-004, SRC-005 | fixed official tree、公开 SFT 边界、报告阶段声明、target checklist |
| MindSpeed-MM identity/ref/tree | SRC-018, SRC-019, SRC-048, SRC-065, SRC-066, SRC-100 | canonical/mirror boundary、fixed SHA、moving master、tree/tag inventory |
| MindSpeed-MM exact route | SRC-020, SRC-021, SRC-022, SRC-023, SRC-043, SRC-067, SRC-068, SRC-069, SRC-070, SRC-072, SRC-073, SRC-074 | exact SFT、FSDP2、NPU/data/checkpoint/export 与验证缺口 |
| MindSpeed-MM environment/license | SRC-024, SRC-071 | documented version and aggregate-license acquisition boundary |
| MindSpeed-LLM identity/ref/tree | SRC-025, SRC-026, SRC-049, SRC-075, SRC-076, SRC-101 | fixed snapshot、moving refs、external dependency boundary |
| MindSpeed-LLM scale lifecycle | SRC-027, SRC-044, SRC-045, SRC-046, SRC-077, SRC-078, SRC-079, SRC-080, SRC-081, SRC-082, SRC-083, SRC-084, SRC-085 | text-Qwen MCore/FSDP2 parallel/checkpoint evidence and TTS attribution boundary |
| MindSpeed-LLM environment/license | SRC-028, SRC-029, SRC-086, SRC-087 | CANN version rows、aggregate notices、install/dependency drift |
| MOSS-TTS speech/codec | SRC-030, SRC-031, SRC-050, SRC-088, SRC-089, SRC-090, SRC-091, SRC-092, SRC-093, SRC-102, SRC-103, SRC-104 | Delay/SFT/data/config、CUDA mismatch、fixed submodule/license |
| CosyVoice optional comparison | SRC-032, SRC-033, SRC-051, SRC-094, SRC-095, SRC-096, SRC-097, SRC-098, SRC-099, SRC-105, SRC-106, SRC-107 | staged data/train/eval/export、CUDA mismatch、fixed submodule/license |

**已完成决策检查点：**用户于 2026-07-17 批准默认组合（CAND-001 main + CAND-002 scale satellite + CAND-003 speech/codec satellite；CAND-004 optional 且未选入）和 external/ignored read-only source-only acquisition，未要求路线变更。下一检查点是完成获批源码获取状态的独立核对，再基于实际固定源码树编写 Phase 2 plan；此处不声称任一项已完成。
