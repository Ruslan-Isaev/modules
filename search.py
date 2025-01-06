# meta developer: @matubuntu, @RUIS_VlP
from telethon import TelegramClient, events, sync, utils
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
    """🌐 Internet search module"""

    strings = {"name": "search"}

    @loader.command()
    async def searchcmd(self, message):
        """<text> / <reply> - 🌐 Search Internet"""
        if not message.is_reply:
         if len(message.text) < 10:
          await message.edit("request not found")
          return
         reply_text = message.text[8:]
        else:
         replied_message = await message.get_reply_message()
         reply_text = replied_message.text 
        await self.inline.form(
    text="🌐 Search Internet",
    message=message,
    reply_markup = [
    [
        {"text": "Yandex", "url": f"https://yandex.ru/search/?text={reply_text}"}, {"text": "Google", "url": f"https://www.google.com/search?q={reply_text}"}
    ],
    [
        {"text": "DuckDuckGo", "url": f"https://duckduckgo.com/?q={reply_text}"}
    ]
    ])
    @loader.inline_handler()
    async def search(self, query: InlineQuery):
        """<text> - 🌐 Search Internet"""
        reply_text = query.query[7:]
        if reply_text == "":
         return
        button = [
    [
        {"text": "Yandex", "url": f"https://yandex.ru/search/?text={reply_text}"}, {"text": "Google", "url": f"https://www.google.com/search?q={reply_text}"}
    ],
    [
        {"text": "DuckDuckGo", "url": f"https://duckduckgo.com/?q={reply_text}"}
    ]
    ]
        return {
            "title": "Search",
            "description": "🌐 Search Internet",
            "thumb": "https://0x0.st/XlHF.png",
            "message": "🌐 Search Internet",
            "reply_markup": button,
        }