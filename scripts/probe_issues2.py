import json, ssl, urllib.request
TOKEN = open('/Users/oygb/Downloads/GeometryAI-Mac-Build/.github_token').read().strip()
ctx = ssl._create_unverified_context()
def api(path):
    req = urllib.request.Request('https://api.github.com' + path,
        headers={'Authorization': 'token ' + TOKEN})
    with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
        return json.loads(r.read().decode())

print('='*60); print('QUTIP #2972 FULL BODY')
print(api('/repos/qutip/qutip/issues/2972')['body'])

print('='*60); print('GRAPHRICCI #37')
i = api('/repos/saibalmars/GraphRicciCurvature/issues/37')
print('title:', i['title'], '| by', i['user']['login'], '| created', i['created_at'])
print(i['body'])
for c in api('/repos/saibalmars/GraphRicciCurvature/issues/37/comments'):
    print('--comment by', c['user']['login'], ':', c['body'][:500])

# Forman-Ricci 论文检查：Balanced Forman 是否有引用实现
r = api('/search/code?q=repo:saibalmars/GraphRicciCurvature+balanced+forman')
print('balanced forman in code:', r.get('total_count'), [x['path'] for x in r.get('items', [])][:5])
