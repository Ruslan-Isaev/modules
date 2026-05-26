# meta developer: @matubuntu 

import time
from datetime import datetime
import aiohttp
from .. import loader, utils

_FLAGS = {
    "AUD": "🇦🇺", "AZN": "🇦🇿", "GBP": "🇬🇧", "AMD": "🇦🇲",
    "BYN": "🇧🇾", "BGN": "🇧🇬", "BRL": "🇧🇷", "HUF": "🇭🇺",
    "VND": "🇻🇳", "HKD": "🇭🇰", "GEL": "🇬🇪", "DKK": "🇩🇰",
    "AED": "🇦🇪", "USD": "🇺🇸", "EUR": "🇪🇺", "EGP": "🇪🇬",
    "INR": "🇮🇳", "IDR": "🇮🇩", "KZT": "🇰🇿", "CAD": "🇨🇦",
    "QAR": "🇶🇦", "KGS": "🇰🇬", "CNY": "🇨🇳", "MDL": "🇲🇩",
    "NZD": "🇳🇿", "NOK": "🇳🇴", "PLN": "🇵🇱", "RON": "🇷🇴",
    "SGD": "🇸🇬", "TJS": "🇹🇯", "THB": "🇹🇭", "TRY": "🇹🇷",
    "TMT": "🇹🇲", "UZS": "🇺🇿", "UAH": "🇺🇦", "CZK": "🇨🇿",
    "SEK": "🇸🇪", "CHF": "🇨🇭", "RSD": "🇷🇸", "ZAR": "🇿🇦",
    "KRW": "🇰🇷", "JPY": "🇯🇵",
}

_CRYPTO_EMOJIS = {
    "BTC":   "<emoji document_id=5289519973285257969>💰</emoji>",
    "ETH":   "<emoji document_id=5287735049301550386>💰</emoji>",
    "SOL":   "<emoji document_id=5251712673258697260>💰</emoji>",
    "TON":   "<emoji document_id=5289648693455119919>💰</emoji>",
    "USDT":  "<emoji document_id=5289904548951911168>💰</emoji>",
    "XRP":   "<emoji document_id=5373312921214401986>💰</emoji>",
    "USDC":  "<emoji document_id=5372958453268497353>💰</emoji>",
    "ADA":   "<emoji document_id=5373076801092338046>💰</emoji>",
    "DOGE":  "<emoji document_id=5375192042420842380>💰</emoji>",
    "TRX":   "<emoji document_id=5375187081733616165>💰</emoji>",
    "AVAX":  "<emoji document_id=5375311275007947936>💰</emoji>",
    "LTC":   "<emoji document_id=5373035462032113888>💰</emoji>",
    "BCH":   "<emoji document_id=5375596920397903962>💰</emoji>",
    "ATOM":  "<emoji document_id=5375468745688889977>💰</emoji>",
    "XLM":   "<emoji document_id=5372823290647690288>💰</emoji>",
    "SHIB":  "<emoji document_id=5375231036428924778>💰</emoji>",
    "UNI":   "<emoji document_id=5372953110329180525>💰</emoji>",
    "XMR":   "<emoji document_id=5375507073977038661>💰</emoji>",
    "LINK":  "<emoji document_id=5375149651093633217>💰</emoji>",
    "ETC":   "<emoji document_id=5375543306321146693>💰</emoji>",
    "SUI":   "<emoji document_id=5391002164929772708>💰</emoji>",
    "NEAR":  "<emoji document_id=5391181990915487346>💰</emoji>",
    "VET":   "<emoji document_id=5391091302681033446>💰</emoji>",
    "FIL":   "<emoji document_id=5373117173784919811>💰</emoji>",
    "XTZ":   "<emoji document_id=5390985478981829698>💰</emoji>",
    "ALGO":  "<emoji document_id=5391337713544738420>💰</emoji>",
    "THETA": "<emoji document_id=5391256014676833736>💰</emoji>",
    "FTM":   "<emoji document_id=5393179395521263785>💰</emoji>",
    "XDAI":  "<emoji document_id=5391325992578988886>💰</emoji>",
    "RUNE":  "<emoji document_id=5391347570494684983>💰</emoji>",
    "DOT":   "<emoji document_id=5375224568208177973>💰</emoji>",
}

