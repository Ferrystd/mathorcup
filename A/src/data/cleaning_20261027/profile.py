import csv,json,math,hashlib,html,re,io
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
import pandas as pd
import openpyxl
from openpyxl.utils import get_column_letter
from context import load_context
p, RUN, OUT = load_context()
markers={'','NA','N/A','nan','NaN','NULL','null','-'}
hashes={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in p.iterdir() if f.is_file()}
def serial(x):return '' if x is None else str(x)
def ismiss(x):return x is None or serial(x).strip() in markers
def num(x):
 try:
  v=float(x)
  return v if math.isfinite(v) else None
 except (ValueError,TypeError):return None
def fnum(x):return '—' if x is None else (str(x) if isinstance(x,str) else format(x,'.9g'))
def spans(rows):
 out=[]
 for r in rows:
  if out and r==out[-1][1]+1:out[-1][1]=r
  else:out.append([r,r])
 return '、'.join(str(a) if a==b else str(a)+'–'+str(b) for a,b in out) or '无'
def inv(M,base):
 if M is None:return '不适用'
 lg=M if base==10 else M/math.log(10)
 if lg>300 or lg< -300:return ('10^('+format(M,'.9g')+')' if base==10 else 'e^('+format(M,'.9g')+')')+'（数量级表达，避免溢出）'
 return format(10**lg,'.9g')
def profile(name,vals,rownums,force_text=False,rawvals=None):
 raw=vals if rawvals is None else rawvals
 missing=[rownums[i] for i,x in enumerate(raw) if ismiss(x)]
 present=[x for x in raw if not ismiss(x)]
 nv=[(rownums[i],num(x)) for i,x in enumerate(vals) if not ismiss(x) and num(x) is not None]
 bad=[rownums[i] for i,x in enumerate(vals) if not ismiss(x) and num(x) is None]
 allnum=bool(nv) and not bad and not force_text
 a=np.array([v for r,v in nv]);q=np.quantile(a,[0,.25,.5,.75,1]).tolist() if allnum else [None]*5
 forms=sum(isinstance(x,str) and x.startswith('=') for x in raw)
 dtype='string' if force_text or bad else 'float64' if nv else '未定（全缺失）'
 if forms:dtype='formula→缓存'+('数值' if allnum else '混合')
 return dict(name=name,n=len(raw),nonmissing=len(present),nonempty=sum(x is not None and x!='' for x in raw),missing_rate=len(missing)/len(raw) if raw else None,missing_rows=missing,missing_tokens=dict(Counter('<空单元格>' if x is None else '<空串>' if x=='' else serial(x) for x in raw if ismiss(x))),unique=len(set(serial(x) for x in present)),dtype=dtype,forms=forms,numeric_n=len(nv),numeric=allnum,negrows=[r for r,v in nv if v<0],over6rows=[r for r,v in nv if v>6],negative_rate=float((a<0).mean()) if allnum else None,stats=q,mean=float(a.mean()) if allnum else None,sd=float(a.std(ddof=1)) if allnum and len(a)>1 else None,noninteger=int((a!=np.floor(a)).sum()) if allnum else None,long_decimals=sum(len(serial(x).split('.',1)[1].split('e')[0].split('E')[0])>3 for x in vals if num(x) is not None and '.' in serial(x)),parse_bad_rows=bad,unit='待确认',scale='待确认',strategy='保持不动',meaning='待确认',allowed='待确认',evidence=[],needs=False,opt1='',opt2='')
rawcsv={}
for filename in ['1.csv','2.csv','4.csv','5.csv','6.csv','7.csv']:
 rows=list(csv.reader(io.StringIO((p/filename).read_bytes().decode('utf-8-sig'),newline='')))
 rawcsv[filename]=(rows[0],rows[1:])
