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

def _load_emoji(percent: float) -> str:
    if percent >= 90:
        return '<tg-emoji emoji-id=5337017423906226569>🔴</tg-emoji>'
    if percent >= 70:
        return '<tg-emoji emoji-id=5336936725765700868>🟠</tg-emoji>'
    if percent >= 40:
        return '<tg-emoji emoji-id=5339082633160703625>🟡</tg-emoji>'
    return '<tg-emoji emoji-id=5339112148175959615>🟢</tg-emoji>'

CPU_EMOJI = '<tg-emoji emoji-id=5839001351647925500>🤩</tg-emoji>'
RAM_EMOJI = '<tg-emoji emoji-id=5803401351278892713>💻</tg-emoji>'
NET_EMOJI = '<tg-emoji emoji-id=5776233299424843260>🌐</tg-emoji>'
DISK_EMOJI = '<tg-emoji emoji-id=5352736961259913125>💿</tg-emoji>'
SYS_EMOJI = '<tg-emoji emoji-id=5199762015861627963>⚠️</tg-emoji>'
TOP_EMOJI = '<tg-emoji emoji-id=5462900531645154669>☝️</tg-emoji>'
TAIL_EMOJI = '<tg-emoji emoji-id=5199628777386172358>⚠️</tg-emoji>'

