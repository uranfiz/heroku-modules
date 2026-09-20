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

from random import choice
from telethon.tl.types import Message
from telethon.utils import get_display_name
from .. import loader, utils
from ..inline.types import InlineCall

MOVES = ["rock", "scissors", "paper"]
EMOJI = {"rock": "🪨", "scissors": "✂️", "paper": "📄"}
BEATS = {"rock": "scissors", "scissors": "paper", "paper": "rock"}

def result(a: str, b: str) -> str:
    if a == b:
        return "draw"
    return "a" if BEATS[a] == b else "b"

@loader.tds
class RPSMod(loader.Module):
    """Камень, ножницы, бумага"""

    strings = {
        "name": "RPS",
        "start": "Ожидание второго игрока...",
        "start_ai": "Игра против бота. Готов?",
        "discarded": "Игра отменена",
        "not_your_game": "Это не твоя игра",
        "not_your_turn": "Не твой ход",
        "already": "Ты уже выбрал",
        "choose": "Выбери ход:",
        "vs": "Игра с <b>{}</b>",
        "turn": "Ходит <b>{}</b>",
        "score": "Счёт: <b>{}</b> {s1} : {s2} <b>{}</b>",
        "round": "Раунд {n}",
        "draw_round": "Ничья",
        "win_round": "Победил <b>{}</b>",
        "final_win": "Победитель: <b>{}</b> ({s1}:{s2})",
        "final_draw": "Ничья ({s1}:{s2})",
        "self": "Нельзя играть с собой",
        "_cmd_doc_rps": "Играть с другим игроком",
        "_cmd_doc_rpsai": "Играть с ботом",
        "_cls_doc": "Камень, ножницы, бумага",
    }

    strings_ru = {
        "start": "Ожидание второго игрока...",
        "start_ai": "Игра против бота. Готов?",
        "discarded": "Игра отменена",
        "not_your_game": "Это не твоя игра",
        "not_your_turn": "Не твой ход",
        "already": "Ты уже выбрал",
        "choose": "Выбери ход:",
        "vs": "Игра с <b>{}</b>",
        "turn": "Ходит <b>{}</b>",
        "score": "Счёт: <b>{}</b> {s1} : {s2} <b>{}</b>",
        "round": "Раунд {n}",
        "draw_round": "Ничья",
        "win_round": "Победил <b>{}</b>",
        "final_win": "Победитель: <b>{}</b> ({s1}:{s2})",
        "final_draw": "Ничья ({s1}:{s2})",
        "self": "Нельзя играть с собой",
        "_cmd_doc_rps": "Играть с другим игроком",
        "_cmd_doc_rpsai": "Играть с ботом",
        "_cls_doc": "Камень, ножницы, бумага",
    }

    WIN = 3

    async def client_ready(self, client, db):
        self._games = {}
        self._me = await client.get_me()

    def _kb(self, cb, uid, owner=None):
        if owner is None:
            return [
                [
                    {"text": "🪨", "callback": cb, "args": (uid, "rock")},
                    {"text": "✂️", "callback": cb, "args": (uid, "scissors")},
                    {"text": "📄", "callback": cb, "args": (uid, "paper")},
                ]
            ]
        return [
            [
                {"text": "🪨", "callback": cb, "args": (uid, "rock", owner)},
                {"text": "✂️", "callback": cb, "args": (uid, "scissors", owner)},
                {"text": "📄", "callback": cb, "args": (uid, "paper", owner)},
            ]
        ]

    async def inline__start(self, call: InlineCall):
        if call.from_user.id == self._me.id:
            await call.answer(self.strings("self"))
            return

        uid = call.form["uid"]
        first = choice([call.from_user.id, self._me.id])
        self._games[uid] = {
            "mode": "pvp",
            "p2": call.from_user.id,
            "turn": first,
            "name1": utils.escape_html(get_display_name(self._me)),
            "name2": utils.escape_html(
                get_display_name(await self._client.get_entity(call.from_user.id))
            ),
            "s1": 0,
            "s2": 0,
            "c1": None,
            "c2": None,
            "round": 1,
        }
        await call.edit(**self._render(uid))

    def _render(self, uid):
        if uid not in self._games or uid not in self.inline._units:
            return {"text": self.strings("discarded")}

        g = self._games[uid]
        turn_name = g["name1"] if g["turn"] == self._me.id else g["name2"]
        text = (
            f"{self.strings('vs').format(g['name2'])}\n"
            f"{self.strings('round').format(n=g['round'])}\n"
            f"{self.strings('score').format(g['name1'], g['name2'], s1=g['s1'], s2=g['s2'])}\n"
            f"{self.strings('turn').format(turn_name)}\n"
            f"{self.strings('choose')}"
        )
        return {
            "text": text,
            "reply_markup": self._kb(self._click, uid, self._me.id)
            + self._kb(self._click, uid, g["p2"]),
        }

    async def _click(self, call: InlineCall, uid, move, owner):
        if uid not in self._games:
            await call.answer(self.strings("discarded"))
            return
        g = self._games[uid]

        if call.from_user.id != owner:
            await call.answer(self.strings("not_your_game"))
            return
        if call.from_user.id != g["turn"]:
            await call.answer(self.strings("not_your_turn"))
            return

        if call.from_user.id == self._me.id:
            if g["c1"] is not None:
                await call.answer(self.strings("already"))
                return
            g["c1"] = move
        else:
            if g["c2"] is not None:
                await call.answer(self.strings("already"))
                return
            g["c2"] = move

        if g["c1"] and g["c2"]:
            await self._resolve(call, uid)
            return

        g["turn"] = self._me.id if call.from_user.id != self._me.id else g["p2"]
        await call.edit(**self._render(uid))

    async def _resolve(self, call, uid):
        g = self._games[uid]
        r = result(g["c1"], g["c2"])
        if r == "a":
            g["s1"] += 1
            line = self.strings("win_round").format(g["name1"])
        elif r == "b":
            g["s2"] += 1
            line = self.strings("win_round").format(g["name2"])
        else:
            line = self.strings("draw_round")

        head = (
            f"{EMOJI[g['c1']]} vs {EMOJI[g['c2']]}\n{line}\n"
            f"{self.strings('score').format(g['name1'], g['name2'], s1=g['s1'], s2=g['s2'])}"
        )

        if g["s1"] >= self.WIN or g["s2"] >= self.WIN:
            del self._games[uid]
            winner = g["name1"] if g["s1"] > g["s2"] else g["name2"]
            await call.edit(
                **{
                    "text": self.strings("final_win").format(
                        winner, s1=g["s1"], s2=g["s2"]
                    )
                }
            )
            return

        g["round"] += 1
        g["c1"] = None
        g["c2"] = None
        g["turn"] = choice([self._me.id, g["p2"]])
        turn_name = g["name1"] if g["turn"] == self._me.id else g["name2"]
        text = (
            f"{head}\n\n{self.strings('round').format(n=g['round'])}\n"
            f"{self.strings('turn').format(turn_name)}\n{self.strings('choose')}"
        )
        await call.edit(
            text=text,
            reply_markup=self._kb(self._click, uid, self._me.id)
            + self._kb(self._click, uid, g["p2"]),
        )

    async def rpscmd(self, message: Message):
        """играть с другим игроком"""
        await self.inline.form(
            self.strings("start"),
            message=message,
            reply_markup={"text": "Начать", "callback": self.inline__start},
            ttl=900,
            disable_security=True,
        )

    async def inline__start_ai(self, call: InlineCall):
        uid = call.form["uid"]
        user = await self._client.get_entity(call.from_user.id)
        self._games[uid] = {
            "mode": "ai",
            "user": user.id,
            "name": utils.escape_html(get_display_name(user)),
            "s1": 0,
            "s2": 0,
            "round": 1,
        }
        await call.edit(**self._render_ai(uid))

    def _render_ai(self, uid):
        if uid not in self._games or uid not in self.inline._units:
            return {"text": self.strings("discarded")}
        g = self._games[uid]
        text = (
            f"{self.strings('round').format(n=g['round'])}\n"
            f"{self.strings('score').format(g['name'], 'Бот', s1=g['s1'], s2=g['s2'])}\n"
            f"{self.strings('choose')}"
        )
        return {
            "text": text,
            "reply_markup": self._kb(self._click_ai, uid),
        }

    async def _click_ai(self, call: InlineCall, uid, move):
        if uid not in self._games:
            await call.answer(self.strings("discarded"))
            return
        g = self._games[uid]

        if call.from_user.id != g["user"]:
            await call.answer(self.strings("not_your_game"))
            return

        ai = choice(MOVES)
        r = result(move, ai)

        if r == "a":
            g["s1"] += 1
            line = self.strings("win_round").format(g["name"])
        elif r == "b":
            g["s2"] += 1
            line = self.strings("win_round").format("Бот")
        else:
            line = self.strings("draw_round")

        head = (
            f"{EMOJI[move]} vs {EMOJI[ai]}\n{line}\n"
            f"{self.strings('score').format(g['name'], 'Бот', s1=g['s1'], s2=g['s2'])}"
        )

        if g["s1"] >= self.WIN or g["s2"] >= self.WIN:
            del self._games[uid]
            if g["s1"] > g["s2"]:
                text = self.strings("final_win").format(g["name"], s1=g["s1"], s2=g["s2"])
            else:
                text = self.strings("final_win").format("Бот", s1=g["s2"], s2=g["s1"])
            await call.edit(**{"text": text})
            return

        g["round"] += 1
        text = f"{head}\n\n{self.strings('round').format(n=g['round'])}\n{self.strings('choose')}"
        await call.edit(
            text=text,
            reply_markup=self._kb(self._click_ai, uid),
        )

    async def rpsaicmd(self, message: Message):
        """Играть с ботом"""
        await self.inline.form(
            self.strings("start_ai"),
            message=message,
            reply_markup={"text": "Начать", "callback": self.inline__start_ai},
            ttl=900,
            disable_security=True,
        )
