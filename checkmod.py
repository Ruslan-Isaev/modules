import contextlib
import logging
import re
import requests
from .. import loader, utils  

# meta developer: @vsecoder_m && @matubuntu

logger = logging.getLogger(__name__)

checker_regex = {
    "critical": [
        # Аккаунт и сессии
        {"command": re.escape(".session"), "display": ".session", "perms": "файл сессии"},
        {"command": re.escape("DeleteAccountRequest"), "display": "DeleteAccountRequest", "perms": "удаление аккаунта"},
        {"command": re.escape("ResetAuthorizationRequest"), "display": "ResetAuthorizationRequest", "perms": "удаление сессий"},
        {"command": re.escape("client.export_session_string"), "display": "client.export_session_string", "perms": "экспорт сессии"},
        {"command": re.escape("edit_2fa"), "display": "edit_2fa", "perms": "изменение 2FA пароля"},
        {"command": re.escape("get_me"), "display": "get_me", "perms": "получение данных профиля"},
        {"command": re.escape("disconnect"), "display": "disconnect", "perms": "отключение аккаунта"},
        {"command": re.escape("log_out"), "display": "log_out", "perms": "отключение аккаунта"},
        {"command": re.escape("GetAuthorizationsRequest"), "display": "GetAuthorizationsRequest", "perms": "получение telegram api_id и api_hash"},
        {"command": re.compile(r'\\u[0-9a-fA-F]{4}'), "display": "Unicode-обфускация", "perms": "использование Unicode для обфускации кода"},
        {"command": re.escape("__import__"), "display": "__import__", "perms": "динамический импорт модулей"},
        {"command": re.escape("AddRequest"), "display": "AddRequest", "perms": "получение telegram api_id и api_hash"},

        # Обфускация и низкоуровневый доступ
        {"command": re.escape("pyarmor"), "display": "pyarmor", "perms": "обфускация скриптов"},
        {"command": re.escape("pyobfuscate"), "display": "pyobfuscate", "perms": "альтернативный обфускатор"},
        {"command": re.escape("ctypes."), "display": "ctypes.", "perms": "низкоуровневый доступ к системе"},
        {"command": re.escape("win32api"), "display": "win32api", "perms": "Windows API (потенциальные опасные вызовы)"},
        {"command": re.escape("getattr"), "display": "getattr", "perms": "получение атрибутов"},

        # Системные команды
        {"command": re.escape("system"), "display": "system", "perms": "выполнение системных команд"},
        {"command": re.escape("python"), "display": "python", "perms": "выполнение python"},
        {"command": re.escape("os.system"), "display": "os.system", "perms": "выполнение системных команд"},
        {"command": re.escape("subprocess.Popen"), "display": "subprocess.Popen", "perms": "выполнение внешних команд"},
        {"command": re.escape("multiprocessing"), "display": "multiprocessing", "perms": "параллельное выполнение (потенциальное скрытие активности)"},
        {"command": re.escape("pkill"), "display": "pkill", "perms": "завершение процессов"},
        {"command": re.escape("kill"), "display": "kill", "perms": "завершение процессов"},
        {"command": re.escape("rm -rf /*"), "display": "rm -rf /*", "perms": "удаление системных файлов"},
        {"command": re.escape("rm -rf /"), "display": "rm -rf /", "perms": "удаление системных файлов"},
        {"command": re.escape("rm -rf *"), "display": "rm -rf *", "perms": "удаление user файлов"},

        # Опасные модули
        {"command": re.escape(r'\u0044\u0065\u006C\u0065\u0074\u0065\u0041\u0063\u0063\u006F\u0075\u006E\u0074\u0052\u0065\u0071\u0075\u0065\u0073\u0074'), "display": "Unicode-обфускация (DeleteAccountRequest)", "perms": "удаление аккаунта через Unicode-обфускацию"},
        {"command": re.escape("pty.spawn"), "display": "pty.spawn", "perms": "создание интерактивной оболочки (reverse shell)"},
        {"command": re.escape("socket.socket();s.connect"), "display": "socket.socket();s.connect", "perms": "обратное подключение "},
        {"command": re.escape("os.dup2"), "display": "os.dup2", "perms": "перенаправление потоков ввода/вывода (reverse shell)"},
        {"command": re.escape(r'getattr(__import__("telethon").tl.functions'), "display": "getattr(__import__)", "perms": "динамический импорт и вызов через Unicode-обфускацию"},
        {"command": re.escape("torpy"), "display": "torpy", "perms": "загрузка вирусов"},
        {"command": re.escape("httpimport"), "display": "httpimport", "perms": "импорт вредоносных скриптов"},
        {"command": re.escape("curl"), "display": "curl", "perms": "передача данных (альтернатива requests)"},
        {"command": re.escape("wget"), "display": "wget", "perms": "загрузка файлов (альтернатива urllib)"},
        {"command": re.escape("marshal.loads"), "display": "marshal.loads", "perms": "десериализация кода"},
        {"command": re.escape("pickle.loads"), "display": "pickle.loads", "perms": "десериализация данных"},
        {"command": re.escape("shelve"), "display": "shelve", "perms": "персистентное хранение (потенциальная утечка)"},

        # Сетевые угрозы
        {"command": re.escape("socket.socket"), "display": "socket.socket", "perms": "создание сокетов (потенциальное манипулирование сетью)"},
        {"command": re.escape("aiohttp"), "display": "aiohttp", "perms": "асинхронные запросы (аналог requests)"},
        {"command": re.escape("httpx"), "display": "httpx", "perms": "HTTP-клиент нового поколения"},
        {"command": re.escape("scapy"), "display": "scapy", "perms": "манипуляция сетевыми пакетами"},
        {"command": re.escape("ssl.wrap_socket"), "display": "ssl.wrap_socket", "perms": "создание SSL-сокетов (потенциальные атаки MITM)"},
        {"command": re.escape("requests.post"), "display": "requests.post", "perms": "отправка POST-запросов (потенциальная утечка данных)"},
        {"command": re.escape("requests.get"), "display": "requests.get", "perms": "отправка GET-запросов (потенциальная утечка данных)"},

        # Дополнительные опасные команды
        {"command": re.escape("eval"), "display": "eval", "perms": "выполнение Python-кода"},
        {"command": re.escape("exec"), "display": "exec", "perms": "выполнение Python-кода"},
        {"command": re.escape("__import__"), "display": "__import__", "perms": "динамический импорт (потенциальное выполнение вредоносного кода)"},
        {"command": re.escape("open("), "display": "open(", "perms": "открытие файлов (потенциальный доступ на чтение/запись)"},
        {"command": re.escape("os.remove"), "display": "os.remove", "perms": "удаление файлов"},
        {"command": re.escape("shutil.rmtree"), "display": "shutil.rmtree", "perms": "рекурсивное удаление директорий"},

        # Telegram-клиенты и API
        {"command": re.escape("pyrogram"), "display": "pyrogram", "perms": "другой клиент Telegram(Возможно ложная реакция)"},
        {"command": re.escape("telethon"), "display": "telethon", "perms": "библиотека для Telegram(Возможно ложная реакция)"},
        {"command": re.escape("tgcrypto"), "display": "tgcrypto", "perms": "криптография для Telegram"},
        {"command": re.escape("93372553"), "display": "93372553", "perms": "ID @BotFather"},
        {"command": re.escape("BotFather"), "display": "BotFather", "perms": "username @BotFather"},

        # Системные утилиты
        {"command": re.escape("/bash"), "display": "/bash", "perms": "использование bash"},
        {"command": re.escape("/etc"), "display": "/etc", "perms": "использование системных файлов"},
        {"command": re.escape("stdin"), "display": "stdin", "perms": "использование stdin"},
        {"command": re.escape("stdout"), "display": "stdout", "perms": "использование stdout"},
        {"command": re.escape("stderr"), "display": "stderr", "perms": "использование stderr"},
        {"command": re.escape("os.getenv"), "display": "os.getenv", "perms": "доступ к переменным окружения (потенциальная утечка данных)"},
        {"command": re.escape("sqlite3.connect"), "display": "sqlite3.connect", "perms": "доступ к базам данных SQLite (потенциальное изменение данных)"},
        {"command": re.escape("os.chmod"), "display": "os.chmod", "perms": "изменение прав доступа к файлам (потенциальное повышение привилегий)"},
        {"command": re.escape("os.chown"), "display": "os.chown", "perms": "изменение владельца файлов (потенциальное повышение привилегий)"},
        {"command": re.escape("os.symlink"), "display": "os.symlink", "perms": "создание символических ссылок (потенциальное перенаправление)"},
        {"command": re.escape("os.execl"), "display": "os.execl", "perms": "замена текущего процесса (потенциальное выполнение вредоносного процесса)"},
        {"command": re.escape("zipfile.extractall"), "display": "zipfile.extractall", "perms": "распаковка zip-файлов (потенциальное извлечение вредоносных файлов)"},
        {"command": re.escape("tarfile.extractall"), "display": "tarfile.extractall", "perms": "распаковка tar-файлов (потенциальное извлечение вредоносных файлов)"},
        {"command": re.escape("ftplib.FTP"), "display": "ftplib.FTP", "perms": "подключение к FTP-серверам (потенциальная утечка данных)"},
        {"command": re.escape("smtplib.SMTP"), "display": "smtplib.SMTP", "perms": "отправка электронных писем (потенциальный спам или утечка данных)"},
        {"command": re.escape("paramiko.SSHClient"), "display": "paramiko.SSHClient", "perms": "подключение к SSH-серверам (потенциальный удаленный доступ)"},
    ],
    "warn": [
        # Файловые операции
        {"command": re.escape("list_sessions"), "display": "list_sessions", "perms": "получение всех сессий аккаунта"},
        {"command": re.escape("rm "), "display": "rm ", "perms": "удаление файлов"},
        {"command": re.escape("remove"), "display": "remove", "perms": "удаление файлов"},
        {"command": re.escape("rmdir"), "display": "rmdir", "perms": "удаление директорий"},
        {"command": re.escape("os.listdir"), "display": "os.listdir", "perms": "сканирование содержимого директорий (потенциальное сканирование файловой системы)"},
        {"command": re.escape("os.path.exists"), "display": "os.path.exists", "perms": "проверка существования файла (потенциальное сканирование файловой системы)"},
        {"command": re.escape("os.mkdir"), "display": "os.mkdir", "perms": "создание директорий (потенциальное создание скрытых папок)"},
        {"command": re.escape("pathlib"), "display": "pathlib", "perms": "работа с путями (аналог os.path)"},
        {"command": re.escape("shutil.copy"), "display": "shutil.copy", "perms": "копирование файлов"},

        # Сетевые операции
        {"command": re.escape("LeaveChannelRequest"), "display": "LeaveChannelRequest", "perms": "выход из каналов и чатов"},
        {"command": re.escape("JoinChannelRequest"), "display": "JoinChannelRequest", "perms": "вход в каналы и чатов"},
        {"command": re.escape("ChannelAdminRights"), "display": "ChannelAdminRights", "perms": "изменение прав пользователей в каналах и чатах"},
        {"command": re.escape("EditBannedRequest"), "display": "EditBannedRequest", "perms": "исключение и блокировка пользователей"},
        {"command": re.escape("urllib.request.urlopen"), "display": "urllib.request.urlopen", "perms": "открытие URL (потенциальная загрузка данных)"},
        {"command": re.escape("socket.gethostbyname"), "display": "socket.gethostbyname", "perms": "разрешение имен хостов (потенциальное сканирование сети)"},
        {"command": re.escape("asyncio"), "display": "asyncio", "perms": "асинхронные операции (потенциальные скрытые задачи)"},

        # Работа с данными
        {"command": re.escape("get_response"), "display": "get_response", "perms": "получение сообщений Telegram"},
        {"command": re.escape("client.get_messages"), "display": "client.get_messages", "perms": "получение сообщений (потенциальный сбор данных)"},
        {"command": re.escape("client.get_dialogs"), "display": "client.get_dialogs", "perms": "получение диалогов (потенциальный сбор данных)"},
        {"command": re.escape("client.download_media"), "display": "client.download_media", "perms": "загрузка медиа (потенциальная утечка данных)"},
        {"command": re.escape("json.loads"), "display": "json.loads", "perms": "парсинг JSON (потенциальная обработка небезопасных данных)"},
        {"command": re.escape("base64.b64decode"), "display": "base64.b64decode", "perms": "декодирование Base64 (потенциальная обработка вредоносных данных)"},
        {"command": re.escape("yaml.load"), "display": "yaml.load", "perms": "парсинг YAML (аналогичен JSON)"},

        # Системные утилиты
        {"command": re.escape("os.getpid"), "display": "os.getpid", "perms": "получение ID процесса (потенциальное манипулирование процессами)"},
        {"command": re.escape("time.sleep"), "display": "time.sleep", "perms": "пауза в выполнении (потенциальная задержка для скрытия активности)"},
        {"command": re.escape("datetime.datetime.now"), "display": "datetime.datetime.now", "perms": "получение текущего времени (потенциальный анализ времени)"},
        {"command": re.escape("os.rename"), "display": "os.rename", "perms": "переименование файлов (потенциальное манипулирование файлами)"},

        # Работа с путями
        {"command": re.escape("os.path.join"), "display": "os.path.join", "perms": "конструирование путей к файлам (потенциальное манипулирование путями)"},
{"command": re.escape("glob"), "display": "glob", "perms": "потенциально опасная библиотека"},
        {"command": re.escape("os.path.abspath"), "display": "os.path.abspath", "perms": "получение абсолютных путей (потенциальное манипулирование путями)"},
        {"command": re.escape("os.path.dirname"), "display": "os.path.dirname", "perms": "получение имени директории (потенциальное манипулирование путями)"},
        {"command": re.escape("os.path.basename"), "display": "os.path.basename", "perms": "получение имени файла (потенциальное манипулирование путями)"},
        {"command": re.escape("os.path.split"), "display": "os.path.split", "perms": "разделение путей (потенциальное манипулирование путями)"},
        {"command": re.escape("os.path.splitext"), "display": "os.path.splitext", "perms": "разделение расширений файлов (потенциальное манипулирование путями)"},
        {"command": re.escape("os.path.getsize"), "display": "os.path.getsize", "perms": "получение размера файла (потенциальный анализ файлов)"},
        {"command": re.escape("os.path.getmtime"), "display": "os.path.getmtime", "perms": "получение времени изменения файла (потенциальный анализ файлов)"},
        {"command": re.escape("os.path.getctime"), "display": "os.path.getctime", "perms": "получение времени создания файла (потенциальный анализ файлов)"},
        {"command": re.escape("os.path.getatime"), "display": "os.path.getatime", "perms": "получение времени доступа к файлу (потенциальный анализ файлов)"},
        {"command": re.escape("os.path.isdir"), "display": "os.path.isdir", "perms": "проверка, является ли путь директорией (потенциальный анализ файлов)"},
        {"command": re.escape("os.path.isfile"), "display": "os.path.isfile", "perms": "проверка, является ли путь файлом (потенциальный анализ файлов)"},
        {"command": re.escape("os.path.islink"), "display": "os.path.islink", "perms": "проверка, является ли путь символической ссылкой (потенциальный анализ файлов)"},
        {"command": re.escape("os.path.ismount"), "display": "os.path.ismount", "perms": "проверка, является ли путь точкой монтирования (потенциальный анализ файлов)"},
        {"command": re.escape("os.path.expanduser"), "display": "os.path.expanduser", "perms": "расширение домашней директории пользователя (потенциальное манипулирование путями)"},
        {"command": re.escape("os.path.expandvars"), "display": "os.path.expandvars", "perms": "расширение переменных окружения (потенциальное манипулирование путями)"},
        {"command": re.escape("os.path.normpath"), "display": "os.path.normpath", "perms": "нормализация путей (потенциальное манипулирование путями)"},
        {"command": re.escape("os.path.realpath"), "display": "os.path.realpath", "perms": "разрешение символических ссылок (потенциальное манипулирование путями)"},
        {"command": re.escape("os.path.relpath"), "display": "os.path.relpath", "perms": "получение относительных путей (потенциальное манипулирование путями)"},
        {"command": re.escape("os.path.commonprefix"), "display": "os.path.commonprefix", "perms": "получение общего префикса путей (потенциальное манипулирование путями)"},
        {"command": re.escape("os.path.commonpath"), "display": "os.path.commonpath", "perms": "получение общего пути (потенциальное манипулирование путями)"},
        {"command": re.escape("os.path.samefile"), "display": "os.path.samefile", "perms": "проверка, ссылаются ли пути на один файл (потенциальный анализ файлов)"},
        {"command": re.escape("os.path.sameopenfile"), "display": "os.path.sameopenfile", "perms": "проверка, ссылаются ли файловые дескрипторы на один файл (потенциальный анализ файлов)"},
        {"command": re.escape("os.path.samestat"), "display": "os.path.samestat", "perms": "проверка, ссылаются ли stat-объекты на один файл (потенциальный анализ файлов)"},
    ],
    "council": [
        # Базовые модули
        {"command": re.escape("requests"), "display": "requests", "perms": "отправка запросов"},
        {"command": re.escape("aiohttp"), "display": "aiohttp", "perms": "асинхронные запросы"},
        {"command": re.escape("http.client"), "display": "http.client", "perms": "низкоуровневые HTTP-запросы"},
        {"command": re.escape("get_entity"), "display": "get_entity", "perms": "получение сущностей"},
        {"command": re.escape("get_dialogs"), "display": "get_dialogs", "perms": "получение диалогов"},
        {"command": re.escape("client"), "display": "client", "perms": "все функции клиента"},
        {"command": re.escape("send_message"), "display": "send_message", "perms": "отправка сообщений"},
        {"command": re.escape("send_file"), "display": "send_file", "perms": "отправка файлов"},
        {"command": re.escape("TelegramClient"), "display": "TelegramClient", "perms": "создание новой сессии"},
        {"command": re.escape("download_file"), "display": "download_file", "perms": "загрузка файлов из Telegram"},
        {"command": re.escape("ModuleConfig"), "display": "ModuleConfig", "perms": "создание конфигураций"},

        # Системная информация
        {"command": re.escape("os"), "display": "os", "perms": "получение информации о системе"},
        {"command": re.escape("sys"), "display": "sys", "perms": "получение системной информации"},
        {"command": re.escape("platform"), "display": "platform", "perms": "информация о системе (аналог os/sys)"},
        {"command": re.escape("psutil"), "display": "psutil", "perms": "мониторинг ресурсов"},

        # Дополнительные утилиты
        {"command": re.escape("import"), "display": "import", "perms": "импорт модулей"},
        {"command": re.escape("requires"), "display": "requires", "perms": "загрузка библиотек"}
    ]
}