w8=openpyxl.load_workbook(p/'8.xlsx',data_only=True)
w8f=openpyxl.load_workbook(p/'8.xlsx',data_only=False)
w3=openpyxl.load_workbook(p/'3.xlsx',data_only=True)
w3f=openpyxl.load_workbook(p/'3.xlsx',data_only=False)
threshold={}
for r,row in enumerate(list(w8['Sensory thresholds'].values)[1:],2):
 if row[1] is not None:threshold[str(row[1])]={'row':r,'chemical_name':row[2],'unit':row[6],'calibrated':row[4],'threshold_mean':row[9],'threshold_median':row[10]}
sensory=defaultdict(list)
for r,row in enumerate(list(w8['Sensory names'].values)[1:],2):
 sensory[(str(row[0]),str(row[1]))].append({'row':r,'name':row[5],'datatype':row[7]})
h1,r1=rawcsv['1.csv'];ih={c:i for i,c in enumerate(h1)}
a={row[0]:row for row in r1}
calrows=list(w8['Calibrated chemical dataset'].values)
hc=calrows[0];cal={serial(row[0]):row for row in calrows[1:]};cr={serial(row[0]):i for i,row in enumerate(calrows[1:],2)}
anchors={}
for j,c in enumerate(hc[3:],3):
 pairs=[(k,num(row[ih[c]]),num(cal[k][j])) for k,row in a.items()]
 positive=[(k,x,y) for k,x,y in pairs if x is not None and y is not None and y>0]
 finite=[(k,x,y) for k,x,y in pairs if x is not None and y is not None]
 def maxerr(fn,ps):return max((abs(x-fn(y)) for k,x,y in ps),default=None)
 el=maxerr(math.log10,positive);en=maxerr(math.log,positive);ei=maxerr(lambda x:x,finite)
 zero=[k for k,x,y in pairs if y==0];neg=[k for k,x,y in pairs if y is not None and y<0];mis=[k for k,x,y in pairs if y is None]
 minpos=min((y for k,x,y in pairs if y is not None and y>0),default=None)
 idgood=[k for k,x,y in finite if math.isclose(x,y,rel_tol=1e-7,abs_tol=1e-9)]
 replaced=[{'beer':k,'csv_row':next(i for i,row in enumerate(r1,2) if row[0]==k),'xlsx_row':cr[k],'source':y,'observed':x,'halfmin_match':abs(x-math.log10(minpos/2))<1e-7} for k,x,y in pairs if x is not None and (y is None or y<=0)] if el is not None and el<1e-7 else []
 mismatches=[{'beer':k,'csv_row':next(i for i,row in enumerate(r1,2) if row[0]==k),'xlsx_row':cr[k],'csv':x,'xlsx':y} for k,x,y in finite if not math.isclose(x,y,rel_tol=1e-7,abs_tol=1e-9)]
 anchors[c]=dict(n_positive=len(positive),n_finite=len(finite),identity_matches=len(idgood),err_identity=ei,err_log10=el,err_ln=en,positive_min=minpos,zero=zero,negative=neg,missing=mis,replaced=replaced,mismatches=mismatches,cal_column=get_column_letter(j+1),csv_missing_at_cal_zero=[k for k,x,y in pairs if x is None and y==0])
tables=[]
def addtable(file,sheet,kind,note,head,rows,start=2,rawrows=None,rownums=None,layer=None):
 rownums=list(range(start,start+len(rows))) if rownums is None else rownums
 rawrows=rows if rawrows is None else rawrows
 t={'file':file,'sheet':sheet,'kind':kind,'note':note,'rows':len(rows),'columns':len(head),'fields':[],'layer':layer}
 for j,c in enumerate(head):
  name=str(c) if c not in [None,''] else '[空表头 '+get_column_letter(j+1)+']'
  vals=[row[j] if j<len(row) else None for row in rows];rv=[row[j] if j<len(row) else None for row in rawrows]
  force=name in ['beer','Beer','beer_id','tasting_category_fine','tasting_category','data'] or (file in ['2.csv','5.csv','6.csv'] and j==0)
  d=profile(name,vals,rownums,force,rv);d['position']=j+1;d['letter']=get_column_letter(j+1)
  t['fields'].append(d)
 tables.append(t);return t
