import json, ssl, urllib.request

TOKEN = open('/Users/oygb/Downloads/GeometryAI-Mac-Build/.github_token').read().strip()
ctx = ssl._create_unverified_context()

def api(path):
    req = urllib.request.Request('https://api.github.com' + path,
        headers={'Authorization': 'token ' + TOKEN, 'Accept': 'application/vnd.github+json'})
    try:
        with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {'__error__': str(e)}

# 1. qutip issue #2972 全文
print('='*60); print('QUTIP #2972')
i = api('/repos/qutip/qutip/issues/2972')
print('title:', i.get('title')); print('state:', i.get('state'), '| comments:', i.get('comments'))
print('body:', (i.get('body') or '')[:1200])
for c in api('/repos/qutip/qutip/issues/2972/comments'):
    print('--comment by', c['user']['login'], ':', c['body'][:400])

# 2. qutip 是否已有 berry 相关文件/PR
print('='*60); print('QUTIP berry search (code search)')
r = api('/search/code?q=repo:qutip/qutip+berry')
print('total:', r.get('total_count'), '| items:', [x['path'] for x in r.get('items', [])][:10])

# 3. geoopt birkhoff issues
print('='*60); print('GEOOPT issues (birkhoff/doubly stochastic)')
for q in ['birkhoff', 'doubly+stochastic']:
    r = api('/search/issues?q=repo:geoopt/geoopt+{}'.format(q))
    print('query', q, 'total:', r.get('total_count'))
    for it in r.get('items', [])[:6]:
        print('  #%d %s [%s]' % (it['number'], it['title'], it['state']))

# 4. geoopt open issues 概览
print('='*60); print('GEOOPT open issues')
r = api('/repos/geoopt/geoopt/issues?state=open&per_page=50')
print('count:', len(r))
for it in r[:25]:
    labs = ','.join(l['name'] for l in it.get('labels', []))
    print('  #%d %s [%s] cmts=%d' % (it['number'], it['title'][:60], labs, it.get('comments')))

# 5. GraphRicciCurvature issues
print('='*60); print('GRAPHRICCI issues')
r = api('/repos/saibalmars/GraphRicciCurvature/issues?state=open&per_page=50')
print('count:', len(r))
for it in r[:25]:
    labs = ','.join(l['name'] for l in it.get('labels', []))
    print('  #%d %s [%s] cmts=%d' % (it['number'], it['title'][:60], labs, it.get('comments')))
