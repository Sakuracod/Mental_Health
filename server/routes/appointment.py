"""
咨询预约路由模块
处理学生预约咨询师、咨询师确认预约等功能
"""
from flask import Blueprint, request
from utils.db import execute_query, execute_update
from utils.auth import login_required
from utils.response import success, error
from utils.notify import create_notification

appointment_bp = Blueprint('appointment', __name__, url_prefix='/api/appointments')

# 可选时间段
TIME_SLOTS = [
    '09:00-10:00', '10:00-11:00', '11:00-12:00',
    '14:00-15:00', '15:00-16:00', '16:00-17:00'
]

_name_column_ready = None
_detail_bio_ready = None


def _ensure_detail_bio_column():
    global _detail_bio_ready
    if _detail_bio_ready is not None:
        return _detail_bio_ready
    try:
        execute_query('SELECT detail_bio FROM counselor_profiles LIMIT 1', fetch_one=True)
        _detail_bio_ready = True
    except Exception:
        try:
            execute_update(
                'ALTER TABLE counselor_profiles ADD COLUMN detail_bio TEXT DEFAULT NULL COMMENT "详细介绍"'
            )
            _detail_bio_ready = True
        except Exception:
            _detail_bio_ready = False
    return _detail_bio_ready


def _counselor_base_sql():
    return (
        'SELECT u.id, u.real_name, u.phone, u.email, u.avatar, u.gender, '
        'IFNULL(cp.title, "心理咨询师") AS title, '
        'IFNULL(cp.specialty, "暂无") AS specialty, '
        'IFNULL(cp.introduction, "暂无简介") AS introduction, '
        'cp.detail_bio, IFNULL(cp.available_days, "1,2,3,4,5") AS available_days '
        'FROM users u '
        'LEFT JOIN counselor_profiles cp ON u.id = cp.user_id '
        'WHERE u.role = "counselor" AND u.status = 1'
    )


def _ensure_appointment_name_column():
    global _name_column_ready
    if _name_column_ready is not None:
        return _name_column_ready
    try:
        execute_query('SELECT student_real_name FROM appointments LIMIT 1', fetch_one=True)
        _name_column_ready = True
    except Exception:
        try:
            execute_update(
                'ALTER TABLE appointments ADD COLUMN student_real_name VARCHAR(50) DEFAULT NULL '
                'COMMENT "预约时填写的真实姓名" AFTER student_id'
            )
            execute_update(
                'UPDATE appointments a JOIN users u ON a.student_id = u.id '
                'SET a.student_real_name = u.real_name WHERE a.student_real_name IS NULL'
            )
            _name_column_ready = True
        except Exception:
            _name_column_ready = False
    return _name_column_ready


@appointment_bp.route('/counselors', methods=['GET'])
@login_required()
def list_counselors():
    """获取所有可预约的咨询师列表（含档案信息）"""
    _ensure_detail_bio_column()
    counselors = execute_query(_counselor_base_sql() + ' ORDER BY u.id')
    return success(counselors)


@appointment_bp.route('/counselors/<int:counselor_id>', methods=['GET'])
@login_required()
def get_counselor(counselor_id):
    """获取咨询师详细信息"""
    _ensure_detail_bio_column()
    counselor = execute_query(
        _counselor_base_sql() + ' AND u.id = %s',
        (counselor_id,),
        fetch_one=True
    )
    if not counselor:
        return error('咨询师不存在', 404)
    if not counselor.get('detail_bio'):
        counselor['detail_bio'] = counselor.get('introduction', '')
    return success(counselor)


@appointment_bp.route('/time-slots', methods=['GET'])
@login_required()
def get_time_slots():
    """获取可选时间段列表"""
    return success(TIME_SLOTS)


@appointment_bp.route('', methods=['GET'])
@login_required()
def list_appointments():
    """
    获取预约列表
    学生查看自己的预约，咨询师查看分配给自己的预约
    """
    _ensure_appointment_name_column()
    user = request.current_user
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    offset = (page - 1) * page_size

    if user['role'] == 'student':
        where = 'WHERE a.student_id = %s'
        params = [user['id']]
    elif user['role'] == 'counselor':
        where = 'WHERE a.counselor_id = %s'
        params = [user['id']]
    else:
        where = 'WHERE 1=1'
        params = []

    total = execute_query(
        f'SELECT COUNT(*) as count FROM appointments a {where}',
        tuple(params) if params else None,
        fetch_one=True
    )['count']

    params.extend([page_size, offset])
    items = execute_query(
        f'SELECT a.*, IFNULL(a.student_real_name, s.real_name) as student_name, c.real_name as counselor_name '
        f'FROM appointments a '
        f'LEFT JOIN users s ON a.student_id = s.id '
        f'LEFT JOIN users c ON a.counselor_id = c.id '
        f'{where} ORDER BY a.appointment_date DESC, a.time_slot ASC '
        f'LIMIT %s OFFSET %s',
        tuple(params)
    )

    return success({
        'list': items,
        'total': total,
        'page': page,
        'page_size': page_size
    })


