import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings

def clean_asyncpg_url(url: str) -> str:
    """Normalize PostgreSQL URL for asyncpg compatibility."""
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    
    parsed = urlparse(url)
    if "asyncpg" in parsed.scheme and parsed.query:
        query_params = parse_qs(parsed.query)
        # Convert sslmode to ssl
        if "sslmode" in query_params:
            sslmode_val = query_params.pop("sslmode")[0]
            if "ssl" not in query_params:
                query_params["ssl"] = ["require" if sslmode_val != "disable" else "disable"]
        # Remove unsupported asyncpg parameters
        query_params.pop("channel_binding", None)
        
        flat_params = {k: v[0] for k, v in query_params.items()}
        new_query = urlencode(flat_params)
        url = urlunparse(parsed._replace(query=new_query))
    return url

db_url = clean_asyncpg_url(settings.DATABASE_URL)

# Create asynchronous engine
engine = create_async_engine(
    db_url,
    echo=(settings.ENVIRONMENT == "development_debug"),
    future=True,
    pool_pre_ping=True,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for providing a transactional async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
