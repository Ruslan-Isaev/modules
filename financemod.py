#meta developer: @matubuntu
import requests, bs4
from datetime import datetime
from .. import loader, utils
import lxml

# requires: lxml requests bs4

_FLAGS = {
    "AUD": "🇦🇺",
    "AZN": "🇦🇿",
    "GBP": "🇬🇧",
    "AMD": "🇦🇲",
    "BYN": "🇧🇾",
    "BGN": "🇧🇬",
    "BRL": "🇧🇷",
    "HUF": "🇭🇺",
    "VND": "🇻🇳",
    "HKD": "🇭🇰",
    "GEL": "🇬🇪",
    "DKK": "🇩🇰",
    "AED": "🇦🇪",
    "USD": "🇺🇸",
    "EUR": "🇪🇺",
    "EGP": "🇪🇬",
    "INR": "🇮🇳",
    "IDR": "🇮🇩",
    "KZT": "🇰🇿",
    "CAD": "🇨🇦",
    "QAR": "🇶🇦",
    "KGS": "🇰🇬",
    "CNY": "🇨🇳",
    "MDL": "🇲🇩",
    "NZD": "🇳🇿",
    "NOK": "🇳🇴",
    "PLN": "🇵🇱",
    "RON": "🇷🇴",
    "SGD": "🇸🇬",
    "TJS": "🇹🇯",
    "THB": "🇹🇭",
    "TRY": "🇹🇷",
    "TMT": "🇹🇲",
    "UZS": "🇺🇿",
    "UAH": "🇺🇦",
    "CZK": "🇨🇿",
    "SEK": "🇸🇪",
    "CHF": "🇨🇭",
    "RSD": "🇷🇸",
    "ZAR": "🇿🇦",
    "KRW": "🇰🇷",
    "JPY": "🇯🇵",
}

_CRYPTO_EMOJIS = {
    "BTC": "<emoji document_id=5289519973285257969>💰</emoji>",
    "ETH": "<emoji document_id=5287735049301550386>💰</emoji>",
    "SOL": "<emoji document_id=5251712673258697260>💰</emoji>",
    "TON": "<emoji document_id=5289648693455119919>💰</emoji>",
    "USDT": "<emoji document_id=5289904548951911168>💰</emoji>",
    "XRP": "<emoji document_id=5373312921214401986>💰</emoji>",
    "USDC": "<emoji document_id=5372958453268497353>💰</emoji>",
    "ADA": "<emoji document_id=5373076801092338046>💰</emoji>",
    "DOGE": "<emoji document_id=5375192042420842380>💰</emoji>",
    "TRX": "<emoji document_id=5375187081733616165>💰</emoji>",
    "AVAX": "<emoji document_id=5375311275007947936>💰</emoji>",
    "LTC": "<emoji document_id=5373035462032113888>💰</emoji>",
    "BCH": "<emoji document_id=5375596920397903962>💰</emoji>",
    "ATOM": "<emoji document_id=5375468745688889977>💰</emoji>",
    "XLM": "<emoji document_id=5372823290647690288>💰</emoji>",
    "SHIB": "<emoji document_id=5375231036428924778>💰</emoji>",
    "UNI": "<emoji document_id=5372953110329180525>💰</emoji>",
    "XMR": "<emoji document_id=5375507073977038661>💰</emoji>",
    "LINK": "<emoji document_id=5375149651093633217>💰</emoji>",
    "ETC": "<emoji document_id=5375543306321146693>💰</emoji>",
    "SUI": "<emoji document_id=5391002164929772708>💰</emoji>",
    "NEAR": "<emoji document_id=5391181990915487346>💰</emoji>",
    "VET": "<emoji document_id=5391091302681033446>💰</emoji>",
    "FIL": "<emoji document_id=5373117173784919811>💰</emoji>",
    "XTZ": "<emoji document_id=5390985478981829698>💰</emoji>",
    "ALGO": "<emoji document_id=5391337713544738420>💰</emoji>",
    "THETA": "<emoji document_id=5391256014676833736>💰</emoji>",
    "FTM": "<emoji document_id=5393179395521263785>💰</emoji>",
    "XDAI": "<emoji document_id=5391325992578988886>💰</emoji>",
    "RUNE": "<emoji document_id=5391347570494684983>💰</emoji>",
    "DOT": "<emoji document_id=5375224568208177973>💰</emoji>",
}

