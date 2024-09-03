'''router.py'''

from typing import Annotated, List, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends, Path, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import httpx
import jwt
import email_service
from schemas import Employee, EmployeeAdd, EmployeeUpdate
from schemas import ProjectBase, ProjectCreate, ProjectResponse
from schemas import Task, TaskCreate, TaskUpdate, Token
from schemas import VacationAdd, VacationUpdate, SubdivisionLeaderUpdate

# Определите SECRET_KEY и ALGORITHM такие же, как в user-service
SECRET_KEY = "kains"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# Конфигурация URL-ов первых двух сервисовё
USER_SERVICE_URL = "http://45.92.176.81:44444"
TASK_SERVICE_URL = "http://45.92.176.81:44445"

# Функция для проверки, что пользователь аутентифицирован
async def user_logined(token: str = Depends(oauth2_scheme)) -> Employee:
    '''Функция для подтверждения аутентификации пользователя'''
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Декодируем JWT токен
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    # Запрос данных о пользователе в user-service по login
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_SERVICE_URL}/employee/users/me",
                                    params={"login": username})
        if response.status_code == 200:
            user_data = response.json()
            return Employee(**user_data)  # Преобразование JSON в объект Employee
        else:
            raise credentials_exception

authentication_router = APIRouter()

@authentication_router.get("/users/me")
async def read_users_me(current_user: Employee = Depends(user_logined)):
    '''Функция для подтверждения аутентификации пользователя'''
    return {"id": current_user.id,"username": current_user.login,"email": current_user.email}

@authentication_router.post("/register", response_model=Token)
async def register(user: Annotated[EmployeeAdd , Depends()]):
    '''Эндпоинт для регистрации через user-service'''
    params = {
        "last_name": user.last_name,
        "first_name": user.first_name,
        "patronymic": user.patronymic,
        "email": user.email,
        "login": user.login,
        "password": user.password,
        "is_supervisor": user.is_supervisor.value,
        "is_vacation": user.is_vacation.value
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{USER_SERVICE_URL}/employee/register", params=params)
        if response.status_code == 200:
            token_data = response.json()
            return {"access_token": token_data["access_token"], "token_type": "bearer"}
        else:
            raise HTTPException(status_code=response.status_code,
                                detail=response.json().get("detail", "Registration failed"))

@authentication_router.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    '''Эндпоинт для логина через user-service'''
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{USER_SERVICE_URL}/employee/token", data={
            'username': form_data.username,
            'password': form_data.password
        })
        if response.status_code == 200:
            token_data = response.json()
            return {"access_token": token_data["access_token"], "token_type": "bearer"}
        else:
            raise HTTPException(status_code=response.status_code,
                                detail=response.json().get("detail", "Login failed"))

@authentication_router.post("/notify_due_tasks")
async def notify_due_tasks(background_tasks: BackgroundTasks, current_user: Employee = Depends(user_logined)):
    '''Эндпоинт для уведомления пользователя на имейл'''
    background_tasks.add_task(email_service.check_due_tasks, current_user.email)
    return {"message": "Notification task has been scheduled"}

employee_router = APIRouter()

@employee_router.get("/employees", dependencies=[Depends(user_logined)])
async def get_employees():
    '''Функция для получения всех работников'''
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_SERVICE_URL}/employee/get_all")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Could not fetch users")
        return response.json()

@employee_router.get("/employee/{user_id}", dependencies=[Depends(user_logined)])
async def get_employee(user_id: int):
    '''Функция для получения конкретного работника'''
    if user_id <= 0:
        raise HTTPException(status_code=400, detail="Invalid user ID")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_SERVICE_URL}/employee/{user_id}")
        print("response:", response)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Could not fetch user")
        return response.json()

@employee_router.post("/employee/add", dependencies=[Depends(user_logined)], response_model=Employee)
async def add_employee(employee: Annotated[EmployeeAdd, Depends()]):
    '''Функция создания работника'''
    async with httpx.AsyncClient() as client:
        employee_dict = employee.model_dump(exclude_none=True)
        employee_dict['email'] = employee.email.format()
        employee_dict['is_supervisor'] = employee.is_supervisor.value
        employee_dict['is_vacation'] = employee.is_vacation.value
        params = {k: v for k, v in employee_dict.items() if v is not None}
        response = await client.post(
            f"{USER_SERVICE_URL}/employee/add",
            params=params
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code,
                                detail="Could not create employee")
        return response.json()

