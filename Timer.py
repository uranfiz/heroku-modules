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

from asyncio import sleep
from .. import loader, utils

class Timer(loader.Module):
    """задержка появления текста"""
    strings = {"name": "Timer"}

    async def client_ready(self, client, db) -> None:
        if hasattr(self, "hikka"):
            return

        self.db = db
        self.client = client

    async def tecmd(self, message):
        """Задержка появления текста в текущем чате
        Формат: .te {задержка} {количество} {текст}
        """
        await self._send_timed_messages(message, use_current_chat=True)

    async def tucmd(self, message):
        """Задержка появления текста в указанном чате
        Формат: .tu {задержка} {количество} {чат} {текст}
        """
        await self._send_timed_messages(message, use_current_chat=False)

    async def _send_timed_messages(self, message, use_current_chat: bool):
        args = utils.get_args(message)
        if not args:
            self.db.set(self.strings["name"], "state", False)
            await utils.answer(message, "<b>Модуль остановлен!</b>")
            return
        
        try:
            time = float(args[0])
            if len(args) >= 2 and args[1].isdigit():
                count = int(args[1])
                text_start = 3 if not use_current_chat else 2
            else:
                count = float('inf')
                text_start = 2 if not use_current_chat else 1
            
            if time <= 0:
                await utils.answer(message, "<b>Задержка должна быть больше 0 секунд!</b>")
                return
            if count != float('inf') and count <= 0:
                await utils.answer(message, "<b>Количество сообщений должно быть больше 0!</b>")
                return
        except ValueError:
            await utils.answer(message, "<b>Введите корректную задержку (число)!</b>")
            return
        except IndexError:
            await utils.answer(message, "<b>Укажите задержку и текст!</b>")
            return

        parts = utils.get_args_raw(message).split()
        
        target_chat = None
        if not use_current_chat:
            if len(parts) < text_start:
                await utils.answer(message, "<b>Укажите чат назначения (username или ID) и текст!</b>")
                return
            
            chat_identifier = parts[text_start - 1]
            try:
                if chat_identifier.startswith('@'):
                    target_chat = await self.client.get_entity(chat_identifier)
                elif chat_identifier.lstrip('-').isdigit():
                    target_chat = await self.client.get_entity(int(chat_identifier))
                else:
                    await utils.answer(message, "<b>Неверный формат чата! Используйте @username или ID чата</b>")
                    return
            except Exception as e:
                await utils.answer(message, f"<b>Ошибка при получении чата: {e}</b>")
                return
            
            text_start += 1
        
        if len(parts) <= text_start:
            await utils.answer(message, "<b>Укажите текст для отображения!</b>")
            return
        
        text = ' '.join(parts[text_start:])
        
        if count == float('inf'):
            mode_text = f"<b>бесконечное количество</b> (интервал: {time}с)"
        else:
            mode_text = f"<b>{count} сообщений</b> (интервал: {time}с)"
        
        if use_current_chat:
            chat_info = "текущий чат"
        else:
            chat_info = f"чат {chat_identifier}"
        
        await utils.answer(
            message,
            (
                f"Модуль запущен!\n"
                f"Режим: {mode_text}\n"
                f"Чат: {chat_info}\n"
                f"Текст: {text}\n"
                f"Остановить: <code>.te</code>"
            ),
        )
        
        self.db.set(self.strings["name"], "state", True)
        sent_count = 0
        
        while self.db.get(self.strings["name"], "state"):
            try:
                if count != float('inf') and sent_count >= count:
                    await utils.answer(message, f"<b>Готово! Отправлено {count} сообщений в {chat_info}</b>")
                    self.db.set(self.strings["name"], "state", False)
                    break
                
                if use_current_chat:
                    await message.respond(text)
                else:
                    await self.client.send_message(target_chat, text)
                
                sent_count += 1
                await sleep(time)
            except Exception as e:
                await utils.answer(message, f"<b>Ошибка: {e}</b>")
                self.db.set(self.strings["name"], "state", False)
                break
