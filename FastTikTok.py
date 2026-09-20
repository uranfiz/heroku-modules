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
# scope: hikka_only

import os
import re
import asyncio
from telethon.tl.types import Message
from .. import loader, utils

@loader.tds
class FastTikTokMod(loader.Module):
    """Прямое скачивание видео и аудио из TikTok"""
    strings = {
        "name": "FastTikTok"
    }

    strings_ru = {
        "_cmd_doc_tt": "<ссылка> скачать видео из TikTok",
        "_cmd_doc_tta": "<ссылка> скачать аудио из TikTok",
        "_cls_doc": "Быстрое и прямое скачивание медиа из TikTok"
    }

    @loader.command(ru_doc="<ссылка> скачать видео из TikTok")
    async def tt(self, message: Message):
        await self._download(message, is_audio=False)

    @loader.command(ru_doc="<ссылка> скачать аудио из TikTok")
    async def tta(self, message: Message):
        await self._download(message, is_audio=True)

    async def _download(self, message: Message, is_audio: bool):
        args = utils.get_args_raw(message)
        reply_to_id = None

        if message.is_reply:
            reply = await message.get_reply_message()
            if reply:
                reply_to_id = reply.id
                if not args:
                    args = reply.raw_text

        if not args or "tiktok.com" not in args.lower():
            return
        chat_id = message.chat_id
        await message.delete()
        url_match = re.search(r'https?://[^\s]+', args)
        target_url = url_match.group(0) if url_match else args.strip()
        ext = "mp3" if is_audio else "mp4"
        file_path = f"/tmp/tt_{message.id}.{ext}"

        cmd = [
            "yt-dlp",
            "--no-warnings",
            "--no-playlist",
            "--impersonate", "chrome",
            "-o", file_path,
            target_url
        ]

        if is_audio:
            cmd.extend(["-x", "--audio-format", "mp3"])

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            if process.returncode != 0 or not os.path.exists(file_path):
                return

            await self._client.send_file(
                chat_id,
                file_path,
                reply_to=reply_to_id
            )

        except Exception:
            pass
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
