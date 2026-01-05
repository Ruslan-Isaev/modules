version = (1, 4, 0)

# meta developer: @RUIS_VlP, @RoKrz
# requires: yt_dlp

import yt_dlp
import uuid
import os
import re
import tempfile
from .. import loader, utils


def extract_video_link(text):
    """Извлекает видео с сайтов"""
    if not text:
        return None
    video_sites_patterns = [
        # YouTube
        r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/[^\s]+",

        # Social Media
        r"(https?://)?(www\.)?(tiktok\.com|vt\.tiktok\.com|vm\.tiktok\.com)/[^\s]+",
        r"(https?://)?(www\.)?instagram\.com/(p|reel|tv)/[^\s]+",
        r"(https?://)?(www\.)?(twitter\.com|x\.com)/[^\s]+/status/[^\s]+",
        r"(https?://)?(www\.)?facebook\.com/[^\s]+/videos/[^\s]+",
        r"(https?://)?(www\.)?reddit\.com/r/[^\s]+/comments/[^\s]+",

        # Video Platforms
        r"(https?://)?(www\.)?vimeo\.com/[^\s]+",
        r"(https?://)?(www\.)?dailymotion\.com/video/[^\s]+",
        r"(https?://)?(www\.)?twitch\.tv/(videos/|clip/|[^/]+$)[^\s]*",
        r"(https?://)?(www\.)?streamable\.com/[^\s]+",

        # News & Media
        r"(https?://)?(www\.)?bbc\.co\.uk/iplayer/[^\s]+",
        r"(https?://)?(www\.)?cnn\.com/videos/[^\s]+",
        r"(https?://)?(www\.)?reuters\.com/video/[^\s]+",

        # Educational
        r"(https?://)?(www\.)?coursera\.org/learn/[^\s]+",
        r"(https?://)?(www\.)?udemy\.com/course/[^\s]+",
        r"(https?://)?(www\.)?khanacademy\.org/[^\s]+",

        # Russian platforms
        r"(https?://)?(www\.)?rutube\.ru/video/[^\s]+",
        r"(https?://)?(www\.)?vk\.com/(video|clip)[^\s]+",
        r"(https?://)?(www\.)?ok\.ru/video/[^\s]+",

        # Other popular platforms
        r"(https?://)?(www\.)?pornhub\.com/view_video\.php\?viewkey=[^\s]+",
        r"(https?://)?(www\.)?xvideos\.com/video[^\s]+",
        r"(https?://)?(www\.)?soundcloud\.com/[^\s]+",
        r"(https?://)?(www\.)?bandcamp\.com/track/[^\s]+",
        r"(https?://)?(www\.)?mixcloud\.com/[^\s]+",

        # Live streaming
        r"(https?://)?(www\.)?periscope\.tv/[^\s]+",
        r"(https?://)?(www\.)?ustream\.tv/[^\s]+",

        # International
        r"(https?://)?(www\.)?bilibili\.com/video/[^\s]+",
        r"(https?://)?(www\.)?niconico\.jp/watch/[^\s]+",
        r"(https?://)?(www\.)?youku\.com/v_show/[^\s]+",

        # Generic fallback for other video URLs
        r"https?://[^\s]+\.(mp4|webm|avi|mkv|mov|flv|m4v)",
    ]
    for pattern in video_sites_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    general_url_pattern = r"https?://[^\s]+"
    match = re.search(general_url_pattern, text)
    if match:
        url = match.group(0)
        excluded_domains = [
            'google.com', 'yandex.ru', 'wikipedia.org', 'github.com',
            'stackoverflow.com', 'reddit.com/r/', 'amazon.com'
        ]
        if not any(domain in url.lower() for domain in excluded_domains):
            return url
    return None
