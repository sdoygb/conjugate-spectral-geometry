import re

data = open('johnston2014.html', encoding='utf-8', errors='replace').read()
# 去掉 script/style
data = re.sub(r'<script.*?</script>', ' ', data, flags=re.S)
data = re.sub(r'<style.*?</style>', ' ', data, flags=re.S)
# 数学环境加标记，便于阅读
data = re.sub(r'<math[^>]*>', ' [M]', data, flags=re.S)
data = re.sub(r'</math>', '[/M]', data, flags=re.S)
text = re.sub(r'<[^>]+>', ' ', data)
text = re.sub(r'\s+', ' ', text)
open('johnston2014.txt', 'w', encoding='utf-8').write(text)
print('len =', len(text))
