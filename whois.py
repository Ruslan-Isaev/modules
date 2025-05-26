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

__version__ = (2, 0, 0)

# meta developer: @RUIS_VlP
# при поддержке @hikka_mods

import json
import aiohttp
from .. import loader, utils
import asyncio
import re
from typing import List

async def clean_domain(value: str) -> List[str]:
    # Убираем протокол, порт, путь
    value = re.sub(r'^(https?://)?', '', value)
    value = value.split('/')[0]
    value = value.split(':')[0]

    return value

async def ipcheck(value: str) -> str:
    # Проверка IPv4 
    parts = value.split('.')
    if len(parts) == 4 and all(part.isdigit() and 0 <= int(part) <= 255 for part in parts):
        return "ip"
    
    # Проверка IPv6 
    ipv6_pattern = re.compile(r'^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}$')
    if ipv6_pattern.match(value):
        return "ip"
    
    return "domain"
    
async def get_whois(identifier, API_KEY: str) -> dict:
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
            response = await resp.json()
            return response
            
async def fetch_dns_record(session, domain, record_type):
    url = "https://unfiltered.adguard-dns.com/resolve"
    headers = {"accept": "application/dns-json"}
    params = {"name": domain, "type": record_type}

    async with session.get(url, headers=headers, params=params) as resp:
        text = await resp.text()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return []

        if not isinstance(data, dict):
            return []

        answers = data.get("Answer")
        if not answers:
            return []

        return [
            ans["data"]
            for ans in answers
            if ans.get("type") == (1 if record_type == "A" else 28)
        ]

async def get_ips(domain):
    async with aiohttp.ClientSession() as session:
        ipv4_task = fetch_dns_record(session, domain, "A")
        ipv6_task = fetch_dns_record(session, domain, "AAAA")
        ipv4, ipv6 = await asyncio.gather(ipv4_task, ipv6_task)
        return [ipv4, ipv6]
            
async def json2text(data: dict, ips, check) -> str:
    def get(value):
        return str(value) if value not in (None, '', [], {}) else 'Неизвестно'

    status = data.get("status", [])
    status_str = ', '.join(status) if isinstance(status, list) else get(status)
    
    nameservers = data.get("nameservers", []) or ['Неизвестнo']
    registered = 'Да' if data.get('registered') else 'Нет'
    if registered == "Нет":
            return f"<emoji document_id=5224450179368767019>🌎</emoji><b>Домен:</b> <code>{(get(data.get('name'))).encode('ascii').decode('idna')}</code>\n\n<emoji document_id=4985637404867036136>🖥</emoji> <b>Домен свободен</b>"
    
    admin = (data.get("contacts", {}).get("admin") or [{}])[0]
    registrar = data.get("registrar", {})

    lines = [
        f"<emoji document_id=5224450179368767019>🌎</emoji><b>Домен:</b> <code>{(get(data.get('name'))).encode('ascii').decode('idna')}</code>",]
    if len(ips) > 0:
        lines += ["<emoji document_id=4992466832364405778>🖥</emoji> <b>IP адреса:</b>"]
        lines += [f"  • <code>{ip}</code>" for ip in ips[0]]
        lines += [f"  • <code>{ip}</code>" for ip in ips[1]]
    else:
    	pass
    
    lines += [
        "",
        f"<emoji document_id=5274055917766202507>🗓</emoji> <b>Дата регистрации:</b> <code>{get(data.get('created'))}</code>",
        f"♻️ <b>Изменено:</b> <code>{get(data.get('changed'))}</code>",
        f"<emoji document_id=5325583469344989152>⏳</emoji><b>Истекает:</b> <code>{get(data.get('expires'))}</code>",
        f"<emoji document_id=5206607081334906820>✔️</emoji> <b>Зарегистрирован:</b> <code>{registered}</code>",
        f"<emoji document_id=5231200819986047254>📊</emoji> <b>Статус:</b> <code>{status_str}</code>",
        "",]
        
    if check == "domain":
        lines += [
        f"<emoji document_id=4985545282113503960>🖥</emoji> <b>DNS-серверы:</b>",
    ]
        lines += [f"  • <code>{ns}</code>" for ns in nameservers]
    
    lines += [
        "",
        "<emoji document_id=5936110055404342764>👤</emoji> <b>Админ-контакт:</b>",
        f"   • Имя: <code>{get(admin.get('name'))}</code>",
        f"   • Email: <code>{get(admin.get('email'))}</code>",
        f"   • Организация: <code>{get(admin.get('organization'))}</code>",
        f"   • Страна: <code>{get(admin.get('country'))}</code>",
        "",]
        
    if check == "domain":
        lines += [
        "<emoji document_id=5445353829304387411>💳</emoji> <b>Регистратор:</b>",
        f"   • ID: <code>{get(registrar.get('id'))}</code>",
        f"   • Название: <code>{get(registrar.get('name'))}</code>",
        f"   • Email: <code>{get(registrar.get('email'))}</code>",
        f"   • Сайт: <code>{get(registrar.get('url'))}</code>",
        f"   • Телефон: <code>{get(registrar.get('phone'))}</code>",
    ]

    return '\n'.join(line for line in lines if '<code>Неизвестно</code>' not in line)

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
        api_key = self.config["api_key"]
        if api_key == "None":
            await utils.answer(message, '❌ <b>Не указан API ключ! Получите его на</b> jsonwhoisapi.com <b>и вставьте в config</b> (<code>.config Whois</code>)')
            return
            
        domain = ((utils.get_args_raw(message)).split()[0]).encode('idna').decode('ascii')
        if not domain:
            await utils.answer(message, "❌ <b>Вы не указали домен!</b>")
            return
            
        try:
            check = await ipcheck(domain)
            clean = await clean_domain(domain)
            if check == "ip":
            	info = await get_whois(clean, api_key)
            	text = await json2text(info, [], "ip")
            	await utils.answer(message, text)
            	return
            whois = get_whois(clean, api_key)
            ips = get_ips(clean)
            info, ips = await asyncio.gather(whois, ips)
            text = await json2text(info, ips, "domain")
            await utils.answer(message, text)
        except Exception as e:
            await utils.answer(message, f"❌ <b>Ошибка!</b>\n\n<code>{e}</code>")