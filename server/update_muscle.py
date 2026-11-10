"""更新渐进式肌肉放松视频路径"""
from utils.db import execute_update

execute_update(
    "UPDATE relaxation_audios SET media_type=%s, audio_url=%s, description=%s WHERE title=%s",
    (
        'video',
        '/static/media/relaxation/muscle.mp4',
        '跟随视频依次收紧再放松全身肌肉群，释放躯体紧张感。',
        '渐进式肌肉放松',
    )
)
print('数据库已更新：渐进式肌肉放松 -> muscle.mp4')
