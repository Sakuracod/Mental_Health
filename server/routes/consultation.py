"""
在线咨询路由模块
提供师生在线咨询会话和消息功能
"""
from flask import Blueprint, request
from utils.db import execute_query, execute_update
from utils.auth import login_required
from utils.response import success, error

from utils.notify import create_notification, mark_related_notifications_read
from routes.auth import _ensure_nickname_column

consultation_bp = Blueprint('consultation', __name__, url_prefix='/api/consultations')

_anonymous_column_ready = None


def _ensure_consultation_anonymous_column():
    global _anonymous_column_ready
    if _anonymous_column_ready is not None:
        return _anonymous_column_ready
    try:
        execute_query('SELECT is_anonymous FROM consultations LIMIT 1', fetch_one=True)
        _anonymous_column_ready = True
    except Exception:
        try:
            execute_update(
                'ALTER TABLE consultations ADD COLUMN is_anonymous TINYINT DEFAULT 0 '
                'COMMENT "学生是否匿名咨询" AFTER title'
            )
            _anonymous_column_ready = True
        except Exception:
            _anonymous_column_ready = False
    return _anonymous_column_ready


def _student_display_name(consultation, viewer_id, student_real_name):
    """根据匿名设置和查看者身份返回学生展示名（非匿名时使用真实姓名）"""
    if consultation['student_id'] == viewer_id:
        if consultation.get('is_anonymous'):
            return '我（匿名咨询）'
        return student_real_name or '学生'
    if consultation.get('is_anonymous'):
        return '匿名用户'
    return student_real_name or '学生'


@consultation_bp.route('', methods=['GET'])
@login_required()
def list_consultations():
    """获取咨询会话列表"""
    _ensure_consultation_anonymous_column()
    _ensure_nickname_column()
    user = request.current_user
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    offset = (page - 1) * page_size

    if user['role'] == 'student':
        where = 'WHERE c.student_id = %s'
        params = [user['id']]
    elif user['role'] == 'counselor':
        where = 'WHERE c.counselor_id = %s'
        params = [user['id']]
    else:
        where = 'WHERE 1=1'
        params = []

    total = execute_query(
        f'SELECT COUNT(*) as count FROM consultations c {where}',
        tuple(params) if params else None,
        fetch_one=True
    )['count']

    params.extend([page_size, offset])
    items = execute_query(
        f'SELECT c.*, s.real_name as student_real_name, '
        f'co.real_name as counselor_name '
        f'FROM consultations c '
        f'LEFT JOIN users s ON c.student_id = s.id '
        f'LEFT JOIN users co ON c.counselor_id = co.id '
        f'{where} ORDER BY c.updated_at DESC LIMIT %s OFFSET %s',
        tuple(params)
    )

    for item in items:
        item['student_name'] = _student_display_name(
            item, user['id'], item.get('student_real_name')
        )
        item.pop('student_real_name', None)

    return success({
        'list': items,
        'total': total,
        'page': page,
        'page_size': page_size
    })


@consultation_bp.route('', methods=['POST'])
@login_required(roles=['student'])
def create_consultation():
    """
    学生发起在线咨询
    请求体: { counselor_id, title, is_anonymous }
    """
    _ensure_consultation_anonymous_column()
    data = request.get_json()
    counselor_id = data.get('counselor_id')
    title = data.get('title', '在线咨询')
    is_anonymous = 1 if data.get('is_anonymous') else 0

    if not counselor_id:
        return error('请选择咨询师')

    counselor = execute_query(
        'SELECT id FROM users WHERE id = %s AND role = "counselor" AND status = 1',
        (counselor_id,),
        fetch_one=True
    )
    if not counselor:
        return error('咨询师不存在')

    consultation_id = execute_update(
        'INSERT INTO consultations (student_id, counselor_id, title, is_anonymous) VALUES (%s, %s, %s, %s)',
        (request.current_user['id'], counselor_id, title, is_anonymous)
    )

    return success({'consultation_id': consultation_id}, '咨询会话创建成功')


