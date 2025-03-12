# meta developer: @RUIS_VlP

import random
from telethon import functions
from telethon.tl.types import Message
from .. import loader, utils
import pyfiglet

@loader.tds
class FigletMod(loader.Module):
    """Длинные слова лучше переносить на другую строчку. Пример:
`.figlet Hello
World!`
Если написать в одну строчку, то слово не уместится в одно сообщение """

    strings = {
        "name": "Figlet",
    }

    def init(self):
        self.name = self.strings["name"]

    @loader.command()
    async def figlet(self, message: Message):
        """<text> - делает текст большим"""
        mtext = message.text[8:]
        ftext = pyfiglet.figlet_format(mtext)
        await utils.answer(message, f"<code>⁣{ftext}</code>")
