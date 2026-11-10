"""
心情日记路由模块
提供心情记录的增删查及媒体上传功能
"""
import os
import uuid
from pathlib import Path

from flask import Blueprint, request
from werkzeug.utils import secure_filename

from utils.db import execute_query, execute_update
from utils.auth import login_required
from utils.response import success, error
from utils.media_list import (
    ensure_media_list_column,
    validate_media_list,
    pack_media_for_db,
    attach_media_list,
    remove_all_media,
)

mood_bp = Blueprint('mood', __name__, url_prefix='/api/mood')

MOOD_LABELS = {
    1: '非常低落',
    2: '有些低落',
    3: '一般',
    4: '还不错',
    5: '非常开心'
}

MEDIA_DIR = Path(__file__).resolve().parent.parent / 'static' / 'media' / 'mood'
IMAGE_EXTS = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
VIDEO_EXTS = {'mp4', 'webm', 'mov', 'm4v'}
MAX_IMAGE_SIZE = 10 * 1024 * 1024
MAX_VIDEO_SIZE = 50 * 1024 * 1024

_media_columns_ready = None


def _ensure_media_columns():
    """为已有数据库自动补充媒体字段"""
    global _media_columns_ready
    if _media_columns_ready is not None:
        return _media_columns_ready
    try:
        execute_query('SELECT media_url, media_type FROM mood_diaries LIMIT 1', fetch_one=True)
        _media_columns_ready = True
    except Exception:
        try:
            execute_update(
                'ALTER TABLE mood_diaries '
                'ADD COLUMN media_url VARCHAR(500) DEFAULT NULL COMMENT "媒体文件地址", '
                'ADD COLUMN media_type ENUM("image", "video") DEFAULT NULL COMMENT "媒体类型"'
            )
            _media_columns_ready = True
        except Exception:
            _media_columns_ready = False
    ensure_media_list_column('mood_diaries')
    return _media_columns_ready


def _media_fields_sql():
    _ensure_media_columns()
    return 'md.*, u.real_name as user_name'


def _remove_media_file(media_url):
    if not media_url or not media_url.startswith('/static/media/mood/'):
        return
    file_path = Path(__file__).resolve().parent.parent / media_url.lstrip('/')
    if file_path.is_file():
        file_path.unlink()


def _resolve_media_list(data):
    """解析请求体中的媒体列表（兼容旧单文件字段）"""
    if data.get('media_list') is not None:
        return validate_media_list(data.get('media_list'), '/static/media/mood/')
    media_url = data.get('media_url') or None
    media_type = data.get('media_type') or None
    if not media_url and not media_type:
        return []
    if bool(media_url) != bool(media_type):
        raise ValueError('媒体信息不完整')
    return validate_media_list(
        [{'media_url': media_url, 'media_type': media_type}],
        '/static/media/mood/'
    )


@mood_bp.route('/labels', methods=['GET'])
@login_required()
def get_mood_labels():
    """获取心情等级标签映射"""
    return success(MOOD_LABELS)


@mood_bp.route('/upload', methods=['POST'])
@login_required()
def upload_media():
    """上传心情日记配图或视频"""
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

    media_url = f'/static/media/mood/{filename}'
    return success({'media_url': media_url, 'media_type': media_type}, '上传成功')


@mood_bp.route('', methods=['GET'])
@login_required()
def list_diaries():
    """获取心情日记列表"""
    user = request.current_user
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    offset = (page - 1) * page_size

    if user['role'] == 'admin':
        where = 'WHERE 1=1'
        params = []
    else:
        where = 'WHERE md.user_id = %s'
        params = [user['id']]

    total = execute_query(
        f'SELECT COUNT(*) as count FROM mood_diaries md {where}',
        tuple(params) if params else None,
        fetch_one=True
    )['count']

    params.extend([page_size, offset])
    items = execute_query(
        f'SELECT {_media_fields_sql()} '
        f'FROM mood_diaries md LEFT JOIN users u ON md.user_id = u.id '
        f'{where} ORDER BY md.created_at DESC LIMIT %s OFFSET %s',
        tuple(params)
    )

    for item in items:
        item['mood_label'] = MOOD_LABELS.get(item['mood_level'], '未知')
        attach_media_list(item)

    return success({
        'list': items,
        'total': total,
        'page': page,
        'page_size': page_size
    })


@mood_bp.route('', methods=['POST'])
@login_required()
def create_diary():
    """
    创建心情日记
    请求体: { mood_level, content, tags, media_list } 或兼容 media_url, media_type
    """
    _ensure_media_columns()
    data = request.get_json()
    mood_level = data.get('mood_level')
    content = data.get('content', '')
    tags = data.get('tags', '')

    if not mood_level or mood_level not in range(1, 6):
        return error('请选择有效的心情等级(1-5)')

    try:
        media_list = _resolve_media_list(data)
    except ValueError as exc:
        return error(str(exc))

    media_json, media_url, media_type = pack_media_for_db(media_list)

    diary_id = execute_update(
        'INSERT INTO mood_diaries (user_id, mood_level, content, tags, media_url, media_type, media_list) '
        'VALUES (%s, %s, %s, %s, %s, %s, %s)',
        (request.current_user['id'], mood_level, content, tags, media_url, media_type, media_json)
    )

    return success({'diary_id': diary_id}, '心情记录保存成功')


