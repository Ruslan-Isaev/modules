version = (1, 1, 1)

# changelog 1.1.0: убрана проверка хэш-суммы, сделано для избежания ошибок

# changelog 1.1.1: изменен способ передачи файла, что бы избежать перерасход оперативной памяти


# meta developer: @RUIS_VlP

import aioboto3
import hashlib
import aiofiles
import os
from .. import loader, utils
import mimetypes
import botocore

CHUNK_SIZE = 50 * 1024 * 1024  # 50MB

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
        	await utils.answer(message, "❌ <b>Вы не указали файл для удаления!")
        	return
        try:
        	await s3_delete(url, bucket, filepath, access, secret)
        	await utils.answer(message, f"✅ <b>Файл</b> <code>{filepath}</code> <b>успешно удален!</b>")
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