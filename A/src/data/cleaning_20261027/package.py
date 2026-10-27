from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import xml.etree.ElementTree as E
import json, re, hashlib, copy, shutil, math
import openpyxl
from context import load_context
RAW, RUN, OUT = load_context()
M='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
E.register_namespace('',M); E.register_namespace('r',R)
ns={'m':M}; sha=lambda b:hashlib.sha256(b).hexdigest()
inventory=json.loads((RUN/'inventory.json').read_text(encoding='utf8'))
tables=[t for t in inventory['tables'] if t['layer'] is None]
assert sum(len(t['fields']) for t in tables)==1599
assert {p.name:sha(p.read_bytes()) for p in RAW.iterdir() if p.is_file()}==inventory['hashes']
assert not OUT.exists(), 'Refuse to overwrite an existing output directory'
# Artifact Tool authors the content. Package only authorized edits because its
# full round-trip drops native source parts; retain source OOXML verbatim.
with ZipFile(RAW/'3.xlsx') as z:original={n:z.read(n) for n in z.namelist()}
with ZipFile(RUN/'formula_authored.xlsx') as z:authored=E.fromstring(z.read('xl/worksheets/sheet13.xml'))
authcells={c.get('r'):c for c in authored.findall('.//m:c',ns)}
summary=original['xl/worksheets/sheet13.xml'].decode('utf8')
for i in range(1,13):
 addr='AX'+str(i+1);old=f'beer_{i}!$AG$76';new=authcells[addr].find('m:f',ns).text
 assert new==f'beer_{i}!$AG$90'
 found=re.search(r'(<c\b[^>]*\br="'+addr+r'"[^>]*>)(.*?)(</c>)',summary,re.S);assert found
 inner=found[2];assert '<f>'+old+'</f>' in inner
 replaced=inner.replace('<f>'+old+'</f>','<f>'+new+'</f>')
 summary=summary[:found.start(2)]+replaced+summary[found.end(2):]
with ZipFile(RUN/'audit_authored.xlsx') as z:audit={n:z.read(n) for n in z.namelist()}
oldstyle=E.fromstring(original['xl/styles.xml']);newstyle=E.fromstring(audit['xl/styles.xml'])
styletext=original['xl/styles.xml'].decode('utf8')
offsets={k:len(oldstyle.find('m:'+k,ns)) for k in ['fonts','fills','borders','cellStyleXfs','cellXfs']}
oldformats=[int(x.get('numFmtId')) for x in oldstyle.find('m:numFmts',ns)]
num_map={int(e.get('numFmtId')):max([163]+oldformats)+i+1 for i,e in enumerate(newstyle.find('m:numFmts',ns))}
component_maps={};component_additions={}
for group in ['fonts','fills','borders']:
 known=[E.tostring(e) for e in oldstyle.find('m:'+group,ns)]
 additions=[];mapping={}
 for i,item in enumerate(newstyle.find('m:'+group,ns)):
  signature=E.tostring(item)
  if signature not in known:
   known.append(signature);additions.append(copy.deepcopy(item))
  mapping[i]=known.index(signature)
 component_maps[group]=mapping;component_additions[group]=additions
def remap_style(el):
 for key,group in [('fontId','fonts'),('fillId','fills'),('borderId','borders'),('xfId','cellStyleXfs')]:
  if key in el.attrib:el.set(key,str(component_maps[group][int(el.get(key))] if group in component_maps else int(el.get(key))+offsets[group]))
 if 'numFmtId' in el.attrib and int(el.get('numFmtId')) in num_map:el.set('numFmtId',str(num_map[int(el.get('numFmtId'))]))
