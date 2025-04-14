import os
import pickle
import sys
import textwrap
import time
import webbrowser
from datetime import datetime
from math import ceil
from pathlib import Path
from threading import Thread
from typing import Literal

from pytimedinput import timedInput

from scripts.site import Site
from scripts.utils import News


class AsimovNews:
    def __init__(self) -> None:
        self.dict_site: dict[str, Site] = {}
        self.all_sites = ["veja", "r7", "globo", "cnn", "livecoins", "poder360"]

        self.workspace = Path(__file__).absolute().parent.parent
        self.page = 1
        self.screen = 0
        self.kill = False

        self.news: list[News] = (
            self._read_file("news")
            if "news" in os.listdir(self.workspace)
            else []
        )
        self._update_file(self.news, "news")
        self.sites: list[str] = (
            self._read_file("sites")
            if "sites" in os.listdir(self.workspace)
            else []
        )
        self._update_file(self.sites, "sites")

        for site in self.all_sites:
            self.dict_site[site] = Site(site)

        self.news_thread = Thread(
            target=self._update_news, name="NewsUpdater", daemon=True
        )
        self.news_thread.start()

    def _update_file(self, lista: list, mode: Literal["news", "sites"]):
        with open(mode, "wb") as f:
            pickle.dump(lista, f)

    def _read_file(self, mode: Literal["news", "sites"]) -> list:
        with open(mode, "rb") as f:
            return pickle.load(f)

    def _receive_command(self, valid_commands: list[str], *, timeout=30) -> str:
        command, timed = timedInput(">> ", timeout=timeout)
        while command.lower() not in valid_commands and not timed:
            print("Comando inválido. Digite novamente", end="\n\n")
            command, timed = timedInput(">> ", timeout=timeout)
        command = "0" if command == "" else command
        return command

    def main_loop(self) -> None:
        while True:
            os.system("cls" if os.name == "nt" else "clear")

            match self.screen:
                case 0:
                    print(
                        textwrap.dedent(
                            """
                        SEJA BEM VINDO AO ASIMOV NEWS.
                        Por favor escolha algum item do menu

                        1. Últimas Notícias
                        2. Adicionar site
                        3. Remover sites
                        4. Fechar o Programa
                        """
                        )
                    )

                    self.screen = int(
                        self._receive_command(
                            ["1", "2", "3", "4"],
                            timeout=5,
                        )
                    )

                    print(self.screen, type(self.screen))
                case 1:
                    self._display_news()
                    command = self._receive_command(
                        ["p", "a", "l", "v"], timeout=5
                    )
                    match command:
                        case "p":
                            if self.page < self.max_page:
                                self.page += 1
                        case "a":
                            if self.page > 1:
                                self.page -= 1
                        case "l":
                            try:
                                link = int(
                                    input(
                                        ">> Insira o número da matéria que deseja abrir: "
                                    )
                                )
                                if link < 1 or link > len(self.filtered_news):
                                    print("Matéria não existe")
                                    continue
                            except ValueError:
                                print("Matéria inválida")
                            else:
                                webbrowser.open(
                                    self.filtered_news[link - 1].link
                                )

                        case "v":
                            self.screen = 0
                            continue
                case 2:
                    os.system("cls" if os.name == "nt" else "clear")

                    print(
                        "Digite o número do site que deseja adicionar para a lista de sites ativos."
                    )
                    print("Pressiona 0 para voltar para o menu.")

                    print()
                    print("\tSITES ATIVOS ".ljust(30, "="))
                    for site in self.sites:
                        print(f"\t {site}")

                    print()
                    print("\tSITES INATIVOS ".ljust(30, "="))
                    offline_sites = [
                        i for i in self.all_sites if i not in self.sites
                    ]
                    for i, site in enumerate(offline_sites, start=1):
                        print(f"\t {i}. {site}")

                    site = int(
                        self._receive_command(
                            [str(i) for i in range(len(offline_sites) + 1)],
                            timeout=50,
                        )
                    )

                    if site == 0:
                        self.screen = 0
                        continue
                    self.sites += [offline_sites[site - 1]]
                    self._update_file(self.sites, "sites")
                case 3:
                    os.system("cls" if os.name == "nt" else "clear")

                    print(
                        "Digite o número do site para remove-lo. Caso queira voltar para o Menu, digite 0",
                        end="\n\n",
                    )

                    print("\tSITES INATIVOS ".ljust(30, "="))
                    for i, site in enumerate(self.sites, start=1):
                        print(f"\t {i}. {site}")

                    site = int(
                        self._receive_command(
                            [str(i) for i in range(len(self.sites) + 1)],
                            timeout=50,
                        )
                    )

                    if site == 0:
                        self.screen = 0
                        continue
                    del self.sites[site - 1]
                    self._update_file(self.sites, "sites")
                case 4:
                    self.kill = True
                    sys.exit()

    def _display_news(self) -> None:
        os.system("cls" if os.name == "nt" else "clear")

        print(
            f"Último update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            end="\n\n",
        )

        self.filtered_news = [i for i in self.news if i.fonte in self.sites]
        self.max_page = ceil(len(self.filtered_news) / 20)

        if self.page > self.max_page:
            self.page = self.max_page

        CONST = (self.page - 1) * 20

        for i, news in enumerate(
            self.filtered_news[CONST : CONST + 20], start=1
        ):
            print(
                f"{CONST + i}. {news.data.strftime('%Y-%m-%d %H:%M:%S')} - {news.fonte.upper()} - {news.materia}"
            )
        print(f"Page {self.page}/{self.max_page}")

        print("=" * 50, end="\n\n")
        print("Comandos:")
        print(
            "P - Próxima Página | A - Página Anterior | L - Abrir matéria no navegador | V - Voltar"
        )

    def _update_news(self) -> None:
        while not self.kill:
            for site in self.all_sites:
                self.dict_site[site].update_news()

                for news in self.dict_site[site].list_news:
                    dict_aux = News(
                        data=datetime.now(),
                        fonte=site,
                        materia=news.title,
                        link=news.url,
                    )

                    if len(self.news) == 0:
                        self.news.insert(0, dict_aux)
                        continue

                    for news in self.news:
                        if (
                            dict_aux.materia == news.materia
                            and dict_aux.fonte == news.fonte
                        ):
                            add_news = False
                            break
                    else:
                        add_news = True

                    if add_news:
                        self.news.insert(0, dict_aux)
                        self._update_file(self.news, "news")

            self.news.sort(key=lambda x: x.data, reverse=True)
            self._update_file(self.news, "news")
            time.sleep(5)
