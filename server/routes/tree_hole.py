"""
栖心树洞路由模块
"""
import os
import uuid
from pathlib import Path

from flask import Blueprint, request
from werkzeug.utils import secure_filename

from utils.db import execute_query, execute_update, DatabaseError
from utils.auth import login_required
from utils.response import success, error
from utils.notify import create_notification
from routes.auth import _ensure_nickname_column
from utils.media_list import (
    ensure_media_list_column,
    validate_media_list,
    pack_media_for_db,
    attach_media_list,
    remove_all_media,
)

tree_hole_bp = Blueprint('tree_hole', __name__, url_prefix='/api/tree-hole')

MEDIA_DIR = Path(__file__).resolve().parent.parent / 'static' / 'media' / 'tree_hole'
IMAGE_EXTS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
VIDEO_EXTS = {'mp4', 'webm', 'mov', 'm4v'}
MAX_IMAGE_SIZE = 10 * 1024 * 1024
MAX_VIDEO_SIZE = 50 * 1024 * 1024

_table_ready = None
_media_columns_ready = None
_reply_media_columns_ready = None


def _ensure_tree_hole_tables():
    """检查树洞相关表是否存在"""
    global _table_ready
    if _table_ready is None:
        try:
            execute_query('SELECT 1 FROM tree_hole_posts LIMIT 1', fetch_one=True)
            _table_ready = True
        except Exception:
            _table_ready = False
    if not _table_ready:
        raise DatabaseError(
            '树洞功能表未创建，请先执行 server/sql/init.sql 初始化数据库',
            1146
        )


def _ensure_media_columns():
    """为已有数据库自动补充媒体字段"""
    global _media_columns_ready
    if _media_columns_ready is not None:
        return _media_columns_ready
    _ensure_tree_hole_tables()
    try:
        execute_query('SELECT media_url, media_type FROM tree_hole_posts LIMIT 1', fetch_one=True)
        _media_columns_ready = True
    except Exception:
        try:
            execute_update(
                'ALTER TABLE tree_hole_posts '
                'ADD COLUMN media_url VARCHAR(500) DEFAULT NULL COMMENT "媒体文件地址", '
                'ADD COLUMN media_type ENUM("image", "video") DEFAULT NULL COMMENT "媒体类型"'
            )
            _media_columns_ready = True
        except Exception:
            _media_columns_ready = False
    ensure_media_list_column('tree_hole_posts')
    return _media_columns_ready


def _ensure_reply_media_columns():
    """为回复表自动补充媒体字段"""
    global _reply_media_columns_ready
    if _reply_media_columns_ready is not None:
        return _reply_media_columns_ready
    _ensure_tree_hole_tables()
    try:
        execute_query('SELECT media_url, media_type FROM tree_hole_replies LIMIT 1', fetch_one=True)
        _reply_media_columns_ready = True
    except Exception:
        try:
            execute_update(
                'ALTER TABLE tree_hole_replies '
                'ADD COLUMN media_url VARCHAR(500) DEFAULT NULL COMMENT "媒体文件地址", '
                'ADD COLUMN media_type ENUM("image", "video") DEFAULT NULL COMMENT "媒体类型"'
            )
            _reply_media_columns_ready = True
        except Exception:
            _reply_media_columns_ready = False
    ensure_media_list_column('tree_hole_replies')
    return _reply_media_columns_ready


def _remove_media_file(media_url):
    if not media_url or not media_url.startswith('/static/media/tree_hole/'):
        return
    file_path = Path(__file__).resolve().parent.parent / media_url.lstrip('/')
    if file_path.is_file():
        file_path.unlink()


def _format_post(p, user):
    """格式化帖子展示字段"""
    attach_media_list(p)
    p['is_mine'] = (p['user_id'] == user['id'])
    if p['is_anonymous']:
        p['display_name'] = '匿名用户'
        p['avatar'] = None
        if not (user['role'] in ('admin', 'counselor') or p['is_mine']):
            p.pop('user_id', None)
    else:
        p['display_name'] = p.get('nickname') or p.get('real_name') or '用户'
        # avatar 来自 JOIN users.avatar
    p.pop('nickname', None)
    p.pop('real_name', None)
    return p


def _format_reply(r, user):
    """格式化回复展示字段"""
    attach_media_list(r)
    r['is_mine'] = (r['replier_id'] == user['id'])
    name = r.get('replier_nickname') or r['replier_name']
    if r['replier_role'] == 'counselor':
        r['display_name'] = name + '（咨询师）'
    elif r['replier_role'] == 'admin':
        r['display_name'] = '管理员'
    elif r['replier_role'] == 'student':
        r['display_name'] = name + '（同学）'
    else:
        r['display_name'] = name
    # 保留 r['avatar'] 供前端展示头像
    r.pop('replier_nickname', None)
    return r


