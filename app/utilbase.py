"""Обеспечение операций ввода-вывода с сайта и жесткого диска."""
import asyncio
from contextlib import nullcontext
import datetime
from email.utils import parsedate_to_datetime
import inspect
import multiprocessing
import os
import sys
import traceback
from typing import TYPE_CHECKING, Callable, NamedTuple, Optional, Union
from urllib.parse import parse_qsl, urljoin, urlparse

import aiofiles
from aiofiles import os as aiofiles_os
import aiohttp

# from aiofile import async_open, TextFileWrapper
if TYPE_CHECKING:
    from aiofiles.threadpool.text import AsyncTextIOWrapper
from aiohttp import ClientConnectorError

# from selectolax.lexbor import LexborHTMLParser, LexborNode
from selectolax.parser import HTMLParser, Node

from app.betexplorer.crud import DATABASE_NOT_USE, DatabaseUsage
from app.database import DatabaseSessionManager


def get_current_depth() -> int:
    """Ручной подсчет фреймов."""
    frame = sys._getframe()
    depth = 0
    while frame:
        frame = frame.f_back
        depth += 1
    return depth

def get_current_depth2() -> int:
    """Ручной подсчет фреймов."""
    return len(inspect.stack())


class ReceivedData(NamedTuple):
    """Загруженные и разобранные данные."""

    node: Optional[Node]
    """Данные."""
    creation_date: Optional[datetime.datetime]
    """Дата загрузки."""

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.node == other.node and self.creation_date == other.creation_date)

    def __hash__(self):
        return hash((self.node, self.creation_date))


class HTMLData(NamedTuple):
    """Скаченные из Интернета данные."""

    text: Union[str, bytes]
    """Данные."""
    creation_date: Optional[datetime.datetime]
    """Дата загрузки."""


