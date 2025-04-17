import logging
import os
import pickle
import sys
import textwrap
import time
import webbrowser
from datetime import datetime
from math import ceil
from pathlib import Path
from threading import Lock, Thread
from typing import Final, Literal

from pytimedinput import timedInput

from scripts.log_config import setup_logging
from scripts.site import Site
from scripts.utils import News

# Configurar logging básico (mesmo que em site.py, pode ser centralizado depois)
setup_logging()


class AsimovNews:
    def __init__(self) -> None:
        self.dict_site: dict[str, Site] = {}
        self.all_sites = ["veja", "r7", "globo", "cnn", "livecoins", "poder360"]

        self.workspace = Path(__file__).absolute().parent.parent
        self.news_file = self.workspace / "news.pkl"
        self.sites_file = self.workspace / "sites.pkl"
        self.page = 1
        self.screen = 0
        self.kill = False
        self.news_lock = Lock()
        self.existing_news_identifiers: set[tuple[str, str]] = set()

        self.news: list[News] = self._read_file(self.news_file, "news")
        with self.news_lock:
            self.existing_news_identifiers = {(n.materia, n.fonte) for n in self.news}

        self.sites: list[str] = self._read_file(self.sites_file, "sites")

        self._update_file(self.news, self.news_file)
        self._update_file(self.sites, self.sites_file)

        for site in self.all_sites:
            self.dict_site[site] = Site(site)

        self.news_thread = Thread(
            target=self._update_news, name="NewsUpdater", daemon=True
        )
        self.news_thread.start()

    def _update_file(self, data: list, filepath: Path):
        file_to_write = None
        lock_acquired = False
        try:
            if filepath == self.news_file:
                self.news_lock.acquire()
                lock_acquired = True
                # Abrir o arquivo *depois* de adquirir o lock
                file_to_write = open(filepath, "wb")
            else:
                # Abrir outros arquivos normalmente
                file_to_write = open(filepath, "wb")

            # Escrever no arquivo
            pickle.dump(data, file_to_write)

        except (OSError, pickle.PicklingError) as e:
            logging.error(f"Erro ao salvar o arquivo {filepath}: {e}")
        finally:
            # Garantir que o arquivo seja fechado
            if file_to_write:
                file_to_write.close()
            # Garantir que o lock seja liberado se foi adquirido
            if lock_acquired:
                self.news_lock.release()

    def _read_file(self, filepath: Path, mode: Literal["news", "sites"]) -> list:
        # Adquirir lock antes de ler news.pkl
        lock_acquired = False
        if filepath == self.news_file:
            self.news_lock.acquire()
            lock_acquired = True

        try:
            if not filepath.exists():
                logging.warning(
                    f"Arquivo {filepath} não encontrado. Retornando lista vazia."
                )
                return []
            with open(filepath, "rb") as f:
                # Certificar que o arquivo não está vazio antes de carregar
                if os.path.getsize(filepath) > 0:
                    return pickle.load(f)
                else:
                    logging.warning(
                        f"Arquivo {filepath} está vazio. Retornando lista vazia."
                    )
                    return []
        except (FileNotFoundError, EOFError, pickle.UnpicklingError) as e:
            logging.error(
                f"Erro ao ler o arquivo {filepath}: {e}. Retornando lista vazia."
            )
            try:
                os.remove(filepath)
                logging.info(f"Arquivo corrompido {filepath} removido.")
            except OSError as remove_error:
                logging.error(
                    "Erro ao tentar remover o arquivo corrompido "
                    f"{filepath}: {remove_error}"
                )
            return []
        except Exception as e:
            logging.error(
                f"Erro inesperado ao ler o arquivo {filepath}: {e}. "
                "Retornando lista vazia."
            )
            return []
        finally:
            # Garantir que o lock seja liberado se foi adquirido
            if lock_acquired:
                self.news_lock.release()

    def _receive_command(self, valid_commands: list[str], *, timeout=30) -> str:
        command, timed = timedInput(">> ", timeout=timeout)
        while command.lower() not in valid_commands and not timed:
            print("Comando inválido. Digite novamente", end="\n\n")
            command, timed = timedInput(">> ", timeout=timeout)
        command = "0" if command == "" else command
        return command

    def _display_menu(self) -> None:
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
        self.screen = int(self._receive_command(["1", "2", "3", "4"], timeout=5))

    def _handle_news_screen(self) -> None:
        self._display_news()
        command = self._receive_command(["p", "a", "l", "v"], timeout=5)
        match command:
            case "p":
                if self.page < self.max_page:
                    self.page += 1
            case "a":
                if self.page > 1:
                    self.page -= 1
            case "l":
                try:
                    prompt = ">> Insira o número da matéria que deseja abrir: "
                    link = int(input(prompt))
                    if link < 1 or link > len(self.filtered_news):
                        print("Matéria não existe")
                        time.sleep(2)
                        return
                except ValueError:
                    print("Matéria inválida")
                    time.sleep(2)
                    return
                webbrowser.open(self.filtered_news[link - 1].link)
            case "v":
                self.screen = 0

    def _handle_add_site_screen(self) -> None:
        os.system("cls" if os.name == "nt" else "clear")
        print(
            "Digite o número do site que deseja adicionar para a lista de sites ativos."
        )
        print("Pressiona 0 para voltar para o menu.")

        print("\n\tSITES ATIVOS ".ljust(30, "="))
        for site in self.sites:
            print(f"\t {site}")

        print("\n\tSITES INATIVOS ".ljust(30, "="))
        offline_sites = [i for i in self.all_sites if i not in self.sites]
        for i, site in enumerate(offline_sites, start=1):
            print(f"\t {i}. {site}")

        site = int(
            self._receive_command(
                [str(i) for i in range(len(offline_sites) + 1)], timeout=50
            )
        )
        if site == 0:
            self.screen = 0
            return
        self.sites += [offline_sites[site - 1]]
        self._update_file(self.sites, self.sites_file)

    def _handle_remove_site_screen(self) -> None:
        os.system("cls" if os.name == "nt" else "clear")
        print(
            "Digite o número do site para remove-lo. "
            "Caso queira voltar para o Menu, digite 0\n"
        )

        print("\tSITES INATIVOS ".ljust(30, "="))
        for i, site in enumerate(self.sites, start=1):
            print(f"\t {i}. {site}")

        site = int(
            self._receive_command(
                [str(i) for i in range(len(self.sites) + 1)], timeout=50
            )
        )
        if site == 0:
            self.screen = 0
            return
        del self.sites[site - 1]
        self._update_file(self.sites, self.sites_file)

    def main_loop(self) -> None:
        while True:
            os.system("cls" if os.name == "nt" else "clear")
            match self.screen:
                case 0:
                    self._display_menu()
                case 1:
                    self._handle_news_screen()
                case 2:
                    self._handle_add_site_screen()
                case 3:
                    self._handle_remove_site_screen()
                case 4:
                    self.kill = True
                    sys.exit()

    def _display_news(self) -> None:
        os.system("cls" if os.name == "nt" else "clear")

        print(
            f"Último update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            end="\n\n",
        )
        with self.news_lock:
            self.filtered_news = [i for i in self.news if i.fonte in self.sites]

        if not self.filtered_news:
            print("Nenhuma notícia para exibir dos sites selecionados.")
            print("Verifique os sites ativos (opção 2 do menu).")
            self.max_page = 0
            self.page = 1
        else:
            self.max_page = ceil(len(self.filtered_news) / 20)
            if self.page > self.max_page:
                self.page = self.max_page

            const: Final = (self.page - 1) * 20

            for i, news_item in enumerate(
                self.filtered_news[const : const + 20], start=1
            ):
                date_str = news_item.data.strftime("%Y-%m-%d %H:%M:%S")
                print(
                    f"{const + i}. {date_str} - {news_item.fonte.upper()} - "
                    f"{news_item.materia}"
                )
        print(f"Page {self.page}/{self.max_page if self.max_page > 0 else 1}")

        print("=" * 50, end="\n\n")
        print("Comandos:")
        print(
            "P - Próxima Página | A - Página Anterior | "
            "L - Abrir matéria no navegador | V - Voltar"
        )

    def _update_news(self) -> None:
        while not self.kill:
            for site in self.all_sites:
                self.dict_site[site].update_news()
                new_articles_this_run = []

                articles_to_process = self.dict_site[site].list_news[:]
                self.dict_site[site].list_news.clear()

                for article in articles_to_process:
                    news_identifier = (article.title, site)
                    if news_identifier not in self.existing_news_identifiers:
                        dict_aux = News(
                            data=datetime.now(),
                            fonte=site,
                            materia=article.title,
                            link=article.url,
                        )
                        new_articles_this_run.append(dict_aux)
                        self.existing_news_identifiers.add(news_identifier)

                if new_articles_this_run:
                    with self.news_lock:
                        self.news[0:0] = new_articles_this_run
                        self.news.sort(key=lambda x: x.data, reverse=True)
                    self._update_file(self.news, self.news_file)

            time.sleep(5)