def _resolve_media_list(data):
    """解析请求体中的媒体列表（兼容旧单文件字段）"""
    if data.get('media_list') is not None:
        return validate_media_list(data.get('media_list'), '/static/media/tree_hole/')
    media_url = data.get('media_url') or None
    media_type = data.get('media_type') or None
    if not media_url and not media_type:
        return []
    if bool(media_url) != bool(media_type):
        raise ValueError('媒体信息不完整')
    return validate_media_list(
        [{'media_url': media_url, 'media_type': media_type}],
        '/static/media/tree_hole/'
    )


@tree_hole_bp.route('/upload', methods=['POST'])
@login_required()
def upload_media():
    """上传树洞配图或视频"""
    _ensure_media_columns()

    file = request.files.get('file')
    if not file or not file.filename:
        return error('请选择要上传的文件')

    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext in IMAGE_EXTS:
        media_type = 'image'
        max_size = MAX_IMAGE_SIZE
    elif ext in VIDEO_EXTS:
        media_type = 'video'
        max_size = MAX_VIDEO_SIZE
    else:
        return error('仅支持图片（jpg/png/gif/webp）或视频（mp4/webm/mov/m4v）')

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > max_size:
        limit_mb = max_size // (1024 * 1024)
        return error(f'文件过大，{"图片" if media_type == "image" else "视频"}请控制在 {limit_mb}MB 以内')

    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    safe_ext = secure_filename(f'file.{ext}').rsplit('.', 1)[-1]
    filename = f'{request.current_user["id"]}_{uuid.uuid4().hex[:12]}.{safe_ext}'
    save_path = MEDIA_DIR / filename
    file.save(save_path)

    media_url = f'/static/media/tree_hole/{filename}'
    return success({'media_url': media_url, 'media_type': media_type}, '上传成功')


@tree_hole_bp.route('', methods=['GET'])
@login_required()
def list_posts():
    """获取树洞帖子列表"""
    _ensure_media_columns()
    _ensure_nickname_column()
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    offset = (page - 1) * page_size
    user = request.current_user

    total = execute_query(
        'SELECT COUNT(*) as count FROM tree_hole_posts WHERE status = 1', fetch_one=True
    )['count']

    posts = execute_query(
        'SELECT p.id, p.content, p.is_anonymous, p.media_url, p.media_type, p.media_list, p.reply_count, '
        'p.created_at, p.user_id, u.nickname, u.real_name '
        'FROM tree_hole_posts p '
        'LEFT JOIN users u ON p.user_id = u.id '
        'WHERE p.status = 1 ORDER BY p.created_at DESC LIMIT %s OFFSET %s',
        (page_size, offset)
    )

    for p in posts:
        _format_post(p, user)

    return success({'list': posts, 'total': total, 'page': page, 'page_size': page_size})


@tree_hole_bp.route('/<int:post_id>', methods=['GET'])
@login_required()
def get_post(post_id):
    """获取树洞帖子详情（含回复列表）"""
    _ensure_media_columns()
    _ensure_nickname_column()
    user = request.current_user

    post = execute_query(
        'SELECT p.id, p.content, p.is_anonymous, p.media_url, p.media_type, p.media_list, p.reply_count, '
        'p.created_at, p.user_id, u.nickname, u.real_name, u.avatar '
        'FROM tree_hole_posts p '
        'LEFT JOIN users u ON p.user_id = u.id '
        'WHERE p.id = %s AND p.status = 1',
        (post_id,), fetch_one=True
    )
    if not post:
        return error('帖子不存在或已删除')

    _format_post(post, user)

    replies = execute_query(
        'SELECT r.*, u.real_name as replier_name, u.nickname as replier_nickname, '
        'u.role as replier_role, u.avatar '
        'FROM tree_hole_replies r LEFT JOIN users u ON r.replier_id = u.id '
        'WHERE r.post_id = %s ORDER BY r.created_at ASC',
        (post_id,)
    )
    for r in replies:
        _format_reply(r, user)

    post['replies'] = replies
    return success(post)


@tree_hole_bp.route('/<int:post_id>', methods=['DELETE'])
@login_required()
def delete_post(post_id):
    """删除树洞帖子（仅本人或管理员）"""
    _ensure_media_columns()
    post = execute_query(
        'SELECT user_id, media_url, media_list FROM tree_hole_posts WHERE id = %s AND status = 1',
        (post_id,), fetch_one=True
    )
    if not post:
        return error('帖子不存在')

    user = request.current_user
    if user['role'] != 'admin' and post['user_id'] != user['id']:
        return error('无权删除此帖子')

    execute_update('UPDATE tree_hole_posts SET status = 0 WHERE id = %s', (post_id,))
    _ensure_reply_media_columns()
    reply_rows = execute_query(
        'SELECT media_url, media_list FROM tree_hole_replies WHERE post_id = %s',
        (post_id,)
    )
    for r in reply_rows:
        remove_all_media(r.get('media_list'), r.get('media_url'), _remove_media_file)
    execute_update('DELETE FROM tree_hole_replies WHERE post_id = %s', (post_id,))
    remove_all_media(post.get('media_list'), post.get('media_url'), _remove_media_file)
    return success(message='帖子已删除')