@consultation_bp.route('/<int:consultation_id>/messages', methods=['GET'])
@login_required()
def get_messages(consultation_id):
    """获取咨询会话的消息列表"""
    _ensure_consultation_anonymous_column()
    _ensure_nickname_column()
    consultation = execute_query(
        'SELECT * FROM consultations WHERE id = %s',
        (consultation_id,),
        fetch_one=True
    )
    if not consultation:
        return error('会话不存在')

    user = request.current_user
    if user['role'] not in ('admin',) and user['id'] not in (
        consultation['student_id'], consultation['counselor_id']
    ):
        return error('无权查看此会话')

    messages = execute_query(
        'SELECT cm.*, u.real_name as sender_name, u.role as sender_role '
        'FROM consultation_messages cm '
        'LEFT JOIN users u ON cm.sender_id = u.id '
        'WHERE cm.consultation_id = %s ORDER BY cm.created_at ASC',
        (consultation_id,)
    )

    for msg in messages:
        if msg['sender_id'] == consultation['student_id'] and consultation.get('is_anonymous'):
            if user['id'] == consultation['student_id']:
                msg['sender_name'] = '我（匿名）'
            else:
                msg['sender_name'] = '匿名用户'

    # 查看会话消息时，自动将该咨询相关通知标为已读
    mark_related_notifications_read(user['id'], 'consultation', consultation_id)

    return success(messages)


@consultation_bp.route('/<int:consultation_id>/messages', methods=['POST'])
@login_required()
def send_message(consultation_id):
    """
    发送咨询消息
    请求体: { content }
    """
    data = request.get_json()
    content = data.get('content', '').strip()

    if not content:
        return error('消息内容不能为空')

    consultation = execute_query(
        'SELECT * FROM consultations WHERE id = %s',
        (consultation_id,),
        fetch_one=True
    )
    if not consultation:
        return error('会话不存在')

    if consultation['status'] == 'closed':
        return error('对话已结束，无法发送消息')

    user = request.current_user
    if user['id'] not in (consultation['student_id'], consultation['counselor_id']):
        return error('无权在此会话中发送消息')

    message_id = execute_update(
        'INSERT INTO consultation_messages (consultation_id, sender_id, content) VALUES (%s, %s, %s)',
        (consultation_id, user['id'], content)
    )

    execute_update(
        'UPDATE consultations SET updated_at = NOW() WHERE id = %s',
        (consultation_id,)
    )

    # 通知对方有新消息
    receiver_id = (
        consultation['counselor_id']
        if user['id'] == consultation['student_id']
        else consultation['student_id']
    )
    if user['id'] == consultation['student_id'] and consultation.get('is_anonymous'):
        sender_label = '匿名用户'
    else:
        sender = execute_query(
            'SELECT real_name FROM users WHERE id = %s',
            (user['id'],), fetch_one=True
        )
        sender_label = sender['real_name'] if sender else user['real_name']

    create_notification(
        receiver_id,
        '收到新咨询消息',
        f'{sender_label} 在咨询会话中给您发送了新消息。',
        'consultation', consultation_id
    )

    # 回复后将自己侧该会话的通知标为已读
    mark_related_notifications_read(user['id'], 'consultation', consultation_id)

    return success({'message_id': message_id}, '消息发送成功')


@consultation_bp.route('/<int:consultation_id>/close', methods=['PUT'])
@login_required()
def close_consultation(consultation_id):
    """结束咨询对话"""
    consultation = execute_query(
        'SELECT * FROM consultations WHERE id = %s',
        (consultation_id,),
        fetch_one=True
    )
    if not consultation:
        return error('会话不存在')

    user = request.current_user
    if user['id'] not in (consultation['student_id'], consultation['counselor_id']) and user['role'] != 'admin':
        return error('无权结束此对话')

    execute_update(
        'UPDATE consultations SET status = "closed" WHERE id = %s',
        (consultation_id,)
    )
    return success(message='对话已结束')
