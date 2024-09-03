'''conftest.py'''

from typing import AsyncGenerator
from contextlib import asynccontextmanager
import httpx
import pytest_asyncio
from fastapi import FastAPI
from router import employee_router, task_router
from router import authentication_router, project_router

@pytest_asyncio.fixture
async def app() -> AsyncGenerator[FastAPI, None]:
    '''Функция для жизненного цикла приложения для тестов'''
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        yield

    app = FastAPI(lifespan=lifespan)
    app.include_router(employee_router)
    app.include_router(project_router)
    app.include_router(task_router)
    app.include_router(authentication_router)
    yield app

@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[httpx.AsyncClient, None]:
    '''Функция для имитации пользователя'''
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://45.92.176.81:44446"
        ) as client:
        print("Client is on")
        yield client
        print("Client is off")
