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
# scope: hikka_only

from telethon.tl.types import Message
from .. import loader, utils

try:
    from dreamsrv import Server
except ImportError:
    Server = None

@loader.tds
class DreamSrvMod(loader.Module):
    """Управление Linux-сервером"""
    strings = {
        "name": "DreamSrv",
        "not_installed": "❌ <b>dreamsrv</b> не установлен.\nУстанови: <code>pip install dreamsrv</code>",
        "no_args": "❌ Укажи аргументы команды.",
    }

    strings_ru = {
        "_cmd_doc_scpu": "загрузка CPU, ядра, частота, температура",
        "_cmd_doc_smem": "память (RAM + Swap) и топ-5 процессов по памяти",
        "_cmd_doc_sdisk": "<путь> состояние диска (по умолчанию /)",
        "_cmd_doc_srun": "<команда> выполнить shell-команду на сервере",
        "_cmd_doc_ssys": "информация о системе (ОС, ядро, аптайм, юзеры)",
        "_cmd_doc_snet": "сеть: трафик, соединения, пинг до 1.1.1.1",
        "_cmd_doc_stop": "<N> топ-N процессов по CPU (по умолчанию 5)",
        "_cmd_doc_stopmem": "<N> топ-N процессов по памяти (по умолчанию 5)",
        "_cmd_doc_stail": "<файл> последние 50 строк файла",
        "_cmd_doc_skill": "<PID> убить процесс по PID",
        "_cls_doc": "Управление сервером из Telegram",
    }

    def __init__(self):
        self.s = Server() if Server else None

    def _guard(self, message: Message) -> bool:
        return self.s is not None

    @loader.command(ru_doc="загрузка CPU, ядра, частота, температура")
    async def scpu(self, message: Message):
        if not self._guard(message):
            return await utils.answer(message, self.strings("not_installed"))

        cpu = self.s.cpu
        freq = f"{cpu.freq:.0f} МГц" if cpu.freq else "н/д"
        temp = f"{cpu.temp:.1f}°C" if cpu.temp else "н/д"
        load_avg = cpu.load_avg
        avg = f"{load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}" if load_avg else "н/д"
        text = (
            "🧠 <b>CPU</b>\n"
            f"▪️ Загрузка: <code>{cpu.load}%</code>\n"
            f"▪️ Ядер: {cpu.count_physical} физ. / {cpu.count_logical} лог.\n"
            f"▪️ Частота: {freq}\n"
            f"▪️ Температура: {temp}\n"
            f"▪️ Load Avg: <code>{avg}</code>\n"
            f"▪️ Модель: <code>{cpu.model[:60]}</code>"
        )
        await utils.answer(message, text)

    @loader.command(ru_doc="память (RAM + Swap) и топ-5 процессов по памяти")
    async def smem(self, message: Message):
        if not self._guard(message):
            return await utils.answer(message, self.strings("not_installed"))
        mem = self.s.mem
        text = (
            "💾 <b>Память</b>\n"
            f"▪️ RAM: {mem.used_human} / {mem.total_human} (<code>{mem.percent}%</code>)\n"
            f"▪️ Доступно: {mem.available_human}\n"
            f"▪️ Swap: {mem.swap_used:.1f} / {mem.swap_total:.1f} MB "
            f"(<code>{mem.swap_percent}%</code>)\n\n"
            "<b>Топ-5 по памяти:</b>\n"
        )
        for p in self.s.processes.top_mem(5):
            text += f"▪️ <code>{p.pid:>6}</code> {p.name[:20]:<20} {p.mem:.1f}%\n"
        await utils.answer(message, text)

    @loader.command(ru_doc="<путь> состояние диска (по умолчанию /)")
    async def sdisk(self, message: Message):
        if not self._guard(message):
            return await utils.answer(message, self.strings("not_installed"))
        path = utils.get_args_raw(message) or "/"
        d = self.s.disk
        text = (
            f"💿 <b>Диск {path}</b>\n"
            f"▪️ Занято: {d.used_human(path)} / {d.total_human(path)}\n"
            f"▪️ Свободно: {d.free_human(path)}\n"
            f"▪️ Использование: <code>{d.percent(path):.1f}%</code>"
        )
        await utils.answer(message, text)

    @loader.command(ru_doc="<команда> выполнить shell-команду на сервере")
    async def srun(self, message: Message):
        if not self._guard(message):
            return await utils.answer(message, self.strings("not_installed"))
        cmd = utils.get_args_raw(message)
        if not cmd:
            return await utils.answer(message, self.strings("no_args"))
        r = self.s.run(cmd, timeout=30)
        out = (r.stdout or r.stderr or "<пусто>").strip()
        status = "✅" if r.ok else "❌"
        text = f"{status} <code>{cmd}</code>\n<pre>{out[:3500]}</pre>"
        await utils.answer(message, text)

    @loader.command(ru_doc="информация о системе (ОС, ядро, аптайм, юзеры)")
    async def ssys(self, message: Message):
        if not self._guard(message):
            return await utils.answer(message, self.strings("not_installed"))
        sys = self.s.system
        users = ", ".join(sys.users) if sys.users else "нет"
        text = (
            "🖥 <b>Система</b>\n"
            f"▪️ ОС: {sys.os_name}\n"
            f"▪️ Ядро: <code>{sys.kernel}</code> ({sys.arch})\n"
            f"▪️ Хост: <code>{sys.hostname}</code>\n"
            f"▪️ Виртуализация: {sys.virtualization}\n"
            f"▪️ Аптайм: {sys.uptime}\n"
            f"▪️ Python: <code>{sys.python}</code>\n"
            f"▪️ Юзеры: {users}"
        )
        await utils.answer(message, text)

    @loader.command(ru_doc="сеть: трафик, соединения, пинг до 1.1.1.1")
    async def snet(self, message: Message):
        if not self._guard(message):
            return await utils.answer(message, self.strings("not_installed"))
        net = self.s.net
        ping = await net.ping()
        ping_str = f"{ping:.1f} мс" if ping else "таймаут"
        text = (
            "🌐 <b>Сеть</b>\n"
            f"▪️ Пинг (1.1.1.1): <code>{ping_str}</code>\n"
            f"▪️ Отправлено: {net.sent_human}\n"
            f"▪️ Получено: {net.recv_human}\n"
            f"▪️ Активных соединений: {net.connections}"
        )
        await utils.answer(message, text)

    @loader.command(ru_doc="<N> топ-N процессов по CPU (по умолчанию 5)")
    async def stop(self, message: Message):
        if not self._guard(message):
            return await utils.answer(message, self.strings("not_installed"))
        arg = utils.get_args_raw(message)
        n = int(arg) if arg and arg.isdigit() else 5
        text = f"🔥 <b>Топ-{n} по CPU:</b>\n"
        for p in self.s.processes.top_cpu(n):
            text += f"▪️ <code>{p.pid:>6}</code> {p.name[:20]:<20} {p.cpu:.1f}%\n"
        await utils.answer(message, text)

    @loader.command(ru_doc="<N> топ-N процессов по памяти (по умолчанию 5)")
    async def stopmem(self, message: Message):
        if not self._guard(message):
            return await utils.answer(message, self.strings("not_installed"))
        arg = utils.get_args_raw(message)
        n = int(arg) if arg and arg.isdigit() else 5
        text = f"💾 <b>Топ-{n} по памяти:</b>\n"
        for p in self.s.processes.top_mem(n):
            text += f"▪️ <code>{p.pid:>6}</code> {p.name[:20]:<20} {p.mem:.1f}%\n"
        await utils.answer(message, text)

    @loader.command(ru_doc="<файл> последние 50 строк файла")
    async def stail(self, message: Message):
        if not self._guard(message):
            return await utils.answer(message, self.strings("not_installed"))

        path = utils.get_args_raw(message)
        if not path:
            return await utils.answer(message, self.strings("no_args"))

        content = self.s.files.tail(path, 50)
        if content is None:
            return await utils.answer(message, f"❌ Не удалось прочитать: <code>{path}</code>")

        await utils.answer(message, f"📄 <code>{path}</code>\n<pre>{content[:3500]}</pre>")

    @loader.command(ru_doc="<PID> убить процесс по PID")
    async def skill(self, message: Message):
        if not self._guard(message):
            return await utils.answer(message, self.strings("not_installed"))

        arg = utils.get_args_raw(message)
        if not arg or not arg.isdigit():
            return await utils.answer(message, self.strings("no_args"))

        pid = int(arg)
        ok = self.s.processes.kill(pid)
        if ok:
            await utils.answer(message, f"✅ Процесс <code>{pid}</code> убит.")
        else:
            await utils.answer(message, f"❌ Не удалось убить процесс <code>{pid}</code>.")
