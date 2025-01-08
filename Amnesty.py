version = (1, 0, 0)

# meta developer: @RUIS_VlP

from telethon import functions, TelegramClient
from telethon.tl.types import Message, ChannelParticipantsKicked, ChatBannedRights
import time
from .. import loader, utils
import typing
from telethon.errors import ChatAdminRequiredError, UserAdminInvalidError

def seq_rights(sequence: str, inv: bool = False) -> typing.Union[dict, None]:
    if not sequence:
        return None

    result = {}

    for right in sequence:
        if right == '0':
            result['view_messages'] = not inv
        elif right == '1':
            result['send_messages'] = not inv
        elif right == '2':
            result['send_media'] = not inv
        elif right == '3':
            result['send_stickers'] = not inv
        elif right == '4':
            result['send_gifs'] = not inv
        elif right == '5':
            result['send_games'] = not inv
        elif right == '6':
            result['send_inline'] = not inv
        elif right == '7':
            result['embed_link_previews'] = not inv
        elif right == '8':
            result['send_polls'] = not inv
        elif right == '9':
            result['change_info'] = not inv
        elif right == 'a':
            result['invite_users'] = not inv
        elif right == 'b':
            result['pin_messages'] = not inv
        else:
            raise ValueError(f'Unknown right: {right}')

    return result

@loader.tds
class AmnestyMod(loader.Module):
    """Модуль для разбана всех пользователей в чате"""

    strings = {
        "name": "Amnesty",
    }
        
    @loader.command()
    async def amnestycmd(self, message):
        """ - разблокирует всех"""
        try:
        	chat_id = message.chat.id
        except:
        	await utils.answer(message, "🚫 <b>Команда доступна только в супергруппах и каналах!</b>")
        	return
        chat = await message.client.get_participants(chat_id, filter=ChannelParticipantsKicked)
        ids = [user.id for user in chat]
        i = 0
        for id in ids:
        	try:
        		await self.client.edit_permissions(chat_id, id, None, **seq_rights('0'),)
        	except ChatAdminRequiredError:
        		return await utils.answer(message, "🚫 <b> Недостаточно прав! </b>")
        	except UserAdminInvalidError:
        		return await utils.answer(message, "🚫 <b> Недостаточно прав! </b>")
        	except Exception as e:
        		return await utils.answer(message, "🚫 <b> Ошибка! </b>\n\n<code>{e}</code>")
        	await utils.answer(message, f"♻️ <b>Разбанено пользователей: {i + 1}/{int(len(ids))}</b>")
        	i += 1
        	time.sleep(1)
        await utils.answer(message, f"✅ <b>Успешно! {int(len(ids))} пользователей разблокировано!</b>")