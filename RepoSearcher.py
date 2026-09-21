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
import json
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
        api_url = f"https://api.github.com/repos/{repo}/git/trees/main?recursive=1"
        async with session.get(api_url) as response:
            if response.status != 200:
                api_url = f"https://api.github.com/repos/{repo}/git/trees/master?recursive=1"
                async with session.get(api_url) as resp:
                    if resp.status != 200:
                        return []
                    data = await resp.json()
            else:
                data = await response.json()
        
        return data.get("tree", [])

    async def dsearchmodcmd(self, message):
        """<запрос> — найти модули по описанию в репозиториях"""
        query = utils.get_args_raw(message)
        if not query:
            await message.edit("<b>❌ Укажите поисковый запрос! Пример: <code>.searchmod id</code></b>")
            return

        await message.edit("<b>🔎 Ищу модули по репозиториям...</b>")
        found_modules = []
        async with aiohttp.ClientSession() as session:
            for repo in self.repos:
                tree = await self._fetch_repo_contents(session, repo)
                if not tree:
                    continue

                py_files = [
                    item for item in tree 
                    if item["path"].endswith(".py") and not item["path"].startswith(".")
                ]

                for file_info in py_files:
                    file_path = file_info["path"]
                    raw_url = f"https://raw.githubusercontent.com/{repo}/main/{file_path}"
                    
                    async with session.get(raw_url) as resp:
                        if resp.status != 200:
                            raw_url = f"https://raw.githubusercontent.com/{repo}/master/{file_path}"
                            async with session.get(raw_url) as resp_master:
                                if resp_master.status != 200:
                                    continue
                                content = await resp_master.text()
                        else:
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

                        found_modules.append({
                            "name": mod_name,
                            "repo": repo,
                            "path": file_path,
                            "url": f"https://github.com/{repo}/blob/main/{file_path}",
                            "desc": description
                        })

        if not found_modules:
            await message.edit(f"<b>😔 По запросу <code>{query}</code> ничего не найдено в подключенных репозиториях.</b>")
            return

        result = f"<b>📦 Результаты поиска по запросу <code>{query}</code>:</b>\n\n"
        for idx, mod in enumerate(found_modules[:10], 1):
            result += (
                f"<blockquote>"
                f"<b>{idx}. <a href='{mod['url']}'>{mod['name']}</a></b>\n"
                f"📂 Репо: <code>{mod['repo']}</code>\n"
                f"💬 Описание: <i>{mod['desc']}</i>"
                f"</blockquote>\n"
            )

        await message.edit(result, link_preview=False)

    async def daddrepocmd(self, message):
        """<owner/repo> — добавить репозиторий для поиска (например: uranfiz/heroku-modules)"""
        args = utils.get_args_raw(message).strip()
        if not args or "/" not in args:
            await message.edit("<b>❌ Укажите репозиторий в формате <code>owner/repo</code></b>")
            return

        if args in self.repos:
            await message.edit(f"<b>⚠️ Репозиторий <code>{args}</code> уже есть в списке поиска!</b>")
            return

        self.repos.append(args)
        self._save_repos()
        await message.edit(f"<b>✅ Репозиторий <code>{args}</code> успешно добавлен!</b>")

    async def ddelrepocmd(self, message):
        """<owner/repo> — удалить репозиторий из поиска"""
        args = utils.get_args_raw(message).strip()
        if not args:
            await message.edit("<b>❌ Укажите репозиторий для удаления.</b>")
            return

        if args not in self.repos:
            await message.edit(f"<b>❌ Репозиторий <code>{args}</code> не найден в списке.</b>")
            return

        self.repos.remove(args)
        self._save_repos()
        await message.edit(f"<b>🗑 Репозиторий <code>{args}</code> удален из поиска.</b>")

    async def dlistrepocmd(self, message):
        """— показать список подключенных репозиториев"""
        if not self.repos:
            await message.edit("<b>📂 Список репозиториев пуст.</b>")
            return

        text = "<b>📂 Подключенные репозитории для поиска:</b>\n\n"
        for repo in self.repos:
            text += f"• <code>{repo}</code>\n"
        
        await message.edit(text)
