"""更新正念身体扫描视频路径"""
from utils.db import execute_update

execute_update(
    "UPDATE relaxation_audios SET media_type=%s, audio_url=%s, duration=%s, description=%s WHERE title=%s",
    (
        'video',
        '/static/media/relaxation/body_scan.m4v',
        '15:00',
        '15分钟身体扫描冥想引导，从头顶到脚尖依次放松，适合睡前或焦虑时使用。',
        '正念身体扫描',
    )
)
print('数据库已更新：正念身体扫描 -> body_scan.m4v')
