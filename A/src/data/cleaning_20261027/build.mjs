import fs from 'node:fs/promises';
import {FileBlob,SpreadsheetFile,Workbook} from '@oai/artifact-tool';
const config=JSON.parse(await fs.readFile(process.env.MATHORCUP_CONTEXT,'utf8'));
const raw=config.input, run=config.run, output=config.output;
const mode=process.argv[2]||'preview';
if(!['preview','build','final'].includes(mode)) throw Error('Unknown build mode');
const wb=await SpreadsheetFile.importXlsx(await FileBlob.load(mode==='final' ? output+'/清洗前后对照表.xlsx' : raw+'/3.xlsx'));
if(mode==='preview'){
 console.log((await wb.inspect({kind:'region',sheetId:'summary',range:'AR1:AZ4',maxChars:2400,tableMaxRows:4,tableMaxCols:9,include:'values,formulas'})).ndjson);
 const pic=await wb.render({sheetName:'summary',range:'AR1:AZ4',scale:1.6,format:'png'});
 await fs.writeFile(run+'/before.png',new Uint8Array(await pic.arrayBuffer()));
} else if(mode==='final') {
 for(const [name,sheetName,range] of [['final_left','清洗前后对照','A1:J18'],['final_right','清洗前后对照','K10:P18'],['final_formula','summary','AR10:AZ13'],['final_long','清洗前后对照','A203:J207'],['final_multiline','清洗前后对照','A578:J582'],['final_changed','清洗前后对照','K1264:P1268']]) {
  const pic=await wb.render({sheetName,range,scale:1.3,format:'png'});
  await fs.writeFile(run+'/'+name+'.png',new Uint8Array(await pic.arrayBuffer()));
 }
 console.log((await wb.inspect({kind:'region',sheetId:'summary',range:'AX2:AX13',include:'values,formulas',maxChars:800})).ndjson);
} else {
 const summary=wb.worksheets.getItem('summary');
 for(let i=1;i<=12;i++) {
  const old=summary.getRange('AX'+(i+1)).formulas[0][0];
  if(old!== '=beer_'+i+'!$AG$76') throw Error('Unexpected original formula '+old);
  summary.getRange('AX'+(i+1)).formulas=[['=beer_'+i+'!$AG$90']];
 }
 wb.recalculate();
 console.log((await wb.inspect({kind:'region',sheetId:'summary',range:'AW1:AY4',include:'values,formulas',maxChars:2000})).ndjson);
 const checks=[];
 const card=wb.worksheets.getItem('beer_1');
 for(const [cell,expected] of [['U90',1],['Y90',3],['AE90',6]]){
  if(card.getRange(cell).values[0][0]!==null) throw Error('Expected blank input');
  card.getRange(cell).values=[['x']];wb.recalculate();
  const b=summary.getRange('AX2').values[0][0], stale=summary.getRange('AR2').values[0][0];
  checks.push({cell,expected,barnyard:b,stale_hops:stale});
  if(b!==expected || stale!==0) throw Error('Dependency mismatch');
  card.getRange(cell).clear({applyTo:'contents'});
 }
 wb.recalculate();
 await fs.writeFile(run+'/dependency_check.json',JSON.stringify(checks,null,2));
 const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#NUM!|#NULL!',options:{useRegex:true,maxResults:20},maxChars:1200});
 console.log(errors.ndjson);
 const pic=await wb.render({sheetName:'summary',range:'AR1:AZ4',scale:1.6,format:'png'});
 await fs.writeFile(run+'/after.png',new Uint8Array(await pic.arrayBuffer()));
 await (await SpreadsheetFile.exportXlsx(wb)).save(run+'/formula_authored.xlsx');
 const inventory=JSON.parse(await fs.readFile(run+'/inventory.json','utf8'));
 const rows=[];
 for(const t of inventory.tables.filter(t=>t.layer===null)) for(const f of t.fields) {
  const changed=t.file==='3.xlsx' && t.sheet==='summary' && f.name==='barnyard';
  const note=t.file==='3.xlsx' ? (t.sheet==='summary' ? '公式缓存；空卡无有效评分' : '布局列；不代表样本特征') : t.sheet==='GBM SHAP Values' ? '混合层，仅作存储统计' : f.mean===null ? '文本或全缺失；数值指标不适用' : '当前存储尺度；未重新变换';
  rows.push([t.file,t.sheet,f.name,t.rows,f.missing_rate,f.missing_rate,f.mean,f.mean,f.negative_rate,f.negative_rate,changed?'公式修正':'原样',changed?12:0,changed?12:0,0,note,f.scale]);
 }
 if(rows.length!==1599)throw Error('Unexpected field count '+rows.length);
 const audit=Workbook.create(), sh=audit.worksheets.add('清洗前后对照');
 sh.showGridLines=false;sh.tabColor='#24486C';
 sh.getRange('A2').values=[['2026 MathorCup A ｜ 清洗前后逐列对照']];
 sh.getRange('A3').values=[['clean.csv：1.csv 原样副本，250 行 × 234 列；73 个 NA 保留；数值改动 0 格。']];
 sh.getRange('A4').values=[['唯一修正：summary!AX2:AX13（barnyard），由各 beer_i!$AG$76 改为 $AG$90；原件不变。']];
 sh.getRange('A5').values=[['缺失率＝缺失格/表行数；负值占比＝负值/非缺失有限数值；空格代表指标不适用。']];
 sh.getRange('A6').values=[['1,599 个源字段；另两份 SHAP 分层视图重复 472 字段不重计。布局、混合层统计不能作为样本特征。']];
 sh.getRange('A7').values=[['评分卡全部未填写。公式缓存 0 不是有效评分；本表不证明感官改善或建模关卡通过。']];
 sh.getRange('A8').values=[['来源：A/data/raw/official-20261024/附件；逐列授权与依据见 cleaning_log.md 及上一轮数据资产盘点。']];
 const headers=['源文件','源工作表','列名','行数','缺失率·前','缺失率·后','均值·前','均值·后','负值占比·前','负值占比·后','动作','影响行数','公式改动格数','数值改动格数','统计限制','量纲判定'];
 sh.getRange('A10:P10').values=[headers];
 sh.getRange('A11:P'+(rows.length+10)).values=rows;
 sh.getRange('A2:P'+(rows.length+10)).format.font={name:'Arial',size:10,color:'#202B36'};
 sh.getRange('A2').format.font={name:'Arial',size:16,bold:true,color:'#24486C'};
 sh.getRange('A3:A8').format.font={name:'Arial',size:10,color:'#59616B'};
 sh.getRange('A7').format.font={name:'Arial',size:10,bold:true,color:'#9C5B12'};
 sh.getRange('A10:P10').format={fill:'#24486C',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},verticalAlignment:'center',horizontalAlignment:'center',wrapText:true,rowHeight:38};
 sh.getRange('A11:P'+(rows.length+10)).format.rowHeight=22;
 sh.getRange('A11:P'+(rows.length+10)).format.verticalAlignment='center';
 sh.getRange('A:A').format.columnWidth=10;
 sh.getRange('B:B').format.columnWidth=31;
 sh.getRange('C:C').format.columnWidth=32;
 sh.getRange('D:D').format.columnWidth=8;
 sh.getRange('E:F').format.columnWidth=13;
 sh.getRange('G:H').format.columnWidth=16;
 sh.getRange('I:J').format.columnWidth=14;
 sh.getRange('K:N').format.columnWidth=13;
 sh.getRange('O:O').format.columnWidth=39;
 sh.getRange('P:P').format.columnWidth=15;
 sh.getRange('D11:D'+(rows.length+10)).setNumberFormat('0');
 sh.getRange('E11:F'+(rows.length+10)).setNumberFormat('0.00%');
 sh.getRange('G11:H'+(rows.length+10)).setNumberFormat('0.000000000');
 sh.getRange('I11:J'+(rows.length+10)).setNumberFormat('0.00%');
 sh.getRange('L11:N'+(rows.length+10)).setNumberFormat('0');
 const tab=sh.tables.add('A10:P'+(rows.length+10),true,'CleaningComparison');
 tab.showFilterButton=true;
 sh.freezePanes.freezeRows(10);
 sh.freezePanes.freezeColumns(3);
 audit.recalculate();
 const prev=await audit.render({sheetName:sh.name,range:'A1:J18',scale:1.3,format:'png'});
 await fs.writeFile(run+'/comparison_preview.png',new Uint8Array(await prev.arrayBuffer()));
 console.log((await audit.inspect({kind:'region',sheetId:sh.name,range:'A10:J14',maxChars:1800})).ndjson);
 await (await SpreadsheetFile.exportXlsx(audit)).save(run+'/audit_authored.xlsx');
 await fs.writeFile(run+'/comparison_rows.json',JSON.stringify({headers,rows}));
 console.log(JSON.stringify({rows:rows.length,formula_changes:12,dependent_cases:checks.length}));
}
