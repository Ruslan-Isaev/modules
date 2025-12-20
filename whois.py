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

__version__ = (3, 0, 1)

# meta developer: @RUIS_VlP
# при поддержке @hikka_mods

import json
import aiohttp
from .. import loader, utils
import asyncio
import re
from typing import List

async def clean_domain(value: str) -> str:
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
    
async def get_whois(identifier, API_KEY: str = None) -> dict:
    """Получение данных через RDAP для доменов и ipwho.is для IP"""
    check = await ipcheck(identifier)
    
    if check == "ip":
        url = f"http://ipwho.is/{identifier}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                response = await resp.json()
                return response
    else:
        # Основной RDAP сервис
        url_primary = f"https://rdap.org/domain/{identifier}"
        # Резервный RDAP сервис
        url_backup = f"https://rdap.active.domains/domain/{identifier}"
        
        # Заголовки для обхода блокировок
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/rdap+json, application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url_primary, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status in (404, 403, 429, 500, 502, 503):
                        # Если ошибка на основном, пробуем резервный
                        async with session.get(url_backup, headers=headers) as resp_backup:
                            resp_backup.raise_for_status()
                            response = await resp_backup.json()
                            return response
                    resp.raise_for_status()
                    response = await resp.json()
                    return response
            except aiohttp.ClientResponseError as e:
                # Любая HTTP ошибка - пробуем резервный
                async with session.get(url_backup, headers=headers) as resp_backup:
                    resp_backup.raise_for_status()
                    response = await resp_backup.json()
                    return response
            except (aiohttp.ClientError, asyncio.TimeoutError):
                # При ошибке соединения пробуем резервный
                async with session.get(url_backup, headers=headers) as resp_backup:
                    resp_backup.raise_for_status()
                    response = await resp_backup.json()
                    return response
            
async def fetch_dns_record(session, domain, record_type):
    url = "https://dns.google/resolve"
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

async def json2text_ip(data: dict) -> str:
    """Форматирование данных IP из ipwho.is"""
    def get(value):
        return str(value) if value not in (None, '', [], {}) else 'Неизвестно'
    
    if not data.get("success", False):
        return f"❌ <b>IP адрес не найден или недоступен</b>"
    
    ip = get(data.get("ip"))
    ip_type = get(data.get("type"))
    continent = get(data.get("continent"))
    country = get(data.get("country"))
    country_code = get(data.get("country_code"))
    region = get(data.get("region"))
    city = get(data.get("city"))
    postal = get(data.get("postal"))
    
    flag = data.get("flag", {})
    flag_emoji = flag.get("emoji", "🌍")
    
    connection = data.get("connection", {})
    asn = get(connection.get("asn"))
    org = get(connection.get("org"))
    isp = get(connection.get("isp"))
    domain = get(connection.get("domain"))
    
    timezone_data = data.get("timezone", {})
    timezone_id = get(timezone_data.get("id"))
    timezone_utc = get(timezone_data.get("utc"))
    
    lines = [
        f"<emoji document_id=5224450179368767019>🌎</emoji><b>IP адрес:</b> <code>{ip}</code>",
        f"<emoji document_id=4992466832364405778>🖥</emoji> <b>Тип:</b> <code>{ip_type}</code>",
        "",
        f"{flag_emoji} <b>Местоположение:</b>",
        f"   • Континент: <code>{continent}</code>",
        f"   • Страна: <code>{country} ({country_code})</code>",
        f"   • Регион: <code>{region}</code>",
        f"   • Город: <code>{city}</code>",
        f"   • Индекс: <code>{postal}</code>",
        "",
        f"<emoji document_id=5431376038628171216>🔗</emoji> <b>Подключение:</b>",
        f"   • ASN: <code>{asn}</code>",
        f"   • Организация: <code>{org}</code>",
        f"   • Провайдер: <code>{isp}</code>",
        f"   • Домен: <code>{domain}</code>",
        "",
        f"<emoji document_id=5431815452437257407>🕐</emoji> <b>Часовой пояс:</b>",
        f"   • Зона: <code>{timezone_id}</code>",
        f"   • UTC: <code>{timezone_utc}</code>",
    ]
    
    return '\n'.join(line for line in lines if '<code>Неизвестно</code>' not in line)
            
