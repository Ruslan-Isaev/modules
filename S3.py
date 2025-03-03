__version__ = (1, 2, 0)

# changelog 1.1.0: убрана проверка хэш-суммы, сделано для избежания ошибок

# changelog 1.1.1: изменен способ передачи файла, что бы избежать перерасход оперативной памяти

# changelog 1.2.0: добавлены команды для переименования, вырезания, копирования файлов, просмотра занятого места, отмены незавершенных загрузок и полной очистки S3 хранилища

# meta developer: @RUIS_VlP

import aioboto3
import aiofiles
import os
from .. import loader, utils
import mimetypes
import botocore
import asyncio

CHUNK_SIZE = 50 * 1024 * 1024  # 50MB

#полная очистка S3 хранилища
async def s3_purge(url, bucket, access_key, secret_key):
    session = aioboto3.Session()
    async with session.client("s3", endpoint_url=url, aws_access_key_id=access_key, aws_secret_access_key=secret_key) as s3:
    	response = await s3.list_objects_v2(Bucket=bucket, Prefix="")
    	files = [obj["Key"] for obj in response.get("Contents", [])]
    	async for file in files:
    		await s3.delete_object(Bucket=bucket, Key=file)
    	await s3_clear(url, bucket, access_key, secret_key)
    	
    
#удаление незавершенных загрузок
async def s3_clear(url, bucket, access_key, secret_key):
    session = aioboto3.Session()
    async with session.client(
        "s3",
        endpoint_url=url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    ) as s3:
        deleted_count = 0

        # Удаляем незавершённые загрузки
        paginator = s3.get_paginator("list_multipart_uploads")
        async for page in paginator.paginate(Bucket=bucket):
            if "Uploads" in page:
                for upload in page["Uploads"]:
                    upload_id = upload["UploadId"]
                    key = upload["Key"]

                    # Прерываем незавершённые загрузки
                    await s3.abort_multipart_upload(
                        Bucket=bucket,
                        Key=key,
                        UploadId=upload_id
                    )
                    deleted_count += 1

        # Проверка объектов, которые могут быть частично загружены
        paginator = s3.get_paginator("list_objects_v2")
        async for page in paginator.paginate(Bucket=bucket):
            if "Contents" in page:
                for obj in page["Contents"]:
                    try:
                        # Получаем размер объекта
                        head_response = await s3.head_object(Bucket=bucket, Key=obj["Key"])
                        # Если размер объекта на сервере меньше ожидаемого (ошибочная загрузка), удаляем его
                        if head_response["ContentLength"] < obj["Size"]:
                            await s3.delete_objects(
                                Bucket=bucket,
                                Delete={"Objects": [{"Key": obj["Key"]}]}
                            )
                            deleted_count += 1
                    except Exception as e:
                        pass  # Игнорируем ошибки, если они возникнут, например, из-за отсутствия доступа

        return deleted_count

#сколько памяти занято
async def s3_usage(url, bucket, access_key, secret_key):
    session = aioboto3.Session()
    async with session.client(
        "s3",
        endpoint_url=url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    ) as s3:
        total_size = 0

        paginator = s3.get_paginator("list_objects_v2")
        async for page in paginator.paginate(Bucket=bucket):
            if "Contents" in page:
                total_size += sum(obj["Size"] for obj in page["Contents"])

        return total_size / (1024**3)  # Размер в ГБ

#вырезать
async def s3_cut(url, bucket, newkey, oldkey, access_key, secret_key):
    session = aioboto3.Session()
    async with session.client(
        "s3",
        endpoint_url=url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    ) as s3:
        await s3.copy_object(
            Bucket=bucket,
            CopySource={'Bucket': bucket, 'Key': oldkey},
            Key=newkey
        )
        await s3.delete_object(Bucket=bucket, Key=oldkey)
        
async def s3_copy(url, bucket, newkey, oldkey, access_key, secret_key):
    session = aioboto3.Session()
    async with session.client(
        "s3",
        endpoint_url=url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key
    ) as s3:
        await s3.copy_object(
            Bucket=bucket,
            CopySource={'Bucket': bucket, 'Key': oldkey},
            Key=newkey
        )

