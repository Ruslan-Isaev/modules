__version__ = (1, 0, 0)

# meta developer: @RUIS_VlP

from .. import loader, utils
import aiohttp
from telethon.tl.types import InputGeoPoint, InputMediaGeoPoint
from urllib.parse import quote

async def get_coordinates(query: str):
    base_url = "https://nominatim.openstreetmap.org/search"
    encoded_query = quote(query)

    url = f"{base_url}?q={encoded_query}&format=json"
    headers = {
        "User-Agent": "Heroku-GeoMod/1.0 (https://t.me/RUIS_VlP)"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data:
                    lat = float(data[0]["lat"])
                    lon = float(data[0]["lon"])
                    return [lat, lon]
            return None
                    
@loader.tds
class GeoMod(loader.Module):
    """Модуль для отправки геолокации с указанным адресом или координатами"""

    strings = {
        "name": "GeoMod",
    }
    
    @loader.command()
    async def sendgeo(self, message):
        """<адрес> - отправить геолокацию с указанным адресом или координатами"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(
                message, 
                "<b>Укажите адрес, например:</b> <code>.sendgeo Москва, Манежная улица, 2</code>"
            )
            return 

        coords = await get_coordinates(args)
        if coords:
            await message.client.send_file(
                message.chat_id,
                InputMediaGeoPoint(
                    geo_point=InputGeoPoint(
                        lat=coords[0],
                        long=coords[1],
                    )
                )
            )
            await message.delete()
        else:
            await utils.answer(message, "<b>Координаты не найдены.</b>")