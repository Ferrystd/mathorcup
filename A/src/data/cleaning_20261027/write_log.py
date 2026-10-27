from pathlib import Path
import json,hashlib
from context import load_context
RAW, RUN, OUT = load_context()
inventory=json.loads((RUN/'inventory.json').read_text(encoding='utf8'));verification=json.loads((RUN/'verification.json').read_text(encoding='utf8'))
tables=[t for t in inventory['tables'] if t['layer'] is None]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def esc(v):return str(v).replace('|','\\|').replace('\n',' ').replace('\r',' ')
log=['# 2026 MathorCup A 题：按确认白名单执行的清洗日志','',
'日期：2026-10-27。运行范围：仅处理上一轮数据字典中“建议修正”的字段；其余原样保留。','',
'## 交付与实际改动','',
'- clean.csv：来源为官方 1.csv（250 行 × 234 列）。官方数据说明将其定义为全部啤酒的化学测量数据，故作为核心化学输入；用户将来源选择委托后采用此表，没有合并标签或矩阵。',
'- clean.csv 与 1.csv 逐字节一致：数值改动 **0 格**、删行 **0**、删列 **0**、新增列 **0**；73 个原文 NA、所有负值、ID 字符串、行列顺序、编码、换行和精度均保留。',
'- 清洗前后对照表.xlsx：第一张表列出 1,599 个实际源字段的前后缺失率、均值、负值占比；其余十三张表是 3.xlsx 的派生副本，仅 summary!AX2:AX13 的 barnyard 引用由各 beer_i!$AG$76 改为 beer_i!$AG$90。原始文件不变。',
'- cleaning_log.md：本文件，含逐列动作、理由、影响行数、精确公式台账与验证。','',
'实际修正为 **1 列、12 个公式单元格**；没有改动观测数值，也没有新增真实评分。','',
'## 规则如何落实','',
'1. 六个 CSV 合计 810 列，上一轮均不在“建议修正”清单中，因此全部保留。未把负数视为错误，未截断、裁剪、删重或重编码。',
'2. 结构性缺失填 0 并加 is_missing、随机缺失按 log/非 log 分别填最小值/中位数，都是有前提的规则。本轮没有同时满足白名单授权与缺失机制已证实的字段，因此没有执行任何填补，也没有新增 is_missing。',
'3. 没有全局标准化、z-score、反对数、重复取 log、0–6 映射或模型拟合。建模时的折内预处理不属于本轮。',
'4. 图片示例不能覆盖本题实测尺度证据。1.csv 的 pH、ethanol..v.v.、bitterness 等存在配对 log10 证据，不能把图片的原量纲示例直接当作当前文件事实。',
'5. 上一轮 2,071 条盘点记录包含 GBM SHAP Values 的两份分层重复视图（236 × 2 = 472）。本次逐列台账只记实际源字段 1,599 个（810 个 CSV 字段与 789 个工作簿字段），不重复计数。空 Sheet2 有表级记录，无字段。','',
'## 唯一公式修正的依据与影响','',
'十二张卡的 R75 为 Stale hops、R89 为 Barnyard/horsey，AG76 和 AG90 分别是对应响应公式。原 summary 的 stale_hops（AR列）与 barnyard（AX列）都引用 AG76，构成可直接核验的错误引用。','',
'对十二张卡分别核对后，barnyard 改引 AG90。该单元格使用 U90、W90、Y90、AA90、AC90、AE90 对应等级 1–6；全部响应格目前为空，原公式默认返回 0。因此修正前后缓存均为 0，**不能作为 12 个有效的 0 分回答或真实训练标签**。','',
'| 源表 | 单元格 | 原公式 | 修正公式 | 影响行数 | 数值变化 |',
'|---|---|---|---|---:|---|']
for i in range(1,13):
 log.append(f'| summary | AX{i+1} | =beer_{i}!$AG$76 | =beer_{i}!$AG$90 | 1 | 当前缓存 0→0；无真实评分 |')
