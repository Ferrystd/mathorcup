"""Read-only evidence for skill design; Codex-assisted, OpenAI, 2026-10-24.
Run from repository root with Python + pandas/numpy/openpyxl. No cleaning.
"""
import argparse
import json
import zipfile
from pathlib import Path
import numpy as np
import pandas as pd
import openpyxl

p = argparse.ArgumentParser()
p.add_argument('--input', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
args = p.parse_args()
if args.output.exists() or args.output.resolve().is_relative_to(args.input.resolve()):
    p.error('Output must be new and outside input')
tables = {n: pd.read_csv(args.input / n, dtype={'beer': str, 'beer_id': str}) for n in ['1.csv', '4.csv', '7.csv']}
out = {'mode': 'inspection_only', 'versions': {'pandas': pd.__version__, 'numpy': np.__version__, 'openpyxl': openpyxl.__version__}}
out['key_checks'] = {}
for name, frame in tables.items():
    if frame.beer.duplicated().any():
        raise ValueError('beer not unique: ' + name)
    joined = tables['1.csv'].merge(frame, on='beer', validate='one_to_one', suffixes=('_1', '_other'))
    out['key_checks'][name] = {'rows': len(frame), 'unique_beer': frame.beer.nunique(),
        'unique_beer_id_raw_string': frame.beer_id.nunique(), 'joined_by_beer': len(joined),
        'style_disagreements': int((joined.tasting_category_fine_1 != joined.tasting_category_fine_other).sum())}
a = tables['1.csv'].set_index('beer')
b = pd.read_excel(args.input / '8.xlsx', sheet_name='Calibrated chemical dataset', dtype={'beer': str, 'beer_id': str}).set_index('beer')
if b.index.duplicated().any():
    raise ValueError('Calibrated beer key not unique')
out['positive_anchor_probes'] = {}
for c in ['pH', 'ethanol..v.v.', 'color.EBC.', 'bitterness', 'CO2.PSI.', 'acetaldehyde']:
    x, y = a[c], b[c].reindex(a.index)
    m = x.notna() & y.notna() & (y > 0)
    out['positive_anchor_probes'][c] = {'n': int(m.sum()), 'nonpositive_or_missing_excluded': int((~m).sum()),
        'max_error_identity': float(abs(x[m]-y[m]).max()),
        'max_error_log10': float(abs(x[m]-np.log10(y[m])).max()),
        'max_error_ln': float(abs(x[m]-np.log(y[m])).max()),
        'observed_finite_calibrated_missing': {'count': int((x.notna() & y.isna()).sum()),
            'beer_keys': [str(k) for k in y.index[x.notna() & y.isna()]],
            'observed_values': sorted(float(v) for v in x[x.notna() & y.isna()].unique())},
        'calibrated_zero_cases': [{'beer': str(k), 'observed': float(x.loc[k])} for k in y.index[(y == 0) & x.notna()]]}
w = openpyxl.load_workbook(args.input / '3.xlsx', data_only=False)
cards = [s for s in w if s.title.startswith('beer_')]
out['cards'] = {'sheets': [s.title for s in cards],
    'differences_from_beer_1': {s.title: [c.coordinate for row in s for c in row if c.value != w['beer_1'][c.coordinate].value] for s in cards},
    'primary_response_nonempty': {s.title: sum(s.cell(r,c).value is not None for r in [7,20,33,45,50,54,58,62,68,72,76,82,86,90,94] for c in [3,5,7,9,11,13,15,19,21,23,25,27,29,31]) for s in cards},
    'summary_barnyard_formula_AX2': w['summary']['AX2'].value,
    'summary_stale_hops_formula_AR2': w['summary']['AR2'].value,
    'barnyard_card_label_R89': w['beer_1']['R89'].value}
w.close()
with zipfile.ZipFile(args.input / '3.xlsx') as z:
    out['cards']['noncell_parts'] = [n for n in z.namelist() if any(x in n for x in ['drawing', 'vml', 'ctrlProps', 'activeX', 'media'])]
args.output.parent.mkdir(parents=True, exist_ok=True)
with args.output.open('x', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2, allow_nan=False)
print(args.output)
