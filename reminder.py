from datetime import datetime
import time

from envparse import Env
from client import TelegramClient
from database import User
from logging import getLogger, StreamHandler


logger = getLogger(__name__)
logger.addHandler(StreamHandler())
logger.setLevel("INFO")

env = Env()
TOKEN = env.str("TOKEN")


class Reminder:

    GET_TASKS = """
        SELECT chat_id FROM users WHERE last_updated_date IS NULL OR last_updated_date < date ('now');
    """



    def __init__(self, telegram_client: TelegramClient, database_client: User):
        self.telegram_client = telegram_client
        self.database_client = database_client


    def notify(self, chat_id: str):
        user_id = chat_id[0]
        user_date, notification = self.database_client.get_notification(user_id)
        while datetime.now() < datetime.strptime(user_date,'%Y-%m-%d %H:%M:%S'):
            logger.info(f'Waiting until {user_date} for chat_id {chat_id}')
            time.sleep(60)
        res = self.telegram_client.post(method = 'sendMessage', params = {'chat_id': user_id,
                                                                          'text': f'{notification}'})
        self.database_client.update_notification(user_id)
        logger.info(res)
    def execute(self,user_id: str):
        chat_id = self.database_client.get_user(user_id)
        if chat_id:
            self.notify(chat_id)

    def __call__(self,user_id, *args, **kwargs):
        self.execute(user_id)
