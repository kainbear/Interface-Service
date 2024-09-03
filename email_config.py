'''email_config.py'''

from pydantic_settings import BaseSettings

class EmailSettings(BaseSettings):
    '''Класс модели настроек имейла'''
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    VALIDATE_CERTS: bool
    TIMEZONE: str

    class Config:
        '''Класс конфига данных имейла'''
        env_file = ".env"

email_settings = EmailSettings()
