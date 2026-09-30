"""Immutable, content-addressed downloads; receipt index is append-only."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta, datetime, timezone
import hashlib
import json
from pathlib import Path
import time
import urllib.request
from urllib.parse import urlencode


def stable_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n'


def acquire(root, start, end, raw_dir=None, workers=8):
    """Acquire a date-bounded snapshot into an isolated content-addressed store."""
    raw = Path(raw_dir) if raw_dir else root / 'data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    index = raw / 'receipts.jsonl'
    previous = [json.loads(x) for x in index.read_text().splitlines()] if index.exists() else []
    cache = {r['url']: r for r in previous if r.get('ok')}

    def download(url, kind):
        if url in cache:
            r = cache[url]
            body = (raw / r['path']).read_bytes()
            if hashlib.sha256(body).hexdigest() != r['sha256']:
                raise ValueError('Raw checksum mismatch: ' + r['path'])
            return r, body
        receipt = {'url': url, 'kind': kind, 'retrieved_at': datetime.now(timezone.utc).isoformat()}
        for attempt in range(3):
            try:
                request = urllib.request.Request(url, headers={'User-Agent': 'Pascal-ABS-Research/0.1 (public research)'})
                with urllib.request.urlopen(request, timeout=90) as response:
                    body = response.read()
                    receipt['content_type'] = response.headers.get('Content-Type')
                    receipt['final_url'] = response.url
                digest = hashlib.sha256(body).hexdigest()
                path = raw / 'objects' / digest
                path.parent.mkdir(exist_ok=True)
                if not path.exists():
                    with path.open('xb') as f:
                        f.write(body)
                receipt.update(ok=True, sha256=digest, path=str(path.relative_to(raw)), bytes=len(body))
                return receipt, body
            except Exception as exc:
                receipt.update(ok=False, error=str(exc))
                if attempt < 2:
                    time.sleep(attempt + 1)
        return receipt, None

    def save(receipt):
        if receipt not in previous:
            with index.open('a') as f:
                f.write(json.dumps(receipt, sort_keys=True) + '\n')
            previous.append(receipt)

    url = 'https://statsapi.mlb.com/api/v1/schedule?' + urlencode(dict(sportId=1, startDate=start, endDate=end, gameType='R'))
    receipt, body = download(url, 'schedule')
    save(receipt)
    if body is None:
        raise RuntimeError('Schedule unavailable; see receipts')
    games = [g for day in json.loads(body)['dates'] for g in day['games']
             if g['gameType'] == 'R' and g['status']['abstractGameState'] == 'Final'
             and start <= g['officialDate'] <= end]
    jobs = [('https://statsapi.mlb.com' + g['link'], 'feed') for g in games]
    teams = sorted({g['teams'][s]['team']['id'] for g in games for s in ('home', 'away')})
    for team in teams:
        query = urlencode(dict(year=start[:4], challengeType='team-summary', gameType='regular', level='mlb', id=team, groupBy=''))
        jobs.append((f'https://baseballsavant.mlb.com/leaderboard/services/abs/{team}?' + query, 'abs'))
    day = date.fromisoformat(start)
    while day <= date.fromisoformat(end):
        query = urlencode(dict(all='true', type='details', game_date_gt=day.isoformat(), game_date_lt=day.isoformat(), hfGT='R|', hfSea=start[:4]+'|'))
        jobs.append(('https://baseballsavant.mlb.com/statcast_search/csv?' + query, 'statcast'))
        day += timedelta(days=1)
    jobs += [('https://baseballsavant.mlb.com/abs', 'abs_dashboard'),
             ('https://baseballsavant.mlb.com/csv-docs', 'source_docs'),
             ('https://baseballsavant.mlb.com/abs-metrics-documentation', 'source_docs'),
             ('https://img.mlbstatic.com/opprops-images/image/upload/opprops/jgdgj1bak2bgiskwpdnm.pdf', 'source_binary'),
             ('https://builds.mlbstatic.com/baseballsavant.mlb.com/v1/sections/homepage-new/builds/e03823d6301cce7f3555537b367f719eccb28333/scripts/build/chunks/zone-Cpwqk-Fc.js', 'source_docs')]
    failures = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for n, (receipt, _) in enumerate(pool.map(lambda job: download(*job), jobs), 1):
            save(receipt)
            if not receipt['ok']:
                failures.append(receipt)
            print(f'{n}/{len(jobs)} {receipt["kind"]}: {"ok" if receipt["ok"] else receipt["error"]}', flush=True)
    print(f'Expected completed games: {len(games)}. Download failures: {len(failures)}', flush=True)
    return not failures


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    p.add_argument('--start', default='2026-08-24')
    p.add_argument('--end', default='2026-08-30')
    p.add_argument('--raw-dir', type=Path)
    p.add_argument('--workers', type=int, default=8)
    a = p.parse_args()
    raise SystemExit(0 if acquire(a.root, a.start, a.end, a.raw_dir, a.workers) else 2)
