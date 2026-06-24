"""
share_routes.py — 用户成果分享模块
功能：上传成果、管理员审批、展示已通过的成果
"""
import os
import json
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request, Response, render_template

logger = logging.getLogger(__name__)

share_bp = Blueprint('share', __name__)

# MySQL 配置（从环境变量或默认值）
MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3306'))
MYSQL_DB = os.getenv('MYSQL_DB', 'geometric_ai')

# 公开接口用的只写用户（SELECT + INSERT）
MYSQL_PUBLIC_USER = os.getenv('MYSQL_PUBLIC_USER', 'share_writer')
MYSQL_PUBLIC_PASS = os.getenv('MYSQL_PUBLIC_PASS', '')

# 管理接口用的管理员用户
MYSQL_ADMIN_USER = os.getenv('MYSQL_ADMIN_USER', '')
MYSQL_ADMIN_PASS = os.getenv('MYSQL_ADMIN_PASS', '')

# 自动选择 MySQL 地址：内网优先，公网备选
_MYSQL_HOST_OVERRIDE = os.getenv('MYSQL_HOST', '')  # 环境变量可强制指定

def _detect_mysql_host():
    """自动检测 MySQL 地址：内网优先"""
    if _MYSQL_HOST_OVERRIDE:
        return _MYSQL_HOST_OVERRIDE
    import socket
    for host in ['192.168.1.88', 'www.sd517.cc']:
        try:
            sock = socket.create_connection((host, MYSQL_PORT), timeout=2)
            sock.close()
            return host
        except Exception:
            continue
    return 'www.sd517.cc'  # 默认公网

MYSQL_HOST = _detect_mysql_host()