_CRYPTO_LIST = {
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    "XMR": "Monero",
    "LTC": "Litecoin",
    "XRP": "XRP",
    "ADA": "Cardano",
    "DOGE": "Dogecoin",
    "SOL": "Solana",
    "DOT": "Polkadot",
    "USDT": "Tether",
    "TON": "Toncoin",
    "USDC": "USD Coin",
    "TRX": "TRON",
    "AVAX": "Avalanche",
    "BCH": "Bitcoin Cash",
    "ATOM": "Cosmos",
    "XLM": "Stellar",
    "SHIB": "Shiba Inu",
    "UNI": "Uniswap",
    "LINK": "Chainlink",
    "ETC": "Ethereum Classic",
    "SUI": "Sui",
    "NEAR": "NEAR Protocol",
    "VET": "VeChain",
    "FIL": "Filecoin",
    "XTZ": "Tezos",
    "ALGO": "Algorand",
    "THETA": "Theta Network",
    "FTM": "Fantom",
    "XDAI": "xDai",
    "RUNE": "THORChain",
}

def _fmt_num(v, d=3):
    p = f"{v:,.{d}f}".replace(",", " ").split(".")
    i = p[0]
    d = p[1].rstrip("0") if len(p) > 1 else ""
    return f"{i},{d}" if d else i