@employee_router.put("/employee/update", dependencies=[Depends(user_logined)], response_model = Employee)
async def update_employee(id: int, employee: Annotated[EmployeeUpdate, Depends()]):
    """Функция для обновления работника"""
    async with httpx.AsyncClient() as client:
        employee_dict = employee.model_dump(exclude_none=True)
        response = await client.put(
            f"{USER_SERVICE_URL}/employee/update",
            params={"id": id, **employee_dict}
        )
        if response.status_code != 200:
            try:
                error_detail = response.json()
            except Exception:
                error_detail = response.text
            raise HTTPException(status_code=response.status_code,
                                detail=f"Could not updated employee: {error_detail}")
        return response.json()

@employee_router.delete("/employee/{id}", dependencies=[Depends(user_logined)])
async def delete_employee(id: int):
    '''Функция для удаления работника'''
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{USER_SERVICE_URL}/employee/{id}")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Not found employee")
        return response.json()

@employee_router.get("/subdivision/get_all", dependencies=[Depends(user_logined)])
async def read_all_subdivision():
    '''Функция получения подразделения'''
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_SERVICE_URL}/subdivision/get_all")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Could not get subdivision")
        return response.json()

@employee_router.get("/subdivision/{subdivision_id}", dependencies=[Depends(user_logined)])
async def read_subdivision(subdivision_id: int):
    '''Функция получения подразделения'''
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_SERVICE_URL}/subdivision/{subdivision_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Could not found subdivision")
        return response.json()

@employee_router.post("/subdivision/add", dependencies=[Depends(user_logined)])
async def add_subdivision(subdivision: Annotated[SubdivisionLeaderUpdate, Depends()]):
    '''Функция создания подразделения'''
    async with httpx.AsyncClient() as client:
        subdivision_dict = subdivision.model_dump(exclude_none=True)
        response = await client.post(
            f"{USER_SERVICE_URL}/subdivision/add",
            params=subdivision_dict
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code,
                                detail="Could not create subdivision")
        return response.json()

@employee_router.put("/subdivision/update/{subdivision_id}", dependencies=[Depends(user_logined)])
async def update_subdivision(subdivision_id: int,name: str,):
    '''Функция обновления подразделения'''
    async with httpx.AsyncClient() as client:
        params = {
            "subdivision_id": subdivision_id,
            "name": name,
        }
        response = await client.put(f"{USER_SERVICE_URL}/subdivision/update/{subdivision_id}",
                                    params=params)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code,
                                detail="Could not update subdivision")
        return response.json()

@employee_router.put("/subdivision/{subdivision_id}/assign_leader/{leader_id}", dependencies=[Depends(user_logined)])
async def assign_leader(
    subdivision_id: int,
    leader_id: int = Path(..., description="ID руководителя (является ID сотрудника)")):
    '''Функция обновления руководителя подразделения'''
    async with httpx.AsyncClient() as client:
        params = {
            "subdivision_id": subdivision_id,
            "leader_id_id": leader_id,
        }
        response = await client.put(f"{USER_SERVICE_URL}/subdivision/{subdivision_id}/assign_leader/{leader_id}",params=params)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code,
                                detail="Could assign leader to subdivision")
        return response.json()

@employee_router.put("/subdivision/assign_employee", dependencies=[Depends(user_logined)])
async def assign_employee_to_subdivision(
    subdivision_id: int = Query(..., description="ID Subdivision"),
    employee_id: int = Query(..., description="ID Employee")):
    '''Функция добновления работника к подразделению'''
    async with httpx.AsyncClient() as client:
        params = {
            "subdivision_id": subdivision_id,
            "employee_id": employee_id,
        }
        response = await client.put(f"{USER_SERVICE_URL}/subdivision/assign_employee",params=params)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code,
                                detail="Could assign employee to subdivision")
        return response.json()