log+=['',
'公式依赖验证在内存副本进行：分别在 beer_1 的 U90、Y90、AE90 临时输入标记，barnyard 分别返回 1、3、6，stale_hops 保持 0；随后恢复全部临时输入。最终文件未保留测试输入。此验证使用 Artifact Tool 计算引擎，未在桌面 Excel 手工操作验收。','',
'## 前后统计口径','',
'- 缺失率：原始空单元格、空串、NA、N/A、nan、NaN、NULL、null、- 候选缺失标记的数量除以该表数据行数。仅统计，不替换这些表示；语义是否不适用仍按原盘点待确认。',
'- 均值及负值占比：对能够整体按数值解释的列，使用有限非缺失项计算；标识强制按文本处理。负值占比的分母为该列有限非缺失数值数。文本、全缺失或混合布局列的数值统计不适用，Excel 中保留空格表示“指标不适用”，不是补零。',
'- CSV 表头不计为数据行；评分卡布局统计包含其物理行，不能作样本率解释。summary 的缓存数值与真实回答分开，原卡全空。',
'- 相关矩阵和 SHAP 混合层统计只描述存储内容，不能作为样本特征的清洗依据。其它未输出文件的“后”即未改动原件。',
'- 对照表均值显示 9 位小数、比例显示 2 位小数，底层保存计算数值；格式仅影响报告展示。字段名中的换行在对照表采用 LF、日志采用空格显示，源字段不变。所有前后统计相同，符合本轮仅修引用、未改数值的事实。','',
'## 未填补的 CSV 缺失','',
'| 文件 | 列 | 保留 NA 数 | 原字典策略 | 不填补理由 |',
'|---|---|---:|---|---|']
for t in tables:
 if t['file'].endswith('.csv'):
  for f in t['fields']:
   if f['missing_rows']:log.append(f"| {t['file']} | {esc(f['name'])} | {len(f['missing_rows'])} | {esc(f['strategy'])} | 不在建议修正白名单；随机/结构性/未检出机制尚未证实 |")
log+=['','## 逐文件、逐表、逐列台账','',
'“影响行数”指该列实际被改动的源数据行数；字段原样时为 0。公式修正行数与数值改动格数分开记。待确认列不因本轮委托而自动扩大修改范围。','']
for t in tables:
 log+=['### '+t['file']+' / '+t['sheet'],'',f"类型：{t['kind']}。数据行数：{t['rows']}；字段数：{t['columns']}。",'']
 if not t['fields']:
  log+=['空工作表，原样保留，无逐列记录。',''];continue
 log+=['| 列名 | 状态 | 原字典策略 | 理由 | 影响行数 | 公式改动格数 | 数值改动格数 |','|---|---|---|---|---:|---:|---:|']
 for f in t['fields']:
  changed=t['file']=='3.xlsx' and t['sheet']=='summary' and f['name']=='barnyard'
  if changed:reason='已核对十二张卡：Barnyard对应AG90，原误引stale_hops的AG76；只改引用，空卡无真实评分'
  elif f['missing_rows']:reason='未获修正授权；缺失表示/机制按原盘点记录，保留全部原值及缺失'
  elif f['needs']:reason='原字典待确认，不在修正白名单；保持当前尺度及原始表示'
  elif t['file'] in ['2.csv','5.csv','6.csv']:reason='相关系数/轴标签保留；不是样本表，负相关不作异常'
  elif t['file']=='3.xlsx':reason='空卡布局或公式缓存保留，不把缓存0当回答'
  else:reason='原字典保持不动；无核实错误或修正授权'
  log.append('| '+' | '.join(esc(v) for v in [f['name'],'改动（仅公式）' if changed else '原样',f['strategy'],reason,12 if changed else 0,12 if changed else 0,0])+' |')
 log.append('')
log+=['## 完成核验','',
'- 原始 9 个文件 SHA-256 与盘点基线一致；没有写回原件。',
'- clean.csv 与 1.csv 字节一致；行列数、NA 和负值表示不变。',
'- 原评分卡十二张工作表的 XML 字节完全一致；summary 仅十二个公式文本变化，其余单元格值、缓存、类型、样式、合并和验证规则保持。',
'- 原工作簿样式索引保留，只追加对照表所需样式；新增工作表需要的目录、关系和表数量元数据已同步。通过选择性打包保留原模板。',
'- 最终文件独立重新读取成功，14 张工作表完整；对照表 1,599 行，前后指标逐格相等，唯一公式变化列与台账一致。',
'- 公式依赖三种响应等级通过，临时输入已撤回。未进行模型训练，不主张预测性能或 Top-3 化合物结论。','',
'## 文件哈希与可追溯来源','',
'复跑盘点依据：本次运行目录 inventory.json；SHA-256：'+sha(RUN/'inventory.json')+'.','',
'| 原文件 | SHA-256（执行前后相同） |','|---|---|']
for name,h in inventory['hashes'].items():log.append(f'| {name} | {h} |')
log+=['','| 交付文件 | SHA-256 |','|---|---|',
'| clean.csv | '+sha(OUT/'clean.csv')+' |',
'| 清洗前后对照表.xlsx | '+sha(OUT/'清洗前后对照表.xlsx')+' |','',
'本日志不记录自身哈希以避免自引用。复现辅助材料位于本次指定的运行目录；复跑方法与边界见仓库报告。没有提交或推送原始数据和完整产物。']
assert len([s for s in log if s.startswith('| ') and (' | 原样 | ' in s or ' | 改动（仅公式） | ' in s)])==1599
with (OUT/'cleaning_log.md').open('x',encoding='utf8') as stream:stream.write('\n'.join(log)+'\n')
verification['output_hashes']={p.name:sha(p) for p in OUT.iterdir()}
(RUN/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'deliverables':[p.name for p in OUT.iterdir()],'log_entries':1599,'log_bytes':(OUT/'cleaning_log.md').stat().st_size},ensure_ascii=False))
