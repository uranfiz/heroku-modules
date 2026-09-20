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
# meta banner: https://bannermods1.yuehost.xyz/tts_banner.jpg
# meta pic: https://bannermods1.yuehost.xyz/tts_icon.jpg
# scope: inline
# meta dependencies: edge-tts

import io
import edge_tts
from .. import loader, utils

VOICES = {
    # русс
    "dimka":     {"id": "ru-RU-DmitryNeural",   "desc": "Дмитрий (мужской)"},
    "dmitry":    {"id": "ru-RU-DmitryNeural",   "desc": "Дмитрий (мужской)"},
    "sveta":     {"id": "ru-RU-SvetlanaNeural", "desc": "Светлана (женский)"},
    "svetlana":  {"id": "ru-RU-SvetlanaNeural", "desc": "Светлана (женский)"},

    # англ
    "guy":       {"id": "en-US-GuyNeural",      "desc": "Guy (US, male)"},
    "aria":      {"id": "en-US-AriaNeural",     "desc": "Aria (US, female)"},
    "jenny":     {"id": "en-US-JennyNeural",    "desc": "Jenny (US, female)"},
    "ryan":      {"id": "en-GB-RyanNeural",     "desc": "Ryan (UK, male)"},
    "sonia":     {"id": "en-GB-SoniaNeural",    "desc": "Sonia (UK, female)"},
  
    "katya":     {"id": "de-DE-KatjaNeural",    "desc": "Katja (DE, female)"},
    "alain":     {"id": "fr-FR-AlainNeural",    "desc": "Alain (FR, male)"},
    "elvira":    {"id": "es-ES-ElviraNeural",   "desc": "Elvira (ES, female)"},
}

DEFAULT_VOICE = "ru-RU-DmitryNeural"
MAX_LEN = 1500

