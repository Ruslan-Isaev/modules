# meta developer: @RUIS_VlP, @RoKrz
# meta banner: https://raw.githubusercontent.com/Ruslan-Isaev/modules/refs/heads/main/photos/banner.jpg
# requires: yt_dlp aiohttp aiofiles

import yt_dlp
import uuid
import os
import re
import json
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
from telethon.tl.types import MessageEntityTextUrl
from herokutl.tl.functions.messages import SendMessageRequest, UploadMediaRequest
from herokutl.tl.types import (
    InputMediaUploadedPhoto,
    InputPhoto,
    InputReplyToMessage,
    InputRichMessage,
    PageBlockPhoto,
    PageBlockSlideshow,
    PageCaption,
    TextEmpty,
    TextPlain,
)
from herokutl.extensions import html as herokutl_html
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

    all_matches = []
    for pattern in video_sites_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            all_matches.append(match)
    if all_matches:
        all_matches.sort(key=lambda m: m.start())
        return all_matches[0].group(0)

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


def find_video_link_in_message(message):
    if not message:
        return None

    link = extract_video_link(message.raw_text or "")
    if link:
        return link

    for entity in (message.entities or []):
        if isinstance(entity, MessageEntityTextUrl):
            found = extract_video_link(entity.url)
            if found:
                return found

    return None


def parse_time_to_seconds(time_str):
    if not time_str:
        return None

    time_str = time_str.strip().lower()

    yt_style = re.fullmatch(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+(?:\.\d+)?)s)?", time_str)
    if yt_style and any(yt_style.groups()):
        h, m, s = yt_style.groups()
        return int(h or 0) * 3600 + int(m or 0) * 60 + float(s or 0)

    if ":" in time_str:
        parts = time_str.split(":")
        try:
            parts = [float(p) if i == len(parts) - 1 else int(p) for i, p in enumerate(parts)]
        except ValueError:
            return None
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        return None

    try:
        return float(time_str)
    except ValueError:
        return None

    return None


def format_seconds(total_seconds):
    if total_seconds is None:
        total_seconds = 0
    whole = int(total_seconds)
    frac_ms = round((total_seconds - whole) * 1000)
    if frac_ms >= 1000:
        whole += 1
        frac_ms = 0
    h, rem = divmod(whole, 3600)
    m, s = divmod(rem, 60)
    ms_part = f".{frac_ms:03d}" if frac_ms else ""
    if h:
        return f"{h}:{m:02d}:{s:02d}{ms_part}"
    return f"{m}:{s:02d}{ms_part}"


SITE_EMOJI = [
    (("youtube.com", "youtu.be"), "🔴", "5355235592844095825"),
    (("tiktok.com",), "🎵", "5353034628263330616"),
    (("instagram.com",), "📸", "5355097780228470775"),
    (("x.com", "twitter.com"), "🐦", "5355148941878900494"),
    (("facebook.com",), "👥", "5355254460635428635"),
    (("vimeo.com",), "🎬", "5334764984142412896"),
    (("twitch.tv",), "🎮", "5352759664457038886"),
    (("reddit.com",), "👽", "5352531593103686999"),
    (("music.yandex",), "🎧", "5346296430166293639"),
    (("soundcloud.com",), "☁️", "5345844509412444249"),
    (("bandcamp.com",), "🎸", "5451966206334513619"),
    (("spotify.com",), "🟢", "5346074681004801565"),
    (("rutube.ru",), "▶️", "5298747646096187189"),
    (("vk.com",), "🔵", "5278229754099540071"),
    (("ok.ru",), "🟠", "5310076528577491230"),
]


def get_site_emoji_html(url):
    url_lower = (url or "").lower()
    for domains, fallback, premium_id in SITE_EMOJI:
        if any(d in url_lower for d in domains):
            if premium_id:
                return f'<tg-emoji emoji-id="{premium_id}">{fallback}</tg-emoji>'
            return fallback
    return "🎥"


def extract_url_timecode(url):
    match = re.search(r"[?&]t=([0-9hms]+)", url)
    if not match:
        match = re.search(r"[?&]start=(\d+)", url)
    if match:
        return parse_time_to_seconds(match.group(1))
    return None


