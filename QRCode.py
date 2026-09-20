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
# meta desc: генерация QR-кода из текста/ссылки и распознавание QR с фото
# requires: qrcode[pil] pillow pyzbar

import io
import html
import re
import asyncio
from .. import loader, utils

def safe_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r'[\u200b-\u200d\u2060\ufeff\u200e\u200f\u202a-\u202e]', '', text)
    return html.escape(text)

@loader.tds
class QRCodeMod(loader.Module):
    """генерация QR-кода и распознавание QR с фото"""

    strings = {
        "name": "QRCode",
        "no_input": "🚫 Укажи текст/ссылку или ответь на сообщение с текстом.",
        "generating": "🖼 Генерирую QR-код...",
        "gen_error": "⚠️ Не удалось сгенерировать QR: <code>{}</code>",
        "no_photo": "🚫 Нужен реплей на фото с QR-кодом.",
        "recognizing": "🔍 Ищу QR-код на фото...",
        "not_found": "🤷 QR-код на фото не найден.",
        "found": "<emoji document_id=5309901482890382924>📄</emoji> <b>Найдено кодов: {}</b>\n\n",
        "found_item": "<b>{i}.</b> <code>{data}</code>\n",
        "download_error": "⚠️ Не удалось скачать фото: <code>{}</code>",
        "decode_error": "⚠️ Ошибка распознавания: <code>{}</code>",
    }

    strings_ru = {
        "_cmd_doc_qr": "<текст|реплей> — сгенерировать QR-код",
        "_cmd_doc_qrscan": "<реплей на фото> — распознать QR-код",
        "_cls_doc": "Генерация QR-кодов и распознавание их с фото",
    }

    async def client_ready(self, client, db):
        self.db = db
        self._client = client
        try:
            from pyzbar import pyzbar
            self._pyzbar_ok = True
        except Exception:
            self._pyzbar_ok = False

    @loader.command(ru_doc="<текст|реплей> — сгенерировать QR-код")
    async def qr(self, message):
        """<текст|реплей> — сгенерировать QR-код"""
        args = utils.get_args_raw(message)
        reply_to_id = None

        if message.is_reply:
            reply = await message.get_reply_message()
            if reply:
                reply_to_id = reply.id
                if not args:
                    args = reply.raw_text

        if not args:
            await utils.answer(message, self.strings("no_input"))
            return

        await utils.answer(message, self.strings("generating"))

        def _make():
            import qrcode
            qr = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
            )
            qr.add_data(args)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            buf.name = f"qr_{message.id}.png"
            return buf

        try:
            buf = await asyncio.get_running_loop().run_in_executor(None, _make)
        except Exception as e:
            await utils.answer(
                message, self.strings("gen_error").format(safe_text(str(e)))
            )
            return

        await self._client.send_file(
            message.chat_id,
            buf,
            reply_to=reply_to_id,
        )

    @loader.command(ru_doc="<реплей на фото> — распознать QR-код")
    async def qrscan(self, message):
        """<реплей на фото> — распознать QR-код"""
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
            await utils.answer(message, self.strings("no_photo"))
            return

        if not self._pyzbar_ok:
            await utils.answer(
                message,
                "⚠️ <code>pyzbar</code> не установлен — распознавание недоступно.",
            )
            return

        await utils.answer(message, self.strings("recognizing"))

        try:
            buf = io.BytesIO()
            await target.download_media(buf)
            image_bytes = buf.getvalue()
        except Exception as e:
            await utils.answer(
                message,
                self.strings("download_error").format(safe_text(str(e))),
            )
            return

        def _decode():
            from PIL import Image
            from pyzbar.pyzbar import decode
            img = Image.open(io.BytesIO(image_bytes))
            results = decode(img)
            out = []
            for r in results:
                out.append({
                    "type": r.type,
                    "data": r.data.decode("utf-8", errors="replace"),
                })
            return out

        try:
            found = await asyncio.get_running_loop().run_in_executor(None, _decode)
        except Exception as e:
            await utils.answer(
                message,
                self.strings("decode_error").format(safe_text(str(e))),
            )
            return

        if not found:
            await utils.answer(message, self.strings("not_found"))
            return

        text = self.strings("found").format(len(found))
        for i, item in enumerate(found, 1):
            text += self.strings("found_item").format(
                i=i, data=safe_text(item["data"])
            )

        max_len = 3500
        if len(text) > max_len:
            text = text[:max_len] + "\n… (обрезано)"

        await utils.answer(
            message,
            text + "<blockquote expandable>готово</blockquote>",
        )
