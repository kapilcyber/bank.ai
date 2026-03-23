"""Test all backend connections."""
import asyncio
from src.config.settings import settings
from src.config.database import create_database_if_not_exists, engine
from sqlalchemy import text


def test_settings():
    """Test settings loading."""
    print("=" * 50)
    print("🔧 Testing Settings Configuration")
    print("=" * 50)
    print(f"✅ PostgreSQL: {settings.postgres_user}@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}")
    print(f"✅ Server: {settings.host}:{settings.port}")
    print(f"✅ JWT: Algorithm={settings.jwt_algorithm}, Expiry={settings.jwt_expiration_hours}h")
    print(f"✅ Ollama URL: {settings.ollama_base_url}")
    print(f"✅ Ollama Model: {settings.ollama_model}")
    print(f"✅ Upload Dir: {settings.upload_dir}, Max Size: {settings.max_file_size_mb}MB")
    print(f"✅ CORS Origins: {settings.cors_origins}")
    print(f"✅ Celery: {settings.celery_broker_url}")
    print()


def test_database():
    """Test database connection."""
    print("=" * 50)
    print("🗄️  Testing Database Connection")
    print("=" * 50)
    try:
        result = create_database_if_not_exists()
        if result:
            print("✅ Database exists or created successfully")
        else:
            print("⚠️  Database creation had issues (check PostgreSQL is running)")
    except Exception as e:
        print(f"❌ Database connection error: {e}")
    print()


async def test_async_database():
    """Test async database connection."""
    print("=" * 50)
    print("🔄 Testing Async Database Connection")
    print("=" * 50)
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ PostgreSQL connected successfully")
            print(f"   Version: {version.split(',')[0]}")
    except Exception as e:
        print(f"❌ Async database connection error: {e}")
        print("   Make sure PostgreSQL is running and credentials are correct")
    print()


def main():
    """Run all connection tests."""
    print("\n" + "=" * 50)
    print("🚀 TechBank.ai Backend - Connection Test")
    print("=" * 50 + "\n")
    
    # Test settings
    test_settings()
    
    # Test database (sync)
    test_database()
    
    # Test async database
    asyncio.run(test_async_database())
    
    print("=" * 50)
    print("✅ Connection tests completed!")
    print("=" * 50)
    print("\nTo start the server, run: python -m src.main\n")


if __name__ == "__main__":
    main()