async def download_video(url, cookies_text=None, youtube_client="default", custom_user_agent=None):
    output_dir = utils.get_base_dir()
    random_uuid = str(uuid.uuid4())
    os.makedirs(output_dir, exist_ok=True)
    formats_to_try = [
        'best[ext=mp4]',
        'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
        'bestvideo+bestaudio/best',
        'best',
        'best*',
        'bestvideo+bestaudio',
        'best[height<=1080]',
        'best[height<=720]',
        'worst',
        'worst*',
    ]
    cookies_file = None
    if cookies_text and cookies_text.strip():
        cleaned_cookies = cookies_text.strip()
        if cleaned_cookies.startswith('"') or cleaned_cookies.startswith("'"):
            cleaned_cookies = cleaned_cookies[1:]
        if cleaned_cookies.endswith('"') or cleaned_cookies.endswith("'"):
            cleaned_cookies = cleaned_cookies[:-1]

        cookies_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8')
        cookies_file.write(cleaned_cookies)
        cookies_file.close()
    try:
        is_youtube = 'youtube.com' in url.lower() or 'youtu.be' in url.lower()
        for format_option in formats_to_try:
            ydl_opts = {
                'format': format_option,
                'outtmpl': os.path.join(output_dir, f'{random_uuid}.%(ext)s'),
                'noplaylist': True,
                'merge_output_format': 'mp4',
            }
            if cookies_file:
                ydl_opts['cookiefile'] = cookies_file.name
            if custom_user_agent:
                ydl_opts['http_headers'] = {'User-Agent': custom_user_agent}
            if is_youtube and youtube_client != "default":
                ydl_opts['extractor_args'] = {'youtube': {'player_client': [youtube_client]}}
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(url, download=True)
                    video_ext = info_dict.get('ext', None)
                    file_path = os.path.join(output_dir, f"{random_uuid}.{video_ext}")
                    title = info_dict.get('title', None)
                    channel = info_dict.get('uploader', None)
                return file_path, title, channel
            except Exception as e:
                if "Requested format is not available" in str(e) or "No video formats found" in str(e):
                    continue
                else:
                    raise e
        raise Exception("Не удалось скачать видео ни в одном формате")

    finally:
        if cookies_file:
            try:
                os.unlink(cookies_file.name)
            except:
                pass
