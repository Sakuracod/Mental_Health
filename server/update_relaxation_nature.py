"""
一次性脚本：更新自然音分类音频路径
运行: cd server && python update_relaxation_nature.py
"""
from utils.db import execute_query, execute_update


def main():
    # 删除指向不存在 rain.mp3 的旧记录
    execute_update(
        "DELETE FROM relaxation_audios WHERE audio_url LIKE '%%rain.mp3%%'"
    )

    tracks = [
        (
            '自然白噪音 · 再次相遇在夏天',
            '治愈纯音乐，轻柔旋律如夏日微风，帮助舒缓情绪、放松身心。',
            '自然音',
            'audio',
            '/static/media/relaxation/nature_summer.mp3',
            '6:30',
            '🌿',
        ),
        (
            '自然白噪音 · 溪畔谧语',
            '溪水潺潺、鸟鸣悠扬的自然疗愈音，适合冥想、阅读与助眠。',
            '自然音',
            'audio',
            '/static/media/relaxation/nature_stream.mp3',
            '6:45',
            '🌧️',
        ),
    ]

    for title, desc, category, media_type, url, duration, icon in tracks:
        exists = execute_query(
            'SELECT id FROM relaxation_audios WHERE audio_url = %s',
            (url,), fetch_one=True
        )
        if exists:
            execute_update(
                'UPDATE relaxation_audios SET title=%s, description=%s, category=%s, '
                'media_type=%s, duration=%s, cover_icon=%s, status=1 WHERE audio_url=%s',
                (title, desc, category, media_type, duration, icon, url)
            )
            print(f'[更新] {title}')
        else:
            execute_update(
                'INSERT INTO relaxation_audios (title, description, category, media_type, audio_url, duration, cover_icon) '
                'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                (title, desc, category, media_type, url, duration, icon)
            )
            print(f'[新增] {title}')

    # 同步其他已有本地文件
    sync_map = [
        ('/static/media/relaxation/breathing.mp4', '深度呼吸练习', 'video'),
        ('/static/media/relaxation/piano.mp3', '舒缓钢琴曲', 'audio'),
    ]
    for url, title, media_type in sync_map:
        execute_update(
            'UPDATE relaxation_audios SET audio_url=%s, media_type=%s WHERE title=%s',
            (url, media_type, title)
        )

    items = execute_query(
        'SELECT id, title, audio_url FROM relaxation_audios WHERE status=1 ORDER BY id'
    )
    print('\n当前放松训练列表:')
    for item in items:
        print(f"  [{item['id']}] {item['title']} -> {item['audio_url']}")


if __name__ == '__main__':
    main()
