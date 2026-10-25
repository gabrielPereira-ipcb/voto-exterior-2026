"""Lê o 2º turno 2026 (eleição 6258) do TSE: Brasil + 27 UFs. Grava data.json e index.html (dados embutidos).
Uso: python3 br_update.py   (na pasta do site). Só grava se algo mudou. Hora do TSE = Brasília (UTC-3)."""
import json, os, urllib.request, datetime as dt
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
B = 'https://resultados.tse.jus.br/oficial/ele2026/6258/dados/%s/%s-c0001-e006258-u.json'
UFS = 'ac al am ap ba ce df es go ma mg ms mt pa pb pe pi pr rj rn ro rr rs sc se sp to'.split()

def get(k):
    with urllib.request.urlopen(B % (k, k), timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))

def parse(d):
    v = {}
    for a in d['carg'][0]['agr']:
        for p in a['par']:
            for c in p['cand']:
                v[c['nmu'].split()[0]] = int(c['vap'])
    s = d['s']
    h = dt.datetime.strptime(d['dg'] + ' ' + d['hg'], '%d/%m/%Y %H:%M:%S') + dt.timedelta(hours=3)
    return dict(lula=v.get('LULA', 0), flavio=v.get('FLAVIO', 0), st=int(s['st']), ts=int(s['ts']),
                utc=h.strftime('%Y-%m-%dT%H:%M:%SZ'))

def main():
    keys = ['br'] + UFS
    with ThreadPoolExecutor(8) as ex:
        docs = list(ex.map(get, keys))
    out = {'ufs': {}}
    for k, d in zip(keys, docs):
        r = parse(d)
        if k == 'br': out['br'] = r
        else: out['ufs'][k.upper()] = r
    out['atualizado'] = max(x['utc'] for x in [out['br']] + list(out['ufs'].values()))
    p = os.path.join(HERE, 'data.json')
    old = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None
    cmp = lambda o: json.dumps({k: o[k] for k in ('br', 'ufs')}, sort_keys=True) if o else None
    if cmp(old) == cmp(out):
        print('sem mudanças'); return 1
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    tpl = open(os.path.join(HERE, 'tpl.html'), encoding='utf-8').read()
    open(os.path.join(HERE, 'index.html'), 'w', encoding='utf-8').write(tpl.replace('/*EMBED*/null', json.dumps(out, ensure_ascii=False)))
    tot = sum(x['lula'] + x['flavio'] for x in out['ufs'].values())
    print('gravado: votos nos estados', tot, '· br', out['br']['lula'], out['br']['flavio'], '· seções', out['br']['st'], '/', out['br']['ts']); return 0

if __name__ == '__main__':
    raise SystemExit(0 if main() in (0, 1) else 2)
