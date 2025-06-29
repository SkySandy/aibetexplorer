"""Сохранение данных в формате FBcup."""
import asyncio
import io
import sys
import time
import timeit

from app.fbcup.analysis import to_analysis
from app.config import settings


async def load() -> None:
    """Загрузка данных."""
    # Увеличивает размер буфера для стандартного вывода через print
    sys.stdout = io.TextIOWrapper(
        io.BufferedWriter(sys.stdout.buffer, buffer_size=10_000_000),
        encoding='utf-8'
    )
    st = timeit.default_timer()
    st_p = time.process_time()
    await to_analysis(
        root_dir=settings.FBCUP_DIRECTORY,
        database=settings.SQLALCHEMY_DATABASE_URI,
        sport_type=settings.SPORT_TYPE,
        load_net=settings.LOAD_NET,
        save_database=settings.SAVE_DATABASE,
        create_tables=settings.CREATE_TABLES,
        config_engine=settings.CONFIG_DATABASE,
        start_updating=settings.START_UPDATING,
        exclude_countries=settings.EXCLUDE_COUNTRIES,
        processes=settings.PROCESSES,
    )
    elapsed_time = timeit.default_timer() - st
    elapsed_time_p = time.process_time() - st_p
    print('Время исполнения:', time.strftime('%H:%M:%S', time.gmtime(elapsed_time)))
    print('Время исполнения CPU:', time.strftime('%H:%M:%S', time.gmtime(elapsed_time_p)))


if __name__ == '__main__':
    asyncio.run(load())
