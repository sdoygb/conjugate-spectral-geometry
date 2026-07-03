"""
Final fix: Add a middleware to intercept and fix the WEUI_NAME in API responses
"""
import os
import json

MAIN_PATH = "/Library/Frameworks/Python.framework/Versions/3.11/lib/python3.11/site-packages/open_webui/main.py"

with open(MAIN_PATH, "r") as f:
    content = f.read()

# 在 import 区域添加 response 拦截中间件
old_import = "from starlette.responses import Response, StreamingResponse"
new_import = old_import + """

# PATCH: Override WEBUI_NAME in /api/config responses
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

class WebUINameFixMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Only intercept /api/config responses
        if request.url.path == "/api/config" and isinstance(response, JSONResponse):
            body = json.loads(response.body.decode())
            if "name" in body and body["name"] != "Geometry AI":
                body["name"] = "Geometry AI"
                return JSONResponse(content=body, status_code=response.status_code, headers=dict(response.headers))
        
        return response
"""

if old_import in content:
    content = content.replace(old_import, new_import)
    
    # 还要在 app 创建后添加 middleware
    old_app_start = "app = FastAPI("
    new_app_start = """# Add the WEBUI_NAME fix middleware
app.add_middleware(WebUINameFixMiddleware)

app = FastAPI("""
    
    if old_app_start in content:
        content = content.replace(old_app_start, new_app_start, 1)
    
    with open(MAIN_PATH, "w") as f:
        f.write(content)
    print("✅ 已添加 WebUINameFixMiddleware")
else:
    print("⚠️ 导入语句未找到")

print("✅ 完成")
