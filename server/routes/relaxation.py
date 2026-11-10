"""
放松训练音频路由模块
提供放松训练内容的浏览、点赞、收藏功能
"""
from flask import Blueprint, request
from utils.db import execute_query, execute_update
from utils.auth import login_required
from utils.response import success, error

relaxation_bp = Blueprint('relaxation', __name__, url_prefix='/api/relaxation')

_media_type_ready = None
_social_ready = None
_db_features = {}


def _media_type_field():
    """返回媒体类型字段，兼容未升级的旧数据库"""
    global _media_type_ready
    if _media_type_ready is None:
        try:
            execute_query('SELECT media_type FROM relaxation_audios LIMIT 1', fetch_one=True)
            _media_type_ready = True
        except Exception:
            _media_type_ready = False
    return 'media_type' if _media_type_ready else "'audio' AS media_type"


def _check_db_feature(key, sql):
    if key not in _db_features:
        try:
            execute_query(sql, fetch_one=True)
            _db_features[key] = True
        except Exception:
            _db_features[key] = False
    return _db_features[key]


def _ensure_social_features():
    """为已有数据库自动补充点赞/收藏相关表和字段"""
    global _social_ready
    if _social_ready is not None:
        return _social_ready

    try:
        if not _check_db_feature('relax_like_count', 'SELECT like_count FROM relaxation_audios LIMIT 1'):
            execute_update(
                'ALTER TABLE relaxation_audios '
                'ADD COLUMN like_count INT DEFAULT 0 COMMENT "点赞数"'
            )
            _db_features['relax_like_count'] = True

        if not _check_db_feature('relaxation_likes', 'SELECT 1 FROM relaxation_likes LIMIT 1'):
            execute_update(
                'CREATE TABLE relaxation_likes ('
                'id INT PRIMARY KEY AUTO_INCREMENT, '
                'user_id INT NOT NULL, '
                'audio_id INT NOT NULL, '
                'created_at DATETIME DEFAULT CURRENT_TIMESTAMP, '
                'UNIQUE KEY uk_relax_like (user_id, audio_id), '
                'FOREIGN KEY (user_id) REFERENCES users(id), '
                'FOREIGN KEY (audio_id) REFERENCES relaxation_audios(id)'
                ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4'
            )
            _db_features['relaxation_likes'] = True

        if not _check_db_feature('relaxation_favorites', 'SELECT 1 FROM relaxation_favorites LIMIT 1'):
            execute_update(
                'CREATE TABLE relaxation_favorites ('
                'id INT PRIMARY KEY AUTO_INCREMENT, '
                'user_id INT NOT NULL, '
                'audio_id INT NOT NULL, '
                'created_at DATETIME DEFAULT CURRENT_TIMESTAMP, '
                'UNIQUE KEY uk_relax_fav (user_id, audio_id), '
                'FOREIGN KEY (user_id) REFERENCES users(id), '
                'FOREIGN KEY (audio_id) REFERENCES relaxation_audios(id)'
                ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4'
            )
            _db_features['relaxation_favorites'] = True

        _social_ready = True
    except Exception:
        _social_ready = False
    return _social_ready


def _like_count_field():
    _ensure_social_features()
    if _check_db_feature('relax_like_count', 'SELECT like_count FROM relaxation_audios LIMIT 1'):
        return 'like_count'
    return '0 AS like_count'


def _attach_user_actions(items, user_id):
    """为列表附加当前用户的点赞/收藏状态"""
    if not items or not user_id:
        return items
    _ensure_social_features()
    if not _check_db_feature('relaxation_likes', 'SELECT 1 FROM relaxation_likes LIMIT 1'):
        for item in items:
            item['is_liked'] = False
            item['is_favorited'] = False
            item.setdefault('like_count', 0)
        return items

    ids = [i['id'] for i in items]
    placeholders = ','.join(['%s'] * len(ids))
    try:
        likes = execute_query(
            f'SELECT audio_id FROM relaxation_likes WHERE user_id = %s AND audio_id IN ({placeholders})',
            tuple([user_id] + ids)
        )
        favs = execute_query(
            f'SELECT audio_id FROM relaxation_favorites WHERE user_id = %s AND audio_id IN ({placeholders})',
            tuple([user_id] + ids)
        )
        liked_ids = {r['audio_id'] for r in likes}
        fav_ids = {r['audio_id'] for r in favs}
        for item in items:
            item['is_liked'] = item['id'] in liked_ids
            item['is_favorited'] = item['id'] in fav_ids
            item.setdefault('like_count', 0)
    except Exception:
        for item in items:
            item['is_liked'] = False
            item['is_favorited'] = False
            item.setdefault('like_count', 0)
    return items


