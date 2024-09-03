'''schemas.py'''

from enum import Enum
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

class Token(BaseModel):
    '''Класс Токена'''
    access_token: str
    token_type: str

class TokenData(BaseModel):
    '''Класс Токен Памяти Пользователя'''
    username: str | None = None

# Определение схем и моделей
class ProjectType(str, Enum):
    '''Класс схемы статуса выполнения проекта'''
    ATWORK = 'at work'
    COMPLITED = 'completed'
    FAILED = 'failed'

class ProjectBase(BaseModel):
    '''Класс модели проекта'''
    name: str
    type: str = Field(description="Type of project: 'at work', 'completed', 'failed'")

    @field_validator('name')
    def to_lower(cls, v):
        return v.lower() if isinstance(v, str) else v

class ProjectCreate(ProjectBase):
    '''Класс модели проекта создания'''
    name: str
    type: str

class ProjectResponse(ProjectBase):
    '''Класс модели проекта айди'''
    id: int
    name : str
    type: str = Field(description="Type of project: 'at work', 'completed', 'failed'") 

class Project(ProjectBase):
    '''Класс модели проекта айди'''
    id: int

    class ConfigDict:
        '''Класс конфига проекта'''
        from_attributes = True

class ProjectResponse(BaseModel):
    '''Класс модели проекта response'''
    id: int
    name: str
    type: str

class TaskType(str, Enum):
    '''Класс схемы статуса выполнения задачи'''
    ATWORK = 'at work'
    COMPLITED = 'completed'
    FAILED = 'failed'

class TaskBase(BaseModel):
    '''Класс модели задачи и зависимости'''
    title: str
    description: str
    due_date: datetime
    actual_due_date: datetime | None = None
    hours_spent: int = 0
    user_id: int | None = None
    project_id: Optional[int] = None
    type: TaskType = Field(description="Type of task: 'at work', 'completed', 'failed'")

    @field_validator('title', 'description')
    def to_lower(cls, v):
        return v.lower() if isinstance(v, str) else v

class TaskUpdate(BaseModel):
    '''Класс модели обновления задачи'''
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    actual_due_date: Optional[datetime] = None
    hours_spent: Optional[int] = None
    user_id: Optional[int] = None
    project_id: Optional[int] = None
    type: TaskType = Field(description="Type of task: 'at work', 'completed', 'failed'")

    @field_validator('title', 'description')
    def to_lower(cls, v):
        return v.lower() if isinstance(v, str) else v

class TaskCreate(BaseModel):
    '''Класс модели создания задачи'''
    title: str
    description: str
    due_date: datetime
    actual_due_date: datetime | None = None
    hours_spent: int = 0
    user_id: int | None = None
    project_id: int
    type: TaskType = Field(description="Type of task: 'at work', 'completed', 'failed'")

    @field_validator('title', 'description')
    def to_lower(cls, v):
        return v.lower() if isinstance(v, str) else v

    class Meta:
        '''Класс таблицы задач'''
        table = "tasks"

class Task(TaskBase):
    '''Класс модели проекта к задаче'''
    id: int
    project: Project

    @field_validator('title', 'description')
    def to_lower(cls, v):
        return v.lower() if isinstance(v, str) else v

    class ConfigDict:
        '''Класс модели конфига задачи'''
        from_attributes = True

class YesNo(str, Enum):
    '''Класс схемы отпуска и командировки для уточнения'''
    YES = 'yes'
    NO = 'no'

class Employee(BaseModel):
    '''Класс схемы работника'''
    id: int
    last_name: str | None = None
    first_name: str | None = None
    patronymic: str | None = None
    email: EmailStr | None = None
    login:str | None = None
    password:str | None = None
    is_supervisor : YesNo  = Field(description="Type of string: 'yes' or 'no'")
    is_vacation : YesNo  = Field(description="Type of string: 'yes' or 'no'")

    @field_validator('last_name', 'first_name', 'patronymic', 'email', 'login')
    def to_lower(cls, v):
        '''Функция для смены регистра в нижний предел'''
        return v.lower() if isinstance(v, str) else v

    class ConfigDict:
        '''Класс настройки'''
        from_attributes = True

