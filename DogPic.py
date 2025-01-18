version = (1, 0, 0)

# meta developer: @RUIS_VlP

import asyncio
from .. import loader, utils
import aiohttp
import asyncio

API_KEY = 'live_AQldtIr1OR2HIwnXKIONXtGRhEvVd0ZDKBthbAwlC3UgFbxwYFwsEDm4fCcWgSfP'
URL = 'https://api.thedogapi.com/v1/images/search'

async def get_image():
    headers = {'x-api-key': API_KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(URL, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                image_url = data[0]['url']
                return image_url, 0
            else:
                return response.status, 1
                    
@loader.tds
class DogPicMod(loader.Module):
    """Модуль для фотографий с милыми собачками"""

    strings = {
        "name": "DogPic",
    }
    
    
    @loader.command()
    async def dogpic(self, message):
        """картинка с собачкой"""
        await utils.answer(message, "🔎 <b>Ищу лучшую картинку</b>")
        try:
        	link, exitcode = await get_image()
        	if exitcode == 0:
        		await message.delete()
        		await utils.answer_file(message, link)
        	else:
        		await utils.answer(message, f"❌ <b>Ошибка!</b>\n\n<code>{link}</code>")
        except Exception as e:
        	await utils.answer(message, f"❌ <b>Ошибка!</b>\n\n<code>{e}</code>")