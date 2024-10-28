# -*- coding: utf-8 -*-
# meta developer: @qShad0, @RUIS_VlP

from telethon.tl.types import Message
from .. import loader, utils
from ..inline.types import (
    BotInlineCall,
    BotInlineMessage,
    BotMessage,
    InlineCall,
    InlineMessage,
    InlineQuery,
    InlineUnit,
)

@loader.tds
class SearchMod(loader.Module):
    """Модуль для поиска в интернете"""

    strings = {"name": "search"}

    @loader.command()
    async def searchcmd(self, message):
        """<text> / <reply> - 🔍 Поиск в Интернете"""
        if not message.is_reply:
        	if len(message.text) < 10:
        		await message.edit("Текст для поиска не обнаружен!")
        		return
        	reply_text = message.text[8:]
        else:
        	replied_message = await message.get_reply_message()
        	reply_text = replied_message.text 
        await self.inline.form(
    text="🔍 Поиск в Интернете",
    message=message,
    reply_markup = [
    [
        {"text": "Yandex", "url": f"https://yandex.ru/search/?text={reply_text}"}
    ],
    [
        {"text": "Google", "url": f"https://www.google.com/search?q={reply_text}"}
    ],
    [
        {"text": "DuckDuckGo", "url": f"https://duckduckgo.com/?q={reply_text}"}
    ]
    ])
    @loader.inline_handler()
    async def search(self, query: InlineQuery):
        """<text> - 🔍 Поиск в Интернете"""
        reply_text = query.query[7:]
        if reply_text == "":
        	return
        button = [
    [
        {"text": "Yandex", "url": f"https://yandex.ru/search/?text={reply_text}"}
    ],
    [
        {"text": "Google", "url": f"https://www.google.com/search?q={reply_text}"}
    ],
    [
        {"text": "DuckDuckGo", "url": f"https://duckduckgo.com/?q={reply_text}"}
    ]
    ]
        return {
            "title": "Search",
            "description": "🔍 Поиск в Интернете",
            "thumb": "https://i.imgur.com/7T3GKiD.jpeg",
            "message": "🔍 Поиск в Интернете",
            "reply_markup": button,
        }

    