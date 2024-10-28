version = (2, 2, 8)

# meta developer: @RUIS_VlP

import random
from datetime import datetime, timedelta
from telethon import functions
from telethon.tl.types import Message

from .. import loader, utils


@loader.tds
class IrisAutoFarm(loader.Module):
    """Автофарм в ирисе"""

    strings = {
        "name": "IrisAutoFarm",
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
    async def блэкстарт(self, message):
        """Завести таймеры в Iris Black Diamond"""
        await utils.answer(message, "Начинаю установку таймеров...")
        for i in range(100):
        	timee = datetime.now()
        	hours_to_add = 4.1 * (i + 1)
        	schedule_time = timee + timedelta(hours=hours_to_add, minutes=5)
        	await self.client.send_message('@iris_black_bot', "Ферма", schedule=schedule_time)
        await utils.answer(message, "Таймеры успешно установлены!")
        
       
        
        