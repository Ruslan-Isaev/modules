version = (1, 0, 0)

# meta developer: @RUIS_VlP
# requires: paramiko

import random
from datetime import timedelta
from telethon import TelegramClient, events
from telethon import functions
from telethon.tl.types import Message
import os
from .. import loader, utils

import paramiko

def upload_file_sftp(host, port, username, password, local_file, remote_file):
    try:
        # Создаем экземпляр SSHClient
        client = paramiko.SSHClient()
        
        # Загружаем параметры по умолчанию
        client.load_system_host_keys()
        
        # Разрешаем соединение с сервером, если ключа нет в системе
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Подключаемся к серверу
        client.connect(hostname=host, port=port, username=username, password=password)
        
        # Открываем SFTP сессию
        sftp = client.open_sftp()
        
        try:
            sftp.listdir("sshmod")
        except IOError:
            sftp.mkdir("sshmod")
        
        # Загружаем файл
        sftp.put(local_file, remote_file)
        
        print(f'Файл {local_file} успешно загружен на {remote_file}')
        
    except Exception as e:
        print(f'Произошла ошибка: {e}')
    finally:
        # Закрываем SFTP сессию и SSH соединение
        if 'sftp' in locals():
            sftp.close()
        client.close()

def execute_ssh_command(host, port, username, password, command):
    try:
        # Создаем экземпляр SSHClient
        client = paramiko.SSHClient()
        
        # Загружаем параметры по умолчанию
        client.load_system_host_keys()
        
        # Разрешаем соединение с сервером, если ключа нет в системе
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Подключаемся к серверу
        client.connect(hostname=host, port=port, username=username, password=password)
        
        # Выполняем команду
        stdin, stdout, stderr = client.exec_command(command)
        
        # Получаем вывод и ошибки
        output = stdout.read().decode()
        error = stderr.read().decode()
        exit_code = stdout.channel.recv_exit_status()
        
        return exit_code, output, error
        
    except Exception as e:
        print(f'Произошла ошибка: {e}')
        return None, None, str(e)
    finally:
        # Закрываем SSH соединение
        client.close()

