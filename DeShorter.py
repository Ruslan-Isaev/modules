version = (1, 0, 0)

# meta developer: @RUIS_VlP
import aiohttp
from .. import loader, utils

@loader.tds
class DeShorterMod(loader.Module):
    """Помогает расшифовать сокращенную ссылку\n\nМодуль не поддерживает ссылки от vk.cc\n\nВсе остальное (bit.ly, clck.ru и тд) поддерживается."""

    strings = {
        "name": "DeShorter",
    }

    @loader.command()
    async def deschortcmd(self, message):
        """<url> - расшифрует ссылку."""
        args = utils.get_args_raw(message)
        if not args:
        	await utils.answer(message, "❌ <b>Вы не указали ссылку!</b>")
        	return
        url = args.split(" ")[0]
        async with aiohttp.ClientSession() as session:
        	async with session.get(url) as response:
        		final_url = str(response.url)
        if final_url.startswith("https://clck.ru/showcaptcha?"):
        	await utils.answer(message, "⛔️ <b>На</b> <code>clck.ru<code> <b>сработала капча! Попробуйте позже.</b>")
        else:
        	await utils.answer(message, f"🔗 <b>Ваша ссылка:</b>\n<code>{final_url}</code>")