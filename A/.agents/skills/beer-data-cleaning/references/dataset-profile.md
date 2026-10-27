# A题附件实测快照与冲突

检查日期：2026-10-24；仅为skill设计进行只读检查，未执行清洗或训练。新版本需重新检查，不把本快照硬编码为任何数据集的预期结果。

原包：`D:/BaiduNetdiskDownload/2026年第七届MathorCup数学应用挑战赛—大数据竞赛初赛赛题.zip`，300525454字节，SHA-256 `9536c6e90cadabe48c3d108d4b01e20f22e29b8015a54eb223780a709b47c38a`。用户本地提供；官方入口见A/OFFICIAL.md。只解出赛道A，保留在忽略目录 `A/data/raw/official-20261024/`，B未展开。

完整字段统计与成员哈希：[inspection.json](../../../../reports/data/20261024-skill/inspection.json)。交叉检查：[semantic-probes.json](../../../../reports/data/20261024-skill/semantic-probes.json)。JSON的缺失数按显式NA候选标记统计，并非缺失机制证明。

| 文件 | 实测结构 | 类型与主要风险 |
|---|---|---|
| 1.csv | 250×234：3个元数据字段+231个数值字段；73个缺失格，分布于9列 | 化学/理化/派生混合表，不是226行；负值不自动判坏 |
| 2.csv | 231×231数值方阵，另含行名列 | 无缺失；轴标签同序，完全对称，对角为1；相关方法存在说明冲突 |
| 3.xlsx | beer_1…beer_12（每张使用范围101×33）+summary（13×52） | 卡片布局和汇总公式，不是10份已核验标签 |
| 4.csv | 250×53：3个元数据+50个数值字段；无缺失 | 专业品评汇总，非原始0–6；beer_id精度受损 |
| 5.csv | 50×50数值方阵，另含行名列 | 无缺失；对称、对角1；不能当样本 |
| 6.csv | 44×50数值交叉相关矩阵，另含行名列 | 非题面46×50；不补造两个化学指标 |
| 7.csv | 250×189：3个元数据+186个描述符字段 | 750个缺失格全部来自3个全NA列；论坛评论衍生量，不是187个专家评分 |
| 8.xlsx | 7张sheet | 阈值/名称字典、既有GBM重要性/SHAP、校准化学表、价格、空Sheet2；逐sheet分流 |

CSV六张表未发现整行完全重复。1/4/7均有250个唯一beer、22种风格；这不证明任意外部数据也能按该编号配对。

## 已发现的高风险事项

1. **精度受损的ID**：1.csv的beer_id有250个不同完整字符串，4/7只有96个科学计数法字符串。`5.41023E+12`不能恢复出唯一完整条码。按beer一对一联接得到250行且风格均一致，这是候选匹配证据；仍须独立血缘核对和人工抽查，不按beer_id去重或多对多联接。
2. **空卡公式零**：12张卡的单元格内容只在S3（Beer#）不同，主响应行均空；summary中公式缓存0不代表真实评分。包中未发现绘图、VML、ActiveX等非单元格响应部件。不能以刻度数字、编号或缓存零创建锚点。
3. **疑似公式错引**：summary的AX2（barnyard）和AR2（stale_hops）均引用`beer_1!$AG$76`；卡片R89才是Barnyard/horsey标识。将其列为需复核映射错误，不修改原件或把错误汇总直接作为标签。
4. **量纲与题面不一致**：将1.csv与8.xlsx的Calibrated chemical dataset按beer匹配，对正值锚点检查，pH、ethanol、color、bitterness、CO2、acetaldehyde的观测值均与log10(校准值)吻合，最大绝对误差均小于5e-10。有效n依次为250、249、250、248、211、249。它们不能因列名被当成原单位。此检查仅覆盖所列字段的正值锚点；零/负/缺失处理和其他列的变换仍须核验，不据此全表指数还原。
5. **相关方法冲突**：题面说2.csv为Pearson，压缩包数据说明.txt写2/5/6为Spearman，源论文Methods也使用Spearman。保留冲突；后续按核验的变量映射重算候选相关并对照，报告实际匹配方法及不一致，不能悄悄改题面或改矩阵。
6. **全缺失评论列**：palate_acetaldehyde、palate_acetate、palate_dentist各250个NA；不能填0并解释为味道不存在。
7. **标准化与来源**：原论文明确先按评分者处理再汇总，并区分评论词汇提取与专家量表。缺少原始评分者参数时不能只算4.csv均值/标准差恢复0–6；7.csv不可因同名描述词就当作同尺度监督标签。
8. **8.xlsx可用但要分辨**：校准表250×73含3个元数据和70个数值字段；阈值表含单位/别名，可作为候选依据，不代表所有缺陷阈值已核验。GBM MDI/SHAP是既有模型结果，不能用来为新实验选择特征后称独立验证。
9. **隐性缺失/替代风险（独立审查补充）**：校准表CO2.PSI.有39个NA，对应1.csv的值全部为`-0.230992129`；另有校准值为0、观测值为有限负数的案例：ethanol的beer=223，bitterness的beer=130/192，acetaldehyde的beer=40。显式NA计数73不能反映这些上游处理疑点。需查原处理脚本、校准NA与0的含义、替代参数拟合总体；暂作`suspected_preimputation/censoring`，不直接改NA、填零或指数反变换。原处理范围无法查清时，后续折内预处理不能被表述为端到端无泄漏。

## 重跑初检

在仓库根运行（Python >=3.10；通用初检需openpyxl，语义检查另需pandas/numpy）：

```powershell
python A/.agents/skills/beer-data-cleaning/scripts/inspect_inputs.py --input A/data/raw/official-20261024/附件 --output A/runs/skill-check-new/inspection.json
python A/reports/data/20261024-skill/probe_semantics.py --input A/data/raw/official-20261024/附件 --output A/runs/skill-check-new/semantic-probes.json
```

输出路径必须是新的且在输入目录之外。首次运行实际使用Codex提供的bundled Python；版本记录在JSON。通用脚本默认逗号分隔CSV和明确NA候选，其他格式先适配解析，不把它当通用自动清洗器。它保留字段名并检查重名/坏行；XLSX使用范围不等于样本量。脚本不验证全部公式、人工语义或许可。
