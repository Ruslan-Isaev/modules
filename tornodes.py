# meta developer: @matubuntu
import os
import re
import qrcode
import httpx
from .. import loader, utils

async def fetch_bridges(brigde, url):
    url = f"{url}?transport={brigde}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()
        return [item['bridge'] for item in data]

async def create_qr(data, filename="qrcode.png", version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4):
    qr = qrcode.QRCode(
        version=version,
        error_correction=error_correction,
        box_size=box_size,
        border=border,
    )
    qr.add_data(f"{str(data)}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)
    return None

@loader.tds
class TorNodes(loader.Module):
    """Получает список мостов для сети Tor"""

    strings = {"name": "TorNodes"}
    
    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "EnabledSubAPI",
                True,
                lambda: "Что то вроде Proxy, на случай блокировки torproject.org. Подробнее: https://github.com/Neotele-Studio/GetTorBridgesSubAPI",
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "LinkSubAPI",
                "https://ruishikka.serv00.net/tor.php",
                lambda: "Ссылка на ваш SubAPI",
                validator=loader.validators.String()
            )
        )
    
    @loader.command()
    async def bridge(self, message):
        """obfs4 / webtunnel - получить мосты для сети Tor"""
        transport_type = None
        if message.is_reply:
            reply_message = await message.get_reply_message()
            transport_type = reply_message.raw_text.lower().strip()  # Получаем транспорт из ответа
        else:
            args = utils.get_args_raw(message)
            if args:
                transport_type = args.lower().strip()  # Получаем транспорт из аргументов команды

        if transport_type == "obfs4":
            url = 'https://bridges.torproject.org/bridges?transport=obfs4'
            pattern = r'obfs4.*?cert=[a-zA-Z0-9+/]+={0,2}.*?iat-mode=\d+'
        elif transport_type == "webtunnel":
            url = 'https://bridges.torproject.org/bridges?transport=webtunnel'
            pattern = r'webtunnel \[.*?\]:\d+ \S+ url=\S+ ver=\d+\.\d+'  # Новое регулярное выражение
        else:
            await utils.answer(message, "Неправильный тип транспорта. Используйте 'obfs4' или 'webtunnel'.")
            return

        try:
            if self.config["EnabledSubAPI"] == False:
                async with httpx.AsyncClient() as client:
                  response = await client.get(url)
                  bridges = re.findall(pattern, response.text, flags=re.MULTILINE)
    
                if not bridges:
                    raise ValueError(f"Не найдено ни одной строки, содержащей '{transport_type}'.")
                    
                await create_qr(bridges)
                
                await utils.answer_file(message, "qrcode.png", caption=f"<code>{bridges[0]}\n{bridges[1]}</code>")
                
                os.remove("qrcode.png")
                
            else:
                bridges = await fetch_bridges(transport_type, self.config["LinkSubAPI"])
                if not bridges:
                    raise ValueError(f"Не найдено ни одной строки, содержащей '{transport_type}'.")
                    
                await create_qr(bridges)
                
                await utils.answer_file(message, "qrcode.png", caption=f"<code>{bridges[0]}\n{bridges[1]}</code>")
                
                os.remove("qrcode.png")
  
        except Exception as e:
            await utils.answer(message, f'Произошла ошибка при получении мостов: {e}')
            
    @loader.command()
    async def tncfg(self, message):
        """- открыть конфигурацию модуля"""
        name = self.strings("name")
        await self.allmodules.commands["config"](
            await utils.answer(message, f"{self.get_prefix()}config {name}")
        )