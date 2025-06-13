__version__ = (1, 1, 0)

# meta developer: @RUIS_VlP, @RoKrz
# requires: yt_dlp

import yt_dlp
import uuid
import os
import re
from .. import loader, utils


def extract_youtube_link(text):
    if not text:
        return None
    match = re.search(r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/[^\s]+", text)
    return match.group(0) if match else None


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
        video_ext = info_dict.get('ext', None)
        file_path = os.path.join(output_dir, f"{random_uuid}.{video_ext}")
        title = info_dict.get('title', None)

    return file_path, title


def convert_markdown_to_html(template: str, link: str) -> str:
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', template).replace("{link}", link)


@loader.tds
class YouTube_DLDMod(loader.Module):
    """Помогает скачивать видео с YouTube"""

    strings = {
        "name": "YouTube-DLD",
        "no_link": "❌ <b>Пожалуйста, укажите ссылку на YouTube либо ответьте на сообщение с ней.</b>",
        "default_downloading": "📥 <b>Начинаю загрузку видео.</b>\n\nℹ️ <code>Это может занять до 5 минут, в зависимости от длины и качества видео.</code>",
        "default_error": "❌ <b>Ошибка!</b>\n\n<code>{}</code>",
        "default_response": "🎥 Вот [ваше видео]({link})!\n\n<code>{title}</code>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "show_link",
                True,
                "Показывать ссылку в сообщении?",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "downloading_text",
                self.strings["default_downloading"],
                "Текст во время загрузки"
            ),
            loader.ConfigValue(
                "error_text",
                self.strings["default_error"],
                "Текст ошибки. (используй {} для ошибки)"
            ),
            loader.ConfigValue(
                "response_text",
                self.strings["default_response"],
                "Ответ после загрузки. (используй {link} для ссылки и {title} для названия видео)"
            ),
        )

    @loader.command()
    async def dlvideo(self, message):
        """<ссылка> или ответ на сообщение со ссылкой — скачивает видео с YouTube"""

        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()

        link = extract_youtube_link(args) if args else None
        if not link and reply:
            link = extract_youtube_link(reply.raw_text)

        if not link:
            await utils.answer(message, self.strings["no_link"])
            return

        await utils.answer(message, self.config["downloading_text"])

        try:
            video, title = await download_video(link)

            if self.config["show_link"]:
                caption_template = self.config["response_text"]
                caption = convert_markdown_to_html(caption_template, link)
                caption = caption.replace("{title}", title or "")
            else:
                caption = title or "Готово!"

            await utils.answer_file(
                message,
                video,
                caption=caption,
                parse_mode="HTML"
            )

            try:
                await message.delete()
            except:
                pass
            try:
                os.remove(video)
            except:
                pass
        except Exception as e:
            error_msg = self.config["error_text"].format(e)
            await utils.answer(message, error_msg)
            try:
                os.remove(video)
            except:
                pass
