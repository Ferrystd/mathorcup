# 清洗 skill 交付核验

2026-10-24。当前阶段：原始A题附件已取得并做只读初检；清洗skill已编写。未开始正式清洗、插补、异常删样、建模或G1最终验收。

交付入口：[beer-data-cleaning/SKILL.md](../../../.agents/skills/beer-data-cleaning/SKILL.md)。文献、方法决策、数据类型和冲突记录都从该入口可达。用户指定的 *Predicting and improving complex beer flavor through machine learning* 作为L1主来源；PPT只借鉴方法框架。

## 已完成的检查

- `skill-creator/scripts/quick_validate.py`：通过；名称、frontmatter、占位内容检查。
- 所有skill内部本地Markdown链接存在，无未完成脚手架。
- `inspect_inputs.py`在真实9个附件上运行：完成，输入文件运行前后SHA-256相同。
- `probe_semantics.py`完成样本键、正值尺度锚点、空卡响应及公式引用检查。它是本版本证据脚本，不是通用清洗器。
- 两脚本第一版在`A/runs/skill-validation-20261024/`重跑，两个JSON分别逐字节一致。后续语义检查补充了隐性替代证据：最终R3在`A/runs/skill-validation-20261024-r3/`及`-r3-repeat/`重跑一致，报告采用R3；R1/R2证据保留。
- A题内部压缩包CRC通过；解出的全部文件与压缩包相应成员SHA-256一致。
- 通用初检器拒绝覆盖已有输出，拒绝向原始输入目录写报告；拒绝后已有文件字节不变。
- 原始附件与完整重跑目录均命中Git忽略规则。

结构验证只证明文件可用，重跑只证明初检可复现，均不证明清洗策略已经实测有效。人类对样本配对、评分维度和阈值的复核尚未进行。

## 独立行为审查及修订

审查agent在未提供预期答案的模拟请求下读取skill及真实1/3/4/7/8附件，只制定下一步动作，不执行清洗。其方案正确隔离空卡缓存零、受损ID、评论全缺失列及未知尺度，并未建议填零或整体截尾。

审查发现CO2校准值缺失、部分校准零值在1.csv中已有有限常数。已在SKILL步骤3、全流程拟合边界、methods及dataset-profile第9项加入隐性缺失/疑似上游替代检查，并补充受影响键/值证据。规则要求查来源而非自动恢复NA；无法核实上游范围时不宣称端到端无泄漏。未将疑似半最小值模式当作已确证处理规则。

独立agent已回查修订后的skill、脚本及JSON，确认问题已解决，无新增必须修复项。该确认不替代人类验收。

## 环境与复现

运行解释器：`C:/Users/admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe`（通过Codex依赖工具取得）。Python及库版本见JSON。普通`python`命令在本机指向另一环境，不能假设已有pandas/openpyxl。

脚本参数与命令见skill的dataset-profile。验证器使用系统Python的PyYAML，并设置`PYTHONUTF8=1`；未改动全局依赖。

## 版本与交接

工作分支：`codex/a-data-cleaning`；基线完整SHA见[provenance.json](provenance.json)。该文件的`run_state`记录初检运行时实现尚未提交的历史状态；本PR将skill、脚本与审计摘要一并纳入版本管理，具体提交以PR记录为准。生成的摘要是探索阶段记录；正式清洗验收应按项目规则冻结代码版本后独立复跑。原始包由用户提供，未声称由agent完成下载；第二份队内备份仍待配置。