def convert_markdown_to_html(template: str, link: str) -> str:
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', template).replace("{link}", link)
@loader.tds
class YouTube_DLDMod(loader.Module):
    """Помогает скачивать видео с YouTube, TikTok и др."""
    strings = {
        "name": "YouTube-DLD",
        "no_link": "❌ <b>Пожалуйста, укажите ссылку на видео либо ответьте на сообщение с ней.</b>",
        "default_downloading": "📥 <b>Начинаю загрузку видео.</b>\n\nℹ️ <code>Это может занять до 5 минут, в зависимости от длины и качества видео.</code>",
        "default_error": "❌ <b>Ошибка!</b>\n\n<code>{}</code>",
        "default_response": "🎥 Вот [ваше видео]({link})!\n\n<code>{title}</code>",
        "default_channel": "📺 Канал: <code>{channel}</code>",
        "cookies_error": "🍪 <b>YouTube требует аутентификацию!</b>\n\n❌ Ошибка: <code>Sign in to confirm you're not a bot</code>\n\n<b>Возможные причины:</b>\n▫️ YouTube детектит запросы без аутентификации\n▫️ IP сервера может быть заблокирован YouTube\n▫️ Видео требует подтверждения возраста/входа\n\n<b>Решения (попробуй по порядку):</b>\n\n<b>1️⃣ Смени YouTube клиент:</b>\n• Открой <code>.cfg YouTube-DLD</code>\n• Попробуй разные значения <code>youtube_client</code>:\n  - <code>mweb</code> (мобильная веб-версия, часто работает)\n  - <code>android</code> (Android приложение, сработало на сервере во Франции)\n  - <code>ios</code> (iOS приложение)\n  - <code>tv_embedded</code> (встроенный ТВ плеер)\n\n<b>2️⃣ Добавь куки (для пользователей из проблемных регионов):</b>\n• Открой НОВОЕ приватное окно (в браузере ctrl+shift+N) и залогинься на YouTube\n• Перейди на https://www.youtube.com/robots.txt в ТОЙ же вкладке\n• Cookie-Editor (расширение) → Export → Netscape format\n• СРАЗУ закрой приватное окно\n• Вставь куки в <code>youtube_cookies</code> (БЕЗ кавычек)",
        "supported_sites": """🎥 <b>Поддерживаемые сайты:</b>

🔴 <b>YouTube</b> — youtube.com, youtu.be
🎵 <b>TikTok</b> — tiktok.com, vt.tiktok.com, vm.tiktok.com
📸 <b>Instagram</b> — instagram.com (посты, reels, IGTV)
🐦 <b>X (Twitter)</b> — x.com, twitter.com
👥 <b>Facebook</b> — facebook.com (видео)
🎬 <b>Vimeo</b> — vimeo.com
📺 <b>Twitch</b> — twitch.tv (стримы, клипы, VOD)
🤖 <b>Reddit</b> — reddit.com (видео из постов)
⚡ <b>Dailymotion</b> — dailymotion.com

<b>🇷🇺 Российские:</b>
▫️ <b>RuTube</b> — rutube.ru
▫️ <b>ВКонтакте</b> — vk.com (видео)
▫️ <b>Одноклассники</b> — ok.ru

<b>📚 Образовательные:</b>
▫️ <b>Coursera</b> — coursera.org
▫️ <b>Udemy</b> — udemy.com
▫️ <b>Khan Academy</b> — khanacademy.org

<b>🌍 Международные:</b>
▫️ <b>Bilibili</b> — bilibili.com
▫️ <b>NicoNico</b> — niconico.jp
▫️ <b>BBC iPlayer</b> — bbc.co.uk/iplayer

<b>🎵 Аудио:</b>
▫️ <b>SoundCloud</b> — soundcloud.com
▫️ <b>Bandcamp</b> — bandcamp.com
▫️ <b>Mixcloud</b> — mixcloud.com

<i>И многие другие платформы...</i>"""
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
            loader.ConfigValue(
                "show_channel",
                True,
                "Показывать название канала?",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "channel_text",
                self.strings["default_channel"],
                "Текст для отображения канала. (используй {channel} для имени канала)"
            ),
            loader.ConfigValue(
                "youtube_cookies",
                "",
                "🍪 Куки YouTube в формате Netscape (опционально)\n\n"
                "⚠️ ВНИМАНИЕ: Риск бана аккаунта! Используй тестовый аккаунт.\n\n"
                "Как получить:\n"
                "1. НОВОЕ приватное окно (Ctrl+Shift+N) → залогинься на YouTube\n"
                "2. Перейди на https://www.youtube.com/robots.txt в той же вкладке\n"
                "3. Cookie-Editor (расширение) → Export → Netscape format\n"
                "4. СРАЗУ закрой приватное окно\n"
                "5. Вставь текст сюда (БЕЗ кавычек)",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "youtube_client",
                "mweb",
                "📱 YouTube клиент для обхода блокировок\n\n"
                "Доступные варианты:\n"
                "• default - стандартный (может не работать)\n"
                "• mweb - мобильная веб-версия\n"
                "• android - Android приложение (рекомендуется)\n"
                "• ios - iOS приложение\n"
                "• tv_embedded - встроенный ТВ плеер\n\n"
                "Если видео не скачивается, попробуй другой клиент!",
                validator=loader.validators.Choice(["default", "mweb", "android", "ios", "tv_embedded"]),
            ),
            loader.ConfigValue(
                "custom_user_agent",
                "",
                "🌐 Кастомный User-Agent (опционально)\n\n"
                "Можно указать User-Agent браузера для обхода некоторых блокировок.\n"
                "Например:\n"
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\n\n"
                "Оставь пустым для использования стандартного.",
                validator=loader.validators.String(),
            ),
        )

    @loader.command()
    async def dvlist(self, message):
        """Показать список всех поддерживаемых сайтов"""
        await utils.answer(message, self.strings["supported_sites"])

    @loader.command()
    async def dlvideo(self, message):
        """<ссылка> или ответ на сообщение со ссылкой — скачивает видео с поддерживаемых платформ"""
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()
        link = extract_video_link(args) if args else None
        if not link and reply:
            link = extract_video_link(reply.raw_text)
        if not link:
            await utils.answer(message, self.strings["no_link"])
            return
        await utils.answer(message, self.config["downloading_text"])
        try:
            cookies_text = self.config["youtube_cookies"].strip() if self.config["youtube_cookies"] else None
            youtube_client = self.config["youtube_client"]
            user_agent = self.config["custom_user_agent"].strip() if self.config["custom_user_agent"] else None
            video, title, channel = await download_video(link, cookies_text, youtube_client, user_agent)
            if self.config["show_link"]:
                caption_template = self.config["response_text"]
                caption = convert_markdown_to_html(caption_template, link)
                caption = caption.replace("{title}", title or "")
                if self.config["show_channel"] and channel:
                    channel_text = self.config["channel_text"].replace("{channel}", channel)
                    caption += f"\n\n{channel_text}"
            else:
                caption = title or "Готово!"

            await utils.answer_file(
                message,
                video,
                caption=caption,
                parse_mode="HTML",
                reply_to=reply or message,
                silent=True
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
            error_str = str(e)
            if "Sign in to confirm you're not a bot" in error_str or "Use --cookies" in error_str:
                await utils.answer(message, self.strings["cookies_error"])
            else:
                error_msg = self.config["error_text"].format(e)
                await utils.answer(message, error_msg)
            try:
                if 'video' in locals():
                    os.remove(video)
            except:
                pass
