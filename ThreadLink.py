# meta developer: @RUIS_VlP, @matubuntu

import re
from telethon import TelegramClient, events, sync, utils
from telethon.tl.types import Channel, Chat
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
class ThreadMod(loader.Module):
    """Модуль для получения ветки"""

    strings = {"name": "Thread"}

    @loader.command()
    async def threadlink(self, message):
        """Получает ссылку на ветку сообщений.
        """
        reply = await message.get_reply_message()
        if not reply:
            await utils.answer(message, "❌ <b>Команда должна быть ответом на сообщение!</b>")
            return
        try:
        	cid = message.chat.id
        except:
        	await utils.answer(message, "❌ <b>Команда доступна только в чатах и каналах!</b>")
        	return
        chat = await message.get_chat()
        url = f'https://t.me/{chat.username}' if chat.username else f'https://t.me/c/{chat.id}'
        msg_link = f"{url}/{reply.id}?thread={reply.id}"
        await utils.answer(message, "<b>🪵 Ветка сообщений</b>", reply_markup={"text": "Перейти", "url": msg_link})