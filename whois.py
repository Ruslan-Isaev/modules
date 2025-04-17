"""whois module for hikka userbot
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

# meta developer: @RUIS_VlP
# при поддержке @hikka_mods

import json
import aiohttp
from .. import loader, utils

async def get_whois(identifier: str, API_KEY: str) -> dict:
    url = "https://api.jsonwhoisapi.com/v1/whois"
    headers = {
        "Authorization": API_KEY
    }
    params = {
        "identifier": identifier
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as resp:
            resp.raise_for_status()
            return await resp.json()
            
async def json2text(data: dict) -> str:
    def get(value):
        return str(value) if value not in (None, '', [], {}) else 'None'

    lines = [
        f"🌐 Домен: {get(data.get('name'))}",
        f"🗓️ Дата регистрации: {get(data.get('created'))}",
        f"♻️ Изменено: {get(data.get('changed'))}",
        f"⌛ Истекает: {get(data.get('expires'))}",
        f"✅ Зарегистрирован: {'Да' if data.get('registered') else 'Нет'}",
        f"📶 Статус: {', '.join(data['status']) if isinstance(data['status'], list) else get(data.get('status'))}",
        f"🧭 DNS-серверы:\n" + '\n'.join(f"  • {ns}" for ns in data.get('nameservers', []) or ['None']),
        "",
        "👤 Админ-контакт:",
    ]

    admin = (data.get("contacts", {}).get("admin") or [{}])[0]
    lines += [
        f"   • Имя: {get(admin.get('name'))}",
        f"   • Email: {get(admin.get('email'))}",
        f"   • Организация: {get(admin.get('organization'))}",
        f"   • Страна: {get(admin.get('country'))}",
    ]

    registrar = data.get("registrar", {})
    lines += [
        "",
        "🏢 Регистратор:",
        f"   • ID: {get(registrar.get('id'))}",
        f"   • Название: {get(registrar.get('name'))}",
        f"   • Email: {get(registrar.get('email'))}",
        f"   • Сайт: {get(registrar.get('url'))}",
        f"   • Телефон: {get(registrar.get('phone'))}",
    ]

    return '\n'.join(lines)

@loader.tds
class WhoisMod(loader.Module):
    """Модуль для получения информации о домене или ip адресе"""
    
    strings = {"name": "Whois"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "api_key",
                "None",
                lambda: "API ключ с сайта https://jsonwhoisapi.com/",
                validator=loader.validators.String(),
            ),
        )

    @loader.command()
    async def whois(self, message):
        """<домен> - получить информацию о домене или IP"""
        api_key = self.config["api_key"] or "None"
        if api_key == "None":
            await utils.answer(message, '❌ <b>Не указан API ключ! Получите его на</b> jsonwhoisapi.com <b>и вставьте в config</b> <b>(</b><code>.config Whois</code><b>).</b>')
            return
        args = utils.get_args_raw(message)
        if not args:
        	await utils.answer(message, "❌ <b>Вы не указали домен или IP!</b>")
        	return
        try:
        	info = await get_whois(args.split(" ")[0], api_key)
        	text = await json2text(info)
        	await utils.answer(message, text)
        except Exception as e:
        	await utils.answer(message, f"❌ <b>Ошибка!</b>\n\n<code>{e}</code>")