class LoadSave():
    """Загрузка и сохранение данных из интернета."""

    def __init__(
            self,
            root_url: str,
            root_dir: str,
    ) -> None:
        """Инициализация класса для загрузки данных.

        :param root_url: Путь к коренной папки сайта
        :param root_dir: Путь для сохранения данных на диске
        """
        self.headers: dict = {
            'referer': root_url,
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',  # noqa: E501
        }
        self.root_url = root_url
        self.root_dir = root_dir
        self.load_net = False
        self.connector = None
        self._session = None
        self._lock = nullcontext()

    async def __aexit__(self, *error_details) -> None:
        await self.close_session()

    async def __aenter__(self):
        return self

    def open_session(self) -> None:
        """Открыть соединение с сетью Интернет."""
        self.connector = aiohttp.TCPConnector(limit=1, force_close=True)
        self._session: aiohttp.ClientSession = aiohttp.ClientSession(connector=self.connector)

    async def close_session(self) -> None:
        """Закрыть соединение с сетью Интернет."""
        if self._session is not None:
            await self._session.close()
        if self.connector is not None:
            await self.connector.close()

    async def load_data(
            self,
            load_net: bool = False,
            lock: Optional[multiprocessing.Lock] = None,
    ) -> None:
        """Загрузка списка всех чемпионатов во всех странах.

        :param load_net: Загружать из интернета False - нет (использовать только сохраненные на диске), True - да
        :param lock: Действия требующие монополизма
        """
        if lock is not None:
            self._lock = lock
        self.load_net = load_net
        if load_net:
            self.open_session()

    async def get_file_bet(self, url: str, is_bytes: bool = False) -> Optional[HTMLData]:
        """Скачать данные из интернета.

        :param url: Путь к странице для скачивания
        :param is_bytes: Данные являются файлом (набор байт)
        """
        with self._lock:
            retries: int = 0
            delay: float = 60.0
            if url == 'javascript:void(0);':
                print(datetime.datetime.now(), flush=True)
                print(url, flush=True)
                return None
            while retries < 4:
                try:
                    r: aiohttp.ClientResponse
                    async with self._session.get(url, headers=self.headers, timeout=200) as r:
                        if r.status != 200:
                            return None
                            # r.raise_for_status()
                        try:
                            creation_date = parsedate_to_datetime(r.headers['Date'])
                            if creation_date.tzinfo is not None and creation_date.tzinfo.utcoffset(creation_date) is not None:
                                creation_date = creation_date.replace(tzinfo=None) + datetime.timedelta(hours=3)
                        except (ValueError, KeyError):
                            creation_date: datetime.datetime = datetime.datetime.now()
                        if not is_bytes:
                            return HTMLData(await r.text(), creation_date)
                        return HTMLData(await r.read(), creation_date)
                except (ClientConnectorError, ConnectionRefusedError, asyncio.TimeoutError) as ex:
                    print(datetime.datetime.now(), flush=True)
                    print(url, flush=True)
                    print(ex, flush=True)
                    await asyncio.sleep(delay)
                    delay *= 2
                    retries += 1
                except RecursionError as ex:
                    print(datetime.datetime.now(), flush=True)
                    print(url, flush=True)
                    print(ex, flush=True)
                    print(traceback.format_exc())
                    print(f'Текущая глубина: {get_current_depth()}')
                    print(f'Текущая глубина2: {get_current_depth2()}')
                    await asyncio.sleep(delay)
                    delay *= 2
                    retries += 1
                except Exception as ex:
                    print(datetime.datetime.now(), flush=True)
                    print(url, flush=True)
                    print(ex, flush=True)
                    print('Неизвестная ошибка', flush=True)
                    await asyncio.sleep(delay)
                    delay *= 2
                    retries += 1
            return None

    async def load_file(self, file_path: str) -> str:
        """Чтение файла с диска.

        :param file_path: Путь к файлу
        """
        f: AsyncTextIOWrapper
        async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
            return await f.read()

    # async def load_file2(self, file_path: str) -> str:
    #     """Чтение файла с диска.
    #
    #     :param file_path: Путь к файлу
    #     """
    #     f: TextFileWrapper
    #     async with async_open(file_path, mode='r', encoding='utf-8') as f:
    #         return await f.read()

    async def save_file(self, file_path: str, text: str, creation_date: datetime.datetime, is_bytes: bool = False) -> None:
        """Запись файла на диск.

        :param file_path: Путь к файлу
        :param text: Содержимое файла
        :param creation_date: Время модификации создаваемого файла
        :param is_bytes: Сохранять данные как набор байт
        """
        await aiofiles_os.makedirs(os.path.dirname(file_path), exist_ok=True)
        f: AsyncTextIOWrapper
        if not is_bytes:
            async with aiofiles.open(file_path, mode='w', encoding='utf-8') as f:
                await f.write(text)
                await f.flush()
        else:
            async with aiofiles.open(file_path, mode='wb') as f:
                await f.write(text)
                await f.flush()
        dt_epoch: float = creation_date.timestamp()
        os.utime(file_path, (dt_epoch, dt_epoch))

    async def get_read(self,
                       url: str,
                       class_: str,
                       need_refresh: bool = False,
                       ) -> Optional[ReceivedData]:
        """Загрузка файла из интернета или скачивание с диска.

        :param url: Путь к странице для скачивания
        :param class_: Имя класса который надо найти в файле
        :param need_refresh: Необходимо обновить данные
        """
        url_p = urlparse(url)
        params: str = '_' + '_'.join('%s_%s' % e for e in parse_qsl(url_p.query)) if url_p.query else ''
        split_url: list = [x for x in url_p.path.split('/') if x]
        dir_adr: str = os.path.join(self.root_dir, *split_url[:-1])
        file_name: str = split_url[-1] + params + '.http'
        file_path: str = os.path.join(dir_adr, file_name)
        if (not need_refresh or not self.load_net) and await aiofiles_os.path.exists(file_path):
            # async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
            #     rrr: str = await f.read()
            # ret_node: Optional[Node] = HTMLParser(rrr).css_first(class_)
            if class_ == '':
                save_text: str = await self.load_file(file_path)
                ret_node: Node | None = HTMLParser(save_text)
            else:
                ret_node: Node | None = HTMLParser(await self.load_file(file_path)).css_first(class_)
            date_file: datetime.datetime = datetime.datetime.fromtimestamp(await aiofiles_os.path.getmtime(file_path))
            if (ret_node is None) and (class_ != ''):
                print(f'{datetime.datetime.now()} Not found: url = {url} class_= {class_}', flush=True)
                return None
            return ReceivedData(ret_node, date_file)
        if self.load_net:
            ret: HTMLData | None
            if (ret := await self.get_file_bet(urljoin(self.root_url, url))) is not None:
                save_text: str = ret.text
                ret_node: Node | None = None
                if class_ == '':
                    save_text = save_text.replace('\\n', '\r\n')
                    save_text = save_text.replace('\\"', '"')
                    save_text = save_text.replace('\\/', '/')
                    save_text = save_text[9:-2]
                    ret_node: Node | None = HTMLParser(save_text)
                    for node in ret_node.css('a[onclick]'):
                        if node.attrs['onclick'][:14] == 'dataLayer.push':
                            del node.attrs['onclick']
                    save_text = ret_node.html
                elif (ret_node := HTMLParser(save_text).css_first(class_)) is not None:
                    save_text = ret_node.html
                await self.save_file(file_path, save_text, ret.creation_date)
                if (ret_node is None) and (class_ != ''):
                    print(f'{datetime.datetime.now()} Not found: url = {url} class_= {class_}', flush=True)
                    return None
                return ReceivedData(ret_node, ret.creation_date)
        return None

    async def get_as_file(self,
                          url: str,
                          need_refresh: bool = False) -> Optional[bytes]:
        """Загрузка файла из интернета в каталог.

        :param url: Путь к странице для скачивания
        :param need_refresh: Необходимо обновить данные
        """
        url_p = urlparse(url)
        params: str = '_' + '_'.join('%s_%s' % e for e in parse_qsl(url_p.query)) if url_p.query else ''
        try:
            split_url: list = [x for x in url_p.path.split('/') if x]
        except:
            print(f'Error in split: {url}', flush=True)
            return None
        dir_adr: str = os.path.join(self.root_dir, *split_url[:-1])
        file_name: str = split_url[-1]
        file_path: str = os.path.join(dir_adr, file_name)
        if (not need_refresh or not self.load_net) and await aiofiles_os.path.exists(file_path):
            f: AsyncTextIOWrapper
            async with aiofiles.open(file_path, mode='rb') as f:
                return await f.read()
        if self.load_net:
            ret: Optional[HTMLData]
            if (ret := await self.get_file_bet(urljoin(self.root_url, url), is_bytes=True)) is not None:
                await self.save_file(file_path, ret.text, ret.creation_date, is_bytes=True)
                return ret.text
        return None
