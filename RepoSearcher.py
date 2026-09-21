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

import aiohttp
from .. import loader, utils

@loader.tds
class RepoSearcher(loader.Module):
    """Поиск модулей по описанию в репозиториях GitHub"""
    strings = {"name": "RepoSearcher"}

    async def client_ready(self, client, db):
        self.db = db
        self.repos = self.db.get(self.strings["name"], "repos", [
            "uranfiz/heroku-modules"
        ])

    def _save_repos(self):
        self.db.set(self.strings["name"], "repos", self.repos)

    async def _fetch_repo_contents(self, session, repo: str):
        """Возвращает (tree, branch) для репозитория."""
        for branch in ("main", "master"):
            api_url = f"https://api.github.com/repos/{repo}/git/trees/{branch}?recursive=1"
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("tree", []), branch
        return [], "main"

    async def searchmodcmd(self, message):
        """<запрос> — найти модули по описанию в репозиториях"""
        query = utils.get_args_raw(message)
        if not query:
            await message.edit("<b>❌ Укажите поисковый запрос! Пример: <code>.searchmod id</code></b>")
            return

        await message.edit("<b>🔎 Ищу модули по репозиториям...</b>")
        found_modules = []
        async with aiohttp.ClientSession() as session:
            for repo in self.repos:
                tree, branch = await self._fetch_repo_contents(session, repo)
                if not tree:
                    continue

                py_files = [
                    item for item in tree
                    if item["path"].endswith(".py") and not item["path"].startswith(".")
                ]

                for file_info in py_files:
                    file_path = file_info["path"]
                    raw_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{file_path}"

                    async with session.get(raw_url) as resp:
                        if resp.status != 200:
                            continue
                        content = await resp.text()

                    lower_content = content.lower()
                    lower_query = query.lower()

                    if lower_query in lower_content:
                        mod_name = file_path.split("/")[-1]
                        description = "Описание не найдено"

                        lines = content.splitlines()
                        for i, line in enumerate(lines):
                            if "class " in line and "(loader.Module):" in line:
                                if i + 1 < len(lines):
                                    next_line = lines[i + 1].strip()
                                    if next_line.startswith('"""') or next_line.startswith("'''"):
                                        description = next_line.strip('"\'')
                                break

                        direct_raw = (
                            f"https://github.com/{repo}/raw/refs/heads/{branch}/{file_path}"
                        )

                        found_modules.append({
                            "name": mod_name,
                            "repo": repo,
                            "path": file_path,
                            "url": f"https://github.com/{repo}/blob/{branch}/{file_path}",
                            "raw_url": direct_raw,
                            "desc": description
                        })

        if not found_modules:
            await message.edit(
                f"<b>😔 По запросу <code>{query}</code> ничего не найдено в подключенных репозиториях.</b>"
            )
            return

        result = f"<b>📦 Результаты поиска по запросу <code>{query}</code>:</b>\n\n"
        for idx, mod in enumerate(found_modules[:10], 1):
            result += (
                f"<blockquote>"
                f"<b>{idx}. <a href='{mod['url']}'>{mod['name']}</a></b>\n"
                f"📂 Репо: <code>{mod['repo']}</code>\n"
                f"💬 Описание: <i>{mod['desc']}</i>\n"
                f"🔗 <code>{mod['raw_url']}</code>"
                f"</blockquote>\n"
            )

        await message.edit(result, link_preview=False)

    async def repocmd(self, message):
        """add/del/list <owner/repo> — управление репозиториями поиска"""
        args = utils.get_args_raw(message).split(maxsplit=1)
        if not args:
            await message.edit(
                "<b>📂 Использование:</b>\n"
                "<code>.repo add owner/repo</code> — добавить\n"
                "<code>.repo del owner/repo</code> — удалить\n"
                "<code>.repo list</code> — показать список"
            )
            return

        sub = args[0].lower()
        value = args[1].strip() if len(args) > 1 else ""

        if sub == "add":
            if not value or "/" not in value:
                await message.edit("<b>❌ Укажите репозиторий в формате <code>owner/repo</code></b>")
                return
            if value in self.repos:
                await message.edit(f"<b>⚠️ Репозиторий <code>{value}</code> уже есть в списке!</b>")
                return
            self.repos.append(value)
            self._save_repos()
            await message.edit(f"<b>✅ Репозиторий <code>{value}</code> добавлен!</b>")

        elif sub == "del":
            if not value:
                await message.edit("<b>❌ Укажите репозиторий для удаления.</b>")
                return
            if value not in self.repos:
                await message.edit(f"<b>❌ Репозиторий <code>{value}</code> не найден.</b>")
                return
            self.repos.remove(value)
            self._save_repos()
            await message.edit(f"<b>🗑 Репозиторий <code>{value}</code> удалён.</b>")

        elif sub == "list":
            if not self.repos:
                await message.edit("<b>📂 Список репозиториев пуст.</b>")
                return
            text = "<b>📂 Подключенные репозитории:</b>\n\n"
            for repo in self.repos:
                text += f"• <code>{repo}</code>\n"
            await message.edit(text)

        else:
            await message.edit(
                f"<b>❌ Неизвестная подкоманда: <code>{sub}</code></b>\n"
                "<code>.repo add/del/list</code>"
          )