@employee_router.delete("/subdivision/{subdivision_id}/employee/{employee_id}", dependencies=[Depends(user_logined)])
async def remove_employee_from_subdivision(subdivision_id: int,employee_id: int):
    '''Функция для удаления работника от подразделения'''
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{USER_SERVICE_URL}/subdivision/{subdivision_id}/employee/{employee_id}")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Not found subdivision")
        return response.json()

@employee_router.delete("/subdivision/{id}", dependencies=[Depends(user_logined)])
async def delete_subdivision(id: int):
    '''Функция для удаления подразделения'''
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{USER_SERVICE_URL}/subdivision/{id}")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Not found subdivision")
        return response.json()

@employee_router.get("/vacation/get_all", dependencies=[Depends(user_logined)])
async def get_all_vacations():
    '''Функция получения всех отпусков и командировок'''
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_SERVICE_URL}/business_and_vacations/get_all")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Could not fetch projects")
        return response.json()

@employee_router.get("/vacation/search", dependencies=[Depends(user_logined)])
async def get_employees_with_vacations(
    employee_id: Optional[int] = Query(default=None),
    type: Optional[str] = Query(..., description="Type of leave: 'vacation' or 'business'"),
):
    '''Функция для получения списка отпуска или командировок на работника'''
    async with httpx.AsyncClient() as client:
        params = {
            "employee_id": employee_id,
            "type": type,
        }
        params = {k: v for k, v in params.items() if v is not None}
        response = await client.get(
            f"{USER_SERVICE_URL}/business_and_vacations/search",
            params=params
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code,detail="Not Found")
        return response.json()
    
@employee_router.post("/vacation/add", dependencies=[Depends(user_logined)])
async def add_vacations_or_business(
    vacation: Annotated[VacationAdd, Depends()],
    type: str = Query(default=None, description="Type of leave: 'vacation' or 'business'")):
    '''Функция для создания отпуска или командировки'''
    async with httpx.AsyncClient() as client:
        vacation_dict = vacation.model_dump()
        vacation_dict['start_date'] = vacation.start_date.isoformat()
        if vacation.end_date:
            vacation_dict['end_date'] = vacation.end_date.isoformat()
        vacation_dict['type'] = vacation_dict['type'].value
        params = {k: v for k, v in vacation_dict.items() if v is not None}
        response = await client.post(
            f"{USER_SERVICE_URL}/business_and_vacations/add",
            params=params
        )
        if response.status_code != 200:
            try:
                error_detail = response.json()
            except Exception:
                error_detail = response.text
            raise HTTPException(status_code=response.status_code,
                                detail=f"Could not create task: {error_detail}")
        return response.json()

@employee_router.put("/vacation/update", dependencies=[Depends(user_logined)])
async def update_vacations_or_business(id: int, vacation: Annotated[VacationUpdate, Depends()]):
    '''Функция для обновления отпуска или командировки'''
    async with httpx.AsyncClient() as client:
        vacation_dict = vacation.model_dump(exclude_none=True)
        if 'start_date' in vacation_dict:
            vacation_dict['start_date'] = vacation_dict['start_date'].isoformat()
        if 'end_date' in vacation_dict:
            vacation_dict['end_date'] = vacation_dict['end_date'].isoformat()
        vacation_dict['type'] = vacation_dict['type'].value
        response = await client.put(
            f"{USER_SERVICE_URL}/business_and_vacations/update",
            params={"id": id, **vacation_dict}
        )
        if response.status_code != 200:
            try:
                error_detail = response.json()
            except Exception:
                error_detail = response.text
            raise HTTPException(status_code=response.status_code,
                                detail=f"Could not updated task: {error_detail}")
        return response.json()

@employee_router.delete("/vacation/{id}", dependencies=[Depends(user_logined)])
async def delete_vacations_or_business(id: int):
    '''Функция для удаления отпуска или командировки'''
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{USER_SERVICE_URL}/business_and_vacations/{id}")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Could not delete task")
        return response.json()

project_router = APIRouter()
task_router = APIRouter()

@project_router.get("/project/read_all", dependencies=[Depends(user_logined)])
async def read_all_projects():
    '''Функция получения всех проектов'''
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{TASK_SERVICE_URL}/project/read_all")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Could not fetch projects")
        return response.json()