@relaxation_bp.route('/audios', methods=['GET'])
@login_required()
def list_audios():
    """获取放松训练音频列表，支持 favorites=1 筛选收藏"""
    _ensure_social_features()
    user = request.current_user
    only_favorites = request.args.get('favorites', '') == '1'

    if only_favorites:
        if not _check_db_feature('relaxation_favorites', 'SELECT 1 FROM relaxation_favorites LIMIT 1'):
            return success([])
        audios = execute_query(
            f'SELECT ra.id, ra.title, ra.description, ra.category, {_media_type_field()}, '
            f'ra.audio_url, ra.duration, ra.cover_icon, {_like_count_field()} '
            f'FROM relaxation_audios ra '
            f'INNER JOIN relaxation_favorites rf ON ra.id = rf.audio_id '
            f'WHERE ra.status = 1 AND rf.user_id = %s ORDER BY rf.created_at DESC',
            (user['id'],)
        )
    else:
        audios = execute_query(
            f'SELECT id, title, description, category, {_media_type_field()}, '
            f'audio_url, duration, cover_icon, {_like_count_field()} '
            f'FROM relaxation_audios WHERE status = 1 ORDER BY id'
        )

    _attach_user_actions(audios, user['id'])
    return success(audios)


@relaxation_bp.route('/audios/<int:audio_id>', methods=['GET'])
@login_required()
def get_audio(audio_id):
    """获取单条放松训练内容详情"""
    _ensure_social_features()
    user = request.current_user
    audio = execute_query(
        f'SELECT id, title, description, category, {_media_type_field()}, '
        f'audio_url, duration, cover_icon, {_like_count_field()} '
        f'FROM relaxation_audios WHERE id = %s AND status = 1',
        (audio_id,), fetch_one=True
    )
    if not audio:
        return error('内容不存在或已下架', 404)

    audio['is_liked'] = False
    audio['is_favorited'] = False
    audio.setdefault('like_count', 0)

    if _check_db_feature('relaxation_likes', 'SELECT 1 FROM relaxation_likes LIMIT 1'):
        liked = execute_query(
            'SELECT id FROM relaxation_likes WHERE user_id = %s AND audio_id = %s',
            (user['id'], audio_id), fetch_one=True
        )
        favorited = execute_query(
            'SELECT id FROM relaxation_favorites WHERE user_id = %s AND audio_id = %s',
            (user['id'], audio_id), fetch_one=True
        )
        audio['is_liked'] = bool(liked)
        audio['is_favorited'] = bool(favorited)

    return success(audio)


@relaxation_bp.route('/audios/<int:audio_id>/like', methods=['POST'])
@login_required()
def like_audio(audio_id):
    """点赞放松训练内容"""
    _ensure_social_features()
    user_id = request.current_user['id']
    exists = execute_query(
        'SELECT id FROM relaxation_likes WHERE user_id = %s AND audio_id = %s',
        (user_id, audio_id), fetch_one=True
    )
    if exists:
        return error('已经点赞过了')

    execute_update(
        'INSERT INTO relaxation_likes (user_id, audio_id) VALUES (%s, %s)',
        (user_id, audio_id)
    )
    execute_update(
        'UPDATE relaxation_audios SET like_count = like_count + 1 WHERE id = %s',
        (audio_id,)
    )
    count = execute_query(
        'SELECT like_count FROM relaxation_audios WHERE id = %s',
        (audio_id,), fetch_one=True
    )
    return success({'like_count': count['like_count']}, '点赞成功')


@relaxation_bp.route('/audios/<int:audio_id>/like', methods=['DELETE'])
@login_required()
def unlike_audio(audio_id):
    """取消点赞"""
    _ensure_social_features()
    user_id = request.current_user['id']
    affected = execute_update(
        'DELETE FROM relaxation_likes WHERE user_id = %s AND audio_id = %s',
        (user_id, audio_id)
    )
    if affected:
        execute_update(
            'UPDATE relaxation_audios SET like_count = GREATEST(like_count - 1, 0) WHERE id = %s',
            (audio_id,)
        )
    count = execute_query(
        'SELECT like_count FROM relaxation_audios WHERE id = %s',
        (audio_id,), fetch_one=True
    )
    return success({'like_count': count['like_count']}, '已取消点赞')


@relaxation_bp.route('/audios/<int:audio_id>/favorite', methods=['POST'])
@login_required()
def favorite_audio(audio_id):
    """收藏放松训练内容"""
    _ensure_social_features()
    user_id = request.current_user['id']
    exists = execute_query(
        'SELECT id FROM relaxation_favorites WHERE user_id = %s AND audio_id = %s',
        (user_id, audio_id), fetch_one=True
    )
    if exists:
        return error('已经收藏过了')

    execute_update(
        'INSERT INTO relaxation_favorites (user_id, audio_id) VALUES (%s, %s)',
        (user_id, audio_id)
    )
    return success(message='收藏成功')


@relaxation_bp.route('/audios/<int:audio_id>/favorite', methods=['DELETE'])
@login_required()
def unfavorite_audio(audio_id):
    """取消收藏"""
    _ensure_social_features()
    user_id = request.current_user['id']
    execute_update(
        'DELETE FROM relaxation_favorites WHERE user_id = %s AND audio_id = %s',
        (user_id, audio_id)
    )
    return success(message='已取消收藏')