_CRYPTO_NAMES = {
    "BTC": "Bitcoin",      "ETH": "Ethereum",      "XMR": "Monero",
    "LTC": "Litecoin",     "XRP": "XRP",            "ADA": "Cardano",
    "DOGE": "Dogecoin",    "SOL": "Solana",          "DOT": "Polkadot",
    "USDT": "Tether",      "TON": "Toncoin",         "USDC": "USD Coin",
    "TRX": "TRON",         "AVAX": "Avalanche",      "BCH": "Bitcoin Cash",
    "ATOM": "Cosmos",      "XLM": "Stellar",         "SHIB": "Shiba Inu",
    "UNI": "Uniswap",      "LINK": "Chainlink",      "ETC": "Ethereum Classic",
    "SUI": "Sui",          "NEAR": "NEAR Protocol",  "VET": "VeChain",
    "FIL": "Filecoin",     "XTZ": "Tezos",           "ALGO": "Algorand",
    "THETA": "Theta Network", "FTM": "Fantom",        "XDAI": "xDai",
    "RUNE": "THORChain",
}

_CBR_URL    = "https://www.cbr.ru/scripts/XML_daily.asp"
_CRYPTO_URL = "https://api.coinlore.net/api/tickers/?limit=100"

CACHE_TTL = 300  # seconds


def _fmt_num(value: float, decimals: int = 3) -> str:
    if decimals == 0:
        return f"{int(value):,}".replace(",", " ")
    rounded = round(value, decimals)
    int_part = int(rounded)
    dec_part = str(rounded - int_part)[2:2 + decimals].rstrip("0")
    int_str = f"{int_part:,}".replace(",", " ")
    return f"{int_str},{dec_part}" if dec_part else int_str


def _parse_cbr_xml(xml_bytes: bytes) -> tuple[str | None, dict]:
    """Parse CBR XML without bs4/lxml — pure stdlib ElementTree."""
    import xml.etree.ElementTree as ET

    root = ET.fromstring(xml_bytes)
    date_str = root.attrib.get("Date", "")
    try:
        date = datetime.strptime(date_str, "%d.%m.%Y").strftime("%d.%m.%Y")
    except ValueError:
        date = date_str

    rates: dict[str, dict] = {}
    for valute in root.findall("Valute"):
        code = valute.findtext("CharCode", "").strip()
        if not code or code == "XDR":
            continue
        try:
            nominal = float(valute.findtext("Nominal", "1").replace(",", "."))
            value   = float(valute.findtext("Value",   "0").replace(",", "."))
        except ValueError:
            continue
        rates[code] = {
            "name":    valute.findtext("Name", code).strip(),
            "nominal": nominal,
            "rub":     value / nominal,
        }
    return date, rates