for filename,(h,rows) in rawcsv.items():
 kind='特征×特征相关矩阵' if filename in ['2.csv','5.csv'] else '交叉表（化学×感官相关矩阵）' if filename=='6.csv' else '样本×特征表'
 t=addtable(filename,'CSV',kind,'UTF-8；逗号分隔；首行为表头；原始字段均保留，数值统计仅在内存解析。',h,rows)
 t['row_widths']=dict(Counter(map(len,rows)))
 t['duplicate_rows']=len(rows)-len(set(map(tuple,rows)))
 if filename in ['2.csv','5.csv','6.csv']:
  mat=np.array([[float(x) for x in row[1:]] for row in rows])
  t['matrix']={'row_axis':[r[0] for r in rows],'column_axis':h[1:],'minimum':float(mat.min()),'maximum':float(mat.max())}
  if mat.shape[0]==mat.shape[1]:t['matrix'].update(axis_equal=[r[0] for r in rows]==h[1:],symmetry_error=float(np.abs(mat-mat.T).max()),diagonal_range=[float(mat.diagonal().min()),float(mat.diagonal().max())])
for s in w3:
 sf=w3f[s.title];rr=list(sf.values);vr=list(s.values)
 if s.title=='summary':
  t=addtable('3.xlsx',s.title,'交叉表（卡片×公式汇总字段）','表头第1行；统计为Excel保存的公式缓存，绝非有效评分。原始输入为空；不重新计算公式。',rr[0],vr[1:],rawrows=rr[1:])
 else:
  t=addtable('3.xlsx',s.title,'交叉表（评分卡布局，非样本矩阵）','无行式表头；逐物理列A:AG审计1–101行；数值包括打印刻度和公式缓存，不代表实际回答；合并单元格的占位空白不是缺测。',[get_column_letter(i) for i in range(1,s.max_column+1)],vr,start=1,rawrows=rr)
for s in w8:
 sf=w8f[s.title];rr=list(sf.values);vr=list(s.values)
 if not rr or not any(any(x is not None for x in row) for row in rr):
  addtable('8.xlsx',s.title,'空表（不强行归入观测类型）','无数据；无语义字段。',[],[]);continue
 kind='样本×特征表' if s.title in ['Calibrated chemical dataset','Beer Prices'] else '长表' if s.title=='GBM SHAP Values' else '交叉表（字典/既有模型结果）'
 note='第1行表头；按原始单元格和公式缓存分别核验。'
 head=list(rr[0])
 if s.title=='GBM importance MDI':head=['[A列：原表头空]','[B列：原表头数值0]'];note+='原始A1为空/B1=0，未重命名原文件；按A2:A232和B2:B232列出231条结果。'
 t=addtable('8.xlsx',s.title,kind,note,head,vr[1:],rawrows=rr[1:])
 if s.title=='GBM SHAP Values':
  for layer in ['SHAP','concentration']:
   ids=[i for i,row in enumerate(vr[1:],2) if row[0]==layer]
   addtable('8.xlsx',s.title+' / '+layer,'样本×特征表（长表分层只读视图）','仅在内存按data分层；没有删除或改写原文件任何行。',head,[vr[i-1] for i in ids],rawrows=[rr[i-1] for i in ids],rownums=ids,layer=layer)
