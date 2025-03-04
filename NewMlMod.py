# ©️ Dan Gazizullin, 2021-2023
# This file is a part of Hikka Userbot
# 🌐 https://github.com/hikariatama/Hikka
# You can redistribute it and/or modify it under the terms of the GNU AGPLv3
# 🔑 https://www.gnu.org/licenses/agpl-3.0.html

import difflib
import inspect
import io
from hikkatl.tl.types import Message
from .. import loader, utils
from ..version import __version__


@loader.tds
class NewMlMod(loader.Module):
    """A module for uploading modules as a file. Let's just say it's a heavily stripped-down UnitHeta."""
    
    strings = {
    "name": "NewMlMod",
    "404": "<emoji document_id=5210952531676504517>❌</emoji> <b>Module not found</b>",
    "not_exact": "<emoji document_id=5312383351217201533>⚠️</emoji> <b>No exact match has been found, so the closest result is shown instead</b>",
    "link": "<emoji document_id=5280658777148760247>🌐</emoji> <b><a href=\"{url}\">Link</a> of</b> <code>{class_name}</code>\n\n<emoji document_id=5188377234380954537>🌘</emoji> <code>{prefix}dlm {url}</code>\n\n{not_exact}",
    "file": "<emoji document_id=5433653135799228968>📁</emoji> <b>File of</b> <code>{class_name}</code>\n\n<emoji document_id=5188377234380954537>🌘</emoji> <code>{prefix}lm</code> <b>in reply to this message to install</b>\n\n{not_exact}",
    "args": "<emoji document_id=5210952531676504517>❌</emoji> <b>You must specify arguments</b>",
    "_cmd_doc_ml": "<module name> - Send link to module"
}

    strings_ru = {
    "404": "<emoji document_id=5210952531676504517>❌</emoji> <b>Модуль не найден</b>",
    "not_exact": "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Точного совпадения не найдено, поэтому показан ближайший результат</b>",
    "link": "<emoji document_id=5280658777148760247>🌐</emoji> <b><a href=\"{url}\">Ссылка</a> на</b> <code>{class_name}</code>\n\n<emoji document_id=5188377234380954537>🌘</emoji> <code>{prefix}dlm {url}</code>\n\n{not_exact}",
    "file": "<emoji document_id=5433653135799228968>📁</emoji> <b>Файл</b> <code>{class_name}</code>\n\n<emoji document_id=5188377234380954537>🌘</emoji> <code>{prefix}lm</code> <b>в ответ на это сообщение, чтобы установить</b>\n\n{not_exact}",
    "args": "<emoji document_id=5210952531676504517>❌</emoji> <b>Вы должны указать аргументы</b>",
    "_cmd_doc_ml": "<имя модуля> - Отправить ссылку на модуль"
}
    strings_uz = {
    "404": "<emoji document_id=5210952531676504517>❌</emoji> <b>Modul topilmadi</b>",
    "not_exact": "<emoji document_id=5312383351217201533>⚠️</emoji> <b>To'g'ri mos keladigan natija topilmadi, shuning uchun eng yaqin natija ko'rsatiladi</b>",
    "link": "<emoji document_id=5280658777148760247>🌐</emoji> <b><a href=\"{url}\">Havola</a> bo'yicha</b> <code>{class_name}</code>\n\n<emoji document_id=5188377234380954537>🌘</emoji> <code>{prefix}dlm {url}</code>\n\n{not_exact}",
    "file": "<emoji document_id=5433653135799228968>📁</emoji> <b>Fayl</b> <code>{class_name}</code>\n\n<emoji document_id=5188377234380954537>🌘</emoji> <code>{prefix}lm</code> <b>bu habarga javob qilib, uni o'rnatish uchun</b>\n\n{not_exact}",
    "args": "<emoji document_id=5210952531676504517>❌</emoji> <b>Siz argumentlarni belgilamadingiz</b>",
    "_cmd_doc_ml": "<modul nomi> - Modulga havola yuborish"
}

    strings_tt = {
    "404": "<emoji document_id=5210952531676504517>❌</emoji> <b>Модуль табылмады</b>",
    "not_exact": "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Тулы тапкыр килгән нәтиҗәләр табылмады, сондыктан ең яңа нәтиҗә күрсәтелә</b>",
    "link": "<emoji document_id=5280658777148760247>🌐</emoji> <b><a href=\"{url}\">Сылтама</a> өчен</b> <code>{class_name}</code>\n\n<emoji document_id=5188377234380954537>🌘</emoji> <code>{prefix}dlm {url}</code>\n\n{not_exact}",
    "file": "<emoji document_id=5433653135799228968>📁</emoji> <b>Файл</b> <code>{class_name}</code>\n\n<emoji document_id=5188377234380954537>🌘</emoji> <code>{prefix}lm</code> <b>осы хәбәрне кабул килгәндә</b>\n\n{not_exact}",
    "args": "<emoji document_id=5210952531676504517>❌</emoji> <b>Аргументларны күрсәтмәгәнсез</b>",
    "_cmd_doc_ml": "<модуль исеме> - Модульга сылтама җибәрү"
}

    strings_tr = {
    "404": "<emoji document_id=5210952531676504517>❌</emoji> <b>Modül bulunamadı</b>",
    "not_exact": "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Herhangi bir tam eşleşme bulunamadığından, en yakın sonuç gösteriliyor</b>",
    "link": "<emoji document_id=5280658777148760247>🌐</emoji> <b><a href=\"{url}\">Bağlantı</a> için</b> <code>{class_name}</code>\n\n<emoji document_id=5188377234380954537>🌘</emoji> <code>{prefix}dlm {url}</code>\n\n{not_exact}",
    "file": "<emoji document_id=5433653135799228968>📁</emoji> <b>Dosya</b> <code>{class_name}</code>\n\n<emoji document_id=5188377234380954537>🌘</emoji> <code>{prefix}lm</code> <b>bu mesaja yanıt olarak yüklemek için</b>\n\n{not_exact}",
    "args": "<emoji document_id=5210952531676504517>❌</emoji> <b>Argümanlar belirtmelisiniz</b>",
    "_cmd_doc_ml": "<modül adı> - Modül bağlantısını gönder"
}

    strings_kk = {
    "404": "<emoji document_id=5210952531676504517>❌</emoji> <b>Модуль табылмады</b>",
    "not_exact": "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Толық сәйкес келетін нәтижелер табылмады, сондықтан ең жақын нәтиже көрсетіледі</b>",
    "link": "<emoji document_id=5280658777148760247>🌐</emoji> <b><a href=\"{url}\">Сілтеме</a> үшін</b> <code>{class_name}</code>\n\n<emoji document_id=5188377234380954537>🌘</emoji> <code>{prefix}dlm {url}</code>\n\n{not_exact}",
    "file": "<emoji document_id=5433653135799228968>📁</emoji> <b>Файл</b> <code>{class_name}</code>\n\n<emoji document_id=5188377234380954537>🌘</emoji> <code>{prefix}lm</code> <b>осы хабарламаны жауап болар енгізу үшін</b>\n\n{not_exact}",
    "args": "<emoji document_id=5210952531676504517>❌</emoji> <b>Аргументтерді көрсетуіңіз керек</b>",
    "_cmd_doc_ml": "<модуль атауы> - Модульге сілтеме жіберу"
}

    strings_it = {
    "404": "<emoji document_id=5210952531676504517>❌</emoji> <b>Modulo non trovato</b>",
    "not_exact": "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Nessuna corrispondenza esatta trovata, quindi viene visualizzato il risultato più vicino</b>",
    "link": "<emoji document_id=5280658777148760247>🌐</emoji> <b><a href=\"{url}\">Collegamento</a> per</b> <code>{class_name}</code>\n\n<emoji document_id=5188377234380954537>🌘</emoji> <code>{prefix}dlm {url}</code>\n\n{not_exact}",
    "file": "<emoji document_id=5433653135799228968>📁</emoji> <b>File</b> <code>{class_name}</code>\n\n<emoji document_id=5188377234380954537>🌘</emoji> <code>{prefix}lm</code> <b>questo messaggio come risposta per installarlo</b>\n\n{not_exact}",
    "args": "<emoji document_id=5210952531676504517>❌</emoji> <b>È necessario specificare gli argomenti</b>",
    "_cmd_doc_ml": "<nome del modulo> - Invia il link al modulo"
}

    strings_fr = {
    "404": "<emoji document_id=5210952531676504517>❌</emoji> <b>Module introuvable</b>",
    "not_exact": "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Aucune correspondance exacte n'a été trouvée, le résultat le plus proche est donc affiché</b>",
    "link": "<emoji document_id=5280658777148760247>🌐</emoji> <b><a href=\"{url}\">Lien</a> vers</b> <code>{class_name}</code>\n\n<emoji document_id=5188377234380954537>🌘</emoji> <code>{prefix}dlm {url}</code>\n\n{not_exact}",
    "file": "<emoji document_id=5433653135799228968>📁</emoji> <b>Fichier</b> <code>{class_name}</code>\n\n<emoji document_id=5188377234380954537>🌘</emoji> <code>{prefix}lm</code> <b>en réponse à ce message pour l'installer</b>\n\n{not_exact}",
    "args": "<emoji document_id=5210952531676504517>❌</emoji> <b>Vous devez spécifier des arguments</b>",
    "_cmd_doc_ml": "<nom du module> - Envoyer le lien vers le module"
}

    strings_es = {
    "404": "<emoji document_id=5210952531676504517>❌</emoji> <b>Módulo no encontrado</b>",
    "not_exact": "<emoji document_id=5312383351217201533>⚠️</emoji> <b>No se ha encontrado una coincidencia exacta, por lo que se muestra el resultado más cercano</b>",
    "link": "<emoji document_id=5280658777148760247>🌐</emoji> <b><a href=\"{url}\">Enlace</a> de</b> <code>{class_name}</code>\n\n<emoji document_id=5188377234380954537>🌘</emoji> <code>{prefix}dlm {url}</code>\n\n{not_exact}",
    "file": "<emoji document_id=5433653135799228968>📁</emoji> <b>Archivo de</b> <code>{class_name}</code>\n\n<emoji document_id=5188377234380954537>🌘</emoji> <code>{prefix}lm</code> <b>en respuesta a este mensaje para instalar</b>\n\n{not_exact}",
    "args": "<emoji document_id=5210952531676504517>❌</emoji> <b>Debes especificar argumentos</b>",
    "_cmd_doc_ml": "<nombre del módulo> - Enviar enlace al módulo"
}

    strings_de = {
    "404": "<emoji document_id=5210952531676504517>❌</emoji> <b>Modul nicht gefunden</b>",
    "not_exact": "<emoji document_id=5312383351217201533>⚠️</emoji> <b>Es wurde keine exakte Übereinstimmung gefunden, daher wird stattdessen das nächstgelegene Ergebnis angezeigt</b>",
    "link": "<emoji document_id=5280658777148760247>🌐</emoji> <b><a href=\"{url}\">Link</a> zu</b> <code>{class_name}</code>\n\n<emoji document_id=5188377234380954537>🌘</emoji> <code>{prefix}dlm {url}</code>\n\n{not_exact}",
    "file": "<emoji document_id=5433653135799228968>📁</emoji> <b>Datei</b> <code>{class_name}</code>\n\n<emoji document_id=5188377234380954537>🌘</emoji> <code>{prefix}lm</code> <b>in Antwort auf diese Nachricht, um sie zu installieren</b>\n\n{not_exact}",
    "args": "<emoji document_id=5210952531676504517>❌</emoji> <b>Du musst Argumente angeben</b>",
    "_cmd_doc_ml": "<Modulname> - Send link to module"
}
    
    @loader.command()
    async def nmlcmd(self, message: Message):
        """send module via file"""
        if not (args := utils.get_args_raw(message)):
            await utils.answer(message, self.strings("args"))
            return

        exact = True
        if not (
            class_name := next(
                (
                    module.strings("name")
                    for module in self.allmodules.modules
                    if args.lower()
                    in {
                        module.strings("name").lower(),
                        module.__class__.__name__.lower(),
                    }
                ),
                None,
            )
        ):
            if not (
                class_name := next(
                    reversed(
                        sorted(
                            [
                                module.strings["name"].lower()
                                for module in self.allmodules.modules
                            ]
                            + [
                                module.__class__.__name__.lower()
                                for module in self.allmodules.modules
                            ],
                            key=lambda x: difflib.SequenceMatcher(
                                None,
                                args.lower(),
                                x,
                            ).ratio(),
                        )
                    ),
                    None,
                )
            ):
                await utils.answer(message, self.strings("404"))
                return

            exact = False

        try:
            module = self.lookup(class_name)
            sys_module = inspect.getmodule(module)
        except Exception:
            await utils.answer(message, self.strings("404"))
            return

        link = module.__origin__

        text = (
            f"<b>🧳 {utils.escape_html(class_name)}</b>"
            if not utils.check_url(link)
            else (
                f'📼 <b><a href="{link}">Link</a> for'
                f" {utils.escape_html(class_name)}:</b>"
                f' <code>{link}</code>\n\n{self.strings("not_exact") if not exact else ""}'
            )
        )

        text = (
            self.strings("link").format(
                class_name=utils.escape_html(class_name),
                url=link,
                not_exact=self.strings("not_exact") if not exact else "",
                prefix=utils.escape_html(self.get_prefix()),
            )
            if utils.check_url(link)
            else self.strings("file").format(
                class_name=utils.escape_html(class_name),
                not_exact=self.strings("not_exact") if not exact else "",
                prefix=utils.escape_html(self.get_prefix()),
            )
        )

        file = io.BytesIO(sys_module.__loader__.data)
        file.name = f"{class_name}.py"
        file.seek(0)

        await utils.answer_file(
            message,
            file,
            caption=text,
        )

    def _format_result(
        self,
        result: dict,
        query: str,
        no_translate: bool = False,
    ) -> str:
        commands = "\n".join(
            [
                f"▫️ <code>{utils.escape_html(self.get_prefix())}{utils.escape_html(cmd)}</code>:"
                f" <b>{utils.escape_html(cmd_doc)}</b>"
                for cmd, cmd_doc in result["module"]["commands"].items()
            ]
        )

        kwargs = {
            "name": utils.escape_html(result["module"]["name"]),
            "dev": utils.escape_html(result["module"]["dev"]),
            "commands": commands,
            "cls_doc": utils.escape_html(result["module"]["cls_doc"]),
            "mhash": result["module"]["hash"],
            "query": utils.escape_html(query),
            "prefix": utils.escape_html(self.get_prefix()),
        }

        strings = (
            self.strings.get("result", "en")
            if self.config["translate"] and not no_translate
            else self.strings("result")
        )

        text = strings.format(**kwargs)

        if len(text) > 2048:
            kwargs["commands"] = "..."
            text = strings.format(**kwargs)

        return text

    