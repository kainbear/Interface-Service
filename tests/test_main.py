'''test_main.py'''

import pytest
from httpx import AsyncClient

USER_SERVICE_URL = "http://45.92.176.81:44444"
TASK_SERVICE_URL = "http://45.92.176.81:44445"

# Вспомогательные функции
async def register_user(client, user_data):
    '''Регистрирует пользователя и возвращает ответ'''
    return await client.post("/register", params=user_data)

async def login_user(client, username, password):
    '''Логинит пользователя и возвращает токен доступа'''
    login_data = {
        "grant_type": "password",
        "username": username,
        "password": password,
    }
    response = await client.post("/token", data=login_data)
    # Добавляем лог для вывода ответа на получение токена
    print(f"Login response JSON: {response.json()}")
    return response

async def get_auth_headers(client, username, password):
    '''Получает заголовок авторизации для последующих запросов'''
    token_response = await login_user(client, username, password)
    # Проверяем, содержит ли ответ ключ 'access_token'
    token_data = token_response.json()
    if 'access_token' not in token_data:
        raise KeyError(f"'access_token' not found in the response: {token_data}")
    return {"Authorization": f"Bearer {token_data['access_token']}"}

@pytest.mark.asyncio
async def test_register_and_get_all_users(client: AsyncClient):
    '''Тест для регистрации и получения всех пользователей'''
    register_data = {
        "last_name": "User",
        "first_name": "Test",
        "email": "testuser@example.com",
        "login": "testuser",
        "password": "testpassword",
        "is_supervisor": "yes",
        "is_vacation": "no"
    }
    # Регистрация пользователя
    register_response = await register_user(client, register_data)
    # Проверяем статус-код
    assert register_response.status_code == 200
    # Логируем ответ после регистрации
    print(f"Register response JSON: {register_response.json()}")
    # Получаем заголовки авторизации
    headers = await get_auth_headers(client, "testuser", "testpassword")
    # Используем полученные заголовки для получения списка пользователей
    response = await client.get("/employees", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 0

@pytest.mark.asyncio
async def test_create_user_and_supervisor(client: AsyncClient):
    '''Тест-Функция Для Создания Пользователя и Суперпользователя'''
    register_data = {
        "last_name": "User2",
        "first_name": "Test2",
        "email": "testuser2@example.com",
        "login": "testuser2",
        "password": "testpassword2",
        "is_supervisor": "no",
        "is_vacation": "no"
    }
    # Регистрация пользователя
    register_response = await client.post("/register", params=register_data)
    # Логирование полного ответа для отладки
    print(f"Register Response Status: {register_response.status_code}")
    print(f"Register Response JSON: {register_response.json()}")
    assert register_response.status_code == 200
    # Логин пользователя и получение токена
    login_data = {
        "grant_type": "password",
        "username": "testuser2",
        "password": "testpassword2",
    }
    token_response = await client.post("/token", data=login_data)
    assert token_response.status_code == 200
    token_data = token_response.json()
    access_token = token_data["access_token"]
    # Получение всех пользователей с использованием токена
    headers = {"Authorization": f"Bearer {access_token}"}
    # Создание обычного пользователя
    user_response = await client.post("/register", headers=headers , params={
        "last_name": "User3",
        "first_name": "Test3",
        "email": "testuser3@example.com",
        "login": "testuser3",
        "password": "testpassword3",
        "is_supervisor": "no",
        "is_vacation": "no"
    })
    assert user_response.status_code == 200
    # Создание руководителя
    supervisor_response = await client.post("/register", headers=headers, params={
        "last_name": "User44",
        "first_name": "Test44",
        "email": "testuser44@example.com",
        "login": "testuser44",
        "password": "testpassword44",
        "is_supervisor": "yes",
        "is_vacation": "no"
    })
    assert supervisor_response.status_code == 200

@pytest.mark.asyncio
async def test_get_user_by_id(client):
    '''Тест для получения пользователя по ID'''
    register_data = {
        "last_name": "User4",
        "first_name": "Test4",
        "email": "testuser4@example.com",
        "login": "testuser4",
        "password": "testpassword4",
        "is_supervisor": "yes",
        "is_vacation": "no"
    }
    register_response = await client.post("/register", params=register_data)
    assert register_response.status_code == 200
    # Логин пользователя и получение токена
    login_data = {
        "grant_type": "password",
        "username": "testuser4",
        "password": "testpassword4",
    }
    token_response = await client.post("/token", data=login_data)
    assert token_response.status_code == 200
    token_data = token_response.json()
    access_token = token_data["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    id_response = await client.get("/users/me", headers=headers)
    print("response:", id_response)
    user_id = id_response.json().get("id")
    print("response:", user_id)
    response = await client.get(f"/employee/{user_id}", headers=headers)
    print("response:", response)
    assert response.status_code == 200
    user_data = response.json()
    print("User_data:", user_data)
    assert user_data["login"] == "testuser4"

@pytest.mark.asyncio
async def test_update_user(client):
    '''Тест для обновления пользователя'''
    register_data = {
        "last_name": "user5",
        "first_name": "test5",
        "email": "testuser5@example.com",
        "login": "testuser5",
        "password": "testpassword5",
        "is_supervisor": "yes",
        "is_vacation": "no"
    }
    register_response = await client.post("/register", params=register_data)
    assert register_response.status_code == 200
    # Логин пользователя и получение токена
    login_data = {
        "grant_type": "password",
        "username": "testuser5",
        "password": "testpassword5",
    }
    token_response = await client.post("/token", data=login_data)
    assert token_response.status_code == 200
    token_data = token_response.json()
    access_token = token_data["access_token"]
    # Обновление информации о пользователе
    headers = {"Authorization": f"Bearer {access_token}"}
    id_response = await client.get("/users/me", headers=headers)
    print("response:", id_response.text)
    user_id = id_response.json().get("id")
    update_data = {
        "last_name": "updateduser5",
        "first_name": "updatedtest5",
        "email": "updatedtestuser6@example.com",
        "is_supervisor": "no",
        "is_vacation": "no",
    }
    response = await client.put(f"/employee/update?id={user_id}", params=update_data, headers=headers)
    assert response.status_code == 200
    updated_user_data = response.json()
    assert updated_user_data["last_name"] == "updateduser5"
    assert updated_user_data["first_name"] == "updatedtest5"
    assert updated_user_data["email"] == "updatedtestuser6@example.com"
    assert updated_user_data["is_supervisor"] == "no"
    assert updated_user_data["is_vacation"] == "no"

@pytest.mark.asyncio
async def test_delete_user(client):
    '''Тест для удаления пользователя'''
    register_data = {
        "last_name": "updateduser6",
        "first_name": "updatedtest6",
        "login": "deldated",
        "password": "deldated",
        "email": "updatedtestuser6@example.com",
        "is_supervisor": "yes",
        "is_vacation": "no"
    }
    register_response = await client.post("/register", params=register_data)
    assert register_response.status_code == 200
    # Логин пользователя и получение токена
    login_data = {
        "grant_type": "password",
        "username": "deldated",
        "password": "deldated",
    }
    token_response = await client.post("/token", data=login_data)
    assert token_response.status_code == 200
    token_data = token_response.json()
    access_token = token_data["access_token"]
    # Удаление пользователя
    headers = {"Authorization": f"Bearer {access_token}"}
    id_response = await client.get("/users/me", headers=headers)
    print("response:", id_response.text)
    user_id = id_response.json().get("id")
    response = await client.delete(f"/employee/{user_id}", headers=headers)
    assert response.status_code == 200
    assert response.json().get("detail") == "Employee deleted"

@pytest.mark.asyncio
async def test_notify(client: AsyncClient):
    '''Тест на создание проекта и задачи'''
    # Регистрация пользователя-супервизора
    register_data = {
        "last_name": "supervisor1",
        "first_name": "pervisor2",
        "login": "test_supervisor",
        "password": "supervisorpassword",
        "email": "supervisor@example.com",
        "is_supervisor": "yes",
        "is_vacation": "no"
    }
    register_response = await client.post("/register", params=register_data)
    assert register_response.status_code == 200
    # Логин супервизора и получение токена
    login_data = {
        "grant_type": "password",
        "username": "test_supervisor",
        "password": "supervisorpassword",
    }
    token_response = await client.post("/token", data=login_data)
    assert token_response.status_code == 200
    token_data = token_response.json()
    access_token = token_data["access_token"]
    # Заголовки для авторизации
    headers = {"Authorization": f"Bearer {access_token}"}
    # Тест на создание проекта
    project_data = {
        "name": "notifyproject",
        "type": "at work",
    }
    project_response = await client.post("/project/add", headers=headers, params=project_data)
    assert project_response.status_code == 200
    project_id = project_response.json().get("id")
    assert project_response.json().get("name") == "notifyproject"
    # Создание пользователя, которому будет назначена задача
    access_token = token_data["access_token"]
    # Заголовки для авторизации
    headers = {"Authorization": f"Bearer {access_token}"}
    user_response = await client.post(f"{USER_SERVICE_URL}/employee/add", headers=headers, params={
        "last_name": "denis",
        "first_name": "denisov",
        "patronymic": "alexevich",
        "email": "denchik@mail.com",
        "login": "denchik",
        "password": "denchik424",
        "is_supervisor": "no",
        "is_vacation": "no"
    })
    assert user_response.status_code == 200
    user_data = user_response.json()
    print("User data:", user_data)
    user_id = user_data["id"]
    # Тест на создание задачи и назначение её пользователю
    task_data = {
        "title": "test task",
        "description": "This is a test task",
        "due_date": "2024-08-15T12:00:00",
        "user_id": user_id, # Назначаем задачу на работника
        "project_id": project_id ,  # Назначаем задачу проекту
        "type" : "at work"
    }
    task_response = await client.post("/task/add", headers=headers, params=task_data)
    assert task_response.status_code == 200
    assert task_response.json().get("title") == "test task"
    # Запуск уведомления для просроченных задач
    notify_response = await client.post("/notify_due_tasks", headers=headers)
    assert notify_response.status_code == 200
    assert notify_response.json() == {"message": "Notification task has been scheduled"}
    print("Notification response:", notify_response.json())

@pytest.mark.asyncio
async def test_get_employees(client):
    '''Тест для получения всех работников'''
    # Регистрация пользователя с правами супервизора
    supervisor_data = {
        "last_name": "oleg",
        "first_name": "legov",
        "patronymic": "legovxevich",
        "email": "legov@mail.com",
        "login": "legov",
        "password": "legov424",
        "is_supervisor": "no",
        "is_vacation": "no"
    }
    supervisor_response = await client.post("/register", params=supervisor_data)
    assert supervisor_response.status_code == 200

    # Логин супервизора и получение токена
    login_data = {
        "grant_type": "password",
        "username": "legov",
        "password": "legov424",
    }
    token_response = await client.post("/token", data=login_data)
    assert token_response.status_code == 200
    token_data = token_response.json()
    access_token = token_data["access_token"]
    # Запрос на получение всех работников
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.get("/employees", headers=headers)
    assert response.status_code == 200
    # Проверка, что в ответе содержится список работников
    employees_data = response.json()
    assert isinstance(employees_data, list)

@pytest.mark.asyncio
async def test_employees_get_tasks(client: AsyncClient):
    '''Тест на получения работниками списка задач на него'''
    # Регистрация пользователя-супервизора
    register_data = {
        "last_name": "emptask_supervisor",
        "first_name": "emptask_supervisor",
        "patronymic": "emptask_supervisor",
        "email": "emptask_supervisor@mail.com",
        "login": "emptask_supervisor",
        "password": "emptask_supervisor4",
        "is_supervisor": "no",
        "is_vacation": "no"
    }
    register_response = await client.post("/register", params=register_data)
    assert register_response.status_code == 200
    # Логин супервизора и получение токена
    login_data = {
        "grant_type": "password",
        "username": "emptask_supervisor",
        "password": "emptask_supervisor4",
    }
    token_response = await client.post("/token", data=login_data)
    assert token_response.status_code == 200
    token_data = token_response.json()
    access_token = token_data["access_token"]
    # Заголовки для авторизации
    headers = {"Authorization": f"Bearer {access_token}"}
    user_response = await client.post(f"{USER_SERVICE_URL}/employee/add", headers=headers, params={
        "last_name": "getlist",
        "first_name": "getlist",
        "patronymic": "agetlistich",
        "email": "getlist@mail.com",
        "login": "getlist",
        "password": "getlist424",
        "is_supervisor": "no",
        "is_vacation": "no"
    })
    assert user_response.status_code == 200
    user_data = user_response.json()
    user_id = user_data["id"]
    # Тест на создание проекта
    project_data = {
        "name": "emptaskprojectfortask",
        "type": "at work",
    }
    project_response = await client.post("/project/add", headers=headers, params=project_data)
    assert project_response.status_code == 200
    project_id = project_response.json().get("id")
    assert project_response.json().get("name") == "emptaskprojectfortask"
    # Тест на создание задачи и назначение её пользователю
    task_one = {
        "title": "taskoneprojectfortask task",
        "description": "This is a test task for oneprojectfortask",
        "due_date": "2024-10-15T08:00:00",
        "actual_due_date": "2024-11-15T08:00:00",
        "hours_spent": 150,  # Передаем как целое число
        "user_id" : user_id, # Назначаем задачу на пользователя
        "project_id": project_id,  # Назначаем задачу проекту
        "type": "at work"  # Передаем тип задачи как строку
    }
    task_response = await client.post("/task/add", headers=headers, params=task_one)
    assert task_response.status_code == 200
    assert task_response.json().get("title") == "taskoneprojectfortask task"
    task_two = {
        "title": "tasktwoprojectfortask task",
        "description": "This is a test task for twoprojectfortask",
        "due_date": "2024-11-16T08:00:00",
        "actual_due_date": "2024-12-16T08:00:00",
        "hours_spent": 150,  # Передаем как целое число
        "user_id" : user_id, # Назначаем задачу на пользователя
        "project_id": project_id,  # Назначаем задачу проекту
        "type": "at work"  # Передаем тип задачи как строку
    }
    task_response = await client.post("/task/add", headers=headers, params=task_two)
    assert task_response.status_code == 200
    assert task_response.json().get("title") == "tasktwoprojectfortask task"
    list_data = {
        "user_id" : user_id
    }
    list_response = await client.get(f"/task/search?user_id={user_id}", headers=headers, params=list_data)
    assert list_response.status_code == 200
    assert task_response.json().get("user_id") == user_id

@pytest.mark.asyncio
async def test_get_user_without_token(client):
    '''Тест на попытку получить данные пользователя без токена'''
    # Пытаемся получить данные пользователя без токена авторизации
    response = await client.get("/employees")
    assert response.status_code == 401  # Ожидаем ошибку 401
    assert "Not authenticated" in response.json().get("detail")

@pytest.mark.asyncio
async def test_delete_nonexistent_user(client):
    '''Тест на попытку удалить несуществующего пользователя'''
    # Логин с существующим пользователем
    register_data = {
        "last_name": "nonexistent",
        "first_name": "nonexistent",
        "patronymic": "nonexistent",
        "email": "nonexistent@mail.com",
        "login": "nonexistent",
        "password": "nonexistent4",
        "is_supervisor": "yes",
        "is_vacation": "no"
    }
    register_response = await client.post("/register", params=register_data)
    assert register_response.status_code == 200
    # Логин супервизора и получение токена
    login_data = {
        "grant_type": "password",
        "username": "nonexistent",
        "password": "nonexistent4",
    }
    token_response = await client.post("/token", data=login_data)
    assert token_response.status_code == 200
    token_data = token_response.json()
    access_token = token_data["access_token"]
    # Пытаемся удалить несуществующего пользователя
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.delete("/users/99999", headers=headers)  # ID пользователя, которого нет
    assert response.status_code == 404  # Ожидаем ошибку 404
    assert "Not Found" in response.json().get("detail")

@pytest.mark.asyncio
async def test_register_user_with_existing_username(client):
    '''Тест на регистрацию пользователя с уже существующим именем'''
    # Регистрируем пользователя
    register_data = {
        "last_name": "existing",
        "first_name": "existing",
        "patronymic": "existing",
        "email": "testuser@example.com",
        "login": "existing21",
        "password": "existing421",
        "is_supervisor": "yes",
        "is_vacation": "no"
    }
    await client.post("/register", params=register_data)
    # Пытаемся зарегистрировать пользователя с таким же именем
    register_response = await client.post("/register", params=register_data)
    assert register_response.status_code == 422  # Ожидаем, что запрос вернёт ошибку

@pytest.mark.asyncio
async def test_login_with_invalid_credentials(client):
    '''Тест на попытку входа с неверными учетными данными'''
    # Неправильные данные для входа
    login_data = {
        "grant_type": "password",
        "username": "nonexistentuser",
        "password": "wrongpassword",
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    token_response = await client.post("/token", data=login_data, headers=headers)
    assert token_response.status_code in [400, 401]
    if token_response.status_code == 400:
        assert "Неправильный логин или пароль" in token_response.text
    elif token_response.status_code == 401:
        assert "Неправильный логин или пароль" in token_response.text

@pytest.mark.asyncio
async def test_update_user_with_invalid_token(client):
    '''Тест на попытку обновить данные пользователя с недействительным токеном'''
    # Регистрируем пользователя
    register_data = register_data = {
        "last_name": "invalidstent",
        "first_name": "invalidstent",
        "patronymic": "invalidstent",
        "email": "invalidstent@mail.com",
        "login": "invalidstent",
        "password": "invalidstent4",
        "is_supervisor": "yes",
        "is_vacation": "no"
    }
    register_response = await client.post("/register", params=register_data)
    assert register_response.status_code == 200
    # Пытаемся обновить данные пользователя с неправильным токеном
    headers = {"Authorization": "Bearer invalidtoken"}
    update_data = {
        "username": "updateduser",
        "email": "updateduser@example.com",
        "is_supervisor": "yes",
        "is_vacation": "no",
    }
    response = await client.put(f"/employee/update?id={register_response.json().get('id')}", params=update_data, headers=headers)
    assert response.status_code == 401  # Ожидаем ошибку 401
    assert "Could not validate credentials" in response.json().get("detail")

@pytest.mark.asyncio
async def test_add_employee_with_missing_fields(client):
    '''Тест на попытку добавить работника с отсутствующими полями'''
    # Логин с существующим пользователем
    login_data = {
        "grant_type": "password",
        "username": "invalidstent",
        "password": "invalidstent4",
    }
    token_response = await client.post("/token", data=login_data)
    assert token_response.status_code == 200
    token_data = token_response.json()
    access_token = token_data["access_token"]
    # Пытаемся добавить работника без обязательного поля email
    employee_data = {
        "last_name": "employee2",
        "first_name": "employee two",
        # Пропускаем поле email
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.post("/employee/add", params=employee_data, headers=headers)
    assert response.status_code == 422  # Ожидаем ошибку 422 (Unprocessable Entity)
    assert "Field required" in response.json()["detail"][0]["msg"]

@pytest.mark.asyncio
async def test_create_task_with_invalid_project(client):
    '''Тест на создание задачи с несуществующим проектом'''
    # Логин с существующим пользователем
    login_data = {
        "grant_type": "password",
        "username": "invalidstent",
        "password": "invalidstent4",
    }
    token_response = await client.post("/token", data=login_data)
    assert token_response.status_code == 200
    token_data = token_response.json()
    access_token = token_data["access_token"]
    # Пытаемся создать задачу для несуществующего проекта
    task_data = {
        "title": "invalid task",
        "description": "This task should fail",
        "due_date": "2024-09-15T08:00:00",
        "project_id": 444,  # Несуществующий ID проекта
        "type": "at work"
    }
    headers = {"Authorization": f"Bearer {access_token}"}
    response = await client.post("/task/add", params=task_data, headers=headers)
    assert response.status_code == 404  # Ожидаем ошибку 404
    assert "Object does not exist" in response.json().get("detail")