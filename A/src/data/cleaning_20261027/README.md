# 2026-10-27 冻结版盘点与有限清洗复现

此入口复现 [本次处理范围](../../../reports/data/20261027-cleaning/README.md)：先只读盘点全部附件，再生成三个交付文件。唯一修改是派生评分卡中 `summary!AX2:AX13` 的 barnyard 引用；不改变任何观测数值。它只适用于 [input_manifest.json](input_manifest.json) 锁定的九个官方附件，**不是可套用其他数据的通用清洗器**。通用方法仍由 [beer-data-cleaning skill](../../../.agents/skills/beer-data-cleaning/SKILL.md) 定义。

## 环境与输入

- 验证环境：Windows、Python 3.12.14、Node v24.19.0；Python 包见 [requirements.txt](requirements.txt)。
- 工作簿内容由 Codex desktop bundled `@oai/artifact-tool` 2.8.99 创建/计算/渲染。该包是私有 bundled 依赖，不能假设可从公共 npm 安装；请在有该运行时的 Codex 环境调用 `load_workspace_dependencies` 获取 Python、Node 和 node_modules 的实际路径。不包含跨平台或桌面 Excel 人工验收承诺。
- 从队内原始附件副本取得 `1.csv`、`2.csv`、`3.xlsx`、`4.csv`、`5.csv`、`6.csv`、`7.csv`、`8.xlsx`、`数据说明.txt`。原始取得记录见 [PR #1](https://github.com/Ferrystd/mathorcup/pull/1) 及 [provenance.json](../../../reports/data/20261024-skill/provenance.json)。原始附件不入 Git，未配置新的受控共享位置。
- 输入目录中普通文件必须与九文件清单完全一致，任何哈希差异都会停止。不同版本应重新盘点，不能通过改清单跳过审查。

## 一次完整复跑

在本仓库根目录运行。替换前三个运行时路径和输入路径；输出目录名每次用新的值。以下 `A/runs` 与 `A/outputs` 是被忽略的工件父目录，不会覆盖既有运行。

```powershell
$taskPython = 'C:/实际运行时路径/python/python.exe'
$taskNode = 'C:/实际运行时路径/node/bin/node.exe'
$taskModules = 'C:/实际运行时路径/node/node_modules'
$taskInput = 'D:/实际数据位置/附件'
New-Item -ItemType Directory -Force A/runs,A/outputs | Out-Null
$env:PYTHONUTF8 = '1'
& $taskPython -B A/src/data/cleaning_20261027/reproduce.py `
  --input $taskInput `
  --run-dir A/runs/cleaning-new-run `
  --output-dir A/outputs/cleaning-new-run `
  --node $taskNode --node-modules $taskModules --render
```

禁止 `python -O`，因为审计断言必须启用。程序拒绝已有运行/输出目录以及输入、运行、输出路径互相包含；始终只读输入。失败保留诊断文件，修复原因后换一个新运行名重跑。入口会在运行目录建立指向 bundled node_modules 的连接，不安装或修改全局包。

执行顺序为：输入哈希校验 → 逐字段盘点 → HTML 报告 → 原表预览（`--render`）→ 工作簿创作和公式依赖验证 → 保留原 OOXML 的选择性打包与独立读取核验 → 逐列日志 → 最终预览（`--render`）→ 原始哈希复查。只从此入口运行，内部脚本依赖自动生成的 `MATHORCUP_CONTEXT`。

## 结果与验证

输出目录严格只包含：

| 文件 | 内容 |
|---|---|
| `clean.csv` | `1.csv` 的字节一致副本，250×234，73 个 NA 原样；没有删行、删列、填补或新增标记 |
| `cleaning_log.md` | 1,599 个实际源字段的逐列动作、理由、影响行数；12 处公式台账和文件哈希 |
| `清洗前后对照表.xlsx` | 第一张表为 1,599 行前后缺失率、均值、负值占比；其余 13 张为修正引用后的 `3.xlsx` 派生副本 |

运行目录另外保存：`数据资产盘点.html`（完整 15 列字典、每列五项依据、A/B/C 清单）、`inventory.json`、`comparison_rows.json`、`dependency_check.json`、`verification.json`、`run_manifest.json`、各阶段日志、创作中间文件和预览图。HTML 的 2,071 条记录包含两份 SHAP 分层视图的 472 个重复字段；清洗台账按 1,599 个实际源字段计数。HTML 保留清洗前判定，不会因后续有限修正而重写历史。

`run_manifest.json` 记录完整 Git SHA、dirty 状态、每个实现文件哈希、输入/输出哈希、环境和阶段退出码。只有 `complete=true` 才表示整次运行结束。Excel 包含生成元数据，日志引用该文件哈希，因此不同运行的 XLSX/日志字节哈希可能不同；应核对源文件、公式差异与逐单元格内容，不要求不同时刻生成的容器字节完全一致。`clean.csv` 必须始终与输入字节一致。

Artifact Tool 完整导出可能重写模板原生部件，所以 `package.py` 只移植它实际创作的 12 个公式和审计表，保留原模板部件；openpyxl 仅独立读取检查，不用于保存。最终核验原卡 12 份工作表 XML 字节不变、原单元格样式/缓存/合并/验证不变、仅 12 个公式变化。内存依赖测试分别模拟 1、3、6 分后恢复空输入，最终文件没有测试标记。

## 科学解释边界

NA 原文确实存在不等于其机制为随机或结构性。九个化学缺失列、三个评论全缺失列均没有同时满足“建议修正白名单”和“机制已证实”，所以本轮不填补。原模板全空，缓存 0 不是真实回答。本次没有模型、切分、0–6 标签恢复或 Top-3 结果。

逐列评分来源依据为 [Schreurs 等论文](https://doi.org/10.1038/s41467-024-46346-0) 的 Methods / Trained panel 和 Online reviews；方法取舍见 [已有文献索引](../../../.agents/skills/beer-data-cleaning/references/literature.md)。分布和反解只是诊断，不能替代字段单位、配对原值和完整预处理血缘。待确认项保留，不将本次有限清洗完成等同于建模数据关卡通过。