@appointment_bp.route('', methods=['POST'])
@login_required(roles=['student'])
def create_appointment():
    """
    学生创建预约
    请求体: { counselor_id, appointment_date, time_slot, reason, student_real_name }
    """
    _ensure_appointment_name_column()
    data = request.get_json()
    counselor_id = data.get('counselor_id')
    appointment_date = data.get('appointment_date')
    time_slot = data.get('time_slot')
    reason = data.get('reason', '')
    student_real_name = (data.get('student_real_name') or '').strip()

    if not all([counselor_id, appointment_date, time_slot]):
        return error('请填写完整的预约信息')
    if not student_real_name:
        return error('请填写真实姓名')

    if time_slot not in TIME_SLOTS:
        return error('无效的时间段')

    # 检查时间段是否已被预约
    conflict = execute_query(
        'SELECT id FROM appointments '
        'WHERE counselor_id = %s AND appointment_date = %s AND time_slot = %s '
        'AND status IN ("pending", "confirmed")',
        (counselor_id, appointment_date, time_slot),
        fetch_one=True
    )
    if conflict:
        return error('该时间段已被预约，请选择其他时间')

    appointment_id = execute_update(
        'INSERT INTO appointments (student_id, student_real_name, counselor_id, appointment_date, time_slot, reason) '
        'VALUES (%s, %s, %s, %s, %s, %s)',
        (request.current_user['id'], student_real_name, counselor_id, appointment_date, time_slot, reason)
    )

    # 通知咨询师有新预约
    create_notification(
        counselor_id,
        '新的咨询预约',
        f'学生 {student_real_name} 提交了预约申请（{appointment_date} {time_slot}），请及时确认。',
        'appointment', appointment_id
    )

    return success({'appointment_id': appointment_id}, '预约提交成功，等待咨询师确认')


@appointment_bp.route('/<int:appointment_id>/status', methods=['PUT'])
@login_required(roles=['counselor', 'admin'])
def update_appointment_status(appointment_id):
    """
    更新预约状态（确认/完成/取消）
    请求体: { status, remark }
    """
    data = request.get_json()
    status = data.get('status')
    remark = data.get('remark', '')

    valid_statuses = ['pending', 'confirmed', 'completed', 'cancelled']
    if status not in valid_statuses:
        return error('无效的状态值')

    appointment = execute_query(
        'SELECT * FROM appointments WHERE id = %s',
        (appointment_id,),
        fetch_one=True
    )
    if not appointment:
        return error('预约不存在')

    if request.current_user['role'] == 'counselor' and appointment['counselor_id'] != request.current_user['id']:
        return error('无权操作此预约')

    execute_update(
        'UPDATE appointments SET status = %s, remark = %s WHERE id = %s',
        (status, remark, appointment_id)
    )

    status_map = {
        'confirmed': '已确认', 'completed': '已完成',
        'cancelled': '已取消', 'pending': '待确认'
    }
    create_notification(
        appointment['student_id'],
        '预约状态更新',
        f'您的咨询预约（{appointment["appointment_date"]} {appointment["time_slot"]}）状态已更新为：{status_map.get(status, status)}。',
        'appointment', appointment_id
    )
    return success(message='预约状态更新成功')


@appointment_bp.route('/<int:appointment_id>', methods=['DELETE'])
@login_required()
def cancel_appointment(appointment_id):
    """取消预约（学生或咨询师均可操作）"""
    appointment = execute_query(
        'SELECT * FROM appointments WHERE id = %s',
        (appointment_id,),
        fetch_one=True
    )
    if not appointment:
        return error('预约不存在')

    user = request.current_user
    if user['role'] == 'student' and appointment['student_id'] != user['id']:
        return error('无权取消此预约')
    if user['role'] == 'counselor' and appointment['counselor_id'] != user['id']:
        return error('无权取消此预约')

    if appointment['status'] in ('completed', 'cancelled'):
        return error('该预约无法取消')

    execute_update(
        'UPDATE appointments SET status = "cancelled" WHERE id = %s',
        (appointment_id,)
    )
    return success(message='预约已取消')