@loader.tds
class FinanceMod(loader.Module):
    """Курсы валют (ЦБ РФ) и криптовалют (CoinLore)"""

    strings = {"name": "FinanceMod"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "crypto_currency",
                "USD",
                lambda: "Валюта для отображения крипты (USD, RUB, EUR)",
                validator=loader.validators.Choice(["USD", "RUB", "EUR"]),
            )
        )
        # Simple in-process cache
        self._cbr_cache:    tuple[float, str, dict] | None = None  # (ts, date, rates)
        self._crypto_cache: tuple[float, list] | None = None        # (ts, data)

    # ──────────────────────────── HTTP helpers ────────────────────────────

    async def _fetch(self, url: str, *, as_json: bool = False):
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                resp.raise_for_status()
                return await resp.json() if as_json else await resp.read()

    # ──────────────────────────── CBR data ────────────────────────────────

    async def _cbr_data(self) -> tuple[str | None, dict]:
        now = time.monotonic()
        if self._cbr_cache and now - self._cbr_cache[0] < CACHE_TTL:
            return self._cbr_cache[1], self._cbr_cache[2]
        try:
            raw = await self._fetch(_CBR_URL)
            date, rates = _parse_cbr_xml(raw)
            self._cbr_cache = (now, date, rates)
            return date, rates
        except Exception:
            if self._cbr_cache:
                return self._cbr_cache[1], self._cbr_cache[2]
            return None, {}

    # ──────────────────────────── Crypto data ─────────────────────────────

    async def _crypto_data(self) -> list:
        now = time.monotonic()
        if self._crypto_cache and now - self._crypto_cache[0] < CACHE_TTL:
            return self._crypto_cache[1]
        try:
            js = await self._fetch(_CRYPTO_URL, as_json=True)
            data = js.get("data", [])
            self._crypto_cache = (now, data)
            return data
        except Exception:
            return self._crypto_cache[1] if self._crypto_cache else []

    # ──────────────────────────── Formatters ──────────────────────────────

    def _fmt_valute(self, code: str, info: dict, amount: float = 1.0) -> str:
        total = info["rub"] * amount
        flag  = _FLAGS.get(code, "🏳")
        return f"{flag} [{_fmt_num(amount, 0)}] {info['name']} ({code}) — {_fmt_num(total, 3)} ₽"

    def _fmt_crypto(self, coin: dict, rates: dict, amount: float = 1.0) -> str:
        symbol = coin["symbol"].upper()
        try:
            price_usd = float(coin["price_usd"])
        except (KeyError, ValueError, TypeError):
            return ""

        currency = self.config["crypto_currency"]
        if currency == "RUB":
            usd_rate = rates.get("USD", {}).get("rub")
            if not usd_rate:
                return ""
            price = price_usd * usd_rate
            sign  = "₽"
        elif currency == "EUR":
            usd_rate = rates.get("USD", {}).get("rub")
            eur_rate = rates.get("EUR", {}).get("rub")
            if not usd_rate or not eur_rate:
                return ""
            price = price_usd * (usd_rate / eur_rate)
            sign  = "€"
        else:
            price = price_usd
            sign  = "$"

        total  = price * amount
        emoji  = _CRYPTO_EMOJIS.get(symbol, "💠")
        name   = _CRYPTO_NAMES.get(symbol, coin.get("name", symbol))
        return f"{emoji} [{_fmt_num(amount, 0)}] {name} ({symbol}) — {_fmt_num(total, 3)}{sign}"

    # ──────────────────────────── Commands ────────────────────────────────

    @loader.command(ru_doc="[кол-во] [код] — курс валюты по ЦБ РФ")
    async def valutecmd(self, message):
        """[amount] [code] — exchange rates from CBR"""
        args = utils.get_args(message)
        date, rates = await self._cbr_data()

        if not rates:
            return await utils.answer(message, "🚫 Не удалось получить данные ЦБ РФ")

        header = (
            f"💵 <b>Курс валюты</b> · <a href='https://www.cbr.ru/'>ЦБ РФ</a>\n"
            f"<b>Актуально на</b> <i>{date}</i>\n\n"
        )

        # .valute  — список всех, кол-во = 1
        if not args:
            lines = [self._fmt_valute(c, i) for c, i in rates.items()]
            return await utils.answer(
                message,
                header + f"<blockquote expandable>{chr(10).join(lines)}</blockquote>",
            )

        # Первый аргумент: число или код валюты?
        amount = 1.0
        code   = None
        arg0   = args[0].upper()

        if len(args) >= 2:
            # .valute 100 USD
            try:
                amount = float(args[0].replace(",", "."))
            except ValueError:
                return await utils.answer(message, "🚫 Некорректное число")
            code = args[1].upper()
        else:
            # .valute USD  или  .valute 100
            try:
                amount = float(arg0.replace(",", "."))
                # число без кода — список с умножением
            except ValueError:
                code = arg0

        if code:
            if code not in rates:
                return await utils.answer(message, f"🚫 Валюта <b>{code}</b> не найдена")
            line = self._fmt_valute(code, rates[code], amount)
            return await utils.answer(message, header + line)

        # список с кол-вом
        lines = [self._fmt_valute(c, i, amount) for c, i in rates.items()]
        await utils.answer(
            message,
            header + f"<blockquote expandable>{chr(10).join(lines)}</blockquote>",
        )

    @loader.command(ru_doc="[кол-во] [код] — курс крипты")
    async def cryptocmd(self, message):
        """[amount] [symbol] — crypto rates from CoinLore"""
        args        = utils.get_args(message)
        coins       = await self._crypto_data()
        _, rates    = await self._cbr_data()

        if not coins:
            return await utils.answer(message, "🚫 Не удалось получить данные крипты")

        header = f"💎 <b>Курсы криптовалют</b> · <i>{self.config['crypto_currency']}</i>\n\n"

        amount = 1.0
        symbol = None

        if not args:
            pass  # список, amount=1
        elif len(args) == 1:
            try:
                amount = float(args[0].replace(",", "."))
            except ValueError:
                symbol = args[0].upper()
        else:
            try:
                amount = float(args[0].replace(",", "."))
            except ValueError:
                return await utils.answer(message, "🚫 Некорректное число")
            symbol = args[1].upper()

        if symbol:
            coin = next((c for c in coins if c["symbol"].upper() == symbol), None)
            if not coin:
                return await utils.answer(message, f"🚫 Крипта <b>{symbol}</b> не найдена")
            line = self._fmt_crypto(coin, rates, amount)
            if not line:
                return await utils.answer(message, "🚫 Ошибка форматирования")
            return await utils.answer(message, header + line)

        # список только известных монет
        known = {c["symbol"].upper(): c for c in coins if c["symbol"].upper() in _CRYPTO_NAMES}
        # сортируем по порядку _CRYPTO_NAMES
        lines = []
        for sym in _CRYPTO_NAMES:
            if sym in known:
                line = self._fmt_crypto(known[sym], rates, amount)
                if line:
                    lines.append(line)

        await utils.answer(
            message,
            header + f"<blockquote expandable>{chr(10).join(lines)}</blockquote>",
        )