def parse_dlvideo_args(args_str):
    result = {"audio_only": False, "start": None, "end": None, "rest": ""}
    if not args_str:
        return result

    tokens = args_str.split()
    rest_tokens = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        low = tok.lower()

        if low in ("-a", "-audio", "--audio"):
            result["audio_only"] = True
        elif low in ("-s", "-start", "--start") and i + 1 < len(tokens):
            result["start"] = parse_time_to_seconds(tokens[i + 1])
            i += 1
        elif low in ("-e", "-end", "--end") and i + 1 < len(tokens):
            result["end"] = parse_time_to_seconds(tokens[i + 1])
            i += 1
        else:
            rest_tokens.append(tok)

        i += 1

    result["rest"] = " ".join(rest_tokens)
    return result


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

VOT_BRIDGE_SCRIPT = """function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function loadVOTClient() {
  if (typeof globalThis.File === "undefined") {
    const bufferModule = await import("node:buffer");
    if (bufferModule.File) {
      globalThis.File = bufferModule.File;
    }
  }
  const mod = await import("@vot.js/node");
  return { VOTClient: mod.default, videoDataUtil: mod.videoData };
}

async function translateVideoUrl(videoUrl, responseLang, maxWaitSeconds) {
  const { VOTClient, videoDataUtil } = await loadVOTClient();
  const data = await videoDataUtil.getVideoData(videoUrl);
  const client = new VOTClient();

  const deadline = Date.now() + maxWaitSeconds * 1000;
  let result = await client.translateVideo({
    videoData: data,
    requestLang: "auto",
    responseLang,
  });

  while (!result.translated || result.remainingTime >= 1) {
    if (Date.now() > deadline) {
      throw new Error(`Timed out waiting for translation (status ${result.status})`);
    }
    const waitMs = Math.min(Math.max(result.remainingTime, 1), 15) * 1000;
    await sleep(waitMs);
    result = await client.translateVideo({
      videoData: data,
      requestLang: "auto",
      responseLang,
    });
  }

  return {
    url: result.url,
    translationId: result.translationId,
    title: data.title || null,
  };
}

async function main() {
  const [, , videoUrl, responseLang = "ru", maxWaitSeconds = "180"] = process.argv;

  if (!videoUrl) {
    console.log(JSON.stringify({ ok: false, error: "no_url" }));
    process.exit(1);
  }

  try {
    const translation = await translateVideoUrl(videoUrl, responseLang, Number(maxWaitSeconds));
    console.log(JSON.stringify({ ok: true, ...translation }));
  } catch (err) {
    console.log(JSON.stringify({ ok: false, error: String((err && err.message) || err) }));
    process.exit(1);
  }
}

main();
"""


LANG_DISPLAY = {
    "en": "EN", "ru": "RU", "uk": "UK", "de": "DE", "ja": "JA",
    "es": "ES", "fr": "FR", "it": "IT", "pt": "PT", "ko": "KO",
    "zh": "ZH", "tr": "TR", "pl": "PL", "ar": "AR", "hi": "HI",
}


def lang_display(code):
    if not code:
        return "??"
    code = code.lower().split("-")[0]
    return LANG_DISPLAY.get(code, code.upper())


def get_vot_bridge_dir():
    return os.path.join(utils.get_base_dir(), "vot_bridge")