paper='https://www.nature.com/articles/s41467-024-46346-0'
def issue(d,one,two):d.update(needs=True,strategy='需确认',opt1=one,opt2=two)
def chemical(d,calibrated=False):
 c=d['name'];meta=threshold.get(c);an=anchors.get(c);e=''
 if meta:
  d['meaning']=str(meta['chemical_name'])+'（8.xlsx/Sensory thresholds!C'+str(meta['row'])+'，按B列精确匹配；不另猜别名）'
  d['unit']=str(meta['unit']) if meta['unit'] not in [None,''] else '待确认（单位单元格为空）'
 else:d['meaning']='待确认（没有精确匹配的字典证据）'
 if calibrated:
  d['scale']='原始量纲' if meta and meta['unit'] not in [None,''] else '待确认'
  e='校准参考表自身数值；单位来自G列。原始量纲仅指表中报告尺度，不证明所有记录无测量/校准错误。'
  if d['negrows'] or d['missing_rows'] or not meta or meta['unit'] in [None,'','v/v','kcal%','PSI'] or (an and an['mismatches'] and not (an['err_log10'] is not None and an['err_log10']<1e-7)):
   issue(d,'保留现有校准值并标记，受影响条目暂不作浓度/阈值约束；可保留其来源信息。','核对仪器/校准记录与单位，证实错误后在派生副本修正；需要额外证据，原件仍保留。')
 elif an and an['err_log10'] is not None and an['err_log10']<1e-7:
  d['scale']='log10';e=f"高置信：按beer逐条配对，{an['n_positive']}个正值锚点；log10最大绝对误差{fnum(an['err_log10'])}，ln误差{fnum(an['err_ln'])}。仅正值锚点证明变换关系。"
  if an['replaced']:
   e+=f" 另{len(an['replaced'])}个非正/NA源格全部与log10(该列最小正值/2)吻合；替代意图和LOD未知。"
   issue(d,'保留发布值并单列替代标记；可复现附件分析，但不能把替代数视为实测浓度。','查清零/负/NA机制后另建缺失或左删失掩码，确认后才在训练折比较处理；样本有效信息和排名可能改变。')
  if meta and meta['unit'] in [None,'','v/v','kcal%','PSI'] and not d['needs']:issue(d,'保留log10数值，记录源单位原文；暂不进行剂量换算。','核对单位、比例基准和上游处理后才另建原单位视图；可能改变物理阈值解释。')
 elif an and an['n_finite'] and an['identity_matches']==an['n_finite']:
  d['scale']='原始量纲';e=f"高置信于两附件同尺度：{an['n_finite']}对非缺失值恒等（最大差{fnum(an['err_identity'])}）；log10最大差{fnum(an['err_log10'])}。实际单位仍以字典为准；校准表缺失而发布表有值的位置不能被这组共同观测证据解释。"
  if d['missing_rows'] or (an and an.get('missing')):issue(d,'保留两来源数值并标记校准表NA位置（beer='+','.join(an.get('missing',[]))+'），不自动覆盖；这些位置的来源仍未知。','追溯这些位置的上游处理后，确认分析版本与掩码；选择可能改变相关性和重要性，不默认删样或补值。')
 else:
  d['scale']='待确认'
  if an:e=f"低置信/未定：{an['identity_matches']}/{an['n_finite']}配对值近似恒等，但其余冲突；原值最大差{fnum(an['err_identity'])}、log10差{fnum(an['err_log10'])}、ln差{fnum(an['err_ln'])}。不能整列套一个转换。"
  else:e='低置信/未定：无原浓度配对锚点；跨度只能筛选候选，不能区分log10、ln、原量纲或其他处理。'
  issue(d,'保持发布尺度，只作该尺度的描述/关系探索，暂不用于浓度阈值与反解；避免伪造单位。','核对原始处理脚本、校准与单位后再逐列决定变换；确认前阻断该列绝对浓度和Top-3剂量解释。')
 if not calibrated:
  h,rows=rawcsv['1.csv'];j=h.index(c)
  common=sum(row[j]=='-1.81781854' for row in rows)
  if common:e+=f" 还有{common}格精确等于-1.81781854；疑似共享底值，仅标记，不判异常/不恢复NA。"
 d['e1extra']=e;d['allowed']='待确认（感觉阈值不是允许上下限；不能以观察最小/最大替代）'