async def s3_upload(url, bucket, filename, filepath, access_key, secret_key):
    session = aioboto3.Session()
    
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type is None:
        mime_type = "binary/octet-stream"

    async with session.client(
        "s3",
        endpoint_url=url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=botocore.config.Config(
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
        ),
    ) as s3:
        async with aiofiles.open(filename, "rb") as file:
            upload_id = None
            parts = []
            part_number = 1

            # Инициализируем многокомпонентную загрузку
            response = await s3.create_multipart_upload(
                Bucket=bucket,
                Key=f"{filepath}/{filename}".replace(" ", "_"),
                ContentType=mime_type
            )
            upload_id = response["UploadId"]

            try:
                while True:
                    chunk = await file.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    
                    response = await s3.upload_part(
                        Bucket=bucket,
                        Key=f"{filepath}/{filename}".replace(" ", "_"),
                        PartNumber=part_number,
                        UploadId=upload_id,
                        Body=chunk
                    )

                    parts.append({"PartNumber": part_number, "ETag": response["ETag"]})
                    part_number += 1

                # Завершаем многокомпонентную загрузку
                await s3.complete_multipart_upload(
                    Bucket=bucket,
                    Key=f"{filepath}/{filename}".replace(" ", "_"),
                    UploadId=upload_id,
                    MultipartUpload={"Parts": parts},
                )
            except Exception as e:
                await s3.abort_multipart_upload(
                    Bucket=bucket,
                    Key=f"{filepath}/{filename}".replace(" ", "_"),
                    UploadId=upload_id,
                )
                raise e

async def s3_download(url, bucket, filename, filepath, access_key, secret_key):
    session = aioboto3.Session()
    async with session.client("s3", endpoint_url=url, aws_access_key_id=access_key, aws_secret_access_key=secret_key) as s3:
    	await s3.download_file(bucket, filename, f"{filepath}/{filename.split('/')[-1]}")
    	return f"{filepath}/{filename.split('/')[-1]}"

async def s3_delete(url, bucket, filename, access_key, secret_key):
    session = aioboto3.Session()
    async with session.client("s3", endpoint_url=url, aws_access_key_id=access_key, aws_secret_access_key=secret_key) as s3:
    	await s3.delete_object(Bucket=bucket, Key=filename)
    	
async def s3_ls(url, bucket, filepath, access_key, secret_key):
    session = aioboto3.Session()
    async with session.client("s3", endpoint_url=url, aws_access_key_id=access_key, aws_secret_access_key=secret_key) as s3:
    	response = await s3.list_objects_v2(Bucket=bucket, Prefix=filepath)
    	return [obj["Key"] for obj in response.get("Contents", [])] #я сам не ебу что это, мне это ChatGPT сделал