@loader.tds
class TTSModule(loader.Module):
    """Модуль для озвучки текста"""
    strings = {
        "name": "TTSNeural",
        "no_text": "<b>Укажите текст для озвучки или ответьте на сообщение!</b>",
        "processing": "<b>Озвучиваю текст...</b>",
        "voice_set": "<b>Голос изменен на:</b> <code>{}</code>",
        "rate_set": "<b>Скорость изменена на:</b> <code>{:+d}%</code>",
        "pitch_set": "<b>Тон изменен на:</b> <code>{:+d}Hz</code>",
        "volume_set": "<b>Громкость изменена на:</b> <code>{:+d}%</code>",
        "reset": "<b>Все настройки сброшены к значениям по умолчанию.</b>",
        "too_long": "<b>Текст слишком длинный (макс. {} символов).</b>",
        "cur_settings": (
            "<b>Текущие настройки:</b>\n"
            "• Голос: <code>{voice}</code> ({voice_desc})\n"
            "• Скорость: <code>{rate:+d}%</code>\n"
            "• Тон: <code>{pitch:+d}Hz</code>\n"
            "• Громкость: <code>{volume:+d}%</code>"
        ),
    }

    async def client_ready(self, client, db) -> None:
        self.db = db
        self.client = client
        defaults = {
            "voice": DEFAULT_VOICE,
            "rate": 0,
            "pitch": 0,
            "volume": 0,
        }
        for key, value in defaults.items():
            if self.db.get(self.strings["name"], key) is None:
                self.db.set(self.strings["name"], key, value)

    def _get_settings(self):
        return {
            "voice":  self.db.get(self.strings["name"], "voice",  DEFAULT_VOICE),
            "rate":   self.db.get(self.strings["name"], "rate",   0),
            "pitch":  self.db.get(self.strings["name"], "pitch",  0),
            "volume": self.db.get(self.strings["name"], "volume", 0),
        }

    def _voice_desc(self, voice_id: str) -> str:
        for v in VOICES.values():
            if v["id"] == voice_id:
                return v["desc"]
        return "custom"

    async def _synthesize(self, text: str, voice: str, rate: int, pitch: int, volume: int):
        communicate = edge_tts.Communicate(
            text,
            voice,
            rate=f"{rate:+d}%",
            pitch=f"{pitch:+d}Hz",
            volume=f"{volume:+d}%",
        )
        audio_data = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data.write(chunk["data"])
        audio_data.seek(0)
        audio_data.name = "voice.ogg"
        return audio_data

    async def audcmd(self, message):
        """Озвучить текст (по арг. или реплею)"""
        args = utils.get_args_raw(message)
        reply = await message.get_reply_message()

        if args:
            text_to_speak = args
        elif reply and reply.text:
            text_to_speak = reply.text
        elif reply and reply.message:
            text_to_speak = reply.message
        else:
            await utils.answer(message, self.strings["no_text"])
            return

        if len(text_to_speak) > MAX_LEN:
            await utils.answer(
                message,
                self.strings["too_long"].format(MAX_LEN),
            )
            return

        status = await utils.answer(message, self.strings["processing"])
        settings = self._get_settings()

        try:
            audio_data = await self._synthesize(
                text_to_speak,
                settings["voice"],
                settings["rate"],
                settings["pitch"],
                settings["volume"],
            )

            if isinstance(status, list):
                await status[0].delete()
            else:
                await status.delete()

            await self.client.send_file(
                message.peer_id,
                audio_data,
                voice_note=True,
                reply_to=reply.id if reply else None,
            )

        except Exception as e:
            await utils.answer(
                message,
                f"<b>Ошибка при генерации речи:</b> <code>{e}</code>",
            )

    async def setvoicecmd(self, message):
        """Установить голос: .setvoice <имя>"""
        args = utils.get_args_raw(message).strip().lower()

        if not args:
            lines = ["<b>Доступные голоса:</b>\n"]
            for key, v in VOICES.items():
                lines.append(f"• <code>setvoice {key}</code> — {v['desc']}")
            await utils.answer(message, "\n".join(lines))
            return

        if args in VOICES:
            voice_id = VOICES[args]["id"]
            self.db.set(self.strings["name"], "voice", voice_id)
            await utils.answer(
                message,
                self.strings["voice_set"].format(voice_id),
            )
        else:
            await utils.answer(
                message,
                f"<b>Голос <code>{args}</code> не найден. "
                f"Введи <code>setvoice</code> без аргументов для списка.</b>",
            )

    async def ratetypecmd(self, message):
        """Изменить скорость: .rate <+N или -N>"""
        await self._change_int_setting(message, "rate", -100, 200, "rate_set")

    async def pitchcmd(self, message):
        """Изменить тон: .pitch <+N или -N>"""
        await self._change_int_setting(message, "pitch", -100, 100, "pitch_set")

    async def volumecmd(self, message):
        """Изменить громкость: .volume <+N или -N>"""
        await self._change_int_setting(message, "volume", -100, 100, "volume_set")

    async def _change_int_setting(self, message, key: str, min_v: int, max_v: int, tmpl: str):
        args = utils.get_args_raw(message).strip()
        try:
            value = int(args)
        except ValueError:
            await utils.answer(
                message,
                f"<b>Укажи число, например:</b> <code>.{key} +20</code> "
                f"(диапазон {min_v}..{max_v})",
            )
            return

        value = max(min_v, min(max_v, value))
        self.db.set(self.strings["name"], key, value)
        await utils.answer(message, self.strings[tmpl].format(value))

    async def ttsresetcmd(self, message):
        """Сбросить все настройки TTS"""
        self.db.set(self.strings["name"], "voice", DEFAULT_VOICE)
        self.db.set(self.strings["name"], "rate", 0)
        self.db.set(self.strings["name"], "pitch", 0)
        self.db.set(self.strings["name"], "volume", 0)
        await utils.answer(message, self.strings["reset"])

    async def ttssettingscmd(self, message):
        """Показать текущие настройки TTS"""
        s = self._get_settings()
        await utils.answer(
            message,
            self.strings["cur_settings"].format(
                voice=s["voice"],
                voice_desc=self._voice_desc(s["voice"]),
                rate=s["rate"],
                pitch=s["pitch"],
                volume=s["volume"],
            ),
        )