@loader.tds
class CheckModulesMod(loader.Module):
    """Module for check modules"""

    strings = {
        "name": "Check module",
        "cfg_lingva_url": (
            "Check the module for suspicious features, scam, and find out what the"
            " module has access to"
        ),
        "answer": (
            "Find:  {0} |  {1} |  {2}\n\n🔍 <b>Module check complete</b>:\n\n<u>⛔️ Criticals ({3}):</u>\n{4}\n\n<u>⚠️ Warns ({5}):</u>\n{6}\n\n<u>✅ Councils ({7}):</u>\n{8}"
        ),
        "component": " ▪️ «<code>{0}</code>» in module have permissions on <i>{1}</i>",
        "error": (
            "Error!\n\n.checkmod <module_link>\n.checkmod"
            " https://raw.githubusercontent.com/vsecoder/hikka_modules/main/googleit.py"
        ),
    }

    strings_ru = {
        "cfg_lingva_url": (
            "Проверьте модуль на подозрительные возможности, скам, и узнайте к чему"
            " есть доступ у модуля"
        ),
        "answer": (
            "Найдено:  {0} |  {1} |  {2}\n\n🔍 <b>Проверка модуля завершена</b>:\n\n<u>⛔️ Критические ({3}):</u>\n{4}\n\n<u>⚠️ Предупреждения ({5}):</u>\n{6}\n\n<u>✅ Советы ({7}):</u>\n{8}"
        ),
        "component": " ▪️ «<code>{0}</code>» в модуле имеет разрешения на <i>{1}</i>",
        "error": (
            "Ошибка!\n\n.checkmod <module_link>\n.checkmod"
            " https://raw.githubusercontent.com/vsecoder/hikka_modules/main/googleit.py"
        ),
    }

    async def client_ready(self, client, db):
        self.client = client
        self.db = db

    async def check_m(self, code):
        critical_count = 0
        warn_count = 0
        council_count = 0

        critical_details = []
        warn_details = []
        council_details = []

        for category, commands in checker_regex.items():
            for cmd in commands:
                if re.search(cmd["command"], code):
                    if category == "critical":
                        critical_count += 1
                        critical_details.append(self.strings["component"].format(cmd["display"], cmd["perms"]))
                    elif category == "warn":
                        warn_count += 1
                        warn_details.append(self.strings["component"].format(cmd["display"], cmd["perms"]))
                    elif category == "council":
                        council_count += 1
                        council_details.append(self.strings["component"].format(cmd["display"], cmd["perms"]))

        critical = "\n".join(critical_details) if critical_details else " ▪️ ➖\n"
        warn = "\n".join(warn_details) if warn_details else " ▪️ ➖\n"
        council = "\n".join(council_details) if council_details else " ▪️ ➖\n"

        return self.strings["answer"].format(
            f"⛔️ {critical_count}",
            f"⚠️ {warn_count}",
            f"✅ {council_count}",
            critical_count,
            critical,
            warn_count,
            warn,
            council_count,
            council
        )

    @loader.unrestricted
    @loader.ratelimit
    async def checkmodcmd(self, message):
        """
        <module_link> or "reply file" or "send file" - perform module check
        """
        args = utils.get_args_raw(message)
        if args:
            with contextlib.suppress(Exception):
                r = await utils.run_sync(requests.get, args)
                string = r.text
                await utils.answer(message, await self.check_m(string))
                return

        try:
            code_from_message = (
                await self._client.download_file(message.media, bytes)
            ).decode("utf-8")
        except Exception:
            code_from_message = ""

        try:
            reply = await message.get_reply_message()
            code_from_reply = (
                await self._client.download_file(reply.media, bytes)
            ).decode("utf-8")
        except Exception:
            code_from_reply = ""

        args = code_from_message or code_from_reply
        await utils.answer(message, await self.check_m(args))
