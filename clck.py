"""clckru module for hikka userbot
    Copyright (C) 2025 Ruslan Isaev
    
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see https://www.gnu.org/licenses/."""

version = (1, 0, 0)

# with the support of: @hikka_mods
# meta developer: @RUIS_VlP

import aiohttp
from .. import loader, utils

@loader.tds
class ClckMod(loader.Module):
    """Помогает сократить ссылку в clck.ru или расшифровать укороченную ссылку."""

    strings = {
        "name": "ClckRu",
    }
    
    async def short_url(self, url: str) -> str:
    	endpoint = 'https://clck.ru/--'
    	params = {'url': url}
    	async with aiohttp.ClientSession() as session:
    	       async with session.get(endpoint, params=params) as response:
    	       	return await response.text()
    	       	
    @loader.command()
    async def schortcmd(self, message):
        """<url> - сократит ссылку."""
        args = utils.get_args_raw(message)
        if not args:
        	await utils.answer(message, "❌ <b>Вы не указали ссылку для сокращения!</b>")
        	return
        url = args.split(" ")[0]
        slink = await self.short_url(url)
        await utils.answer(message, f"🔗 <b>Ваша ссылка:</b>\n<code>{slink}</code>")
    
    @loader.command()
    async def deschortcmd(self, message):
        """<url> - расшифрует ссылку."""
        args = utils.get_args_raw(message)
        if not args:
        	await utils.answer(message, "❌ <b>Вы не указали ссылку для расшифровки!</b>")
        	return
        url = args.split(" ")[0]
        async with aiohttp.ClientSession() as session:
        	async with session.get(url) as response:
        		final_url = str(response.url)
        if final_url.startswith("https://clck.ru/showcaptcha?"):
        	await utils.answer(message, "⛔️ <b>На</b> <code>clck.ru<code> <b>сработала капча! Попробуйте позже.</b>")
        else:
        	await utils.answer(message, f"🔗 <b>Ваша ссылка:</b>\n<code>{final_url}</code>")