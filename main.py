'''main.py'''

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from graphql_schema import graphql_app
from router import employee_router, task_router
from router import authentication_router
from router import project_router

app = FastAPI(
        title="Interface-service",
        version="1.0.0",
        description="Сервис для создания и хранения данных о пользователях и задач.\
            Так же иметь доступ к двум другим сервисам,и объединить их взаимосвязь в Graphql",
    )

app.include_router(authentication_router,prefix="/authentication",
                            tags=["Authentication Interface Manager"])
app.include_router(employee_router,prefix="/employee-service",
                            tags=["Employee Manager"])
app.include_router(project_router,prefix="/task-service",
                            tags=["Task Manager"])
app.include_router(task_router,prefix="/task-service",
                            tags=["Task Manager"])
app.include_router(graphql_app, tags=["Graphql Connect"], prefix="/graphql")

# Обновление схемы OpenAPI
def custom_openapi():
    '''Функция для работа авторизации приложения'''
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Interface-service",
        version="1.0.0",
        description="Сервис для создания и хранения данных о пользователях и задач.\
            Так же иметь доступ к двум другим сервисам,и объединить их взаимосвязь в Graphql",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/authentication/token",
                    "scopes": {}
                }
            }
        }
    }
    openapi_schema["security"] = [
        {"OAuth2PasswordBearer": []}
    ]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
