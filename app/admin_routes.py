"""
admin_routes.py — Geometry AI Server 管理后台路由
提供管理页面渲染、配置读写、日志查看等功能。
"""

import os
import json
import functools
import logging
from flask import Blueprint, render_template, request, jsonify, Response

import config as _config_module

admin_bp = Blueprint('admin', __name__)

# 快捷引用
PROJECT_ROOT = _config_module.PROJECT_ROOT
_LOG_DIR = _config_module._LOG_DIR
logger = _config_module.logger


def require_admin(f):
    """简单的 admin 认证：通过环境变量 GAI_ADMIN_TOKEN 或默认 token 验证"""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = os.getenv('GAI_ADMIN_TOKEN', 'geometry-ai-admin')
        auth = request.headers.get('Authorization', '')
        query_token = request.args.get('token', '')
        if auth == f'Bearer {token}' or query_token == token:
            return f(*args, **kwargs)
        return jsonify({"error": "未授权访问", "code": 401}), 401
    return decorated


def _find_env_file():
    """
    查找 .env 文件路径。
    优先级：PROJECT_ROOT/.env > 上级目录/.env
    """
    # 项目根目录
    candidates = [
        os.path.join(PROJECT_ROOT, '.env'),
        os.path.join(os.path.dirname(PROJECT_ROOT), '.env'),
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def _parse_env_file(filepath):
    """
    解析 .env 文件为字典。
    支持 # 注释和空行，忽略无等号的行。
    """
    config = {}
    if not filepath or not os.path.isfile(filepath):
        return config
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过空行和注释
                if not line or line.startswith('#'):
                    continue
                # 解析 KEY=VALUE
                if '=' in line:
                    key, _, value = line.partition('=')
                    config[key.strip()] = value.strip()
    except Exception as e:
        logger.error(f"[ADMIN] 读取 .env 文件失败: {e}")
    return config


def _write_env_file(filepath, config):
    """
    将字典写入 .env 文件。
    保留原始注释和格式，仅更新已知的键值。
    """
    # 已知的配置键（只更新这些键，保留其他内容）
    known_keys = {
        'GAI_API_KEY', 'GAI_BASE_URL', 'GAI_MODEL', 'GAI_MODEL_LITE',
        'GAI_MODEL_VISION', 'GAI_EMBEDDING_MODEL', 'GT_EMBEDDING_MODE',
        'GT_LOCAL_EMBEDDING_MODEL', 'EXTRA_MODELS',
    }

    # 如果文件不存在，直接写入
    if not os.path.isfile(filepath):
        lines = ['# Geometry AI Server 配置文件', '']
        for key in known_keys:
            if key in config:
                lines.append(f'{key}={config[key]}')
        content = '\n'.join(lines) + '\n'
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return

    # 文件存在，逐行更新
    updated_keys = set()
    new_lines = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original_lines = f.readlines()

        for line in original_lines:
            stripped = line.strip()
            # 保留空行和注释
            if not stripped or stripped.startswith('#'):
                new_lines.append(line)
                continue
            # 解析键值
            if '=' in stripped:
                key, _, _ = stripped.partition('=')
                key = key.strip()
                if key in known_keys and key in config:
                    new_lines.append(f'{key}={config[key]}\n')
                    updated_keys.add(key)
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)

        # 追加新增的键
        for key in known_keys:
            if key in config and key not in updated_keys:
                new_lines.append(f'{key}={config[key]}\n')

        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    except Exception as e:
        logger.error(f"[ADMIN] 写入 .env 文件失败: {e}")
        raise


def _mask_api_key(key):
    """
    对 API Key 进行脱敏处理：只显示前8位 + ***
    如果长度不足8位，显示前半部分 + ***
    """
    if not key:
        return ''
    if len(key) <= 8:
        return key[:4] + '***'
    return key[:8] + '***'


# ==================== 路由 ====================

@admin_bp.route('/admin')
def admin_page():
    """渲染管理页面（未认证时显示登录表单）"""
    token = os.getenv('GAI_ADMIN_TOKEN', 'geometry-ai-admin')
    auth = request.headers.get('Authorization', '')
    query_token = request.args.get('token', '')
    if auth == f'Bearer {token}' or query_token == token:
        return render_template('admin.html')
    # 未认证，显示登录表单
    login_html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>Geometry AI 管理后台 - 登录</title>
