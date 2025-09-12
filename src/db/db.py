from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from config.config import get_config

# from db.models import init_db

# Откладываем загрузку конфигурации
_engine = None
_AsyncSessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        config = get_config()
        DATABASE_URL = config.db.url
        _engine = create_async_engine(DATABASE_URL, echo=False)
    return _engine


def get_session_factory():
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _AsyncSessionLocal = sessionmaker(
            get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _AsyncSessionLocal


# Создаем класс-обертку для ленивого доступа
class _AsyncSessionLocalProxy:
    def __call__(self):
        return get_session_factory()()


AsyncSessionLocal = _AsyncSessionLocalProxy()


Base = declarative_base()


async def get_db():
    async with get_session_factory()() as session:
        yield session


if __name__ == "__main__":

    # asyncio.run(init_db())
    print("База данных инициализирована.")