async def json2text(data: dict, ips, check) -> str:
    def get(value):
        return str(value) if value not in (None, '', [], {}) else 'Неизвестно'

    # Обработка RDAP формата
    ldhName = data.get("ldhName", data.get("handle", ""))
    
    # Проверка статуса регистрации
    status = data.get("status", [])
    if isinstance(status, list):
        status_str = ', '.join(status) if status else 'Неизвестно'
    else:
        status_str = get(status)
    
    # Проверка на свободный домен
    if not ldhName or "object not found" in str(data).lower():
        domain_name = data.get("ldhName", data.get("handle", "Неизвестно"))
        return f"<emoji document_id=5224450179368767019>🌎</emoji><b>Домен:</b> <code>{domain_name}</code>\n\n<emoji document_id=4985637404867036136>🖥</emoji> <b>Домен свободен</b>"
    
    # Извлечение событий (даты)
    events = data.get("events", [])
    created = next((e["eventDate"] for e in events if e.get("eventAction") == "registration"), None)
    changed = next((e["eventDate"] for e in events if e.get("eventAction") == "last changed"), None)
    expires = next((e["eventDate"] for e in events if e.get("eventAction") == "expiration"), None)
    
    # Извлечение nameservers
    nameservers_data = data.get("nameservers", [])
    nameservers = [ns.get("ldhName", "Неизвестно") for ns in nameservers_data] if nameservers_data else ['Неизвестно']
    
    # Извлечение контактов
    entities = data.get("entities", [])
    admin = {}
    registrar = {}
    
    for entity in entities:
        roles = entity.get("roles", [])
        if "administrative" in roles or "admin" in roles:
            vcard = entity.get("vcardArray", [[]])
            if len(vcard) > 1:
                for field in vcard[1]:
                    if field[0] == "fn":
                        admin["name"] = field[3]
                    elif field[0] == "email":
                        admin["email"] = field[3]
                    elif field[0] == "org":
                        admin["organization"] = field[3]
                    elif field[0] == "adr":
                        if len(field[3]) > 6:
                            admin["country"] = field[3][6]
        
        if "registrar" in roles:
            vcard = entity.get("vcardArray", [[]])
            registrar["name"] = entity.get("handle", "")
            if len(vcard) > 1:
                for field in vcard[1]:
                    if field[0] == "fn":
                        registrar["name"] = field[3]
                    elif field[0] == "email":
                        registrar["email"] = field[3]
                    elif field[0] == "tel":
                        registrar["phone"] = field[3]
    
    registered = 'Да' if ldhName else 'Нет'
    
    lines = [
        f"<emoji document_id=5224450179368767019>🌎</emoji><b>Домен:</b> <code>{ldhName}</code>",
    ]
    
    if len(ips) > 0 and (ips[0] or ips[1]):
        lines += ["<emoji document_id=4992466832364405778>🖥</emoji> <b>IP адреса:</b>"]
        lines += [f"  • <code>{ip}</code>" for ip in ips[0]]
        lines += [f"  • <code>{ip}</code>" for ip in ips[1]]
    
    lines += [
        "",
        f"<emoji document_id=5274055917766202507>🗓</emoji> <b>Дата регистрации:</b> <code>{get(created)}</code>",
        f"♻️ <b>Изменено:</b> <code>{get(changed)}</code>",
        f"<emoji document_id=5325583469344989152>⏳</emoji><b>Истекает:</b> <code>{get(expires)}</code>",
        f"<emoji document_id=5206607081334906820>✔️</emoji> <b>Зарегистрирован:</b> <code>{registered}</code>",
        f"<emoji document_id=5231200819986047254>📊</emoji> <b>Статус:</b> <code>{status_str}</code>",
        "",
    ]
    
    if check == "domain" and nameservers[0] != 'Неизвестно':
        lines += ["<emoji document_id=4985545282113503960>🖥</emoji> <b>DNS-серверы:</b>"]
        lines += [f"  • <code>{ns}</code>" for ns in nameservers]
    
    if admin:
        lines += [
            "",
            "<emoji document_id=5936110055404342764>👤</emoji> <b>Админ-контакт:</b>",
            f"   • Имя: <code>{get(admin.get('name'))}</code>",
            f"   • Email: <code>{get(admin.get('email'))}</code>",
            f"   • Организация: <code>{get(admin.get('organization'))}</code>",
            f"   • Страна: <code>{get(admin.get('country'))}</code>",
            "",
        ]
    
    if check == "domain" and registrar:
        lines += [
            "<emoji document_id=5445353829304387411>💳</emoji> <b>Регистратор:</b>",
            f"   • Название: <code>{get(registrar.get('name'))}</code>",
            f"   • Email: <code>{get(registrar.get('email'))}</code>",
            f"   • Телефон: <code>{get(registrar.get('phone'))}</code>",
        ]

    return '\n'.join(line for line in lines if '<code>Неизвестно</code>' not in line)

@loader.tds
class WhoisMod(loader.Module):
    """Модуль для получения информации о домене или ip адресе"""
    
    strings = {"name": "Whois"}

    @loader.command()
    async def whois(self, message):
        """<домен> - получить информацию о домене или IP"""
        domain = ((utils.get_args_raw(message)).split()[0]).encode('idna').decode('ascii')
        if not domain:
            await utils.answer(message, "❌ <b>Вы не указали домен!</b>")
            return
        await utils.answer(message, "📡 <i>Отправляю запрос...</i>")
        try:
            check = await ipcheck(domain)
            clean = await clean_domain(domain)
            
            if check == "ip":
                info = await get_whois(clean)
                text = await json2text_ip(info)
                await utils.answer(message, text)
                return
            
            whois = get_whois(clean)
            ips = get_ips(clean)
            info, ips = await asyncio.gather(whois, ips)
            text = await json2text(info, ips, "domain")
            await utils.answer(message, text)
        except Exception as e:
            if "404" in str(e):
            	await utils.answer(message, f"<emoji document_id=5224450179368767019>🌎</emoji><b>Домен:</b> <code>{clean}</code>\n\n<emoji document_id=4985637404867036136>🖥</emoji> <b>Домен свободен</b>")
            	return
            else:
            	await utils.answer(message, f"❌ <b>Ошибка!</b>\n\n<code>{e}</code>")