for t in tables:
 file=t['file'];sh=t['sheet'];layer=t['layer']
 for d in t['fields']:
  c=d['name'];pos=d['position'];meta=c in ['beer','Beer','beer_id','tasting_category_fine','tasting_category','data']
  d['e1extra']=''
  if meta:
   d.update(scale='分类编码',meaning='样本键/分层元数据；保持原始表示，具体编码映射见来源',allowed='待确认（仅核对唯一性/映射，不设数值范围）',strategy='保持不动')
   if c=='beer_id' and file in ['4.csv','7.csv']:
    issue(d,'保留原始ID字符串，使用经核验的beer一对一映射；原ID不能作唯一键。','从可靠原始条码表补建独立ID映射；需要人工/血缘核对，不可从科学计数法猜回低位。')
  elif file in ['2.csv','5.csv','6.csv']:
   d.update(scale='分类编码' if pos==1 else '原始量纲',meaning='相关矩阵行轴标签' if pos==1 else '与该列轴字段的相关系数（无量纲）',unit='无量纲' if pos>1 else '不适用',allowed='行轴映射待核验' if pos==1 else '[-1,1]',strategy='保持不动')
   d['e1extra']='系数原值，不是化合物丰度；负号代表反向关系。数据说明写Spearman，题面Pearson冲突另列，禁止按样本删除行。'
  elif file=='1.csv' or (file=='8.xlsx' and layer=='concentration' and c not in ['base_prediction']):chemical(d)
  elif file=='4.csv':
   match=sensory.get(('Trained panel',c),[])
   d.update(scale='z标准化',meaning='；'.join(str(x['name'])+'（Sensory names第'+str(x['row'])+'行）' for x in match) if match else '品评汇总指标，具体字段含义待确认',unit='无量纲',allowed='无固定0–6界限；具体汇总范围待确认')
   d['e1extra']='中高置信，依据Schreurs等(2024) Methods / Trained panel与Sensory names精确映射；逐列分布见判定4。附件完整预处理血缘仍待核验。'
   issue(d,'保留现有z汇总尺度建模并按该尺度评价；不能声称输出原始0–6评分。','取得原评分及逐评分员参数/独立锚点后另建校准；成本增加，确认前0–6评分不可识别。')
  elif file=='7.csv':
   matches=[x for (ds,key),v in sensory.items() if ds=='Ratebeer' and key==c for x in v]
   d.update(scale='待确认',meaning=('；'.join(str(x['name'])+'（Sensory names第'+str(x['row'])+'行）' for x in matches) if matches else '论坛评论衍生字段；具体词义/聚合未获得精确字典映射'),allowed='待确认（不是0–6量表，也不按名称认作计数）')
   d['e1extra']='具体变换置信度低，Schreurs等(2024) Methods / Online reviews不能唯一识别本列处理。负数/长小数排除原始非负计数，却不能证明具体对数底数或z参数。'
   if d['nonmissing']==0:
    d['e1extra']='无分布证据：本列全部为原始字面NA，没有任何可观察数值；无法用负数、长小数或跨度区分计数、评分、对数或标准化尺度，置信度不足，待确认。'
    d['allowed']='待确认（全缺失，无法依据分布判断量表或允许范围）'
    issue(d,'保留全NA列及不可用状态，在模型输入视图中显式不使用；维度数减少但不制造信息。','追溯文本提取/字典生成，若有原评论可重算；成本增加，不能用0代替“没有感觉”。')
   else:issue(d,'保留发布尺度作评论侧辅助描述，与专家评分分开；不能解释成绝对味觉强度。','取得完整文本处理/缩放规则后单独重建评论特征；可能改变相关性与特征排名。')
  elif file=='3.xlsx':
   if sh=='summary':
    d.update(scale='待确认',meaning='汇总公式/空卡引用；缓存0不是真实回答',allowed='真实量表需逐字段确认；未填输入无有效分值')
    d['e1extra']='本列统计只描述已保存的公式缓存。卡片原始响应格全部为空；不能用缓存0判断0–6或中心化。'
    issue(d,'保留空模板和公式缓存，标记标签不可用；Q1绝对评分没有这些锚点。','取得已填写的真实评分卡并核验映射再建立标签；不得自己补答。')
    if c=='barnyard':
     d['meaning']='barnyard汇总公式与stale_hops错引同一单元格AG76（待确认）'
     d['strategy']='建议修正（理由：与stale_hops同引AG76；需核对AG90）'
     d['opt1']='保留原公式并隔离本列，避免错标签，但该维暂不可用。'
     d['opt2']='经确认后在派生副本将barnyard映射核对至AG90；需逐12张验证，不能改原件。'
   else:
    d.update(scale='待确认',meaning='评分卡物理布局列；文字/刻度/输入占位/公式混排，不对应单一变量',allowed='不适用（布局列不设统一允许范围）',strategy='保持不动')
    d['e1extra']='这些列的空白多数是排版或未回答。0–6打印刻度/缓存零不是观测评分；不以物理列统计推断中心化。'
  elif file=='8.xlsx' and sh=='Calibrated chemical dataset':chemical(d,True)
  elif file=='8.xlsx' and sh.startswith('GBM SHAP Values'):
   if c=='base_prediction':
    d.update(meaning='既有模型基线预测（值恒定，预测目标/训练范围待确认）',scale='待确认',allowed='待确认',unit='模型输出单位待确认')
   elif layer=='SHAP':
    d.update(meaning='既有模型对该字段的SHAP贡献值',scale='待确认',allowed='无通用正负限制；具体模型输出单位待确认',unit='模型输出单位待确认')
   else:d.update(meaning='同列混合SHAP贡献值与concentration发布尺度；必须按data分层',scale='待确认',allowed='混合尺度，不能设置全列共同范围',unit='混合')
   d['e1extra']='高置信于层结构：data=SHAP与data=concentration各250行。SHAP符号是贡献方向；concentration层231列与1.csv逐beer相等（最大差<1e-15）。整体列的分位数仅供资产记录，不能用于清洗。'
   issue(d,'保留既有模型结果并按data隔离，只作来源参考；不把它用于独立Top-3评价。','取得模型目标、训练样本/背景集后作为明确的外部比较；本题模型另用训练折重新求重要性。')
  elif file=='8.xlsx' and sh=='GBM importance MDI':
   d.update(scale='原始量纲' if pos==1 else '分类编码',meaning='疑似既有GBM的MDI重要性值（sheet名称与231值和≈1支持；空表头需确认）' if pos==1 else '对应特征原始标识',unit='无量纲' if pos==1 else '不适用',allowed='非负；全列和≈1（现有结果事实，不是新模型约束）' if pos==1 else '对应231特征')
   issue(d,'作为外部参考保留，不参与当前特征筛选；独立验证不被已有排名影响。','核对目标与训练范围后单独做对照，不把原模型排名冒充本题Top-3。')
  elif file=='8.xlsx' and sh=='Sensory thresholds':
   d.update(scale='原始量纲' if c in ['threshold_mean','threshold_median'] else '分类编码',meaning='源字典元数据字段 '+c+('（原表内容为Yeast/Hops等来源类别，不是文献引文）' if c=='origin_paper' else ''),allowed='待确认（按行unit/来源解释，不设全列统一范围）')
   d['e1extra']='列含不同化合物元数据。threshold列按行具有不同单位，感觉阈值≠允许浓度上限；unit为空不能靠字段名补。'
   if d['missing_rows']:issue(d,'保留元数据空白/NA并标记未知或可能不适用；对应物理约束暂不可用。','查原作者说明和化合物对应文献后在派生字典填写；不能用众数补单位或阈值。')
  elif file=='8.xlsx' and sh=='Sensory names':
   d.update(scale='分类编码',meaning='源感官映射元数据字段 '+c,allowed='待确认（文本枚举不作连续数值处理）')
   d['e1extra']='101条映射；DataType全部51条Ratebeer为空是分组覆盖差异。Ratebeer/aroma_citrus在第57、58行重复，映射键非唯一；不直接去重。'
   issue(d,'保留两条映射并显式报告一对多/缺省，暂停歧义联接；不会造成静默行数膨胀。','结合原字典人工确认保留/合并规则并建映射副本；必须记录语义取舍。')
  elif file=='8.xlsx' and sh=='Beer Prices' and c=='ABV':
   d.update(scale='待确认',meaning='ABV字段；当前工作表未提供该字段定义与比例基准，待确认',unit='待确认（不是价格单位；百分数或比例基准尚未核验）',allowed='待确认（先核对单位与字段来源）')
   d['e1extra']='该列与价格字段分开。没有独立字段说明或已核验的校准对应关系；不凭ABV列名自行补单位，也不套用欧元/升。'
   issue(d,'保留本列独立，暂不与乙醇测量互相替换或作换算锚点；单位相关解释受限。','核对原始字段说明及同一beer的校准记录，确认是否为标签标注、测量值及其比例基准后另建映射；可能影响酒精度约束。')
  elif file=='8.xlsx' and sh=='Beer Prices':
   d.update(scale='原始量纲',meaning='价格相关记录（论文价格节为欧元/升）；'+('ABV具体比例/百分比编码待确认' if c=='ABV' else '各渠道字段的币种/折算血缘待确认'),unit='待确认（论文欧元/升，附件逐字段转换待核验）',allowed='确认单位后通常非负；上限待确认')
   d['e1extra']='论文Beer price collection说明换欧元并按升，但不能仅凭价格列名假设当前原表已完成相同转换。'
   issue(d,'保留现值/NA，暂不并入风味预测，避免价格偏倚与单位混合。','核对各渠道货币、容量、日期和缺失原因后统一到独立派生视图；可能改变与喜好度的相关性。')
  q=d['stats'];m=d['mean']
  e1=f"判定={d['scale']}；范围[{fnum(q[0])},{fnum(q[4])}]；单位={d['unit']}。"+d['e1extra']
  if d['numeric'] and not meta:
   e2=f"最大值M={fnum(q[4])}；10^M={inv(q[4],10)}；e^M={inv(q[4],math.e)}。"
   if d['scale']=='log10':e2+='底数log10，高置信依据为上述配对误差。浓度列的宽泛μg/L~g/L区间不能单独排除另一个底数；pH/EBC/IBU/v/v/PSI/kcal%等指标不适用质量浓度区间。'
   elif file in ['2.csv','5.csv','6.csv'] or file=='3.xlsx' or sh.startswith('GBM SHAP Values') and layer!='concentration' or file in ['4.csv','7.csv']:e2+='两反解只作机械诊断，当前字段不是已证实的化合物log浓度，不能作物理解读。底数判定不适用/待确认。'
   else:e2+='当前没有逐化合物、逐基质的合理浓度上下限；不以感觉阈值冒充合理区间。对数底数置信度低/待确认；原值锚点优先于跨度猜测。'
  else:e2='不适用：标识/文本/混合布局/全缺失字段没有有意义的化合物最大值反解。'
  if meta:e3='标识字段不做正负异常判断。'
  elif d['scale']=='log10':e3=(f"负值{len(d['negrows'])}个，负对数值对应原尺度数值<1，保持不动。行号：{spans(d['negrows'])}。" if d['negrows'] else '本列没有负值。')+'上游替代候选另列，不把负号当错误，也不把替代数认定为真实测量。'
  elif file in ['2.csv','5.csv','6.csv']:e3=f"负值{len(d['negrows'])}个，是负相关；全部保持。"
  elif file=='4.csv' or layer=='SHAP':e3=f"负值{len(d['negrows'])}个，是标准化评分或模型贡献可允许的值；不标异常。"
  elif file=='8.xlsx' and sh=='Calibrated chemical dataset' and d['negrows']:e3=f"负值行号{spans(d['negrows'])}；只列待确认。betaglucan源单位mg/L下负数物理解释待查；unfermentables单位缺失，不能自动判坏。"
  else:e3=f"负值{len(d['negrows'])}个；尺度/字段角色未支持负值即异常的判断，保持。具体行号：{spans(d['negrows'])}。"
  if not d['numeric'] or meta:e4='不适用：不是可独立解释的原始评分数值列；不从列名推断量表。'
  else:
   e4=f"负值n={len(d['negrows'])}；>6的n={len(d['over6rows'])}；非整数n={d['noninteger']}；长小数(>3位)n={d['long_decimals']}；均值={fnum(m)}；样本SD={fnum(d['sd'])}；|均值|≤0.1={'是' if abs(m)<=.1 else '否'}（仅描述阈值）。"
   if file=='4.csv':e4+='逐评分员z后汇总；非原始0–6。长小数/负数支持，均值不近0不能推翻来源证据。'
   elif file=='3.xlsx':e4+='打印刻度或空卡公式缓存；不能据此识别已填写评分。'
   else:e4+='不是已验证的0–6评分；仅落在0–6也不能证明量表，均值近0也不能证明中心化。'
  e5=f"原始非空格={d['nonempty']}/{d['n']}；按候选标记后的非缺失={d['nonmissing']}；标记频数={json.dumps(d['missing_tokens'],ensure_ascii=False)}；缺失行={spans(d['missing_rows'])}。"
  if file.endswith('.csv'):
   e5+=f"全文件记录宽度恒为{t['columns']}且可读至末行；未见分隔错位/尾段截断证据。"
   if file=='7.csv' and d['nonmissing']==0:e5+='本列2–251行与另外两全NA列同步；原始字面NA，邻列完整，支持源数据缺省，不能仅因成块认定截断。'
   elif d['missing_rows']:
    e5+='源文件确实含NA；测量未检出/上游删失/不适用等机制仍待确认，解析成功不证明MCAR/MAR。'
    sync=[(o['name'],sorted(set(d['missing_rows']) & set(o['missing_rows']))) for o in t['fields'] if o is not d and set(d['missing_rows']) & set(o['missing_rows'])]
    e5+=' 与其他列同时缺失：'+('；'.join(name+':'+spans(rows) for name,rows in sync) or '无')+'。'
   else:e5+='无显式缺失；不排除已被上游常数替代。'
  elif file=='3.xlsx':e5+='空白是排版/未填写；公式原文与缓存分别读，缓存0不当作有效回答；未执行公式。'
  else:e5+='XLSX空单元格与文本NA逐类记录；分组块状缺失可由模板或覆盖范围产生，不等于文件截断。'
  if c in anchors and file=='1.csv':
   an=anchors[c]
   if an['csv_missing_at_cal_zero']:e5+=f"本列{len(an['csv_missing_at_cal_zero'])}个CSV NA对应校准表0，表明源编码差异，不能擅自填0。"
   if an['replaced']:e5+=f"另有{len(an['replaced'])}个隐性替代候选，不包含在显式缺失率中；精确行/键见附录。"
  d['evidence']=[e1,e2,e3,e4,e5]
