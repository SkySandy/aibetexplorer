"""Обеспечение операций ввода-вывода с сайта и жесткого диска."""
import datetime
import os
from typing import TYPE_CHECKING

import aiofiles
from aiofiles import os as aiofiles_os

if TYPE_CHECKING:
    from aiofiles.threadpool.text import AsyncTextIOWrapper


async def load_file(file_path: str) -> str:
    """Чтение файла с диска.

    :param file_path: Путь к файлу
    """
    f: AsyncTextIOWrapper
    async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
        return await f.read()

async def save_list(file_path: str, text: list, creation_date: datetime.datetime, is_bytes: bool = False) -> None:
    """Запись списка на диск.

    :param file_path: Путь к файлу
    :param text: Содержимое файла
    :param creation_date: Время модификации создаваемого файла
    :param is_bytes: Сохранять данные как набор байт
    """
    await aiofiles_os.makedirs(os.path.dirname(file_path), exist_ok=True)
    f: AsyncTextIOWrapper
    if not is_bytes:
        async with aiofiles.open(file_path, mode='w', encoding='utf-8') as f:
            for line in text:
                await f.write(f'{line}\n')
            await f.flush()
    dt_epoch: float = creation_date.timestamp()
    os.utime(file_path, (dt_epoch, dt_epoch))

async def save_file(file_path: str, text: str, creation_date: datetime.datetime, is_bytes: bool = False) -> None:
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
