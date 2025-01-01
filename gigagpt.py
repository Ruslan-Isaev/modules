version = (1, 0, 0)

# meta developer: @RUIS_VlP, @matubuntu

import random
from datetime import timedelta
from telethon import events
from telethon import functions
from telethon.tl.types import Message
from .. import loader, utils

bot = ["@GPTChatRBot", 5989217330]
bot1 = ["@gigachat_bot", 6218783903]
@loader.tds
class RUISChatGPTMod(loader.Module):
    """ChatGPT 3, Gigachat без API ключа и с контекстом. Бот, который используется для запросов: @Gigachat_bot и @GPTChatRBot. Модуль распространяется по лицензии MIT."""

    strings = {
        "name": "RUIS-GigaGpt",
    }
            	
    @loader.command()
    async def gptdelcmd(self, message):
        """- очищает историю переписки с нейросетью(контекст)"""
        chat = bot[1]
        text = "/clear"
        async with message.client.conversation(bot[0]) as conv:
            response = await conv.send_message(text)
            response1 = await conv.wait_event(events.NewMessage(incoming=True, from_users=chat))
            await utils.answer(message, "✅<b>Контекст успешно очищен!</b>")
            await response.delete()
            await response1.delete()
           
    @loader.command()
    async def giga(self, message):
        """<текст> - запрос к нейросети GigaChat"""
        chat = bot1[1]
        reply = await message.get_reply_message()
        text = reply.raw_text if reply else message.text[5:]
        if len(text) < 3:
         await utils.answer(message, "🚫<b>Ошибка!\nСлишком маленький запрос.</b>")
         return
        await utils.answer(message, "🤖<b>Нейросеть обрабатывает ваш запрос...</b>")
        async with message.client.conversation(bot1[0]) as conv:
            
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
    async def gigadelcmd(self, message):
        """- очищает историю переписки с нейросетью(контекст)"""
        chat = bot1[1]
        text = "🆕 Перезапустить диалог"
        async with message.client.conversation(bot1[0]) as conv:
            response = await conv.send_message(text)
            response1 = await conv.wait_event(events.NewMessage(incoming=True, from_users=chat))
            await utils.answer(message, "✅<b>Контекст успешно очищен!</b>")
            await response.delete()
            await response1.delete()
           
    @loader.command()
    async def gptcmd(self, message):
        """<текст> - запрос к нейросети ChatGPT"""
        chat = bot[1]
        reply = await message.get_reply_message()
        text = reply.raw_text if reply else message.text[5:]
        if len(text) < 3:
        	await utils.answer(message, "🚫<b>Ошибка!\nСлишком маленький запрос.</b>")
        	return
        await utils.answer(message, "🤖<b>Нейросеть обрабатывает ваш запрос...</b>")
        async with message.client.conversation(bot[0]) as conv:
            response = await conv.send_message(text)
            response1 = await conv.wait_event(events.NewMessage(incoming=True, from_users=chat))
            await utils.answer(message, f"❓<b>Вопрос:</b> \n{text}\n\n🤖 <b>Ответ нейросети:</b>\n{response1.text}")
            await response.delete()
            await response1.delete()