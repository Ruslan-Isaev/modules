version = (2, 2, 8)

# meta developer: @RUIS_VlP

import random
from datetime import timedelta

from telethon import functions
from telethon.tl.types import Message

from .. import loader, utils


@loader.tds
class IrisSupMod(loader.Module):
    """Саппорт для лс"""

    strings = {
        "name": "irissup",
    }

    def __init__(self):
        self.name = self.strings["name"]

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        self.myid = (await client.get_me()).id
        self.iris = 5443619563

    async def message_q(
        self,
        text: str,
        user_id: int,
        mark_read: bool = False,
        delete: bool = False,
    ):
        """Отправляет сообщение и возращает ответ"""
        async with self.client.conversation(user_id) as conv:
            msg = await conv.send_message(text)
            response = await conv.get_response()
            if mark_read:
                await conv.mark_read()

            if delete:
                await msg.delete()
                await response.delete()

            return response
        
    @loader.command()
    async def команды(self, message):
        """Команды Iris Support Bot"""
        ihelp = (
            "Команды Iris Support Bot: https://teletype.in/@iris_cm/isb_commands"
        )
        await utils.answer(message, ihelp)
    
    
    @loader.command()
    async def перевод(self, message):
        """перевод текста с помощью Iris Support Bot"""
        bot = "@IrisSupportBot"
        if len(message.text) < 11:
        	try:
        		reply = await message.get_reply_message()
        		text = reply.raw_text
        		text = f".переведи \n{text}"
        		givs = await self.message_q(text, bot, mark_read=True, delete=True)
        		await utils.answer(message, givs)
        		return
        	except:
        		await utils.answer(message, "Где текст?")
        		return
        text = f".переведи {message.text[9:]}"
        givs = await self.message_q(
            text,
            bot,
            mark_read=True,
            delete=True,
        )
        await utils.answer(message, givs.text)
        
    @loader.command()
    async def раскладка(self, message):
        """меняет раскладку текста с помощью Iris Support Bot"""
        bot = "@IrisSupportBot"
        if len(message.text) < 15:
        	try:
        		reply = await message.get_reply_message()
        		text = reply.raw_text
        		text = f".раскладка {text}"
        		givs = await self.message_q(text, bot, mark_read=True, delete=True)
        		await utils.answer(message, givs)
        		return
        	except:
        		await utils.answer(message, "Где текст?")
        		return
        text = f".раскладка {message.text[11:]}"
        givs = await self.message_q(
            text,
            bot,
            mark_read=True,
            delete=True,
        )
        await utils.answer(message, givs.text)
        
    @loader.command()
    async def длина(self, message):
        """перевод текста с помощью Iris Support Bot"""
        bot = "@IrisSupportBot"
        if len(message.text) < 10:
        	try:
        		reply = await message.get_reply_message()
        		text = reply.raw_text
        		text = f".длина {text}"
        		givs = await self.message_q(text, bot, mark_read=True, delete=True)
        		await utils.answer(message, givs)
        		return
        	except:
        		await utils.answer(message, "Где текст?")
        		return
        text = f".длина {message.text[7:]}"
        givs = await self.message_q(
            text,
            bot,
            mark_read=True,
            delete=True,
        )
        await utils.answer(message, givs.text)
        
    @loader.command()
    async def сап(self, message):
        """передает введенную команду в Iris Support Bot"""
        bot = "@IrisSupportBot"
        if len(message.text) < 6:
        	await utils.answer(message, "Где текст?")
        	return
        text = f".{message.text[4:]}"
        offtoptext = """⚠️ <b>Внимание! В этой беседе запрещён оффтоп.</b>
<i>Если вы хотите поболтать или обсудить что-то, то переходите в </i><a href="https://t.me/iris_talk"><i>оффтоп-чатик</i></a><i>!</i>

ℹ️ <b>Оффтоп</b> — <u>сообщения не по теме чата</u>. Этот чат только по вопросам <a href="https://t.me/iris_cm">Iris | Чат-менеджера</a>.

💬 Если вы проигнорируете это сообщение, то модераторы в полном праве могут выдать вам наказание или удалить из чата!
        """
        if message.text[4:] == " оффтоп" or message.text[4:] == "оффтоп":
          await self.inline.form(
    text=offtoptext,
    message=message,
    reply_markup = [
    [
        {"text": "💬 В оффтоп-чат", "url": f"https://t.me/iris_talk"}, {"text": "🧠 Стать умнее", "url": f"https://teletype.in/@iris_cm/rules"}
    ],
    ])
          return
        givs = await self.message_q(
            text,
            bot,
            mark_read=True,
            delete=True,
        )
        await utils.answer(message, givs.text)
    
        
       
        
        
