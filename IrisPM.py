version = (2, 2, 8)

# meta developer: @YA_ManuI

import random
from datetime import timedelta
from telethon import functions
from telethon.tl.types import Message
from telethon import events
from .. import loader, utils
import os
import logging
import time
import datetime
from telethon.tl.custom import Message
from .. import utils, loader
from random import choice

cubes = ["🎲 Выпало: 1", "🎲 Выпало: 2", "🎲 Выпало: 3", "🎲 Выпало: 4", "🎲 Выпало: 5", "🎲 Выпало: 6"]

bot = "@iris_black_bot"

@loader.tds
class IrisMods(loader.Module):
    """Ирис чат менеджер для пользования в лс"""

    strings = {
        "name": "IrisPM"
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
    async def кубик(self, m):
        "кинуть кубик"
        randomfraza = choice(cubes)
        await utils.answer(m, randomfraza)

    @loader.command()
    async def передать(self, message):
        """Передает ириски/голд или од на другой акк"""
        
        args = utils.get_args_raw(message)
        nmb = int(args.split(" ")[1])
        if message.is_reply:
            replied_to = await message.get_reply_message()
            player = "@" + str(replied_to.from_id)
        else:            
            player = args.split(" ")[2]
        dada = ""
        if args.split(" ")[0] == "голд":
            dada = " голд"
        elif args.split(" ")[0] == "ириски" or args[0] == "ирис":
            dada = ""
        if args.split(" ")[0] == "од":
            dada = " од"
        else:
            return await utils.answer(
                message, "❌| Ошибка,что-бы передать требуется написать ириски голд или од."
            )

        text = f"Передать{dada} {nmb} {player}"
        try:
            text += f'\n{args.split(" | ")[1]}'
        except IndexError:
            pass
            givs = await self.message_q(
            text,
            bot,
            mark_read=True,
            delete=True,
        )

        await utils.answer(message, givs.text)

    @loader.command()
    async def ГМИ(self, message):
        """Информация о путешествии ваших ирисок"""
        
        text = f"где мои ириски"
        givs = await self.message_q(
            text,
            bot,
            mark_read=True,
            delete=True,
        )

        await utils.answer(message, givs.text)

    @loader.command()
    async def ГМЗ(self, message):
        """Информация о путешествии ваших голд"""
        
        text = f"где моя голда"
        givs = await self.message_q(
            text,
            bot,
            mark_read=True,
            delete=True,
        )

        await utils.answer(message, givs.text)

    @loader.command()
    async def ГМП(self, message):
        """Информация о путешествии ваших од"""
        
        text = f"где мои пончики"
        givs = await self.message_q(
            text,
            bot,
            mark_read=True,
            delete=True,
        )

        await utils.answer(message, givs.text)
    
    @loader.command()
    async def мешокcmd(self, message):
        """Показывает ваш мешок"""

        
        bags = await self.message_q(
            "Мешок",
            bot,
            delete=True,
        )

        args = utils.get_args_raw(message)

        if not args:
            await utils.answer(message, bags.text)
            
    @loader.command()
    async def биржа(self, message):
        """Информация о данном состоянии биржи"""
        
        text = f"биржа"
        trade = await self.message_q(
            text,
            bot,
            mark_read=True,
            delete=True,
        )

        await utils.answer(message, trade.text) 
        
    @loader.command()
    async def хелп(self, message):
        """выводит помощь по ирису"""
        chat = 5443619563
        text = f".помощь"
        async with message.client.conversation(chat) as conv:
            await utils.answer(message, "<b>Подождите...</b>")
            await conv.send_message(text)
            response1 = await conv.wait_event(events.NewMessage(incoming=True, from_users=5443619563))
            if response1.text == "Установка меню":
            	response2 = await conv.wait_event(events.NewMessage(incoming=True, from_users=5443619563))
            	await utils.answer(message, response2.text)
            	return
            else:
            	await utils.answer(message, response1.text)
            
        
    @loader.command()
    async def итоп(self, message):
        """выводит бтоп дня"""
        
        text = f"бтоп дня"
        top = await self.message_q(
            text,
            bot,
            mark_read=True,
            delete=True,
        )
        
        await utils.answer(message, top.text)
        
    @loader.command()
    async def ипинг(self, message):
        """выводит актив ириса"""
        
        text = f".актив ириса"
        ping = await self.message_q(
            text,
            bot,
            mark_read=True,
            delete=True,
        )
        
        await utils.answer(message, ping.text)
        
    @loader.command()
    async def ф(self, message):
        """обычная ферма"""
        
        text = f"фарма"
        farm = await self.message_q(
            text,
            bot,
            mark_read=True,
            delete=True,
        )
        
        await utils.answer(message, farm.text)
        
    @loader.command()
    async def голд(self, message):
        """выводит топ хранителей голды"""
        
        text = f"золотой рейтинг"
        topg = await self.message_q(
            text,
            bot,
            mark_read=True,
            delete=True,
        )
        
        await utils.answer(message, topg.text)
        
    @loader.command()
    async def графикcmd(self, message):
        """выводит график цен голды"""

        await utils.answer(message, self.strings("loading_photo"))
        
        async with self._client.conversation("@iris_black_bot") as conv:
            
            await conv.send_message(".биржа график")
      
            otvet = await conv.get_response()
          
            if otvet.photo:
                phota = await self._client.download_media(otvet.photo, "graphic")
                await message.client.send_message(
                    message.peer_id,
                    file=phota,
                    reply_to=getattr(message, "reply_to_msg_id", None),
                    )

                os.remove(phota)
                
                await message.delete()
        
    @loader.command()
    async def ком(self, message):
        """выводит команды ириса"""
        
        text = f"команды"
        commands = await self.message_q(
            text,
            bot,
            mark_read=True,
            delete=True,
        )
        
        await utils.answer(message, commands.text)
        
    async def осиcmd(self, message):
        """официальная сетка ириса"""
        osi = (
            "🗓| <b>Чаты из сетки «ирис_чм»:\n"
            "<b><i>1. <emoji document_id=5319161050128459957>👨‍💻</emoji> Iris | Помощь по функционалу</i></b>\n"
            "@iris_cm_chat\n\n"
            "<b><i>2. <emoji document_id=5291897920583381342>🥵</emoji> Iris | Оффтоп</i></b>\n"
            "@iris_talk\n\n"
            "<b><i>3. <emoji document_id=5213224006735376143>💩</emoji> Iris | Антиспам дружина</i></b>\n"
            "@iris_spam\n\n"
            "<b><i>4. <emoji document_id=5240379805047728736>💰</emoji> Iris | Биржа</i></b>\n"
            "@iris_trade\n\n"
            "<b><i>5. <emoji document_id=5224570799230298867>☣️</emoji> Iris | Биовойны</i></b>\n"
            "@iris_biogame\n\n"
            "<b><i>6. <emoji document_id=5404573776253825754>🍬</emoji> Iris | Акции и бонусы</i></b>\n"
            "@iris_bonus\n\n"
            "<b><i>7. <emoji document_id=5314678293977378981>☎️</emoji> Iris | Мастерская идей</i></b>\n"
            "@iris_brief_chat\n\n"
            "<b><i>8. <emoji document_id=5215209935188534658>📝</emoji> Iris | Отзывы об агентах</i></b>\n"
            "@iris_feedback\n\n"
            "<b><i>9. <emoji document_id=5402320181143811311>🤨</emoji> Iris | Золотые дуэли</i></b>\n"
            "@iris_duels\n\n"
        )
        await utils.answer(message, osi)        
        
    async def хелпирисcmd(self, message):
        """Помощь по модулю Ирис для лс"""
        ihelp = (
            "🍀| <b>Помощь по командам:</b>\n\n <code>.передать</code> - передаёт ириски/голд/од\n"
            "<code>.гми</code> - выводит путешествие ваших ирисок за последнее время.\n"
            "<code>.гмз</code> - выводит путешествие ваших голд за последнее время \n"
            "<code>.гмп</code> - выводит путешествие ваших од за последнее время \n"
            "<code>.мешок</code> -покажет ваш мешочек) \n"
            "<code>.биржа</code> - выводит стакан заявок биржи /n"
            "<code>.график</code> - вывод графика цен биржи"
            "<code>.хелп</code> - выводит меню помощи ириса \n"
            "<code>.итоп</code> - покажет топ дня по вложению коинов в чат \n"
            "<code>.ипинг</code> - покажет пинг всех ботов ирис \n"
            "<code>.ф</code> - просто пересылает результат фермы \n"
            "<code>.голд</code> - покажет топ хранителей голды \n"
            "<code>.кубик</code> - кинет рандом число типо кубика (НЕ ИРИС) \n"
            "<code>.ком</code> - скидывает ссылку на команды ириса \n"
            "<code>.оси</code> - выводит основные чата ириса \n"
     
        )
        await utils.answer(message, ihelp)
           