def _get_conn(user=None, password=None):
    """获取 MySQL 连接"""
    import pymysql
    return pymysql.connect(
        host=MYSQL_HOST, port=MYSQL_PORT,
        user=user or MYSQL_ADMIN_USER,
        password=password or MYSQL_ADMIN_PASS,
        database=MYSQL_DB, charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


def _get_public_conn():
    """获取公开接口连接（只写用户）"""
    return _get_conn(MYSQL_PUBLIC_USER, MYSQL_PUBLIC_PASS)


# ==================== 分享展示页 ====================

@share_bp.route('/share')
def share_page():
    """分享展示页"""
    return render_template('share.html')


@share_bp.route('/share/upload')
def upload_page():
    """上传页"""
    return render_template('share.html', mode='upload')


# ==================== API 接口 ====================

@share_bp.route('/api/share/list', methods=['GET'])
def api_share_list():
    """获取已通过的成果列表（公开）"""
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 20))
        category = request.args.get('category', '')
        keyword = request.args.get('keyword', '')

        conn = _get_public_conn()
        cur = conn.cursor()

        where = "WHERE status='approved'"
        params = []
        if category:
            where += " AND category=%s"
            params.append(category)
        if keyword:
            where += " AND (title LIKE %s OR content LIKE %s)"
            params.extend([f'%{keyword}%', f'%{keyword}%'])

        # 总数
        cur.execute(f"SELECT COUNT(*) as total FROM shares {where}", params)
        total = cur.fetchone()['total']

        # 分页
        offset = (page - 1) * size
        cur.execute(
            f"SELECT id, title, author, category, created_at, views, likes FROM shares {where} ORDER BY created_at DESC LIMIT %s OFFSET %s",
            params + [size, offset]
        )
        items = cur.fetchall()
        conn.close()

        for item in items:
            item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M') if item['created_at'] else ''
            # 截取内容前200字作为摘要
            item['summary'] = ''

        return jsonify({"success": True, "total": total, "page": page, "size": size, "items": items})
    except Exception as e:
        logger.error(f"[SHARE] 获取列表失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@share_bp.route('/api/share/<int:share_id>', methods=['GET'])
def api_share_detail(share_id):
    """获取成果详情（公开）"""
    try:
        conn = _get_public_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM shares WHERE id=%s AND status='approved'", (share_id,))
        item = cur.fetchone()
        if not item:
            conn.close()
            return jsonify({"success": False, "error": "不存在或未通过审批"}), 404
        conn.close()

        # 增加浏览量（用管理员连接）
        try:
            conn2 = _get_conn()
            cur2 = conn2.cursor()
            cur2.execute("UPDATE shares SET views=views+1 WHERE id=%s", (share_id,))
            conn2.commit()
            conn2.close()
        except Exception:
            pass

        item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M') if item['created_at'] else ''
        item['content'] = item['content'] or ''
        return jsonify({"success": True, "item": item})
    except Exception as e:
        logger.error(f"[SHARE] 获取详情失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@share_bp.route('/api/share/submit', methods=['POST'])
def api_share_submit():
    """用户提交成果（公开接口）"""
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        author = data.get('author', '').strip()
        category = data.get('category', '其他').strip()

        if not title or not content or not author:
            return jsonify({"success": False, "error": "标题、内容和作者不能为空"}), 400

        if len(title) > 200:
            return jsonify({"success": False, "error": "标题不能超过200字"}), 400

        conn = _get_public_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO shares (title, content, author, category) VALUES (%s, %s, %s, %s)",
            (title, content, author, category)
        )
        conn.commit()
        new_id = cur.lastrowid
        conn.close()

        logger.info(f"[SHARE] 新提交: id={new_id}, title={title}, author={author}")
        return jsonify({"success": True, "message": "提交成功，等待管理员审批", "id": new_id})
    except Exception as e:
        logger.error(f"[SHARE] 提交失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@share_bp.route('/api/share/like/<int:share_id>', methods=['POST'])
def api_share_like(share_id):
    """点赞"""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE shares SET likes=likes+1 WHERE id=%s AND status='approved'", (share_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==================== 管理员审批接口 ====================

@share_bp.route('/api/admin/share/pending', methods=['GET'])
def api_admin_pending():
    """获取待审批列表"""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, title, author, category, created_at FROM shares WHERE status='pending' ORDER BY created_at ASC"
        )
        items = cur.fetchall()
        conn.close()

        for item in items:
            item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M') if item['created_at'] else ''

        return jsonify({"success": True, "items": items})
    except Exception as e:
        logger.error(f"[SHARE] 获取待审批列表失败: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@share_bp.route('/api/admin/share/<int:share_id>/detail', methods=['GET'])
def api_admin_share_detail(share_id):
    """管理员查看待审批详情"""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM shares WHERE id=%s", (share_id,))
        item = cur.fetchone()
        conn.close()

        if not item:
            return jsonify({"success": False, "error": "不存在"}), 404

        item['created_at'] = item['created_at'].strftime('%Y-%m-%d %H:%M') if item['created_at'] else ''
        item['reviewed_at'] = item['reviewed_at'].strftime('%Y-%m-%d %H:%M') if item['reviewed_at'] else ''
        return jsonify({"success": True, "item": item})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@share_bp.route('/api/admin/share/<int:share_id>/approve', methods=['POST'])
def api_admin_approve(share_id):
    """审批通过"""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE shares SET status='approved', reviewed_at=NOW(), reviewer='admin' WHERE id=%s AND status='pending'",
            (share_id,)
        )
        conn.commit()
        affected = cur.rowcount
        conn.close()

        if affected == 0:
            return jsonify({"success": False, "error": "不存在或已审批"}), 400

        logger.info(f"[SHARE] 审批通过: id={share_id}")
        return jsonify({"success": True, "message": "已通过审批"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@share_bp.route('/api/admin/share/<int:share_id>/reject', methods=['POST'])
def api_admin_reject(share_id):
    """审批拒绝"""
    try:
        data = request.get_json()
        reason = data.get('reason', '').strip() if data else ''

        conn = _get_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE shares SET status='rejected', reject_reason=%s, reviewed_at=NOW(), reviewer='admin' WHERE id=%s AND status='pending'",
            (reason, share_id)
        )
        conn.commit()
        affected = cur.rowcount
        conn.close()

        if affected == 0:
            return jsonify({"success": False, "error": "不存在或已审批"}), 400

        logger.info(f"[SHARE] 审批拒绝: id={share_id}, reason={reason}")
        return jsonify({"success": True, "message": "已拒绝"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@share_bp.route('/api/admin/share/stats', methods=['GET'])
def api_admin_share_stats():
    """分享统计"""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT status, COUNT(*) as cnt FROM shares GROUP BY status")
        rows = cur.fetchall()
        conn.close()

        stats = {"pending": 0, "approved": 0, "rejected": 0, "total": 0}
        for row in rows:
            stats[row['status']] = row['cnt']
            stats['total'] += row['cnt']

        return jsonify({"success": True, "stats": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
