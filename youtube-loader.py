version = (2, 3, 0)

# meta developer: @RUIS_VlP, @RoKrz
# requires: yt_dlp aiohttp aiofiles

import yt_dlp
import uuid
import os
import re
import random
import asyncio
import shutil
import tempfile
import zipfile
import platform
import urllib.parse
import aiohttp
import aiofiles
from pathlib import Path
from .. import loader, utils
import logging

logger = logging.getLogger(__name__)


def extract_video_link(text):
    if not text:
        return None

    video_sites_patterns = [
        r"(https?://)?(www\.)?(youtube\.com|youtu\.be|music\.youtube\.com)/[^\s]+",
        r"(https?://)?(www\.)?(tiktok\.com|vt\.tiktok\.com|vm\.tiktok\.com)/[^\s]+",
        r"(https?://)?(www\.)?instagram\.com/(p|reel|tv)/[^\s]+",
        r"(https?://)?(www\.)?(twitter\.com|x\.com)/[^\s]+/status/[^\s]+",
        r"(https?://)?(www\.)?facebook\.com/[^\s]+/videos/[^\s]+",
        r"(https?://)?(www\.)?reddit\.com/r/[^\s]+/comments/[^\s]+",
        r"(https?://)?(www\.)?vimeo\.com/[^\s]+",
        r"(https?://)?(www\.)?dailymotion\.com/video/[^\s]+",
        r"(https?://)?(www\.)?twitch\.tv/(videos/|clip/|[^/]+$)[^\s]*",
        r"(https?://)?(www\.)?streamable\.com/[^\s]+",
        r"(https?://)?(music\.)?yandex\.(ru|com|by|kz|ua)/album/[^\s]+",
        r"(https?://)?(www\.)?soundcloud\.com/[^\s]+",
        r"(https?://)?(www\.)?bandcamp\.com/[^\s]+",
        r"(https?://)?(www\.)?mixcloud\.com/[^\s]+",
        r"(https?://)?(www\.)?spotify\.com/(track|album|playlist)/[^\s]+",
        r"(https?://)?(www\.)?rutube\.ru/video/[^\s]+",
        r"(https?://)?(www\.)?vk\.com/(video|clip)[^\s]+",
        r"(https?://)?(www\.)?ok\.ru/video/[^\s]+",
        r"https?://[^\s]+\.(mp4|webm|avi|mkv|mov|flv|m4v|mp3|m4a|wav|flac)",
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


def get_random_user_agent():
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.3; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1",
    ]
    return random.choice(agents)


async def check_proxy_health(proxy, timeout_seconds=5):
    try:
        parsed = urllib.parse.urlsplit(proxy)
        if not parsed.hostname or not parsed.port:
            return False

        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(parsed.hostname, parsed.port),
            timeout=timeout_seconds
        )
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        return True
    except Exception:
        return False


SPONSORBLOCK_CATEGORY_IDS = ["sponsor", "interaction", "selfpromo", "intro", "outro", "preview", "hook", "filler"]

DEFAULT_SB_CATEGORIES = ["sponsor", "interaction"]


