import requests
import json
from urllib.parse import quote
from .. import loader, utils  

# meta developer: @matubuntu
@loader.tds
class CheckModulesMod(loader.Module):
    """Модуль для проверки модулей"""

    strings = {
        "name": "Check module",
        "answer": (
            "<pre>Found:  ❌️ {0} |  ⚠️ {1} |  ✅ {2}\n\n"
            "🔍 Module check completed:\n\n"
            "❌️ Criticals ({3}):\n{4}\n\n"
            "⚠️ Warnings ({5}):\n{6}\n\n"
            "🔰 Advices ({7}):\n{8}</pre>"
        ),
        "error": "Error!\n\n.checkmod <module_link> or reply to a file",
    }

    strings_ru = {
        "answer": (
            "<pre>Найдено:  ❌️ {0} |  ⚠️ {1} |  ✅ {2}\n\n"
            "🔍 Проверка модуля завершена:\n\n"
            "❌️ Критические ({3}):\n{4}\n\n"
            "⚠️ Предупреждения ({5}):\n{6}\n\n"
            "🔰 Советы ({7}):\n{8}</pre>"
        ),
        "error": "Ошибка!\n\n.checkmod <ссылка_на_модуль> или ответ на файл",
    }

    async def client_ready(self, client, db):
        self.client = client
        self.db = db

    async def send_request(self, url, code=None):
        try:
            if code:
                response = requests.post(url, json={"code": code})
            else:
                response = requests.get(url)
            response.raise_for_status()  # Проверяем, нет ли ошибок в запросе
            return json.loads(response.text)
        except Exception as e:
            return {"error": str(e)}

    async def format_response(self, response):
        if "error" in response:
            return f"<b>Error:</b> {response['error']}"

        critical = "\n".join([f"  {item}" for item in response.get("critical_details", [])]) or " ▪️ ➖"
        warn = "\n".join([f"  {item}" for item in response.get("warn_details", [])]) or " ▪️ ➖"
        council = "\n".join([f"  {item}" for item in response.get("council_details", [])]) or " ▪️ ➖"

        return self.strings["answer"].format(
            response.get("critical_count", 0),
            response.get("warn_count", 0),
            response.get("council_count", 0),
            response.get("critical_count", 0),
            critical,
            response.get("warn_count", 0),
            warn,
            response.get("council_count", 0),
            council
        )

    @loader.unrestricted
    @loader.ratelimit
    async def checkmodcmd(self, message):
        """
        <url/reply file> - проверяет модули
        """
        args = utils.get_args_raw(message)
        if args:
            url = f"http://ruisblyat.serv00.net/checkmod.php?url={quote(args)}"
            response = await self.send_request(url)
            await utils.answer(message, await self.format_response(response))
            return

        try:
            code_from_message = (await self._client.download_file(message.media, bytes)).decode("utf-8")
        except Exception:
            code_from_message = ""

        try:
            reply = await message.get_reply_message()
            code_from_reply = (await self._client.download_file(reply.media, bytes)).decode("utf-8")
        except Exception:
            code_from_reply = ""

        code = code_from_message or code_from_reply
        if code:
            url = "http://ruisblyat.serv00.net/checkmod.php"
            response = await self.send_request(url, code)
            await utils.answer(message, await self.format_response(response))
        else:
            await utils.answer(message, self.strings["error"])
