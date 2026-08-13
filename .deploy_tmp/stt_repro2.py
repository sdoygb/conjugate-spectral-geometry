import asyncio, aiohttp

API_KEY = open('/usr/local/geometry-ai/.env').read().split('SILICONFLOW_API_KEY=')[1].split('\n')[0].strip()
URL = 'https://api.siliconflow.cn/v1/audio/transcriptions'
MP3 = '/tmp/test_latest.mp3'

async def main():
    form = aiohttp.FormData()
    form.add_field('model', 'FunAudioLLM/SenseVoiceSmall')
    with open(MP3,'rb') as f:
        data = f.read()
    form.add_field('file', data, filename='test.mp3')
    headers = {'Authorization': f'Bearer {API_KEY}'}
    async with aiohttp.ClientSession() as s:
        async with s.post(URL, headers=headers, data=form) as r:
            body = await r.text()
            print(f'[5 非流式+无引号model] status={r.status} body={body[:250]}')
            # 打印请求头确认传输编码
            print('request headers:', dict(s._default_headers) if hasattr(s, '_default_headers') else 'n/a')

asyncio.run(main())