async def download_media(
    url,
    cookies_text=None,
    proxy=None,
    deno_path=None,
    max_attempts=50,
    audio_only=False,
    sponsorblock_categories=None,
    on_attempt=None,
):
    output_dir = utils.get_base_dir()
    random_uuid = str(uuid.uuid4())
    os.makedirs(output_dir, exist_ok=True)

    is_youtube = 'youtube.com' in url.lower() or 'youtu.be' in url.lower() or 'music.youtube.com' in url.lower()

    clients_to_try = ['android', 'ios', 'mweb', 'tv_embedded'] if is_youtube else [None]

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

    methods = []
    if proxy:
        if await check_proxy_health(proxy):
            methods.append(("proxy", proxy, None))
    if cookies_file:
        methods.append(("cookies", None, cookies_file.name))
    methods.append(("direct", None, None))

    attempt = 0
    last_error = None

    try:
        while attempt < max_attempts:
            for method_name, method_proxy, method_cookiefile in methods:
                for client in clients_to_try:
                    if attempt >= max_attempts:
                        break
                    attempt += 1

                    if on_attempt:
                        await on_attempt(attempt, method_name)

                    user_agent = get_random_user_agent()

                    if audio_only:
                        ydl_opts = {
                            'format': 'bestaudio/best',
                            'outtmpl': os.path.join(output_dir, f'{random_uuid}.%(ext)s'),
                            'noplaylist': True,
                            'quiet': True,
                            'no_warnings': True,
                            'http_headers': {'User-Agent': user_agent},
                            'postprocessors': [
                                {
                                    'key': 'FFmpegExtractAudio',
                                    'preferredcodec': 'mp3',
                                    'preferredquality': '320',
                                },
                                {
                                    'key': 'FFmpegMetadata',
                                    'add_metadata': True,
                                },
                                {
                                    'key': 'EmbedThumbnail',
                                },
                            ],
                            'writethumbnail': True,
                        }
                    else:
                        ydl_opts = {
                            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                            'outtmpl': os.path.join(output_dir, f'{random_uuid}.%(ext)s'),
                            'noplaylist': True,
                            'merge_output_format': 'mp4',
                            'quiet': True,
                            'no_warnings': True,
                            'http_headers': {'User-Agent': user_agent},
                            'postprocessors': [],
                        }

                    if sponsorblock_categories:
                        ydl_opts['postprocessors'].append({
                            'key': 'SponsorBlock',
                            'categories': sponsorblock_categories,
                            'when': 'after_filter',
                        })
                        ydl_opts['postprocessors'].append({
                            'key': 'ModifyChapters',
                            'remove_sponsor_segments': sponsorblock_categories,
                        })

                    ydl_opts['extractor_retries'] = 5
                    ydl_opts['fragment_retries'] = 15
                    ydl_opts['retries'] = 15

                    if method_proxy:
                        ydl_opts['proxy'] = method_proxy

                    if method_cookiefile:
                        ydl_opts['cookiefile'] = method_cookiefile

                    if deno_path and os.path.exists(deno_path):
                        ydl_opts['js_runtimes'] = {'deno': {'path': deno_path}}

                    if is_youtube and client:
                        ydl_opts['extractor_args'] = {'youtube': {'player_client': [client]}}

                    try:
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            info_dict = ydl.extract_info(url, download=True)

                            if audio_only:
                                file_path = os.path.join(output_dir, f"{random_uuid}.mp3")
                            else:
                                video_ext = info_dict.get('ext', 'mp4')
                                file_path = os.path.join(output_dir, f"{random_uuid}.{video_ext}")

                            title = info_dict.get('title', 'Media')
                            channel = info_dict.get('uploader', None)

                        return file_path, title, channel

                    except Exception as e:
                        error_str = str(e)
                        last_error = e

                        if "This video is unavailable" in error_str or "Private video" in error_str:
                            raise Exception("Видео недоступно (приватное, удалено или только для подписчиков)")

                        await asyncio.sleep(2)
                        continue

                if attempt >= max_attempts:
                    break

        if last_error:
            raise last_error
        raise Exception(f"Не удалось скачать после {attempt} попыток")

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
    """Помогает скачивать видео с YouTube, TikTok и др. Поддерживает SponsorBlock — вырезает рекламные и другие ненужные вставки прямо из видео при скачивании."""

    strings = {
        "name": "YouTube-DLD",
        "no_link": "❌ <b>Пожалуйста, укажите ссылку на видео либо ответьте на сообщение с ней.</b>",
        "default_downloading": "📥 <b>Начинаю загрузку...</b>\n\n<i>Попытка {attempt} ({method})</i>",
        "default_error": "❌ <b>Ошибка после {attempts} попыток!</b>\n\n<code>{error}</code>",
        "default_response": "🎥 Вот [ваше видео]({link})!\n\n<code>{title}</code>",
        "default_music_response": "🎵 <b>Аудио готово!</b>\n\n<code>{title}</code>",
        "default_channel": "📺 Канал: <code>{channel}</code>",
        "downloading_audio": "🎵 <b>Скачиваю аудио...</b>",
        "done_fallback": "Готово!",
        "method_proxy": "прокси",
        "method_cookies": "куки",
        "method_direct": "напрямую",
        "supported_sites": """🎥 <b>Поддерживаемые сайты:</b>

🔴 <b>YouTube</b> — youtube.com, youtu.be, music.youtube.com
🎵 <b>TikTok</b> — tiktok.com, vt.tiktok.com, vm.tiktok.com
📸 <b>Instagram</b> — instagram.com
🐦 <b>X (Twitter)</b> — x.com, twitter.com
👥 <b>Facebook</b> — facebook.com
🎬 <b>Vimeo</b> — vimeo.com
📺 <b>Twitch</b> — twitch.tv
🤖 <b>Reddit</b> — reddit.com

<b>🎵 Музыка:</b>
▫️ <b>Яндекс.Музыка</b> — music.yandex.ru
▫️ <b>SoundCloud</b> — soundcloud.com
▫️ <b>Bandcamp</b> — bandcamp.com
▫️ <b>Spotify</b> — spotify.com

<b>🇷🇺 Российские:</b>
▫️ <b>RuTube</b> — rutube.ru
▫️ <b>ВКонтакте</b> — vk.com
▫️ <b>Одноклассники</b> — ok.ru

<b>📝 Команды:</b>
▫️ .dlvideo <ссылка> — скачать видео
▫️ .dlvideo -a <ссылка> — скачать аудио
▫️ .dvlist — список сайтов
▫️ .sblock — настройки SponsorBlock (инлайн-меню)""",
        "sb_state_on": "включён ✅",
        "sb_state_off": "выключен 🚫",
        "sb_main_text": "✂️ <b>SponsorBlock</b> — {state}\n\n✅ — вырежется при скачивании, ❌ — останется в видео.\nУ пункта с ⚙️ есть отдельные настройки.",
        "sb_master_label": "✂️ SponsorBlock — {state}",
        "sb_close": "❌ Закрыть",
        "sb_cut_answer": "✅ Буду вырезать",
        "sb_keep_answer": "❌ Оставляю в видео",
        "sb_on_answer": "✅ Включено",
        "sb_off_answer": "🚫 Выключено",
        "sb_music_label": "🎵 Немузыкальный момент",
        "sb_music_text": "{label}\n\nМомент внутри музыкального ролика, где самой музыки нет — например, устная подводка перед клипом.\n\nСейчас: <b>{state}</b>\n\nТолько на music.youtube.com: <b>{music_only}</b>\n<i>Если включено — вырезается только когда ссылка с music.youtube.com, на обычном youtube.com сегмент не трогается.</i>",
        "sb_state_cut": "вырезается",
        "sb_state_keep": "остаётся в видео",
        "sb_yes": "да",
        "sb_no": "нет",
        "sb_cut_btn": "Вырезать",
        "sb_keep_btn": "Оставить",
        "sb_music_only_btn": "Только на music.youtube.com",
        "sb_back": "◀️ Назад",
        "sb_saved": "Сохранено",
        "cat_sponsor": "📢 Спонсор",
        "cat_interaction": "🔔 Подписка",
        "cat_selfpromo": "🎗 Самореклама",
        "cat_intro": "⏯ Интро/пауза",
        "cat_outro": "🎬 Титры",
        "cat_preview": "⏪ Промо/повтор",
        "cat_hook": "👋 Вступление",
        "cat_filler": "💬 Отступления",
    }

    strings_en = {
        "no_link": "❌ <b>Please provide a video link, or reply to a message that has one.</b>",
        "default_downloading": "📥 <b>Starting download...</b>\n\n<i>Attempt {attempt} ({method})</i>",
        "default_error": "❌ <b>Failed after {attempts} attempts!</b>\n\n<code>{error}</code>",
        "default_response": "🎥 Here's [your video]({link})!\n\n<code>{title}</code>",
        "default_music_response": "🎵 <b>Audio ready!</b>\n\n<code>{title}</code>",
        "default_channel": "📺 Channel: <code>{channel}</code>",
        "downloading_audio": "🎵 <b>Downloading audio...</b>",
        "done_fallback": "Done!",
        "method_proxy": "proxy",
        "method_cookies": "cookies",
        "method_direct": "direct",
        "supported_sites": """🎥 <b>Supported sites:</b>

🔴 <b>YouTube</b> — youtube.com, youtu.be, music.youtube.com
🎵 <b>TikTok</b> — tiktok.com, vt.tiktok.com, vm.tiktok.com
📸 <b>Instagram</b> — instagram.com
🐦 <b>X (Twitter)</b> — x.com, twitter.com
👥 <b>Facebook</b> — facebook.com
🎬 <b>Vimeo</b> — vimeo.com
📺 <b>Twitch</b> — twitch.tv
🤖 <b>Reddit</b> — reddit.com

<b>🎵 Music:</b>
▫️ <b>Yandex Music</b> — music.yandex.ru
▫️ <b>SoundCloud</b> — soundcloud.com
▫️ <b>Bandcamp</b> — bandcamp.com
▫️ <b>Spotify</b> — spotify.com

<b>🇷🇺 Russian:</b>
▫️ <b>RuTube</b> — rutube.ru
▫️ <b>VK</b> — vk.com
▫️ <b>Odnoklassniki</b> — ok.ru

<b>📝 Commands:</b>
▫️ .dlvideo <link> — download video
▫️ .dlvideo -a <link> — download audio
▫️ .dvlist — list of supported sites
▫️ .sblock — SponsorBlock settings (inline menu)""",
        "sb_state_on": "enabled ✅",
        "sb_state_off": "disabled 🚫",
        "sb_main_text": "✂️ <b>SponsorBlock</b> — {state}\n\n✅ — will be cut on download, ❌ — stays in the video.\nThe item with ⚙️ has its own extra settings.",
        "sb_master_label": "✂️ SponsorBlock — {state}",
        "sb_close": "❌ Close",
        "sb_cut_answer": "✅ Will cut",
        "sb_keep_answer": "❌ Leaving it in",
        "sb_on_answer": "✅ Enabled",
        "sb_off_answer": "🚫 Disabled",
        "sb_music_label": "🎵 Non-music moment",
        "sb_music_text": "{label}\n\nA moment inside a music video where there's no actual music — e.g. a spoken intro before the song.\n\nRight now: <b>{state}</b>\n\nOnly on music.youtube.com: <b>{music_only}</b>\n<i>If enabled, it's only cut when the link is from music.youtube.com — on regular youtube.com the segment is left alone.</i>",
        "sb_state_cut": "will be cut",
        "sb_state_keep": "stays in the video",
        "sb_yes": "yes",
        "sb_no": "no",
        "sb_cut_btn": "Cut",
        "sb_keep_btn": "Keep",
        "sb_music_only_btn": "Only on music.youtube.com",
        "sb_back": "◀️ Back",
        "sb_saved": "Saved",
        "cat_sponsor": "📢 Sponsor",
        "cat_interaction": "🔔 Subscribe reminder",
        "cat_selfpromo": "🎗 Self-promo",
        "cat_intro": "⏯ Intro/intermission",
        "cat_outro": "🎬 Outro/credits",
        "cat_preview": "⏪ Preview/recap",
        "cat_hook": "👋 Intro hook",
        "cat_filler": "💬 Filler tangent",
    }

    async def get_deno_target(self):
        system = platform.system()
        machine = platform.machine().lower()

        if system == "Windows":
            return None
        if system == "Darwin":
            return "aarch64-apple-darwin" if machine == "arm64" else "x86_64-apple-darwin"
        if system == "Linux":
            return "aarch64-unknown-linux-gnu" if machine in ("aarch64", "arm64") else "x86_64-unknown-linux-gnu"
        return "x86_64-unknown-linux-gnu"

    async def client_ready(self, client, db):
        deno_path = Path("deno")
        deno_which = shutil.which("deno")

        if self.get("deno_source") == "file":
            self.set("deno_source", str(deno_path.resolve()))
            
        if not deno_which and not deno_path.is_file():
            logger.info("Deno не установлен, начинаю установку...")
            target = await self.get_deno_target()
            
            if not target:
                logger.warning("Windows не поддерживается для автоустановки Deno")
                self.set("deno_source", "install_failed")
                return
            
            try:
                async with aiohttp.ClientSession() as session:
                    download_link = f"https://github.com/denoland/deno/releases/latest/download/deno-{target}.zip"
                    async with session.get(download_link) as resp:
                        if resp.status == 200:
                            async with aiofiles.open("deno.zip", mode="wb") as f:
                                async for chunk in resp.content.iter_chunked(8192):
                                    await f.write(chunk)
                            logger.info("Deno успешно скачан")
                        else:
                            logger.error(f"Не удалось скачать Deno: HTTP {resp.status}")
                            self.set("deno_source", "install_failed")
                            return
                
                if Path("deno.zip").is_file():
                    with zipfile.ZipFile("deno.zip", "r") as zip_ref:
                        zip_ref.extractall()
                    os.remove("deno.zip")
                    os.chmod(deno_path, 0o755)
                    self.set("deno_source", str(deno_path.resolve()))
                    logger.info(f"Deno установлен: {deno_path.resolve()}")
            except Exception as e:
                logger.error(f"Ошибка установки Deno: {e}")
                self.set("deno_source", "install_failed")
        elif deno_which:
            self.set("deno_source", deno_which)
            logger.info(f"Deno найден в системе: {deno_which}")

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
                "Текст во время загрузки.\n\n"
                "Доступные плейсхолдеры (писать ровно так, с фигурными скобками):\n"
                "{attempt} — номер попытки\n"
                "{method} — через что пробуем сейчас: прокси / куки / напрямую\n\n"
                "Пустые {} код не понимает и оставит как есть.",
            ),
            loader.ConfigValue(
                "error_text",
                self.strings["default_error"],
                "Текст ошибки.\n\n"
                "Доступные плейсхолдеры (писать ровно так, с фигурными скобками):\n"
                "{attempts} — сколько всего попыток было сделано\n"
                "{error} — текст самой ошибки\n\n"
                "Пустые {} код не понимает и оставит как есть — нужны именно эти два слова внутри скобок.",
            ),
            loader.ConfigValue(
                "response_text",
                self.strings["default_response"],
                "Ответ после загрузки видео"
            ),
            loader.ConfigValue(
                "music_response_text",
                self.strings["default_music_response"],
                "Ответ после загрузки музыки"
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
                "Текст для отображения канала"
            ),
            loader.ConfigValue(
                "youtube_cookies",
                "",
                "🍪 Куки YouTube в формате Netscape (ТЕКСТОМ!)\n\n"
                "⚠️ ВАЖНО: Если твой Heroku сервер во Франции/UK - экспортируй куки через VPN той же страны!\n\n"
                "Как получить:\n"
                "1. Подключись к VPN страны где твой сервер (узнай регион Heroku)\n"
                "2. Приватное окно → залогинься на YouTube\n"
                "3. Перейди на youtube.com/robots.txt\n"
                "4. Cookie-Editor → Export → Netscape\n"
                "5. СРАЗУ закрой окно\n"
                "6. Вставь ВЕСЬ текст сюда (БЕЗ кавычек)\n\n"
                "Начинается с: # Netscape HTTP Cookie File",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "proxy",
                "",
                "🌐 Прокси (опционально)\n\n"
                "Форматы:\n"
                "• HTTP: http://user:pass@host:port\n"
                "• SOCKS5: socks5://host:port\n\n"
                "⚠️ Trojan/VLESS не поддерживаются!",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "max_attempts",
                50,
                "Максимум попыток (1-100)",
                validator=loader.validators.Integer(minimum=1, maximum=100),
            ),
        )

    @loader.command()
    async def dvlist(self, message):
        """Список поддерживаемых сайтов и команд модуля"""
        await utils.answer(message, self.strings["supported_sites"])

    @loader.command()
    async def sblock(self, message):
        """Настройки SponsorBlock — что вырезать из видео при скачивании"""
        await self.inline.form(
            text=self._sb_main_text(),
            message=message,
            reply_markup=self._sb_main_markup(),
        )

    def _sb_main_text(self):
        enabled = self.get("sb_enabled", True)
        state = self.strings("sb_state_on") if enabled else self.strings("sb_state_off")
        return self.strings("sb_main_text").format(state=state)

    def _sb_main_markup(self):
        enabled = self.get("sb_enabled", True)
        active = self.get("sb_categories", DEFAULT_SB_CATEGORIES)

        state = self.strings("sb_state_on") if enabled else self.strings("sb_state_off")
        master_label = self.strings("sb_master_label").format(state=state)
        rows = [[{"text": master_label, "callback": self._sb_toggle_master}]]

        cat_buttons = []
        for cat_id in SPONSORBLOCK_CATEGORY_IDS:
            label = self.strings(f"cat_{cat_id}")
            state_icon = "✅" if cat_id in active else "❌"
            cat_buttons.append({
                "text": f"{label} {state_icon}",
                "callback": self._sb_toggle_category,
                "args": (cat_id,),
            })
        for i in range(0, len(cat_buttons), 2):
            rows.append(cat_buttons[i:i + 2])

        music_icon = "✅" if "music_offtopic" in active else "❌"
        rows.append([{
            "text": f"{self.strings('sb_music_label')} {music_icon} ⚙️",
            "callback": self._sb_open_music_detail,
        }])

        rows.append([{"text": self.strings("sb_close"), "action": "close"}])

        return rows

    async def _sb_toggle_master(self, call):
        enabled = self.get("sb_enabled", True)
        self.set("sb_enabled", not enabled)
        await call.answer(self.strings("sb_off_answer") if enabled else self.strings("sb_on_answer"))
        await call.edit(self._sb_main_text(), reply_markup=self._sb_main_markup())

    async def _sb_toggle_category(self, call, cat_id):
        active = list(self.get("sb_categories", DEFAULT_SB_CATEGORIES))

        if cat_id in active:
            active.remove(cat_id)
            await call.answer(self.strings("sb_keep_answer"))
        else:
            active.append(cat_id)
            await call.answer(self.strings("sb_cut_answer"))

        self.set("sb_categories", active)
        await call.edit(self._sb_main_text(), reply_markup=self._sb_main_markup())

    def _sb_music_text(self):
        active = self.get("sb_categories", DEFAULT_SB_CATEGORIES)
        only_music = self.get("sb_music_only", True)
        state = self.strings("sb_state_cut") if "music_offtopic" in active else self.strings("sb_state_keep")
        music_only_text = self.strings("sb_yes") if only_music else self.strings("sb_no")
        return self.strings("sb_music_text").format(
            label=self.strings("sb_music_label"),
            state=state,
            music_only=music_only_text,
        )

    def _sb_music_markup(self):
        active = self.get("sb_categories", DEFAULT_SB_CATEGORIES)
        is_on = "music_offtopic" in active
        only_music = self.get("sb_music_only", True)

        return [
            [
                {"text": f"{'✅' if is_on else '▫️'} {self.strings('sb_cut_btn')}", "callback": self._sb_set_music, "args": (True,)},
                {"text": f"{'✅' if not is_on else '▫️'} {self.strings('sb_keep_btn')}", "callback": self._sb_set_music, "args": (False,)},
            ],
            [{
                "text": f"{'✅' if only_music else '▫️'} {self.strings('sb_music_only_btn')}",
                "callback": self._sb_toggle_music_only,
            }],
            [{"text": self.strings("sb_back"), "callback": self._sb_back}],
        ]

    async def _sb_open_music_detail(self, call):
        await call.edit(self._sb_music_text(), reply_markup=self._sb_music_markup())

    async def _sb_set_music(self, call, cut):
        active = list(self.get("sb_categories", DEFAULT_SB_CATEGORIES))

        if cut and "music_offtopic" not in active:
            active.append("music_offtopic")
        elif not cut and "music_offtopic" in active:
            active.remove("music_offtopic")

        self.set("sb_categories", active)
        await call.answer(self.strings("sb_saved"))
        await call.edit(self._sb_music_text(), reply_markup=self._sb_music_markup())

    async def _sb_toggle_music_only(self, call):
        only_music = self.get("sb_music_only", True)
        self.set("sb_music_only", not only_music)
        await call.answer(self.strings("sb_saved"))
        await call.edit(self._sb_music_text(), reply_markup=self._sb_music_markup())

    async def _sb_back(self, call):
        await call.edit(self._sb_main_text(), reply_markup=self._sb_main_markup())

    @loader.command()
    async def dlvideo(self, message):
        """Скачать видео или аудио по ссылке (или в ответ на сообщение со ссылкой)"""
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()

        audio_only = False
        if args and args.startswith(('-a', '-audio', '--audio')):
            audio_only = True
            args = args.split(maxsplit=1)[1] if len(args.split(maxsplit=1)) > 1 else ""

        link = extract_video_link(args) if args else None
        if not link and reply:
            link = extract_video_link(reply.raw_text)

        if not link:
            await utils.answer(message, self.strings["no_link"])
            return

        if audio_only:
            status_msg = await utils.answer(message, self.strings("downloading_audio"))
        else:
            status_msg = await utils.answer(message, self.config["downloading_text"].replace("{attempt}", "1").replace("{method}", "..."))

        cookies = self.config["youtube_cookies"].strip() if self.config["youtube_cookies"] else None
        proxy = self.config["proxy"].strip() if self.config["proxy"] else None
        deno = self.get("deno_source") if self.get("deno_source") not in ["install_failed", None] else None
        max_attempts = self.config["max_attempts"]

        sb_enabled = self.get("sb_enabled", True)
        sb_categories = list(self.get("sb_categories", DEFAULT_SB_CATEGORIES)) if sb_enabled else []
        if "music_offtopic" in sb_categories and self.get("sb_music_only", True) and "music.youtube.com" not in link.lower():
            sb_categories.remove("music_offtopic")

        method_labels = {
            "proxy": self.strings("method_proxy"),
            "cookies": self.strings("method_cookies"),
            "direct": self.strings("method_direct"),
        }
        progress = {"attempt": 1, "method": "direct"}

        async def update_status(attempt, method_name):
            progress["attempt"] = attempt
            progress["method"] = method_name
            if not audio_only:
                try:
                    text = self.config["downloading_text"].replace(
                        "{attempt}", str(attempt)
                    ).replace(
                        "{method}", method_labels.get(method_name, method_name)
                    )
                    await status_msg.edit(text)
                except Exception:
                    pass

        try:
            media, title, channel = await download_media(
                link,
                cookies_text=cookies,
                proxy=proxy,
                deno_path=deno,
                max_attempts=max_attempts,
                audio_only=audio_only,
                sponsorblock_categories=sb_categories,
                on_attempt=update_status,
            )

            if audio_only:
                caption = self.config["music_response_text"].replace("{title}", title or "")
            else:
                if self.config["show_link"]:
                    caption_template = self.config["response_text"]
                    caption = convert_markdown_to_html(caption_template, link)
                    caption = caption.replace("{title}", title or "")

                    if self.config["show_channel"] and channel:
                        channel_text = self.config["channel_text"].replace("{channel}", channel)
                        caption += f"\n\n{channel_text}"
                else:
                    caption = title or self.strings("done_fallback")

            await utils.answer_file(
                status_msg,
                media,
                caption=caption,
                parse_mode="HTML",
                reply_to=reply or message,
                silent=True,
                voice=False
            )

            try:
                await status_msg.delete()
            except:
                pass
            try:
                os.remove(media)
            except:
                pass

        except Exception as e:
            error_msg = self.config["error_text"].replace("{attempts}", str(progress["attempt"])).replace("{error}", str(e))
            await utils.answer(status_msg, error_msg)
            try:
                if 'media' in locals():
                    os.remove(media)
            except:
                pass
