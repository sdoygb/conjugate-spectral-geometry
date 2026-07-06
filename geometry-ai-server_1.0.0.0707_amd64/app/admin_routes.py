"""
admin_routes.py — Geometry AI Server 管理后台路由
提供管理页面渲染、配置读写、日志查看等功能。
"""

import os
import json
import functools
import logging
from flask import Blueprint, render_template, request, jsonify, Response
import re
import datetime
import subprocess

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
    """重启中间层服务。先返回响应，再延迟执行 launchctl unload/load"""
    import threading
    try:
        plist_path = os.path.expanduser('~/Library/LaunchAgents/com.geometryai.server.plist')
        if not os.path.exists(plist_path):
            return jsonify({"success": False, "error": "未找到 plist 文件"}), 500

        def _delayed_restart():
            import time, subprocess
            time.sleep(1.5)
            try:
                subprocess.run(['launchctl', 'unload', plist_path], capture_output=True, timeout=10)
                time.sleep(1)
                subprocess.run(['launchctl', 'load', '-w', plist_path], capture_output=True, timeout=10)
                logger.info("[ADMIN] 重启完成")
            except Exception as e:
                logger.error(f"[ADMIN] 重启执行失败: {e}")

        t = threading.Thread(target=_delayed_restart, daemon=True)
        t.start()
        logger.info("[ADMIN] 服务即将重启（1.5秒后）")
        return jsonify({"success": True, "message": "服务正在重启（launchctl）..."})
    except Exception as e:
        logger.error(f"[ADMIN] 重启失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@admin_bp.route('/admin/git/status')
@require_admin
def admin_git_status():
    """
    获取 Git 仓库状态总览
    """
    cwd = _config_module.PROJECT_ROOT

    ok, branch = _run_git_command(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd)
    if not ok:
        return jsonify({"success": False, "error": "不是 Git 仓库", "is_git_repo": False})

    ok, last_commit = _run_git_command(['git', 'log', '-1', '--oneline'], cwd)

    ok, status_output = _run_git_command(['git', 'status', '--short', '--', 'articles/'], cwd)
    changes = []
    added = modified = deleted = 0
    if ok and status_output:
        for line in status_output.split('\n'):
            if line.strip():
                changes.append(line.strip())
                code = line[:2].strip()
                if code in ('A', '??'):
                    added += 1
                elif code in ('M', 'D'):
                    modified += 1
                elif line[:1] == ' ' and line[1:2] == 'M':
                    modified += 1

    version, _ = _get_git_version()

    articles_count = 0
    articles_dir = os.path.join(cwd, 'articles')
    if os.path.isdir(articles_dir):
        articles_count = len([f for f in os.listdir(articles_dir)
                              if f.endswith('.md') and '目录_总览' not in f])

    return jsonify({
        "success": True,
        "is_git_repo": True,
        "branch": branch,
        "last_commit": last_commit or "N/A",
        "changes": {
            "added": added,
            "modified": modified,
            "deleted": deleted,
            "total": added + modified + deleted,
            "details": changes[:50]
        },
        "version": version or "未知",
        "articles_count": articles_count
    })


@admin_bp.route('/admin/git/commit', methods=['POST'])
@require_admin
def admin_git_commit():
    """
    执行 Git 提交：自动更新版本号 + add + commit
    """
    cwd = _config_module.PROJECT_ROOT

    ok, _ = _run_git_command(['git', 'rev-parse', '--git-dir'], cwd)
    if not ok:
        return jsonify({"success": False, "error": "不是 Git 仓库"})

    ok, status_output = _run_git_command(['git', 'status', '--porcelain', '--', 'articles/'], cwd)
    if not ok or not status_output.strip():
        return jsonify({"success": False, "error": "articles/ 目录无任何变更，无需提交"})

    # 计算新版本号
    current_version, commit_count = _get_git_version()
    
    # 用 Git 提交数作为版本号
    if commit_count and commit_count > 0:
        new_version = f"{commit_count}"
    else:
        today = datetime.datetime.now().strftime("%y%m%d")
        if current_version:
            minor = int(current_version.split('.')[1]) if '.' in current_version else 0
            new_version = f"{today}.{minor + 1}" if current_version.startswith(today) else f"{today}.1"
        else:
            new_version = f"{today}.1"

    # 自动发现目录总纲文件
    catalog_path, old_ver = _find_catalog_file()
    if not catalog_path:
        return jsonify({"success": False, "error": "目录总纲文件不存在"})

    # 更新文件内容中的版本号
    try:
        with open(catalog_path, 'r', encoding='utf-8') as f:
            file_content = f.read()

        file_content = re.sub(
            r'文件打包版本[：:]\s*[0-9]+(\.[0-9]+)?',
            f'文件打包版本：{new_version}',
            file_content
        )
        file_content = re.sub(
            r'目录_总览与文件管理_CN_[0-9]+(\.[0-9]+)?\.md',
            f'目录_总览与文件管理_CN_{new_version}.md',
            file_content
        )

        with open(catalog_path, 'w', encoding='utf-8') as f:
            f.write(file_content)

        # 重命名文件：同步文件名中的版本号
        articles_dir = os.path.dirname(catalog_path)
        old_filename = os.path.basename(catalog_path)
        new_filename = f'目录_总览与文件管理_CN_{new_version}.md'
        new_catalog_path = os.path.join(articles_dir, new_filename)

        if old_filename != new_filename:
            os.rename(catalog_path, new_catalog_path)
            logger.info(f"[ADMIN] 目录总纲文件重命名: {old_filename} → {new_filename}")

    except Exception as e:
        return jsonify({"success": False, "error": f"更新版本号失败: {str(e)}"})

    # git add
    ok, err = _run_git_command(['git', 'add', '--', 'articles/'], cwd)
    if not ok:
        return jsonify({"success": False, "error": f"git add 失败: {err}"})

    # 生成 commit message
    changed_count = 0
    if status_output:
        changed_count = len([l for l in status_output.split('\n') if l.strip() and '目录_总览' not in l])

    articles_count = 0
    articles_dir = os.path.join(cwd, 'articles')
    if os.path.isdir(articles_dir):
        articles_count = len([f for f in os.listdir(articles_dir)
                              if f.endswith('.md') and '目录_总览' not in f])

    if changed_count > 0:
        commit_msg = f"修改 {changed_count} 篇文章 | v{new_version} | 共 {articles_count} 篇文章"
    else:
        commit_msg = f"文章目录自动维护 | v{new_version} | 共 {articles_count} 篇文章"

    # git commit
    ok, err = _run_git_command(['git', 'commit', '-m', commit_msg], cwd)
    if not ok:
        try:
            _run_git_command(['git', 'reset', 'HEAD', '--', 'articles/'], cwd)
        except:
            pass
        return jsonify({"success": False, "error": f"git commit 失败: {err}"})

    ok, commit_hash = _run_git_command(['git', 'log', '-1', '--format=%h'], cwd)
    ok, commit_full = _run_git_command(['git', 'log', '-1', '--oneline'], cwd)

    logger.info(f"[ADMIN] Git 自动提交成功: {commit_full}")

    return jsonify({
        "success": True,
        "message": "Git 提交成功",
        "commit": {
            "hash": commit_hash or "未知",
            "message": commit_full or commit_msg,
            "version": new_version
        },
        "summary": {
            "changed_files": changed_count,
            "total_articles": articles_count,
            "version": new_version
        }
    })


@admin_bp.route('/admin/git/log')
@require_admin
def admin_git_log():
    """获取 Git 提交历史（最近20条）"""
    cwd = _config_module.PROJECT_ROOT
    ok, output = _run_git_command(['git', 'log', '-20', '--oneline', '--', 'articles/'], cwd)
    if not ok:
        return jsonify({"success": False, "error": output})

    commits = []
    if output:
        for line in output.split('\n'):
            if line.strip():
                parts = line.strip().split(' ', 1)
                commits.append({
                    "hash": parts[0],
                    "message": parts[1] if len(parts) > 1 else ""
                })

    return jsonify({
        "success": True,
        "commits": commits
    })


@admin_bp.route('/admin/git/push', methods=['POST'])
@require_admin
def admin_git_push():
    """推送到远程仓库"""
    cwd = _config_module.PROJECT_ROOT

    ok, remotes = _run_git_command(['git', 'remote', '-v'], cwd)
    if not ok or not remotes.strip():
        return jsonify({"success": False, "error": "未配置远程仓库"})

    ok, branch = _run_git_command(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd)
    if not ok:
        branch = 'main'

    ok, output = _run_git_command(['git', 'push', 'origin', branch], cwd)
    if not ok:
        return jsonify({"success": False, "error": f"推送失败: {output}"})

    return jsonify({
        "success": True,
        "message": f"已推送到 origin/{branch}",
        "branch": branch
    })

# ==================== Git 文章目录版本管理 ====================

def _find_catalog_file():
    """自动发现 articles/ 下的目录总纲文件"""
    articles_dir = os.path.join(_config_module.PROJECT_ROOT, 'articles')
    if not os.path.isdir(articles_dir):
        return None, None
    for f in os.listdir(articles_dir):
        if f.startswith('目录_总览') and f.endswith('.md'):
            m = re.search(r'CN_([0-9]+(\.[0-9]+)?)\.md$', f)
            if m:
                return os.path.join(articles_dir, f), m.group(1)
    return None, None


def _get_git_version():
    """获取当前目录总纲中的版本号和 Git 提交次数"""
    catalog_path, version = _find_catalog_file()
    
    # 获取 articles/ 目录的 Git 提交总数
    commit_count = None
    ok, output = _run_git_command(['git', 'rev-list', '--count', 'HEAD', '--', 'articles/'])
    if ok and output:
        try:
            commit_count = int(output.strip())
        except:
            pass
    
    return version, commit_count


def _run_git_command(cmd, cwd=None):
    """安全执行 git 命令"""
    if cwd is None:
        cwd = _config_module.PROJECT_ROOT
    import subprocess
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=30, shell=False)
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, '命令执行超时'
    except Exception as e:
        return False, str(e)