@mood_bp.route('/calendar', methods=['GET'])
@login_required()
def calendar_data():
    """获取指定月份的心情日历数据（每日展示最新一条心情）"""
    user_id = request.current_user['id']
    year = int(request.args.get('year', 0))
    month = int(request.args.get('month', 0))
    if not year or not month or month < 1 or month > 12:
        return error('请提供有效的 year 和 month 参数')

    if month == 12:
        end_date = f'{year + 1}-01-01'
    else:
        end_date = f'{year}-{month + 1:02d}-01'
    start_date = f'{year}-{month:02d}-01'

    items = execute_query(
        f'SELECT {_media_fields_sql()} '
        f'FROM mood_diaries md LEFT JOIN users u ON md.user_id = u.id '
        f'WHERE md.user_id = %s AND md.created_at >= %s AND md.created_at < %s '
        f'ORDER BY md.created_at ASC',
        (user_id, start_date, end_date)
    )

    day_map = {}
    counts = {}
    for item in items:
        created = item['created_at']
        if hasattr(created, 'strftime'):
            date_key = created.strftime('%Y-%m-%d')
        else:
            date_key = str(created)[:10]
        counts[date_key] = counts.get(date_key, 0) + 1
        item['mood_label'] = MOOD_LABELS.get(item['mood_level'], '未知')
        day_map[date_key] = {
            'date': date_key,
            'mood_level': item['mood_level'],
            'mood_label': item['mood_label'],
            'latest_id': item['id'],
        }

    result = []
    for date_key in sorted(day_map.keys()):
        entry = day_map[date_key]
        entry['count'] = counts[date_key]
        result.append(entry)

    return success({
        'year': year,
        'month': month,
        'days': result,
    })


@mood_bp.route('/by-date', methods=['GET'])
@login_required()
def diaries_by_date():
    """获取指定日期的全部心情日记"""
    user = request.current_user
    date_str = request.args.get('date', '').strip()
    if not date_str or len(date_str) != 10:
        return error('请提供 date 参数，格式 YYYY-MM-DD')

    try:
        parts = date_str.split('-')
        if len(parts) != 3:
            raise ValueError
        int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return error('日期格式无效')

    if user['role'] == 'admin':
        where = 'WHERE DATE(md.created_at) = %s'
        params = [date_str]
    else:
        where = 'WHERE md.user_id = %s AND DATE(md.created_at) = %s'
        params = [user['id'], date_str]

    items = execute_query(
        f'SELECT {_media_fields_sql()} '
        f'FROM mood_diaries md LEFT JOIN users u ON md.user_id = u.id '
        f'{where} ORDER BY md.created_at DESC',
        tuple(params)
    )

    for item in items:
        item['mood_label'] = MOOD_LABELS.get(item['mood_level'], '未知')
        attach_media_list(item)

    return success({
        'date': date_str,
        'list': items,
        'total': len(items),
    })


@mood_bp.route('/<int:diary_id>', methods=['DELETE'])
@login_required()
def delete_diary(diary_id):
    """删除心情日记（仅本人或管理员可删除）"""
    _ensure_media_columns()
    diary = execute_query(
        'SELECT user_id, media_url, media_list FROM mood_diaries WHERE id = %s',
        (diary_id,),
        fetch_one=True
    )
    if not diary:
        return error('日记不存在')

    user = request.current_user
    if user['role'] != 'admin' and diary['user_id'] != user['id']:
        return error('无权删除此日记')

    execute_update('DELETE FROM mood_diaries WHERE id = %s', (diary_id,))
    remove_all_media(diary.get('media_list'), diary.get('media_url'), _remove_media_file)
    return success(message='日记已删除')


@mood_bp.route('/stats', methods=['GET'])
@login_required()
def mood_stats():
    """获取当前用户近30天心情统计"""
    user_id = request.current_user['id']
    stats = execute_query(
        'SELECT mood_level, COUNT(*) as count '
        'FROM mood_diaries '
        'WHERE user_id = %s AND created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) '
        'GROUP BY mood_level ORDER BY mood_level',
        (user_id,)
    )

    result = [{'mood_level': i, 'mood_label': MOOD_LABELS[i], 'count': 0} for i in range(1, 6)]
    for s in stats:
        for r in result:
            if r['mood_level'] == s['mood_level']:
                r['count'] = s['count']

    return success(result)
