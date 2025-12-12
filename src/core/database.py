"""
Database Connection Module

PostgreSQL 비동기 연결 관리
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import asyncpg


# 환경변수에서 DATABASE_URL 가져오기
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://wsoptv:wsoptv@localhost:5434/wsoptv"
)


class Database:
    """PostgreSQL 비동기 연결 풀 관리"""

    _pool: asyncpg.Pool | None = None

    @classmethod
    async def get_pool(cls) -> asyncpg.Pool:
        """연결 풀 가져오기 (싱글톤)"""
        if cls._pool is None:
            # DATABASE_URL 파싱
            url = DATABASE_URL.replace("postgresql://", "")
            user_pass, host_db = url.split("@")
            user, password = user_pass.split(":")
            host_port, database = host_db.split("/")

            if ":" in host_port:
                host, port = host_port.split(":")
                port = int(port)
            else:
                host = host_port
                port = 5432

            cls._pool = await asyncpg.create_pool(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database,
                min_size=2,
                max_size=10,
                ssl=False,  # 로컬 개발환경에서 SSL 비활성화
            )
        return cls._pool

    @classmethod
    async def close(cls):
        """연결 풀 닫기"""
        if cls._pool:
            await cls._pool.close()
            cls._pool = None

    @classmethod
    @asynccontextmanager
    async def connection(cls) -> AsyncGenerator[asyncpg.Connection, None]:
        """컨텍스트 매니저로 연결 가져오기"""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            yield conn


async def get_db_connection() -> asyncpg.Connection:
    """의존성 주입용 연결 함수"""
    pool = await Database.get_pool()
    return await pool.acquire()
