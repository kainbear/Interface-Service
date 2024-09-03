'''graphql_schema.py'''

from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException
import httpx
import strawberry
from strawberry.fastapi import GraphQLRouter

USER_SERVICE_URL = "http://user-service:8003"
TASK_SERVICE_URL = "http://task-service:8002"

@strawberry.type
class EmployeesType:
    '''Класс Работника'''
    id: int
    last_name: str
    first_name: str
    patronymic: str
    email: str
    login: str
    password: str
    is_supervisor: str
    is_vacation: str

@strawberry.type
class VacationsType:
    '''Класс Вакансии'''
    id: int
    employee_id: int
    type: str
    start_date: str
    end_date: str

@strawberry.type
class SubdivisionsType:
    '''Класс Подразделения'''
    id: int
    name: str
    leader_id: int
    employee_ids: List[int]

@strawberry.type
class ProjectsType:
    '''Класс Проекта'''
    id: int
    name: str
    type: str

@strawberry.type
class TaskType:
    '''Класс Задач'''
    id: int
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None
    actual_due_date: Optional[str] = None
    hours_spent: Optional[str] = None
    user_id: Optional[int] = None
    project_id: Optional[int] = None
    type: Optional[str] = None

@strawberry.type
class Query:
    '''Класс Запроса '''
    @strawberry.field
    async def all_employees(self) -> List[EmployeesType]:
        '''Функция для получения всех работников'''
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{USER_SERVICE_URL}/employee/get_all")
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code,
                                    detail="Could not fetch users")
            return [EmployeesType(**user) for user in response.json()]

    @strawberry.field
    async def all_vacations(self) -> List[VacationsType]:
        '''Функция для получения всех вакансий'''
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{USER_SERVICE_URL}/business_and_vacations/get_all")
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code,
                                    detail="Could not fetch vacations")
            return [VacationsType(**vacation) for vacation in response.json()]

    @strawberry.field
    async def all_subdivisions(self) -> List[SubdivisionsType]:
        '''Функция для получения всех подразделений'''
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{USER_SERVICE_URL}/subdivision/get_all")
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code,
                                    detail="Could not fetch subdivisions")
            subdivisions = response.json()
            # Проверяем наличие 'employee_ids' в каждом подразделении
            for subdivision in subdivisions:
                if "employee_ids" not in subdivision:
                    raise ValueError(f"'employee_ids' key is missing in the subdivision: {subdivision}")
            # Возвращаем список подразделений
            return [
                SubdivisionsType(
                    id=subdivision["id"],
                    name=subdivision["name"],
                    leader_id=subdivision["leader_id"],
                    employee_ids=subdivision.get("employee_ids", [])
                )
                for subdivision in subdivisions
            ]

    @strawberry.field
    async def all_projects(self) -> List[ProjectsType]:
        '''Функция для получения всех проектов'''
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{TASK_SERVICE_URL}/project/read_all")
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code,
                                    detail="Could not fetch projects")
            return [ProjectsType(**project) for project in response.json()]

    @strawberry.field
    async def all_task(self) -> List[TaskType]:
        '''Функция для получения задач'''
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{TASK_SERVICE_URL}/task/read_all")
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code,
                                    detail="Could not fetch tasks")
            return [TaskType(**task) for task in response.json()]

@strawberry.input
class EmployeeCreateInput:
    '''Класс Работника'''
    last_name: str
    first_name: str
    patronymic: str
    email: str
    login: str
    password: str
    is_supervisor: str
    is_vacation: str

@strawberry.input
class VacationCreateInput:
    '''Класс Вакансии'''
    employee_id: int
    type: str
    start_date: str
    end_date: str

@strawberry.input
class SubdivisionCreateInput:
    '''Класс Подразделения'''
    name: str
    leader_id: int


@strawberry.input
class ProjectCreateInput:
    '''Класс Проекта'''
    name: str
    type: str

@strawberry.input
class TaskCreateInput:
    '''Класс Задачи'''
    title: str
    description: str
    due_date: datetime
    actual_due_date: Optional[datetime] = None
    hours_spent: Optional[int] = None
    user_id: Optional[int] = None
    project_id: int
    type: str

@strawberry.type
class Mutation:
    '''Класс Мутаций'''
    @strawberry.mutation
    async def create_employee(self, input: EmployeeCreateInput) -> EmployeesType:
        '''Функция для создания работника'''
        async with httpx.AsyncClient() as client:
            input_params = {
                "last_name": input.last_name,
                "first_name": input.first_name,
                "patronymic": input.patronymic,
                "email": input.email,
                "login": input.login,
                "password": input.password,
                "is_supervisor": input.is_supervisor,
                "is_vacation": input.is_vacation
            }
            print(f"Sending data: {input_params}")  # Логирование данных
            # Отправка POST-запроса с параметрами в строке запроса
            response = await client.post(f"{USER_SERVICE_URL}/employee/add", params=input_params)
            if response.status_code == 200:
                employee_data = response.json()
                return EmployeesType(**employee_data)
            else:
                error_details = response.text
                print(f"Error details: {error_details}")  # Логирование ошибок
                raise HTTPException(status_code=response.status_code,
                                    detail=f"Could not create employee: {error_details}")

    @strawberry.mutation
    async def create_vacation(self, input: VacationCreateInput) -> VacationsType:
        '''Функция для создания отпуска/командировка'''
        async with httpx.AsyncClient() as client:
            input_dict = input.__dict__
            response = await client.post(f"{USER_SERVICE_URL}/business_and_vacations/add",
                                         params=input_dict)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code,
                                    detail="Could not create vacation")
            vacation_data = response.json()
            return VacationsType(**vacation_data)

    @strawberry.mutation
    async def create_subdivision(self, input: SubdivisionCreateInput) -> SubdivisionsType:
        '''Функция для создания подразделения'''
        async with httpx.AsyncClient() as client:
            input_dict = input.__dict__
            response = await client.post(f"{USER_SERVICE_URL}/subdivision/add", params=input_dict)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code,
                                    detail="Could not create subdivision")
            
            subdivision_data = response.json()
            
            # Убедитесь, что employee_ids присутствует в данных или задайте его по умолчанию
            if 'employee_ids' not in subdivision_data:
                subdivision_data['employee_ids'] = []

            return SubdivisionsType(**subdivision_data)

    @strawberry.mutation
    async def create_project(self, input: ProjectCreateInput) -> ProjectsType:
        '''Функция для создания проекта'''
        async with httpx.AsyncClient() as client:
            input_dict = input.__dict__
            response = await client.post(f"{TASK_SERVICE_URL}/project/add", params=input_dict)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code,
                                    detail="Could not create project")
            project_data = response.json()
            return ProjectsType(**project_data)

    @strawberry.mutation
    async def create_task(self, input: TaskCreateInput) -> TaskType:
        '''Функция для создания задачи'''
        async with httpx.AsyncClient() as client:
            task_dict = input.__dict__
            task_dict['due_date'] = input.due_date.isoformat()
            if input.actual_due_date:
                task_dict['actual_due_date'] = input.actual_due_date.isoformat()
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
            task_data = response.json()
            return TaskType(**task_data)

schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema)
