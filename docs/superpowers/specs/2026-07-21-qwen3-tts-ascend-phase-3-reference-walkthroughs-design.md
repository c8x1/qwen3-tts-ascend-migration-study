# Phase 3 参考工程走读与迁移映射设计

## 目标

将已选定的三个成熟工程转化为可追溯、可逐页学习的中文走读材料，并把其已验证的工程事实映射到 Qwen3-TTS 向 Ascend 910B 训练迁移时需要理解和验证的工作面。交付物是研究与学习站点，不是 Qwen3-TTS 的 Ascend 迁移实现。

## 已确认的范围与边界

- 主锚点为固定 revision 的 MindSpeed-MM；它承担最接近 Qwen3-TTS SFT/NPU 训练工程的解释责任。
- MindSpeed-LLM 是规模化训练卫星：解释分布式并行、启动、通信、性能与恢复训练，但不被表述为 TTS 实现。
- MOSS-TTS 是语音/codec 卫星：解释 TTS 特有的数据与模块边界，但不被表述为 Ascend 训练已验证实现。
- Qwen3-TTS 官方目标源码、四个固定 revision、既有 evidence/catalog/index/coverage 契约继续是唯一的本地源码事实基础。
- 既有双环境 lane 不变：原生学习 lane 为 PyTorch/torch-npu 2.7.1 + CANN 8.5.0；目标验证 lane 为 PyTorch/torch-npu 2.7.1 + CANN 8.5.2。后者兼容性始终标记为 `pending_hardware`，直到真实 910B 验证。
- 覆盖单机单卡理解、单机多卡与多机路径；不声称实际 CUDA、NPU、8 卡或多机训练执行。
- 不追踪或公开 vendored 源码、权重、数据集、音频样本、checkpoint、token 或本地绝对路径。

## 方案比较

1. **主锚点 + 两个卫星 + 映射总线（已选）**：先保留三个工程各自的原始边界，再以独立映射页汇总 Qwen3-TTS 的迁移面。读者可以先理解工程，再理解为什么需要迁移改造。
2. **先写映射、后回填证据**：较快产出清单，但会提高将分析推断误写为事实的风险。
3. **生命周期混排比较**：每个页面横向比较三个项目，信息密度高，但会掩盖每个工程的入口与控制流，不利于初学者走读。

## 信息架构

### 主锚点：MindSpeed-MM

拆分为可独立阅读的章节：工程总览与启动入口、配置与环境、数据和多模态样本、模型/适配层、训练循环与优化器、NPU 与分布式路径、checkpoint/恢复、性能与排障。每个章节给出固定 revision 的文件/符号链接、调用关系、可迁移性判断和未证明边界。

### 规模化卫星：MindSpeed-LLM

以并行与运行方式为中心：启动脚本、并行维度与组、通信/拓扑、训练恢复、日志与 profiling、单机多卡到多机的扩展路径。页面明确区分该项目对文本 Qwen 规模化训练的事实，和对 Qwen3-TTS 的分析性借鉴。

### 语音卫星：MOSS-TTS

覆盖 TTS/codec 模块边界、音频/文本数据责任、训练与推理入口、与 Qwen3-TTS 的 token/声码器/说话人相关差异，以及其不能直接证明 Ascend 可训练的地方。受限音频与数据资产只描述排除边界，不嵌入或重新分发内容。

### 迁移映射总线

映射页以 Qwen3-TTS 训练生命周期组织：

1. 环境、版本和依赖边界；
2. Python/CUDA 假设、torch-npu 与算子风险；
3. 数据、tokenizer、音频处理与 batch/collate；
4. 模型前向、loss、精度与显存；
5. 单机多卡并行；
6. 多机启动、通信与故障恢复；
7. checkpoint、导出、评测与回归验收；
8. 性能剖析、调优顺序和硬件验证清单。

每一个映射项均列出：Qwen3-TTS 的目标表面、参考工程证据、建议的保守迁移方向、适用规模、状态、风险和真实 910B 验证条件。没有固定源码或官方资料支持的内容只能写作 `inference` 或 `pending_hardware`。

## 数据流与证据模型

四个既有 source index 提供文件、符号和配置键定位。Phase 3 新增参考工程 evidence 与 coverage 数据，生成器从这些结构化输入渲染多个 HTML 页面和本地搜索文档。验证器必须能够确认：

- 每个展示的源码主张连接到一个固定 revision、文件和行范围；
- 每个关键章节具有 evidence，或具有显式的排除/待验证说明；
- reference facts、project claims、analysis inferences 和 hardware-pending 内容使用文字与非颜色状态标识；
- 所有相对链接、标题锚点、ARIA 引用、页面目录和本地搜索条目完整；
- 生成站点离线可用，且无远程运行时依赖。

## 页面与交互约束

保持现有暖纸张三栏 shell、可收缩双侧栏、移动端抽屉、键盘操作、无 JavaScript 降级、打印和本地搜索机制。新章节通过现有导航树、相邻页链接、源文件/符号索引与迁移映射入口接入；不重新设计 UI，也不把项目走读和映射压缩进单页。

## 并行执行划分

在规划获批后，使用三个独立子代理并行完成只读的源码/官方资料核验与章节提纲：

- Agent A：MindSpeed-MM；
- Agent B：MindSpeed-LLM；
- Agent C：MOSS-TTS 与语音/codec 对照。

主代理负责统一的 Qwen3-TTS → Ascend 映射、数据契约、页面集成、验证、审查与提交。子代理只写其隔离产物或报告，不直接修改共享生成器和公共导航，避免冲突。

## 错误处理与验收

输入缺失、revision 不匹配、行范围越界、coverage 漏项、未知状态、生成页遗漏或断链必须导致验证失败。对硬件兼容、吞吐、显存、算子覆盖和多机稳定性，不用文档推断替代真机证据；页面应明确列出下一次真实验证所需的命令、观测量和通过条件，但不执行它们。

验收包括现有 Python/Playwright 基线，以及新增的 reference evidence、reference coverage、mapping contract、生成页、搜索、离线、无脚本、可访问性、响应式与公开文件边界检查。

## 非目标

- 不实现或运行 Qwen3-TTS 的 Ascend/NPU 迁移。
- 不承诺 CANN 8.5.2 与 PyTorch/torch-npu 2.7.1 的真实兼容性。
- 不下载模型、数据集、checkpoint、音频或 token。
- 不把 MindSpeed-LLM 或 MOSS-TTS 描述成 Qwen3-TTS 的一键替代品。

## 决策与偏差记录

若具体库版本、算子替换、并行策略或真实集群拓扑无法由固定源码与官方资料确定，采用最保守解释，标为 `inference` 或 `pending_hardware`，并在 `IMPLEMENTATION_NOTES.md` 记录。只有会改变所选三项目角色、公开范围、硬件验证 lane 或迁移目标的决策才升级向用户确认。