def fragment(el):return E.tostring(el,encoding='unicode').replace(' xmlns="'+M+'"','')
for group in ['numFmts','fonts','fills','borders','cellStyleXfs','cellXfs']:
 items=component_additions[group] if group in component_additions else [copy.deepcopy(e) for e in newstyle.find('m:'+group,ns)]
 for item in items:
  if group=='numFmts':item.set('numFmtId',str(num_map[int(item.get('numFmtId'))]))
  if group in ['cellStyleXfs','cellXfs']:remap_style(item)
 pattern=r'(<'+group+r'\b[^>]*\bcount=")(\d+)("[^>]*>)(.*?)(</'+group+r'>)'
 match=re.search(pattern,styletext,re.S);assert match,group
 newblock=match[1]+str(int(match[2])+len(items))+match[3]+match[4]+''.join(fragment(e) for e in items)+match[5]
 styletext=styletext[:match.start()]+newblock+styletext[match.end():]
audit_sheet=E.fromstring(audit['xl/worksheets/sheet1.xml'])
shared=E.fromstring(audit['xl/sharedStrings.xml']).findall('m:si',ns)
for cell in audit_sheet.findall('.//m:c',ns):
 cell.set('s',str(int(cell.get('s','0'))+offsets['cellXfs']))
 if cell.get('t')=='s':
  value=cell.find('m:v',ns);si=shared[int(value.text)]
  cell.remove(value);cell.set('t','inlineStr');inline=E.SubElement(cell,'{'+M+'}is')
  for item in si:inline.append(copy.deepcopy(item))
for col in audit_sheet.findall('.//m:col',ns):
 if col.get('style') is not None:col.set('style',str(int(col.get('style'))+offsets['cellXfs']))
for row in audit_sheet.findall('.//m:row',ns):
 if row.get('s') is not None:row.set('s',str(int(row.get('s'))+offsets['cellXfs']))
parts=dict(original)
parts['xl/worksheets/sheet13.xml']=summary.encode('utf8')
parts['xl/styles.xml']=styletext.encode('utf8')
parts['xl/worksheets/sheet14.xml']=E.tostring(audit_sheet,encoding='utf-8',xml_declaration=True)
parts['xl/worksheets/_rels/sheet14.xml.rels']=audit['xl/worksheets/_rels/sheet1.xml.rels']
parts['xl/tables/table1.xml']=audit['xl/tables/table1.xml']
workbook=original['xl/workbook.xml'].decode('utf8')
workbook=workbook.replace('<sheets>','<sheets><sheet name="清洗前后对照" sheetId="14" r:id="rIdCleaningAudit"/>',1)
workbook=re.sub(r'activeTab="\d+"','activeTab="0"',workbook)
parts['xl/workbook.xml']=workbook.encode('utf8')
rels=original['xl/_rels/workbook.xml.rels'].decode('utf8')
rels=rels.replace('</Relationships>','<Relationship Id="rIdCleaningAudit" Type="'+R+'/worksheet" Target="worksheets/sheet14.xml"/></Relationships>')
parts['xl/_rels/workbook.xml.rels']=rels.encode('utf8')
types=original['[Content_Types].xml'].decode('utf8')
types=types.replace('</Types>','<Override PartName="/xl/worksheets/sheet14.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/tables/table1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.table+xml"/></Types>')
parts['[Content_Types].xml']=types.encode('utf8')
app=original['docProps/app.xml'].decode('utf8')
app=app.replace('<vt:i4>13</vt:i4>','<vt:i4>14</vt:i4>').replace('<vt:vector size="13" baseType="lpstr">','<vt:vector size="14" baseType="lpstr"><vt:lpstr>清洗前后对照</vt:lpstr>')
parts['docProps/app.xml']=app.encode('utf8')
changed_parts=[n for n in original if parts[n]!=original[n]]
assert set(changed_parts)=={'xl/worksheets/sheet13.xml','xl/styles.xml','xl/workbook.xml','xl/_rels/workbook.xml.rels','[Content_Types].xml','docProps/app.xml'}
for i in range(1,13):assert parts[f'xl/worksheets/sheet{i}.xml']==original[f'xl/worksheets/sheet{i}.xml']
beforetree=E.fromstring(original['xl/worksheets/sheet13.xml']);aftertree=E.fromstring(parts['xl/worksheets/sheet13.xml'])
beforecells={x.get('r'):E.tostring(x) for x in beforetree.findall('.//m:c',ns)}
aftercells={x.get('r'):E.tostring(x) for x in aftertree.findall('.//m:c',ns)}
assert [k for k in beforecells if beforecells[k]!=aftercells[k]]==['AX'+str(i) for i in range(2,14)]
for i in range(2,14):aftertree.find('.//m:c[@r="AX'+str(i)+'"]/m:f',ns).text=f'beer_{i-1}!$AG$76'
assert E.tostring(aftertree)==E.tostring(beforetree)
finalstyle=E.fromstring(parts['xl/styles.xml'])
for group in oldstyle:
 name=group.tag.split('}')[-1];other=finalstyle.find('m:'+name,ns)
 if name in ['numFmts','fonts','fills','borders','cellStyleXfs','cellXfs']:
  assert [E.tostring(e) for e in group]==[E.tostring(e) for e in list(other)[:len(group)]]
 else:assert E.tostring(group)==E.tostring(other)