@loader.tds
class DreamSrvMod(loader.Module):
    """Управление Linux-сервером"""
    strings = {
        "name": "DreamSrv",
        "not_installed": "❌ <b>dreamsrv</b> не установлен.\nУстанови: <code>pip install dreamsrv</code>",
        "no_args": "❌ Укажи аргументы команды.",
    }

    strings_ru = {
        "_cmd_doc_dscpu": "загрузка CPU, ядра, частота, температура",
        "_cmd_doc_dsmem": "память (RAM + Swap) и топ-5 процессов по памяти",
        "_cmd_doc_dsdisk": "<путь> состояние диска (по умолчанию /)",
        "_cmd_doc_dsrun": "<команда> выполнить shell-команду на сервере",
        "_cmd_doc_dssys": "информация о системе (ОС, ядро, аптайм, юзеры)",
        "_cmd_doc_dsnet": "сеть: трафик, соединения, пинг до 1.1.1.1",
        "_cmd_doc_dsstop": "<N> топ-N процессов по CPU (по умолчанию 5)",
        "_cmd_doc_dstopmem": "<N> топ-N процессов по памяти (по умолчанию 5)",
        "_cmd_doc_dstail": "<файл> последние 50 строк файла",
        "_cmd_doc_dskill": "<PID> убить процесс по PID",
        "_cmd_doc_dsall": "вся информация о сервере одним сообщением",
        "_cls_doc": "Управление сервером",
    }

    def __init__(self):
        self.s = Server() if Server else None

    def _guard(self, message: Message) -> bool:
        return self.s is not None

    @loader.command(ru_doc="загрузка CPU, ядра, частота, температура")
    async def dscpu(self, message: Message):
        if not self._guard(message):
            return await utils.answer(message, self.strings("not_installed"))

        cpu = self.s.cpu
        freq = f"{cpu.freq:.0f} МГц" if cpu.freq else "н/д"
        temp = f"{cpu.temp:.1f}°C" if cpu.temp else "н/д"
        load_avg = cpu.load_avg
        avg = f"{load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}" if load_avg else "н/д"
        emoji = _load_emoji(cpu.load)
        text = (
            f"{CPU_EMOJI} <b>CPU</b> {emoji}\n"
            f"Загрузка: <code>{cpu.load}%</code>\n"
            f"Ядер: {cpu.count_physical} физ. / {cpu.count_logical} лог.\n"
            f"Частота: {freq}\n"
            f"Температура: {temp}\n"
            f"Load Avg: <code>{avg}</code>\n"
            f"Модель: <code>{cpu.model[:60]}</code>"
        )
        await utils.answer(message, text)

    @loader.command(ru_doc="память (RAM + Swap) и топ-5 процессов по памяти")
    async def dsmem(self, message: Message):
        if not self._guard(message):
            return await utils.answer(message, self.strings("not_installed"))
        mem = self.s.mem
        emoji = _load_emoji(mem.percent)
        text = (
            f"{RAM_EMOJI} <b>Память</b> {emoji}\n"
            f"RAM: {mem.used_human} / {mem.total_human} (<code>{mem.percent}%</code>)\n"
            f"Доступно: {mem.available_human}\n"
            f"Swap: {mem.swap_used:.1f} / {mem.swap_total:.1f} MB "
            f"(<code>{mem.swap_percent}%</code>)\n\n"
            "<b>Топ-5 по памяти:</b>\n"
        )
        for p in self.s.processes.top_mem(5):
            text += f"<code>{p.pid:>6}</code> {p.name[:20]:<20} {p.mem:.1f}%\n"
        await utils.answer(message, text)

    @loader.command(ru_doc="<путь> состояние диска (по умолчанию /)")
    async def dsdisk(self, message: Message):
        if not self._guard(message):
            return await utils.answer(message, self.strings("not_installed"))
        path = utils.get_args_raw(message) or "/"
        d = self.s.disk
        percent = d.percent(path)
        emoji = _load_emoji(percent)
        text = (
            f"{DISK_EMOJI} <b>Диск {path}</b> {emoji}\n"
            f"Занято: {d.used_human(path)} / {d.total_human(path)}\n"
            f"Свободно: {d.free_human(path)}\n"
            f"Использование: <code>{percent:.1f}%</code>"
        )
        await utils.answer(message, text)

    @loader.command(ru_doc="<команда> выполнить shell-команду на сервере")
    async def dsrun(self, message: Message):
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
    async def dssys(self, message: Message):
        if not self._guard(message):
            return await utils.answer(message, self.strings("not_installed"))
        sys = self.s.system
        users = ", ".join(sys.users) if sys.users else "нет"
        text = (
            f"{SYS_EMOJI} <b>Система</b>\n"
            f"ОС: {sys.os_name}\n"
            f"Ядро: <code>{sys.kernel}</code> ({sys.arch})\n"
            f"Хост: <code>{sys.hostname}</code>\n"
            f"Виртуализация: {sys.virtualization}\n"
            f"Аптайм: {sys.uptime}\n"
            f"Python: <code>{sys.python}</code>\n"
            f"Юзеры: {users}"
        )
        await utils.answer(message, text)

    @loader.command(ru_doc="сеть: трафик, соединения, пинг до 1.1.1.1")
    async def dsnet(self, message: Message):
        if not self._guard(message):
            return await utils.answer(message, self.strings("not_installed"))
        net = self.s.net
        ping = await net.ping()
        ping_str = f"{ping:.1f} мс" if ping else "таймаут"
        text = (
            f"{NET_EMOJI} <b>Сеть</b>\n"
            f"Пинг (1.1.1.1): <code>{ping_str}</code>\n"
            f"Отправлено: {net.sent_human}\n"
            f"Получено: {net.recv_human}\n"
            f"Активных соединений: {net.connections}"
        )
        await utils.answer(message, text)

    @loader.command(ru_doc="<N> топ-N процессов по CPU (по умолчанию 5)")
    async def dsstop(self, message: Message):
        if not self._guard(message):
            return await utils.answer(message, self.strings("not_installed"))
        arg = utils.get_args_raw(message)
        n = int(arg) if arg and arg.isdigit() else 5
        text = f"{TOP_EMOJI} <b>Топ-{n} по CPU:</b>\n"
        for p in self.s.processes.top_cpu(n):
            text += f"<code>{p.pid:>6}</code> {p.name[:20]:<20} {p.cpu:.1f}%\n"
        await utils.answer(message, text)

    @loader.command(ru_doc="<N> топ-N процессов по памяти (по умолчанию 5)")
    async def dstopmem(self, message: Message):
        if not self._guard(message):
            return await utils.answer(message, self.strings("not_installed"))
        arg = utils.get_args_raw(message)
        n = int(arg) if arg and arg.isdigit() else 5
        text = f"{RAM_EMOJI} <b>Топ-{n} по памяти:</b>\n"
        for p in self.s.processes.top_mem(n):
            text += f"<code>{p.pid:>6}</code> {p.name[:20]:<20} {p.mem:.1f}%\n"
        await utils.answer(message, text)

    @loader.command(ru_doc="<файл> последние 50 строк файла")
    async def dstail(self, message: Message):
        if not self._guard(message):
            return await utils.answer(message, self.strings("not_installed"))
        path = utils.get_args_raw(message)
        if not path:
            return await utils.answer(message, self.strings("no_args"))
        content = self.s.files.tail(path, 50)
        if content is None:
            return await utils.answer(message, f"❌ Не удалось прочитать: <code>{path}</code>")
        await utils.answer(message, f"{TAIL_EMOJI} <code>{path}</code>\n<pre>{content[:3500]}</pre>")

    @loader.command(ru_doc="<PID> убить процесс по PID")
    async def dskill(self, message: Message):
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

    @loader.command(ru_doc="вся информация о сервере одним сообщением")
    async def dsall(self, message: Message):
        if not self._guard(message):
            return await utils.answer(message, self.strings("not_installed"))
        cpu = self.s.cpu
        mem = self.s.mem
        sys = self.s.system
        net = self.s.net
        disk = self.s.disk
        cpu_emoji = _load_emoji(cpu.load)
        freq = f"{cpu.freq:.0f} МГц" if cpu.freq else "н/д"
        temp = f"{cpu.temp:.1f}°C" if cpu.temp else "н/д"
        load_avg = cpu.load_avg
        avg = f"{load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}" if load_avg else "н/д"
        ram_emoji = _load_emoji(mem.percent)
        disk_percent = disk.percent("/")
        disk_emoji = _load_emoji(disk_percent)
        ping = await net.ping()
        ping_str = f"{ping:.1f} мс" if ping else "таймаут"
        users = ", ".join(sys.users) if sys.users else "нет"
        top_cpu = self.s.processes.top_cpu(3)
        top_mem = self.s.processes.top_mem(3)

        text = (
            f"<blockquote expandable>{CPU_EMOJI} <b>CPU</b> {cpu_emoji}\n"
            f"Загрузка: <code>{cpu.load}%</code>\n"
            f"Ядер: {cpu.count_physical} физ. / {cpu.count_logical} лог.\n"
            f"Частота: {freq}\n"
            f"Температура: {temp}\n"
            f"Load Avg: <code>{avg}</code>\n"
            f"Модель: <code>{cpu.model[:60]}</code>\n\n"

            f"{RAM_EMOJI} <b>Память</b> {ram_emoji}\n"
            f"RAM: {mem.used_human} / {mem.total_human} (<code>{mem.percent}%</code>)\n"
            f"Доступно: {mem.available_human}\n"
            f"Swap: {mem.swap_used:.1f} / {mem.swap_total:.1f} MB "
            f"(<code>{mem.swap_percent}%</code>)\n\n"

            f"{DISK_EMOJI} <b>Диск /</b> {disk_emoji}\n"
            f"Занято: {disk.used_human('/')} / {disk.total_human('/')}\n"
            f"Свободно: {disk.free_human('/')}\n"
            f"Использование: <code>{disk_percent:.1f}%</code>\n\n"

            f"{NET_EMOJI} <b>Сеть</b>\n"
            f"Пинг (1.1.1.1): <code>{ping_str}</code>\n"
            f"Отправлено: {net.sent_human}\n"
            f"Получено: {net.recv_human}\n"
            f"Активных соединений: {net.connections}\n\n"

            f"{SYS_EMOJI} <b>Система</b>\n"
            f"ОС: {sys.os_name}\n"
            f"Ядро: <code>{sys.kernel}</code> ({sys.arch})\n"
            f"Хост: <code>{sys.hostname}</code>\n"
            f"Виртуализация: {sys.virtualization}\n"
            f"Аптайм: {sys.uptime}\n"
            f"Python: <code>{sys.python}</code>\n"
            f"Юзеры: {users}</blockquote>\n\n"
        )

        text += f"<blockquote expandable>{TOP_EMOJI} <b>Топ-3 по CPU:</b>\n"
        for p in top_cpu:
            text += f"<code>{p.pid:>6}</code> {p.name[:20]:<20} {p.cpu:.1f}%\n"

        text += f"\n{RAM_EMOJI} <b>Топ-3 по памяти:</b>\n"
        for p in top_mem:
            text += f"<code>{p.pid:>6}</code> {p.name[:20]:<20} {p.mem:.1f}%\n"
        text += "</blockquote>"

        await utils.answer(message, text)
