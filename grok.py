version = (1, 0, 0)

# meta developer: @RUIS_VlP

import random
from datetime import timedelta
from telethon import events
from telethon import functions
from telethon.tl.types import Message
from .. import loader, utils

bot = "@GrokAI"
bot_id = 7828964235

@loader.tds
class GrokAIMod(loader.Module):
    """Модуль для нейросети Grok через бота @GrokAI"""

    strings = {
        "name": "GrokAI",
    }
            	
    @loader.command()
    async def grokdelcmd(self, message):
        """- очищает историю переписки с нейросетью (контекст)"""
        chat = bot_id
        text = "/newchat"
        async with message.client.conversation(bot) as conv:
            response = await conv.send_message(text)
            response1 = await conv.wait_event(events.NewMessage(incoming=True, from_users=chat))
            await utils.answer(message, "✅ <b>Контекст успешно очищен!</b>")
            await response.delete()
            await response1.delete()
           
           
    @loader.command()
    async def grokcmd(self, message):
        """<текст> - запрос к нейросети Grok"""
        chat = bot_id
        reply = await message.get_reply_message()
        text = reply.raw_text if reply else utils.get_args_raw(message)
        if len(text) < 3:
        	await utils.answer(message, "🚫<b>Ошибка!\nСлишком маленький запрос.</b>")
        	return
        await utils.answer(message, "🤖<b>Нейросеть обрабатывает ваш запрос...</b>")
        async with message.client.conversation(bot) as conv:
            response = await conv.send_message(text)
            response1 = await conv.wait_event(events.NewMessage(incoming=True, from_users=chat))
            await utils.answer(message, f"❓<b>Вопрос:</b> \n{text}\n\n🤖 <b>Ответ нейросети:</b>\n{response1.text}")
            await response.delete()
            await response1.delete()