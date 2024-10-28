# -*- coding: utf-8 -*-
version = (1, 0, 0)

# meta developer: @RUIS_VlP

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
        	sftp.listdir("SFTP_files")
        except IOError:
        	sftp.mkdir("SFTP_files")
        
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


@loader.tds
class SFTPUploaderMod(loader.Module):
    """Загрузка файлов на SFTP"""

    strings = {
        "name": "SFTPUploader",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "host",
                "None",
                "IP address or domain",
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                "username",
                "None",
                "SFTP username",
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                "password",
                "None",
                "SFTP password",
                validator=loader.validators.Hidden()
            ),
            loader.ConfigValue(
                "Port",
                22,
                "SFTP port",
                validator=loader.validators.String()
            ),
        )

    @loader.command()
    async def sftp(self, message):
        """<reply> - загружает файл на SFPT"""
        host = self.config["host"] or "None"
        username = self.config["username"] or "None"
        password = self.config["password"] or "None"
        port = self.config["Port"] or "None"
        if host == "None" or username == "None" or password == "None" or port == "None":
        	await utils.answer(message, "<b>Значения не указаны. Укажите их через команду:</b>\n<code>.config SFTPUploader</code>")
        	return
        reply = await message.get_reply_message()
        if reply:
        	if reply.media:
        		await utils.answer(message, f"<b>Начинаю загрузку....</b>")
        		file_path = await message.client.download_media(reply.media)
        		sftp_path = f"SFTP_files/{file_path}"
        		upld = upload_file_sftp(host, port, username, password, file_path, sftp_path)
        		os.remove(file_path)
        		await utils.answer(message, f"<b>Файл загружен на SFTP сервер(не факт), расположение файла:</b> <code>~/SFTP_files/{file_path}</code>")
        	else:
        		await utils.answer(message, "<b>В сообщении не найдены файлы!</b>")
        else:
        	await utils.answer(message, "<b>Команда должна быть ответом на сообщение!</b>")
        	return
    