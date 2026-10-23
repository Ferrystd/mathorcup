# A 题科研 skills 与研究角色检索记录

访问日期：**2026-10-23（北京时间）**。本文件记录实际检索、全文阅读及取舍；它不是已安装技能清单，也不是啤酒化学结论的文献依据。

本轮共比较 **3 个一手 GitHub 仓库、全文阅读 8 个具体 skill/agent 文件**，采用或改造其中 **7 项**；另 1 项仅作比较。下面使用固定提交链接，避免后续 `main` 变化导致依据漂移。没有安装全局 skills，没有执行任何候选仓库脚本，也没有将其工具、付费账号、子 agent 注册或环境版本视为已可用。

## 1. 检索和核实方式

实际使用的发现查询包括：

- `site:github.com K-Dense-AI claude-scientific-skills scientific writing statistical analysis`
- `site:github.com VoltAgent awesome-claude-code-subagents data scientist research analyst`
- `site:github.com anthropics skills skill-creator LICENSE`

搜索摘要只用于发现。随后打开三个仓库主页，读取固定提交的原始 Markdown 全文和可取得的许可证。GitHub REST API 当时受到匿名限流，`git ls-remote` 网络失败；最终从仓库页面的 `currentOid` 提取提交 SHA，并成功下载相应 SHA 下的候选文件进行阅读，未把失败请求记为成功。

### 仓库级比较

