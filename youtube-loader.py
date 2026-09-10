# meta developer: @RUIS_VlP, @RoKrz
# meta banner: https://raw.githubusercontent.com/Ruslan-Isaev/modules/refs/heads/main/photos/banner.jpg
# meta pic: https://kappa.lol/21nHvy
# requires: yt_dlp aiohttp aiofiles mutagen

__version__ = (3, 4, 9)

import yt_dlp
import uuid
import os
import re
import html as html_escaping
import json
import random
import time
import threading
import asyncio
import shutil
import tempfile
import zipfile
import platform
import urllib.parse
import hmac
import hashlib
import base64
import struct
import aiohttp
import aiofiles
from mutagen import File as MutagenFile
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC, ID3NoHeaderError
from mutagen.mp3 import MP3
from mutagen.flac import FLAC, Picture as FlacPicture
from pathlib import Path
from telethon.tl.types import MessageEntityTextUrl
from telethon.tl import types as tl_types
from telethon.tl.custom import Message
from telethon import utils as tl_utils
from herokutl.tl.functions.messages import SendMessageRequest, UploadMediaRequest, UpdatePinnedMessageRequest, GetPeerDialogsRequest, SendMultiMediaRequest
from herokutl.tl.functions.account import UpdateNotifySettingsRequest, GetNotifySettingsRequest
from herokutl.tl.types import (
    DocumentAttributeAudio,
    DocumentAttributeFilename,
    InputDialogPeer,
    InputMediaUploadedDocument,
    InputMediaUploadedPhoto,
    InputNotifyPeer,
    InputPeerNotifySettings,
    InputPhoto,
    InputReplyToMessage,
    InputRichMessage,
    InputSingleMedia,
    PageBlockPhoto,
    PageBlockSlideshow,
    PageCaption,
    TextEmpty,
    TextPlain,
)
from herokutl.extensions import html as herokutl_html
from herokutl import utils as herokutl_utils
from .. import loader, utils
import logging

logger = logging.getLogger(__name__)

EMOJI_OK = "<tg-emoji emoji-id=5350572310627632617>✅</tg-emoji>"
EMOJI_FAIL = "<tg-emoji emoji-id=5348514879558926674>👎</tg-emoji>"
EMOJI_WARN = "<tg-emoji emoji-id=5350477112677515642>⚠️</tg-emoji>"
EMOJI_DOWNLOAD = "<tg-emoji emoji-id=5899757765743615694>📥</tg-emoji>"
EMOJI_COMPRESS = "<tg-emoji emoji-id=5988023995125993550>🛠</tg-emoji>"
EMOJI_INFO = "<tg-emoji emoji-id=5879785854284599288>ℹ️</tg-emoji>"
EMOJI_NOTE = "<tg-emoji emoji-id=5891249688933305846>🎵</tg-emoji>"
EMOJI_CHECK = "<tg-emoji emoji-id=5985596818912712352>✅</tg-emoji>"
EMOJI_CROSS = "<tg-emoji emoji-id=5985346521103604145>❌</tg-emoji>"
EMOJI_SCISSORS = "<tg-emoji emoji-id=5870462219019358212>✂️</tg-emoji>"
EMOJI_GEAR = "<tg-emoji emoji-id=5877260593903177342>⚙️</tg-emoji>"
EMOJI_MIC = "<tg-emoji emoji-id=5350790271627968474>🗣️</tg-emoji>"
EMOJI_ARROW = "<tg-emoji emoji-id=5875506366050734240>➡️</tg-emoji>"
EMOJI_GLOBE = "<tg-emoji emoji-id=5879585266426973039>🌐</tg-emoji>"
EMOJI_COOKIE = "<tg-emoji emoji-id=5845945815549350824>🍪</tg-emoji>"
EMOJI_WAND = "<tg-emoji emoji-id=5785326857587003471>🪄</tg-emoji>"
EMOJI_CLOCK = "<tg-emoji emoji-id=5776213190387961618>🕓</tg-emoji>"
EMOJI_PHOTO = "<tg-emoji emoji-id=5766879414704935108>🖼</tg-emoji>"

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def redact_secrets(text, cookies_text=None, proxy=None):
    """Вычищает из пользовательских сообщений значения кук/прокси."""
    if not text:
        return text
    out = str(text)
    secrets = []
    if proxy:
        secrets.append(str(proxy).strip())
    if cookies_text:
        for line in str(cookies_text).splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t") if "\t" in line else line.split()
            if len(parts) >= 7:
                secrets.append(parts[6])
            elif len(parts) >= 2 and "=" not in parts[0]:
                secrets.append(parts[-1])
        blob = str(cookies_text).strip()
        if len(blob) > 24:
            secrets.append(blob)
    for s in sorted({x for x in secrets if x and len(x) >= 6}, key=len, reverse=True):
        out = out.replace(s, "•••")
    return out


def clean_error_text(text, cookies_text=None, proxy=None):
    text = ANSI_RE.sub("", str(text))
    text = re.sub(r"^ERROR:\s*", "", text.strip())
    text = re.sub(r"^\[\w+\]\s*[\w.-]+:\s*", "", text)
    text = re.sub(r":\s+", ":\n", text)
    text = re.sub(r"(https?://[^:\s/]+:)[^@\s/]+@", r"\1•••@", text)
    text = re.sub(r"(socks5?://[^:\s/]+:)[^@\s/]+@", r"\1•••@", text)
    text = re.sub(
        r"(?i)\b(session_id|sessionid2|sid|psuid|yandexuid|auth_token|login_info|SAPISID|HSID|SSID|APISID|SIDCC)=[^\s;\"']+",
        r"\1=•••",
        text,
    )
    text = redact_secrets(text, cookies_text=cookies_text, proxy=proxy)
    return text.strip()



def cookies_error_message(site_name, robots_url, detail):
    """Единый текст ошибки нехватки куки — тот же, что при обычной нехватке куки YouTube,
    плюс явное пояснение, что для этого сайта нужен ВТОРОЙ, отдельный набор куки, добавленный
    отдельным элементом списка youtube_cookies (рядом с куками YouTube, не вместо них)."""
    return (
        f"{EMOJI_CROSS} <b>Ошибка куки.</b> Просьба вставить куки через команду "
        f"<code>.cfg YouTube-DLD youtube_cookies</code>.\n"
        f"Если куки YouTube там уже есть — добавьте ещё и куки {site_name} отдельным элементом "
        f"списка («Добавить элемент»): откройте залогиненными <code>{robots_url}</code>, "
        f"экспортируйте куки тем же Cookie-Editor в формате Netscape и вставьте — нужны оба набора "
        f"сразу, каждый своим элементом.\n\n"
        f"<code>{detail}</code>"
    )


AUDIO_ONLY_DOMAINS = (
    "myinstants.com",
    "music.yandex.",
    "soundcloud.com",
    "bandcamp.com",
    "mixcloud.com",
    "spotify.com",
)


def is_audio_only_platform(link):
    """Площадки, где видео в принципе нет — только звук (VK-аудио/музыка входят отдельной
    проверкой, у них нет единого домена-паттерна с остальными)."""
    link_lower = (link or "").lower()
    if any(d in link_lower for d in AUDIO_ONLY_DOMAINS):
        return True
    return any(p in link_lower for p in ("vk.com/audio", "vk.ru/audio", "vk.com/music", "vk.ru/music"))


COOKIE_DOMAIN_GROUPS = [
    ("youtube", ("youtube.com",)),
    ("yandex", ("yandex.",)),
    ("vk", ("vk.com", "vk.ru")),
    ("instagram", ("instagram.com",)),
    ("twitter", ("twitter.com", "x.com")),
]


def config_cookies_text(cfg_val):
    if not cfg_val:
        return ""
    if isinstance(cfg_val, (list, tuple)):
        return clean_cookies_text("\n".join(str(x) for x in cfg_val if x))
    return clean_cookies_text(str(cfg_val))


def clean_cookies_text(raw_text):
    """Пользователь обычно вставляет в youtube_cookies весь экспорт Cookie-Editor целиком —
    десятки кук с посторонних доменов плюс шапка-комментарий. Модулю из этого реально нужны
    только куки YouTube, Яндекса, VK и Instagram — остальное (и комментарии) выкидываем, а
    то, что нужно, оставляем сгруппированным в порядке ют → музыка → vk → инста. Строки вида
    '#HttpOnly_.youtube.com ...' — это НЕ комментарий, а обычная HttpOnly-кука в формате
    curl/Netscape, отличить их от настоящих комментариев ("# Netscape HTTP Cookie File" и
    т.п.) можно по числу табов: у настоящей строки куки их всегда 6."""
    if not raw_text:
        return None

    grouped = {"youtube": [], "yandex": [], "vk": [], "instagram": [], "twitter": []}
    for line in raw_text.splitlines():
        stripped = line.rstrip("\r\n")
        if not stripped.strip():
            continue
        parts = stripped.split("\t")
        if len(parts) < 7:
            parts = stripped.split()
        if len(parts) < 7:
            continue
        if len(parts) > 7:
            parts = parts[:6] + [" ".join(parts[6:])]
        if parts[0] == "#":
            continue
        normalized_line = "\t".join(parts)
        domain = parts[0].lower()
        for group_name, needles in COOKIE_DOMAIN_GROUPS:
            if any(n in domain for n in needles):
                grouped[group_name].append(normalized_line)
                break

    ordered_lines = grouped["youtube"] + grouped["yandex"] + grouped["vk"] + grouped["instagram"] + grouped["twitter"]
    if not ordered_lines:
        return None

    return "# Netscape HTTP Cookie File\n" + "\n".join(ordered_lines)


def extract_video_link(text):
    if not text:
        return None

    video_sites_patterns = [
        r"(https?://)?(www\.)?(youtube\.com|youtu\.be|music\.youtube\.com)/[^\s]+",
        r"(https?://)?(www\.)?(tiktok\.com|vt\.tiktok\.com|vm\.tiktok\.com)/[^\s]+",
        r"(https?://)?(www\.)?instagram\.com/(p|reel|tv)/[^\s]+",
        r"(https?://)?(www\.)?(twitter\.com|x\.com)/[^\s]+/status/[^\s]+",
        r"(https?://)?(www\.)?facebook\.com/[^\s]+/videos/[^\s]+",
        r"(https?://)?(www\.)?reddit\.com/r/[^\s]+/(comments|s)/[^\s]+",
        r"(https?://)?(www\.)?vimeo\.com/[^\s]+",
        r"(https?://)?(www\.)?dailymotion\.com/video/[^\s]+",
        r"(https?://)?(www\.)?twitch\.tv/(videos/|clip/|[^/]+$)[^\s]*",
        r"(https?://)?(www\.)?streamable\.com/[^\s]+",
        r"(https?://)?(music\.)?yandex\.(ru|com|by|kz|ua)/album/[^\s]+",
        r"(https?://)?(music\.)?yandex\.(ru|com|by|kz|ua)/track/[^\s]+",
        r"(https?://)?(music\.)?yandex\.(ru|com|by|kz|ua)/(users/[^\s]+/)?playlists/[^\s]+",
        r"(https?://)?(www\.)?soundcloud\.com/[^\s]+",
        r"(https?://)?(www\.)?bandcamp\.com/[^\s]+",
        r"(https?://)?(www\.)?mixcloud\.com/[^\s]+",
        r"(https?://)?(www\.)?spotify\.com/(track|album|playlist)/[^\s]+",
        r"(https?://)?(www\.)?rutube\.ru/video/[^\s]+",
        r"(https?://)?(www\.)?(vk\.com|vk\.ru)/(video|clip|audio|music)[^\s]+",
        r"(https?://)?(www\.)?ok\.ru/video/[^\s]+",
        r"(https?://)?(www\.)?(cdn\.discordapp\.com|media\.discordapp\.net)/attachments/[^\s]+",
        r"https?://[^\s]+\.(mp4|webm|avi|mkv|mov|flv|m4v|mp3|m4a|wav|flac)(\?[^\s]*)?",
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
            'stackoverflow.com', 'reddit.com/r/', 'amazon.com',
            'fixupx.com', 'vxtwitter.com', 'ozon.ru',
        ]
        if not any(domain in url.lower() for domain in excluded_domains):
            return url

    return None


INSTAGRAM_MIRROR_DOMAINS = ("kkinstagram.com",)


def normalize_link(link):
    if not link:
        return link
    for mirror in INSTAGRAM_MIRROR_DOMAINS:
        if mirror in link.lower():
            return re.sub(re.escape(mirror), "instagram.com", link, flags=re.IGNORECASE)
    return link


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
    (("youtube.com/shorts",), "🔴", "5352632932857035523"),
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
    (("vk.com/clip", "vk.ru/clip"), "🎥", "5280894678227492455"),
    (("vk.com", "vk.ru"), "🔵", "5278229754099540071"),
    (("ok.ru",), "🟠", "5310076528577491230"),
    (("cdn.discordapp.com", "media.discordapp.net"), "🎮", "5352866798121271480"),
    (("pornhub.com",), "🔞", "5370975411033356097"),
    (("likee.video", "likee.com"), "🌐", "5352672553930342216"),
    (("snapchat.com",), "🌐", "5352719553757466112"),
    (("pinterest.com", "pin.it"), "📷", "5303183810442044150"),
    (("steamcommunity.com", "store.steampowered.com"), "🎮", "5298975451161565553"),
    (("github.com",), "💻", "5303382121967001310"),
]


def get_site_emoji_html(url):
    url_lower = (url or "").lower()
    for domains, fallback, premium_id in SITE_EMOJI:
        if any(d in url_lower for d in domains):
            if premium_id:
                return f'<tg-emoji emoji-id="{premium_id}">{fallback}</tg-emoji>'
            return fallback
    return '<tg-emoji emoji-id="6005986106703613755">🎥</tg-emoji>'


def extract_url_timecode(url):
    match = re.search(r"[?&]t=([0-9hms]+)", url)
    if not match:
        match = re.search(r"[?&]start=(\d+)", url)
    if match:
        return parse_time_to_seconds(match.group(1))
    return None


def parse_dlvideo_args(args_str):
    result = {"audio_only": False, "start": None, "end": None, "raw_quality": False, "playlist": False, "rest": ""}
    if not args_str:
        return result

    tokens = args_str.split()

    merged_tokens = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == "-" and i + 1 < len(tokens) and re.fullmatch(r"[a-zA-Z]", tokens[i + 1]):
            merged_tokens.append("-" + tokens[i + 1])
            i += 2
        else:
            merged_tokens.append(tok)
            i += 1
    tokens = merged_tokens

    rest_tokens = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        low = tok.lower()

        if low in ("-a", "-audio", "--audio"):
            result["audio_only"] = True
        elif low in ("-q", "-quality", "--quality", "-raw", "--raw"):
            result["raw_quality"] = True
        elif low in ("-p", "-playlist", "--playlist"):
            result["playlist"] = True
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
    """Проверяет, что прокси реально работает, а не просто отвечает на TCP-хендшейк. Для
    HTTP(S)-прокси делаем настоящий CONNECT-туннель к эталонному хосту — мёртвый/«полуживой»
    прокси, который принимает соединение, но ничего не проксирует, такую проверку не пройдёт.
    Для SOCKS (которому этот стек напрямую не умеет) остаётся TCP-проверка — она хотя бы
    отсекает явно недоступные адреса."""
    try:
        parsed = urllib.parse.urlsplit(proxy)
        if not parsed.hostname or not parsed.port:
            return False
        scheme = (parsed.scheme or "http").lower()
        if scheme in ("http", "https"):
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(parsed.hostname, parsed.port),
                timeout=timeout_seconds,
            )
            try:
                auth = ""
                if parsed.username:
                    cred = (
                        f"{urllib.parse.unquote(parsed.username)}:"
                        f"{urllib.parse.unquote(parsed.password or '')}"
                    )
                    auth = "\r\nProxy-Authorization: Basic " + base64.b64encode(cred.encode()).decode()
                writer.write(
                    f"CONNECT www.gstatic.com:443 HTTP/1.1\r\nHost: www.gstatic.com:443{auth}\r\n\r\n".encode()
                )
                await writer.drain()
                status_line = await asyncio.wait_for(reader.readline(), timeout=timeout_seconds)
                while True:
                    line = await asyncio.wait_for(reader.readline(), timeout=timeout_seconds)
                    if line in (b"\r\n", b"\n", b""):
                        break
                return status_line.startswith(b"HTTP/1.1 2")
            finally:
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    pass

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

MAX_DOWNLOAD_ATTEMPTS = 10
SAVEASBOT_ID = 523131145

FORMAT_STANDARD = (
    'bestvideo[height<=720][height>=480][ext=mp4]+bestaudio[ext=m4a]/'
    'bestvideo[height<=720][height>=480]+bestaudio/'
    'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/'
    'bestvideo[height<=720]+bestaudio/'
    'best[height<=720][height>=480][ext=mp4]/best[height<=720][height>=480]/'
    'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/'
    'best[height<=480][ext=mp4]/best[height<=480]/'
    'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
)
FORMAT_CAPPED_2K = (
    'bestvideo[height<=1080][height>=720]+bestaudio/best[height<=1080][height>=720]/'
    'bestvideo[height<=1080]+bestaudio/best[height<=1080]/'
    'bestvideo[height<=720]+bestaudio/best[height<=720]/best'
)
FORMAT_RAW_1080 = (
    'bestvideo[height<=1080][height>=720][vcodec^=avc1]+bestaudio[ext=m4a]/'
    'bestvideo[height<=1080][vcodec^=avc1]+bestaudio[ext=m4a]/'
    'bestvideo[height<=1080][vcodec^=avc1]+bestaudio/'
    'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best'
)

QUALITY_FORMAT_MAP = {
    "standard": (FORMAT_STANDARD, "mp4"),
    "best": (FORMAT_CAPPED_2K, "mkv"),
    "capped_2k": (FORMAT_CAPPED_2K, "mkv"),
    "raw": (FORMAT_RAW_1080, "mp4"),
}

QUALITY_SPEEDTEST_URL = "https://speed.cloudflare.com/__down?bytes=25000000"
QUALITY_SPEEDTEST_WINDOW_SECONDS = 2.5
QUALITY_SPEEDTEST_THRESHOLD_MBPS = 80
QUALITY_FAST_LINE_THRESHOLD_MBPS = 200
QUALITY_SHORT_VIDEO_SECONDS = 300
QUALITY_LIGHT_VIDEO_SECONDS = 180
QUALITY_LONG_VIDEO_SECONDS = 3600
QUALITY_EXTENDED_VIDEO_SECONDS = 10800

MEDIUM_COMPRESS_ARGS = {
    "hevc_nvenc": ["-c:v", "hevc_nvenc", "-preset", "p6", "-tune", "hq", "-rc", "vbr", "-cq", "29",
                   "-spatial_aq", "1", "-temporal_aq", "1", "-rc-lookahead", "32",
                   "-b_ref_mode", "middle", "-pix_fmt", "yuv420p"],
    "hevc_amf": ["-c:v", "hevc_amf", "-quality", "quality", "-rc", "cqp", "-qp_i", "27", "-qp_p", "29",
                 "-qp_b", "31", "-vbaq", "true", "-preanalysis", "true", "-pix_fmt", "yuv420p"],
    "hevc_qsv": ["-c:v", "hevc_qsv", "-preset", "slower", "-global_quality", "29",
                 "-look_ahead", "1", "-pix_fmt", "nv12"],
    "libx264": ["-c:v", "libx264", "-preset", "medium", "-crf", "26", "-pix_fmt", "yuv420p"],
}

