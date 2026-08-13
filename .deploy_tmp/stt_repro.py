import asyncio, aiohttp, json

API_KEY = open('/usr/local/geometry-ai/.env').read().split('SILICONFLOW_API_KEY=')[1].split('\n')[0].strip()
URL = 'https://api.siliconflow.cn/v1/audio/transcriptions'
MP3 = '/tmp/test_latest.mp3'

async def try_case(name, model, use_stream, content_type=None):
    form = aiohttp.FormData()
    form.add_field('model', model)
    if use_stream:
        async def chunks():
            with open(MP3,'rb') as f:
                while True:
                    c = f.read(64*1024)
                    if not c: break
                    yield c
        if content_type:
            form.add_field('file', chunks(), filename='test.mp3', content_type=content_type)
        else:
            form.add_field('file', chunks(), filename='test.mp3')
    else:
        with open(MP3,'rb') as f:
            data = f.read()
        if content_type:
            form.add_field('file', data, filename='test.mp3', content_type=content_type)
        else:
            form.add_field('file', data, filename='test.mp3')
    headers = {'Authorization': f'Bearer {API_KEY}'}
    async with aiohttp.ClientSession() as s:
        async with s.post(URL, headers=headers, data=form) as r:
            body = await r.text()
            print(f'[{name}] status={r.status} body={body[:250]}')

async def main():
    await try_case('1 流式+带引号model', '"FunAudioLLM/SenseVoiceSmall"', True)
    await try_case('2 非流式+带引号model', '"FunAudioLLM/SenseVoiceSmall"', False)
    await try_case('3 流式+带引号model+audio/mpeg', '"FunAudioLLM/SenseVoiceSmall"', True, 'audio/mpeg')
    await try_case('4 流式+无引号model', 'FunAudioLLM/SenseVoiceSmall', True)

asyncio.run(main())