async def ensure_vot_bridge_ready():
    bridge_dir = get_vot_bridge_dir()
    script_path = os.path.join(bridge_dir, "vot_bridge.mjs")
    node_modules_path = os.path.join(bridge_dir, "node_modules", "@vot.js")

    os.makedirs(bridge_dir, exist_ok=True)

    async with aiofiles.open(script_path, "w", encoding="utf-8") as f:
        await f.write(VOT_BRIDGE_SCRIPT)

    if not shutil.which("node") or not shutil.which("npm"):
        raise Exception("Node.js/npm не найдены на сервере — озвучка требует их установки отдельно")

    await ensure_node_version_ok()

    if not os.path.isdir(node_modules_path):
        proc = await asyncio.create_subprocess_exec(
            "npm", "install", "@vot.js/node", "--no-audit", "--no-fund",
            cwd=bridge_dir,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise Exception(f"npm install @vot.js/node не удался: {stderr.decode()[:300]}")

    return script_path


async def get_node_major_version():
    proc = await asyncio.create_subprocess_exec(
        "node", "--version",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    stdout, _ = await proc.communicate()
    version_str = stdout.decode().strip()
    match = re.match(r"v?(\d+)\.", version_str)
    return int(match.group(1)) if match else None


async def ensure_node_version_ok(minimum=20):
    major = await get_node_major_version()
    if major is not None and major >= minimum:
        return

    if not shutil.which("n"):
        raise Exception(
            f"Node.js слишком старый (нужен {minimum}+), а менеджер версий n не найден. "
            f"Выполните вручную: n latest"
        )

    proc = await asyncio.create_subprocess_exec(
        "n", "latest",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()

    new_major = await get_node_major_version()
    if new_major is None or new_major < minimum:
        raise Exception(
            f"Node.js слишком старый (нужен {minimum}+) и автообновление через 'n latest' не сработало "
            f"({stderr.decode()[:200]}). Выполните вручную: n latest"
        )


async def get_translated_audio(video_url, response_lang="ru", max_wait_seconds=180):
    script_path = await ensure_vot_bridge_ready()

    proc = await asyncio.create_subprocess_exec(
        "node", script_path, video_url, response_lang, str(max_wait_seconds),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    try:
        result = json.loads(stdout.decode().strip().splitlines()[-1])
    except Exception:
        raise Exception(f"Не удалось разобрать ответ моста озвучки: {stderr.decode()[:300] or stdout.decode()[:300]}")

    if not result.get("ok"):
        raise Exception(result.get("error", "неизвестная ошибка озвучки"))

    return result["url"], result.get("title")


async def mux_translated_audio(video_path, audio_url, orig_volume_percent=50):
    output_path = video_path + ".vo.mp4"
    audio_temp = video_path + ".vo_audio.tmp"

    async with aiohttp.ClientSession() as session:
        async with session.get(audio_url) as resp:
            async with aiofiles.open(audio_temp, "wb") as f:
                async for chunk in resp.content.iter_chunked(8192):
                    await f.write(chunk)

    extra_gain = max(0, min(100, orig_volume_percent)) / 100

    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", audio_temp,
        "-filter_complex",
        f"[0:a][1:a]sidechaincompress=threshold=0.02:ratio=15:attack=50:release=400:makeup=1[ducked];"
        f"[ducked]volume={extra_gain}[quiet];"
        f"[quiet][1:a]amix=inputs=2:duration=shortest:dropout_transition=0:normalize=0[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-shortest",
        output_path,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()

    try:
        os.remove(audio_temp)
    except Exception:
        pass

    if proc.returncode != 0 or not os.path.exists(output_path):
        raise Exception("ffmpeg не смог вклеить переведённую дорожку")

    try:
        os.remove(video_path)
    except Exception:
        pass

    return output_path


async def resolve_tiktok_url(url):
    parts = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


async def tikwm_lookup(url):
    resolved = await resolve_tiktok_url(url)
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://www.tikwm.com/api/",
            params={"url": resolved},
            timeout=aiohttp.ClientTimeout(total=15),
        ) as resp:
            payload = await resp.json(content_type=None)

    if payload.get("code") != 0:
        raise Exception(payload.get("msg", "tikwm вернул ошибку"))

    return payload.get("data") or {}


async def download_file(url, output_dir, ext, min_size=512, retries=2):
    path = os.path.join(output_dir, f"{uuid.uuid4()}.{ext}")
    last_err = None
    for attempt in range(retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    async with aiofiles.open(path, "wb") as f:
                        async for chunk in resp.content.iter_chunked(8192):
                            await f.write(chunk)

            if os.path.isfile(path) and os.path.getsize(path) >= min_size:
                return path
            last_err = Exception(f"файл слишком маленький ({os.path.getsize(path) if os.path.isfile(path) else 0} байт)")
        except Exception as e:
            last_err = e

        if os.path.isfile(path):
            try:
                os.remove(path)
            except Exception:
                pass

    raise last_err or Exception("не удалось скачать файл")


async def download_tiktok_via_api(url, output_dir):
    data = await tikwm_lookup(url)
    video_url = data.get("play") or data.get("hdplay")
    if not video_url:
        raise Exception("tikwm не вернул ссылку на видео")

    title = data.get("title") or "TikTok"
    author = ((data.get("author") or {}).get("nickname")) or None
    file_path = await download_file(video_url, output_dir, "mp4")

    return file_path, title, author


async def download_tiktok_slideshow(url, output_dir):
    data = await tikwm_lookup(url)
    images = data.get("images") or []
    if not images:
        return None

    image_paths = []
    for image_url in images:
        image_paths.append(await download_file(image_url, output_dir, "jpg"))

    audio_path = None
    music_url = data.get("music")
    if music_url:
        audio_path = await download_file(music_url, output_dir, "mp3")

    title = data.get("title") or "TikTok"
    author = ((data.get("author") or {}).get("nickname")) or None
    music_title = (data.get("music_info") or {}).get("title")

    return image_paths, audio_path, title, author, music_title


async def send_tiktok_rich_slideshow(client, chat_id, image_paths, caption_html, reply_to_msg_id=None):
    input_peer = await client.get_input_entity(chat_id)

    input_photos = []
    for path in image_paths:
        uploaded_file = await client.upload_file(path)
        media = await client(
            UploadMediaRequest(peer=input_peer, media=InputMediaUploadedPhoto(file=uploaded_file))
        )
        photo = media.photo
        input_photos.append(
            InputPhoto(id=photo.id, access_hash=photo.access_hash, file_reference=photo.file_reference)
        )

    items = [
        PageBlockPhoto(photo_id=ip.id, caption=PageCaption(text=TextEmpty(), credit=TextEmpty()))
        for ip in input_photos
    ]
    slideshow = PageBlockSlideshow(items=items, caption=PageCaption(text=TextEmpty(), credit=TextEmpty()))
    rich_message = InputRichMessage(blocks=[slideshow], photos=input_photos)

    text, entities = herokutl_html.parse(caption_html) if caption_html else ("", [])
    reply_to = InputReplyToMessage(reply_to_msg_id=reply_to_msg_id) if reply_to_msg_id else None

    await client(
        SendMessageRequest(
            peer=input_peer,
            message=text,
            entities=entities or None,
            rich_message=rich_message,
            reply_to=reply_to,
            silent=True,
            random_id=int.from_bytes(os.urandom(8), "big", signed=True),
        )
    )


async def download_media(
    url,
    cookies_text=None,
    proxy=None,
    deno_path=None,
    max_attempts=50,
    audio_only=False,
    sponsorblock_categories=None,
    start_time=None,
    end_time=None,
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

                    if start_time is not None or end_time is not None:
                        section = {'start_time': start_time or 0}
                        if end_time is not None:
                            section['end_time'] = end_time
                        ydl_opts['download_ranges'] = lambda info, ydl_instance, section=section: [section]
                        ydl_opts['force_keyframes_at_cuts'] = True

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
                            source_lang = info_dict.get('language', None)

                        return file_path, title, channel, source_lang

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
    """Помогает скачивать видео с YouTube, TikTok и др. SponsorBlock вырезает рекламу, -s/-e берут только отрезок."""

    __version__ = (3, 2, 1)

    strings = {
        "name": "YouTube-DLD",
        "no_link": "❌ <b>Пожалуйста, укажите ссылку на видео либо ответьте на сообщение с ней.</b>",
        "default_downloading": "📥 <b>Начинаю загрузку...</b>\n\n<i>Попытка {attempt} ({method})</i>",
        "default_error": "❌ <b>Ошибка после {attempts} попыток!</b>\n\n<code>{error}</code>",
        "default_response": "{site} Вот [ваше видео]({link})!\n\n<code>{title}</code>",
        "default_music_response": "🎵 <b>Аудио готово!</b> [ссылка]({link})\n\n<code>{title}</code>",
        "default_channel": "<tg-emoji emoji-id=\"5886412370347036129\">👤</tg-emoji> Канал: <code>{channel}</code>",
        "downloading_audio": "🎵 <b>Скачиваю аудио...</b>",
        "done_fallback": "Готово!",
        "method_proxy": "прокси",
        "method_cookies": "куки",
        "method_direct": "напрямую",
        "cookies_required_error": "❌ <b>Ошибка куки.</b> Просьба вставить куки через команду <code>.cfg YouTube-DLD youtube_cookies</code>.",
        "supported_sites": """🎥 <b>Поддерживаемые сайты:</b>

<tg-emoji emoji-id="5355235592844095825">🔴</tg-emoji> <b>YouTube</b> — youtube.com, youtu.be, music.youtube.com
<tg-emoji emoji-id="5353034628263330616">🎵</tg-emoji> <b>TikTok</b> — tiktok.com, vt.tiktok.com, vm.tiktok.com
<tg-emoji emoji-id="5355097780228470775">📸</tg-emoji> <b>Instagram</b> — instagram.com
<tg-emoji emoji-id="5355148941878900494">🐦</tg-emoji> <b>X (Twitter)</b> — x.com, twitter.com
<tg-emoji emoji-id="5355254460635428635">👥</tg-emoji> <b>Facebook</b> — facebook.com
<tg-emoji emoji-id="5334764984142412896">🎬</tg-emoji> <b>Vimeo</b> — vimeo.com
<tg-emoji emoji-id="5352759664457038886">🎮</tg-emoji> <b>Twitch</b> — twitch.tv
<tg-emoji emoji-id="5352531593103686999">👽</tg-emoji> <b>Reddit</b> — reddit.com

<b>🎵 Музыка:</b>
<tg-emoji emoji-id="5346296430166293639">🎧</tg-emoji> <b>Яндекс.Музыка</b> — music.yandex.ru
<tg-emoji emoji-id="5345844509412444249">☁️</tg-emoji> <b>SoundCloud</b> — soundcloud.com
<tg-emoji emoji-id="5451966206334513619">🎸</tg-emoji> <b>Bandcamp</b> — bandcamp.com
<tg-emoji emoji-id="5346074681004801565">🟢</tg-emoji> <b>Spotify</b> — spotify.com

<b>🇷🇺 Российские:</b>
<tg-emoji emoji-id="5298747646096187189">▶️</tg-emoji> <b>RuTube</b> — rutube.ru
<tg-emoji emoji-id="5278229754099540071">🔵</tg-emoji> <b>ВКонтакте</b> — vk.com
<tg-emoji emoji-id="5310076528577491230">🟠</tg-emoji> <b>Одноклассники</b> — ok.ru

Полный список поддерживаемых сайтов — <a href="https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md">тут</a>.

<b>📝 Команды:</b>
▫️ .dlvideo <ссылка> — скачать видео
▫️ .dlvideo -a <ссылка> — скачать аудио
▫️ .dlvideo -s 1:30 -e 5:00 <ссылка> — только отрезок (можно и без -e)
▫️ .dvlist — список сайтов
▫️ .sblock — настройки SponsorBlock (инлайн-меню)
▫️ .dlvo — то же самое, что .dlvideo, но с переводом озвучки""",
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
        "vo_translating": "🗣 <b>Перевожу озвучку...</b>\n\n<i>Это не мгновенно, может занять пару минут.</i>",
        "vo_failed": "⚠️ Озвучка не получилась: <code>{error}</code>\n\nОтправляю видео без перевода...",
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
        "default_response": "{site} Here's [your video]({link})!\n\n<code>{title}</code>",
        "default_music_response": "🎵 <b>Audio ready!</b> [link]({link})\n\n<code>{title}</code>",
        "default_channel": "<tg-emoji emoji-id=\"5886412370347036129\">👤</tg-emoji> Channel: <code>{channel}</code>",
        "downloading_audio": "🎵 <b>Downloading audio...</b>",
        "done_fallback": "Done!",
        "method_proxy": "proxy",
        "method_cookies": "cookies",
        "method_direct": "direct",
        "cookies_required_error": "❌ <b>Cookies error.</b> Please add cookies via <code>.cfg YouTube-DLD youtube_cookies</code>.",
        "supported_sites": """🎥 <b>Supported sites:</b>

<tg-emoji emoji-id="5355235592844095825">🔴</tg-emoji> <b>YouTube</b> — youtube.com, youtu.be, music.youtube.com
<tg-emoji emoji-id="5353034628263330616">🎵</tg-emoji> <b>TikTok</b> — tiktok.com, vt.tiktok.com, vm.tiktok.com
<tg-emoji emoji-id="5355097780228470775">📸</tg-emoji> <b>Instagram</b> — instagram.com
<tg-emoji emoji-id="5355148941878900494">🐦</tg-emoji> <b>X (Twitter)</b> — x.com, twitter.com
<tg-emoji emoji-id="5355254460635428635">👥</tg-emoji> <b>Facebook</b> — facebook.com
<tg-emoji emoji-id="5334764984142412896">🎬</tg-emoji> <b>Vimeo</b> — vimeo.com
<tg-emoji emoji-id="5352759664457038886">🎮</tg-emoji> <b>Twitch</b> — twitch.tv
<tg-emoji emoji-id="5352531593103686999">👽</tg-emoji> <b>Reddit</b> — reddit.com

<b>🎵 Music:</b>
<tg-emoji emoji-id="5346296430166293639">🎧</tg-emoji> <b>Yandex Music</b> — music.yandex.ru
<tg-emoji emoji-id="5345844509412444249">☁️</tg-emoji> <b>SoundCloud</b> — soundcloud.com
<tg-emoji emoji-id="5451966206334513619">🎸</tg-emoji> <b>Bandcamp</b> — bandcamp.com
<tg-emoji emoji-id="5346074681004801565">🟢</tg-emoji> <b>Spotify</b> — spotify.com

<b>🇷🇺 Russian:</b>
<tg-emoji emoji-id="5298747646096187189">▶️</tg-emoji> <b>RuTube</b> — rutube.ru
<tg-emoji emoji-id="5278229754099540071">🔵</tg-emoji> <b>VK</b> — vk.com
<tg-emoji emoji-id="5310076528577491230">🟠</tg-emoji> <b>Odnoklassniki</b> — ok.ru

Full list of supported sites — <a href="https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md">here</a>.

<b>📝 Commands:</b>
▫️ .dlvideo <link> — download video
▫️ .dlvideo -a <link> — download audio
▫️ .dlvideo -s 1:30 -e 5:00 <link> — just a clip (-e is optional)
▫️ .dvlist — list of supported sites
▫️ .sblock — SponsorBlock settings (inline menu)
▫️ .dlvo — same as .dlvideo, but with voice-over translation""",
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
        "vo_translating": "🗣 <b>Translating voice-over...</b>\n\n<i>Not instant, can take a couple of minutes.</i>",
        "vo_failed": "⚠️ Voice-over failed: <code>{error}</code>\n\nSending the video without translation...",
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
                "1. Подключись к VPN страны где твой сервер (не обязательно)\n"
                "2. Открой приватное окно в браузере → залогинься на YouTube\n"
                "3. Перейди на youtube.com/robots.txt\n"
                "4. <a href='https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm'>Cookie-Editor</a> → Export → Netscape\n"
                "5. СРАЗУ закрой окно\n"
                "6. Вставь ВЕСЬ текст сюда из файла\n\n"
                "Начинается с: # Netscape HTTP Cookie File",
                validator=loader.validators.Hidden(),
            ),
            loader.ConfigValue(
                "proxy",
                "",
                "🌐 Прокси (опционально)\n\n"
                "Форматы:\n"
                "• HTTP: http://user:pass@host:port\n"
                "• SOCKS5: socks5://host:port\n\n"
                "Пусто — прокси не используется. Заполнено — пробуем через прокси, затем куки, затем напрямую.\n\n"
                "⚠️ Trojan/VLESS не поддерживаются!",
                validator=loader.validators.Hidden(),
            ),
            loader.ConfigValue(
                "max_attempts",
                10,
                "Максимум попыток (1-10)",
                validator=loader.validators.Integer(minimum=1, maximum=10),
            ),
            loader.ConfigValue(
                "vo_orig_volume",
                50,
                "🔊 Громкость оригинальной озвучки при переводе (0-100%), пока идёт перевод поверх",
                validator=loader.validators.Integer(minimum=0, maximum=100),
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
        """Скачать видео/аудио по ссылке. -a аудио, -s/-e начало/конец отрезка"""
        await self._dlvideo_impl(message, force_translate=False)

    @loader.command()
    async def dlvo(self, message):
        """То же самое что .dlvideo (те же флаги -a/-s/-e), но с переводом озвучки"""
        await self._dlvideo_impl(message, force_translate=True)

    async def _dlvideo_impl(self, message, force_translate=False):
        args_raw = utils.get_args_raw(message)
        reply = await message.get_reply_message()

        parsed = parse_dlvideo_args(args_raw)
        audio_only = parsed["audio_only"]
        start_time = parsed["start"]
        end_time = parsed["end"]

        link = find_video_link_in_message(message)
        if not link and reply:
            link = find_video_link_in_message(reply)

        if not link:
            await utils.answer(message, self.strings["no_link"])
            return

        if start_time is None:
            url_timecode = extract_url_timecode(link)
            if url_timecode is not None:
                start_time = url_timecode

        if start_time is not None and end_time is not None and end_time <= start_time:
            end_time = None

        if audio_only:
            status_msg = await utils.answer(message, self.strings("downloading_audio"))
        else:
            status_msg = await utils.answer(message, self.config["downloading_text"].replace("{attempt}", "1").replace("{method}", "..."))

        cookies = self.config["youtube_cookies"].strip() if self.config["youtube_cookies"] else None
        proxy = self.config["proxy"].strip() if self.config["proxy"] else None
        is_tiktok = "tiktok.com" in link.lower()
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
            tiktok_slideshow = None
            if is_tiktok and not audio_only and not force_translate:
                try:
                    tiktok_slideshow = await download_tiktok_slideshow(link, utils.get_base_dir())
                except Exception:
                    tiktok_slideshow = None

            if tiktok_slideshow:
                image_paths, audio_path, title, channel, _ = tiktok_slideshow

                async def send_album_fallback(files, cap):
                    try:
                        await utils.answer_file(
                            status_msg, files, caption=cap, parse_mode="HTML",
                            reply_to=reply or message, silent=True,
                        )
                    except TypeError as silent_err:
                        if "silent" not in str(silent_err):
                            raise
                        await utils.answer_file(
                            status_msg, files, caption=cap, parse_mode="HTML",
                            reply_to=reply or message,
                        )

                try:
                    caption = convert_markdown_to_html(self.config["response_text"], link)
                    caption = caption.replace("{title}", title or "")
                    caption = caption.replace("{site}", get_site_emoji_html(link))
                    if self.config["show_channel"] and channel:
                        channel_text = self.config["channel_text"].replace("{channel}", channel)
                        caption += f"\n\n{channel_text}"

                    reply_target = reply or message
                    reply_to_id = reply_target.id if reply_target else None
                    slideshow_caption = None if audio_path else caption

                    try:
                        await send_tiktok_rich_slideshow(
                            message.client, message.chat_id, image_paths, slideshow_caption, reply_to_id
                        )
                    except Exception:
                        chunks = [image_paths[i:i + 10] for i in range(0, len(image_paths), 10)]
                        for idx, chunk in enumerate(chunks):
                            fallback_cap = None
                            if not audio_path and idx == len(chunks) - 1:
                                fallback_cap = caption
                            await send_album_fallback(chunk, fallback_cap)

                    if audio_path:
                        await send_album_fallback(audio_path, caption)

                    try:
                        await status_msg.delete()
                    except Exception:
                        pass
                finally:
                    for path in image_paths:
                        try:
                            os.remove(path)
                        except Exception:
                            pass
                    if audio_path:
                        try:
                            os.remove(audio_path)
                        except Exception:
                            pass

                return

            media = title = channel = source_lang = None
            last_err = None
            for attempt_idx in range(2):
                try:
                    media, title, channel, source_lang = await download_media(
                        link,
                        cookies_text=cookies,
                        proxy=proxy,
                        deno_path=deno,
                        max_attempts=max_attempts,
                        audio_only=audio_only,
                        sponsorblock_categories=sb_categories,
                        start_time=start_time,
                        end_time=end_time,
                        on_attempt=update_status,
                    )
                except Exception as primary_err:
                    last_err = primary_err
                    media = None
                    if is_tiktok and not audio_only:
                        try:
                            media, title, channel = await download_tiktok_via_api(link, utils.get_base_dir())
                            source_lang = None
                        except Exception:
                            media = None

                if media and os.path.isfile(media) and os.path.getsize(media) > 0:
                    break
                media = None

            if not media:
                raise last_err or Exception(self.strings("done_fallback"))

            translation_marker = ""
            if force_translate and not audio_only:
                try:
                    try:
                        await status_msg.edit(self.strings("vo_translating"))
                    except Exception:
                        pass
                    ub_lang_raw = (self.db.get("heroku.translations", "lang", "en") or "en").strip().lower()
                    ub_lang_code = ub_lang_raw.split()[0] if ub_lang_raw else "en"
                    vo_lang = "ru" if ub_lang_code in ("ru", "uk", "ua") else "en"
                    audio_url, _ = await get_translated_audio(link, response_lang=vo_lang)
                    media = await mux_translated_audio(media, audio_url, orig_volume_percent=self.config["vo_orig_volume"])
                    translation_marker = f"🌐 {lang_display(source_lang)} ➔ {lang_display(vo_lang)}\n"
                except Exception as vo_err:
                    logger.warning(f"VOT translation failed: {vo_err}")
                    try:
                        await status_msg.edit(self.strings("vo_failed").replace("{error}", str(vo_err)))
                        await asyncio.sleep(3)
                    except Exception:
                        pass

            if not (media and os.path.isfile(media) and os.path.getsize(media) > 0):
                raise Exception(self.strings("done_fallback"))

            clip_marker = ""
            if start_time is not None or end_time is not None:
                clip_marker = f" ✂️({format_seconds(start_time or 0)}-{format_seconds(end_time) if end_time is not None else '…'})"

            if audio_only:
                caption = convert_markdown_to_html(self.config["music_response_text"], link)
                caption = caption.replace("{title}", title or "")
            else:
                if self.config["show_link"]:
                    caption_template = self.config["response_text"]
                    caption = convert_markdown_to_html(caption_template, link)
                    caption = caption.replace("{title}", title or "")
                    caption = caption.replace("{site}", get_site_emoji_html(link))

                    if translation_marker:
                        lines = caption.split("\n", 1)
                        lines[0] = translation_marker + lines[0]
                        caption = "\n".join(lines)

                    if clip_marker:
                        lines = caption.split("\n", 1)
                        lines[0] = lines[0] + clip_marker
                        caption = "\n".join(lines)

                    if self.config["show_channel"] and channel:
                        channel_text = self.config["channel_text"].replace("{channel}", channel)
                        caption += f"\n\n{channel_text}"
                else:
                    caption = (translation_marker + (title or self.strings("done_fallback"))) + clip_marker

            try:
                await utils.answer_file(
                    status_msg,
                    media,
                    caption=caption,
                    parse_mode="HTML",
                    reply_to=reply or message,
                    silent=True,
                )
            except TypeError as silent_err:
                if "silent" not in str(silent_err):
                    raise
                await utils.answer_file(
                    status_msg,
                    media,
                    caption=caption,
                    parse_mode="HTML",
                    reply_to=reply or message,
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
            error_str = str(e)
            if "sign in to confirm" in error_str.lower() or "confirm you" in error_str.lower():
                error_msg = self.strings("cookies_required_error")
            else:
                error_msg = self.config["error_text"].replace("{attempts}", str(progress["attempt"])).replace("{error}", str(e))
            await utils.answer(status_msg, error_msg)
            try:
                if 'media' in locals():
                    os.remove(media)
            except:
                pass
