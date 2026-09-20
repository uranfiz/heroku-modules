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
# meta pic: https://bannermods1.yuehost.xyz/photoreader_icon.jpg
# meta desc: распознаёт текст с фото по реплею
# requires: pytesseract pillow aiohttp

import asyncio
import html
import io
import re
import aiohttp
from .. import loader, utils

def safe_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'[\u200b-\u200d\u2060\ufeff\u200e\u200f\u202a-\u202e]', '', text)
    return html.escape(text)

@loader.tds
class PhotoReader(loader.Module):
    """распознаёт текст с фото по реплею"""
    strings = {"name": "PhotoReader"}

    async def client_ready(self, client, db):
        self.db = db
        self._session = aiohttp.ClientSession()

        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            self._local_ok = True
        except Exception:
            self._local_ok = False
            try:
                await client.send_message(
                    "me",
                    "ℹ️ <b>PhotoReader</b>: локальный <code>tesseract</code> не найден.\n"
                    "модуль будет использовать онлайн-OCR.\n\n"
                    "для локального режима выполни на сервере:\n"
                    "<code>sudo apt install tesseract-ocr tesseract-ocr-rus</code>",
                )
            except Exception:
                pass

    async def on_unload(self):
        if getattr(self, "_session", None) and not self._session.closed:
            await self._session.close()

    async def _ocr_local(self, image_bytes: bytes):
        if not getattr(self, "_local_ok", False):
            return None

        def _run():
            import pytesseract
            from PIL import Image

            img = Image.open(io.BytesIO(image_bytes))
            try:
                return pytesseract.image_to_string(img, lang="rus+eng")
            except pytesseract.TesseractError:
                return pytesseract.image_to_string(img, lang="eng")

        try:
            return await asyncio.get_running_loop().run_in_executor(None, _run)
        except Exception:
            return None

    async def _ocr_online(self, image_bytes: bytes):
        try:
            form = aiohttp.FormData()
            form.add_field(
                "file",
                image_bytes,
                filename="image.jpg",
                content_type="image/jpeg",
            )
            form.add_field("language", "rus")
            form.add_field("isOverlayRequired", "false")
            form.add_field("OCREngine", "2")
            async with self._session.post(
                "https://api.ocr.space/parse/image",
                data=form,
                headers={"apikey": "helloworld"},
                timeout=aiohttp.ClientTimeout(total=60),
            ) as resp:
                data = await resp.json(content_type=None)
            if data.get("IsErroredOnProcessing"):
                err = data.get("ErrorMessage") or data.get("ErrorDetails")
                return f"⚠️ Ошибка OCR API: {err}"

            parsed = data.get("ParsedResults") or []
            if not parsed:
                return ""
            return parsed[0].get("ParsedText", "") or ""
        except Exception as e:
            return f"⚠️ Ошибка запроса OCR: {e}"

    @loader.command(ru_doc="Распознать текст на фото (по реплею или в самом сообщении)")
    async def read(self, message):
        """<реплей на фото> — распознать текст"""
        reply = await message.get_reply_message()
        target = reply or message
        has_photo = target and (
            target.photo
            or (
                target.document
                and (target.document.mime_type or "").startswith("image/")
            )
        )

        if not has_photo:
            await utils.answer(message, "🚫 Нужен реплей на фото или изображение.")
            return
            
        await utils.answer(message, "🔍 Распознаю текст...")
        try:
            buf = io.BytesIO()
            await target.download_media(buf)
            image_bytes = buf.getvalue()
        except Exception as e:
            await utils.answer(message, f"⚠️ Не удалось скачать фото: {e}")
            return

        text = await self._ocr_local(image_bytes)
        if text is None:
            text = await self._ocr_online(image_bytes)
        if isinstance(text, str) and text.startswith("⚠️"):
            await utils.answer(message, text)
            return
        text = (text or "").strip()
        if not text:
            await utils.answer(message, "🤷 Текст на фото не найден.")
            return
        text = safe_text(text)
        header = (
            "<emoji document_id=5309901482890382924>📄</emoji> "
            "<b>Распознанный текст:</b>\n\n"
        )
        max_len = 3500
        if len(text) > max_len:
            text = text[:max_len] + "\n… (обрезано)"
        await utils.answer(
            message,
            header + f"<blockquote expandable>{text}</blockquote>",
        )
