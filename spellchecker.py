# meta developer: @RUIS_VlP
from .. import loader, utils
from telethon.tl.types import Message
import aiohttp

@loader.tds
class SpellCheckerMod(loader.Module):
    strings = {
        "name": "SpellChecker",
        "no_text": "❌ <b>Укажите текст для проверки или используйте реплай.</b>",
        "no_reply": "❌ <b>Это не реплай на сообщение.</b>",
        "api_error": "❌ <b>Ошибка при обращении к API Яндекс.Спеллера.</b>"
    }
    
    async def client_ready(self, client, db):
        self.db = db
        self._client = client
    
    async def spellcheckcmd(self, message: Message):
        """
        Проверить орфографию текста.
        
        Использование:
        .spellcheck [текст] - проверка указанного текста.
        .spellcheck -r - проверка текста из реплая.
        """
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()

        # Если используется флаг -r, проверяем текст из реплая
        if "-r" in args or "-r" in message.text:
            if not reply or not reply.text:
                return await utils.answer(message, self.strings["no_reply"])
            text_to_check = reply.text
        else:
            if not args:
                return await utils.answer(message, self.strings["no_text"])
            text_to_check = args

        corrected_text = await self.correct_text(text_to_check)
        await utils.answer(message, corrected_text)
    
    async def correct_text(self, text: str) -> str:
        """Исправление текста через API Яндекс.Спеллера"""
        url = "https://speller.yandex.net/services/spellservice.json/checkText"
        params = {
            "text": text,
            "lang": "ru",
            "options": 518
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=params) as response:
                    if response.status != 200:
                        return text
                    
                    data = await response.json()
                    if not data:
                        return text
                    
                    corrected_text = text
                    for error in reversed(data):
                        start = error["pos"]
                        end = start + error["len"]
                        corrected_text = corrected_text[:start] + error["s"][0] + corrected_text[end:]
                    
                    return corrected_text
        except Exception as e:
            print(f"Ошибка при обращении к API: {e}")
            return text