@loader.tds
class FinanceMod(loader.Module):
    strings = {
        "name": "FinanceMod",
        "valute_description": "<кол-во> <код> - курс валюты\n<кол-во> - список",
        "valute_no_args": (
            "💵 <b>Курс валюты с сайта </b><a href='https://www.cbr.ru/'>ЦБ(РФ)</a>\n"
            "<b>Актуально на</b> <i>{}</i>\n\n<blockquote expandable>{}</blockquote>"
        ),
        "valute_specific": (
            "💵 <b>Курс валюты с сайта </b><a href='https://www.cbr.ru/'>ЦБ(РФ)</a>\n"
            "<b>Актуально на</b> <i>{}</i>\n\n{}"
        ),
        "valute_not_found": "🚫 Валюта {} не найдена",
        "crypto_description": "<кол-во> <код> - курс крипты\n<кол-во> - список",
        "crypto_no_args": "💎 <b>Курсы криптовалют</b>\n\n<blockquote expandable>{}</blockquote>",
        "crypto_specific": "💎 <b>Курс криптовалюты</b>\n\n{}",
        "crypto_not_found": "🚫 Криптовалюта {} не найдена",
        "error": "🚫 Ошибка получения данных",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "crypto_currency",
                "USD",
                lambda: "Валюта для отображения крипты (USD, RUB, EUR)",
                validator=loader.validators.Choice(["USD", "RUB", "EUR"])
            )
        )

    async def _get_curr_data(self):
        try:
            r = requests.get("https://www.cbr.ru/scripts/XML_daily.asp")
            s = bs4.BeautifulSoup(r.content, 'xml')
            d = datetime.strptime(s.ValCurs['Date'], "%d.%m.%Y").strftime("%d.%m.%Y")
            return d, s.find_all('Valute')
        except:
            return None, None

    async def _get_rates(self):
        try:
            r = requests.get("https://www.cbr.ru/scripts/XML_daily.asp")
            s = bs4.BeautifulSoup(r.content, 'xml')
            rt = {'USD': None, 'EUR': None}
            for v in s.find_all('Valute'):
                if v.CharCode.text in ['USD', 'EUR']:
                    n = float(v.Nominal.text.replace(',', '.'))
                    vl = float(v.Value.text.replace(',', '.'))
                    rt[v.CharCode.text] = vl / n
            if rt['USD'] and rt['EUR']:
                rt['EUR_USD'] = rt['USD'] / rt['EUR']
            else:
                rt['EUR_USD'] = None
            return rt
        except:
            return None

    async def _fmt_curr(self, v, a=1):
        if v.CharCode.text == "XDR":
            return None
        c = v.CharCode.text
        n = v.Name.text
        v = float(v.Value.text.replace(',', '.')) / float(v.Nominal.text.replace(',', '.'))
        t = v * a
        ts = _fmt_num(t, 3)
        return f"{_FLAGS.get(c, '🏳')} [{a}] {n} ({c}) - {ts} руб."

    async def _get_crypto(self):
        try:
            return requests.get("https://api.coinlore.net/api/tickers/").json().get('data', [])
        except:
            return None

    async def _fmt_crypto(self, c, a=1):
        r = await self._get_rates()
        if not r:
            return "🚫 Ошибка получения курсов валют"
        cr = self.config["crypto_currency"]
        try:
            p = float(c['price_usd'])
        except:
            return "🚫 Ошибка данных криптовалюты"
        if cr == "RUB":
            if not r['USD']:
                return "🚫 Курс USD не найден"
            p *= r['USD']
        elif cr == "EUR":
            if not r['EUR_USD']:
                return "🚫 Курс EUR/USD не рассчитан"
            p *= r['EUR_USD']
        t = p * a
        ts = _fmt_num(t)
        s = c['symbol'].upper()
        e = _CRYPTO_EMOJIS.get(s, "💠")
        n = _CRYPTO_LIST.get(s, c['name'])
        cs = {"USD": "$", "RUB": "₽", "EUR": "€"}.get(cr, "$")
        return f"{e} [{a}] {n} ({s}) - {ts}{cs}"

    @loader.command()
    async def valutecmd(self, m):
        """[count]  [usd, eur, ...]"""
        a = utils.get_args(m)
        d, v = await self._get_curr_data()
        if not d or not v:
            return await utils.answer(m, self.strings["error"])
        if len(a) == 0:
            l = []
            for x in v:
                if (n := await self._fmt_curr(x)):
                    l.append(n)
            await utils.answer(m, self.strings["valute_no_args"].format(d, "\n".join(l)))
        elif len(a) == 1:
            try:
                am = float(a[0])
                l = []
                for x in v:
                    if (n := await self._fmt_curr(x, am)):
                        l.append(n)
                await utils.answer(m, self.strings["valute_no_args"].format(d, "\n".join(l)))
            except:
                await utils.answer(m, "🚫 Некорректное число")
        elif len(a) == 2:
            try:
                am = float(a[0])
                c = a[1].upper()
                for x in v:
                    if x.CharCode.text == c:
                        if (n := await self._fmt_curr(x, am)):
                            return await utils.answer(m, self.strings["valute_specific"].format(d, n))
                await utils.answer(m, self.strings["valute_not_found"].format(c))
            except:
                await utils.answer(m, "🚫 Некорректное число")

    @loader.command()
    async def cryptocmd(self, m):
        """[count] [ton, btc, ...]"""
        a = utils.get_args(m)
        c = await self._get_crypto()
        if not c:
            return await utils.answer(m, self.strings["error"])
        try:
            if len(a) == 0:
                f = [x for x in c if x['symbol'].upper() in _CRYPTO_LIST]
                l = []
                for x in f:
                    if (n := await self._fmt_crypto(x)):
                        l.append(n)
                await utils.answer(m, self.strings["crypto_no_args"].format("\n".join(l)))
            elif len(a) == 1:
                am = float(a[0])
                f = [x for x in c if x['symbol'].upper() in _CRYPTO_LIST]
                l = []
                for x in f:
                    if (n := await self._fmt_crypto(x, am)):
                        l.append(n)
                await utils.answer(m, self.strings["crypto_no_args"].format("\n".join(l)))
            elif len(a) == 2:
                am = float(a[0])
                t = a[1].upper()
                f = False
                for x in c:
                    if x['symbol'].upper() == t:
                        if (n := await self._fmt_crypto(x, am)):
                            f = True
                            await utils.answer(m, self.strings["crypto_specific"].format(n))
                            break
                if not f:
                    await utils.answer(m, self.strings["crypto_not_found"].format(t))
        except ValueError:
            await utils.answer(m, "🚫 Некорректное число")
        except Exception as e:
            await utils.answer(m, f"🚫 Ошибка: {str(e)}")