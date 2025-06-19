from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from app.config import settings
import ssl

# Base para models
Base = declarative_base()

# SSL context para DigitalOcean
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

# Async engine para PostgreSQL
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=True if settings.ENVIRONMENT == "development" else False,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={
        "ssl": ssl_context,
        "server_settings": {
            "application_name": "formerr_api_brunov7",
        }
    }
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    """Database dependency para FastAPI"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Inicializar database"""
    async with engine.begin() as conn:
        # Criar todas as tabelas
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables created successfully!")

async def close_db():
    """Fechar conexão com database"""
    await engine.dispose()
    print("✅ Database connection closed!")