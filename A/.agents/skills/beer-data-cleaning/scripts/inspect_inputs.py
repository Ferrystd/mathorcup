"""Read-only inspection, not cleaning. AI-assisted: OpenAI Codex, 2026-10-24.
Python >=3.10; openpyxl required for XLSX. No formula evaluation or source edits.
"""
import argparse
import csv
import hashlib
import io
import json
import math
import platform
from collections import Counter
from pathlib import Path

NA = {'', 'NA', 'N/A', 'NaN', 'nan', 'NULL', 'null'}
KEYS = {'beer', 'beer_id', 'tasting_category_fine'}


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def profile_csv(path):
    raw = path.read_bytes()
    for encoding in ('utf-8-sig', 'gb18030'):
        try:
            text = raw.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f'Unsupported encoding: {path}')
    rows = list(csv.reader(io.StringIO(text), delimiter=','))
    if not rows:
        return {'rows': 0, 'columns': 0, 'encoding': encoding}
    head, data = rows[0], rows[1:]
    if any(len(row) != len(head) for row in data):
        raise ValueError(f'Ragged CSV: {path}')
    fields = []
    for j, name in enumerate(head):
        values = [r[j] for r in data]
        missing = [v for v in values if v.strip() in NA]
        present = [v for v in values if v.strip() not in NA]
        nums, invalid = [], 0
        for v in present:
            try:
                nums.append(float(v))
            except ValueError:
                invalid += 1
        finite = [v for v in nums if math.isfinite(v)]
        fields.append({'name': name, 'position_1based': j + 1,
                       'role_hint': 'metadata' if name in KEYS else 'unclassified',
                       'missing_candidates': len(missing), 'missing_tokens': dict(Counter(missing)),
                       'unique_present_strings': len(set(present)),
                       'numeric_parse_failures': invalid, 'nonfinite_count': len(nums)-len(finite),
                       'zero_count': sum(v == 0 for v in finite),
                       'negative_count': sum(v < 0 for v in finite),
                       'minimum': min(finite) if finite else None,
                       'maximum': max(finite) if finite else None})
    result = {'encoding': encoding, 'delimiter': ',', 'rows': len(data), 'columns': len(head),
              'duplicate_headers': [k for k, v in Counter(head).items() if v > 1],
              'duplicate_rows': len(data)-len(set(map(tuple, data))), 'fields': fields}
    if head and head[0] not in KEYS and len(data) == len(head)-1:
        result['square_axis_labels_equal'] = [r[0] for r in data] == head[1:]
        try:
            matrix = [[float(v) for v in r[1:]] for r in data]
            if result['square_axis_labels_equal'] and matrix and all(math.isfinite(v) for r in matrix for v in r):
                result['max_asymmetry'] = max(abs(matrix[i][j]-matrix[j][i]) for i in range(len(matrix)) for j in range(len(matrix)))
                result['max_diagonal_error_from_one'] = max(abs(matrix[i][i]-1) for i in range(len(matrix)))
        except ValueError:
            pass
    return result


def profile_xlsx(path):
    import openpyxl
    formula = openpyxl.load_workbook(path, data_only=False, read_only=True)
    cached = openpyxl.load_workbook(path, data_only=True, read_only=True)
    sheets = []
    try:
        for sheet in formula:
            nformula = zero_cache = nonempty = 0
            for row, crow in zip(sheet.iter_rows(), cached[sheet.title].iter_rows()):
                for c, cc in zip(row, crow):
                    nonempty += c.value is not None
                    if c.data_type == 'f':
                        nformula += 1
                        zero_cache += cc.value == 0
            sheets.append({'sheet': sheet.title, 'used_rows': sheet.max_row,
                           'used_columns': sheet.max_column, 'nonempty_cells': nonempty,
                           'formulas': nformula, 'formulas_with_cached_zero': zero_cache})
    finally:
        formula.close()
        cached.close()
    return {'openpyxl_version': openpyxl.__version__, 'sheets': sheets,
            'warning': 'Used range is not sample count; cached zero is not evidence of a real response.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='Extracted attachment directory, not ZIP')
    parser.add_argument('--output', type=Path, required=True, help='New JSON path outside input directory')
    args = parser.parse_args()
    root, output = args.input.resolve(), args.output.resolve()
    if not root.is_dir():
        parser.error('--input must be an existing directory')
    if output.is_relative_to(root) or output.exists():
        parser.error('--output must be new and outside the input directory')
    files = sorted(p for p in root.iterdir() if p.is_file())
    if not files:
        parser.error('Input directory is empty')
    records = []
    for path in files:
        before = sha256(path)
        record = {'name': path.name, 'bytes': path.stat().st_size, 'sha256': before}
        if path.suffix.lower() == '.csv':
            record['profile'] = profile_csv(path)
        elif path.suffix.lower() == '.xlsx':
            record['profile'] = profile_xlsx(path)
        else:
            record['profile_status'] = 'hash_only'
        if sha256(path) != before:
            raise RuntimeError(f'Input changed during inspection: {path}')
        records.append(record)
    report = {'mode': 'inspection_only_no_cleaning', 'python': platform.python_version(),
              'script_sha256': sha256(Path(__file__)), 'missing_candidate_tokens': sorted(NA), 'files': records}
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, allow_nan=False)
    print(f'Inspected {len(records)} files; raw hashes unchanged. Report: {output}')


if __name__ == '__main__':
    main()
