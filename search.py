# meta developer: @RUIS_VlP
# requires: requests pillow

from telethon import TelegramClient, events
from .. import loader, utils
from urllib.parse import quote
import requests
from io import BytesIO
from PIL import Image
from ..inline.types import InlineQuery
import json

@loader.tds
class SearchMod(loader.Module):
    """🌐 Internet search module"""

    strings = {
        "name": "search",
        "picsearch": "🔍 Image search",
        "no_photo": "🚫 Reply to an image to search",
        "upload_error": "❌ Image upload error",
        "search_title": "🌐 Search Internet",
        "search_description": "Search the web using different engines",
        "failed_download": "❌ Failed to download image: {}",
        "image_processing_error": "❌ Image processing error",
        "google_images": "Google Images",
        "yandex_images": "Yandex Images",
        "loading" : "⚙️ Loading...", 
        "search_query_prompt": "🔍 Please specify search query"
    }

    strings_ru = {
        "picsearch": "🔍 Поиск по изображению",
        "no_photo": "🚫 Ответьте на изображение для поиска",
        "upload_error": "❌ Ошибка загрузки изображения",
        "search_title": "🌐 Поиск в интернете",
        "loading" : "⚙️ Загрузка...", 
        "search_description": "Поиск в сети с использованием разных систем",
        "failed_download": "❌ Не удалось загрузить изображение: {}",
        "image_processing_error": "❌ Ошибка обработки изображения",
        "google_images": "Google Картинки",
        "yandex_images": "Яндекс.Картинки",
        "search_query_prompt": "🔍 Укажите запрос для поиска"
    }

    async def upload_to_x0(self, image_bytes: bytes) -> str:
        """Upload image to x0.at"""
        try:
            files = {'file': image_bytes}
            response = requests.post('https://x0.at/', files=files)
            response.raise_for_status()
            return response.text.strip()  # x0.at возвращает прямую ссылку
        except Exception as e:
            print(f"x0.at upload error: {e}")
            return None

    async def yandex_image_search(self, image_bytes: bytes) -> str:
        """Search image via Yandex"""
        try:
            searchUrl = "https://yandex.ru/images/search"
            files = {"upfile": ("blob", image_bytes, "image/jpeg")}
            params = {
                "rpt": "imageview",
                "format": "json",
                "request": '{"blocks":[{"block":"b-page_type_search-by-image__link"}]}',
            }
            response = requests.post(searchUrl, params=params, files=files)
            if response.ok:
                query_string = json.loads(response.content)["blocks"][0]["params"]["url"]
                return searchUrl + "?" + query_string
            return None
        except Exception as e:
            print(f"Yandex search error: {e}")
            return None

    @loader.command()
    async def picsearchcmd(self, message):
        """<reply to image> - 🔍 Reverse image search"""
        if not message.is_reply:
            await utils.answer(message, self.strings["no_photo"])
            return

        reply = await message.get_reply_message()
        
        if not (reply.photo or (reply.document and reply.document.mime_type.startswith('image/'))):
            await utils.answer(message, self.strings["no_photo"])
            return

        # Download image
        try:
            await utils.answer(message, self.strings["loading"])
            image = await reply.download_media(bytes)
        except Exception as e:
            await utils.answer(message, self.strings["failed_download"].format(e))
            return

        # Convert to JPEG
        try:
            with BytesIO(image) as img_buffer:
                with Image.open(img_buffer) as img:
                    jpeg_buffer = BytesIO()
                    img.convert('RGB').save(jpeg_buffer, 'JPEG')
                    image_bytes = jpeg_buffer.getvalue()
        except Exception as e:
            print(f"Image processing error: {e}")
            await utils.answer(message, self.strings["image_processing_error"])
            return

        # Upload to x0.at
        url = await self.upload_to_x0(image_bytes)
        if not url:
            await utils.answer(message, self.strings["upload_error"])
            return
        
        # Create search buttons
        encoded_url = quote(url, safe='')
        yandex_url = await self.yandex_image_search(image_bytes)

        await self.inline.form(
            text=self.strings["picsearch"],
            message=message,
            reply_markup=[
                [
                    {"text": self.strings["google_images"], "url": f"https://lens.google.com/uploadbyurl?url={encoded_url}"},
                    {"text": self.strings["yandex_images"], "url": yandex_url if yandex_url else f"https://yandex.ru/images/search?rpt=imageview&url={encoded_url}"}
                ]
            ]
        )

    @loader.command()
    async def searchcmd(self, message):
        """<text> / <reply> - 🌐 Search Internet"""
        if not message.is_reply:
            if len(message.text) < 8:
                await utils.answer(message, self.strings["search_query_prompt"])
                return
            reply_text = utils.get_args_raw(message)
        else:
            replied_message = await message.get_reply_message()
            reply_text = replied_message.text
        
        encoded_query = quote(reply_text)
        await self.inline.form(
            text=self.strings["search_title"],
            message=message,
            reply_markup=[
                [
                    {"text": "Google", "url": f"https://www.google.com/search?q={encoded_query}"},
                    {"text": "Yandex",  "url": f"https://yandex.ru/search/?text={encoded_query}"}
                ],
                [
                    {"text": "Duckduckgo", "url": f"https://duckduckgo.com/?q={encoded_query}"}
                ]
            ]
        )

    @loader.inline_handler()
    async def search(self, query: InlineQuery):
        """<text> - 🌐 Search Internet"""
        search_text = query.query.strip()
        if not search_text:
            return
        
        encoded_query = quote(search_text)
        buttons = [
            [
                {"text": "Google", "url": f"https://www.google.com/search?q={encoded_query}"},
                {"text": "Yandex", "url": f"https://yandex.ru/search/?text={encoded_query}"}
            ],
            [
                {"text": "Duckduckgo", "url": f"https://duckduckgo.com/?q={encoded_query}"}
            ]
        ]
        
        return {
            "title": self.strings["search_title"],
            "description": self.strings["search_description"],
            "thumb": "https://0x0.st/XlHF.png",
            "message": self.strings["search_title"],
            "reply_markup": buttons
            }