@project_router.post("/project/add", response_model=ProjectResponse, dependencies=[Depends(user_logined)])
async def create_project(project: Annotated[ProjectCreate, Depends()]):
    '''Функция создания проектов'''
    async with httpx.AsyncClient() as client:
        project_dict = project.model_dump()
        response = await client.post(
            f"{TASK_SERVICE_URL}/project/add",
            params=project_dict
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Could not create project")
        return response.json()

@project_router.put("/project/update", dependencies=[Depends(user_logined)])
async def update_project(id: int, project: Annotated[ProjectBase, Depends()]):
    '''Функция обновления проектов'''
    async with httpx.AsyncClient() as client:
        project_dict = project.model_dump()
        response = await client.put(
            f"{TASK_SERVICE_URL}/project/update",
            params={"id": id, **project_dict}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Could not update project")
        return response.json()

@project_router.delete("/project/{id}", dependencies=[Depends(user_logined)])
async def delete_project(id: int):
    '''Функция для удаления проекта'''
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{TASK_SERVICE_URL}/project/{id}")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Could not delete project")
        return response.json()

@task_router.get("/task/read_all", dependencies=[Depends(user_logined)])
async def read_all_tasks():
    '''Функция для получения всех задач'''
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{TASK_SERVICE_URL}/task/read_all")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Could not fetch tasks")
        return response.json()

@task_router.post("/task/add", response_model=TaskCreate, dependencies=[Depends(user_logined)])
async def create_task(task: Annotated[TaskCreate, Depends()]):
    '''Функция для создания задачи'''
    async with httpx.AsyncClient() as client:
        task_dict = task.model_dump()
        task_dict['due_date'] = task.due_date.isoformat()
        if task.actual_due_date:
            task_dict['actual_due_date'] = task.actual_due_date.isoformat()
        task_dict['type'] = task_dict['type'].value
        params = {k: v for k, v in task_dict.items() if v is not None}
        response = await client.post(
            f"{TASK_SERVICE_URL}/task/add",
            params=params
        )
        if response.status_code != 200:
            try:
                error_detail = response.json()
            except Exception:
                error_detail = response.text
            raise HTTPException(status_code=response.status_code, detail=f"Could not create task: {error_detail}")
        return response.json()

@task_router.get("/task/search", response_model=List[Task], dependencies=[Depends(user_logined)])
async def search_task(
    id: Optional[int] = Query(default=None),
    title: Optional[str] = Query(default=None),
    description: Optional[str] = Query(default=None),
    user_id: Optional[int] = Query(default=None),
    project_id: Optional[int] = Query(default=None),
    project: Optional[str] = Query(default=None),
):
    '''Функция для поиска задач'''
    async with httpx.AsyncClient() as client:
        params = {
            "id": id,
            "title": title,
            "description": description,
            "user_id": user_id,
            "project_id": project_id,
            "project": project,
        }
        params = {k: v for k, v in params.items() if v is not None}
        response = await client.get(
            f"{TASK_SERVICE_URL}/task/search",
            params=params
        )
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code,detail="Not Found")
        return response.json()

@task_router.put("/task/update", response_model=TaskUpdate, dependencies=[Depends(user_logined)])
async def update_task(id: int, task: Annotated[TaskUpdate, Depends()]):
    '''Функция для обновления задачи'''
    async with httpx.AsyncClient() as client:
        task_dict = task.model_dump(exclude_none=True)
        if 'due_date' in task_dict:
            task_dict['due_date'] = task_dict['due_date'].isoformat()
        if 'actual_due_date' in task_dict:
            task_dict['actual_due_date'] = task_dict['actual_due_date'].isoformat()
        task_dict['type'] = task_dict['type'].value
        response = await client.put(
            f"{TASK_SERVICE_URL}/task/update",
            params={"id": id, **task_dict}
        )
        if response.status_code != 200:
            try:
                error_detail = response.json()
            except Exception:
                error_detail = response.text
            raise HTTPException(status_code=response.status_code, detail=f"Could not updated task: {error_detail}")
        return response.json()

@task_router.delete("/task/{id}", dependencies=[Depends(user_logined)])
async def delete_task(id: int):
    '''Функция для удаления задачи'''
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{TASK_SERVICE_URL}/task/{id}")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Could not delete task")
        return response.json()