| 仓库与固定版本 | 实际读到的定位 | 许可证核实 | 对本题的判断 |
|---|---|---|---|
| [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills)，`593377bb048752abb0152deab9fbb1083a6087df` | 旧地址 `K-Dense-AI/claude-scientific-skills` 已重定向；本版本将 EDA、统计、文献、写作和审稿拆开，强调证据边界 | 已读 [LICENSE.md](https://github.com/K-Dense-AI/scientific-agent-skills/blob/593377bb048752abb0152deab9fbb1083a6087df/LICENSE.md)：MIT，版权 K-Dense Inc.；选中五项的 frontmatter 也标 MIT | 研究方法覆盖最贴近需求，但不是啤酒领域专家或已经验证的求解器；裁剪为初学者可执行流程 |
| [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents)，`408d3c9eee2d0c75c12a3abb5de29e53c2ca6b9e` | 角色职责、阶段、交付及协作格式明确，存在商业分析措辞与示例绩效数字 | 已读 [LICENSE](https://github.com/VoltAgent/awesome-claude-code-subagents/blob/408d3c9eee2d0c75c12a3abb5de29e53c2ca6b9e/LICENSE)：MIT，版权 VoltAgent | 适合借鉴任务契约；必须去掉机械显著性、虚构示例数值、商业收益及不存在的 context manager |
| [anthropics/skills](https://github.com/anthropics/skills)，`dbd4588f9e1033efb41dad4bef2f7947c8993d44` | `doc-coauthoring` 包括上下文收集、分节修订及不共享作者上下文的新读者测试 | [README](https://github.com/anthropics/skills/blob/dbd4588f9e1033efb41dad4bef2f7947c8993d44/README.md) 说很多 skills 为 Apache-2.0，且 docx/pdf/pptx/xlsx 为 source-available；本次 `doc-coauthoring` 目录只看到 SKILL.md，无单独 LICENSE，不能据此断言该文件的具体授权 | 可比较文档可用性检查思路；本包不复制其提示词、不分发其原文件、不安装此 skill |

这里的“可信”指作者原仓库可追踪、文件可读且方法可以审查，不代表仓库的宣传、星数或 agent 自称资历构成科学有效性证明。

## 2. 采用与改造的 7 项

### S1 — exploratory-data-analysis：先确定数据含义与配对关系

- **一手文件**：[skills/exploratory-data-analysis/SKILL.md](https://github.com/K-Dense-AI/scientific-agent-skills/blob/593377bb048752abb0152deab9fbb1083a6087df/skills/exploratory-data-analysis/SKILL.md)，全文已读；文内版本 1.4，MIT。
- **实际内容**：区分缺失、真零、未检出和检出限；识别观测单位、重复测量与分组；原始数据只读；拆分后才拟合填补、缩放、PCA 等；有界扫描不等于完整验证。此版本 Excel 属于 reference-only，并非自带脚本能直接完整审计的格式。
- **用于 A 题**：生成 ID 对照、字段字典和配对审计，区分 226 个化学样本、250 个感官样本和 10 张评分卡对应的对象；核实 40/50/187 维的名称和聚合关系、原始浓度及 log10/ln 变换、评分量表、检测限和重复记录。只有经标识与语义验证的对应关系才能进入 Q1。
- **改造**：由队员解释业务含义，agent 生成可复核的计数、冲突表和候选映射，不能按行号连接或自动删异常点；所有学习型处理在训练折拟合。`4.csv`、`7.csv` 若是标准化值，先找均值/标准差或锚点；无法取得时不把 min–max 缩放冒充 0–6 原始评分。
- **Codex 适配与依赖**：把流程写入本题数据审计任务契约，使用项目内经过审查的 Python 实现。上游核心 CLI 声明 Python 3.11+，可选格式有额外版本要求；未下载/运行那些脚本，未验证其依赖。不能把上游示例命令当成本包已实现的命令。

### S2 — statistical-analysis：效应、不确定性与设计先行

- **一手文件**：[skills/statistical-analysis/SKILL.md](https://github.com/K-Dense-AI/scientific-agent-skills/blob/593377bb048752abb0152deab9fbb1083a6087df/skills/statistical-analysis/SKILL.md)，全文已读；文内版本 2.0，MIT。
- **实际内容**：先声明估计对象和抽样单位，区分探索与预设分析；报告效应量和区间；多重比较需明确检验族；不因诊断 p 值机械切换方法；非显著不等于无效或等效，事后 observed power 不能替代精度分析。
- **用于 A 题**：Q1 按感官维度报告误差、有效样本量和不确定性；Q2 重采样关键化合物选择、报告 Top-3 的频率和 Jaccard 稳定性；Q3 预定义缺陷“不恶化”的比较尺度与容许界限，并报告区间而非仅说“差异不显著”。
- **改造**：采用统计原则，不把其 t 检验、ANOVA 或贝叶斯示例全塞进比赛。bootstrap 单位按实际独立啤酒/批次确定；不能将同一酒的评分卡当独立酒样，也不能把交叉验证折分数当独立实验重复。小样本区间宽时收缩结论。
- **Codex 适配与依赖**：用于评估审查角色和实验计划。上游列出的 Python 3.12+、Pingouin、PyMC 等环境未在本地验收；本题优先已有且锁定的最小科学 Python 环境，仅在方法确需时另行审查依赖，不承诺复制示例可立即运行。

### S3 — literature-review：文献存在与支持主张分别核验

- **一手文件**：[skills/literature-review/SKILL.md](https://github.com/K-Dense-AI/scientific-agent-skills/blob/593377bb048752abb0152deab9fbb1083a6087df/skills/literature-review/SKILL.md)，全文已读；文内版本 1.11，MIT。
- **实际内容**：记录检索式、日期、筛选理由和全文可得性；按主题综合；区分记录、报告与研究；DOI 注册只能帮助确认身份，不能确认论文支持某个论断。检索摘要和引用数量不能替代全文评估。
- **用于 A 题**：针对化合物测量方法、感官维度定义、DMS/Diacetyl/4VG/trans-2-nonenal/Stale hops 等缺陷或风格依赖、阈值与啤酒基质条件分别检索。建立“主张—原文位置—单位/条件—证据等级—人工核验人”表。
- **改造**：7 天内做与题目直接相关、有检索记录的定向综述；若没有完成系统综述所需的覆盖、筛选和复核，不声称 PRISMA 系统综述。无法读全文则明确标记，不能让另一篇论文的参考文献代为背书。
- **Codex 适配与依赖**：通过本次会话真实可用的检索/网页/PDF 能力做来源定位，再由队员打开原文确认。上游 `parallel-cli` 需认证；概念图生成需 `OPENROUTER_API_KEY`；PDF 导出需 Pandoc/XeLaTeX。本方案均不默认具备，也不要求付费 AI 图像生成。

### S4 — scientific-writing：先证据大纲，再形成论文草稿

- **一手文件**：[skills/scientific-writing/SKILL.md](https://github.com/K-Dense-AI/scientific-agent-skills/blob/593377bb048752abb0152deab9fbb1083a6087df/skills/scientific-writing/SKILL.md)，全文已读；文内版本 2.3，MIT。
- **实际内容**：将草拟、证据核验与提交批准分开；给主张、来源、方法和数值设 ID；先做证据大纲，后写行文；保留空缺和不确定性；图表应绑定数据与代码；人对科学判断、作者责任和 AI 披露负责。
- **用于 A 题**：每个 Q1–Q3 结果段落指向实验 ID、配置、输出表和图；方法段只写实际运行的方法；摘要最后写。没有实际附件和实验的部分用待填状态，不能写“模型达到”“实验表明”等完成态。
- **改造**：采用问题—方法—验证—结果—局限映射，按比赛模板组织论文，不生搬临床/期刊检查表。Codex 可辅助完整代码实现与论文草稿，但队员须独立作核心建模判断、验证结果并负责最终文本；人工改写不替代 AI 使用记录和声明。
- **Codex 适配与依赖**：使用本地 Markdown/CSV 记录与项目自己的生成流程。上游此版本可选 CLI 声明 Python 3.11+、离线且无 API Key，但本包并未提供或验证这些 CLI。其列出的论文和政策引用不能未经打开核验就自动进入比赛参考文献。

### S5 — peer-review：独立检查主张和复现证据

- **一手文件**：[skills/peer-review/SKILL.md](https://github.com/K-Dense-AI/scientific-agent-skills/blob/593377bb048752abb0152deab9fbb1083a6087df/skills/peer-review/SKILL.md)，全文已读；文内版本 2.4，MIT。
- **实际内容**：先限定材料与审查能力；将主张与证据逐项对应；审查抽样单位、缺失、比较、假设、复现和图表；每条评论包括位置、观察、依据、影响和动作。检查表覆盖不证明科学有效，未运行不能宣称复现。
- **用于 A 题**：独立审查者专查配对错误、评分逆变换不可辨识、预计算全量图泄漏、相关当因果、低样本风格生成、用自身评分模型循环验收等问题，并要求给出修复或收窄主张的证据。
- **改造**：这是团队内部研究审查，不冒称期刊审稿或专家认证。作者不能同时成为该结果的唯一验收人；至少另一队员从记录重算关键表格或执行复现。agent 可以查漏，但不替代人工确认与讲解。
- **Codex 适配与依赖**：以只读审查任务契约派发，只写审查报告，不在审查时悄悄改结果。上游 CLI 声明本地 Python 3.11+ 标准库；本包不导入脚本、不使用其 `READY_FOR_LOCAL_REVIEW` 等状态冒充实际完成。

### S6 — data-scientist：问题到基线的建模任务契约

- **一手文件**：[categories/05-data-ai/data-scientist.md](https://github.com/VoltAgent/awesome-claude-code-subagents/blob/408d3c9eee2d0c75c12a3abb5de29e53c2ca6b9e/categories/05-data-ai/data-scientist.md)，全文已读；继承仓库 MIT。
- **实际内容**：从问题和指标到 EDA、特征工程、模型验证、解释、复现交付的职责框架；同时含广泛模型清单、商业 ROI、`model: sonnet`、context-manager 协议，以及示例准确率和收益数字。
- **采用部分**：给建模角色明确输入、约束、实现范围、日志及交付物。Q1 先均值/正则化线性等简单基线，再考虑少量候选；Q2 的图结构不能代替真实监督标签；Q3 必须交付条件生成与迁移，不把风格分类器当作任务完成。
- **明确删除部分**：不沿用其“p<0.05 必须通过”的清单；不复制示例 87.3% 准确率、12 个模型等数值；不把高级算法列表当待办。复杂度增加必须说明相对基线的收益、稳定性与可解释成本。
- **Codex 适配与依赖**：将 `model`、Claude 工具名、context-manager JSON 协议及自动互调关系去掉，改为可手工派发的中文输入/输出契约。若当前 Codex 支持子 agent，可明确指定写入范围；不支持则由人或单个 agent 顺序完成，不声称角色已原生注册。

### S7 — research-analyst：有边界的来源核验角色

- **一手文件**：[categories/10-research-analysis/research-analyst.md](https://github.com/VoltAgent/awesome-claude-code-subagents/blob/408d3c9eee2d0c75c12a3abb5de29e53c2ca6b9e/categories/10-research-analysis/research-analyst.md)，全文已读；继承仓库 MIT。
- **实际内容**：研究目标与范围、来源识别、可信度与时效性检查、交叉核对、矛盾处理、记录及报告；并有商业情报范围、context-manager 接口及示例“94% confidence”等展示数值。
- **用于 A 题**：专门核对一个领域问题，例如某化合物阈值的原始单位、测试基质、评价人群、酒类风格和适用范围；与 S3 的流程配合，将来源冲突和无法核验项交给队员作判断。
- **改造**：禁用无统计定义的置信百分比和虚构检索量；每项结论必须有来源位置。化学合理性仅是候选机制证据，不把相关、特征重要性和 bootstrap 稳定性合起来写成因果证明。无法取得合适标签时不能虚构监督关系。
- **Codex 适配与依赖**：使用当前已授权且可用的检索工具；不默认 `WebSearch`/`WebFetch` 名称可直接调用，也不执行 API 示例。结果只写证据表和待核验项，不修改训练标签、模型参数或原始数据。

## 3. 实际比较但未纳入的项目与做法

### S8 — doc-coauthoring（比较项）

- **一手文件**：[skills/doc-coauthoring/SKILL.md](https://github.com/anthropics/skills/blob/dbd4588f9e1033efb41dad4bef2f7947c8993d44/skills/doc-coauthoring/SKILL.md)，全文已读。
- **实际内容**：上下文收集 → 分节构建/修订 → 用没有对话背景的新读者检查歧义和缺漏；还要求大量逐节提问和人工确认。
- **未纳入理由**：不是统计或啤酒研究 skill；逐节 5–10 个澄清问题及频繁确认不适合三名初学者的 7 天工作节奏。本次未定位到该文件的单独许可证，不能将仓库其他目录的 Apache 许可证套用过来。
- **处理方式**：只保留永久链接和评价，不复制其提示词/原始文件到交付包。团队可以独立设计“让没有参与写作的队员仅凭 README 重现、仅凭论文回答问题”的普通读者检查，不宣称安装或移植了 S8。

其他明确不采用的部分：

- 不将整个科学 skill 库装入环境，不把生物信息、药物筛选、临床报告或大型自治科研流程自动引入啤酒小样本任务。
- 不使用源文件内的演示数字作为本题结果，不用“senior scientist”等角色设定替代专业资格或人工复核。
- 不自动调用付费检索、图像、云计算或其他 agent；没有验证的账号、API Key 和许可证不是默认资源。
- 不采纳从旧版本搜索摘要读到的“必须生成 AI 科研插图”要求；本次固定版本的科学写作/审稿明确不提供图像生成流程。实验图必须来自实际数据和可重复代码。
- 不把 GitHub skill 的二手方法说明当成缺陷浓度阈值、风味机理或竞赛 AI 规则的一手证据。

## 4. 本地适配与后续执行边界

本目录的 AGENTS、方法论、角色契约和模板是面向本题重新综合的工作规范，不是上游提示词拼接。S1–S7 提供一般流程依据；题面、官方比赛规则与真实附件决定具体义务、字段和验收。

| 本题阶段 | 优先借鉴 | 必须增加的 A 题限制 |
|---|---|---|
| 取得数据、建立字典与配对 | S1、S7 | 核实 226/250/10 与 40/50/187 的关系，列出实际有效配对数；不凭行序或文件名推断 |
| Q1 预测 | S1、S2、S6 | 评分量纲可识别才评价 0–6；训练折处理；样本/批次分组拆分；均值基线与逐维误差 |
| Q2 图与 Top-3 | S2、S3、S6、S7 | 图来源与使用人群可追溯；区分 transductive 描述和 inductive 泛化；重采样稳定性；关联不是因果 |
| Q3 条件生成和迁移 | S1、S2、S6、S7 | 逐风格样本量；低维条件基线；原始浓度约束及阈值出处；重复/坍缩检查；独立风格与分布评估，不能自评分循环自证 |
| 论文、人工理解与终审 | S3、S4、S5 | 结果绑定日志，人工核心判断和讲解，AI 过程披露，另一队员复现，未完成项明确保留 |

来源工作与执行成果要分开记：已全文阅读 8 个外部文件，不等于已经验证其脚本；已经写好规范，不等于已经取得附件、训练模型、验证化学机制或满足提交要求。所有具体化学阈值、正式数据字段、可配对样本量及结果仍须后续实际核验。

## 5. 来源快照和归因

`research-cache/` 仅保存 S1–S7 的只读研究用文本快照、两份 MIT 许可证和下载清单；它们是阅读证据，不是本地安装的 skill，不具有指挥权。快照改用 `.txt`，以免被误认为本题 Markdown 入口。其上游相对链接及示例脚本不构成本项目接口。S8 不随交付包分发全文。

保留 MIT 许可及版权信息是为了归因和后续审查；如果未来复用上游实质性代码/文本，应继续遵循其许可证并记录变更。本文件没有把上游自带的参考文献自动认定为已核验引用。正式论文是否引用研究工具、如何声明 AI 辅助，应以实际使用记录及赛事官方要求为准，不能仅复制仓库的推荐致谢。