LIGHT_COMPRESS_ARGS = {
    "hevc_nvenc": ["-c:v", "hevc_nvenc", "-preset", "p6", "-tune", "hq", "-rc", "vbr", "-cq", "20",
                   "-spatial_aq", "1", "-temporal_aq", "1", "-rc-lookahead", "32",
                   "-b_ref_mode", "middle", "-pix_fmt", "yuv420p"],
    "hevc_amf": ["-c:v", "hevc_amf", "-quality", "quality", "-rc", "cqp", "-qp_i", "18", "-qp_p", "20",
                 "-qp_b", "22", "-vbaq", "true", "-preanalysis", "true", "-pix_fmt", "yuv420p"],
    "hevc_qsv": ["-c:v", "hevc_qsv", "-preset", "slower", "-global_quality", "20",
                 "-look_ahead", "1", "-pix_fmt", "nv12"],
    "libx264": ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p"],
}

COMPRESS_TIERS = {"light": LIGHT_COMPRESS_ARGS, "medium": MEDIUM_COMPRESS_ARGS}

HW_ENCODER_PROBE_ORDER = ["hevc_nvenc", "hevc_amf", "hevc_qsv"]


async def _ffmpeg_encoder_works(codec_args, timeout_seconds=8):
    probe_path = os.path.join(tempfile.gettempdir(), f"dld_hwprobe_{uuid.uuid4().hex}.mp4")
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=64x64:d=0.1",
            *codec_args, probe_path,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        try:
            await asyncio.wait_for(proc.wait(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            proc.kill()
            return False
        return proc.returncode == 0 and os.path.exists(probe_path) and os.path.getsize(probe_path) > 0
    except Exception:
        return False
    finally:
        try:
            os.remove(probe_path)
        except Exception:
            pass


async def probe_hw_encoder():
    """Пробует реально закодировать тестовый кадр каждым аппаратным энкодером по очереди
    (NVIDIA → AMD → Intel). Первый, который завёлся — то и есть железо на этой машине.
    Если не завёлся ни один (нет GPU/дров — обычное дело на голом VPS/в докере) — едем на CPU."""
    for encoder_name in HW_ENCODER_PROBE_ORDER:
        if await _ffmpeg_encoder_works(MEDIUM_COMPRESS_ARGS[encoder_name]):
            return encoder_name
    return "libx264"


EMOJI_QUEUE = "<tg-emoji emoji-id=5348557584418750233>🕒</tg-emoji>"


class QueueCancelled(Exception):
    """Пользователь (или кто угодно в чате) удалил сообщение об ожидании в очереди —
    отменяем эту загрузку, не начиная её."""
    pass


class DownloadCancelled(Exception):
    """.dlstop — юзер сам остановил активную загрузку."""
    pass


class DownloadTurnQueue:
    """FIFO-очередь с видимыми позициями и поддержкой отмены: пока ждёшь своей очереди,
    в статусе видно место (Видео в очереди(N)...). Если удалить это сообщение, ожидающий
    сам выпадает из очереди при следующей проверке, и следующие сдвигаются вперёд —
    защита от OOM (см. release/acquire) остаётся той же: тяжёлые загрузки строго по одной."""

    def __init__(self):
        self._waiters = []

    async def acquire(self, status_msg, message, position_text_fn):
        entry = {"event": asyncio.Event(), "status_msg": status_msg, "message": message}
        self._waiters.append(entry)
        if len(self._waiters) == 1:
            entry["event"].set()

        try:
            while True:
                if self._waiters and self._waiters[0] is entry and entry["event"].is_set():
                    return entry

                try:
                    await asyncio.wait_for(entry["event"].wait(), timeout=3)
                except asyncio.TimeoutError:
                    pass

                if entry not in self._waiters:
                    raise QueueCancelled()

                if self._waiters[0] is entry and entry["event"].is_set():
                    return entry

                position = self._waiters.index(entry)
                if position > 0:
                    if not await self._still_alive(entry):
                        self._waiters.remove(entry)
                        self._wake_front()
                        raise QueueCancelled()
                    try:
                        await status_msg.edit(position_text_fn(position))
                    except Exception:
                        pass
        except asyncio.CancelledError:
            if entry in self._waiters:
                self._waiters.remove(entry)
                self._wake_front()
            raise

    def release(self, entry):
        if entry in self._waiters:
            self._waiters.remove(entry)
        self._wake_front()

    def cancel_all(self, chat_id=None):
        """Убирает из очереди записи, которые ещё реально ЖДУТ своей очереди (не забрали
        event) — или только для chat_id, если он передан. Запись активной загрузки
        acquire() не убирает из _waiters при выдаче хода (она там и остаётся, просто с
        set() событием, как "текущий фронт"), поэтому без фильтра по event.is_set() тут
        задваивался счёт с _active_jobs в .dlstop — одна и та же загрузка считалась
        и активной, и стоящей в очереди одновременно."""
        removed = []
        for entry in list(self._waiters):
            if entry["event"].is_set():
                continue
            if chat_id is not None and getattr(entry["message"], "chat_id", None) != chat_id:
                continue
            self._waiters.remove(entry)
            entry["event"].set()
            removed.append(entry)
        self._wake_front()
        return removed

    def _wake_front(self):
        if self._waiters:
            self._waiters[0]["event"].set()

    async def _still_alive(self, entry):
        try:
            check_id = entry["status_msg"].id or entry["message"].id
            result = await entry["message"].client.get_messages(entry["message"].chat_id, ids=check_id)
            return result is not None
        except Exception:
            return True


async def target_still_exists(message, status_msg):
    """Проверяет, что сообщение(-я), к которым привязана загрузка, всё ещё существуют — если
    юзер (или кто угодно в чате) удалил команду/статус посреди скачивания, не будем ни
    переводить озвучку, ни слать готовое видео в пустоту."""
    try:
        check_id = status_msg.id or message.id
        result = await message.client.get_messages(message.chat_id, ids=check_id)
        return result is not None
    except Exception:
        return True


class _MutedStatus:
    """Заглушка вместо статус-сообщения для тихого авторезюма после краша: .edit()/.delete()
    просто ничего не делают, чтобы весь обычный код (update_status, quality_downloading и т.д.)
    работал без единой правки, но ни одного нового сообщения в чат не улетало."""
    id = None

    async def edit(self, *args, **kwargs):
        return None

    async def delete(self, *args, **kwargs):
        return None


async def compress_video(input_path, encoder_key, tier="medium", duration_hint=None, on_progress=None, cancel_event=None):
    """Перегоняет видео в HEVC (или H.264 на софте) по выбранному пресету, аудио — в AAC.
    Возвращает путь к новому файлу или None, если сжатие не удалось (тогда шлём как скачалось).
    Довешивает safety-фильтр на чётность сторон — нечётная высота/ширина (нередко у вертикальных
    Shorts) иначе может отправить кодировщик в артефакты или вовсе уронить его.
    on_progress(eta_seconds) — тот же принцип, что и для скачивания: -progress pipe:1 отдаёт
    машиночитаемый прогресс (out_time_ms, speed), по ним считаем оставшееся время и троттлим
    коллбек до раза в 3 секунды, чтобы не долбить правками сообщения.
    cancel_event — .dlstop: раньше отмена проверялась только внутри yt-dlp прогресс-хука,
    то есть только во время самого скачивания — если юзер жал .dlstop уже на этапе сжатия,
    ничего не происходило, и видео всё равно прилетало через несколько секунд."""
    preset_args = COMPRESS_TIERS.get(tier, MEDIUM_COMPRESS_ARGS)
    args = preset_args.get(encoder_key, preset_args["libx264"])
    output_path = os.path.splitext(input_path)[0] + "_compressed.mp4"

    duration_total = None
    if duration_hint:
        try:
            duration_total = float(duration_hint)
        except (TypeError, ValueError):
            duration_total = None
    if not duration_total:
        duration_total = await probe_media_duration(input_path)

    use_progress = bool(on_progress and duration_total and duration_total > 0)

    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-i", input_path,
        *args,
        "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
        "-c:a", "aac", "-b:a", "192k",
        *(["-progress", "pipe:1", "-nostats"] if use_progress else []),
        output_path,
        stdout=asyncio.subprocess.PIPE if use_progress else asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )

    if use_progress:
        last_ts = 0.0
        out_time_seconds = 0.0
        speed = 1.0
        while True:
            if cancel_event is not None and cancel_event.is_set():
                try:
                    proc.kill()
                except Exception:
                    pass
                try:
                    os.remove(output_path)
                except Exception:
                    pass
                raise DownloadCancelled()
            try:
                line = await asyncio.wait_for(proc.stdout.readline(), timeout=1)
            except asyncio.TimeoutError:
                continue
            if not line:
                break
            try:
                text = line.decode("utf-8", "ignore").strip()
            except Exception:
                continue
            if "=" not in text:
                continue
            key, _, value = text.partition("=")
            if key == "out_time_ms":
                try:
                    out_time_seconds = max(0, int(value)) / 1_000_000
                except ValueError:
                    pass
            elif key == "out_time":
                out_time_seconds = format_seconds_to_number(value) or out_time_seconds
            elif key == "speed":
                try:
                    speed = float(value.rstrip("x")) or speed
                except ValueError:
                    pass
            elif key == "progress" and value == "end":
                break

            now = time.monotonic()
            if now - last_ts < 3:
                continue
            remaining = max(0, duration_total - out_time_seconds)
            if speed <= 0:
                continue
            eta_seconds = remaining / speed
            last_ts = now
            try:
                await on_progress(eta_seconds)
            except Exception:
                pass

    await proc.wait()

    if proc.returncode != 0 or not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        try:
            os.remove(output_path)
        except Exception:
            pass
        return None

    if not await has_video_stream(output_path):
        try:
            os.remove(output_path)
        except Exception:
            pass
        return None

    try:
        os.remove(input_path)
    except Exception:
        pass
    return output_path


async def has_video_stream(path):
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=codec_type", "-of", "csv=p=0", path,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await proc.communicate()
        return bool(stdout.decode().strip())
    except Exception:
        return True


async def probe_media_duration(path):
    """ffprobe-длительность файла в секундах (для ETA сжатия, если duration неизвестна заранее)."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", path,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await proc.communicate()
        return float(stdout.decode().strip())
    except Exception:
        return None


def format_seconds_to_number(hms):
    """'HH:MM:SS.micro' -> секунды (float). Формат ffmpeg -progress out_time."""
    try:
        parts = hms.strip().split(":")
        if len(parts) != 3:
            return None
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    except Exception:
        return None


_speedtest_cache = {"ts": 0.0, "mbps": None}
SPEEDTEST_CACHE_TTL_SECONDS = 300


async def measure_download_speed_mbps(window_seconds=QUALITY_SPEEDTEST_WINDOW_SECONDS):
    """Короткий (~2.5 сек) замер входящей скорости — качаем кусок с Cloudflare, считаем Мбит/с.
    Результат кэшируется на 5 минут: на одном и том же сервере скорость между двумя видео
    подряд почти не меняется, а качать по 25 МБ под каждую ссылку — трата времени/трафика."""
    now = time.monotonic()
    if _speedtest_cache["mbps"] is not None and now - _speedtest_cache["ts"] < SPEEDTEST_CACHE_TTL_SECONDS:
        return _speedtest_cache["mbps"]
    try:
        total_bytes = 0
        loop = asyncio.get_event_loop()
        start = loop.time()
        timeout = aiohttp.ClientTimeout(total=window_seconds + 5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(QUALITY_SPEEDTEST_URL) as resp:
                async for chunk in resp.content.iter_chunked(65536):
                    total_bytes += len(chunk)
                    if loop.time() - start >= window_seconds:
                        break
        elapsed = loop.time() - start
        if elapsed <= 0 or total_bytes == 0:
            return None
        mbps = (total_bytes * 8) / elapsed / 1_000_000
        _speedtest_cache["ts"] = time.monotonic()
        _speedtest_cache["mbps"] = mbps
        return mbps
    except Exception:
        return None


_probe_cache = {}
PROBE_CACHE_TTL_SECONDS = 600


async def quick_probe_duration(url, timeout_seconds=6):
    """Лёгкий пик метаданных без скачивания — узнаём длительность видео заранее,
    чтобы решить, нужен ли спидтест вообще и не отвалиться по лимиту потом.
    Результат кэшируется на 10 минут — повторная загрузка той же ссылки не пингует YouTube снова."""
    now = time.monotonic()
    cached = _probe_cache.get(url)
    if cached is not None and now - cached[0] < PROBE_CACHE_TTL_SECONDS:
        return cached[1]

    def _extract():
        opts = {"quiet": True, "no_warnings": True, "skip_download": True, "noplaylist": True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get("duration")

    try:
        duration = await asyncio.wait_for(asyncio.to_thread(_extract), timeout=timeout_seconds)
    except Exception:
        return None
    _probe_cache[url] = (time.monotonic(), duration)
    if len(_probe_cache) > 200:
        _probe_cache.clear()
    return duration


async def probe_playlist_entries(url, cookies_text=None, proxy=None, max_entries=50, timeout_seconds=30):
    """Плоский список роликов внутри плейлиста (YouTube) — flat-экстракт без скачивания
    каждого элемента. Возвращает [{url, title}, ...], None — если это не плейлист/ничего
    не удалось достать, или список из 1 элемента — тогда вызывающий идёт обычным путём."""
    cookiefile = None
    if cookies_text and cookies_text.strip():
        cookiefile = os.path.join(tempfile.gettempdir(), f"pl_cookies_{uuid.uuid4().hex}.txt")
        with open(cookiefile, "w", encoding="utf-8") as f:
            f.write(cookies_text.strip())

    def _extract():
        opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": False,
            "extract_flat": "in_playlist",
            "playlistend": max_entries,
        }
        if cookiefile:
            opts["cookiefile"] = cookiefile
        if proxy:
            opts["proxy"] = proxy
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        entries = info.get("entries") if isinstance(info, dict) else None
        if not entries:
            return None
        out = []
        for e in entries:
            if not e:
                continue
            entry_url = e.get("url") or e.get("webpage_url")
            if not entry_url:
                continue
            if not entry_url.startswith("http"):
                entry_url = "https://www.youtube.com/watch?v=" + entry_url
            out.append({"url": entry_url, "title": e.get("title")})
        return out or None

    try:
        return await asyncio.wait_for(asyncio.to_thread(_extract), timeout=timeout_seconds)
    except Exception:
        return None
    finally:
        if cookiefile:
            try:
                os.remove(cookiefile)
            except Exception:
                pass


async def probe_title_channel(url, cookies_text=None, timeout_seconds=8):
    """Лёгкий пик title/channel без скачивания — иногда метаданные доступны, даже когда
    сама медиа-загрузка упирается в куки. Пригождается для фолбека через @SaveAsBot,
    чтобы оформить итог как обычно (название, канал), а не голым файлом."""
    cookiefile = None

    def _extract():
        opts = {"quiet": True, "no_warnings": True, "skip_download": True, "noplaylist": True}
        if cookiefile:
            opts["cookiefile"] = cookiefile
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get("title")
            channel = info.get("uploader") or info.get("channel") or info.get("uploader_id")
            if channel:
                channel = channel.lstrip("@")
            return title, channel

    try:
        if cookies_text and cookies_text.strip():
            cookiefile = os.path.join(tempfile.gettempdir(), f"probe_cookies_{uuid.uuid4().hex}.txt")
            with open(cookiefile, "w", encoding="utf-8") as f:
                f.write(cookies_text.strip())
        return await asyncio.wait_for(asyncio.to_thread(_extract), timeout=timeout_seconds)
    except Exception:
        return None, None
    finally:
        if cookiefile:
            try:
                os.remove(cookiefile)
            except Exception:
                pass


async def fetch_og_preview(url, timeout_seconds=8):
    """Если метаданные вообще никак не достать (ссылка "не бьётся" совсем даже для пика) —
    последний резерв: тянем og:title/og:description прямо со страницы, как это делает
    предпросмотр ссылок в Telegram."""
    try:
        timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(url) as resp:
                status = resp.status
                html = await resp.text(errors="ignore")
    except Exception as fetch_err:
        logger.warning(f"fetch_og_preview: request failed for {url}: {fetch_err}")
        return None, None

    def _meta(prop):
        m = re.search(
            rf'<meta[^>]+property=["\']og:{prop}["\'][^>]+content=["\']([^"\']*)["\']', html, re.IGNORECASE
        )
        if not m:
            m = re.search(
                rf'<meta[^>]+content=["\']([^"\']*)["\'][^>]+property=["\']og:{prop}["\']', html, re.IGNORECASE
            )
        return m.group(1).strip() if m else None

    title, desc = _meta("title"), _meta("description")
    if not title and not desc:
        logger.warning(f"fetch_og_preview: no og:title/description found for {url} (status={status}, len={len(html)})")

    return title, desc


async def decide_quality_mode(is_short, duration, auto_quality_enabled, is_discord, audio_only):
    """Решает, в каком режиме качать видео: standard / best / capped_2k.
    Принимает уже вычисленные is_short/duration снаружи — чтобы не пинговать yt-dlp дважды
    (длительность и так нужна отдельно для выбора пресета сжатия, light/medium).

    Правила:
    - Выключено в конфиге, Discord-ссылка или качаем только аудио → всегда standard.
    - Shorts — всегда standard, старым способом, без сжатия. На практике их "улучшенное"
      2K-качество почему-то выходило хуже обычного (похоже на заниженный битрейт у формата
      без потолка на коротких вертикальных роликах) — не разбираясь глубже, проще откатить.
    - Ролик до 5 минут (но не Shorts) → best, спидтест не нужен (мелочь, скорость не важна).
    - Длительность не удалось узнать → standard (перестраховка, вдруг это многочасовое видео).
    - 200+ Мбит/с стабильно и ролик до 3 часов → capped_2k (2K, при отсутствии — 1080p).
    - 80+ Мбит/с стабильно и ролик до 1 часа → best (без потолка разрешения).
    - Иначе → standard.
    """
    if not auto_quality_enabled or is_discord or audio_only or is_short:
        return "standard"

    if duration is not None and duration <= QUALITY_SHORT_VIDEO_SECONDS:
        return "best"

    if duration is None:
        return "standard"

    speed = await measure_download_speed_mbps()
    if speed is None:
        return "standard"

    if speed >= QUALITY_FAST_LINE_THRESHOLD_MBPS and duration <= QUALITY_EXTENDED_VIDEO_SECONDS:
        return "capped_2k"

    if speed >= QUALITY_SPEEDTEST_THRESHOLD_MBPS and duration <= QUALITY_LONG_VIDEO_SECONDS:
        return "best"

    return "standard"

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
  if (typeof result.remainingTime === "number") {
    console.log(JSON.stringify({ progress: true, remainingTime: result.remainingTime }));
  }

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
    if (typeof result.remainingTime === "number") {
      console.log(JSON.stringify({ progress: true, remainingTime: result.remainingTime }));
    }
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


class NodeVersionError(Exception):
    """Отдельный тип ошибки для проблем с версией Node.js — несёт готовый HTML с инструкцией
    по .terminal, чтобы вызывающий код показал её отдельным, не исчезающим сообщением."""
    def __init__(self, html_message):
        self.html_message = html_message
        super().__init__(html_message)


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

    has_n = bool(shutil.which("n"))

    if not has_n:
        proc = await asyncio.create_subprocess_exec(
            "npm", "i", "-g", "n",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        has_n = proc.returncode == 0 and bool(shutil.which("n"))

        if not has_n:
            raise NodeVersionError(
                f"{EMOJI_WARN} <b>Перевод не удался: нужна более новая версия Node.js ({minimum}+).</b>\n\n"
                f"Введите по очереди:\n<code>.terminal npm i -g n</code>\n<code>.terminal n latest</code>"
            )

    proc = await asyncio.create_subprocess_exec(
        "n", "latest",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    await proc.communicate()

    await asyncio.sleep(10)
    new_major = await get_node_major_version()

    if new_major is None or new_major < minimum:
        raise NodeVersionError(
            f"{EMOJI_WARN} <b>Перевод не удался: нужна более новая версия Node.js ({minimum}+).</b>\n\n"
            f"Введите:\n<code>.terminal n latest</code>"
        )


async def get_translated_audio(video_url, response_lang="ru", max_wait_seconds=180, on_progress=None):
    script_path = await ensure_vot_bridge_ready()

    proc = await asyncio.create_subprocess_exec(
        "node", script_path, video_url, response_lang, str(max_wait_seconds),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    result = None
    last_line = ""
    while True:
        line = await proc.stdout.readline()
        if not line:
            break
        try:
            text = line.decode("utf-8", "ignore").strip()
        except Exception:
            continue
        if not text:
            continue
        last_line = text
        try:
            parsed = json.loads(text)
        except Exception:
            continue
        if parsed.get("progress") and on_progress:
            remaining = parsed.get("remainingTime")
            if remaining is not None:
                try:
                    await on_progress(remaining)
                except Exception:
                    pass
            continue
        result = parsed

    stderr = await proc.stderr.read()
    await proc.wait()

    if result is None:
        try:
            result = json.loads(last_line)
        except Exception:
            raise Exception(f"Не удалось разобрать ответ моста озвучки: {stderr.decode()[:300] or last_line[:300]}")

    if not result.get("ok"):
        raise Exception(result.get("error", "неизвестная ошибка озвучки"))

    return result["url"], result.get("title")


async def extract_audio_from_video(video_path, output_dir):
    """Вырезает звуковую дорожку из локального видеофайла в mp3. Для случая "реплай на
    видео в чате (без ссылки) + -a" — там качать через yt-dlp нечего, звук вырезаем из
    самого видеофайла, который уже есть в Telegram."""
    output_path = os.path.join(output_dir, f"{uuid.uuid4()}.mp3")
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-i", video_path, "-vn", "-c:a", "libmp3lame", "-q:a", "2",
        output_path,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()
    if proc.returncode != 0 or not os.path.isfile(output_path) or os.path.getsize(output_path) == 0:
        try:
            os.remove(output_path)
        except Exception:
            pass
        return None
    return output_path


async def mux_translated_audio(video_path, audio_url, orig_volume_percent=50, clip_start=None):
    output_path = video_path + ".vo.mp4"
    audio_temp = video_path + ".vo_audio.tmp"

    async with aiohttp.ClientSession() as session:
        async with session.get(audio_url) as resp:
            async with aiofiles.open(audio_temp, "wb") as f:
                async for chunk in resp.content.iter_chunked(8192):
                    await f.write(chunk)

    extra_gain = max(0, min(100, orig_volume_percent)) / 100

    audio_seek_args = ["-ss", str(clip_start)] if clip_start else []

    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y",
        "-i", video_path,
        *audio_seek_args, "-i", audio_temp,
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
    video_url = data.get("hdplay") or data.get("play")
    if not video_url:
        raise Exception("tikwm не вернул ссылку на видео")

    title = data.get("title") or "TikTok"
    author = ((data.get("author") or {}).get("nickname")) or None
    file_path = await download_file(video_url, output_dir, "mp4")

    return file_path, title, author


async def download_tiktok_audio_via_api(url, output_dir):
    data = await tikwm_lookup(url)
    music_url = data.get("music")
    if not music_url:
        raise Exception("tikwm не вернул ссылку на аудио")

    title = (data.get("music_info") or {}).get("title") or data.get("title") or "TikTok"
    author = ((data.get("author") or {}).get("nickname")) or None
    file_path = await download_file(music_url, output_dir, "mp3")

    return file_path, title, author


DISCORD_RE = re.compile(
    r"https?://(?:cdn\.discordapp\.com|media\.discordapp\.net)/attachments/(\d+)/\d+/[^\s?]+\.(\w+)(?:\?[^\s]*)?",
    re.IGNORECASE,
)


async def download_discord_video(url, output_dir):
    match = DISCORD_RE.search(url)
    channel_id = match.group(1) if match else None
    ext = match.group(2) if match else "mp4"
    filename = url.split("/")[-1].split("?")[0]

    file_path = await download_file(url, output_dir, ext)
    title = filename
    channel = f"#{channel_id}" if channel_id else None
    return file_path, title, channel


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


async def download_instagram_carousel(url, output_dir, cookies_text=None, proxy=None):
    """Instagram-карусель (несколько фото/видео в одном посте) — yt-dlp отдаёт её как playlist
    с несколькими entries. Обычный noplaylist=True, что используется для одиночных постов,
    тут не подходит — он либо хватает только первый элемент, либо (судя по багрепорту) роняет
    всё с ошибкой про куки. Возвращает список путей к файлам, или None если пост не карусель
    (обычный одиночный пост/reel — пусть идёт по старому, обычному пути)."""
    cookiefile = None
    if cookies_text and cookies_text.strip():
        cookiefile = os.path.join(output_dir, f"ig_cookies_{uuid.uuid4().hex}.txt")
        with open(cookiefile, "w", encoding="utf-8") as f:
            f.write(cookies_text.strip())

    random_uuid = uuid.uuid4().hex
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": False,
        "outtmpl": os.path.join(output_dir, f"ig_{random_uuid}_%(playlist_index)s.%(ext)s"),
    }
    if cookiefile:
        ydl_opts["cookiefile"] = cookiefile
    if proxy:
        ydl_opts["proxy"] = proxy

    def _extract_and_download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=True)

    try:
        info = await asyncio.wait_for(asyncio.to_thread(_extract_and_download), timeout=180)
    finally:
        if cookiefile:
            try:
                os.remove(cookiefile)
            except Exception:
                pass

    entries = info.get("entries") if info else None
    if not entries or len(entries) < 2:
        return None

    files = []
    for entry in entries:
        if not entry:
            continue
        for rd in entry.get("requested_downloads") or []:
            fp = rd.get("filepath")
            if fp and os.path.exists(fp):
                files.append(fp)

    return files or None


YANDEX_MUSIC_SIGN_KEY = "7tvSmFbyf5hJnIHhCimDDD"

YANDEX_MUSIC_TRACK_RE = re.compile(
    r"music\.yandex\.(?:ru|com|by|kz|ua)/album/\d+/track/(\d+)", re.IGNORECASE
)
YANDEX_MUSIC_TRACK_ONLY_RE = re.compile(
    r"music\.yandex\.(?:ru|com|by|kz|ua)/track/(\d+)", re.IGNORECASE
)
YANDEX_MUSIC_ALBUM_RE = re.compile(
    r"music\.yandex\.(?:ru|com|by|kz|ua)/album/(\d+)(?:/|$|\?)", re.IGNORECASE
)
YANDEX_MUSIC_PLAYLIST_RE = re.compile(
    r"music\.yandex\.(?:ru|com|by|kz|ua)/users/([^/]+)/playlists/(\d+)", re.IGNORECASE
)
YANDEX_MUSIC_PLAYLIST_UUID_RE = re.compile(
    r"music\.yandex\.(?:ru|com|by|kz|ua)/playlists/([0-9a-fA-F-]{36})", re.IGNORECASE
)


def extract_yandex_track_id(url):
    if not url:
        return None
    m = YANDEX_MUSIC_TRACK_RE.search(url)
    if m:
        return m.group(1)
    m = YANDEX_MUSIC_TRACK_ONLY_RE.search(url)
    if m:
        return m.group(1)
    return None


def extract_yandex_album_id(url):
    if not url or extract_yandex_track_id(url):
        return None
    m = YANDEX_MUSIC_ALBUM_RE.search(url or "")
    return m.group(1) if m else None


def extract_yandex_playlist(url):
    m = YANDEX_MUSIC_PLAYLIST_RE.search(url or "")
    return (m.group(1), m.group(2)) if m else None


def extract_yandex_playlist_uuid(url):
    m = YANDEX_MUSIC_PLAYLIST_UUID_RE.search(url or "")
    return m.group(1) if m else None


def parse_netscape_cookies(cookies_text, domain_filter=None):
    """Парсит cookies.txt в Netscape-формате (тот же, что и youtube_cookies) и отдаёт
    {name: value}, отфильтрованный по вхождению domain_filter в поле домена."""
    cookies = {}
    if not cookies_text:
        return cookies
    for line in cookies_text.splitlines():
        line = line.rstrip("\r\n")
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 7:
            parts = line.split()
        if len(parts) < 7:
            continue
        if len(parts) > 7:
            parts = parts[:6] + [" ".join(parts[6:])]
        if parts[0] == "#":
            continue
        domain, _flag, _path, _secure, _expiry, name, value = parts[:7]
        if domain_filter and domain_filter not in domain.lower():
            continue
        cookies[name] = value
    return cookies


def _yandex_music_sign(payload):
    digest = hmac.new(YANDEX_MUSIC_SIGN_KEY.encode(), payload.encode(), hashlib.sha256).digest()
    return base64.b64encode(digest).decode().rstrip("=")


def _iter_mp4_boxes(data, start, end):
    pos = start
    while pos + 8 <= end:
        size = struct.unpack(">I", data[pos:pos + 4])[0]
        btype = data[pos + 4:pos + 8].decode("latin1")
        data_start = pos + 8
        if size == 1:
            if pos + 16 > end:
                break
            size = struct.unpack(">Q", data[pos + 8:pos + 16])[0]
            data_start = pos + 16
        elif size == 0:
            size = end - pos
        if size < 8 or pos + size > end:
            break
        yield btype, pos, size, data_start
        pos += size


_MP4_CONTAINER_BOXES = {"moov", "trak", "mdia", "minf", "stbl", "udta", "edts", "mvex", "moof", "traf"}


def _find_mp4_box(data, start, end, target):
    for btype, box_start, size, data_start in _iter_mp4_boxes(data, start, end):
        if btype == target:
            return (box_start, size, data_start)
        if btype in _MP4_CONTAINER_BOXES:
            found = _find_mp4_box(data, data_start, box_start + size, target)
            if found:
                return found
    return None


def demux_flac_from_mp4(data):
    """Яндекс.Музыка отдаёт lossless-поток завёрнутым в MP4-контейнер (codec 'flac-mp4') — тот
    же формат, что и расширение получает и распаковывает у себя в браузере (см. функцию me()
    в его content.js). Достаём raw FLAC: находим 'mdat' (сырые сэмплы) и 'dfLa' box внутри
    'stsd' (там лежат оригинальные FLAC metadata-блоки, включая STREAMINFO), склеиваем.
    Упрощение относительно расширения: сэмплы берём из mdat одним куском по смещению/размеру
    (без разбора stsz/stsc/stco) — для одиночного аудиотрека (один run, не фрагментированный
    moof/mfra) сэмплы и так лежат в mdat подряд, этого достаточно."""
    n = len(data)
    mdat = _find_mp4_box(data, 0, n, "mdat")
    if not mdat:
        raise ValueError("mdat box not found")
    mdat_start, mdat_size, mdat_data_start = mdat

    stsd = _find_mp4_box(data, 0, n, "stsd")
    if not stsd:
        raise ValueError("stsd box not found")
    stsd_start, stsd_size, stsd_data_start = stsd
    sample_entries_start = stsd_data_start + 4 + 4
    sample_entries_end = stsd_start + stsd_size

    flac_entry = None
    for btype, box_start, size, data_start in _iter_mp4_boxes(data, sample_entries_start, sample_entries_end):
        if btype == "fLaC":
            flac_entry = (box_start, size, data_start)
            break
    if not flac_entry:
        raise ValueError("fLaC sample entry not found in stsd")
    flac_start, flac_size, flac_data_start = flac_entry

    dfla = None
    search_end = flac_start + flac_size
    pos = flac_data_start
    while pos + 8 <= search_end:
        if data[pos + 4:pos + 8] == b"dfLa":
            box_size = struct.unpack(">I", data[pos:pos + 4])[0]
            if box_size >= 8 and pos + box_size <= search_end:
                dfla = (pos, box_size, pos + 8)
            break
        pos += 1
    if not dfla:
        raise ValueError("dfLa box not found")
    dfla_start, dfla_size, dfla_data_start = dfla

    meta_start = dfla_data_start + 4
    meta_end = dfla_start + dfla_size
    meta_bytes = data[meta_start:meta_end]
    if not meta_bytes:
        raise ValueError("empty FLAC metadata in dfLa")

    blocks = []
    pos2 = 0
    while pos2 + 4 <= len(meta_bytes):
        header_byte = meta_bytes[pos2]
        block_len = (meta_bytes[pos2 + 1] << 16) | (meta_bytes[pos2 + 2] << 8) | meta_bytes[pos2 + 3]
        total = 4 + block_len
        if pos2 + total > len(meta_bytes):
            break
        blocks.append(bytearray(meta_bytes[pos2:pos2 + total]))
        pos2 += total
        if header_byte & 0x80:
            break
    if not blocks:
        raise ValueError("no FLAC metadata blocks parsed from dfLa")

    for b in blocks[:-1]:
        b[0] &= 0x7F
    blocks[-1][0] |= 0x80

    flac_bytes = b"fLaC" + b"".join(bytes(b) for b in blocks) + data[mdat_data_start:mdat_start + mdat_size]
    return flac_bytes


async def download_yandex_music_track(url, output_dir, cookies_text=None, prefer_flac=False):
    """Скачивание трека Яндекс.Музыки через их же неофициальный web-API — теми же запросами
    (get-file-info с HMAC-подписью), что использует расширение Yandex Music Downloader.
    yt-dlp с Я.Музыкой почти не справляется: без залогиненного аккаунта отдаёт максимум
    превью на 30-60 секунд. Нужны куки залогиненного аккаунта music.yandex.* — берутся из
    той же настройки youtube_cookies (это просто общий cookies.txt, туда можно добавить куки
    с любых доменов, не только YouTube). prefer_flac=True — пробуем lossless (MP4-обёрнутый
    FLAC, распаковываем сами), если недоступно — тихий фолбек на mp3 320."""
    track_id = extract_yandex_track_id(url)
    if not track_id:
        raise ValueError("Не удалось определить ID трека из ссылки Яндекс.Музыки")

    yandex_cookies = parse_netscape_cookies(cookies_text, domain_filter="yandex")
    if not yandex_cookies:
        raw_len = len(cookies_text) if cookies_text else 0
        raw_has_word = "yandex" in (cookies_text or "").lower()
        raise ValueError(
            "Нужны куки залогиненного аккаунта music.yandex.ru — добавьте их в youtube_cookies "
            "(команда .cfg YouTube-DLD youtube_cookies). "
            f"[диагностика: конфиг прочитан, длина {raw_len} симв., слово 'yandex' в тексте: "
            f"{'есть' if raw_has_word else 'НЕТ'}, распознано строк кук: 0]"
        )

    cookie_header = "; ".join(f"{k}={v}" for k, v in yandex_cookies.items())
    api_headers = {
        "x-yandex-music-client": "YandexMusicWebNext/1.0.0",
        "x-yandex-music-without-invocation-info": "1",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://music.yandex.ru/",
        "Cookie": cookie_header,
    }

    async with aiohttp.ClientSession() as session:
        title, artist, album = "Unknown Track", "Unknown Artist", None
        cover_bytes = None
        duration_sec = 0
        meta_debug = None
        try:
            meta_headers = dict(api_headers, **{"Content-Type": "application/x-www-form-urlencoded"})
            async with session.post(
                "https://api.music.yandex.ru/tracks",
                data=f"trackIds={track_id}&removeDuplicates=false&withProgress=true",
                headers=meta_headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status == 200:
                    meta_json = await resp.json(content_type=None)
                    result = meta_json.get("result") if isinstance(meta_json, dict) else meta_json
                    track_meta = (result or [None])[0]
                    if track_meta:
                        title = track_meta.get("title") or title
                        artists = track_meta.get("artists") or []
                        artist_names = ", ".join(a.get("name", "") for a in artists if a.get("name"))
                        artist = artist_names or artist
                        duration_sec = int((track_meta.get("durationMs") or 0) / 1000)

                        albums = track_meta.get("albums") or []
                        album = (albums[0].get("title") if albums else None) or album
                        cover_uri = track_meta.get("coverUri") or (albums[0].get("coverUri") if albums else None)
                        if cover_uri:
                            cover_url = "https://" + cover_uri.replace("%%", "400x400")
                            try:
                                async with session.get(cover_url, timeout=aiohttp.ClientTimeout(total=15)) as cover_resp:
                                    if cover_resp.status == 200:
                                        cover_bytes = await cover_resp.read()
                            except Exception as cover_err:
                                logger.warning(f"Yandex Music: cover fetch failed: {cover_err}")
                    else:
                        meta_debug = "пустой result"
                else:
                    meta_debug = f"HTTP {resp.status}"
        except Exception as meta_err:
            meta_debug = str(meta_err)[:150]
            logger.warning(f"Yandex Music: metadata fetch failed: {meta_err}")

        async def fetch_stream_url(quality, codec, transport):
            ts = int(time.time())
            sign = _yandex_music_sign(f"{ts}{track_id}{quality}{codec}{transport}")
            file_info_url = (
                f"https://api.music.yandex.ru/get-file-info?ts={ts}&trackId={track_id}"
                f"&quality={quality}&codecs={codec}&transports={transport}&sign={urllib.parse.quote(sign)}"
            )
            async with session.get(file_info_url, headers=api_headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status != 200:
                    raise ValueError(f"Яндекс.Музыка API вернула {resp.status} — куки протухли или трек недоступен")
                info_json = await resp.json(content_type=None)
            download_info = (info_json or {}).get("downloadInfo") or {}
            stream_url = download_info.get("url")
            if not stream_url:
                raise ValueError("Яндекс.Музыка не отдала ссылку на поток — куки протухли или трек недоступен без подписки")
            return urllib.parse.unquote(stream_url)

        used_flac = False
        stream_bytes = None
        stream_url = None
        if prefer_flac:
            try:
                stream_url = await fetch_stream_url("lossless", "flac-mp4", "raw")
                async with session.get(stream_url, timeout=aiohttp.ClientTimeout(total=180)) as resp:
                    if resp.status != 200:
                        raise ValueError(f"HTTP {resp.status} при скачивании lossless-потока")
                    raw_bytes = await resp.read()
                stream_bytes = demux_flac_from_mp4(raw_bytes)
                used_flac = True
            except Exception as flac_err:
                logger.warning(f"Yandex Music: FLAC unavailable, falling back to mp3: {flac_err}")
                used_flac = False
                stream_bytes = None

        if not used_flac:
            stream_url = await fetch_stream_url("hq", "mp3", "raw")

        safe_name = re.sub(r'[\\/*?:"<>|]', "_", f"{artist} - {title}").strip()[:150] or track_id
        ext = "flac" if used_flac else "mp3"
        out_path = os.path.join(output_dir, f"{safe_name}.{ext}")

        if used_flac:
            async with aiofiles.open(out_path, "wb") as f:
                await f.write(stream_bytes)
        else:
            async with session.get(stream_url, timeout=aiohttp.ClientTimeout(total=180)) as resp:
                if resp.status != 200:
                    raise ValueError(f"Не удалось скачать сам файл трека (HTTP {resp.status})")
                async with aiofiles.open(out_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(1024 * 256):
                        await f.write(chunk)

    try:
        if used_flac:
            flac_tags = FLAC(out_path)
            flac_tags["title"] = title
            flac_tags["artist"] = artist
            if album:
                flac_tags["album"] = album
            if cover_bytes:
                pic = FlacPicture()
                pic.data = cover_bytes
                pic.type = 3
                pic.mime = "image/jpeg"
                flac_tags.clear_pictures()
                flac_tags.add_picture(pic)
            flac_tags.save()
            if not duration_sec:
                try:
                    duration_sec = int(flac_tags.info.length)
                except Exception:
                    pass
        else:
            try:
                tags = ID3(out_path)
            except ID3NoHeaderError:
                tags = ID3()
            tags["TIT2"] = TIT2(encoding=3, text=title)
            tags["TPE1"] = TPE1(encoding=3, text=artist)
            if album:
                tags["TALB"] = TALB(encoding=3, text=album)
            if cover_bytes:
                tags["APIC"] = APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=cover_bytes)
            tags.save(out_path)
            if not duration_sec:
                try:
                    duration_sec = int(MP3(out_path).info.length)
                except Exception:
                    pass
    except Exception as tag_err:
        logger.warning(f"Yandex Music: tagging failed: {tag_err}")

    return out_path, title, artist, album, duration_sec, cover_bytes, meta_debug


async def _yandex_cookie_header(cookies_text):
    yandex_cookies = parse_netscape_cookies(cookies_text, domain_filter="yandex")
    if not yandex_cookies:
        raise ValueError(
            "Нужны куки залогиненного аккаунта music.yandex.ru — добавьте их в youtube_cookies"
        )
    return yandex_cookies, "; ".join(f"{k}={v}" for k, v in yandex_cookies.items())


async def _yandex_oauth_from_cookies(cookies_text):
    yandex_cookies, cookie_header = await _yandex_cookie_header(cookies_text)
    session_id = yandex_cookies.get("Session_id") or yandex_cookies.get("sessionid2")
    if not session_id:
        return None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://mobileproxy.passport.yandex.net/1/bundle/oauth/token_by_sessionid",
                data={
                    "client_id": "c0ebe342af7d48fbbbfcf2d2eedb8f9e",
                    "client_secret": "ad0a908f0aa341a182a37ecd75bc319e",
                },
                headers={
                    "Ya-Client-Host": "passport.yandex.ru",
                    "Ya-Client-Cookie": f"Session_id={session_id}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json(content_type=None)
            x_token = (data or {}).get("access_token")
            if not x_token:
                return None
            async with session.post(
                "https://oauth.mobile.yandex.net/1/token",
                data={
                    "client_id": "23cabbbdc6cd418abb4b39c32c41195d",
                    "client_secret": "53bc75238f0c4d08a118e51fe9203300",
                    "grant_type": "x-token",
                    "access_token": x_token,
                },
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp2:
                if resp2.status != 200:
                    return x_token
                data2 = await resp2.json(content_type=None)
            return (data2 or {}).get("access_token") or x_token
    except Exception:
        return None


async def _yandex_api_headers(cookies_text):
    _, cookie_header = await _yandex_cookie_header(cookies_text)
    headers = {
        "x-yandex-music-client": "YandexMusicWebNext/1.0.0",
        "x-yandex-music-without-invocation-info": "1",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://music.yandex.ru/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Cookie": cookie_header,
    }
    oauth = await _yandex_oauth_from_cookies(cookies_text)
    if oauth:
        headers["Authorization"] = f"OAuth {oauth}"
    return headers


def _yandex_artists_line(obj):
    if not isinstance(obj, dict):
        return ""
    names = [a.get("name", "") for a in (obj.get("artists") or []) if isinstance(a, dict) and a.get("name")]
    return ", ".join(names)


def _yandex_playlist_debug_hint(result):
    if not isinstance(result, dict):
        return f" (result type={type(result).__name__})"
    tracks_val = result.get("tracks")
    parts = [
        f"trackCount={result.get('trackCount')}",
        f"tracks={'list[' + str(len(tracks_val)) + ']' if isinstance(tracks_val, list) else type(tracks_val).__name__}",
    ]
    if isinstance(tracks_val, list) and tracks_val and isinstance(tracks_val[0], dict):
        parts.append(f"item_keys={sorted(tracks_val[0].keys())}")
    parts.append(f"result_keys={sorted(result.keys())[:12]}")
    if not result:
        parts.append("raw=" + repr(result)[:300])
    return " (" + ", ".join(parts) + ")"


def _yandex_collect_track_ids(result):
    track_ids = []
    if not isinstance(result, dict):
        return track_ids
    for vol in (result.get("volumes") or []):
        for t in (vol or []):
            if isinstance(t, dict):
                tid = t.get("id") or t.get("realId")
                if tid is not None:
                    track_ids.append(str(tid).split(":")[0])
    if track_ids:
        return track_ids
    for t in (result.get("tracks") or []):
        if not isinstance(t, dict):
            continue
        track = t.get("track") if isinstance(t.get("track"), dict) else t
        tid = track.get("id") or track.get("realId") or t.get("id") or t.get("trackId")
        if tid is not None:
            track_ids.append(str(tid).split(":")[0])
    return track_ids


async def _yandex_get_json(session, url, headers):
    async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as resp:
        body = await resp.text()
        status = resp.status
    try:
        return status, json.loads(body)
    except Exception:
        return status, None


async def _yandex_download_cover(session, cover_uri):
    if not cover_uri:
        return None
    try:
        url = "https://" + str(cover_uri).replace("%%", "400x400")
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status == 200:
                return await resp.read()
    except Exception:
        pass
    return None


async def fetch_yandex_album_tracks(album_id, cookies_text=None):
    headers = await _yandex_api_headers(cookies_text)
    async with aiohttp.ClientSession() as session:
        for url in (
            f"https://api.music.yandex.ru/albums/{album_id}/with-tracks",
            f"https://api.music.yandex.ru/albums/{album_id}",
        ):
            status, data = await _yandex_get_json(session, url, headers)
            if status != 200 or not isinstance(data, dict):
                continue
            result = data.get("result", data)
            track_ids = _yandex_collect_track_ids(result)
            if track_ids:
                title = (result.get("title") if isinstance(result, dict) else None) or f"Album {album_id}"
                artists = _yandex_artists_line(result if isinstance(result, dict) else {})
                cover_bytes = await _yandex_download_cover(
                    session, result.get("coverUri") if isinstance(result, dict) else None
                )
                return title, artists, track_ids, cover_bytes

        page_url = f"https://music.yandex.ru/album/{album_id}"
        try:
            async with session.get(
                page_url,
                headers={
                    "User-Agent": headers.get("User-Agent", "Mozilla/5.0"),
                    "Cookie": headers.get("Cookie", ""),
                    "Referer": "https://music.yandex.ru/",
                },
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                html = await resp.text()
        except Exception:
            html = ""
        html_ids = re.findall(r'"id"\s*:\s*"?(\d{5,})"?\s*,\s*"realId"', html) or re.findall(r'/track/(\d+)', html)
        seen, track_ids = set(), []
        for tid in html_ids:
            if tid != str(album_id) and tid not in seen:
                seen.add(tid)
                track_ids.append(tid)
        if track_ids:
            return f"Album {album_id}", "", track_ids, None

    raise ValueError(
        "Не удалось получить треки альбома. Обновите куки music.yandex.ru "
        "(нужен Session_id; для списка треков требуется авторизация)"
    )


async def fetch_yandex_playlist_tracks(user, kind, cookies_text=None):
    headers = await _yandex_api_headers(cookies_text)
    url = f"https://api.music.yandex.ru/users/{urllib.parse.quote(user)}/playlists/{kind}"
    async with aiohttp.ClientSession() as session:
        status, data = await _yandex_get_json(session, url, headers)
        if status != 200 or not isinstance(data, dict):
            raise ValueError(
                "Не удалось получить плейлист. Обновите куки music.yandex.ru (нужен Session_id)"
            )
        result = data.get("result")
        if not isinstance(result, dict) or not result:
            result = data if isinstance(data, dict) else {}
        track_ids = _yandex_collect_track_ids(result)
        if not track_ids:
            raise ValueError("В плейлисте нет треков" + _yandex_playlist_debug_hint(result))
        title = result.get("title") or f"Playlist {kind}"
        owner = result.get("owner") or {}
        artists = owner.get("name") or owner.get("login") or ""
        cover_bytes = await _yandex_download_cover(session, result.get("coverUri") or result.get("ogImage"))
        return title, artists, track_ids, cover_bytes


async def fetch_yandex_playlist_by_uuid(playlist_uuid, cookies_text=None):
    headers = await _yandex_api_headers(cookies_text)
    url = f"https://api.music.yandex.ru/playlist/{playlist_uuid}"
    async with aiohttp.ClientSession() as session:
        status, data = await _yandex_get_json(session, url, headers)
        if status != 200 or not isinstance(data, dict):
            raise ValueError(
                "Не удалось получить плейлист. Обновите куки music.yandex.ru (нужен Session_id)"
            )
        result = data.get("result")
        if not isinstance(result, dict) or not result:
            result = data if isinstance(data, dict) else {}
        track_ids = _yandex_collect_track_ids(result)
        if not track_ids:
            raise ValueError("В плейлисте нет треков" + _yandex_playlist_debug_hint(result))
        title = result.get("title") or "Playlist"
        owner = result.get("owner") or {}
        artists = owner.get("name") or owner.get("login") or ""
        cover_bytes = await _yandex_download_cover(session, result.get("coverUri") or result.get("ogImage"))
        return title, artists, track_ids, cover_bytes


async def _yandex_stamp_cover(path, cover_bytes):
    """Вшивает обложку в mp3/flac. Сначала ffmpeg (как в Telegram/проводнике), иначе mutagen."""
    if not path or not cover_bytes or not os.path.isfile(path):
        return
    cover_path = path + ".cover.jpg"
    out_path = path + ".covtmp" + os.path.splitext(path)[1]
    try:
        async with aiofiles.open(cover_path, "wb") as cf:
            await cf.write(cover_bytes)
        is_mp3 = path.lower().endswith(".mp3")
        cmd = [
            "ffmpeg", "-y", "-i", path, "-i", cover_path,
            "-map", "0:a", "-map", "1", "-c", "copy",
        ]
        if is_mp3:
            cmd += ["-id3v2_version", "3"]
        cmd += [
            "-metadata:s:v", "title=Album cover",
            "-metadata:s:v", "comment=Cover (front)",
            "-disposition:v:0", "attached_pic",
            out_path,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        try:
            await asyncio.wait_for(proc.communicate(), timeout=60)
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            proc = None
        if proc is not None and proc.returncode == 0 and os.path.isfile(out_path):
            os.replace(out_path, path)
            return
        logger.warning(
            f"Yandex cover stamp: ffmpeg mux failed (code={proc.returncode if proc else 'timeout'}) "
            f"for {os.path.basename(path)}, falling back to mutagen"
        )
        if path.lower().endswith(".flac"):
            tags = FLAC(path)
            pic = FlacPicture()
            pic.data = cover_bytes
            pic.type = 3
            pic.mime = "image/jpeg"
            tags.clear_pictures()
            tags.add_picture(pic)
            tags.save()
        else:
            try:
                tags = ID3(path)
            except ID3NoHeaderError:
                tags = ID3()
            tags.delall("APIC")
            tags.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=cover_bytes))
            tags.save(path)
    except Exception as e:
        logger.warning(f"Yandex cover stamp failed: {e}")
    finally:
        for p in (cover_path, out_path):
            try:
                if os.path.isfile(p):
                    os.remove(p)
            except Exception:
                pass


async def _send_audio_album(client, entity, items, reply_to_id=None, silent=True):
    """Настоящий Telegram-альбом (messages.sendMultiMedia) с превью и атрибутами НА КАЖДОМ
    файле — одним чанком (до 10 штук). utils.answer_file/send_file с файлом-списком уходит в
    herokutl _send_album, а та не прокидывает thumb/attributes ни в один файл пачки, кроме
    случая одиночной отправки — поэтому в обычном пачечном send'е обложка и не показывалась
    нигде, кроме последнего трека, отправленного отдельным вызовом. Тут каждый файл проходит
    через client._file_to_media(..., attributes=, thumb=) индивидуально (ровно то же самое,
    что делает официальный клиент при перетаскивании нескольких файлов), и только потом всё
    собирается в один messages.sendMultiMedia. items: [{"path", "attributes", "thumb",
    "caption"}, ...] (caption обычно только у последнего)."""
    input_entity = await client.get_input_entity(entity)
    media_list = []
    for item in items:
        fh, fm, _ = await client._file_to_media(
            item["path"],
            attributes=item.get("attributes"),
            thumb=item.get("thumb"),
        )
        if isinstance(fm, InputMediaUploadedDocument):
            uploaded = await client(UploadMediaRequest(input_entity, media=fm))
            fm = herokutl_utils.get_input_media(uploaded.document)
        caption_html = item.get("caption") or ""
        if caption_html:
            caption_text, entities = await client._parse_message_text(caption_html, "HTML")
        else:
            caption_text, entities = "", None
        media_list.append(InputSingleMedia(fm, message=caption_text, entities=entities))
    request = SendMultiMediaRequest(
        input_entity,
        reply_to=InputReplyToMessage(reply_to_id) if reply_to_id else None,
        multi_media=media_list,
        silent=silent,
    )
    return await client(request)


def _ru_track_word(n):
    if n % 10 == 1 and n % 100 != 11:
        return "трек"
    if 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
        return "трека"
    return "треков"



async def download_yandex_track_by_id(track_id, output_dir, cookies_text=None, prefer_flac=False):
    fake_url = f"https://music.yandex.ru/track/{track_id}"
    return await download_yandex_music_track(
        fake_url, output_dir, cookies_text=cookies_text, prefer_flac=prefer_flac
    )


async def _resolve_input_peer(client, peer_id):
    try:
        return await client.get_input_entity(peer_id)
    except (ValueError, TypeError):
        await client.get_entity(peer_id)
        return await client.get_input_entity(peer_id)


async def get_dialog_archived(client, peer_id):
    """True/False — в архиве ли диалог с этим peer сейчас. None, если не удалось определить
    (тогда трогать архивное состояние вообще не будем — не рискуем перепутать)."""
    try:
        input_peer = await _resolve_input_peer(client, peer_id)
        result = await client(GetPeerDialogsRequest(peers=[InputDialogPeer(input_peer)]))
        if result.dialogs:
            return bool(getattr(result.dialogs[0], "folder_id", 0))
        return False
    except Exception:
        return None


async def get_dialog_muted(client, peer_id):
    """True/False — заглушен ли диалог с этим peer прямо сейчас (по mute_until в будущем).
    None, если не удалось определить."""
    try:
        input_peer = await _resolve_input_peer(client, peer_id)
        settings = await client(GetNotifySettingsRequest(peer=InputNotifyPeer(input_peer)))
        mute_until = getattr(settings, "mute_until", None)
        if not mute_until:
            return False
        return mute_until > int(time.time())
    except Exception:
        return None


async def set_dialog_muted(client, peer_id, muted):
    try:
        input_peer = await _resolve_input_peer(client, peer_id)
        mute_until = (2 ** 31 - 1) if muted else 0
        await client(UpdateNotifySettingsRequest(
            peer=InputNotifyPeer(input_peer),
            settings=InputPeerNotifySettings(mute_until=mute_until),
        ))
    except Exception:
        pass


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


STALE_DOWNLOAD_RE = re.compile(
    r"^(?:[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
    r"|ig_[0-9a-f]{32}"
    r"|ymcover_[0-9a-f]{8})"
)
STALE_DOWNLOAD_MAX_AGE = 60 * 60


def cleanup_stale_downloads(base_dir, max_age=STALE_DOWNLOAD_MAX_AGE):
    """Удаляет старые частичные файлы загрузок в base_dir. Возвращает число удалённых файлов."""
    removed = 0
    try:
        if not os.path.isdir(base_dir):
            return 0
        now = time.time()
        for fname in os.listdir(base_dir):
            if not STALE_DOWNLOAD_RE.match(fname):
                continue
            fpath = os.path.join(base_dir, fname)
            try:
                if os.path.isfile(fpath) and now - os.path.getmtime(fpath) > max_age:
                    os.remove(fpath)
                    removed += 1
            except Exception:
                continue
    except Exception:
        pass
    return removed


async def download_media(
    url,
    cookies_text=None,
    proxy=None,
    deno_path=None,
    max_attempts=MAX_DOWNLOAD_ATTEMPTS,
    audio_only=False,
    audio_codec="mp3",
    sponsorblock_categories=None,
    start_time=None,
    end_time=None,
    on_attempt=None,
    on_progress=None,
    quality_mode="standard",
    cancel_event=None,
):
    video_format, merge_format = QUALITY_FORMAT_MAP.get(quality_mode, QUALITY_FORMAT_MAP["standard"])
    progress_loop = asyncio.get_running_loop()
    last_progress_ts = [0.0]
    last_activity_ts = [time.monotonic()]
    speed_ema = [None]
    bytes_samples = []

    def progress_hook(d):
        if cancel_event is not None and cancel_event.is_set():
            raise DownloadCancelled()
        if d.get('status') != 'downloading':
            return
        last_activity_ts[0] = time.monotonic()
        if not on_progress:
            return
        now = time.monotonic()
        downloaded = d.get('downloaded_bytes') or 0
        total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
        speed = d.get('speed') or 0
        if downloaded and now:
            bytes_samples.append((now, downloaded))
            if len(bytes_samples) > 12:
                bytes_samples.pop(0)
            if len(bytes_samples) >= 2:
                t0, b0 = bytes_samples[0]
                dt = now - t0
                db = downloaded - b0
                if dt >= 0.8 and db > 0:
                    speed = db / dt
        if speed and speed > 0:
            speed_ema[0] = speed if speed_ema[0] is None else (0.35 * speed + 0.65 * speed_ema[0])
        if now - last_progress_ts[0] < 2.0:
            return
        eta = None
        avg = speed_ema[0]
        if avg and total and downloaded < total:
            eta = (total - downloaded) / avg
        elif d.get('eta') is not None:
            eta = float(d['eta'])
        if eta is None or eta < 3:
            return
        last_progress_ts[0] = now
        asyncio.run_coroutine_threadsafe(on_progress(eta), progress_loop)
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

                    if cancel_event is not None and cancel_event.is_set():
                        raise DownloadCancelled()

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
                                    'preferredcodec': audio_codec,
                                    'preferredquality': '320' if audio_codec != 'flac' else None,
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
                            'format': video_format,
                            'outtmpl': os.path.join(output_dir, f'{random_uuid}.%(ext)s'),
                            'noplaylist': True,
                            'merge_output_format': merge_format,
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
                        ydl_opts['force_keyframes_at_cuts'] = (quality_mode != "raw")

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

                    ydl_opts['progress_hooks'] = [progress_hook]

                    def _extract_and_download(ydl_opts=ydl_opts):
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            return ydl.extract_info(url, download=True)

                    try:
                        last_activity_ts[0] = time.monotonic()

                        async def _stall_watchdog():
                            while True:
                                await asyncio.sleep(1)
                                if time.monotonic() - last_activity_ts[0] > 10:
                                    return

                        download_future = asyncio.ensure_future(asyncio.to_thread(_extract_and_download))
                        watchdog_future = asyncio.ensure_future(_stall_watchdog())
                        done, _pending = await asyncio.wait(
                            {download_future, watchdog_future}, return_when=asyncio.FIRST_COMPLETED
                        )

                        if download_future in done:
                            watchdog_future.cancel()
                            info_dict = download_future.result()
                        else:
                            raise Exception("Timed Out")

                        if audio_only:
                            file_path = os.path.join(output_dir, f"{random_uuid}.{audio_codec}")
                        else:
                            video_ext = info_dict.get('ext') or merge_format
                            file_path = os.path.join(output_dir, f"{random_uuid}.{video_ext}")

                        title = info_dict.get('title', 'Media')
                        channel = info_dict.get('uploader') or info_dict.get('channel') or info_dict.get('uploader_id')
                        if channel:
                            channel = channel.lstrip('@')
                        source_lang = info_dict.get('language', None)
                        quality_info = {
                            'height': info_dict.get('height'),
                            'vcodec': info_dict.get('vcodec'),
                            'format_id': info_dict.get('format_id'),
                            'requested_format': video_format if not audio_only else None,
                            'duration': info_dict.get('duration'),
                        }

                        h = quality_info.get('height')
                        min_h = 720 if quality_mode == "raw" else (480 if quality_mode == "standard" else None)
                        if (
                            not audio_only and min_h and h and h < min_h
                            and attempt < min(max_attempts, 6)
                        ):
                            try:
                                os.remove(file_path)
                            except Exception:
                                pass
                            last_error = Exception(
                                f"Раздобыли только {h}p (format {quality_info['format_id']}) — пробую другой клиент/метод"
                            )
                            await asyncio.sleep(1)
                            continue

                        return file_path, title, channel, source_lang, quality_info

                    except DownloadCancelled:
                        raise

                    except Exception as e:
                        error_str = str(e)
                        last_error = e

                        if "This video is unavailable" in error_str or "Private video" in error_str:
                            raise Exception("Видео недоступно (приватное, удалено или только для подписчиков)")

                        if "Unsupported URL" in error_str or "is not a valid URL" in error_str:
                            raise Exception("Эта ссылка не поддерживается yt-dlp")

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


MYINSTANTS_COVER_URL = "https://wsrv.nl/?url=pbs.twimg.com/profile_images/1091271508/myinstants_400x400.png"
_myinstants_cover_cache = {"path": None}


async def get_myinstants_cover_path(base_dir):
    if _myinstants_cover_cache["path"] and os.path.isfile(_myinstants_cover_cache["path"]):
        return _myinstants_cover_cache["path"]
    try:
        cover_path = os.path.join(base_dir, "myinstants_cover.jpg")
        async with aiohttp.ClientSession() as session:
            async with session.get(MYINSTANTS_COVER_URL, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.read()
        with open(cover_path, "wb") as f:
            f.write(data)
        _myinstants_cover_cache["path"] = cover_path
        return cover_path
    except Exception:
        return None


def clean_twitter_title(title):
    """yt-dlp отдаёт заголовок твита как 'Имя канала - текст твита' — оставляем только
    сам текст. У твитов без текста (только медиа) в этом же поле иногда остаётся голая
    t.co-ссылка — в таком случае возвращаем пустую строку (без заголовка вообще)."""
    if not title:
        return title
    if " - " in title:
        title = title.split(" - ", 1)[1].strip()
    if re.match(r"^https?://t\.co/\S+$", title.strip(), re.IGNORECASE):
        return ""
    return title


def clean_myinstants_title(title):
    """Заголовок страницы myinstants приходит вида 'Название - Sound Button — www.myinstants.com',
    но 'Sound Button' локализуется под язык страницы ('Звуковая кнопка' и т.п.) — вместо
    попытки перечислить все варианты просто берём всё до первого ' - ', как и с твиттером."""
    if not title:
        return title
    if " - " in title:
        title = title.split(" - ", 1)[0].strip()
    return title


def clean_tenor_title(title):
    """Заголовок страницы tenor.com приходит вида 'Название GIF - Название - Discover & Share
    GIFs' — берём всё до первого ' - ' (как и myinstants/твиттер), затем убираем хвостовое
    'GIF', которое там всегда приклеено к самому названию."""
    if not title:
        return title
    if " - " in title:
        title = title.split(" - ", 1)[0].strip()
    title = re.sub(r"\s+GIF$", "", title, flags=re.IGNORECASE).strip()
    return title


def sanitize_media_filename(name, max_len=120, fallback="audio"):
    """Готовит название видео/трека для показа как имя файла: убирает переносы строк
    и символы, недопустимые в именах файлов на большинстве ОС, режет по длине."""
    if not name:
        return fallback
    name = re.sub(r"[\r\n\t]+", " ", name).strip()
    name = re.sub(r'[/\\:*?"<>|]', "_", name)
    name = re.sub(r"\s+", " ", name).strip()
    if len(name) > max_len:
        name = name[:max_len].rstrip()
    return name or fallback


def convert_markdown_to_html(template: str, link: str) -> str:
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', template).replace("{link}", link)




@loader.tds
class YouTube_DLDMod(loader.Module):
    """Помогает скачивать видео с YouTube, TikTok и др. SponsorBlock вырезает рекламу, -s/-e берут только отрезок."""

    __version__ = (3, 4, 10)

    strings = {
        "name": "YouTube-DLD",
        "no_link": EMOJI_WARN + " <b>Пожалуйста, укажите ссылку на видео либо ответьте на сообщение с ней.</b>",
        "youtube_posts_unsupported": EMOJI_WARN + " <b>Посты YouTube временно не поддерживаются.</b>",
        "default_downloading": "<b>Загружаю видео.</b>\n\n" + EMOJI_CLOCK + " <code>{eta}</code>",
        "default_downloading_simple": "<b>Загружаю видео.</b>",
        "eta_unknown": "...",
        "default_error": "<b>Ошибка загрузки.</b>\n\n<code>{error}</code>",
        "too_long": "Видео длиннее {minutes} мин. Скачивание отменено — лимит меняется в .cfg YouTube-DLD (max_duration).",
        "cancelled": EMOJI_WARN + " <b>Загрузка отменена (.dlstop).</b>",
        "nothing_to_cancel": EMOJI_WARN + " <b>Нет активных загрузок для отмены.</b>",
        "cancelled_ok": EMOJI_OK + " Остановлено загрузок: <b>{count}</b>",
        "playlist_progress": EMOJI_DOWNLOAD + " <b>Плейлист {idx}/{total}</b>\n\n<code>{title}</code>",
        "default_response": "Вот [ваше видео]({link})! {quality}\n\n<code>{title}</code>",
        "default_music_response": "Вот [ваше аудио]({link})!\n\n<code>{title}</code>",
        "default_channel": "<tg-emoji emoji-id=\"5886412370347036129\">👤</tg-emoji> Канал: <code>{channel}</code>",
        "downloading_audio": EMOJI_NOTE + " <b>Скачиваю аудио...</b>",
        "quality_downloading": EMOJI_DOWNLOAD + " <b>Качаю в улучшенном качестве...</b>\n\n<i>Займёт чуть дольше обычного.</i>",
        "quality_compressing": EMOJI_COMPRESS + " <b>Сжимаю видео перед отправкой.</b>\n\n" + EMOJI_INFO + " <code>Осталось ≈ {eta}</code>",
        "queue_waiting": EMOJI_QUEUE + " <b>Видео в очереди({position})...</b>",
        "done_fallback": "Готово!",
        "extracting_audio": EMOJI_NOTE + " <b>Вырезаю звук из видео...</b>",
        "method_proxy": "прокси",
        "method_cookies": "куки",
        "method_direct": "напрямую",
        "cookies_required_error": EMOJI_CROSS + " <b>Ошибка куки.</b> Просьба вставить куки через команду <code>.cfg YouTube-DLD youtube_cookies</code>.",
        "supported_sites": """<tg-emoji emoji-id=6005986106703613755>🎥</tg-emoji> <b>Поддерживаемые сайты:</b>

<tg-emoji emoji-id="5355235592844095825">🔴</tg-emoji> <b>YouTube</b> — youtube.com, youtu.be, music.youtube.com
<tg-emoji emoji-id="5353034628263330616">🎵</tg-emoji> <b>TikTok</b> — tiktok.com, vt.tiktok.com, vm.tiktok.com
<tg-emoji emoji-id="5355097780228470775">📸</tg-emoji> <b>Instagram</b> — instagram.com
<tg-emoji emoji-id="5355148941878900494">🐦</tg-emoji> <b>X (Twitter)</b> — x.com, twitter.com
<tg-emoji emoji-id="5355254460635428635">👥</tg-emoji> <b>Facebook</b> — facebook.com
<tg-emoji emoji-id="5334764984142412896">🎬</tg-emoji> <b>Vimeo</b> — vimeo.com
<tg-emoji emoji-id="5352759664457038886">🎮</tg-emoji> <b>Twitch</b> — twitch.tv
<tg-emoji emoji-id="5352531593103686999">👽</tg-emoji> <b>Reddit</b> — reddit.com

<b><tg-emoji emoji-id=5891249688933305846>🎵</tg-emoji> Музыка:</b>
<tg-emoji emoji-id="5346296430166293639">🎧</tg-emoji> <b>Яндекс.Музыка</b> — music.yandex.ru
<tg-emoji emoji-id="5345844509412444249">☁️</tg-emoji> <b>SoundCloud</b> — soundcloud.com
<tg-emoji emoji-id="5451966206334513619">🎸</tg-emoji> <b>Bandcamp</b> — bandcamp.com
<tg-emoji emoji-id="5346074681004801565">🟢</tg-emoji> <b>Spotify</b> — spotify.com

<b><tg-emoji emoji-id=5994750571041525522>🇷🇺</tg-emoji> Российские:</b>
<tg-emoji emoji-id="5298747646096187189">▶️</tg-emoji> <b>RuTube</b> — rutube.ru
<tg-emoji emoji-id="5278229754099540071">🔵</tg-emoji> <b>ВКонтакте</b> — vk.com
<tg-emoji emoji-id="5310076528577491230">🟠</tg-emoji> <b>Одноклассники</b> — ok.ru

Полный список поддерживаемых сайтов — <a href="https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md">тут</a>.

<b><tg-emoji emoji-id=5891243564309942507>📝</tg-emoji> Команды:</b>
▫️ .dlvideo <ссылка> — скачать видео
▫️ .dlvideo -a <ссылка> — скачать аудио
▫️ .dlvideo -s 1:30 -e 5:00 <ссылка> — только отрезок (можно и без -e)
▫️ .dlvideo -p <ссылка на плейлист> — скачать плейлист целиком (до 30 роликов, каждый отдельным сообщением)
▫️ .dvlist — список сайтов
▫️ .sblock — настройки SponsorBlock (инлайн-меню)
▫️ .dlwl — вкл/выкл автозагрузку в этом чате, .dlwl <id/@username> — конкретный чат, .dlwl list — список
▫️ .dlvo — то же самое, что .dlvideo, но с переводом озвучки
▫️ .dlstop — остановить все активные загрузки (идущие и в очереди), сразу во всех чатах""",
        "sb_state_on": "включён ✅",
        "sb_state_off": "выключен 🚫",
        "sb_main_text": EMOJI_SCISSORS + " <b>SponsorBlock</b> — {state}\n\n" + EMOJI_CHECK + " — вырежется при скачивании, " + EMOJI_CROSS + " — останется в видео.\nУ пункта с " + EMOJI_GEAR + " есть отдельные настройки.",
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
        "vo_translating": EMOJI_MIC + " <b>Перевожу озвучку.</b>\n\n" + EMOJI_INFO + " <code>Осталось ≈ {eta}</code>",
        "vo_translating_simple": EMOJI_MIC + " <b>Перевожу озвучку.</b>",
        "vo_failed": EMOJI_WARN + " Озвучка не получилась: <code>{error}</code>\n\nОтправляю видео без перевода...",
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
        "no_link": EMOJI_WARN + " <b>Please provide a video link, or reply to a message that has one.</b>",
        "youtube_posts_unsupported": EMOJI_WARN + " <b>YouTube posts are temporarily not supported.</b>",
        "default_downloading": "<b>Downloading the video.</b>\n\n" + EMOJI_CLOCK + " <code>{eta}</code>",
        "default_downloading_simple": "<b>Downloading the video.</b>",
        "eta_unknown": "...",
        "default_error": "<b>Download failed.</b>\n\n<code>{error}</code>",
        "too_long": "The video is longer than {minutes} min. Download cancelled — the limit is set in .cfg YouTube-DLD (max_duration).",
        "cancelled": EMOJI_WARN + " <b>Download cancelled (.dlstop).</b>",
        "nothing_to_cancel": EMOJI_WARN + " <b>No active downloads to cancel.</b>",
        "cancelled_ok": EMOJI_OK + " Downloads stopped: <b>{count}</b>",
        "playlist_progress": EMOJI_DOWNLOAD + " <b>Playlist {idx}/{total}</b>\n\n<code>{title}</code>",
        "default_response": "Here's [your video]({link})! {quality}\n\n<code>{title}</code>",
        "default_music_response": "Here's [your audio]({link})!\n\n<code>{title}</code>",
        "default_channel": "<tg-emoji emoji-id=\"5886412370347036129\">👤</tg-emoji> Channel: <code>{channel}</code>",
        "downloading_audio": EMOJI_NOTE + " <b>Downloading audio...</b>",
        "quality_downloading": EMOJI_DOWNLOAD + " <b>Downloading in enhanced quality...</b>\n\n<i>Takes a bit longer than usual.</i>",
        "quality_compressing": EMOJI_COMPRESS + " <b>Compressing the video before sending.</b>\n\n" + EMOJI_INFO + " <code>≈ {eta} remaining</code>",
        "queue_waiting": EMOJI_QUEUE + " <b>Video queued ({position})...</b>",
        "done_fallback": "Done!",
        "extracting_audio": EMOJI_NOTE + " <b>Extracting audio from the video...</b>",
        "method_proxy": "proxy",
        "method_cookies": "cookies",
        "method_direct": "direct",
        "cookies_required_error": EMOJI_CROSS + " <b>Cookies error.</b> Please add cookies via <code>.cfg YouTube-DLD youtube_cookies</code>.",
        "supported_sites": """<tg-emoji emoji-id=6005986106703613755>🎥</tg-emoji> <b>Supported sites:</b>

<tg-emoji emoji-id="5355235592844095825">🔴</tg-emoji> <b>YouTube</b> — youtube.com, youtu.be, music.youtube.com
<tg-emoji emoji-id="5353034628263330616">🎵</tg-emoji> <b>TikTok</b> — tiktok.com, vt.tiktok.com, vm.tiktok.com
<tg-emoji emoji-id="5355097780228470775">📸</tg-emoji> <b>Instagram</b> — instagram.com
<tg-emoji emoji-id="5355148941878900494">🐦</tg-emoji> <b>X (Twitter)</b> — x.com, twitter.com
<tg-emoji emoji-id="5355254460635428635">👥</tg-emoji> <b>Facebook</b> — facebook.com
<tg-emoji emoji-id="5334764984142412896">🎬</tg-emoji> <b>Vimeo</b> — vimeo.com
<tg-emoji emoji-id="5352759664457038886">🎮</tg-emoji> <b>Twitch</b> — twitch.tv
<tg-emoji emoji-id="5352531593103686999">👽</tg-emoji> <b>Reddit</b> — reddit.com

<b><tg-emoji emoji-id=5891249688933305846>🎵</tg-emoji> Music:</b>
<tg-emoji emoji-id="5346296430166293639">🎧</tg-emoji> <b>Yandex Music</b> — music.yandex.ru
<tg-emoji emoji-id="5345844509412444249">☁️</tg-emoji> <b>SoundCloud</b> — soundcloud.com
<tg-emoji emoji-id="5451966206334513619">🎸</tg-emoji> <b>Bandcamp</b> — bandcamp.com
<tg-emoji emoji-id="5346074681004801565">🟢</tg-emoji> <b>Spotify</b> — spotify.com

<b><tg-emoji emoji-id=5994750571041525522>🇷🇺</tg-emoji> Russian:</b>
<tg-emoji emoji-id="5298747646096187189">▶️</tg-emoji> <b>RuTube</b> — rutube.ru
<tg-emoji emoji-id="5278229754099540071">🔵</tg-emoji> <b>VK</b> — vk.com
<tg-emoji emoji-id="5310076528577491230">🟠</tg-emoji> <b>Odnoklassniki</b> — ok.ru

Full list of supported sites — <a href="https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md">here</a>.

<b><tg-emoji emoji-id=5891243564309942507>📝</tg-emoji> Commands:</b>
▫️ .dlvideo <link> — download video
▫️ .dlvideo -a <link> — download audio
▫️ .dlvideo -s 1:30 -e 5:00 <link> — just a clip (-e is optional)
▫️ .dlvideo -p <playlist link> — download the whole playlist (up to 30 videos, each as a separate message)
▫️ .dvlist — list of supported sites
▫️ .sblock — SponsorBlock settings (inline menu)
▫️ .dlwl — toggle auto-download in this chat, .dlwl <id/@username> — specific chat, .dlwl list — list of chats
▫️ .dlvo — same as .dlvideo, but with voice-over translation
▫️ .dlstop — stop all active downloads (running and queued), across every chat at once""",
        "sb_state_on": "enabled ✅",
        "sb_state_off": "disabled 🚫",
        "sb_main_text": EMOJI_SCISSORS + " <b>SponsorBlock</b> — {state}\n\n" + EMOJI_CHECK + " — will be cut on download, " + EMOJI_CROSS + " — stays in the video.\nThe item with " + EMOJI_GEAR + " has its own extra settings.",
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
        "vo_translating": EMOJI_MIC + " <b>Translating voice-over.</b>\n\n" + EMOJI_INFO + " <code>≈ {eta} remaining</code>",
        "vo_translating_simple": EMOJI_MIC + " <b>Translating voice-over.</b>",
        "vo_failed": EMOJI_WARN + " Voice-over failed: <code>{error}</code>\n\nSending the video without translation...",
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

    async def _resume_pending_downloads(self, client):
        """Если процесс упал посреди загрузки (крашнулся без лога, OOM и т.п.), при следующем
        старте здесь найдутся "осиротевшие" записи в self.db — пробуем продолжить их сами,
        без участия юзера. Максимум 2 попытки на загрузку, дальше — молча сдаёмся и чистим."""
        active_downloads = self.get("active_downloads", {})
        if not active_downloads:
            return

        MAX_RESUME_ATTEMPTS = 2
        for resume_job_id, entry in list(active_downloads.items()):
            attempts = entry.get("attempts", 0)
            chat_id = entry.get("chat_id")
            message_id = entry.get("message_id")

            if attempts >= MAX_RESUME_ATTEMPTS:
                active_downloads.pop(resume_job_id, None)
                self.set("active_downloads", active_downloads)
                try:
                    await client.send_message(
                        chat_id,
                        f"{EMOJI_WARN} <b>Загрузка сорвалась несколько раз подряд, отменяю.</b>",
                        parse_mode="HTML",
                        reply_to=message_id,
                    )
                except Exception:
                    pass
                continue

            try:
                orig_message = await client.get_messages(chat_id, ids=message_id)
            except Exception:
                orig_message = None

            if not orig_message:
                active_downloads.pop(resume_job_id, None)
                self.set("active_downloads", active_downloads)
                continue

            stale_status_msg_id = entry.get("status_msg_id")

            active_downloads[resume_job_id]["attempts"] = attempts + 1
            self.set("active_downloads", active_downloads)

            resolved_link = entry.get("link")
            resolved_args_raw = entry.get("args_raw")

            if not resolved_link:
                resolved_link = find_video_link_in_message(orig_message)
                if not resolved_link:
                    try:
                        reply_msg = await orig_message.get_reply_message()
                    except Exception:
                        reply_msg = None
                    if reply_msg:
                        resolved_link = find_video_link_in_message(reply_msg)

            if not resolved_link:
                debug_text = (orig_message.raw_text or "")[:200]
                active_downloads.pop(resume_job_id, None)
                self.set("active_downloads", active_downloads)
                fail_text = (
                    f"{EMOJI_WARN} <b>Не удалось возобновить загрузку после краша: "
                    f"в сообщении не найдена ссылка.</b>\n\n"
                    f"<code>{html_escaping.escape(debug_text) or '(пусто)'}</code>"
                )
                try:
                    await orig_message.edit(fail_text, parse_mode="HTML")
                except Exception:
                    try:
                        await client.send_message(chat_id, fail_text, parse_mode="HTML", reply_to=message_id)
                    except Exception:
                        pass
                continue

            try:
                await orig_message.edit(
                    f"{EMOJI_WARN} <b>Краш, повторяю попытку...</b>", parse_mode="HTML"
                )
            except Exception:
                pass

            try:
                await self._dlvideo_impl(
                    orig_message, force_translate=entry.get("force_translate", False),
                    link_override=resolved_link, quiet=True, args_override=resolved_args_raw,
                )
                if not getattr(orig_message, "out", True) and stale_status_msg_id and stale_status_msg_id != orig_message.id:
                    try:
                        await client.delete_messages(chat_id, stale_status_msg_id)
                    except Exception:
                        pass
            except Exception as resume_err:
                logger.warning(f"Не удалось продолжить загрузку после перезапуска: {resume_err}")

    async def client_ready(self, client, db):
        self._client = client
        asyncio.create_task(self._resume_pending_downloads(client))
        cleanup_stale_downloads(utils.get_base_dir())

        try:
            forum_channel_id = db.get("heroku.forums", "channel_id", None)
            if forum_channel_id:
                topic = await utils.asset_forum_topic(
                    client,
                    db,
                    forum_channel_id,
                    "YouTube-DLD Logs",
                    description="📃 Сюда прилетают логи автозагрузки модуля YouTube-DLD (тихие сбои: неподдерживаемая ссылка, ошибка скачивания и т.п.).",
                )
                is_new = self.get("log_topic_id") != topic.id
                self.set("log_topic_id", topic.id)
                self.set("log_channel_id", forum_channel_id)

                if is_new:
                    try:
                        channel_entity = await client.get_entity(forum_channel_id)
                        async for topic_msg in client.iter_messages(forum_channel_id, reply_to=topic.id, limit=1):
                            await client(UpdatePinnedMessageRequest(peer=channel_entity, id=topic_msg.id, silent=True))
                            break
                    except Exception:
                        pass
        except Exception:
            pass

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
        self._download_queue = DownloadTurnQueue()
        self._active_jobs = {}
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
                EMOJI_DOWNLOAD + " перед этим текстом добавляется в коде и не редактируется здесь.\n\n"
                "Доступные плейсхолдеры (писать ровно так, с фигурными скобками):\n"
                "{attempt} — номер попытки, {method} — способ (напрямую/куки/прокси), "
                "{eta} — оставшееся время (обновляется во время скачивания, примерно раз в 3 секунды)",
            ),
            loader.ConfigValue(
                "error_text",
                self.strings["default_error"],
                EMOJI_WARN + " перед этим текстом добавляется в коде и не редактируется здесь.\n\n"
                "Доступный плейсхолдер (писать ровно так, с фигурными скобками):\n"
                "{error} — текст самой ошибки",
            ),
            loader.ConfigValue(
                "response_text",
                self.strings["default_response"],
                "Ответ после загрузки видео. Иконка сайта добавляется в коде перед текстом и не "
                "редактируется здесь.\n\nДоступные плейсхолдеры: {title} — название видео, "
                "{quality} — разрешение и кодек (например \"720p | h264\"), пусто для аудио."
            ),
            loader.ConfigValue(
                "music_response_text",
                self.strings["default_music_response"],
                EMOJI_NOTE + " перед этим текстом добавляется в коде и не редактируется здесь."
            ),
            loader.ConfigValue(
                "show_channel",
                True,
                "Показывать название канала?",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "youtube_cookies",
                [],
                EMOJI_COOKIE + " Куки Netscape (ТЕКСТОМ!) — каждый сайт ОТДЕЛЬНЫМ элементом "
                "(«Добавить элемент»). YouTube, Яндекс.Музыка, VK, Instagram, Twitter/X — "
                "модуль сам оставит только нужные строки по доменам.\n\n"
                "Как получить: Cookie-Editor → Export → Netscape "
                "(youtube.com/robots.txt, music.yandex.ru/robots.txt, …).\n"
                "Можно вставлять весь экспорт — лишнее срежется при сохранении.\n"
                "Начинается с: # Netscape HTTP Cookie File",
                validator=loader.validators.Series(validator=loader.validators.String()),
                on_change=self._on_youtube_cookies_change,
            ),
            loader.ConfigValue(
                "proxy",
                "",
                EMOJI_GLOBE + " Прокси (опционально)\n\n"
                "Форматы:\n"
                "• HTTP: http://user:pass@host:port\n"
                "• SOCKS5: socks5://host:port\n\n"
                "Пусто — прокси не используется. Заполнено — пробуем через прокси, затем куки, затем напрямую.\n\n"
                + EMOJI_WARN + " Trojan/VLESS не поддерживаются!",
                validator=loader.validators.Hidden(),
            ),
            loader.ConfigValue(
                "whitelist",
                [],
                "📃 Список чатов (ID), где ссылки скачиваются автоматически. Можно редактировать прямо здесь "
                "или командой .dlwl в самом чате.",
                validator=loader.validators.Series(validator=loader.validators.TelegramID()),
            ),
            loader.ConfigValue(
                "auto_quality",
                True,
                "🎞 Умное качество. Если интернет достаточно быстрый и стабильный — качаю качество "
                "получше и сжимаю. Дольше, но чётче.",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "max_duration",
                0,
                "<tg-emoji emoji-id=5900104897885376843>🕓</tg-emoji> Лимит длительности видео в минутах (только YouTube). 0 — без лимита. "
                "Видео длиннее лимита не скачивается вообще (дорого качать/сжимать и рискует "
                "упереться в лимит Telegram на размер файла).",
                validator=loader.validators.Integer(minimum=0),
            ),
            loader.ConfigValue(
                "vo_orig_volume",
                50,
                "🔊 Громкость оригинальной озвучки при переводе (0-100%), пока идёт перевод поверх",
                validator=loader.validators.Integer(minimum=0, maximum=100),
            ),
        )


    def _on_youtube_cookies_change(self):
        raw = self.config["youtube_cookies"]
        if raw is None:
            self.config["youtube_cookies"] = []
            return
        if isinstance(raw, str):
            items = [raw]
        else:
            try:
                items = list(raw)
            except TypeError:
                items = [str(raw)]
        cleaned = []
        seen = set()
        for item in items:
            text = item or ""
            if not text.strip():
                cleaned.append(text)
                continue
            c = clean_cookies_text(text)
            if c is None:
                cleaned.append(text)
                continue
            body_lines = [
                ln for ln in c.splitlines()
                if ln.strip() and not ln.strip().startswith("#")
            ]
            if not body_lines:
                cleaned.append(text)
                continue
            body = "\n".join(body_lines)
            if body in seen:
                continue
            seen.add(body)
            if not c.lstrip().startswith("#"):
                c = "# Netscape HTTP Cookie File\n" + c
            cleaned.append(c)
        self.config["youtube_cookies"] = cleaned

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

    async def _saveasbot_fallback(self, call, link, chat_id, reply_to_id, audio_only=False):
        """Крайний случай: сайт поддерживается (TikTok/Instagram/Pinterest — то, что и сам
        @SaveAsBot умеет по его же /start), но скачать напрямую не вышло. Пересылаем ссылку
        @SaveAsBot, забираем у него медиа и постим в чат сами — как будто скачали своими
        силами, плюс подчищаем переписку с ботом, чтобы не копился мусор."""
        try:
            await call.edit(
                f"{EMOJI_DOWNLOAD} " + self.config["downloading_text"].replace("{attempt}", "1").replace("{method}", "SaveAsBot").replace("{eta}", self.strings("eta_unknown")),
                reply_markup=None,
            )
        except Exception:
            pass

        client = getattr(call, "client", None) or self._client

        was_archived = await get_dialog_archived(client, SAVEASBOT_ID)
        if was_archived is False:
            try:
                await client.edit_folder(SAVEASBOT_ID, 1)
            except Exception:
                pass

        was_muted = await get_dialog_muted(client, SAVEASBOT_ID)
        if was_muted is False:
            await set_dialog_muted(client, SAVEASBOT_ID, True)

        try:
            our_and_their_ids = []
            responses = []
            try:
                async with client.conversation(SAVEASBOT_ID, timeout=60) as conv:
                    start_msg = await conv.send_message("/start", parse_mode=None)
                    our_and_their_ids.append(start_msg.id)
                    try:
                        start_resp = await conv.get_response(timeout=10)
                        our_and_their_ids.append(start_resp.id)
                    except asyncio.TimeoutError:
                        pass

                    link_msg = await conv.send_message(link, parse_mode=None)
                    our_and_their_ids.append(link_msg.id)

                    first_resp = await conv.get_response()
                    responses.append(first_resp)
                    our_and_their_ids.append(first_resp.id)
                    while True:
                        try:
                            nxt = await conv.get_response(timeout=4)
                            responses.append(nxt)
                            our_and_their_ids.append(nxt.id)
                        except asyncio.TimeoutError:
                            break
            except Exception as fallback_err:
                logger.warning(
                    f"SaveAsBot fallback failed ({type(fallback_err).__name__}): {fallback_err}"
                )
                try:
                    await call.edit(
                        f"{EMOJI_WARN} <b>@SaveAsBot не ответил или не смог скачать:</b>\n\n"
                        f"<code>{type(fallback_err).__name__}: {clean_error_text(fallback_err)}</code>"
                    )
                except Exception:
                    pass
                return

            media_messages = [m for m in responses if getattr(m, "media", None)]
            if not media_messages:
                try:
                    await call.edit(f"{EMOJI_WARN} <b>@SaveAsBot не прислал медиа в ответ.</b>")
                except Exception:
                    pass
                try:
                    await client.delete_messages(SAVEASBOT_ID, our_and_their_ids, revoke=True)
                except Exception:
                    pass
                return

            downloaded_files = []
            is_photo = []
            for m in media_messages:
                try:
                    path = await client.download_media(m, file=utils.get_base_dir())
                    if path:
                        downloaded_files.append(path)
                        is_photo.append(bool(getattr(m, "photo", None)))
                except Exception:
                    continue

            if not downloaded_files:
                try:
                    await call.edit(f"{EMOJI_WARN} <b>Не удалось скачать медиа, присланное @SaveAsBot.</b>")
                except Exception:
                    pass
                try:
                    await client.delete_messages(SAVEASBOT_ID, our_and_their_ids, revoke=True)
                except Exception:
                    pass
                return

            if audio_only:
                type_word = "Аудио"
            elif len(downloaded_files) > 1:
                type_word = None
            elif is_photo[0]:
                type_word = "Фото"
            else:
                type_word = "Видео"

            site_icon = get_site_emoji_html(link)
            if type_word is None:
                safe_link_attr = html_escaping.escape(link, quote=True)
                header = f'{site_icon} <a href="{safe_link_attr}">Карусель</a>.'
            else:
                header = f"{site_icon} {type_word}"

            is_instagram_link = "instagram.com" in link.lower()
            if is_instagram_link:
                title_hint, channel_hint = None, None
            else:
                cookies_cfg = config_cookies_text(self.config["youtube_cookies"])
                title_hint, channel_hint = await probe_title_channel(link, cookies_text=cookies_cfg)
                if not title_hint:
                    og_title, og_desc = await fetch_og_preview(link)
                    title_hint = title_hint or og_title
                    channel_hint = channel_hint or og_desc

            caption = header
            if title_hint:
                safe_title = html_escaping.escape(html_escaping.unescape(title_hint)[:300])
                caption += f"\n\n<code>{safe_title}</code>"
            if channel_hint and self.config["show_channel"]:
                safe_channel = html_escaping.escape(html_escaping.unescape(channel_hint)[:200])
                caption += f"\n\n{self.strings('default_channel').replace('{channel}', safe_channel)}"

            try:
                chunks = [downloaded_files[i:i + 10] for i in range(0, len(downloaded_files), 10)]
                for idx, chunk in enumerate(chunks):
                    chunk_caption = caption if idx == 0 else None
                    await client.send_file(chat_id, chunk, caption=chunk_caption, parse_mode="HTML", reply_to=reply_to_id)
            finally:
                for f in downloaded_files:
                    try:
                        os.remove(f)
                    except Exception:
                        pass

            try:
                await client.delete_messages(SAVEASBOT_ID, our_and_their_ids, revoke=True)
            except Exception:
                pass

            try:
                await call.delete()
            except Exception:
                try:
                    await call.edit(f"{EMOJI_OK} <b>Готово через @SaveAsBot!</b>", reply_markup=None)
                except Exception:
                    pass
        finally:
            if was_archived is False:
                try:
                    await client.edit_folder(SAVEASBOT_ID, 0)
                except Exception:
                    pass
            if was_muted is False:
                await set_dialog_muted(client, SAVEASBOT_ID, False)

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

    @staticmethod
    def _normalize_chat_id(cid):
        s = str(cid)
        if s.startswith("-100"):
            return int(s[4:])
        return cid

    @staticmethod
    async def _resolve_whitelist_entity(client, cid):
        for candidate in (cid, int(f"-100{cid}"), -cid if cid > 0 else cid):
            try:
                return await client.get_entity(candidate)
            except Exception:
                continue
        return None

    @loader.command()
    async def dlwl(self, message):
        """Вкл/выкл автозагрузку ссылок. Без аргумента — этот чат, .dlwl <id/@username> — конкретный чат, .dlwl list — список"""
        args_raw = utils.get_args_raw(message).strip()

        if args_raw.lower() == "list":
            whitelist = self.config["whitelist"]
            if not whitelist:
                await utils.answer(message, "📃 Вайтлист пуст.")
                return
            lines = []
            for cid in whitelist:
                entity = await self._resolve_whitelist_entity(message.client, cid)
                if entity is None:
                    lines.append(f"• <b>{cid}</b> (<code>{cid}</code>)")
                    continue

                name = tl_utils.get_display_name(entity) or str(cid)
                username = getattr(entity, "username", None)

                if isinstance(entity, tl_types.User):
                    link_url = f"tg://user?id={entity.id}"
                    id_part = f'<a href="{link_url}">{cid}</a>'
                    name_part = f'<a href="{link_url}">{name}</a>'
                elif username:
                    link_url = f"https://t.me/{username}"
                    id_part = f"<code>{cid}</code>"
                    name_part = f'<a href="{link_url}">{name}</a>'
                else:
                    id_part = f"<code>{cid}</code>"
                    name_part = f"<b>{name}</b>"

                lines.append(f"• {name_part} ({id_part})")
            await utils.answer(message, "📃 <b>Автозагрузка включена в:</b>\n\n" + "\n".join(lines))
            return

        if args_raw:
            try:
                entity = await message.client.get_entity(args_raw)
                raw_chat_id = await message.client.get_peer_id(entity)
                chat_id = self._normalize_chat_id(raw_chat_id)
            except Exception:
                await utils.answer(message, f"❌ Не нашла чат/пользователя по «{args_raw}».")
                return
            target_name = tl_utils.get_display_name(entity) or str(raw_chat_id)
        else:
            raw_chat_id = message.chat_id
            chat_id = self._normalize_chat_id(raw_chat_id)
            target_name = "этот чат"

        whitelist = list(self.config["whitelist"])
        if chat_id in whitelist:
            whitelist.remove(chat_id)
            self.config["whitelist"] = whitelist
            await utils.answer(message, f"{EMOJI_FAIL} Автозагрузка выключена:\n{target_name} (<code>{raw_chat_id}</code>)")
        else:
            whitelist.append(chat_id)
            self.config["whitelist"] = whitelist
            await utils.answer(message, f"{EMOJI_OK} Автозагрузка включена:\n{target_name} (<code>{raw_chat_id}</code>)")

    @loader.watcher()
    async def watcher(self, message):
        if not isinstance(message, Message):
            return
        if message.out:
            return
        if message.media and not isinstance(message.media, tl_types.MessageMediaWebPage):
            return

        raw = (message.raw_text or "").strip()
        if not raw or raw.lower().startswith(".dl"):
            return

        whitelist = self.config["whitelist"]
        if not whitelist or self._normalize_chat_id(message.chat_id) not in whitelist:
            return

        link = find_video_link_in_message(message)
        if not link:
            return

        await self._dlvideo_impl(message, link_override=link, silent_errors=True)

    def _register_active_job(self, job_id, cancel_event, chat_id):
        self._active_jobs[job_id] = {"cancel_event": cancel_event, "chat_id": chat_id}

    def _unregister_active_job(self, job_id):
        self._active_jobs.pop(job_id, None)

    async def _download_playlist(self, message, link, audio_only, cookies, proxy, deno, answer_target, reply, status_msg, cancel_event):
        """Плейлист по флагу -p: качаем все ролики по одному, каждый — отдельным сообщением.
        Возвращает True, если это реально плейлист (обработан целиком или с пропуском
        упавших роликов), False — если плейлиста нет и вызывающий идёт обычным путём."""
        entries = await probe_playlist_entries(link, cookies_text=cookies, proxy=proxy)
        if not entries or len(entries) < 2:
            return False
        entries = entries[:30]
        total = len(entries)

        try:
            for idx, entry in enumerate(entries, start=1):
                if cancel_event.is_set():
                    raise DownloadCancelled()
                entry_url = entry.get("url")
                entry_title = entry.get("title") or ""
                if not entry_url:
                    continue

                try:
                    await status_msg.edit(
                        self.strings("playlist_progress")
                        .replace("{idx}", str(idx))
                        .replace("{total}", str(total))
                        .replace("{title}", html_escaping.escape(entry_title or "…")),
                    )
                except Exception:
                    pass

                try:
                    media_path, _, _, _, _ = await download_media(
                        entry_url,
                        cookies_text=cookies,
                        proxy=proxy,
                        deno_path=deno,
                        max_attempts=3,
                        audio_only=audio_only,
                        audio_codec="mp3",
                        sponsorblock_categories=[],
                        on_progress=None,
                        cancel_event=cancel_event,
                        quality_mode="standard",
                    )
                except DownloadCancelled:
                    raise
                except Exception as entry_err:
                    logger.warning(f"Playlist entry {idx}/{total} failed: {entry_err}")
                    continue

                if not (media_path and os.path.isfile(media_path) and os.path.getsize(media_path) > 0):
                    continue

                try:
                    caption_head = convert_markdown_to_html(self.config["response_text"], entry_url)
                    caption_head = caption_head.replace("{title}", entry_title or "").replace("{quality}", "")
                    caption = f"{get_site_emoji_html(entry_url)} {caption_head}\n\n<code>{idx}/{total}</code>"
                    try:
                        await utils.answer_file(
                            answer_target, media_path, caption=caption, parse_mode="HTML", silent=True,
                        )
                    except TypeError as silent_err:
                        if "silent" not in str(silent_err):
                            raise
                        await utils.answer_file(
                            answer_target, media_path, caption=caption, parse_mode="HTML",
                        )
                except Exception as send_err:
                    logger.warning(f"Playlist entry {idx}/{total} send failed: {send_err}")
                finally:
                    try:
                        os.remove(media_path)
                    except Exception:
                        pass
        finally:
            try:
                await status_msg.delete()
            except Exception:
                pass
        return True

    @loader.command(alias="dlv")
    async def dlvideo(self, message):
        """Скачать видео/аудио по ссылке. -a аудио, -s/-e начало/конец отрезка, -p плейлист (до 30 роликов)"""
        await self._dlvideo_impl(message, force_translate=False)

    @loader.command()
    async def dlvo(self, message):
        """То же самое что .dlvideo (те же флаги -a/-s/-e), но с переводом озвучки"""
        await self._dlvideo_impl(message, force_translate=True)

    @loader.command()
    async def dlstop(self, message):
        """Остановить ВСЕ активные загрузки — и идущие, и стоящие в очереди, сразу во всех чатах"""
        targets = list(self._active_jobs.values())
        for job in targets:
            ev = job.get("cancel_event")
            if ev:
                ev.set()

        queued_removed = self._download_queue.cancel_all()
        for entry in queued_removed:
            try:
                await entry["status_msg"].edit(self.strings("cancelled"))
            except Exception:
                pass

        total = len(targets) + len(queued_removed)
        if total == 0:
            await utils.answer(message, self.strings("nothing_to_cancel"))
            return
        await utils.answer(message, self.strings("cancelled_ok").replace("{count}", str(total)))

    async def _dlvideo_impl(self, message, force_translate=False, link_override=None, silent_errors=False, quiet=False, args_override=None):
        args_raw = args_override if args_override is not None else utils.get_args_raw(message)
        reply = await message.get_reply_message()

        parsed = parse_dlvideo_args(args_raw)
        audio_only = parsed["audio_only"]
        start_time = parsed["start"]
        end_time = parsed["end"]
        raw_quality = parsed["raw_quality"]

        link = link_override or find_video_link_in_message(message)
        if not link and reply:
            link = find_video_link_in_message(reply)

        if not link and reply and audio_only and getattr(reply, "video", None):
            status_msg = _MutedStatus() if quiet else await utils.answer(message, self.strings("extracting_audio"))
            video_path = None
            audio_path = None
            try:
                video_path = await self._client.download_media(reply, file=utils.get_base_dir())
                if not video_path:
                    raise Exception(self.strings("done_fallback"))
                audio_path = await extract_audio_from_video(video_path, utils.get_base_dir())
                if not audio_path:
                    raise Exception("не удалось извлечь звук из видео (ffmpeg)")

                reply_title = (reply.raw_text or "").strip().splitlines()[0][:100] if reply.raw_text else ""
                safe_title = sanitize_media_filename(reply_title, fallback="Аудио")
                send_attributes = [
                    DocumentAttributeFilename(f"{safe_title}.mp3"),
                    DocumentAttributeAudio(duration=0, performer=None, voice=False),
                ]
                await utils.answer_file(
                    message, audio_path, caption=f"{EMOJI_NOTE} {safe_title}", parse_mode="HTML",
                    reply_to=reply, attributes=send_attributes,
                )
                try:
                    await status_msg.delete()
                except Exception:
                    pass
            except Exception as e:
                try:
                    await status_msg.edit(f"{EMOJI_WARN} {clean_error_text(e)}")
                except Exception:
                    pass
            finally:
                for p in (video_path, audio_path):
                    if p:
                        try:
                            os.remove(p)
                        except Exception:
                            pass
            return

        if not link:
            await utils.answer(message, self.strings["no_link"])
            return

        link = normalize_link(link)

        if is_audio_only_platform(link):
            audio_only = True

        if re.search(r"youtube\.com/post/", link.lower()):
            await utils.answer(message, self.strings("youtube_posts_unsupported"))
            return

        is_short_form_by_url = (
            "tiktok.com" in link.lower()
            or (("youtube.com" in link.lower() or "youtu.be" in link.lower()) and "/shorts/" in link.lower())
            or "/reel/" in link.lower() or "/clip/" in link.lower() or "clips.twitch.tv" in link.lower()
            or bool(re.search(r"vk\.(com|ru)/clip", link.lower()))
        )

        if start_time is None:
            url_timecode = extract_url_timecode(link)
            if url_timecode is not None:
                start_time = url_timecode

        if start_time is not None and end_time is not None and end_time <= start_time:
            end_time = None

        if audio_only:
            status_msg = _MutedStatus() if quiet else await utils.answer(message, self.strings("downloading_audio"))
        elif is_short_form_by_url:
            status_msg = _MutedStatus() if quiet else await utils.answer(message, f"{EMOJI_DOWNLOAD} " + self.strings("default_downloading_simple"))
        else:
            status_msg = _MutedStatus() if quiet else await utils.answer(message, f"{EMOJI_DOWNLOAD} " + self.config["downloading_text"].replace("{attempt}", "1").replace("{method}", "...").replace("{eta}", self.strings("eta_unknown")))

        answer_target = message if quiet else status_msg

        resume_job_id = f"{message.chat_id}:{message.id}"
        active_downloads = self.get("active_downloads", {})
        active_downloads[resume_job_id] = {
            "chat_id": message.chat_id,
            "message_id": message.id,
            "force_translate": force_translate,
            "status_msg_id": status_msg.id,
            "link": link,
            "args_raw": args_raw,
            "attempts": active_downloads.get(resume_job_id, {}).get("attempts", 0),
            "ts": time.time(),
        }
        self.set("active_downloads", active_downloads)

        cancel_event = threading.Event()
        self._register_active_job(resume_job_id, cancel_event, message.chat_id)

        cookies = config_cookies_text(self.config["youtube_cookies"])
        proxy = self.config["proxy"].strip() if self.config["proxy"] else None
        is_tiktok = "tiktok.com" in link.lower()
        is_instagram = "instagram.com" in link.lower()
        is_pinterest = "pinterest." in link.lower() or "pin.it" in link.lower()
        is_twitter = "twitter.com" in link.lower() or "x.com" in link.lower()
        is_discord = bool(DISCORD_RE.search(link))
        yandex_track_id = extract_yandex_track_id(link)
        yandex_album_id = extract_yandex_album_id(link)
        yandex_playlist = extract_yandex_playlist(link)
        yandex_playlist_uuid = extract_yandex_playlist_uuid(link)
        deno = self.get("deno_source") if self.get("deno_source") not in ["install_failed", None] else None
        max_attempts = MAX_DOWNLOAD_ATTEMPTS

        sb_enabled = self.get("sb_enabled", True)
        sb_categories = list(self.get("sb_categories", DEFAULT_SB_CATEGORIES)) if sb_enabled else []
        if "music_offtopic" in sb_categories and self.get("sb_music_only", True) and "music.youtube.com" not in link.lower():
            sb_categories.remove("music_offtopic")

        method_labels = {
            "proxy": self.strings("method_proxy"),
            "cookies": self.strings("method_cookies"),
            "direct": self.strings("method_direct"),
        }
        progress = {"attempt": 1, "method": "direct", "eta": self.strings("eta_unknown"), "short_form": is_short_form_by_url}

        def render_downloading_text():
            if progress["short_form"]:
                return f"{EMOJI_DOWNLOAD} " + self.strings("default_downloading_simple")
            eta = progress.get("eta") or self.strings("eta_unknown")
            if eta in ("…", "...", self.strings("eta_unknown")):
                return f"{EMOJI_DOWNLOAD} " + self.strings("default_downloading_simple")
            return (
                f"{EMOJI_DOWNLOAD} <b>Загружаю видео.</b>\n\n"
                f"{EMOJI_CLOCK} <code>{eta}</code>"
            )

        async def update_status(attempt, method_name):
            progress["attempt"] = attempt
            progress["method"] = method_name
            progress["eta"] = self.strings("eta_unknown")
            if not audio_only:
                try:
                    await status_msg.edit(render_downloading_text())
                except Exception:
                    pass

        async def update_eta(eta_seconds):
            if audio_only or progress.get("short_form"):
                return
            if eta_seconds is None or eta_seconds < 3:
                return
            eta_text = format_seconds(max(0, int(eta_seconds)))
            if progress["eta"] == eta_text:
                return
            progress["eta"] = eta_text
            try:
                await status_msg.edit(render_downloading_text())
            except Exception:
                pass

        was_queued = bool(self._download_queue._waiters)
        try:
            queue_entry = await self._download_queue.acquire(
                status_msg, message,
                lambda position: self.strings("queue_waiting").replace("{position}", str(position)),
            )
        except QueueCancelled:
            self._unregister_active_job(resume_job_id)
            try:
                active_downloads = self.get("active_downloads", {})
                active_downloads.pop(resume_job_id, None)
                self.set("active_downloads", active_downloads)
            except Exception:
                pass
            try:
                await status_msg.edit(self.strings("cancelled"))
            except Exception:
                pass
            return

        if was_queued:
            try:
                if audio_only:
                    await status_msg.edit(self.strings("downloading_audio"))
                else:
                    progress["attempt"] = 1
                    progress["method"] = "direct"
                    progress["eta"] = self.strings("eta_unknown")
                    await status_msg.edit(render_downloading_text())
            except Exception:
                pass

        try:
            if parsed["playlist"]:
                try:
                    handled = await self._download_playlist(
                        message, link, audio_only, cookies, proxy, deno,
                        answer_target, reply, status_msg, cancel_event,
                    )
                except DownloadCancelled:
                    raise
                except Exception as playlist_err:
                    logger.warning(f"Playlist download failed, falling back to single video: {playlist_err}")
                    handled = False
                if handled:
                    return

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
                            answer_target, files, caption=cap, parse_mode="HTML",
                            reply_to=reply or message, silent=True,
                        )
                    except TypeError as silent_err:
                        if "silent" not in str(silent_err):
                            raise
                        await utils.answer_file(
                            answer_target, files, caption=cap, parse_mode="HTML",
                            reply_to=reply or message,
                        )

                try:
                    caption = convert_markdown_to_html(self.config["response_text"], link)
                    caption = caption.replace("{title}", title or "").replace("{quality}", "")
                    caption = f"{get_site_emoji_html(link)} {caption}"
                    if self.config["show_channel"] and channel:
                        channel_text = self.strings("default_channel").replace("{channel}", channel)
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
                            if not audio_path and idx == 0:
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

            instagram_files = None
            instagram_carousel_err = None
            if is_instagram and not audio_only and not force_translate:
                try:
                    instagram_files = await download_instagram_carousel(
                        link, utils.get_base_dir(), cookies_text=cookies, proxy=proxy
                    )
                except Exception as ig_err:
                    instagram_files = None
                    instagram_carousel_err = ig_err
                    logger.warning(f"Instagram carousel extraction failed, falling back to single-file: {ig_err}")

            if instagram_files:
                try:
                    site_icon = get_site_emoji_html(link)
                    safe_link_attr = html_escaping.escape(link, quote=True)
                    caption = f'{site_icon} <a href="{safe_link_attr}">Карусель</a>.'

                    chunks = [instagram_files[i:i + 10] for i in range(0, len(instagram_files), 10)]
                    for idx, chunk in enumerate(chunks):
                        chunk_caption = caption if idx == 0 else None
                        try:
                            await utils.answer_file(
                                answer_target, chunk, caption=chunk_caption, parse_mode="HTML",
                                reply_to=reply or message, silent=True,
                            )
                        except TypeError as silent_err:
                            if "silent" not in str(silent_err):
                                raise
                            await utils.answer_file(
                                answer_target, chunk, caption=chunk_caption, parse_mode="HTML",
                                reply_to=reply or message,
                            )

                    try:
                        await status_msg.delete()
                    except Exception:
                        pass
                finally:
                    for path in instagram_files:
                        try:
                            os.remove(path)
                        except Exception:
                            pass

                return

            if yandex_track_id or yandex_album_id or yandex_playlist or yandex_playlist_uuid:
                try:
                    collection_title = None
                    collection_artists = ""
                    collection_cover = None
                    track_ids = []
                    if yandex_track_id:
                        track_ids = [yandex_track_id]
                    elif yandex_album_id:
                        collection_title, collection_artists, track_ids, collection_cover = await fetch_yandex_album_tracks(
                            yandex_album_id, cookies_text=cookies
                        )
                    elif yandex_playlist:
                        collection_title, collection_artists, track_ids, collection_cover = await fetch_yandex_playlist_tracks(
                            yandex_playlist[0], yandex_playlist[1], cookies_text=cookies
                        )
                    else:
                        collection_title, collection_artists, track_ids, collection_cover = await fetch_yandex_playlist_by_uuid(
                            yandex_playlist_uuid, cookies_text=cookies
                        )

                    total_n = len(track_ids)
                    safe_link_attr = html_escaping.escape(link, quote=True)
                    downloaded = []
                    t0 = time.monotonic()

                    for idx, tid in enumerate(track_ids, 1):
                        if cancel_event is not None and cancel_event.is_set():
                            raise DownloadCancelled()
                        try:
                            if total_n > 1:
                                elapsed = time.monotonic() - t0
                                if idx > 1 and elapsed > 0:
                                    per = elapsed / (idx - 1)
                                    eta_left = format_seconds(max(0, int(per * (total_n - idx + 1))))
                                else:
                                    eta_left = self.strings("eta_unknown")
                                try:
                                    await status_msg.edit(
                                        f"{EMOJI_NOTE} <b>Скачиваю {idx}/{total_n}</b>\n"
                                        f"{EMOJI_CLOCK} <code>{eta_left}</code>\n"
                                        f"<code>{html_escaping.escape(collection_title or tid)}</code>"
                                    )
                                except Exception:
                                    pass

                            if yandex_track_id:
                                (ym_path, ym_title, ym_artist, ym_album, ym_duration,
                                 ym_cover_bytes, ym_meta_debug) = await download_yandex_music_track(
                                    link, utils.get_base_dir(), cookies_text=cookies, prefer_flac=raw_quality
                                )
                            else:
                                (ym_path, ym_title, ym_artist, ym_album, ym_duration,
                                 ym_cover_bytes, ym_meta_debug) = await download_yandex_track_by_id(
                                    tid, utils.get_base_dir(), cookies_text=cookies, prefer_flac=raw_quality
                                )

                            downloaded.append({
                                "path": ym_path,
                                "title": ym_title,
                                "artist": ym_artist,
                                "duration": ym_duration or 0,
                                "track_cover_bytes": ym_cover_bytes if total_n == 1 else None,
                                "flac": bool(ym_path) and ym_path.lower().endswith(".flac"),
                                "ext": (os.path.splitext(ym_path)[1].lstrip(".") or "mp3"),
                            })
                        except DownloadCancelled:
                            for item in downloaded:
                                p = item.get("path")
                                if p:
                                    try:
                                        os.remove(p)
                                    except Exception:
                                        pass
                            raise
                        except Exception as one_err:
                            logger.warning(f"Yandex track {tid} failed: {one_err}")
                            continue

                    if not downloaded:
                        raise ValueError("Не удалось скачать ни одного трека")

                    if cancel_event is not None and cancel_event.is_set():
                        for item in downloaded:
                            p = item.get("path")
                            if p:
                                try:
                                    os.remove(p)
                                except Exception:
                                    pass
                        raise DownloadCancelled()

                    coll_cover_path = None
                    if collection_cover:
                        coll_cover_path = os.path.join(
                            utils.get_base_dir(), f"ymcover_{uuid.uuid4().hex[:8]}.jpg"
                        )
                        async with aiofiles.open(coll_cover_path, "wb") as cf:
                            await cf.write(collection_cover)

                    if len(downloaded) == 1:
                        item = downloaded[0]
                        info_line = (
                            f"{item['title']} — {item['artist']}"
                            if item['artist'] and item['artist'] != "Unknown Artist" else item['title']
                        )
                        if item["flac"]:
                            caption = (
                                f'{get_site_emoji_html(link)} <a href="{safe_link_attr}"><b>Аудио</b></a>'
                                f'<b>. Flac</b>\n\n{info_line}'
                            )
                        else:
                            caption_head = convert_markdown_to_html(self.config["music_response_text"], link)
                            caption_head = caption_head.replace("{title}", "")
                            caption_head = re.sub(r"<(\w+)>\s*</\1>\s*$", "", caption_head).rstrip()
                            caption = f"{get_site_emoji_html(link)} {caption_head}\n\n{info_line}"
                        if item["duration"]:
                            caption += f"\n{EMOJI_CLOCK} {format_seconds(item['duration'])}"
                        safe_name = sanitize_media_filename(item["title"])
                        audio_attributes = [
                            DocumentAttributeFilename(f"{safe_name}.{item['ext']}"),
                            DocumentAttributeAudio(
                                duration=item["duration"],
                                title=item["title"],
                                performer=item["artist"],
                            ),
                        ]
                        thumb_path = None
                        cover_bytes = item.get("track_cover_bytes") or collection_cover
                        if cover_bytes:
                            await _yandex_stamp_cover(item["path"], cover_bytes)
                            thumb_path = os.path.join(
                                utils.get_base_dir(), f"ymcover_{uuid.uuid4().hex[:8]}.jpg"
                            )
                            async with aiofiles.open(thumb_path, "wb") as cf:
                                await cf.write(cover_bytes)
                        send_kwargs = dict(
                            caption=caption, parse_mode="HTML", reply_to=reply or message,
                            attributes=audio_attributes,
                        )
                        if thumb_path:
                            send_kwargs["thumb"] = thumb_path
                        try:
                            await utils.answer_file(answer_target, item["path"], silent=True, **send_kwargs)
                        except TypeError as silent_err:
                            if "silent" not in str(silent_err):
                                raise
                            await utils.answer_file(answer_target, item["path"], **send_kwargs)
                        if thumb_path and thumb_path != coll_cover_path:
                            try:
                                os.remove(thumb_path)
                            except Exception:
                                pass
                    else:
                        n = len(downloaded)
                        word = _ru_track_word(n)
                        coll = html_escaping.escape(collection_title or "Плейлист")
                        arts = html_escaping.escape(collection_artists or "")
                        if not arts:
                            from collections import Counter
                            c = Counter(
                                it["artist"] for it in downloaded
                                if it.get("artist") and it["artist"] != "Unknown Artist"
                            )
                            arts = html_escaping.escape(c.most_common(1)[0][0]) if c else ""
                        info_line = f"{coll} — {arts}" if arts else coll
                        group_caption = (
                            f'{get_site_emoji_html(link)} <a href="{safe_link_attr}"><b>Плейлист</b></a>. {n} {word}\n\n'
                            f'{info_line}'
                        )
                        try:
                            await status_msg.edit(f"{EMOJI_NOTE} <b>Отправляю {n} {word}...</b>")
                        except Exception:
                            pass

                        if collection_cover:
                            for item in downloaded:
                                await _yandex_stamp_cover(item["path"], collection_cover)

                        paths = [it["path"] for it in downloaded]
                        attrs_list = []
                        for item in downloaded:
                            safe_name = sanitize_media_filename(item["title"])
                            attrs_list.append([
                                DocumentAttributeFilename(f"{safe_name}.{item['ext']}"),
                                DocumentAttributeAudio(
                                    duration=item["duration"],
                                    title=item["title"],
                                    performer=item["artist"] or None,
                                ),
                            ])

                        album_items = [
                            {
                                "path": p,
                                "attributes": a,
                                "thumb": coll_cover_path,
                                "caption": None,
                            }
                            for p, a in zip(paths, attrs_list)
                        ]
                        album_items[-1]["caption"] = group_caption

                        reply_id = (reply or message).id
                        chunks = [album_items[i:i + 10] for i in range(0, len(album_items), 10)]

                        sent_so_far = 0
                        for chunk in chunks:
                            if cancel_event is not None and cancel_event.is_set():
                                raise DownloadCancelled()
                            await _send_audio_album(
                                answer_target.client, answer_target.peer_id, chunk,
                                reply_to_id=reply_id, silent=True,
                            )
                            sent_so_far += len(chunk)
                            remaining = n - sent_so_far
                            if remaining > 0:
                                try:
                                    await status_msg.edit(
                                        f"{EMOJI_NOTE} <b>Отправлено {sent_so_far}, отправляю ещё "
                                        f"{remaining} {_ru_track_word(remaining)}...</b>"
                                    )
                                except Exception:
                                    pass

                    try:
                        await status_msg.delete()
                    except Exception:
                        pass
                    if coll_cover_path:
                        try:
                            os.remove(coll_cover_path)
                        except Exception:
                            pass
                    for item in downloaded:
                        p = item.get("path")
                        if p:
                            try:
                                os.remove(p)
                            except Exception:
                                pass
                except DownloadCancelled:
                    try:
                        await status_msg.edit(self.strings("cancelled"))
                    except Exception:
                        pass
                except Exception as ym_err:
                    logger.warning(f"Yandex Music download failed: {ym_err}")
                    detail = clean_error_text(ym_err, cookies_text=cookies, proxy=proxy)
                    low = detail.lower()
                    if any(x in low for x in ("куки", "cookie", "session_id", "нужны куки", "авторизац")):
                        error_msg = cookies_error_message(
                            "Яндекс.Музыки", "music.yandex.ru/robots.txt", detail,
                        )
                    else:
                        error_msg = f"{EMOJI_WARN} <b>Яндекс.Музыка:</b>\n\n<code>{html_escaping.escape(detail)}</code>"
                    try:
                        await utils.answer(answer_target, error_msg)
                    except Exception:
                        pass
                return

            is_youtube_link = "youtube.com" in link.lower() or "youtu.be" in link.lower()
            is_short_link = is_youtube_link and "/shorts/" in link.lower()
            try:
                max_duration_minutes = int(self.config["max_duration"] or 0)
            except (TypeError, ValueError):
                max_duration_minutes = 0
            duration_probe = None
            if is_youtube_link and (self.config["auto_quality"] or max_duration_minutes) and not is_discord and not audio_only:
                duration_probe = await quick_probe_duration(link)

            if duration_probe is not None and max_duration_minutes and duration_probe > max_duration_minutes * 60:
                raise Exception(self.strings("too_long").replace("{minutes}", str(max_duration_minutes)))

            quality_mode = await decide_quality_mode(
                is_short_link, duration_probe,
                self.config["auto_quality"] and is_youtube_link, is_discord, audio_only
            )
            if raw_quality and not audio_only:
                quality_mode = "raw"
            compress_tier = "light" if (
                is_short_link or (duration_probe is not None and duration_probe <= QUALITY_LIGHT_VIDEO_SECONDS)
            ) else "medium"

            is_short_form_content = (
                is_short_form_by_url
                or (duration_probe is not None and duration_probe <= QUALITY_LIGHT_VIDEO_SECONDS)
            )
            if is_short_form_content and not progress["short_form"] and not audio_only:
                progress["short_form"] = True
                try:
                    await status_msg.edit(render_downloading_text())
                except Exception:
                    pass

            if quality_mode != "standard" and not audio_only:
                try:
                    await status_msg.edit(self.strings("quality_downloading"))
                except Exception:
                    pass

            audio_codecs_to_try = (
                ["flac", "mp3"] if (raw_quality and audio_only and is_audio_only_platform(link)) else ["mp3"]
            )

            media = title = channel = source_lang = None
            quality_info = None
            last_err = None
            used_quality_path = False
            for audio_codec in audio_codecs_to_try:
                for attempt_idx in range(2):
                    used_quality_path = False
                    quality_info = None
                    if is_discord:
                        try:
                            media, title, channel = await download_discord_video(link, utils.get_base_dir())
                            source_lang = None
                        except Exception as e:
                            last_err = e
                            media = None

                        if media and os.path.isfile(media) and os.path.getsize(media) > 0:
                            if not audio_only and not await has_video_stream(media):
                                try:
                                    os.remove(media)
                                except Exception:
                                    pass
                                last_err = Exception("Скачался файл без видеодорожки (только звук) — пробую ещё раз")
                                media = None
                                continue
                            break
                        media = None
                        continue

                    try:
                        media, title, channel, source_lang, quality_info = await download_media(
                            link,
                            cookies_text=cookies,
                            proxy=proxy,
                            deno_path=deno,
                            max_attempts=max_attempts,
                            audio_only=audio_only,
                            audio_codec=audio_codec,
                            sponsorblock_categories=sb_categories,
                            start_time=start_time,
                            end_time=end_time,
                            on_attempt=update_status,
                            on_progress=(None if is_short_form_content else update_eta),
                            cancel_event=cancel_event,
                            quality_mode=quality_mode,
                        )
                        used_quality_path = True
                    except DownloadCancelled:
                        raise
                    except Exception as primary_err:
                        last_err = primary_err
                        media = None
                        if is_tiktok:
                            try:
                                if audio_only:
                                    media, title, channel = await download_tiktok_audio_via_api(link, utils.get_base_dir())
                                else:
                                    media, title, channel = await download_tiktok_via_api(link, utils.get_base_dir())
                                source_lang = None
                            except DownloadCancelled:
                                raise
                            except Exception:
                                media = None
                        elif is_instagram:
                            try:
                                kk_link = re.sub(r"instagram\.com", "kkinstagram.com", link, flags=re.IGNORECASE)
                                media, title, channel, source_lang, quality_info = await download_media(
                                    kk_link,
                                    cookies_text=cookies,
                                    proxy=proxy,
                                    deno_path=deno,
                                    max_attempts=max_attempts,
                                    audio_only=audio_only,
                                    audio_codec=audio_codec,
                                    sponsorblock_categories=sb_categories,
                                    start_time=start_time,
                                    end_time=end_time,
                                    on_attempt=update_status,
                                    on_progress=(None if is_short_form_content else update_eta),
                                    cancel_event=cancel_event,
                                    quality_mode=quality_mode,
                                )
                                used_quality_path = True
                            except DownloadCancelled:
                                raise
                            except Exception:
                                media = None
                        elif is_twitter:
                            try:
                                fx_link = re.sub(
                                    r"(?:twitter\.com|x\.com)", "fxtwitter.com", link, flags=re.IGNORECASE
                                )
                                media, title, channel, source_lang, quality_info = await download_media(
                                    fx_link,
                                    cookies_text=cookies,
                                    proxy=proxy,
                                    deno_path=deno,
                                    max_attempts=max_attempts,
                                    audio_only=audio_only,
                                    audio_codec=audio_codec,
                                    sponsorblock_categories=sb_categories,
                                    start_time=start_time,
                                    end_time=end_time,
                                    on_attempt=update_status,
                                    on_progress=(None if is_short_form_content else update_eta),
                                    cancel_event=cancel_event,
                                    quality_mode=quality_mode,
                                )
                                used_quality_path = True
                            except DownloadCancelled:
                                raise
                            except Exception:
                                media = None

                    if media and os.path.isfile(media) and os.path.getsize(media) > 0:
                        if not audio_only and not await has_video_stream(media):
                            try:
                                os.remove(media)
                            except Exception:
                                pass
                            last_err = Exception("Скачался файл без видеодорожки (только звук) — пробую ещё раз")
                            media = None
                            continue
                        break
                    media = None
                if media:
                    break

            if not media:
                raise last_err or Exception(self.strings("done_fallback"))

            if used_quality_path and (
                quality_mode in ("best", "capped_2k")
                or (quality_mode == "standard" and not is_short_form_content and not audio_only)
            ):
                try:
                    async def update_compress_eta(eta_seconds):
                        eta_text = format_seconds(max(0, int(eta_seconds)))
                        if progress["eta"] == eta_text:
                            return
                        progress["eta"] = eta_text
                        try:
                            await status_msg.edit(render_downloading_text())
                        except Exception:
                            pass

                    if compress_tier == "medium":
                        progress["eta"] = self.strings("eta_unknown")
                        try:
                            await status_msg.edit(render_downloading_text())
                        except Exception:
                            pass
                    hw_encoder = self.get("hw_encoder")
                    if hw_encoder not in MEDIUM_COMPRESS_ARGS:
                        hw_encoder = await probe_hw_encoder()
                        self.set("hw_encoder", hw_encoder)
                    compressed = await compress_video(
                        media, hw_encoder, tier=compress_tier,
                        duration_hint=(quality_info or {}).get("duration"),
                        on_progress=update_compress_eta,
                        cancel_event=cancel_event,
                    )
                    if compressed:
                        media = compressed
                except DownloadCancelled:
                    raise
                except Exception as compress_err:
                    logger.warning(f"Auto-quality compression failed: {compress_err}")

            if not await target_still_exists(message, status_msg):
                try:
                    if media and os.path.exists(media):
                        os.remove(media)
                except Exception:
                    pass
                return

            translation_marker = ""
            if force_translate and not audio_only:
                ub_lang_raw = (self.db.get("heroku.translations", "lang", "en") or "en").strip().lower()
                ub_lang_code = ub_lang_raw.split()[0] if ub_lang_raw else "en"
                vo_lang = "ru" if ub_lang_code in ("ru", "uk", "ua") else "en"
                source_lang_norm = (source_lang or "").split("-")[0].strip().lower()

                if source_lang_norm and source_lang_norm == vo_lang:
                    pass
                else:
                    vo_attempts = 2
                    vo_err = None
                    for vo_attempt in range(1, vo_attempts + 1):
                        try:
                            is_short_vo = bool(quality_info and quality_info.get("duration")
                                               and quality_info["duration"] <= QUALITY_LIGHT_VIDEO_SECONDS)

                            try:
                                if is_short_vo:
                                    await status_msg.edit(self.strings("vo_translating_simple"))
                                else:
                                    await status_msg.edit(
                                        self.strings("vo_translating").replace("{eta}", self.strings("eta_unknown"))
                                    )
                            except Exception:
                                pass

                            vo_eta_state = {"value": None}

                            async def update_vo_eta(eta_seconds):
                                eta_text = format_seconds(max(0, int(eta_seconds)))
                                if vo_eta_state["value"] == eta_text:
                                    return
                                vo_eta_state["value"] = eta_text
                                try:
                                    await status_msg.edit(
                                        self.strings("vo_translating").replace("{eta}", eta_text)
                                    )
                                except Exception:
                                    pass

                            audio_url, _ = await get_translated_audio(
                                link, response_lang=vo_lang,
                                on_progress=(None if is_short_vo else update_vo_eta),
                            )
                            media = await mux_translated_audio(media, audio_url, orig_volume_percent=self.config["vo_orig_volume"], clip_start=start_time)
                            translation_marker = f"{EMOJI_GLOBE} {lang_display(source_lang)} ➔ {lang_display(vo_lang)}\n"
                            vo_err = None
                            break
                        except Exception as e:
                            vo_err = e
                            if vo_attempt < vo_attempts:
                                logger.warning(f"VOT translation failed (attempt {vo_attempt}/{vo_attempts}), retrying: {e}")
                                continue

                    if vo_err is not None:
                        logger.warning(f"VOT translation failed: {vo_err}")
                        try:
                            if isinstance(vo_err, NodeVersionError):
                                vo_error_text = vo_err.html_message
                            else:
                                vo_error_text = self.strings("vo_failed").replace("{error}", clean_error_text(vo_err))
                            await message.client.send_message(
                                message.chat_id, vo_error_text, parse_mode="HTML", reply_to=message.id,
                            )
                        except Exception:
                            pass

            if not (media and os.path.isfile(media) and os.path.getsize(media) > 0):
                raise Exception(self.strings("done_fallback"))

            clip_marker = ""
            if start_time is not None or end_time is not None:
                clip_marker = (
                    f" {EMOJI_SCISSORS}(<code>{format_seconds(start_time or 0)}-"
                    f"{format_seconds(end_time) if end_time is not None else '…'}</code>)"
                )

            link_lower = link.lower()
            if "twitter.com" in link_lower or "x.com" in link_lower:
                title = clean_twitter_title(title)
            elif "myinstants.com" in link_lower:
                title = clean_myinstants_title(title)
            elif "tenor.com" in link_lower:
                title = clean_tenor_title(title)

            quality_line = ""
            if not audio_only and quality_info and quality_info.get('height'):
                codec = (quality_info.get('vcodec') or '').split('.')[0]
                quality_line = f"{quality_info['height']}p | {codec}" if codec else f"{quality_info['height']}p"

            if audio_only:
                if is_audio_only_platform(link):
                    caption_head = convert_markdown_to_html(self.config["music_response_text"], link)
                    caption_head = caption_head.replace("{title}", "").replace("{quality}", quality_line)
                    caption_head = re.sub(r"<(\w+)>\s*</\1>\s*$", "", caption_head).rstrip()
                    caption = f"{get_site_emoji_html(link)} {caption_head}"

                    info_line = f"{title} — {channel}" if (self.config["show_channel"] and channel) else (title or "")
                    if info_line:
                        caption += f"\n\n{info_line}"

                    duration_line = None
                    if "myinstants.com" not in link.lower():
                        try:
                            probe = MutagenFile(media)
                            if probe and probe.info and getattr(probe.info, "length", None):
                                duration_line = f"{EMOJI_CLOCK} {format_seconds(int(probe.info.length))}"
                        except Exception:
                            pass
                    if duration_line:
                        caption += f"\n{duration_line}"
                else:
                    caption = convert_markdown_to_html(self.config["music_response_text"], link)
                    caption = caption.replace("{title}", title or "").replace("{quality}", quality_line)
                    caption = f"{EMOJI_NOTE} {caption}"
            else:
                IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".heic")
                media_ext = os.path.splitext(media)[1].lower() if media else ""
                is_downloaded_gif = media_ext == ".gif" or "tenor.com" in link.lower()
                is_downloaded_photo = bool(media) and (media_ext in IMAGE_EXTENSIONS or is_downloaded_gif)
                if self.config["show_link"]:
                    caption_template = self.config["response_text"]
                    caption = convert_markdown_to_html(caption_template, link)
                    caption = caption.replace("{title}", title or "")
                    caption = caption.replace("{quality}", quality_line)
                    if is_downloaded_gif:
                        for src_word, dst_word in (("Видео", "Гиф"), ("видео", "гиф"), ("ВИДЕО", "ГИФ")):
                            caption = caption.replace(src_word, dst_word)
                    elif is_downloaded_photo:
                        for src_word, dst_word in (("Видео", "Фото"), ("видео", "фото"), ("ВИДЕО", "ФОТО")):
                            caption = caption.replace(src_word, dst_word)
                    icon = EMOJI_PHOTO if is_downloaded_photo else get_site_emoji_html(link)
                    caption = f"{icon} {caption}"

                    if translation_marker:
                        lines = caption.split("\n", 1)
                        lines[0] = translation_marker + lines[0]
                        caption = "\n".join(lines)

                    if clip_marker:
                        lines = caption.split("\n", 1)
                        lines[0] = lines[0] + clip_marker
                        caption = "\n".join(lines)

                    if self.config["show_channel"] and channel:
                        channel_text = self.strings("default_channel").replace("{channel}", channel)
                        caption += f"\n\n{channel_text}"
                else:
                    caption = (translation_marker + (title or self.strings("done_fallback"))) + clip_marker

            send_attributes = None
            send_extra = {}
            if audio_only:
                safe_title = sanitize_media_filename(title)
                ext = (os.path.splitext(media)[1].lstrip(".") or audio_codec)
                send_attributes = [
                    DocumentAttributeFilename(f"{safe_title}.{ext}"),
                    DocumentAttributeAudio(
                        duration=int((quality_info or {}).get("duration") or 0),
                        performer=channel or None,
                        voice=False,
                    ),
                ]
                if "myinstants.com" in link.lower():
                    cover_path = await get_myinstants_cover_path(utils.get_base_dir())
                    if cover_path:
                        send_extra["thumb"] = cover_path

            try:
                await utils.answer_file(
                    answer_target,
                    media,
                    caption=caption,
                    parse_mode="HTML",
                    reply_to=reply or message,
                    silent=True,
                    force_document=raw_quality and not audio_only,
                    attributes=send_attributes,
                    **send_extra,
                )
            except TypeError as silent_err:
                if "silent" not in str(silent_err):
                    raise
                await utils.answer_file(
                    answer_target,
                    media,
                    caption=caption,
                    parse_mode="HTML",
                    reply_to=reply or message,
                    force_document=raw_quality and not audio_only,
                    attributes=send_attributes,
                    **send_extra,
                )

            try:
                await status_msg.delete()
            except:
                pass
            try:
                os.remove(media)
            except:
                pass

        except DownloadCancelled:
            try:
                await status_msg.edit(self.strings("cancelled"))
            except Exception:
                pass

        except Exception as e:
            if silent_errors:
                try:
                    log_channel_id = self.get("log_channel_id")
                    log_topic_id = self.get("log_topic_id")
                    if not log_channel_id:
                        log_channel_id = logging.getLogger().handlers[0].get_logid_by_client(message.client.tg_id)
                        log_topic_id = None

                    log_text = (
                        f"{EMOJI_WARN} <b>YouTube-DLD: автозагрузка не смогла скачать ссылку</b>\n\n"
                        f"Чат: <code>{message.chat_id}</code>\n"
                        f"Ссылка: <code>{link}</code>\n\n"
                        f"<code>{clean_error_text(e)}</code>"
                    )
                    try:
                        await message.client.send_message(
                            log_channel_id, log_text, parse_mode="HTML", reply_to=log_topic_id,
                        )
                    except Exception:
                        self.set("log_topic_id", None)
                        try:
                            await message.client.send_message(log_channel_id, log_text, parse_mode="HTML")
                        except Exception:
                            pass
                except Exception:
                    pass
                try:
                    await status_msg.delete()
                except Exception:
                    pass
                try:
                    if 'media' in locals():
                        os.remove(media)
                except Exception:
                    pass
                return

            error_str = str(e)
            needs_cookies = ("sign in to confirm" in error_str.lower() or "confirm you" in error_str.lower()
                              or "login required" in error_str.lower())
            twitter_needs_cookies = is_twitter and "no video could be found" in error_str.lower()
            saveasbot_eligible = is_tiktok or is_instagram or is_pinterest

            if needs_cookies:
                if is_instagram:
                    error_msg = cookies_error_message(
                        "Instagram", "instagram.com/robots.txt",
                        clean_error_text(instagram_carousel_err or e, cookies_text=cookies, proxy=proxy),
                    )
                else:
                    error_msg = (
                        f"{EMOJI_CROSS} <b>Загрузка не удалась</b> (нужны куки).\n\n"
                        f"<code>{clean_error_text(instagram_carousel_err or e, cookies_text=cookies, proxy=proxy)}</code>"
                    )
            elif twitter_needs_cookies:
                error_msg = cookies_error_message("Twitter/X", "x.com/robots.txt", clean_error_text(e, cookies_text=cookies, proxy=proxy))
            else:
                error_msg = f"{EMOJI_WARN} " + self.config["error_text"].replace("{error}", clean_error_text(e, cookies_text=cookies, proxy=proxy))

            if saveasbot_eligible and is_instagram:
                reply_target = reply or message
                await self._saveasbot_fallback(
                    status_msg, link, message.chat_id,
                    reply_target.id if reply_target else message.id, audio_only,
                )
            elif saveasbot_eligible:
                reply_target = reply or message
                try:
                    await self.inline.form(
                        text=error_msg,
                        message=message,
                        reply_markup=[[{
                            "text": "📥 Скачать через @SaveAsBot",
                            "callback": self._saveasbot_fallback,
                            "args": (link, message.chat_id, reply_target.id if reply_target else message.id, audio_only),
                        }]],
                    )
                except Exception:
                    await utils.answer(answer_target, error_msg)
            else:
                await utils.answer(answer_target, error_msg)
            try:
                if 'media' in locals():
                    os.remove(media)
            except:
                pass

        finally:
            self._download_queue.release(queue_entry)
            self._unregister_active_job(resume_job_id)
            try:
                active_downloads = self.get("active_downloads", {})
                active_downloads.pop(resume_job_id, None)
                self.set("active_downloads", active_downloads)
            except Exception:
                pass