for w in [w8,w8f,w3,w3f]:w.close()
report={'hashes':hashes,'tables':tables,'anchors':anchors,'notes':{'stats':'分位数用线性插值；展示9位有效数字只影响报告显示，不修改数据。CSV dtype是只读解析类型，标识强制string；唯一值按非缺失源表示计数。缺失率分母为表数据行，负值占比以非缺失有限数值为分母。布局/混合单位列的统计不具有样本特征意义。','paper':paper}}
assert len([t for t in tables if t['file'].endswith('.csv')])==6
assert sum(t['columns'] for t in tables if t['file'].endswith('.csv'))==810
assert all(len(d['evidence'])==5 for t in tables for d in t['fields'])
hashes_after={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in p.iterdir() if f.is_file()}
assert hashes_after==hashes
print(json.dumps({'hashes_unchanged':True,'tables':len(tables),'fields':sum(len(t['fields']) for t in tables),'log10_cols':[c for c,x in anchors.items() if x['err_log10'] is not None and x['err_log10']<1e-7],'implicit_replacements':sum(len(x['replaced']) for x in anchors.values()),'needs_confirmation':sum(d['needs'] for t in tables for d in t['fields']),'file_hashes':hashes},ensure_ascii=False))

(RUN/'inventory.json').write_text(json.dumps(report,ensure_ascii=False,allow_nan=False),encoding='utf-8')
