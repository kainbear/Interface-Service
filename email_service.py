'''email_service.py'''

from datetime import datetime, timedelta
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import httpx
from email_config import email_settings

conf = ConnectionConfig(
    MAIL_USERNAME=email_settings.MAIL_USERNAME,
    MAIL_PASSWORD=email_settings.MAIL_PASSWORD,
    MAIL_PORT=email_settings.MAIL_PORT,
    MAIL_SERVER=email_settings.MAIL_SERVER,
    MAIL_FROM=email_settings.MAIL_FROM,
    MAIL_STARTTLS=email_settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=email_settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=email_settings.VALIDATE_CERTS
)

USER_SERVICE_URL = "http://45.92.176.81:44444"
TASK_SERVICE_URL = "http://45.92.176.81:44445"

async def send_email(subject: str, recipients: list, body: str):
    '''Функция отправки уведомления'''
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=body,
        subtype="html"
    )
    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

async def get_upcoming_tasks():
    '''Функция получения задач с близким сроком выполнения из task-сервиса'''
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{TASK_SERVICE_URL}/task/read_all?due_date_lte={tomorrow.isoformat()}")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Ошибка проверки задач: {response.status_code} {response.text}")
            return []

async def check_due_tasks(*args, **kwargs):
    '''Функция проверки задач на уведомление'''
    upcoming_tasks = await get_upcoming_tasks()
    for task in upcoming_tasks:
        user_id = task.get('user_id')
        if user_id:
            email = await get_user_email(user_id)
            if email:
                success = await send_due_date_notification(email, task)
                if success:
                    print(f"Reminder sent to {email} for task {task['title']}")
                else:
                    print(f"Failed to send reminder to {email} for task {task['title']}")


async def get_user_email(user_id: int) -> str:
    '''Функция получения email пользователя по user_id из внешнего сервиса'''
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{USER_SERVICE_URL}/employee/{user_id}")
        print("Response:", response)
        if response.status_code == 200:
            user_data = response.json()
            return user_data.get('email')
        else:
            print(f"Ошибка получения email по ID: {response.status_code} {response.text}")
            return ""

async def send_due_date_notification(email: str, task):
    '''Функция для отправки уведомления'''
    message = MessageSchema(
        subject="Task Due Date Reminder",
        recipients=[email],
        body=f"Dear user,\n\nThis is a reminder that the task '{task['title']}' is due soon.\n\nRegards,\nYour Team",
        subtype="plain"
    )

    return await send_email(subject=message.subject,
                            recipients=message.recipients, body=message.body)

# Шедулер это задачник бэкграунд который и добавляет задачу при запуске сервиса
trigger = CronTrigger(hour=9, minute=0, timezone="Europe/Moscow")
scheduler = BackgroundScheduler()

def schedule_tasks():
    '''Функция действия отправки'''
    scheduler.add_job(check_due_tasks, trigger)
    scheduler.start()

schedule_tasks()
