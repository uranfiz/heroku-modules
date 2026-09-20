# +-------------------------------------------------------------------+
# |  [!] LICENSE NOTICE                                               |
# |                                                                   |
# |  Author : Dream (https://t.me/devuranium)                         |
# |  Rights : (c) 2026 Dream. All rights reserved.                    |
# |  License: GNU Affero General Public License v3.0 (AGPL-3.0)       |
# |           https://www.gnu.org/licenses/agpl-3.0.html              |
# |                                                                   |
# |  You may use, modify and distribute this code, including for      |
# |  commercial purposes, BUT any derivative work MUST be released    |
# |  under the same AGPL-3.0 license, with attribution to the         |
# |  original author. If you run a modified version as a network      |
# |  service, you MUST publish its full source code.                  |
# +-------------------------------------------------------------------+

__version__ = (1, 2, 3)
# meta developer: @devuranium
# meta banner: https://bannermods1.yuehost.xyz/photoreader_banner.jpg
# meta pic: https://bannermods1.yuehost.xyz/photoreader_banner.jpg

import asyncio
import io
import html
import re
from asyncio import sleep
from os import remove

from telethon import errors, functions
from telethon.errors import (
    BotGroupsBlockedError,
    ChannelPrivateError,
    ChatAdminRequiredError,
    ChatWriteForbiddenError,
    InputUserDeactivatedError,
    MessageTooLongError,
    UserAlreadyParticipantError,
    UserBlockedError,
    UserIdInvalidError,
    UserKickedError,
    UserNotMutualContactError,
    UserPrivacyRestrictedError,
    YouBlockedUserError,
)
from telethon.tl.functions.channels import InviteToChannelRequest, LeaveChannelRequest
from telethon.tl.functions.messages import AddChatUserRequest, GetCommonChatsRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import (
    ChannelParticipantCreator,
    ChannelParticipantsAdmins,
    ChannelParticipantsBots,
)

from .. import loader, utils

def safe_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'[\u064B-\u065F]', '', text)
    text = re.sub(r'[\u200b-\u200d\u2060\ufeff\u200e\u200f\u202a-\u202e]', '', text)
    clean = text.encode('utf-16', 'surrogatepass').decode('utf-16', 'ignore')
    return html.escape(clean)

@loader.tds
class Userid(loader.Module):
    """id пользователя и чата"""
    strings = {"name": "Userid"}

    async def client_ready(self, client, db):
        self.db = db

    async def udcmd(self, message):
        """команда .ud <@ или реплей>"""
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()

        try:
            if args:
                user = await message.client.get_entity(
                    int(args) if args.isdigit() else args
                )
            elif reply:
                user = await message.client.get_entity(reply.sender_id)
            else:
                user = await message.client.get_entity(message.sender_id)
        except ValueError:
            user = await message.client.get_entity(message.sender_id)

        first_name = user.first_name or ""
        last_name = user.last_name or ""
        
        full_name = f"{first_name} {last_name}".strip()
        full_name = safe_text(full_name)
        if not full_name:
            full_name = "Нет имени"
        
        username_list = []
        if hasattr(user, 'usernames') and user.usernames:
            for u in user.usernames:
                if getattr(u, 'active', True):
                    safe_u = safe_text(f"@{u.username}")
                    username_list.append(f"<code>{safe_u}</code>")
        elif user.username:
            safe_u = safe_text(f"@{user.username}")
            username_list.append(f"<code>{safe_u}</code>")
            
        if username_list:
            username_string = ", ".join(username_list)
        else:
            username_string = f"<code>Нет юзернейма</code>"
        result = (
            f"<blockquote>"
            f"<emoji document_id=5309901482890382924>👤</emoji> <code>{full_name}</code>\n"
            f"<emoji document_id=5312018068543657325>🐶</emoji> {username_string}\n"
            f"<emoji document_id=5310024172926161438>🆔</emoji> <code>{user.id}</code>"
            f"</blockquote>"
        )
        await message.edit(result)

    async def chatidcmd(self, message):
        """команда .chatid - получить ID чата"""
        chat = await message.get_chat()
        chat_title = getattr(chat, 'title', 'ЛС / Приватный чат') or 'ЛС / Приватный чат'
        chat_title = safe_text(chat_title)
        
        if hasattr(message.peer_id, 'channel_id'):
            chat_id = f"-100{message.peer_id.channel_id}"
        elif hasattr(message.peer_id, 'chat_id'):
            chat_id = f"-{message.peer_id.chat_id}"
        elif hasattr(message.peer_id, 'user_id'):
            chat_id = f"{message.peer_id.user_id}"
        else:
            chat_id = "Не удалось получить ID"
            
        result = (
            f"<blockquote>"
            f"<emoji document_id=5309844291105869907>👥</emoji> <code>{chat_title}</code>\n"
            f"<emoji document_id=5310011257959508085>✉️</emoji> <code>{chat_id}</code>"
            f"</blockquote>"
        )
        
        await utils.answer(message, result)
