# meta developer: @RUIS_VlP, @matubuntu
import os
from telethon import TelegramClient, events, sync, utils

from .. import loader, utils

@loader.tds
class TTFMod(loader.Module):
    """Создает текстовый файл, отправляет его в Telegram, а затем удаляет."""

    strings = {
        "name": "TTF",
    }

    def init(self):
        self.name = self.strings["name"]

    @loader.command()
    async def ttf(self, message):
        """
        Создает текстовый файл с заданным именем и расширением, 
        записывает в него текст, отправляет его в Telegram и удаляет с диска.

        Пример:
        .ttf название.txt
        Текст для файла/<reply>
        """
        args = utils.get_args_raw(message).split("\n")
        if len(args) < 1:
            await message.edit("Недостаточно аргументов. Используйте: .ttf название.txt\nТекст для файла")
            return

        filename = args[0].strip()
        reply = await message.get_reply_message()
        if reply:
        	txt = reply.raw_text
        	if txt:
        		text = txt
        else:
        	text = "\n".join(args[1:])

        # Создание файла
        file_path = os.path.join(os.getcwd(), filename)
        with open(file_path, 'w') as file:
            file.write(text)
        await message.client.delete_messages(message.chat_id, message.id)
        # Отправка файла
        await message.client.send_file(message.chat_id, file_path)

        # Удаление файла
        os.remove(file_path)
    