<style>
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f5f5f5; }
.card { background: #fff; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.1); padding: 40px; width: 360px; }
h2 { margin: 0 0 20px; color: #333; text-align: center; }
input[type=password] { width: 100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; box-sizing: border-box; margin-bottom: 16px; }
button { width: 100%; padding: 10px; background: #4a90d9; color: #fff; border: none; border-radius: 6px; font-size: 14px; cursor: pointer; }
button:hover { background: #357abd; }
.error { color: #e74c3c; font-size: 13px; text-align: center; margin-bottom: 12px; display: none; }
</style>
</head>
<body>
<div class="card">
<h2>Geometry AI 管理后台</h2>
<p class="error" id="error">Token 不正确，请重试</p>
<form id="loginForm">
<input type="password" id="tokenInput" placeholder="请输入 Admin Token" autofocus>
<button type="submit">登 录</button>
</form>
</div>
<script>
document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault();
    var t = document.getElementById('tokenInput').value.trim();
    if (t) { window.location.href = '/admin?token=' + encodeURIComponent(t); }
});
if (new URLSearchParams(window.location.search).get('error') === '1') {
    document.getElementById('error').style.display = 'block';
}
</script>
</body>
</html>'''
    return Response(login_html, mimetype='text/html; charset=utf-8')


@admin_bp.route('/admin/config', methods=['GET'])
@require_admin
def admin_get_config():
    """
    读取 .env 配置文件，返回 JSON 格式的配置。
    API Key 进行脱敏处理（只显示前8位+***）。
    """
    env_path = _find_env_file()
    config = _parse_env_file(env_path)

    # 对 API Key 进行脱敏
    if 'GAI_API_KEY' in config:
        config['GAI_API_KEY'] = _mask_api_key(config['GAI_API_KEY'])

    # 标记 API Key 是否已脱敏
    config['_api_key_masked'] = True
    config['_env_path'] = env_path or '未找到 .env 文件'

    return jsonify(config)


@admin_bp.route('/admin/config', methods=['POST'])
@require_admin
def admin_save_config():
    """
    保存 .env 配置文件。
    接收 JSON body，验证必要字段后写入 .env 文件。
    """
    data = request.get_json(force=True, silent=True) or {}

    # 验证必要字段
    required_fields = ['GAI_API_KEY', 'GAI_BASE_URL', 'GAI_MODEL']
    for field in required_fields:
        value = data.get(field, '').strip()
        if not value:
            return jsonify({
                "success": False,
                "error": f"缺少必要字段: {field}"
            }), 400

    # 如果 API Key 是脱敏值（包含 ***），说明用户没有修改，跳过
    api_key = data.get('GAI_API_KEY', '').strip()
    if '***' in api_key:
        # 保留原始值，从 .env 文件读取
        env_path = _find_env_file()
        original = _parse_env_file(env_path)
        if 'GAI_API_KEY' in original:
            data['GAI_API_KEY'] = original['GAI_API_KEY']

    # 查找或创建 .env 文件路径
    env_path = _find_env_file()
    if not env_path:
        env_path = os.path.join(PROJECT_ROOT, '.env')

    try:
        _write_env_file(env_path, data)
        # 实时重载 EXTRA_MODELS（无需重启）
        if 'EXTRA_MODELS' in data:
            new_models = [m.strip() for m in data['EXTRA_MODELS'].split(',') if m.strip()]
            _config_module.EXTRA_MODELS[:] = new_models
        logger.info(f"[ADMIN] 配置已保存到 {env_path}")
        return jsonify({
            "success": True,
            "message": "配置已保存",
            "env_path": env_path
        })
    except Exception as e:
        logger.error(f"[ADMIN] 保存配置失败: {e}")
        return jsonify({
            "success": False,
            "error": f"保存配置失败: {str(e)}"
        }), 500


@admin_bp.route('/admin/logs')
@require_admin
def admin_logs():
    """
    返回最近的日志内容（纯文本）。
    读取 logs/geometry_ai.log 的最后 200 行。
    """
    log_file = os.path.join(_LOG_DIR, 'geometry_ai.log')

    if not os.path.isfile(log_file):
        return Response("日志文件不存在: " + log_file, mimetype='text/plain')

    try:
        # 读取最后 200 行
        with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()

        # 取最后 200 行
        recent_lines = lines[-200:] if len(lines) > 200 else lines
        content = ''.join(recent_lines)

        return Response(content, mimetype='text/plain; charset=utf-8')

    except Exception as e:
        logger.error(f"[ADMIN] 读取日志失败: {e}")
        return Response("读取日志失败: " + str(e), mimetype='text/plain')


@admin_bp.route('/admin/restart', methods=['POST'])
@require_admin
def admin_restart():
    """
    重启中间层服务。
    通过 launchctl 或直接 kill 进程实现。
    """
    import subprocess
    try:
        my_pid = os.getpid()
        plist_path = os.path.expanduser('~/Library/LaunchAgents/com.geometryai.server.plist')
        if os.path.exists(plist_path):
            subprocess.Popen(['launchctl', 'kickstart', '-k', 'gui/$(id -u)/com.geometryai.server'],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return jsonify({"success": True, "message": "服务正在重启..."})
        else:
            # 非 launchd 管理：用 setsid 启动新进程，确保不被父进程终止
            import sys
            python = sys.executable
            server_dir = _config_module.PROJECT_ROOT
            subprocess.Popen([
                'bash', '-c',
                f'nohup {python} {server_dir}/server.py > /dev/null 2>&1 & sleep 1 && kill -9 {my_pid}'
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
               preexec_fn=os.setsid)
            return jsonify({"success": True, "message": "服务正在重启..."})
    except Exception as e:
        logger.error(f"[ADMIN] 重启失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