@tree_hole_bp.route('', methods=['POST'])
@login_required()
def create_post():
    """
    发布树洞留言
    请求体: { content, is_anonymous, media_list } 或兼容 media_url, media_type
    """
    _ensure_media_columns()
    data = request.get_json()
    content = data.get('content', '').strip()
    is_anonymous = 1 if data.get('is_anonymous', True) else 0

    if not content:
        try:
            media_list = _resolve_media_list(data)
        except ValueError as exc:
            return error(str(exc))
        if not media_list:
            return error('请填写留言内容或上传图片/视频')
    else:
        if len(content) > 1000:
            return error('留言内容不能超过1000字')
        try:
            media_list = _resolve_media_list(data)
        except ValueError as exc:
            return error(str(exc))

    media_json, media_url, media_type = pack_media_for_db(media_list)

    post_id = execute_update(
        'INSERT INTO tree_hole_posts (user_id, content, is_anonymous, media_url, media_type, media_list) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        (request.current_user['id'], content, is_anonymous, media_url, media_type, media_json)
    )
    return success({'post_id': post_id}, '留言发布成功')


@tree_hole_bp.route('/<int:post_id>/replies', methods=['GET'])
@login_required()
def get_replies(post_id):
    """获取树洞帖子的回复列表"""
    _ensure_nickname_column()
    replies = execute_query(
        'SELECT r.*, u.real_name as replier_name, u.nickname as replier_nickname, '
        'u.role as replier_role, u.avatar '
        'FROM tree_hole_replies r LEFT JOIN users u ON r.replier_id = u.id '
        'WHERE r.post_id = %s ORDER BY r.created_at ASC',
        (post_id,)
    )
    for r in replies:
        _format_reply(r, request.current_user)
    return success(replies)


@tree_hole_bp.route('/<int:post_id>/replies', methods=['POST'])
@login_required()
def create_reply(post_id):
    """
    回复树洞留言（所有登录用户均可回复）
    请求体: { content, media_list } 或兼容 media_url, media_type
    """
    _ensure_reply_media_columns()
    data = request.get_json()
    content = data.get('content', '').strip()

    if not content:
        try:
            media_list = _resolve_media_list(data)
        except ValueError as exc:
            return error(str(exc))
        if not media_list:
            return error('请填写回复内容或上传图片/视频')
    else:
        if len(content) > 500:
            return error('回复内容不能超过500字')
        try:
            media_list = _resolve_media_list(data)
        except ValueError as exc:
            return error(str(exc))

    post = execute_query(
        'SELECT * FROM tree_hole_posts WHERE id = %s AND status = 1',
        (post_id,), fetch_one=True
    )
    if not post:
        return error('帖子不存在')

    media_json, media_url, media_type = pack_media_for_db(media_list)

    replier = request.current_user
    execute_update(
        'INSERT INTO tree_hole_replies (post_id, replier_id, content, media_url, media_type, media_list) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        (post_id, replier['id'], content, media_url, media_type, media_json)
    )
    execute_update(
        'UPDATE tree_hole_posts SET reply_count = reply_count + 1 WHERE id = %s', (post_id,)
    )

    if post['user_id'] != replier['id']:
        create_notification(
            post['user_id'],
            '栖心树洞收到新回复',
            '您的栖心树洞留言收到了新回复，快去看看吧。',
            'tree_hole', post_id
        )
    return success(message='回复成功')


@tree_hole_bp.route('/<int:post_id>/replies/<int:reply_id>', methods=['DELETE'])
@login_required()
def delete_reply(post_id, reply_id):
    """删除树洞回复（仅本人或管理员）"""
    _ensure_reply_media_columns()
    reply = execute_query(
        'SELECT id, replier_id, media_url, media_list FROM tree_hole_replies WHERE id = %s AND post_id = %s',
        (reply_id, post_id), fetch_one=True
    )
    if not reply:
        return error('回复不存在')

    user = request.current_user
    if user['role'] != 'admin' and reply['replier_id'] != user['id']:
        return error('无权删除此回复')

    execute_update('DELETE FROM tree_hole_replies WHERE id = %s', (reply_id,))
    remove_all_media(reply.get('media_list'), reply.get('media_url'), _remove_media_file)
    execute_update(
        'UPDATE tree_hole_posts SET reply_count = GREATEST(reply_count - 1, 0) WHERE id = %s',
        (post_id,)
    )
    return success(message='回复已删除')
