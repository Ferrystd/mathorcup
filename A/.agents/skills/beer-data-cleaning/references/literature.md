# 文献到规则的证据索引

核验日期：2026-10-24。仅采用原始研究/官方方法文档。检索从“beer flavor 250 beers chemical sensory machine learning”追到源研究，再按“metabolomics missing value left censored”“centering scaling transformations metabolomics”“outlier detection”“preprocessing data leakage”补方法。页面或摘要读到的内容不扩写成未读结论。

## L1 数据源研究

Schreurs M. et al. (2024), *Predicting and improving complex beer flavor through machine learning*, Nature Communications 15, 2368.

- [DOI](https://doi.org/10.1038/s41467-024-46346-0)；[开放全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC10966102/)；[作者数据与脚本存档](https://zenodo.org/records/10653704)，DOI 10.5281/zenodo.10653704。
- 已读 Methods：Chemical dataset、Correlation calculations、Trained panel、Online reviews、Predictive modeling；存档文件说明。
- 直接证据：化学测量与感官/评论衍生量属于不同数据源；评分有逐评分者标准化及汇总；作者相关分析为Spearman；预测流程使用训练集均值/标准差缩放，文中也报告均值插补。
- 本项目采用：核查数据血缘、区分评分来源、调查题面冲突；不把原论文的插补时机视为已通过当前防泄漏审查。比赛附件与存档尚未逐字节比对，不能宣称相同版本；不拿上游数据覆盖附件。

## L2 缺失机制与方法比较

Wei R. et al. (2018), *Missing Value Imputation Approach for Mass Spectrometry-based Metabolomics Data*, Scientific Reports 8, 663.

- [DOI](https://doi.org/10.1038/s41598-017-19120-0)；[全文](https://pmc.ncbi.nlm.nih.gov/articles/PMC5766532/)。已读Introduction、Results缺失复核、Discussion、Methods。
- 研究比较不同缺失机制下的方法；左删失才考虑QRILC，MCAR/MAR可比较RF/KNN。半最小值不是普适解决办法。
- 边界：四套MS数据不等于本题；方法排名、缺失比例阈值不可移植为本题结论。先查原始记录，不凭NA比例认定机制。

## L3 批次和检测限

Do K.T. et al. (2018), *Characterization of missing values in untargeted MS-based metabolomics data and evaluation of missing data handling strategies*, Metabolomics 14, 128.

- [DOI/原文](https://doi.org/10.1007/s11306-018-1420-2)。已读Introduction、§2.2.1–2.2.3、§4插补方法。
- 缺失可能关联运行日、批次和检测限；全局常数/错误LOD假设会改变分布与分析。
- 本项目采用：缺少运行日和LOD时记未知，不用每列最小值冒充检测限。研究对象为血清代谢组，KNN结果不证明在啤酒上最优。

## L4 变换与缩放

van den Berg R.A. et al. (2006), *Centering, scaling, and transformations: improving the biological information content of metabolomics data*, BMC Genomics 7, 142.

- [DOI/原文](https://doi.org/10.1186/1471-2164-7-142)。已读Properties of metabolome data、Class II: Scaling、Class III: Transformations、Data preprocessing。
- 变换与缩放影响分析；对数不直接适用零，且可能放大近零噪声；不存在普遍最优处理。
- 本项目采用：按量纲/模型选择并折内验证，保留原尺度。论文特定实验的峰面积加1不成为浓度统一加1规则；不重复转换已变换数据。

## L5 异常值

NIST/SEMATECH e-Handbook of Statistical Methods, §1.3.5.17 [Detection of Outliers](https://www.itl.nist.gov/div898/handbook/eda/section3/eda35h.htm)。已读Introduction、Labeling、Normality Assumption、Modified Z-Scores。

先标记调查，确证错误才修正/排除；真实极端值可保留并做稳健分析。修正Z的3.5是候选标记而非删样命令。实施时检查分布前提与MAD=0，不把均值±3σ或分位尾部当“错误”定义。

## L6 防泄漏实现

scikit-learn developers，官方 [Common pitfalls §12.2](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage)、[Cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html) 的 held-out transformation 与 grouped data。

预处理在训练折fit，验证/测试仅transform；重复测量按目标实体分组。这里支持工程实现，不决定本题最佳模型或插补法。QRILC若缺少fit/transform隔离能力，应阻断其预测用途——这是文献与防泄漏原则结合的工程推论。

## 提供材料的采用边界

用户提供的PPT只借鉴“按类型处理、记录变换、防泄漏”；其中磁性纳米颗粒数据、模拟标签、5–95尾部删除、交换偏置缺失填0、固定KNN参数不移植到啤酒。三张截图仅借鉴规则先行、留痕、行数闭环和复核；问卷答题时长/年龄职业冲突不适用于仪器和感官汇总数据。未执行PPT程序，未使用其演示数据。
