version = (1, 0, 0)

# meta developer: @RUIS_VlP

import telethon
from .. import loader, utils

@loader.tds
class QuotlyMod(loader.Module):
    """Модуль для создания стикеров по сообщению через @QuotLyBot"""

    strings = {
        "name": "Quotly",
    }
    
    async def on_dlmod(self):
        await self.client.send_message("@QuotLyBot", "/start")
    
    bot = ["@QuotLyBot", 1031952739]
    
    @loader.command()
    async def quotly(self, message):
        """<reply> - создать стикер по сообщению"""
        reply = await message.get_reply_message()
        try: chat_id = message.chat_id
        except: chat_id = (await utils.get_user(message)).id
        if not reply:
        	await utils.answer(message, "❌ <b>Команда должна быть ответом на сообщение!</b>")
        	return
        try:
        	async with message.client.conversation(self.bot[0]) as conv:
        		forward = await reply.forward_to(self.bot[0])
        		answer = await conv.wait_event(telethon.events.NewMessage(incoming=True, from_users=self.bot[1]))
        	await utils.answer_file(message, answer.message)
        	await forward.delete()
        	await answer.delete()
        except Exception as e:
        	await utils.answer(message, f"❌ <b>Ошибка!</b>\n\n<code>{e}</code>")