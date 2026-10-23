# 实验与证据模板

本模板未含实验结果。每个运行复制一份，旧运行不覆盖。所有空位保持空位，不能填示意准确率。

## 1. 运行前预登记

- run_id / 问题 / 提出人 / 日期：<待填>
- 可证伪假设、估计对象、目标人群：<待填>
- 数据路径及SHA-256、语义审计版本：<待填>
- 目标及尺度/候选特征、有效n、分组单位：<待填>
- 切分路径及哈希、内外层设置、开发/最终评价角色：<待填>
- 基线、候选方法、参数网格、最大运行预算：<待填>
- 缺失/缩放/降维/图/标签校准在哪层fit：<待填>
- 主指标、逐维指标、比较口径、区间方法、允许解释：<待填>
- Q1主七级输出与冻结离散化规则：<待填>
- Q2排序/并列规则、bootstrap单位和计划次数：<待填>
- Q3评价器版本、约束字典、每风格候选数/批次数、最大尝试、全部失败保留：<待填>
- 随机种子、线程数、预计时长、停止条件：<待填>
- 人工方法判断及理由：<姓名/日期/简要推导或对照理由>

## 2. 实际运行记录

Python/OS/包锁定文件：<待填>；code_commit（完整SHA）：<待填>；git_dirty及补丁/未跟踪实现快照：<待填>；配置/切分哈希：<待填>；真实执行命令：<实现后填写>。正式验收从干净且可取得的提交运行，不能仅凭HEAD声称复现了dirty运行。

脱敏摘要归档到`reports/experiments/<run_id>/`入Git；完整`runs/<run_id>/`工件及备份位置/哈希：<待填>。PR地址、Squash后主分支SHA及对应复跑：<如适用填写>。

开始/结束时间、退出码、日志路径、实际时长/资源、异常和与预登记偏离：<待填>。没有运行则写未运行，不用计划命令冒充执行证据。

## 3. 输出字段契约（待实现CSV）

- `q1_predictions.csv`：run_id, sample_id, group_id, fold, sensory_id, scale_status, prediction_type, grade_0_6, continuous_estimate, interval_low, interval_high, interval_method, available_status。主grade只能0…6整数或因明确缺口留空；连续估计是辅助。
- `q1_metrics.csv`：target, scale, n_valid, baseline, candidate, MAE_continuous, MAE_grade, RMSE, within_one, delta_MAE, uncertainty_method, coverage_status。总体宏均值须绑定同一目标/样本口径。
- `q2_top3.csv`：sensory_id, rank, compound_id, compound_type, method, direction, importance, graph_scope, n_paired, bootstrap_requested, bootstrap_valid, inclusion_frequency, jaccard_summary, cluster_id, evidence_id, limitation。
- `q3_generated.csv`：run_id, batch_id, candidate_id, style, seed, parent_id_if_resampled, acceptance_status, failure_reason, transformation_version，加逐化学量（附单位字典）；保存全部候选和筛后样本，不能只保存成功。
- `q3_transfer_pairs.csv`：source_id, source_style, target_style, candidate_id, lambda, distance_before, distance_after, change_norm, 每缺陷before/after/阈值/超阈/未知状态。
- `q3_metrics.csv`：style, batch_id, requested, attempted, accepted, failed, acceptance_rate, defect_violations, unknown_constraints, duplicate_rate, nearest_neighbor_summary, distribution_distance, frozen_evaluator_score, real_holdout_evaluator_quality。

输出实际路径与哈希：<待填>。未实现字段调整必须说明，不捏造CSV已存在。

## 4. 稳健性与失败

| 对照/消融 | 固定因素 | 改变因素 | 观察结果工件 | 不确定性/失败 | 是否改变结论及理由 |
|---|---|---|---|---|---|
| <待填> | | | | | |

所有失败运行/缺失维度/罕见风格：<待填>。bootstrap失败的次数与分母：<待填>。Q3全批次合格率及失败样本路径：<待填>。是否复用测试集调方案：<如有，改称开发结果并说明>。

## 5. 图表、论文主张与文献

| claim/figure ID | 论文节/表述 | run_id及源数据行列 | 生成脚本/参数 | 来源原文页/段/DOI | 可支持范围/反证 | 核验人/日期 |
|---|---|---|---|---|---|---|
| <待填> | | | | | | |

图注必须包含单位、n、真实/预测/生成身份、区间定义和相关AI贡献。文献无法核验则不能标“已读全文”。

## 6. 复现与决定

独立复跑人/日期/新run_id：<待填>；比较容差（复跑前写）：<待填>；差异及原因：<待填>。

采用/保留基线/降级/受阻，依据与尚未知项：<待填>。人工核心判断记录不等于额外签字审批；保留姓名和日期即可。
