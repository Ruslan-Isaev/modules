# meta developer: @qShad0_bio
import os
import tempfile
import zipfile
import aiohttp
import asyncio
from .. import loader, utils

async def run_subprocess(command):
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return process.returncode, stdout.decode(), stderr.decode()

async def clonerepo(url: str, dir: str):
    command = ['git', 'clone', url, dir]
    returncode, stdout, stderr = await run_subprocess(command)
    return returncode, stderr

class GitRepoMod(loader.Module):
    """Клонирует git репозиторий и отправляет его в виде zip-архива"""

    strings = {'name': 'GitRepo'}

    @loader.command()
    async def git(self, message):
        """Клонирует git репозиторий и отправляет его в виде zip-архива"""
        if message.reply_to_msg_id:
            replied_message = await message.get_reply_message()
            url = replied_message.message.strip()
        else:
            args = utils.get_args_raw(message)
            if not args:
                await utils.answer(message, "<b>Укажите URL git репозитория.</b>")
                return
            url = args.strip()

        await utils.answer(message, "<b>Начинаю загрузку....</b>")
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                repo_dir = os.path.join(temp_dir, "repo")
                try:
                    repocode, stderr = await clonerepo(url, repo_dir)
                    if repocode != 0:
                        await utils.answer(message, f"<b>Ошибка при клонировании репозитория: {str(stderr)}</b>")
                        return
                    repo_name = os.path.basename(url.split("/").pop().rstrip(".git"))
                except Exception as e:
                    await utils.answer(message, f"<b>Ошибка при клонировании репозитория: {str(e)}</b>")
                    return

                zip_file = os.path.join(temp_dir, f"{repo_name}.zip")
                try:
                    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for root, _, files in os.walk(repo_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, repo_dir)
                                zipf.write(file_path, arcname)
                except Exception as e:
                    await utils.answer(message, f"<b>Ошибка при архивации репозитория: {str(e)}</b>")
                    return

                await utils.answer_file(message, zip_file, f"<b>Репозиторий {repo_name} в виде zip-архива.</b>")
                await message.delete()

        except Exception as e:
            await utils.answer(message, f"<b>Произошла ошибка: {str(e)}</b>")

    @loader.command()
    async def wget(self, message):
        """Сохраняет файл из интернета"""
        if message.reply_to_msg_id:
            replied_message = await message.get_reply_message()
            url = replied_message.message.strip()
        else:
            args = utils.get_args_raw(message)
            if not args:
                await utils.answer(message, "<b>Укажите URL с файлом</b>")
                return
            url = args.strip()

        await utils.answer(message, "<b>Начинаю загрузку....</b>")
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                downloaded_file_path = os.path.join(temp_dir, os.path.basename(url))
                
                # Скачивание файла
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as resp:
                            if resp.status == 200:
                                with open(downloaded_file_path, 'wb') as f:
                                    f.write(await resp.read())
                            else:
                                await utils.answer(message, "<b>Ошибка при скачивании файла.</b>")
                                return
                except Exception as e:
                    await utils.answer(message, f"<b>Ошибка сохранения: {str(e)}</b>")
                    return

                await utils.answer_file(message, downloaded_file_path, f"<b>Файл {url} успешно сохранен</b>")
                await message.delete()

        except Exception as e:
            await utils.answer(message, f"<b>Произошла ошибка: {str(e)}</b>")