@loader.tds
class S3Mod(loader.Module):
    """Модуль для работы с S3 хранилищами"""

    strings = {
        "name": "S3",
    }
    
    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "url",
                "None",
                lambda: "Ссылка на ваше S3 хранилище",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "bucketname",
                "None",
                lambda: "Имя bucket'а",
                validator=loader.validators.String(),
            ),
            loader.ConfigValue(
                "access_key",
                "None",
                lambda: "Ключ авторизации",
                validator=loader.validators.Hidden(),
            ),
            loader.ConfigValue(
                "secret_key",
                "None",
                lambda: "Секретный ключ",
                validator=loader.validators.Hidden(),
            ),
        )

    @loader.command()
    async def S3upload(self, message):
        """<path> <reply> - сохраняет файл в S3 хранилище"""
        url = self.config["url"] or "None"
        bucket = self.config["bucketname"] or "None"
        access = self.config["access_key"] or "None"
        secret = self.config["secret_key"] or "None"
        if url == "None" or bucket == "None" or secret == "None" or access == "None":
            await utils.answer(message, f"❌ <b>Вы не настроили модуль! Укажите необходимые данные в config. Команда: </b><code>{self.get_prefix()}config S3</code>")
            return
        args = utils.get_args_raw(message)
        if args:
        	filepath = args.split(" ")[0]
        	filepath = filepath[1:] if filepath.startswith('/') else filepath #удаление / из переменной, если она идет первым символом
        else:
        	filepath = "FromHikka"
        reply = await message.get_reply_message()
        if reply and reply.media:
        	await utils.answer(message, "💿 <b>Сохраняю файл на сервер...</b>")
        	try:
        		filename = await message.client.download_media(reply.media)
        		await utils.answer(message, "☁️ <b>Сохраняю файл в S3 хранилище...</b>")
        		await s3_upload(url, bucket, filename, filepath, access, secret)
        		await utils.answer(message, "💿 <b>Удаляю файл с сервера...</b>")
        		os.remove(filename)
        		await utils.answer(message, f"✅ <b>Успешно! Файл сохранен в директорию</b> <code>/{filepath}</code> <b>на вашем S3 хранилище</b>")
        	except Exception as e:
        		await utils.answer(message, f"❌ <b>Ошибка!</b>\n\n<code>{e}</code>")
        		os.remove(filename)
        else:
        	await utils.answer(message, "❌  <b>Ошибка! Не найден ответ на сообщение или в ответном сообщении отсутствуют файлы.</b>")
        	
        	
    @loader.command()
    async def S3LS(self, message):
        """<path> - список файлов в S3 хранилище"""
        url = self.config["url"] or "None"
        bucket = self.config["bucketname"] or "None"
        access = self.config["access_key"] or "None"
        secret = self.config["secret_key"] or "None"
        if url == "None" or bucket == "None" or secret == "None" or access == "None":
            await utils.answer(message, f"❌ <b>Вы не настроили модуль! Укажите необходимые данные в config. Команда: </b><code>{self.get_prefix()}config S3</code>")
            return
        args = utils.get_args_raw(message)
        if args:
        	filepath = args
        	filepath = filepath[1:] if filepath.startswith('/') else filepath
        else:
        	filepath = ""
        try:
        	ls = await s3_ls(url, bucket, filepath, access, secret)
        	output = '\n'.join(['▪️<code>' + item + '</code>' for item in ls]) #превращение списка в человекочитаемый текст
        	await utils.answer(message, f"🗂 <b>Список файлов и директорий в</b> <code>/{filepath}</code><b>:</b>\n\n{output}")
        except Exception as e:
        	await utils.answer(message, f"❌ <b>Ошибка!</b>\n\n<code>{e}</code>")
        	
    @loader.command()
    async def S3delete(self, message):
        """<path> - удаляет файл из S3 хрпнилища"""
        url = self.config["url"] or "None"
        bucket = self.config["bucketname"] or "None"
        access = self.config["access_key"] or "None"
        secret = self.config["secret_key"] or "None"
        if url == "None" or bucket == "None" or secret == "None" or access == "None":
            await utils.answer(message, f"❌ <b>Вы не настроили модуль! Укажите необходимые данные в config. Команда: </b><code>{self.get_prefix()}config S3</code>")
            return
        args = utils.get_args_raw(message)
        if args:
        	filepath = args
        	filepath = filepath[1:] if filepath.startswith('/') else filepath #удаление / из переменной, если она идет первым символом
        else:
        	await utils.answer(message, "❌ <b>Вы не указали файл для удаления!</b>")
        	return
        try:
        	await s3_delete(url, bucket, filepath, access, secret)
        	await utils.answer(message, f"✅ <b>Файл</b> <code>{filepath}</code> <b>успешно удален!</b>")
        except Exception as e:
        	await utils.answer(message, f"❌ <b>Ошибка!</b>\n\n<code>{e}</code>")
        	
    @loader.command()
    async def S3rename(self, message):
        """<folder> <old_filename> <new_filename> - переименовывает файл. Пробелы в адресе заменяйте на %20"""
        url = self.config["url"] or "None"
        bucket = self.config["bucketname"] or "None"
        access = self.config["access_key"] or "None"
        secret = self.config["secret_key"] or "None"
        if url == "None" or bucket == "None" or secret == "None" or access == "None":
            await utils.answer(message, f"❌ <b>Вы не настроили модуль! Укажите необходимые данные в config. Команда: </b><code>{self.get_prefix()}config S3</code>")
            return
        args = utils.get_args_raw(message)
        if args:
        	keys = args.split(" ")
        	if len(keys) == 3 or len(keys) > 3:
        		key0 = keys[0]
        		key0 = key0[1:] if key0.startswith('/') else key0
        		key0 = key0.replace("%20", " ")
        		
        		key1 = keys[1]
        		key1 = key1[1:] if key1.startswith('/') else key1
        		key1 = key1.replace("%20", " ")
        		
        		key2 = keys[2]
        		key2 = key2[1:] if key2.startswith('/') else key2
        		key2 = key2.replace("%20", " ")
        	else:
        		await utils.answer(message, "❌ <b>Вы указали недостаточно аргументов!</b>")
        		return
        else:
        	await utils.answer(message, "❌ <b>Вы не указали файл для переименования!</b>")
        	return
        try:
        	oldfilename = f"{key0}/{key1}"
        	newfilename = f"{key0}/{key2}"
        	await s3_cut(url, bucket, newfilename, oldfilename, access, secret)
        	await utils.answer(message, f"✅ <b>Файл</b> <code>{oldfilename}</code> <b>успешно переименован в</b> <code>{newfilename}</code>!</b>")
        except Exception as e:
        	await utils.answer(message, f"❌ <b>Ошибка!</b>\n\n<code>{e}</code>")
        	
    @loader.command()
    async def S3cut(self, message):
        """<file> <old_folder> <new_folder> - вырезает файл. Пробелы в адресе заменяйте на %20"""
        url = self.config["url"] or "None"
        bucket = self.config["bucketname"] or "None"
        access = self.config["access_key"] or "None"
        secret = self.config["secret_key"] or "None"
        if url == "None" or bucket == "None" or secret == "None" or access == "None":
            await utils.answer(message, f"❌ <b>Вы не настроили модуль! Укажите необходимые данные в config. Команда: </b><code>{self.get_prefix()}config S3</code>")
            return
        args = utils.get_args_raw(message)
        if args:
        	keys = args.split(" ")
        	if len(keys) == 3 or len(keys) > 3:
        		key0 = keys[0]
        		key0 = key0[1:] if key0.startswith('/') else key0
        		key0 = key0.replace("%20", " ")
        		
        		key1 = keys[1]
        		key1 = key1[1:] if key1.startswith('/') else key1
        		key1 = key1.replace("%20", " ")
        		
        		key2 = keys[2]
        		key2 = key2[1:] if key2.startswith('/') else key2
        		key2 = key2.replace("%20", " ")
        	else:
        		await utils.answer(message, "❌ <b>Вы указали недостаточно аргументов!</b>")
        		return
        else:
        	await utils.answer(message, "❌ <b>Вы не указали файл для вырезания!</b>")
        	return
        try:
        	oldfilename = f"{key1}/{key0}"
        	newfilename = f"{key2}/{key0}"
        	await s3_cut(url, bucket, newfilename, oldfilename, access, secret)
        	await utils.answer(message, f"✅ <b>Файл</b> <code>{oldfilename}</code> <b>успешно вырезан в</b> <code>{newfilename}</code>!</b>")
        except Exception as e:
        	await utils.answer(message, f"❌ <b>Ошибка!</b>\n\n<code>{e}</code>")
        	
    @loader.command()
    async def S3copy(self, message):
        """<file> <old_folder> <new_folder> - копирует файл. Пробелы в адресе заменяйте на %20"""
        url = self.config["url"] or "None"
        bucket = self.config["bucketname"] or "None"
        access = self.config["access_key"] or "None"
        secret = self.config["secret_key"] or "None"
        if url == "None" or bucket == "None" or secret == "None" or access == "None":
            await utils.answer(message, f"❌ <b>Вы не настроили модуль! Укажите необходимые данные в config. Команда: </b><code>{self.get_prefix()}config S3</code>")
            return
        args = utils.get_args_raw(message)
        if args:
        	keys = args.split(" ")
        	if len(keys) == 3 or len(keys) > 3:
        		key0 = keys[0]
        		key0 = key0[1:] if key0.startswith('/') else key0
        		key0 = key0.replace("%20", " ")
        		
        		key1 = keys[1]
        		key1 = key1[1:] if key1.startswith('/') else key1
        		key1 = key1.replace("%20", " ")
        		
        		key2 = keys[2]
        		key2 = key2[1:] if key2.startswith('/') else key2
        		key2 = key2.replace("%20", " ")
        	else:
        		await utils.answer(message, "❌ <b>Вы указали недостаточно аргументов!</b>")
        		return
        else:
        	await utils.answer(message, "❌ <b>Вы не указали файл для копирования!</b>")
        	return
        try:
        	oldfilename = f"{key1}/{key0}"
        	newfilename = f"{key2}/{key0}"
        	await s3_copy(url, bucket, newfilename, oldfilename, access, secret)
        	await utils.answer(message, f"✅ <b>Файл</b> <code>{oldfilename}</code> <b>успешно копирован в</b> <code>{newfilename}</code>!</b>")
        except Exception as e:
        	await utils.answer(message, f"❌ <b>Ошибка!</b>\n\n<code>{e}</code>")
        	
    @loader.command()
    async def S3download(self, message):
        """<path> - скачивает файл из S3 хрпнилища и отправляет в Telegram"""
        url = self.config["url"] or "None"
        bucket = self.config["bucketname"] or "None"
        access = self.config["access_key"] or "None"
        secret = self.config["secret_key"] or "None"
        if url == "None" or bucket == "None" or secret == "None" or access == "None":
            await utils.answer(message, f"❌ <b>Вы не настроили модуль! Укажите необходимые данные в config. Команда: </b><code>{self.get_prefix()}config S3</code>")
            return
        args = utils.get_args_raw(message)
        if args:
        	filename = args
        	filename = filename[1:] if filename.startswith('/') else filename #удаление / из переменной, если она идет первым символом
        else:
        	await utils.answer(message, "❌ <b>Вы не указали файл для сохранения!</b>")
        	return
        try:
        	dl = await s3_download(url, bucket, filename, utils.get_base_dir(), access, secret)
        	await utils.answer_file(message, dl,  caption=f"✅ <b>Вот ваш файл</b> <code>/{filename}</code><b>!</b>")
        	os.remove(dl)
        except Exception as e:
        	await utils.answer(message, f"❌ <b>Ошибка!</b>\n\n<code>{e}</code>")
        	
    @loader.command()
    async def s3config(self, message):
        """- открыть конфигурацию модуля"""
        name = "S3"
        await self.allmodules.commands["config"](
            await utils.answer(message, f"{self.get_prefix()}config {name}")
        )
        
    @loader.command()
    async def S3usage(self, message):
        """- сколько занято памяти на S3"""
        url = self.config["url"] or "None"
        bucket = self.config["bucketname"] or "None"
        access = self.config["access_key"] or "None"
        secret = self.config["secret_key"] or "None"
        if url == "None" or bucket == "None" or secret == "None" or access == "None":
            await utils.answer(message, f"❌ <b>Вы не настроили модуль! Укажите необходимые данные в config. Команда: </b><code>{self.get_prefix()}config S3</code>")
            return
        try:
        	usage = await s3_usage(url, bucket, access, secret)
        	await utils.answer(message, f"🗂 <b>Использовано</b> <code>{round(usage, 2)}</code> <b>ГБ памяти.</b>")
        except Exception as e:
        	await utils.answer(message, f"❌ <b>Ошибка!</b>\n\n<code>{e}</code>")
        	
    @loader.command()
    async def S3clear(self, message):
        """- удаление незавершенных загрузок"""
        url = self.config["url"] or "None"
        bucket = self.config["bucketname"] or "None"
        access = self.config["access_key"] or "None"
        secret = self.config["secret_key"] or "None"
        if url == "None" or bucket == "None" or secret == "None" or access == "None":
            await utils.answer(message, f"❌ <b>Вы не настроили модуль! Укажите необходимые данные в config. Команда: </b><code>{self.get_prefix()}config S3</code>")
            return
        try:
        	await utils.answer(message, "🔎 <b>Ищу незавершенные загрузки...</b>")
        	clear = await s3_clear(url, bucket, access, secret)
        	await utils.answer(message, f"🗂 <b>Удалено</b> <code>{clear}</code> <b>неудавшихся загрузок.</b>")
        except Exception as e:
        	await utils.answer(message, f"❌ <b>Ошибка!</b>\n\n<code>{e}</code>")
        	
    @loader.command()
    async def S3purge(self, message):
        """- ПОЛНАЯ ОЧИСТКА ХРАНИЛИЩА S3. Будьте осторожны с этой командой"""
        url = self.config["url"] or "None"
        bucket = self.config["bucketname"] or "None"
        access = self.config["access_key"] or "None"
        secret = self.config["secret_key"] or "None"
        if url == "None" or bucket == "None" or secret == "None" or access == "None":
            await utils.answer(message, f"❌ <b>Вы не настроили модуль! Укажите необходимые данные в config. Команда: </b><code>{self.get_prefix()}config S3</code>")
            return
        try:
        	await utils.answer(message, "🗂 <b>Начинаю очистку...</b>")
        	clear = await s3_purge(url, bucket, access, secret)
        	await utils.answer(message, f"🗂 <b>Ваше S3 хранилище полностью очищено.</b>")
        except Exception as e:
        	await utils.answer(message, f"❌ <b>Ошибка!</b>\n\n<code>{e}</code>")