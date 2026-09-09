# meta developer: @RUIS_VlP, @RoKrz
# meta banner: https://raw.githubusercontent.com/Ruslan-Isaev/modules/refs/heads/main/photos/banner.jpg
# meta pic: https://kappa.lol/21nHvy
# requires: yt_dlp aiohttp aiofiles mutagen

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
from herokutl.tl.functions.messages import SendMessageRequest, UploadMediaRequest, UpdatePinnedMessageRequest, GetPeerDialogsRequest
from herokutl.tl.functions.account import UpdateNotifySettingsRequest, GetNotifySettingsRequest
from herokutl.tl.types import (
    DocumentAttributeAudio,
    DocumentAttributeFilename,
    InputDialogPeer,
    InputMediaUploadedPhoto,
    InputNotifyPeer,
    InputPeerNotifySettings,
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

EMOJI_OK = "<tg-emoji emoji-id=5350572310627632617>вњ…</tg-emoji>"
EMOJI_FAIL = "<tg-emoji emoji-id=5348514879558926674>рџ‘Ћ</tg-emoji>"
EMOJI_WARN = "<tg-emoji emoji-id=5350477112677515642>вљ пёЏ</tg-emoji>"
EMOJI_DOWNLOAD = "<tg-emoji emoji-id=5899757765743615694>рџ“Ґ</tg-emoji>"
EMOJI_COMPRESS = "<tg-emoji emoji-id=5988023995125993550>рџ› </tg-emoji>"
EMOJI_INFO = "<tg-emoji emoji-id=5879785854284599288>в„№пёЏ</tg-emoji>"
EMOJI_NOTE = "<tg-emoji emoji-id=5891249688933305846>рџЋµ</tg-emoji>"
EMOJI_CHECK = "<tg-emoji emoji-id=5985596818912712352>вњ…</tg-emoji>"
EMOJI_CROSS = "<tg-emoji emoji-id=5985346521103604145>вќЊ</tg-emoji>"
EMOJI_SCISSORS = "<tg-emoji emoji-id=5870462219019358212>вњ‚пёЏ</tg-emoji>"
EMOJI_GEAR = "<tg-emoji emoji-id=5877260593903177342>вљ™пёЏ</tg-emoji>"
EMOJI_MIC = "<tg-emoji emoji-id=5350790271627968474>рџ—ЈпёЏ</tg-emoji>"
EMOJI_ARROW = "<tg-emoji emoji-id=5875506366050734240>вћЎпёЏ</tg-emoji>"
EMOJI_GLOBE = "<tg-emoji emoji-id=5879585266426973039>рџЊђ</tg-emoji>"
EMOJI_COOKIE = "<tg-emoji emoji-id=5845945815549350824>рџЌЄ</tg-emoji>"
EMOJI_WAND = "<tg-emoji emoji-id=5785326857587003471>рџЄ„</tg-emoji>"
EMOJI_CLOCK = "<tg-emoji emoji-id=5776213190387961618>рџ•“</tg-emoji>"
EMOJI_PHOTO = "<tg-emoji emoji-id=5766879414704935108>рџ–ј</tg-emoji>"

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def clean_error_text(text):
    text = ANSI_RE.sub("", str(text))
    text = re.sub(r"^ERROR:\s*", "", text.strip())
    text = re.sub(r"^\[\w+\]\s*[\w.-]+:\s*", "", text)
    text = re.sub(r":\s+", ":\n", text)
    return text.strip()


def cookies_error_message(site_name, robots_url, detail):
    """Р•РґРёРЅС‹Р№ С‚РµРєСЃС‚ РѕС€РёР±РєРё РЅРµС…РІР°С‚РєРё РєСѓРєРё вЂ” С‚РѕС‚ Р¶Рµ, С‡С‚Рѕ РїСЂРё РѕР±С‹С‡РЅРѕР№ РЅРµС…РІР°С‚РєРµ РєСѓРєРё YouTube,
    РїР»СЋСЃ СЏРІРЅРѕРµ РїРѕСЏСЃРЅРµРЅРёРµ, С‡С‚Рѕ РґР»СЏ СЌС‚РѕРіРѕ СЃР°Р№С‚Р° РЅСѓР¶РµРЅ Р’РўРћР РћР™, РѕС‚РґРµР»СЊРЅС‹Р№ РЅР°Р±РѕСЂ РєСѓРєРё, РґРѕР±Р°РІР»РµРЅРЅС‹Р№
    РѕС‚РґРµР»СЊРЅС‹Рј СЌР»РµРјРµРЅС‚РѕРј СЃРїРёСЃРєР° youtube_cookies (СЂСЏРґРѕРј СЃ РєСѓРєР°РјРё YouTube, РЅРµ РІРјРµСЃС‚Рѕ РЅРёС…)."""
    return (
        f"{EMOJI_CROSS} <b>РћС€РёР±РєР° РєСѓРєРё.</b> РџСЂРѕСЃСЊР±Р° РІСЃС‚Р°РІРёС‚СЊ РєСѓРєРё С‡РµСЂРµР· РєРѕРјР°РЅРґСѓ "
        f"<code>.cfg YouTube-DLD youtube_cookies</code>.\n"
        f"Р•СЃР»Рё РєСѓРєРё YouTube С‚Р°Рј СѓР¶Рµ РµСЃС‚СЊ вЂ” РґРѕР±Р°РІСЊС‚Рµ РµС‰С‘ Рё РєСѓРєРё {site_name} РѕС‚РґРµР»СЊРЅС‹Рј СЌР»РµРјРµРЅС‚РѕРј "
        f"СЃРїРёСЃРєР° (В«Р”РѕР±Р°РІРёС‚СЊ СЌР»РµРјРµРЅС‚В»): РѕС‚РєСЂРѕР№С‚Рµ Р·Р°Р»РѕРіРёРЅРµРЅРЅС‹РјРё <code>{robots_url}</code>, "
        f"СЌРєСЃРїРѕСЂС‚РёСЂСѓР№С‚Рµ РєСѓРєРё С‚РµРј Р¶Рµ Cookie-Editor РІ С„РѕСЂРјР°С‚Рµ Netscape Рё РІСЃС‚Р°РІСЊС‚Рµ вЂ” РЅСѓР¶РЅС‹ РѕР±Р° РЅР°Р±РѕСЂР° "
        f"СЃСЂР°Р·Сѓ, РєР°Р¶РґС‹Р№ СЃРІРѕРёРј СЌР»РµРјРµРЅС‚РѕРј.\n\n"
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
    """РџР»РѕС‰Р°РґРєРё, РіРґРµ РІРёРґРµРѕ РІ РїСЂРёРЅС†РёРїРµ РЅРµС‚ вЂ” С‚РѕР»СЊРєРѕ Р·РІСѓРє (VK-Р°СѓРґРёРѕ/РјСѓР·С‹РєР° РІС…РѕРґСЏС‚ РѕС‚РґРµР»СЊРЅРѕР№
    РїСЂРѕРІРµСЂРєРѕР№, Сѓ РЅРёС… РЅРµС‚ РµРґРёРЅРѕРіРѕ РґРѕРјРµРЅР°-РїР°С‚С‚РµСЂРЅР° СЃ РѕСЃС‚Р°Р»СЊРЅС‹РјРё)."""
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


def clean_cookies_text(raw_text):
    """РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ РѕР±С‹С‡РЅРѕ РІСЃС‚Р°РІР»СЏРµС‚ РІ youtube_cookies РІРµСЃСЊ СЌРєСЃРїРѕСЂС‚ Cookie-Editor С†РµР»РёРєРѕРј вЂ”
    РґРµСЃСЏС‚РєРё РєСѓРє СЃ РїРѕСЃС‚РѕСЂРѕРЅРЅРёС… РґРѕРјРµРЅРѕРІ РїР»СЋСЃ С€Р°РїРєР°-РєРѕРјРјРµРЅС‚Р°СЂРёР№. РњРѕРґСѓР»СЋ РёР· СЌС‚РѕРіРѕ СЂРµР°Р»СЊРЅРѕ РЅСѓР¶РЅС‹
    С‚РѕР»СЊРєРѕ РєСѓРєРё YouTube, РЇРЅРґРµРєСЃР°, VK Рё Instagram вЂ” РѕСЃС‚Р°Р»СЊРЅРѕРµ (Рё РєРѕРјРјРµРЅС‚Р°СЂРёРё) РІС‹РєРёРґС‹РІР°РµРј, Р°
    С‚Рѕ, С‡С‚Рѕ РЅСѓР¶РЅРѕ, РѕСЃС‚Р°РІР»СЏРµРј СЃРіСЂСѓРїРїРёСЂРѕРІР°РЅРЅС‹Рј РІ РїРѕСЂСЏРґРєРµ СЋС‚ в†’ РјСѓР·С‹РєР° в†’ vk в†’ РёРЅСЃС‚Р°. РЎС‚СЂРѕРєРё РІРёРґР°
    '#HttpOnly_.youtube.com ...' вЂ” СЌС‚Рѕ РќР• РєРѕРјРјРµРЅС‚Р°СЂРёР№, Р° РѕР±С‹С‡РЅР°СЏ HttpOnly-РєСѓРєР° РІ С„РѕСЂРјР°С‚Рµ
    curl/Netscape, РѕС‚Р»РёС‡РёС‚СЊ РёС… РѕС‚ РЅР°СЃС‚РѕСЏС‰РёС… РєРѕРјРјРµРЅС‚Р°СЂРёРµРІ ("# Netscape HTTP Cookie File" Рё
    С‚.Рї.) РјРѕР¶РЅРѕ РїРѕ С‡РёСЃР»Сѓ С‚Р°Р±РѕРІ: Сѓ РЅР°СЃС‚РѕСЏС‰РµР№ СЃС‚СЂРѕРєРё РєСѓРєРё РёС… РІСЃРµРіРґР° 6."""
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
        r"(https?://)?(www\.)?reddit\.com/r/[^\s]+/comments/[^\s]+",
        r"(https?://)?(www\.)?vimeo\.com/[^\s]+",
        r"(https?://)?(www\.)?dailymotion\.com/video/[^\s]+",
        r"(https?://)?(www\.)?twitch\.tv/(videos/|clip/|[^/]+$)[^\s]*",
        r"(https?://)?(www\.)?streamable\.com/[^\s]+",
        r"(https?://)?(music\.)?yandex\.(ru|com|by|kz|ua)/album/[^\s]+",
        r"(https?://)?(music\.)?yandex\.(ru|com|by|kz|ua)/track/[^\s]+",
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
    (("youtube.com/shorts",), "рџ”ґ", "5352632932857035523"),
    (("youtube.com", "youtu.be"), "рџ”ґ", "5355235592844095825"),
    (("tiktok.com",), "рџЋµ", "5353034628263330616"),
    (("instagram.com",), "рџ“ё", "5355097780228470775"),
    (("x.com", "twitter.com"), "рџђ¦", "5355148941878900494"),
    (("facebook.com",), "рџ‘Ґ", "5355254460635428635"),
    (("vimeo.com",), "рџЋ¬", "5334764984142412896"),
    (("twitch.tv",), "рџЋ®", "5352759664457038886"),
    (("reddit.com",), "рџ‘Ѕ", "5352531593103686999"),
    (("music.yandex",), "рџЋ§", "5346296430166293639"),
    (("soundcloud.com",), "вЃпёЏ", "5345844509412444249"),
    (("bandcamp.com",), "рџЋё", "5451966206334513619"),
    (("spotify.com",), "рџџў", "5346074681004801565"),
    (("rutube.ru",), "в–¶пёЏ", "5298747646096187189"),
    (("vk.com/clip", "vk.ru/clip"), "рџЋҐ", "5280894678227492455"),
    (("vk.com", "vk.ru"), "рџ”µ", "5278229754099540071"),
    (("ok.ru",), "рџџ ", "5310076528577491230"),
    (("cdn.discordapp.com", "media.discordapp.net"), "рџЋ®", "5352866798121271480"),
    (("pornhub.com",), "рџ”ћ", "5370975411033356097"),
    (("likee.video", "likee.com"), "рџЊђ", "5352672553930342216"),
    (("snapchat.com",), "рџЊђ", "5352719553757466112"),
    (("pinterest.com", "pin.it"), "рџ“·", "5303183810442044150"),
    (("steamcommunity.com", "store.steampowered.com"), "рџЋ®", "5298975451161565553"),
    (("github.com",), "рџ’»", "5303382121967001310"),
]


def get_site_emoji_html(url):
    url_lower = (url or "").lower()
    for domains, fallback, premium_id in SITE_EMOJI:
        if any(d in url_lower for d in domains):
            if premium_id:
                return f'<tg-emoji emoji-id="{premium_id}">{fallback}</tg-emoji>'
            return fallback
    return '<tg-emoji emoji-id="6005986106703613755">рџЋҐ</tg-emoji>'


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
    """РџСЂРѕРІРµСЂСЏРµС‚, С‡С‚Рѕ РїСЂРѕРєСЃРё СЂРµР°Р»СЊРЅРѕ СЂР°Р±РѕС‚Р°РµС‚, Р° РЅРµ РїСЂРѕСЃС‚Рѕ РѕС‚РІРµС‡Р°РµС‚ РЅР° TCP-С…РµРЅРґС€РµР№Рє. Р”Р»СЏ
    HTTP(S)-РїСЂРѕРєСЃРё РґРµР»Р°РµРј РЅР°СЃС‚РѕСЏС‰РёР№ CONNECT-С‚СѓРЅРЅРµР»СЊ Рє СЌС‚Р°Р»РѕРЅРЅРѕРјСѓ С…РѕСЃС‚Сѓ вЂ” РјС‘СЂС‚РІС‹Р№/В«РїРѕР»СѓР¶РёРІРѕР№В»
    РїСЂРѕРєСЃРё, РєРѕС‚РѕСЂС‹Р№ РїСЂРёРЅРёРјР°РµС‚ СЃРѕРµРґРёРЅРµРЅРёРµ, РЅРѕ РЅРёС‡РµРіРѕ РЅРµ РїСЂРѕРєСЃРёСЂСѓРµС‚, С‚Р°РєСѓСЋ РїСЂРѕРІРµСЂРєСѓ РЅРµ РїСЂРѕР№РґС‘С‚.
    Р”Р»СЏ SOCKS (РєРѕС‚РѕСЂРѕРјСѓ СЌС‚РѕС‚ СЃС‚РµРє РЅР°РїСЂСЏРјСѓСЋ РЅРµ СѓРјРµРµС‚) РѕСЃС‚Р°С‘С‚СЃСЏ TCP-РїСЂРѕРІРµСЂРєР° вЂ” РѕРЅР° С…РѕС‚СЏ Р±С‹
    РѕС‚СЃРµРєР°РµС‚ СЏРІРЅРѕ РЅРµРґРѕСЃС‚СѓРїРЅС‹Рµ Р°РґСЂРµСЃР°."""
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
    'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/'
    'bestvideo[height<=720]+bestaudio/best[height<=720]/'
    'bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/'
    'bestvideo[height<=480]+bestaudio/best[height<=480]/'
    'bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/'
    'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
)
FORMAT_CAPPED_2K = (
    'bestvideo[height<=1080]+bestaudio/best[height<=1080]/'
    'bestvideo[height<=720]+bestaudio/best[height<=720]/best'
)
FORMAT_RAW_1080 = (
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
    """РџСЂРѕР±СѓРµС‚ СЂРµР°Р»СЊРЅРѕ Р·Р°РєРѕРґРёСЂРѕРІР°С‚СЊ С‚РµСЃС‚РѕРІС‹Р№ РєР°РґСЂ РєР°Р¶РґС‹Рј Р°РїРїР°СЂР°С‚РЅС‹Рј СЌРЅРєРѕРґРµСЂРѕРј РїРѕ РѕС‡РµСЂРµРґРё
    (NVIDIA в†’ AMD в†’ Intel). РџРµСЂРІС‹Р№, РєРѕС‚РѕСЂС‹Р№ Р·Р°РІС‘Р»СЃСЏ вЂ” С‚Рѕ Рё РµСЃС‚СЊ Р¶РµР»РµР·Рѕ РЅР° СЌС‚РѕР№ РјР°С€РёРЅРµ.
    Р•СЃР»Рё РЅРµ Р·Р°РІС‘Р»СЃСЏ РЅРё РѕРґРёРЅ (РЅРµС‚ GPU/РґСЂРѕРІ вЂ” РѕР±С‹С‡РЅРѕРµ РґРµР»Рѕ РЅР° РіРѕР»РѕРј VPS/РІ РґРѕРєРµСЂРµ) вЂ” РµРґРµРј РЅР° CPU."""
    for encoder_name in HW_ENCODER_PROBE_ORDER:
        if await _ffmpeg_encoder_works(MEDIUM_COMPRESS_ARGS[encoder_name]):
            return encoder_name
    return "libx264"


EMOJI_QUEUE = "<tg-emoji emoji-id=5348557584418750233>рџ•’</tg-emoji>"


class QueueCancelled(Exception):
    """РџРѕР»СЊР·РѕРІР°С‚РµР»СЊ (РёР»Рё РєС‚Рѕ СѓРіРѕРґРЅРѕ РІ С‡Р°С‚Рµ) СѓРґР°Р»РёР» СЃРѕРѕР±С‰РµРЅРёРµ РѕР± РѕР¶РёРґР°РЅРёРё РІ РѕС‡РµСЂРµРґРё вЂ”
    РѕС‚РјРµРЅСЏРµРј СЌС‚Сѓ Р·Р°РіСЂСѓР·РєСѓ, РЅРµ РЅР°С‡РёРЅР°СЏ РµС‘."""
    pass


class DownloadCancelled(Exception):
    """.dlstop вЂ” СЋР·РµСЂ СЃР°Рј РѕСЃС‚Р°РЅРѕРІРёР» Р°РєС‚РёРІРЅСѓСЋ Р·Р°РіСЂСѓР·РєСѓ."""
    pass


class DownloadTurnQueue:
    """FIFO-РѕС‡РµСЂРµРґСЊ СЃ РІРёРґРёРјС‹РјРё РїРѕР·РёС†РёСЏРјРё Рё РїРѕРґРґРµСЂР¶РєРѕР№ РѕС‚РјРµРЅС‹: РїРѕРєР° Р¶РґС‘С€СЊ СЃРІРѕРµР№ РѕС‡РµСЂРµРґРё,
    РІ СЃС‚Р°С‚СѓСЃРµ РІРёРґРЅРѕ РјРµСЃС‚Рѕ (Р’РёРґРµРѕ РІ РѕС‡РµСЂРµРґРё(N)...). Р•СЃР»Рё СѓРґР°Р»РёС‚СЊ СЌС‚Рѕ СЃРѕРѕР±С‰РµРЅРёРµ, РѕР¶РёРґР°СЋС‰РёР№
    СЃР°Рј РІС‹РїР°РґР°РµС‚ РёР· РѕС‡РµСЂРµРґРё РїСЂРё СЃР»РµРґСѓСЋС‰РµР№ РїСЂРѕРІРµСЂРєРµ, Рё СЃР»РµРґСѓСЋС‰РёРµ СЃРґРІРёРіР°СЋС‚СЃСЏ РІРїРµСЂС‘Рґ вЂ”
    Р·Р°С‰РёС‚Р° РѕС‚ OOM (СЃРј. release/acquire) РѕСЃС‚Р°С‘С‚СЃСЏ С‚РѕР№ Р¶Рµ: С‚СЏР¶С‘Р»С‹Рµ Р·Р°РіСЂСѓР·РєРё СЃС‚СЂРѕРіРѕ РїРѕ РѕРґРЅРѕР№."""

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
        """РЈР±РёСЂР°РµС‚ РёР· РѕС‡РµСЂРµРґРё Р·Р°РїРёСЃРё, РєРѕС‚РѕСЂС‹Рµ РµС‰С‘ СЂРµР°Р»СЊРЅРѕ Р–Р”РЈРў СЃРІРѕРµР№ РѕС‡РµСЂРµРґРё (РЅРµ Р·Р°Р±СЂР°Р»Рё
        event) вЂ” РёР»Рё С‚РѕР»СЊРєРѕ РґР»СЏ chat_id, РµСЃР»Рё РѕРЅ РїРµСЂРµРґР°РЅ. Р—Р°РїРёСЃСЊ Р°РєС‚РёРІРЅРѕР№ Р·Р°РіСЂСѓР·РєРё
        acquire() РЅРµ СѓР±РёСЂР°РµС‚ РёР· _waiters РїСЂРё РІС‹РґР°С‡Рµ С…РѕРґР° (РѕРЅР° С‚Р°Рј Рё РѕСЃС‚Р°С‘С‚СЃСЏ, РїСЂРѕСЃС‚Рѕ СЃ
        set() СЃРѕР±С‹С‚РёРµРј, РєР°Рє "С‚РµРєСѓС‰РёР№ С„СЂРѕРЅС‚"), РїРѕСЌС‚РѕРјСѓ Р±РµР· С„РёР»СЊС‚СЂР° РїРѕ event.is_set() С‚СѓС‚
        Р·Р°РґРІР°РёРІР°Р»СЃСЏ СЃС‡С‘С‚ СЃ _active_jobs РІ .dlstop вЂ” РѕРґРЅР° Рё С‚Р° Р¶Рµ Р·Р°РіСЂСѓР·РєР° СЃС‡РёС‚Р°Р»Р°СЃСЊ
        Рё Р°РєС‚РёРІРЅРѕР№, Рё СЃС‚РѕСЏС‰РµР№ РІ РѕС‡РµСЂРµРґРё РѕРґРЅРѕРІСЂРµРјРµРЅРЅРѕ."""
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
    """РџСЂРѕРІРµСЂСЏРµС‚, С‡С‚Рѕ СЃРѕРѕР±С‰РµРЅРёРµ(-СЏ), Рє РєРѕС‚РѕСЂС‹Рј РїСЂРёРІСЏР·Р°РЅР° Р·Р°РіСЂСѓР·РєР°, РІСЃС‘ РµС‰С‘ СЃСѓС‰РµСЃС‚РІСѓСЋС‚ вЂ” РµСЃР»Рё
    СЋР·РµСЂ (РёР»Рё РєС‚Рѕ СѓРіРѕРґРЅРѕ РІ С‡Р°С‚Рµ) СѓРґР°Р»РёР» РєРѕРјР°РЅРґСѓ/СЃС‚Р°С‚СѓСЃ РїРѕСЃСЂРµРґРё СЃРєР°С‡РёРІР°РЅРёСЏ, РЅРµ Р±СѓРґРµРј РЅРё
    РїРµСЂРµРІРѕРґРёС‚СЊ РѕР·РІСѓС‡РєСѓ, РЅРё СЃР»Р°С‚СЊ РіРѕС‚РѕРІРѕРµ РІРёРґРµРѕ РІ РїСѓСЃС‚РѕС‚Сѓ."""
    try:
        check_id = status_msg.id or message.id
        result = await message.client.get_messages(message.chat_id, ids=check_id)
        return result is not None
    except Exception:
        return True


class _MutedStatus:
    """Р—Р°РіР»СѓС€РєР° РІРјРµСЃС‚Рѕ СЃС‚Р°С‚СѓСЃ-СЃРѕРѕР±С‰РµРЅРёСЏ РґР»СЏ С‚РёС…РѕРіРѕ Р°РІС‚РѕСЂРµР·СЋРјР° РїРѕСЃР»Рµ РєСЂР°С€Р°: .edit()/.delete()
    РїСЂРѕСЃС‚Рѕ РЅРёС‡РµРіРѕ РЅРµ РґРµР»Р°СЋС‚, С‡С‚РѕР±С‹ РІРµСЃСЊ РѕР±С‹С‡РЅС‹Р№ РєРѕРґ (update_status, quality_downloading Рё С‚.Рґ.)
    СЂР°Р±РѕС‚Р°Р» Р±РµР· РµРґРёРЅРѕР№ РїСЂР°РІРєРё, РЅРѕ РЅРё РѕРґРЅРѕРіРѕ РЅРѕРІРѕРіРѕ СЃРѕРѕР±С‰РµРЅРёСЏ РІ С‡Р°С‚ РЅРµ СѓР»РµС‚Р°Р»Рѕ."""
    id = None

    async def edit(self, *args, **kwargs):
        return None

    async def delete(self, *args, **kwargs):
        return None


async def compress_video(input_path, encoder_key, tier="medium", duration_hint=None, on_progress=None, cancel_event=None):
    """РџРµСЂРµРіРѕРЅСЏРµС‚ РІРёРґРµРѕ РІ HEVC (РёР»Рё H.264 РЅР° СЃРѕС„С‚Рµ) РїРѕ РІС‹Р±СЂР°РЅРЅРѕРјСѓ РїСЂРµСЃРµС‚Сѓ, Р°СѓРґРёРѕ вЂ” РІ AAC.
    Р’РѕР·РІСЂР°С‰Р°РµС‚ РїСѓС‚СЊ Рє РЅРѕРІРѕРјСѓ С„Р°Р№Р»Сѓ РёР»Рё None, РµСЃР»Рё СЃР¶Р°С‚РёРµ РЅРµ СѓРґР°Р»РѕСЃСЊ (С‚РѕРіРґР° С€Р»С‘Рј РєР°Рє СЃРєР°С‡Р°Р»РѕСЃСЊ).
    Р”РѕРІРµС€РёРІР°РµС‚ safety-С„РёР»СЊС‚СЂ РЅР° С‡С‘С‚РЅРѕСЃС‚СЊ СЃС‚РѕСЂРѕРЅ вЂ” РЅРµС‡С‘С‚РЅР°СЏ РІС‹СЃРѕС‚Р°/С€РёСЂРёРЅР° (РЅРµСЂРµРґРєРѕ Сѓ РІРµСЂС‚РёРєР°Р»СЊРЅС‹С…
    Shorts) РёРЅР°С‡Рµ РјРѕР¶РµС‚ РѕС‚РїСЂР°РІРёС‚СЊ РєРѕРґРёСЂРѕРІС‰РёРє РІ Р°СЂС‚РµС„Р°РєС‚С‹ РёР»Рё РІРѕРІСЃРµ СѓСЂРѕРЅРёС‚СЊ РµРіРѕ.
    on_progress(eta_seconds) вЂ” С‚РѕС‚ Р¶Рµ РїСЂРёРЅС†РёРї, С‡С‚Рѕ Рё РґР»СЏ СЃРєР°С‡РёРІР°РЅРёСЏ: -progress pipe:1 РѕС‚РґР°С‘С‚
    РјР°С€РёРЅРѕС‡РёС‚Р°РµРјС‹Р№ РїСЂРѕРіСЂРµСЃСЃ (out_time_ms, speed), РїРѕ РЅРёРј СЃС‡РёС‚Р°РµРј РѕСЃС‚Р°РІС€РµРµСЃСЏ РІСЂРµРјСЏ Рё С‚СЂРѕС‚С‚Р»РёРј
    РєРѕР»Р»Р±РµРє РґРѕ СЂР°Р·Р° РІ 3 СЃРµРєСѓРЅРґС‹, С‡С‚РѕР±С‹ РЅРµ РґРѕР»Р±РёС‚СЊ РїСЂР°РІРєР°РјРё СЃРѕРѕР±С‰РµРЅРёСЏ.
    cancel_event вЂ” .dlstop: СЂР°РЅСЊС€Рµ РѕС‚РјРµРЅР° РїСЂРѕРІРµСЂСЏР»Р°СЃСЊ С‚РѕР»СЊРєРѕ РІРЅСѓС‚СЂРё yt-dlp РїСЂРѕРіСЂРµСЃСЃ-С…СѓРєР°,
    С‚Рѕ РµСЃС‚СЊ С‚РѕР»СЊРєРѕ РІРѕ РІСЂРµРјСЏ СЃР°РјРѕРіРѕ СЃРєР°С‡РёРІР°РЅРёСЏ вЂ” РµСЃР»Рё СЋР·РµСЂ Р¶Р°Р» .dlstop СѓР¶Рµ РЅР° СЌС‚Р°РїРµ СЃР¶Р°С‚РёСЏ,
    РЅРёС‡РµРіРѕ РЅРµ РїСЂРѕРёСЃС…РѕРґРёР»Рѕ, Рё РІРёРґРµРѕ РІСЃС‘ СЂР°РІРЅРѕ РїСЂРёР»РµС‚Р°Р»Рѕ С‡РµСЂРµР· РЅРµСЃРєРѕР»СЊРєРѕ СЃРµРєСѓРЅРґ."""
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
    """ffprobe-РґР»РёС‚РµР»СЊРЅРѕСЃС‚СЊ С„Р°Р№Р»Р° РІ СЃРµРєСѓРЅРґР°С… (РґР»СЏ ETA СЃР¶Р°С‚РёСЏ, РµСЃР»Рё duration РЅРµРёР·РІРµСЃС‚РЅР° Р·Р°СЂР°РЅРµРµ)."""
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
    """'HH:MM:SS.micro' -> СЃРµРєСѓРЅРґС‹ (float). Р¤РѕСЂРјР°С‚ ffmpeg -progress out_time."""
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
    """РљРѕСЂРѕС‚РєРёР№ (~2.5 СЃРµРє) Р·Р°РјРµСЂ РІС…РѕРґСЏС‰РµР№ СЃРєРѕСЂРѕСЃС‚Рё вЂ” РєР°С‡Р°РµРј РєСѓСЃРѕРє СЃ Cloudflare, СЃС‡РёС‚Р°РµРј РњР±РёС‚/СЃ.
    Р РµР·СѓР»СЊС‚Р°С‚ РєСЌС€РёСЂСѓРµС‚СЃСЏ РЅР° 5 РјРёРЅСѓС‚: РЅР° РѕРґРЅРѕРј Рё С‚РѕРј Р¶Рµ СЃРµСЂРІРµСЂРµ СЃРєРѕСЂРѕСЃС‚СЊ РјРµР¶РґСѓ РґРІСѓРјСЏ РІРёРґРµРѕ
    РїРѕРґСЂСЏРґ РїРѕС‡С‚Рё РЅРµ РјРµРЅСЏРµС‚СЃСЏ, Р° РєР°С‡Р°С‚СЊ РїРѕ 25 РњР‘ РїРѕРґ РєР°Р¶РґСѓСЋ СЃСЃС‹Р»РєСѓ вЂ” С‚СЂР°С‚Р° РІСЂРµРјРµРЅРё/С‚СЂР°С„РёРєР°."""
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
    """Р›С‘РіРєРёР№ РїРёРє РјРµС‚Р°РґР°РЅРЅС‹С… Р±РµР· СЃРєР°С‡РёРІР°РЅРёСЏ вЂ” СѓР·РЅР°С‘Рј РґР»РёС‚РµР»СЊРЅРѕСЃС‚СЊ РІРёРґРµРѕ Р·Р°СЂР°РЅРµРµ,
    С‡С‚РѕР±С‹ СЂРµС€РёС‚СЊ, РЅСѓР¶РµРЅ Р»Рё СЃРїРёРґС‚РµСЃС‚ РІРѕРѕР±С‰Рµ Рё РЅРµ РѕС‚РІР°Р»РёС‚СЊСЃСЏ РїРѕ Р»РёРјРёС‚Сѓ РїРѕС‚РѕРј.
    Р РµР·СѓР»СЊС‚Р°С‚ РєСЌС€РёСЂСѓРµС‚СЃСЏ РЅР° 10 РјРёРЅСѓС‚ вЂ” РїРѕРІС‚РѕСЂРЅР°СЏ Р·Р°РіСЂСѓР·РєР° С‚РѕР№ Р¶Рµ СЃСЃС‹Р»РєРё РЅРµ РїРёРЅРіСѓРµС‚ YouTube СЃРЅРѕРІР°."""
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
    """РџР»РѕСЃРєРёР№ СЃРїРёСЃРѕРє СЂРѕР»РёРєРѕРІ РІРЅСѓС‚СЂРё РїР»РµР№Р»РёСЃС‚Р° (YouTube) вЂ” flat-СЌРєСЃС‚СЂР°РєС‚ Р±РµР· СЃРєР°С‡РёРІР°РЅРёСЏ
    РєР°Р¶РґРѕРіРѕ СЌР»РµРјРµРЅС‚Р°. Р’РѕР·РІСЂР°С‰Р°РµС‚ [{url, title}, ...], None вЂ” РµСЃР»Рё СЌС‚Рѕ РЅРµ РїР»РµР№Р»РёСЃС‚/РЅРёС‡РµРіРѕ
    РЅРµ СѓРґР°Р»РѕСЃСЊ РґРѕСЃС‚Р°С‚СЊ, РёР»Рё СЃРїРёСЃРѕРє РёР· 1 СЌР»РµРјРµРЅС‚Р° вЂ” С‚РѕРіРґР° РІС‹Р·С‹РІР°СЋС‰РёР№ РёРґС‘С‚ РѕР±С‹С‡РЅС‹Рј РїСѓС‚С‘Рј."""
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
    """Р›С‘РіРєРёР№ РїРёРє title/channel Р±РµР· СЃРєР°С‡РёРІР°РЅРёСЏ вЂ” РёРЅРѕРіРґР° РјРµС‚Р°РґР°РЅРЅС‹Рµ РґРѕСЃС‚СѓРїРЅС‹, РґР°Р¶Рµ РєРѕРіРґР°
    СЃР°РјР° РјРµРґРёР°-Р·Р°РіСЂСѓР·РєР° СѓРїРёСЂР°РµС‚СЃСЏ РІ РєСѓРєРё. РџСЂРёРіРѕР¶РґР°РµС‚СЃСЏ РґР»СЏ С„РѕР»Р±РµРєР° С‡РµСЂРµР· @SaveAsBot,
    С‡С‚РѕР±С‹ РѕС„РѕСЂРјРёС‚СЊ РёС‚РѕРі РєР°Рє РѕР±С‹С‡РЅРѕ (РЅР°Р·РІР°РЅРёРµ, РєР°РЅР°Р»), Р° РЅРµ РіРѕР»С‹Рј С„Р°Р№Р»РѕРј."""
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
    """Р•СЃР»Рё РјРµС‚Р°РґР°РЅРЅС‹Рµ РІРѕРѕР±С‰Рµ РЅРёРєР°Рє РЅРµ РґРѕСЃС‚Р°С‚СЊ (СЃСЃС‹Р»РєР° "РЅРµ Р±СЊС‘С‚СЃСЏ" СЃРѕРІСЃРµРј РґР°Р¶Рµ РґР»СЏ РїРёРєР°) вЂ”
    РїРѕСЃР»РµРґРЅРёР№ СЂРµР·РµСЂРІ: С‚СЏРЅРµРј og:title/og:description РїСЂСЏРјРѕ СЃРѕ СЃС‚СЂР°РЅРёС†С‹, РєР°Рє СЌС‚Рѕ РґРµР»Р°РµС‚
    РїСЂРµРґРїСЂРѕСЃРјРѕС‚СЂ СЃСЃС‹Р»РѕРє РІ Telegram."""
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
    """Р РµС€Р°РµС‚, РІ РєР°РєРѕРј СЂРµР¶РёРјРµ РєР°С‡Р°С‚СЊ РІРёРґРµРѕ: standard / best / capped_2k.
    РџСЂРёРЅРёРјР°РµС‚ СѓР¶Рµ РІС‹С‡РёСЃР»РµРЅРЅС‹Рµ is_short/duration СЃРЅР°СЂСѓР¶Рё вЂ” С‡С‚РѕР±С‹ РЅРµ РїРёРЅРіРѕРІР°С‚СЊ yt-dlp РґРІР°Р¶РґС‹
    (РґР»РёС‚РµР»СЊРЅРѕСЃС‚СЊ Рё С‚Р°Рє РЅСѓР¶РЅР° РѕС‚РґРµР»СЊРЅРѕ РґР»СЏ РІС‹Р±РѕСЂР° РїСЂРµСЃРµС‚Р° СЃР¶Р°С‚РёСЏ, light/medium).

    РџСЂР°РІРёР»Р°:
    - Р’С‹РєР»СЋС‡РµРЅРѕ РІ РєРѕРЅС„РёРіРµ, Discord-СЃСЃС‹Р»РєР° РёР»Рё РєР°С‡Р°РµРј С‚РѕР»СЊРєРѕ Р°СѓРґРёРѕ в†’ РІСЃРµРіРґР° standard.
    - Shorts вЂ” РІСЃРµРіРґР° standard, СЃС‚Р°СЂС‹Рј СЃРїРѕСЃРѕР±РѕРј, Р±РµР· СЃР¶Р°С‚РёСЏ. РќР° РїСЂР°РєС‚РёРєРµ РёС… "СѓР»СѓС‡С€РµРЅРЅРѕРµ"
      2K-РєР°С‡РµСЃС‚РІРѕ РїРѕС‡РµРјСѓ-С‚Рѕ РІС‹С…РѕРґРёР»Рѕ С…СѓР¶Рµ РѕР±С‹С‡РЅРѕРіРѕ (РїРѕС…РѕР¶Рµ РЅР° Р·Р°РЅРёР¶РµРЅРЅС‹Р№ Р±РёС‚СЂРµР№С‚ Сѓ С„РѕСЂРјР°С‚Р°
      Р±РµР· РїРѕС‚РѕР»РєР° РЅР° РєРѕСЂРѕС‚РєРёС… РІРµСЂС‚РёРєР°Р»СЊРЅС‹С… СЂРѕР»РёРєР°С…) вЂ” РЅРµ СЂР°Р·Р±РёСЂР°СЏСЃСЊ РіР»СѓР±Р¶Рµ, РїСЂРѕС‰Рµ РѕС‚РєР°С‚РёС‚СЊ.
    - Р РѕР»РёРє РґРѕ 5 РјРёРЅСѓС‚ (РЅРѕ РЅРµ Shorts) в†’ best, СЃРїРёРґС‚РµСЃС‚ РЅРµ РЅСѓР¶РµРЅ (РјРµР»РѕС‡СЊ, СЃРєРѕСЂРѕСЃС‚СЊ РЅРµ РІР°Р¶РЅР°).
    - Р”Р»РёС‚РµР»СЊРЅРѕСЃС‚СЊ РЅРµ СѓРґР°Р»РѕСЃСЊ СѓР·РЅР°С‚СЊ в†’ standard (РїРµСЂРµСЃС‚СЂР°С…РѕРІРєР°, РІРґСЂСѓРі СЌС‚Рѕ РјРЅРѕРіРѕС‡Р°СЃРѕРІРѕРµ РІРёРґРµРѕ).
    - 200+ РњР±РёС‚/СЃ СЃС‚Р°Р±РёР»СЊРЅРѕ Рё СЂРѕР»РёРє РґРѕ 3 С‡Р°СЃРѕРІ в†’ capped_2k (2K, РїСЂРё РѕС‚СЃСѓС‚СЃС‚РІРёРё вЂ” 1080p).
    - 80+ РњР±РёС‚/СЃ СЃС‚Р°Р±РёР»СЊРЅРѕ Рё СЂРѕР»РёРє РґРѕ 1 С‡Р°СЃР° в†’ best (Р±РµР· РїРѕС‚РѕР»РєР° СЂР°Р·СЂРµС€РµРЅРёСЏ).
    - РРЅР°С‡Рµ в†’ standard.
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
        raise Exception("Node.js/npm РЅРµ РЅР°Р№РґРµРЅС‹ РЅР° СЃРµСЂРІРµСЂРµ вЂ” РѕР·РІСѓС‡РєР° С‚СЂРµР±СѓРµС‚ РёС… СѓСЃС‚Р°РЅРѕРІРєРё РѕС‚РґРµР»СЊРЅРѕ")

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
            raise Exception(f"npm install @vot.js/node РЅРµ СѓРґР°Р»СЃСЏ: {stderr.decode()[:300]}")

    return script_path


class NodeVersionError(Exception):
    """РћС‚РґРµР»СЊРЅС‹Р№ С‚РёРї РѕС€РёР±РєРё РґР»СЏ РїСЂРѕР±Р»РµРј СЃ РІРµСЂСЃРёРµР№ Node.js вЂ” РЅРµСЃС‘С‚ РіРѕС‚РѕРІС‹Р№ HTML СЃ РёРЅСЃС‚СЂСѓРєС†РёРµР№
    РїРѕ .terminal, С‡С‚РѕР±С‹ РІС‹Р·С‹РІР°СЋС‰РёР№ РєРѕРґ РїРѕРєР°Р·Р°Р» РµС‘ РѕС‚РґРµР»СЊРЅС‹Рј, РЅРµ РёСЃС‡РµР·Р°СЋС‰РёРј СЃРѕРѕР±С‰РµРЅРёРµРј."""
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
                f"{EMOJI_WARN} <b>РџРµСЂРµРІРѕРґ РЅРµ СѓРґР°Р»СЃСЏ: РЅСѓР¶РЅР° Р±РѕР»РµРµ РЅРѕРІР°СЏ РІРµСЂСЃРёСЏ Node.js ({minimum}+).</b>\n\n"
                f"Р’РІРµРґРёС‚Рµ РїРѕ РѕС‡РµСЂРµРґРё:\n<code>.terminal npm i -g n</code>\n<code>.terminal n latest</code>"
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
            f"{EMOJI_WARN} <b>РџРµСЂРµРІРѕРґ РЅРµ СѓРґР°Р»СЃСЏ: РЅСѓР¶РЅР° Р±РѕР»РµРµ РЅРѕРІР°СЏ РІРµСЂСЃРёСЏ Node.js ({minimum}+).</b>\n\n"
            f"Р’РІРµРґРёС‚Рµ:\n<code>.terminal n latest</code>"
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
            raise Exception(f"РќРµ СѓРґР°Р»РѕСЃСЊ СЂР°Р·РѕР±СЂР°С‚СЊ РѕС‚РІРµС‚ РјРѕСЃС‚Р° РѕР·РІСѓС‡РєРё: {stderr.decode()[:300] or last_line[:300]}")

    if not result.get("ok"):
        raise Exception(result.get("error", "РЅРµРёР·РІРµСЃС‚РЅР°СЏ РѕС€РёР±РєР° РѕР·РІСѓС‡РєРё"))

    return result["url"], result.get("title")


async def extract_audio_from_video(video_path, output_dir):
    """Р’С‹СЂРµР·Р°РµС‚ Р·РІСѓРєРѕРІСѓСЋ РґРѕСЂРѕР¶РєСѓ РёР· Р»РѕРєР°Р»СЊРЅРѕРіРѕ РІРёРґРµРѕС„Р°Р№Р»Р° РІ mp3. Р”Р»СЏ СЃР»СѓС‡Р°СЏ "СЂРµРїР»Р°Р№ РЅР°
    РІРёРґРµРѕ РІ С‡Р°С‚Рµ (Р±РµР· СЃСЃС‹Р»РєРё) + -a" вЂ” С‚Р°Рј РєР°С‡Р°С‚СЊ С‡РµСЂРµР· yt-dlp РЅРµС‡РµРіРѕ, Р·РІСѓРє РІС‹СЂРµР·Р°РµРј РёР·
    СЃР°РјРѕРіРѕ РІРёРґРµРѕС„Р°Р№Р»Р°, РєРѕС‚РѕСЂС‹Р№ СѓР¶Рµ РµСЃС‚СЊ РІ Telegram."""
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
        raise Exception("ffmpeg РЅРµ СЃРјРѕРі РІРєР»РµРёС‚СЊ РїРµСЂРµРІРµРґС‘РЅРЅСѓСЋ РґРѕСЂРѕР¶РєСѓ")

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
        raise Exception(payload.get("msg", "tikwm РІРµСЂРЅСѓР» РѕС€РёР±РєСѓ"))

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
            last_err = Exception(f"С„Р°Р№Р» СЃР»РёС€РєРѕРј РјР°Р»РµРЅСЊРєРёР№ ({os.path.getsize(path) if os.path.isfile(path) else 0} Р±Р°Р№С‚)")
        except Exception as e:
            last_err = e

        if os.path.isfile(path):
            try:
                os.remove(path)
            except Exception:
                pass

    raise last_err or Exception("РЅРµ СѓРґР°Р»РѕСЃСЊ СЃРєР°С‡Р°С‚СЊ С„Р°Р№Р»")


async def download_tiktok_via_api(url, output_dir):
    data = await tikwm_lookup(url)
    video_url = data.get("hdplay") or data.get("play")
    if not video_url:
        raise Exception("tikwm РЅРµ РІРµСЂРЅСѓР» СЃСЃС‹Р»РєСѓ РЅР° РІРёРґРµРѕ")

    title = data.get("title") or "TikTok"
    author = ((data.get("author") or {}).get("nickname")) or None
    file_path = await download_file(video_url, output_dir, "mp4")

    return file_path, title, author


async def download_tiktok_audio_via_api(url, output_dir):
    data = await tikwm_lookup(url)
    music_url = data.get("music")
    if not music_url:
        raise Exception("tikwm РЅРµ РІРµСЂРЅСѓР» СЃСЃС‹Р»РєСѓ РЅР° Р°СѓРґРёРѕ")

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
    """Instagram-РєР°СЂСѓСЃРµР»СЊ (РЅРµСЃРєРѕР»СЊРєРѕ С„РѕС‚Рѕ/РІРёРґРµРѕ РІ РѕРґРЅРѕРј РїРѕСЃС‚Рµ) вЂ” yt-dlp РѕС‚РґР°С‘С‚ РµС‘ РєР°Рє playlist
    СЃ РЅРµСЃРєРѕР»СЊРєРёРјРё entries. РћР±С‹С‡РЅС‹Р№ noplaylist=True, С‡С‚Рѕ РёСЃРїРѕР»СЊР·СѓРµС‚СЃСЏ РґР»СЏ РѕРґРёРЅРѕС‡РЅС‹С… РїРѕСЃС‚РѕРІ,
    С‚СѓС‚ РЅРµ РїРѕРґС…РѕРґРёС‚ вЂ” РѕРЅ Р»РёР±Рѕ С…РІР°С‚Р°РµС‚ С‚РѕР»СЊРєРѕ РїРµСЂРІС‹Р№ СЌР»РµРјРµРЅС‚, Р»РёР±Рѕ (СЃСѓРґСЏ РїРѕ Р±Р°РіСЂРµРїРѕСЂС‚Сѓ) СЂРѕРЅСЏРµС‚
    РІСЃС‘ СЃ РѕС€РёР±РєРѕР№ РїСЂРѕ РєСѓРєРё. Р’РѕР·РІСЂР°С‰Р°РµС‚ СЃРїРёСЃРѕРє РїСѓС‚РµР№ Рє С„Р°Р№Р»Р°Рј, РёР»Рё None РµСЃР»Рё РїРѕСЃС‚ РЅРµ РєР°СЂСѓСЃРµР»СЊ
    (РѕР±С‹С‡РЅС‹Р№ РѕРґРёРЅРѕС‡РЅС‹Р№ РїРѕСЃС‚/reel вЂ” РїСѓСЃС‚СЊ РёРґС‘С‚ РїРѕ СЃС‚Р°СЂРѕРјСѓ, РѕР±С‹С‡РЅРѕРјСѓ РїСѓС‚Рё)."""
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


def parse_netscape_cookies(cookies_text, domain_filter=None):
    """РџР°СЂСЃРёС‚ cookies.txt РІ Netscape-С„РѕСЂРјР°С‚Рµ (С‚РѕС‚ Р¶Рµ, С‡С‚Рѕ Рё youtube_cookies) Рё РѕС‚РґР°С‘С‚
    {name: value}, РѕС‚С„РёР»СЊС‚СЂРѕРІР°РЅРЅС‹Р№ РїРѕ РІС…РѕР¶РґРµРЅРёСЋ domain_filter РІ РїРѕР»Рµ РґРѕРјРµРЅР°."""
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
    """РЇРЅРґРµРєСЃ.РњСѓР·С‹РєР° РѕС‚РґР°С‘С‚ lossless-РїРѕС‚РѕРє Р·Р°РІС‘СЂРЅСѓС‚С‹Рј РІ MP4-РєРѕРЅС‚РµР№РЅРµСЂ (codec 'flac-mp4') вЂ” С‚РѕС‚
    Р¶Рµ С„РѕСЂРјР°С‚, С‡С‚Рѕ Рё СЂР°СЃС€РёСЂРµРЅРёРµ РїРѕР»СѓС‡Р°РµС‚ Рё СЂР°СЃРїР°РєРѕРІС‹РІР°РµС‚ Сѓ СЃРµР±СЏ РІ Р±СЂР°СѓР·РµСЂРµ (СЃРј. С„СѓРЅРєС†РёСЋ me()
    РІ РµРіРѕ content.js). Р”РѕСЃС‚Р°С‘Рј raw FLAC: РЅР°С…РѕРґРёРј 'mdat' (СЃС‹СЂС‹Рµ СЃСЌРјРїР»С‹) Рё 'dfLa' box РІРЅСѓС‚СЂРё
    'stsd' (С‚Р°Рј Р»РµР¶Р°С‚ РѕСЂРёРіРёРЅР°Р»СЊРЅС‹Рµ FLAC metadata-Р±Р»РѕРєРё, РІРєР»СЋС‡Р°СЏ STREAMINFO), СЃРєР»РµРёРІР°РµРј.
    РЈРїСЂРѕС‰РµРЅРёРµ РѕС‚РЅРѕСЃРёС‚РµР»СЊРЅРѕ СЂР°СЃС€РёСЂРµРЅРёСЏ: СЃСЌРјРїР»С‹ Р±РµСЂС‘Рј РёР· mdat РѕРґРЅРёРј РєСѓСЃРєРѕРј РїРѕ СЃРјРµС‰РµРЅРёСЋ/СЂР°Р·РјРµСЂСѓ
    (Р±РµР· СЂР°Р·Р±РѕСЂР° stsz/stsc/stco) вЂ” РґР»СЏ РѕРґРёРЅРѕС‡РЅРѕРіРѕ Р°СѓРґРёРѕС‚СЂРµРєР° (РѕРґРёРЅ run, РЅРµ С„СЂР°РіРјРµРЅС‚РёСЂРѕРІР°РЅРЅС‹Р№
    moof/mfra) СЃСЌРјРїР»С‹ Рё С‚Р°Рє Р»РµР¶Р°С‚ РІ mdat РїРѕРґСЂСЏРґ, СЌС‚РѕРіРѕ РґРѕСЃС‚Р°С‚РѕС‡РЅРѕ."""
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
    """РЎРєР°С‡РёРІР°РЅРёРµ С‚СЂРµРєР° РЇРЅРґРµРєСЃ.РњСѓР·С‹РєРё С‡РµСЂРµР· РёС… Р¶Рµ РЅРµРѕС„РёС†РёР°Р»СЊРЅС‹Р№ web-API вЂ” С‚РµРјРё Р¶Рµ Р·Р°РїСЂРѕСЃР°РјРё
    (get-file-info СЃ HMAC-РїРѕРґРїРёСЃСЊСЋ), С‡С‚Рѕ РёСЃРїРѕР»СЊР·СѓРµС‚ СЂР°СЃС€РёСЂРµРЅРёРµ Yandex Music Downloader.
    yt-dlp СЃ РЇ.РњСѓР·С‹РєРѕР№ РїРѕС‡С‚Рё РЅРµ СЃРїСЂР°РІР»СЏРµС‚СЃСЏ: Р±РµР· Р·Р°Р»РѕРіРёРЅРµРЅРЅРѕРіРѕ Р°РєРєР°СѓРЅС‚Р° РѕС‚РґР°С‘С‚ РјР°РєСЃРёРјСѓРј
    РїСЂРµРІСЊСЋ РЅР° 30-60 СЃРµРєСѓРЅРґ. РќСѓР¶РЅС‹ РєСѓРєРё Р·Р°Р»РѕРіРёРЅРµРЅРЅРѕРіРѕ Р°РєРєР°СѓРЅС‚Р° music.yandex.* вЂ” Р±РµСЂСѓС‚СЃСЏ РёР·
    С‚РѕР№ Р¶Рµ РЅР°СЃС‚СЂРѕР№РєРё youtube_cookies (СЌС‚Рѕ РїСЂРѕСЃС‚Рѕ РѕР±С‰РёР№ cookies.txt, С‚СѓРґР° РјРѕР¶РЅРѕ РґРѕР±Р°РІРёС‚СЊ РєСѓРєРё
    СЃ Р»СЋР±С‹С… РґРѕРјРµРЅРѕРІ, РЅРµ С‚РѕР»СЊРєРѕ YouTube). prefer_flac=True вЂ” РїСЂРѕР±СѓРµРј lossless (MP4-РѕР±С‘СЂРЅСѓС‚С‹Р№
    FLAC, СЂР°СЃРїР°РєРѕРІС‹РІР°РµРј СЃР°РјРё), РµСЃР»Рё РЅРµРґРѕСЃС‚СѓРїРЅРѕ вЂ” С‚РёС…РёР№ С„РѕР»Р±РµРє РЅР° mp3 320."""
    track_id = extract_yandex_track_id(url)
    if not track_id:
        raise ValueError("РќРµ СѓРґР°Р»РѕСЃСЊ РѕРїСЂРµРґРµР»РёС‚СЊ ID С‚СЂРµРєР° РёР· СЃСЃС‹Р»РєРё РЇРЅРґРµРєСЃ.РњСѓР·С‹РєРё")

    yandex_cookies = parse_netscape_cookies(cookies_text, domain_filter="yandex")
    if not yandex_cookies:
        raw_len = len(cookies_text) if cookies_text else 0
        raw_has_word = "yandex" in (cookies_text or "").lower()
        raise ValueError(
            "РќСѓР¶РЅС‹ РєСѓРєРё Р·Р°Р»РѕРіРёРЅРµРЅРЅРѕРіРѕ Р°РєРєР°СѓРЅС‚Р° music.yandex.ru вЂ” РґРѕР±Р°РІСЊС‚Рµ РёС… РІ youtube_cookies "
            "(РєРѕРјР°РЅРґР° .cfg YouTube-DLD youtube_cookies). "
            f"[РґРёР°РіРЅРѕСЃС‚РёРєР°: РєРѕРЅС„РёРі РїСЂРѕС‡РёС‚Р°РЅ, РґР»РёРЅР° {raw_len} СЃРёРјРІ., СЃР»РѕРІРѕ 'yandex' РІ С‚РµРєСЃС‚Рµ: "
            f"{'РµСЃС‚СЊ' if raw_has_word else 'РќР•Рў'}, СЂР°СЃРїРѕР·РЅР°РЅРѕ СЃС‚СЂРѕРє РєСѓРє: 0]"
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
                        meta_debug = "РїСѓСЃС‚РѕР№ result"
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
                    raise ValueError(f"РЇРЅРґРµРєСЃ.РњСѓР·С‹РєР° API РІРµСЂРЅСѓР»Р° {resp.status} вЂ” РєСѓРєРё РїСЂРѕС‚СѓС…Р»Рё РёР»Рё С‚СЂРµРє РЅРµРґРѕСЃС‚СѓРїРµРЅ")
                info_json = await resp.json(content_type=None)
            download_info = (info_json or {}).get("downloadInfo") or {}
            stream_url = download_info.get("url")
            if not stream_url:
                raise ValueError("РЇРЅРґРµРєСЃ.РњСѓР·С‹РєР° РЅРµ РѕС‚РґР°Р»Р° СЃСЃС‹Р»РєСѓ РЅР° РїРѕС‚РѕРє вЂ” РєСѓРєРё РїСЂРѕС‚СѓС…Р»Рё РёР»Рё С‚СЂРµРє РЅРµРґРѕСЃС‚СѓРїРµРЅ Р±РµР· РїРѕРґРїРёСЃРєРё")
            return urllib.parse.unquote(stream_url)

        used_flac = False
        stream_bytes = None
        stream_url = None
        if prefer_flac:
            try:
                stream_url = await fetch_stream_url("lossless", "flac-mp4", "raw")
                async with session.get(stream_url, timeout=aiohttp.ClientTimeout(total=180)) as resp:
                    if resp.status != 200:
                        raise ValueError(f"HTTP {resp.status} РїСЂРё СЃРєР°С‡РёРІР°РЅРёРё lossless-РїРѕС‚РѕРєР°")
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
                    raise ValueError(f"РќРµ СѓРґР°Р»РѕСЃСЊ СЃРєР°С‡Р°С‚СЊ СЃР°Рј С„Р°Р№Р» С‚СЂРµРєР° (HTTP {resp.status})")
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


async def _resolve_input_peer(client, peer_id):
    """get_input_entity СЃРјРѕС‚СЂРёС‚ РўРћР›Р¬РљРћ РІ Р»РѕРєР°Р»СЊРЅС‹Р№ РєСЌС€ СЃРµСЃСЃРёРё Рё РїР°РґР°РµС‚, РµСЃР»Рё СЃСѓС‰РЅРѕСЃС‚СЊ С‚СѓРґР°
    РµС‰С‘ РЅРµ РїРѕРїР°Р»Р° (РЅР°РїСЂРёРјРµСЂ, СЌС‚Рѕ РїРµСЂРІРѕРµ РѕР±СЂР°С‰РµРЅРёРµ Рє Р±РѕС‚Сѓ Р·Р° СЃРµСЃСЃРёСЋ/РїРѕСЃР»Рµ СЂРµСЃС‚Р°СЂС‚Р°) вЂ” РёР·-Р·Р°
    СЌС‚РѕРіРѕ РїСЂРѕРІРµСЂРєРё РјСЊСЋС‚Р°/Р°СЂС…РёРІР° РјРѕР»С‡Р° РІРѕР·РІСЂР°С‰Р°Р»Рё None Рё РјСЊСЋС‚ РЅРµ СЃСЂР°Р±Р°С‚С‹РІР°Р» РІРѕРѕР±С‰Рµ. get_entity
    РІ С‚Р°РєРѕР№ СЃРёС‚СѓР°С†РёРё СЃС…РѕРґРёС‚ РІ API, Р·Р°РєСЌС€РёСЂСѓРµС‚ СЃСѓС‰РЅРѕСЃС‚СЊ вЂ” Рё РїРѕРІС‚РѕСЂРЅС‹Р№ get_input_entity СѓР¶Рµ
    РѕС‚СЂР°Р±РѕС‚Р°РµС‚."""
    try:
        return await client.get_input_entity(peer_id)
    except (ValueError, TypeError):
        await client.get_entity(peer_id)
        return await client.get_input_entity(peer_id)


async def get_dialog_archived(client, peer_id):
    """True/False вЂ” РІ Р°СЂС…РёРІРµ Р»Рё РґРёР°Р»РѕРі СЃ СЌС‚РёРј peer СЃРµР№С‡Р°СЃ. None, РµСЃР»Рё РЅРµ СѓРґР°Р»РѕСЃСЊ РѕРїСЂРµРґРµР»РёС‚СЊ
    (С‚РѕРіРґР° С‚СЂРѕРіР°С‚СЊ Р°СЂС…РёРІРЅРѕРµ СЃРѕСЃС‚РѕСЏРЅРёРµ РІРѕРѕР±С‰Рµ РЅРµ Р±СѓРґРµРј вЂ” РЅРµ СЂРёСЃРєСѓРµРј РїРµСЂРµРїСѓС‚Р°С‚СЊ)."""
    try:
        input_peer = await _resolve_input_peer(client, peer_id)
        result = await client(GetPeerDialogsRequest(peers=[InputDialogPeer(input_peer)]))
        if result.dialogs:
            return bool(getattr(result.dialogs[0], "folder_id", 0))
        return False
    except Exception:
        return None


async def get_dialog_muted(client, peer_id):
    """True/False вЂ” Р·Р°РіР»СѓС€РµРЅ Р»Рё РґРёР°Р»РѕРі СЃ СЌС‚РёРј peer РїСЂСЏРјРѕ СЃРµР№С‡Р°СЃ (РїРѕ mute_until РІ Р±СѓРґСѓС‰РµРј).
    None, РµСЃР»Рё РЅРµ СѓРґР°Р»РѕСЃСЊ РѕРїСЂРµРґРµР»РёС‚СЊ."""
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
    """РЈРґР°Р»СЏРµС‚ СЃС‚Р°СЂС‹Рµ С‡Р°СЃС‚РёС‡РЅС‹Рµ С„Р°Р№Р»С‹ Р·Р°РіСЂСѓР·РѕРє РІ base_dir. Р’РѕР·РІСЂР°С‰Р°РµС‚ С‡РёСЃР»Рѕ СѓРґР°Р»С‘РЅРЅС‹С… С„Р°Р№Р»РѕРІ."""
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

    def progress_hook(d):
        if cancel_event is not None and cancel_event.is_set():
            raise DownloadCancelled()
        if d.get('status') == 'downloading':
            last_activity_ts[0] = time.monotonic()
        if not on_progress or d.get('status') != 'downloading':
            return
        eta = d.get('eta')
        if eta is None:
            return
        now = time.monotonic()
        if now - last_progress_ts[0] < 3:
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

                        if (
                            quality_mode == "raw" and not audio_only
                            and quality_info['height'] and quality_info['height'] < 720
                            and attempt < max_attempts
                        ):
                            try:
                                os.remove(file_path)
                            except Exception:
                                pass
                            last_error = Exception(
                                f"Р Р°Р·РґРѕР±С‹Р»Рё С‚РѕР»СЊРєРѕ {quality_info['height']}p (format "
                                f"{quality_info['format_id']}) вЂ” РїСЂРѕР±СѓСЋ РґСЂСѓРіРѕР№ РєР»РёРµРЅС‚/РјРµС‚РѕРґ"
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
                            raise Exception("Р’РёРґРµРѕ РЅРµРґРѕСЃС‚СѓРїРЅРѕ (РїСЂРёРІР°С‚РЅРѕРµ, СѓРґР°Р»РµРЅРѕ РёР»Рё С‚РѕР»СЊРєРѕ РґР»СЏ РїРѕРґРїРёСЃС‡РёРєРѕРІ)")

                        if "Unsupported URL" in error_str or "is not a valid URL" in error_str:
                            raise Exception("Р­С‚Р° СЃСЃС‹Р»РєР° РЅРµ РїРѕРґРґРµСЂР¶РёРІР°РµС‚СЃСЏ yt-dlp")

                        await asyncio.sleep(2)
                        continue

                if attempt >= max_attempts:
                    break

        if last_error:
            raise last_error
        raise Exception(f"РќРµ СѓРґР°Р»РѕСЃСЊ СЃРєР°С‡Р°С‚СЊ РїРѕСЃР»Рµ {attempt} РїРѕРїС‹С‚РѕРє")

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
    """yt-dlp РѕС‚РґР°С‘С‚ Р·Р°РіРѕР»РѕРІРѕРє С‚РІРёС‚Р° РєР°Рє 'РРјСЏ РєР°РЅР°Р»Р° - С‚РµРєСЃС‚ С‚РІРёС‚Р°' вЂ” РѕСЃС‚Р°РІР»СЏРµРј С‚РѕР»СЊРєРѕ
    СЃР°Рј С‚РµРєСЃС‚. РЈ С‚РІРёС‚РѕРІ Р±РµР· С‚РµРєСЃС‚Р° (С‚РѕР»СЊРєРѕ РјРµРґРёР°) РІ СЌС‚РѕРј Р¶Рµ РїРѕР»Рµ РёРЅРѕРіРґР° РѕСЃС‚Р°С‘С‚СЃСЏ РіРѕР»Р°СЏ
    t.co-СЃСЃС‹Р»РєР° вЂ” РІ С‚Р°РєРѕРј СЃР»СѓС‡Р°Рµ РІРѕР·РІСЂР°С‰Р°РµРј РїСѓСЃС‚СѓСЋ СЃС‚СЂРѕРєСѓ (Р±РµР· Р·Р°РіРѕР»РѕРІРєР° РІРѕРѕР±С‰Рµ)."""
    if not title:
        return title
    if " - " in title:
        title = title.split(" - ", 1)[1].strip()
    if re.match(r"^https?://t\.co/\S+$", title.strip(), re.IGNORECASE):
        return ""
    return title


def clean_myinstants_title(title):
    """Р—Р°РіРѕР»РѕРІРѕРє СЃС‚СЂР°РЅРёС†С‹ myinstants РїСЂРёС…РѕРґРёС‚ РІРёРґР° 'РќР°Р·РІР°РЅРёРµ - Sound Button вЂ” www.myinstants.com',
    РЅРѕ 'Sound Button' Р»РѕРєР°Р»РёР·СѓРµС‚СЃСЏ РїРѕРґ СЏР·С‹Рє СЃС‚СЂР°РЅРёС†С‹ ('Р—РІСѓРєРѕРІР°СЏ РєРЅРѕРїРєР°' Рё С‚.Рї.) вЂ” РІРјРµСЃС‚Рѕ
    РїРѕРїС‹С‚РєРё РїРµСЂРµС‡РёСЃР»РёС‚СЊ РІСЃРµ РІР°СЂРёР°РЅС‚С‹ РїСЂРѕСЃС‚Рѕ Р±РµСЂС‘Рј РІСЃС‘ РґРѕ РїРµСЂРІРѕРіРѕ ' - ', РєР°Рє Рё СЃ С‚РІРёС‚С‚РµСЂРѕРј."""
    if not title:
        return title
    if " - " in title:
        title = title.split(" - ", 1)[0].strip()
    return title


def clean_tenor_title(title):
    """Р—Р°РіРѕР»РѕРІРѕРє СЃС‚СЂР°РЅРёС†С‹ tenor.com РїСЂРёС…РѕРґРёС‚ РІРёРґР° 'РќР°Р·РІР°РЅРёРµ GIF - РќР°Р·РІР°РЅРёРµ - Discover & Share
    GIFs' вЂ” Р±РµСЂС‘Рј РІСЃС‘ РґРѕ РїРµСЂРІРѕРіРѕ ' - ' (РєР°Рє Рё myinstants/С‚РІРёС‚С‚РµСЂ), Р·Р°С‚РµРј СѓР±РёСЂР°РµРј С…РІРѕСЃС‚РѕРІРѕРµ
    'GIF', РєРѕС‚РѕСЂРѕРµ С‚Р°Рј РІСЃРµРіРґР° РїСЂРёРєР»РµРµРЅРѕ Рє СЃР°РјРѕРјСѓ РЅР°Р·РІР°РЅРёСЋ."""
    if not title:
        return title
    if " - " in title:
        title = title.split(" - ", 1)[0].strip()
    title = re.sub(r"\s+GIF$", "", title, flags=re.IGNORECASE).strip()
    return title


def sanitize_media_filename(name, max_len=120, fallback="audio"):
    """Р“РѕС‚РѕРІРёС‚ РЅР°Р·РІР°РЅРёРµ РІРёРґРµРѕ/С‚СЂРµРєР° РґР»СЏ РїРѕРєР°Р·Р° РєР°Рє РёРјСЏ С„Р°Р№Р»Р°: СѓР±РёСЂР°РµС‚ РїРµСЂРµРЅРѕСЃС‹ СЃС‚СЂРѕРє
    Рё СЃРёРјРІРѕР»С‹, РЅРµРґРѕРїСѓСЃС‚РёРјС‹Рµ РІ РёРјРµРЅР°С… С„Р°Р№Р»РѕРІ РЅР° Р±РѕР»СЊС€РёРЅСЃС‚РІРµ РћРЎ, СЂРµР¶РµС‚ РїРѕ РґР»РёРЅРµ."""
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
    """РџРѕРјРѕРіР°РµС‚ СЃРєР°С‡РёРІР°С‚СЊ РІРёРґРµРѕ СЃ YouTube, TikTok Рё РґСЂ. SponsorBlock РІС‹СЂРµР·Р°РµС‚ СЂРµРєР»Р°РјСѓ, -s/-e Р±РµСЂСѓС‚ С‚РѕР»СЊРєРѕ РѕС‚СЂРµР·РѕРє."""

    __version__ = (3, 4, 5)

    strings = {
        "name": "YouTube-DLD",
        "no_link": EMOJI_WARN + " <b>РџРѕР¶Р°Р»СѓР№СЃС‚Р°, СѓРєР°Р¶РёС‚Рµ СЃСЃС‹Р»РєСѓ РЅР° РІРёРґРµРѕ Р»РёР±Рѕ РѕС‚РІРµС‚СЊС‚Рµ РЅР° СЃРѕРѕР±С‰РµРЅРёРµ СЃ РЅРµР№.</b>",
        "youtube_posts_unsupported": EMOJI_WARN + " <b>РџРѕСЃС‚С‹ YouTube РІСЂРµРјРµРЅРЅРѕ РЅРµ РїРѕРґРґРµСЂР¶РёРІР°СЋС‚СЃСЏ.</b>",
        "default_downloading": "<b>Р—Р°РіСЂСѓР¶Р°СЋ РІРёРґРµРѕ.</b>\n\n" + EMOJI_INFO + " <code>РћСЃС‚Р°Р»РѕСЃСЊ в‰€ {eta}</code>",
        "default_downloading_simple": "<b>Р—Р°РіСЂСѓР¶Р°СЋ РІРёРґРµРѕ.</b>",
        "eta_unknown": "<tg-emoji emoji-id=5350773074578916842>рџ•ђ</tg-emoji>",
        "default_error": "<b>РћС€РёР±РєР° Р·Р°РіСЂСѓР·РєРё.</b>\n\n<code>{error}</code>",
        "too_long": "Р’РёРґРµРѕ РґР»РёРЅРЅРµРµ {minutes} РјРёРЅ. РЎРєР°С‡РёРІР°РЅРёРµ РѕС‚РјРµРЅРµРЅРѕ вЂ” Р»РёРјРёС‚ РјРµРЅСЏРµС‚СЃСЏ РІ .cfg YouTube-DLD (max_duration).",
        "cancelled": EMOJI_WARN + " <b>Р—Р°РіСЂСѓР·РєР° РѕС‚РјРµРЅРµРЅР° (.dlstop).</b>",
        "nothing_to_cancel": EMOJI_WARN + " <b>РќРµС‚ Р°РєС‚РёРІРЅС‹С… Р·Р°РіСЂСѓР·РѕРє РґР»СЏ РѕС‚РјРµРЅС‹.</b>",
        "cancelled_ok": EMOJI_OK + " РћСЃС‚Р°РЅРѕРІР»РµРЅРѕ Р·Р°РіСЂСѓР·РѕРє: <b>{count}</b>",
        "playlist_progress": EMOJI_DOWNLOAD + " <b>РџР»РµР№Р»РёСЃС‚ {idx}/{total}</b>\n\n<code>{title}</code>",
        "default_response": "Р’РѕС‚ [РІР°С€Рµ РІРёРґРµРѕ]({link})! {quality}\n\n<code>{title}</code>",
        "default_music_response": "Р’РѕС‚ [РІР°С€Рµ Р°СѓРґРёРѕ]({link})!\n\n<code>{title}</code>",
        "default_channel": "<tg-emoji emoji-id=\"5886412370347036129\">рџ‘¤</tg-emoji> РљР°РЅР°Р»: <code>{channel}</code>",
        "downloading_audio": EMOJI_NOTE + " <b>РЎРєР°С‡РёРІР°СЋ Р°СѓРґРёРѕ...</b>",
        "quality_downloading": EMOJI_DOWNLOAD + " <b>РљР°С‡Р°СЋ РІ СѓР»СѓС‡С€РµРЅРЅРѕРј РєР°С‡РµСЃС‚РІРµ...</b>\n\n<i>Р—Р°Р№РјС‘С‚ С‡СѓС‚СЊ РґРѕР»СЊС€Рµ РѕР±С‹С‡РЅРѕРіРѕ.</i>",
        "quality_compressing": EMOJI_COMPRESS + " <b>РЎР¶РёРјР°СЋ РІРёРґРµРѕ РїРµСЂРµРґ РѕС‚РїСЂР°РІРєРѕР№.</b>\n\n" + EMOJI_INFO + " <code>РћСЃС‚Р°Р»РѕСЃСЊ в‰€ {eta}</code>",
        "queue_waiting": EMOJI_QUEUE + " <b>Р’РёРґРµРѕ РІ РѕС‡РµСЂРµРґРё({position})...</b>",
        "done_fallback": "Р“РѕС‚РѕРІРѕ!",
        "extracting_audio": EMOJI_NOTE + " <b>Р’С‹СЂРµР·Р°СЋ Р·РІСѓРє РёР· РІРёРґРµРѕ...</b>",
        "method_proxy": "РїСЂРѕРєСЃРё",
        "method_cookies": "РєСѓРєРё",
        "method_direct": "РЅР°РїСЂСЏРјСѓСЋ",
        "cookies_required_error": EMOJI_CROSS + " <b>РћС€РёР±РєР° РєСѓРєРё.</b> РџСЂРѕСЃСЊР±Р° РІСЃС‚Р°РІРёС‚СЊ РєСѓРєРё С‡РµСЂРµР· РєРѕРјР°РЅРґСѓ <code>.cfg YouTube-DLD youtube_cookies</code>.",
        "supported_sites": """<tg-emoji emoji-id=6005986106703613755>рџЋҐ</tg-emoji> <b>РџРѕРґРґРµСЂР¶РёРІР°РµРјС‹Рµ СЃР°Р№С‚С‹:</b>

<tg-emoji emoji-id="5355235592844095825">рџ”ґ</tg-emoji> <b>YouTube</b> вЂ” youtube.com, youtu.be, music.youtube.com
<tg-emoji emoji-id="5353034628263330616">рџЋµ</tg-emoji> <b>TikTok</b> вЂ” tiktok.com, vt.tiktok.com, vm.tiktok.com
<tg-emoji emoji-id="5355097780228470775">рџ“ё</tg-emoji> <b>Instagram</b> вЂ” instagram.com
<tg-emoji emoji-id="5355148941878900494">рџђ¦</tg-emoji> <b>X (Twitter)</b> вЂ” x.com, twitter.com
<tg-emoji emoji-id="5355254460635428635">рџ‘Ґ</tg-emoji> <b>Facebook</b> вЂ” facebook.com
<tg-emoji emoji-id="5334764984142412896">рџЋ¬</tg-emoji> <b>Vimeo</b> вЂ” vimeo.com
<tg-emoji emoji-id="5352759664457038886">рџЋ®</tg-emoji> <b>Twitch</b> вЂ” twitch.tv
<tg-emoji emoji-id="5352531593103686999">рџ‘Ѕ</tg-emoji> <b>Reddit</b> вЂ” reddit.com

<b><tg-emoji emoji-id=5891249688933305846>рџЋµ</tg-emoji> РњСѓР·С‹РєР°:</b>
<tg-emoji emoji-id="5346296430166293639">рџЋ§</tg-emoji> <b>РЇРЅРґРµРєСЃ.РњСѓР·С‹РєР°</b> вЂ” music.yandex.ru
<tg-emoji emoji-id="5345844509412444249">вЃпёЏ</tg-emoji> <b>SoundCloud</b> вЂ” soundcloud.com
<tg-emoji emoji-id="5451966206334513619">рџЋё</tg-emoji> <b>Bandcamp</b> вЂ” bandcamp.com
<tg-emoji emoji-id="5346074681004801565">рџџў</tg-emoji> <b>Spotify</b> вЂ” spotify.com

<b><tg-emoji emoji-id=5994750571041525522>рџ‡·рџ‡є</tg-emoji> Р РѕСЃСЃРёР№СЃРєРёРµ:</b>
<tg-emoji emoji-id="5298747646096187189">в–¶пёЏ</tg-emoji> <b>RuTube</b> вЂ” rutube.ru
<tg-emoji emoji-id="5278229754099540071">рџ”µ</tg-emoji> <b>Р’РљРѕРЅС‚Р°РєС‚Рµ</b> вЂ” vk.com
<tg-emoji emoji-id="5310076528577491230">рџџ </tg-emoji> <b>РћРґРЅРѕРєР»Р°СЃСЃРЅРёРєРё</b> вЂ” ok.ru

РџРѕР»РЅС‹Р№ СЃРїРёСЃРѕРє РїРѕРґРґРµСЂР¶РёРІР°РµРјС‹С… СЃР°Р№С‚РѕРІ вЂ” <a href="https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md">С‚СѓС‚</a>.

<b><tg-emoji emoji-id=5891243564309942507>рџ“ќ</tg-emoji> РљРѕРјР°РЅРґС‹:</b>
в–«пёЏ .dlvideo <СЃСЃС‹Р»РєР°> вЂ” СЃРєР°С‡Р°С‚СЊ РІРёРґРµРѕ
в–«пёЏ .dlvideo -a <СЃСЃС‹Р»РєР°> вЂ” СЃРєР°С‡Р°С‚СЊ Р°СѓРґРёРѕ
в–«пёЏ .dlvideo -s 1:30 -e 5:00 <СЃСЃС‹Р»РєР°> вЂ” С‚РѕР»СЊРєРѕ РѕС‚СЂРµР·РѕРє (РјРѕР¶РЅРѕ Рё Р±РµР· -e)
в–«пёЏ .dlvideo -p <СЃСЃС‹Р»РєР° РЅР° РїР»РµР№Р»РёСЃС‚> вЂ” СЃРєР°С‡Р°С‚СЊ РїР»РµР№Р»РёСЃС‚ С†РµР»РёРєРѕРј (РґРѕ 30 СЂРѕР»РёРєРѕРІ, РєР°Р¶РґС‹Р№ РѕС‚РґРµР»СЊРЅС‹Рј СЃРѕРѕР±С‰РµРЅРёРµРј)
в–«пёЏ .dvlist вЂ” СЃРїРёСЃРѕРє СЃР°Р№С‚РѕРІ
в–«пёЏ .sblock вЂ” РЅР°СЃС‚СЂРѕР№РєРё SponsorBlock (РёРЅР»Р°Р№РЅ-РјРµРЅСЋ)
в–«пёЏ .dlwl вЂ” РІРєР»/РІС‹РєР» Р°РІС‚РѕР·Р°РіСЂСѓР·РєСѓ РІ СЌС‚РѕРј С‡Р°С‚Рµ, .dlwl <id/@username> вЂ” РєРѕРЅРєСЂРµС‚РЅС‹Р№ С‡Р°С‚, .dlwl list вЂ” СЃРїРёСЃРѕРє
в–«пёЏ .dlvo вЂ” С‚Рѕ Р¶Рµ СЃР°РјРѕРµ, С‡С‚Рѕ .dlvideo, РЅРѕ СЃ РїРµСЂРµРІРѕРґРѕРј РѕР·РІСѓС‡РєРё
в–«пёЏ .dlstop вЂ” РѕСЃС‚Р°РЅРѕРІРёС‚СЊ РІСЃРµ Р°РєС‚РёРІРЅС‹Рµ Р·Р°РіСЂСѓР·РєРё (РёРґСѓС‰РёРµ Рё РІ РѕС‡РµСЂРµРґРё), СЃСЂР°Р·Сѓ РІРѕ РІСЃРµС… С‡Р°С‚Р°С…""",
        "sb_state_on": "РІРєР»СЋС‡С‘РЅ вњ…",
        "sb_state_off": "РІС‹РєР»СЋС‡РµРЅ рџљ«",
        "sb_main_text": EMOJI_SCISSORS + " <b>SponsorBlock</b> вЂ” {state}\n\n" + EMOJI_CHECK + " вЂ” РІС‹СЂРµР¶РµС‚СЃСЏ РїСЂРё СЃРєР°С‡РёРІР°РЅРёРё, " + EMOJI_CROSS + " вЂ” РѕСЃС‚Р°РЅРµС‚СЃСЏ РІ РІРёРґРµРѕ.\nРЈ РїСѓРЅРєС‚Р° СЃ " + EMOJI_GEAR + " РµСЃС‚СЊ РѕС‚РґРµР»СЊРЅС‹Рµ РЅР°СЃС‚СЂРѕР№РєРё.",
        "sb_master_label": "вњ‚пёЏ SponsorBlock вЂ” {state}",
        "sb_close": "вќЊ Р—Р°РєСЂС‹С‚СЊ",
        "sb_cut_answer": "вњ… Р‘СѓРґСѓ РІС‹СЂРµР·Р°С‚СЊ",
        "sb_keep_answer": "вќЊ РћСЃС‚Р°РІР»СЏСЋ РІ РІРёРґРµРѕ",
        "sb_on_answer": "вњ… Р’РєР»СЋС‡РµРЅРѕ",
        "sb_off_answer": "рџљ« Р’С‹РєР»СЋС‡РµРЅРѕ",
        "sb_music_label": "рџЋµ РќРµРјСѓР·С‹РєР°Р»СЊРЅС‹Р№ РјРѕРјРµРЅС‚",
        "sb_music_text": "{label}\n\nРњРѕРјРµРЅС‚ РІРЅСѓС‚СЂРё РјСѓР·С‹РєР°Р»СЊРЅРѕРіРѕ СЂРѕР»РёРєР°, РіРґРµ СЃР°РјРѕР№ РјСѓР·С‹РєРё РЅРµС‚ вЂ” РЅР°РїСЂРёРјРµСЂ, СѓСЃС‚РЅР°СЏ РїРѕРґРІРѕРґРєР° РїРµСЂРµРґ РєР»РёРїРѕРј.\n\nРЎРµР№С‡Р°СЃ: <b>{state}</b>\n\nРўРѕР»СЊРєРѕ РЅР° music.youtube.com: <b>{music_only}</b>\n<i>Р•СЃР»Рё РІРєР»СЋС‡РµРЅРѕ вЂ” РІС‹СЂРµР·Р°РµС‚СЃСЏ С‚РѕР»СЊРєРѕ РєРѕРіРґР° СЃСЃС‹Р»РєР° СЃ music.youtube.com, РЅР° РѕР±С‹С‡РЅРѕРј youtube.com СЃРµРіРјРµРЅС‚ РЅРµ С‚СЂРѕРіР°РµС‚СЃСЏ.</i>",
        "sb_state_cut": "РІС‹СЂРµР·Р°РµС‚СЃСЏ",
        "sb_state_keep": "РѕСЃС‚Р°С‘С‚СЃСЏ РІ РІРёРґРµРѕ",
        "sb_yes": "РґР°",
        "sb_no": "РЅРµС‚",
        "sb_cut_btn": "Р’С‹СЂРµР·Р°С‚СЊ",
        "sb_keep_btn": "РћСЃС‚Р°РІРёС‚СЊ",
        "sb_music_only_btn": "РўРѕР»СЊРєРѕ РЅР° music.youtube.com",
        "sb_back": "в—ЂпёЏ РќР°Р·Р°Рґ",
        "sb_saved": "РЎРѕС…СЂР°РЅРµРЅРѕ",
        "vo_translating": EMOJI_MIC + " <b>РџРµСЂРµРІРѕР¶Сѓ РѕР·РІСѓС‡РєСѓ.</b>\n\n" + EMOJI_INFO + " <code>РћСЃС‚Р°Р»РѕСЃСЊ в‰€ {eta}</code>",
        "vo_translating_simple": EMOJI_MIC + " <b>РџРµСЂРµРІРѕР¶Сѓ РѕР·РІСѓС‡РєСѓ.</b>",
        "vo_failed": EMOJI_WARN + " РћР·РІСѓС‡РєР° РЅРµ РїРѕР»СѓС‡РёР»Р°СЃСЊ: <code>{error}</code>\n\nРћС‚РїСЂР°РІР»СЏСЋ РІРёРґРµРѕ Р±РµР· РїРµСЂРµРІРѕРґР°...",
        "cat_sponsor": "рџ“ў РЎРїРѕРЅСЃРѕСЂ",
        "cat_interaction": "рџ”” РџРѕРґРїРёСЃРєР°",
        "cat_selfpromo": "рџЋ— РЎР°РјРѕСЂРµРєР»Р°РјР°",
        "cat_intro": "вЏЇ РРЅС‚СЂРѕ/РїР°СѓР·Р°",
        "cat_outro": "рџЋ¬ РўРёС‚СЂС‹",
        "cat_preview": "вЏЄ РџСЂРѕРјРѕ/РїРѕРІС‚РѕСЂ",
        "cat_hook": "рџ‘‹ Р’СЃС‚СѓРїР»РµРЅРёРµ",
        "cat_filler": "рџ’¬ РћС‚СЃС‚СѓРїР»РµРЅРёСЏ",
    }

    strings_en = {
        "no_link": EMOJI_WARN + " <b>Please provide a video link, or reply to a message that has one.</b>",
        "youtube_posts_unsupported": EMOJI_WARN + " <b>YouTube posts are temporarily not supported.</b>",
        "default_downloading": "<b>Downloading the video.</b>\n\n" + EMOJI_INFO + " <code>в‰€ {eta} remaining</code>",
        "default_downloading_simple": "<b>Downloading the video.</b>",
        "eta_unknown": "<tg-emoji emoji-id=5350773074578916842>рџ•ђ</tg-emoji>",
        "default_error": "<b>Download failed.</b>\n\n<code>{error}</code>",
        "too_long": "The video is longer than {minutes} min. Download cancelled вЂ” the limit is set in .cfg YouTube-DLD (max_duration).",
        "cancelled": EMOJI_WARN + " <b>Download cancelled (.dlstop).</b>",
        "nothing_to_cancel": EMOJI_WARN + " <b>No active downloads to cancel.</b>",
        "cancelled_ok": EMOJI_OK + " Downloads stopped: <b>{count}</b>",
        "playlist_progress": EMOJI_DOWNLOAD + " <b>Playlist {idx}/{total}</b>\n\n<code>{title}</code>",
        "default_response": "Here's [your video]({link})! {quality}\n\n<code>{title}</code>",
        "default_music_response": "Here's [your audio]({link})!\n\n<code>{title}</code>",
        "default_channel": "<tg-emoji emoji-id=\"5886412370347036129\">рџ‘¤</tg-emoji> Channel: <code>{channel}</code>",
        "downloading_audio": EMOJI_NOTE + " <b>Downloading audio...</b>",
        "quality_downloading": EMOJI_DOWNLOAD + " <b>Downloading in enhanced quality...</b>\n\n<i>Takes a bit longer than usual.</i>",
        "quality_compressing": EMOJI_COMPRESS + " <b>Compressing the video before sending.</b>\n\n" + EMOJI_INFO + " <code>в‰€ {eta} remaining</code>",
        "queue_waiting": EMOJI_QUEUE + " <b>Video queued ({position})...</b>",
        "done_fallback": "Done!",
        "extracting_audio": EMOJI_NOTE + " <b>Extracting audio from the video...</b>",
        "method_proxy": "proxy",
        "method_cookies": "cookies",
        "method_direct": "direct",
        "cookies_required_error": EMOJI_CROSS + " <b>Cookies error.</b> Please add cookies via <code>.cfg YouTube-DLD youtube_cookies</code>.",
        "supported_sites": """<tg-emoji emoji-id=6005986106703613755>рџЋҐ</tg-emoji> <b>Supported sites:</b>

<tg-emoji emoji-id="5355235592844095825">рџ”ґ</tg-emoji> <b>YouTube</b> вЂ” youtube.com, youtu.be, music.youtube.com
<tg-emoji emoji-id="5353034628263330616">рџЋµ</tg-emoji> <b>TikTok</b> вЂ” tiktok.com, vt.tiktok.com, vm.tiktok.com
<tg-emoji emoji-id="5355097780228470775">рџ“ё</tg-emoji> <b>Instagram</b> вЂ” instagram.com
<tg-emoji emoji-id="5355148941878900494">рџђ¦</tg-emoji> <b>X (Twitter)</b> вЂ” x.com, twitter.com
<tg-emoji emoji-id="5355254460635428635">рџ‘Ґ</tg-emoji> <b>Facebook</b> вЂ” facebook.com
<tg-emoji emoji-id="5334764984142412896">рџЋ¬</tg-emoji> <b>Vimeo</b> вЂ” vimeo.com
<tg-emoji emoji-id="5352759664457038886">рџЋ®</tg-emoji> <b>Twitch</b> вЂ” twitch.tv
<tg-emoji emoji-id="5352531593103686999">рџ‘Ѕ</tg-emoji> <b>Reddit</b> вЂ” reddit.com

<b><tg-emoji emoji-id=5891249688933305846>рџЋµ</tg-emoji> Music:</b>
<tg-emoji emoji-id="5346296430166293639">рџЋ§</tg-emoji> <b>Yandex Music</b> вЂ” music.yandex.ru
<tg-emoji emoji-id="5345844509412444249">вЃпёЏ</tg-emoji> <b>SoundCloud</b> вЂ” soundcloud.com
<tg-emoji emoji-id="5451966206334513619">рџЋё</tg-emoji> <b>Bandcamp</b> вЂ” bandcamp.com
<tg-emoji emoji-id="5346074681004801565">рџџў</tg-emoji> <b>Spotify</b> вЂ” spotify.com

<b><tg-emoji emoji-id=5994750571041525522>рџ‡·рџ‡є</tg-emoji> Russian:</b>
<tg-emoji emoji-id="5298747646096187189">в–¶пёЏ</tg-emoji> <b>RuTube</b> вЂ” rutube.ru
<tg-emoji emoji-id="5278229754099540071">рџ”µ</tg-emoji> <b>VK</b> вЂ” vk.com
<tg-emoji emoji-id="5310076528577491230">рџџ </tg-emoji> <b>Odnoklassniki</b> вЂ” ok.ru

Full list of supported sites вЂ” <a href="https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md">here</a>.

<b><tg-emoji emoji-id=5891243564309942507>рџ“ќ</tg-emoji> Commands:</b>
в–«пёЏ .dlvideo <link> вЂ” download video
в–«пёЏ .dlvideo -a <link> вЂ” download audio
в–«пёЏ .dlvideo -s 1:30 -e 5:00 <link> вЂ” just a clip (-e is optional)
в–«пёЏ .dlvideo -p <playlist link> вЂ” download the whole playlist (up to 30 videos, each as a separate message)
в–«пёЏ .dvlist вЂ” list of supported sites
в–«пёЏ .sblock вЂ” SponsorBlock settings (inline menu)
в–«пёЏ .dlwl вЂ” toggle auto-download in this chat, .dlwl <id/@username> вЂ” specific chat, .dlwl list вЂ” list of chats
в–«пёЏ .dlvo вЂ” same as .dlvideo, but with voice-over translation
в–«пёЏ .dlstop вЂ” stop all active downloads (running and queued), across every chat at once""",
        "sb_state_on": "enabled вњ…",
        "sb_state_off": "disabled рџљ«",
        "sb_main_text": EMOJI_SCISSORS + " <b>SponsorBlock</b> вЂ” {state}\n\n" + EMOJI_CHECK + " вЂ” will be cut on download, " + EMOJI_CROSS + " вЂ” stays in the video.\nThe item with " + EMOJI_GEAR + " has its own extra settings.",
        "sb_master_label": "вњ‚пёЏ SponsorBlock вЂ” {state}",
        "sb_close": "вќЊ Close",
        "sb_cut_answer": "вњ… Will cut",
        "sb_keep_answer": "вќЊ Leaving it in",
        "sb_on_answer": "вњ… Enabled",
        "sb_off_answer": "рџљ« Disabled",
        "sb_music_label": "рџЋµ Non-music moment",
        "sb_music_text": "{label}\n\nA moment inside a music video where there's no actual music вЂ” e.g. a spoken intro before the song.\n\nRight now: <b>{state}</b>\n\nOnly on music.youtube.com: <b>{music_only}</b>\n<i>If enabled, it's only cut when the link is from music.youtube.com вЂ” on regular youtube.com the segment is left alone.</i>",
        "sb_state_cut": "will be cut",
        "sb_state_keep": "stays in the video",
        "sb_yes": "yes",
        "sb_no": "no",
        "sb_cut_btn": "Cut",
        "sb_keep_btn": "Keep",
        "sb_music_only_btn": "Only on music.youtube.com",
        "sb_back": "в—ЂпёЏ Back",
        "sb_saved": "Saved",
        "vo_translating": EMOJI_MIC + " <b>Translating voice-over.</b>\n\n" + EMOJI_INFO + " <code>в‰€ {eta} remaining</code>",
        "vo_translating_simple": EMOJI_MIC + " <b>Translating voice-over.</b>",
        "vo_failed": EMOJI_WARN + " Voice-over failed: <code>{error}</code>\n\nSending the video without translation...",
        "cat_sponsor": "рџ“ў Sponsor",
        "cat_interaction": "рџ”” Subscribe reminder",
        "cat_selfpromo": "рџЋ— Self-promo",
        "cat_intro": "вЏЇ Intro/intermission",
        "cat_outro": "рџЋ¬ Outro/credits",
        "cat_preview": "вЏЄ Preview/recap",
        "cat_hook": "рџ‘‹ Intro hook",
        "cat_filler": "рџ’¬ Filler tangent",
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
        """Р•СЃР»Рё РїСЂРѕС†РµСЃСЃ СѓРїР°Р» РїРѕСЃСЂРµРґРё Р·Р°РіСЂСѓР·РєРё (РєСЂР°С€РЅСѓР»СЃСЏ Р±РµР· Р»РѕРіР°, OOM Рё С‚.Рї.), РїСЂРё СЃР»РµРґСѓСЋС‰РµРј
        СЃС‚Р°СЂС‚Рµ Р·РґРµСЃСЊ РЅР°Р№РґСѓС‚СЃСЏ "РѕСЃРёСЂРѕС‚РµРІС€РёРµ" Р·Р°РїРёСЃРё РІ self.db вЂ” РїСЂРѕР±СѓРµРј РїСЂРѕРґРѕР»Р¶РёС‚СЊ РёС… СЃР°РјРё,
        Р±РµР· СѓС‡Р°СЃС‚РёСЏ СЋР·РµСЂР°. РњР°РєСЃРёРјСѓРј 2 РїРѕРїС‹С‚РєРё РЅР° Р·Р°РіСЂСѓР·РєСѓ, РґР°Р»СЊС€Рµ вЂ” РјРѕР»С‡Р° СЃРґР°С‘РјСЃСЏ Рё С‡РёСЃС‚РёРј."""
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
                        f"{EMOJI_WARN} <b>Р—Р°РіСЂСѓР·РєР° СЃРѕСЂРІР°Р»Р°СЃСЊ РЅРµСЃРєРѕР»СЊРєРѕ СЂР°Р· РїРѕРґСЂСЏРґ, РѕС‚РјРµРЅСЏСЋ.</b>",
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
                    f"{EMOJI_WARN} <b>РќРµ СѓРґР°Р»РѕСЃСЊ РІРѕР·РѕР±РЅРѕРІРёС‚СЊ Р·Р°РіСЂСѓР·РєСѓ РїРѕСЃР»Рµ РєСЂР°С€Р°: "
                    f"РІ СЃРѕРѕР±С‰РµРЅРёРё РЅРµ РЅР°Р№РґРµРЅР° СЃСЃС‹Р»РєР°.</b>\n\n"
                    f"<code>{html_escaping.escape(debug_text) or '(РїСѓСЃС‚Рѕ)'}</code>"
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
                    f"{EMOJI_WARN} <b>РљСЂР°С€, РїРѕРІС‚РѕСЂСЏСЋ РїРѕРїС‹С‚РєСѓ...</b>", parse_mode="HTML"
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
                logger.warning(f"РќРµ СѓРґР°Р»РѕСЃСЊ РїСЂРѕРґРѕР»Р¶РёС‚СЊ Р·Р°РіСЂСѓР·РєСѓ РїРѕСЃР»Рµ РїРµСЂРµР·Р°РїСѓСЃРєР°: {resume_err}")

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
                    description="рџ“ѓ РЎСЋРґР° РїСЂРёР»РµС‚Р°СЋС‚ Р»РѕРіРё Р°РІС‚РѕР·Р°РіСЂСѓР·РєРё РјРѕРґСѓР»СЏ YouTube-DLD (С‚РёС…РёРµ СЃР±РѕРё: РЅРµРїРѕРґРґРµСЂР¶РёРІР°РµРјР°СЏ СЃСЃС‹Р»РєР°, РѕС€РёР±РєР° СЃРєР°С‡РёРІР°РЅРёСЏ Рё С‚.Рї.).",
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
            logger.info("Deno РЅРµ СѓСЃС‚Р°РЅРѕРІР»РµРЅ, РЅР°С‡РёРЅР°СЋ СѓСЃС‚Р°РЅРѕРІРєСѓ...")
            target = await self.get_deno_target()
            
            if not target:
                logger.warning("Windows РЅРµ РїРѕРґРґРµСЂР¶РёРІР°РµС‚СЃСЏ РґР»СЏ Р°РІС‚РѕСѓСЃС‚Р°РЅРѕРІРєРё Deno")
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
                            logger.info("Deno СѓСЃРїРµС€РЅРѕ СЃРєР°С‡Р°РЅ")
                        else:
                            logger.error(f"РќРµ СѓРґР°Р»РѕСЃСЊ СЃРєР°С‡Р°С‚СЊ Deno: HTTP {resp.status}")
                            self.set("deno_source", "install_failed")
                            return
                
                if Path("deno.zip").is_file():
                    with zipfile.ZipFile("deno.zip", "r") as zip_ref:
                        zip_ref.extractall()
                    os.remove("deno.zip")
                    os.chmod(deno_path, 0o755)
                    self.set("deno_source", str(deno_path.resolve()))
                    logger.info(f"Deno СѓСЃС‚Р°РЅРѕРІР»РµРЅ: {deno_path.resolve()}")
            except Exception as e:
                logger.error(f"РћС€РёР±РєР° СѓСЃС‚Р°РЅРѕРІРєРё Deno: {e}")
                self.set("deno_source", "install_failed")
        elif deno_which:
            self.set("deno_source", deno_which)
            logger.info(f"Deno РЅР°Р№РґРµРЅ РІ СЃРёСЃС‚РµРјРµ: {deno_which}")

    def __init__(self):
        self._download_queue = DownloadTurnQueue()
        self._active_jobs = {}
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "show_link",
                True,
                "РџРѕРєР°Р·С‹РІР°С‚СЊ СЃСЃС‹Р»РєСѓ РІ СЃРѕРѕР±С‰РµРЅРёРё?",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "downloading_text",
                self.strings["default_downloading"],
                EMOJI_DOWNLOAD + " РїРµСЂРµРґ СЌС‚РёРј С‚РµРєСЃС‚РѕРј РґРѕР±Р°РІР»СЏРµС‚СЃСЏ РІ РєРѕРґРµ Рё РЅРµ СЂРµРґР°РєС‚РёСЂСѓРµС‚СЃСЏ Р·РґРµСЃСЊ.\n\n"
                "Р”РѕСЃС‚СѓРїРЅС‹Рµ РїР»РµР№СЃС…РѕР»РґРµСЂС‹ (РїРёСЃР°С‚СЊ СЂРѕРІРЅРѕ С‚Р°Рє, СЃ С„РёРіСѓСЂРЅС‹РјРё СЃРєРѕР±РєР°РјРё):\n"
                "{attempt} вЂ” РЅРѕРјРµСЂ РїРѕРїС‹С‚РєРё, {method} вЂ” СЃРїРѕСЃРѕР± (РЅР°РїСЂСЏРјСѓСЋ/РєСѓРєРё/РїСЂРѕРєСЃРё), "
                "{eta} вЂ” РѕСЃС‚Р°РІС€РµРµСЃСЏ РІСЂРµРјСЏ (РѕР±РЅРѕРІР»СЏРµС‚СЃСЏ РІРѕ РІСЂРµРјСЏ СЃРєР°С‡РёРІР°РЅРёСЏ, РїСЂРёРјРµСЂРЅРѕ СЂР°Р· РІ 3 СЃРµРєСѓРЅРґС‹)",
            ),
            loader.ConfigValue(
                "error_text",
                self.strings["default_error"],
                EMOJI_WARN + " РїРµСЂРµРґ СЌС‚РёРј С‚РµРєСЃС‚РѕРј РґРѕР±Р°РІР»СЏРµС‚СЃСЏ РІ РєРѕРґРµ Рё РЅРµ СЂРµРґР°РєС‚РёСЂСѓРµС‚СЃСЏ Р·РґРµСЃСЊ.\n\n"
                "Р”РѕСЃС‚СѓРїРЅС‹Р№ РїР»РµР№СЃС…РѕР»РґРµСЂ (РїРёСЃР°С‚СЊ СЂРѕРІРЅРѕ С‚Р°Рє, СЃ С„РёРіСѓСЂРЅС‹РјРё СЃРєРѕР±РєР°РјРё):\n"
                "{error} вЂ” С‚РµРєСЃС‚ СЃР°РјРѕР№ РѕС€РёР±РєРё",
            ),
            loader.ConfigValue(
                "response_text",
                self.strings["default_response"],
                "РћС‚РІРµС‚ РїРѕСЃР»Рµ Р·Р°РіСЂСѓР·РєРё РІРёРґРµРѕ. РРєРѕРЅРєР° СЃР°Р№С‚Р° РґРѕР±Р°РІР»СЏРµС‚СЃСЏ РІ РєРѕРґРµ РїРµСЂРµРґ С‚РµРєСЃС‚РѕРј Рё РЅРµ "
                "СЂРµРґР°РєС‚РёСЂСѓРµС‚СЃСЏ Р·РґРµСЃСЊ.\n\nР”РѕСЃС‚СѓРїРЅС‹Рµ РїР»РµР№СЃС…РѕР»РґРµСЂС‹: {title} вЂ” РЅР°Р·РІР°РЅРёРµ РІРёРґРµРѕ, "
                "{quality} вЂ” СЂР°Р·СЂРµС€РµРЅРёРµ Рё РєРѕРґРµРє (РЅР°РїСЂРёРјРµСЂ \"720p | h264\"), РїСѓСЃС‚Рѕ РґР»СЏ Р°СѓРґРёРѕ."
            ),
            loader.ConfigValue(
                "music_response_text",
                self.strings["default_music_response"],
                EMOJI_NOTE + " РїРµСЂРµРґ СЌС‚РёРј С‚РµРєСЃС‚РѕРј РґРѕР±Р°РІР»СЏРµС‚СЃСЏ РІ РєРѕРґРµ Рё РЅРµ СЂРµРґР°РєС‚РёСЂСѓРµС‚СЃСЏ Р·РґРµСЃСЊ."
            ),
            loader.ConfigValue(
                "show_channel",
                True,
                "РџРѕРєР°Р·С‹РІР°С‚СЊ РЅР°Р·РІР°РЅРёРµ РєР°РЅР°Р»Р°?",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "youtube_cookies",
                [],
                EMOJI_COOKIE + " РљСѓРєРё РІ С„РѕСЂРјР°С‚Рµ Netscape (РўР•РљРЎРўРћРњ!) вЂ” СЃРїРёСЃРѕРє: РґРѕР±Р°РІР»СЏР№ РєСѓРєРё РєР°Р¶РґРѕРіРѕ СЃР°Р№С‚Р° РћРўР”Р•Р›Р¬РќР«Рњ "
                "СЌР»РµРјРµРЅС‚РѕРј (В«Р”РѕР±Р°РІРёС‚СЊ СЌР»РµРјРµРЅС‚В»), РЅРµ РЅСѓР¶РЅРѕ СЃРєР»РµРёРІР°С‚СЊ РІСЃС‘ РІ РѕРґРёРЅ С‚РµРєСЃС‚. РџРѕРґРґРµСЂР¶РёРІР°СЋС‚СЃСЏ YouTube, "
                "РЇРЅРґРµРєСЃ.РњСѓР·С‹РєР°, VK, Instagram, Twitter/X вЂ” РѕРїСЂРµРґРµР»СЏСЋС‚СЃСЏ Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРё РїРѕ СЃРѕРґРµСЂР¶РёРјРѕРјСѓ, РЅРµРІР°Р¶РЅРѕ РІ РєР°РєРѕРј РїРѕСЂСЏРґРєРµ "
                "РґРѕР±Р°РІР»РµРЅС‹. В«РЈРґР°Р»РёС‚СЊ СЌР»РµРјРµРЅС‚В» СѓРґР°Р»СЏРµС‚ РІС‹Р±СЂР°РЅРЅС‹Р№ С†РµР»РёРєРѕРј (СЃРїРёСЃРѕРє РїРѕРєР°Р¶РµС‚ СЃС‹СЂРѕР№ РІСЃС‚Р°РІР»РµРЅРЅС‹Р№ С‚РµРєСЃС‚, "
                "РЅРµ РЅР°Р·РІР°РЅРёРµ СЃР°Р№С‚Р° вЂ” С‚Р°Рє СЂР°Р±РѕС‚Р°РµС‚ СЌС‚РѕС‚ С‚РёРї РїРѕР»СЏ РІ Heroku).\n\n" +
                EMOJI_WARN + " Р’РђР–РќРћ: Р•СЃР»Рё С‚РІРѕР№ Heroku СЃРµСЂРІРµСЂ РІРѕ Р¤СЂР°РЅС†РёРё/UK - СЌРєСЃРїРѕСЂС‚РёСЂСѓР№ РєСѓРєРё С‡РµСЂРµР· VPN С‚РѕР№ Р¶Рµ СЃС‚СЂР°РЅРµ!\n\n"
                "РљР°Рє РїРѕР»СѓС‡РёС‚СЊ РєСѓРєРё YouTube:\n"
                "1. РџРѕРґРєР»СЋС‡РёСЃСЊ Рє VPN СЃС‚СЂР°РЅС‹ РіРґРµ С‚РІРѕР№ СЃРµСЂРІРµСЂ (РЅРµ РѕР±СЏР·Р°С‚РµР»СЊРЅРѕ)\n"
                "2. РћС‚РєСЂРѕР№ РїСЂРёРІР°С‚РЅРѕРµ РѕРєРЅРѕ РІ Р±СЂР°СѓР·РµСЂРµ в†’ Р·Р°Р»РѕРіРёРЅСЊСЃСЏ РЅР° YouTube\n"
                "3. РџРµСЂРµР№РґРё РЅР° youtube.com/robots.txt\n"
                "4. <a href='https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm'>Cookie-Editor</a> в†’ Export в†’ Netscape\n"
                "5. РЎР РђР—РЈ Р·Р°РєСЂРѕР№ РѕРєРЅРѕ\n"
                "6. Р”РѕР±Р°РІСЊ СЌР»РµРјРµРЅС‚РѕРј РІРµСЃСЊ С‚РµРєСЃС‚ РёР· С„Р°Р№Р»Р°\n\n"
                "РќР°С‡РёРЅР°РµС‚СЃСЏ СЃ: # Netscape HTTP Cookie File",
                validator=loader.validators.Series(validator=loader.validators.Hidden()),
            ),
            loader.ConfigValue(
                "proxy",
                "",
                EMOJI_GLOBE + " РџСЂРѕРєСЃРё (РѕРїС†РёРѕРЅР°Р»СЊРЅРѕ)\n\n"
                "Р¤РѕСЂРјР°С‚С‹:\n"
                "вЂў HTTP: http://user:pass@host:port\n"
                "вЂў SOCKS5: socks5://host:port\n\n"
                "РџСѓСЃС‚Рѕ вЂ” РїСЂРѕРєСЃРё РЅРµ РёСЃРїРѕР»СЊР·СѓРµС‚СЃСЏ. Р—Р°РїРѕР»РЅРµРЅРѕ вЂ” РїСЂРѕР±СѓРµРј С‡РµСЂРµР· РїСЂРѕРєСЃРё, Р·Р°С‚РµРј РєСѓРєРё, Р·Р°С‚РµРј РЅР°РїСЂСЏРјСѓСЋ.\n\n"
                + EMOJI_WARN + " Trojan/VLESS РЅРµ РїРѕРґРґРµСЂР¶РёРІР°СЋС‚СЃСЏ!",
                validator=loader.validators.Hidden(),
            ),
            loader.ConfigValue(
                "whitelist",
                [],
                "рџ“ѓ РЎРїРёСЃРѕРє С‡Р°С‚РѕРІ (ID), РіРґРµ СЃСЃС‹Р»РєРё СЃРєР°С‡РёРІР°СЋС‚СЃСЏ Р°РІС‚РѕРјР°С‚РёС‡РµСЃРєРё. РњРѕР¶РЅРѕ СЂРµРґР°РєС‚РёСЂРѕРІР°С‚СЊ РїСЂСЏРјРѕ Р·РґРµСЃСЊ "
                "РёР»Рё РєРѕРјР°РЅРґРѕР№ .dlwl РІ СЃР°РјРѕРј С‡Р°С‚Рµ.",
                validator=loader.validators.Series(validator=loader.validators.TelegramID()),
            ),
            loader.ConfigValue(
                "auto_quality",
                True,
                "рџЋћ РЈРјРЅРѕРµ РєР°С‡РµСЃС‚РІРѕ. Р•СЃР»Рё РёРЅС‚РµСЂРЅРµС‚ РґРѕСЃС‚Р°С‚РѕС‡РЅРѕ Р±С‹СЃС‚СЂС‹Р№ Рё СЃС‚Р°Р±РёР»СЊРЅС‹Р№ вЂ” РєР°С‡Р°СЋ РєР°С‡РµСЃС‚РІРѕ "
                "РїРѕР»СѓС‡С€Рµ Рё СЃР¶РёРјР°СЋ. Р”РѕР»СЊС€Рµ, РЅРѕ С‡С‘С‚С‡Рµ.",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "max_duration",
                0,
                "<tg-emoji emoji-id=5900104897885376843>рџ•“</tg-emoji> Р›РёРјРёС‚ РґР»РёС‚РµР»СЊРЅРѕСЃС‚Рё РІРёРґРµРѕ РІ РјРёРЅСѓС‚Р°С… (С‚РѕР»СЊРєРѕ YouTube). 0 вЂ” Р±РµР· Р»РёРјРёС‚Р°. "
                "Р’РёРґРµРѕ РґР»РёРЅРЅРµРµ Р»РёРјРёС‚Р° РЅРµ СЃРєР°С‡РёРІР°РµС‚СЃСЏ РІРѕРѕР±С‰Рµ (РґРѕСЂРѕРіРѕ РєР°С‡Р°С‚СЊ/СЃР¶РёРјР°С‚СЊ Рё СЂРёСЃРєСѓРµС‚ "
                "СѓРїРµСЂРµС‚СЊСЃСЏ РІ Р»РёРјРёС‚ Telegram РЅР° СЂР°Р·РјРµСЂ С„Р°Р№Р»Р°).",
                validator=loader.validators.Integer(minimum=0),
            ),
            loader.ConfigValue(
                "vo_orig_volume",
                50,
                "рџ”Љ Р“СЂРѕРјРєРѕСЃС‚СЊ РѕСЂРёРіРёРЅР°Р»СЊРЅРѕР№ РѕР·РІСѓС‡РєРё РїСЂРё РїРµСЂРµРІРѕРґРµ (0-100%), РїРѕРєР° РёРґС‘С‚ РїРµСЂРµРІРѕРґ РїРѕРІРµСЂС…",
                validator=loader.validators.Integer(minimum=0, maximum=100),
            ),
        )

    @loader.command()
    async def dvlist(self, message):
        """РЎРїРёСЃРѕРє РїРѕРґРґРµСЂР¶РёРІР°РµРјС‹С… СЃР°Р№С‚РѕРІ Рё РєРѕРјР°РЅРґ РјРѕРґСѓР»СЏ"""
        await utils.answer(message, self.strings["supported_sites"])

    @loader.command()
    async def sblock(self, message):
        """РќР°СЃС‚СЂРѕР№РєРё SponsorBlock вЂ” С‡С‚Рѕ РІС‹СЂРµР·Р°С‚СЊ РёР· РІРёРґРµРѕ РїСЂРё СЃРєР°С‡РёРІР°РЅРёРё"""
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
            state_icon = "вњ…" if cat_id in active else "вќЊ"
            cat_buttons.append({
                "text": f"{label} {state_icon}",
                "callback": self._sb_toggle_category,
                "args": (cat_id,),
            })
        for i in range(0, len(cat_buttons), 2):
            rows.append(cat_buttons[i:i + 2])

        music_icon = "вњ…" if "music_offtopic" in active else "вќЊ"
        rows.append([{
            "text": f"{self.strings('sb_music_label')} {music_icon} вљ™пёЏ",
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
        """РљСЂР°Р№РЅРёР№ СЃР»СѓС‡Р°Р№: СЃР°Р№С‚ РїРѕРґРґРµСЂР¶РёРІР°РµС‚СЃСЏ (TikTok/Instagram/Pinterest вЂ” С‚Рѕ, С‡С‚Рѕ Рё СЃР°Рј
        @SaveAsBot СѓРјРµРµС‚ РїРѕ РµРіРѕ Р¶Рµ /start), РЅРѕ СЃРєР°С‡Р°С‚СЊ РЅР°РїСЂСЏРјСѓСЋ РЅРµ РІС‹С€Р»Рѕ. РџРµСЂРµСЃС‹Р»Р°РµРј СЃСЃС‹Р»РєСѓ
        @SaveAsBot, Р·Р°Р±РёСЂР°РµРј Сѓ РЅРµРіРѕ РјРµРґРёР° Рё РїРѕСЃС‚РёРј РІ С‡Р°С‚ СЃР°РјРё вЂ” РєР°Рє Р±СѓРґС‚Рѕ СЃРєР°С‡Р°Р»Рё СЃРІРѕРёРјРё
        СЃРёР»Р°РјРё, РїР»СЋСЃ РїРѕРґС‡РёС‰Р°РµРј РїРµСЂРµРїРёСЃРєСѓ СЃ Р±РѕС‚РѕРј, С‡С‚РѕР±С‹ РЅРµ РєРѕРїРёР»СЃСЏ РјСѓСЃРѕСЂ."""
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
                        f"{EMOJI_WARN} <b>@SaveAsBot РЅРµ РѕС‚РІРµС‚РёР» РёР»Рё РЅРµ СЃРјРѕРі СЃРєР°С‡Р°С‚СЊ:</b>\n\n"
                        f"<code>{type(fallback_err).__name__}: {clean_error_text(fallback_err)}</code>"
                    )
                except Exception:
                    pass
                return

            media_messages = [m for m in responses if getattr(m, "media", None)]
            if not media_messages:
                try:
                    await call.edit(f"{EMOJI_WARN} <b>@SaveAsBot РЅРµ РїСЂРёСЃР»Р°Р» РјРµРґРёР° РІ РѕС‚РІРµС‚.</b>")
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
                    await call.edit(f"{EMOJI_WARN} <b>РќРµ СѓРґР°Р»РѕСЃСЊ СЃРєР°С‡Р°С‚СЊ РјРµРґРёР°, РїСЂРёСЃР»Р°РЅРЅРѕРµ @SaveAsBot.</b>")
                except Exception:
                    pass
                try:
                    await client.delete_messages(SAVEASBOT_ID, our_and_their_ids, revoke=True)
                except Exception:
                    pass
                return

            if audio_only:
                type_word = "РђСѓРґРёРѕ"
            elif len(downloaded_files) > 1:
                type_word = None
            elif is_photo[0]:
                type_word = "Р¤РѕС‚Рѕ"
            else:
                type_word = "Р’РёРґРµРѕ"

            site_icon = get_site_emoji_html(link)
            if type_word is None:
                safe_link_attr = html_escaping.escape(link, quote=True)
                header = f'{site_icon} <a href="{safe_link_attr}">РљР°СЂСѓСЃРµР»СЊ</a>.'
            else:
                header = f"{site_icon} {type_word}"

            is_instagram_link = "instagram.com" in link.lower()
            if is_instagram_link:
                title_hint, channel_hint = None, None
            else:
                cookies_cfg = clean_cookies_text("\n".join(self.config["youtube_cookies"]))
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
                    await call.edit(f"{EMOJI_OK} <b>Р“РѕС‚РѕРІРѕ С‡РµСЂРµР· @SaveAsBot!</b>", reply_markup=None)
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
                {"text": f"{'вњ…' if is_on else 'в–«пёЏ'} {self.strings('sb_cut_btn')}", "callback": self._sb_set_music, "args": (True,)},
                {"text": f"{'вњ…' if not is_on else 'в–«пёЏ'} {self.strings('sb_keep_btn')}", "callback": self._sb_set_music, "args": (False,)},
            ],
            [{
                "text": f"{'вњ…' if only_music else 'в–«пёЏ'} {self.strings('sb_music_only_btn')}",
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
        """Р’РєР»/РІС‹РєР» Р°РІС‚РѕР·Р°РіСЂСѓР·РєСѓ СЃСЃС‹Р»РѕРє. Р‘РµР· Р°СЂРіСѓРјРµРЅС‚Р° вЂ” СЌС‚РѕС‚ С‡Р°С‚, .dlwl <id/@username> вЂ” РєРѕРЅРєСЂРµС‚РЅС‹Р№ С‡Р°С‚, .dlwl list вЂ” СЃРїРёСЃРѕРє"""
        args_raw = utils.get_args_raw(message).strip()

        if args_raw.lower() == "list":
            whitelist = self.config["whitelist"]
            if not whitelist:
                await utils.answer(message, "рџ“ѓ Р’Р°Р№С‚Р»РёСЃС‚ РїСѓСЃС‚.")
                return
            lines = []
            for cid in whitelist:
                entity = await self._resolve_whitelist_entity(message.client, cid)
                if entity is None:
                    lines.append(f"вЂў <b>{cid}</b> (<code>{cid}</code>)")
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

                lines.append(f"вЂў {name_part} ({id_part})")
            await utils.answer(message, "рџ“ѓ <b>РђРІС‚РѕР·Р°РіСЂСѓР·РєР° РІРєР»СЋС‡РµРЅР° РІ:</b>\n\n" + "\n".join(lines))
            return

        if args_raw:
            try:
                entity = await message.client.get_entity(args_raw)
                raw_chat_id = await message.client.get_peer_id(entity)
                chat_id = self._normalize_chat_id(raw_chat_id)
            except Exception:
                await utils.answer(message, f"вќЊ РќРµ РЅР°С€Р»Р° С‡Р°С‚/РїРѕР»СЊР·РѕРІР°С‚РµР»СЏ РїРѕ В«{args_raw}В».")
                return
            target_name = tl_utils.get_display_name(entity) or str(raw_chat_id)
        else:
            raw_chat_id = message.chat_id
            chat_id = self._normalize_chat_id(raw_chat_id)
            target_name = "СЌС‚РѕС‚ С‡Р°С‚"

        whitelist = list(self.config["whitelist"])
        if chat_id in whitelist:
            whitelist.remove(chat_id)
            self.config["whitelist"] = whitelist
            await utils.answer(message, f"{EMOJI_FAIL} РђРІС‚РѕР·Р°РіСЂСѓР·РєР° РІС‹РєР»СЋС‡РµРЅР°:\n{target_name} (<code>{raw_chat_id}</code>)")
        else:
            whitelist.append(chat_id)
            self.config["whitelist"] = whitelist
            await utils.answer(message, f"{EMOJI_OK} РђРІС‚РѕР·Р°РіСЂСѓР·РєР° РІРєР»СЋС‡РµРЅР°:\n{target_name} (<code>{raw_chat_id}</code>)")

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
        """РџР»РµР№Р»РёСЃС‚ РїРѕ С„Р»Р°РіСѓ -p: РєР°С‡Р°РµРј РІСЃРµ СЂРѕР»РёРєРё РїРѕ РѕРґРЅРѕРјСѓ, РєР°Р¶РґС‹Р№ вЂ” РѕС‚РґРµР»СЊРЅС‹Рј СЃРѕРѕР±С‰РµРЅРёРµРј.
        Р’РѕР·РІСЂР°С‰Р°РµС‚ True, РµСЃР»Рё СЌС‚Рѕ СЂРµР°Р»СЊРЅРѕ РїР»РµР№Р»РёСЃС‚ (РѕР±СЂР°Р±РѕС‚Р°РЅ С†РµР»РёРєРѕРј РёР»Рё СЃ РїСЂРѕРїСѓСЃРєРѕРј
        СѓРїР°РІС€РёС… СЂРѕР»РёРєРѕРІ), False вЂ” РµСЃР»Рё РїР»РµР№Р»РёСЃС‚Р° РЅРµС‚ Рё РІС‹Р·С‹РІР°СЋС‰РёР№ РёРґС‘С‚ РѕР±С‹С‡РЅС‹Рј РїСѓС‚С‘Рј."""
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
                        .replace("{title}", html_escaping.escape(entry_title or "вЂ¦")),
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
        """РЎРєР°С‡Р°С‚СЊ РІРёРґРµРѕ/Р°СѓРґРёРѕ РїРѕ СЃСЃС‹Р»РєРµ. -a Р°СѓРґРёРѕ, -s/-e РЅР°С‡Р°Р»Рѕ/РєРѕРЅРµС† РѕС‚СЂРµР·РєР°, -p РїР»РµР№Р»РёСЃС‚ (РґРѕ 30 СЂРѕР»РёРєРѕРІ)"""
        await self._dlvideo_impl(message, force_translate=False)

    @loader.command()
    async def dlvo(self, message):
        """РўРѕ Р¶Рµ СЃР°РјРѕРµ С‡С‚Рѕ .dlvideo (С‚Рµ Р¶Рµ С„Р»Р°РіРё -a/-s/-e), РЅРѕ СЃ РїРµСЂРµРІРѕРґРѕРј РѕР·РІСѓС‡РєРё"""
        await self._dlvideo_impl(message, force_translate=True)

    @loader.command()
    async def dlstop(self, message):
        """РћСЃС‚Р°РЅРѕРІРёС‚СЊ Р’РЎР• Р°РєС‚РёРІРЅС‹Рµ Р·Р°РіСЂСѓР·РєРё вЂ” Рё РёРґСѓС‰РёРµ, Рё СЃС‚РѕСЏС‰РёРµ РІ РѕС‡РµСЂРµРґРё, СЃСЂР°Р·Сѓ РІРѕ РІСЃРµС… С‡Р°С‚Р°С…"""
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
                    raise Exception("РЅРµ СѓРґР°Р»РѕСЃСЊ РёР·РІР»РµС‡СЊ Р·РІСѓРє РёР· РІРёРґРµРѕ (ffmpeg)")

                reply_title = (reply.raw_text or "").strip().splitlines()[0][:100] if reply.raw_text else ""
                safe_title = sanitize_media_filename(reply_title, fallback="РђСѓРґРёРѕ")
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

        cookies = clean_cookies_text("\n".join(self.config["youtube_cookies"]))
        proxy = self.config["proxy"].strip() if self.config["proxy"] else None
        is_tiktok = "tiktok.com" in link.lower()
        is_instagram = "instagram.com" in link.lower()
        is_pinterest = "pinterest." in link.lower() or "pin.it" in link.lower()
        is_twitter = "twitter.com" in link.lower() or "x.com" in link.lower()
        is_discord = bool(DISCORD_RE.search(link))
        yandex_track_id = extract_yandex_track_id(link)
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
            return f"{EMOJI_DOWNLOAD} " + self.config["downloading_text"].replace(
                "{attempt}", str(progress["attempt"])
            ).replace(
                "{method}", method_labels.get(progress["method"], progress["method"])
            ).replace(
                "{eta}", progress["eta"]
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
            if audio_only:
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
                    caption = f'{site_icon} <a href="{safe_link_attr}">РљР°СЂСѓСЃРµР»СЊ</a>.'

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

            if yandex_track_id:
                ym_path = None
                ym_cover_path = None
                try:
                    (ym_path, ym_title, ym_artist, ym_album, ym_duration,
                     ym_cover_bytes, ym_meta_debug) = await download_yandex_music_track(
                        link, utils.get_base_dir(), cookies_text=cookies, prefer_flac=raw_quality
                    )

                    used_flac = bool(ym_path) and ym_path.lower().endswith(".flac")
                    info_line = f"{ym_title} вЂ” {ym_artist}" if ym_artist and ym_artist != "Unknown Artist" else ym_title
                    if used_flac:
                        safe_link_attr = html_escaping.escape(link, quote=True)
                        caption = (
                            f'{get_site_emoji_html(link)} <a href="{safe_link_attr}"><b>РђСѓРґРёРѕ</b></a>'
                            f'<b>. Flac</b>\n\n{info_line}'
                        )
                    else:
                        caption_head = convert_markdown_to_html(self.config["music_response_text"], link)
                        caption_head = caption_head.replace("{title}", "")
                        caption_head = re.sub(r"<(\w+)>\s*</\1>\s*$", "", caption_head).rstrip()
                        caption = f"{get_site_emoji_html(link)} {caption_head}\n\n{info_line}"
                    if ym_duration:
                        caption += f"\n{EMOJI_CLOCK} {format_seconds(ym_duration)}"
                    if ym_meta_debug:
                        caption += f"\n\n<code>[РјРµС‚Р°РґР°РЅРЅС‹Рµ РЅРµ РїРѕР»СѓС‡РµРЅС‹: {html_escaping.escape(ym_meta_debug)}]</code>"

                    audio_attributes = [DocumentAttributeAudio(
                        duration=ym_duration or 0,
                        title=ym_title,
                        performer=ym_artist,
                    )]

                    if ym_cover_bytes:
                        ym_cover_path = os.path.join(utils.get_base_dir(), f"ymcover_{uuid.uuid4().hex[:8]}.jpg")
                        async with aiofiles.open(ym_cover_path, "wb") as cf:
                            await cf.write(ym_cover_bytes)

                    send_kwargs = dict(
                        caption=caption, parse_mode="HTML", reply_to=reply or message,
                        attributes=audio_attributes,
                    )
                    if ym_cover_path:
                        send_kwargs["thumb"] = ym_cover_path

                    try:
                        await utils.answer_file(answer_target, ym_path, silent=True, **send_kwargs)
                    except TypeError as silent_err:
                        if "silent" not in str(silent_err):
                            raise
                        await utils.answer_file(answer_target, ym_path, **send_kwargs)
                    try:
                        await status_msg.delete()
                    except Exception:
                        pass
                except Exception as ym_err:
                    logger.warning(f"Yandex Music download failed: {ym_err}")
                    error_msg = cookies_error_message(
                        "РЇРЅРґРµРєСЃ.РњСѓР·С‹РєРё", "music.yandex.ru/robots.txt", clean_error_text(ym_err),
                    )
                    try:
                        await utils.answer(answer_target, error_msg)
                    except Exception:
                        pass
                finally:
                    if ym_cover_path:
                        try:
                            os.remove(ym_cover_path)
                        except Exception:
                            pass
                    if ym_path:
                        try:
                            os.remove(ym_path)
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
                                last_err = Exception("РЎРєР°С‡Р°Р»СЃСЏ С„Р°Р№Р» Р±РµР· РІРёРґРµРѕРґРѕСЂРѕР¶РєРё (С‚РѕР»СЊРєРѕ Р·РІСѓРє) вЂ” РїСЂРѕР±СѓСЋ РµС‰С‘ СЂР°Р·")
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
                            last_err = Exception("РЎРєР°С‡Р°Р»СЃСЏ С„Р°Р№Р» Р±РµР· РІРёРґРµРѕРґРѕСЂРѕР¶РєРё (С‚РѕР»СЊРєРѕ Р·РІСѓРє) вЂ” РїСЂРѕР±СѓСЋ РµС‰С‘ СЂР°Р·")
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
                            translation_marker = f"{EMOJI_GLOBE} {lang_display(source_lang)} вћ” {lang_display(vo_lang)}\n"
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
                    f"{format_seconds(end_time) if end_time is not None else 'вЂ¦'}</code>)"
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

                    info_line = f"{title} вЂ” {channel}" if (self.config["show_channel"] and channel) else (title or "")
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
                        for src_word, dst_word in (("Р’РёРґРµРѕ", "Р“РёС„"), ("РІРёРґРµРѕ", "РіРёС„"), ("Р’РР”Р•Рћ", "Р“РР¤")):
                            caption = caption.replace(src_word, dst_word)
                    elif is_downloaded_photo:
                        for src_word, dst_word in (("Р’РёРґРµРѕ", "Р¤РѕС‚Рѕ"), ("РІРёРґРµРѕ", "С„РѕС‚Рѕ"), ("Р’РР”Р•Рћ", "Р¤РћРўРћ")):
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
                        f"{EMOJI_WARN} <b>YouTube-DLD: Р°РІС‚РѕР·Р°РіСЂСѓР·РєР° РЅРµ СЃРјРѕРіР»Р° СЃРєР°С‡Р°С‚СЊ СЃСЃС‹Р»РєСѓ</b>\n\n"
                        f"Р§Р°С‚: <code>{message.chat_id}</code>\n"
                        f"РЎСЃС‹Р»РєР°: <code>{link}</code>\n\n"
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
                        clean_error_text(instagram_carousel_err or e),
                    )
                else:
                    error_msg = (
                        f"{EMOJI_CROSS} <b>Р—Р°РіСЂСѓР·РєР° РЅРµ СѓРґР°Р»Р°СЃСЊ</b> (РЅСѓР¶РЅС‹ РєСѓРєРё).\n\n"
                        f"<code>{clean_error_text(instagram_carousel_err or e)}</code>"
                    )
            elif twitter_needs_cookies:
                error_msg = cookies_error_message("Twitter/X", "x.com/robots.txt", clean_error_text(e))
            else:
                error_msg = f"{EMOJI_WARN} " + self.config["error_text"].replace("{error}", clean_error_text(e))

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
                            "text": "рџ“Ґ РЎРєР°С‡Р°С‚СЊ С‡РµСЂРµР· @SaveAsBot",
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
