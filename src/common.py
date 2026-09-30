import csv
import hashlib
import io
import json
import re
from .acquire import stable_json


def number(value):
    if value is None or value == '':
        return None
    value = float(value)
    if not __import__('math').isfinite(value):
        return None
    return int(value) if value.is_integer() else value


def constant(html, name):
    match = re.search(r'const\s+' + re.escape(name) + r'\s*=\s*', html)
    if not match:
        raise ValueError('Missing official dashboard constant ' + name)
    return json.JSONDecoder().raw_decode(html[match.end():])[0]


def read_sources(root, raw_dir=None):
    raw = raw_dir or root / 'data/raw'
    receipts = [json.loads(s) for s in (raw / 'receipts.jsonl').read_text().splitlines()]
    latest = {r['url']: r for r in receipts}
    sources = []
    for r in sorted(latest.values(), key=lambda x: x['url']):
        if not r['ok']:
            sources.append((r, None))
            continue
        body = (raw / r['path']).read_bytes()
        if hashlib.sha256(body).hexdigest() != r['sha256']:
            raise ValueError('Raw checksum mismatch: ' + r['path'])
        if r['kind'] == 'statcast':
            body = list(csv.DictReader(io.StringIO(body.decode('utf-8-sig'))))
        elif r['kind'] in ('schedule', 'feed', 'abs'):
            body = json.loads(body)
        elif r['kind'] != 'source_binary':
            body = body.decode('utf-8-sig')
        sources.append((r, body))
    return sources


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(value))


def write_csv(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or sorted({k for r in rows for k in r})
    with path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else v for k, v in row.items()})