OUT.mkdir()
shutil.copyfile(RAW/'1.csv',OUT/'clean.csv')
target=OUT/'清洗前后对照表.xlsx'
with ZipFile(target,'w',ZIP_DEFLATED) as z:
 for name,data in parts.items():z.writestr(name,data)
assert (OUT/'clean.csv').read_bytes()==(RAW/'1.csv').read_bytes()
final=openpyxl.load_workbook(target,data_only=False);cached=openpyxl.load_workbook(target,data_only=True)
src=openpyxl.load_workbook(RAW/'3.xlsx',data_only=False);src_cache=openpyxl.load_workbook(RAW/'3.xlsx',data_only=True)
cell_diffs=[]
for sheet in src.sheetnames:
 for row in src[sheet]:
  for c in row:
   other=final[sheet][c.coordinate]
   if c.value!=other.value:cell_diffs.append((sheet,c.coordinate,c.value,other.value))
   assert src_cache[sheet][c.coordinate].value==cached[sheet][c.coordinate].value
   assert c.data_type==other.data_type
   assert c._style==other._style
 assert list(src[sheet].merged_cells.ranges)==list(final[sheet].merged_cells.ranges)
 assert E.tostring(src[sheet].data_validations.to_tree())==E.tostring(final[sheet].data_validations.to_tree())
assert len(cell_diffs)==12
assert final.sheetnames==['清洗前后对照']+src.sheetnames
compare=json.loads((RUN/'comparison_rows.json').read_text(encoding='utf8'));view=final['清洗前后对照']
assert view.max_row==1609 and view.max_column==16 and view.freeze_panes=='D11'
assert list(view.tables)==['CleaningComparison']
for actual,expect in zip(view.iter_rows(min_row=11,values_only=True),compare['rows']):
 for v,e in zip(actual,expect):
  assert v==e or (isinstance(v,str) and isinstance(e,str) and v==e.replace('\r\n','\n')) or (isinstance(v,(int,float)) and isinstance(e,(int,float)) and math.isclose(v,e,rel_tol=1e-14,abs_tol=1e-14)),(v,e)
assert all(row[4]==row[5] and row[6]==row[7] and row[8]==row[9] for row in compare['rows'])
checks=json.loads((RUN/'dependency_check.json').read_text(encoding='utf8'))
assert [x['barnyard'] for x in checks]==[1,3,6]
assert {p.name:sha(p.read_bytes()) for p in RAW.iterdir() if p.is_file()}==inventory['hashes']
verification={'raw_hashes_unchanged':True,'clean_byte_identical':True,'data_value_changes':0,'formula_cell_changes':cell_diffs,'source_fields':1599,'original_card_sheets_byte_identical':12,'package_changed_parts':changed_parts,'package_added_parts':sorted(set(parts)-set(original)),'artifact_dependency_cases':checks}
(RUN/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2),encoding='utf8')
for w in [final,cached,src,src_cache]:w.close()
print(json.dumps(verification,ensure_ascii=False))