class EmployeeAdd(BaseModel):
    '''Класс схемы работника для добавления'''
    last_name: str
    first_name: str
    patronymic: str | None = None
    email: EmailStr
    login:str | None = None
    password:str | None = None
    is_supervisor : YesNo  = Field(description="Type of string: 'yes' or 'no'")
    is_vacation : YesNo  = Field(description="Type of string: 'yes' or 'no'")

    @field_validator('last_name', 'first_name', 'patronymic', 'email', 'login')
    def to_lower(cls, v):
        '''Функция для смены регистра в нижний предел'''
        return v.lower() if isinstance(v, str) else v

class EmployeeUpdate(BaseModel):
    '''Класс схемы работника для обновления'''
    id : int
    last_name: str | None = None
    first_name: str | None = None
    patronymic: str | None = None
    email: EmailStr | None = None
    login:str | None = None
    password:str | None = None
    is_supervisor : str
    is_vacation : str

    @field_validator('last_name', 'first_name', 'patronymic', 'email', 'login')
    def to_lower(cls, v):
        '''Функция для смены регистра в нижний предел'''
        return v.lower() if isinstance(v, str) else v

class EmployeeSearch(BaseModel):
    '''Класс схемы работника для поиска'''
    last_name: str | None = None
    first_name: str | None = None
    patronymic: str | None = None
    email: EmailStr | None = None
    login:str | None = None

    @field_validator('last_name', 'first_name', 'patronymic', 'email', 'login')
    def to_lower(cls, v):
        '''Функция для смены регистра в нижний предел'''
        return v.lower() if isinstance(v, str) else v

class EmployeeDelete(BaseModel):
    '''Класс схемы работника для удаления'''
    id:int

class VacationType(str, Enum):
    '''Класс схемы отпуска и командировки для уточнения'''
    VACATION = 'vacation'
    BUSINESS = 'business'

class Vacation(BaseModel):
    '''Класс схемы отпуска или командировки'''
    id: int
    employee_id : int | None = None
    type: VacationType = Field(description="Type of string: 'vacation' or 'business'")
    start_date: date | None = None
    end_date: date | None = None

class EmployeeWithVacations(BaseModel):
    '''Класс схемы отпуска или командировки с работником'''
    id: int
    last_name: Optional[str]
    first_name: Optional[str]
    patronymic: Optional[str]
    email: Optional[str]
    login: Optional[str]
    password: Optional[str]
    vacations: List[Vacation]

    class ConfigDict:
        '''Класс настройки для схемы отпуска или командировки с работником'''
        from_attributes = True

class VacationAdd(BaseModel):
    '''Класс схемы отпуска или командировки,для добавления'''
    employee_id: int
    type: VacationType = Field(description="Type of string: 'vacation' or 'business'")
    start_date: date | None = None
    end_date: date | None = None

class VacationUpdate(BaseModel):
    '''Класс схемы отпуска или командировки,дял обновления'''
    id: int
    employee_id: int | None = None
    type: VacationType = Field(description="Type of string: 'vacation' or 'business'")
    start_date: date | None = None
    end_date: date | None = None

class VacationDelete(BaseModel):
    '''Класс схемы отпуска или командировки для удаления'''
    id:int

class Subdivision(BaseModel):
    '''Класс схемы подразделения'''
    id: int
    name: str
    leader_id: int | None = None
    employee_ids: List[int]

    @field_validator('name')
    def to_lower(cls, v):
        '''Функция для смены регистра в нижний предел'''
        return v.lower() if isinstance(v, str) else v

    class ConfigDict:
        '''Класс настройки для схемы подразделений'''
        from_attributes = True

class SubdivisionAdd(BaseModel):
    '''Класс схемы подразделения для добавления'''
    id: int
    name: str
    leader_id: int | None = None

class SubdivisionLeaderUpdate(BaseModel):
    '''Класс схемы подразделения для добавления руководителя'''
    name : str
    leader_id: int | None = None

class SubdivisionEmployeeAdd(BaseModel):
    '''Класс схемы подразделения для добавления работника'''
    id: int
    name: str

class SubdivisionUpdate(BaseModel):
    '''Класс схемы подразделения для обновления'''
    id : int
    name: str

    @field_validator('name')
    def to_lower(cls, v):
        '''Функция для смены регистра в нижний предел'''
        return v.lower() if isinstance(v, str) else v

class SubdivisionDelete(BaseModel):
    '''Класс схемы подразделения для удаления'''
    id: int