@loader.tds
class SSHMod(loader.Module):
    """SSH module for uploading files and executing commands"""

    strings = {
        "name": "SSHMod",
        "cfg_host": "IP address or domain",
        "cfg_username": "SSH username",
        "cfg_password": "SSH password",
        "cfg_port": "SSH port",
        "save_description": "<reply> - saves the file to the ~/sshmod directory",
        "save_uploading": "<b>Starting upload....</b>",
        "save_success": "<b>File uploaded to SSH server, file location:</b> <code>~/sshmod/{}</code>",
        "save_no_file": "<b>No files found in the message!</b>",
        "save_reply_required": "<b>The command must be a reply to a message!</b>",
        "sterminal_description": "<command> - executes a command on the SSH server",
        "sterminal_no_command": "<b>No command specified!</b>",
        "sterminal_output": "⌨️<b> System command</b>\n<pre><code class='language-bash'>{}</code></pre>\n<b>Exit code:</b> <code>{}</code>\n<b>📼 Output:</b>\n<pre><code class='language-stdout'>{}</code></pre>",
        "sterminal_error": "⌨️<b> System command</b>\n<pre><code class='language-bash'>{}</code></pre>\n<b>Exit code:</b> <code>{}</code>\n<b>🚫 Errors:</b>\n<pre><code class='language-stderr'>{}</code></pre>",
        "sterminal_output_and_error": "⌨️<b> System command</b>\n<pre><code class='language-bash'>{}</code></pre>\n<b>Exit code:</b> <code>{}</code>\n<b>📼 Output:</b>\n<pre><code class='language-stdout'>{}</code></pre>\n<b>🚫 Errors:</b>\n<pre><code class='language-stderr'>{}</code></pre>",
        "config_not_set": "<b>Values are not set. Set them using the command:</b>\n<code>.config SSHMod</code>",
    }

    strings_ru = {
        "name": "SSHMod",
        "cfg_host": "IP-адрес или домен",
        "cfg_username": "Имя пользователя SSH",
        "cfg_password": "Пароль SSH",
        "cfg_port": "Порт SSH",
        "save_description": "<reply> - сохраняет файл в директорию ~/sshmod",
        "save_uploading": "<b>Начинаю загрузку....</b>",
        "save_success": "<b>Файл загружен на SSH сервер, расположение файла:</b> <code>~/sshmod/{}</code>",
        "save_no_file": "<b>В сообщении не найдены файлы!</b>",
        "save_reply_required": "<b>Команда должна быть ответом на сообщение!</b>",
        "sterminal_description": "<command> - выполняет команду на SSH сервере",
        "sterminal_no_command": "<b>Не указана команда для выполнения!</b>",
        "sterminal_output": "⌨️<b> Системная команда</b>\n<pre><code class='language-bash'>{}</code></pre>\n<b>Код выхода:</b> <code>{}</code>\n<b>📼 Вывод:</b>\n<pre><code class='language-stdout'>{}</code></pre>",
        "sterminal_error": "⌨️<b> Системная команда</b>\n<pre><code class='language-bash'>{}</code></pre>\n<b>Код выхода:</b> <code>{}</code>\n<b>🚫 Ошибки:</b>\n<pre><code class='language-stderr'>{}</code></pre>",
        "sterminal_output_and_error": "⌨️<b> Системная команда</b>\n<pre><code class='language-bash'>{}</code></pre>\n<b>Код выхода:</b> <code>{}</code>\n<b>📼 Вывод:</b>\n<pre><code class='language-stdout'>{}</code></pre>\n<b>🚫 Ошибки:</b>\n<pre><code class='language-stderr'>{}</code></pre>",
        "config_not_set": "<b>Значения не указаны. Укажите их через команду:</b>\n<code>.config SSHMod</code>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "host",
                "None",
                lambda: self.strings["cfg_host"],
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "username",
                "None",
                lambda: self.strings["cfg_username"],
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "password",
                "None",
                lambda: self.strings["cfg_password"],
                validator=loader.validators.Hidden(),
            ),
            loader.ConfigValue(
                "Port",
                22,
                lambda: self.strings["cfg_port"],
                validator=loader.validators.String(),
            ),
        )

    @loader.command(alias="save")
    async def save(self, message):
        """<reply> - saves the file to the ~/sshmod directory"""
        host = self.config["host"] or "None"
        username = self.config["username"] or "None"
        password = self.config["password"] or "None"
        port = self.config["Port"] or "None"
        if host == "None" or username == "None" or password == "None" or port == "None":
            await utils.answer(message, self.strings["config_not_set"])
            return
        reply = await message.get_reply_message()
        if reply:
            if reply.media:
                await utils.answer(message, self.strings["save_uploading"])
                file_path = await message.client.download_media(reply.media)
                sftp_path = f"sshmod/{os.path.basename(file_path)}"
                upload_file_sftp(host, port, username, password, file_path, sftp_path)
                os.remove(file_path)
                await utils.answer(
                    message,
                    self.strings["save_success"].format(os.path.basename(file_path)),
                )
            else:
                await utils.answer(message, self.strings["save_no_file"])
        else:
            await utils.answer(message, self.strings["save_reply_required"])

    @loader.command(alias="sterminal")
    async def sterminal(self, message):
        """<command> - executes a command on the SSH server"""
        host = self.config["host"] or "None"
        username = self.config["username"] or "None"
        password = self.config["password"] or "None"
        port = self.config["Port"] or "None"
        if host == "None" or username == "None" or password == "None" or port == "None":
            await utils.answer(message, self.strings["config_not_set"])
            return
        command = utils.get_args_raw(message)
        if not command:
            await utils.answer(message, self.strings["sterminal_no_command"])
            return

        # Выполняем команду на SSH сервере
        exit_code, output, error = execute_ssh_command(host, port, username, password, command)

        # Формируем ответ в зависимости от наличия вывода и ошибок
        if output and not error:
            response = self.strings["sterminal_output"].format(command, exit_code, output)
        elif error and not output:
            response = self.strings["sterminal_error"].format(command, exit_code, error)
        elif output and error:
            response = self.strings["sterminal_output_and_error"].format(command, exit_code, output, error)
        else:
            response = f"⌨️<b> System command</b>\n<pre><code class='language-bash'>{command}</code></pre>\n<b>Exit code:</b> <code>{exit_code}</code>"

        await utils.answer(message, response)