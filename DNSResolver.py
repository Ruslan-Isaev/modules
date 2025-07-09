__version__ = (1, 0, 0)

# meta developer: @RUIS_VlP
# requires: dnspython

import asyncio
import dns.asyncresolver
import dns.exception
from .. import loader, utils

RECORD_TYPES = ["A", "AAAA", "CNAME", "MX", "NS", "TXT"]

async def resolve_record(domain: str, dns_servers: list, record_type: str):
    resolver = dns.asyncresolver.Resolver()
    resolver.nameservers = dns_servers
    try:
        response = await resolver.resolve(domain, record_type)
        results = []
        for rdata in response:
            if record_type == "MX":
                results.append(str(rdata.exchange).rstrip('.'))
            elif record_type == "TXT":
                results.append(''.join(part.decode() for part in rdata.strings))
            else:
                results.append(str(rdata).rstrip('.'))
        return results
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers, dns.exception.Timeout):
        return []

async def resolve_all(domain: str, dns_servers: list):
    results = {}
    for record_type in RECORD_TYPES:
        records = await resolve_record(domain, dns_servers, record_type)
        if records:
            results[record_type] = records
    return results

def json2html(dns_data: dict) -> str:
    icons = {
        "A": "<emoji document_id=4967646650152519154>🌐</emoji>",
        "AAAA": "<emoji document_id=4967646650152519154>🌐</emoji>",
        "MX": "<emoji document_id=4967594608033792786>✉️</emoji>",
        "NS": "<emoji document_id=4967677110060581624>🗄</emoji>",
        "TXT": "<emoji document_id=4969849354195043059>📝</emoji>"
    }

    def section(title: str, items: list) -> str:
        icon = icons.get(title, "")
        if not items or items == ['']:
            return f"<b>{icon} {title}:</b> Нет записей\n"
        lines = '\n'.join(f"• <code>{item}</code>" for item in items)
        return f"<b>{icon} {title}:</b>\n{lines}\n"

    html_parts = [
        section("A", dns_data.get("A", [])),
        section("AAAA", dns_data.get("AAAA", [])),
        section("MX", dns_data.get("MX", [])),
        section("NS", dns_data.get("NS", [])),
        section("TXT", dns_data.get("TXT", [])),
    ]

    return '\n'.join(html_parts)
    
@loader.tds
class DNSResolverMod(loader.Module):
    """Модуль для отправки DNS запросов """

    strings = {
        "name": "DNSResolver",
    }
    
    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "DNS",
                ["8.8.8.8"],
                lambda: "DNS сервера",
                validator=loader.validators.Series(loader.validators.String()),
            )
            )

    @loader.command()
    async def resolvecmd(self, message):
        """<домен> - получает DNS записи указанного домена"""
        dns_servers = self.config["DNS"]
        if not dns_servers:
        	dns_servers = ["8.8.8.8"]
        dns_str = ',  '.join(f"<code>{item}</code>" for item in dns_servers)
        args = utils.get_args_raw(message)
        if not args:
        	await utils.answer(message, "<b>Укажите домен, например:</b> <code>.resolve example.com</code>")
        	return
        records = await resolve_all(args, dns_servers)
        records = json2html(records)
        answer = f"<b>DNS сервер:</b> {dns_str}\n<b>DNS записи</b> <code>{args}</code>:\n\n{records}"
        await utils.answer(message, answer)