"""Render the complete read-only inventory as a standalone local HTML report."""
import html
import json
from context import load_context

RAW, RUN, OUT = load_context()
inventory = json.loads((RUN / "inventory.json").read_text(encoding="utf-8"))
esc = lambda value: html.escape(str(value), quote=True)

def number(value, percent=False):
    if value is None:
        return "不适用"
    return f"{value:.4%}" if percent else f"{value:.9g}"

def table(headers, rows):
    return '<div class="scroll"><table><thead><tr>' + ''.join('<th>' + esc(x) + '</th>' for x in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>' + esc(x) + '</td>' for x in row) + '</tr>' for row in rows) + '</tbody></table></div>'

parts = ['''<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>2026 MathorCup A 数据资产盘点</title>
<style>body{font:15px/1.65 system-ui,sans-serif;color:#223247;margin:24px;max-width:1500px}h1,h2,h3{color:#24486c}a{color:#125cac}.scroll{overflow-x:auto;margin:16px 0}table{border-collapse:collapse;min-width:100%}th,td{border:1px solid #cbd6e1;padding:8px;text-align:left;vertical-align:top;overflow-wrap:anywhere}th{background:#eaf1f7}details{border:1px solid #d4dce5;margin:10px 0;padding:10px}summary{cursor:pointer;font-weight:600}.note{background:#fff3d4;padding:14px}code{overflow-wrap:anywhere}li{margin:8px 0}</style>
<h1>2026 MathorCup A 数据资产盘点</h1>
<p>冻结版本：2026-10-27。只读原始附件；本报告不执行清洗。统计均在内存计算，源文件前后哈希一致。</p>
<p class="note">这是原始数据盘点，建议修正不等于已经修改。后续派生副本的十二处公式修正另见 cleaning_log.md。空评分卡的缓存 0 不是真实评分；未知量纲与缺失机制继续保留未知。</p>''']
parts += ['<p>' + esc(inventory['notes']['stats']) + '</p>', '<p>来源：<a href="' + esc(inventory['notes']['paper']) + '">Schreurs 等 (2024)</a>；Methods 的 Trained panel / Online reviews 分别支持专家评分与评论特征的来源区分。具体附件血缘的未核验部分逐列标记。</p>', '<h2>文件与表清单</h2>']
tables = inventory['tables']
parts.append(table(['文件', '工作表/视图', '类型', '数据行数', '字段数', '说明'], [[t['file'], t['sheet'], t['kind'], t['rows'], t['columns'], t['note']] for t in tables]))
parts.append('<p>6 个 CSV、20 张实际工作表，另有 2 份 SHAP 分层视图。共 2,071 条字段记录，其中重复视图 472 条；实际源字段 1,599 个。评分卡按物理列盘点，不将其排版空白解释为样本缺失。</p><ul>')
for index, t in enumerate(tables):
    parts.append(f'<li><a href="#t{index}">{esc(t["file"])} / {esc(t["sheet"])}</a></li>')
parts.append('</ul>')
headers = ['列名', 'dtype', '非空数', '缺失率', '负值占比', '最小', 'P25', '中位', 'P75', '最大', '唯一值', '疑似含义', '量纲判定', '允许范围', '处理策略']
allowed_scales = {'原始量纲','log10','ln','z标准化','中心化','0-6原始评分','计数','分类编码','待确认'}
count = 0
for index, t in enumerate(tables):
    parts.append(f'<h2 id="t{index}">{esc(t["file"])} / {esc(t["sheet"])}</h2><p>{esc(t["kind"])}。{esc(t["note"])}</p>')
    if 'matrix' in t:
        matrix = {k:v for k,v in t['matrix'].items() if k not in {'row_axis','column_axis'}}
        parts.append('<p>矩阵结构核验：' + esc(json.dumps(matrix, ensure_ascii=False)) + '。禁止当作样本表删除行或标准化。</p>')
    rows = []
    for field in t['fields']:
        assert field['scale'] in allowed_scales
        assert field['strategy'] in {'保持不动','仅记录','需确认'} or field['strategy'].startswith('建议修正（')
        rows.append([field['name'], field['dtype'], field['nonmissing'], number(field['missing_rate'], True), number(field['negative_rate'], True), *[number(x) for x in field['stats']], field['unique'], field['meaning'], field['scale'], field['allowed'], field['strategy']])
    parts.append(table(headers, rows) if rows else '<p>空工作表，无列可盘点，原样保留。</p>')
    parts.append('<p>“非空数”按明确列出的候选缺失标记计算；物理非空数、原文标记、精确行号和同步缺失见每列第 5 项。行号为原文件行号，包含表头偏移。</p>')
    for field in t['fields']:
        assert len(field['evidence']) == 5
        parts.append('<details class="field"><summary>' + esc(field['name']) + '：五项判定与依据</summary><ol>')
        parts.extend('<li>' + esc(e) + '</li>' for e in field['evidence'])
        parts.append('</ol></details>')
        count += 1

parts.append('<h2>附录：配对锚点与上游替代候选</h2><p>按 beer 对照 1.csv 与 8.xlsx / Calibrated chemical dataset。以下只是来源差异证据，不是本轮生成或修正的数据。零、负值和 NA 的机制没有被猜测为随机或结构性。</p>')
parts.append(table(['字段','正值配对数','原值最大误差','log10 最大误差','ln 最大误差','替代候选数'], [[name, a['n_positive'], number(a['err_identity']), number(a['err_log10']), number(a['err_ln']), len(a['replaced'])] for name, a in inventory['anchors'].items()]))
for name, anchor in inventory['anchors'].items():
    if anchor['replaced']:
        parts.append('<h3>' + esc(name) + '：精确行号/键</h3>')
        parts.append(table(['beer','CSV 行号','XLSX 行号','校准表源值','CSV 发布值','是否吻合 log10(半最小正值)'], [[r['beer'], r['csv_row'], r['xlsx_row'], r['source'], r['observed'], r['halfmin_match']] for r in anchor['replaced']]))
parts.append('<p>所有原值不一致明细及配对字段映射另见同目录 <a href="inventory.json">inventory.json</a> 的 anchors；不同单位不得直接合并比较误差。</p>')
parts.append('<h2>原始文件 SHA-256</h2>')
parts.append(table(['文件', '执行前后相同的 SHA-256'], inventory['hashes'].items()))
parts.append('<h2>A. 必须保持不动的列</h2><p>以下按原始盘点列出未建议修正字段。标为“需确认”的列在确认前也保持不动；后续已授权的有限清洗只改 barnyard 公式，不改变这些列。</p>')
for t in tables:
    if t['layer'] is not None:
        continue
    rows = [[f['name'], f['scale'], '原字典策略：' + f['strategy'] + '。' + f['evidence'][2]] for f in t['fields'] if not f['strategy'].startswith('建议修正')]
    if rows:
        parts.append('<h3>' + esc(t['file'] + ' / ' + t['sheet']) + '</h3>' + table(['列名','量纲判定','保持理由'], rows))
parts.append('<h2>B. 需要确认的列及两种方案</h2><p>这是逐列语义未决项和后续选择，不是本轮新增授权请求。默认保留未知；实施扩大范围的处理前才需要新证据或确认。分层视图不重复列出。</p>')
for t in tables:
    if t['layer'] is not None:
        continue
    rows = [[f['name'], f['opt1'], f['opt2']] for f in t['fields'] if f['needs']]
    if rows:
        assert all(row[1] and row[2] for row in rows)
        parts.append('<h3>' + esc(t['file'] + ' / ' + t['sheet']) + '</h3>' + table(['列名','方案一及后果','方案二及后果'], rows))
parts.append('''<h2>C. 最可能出错的三处及后续影响</h2><ol>
<li><strong>尺度误判与整表再变换。</strong>将负对数浓度当异常删除，或对已 log 的 pH 等按列名反推原量纲，会改变样本分布、相关性、特征重要性及 Top-3 化合物。需逐列依据配对锚点；不能只用正负号或宽泛浓度区间定底数。</li>
<li><strong>缺失、模板零与真实测量混淆。</strong>73 个化学 NA、3 列评论全 NA、校准表的 0/NA 和空卡缓存 0 含义不同；统一填补或当真实标签会制造相关性、改变重要性并产生虚假 Top-3 证据。</li>
<li><strong>表角色和联接键错误。</strong>2/5/6.csv 是相关矩阵，4/7 的 beer_id 精度受损；把矩阵当样本、按受损 ID 去重联接或把既有 SHAP 当独立验证，会错配样本、泄漏标签并使 Top-3 无法独立评价。</li>
</ol></html>''')
assert count == 2071
target = RUN / '数据资产盘点.html'
with target.open('x', encoding='utf-8') as stream:
    stream.write('\n'.join(parts))
print(json.dumps({'inventory_fields': count, 'tables': len(tables), 'report': target.name}, ensure_ascii=False))
