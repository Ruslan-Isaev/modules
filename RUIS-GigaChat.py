version = (1, 0, 0)

# meta developer: @RUIS_VlP

import random
from datetime import timedelta
from telethon import events
from telethon import functions
from telethon.tl.types import Message
from .. import loader, utils

bot = "@gigachat_bot"

@loader.tds
class RUISGigaChatMod(loader.Module):
    """GigaChat без API ключа. Интеллект на уровне ChatGPT 3. Бот, который используется для запросов: @gigachat_bot. Модуль распространяется по лицензии MIT."""

    strings = {
        "name": "RUIS-GigaChat",
    }
    
    @loader.command()
    async def gpt(self, message):
        """<текст> - запрос к нейросети GigaChat"""
        chat = 6218783903
        reply = await message.get_reply_message()
        text = reply.raw_text if reply else message.text[5:]
        if len(text) < 3:
        	await utils.answer(message, "🚫<b>Ошибка!\nСлишком маленький запрос.</b>")
        	return
        await utils.answer(message, "🤖<b>Нейросеть обрабатывает ваш запрос...</b>")
        async with message.client.conversation(bot) as conv:
            
            response = await conv.send_message(text)
            
            response1 = await conv.wait_event(events.NewMessage(incoming=True, from_users=chat))
            
            if "💭Ещё чуть-чуть, готовлю ответ" in response1.text:
            	response2 = await conv.wait_event(events.NewMessage(incoming=True, from_users=chat))
            	await utils.answer(message, f"❓<b>Вопрос:</b> \n{text}\n\n🤖 <b>Ответ нейросети:</b>\n{response2.text}")
            	await response.delete()
            	await response1.delete()
            	await response2.delete()
            	return
            else:
            	await utils.answer(message, f"❓<b>Вопрос:</b> \n{text}\n\n🤖 <b>Ответ нейросети:</b>\n{response1.text}")
            	await response.delete()
            	await response1.delete()
            	
    @loader.command()
    async def deletecontext(self, message):
        """- очищает историю переписки с нейросетью(контекст)"""
        chat = 6218783903
        text = "🆕 Перезапустить диалог"
        async with message.client.conversation(bot) as conv:
            response = await conv.send_message(text)
            response1 = await conv.wait_event(events.NewMessage(incoming=True, from_users=chat))
            await utils.answer(message, "✅<b>Контекст успешно очищен!</b>")
            await response.delete()
            await response1.delete()
            