version = (1, 0, 0)

# meta developer: @RUIS_VlP
# requires: yt_dlp

import yt_dlp
import uuid
import os
from .. import loader, utils

async def download_video(url):
    output_dir = utils.get_base_dir()
    random_uuid = str(uuid.uuid4())
    os.makedirs(output_dir, exist_ok=True)
    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join(output_dir, f'{random_uuid}.%(ext)s'),
        'noplaylist': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        video_ext = info_dict.get('ext', None) #расширение файла
        
        file_path = os.path.join(output_dir, f"{random_uuid}.{video_ext}")
        
        title = info_dict.get('title', None) 
        
    return file_path, title
    
    
@loader.tds
class YouTube_DLDMod(loader.Module):
    """Помогает скачивать видео с YouTube"""

    strings = {
        "name": "YouTube-DLD",
    }
    
    @loader.command()
    async def dlvideo(self, message):
        """<link> - скачивает видео с ютуба"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, "❌ <b>Вы не указали ссылку</b>")
            return
        link = args
        await utils.answer(message, "📥 <b>Начинаю загрузку видео.</b>\n\nℹ️ <code>Обычно приходится ждать ≈5 минут. Все зависит от длины и качества видео. А так же от вашего интернета.</code>")
        try:
            video, title = await download_video(link)
            print(video)
            if title:
                await utils.answer_file(message, video, caption=f"🎥 Вот ваше видео!\n\n<code>{title}</code>")
            else:
                await utils.answer_file(message, video, caption=f"🎥 Вот ваше видео!")
            try:
                await message.delete()
            except:
                pass
            try:
                os.remove(video)
            except:
                pass
        except Exception as e:
            await utils.answer(message, f"❌ <b>Ошибка!</b>\n\n<code>{e}</code>")
            try:
                os.remove(video)
            except:
                pass
            return