@admin_bp.route('/admin/git/bump-version', methods=['POST'])
@require_admin
def admin_git_bump_version():
    """根据实际文件更新目录总纲的表格和版本号"""
    cwd = _config_module.PROJECT_ROOT
    articles_dir = os.path.join(cwd, 'articles')

    if not os.path.isdir(articles_dir):
        return jsonify({"success": False, "error": "articles/ 目录不存在"})

    cn_articles = []
    en_articles = []
    version_map = {}

    for f in sorted(os.listdir(articles_dir)):
        if not f.endswith('.md') or f.startswith('目录_总览'):
            continue
        m = re.match(r'^([\d.]+)_(.+)_(CN|EN)_([\d.]+)\.md$', f)
        if not m:
            continue
        num = m.group(1)
        raw_title = m.group(2).replace('_', ' ')
        lang = m.group(3)
        ver = m.group(4)
        version_map[num] = ver

        if lang == 'CN':
            try:
                with open(os.path.join(articles_dir, f), 'r', encoding='utf-8') as fh:
                    first_line = fh.readline().strip()
                    cn_title = first_line[2:].strip() if first_line.startswith('# ') else raw_title
            except:
                cn_title = raw_title
            cn_articles.append((num, cn_title, ver))
        else:
            en_articles.append((num, raw_title, ver))

    def sort_key(item):
        nums = item[0].split('.')
        result = []
        for x in nums:
            try:
                result.append(int(x))
            except:
                result.append(0)
        return result
    cn_articles.sort(key=sort_key)
    en_articles.sort(key=sort_key)

    from collections import Counter
    most_common_ver = Counter(version_map.values()).most_common(1)[0][0] if version_map else "301"
    suffix = most_common_ver.split(".")[-1] if "." in most_common_ver else most_common_ver
    today = datetime.datetime.now().strftime("%y%m%d")
    new_version = f'{today}.{suffix}'

    all_rows = []
    merged = {}
    for num, title, ver in cn_articles:
        merged[num] = {"cn": title, "cn_ver": ver, "en": "", "en_ver": ""}
    for num, title, ver in en_articles:
        if num in merged:
            merged[num]["en"] = title
            merged[num]["en_ver"] = ver
        else:
            merged[num] = {"cn": "", "cn_ver": "", "en": title, "en_ver": ver}

    sorted_nums = sorted(merged.keys(), key=lambda x: [int(p) if p.isdigit() else 0 for p in x.split(".")])
    base_rows = []
    app_rows = []
    NL = chr(10)
    for num in sorted_nums:
        entry = merged[num]
        if entry["cn"]:
            row = f'| {num} | {entry["cn"]} | {entry["cn_ver"]} |'
        else:
            row = f'| {num} |  |  |'
        if entry["en"]:
            row_en = f'| {num} | {entry["en"]} | {entry["en_ver"]} |'
        else:
            row_en = f'| {num} |  |  |'
        try:
            is_base = float(num.split('.')[0] if '.' in num else num) < 1 or num.startswith('0.')
        except:
            is_base = True
        if entry["cn"]:
            if is_base:
                base_rows.append(row)
            else:
                app_rows.append(row)
        if entry["en"]:
            if is_base:
                base_rows.append(row_en)
            else:
                app_rows.append(row_en)

    base_header = '| 编号 | 标题 | 版本 |'
    base_sep = '|------|------|------|'
    app_header = '| 编号 | 标题 | 版本 |'
    app_sep = '|------|------|------|'
    base_table_section = base_header + NL + base_sep + NL + NL.join(base_rows)
    app_table_section = app_header + NL + app_sep + NL + NL.join(app_rows)

    catalog_path, old_version = _find_catalog_file()
    if not catalog_path:
        return jsonify({"success": False, "error": "目录总纲文件不存在"})

    try:
        with open(catalog_path, 'r', encoding='utf-8') as f:
            content = f.read()

        marker_base = '### 基础篇（卷 0）'
        if marker_base not in content:
            marker_base = '### 基础篇'
        parts = content.split(marker_base)
        if len(parts) < 2:
            return jsonify({"success": False, "error": "未找到基础篇标记"})

        before_base = parts[0]
        rest = parts[1]

        table_start = rest.find('| 编号')
        if table_start < 0:
            table_start = rest.find('|------')
            if table_start >= 0:
                table_start -= 50
            table_end = rest.find(NL + chr(35)*3 + chr(32), table_start)


        if table_start >= 0:
            # 找基础篇表格结束：下一个 ### 或文件末尾
            table_end = rest.find(NL + '### ', table_start + 20)
            if table_end < 0: table_end = len(rest)
            rest = rest[:table_start] + base_table_section + rest[table_end:]

        # 处理应用篇
        marker_app = '### 应用篇'
        app_parts = rest.split(marker_app)
        if len(app_parts) >= 2:
            before_app_marker = app_parts[0]
            after_app = app_parts[1]

            app_table_start = after_app.find('| 编号')
            if app_table_start < 0:
                app_table_start = after_app.find('|------')
                if app_table_start >= 0:
                    app_table_start -= 50

            if app_table_start >= 0:
                # 找应用篇表格结束：下一个 ### 或文件末尾
                app_table_end = after_app.find(NL + '### ', app_table_start + 20)
                if app_table_end < 0:
                    app_table_end = len(after_app)
                # 替换旧表格为新表格
                after_app = after_app[:app_table_start] + NL + app_table_section + NL + after_app[app_table_end:]
            else:
                # 有 ### 应用篇 标记但没有表格，直接追加
                after_app = NL + NL + app_table_section + NL + after_app

            rest = before_app_marker + marker_app + after_app
        else:
            # 目录总纲中缺少 ### 应用篇 标记，在基础篇表格后自动追加
            rest = rest + NL + NL + marker_app + NL + NL + app_table_section + NL

        content = before_base + marker_base + rest

        content = re.sub(r'文件打包版本[：:]\s*[0-9]+(\.[0-9]+)?', '文件打包版本：' + new_version, content)
        content = re.sub(r'目录_总览与文件管理_CN_[0-9]+(\.[0-9]+)?\.md', f'目录_总览与文件管理_CN_{new_version}.md', content)

        with open(catalog_path, 'w', encoding='utf-8') as f:
            f.write(content)

        old_fn = os.path.basename(catalog_path)
        new_fn = f'目录_总览与文件管理_CN_{new_version}.md'
        new_path = os.path.join(os.path.dirname(catalog_path), new_fn)
        if old_fn != new_fn:
            os.rename(catalog_path, new_path)

        total_unique = len(set(n for n, _, _ in cn_articles + en_articles))
        logger.info(f'[ADMIN] 目录总纲已更新: 版本 {new_version}, 共 {total_unique} 篇文章')

        return jsonify({
            "success": True,
            "message": f"目录总纲已根据 {total_unique} 篇文章实际文件更新",
            "version": new_version,
            "total_articles": total_unique
        })
    except Exception as e:
        logger.error(f'[ADMIN] 更新失败: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500
