from datetime import datetime, date
from json import JSONDecodeError
from logging import getLogger, StreamHandler

import telebot
from telebot.types import Message
from envparse import Env

from client import TelegramClient
from database import User, SQLiteClient
from reminder import Reminder

logger = getLogger(__name__)
logger.addHandler(StreamHandler())
logger.setLevel("INFO")

env = Env()
TOKEN = env.str("TOKEN")
ADMIN_CHAT_ID = env.int("ADMIN_CHAT_ID")

class MyBot(telebot.TeleBot):
    def __init__(self,telegram_client: TelegramClient,
                 user_field:User,
                 reminder_client: Reminder, *args, **kwargs):
        super().__init__(*args,**kwargs)
        self.telegram_client = telegram_client
        self.user_field = user_field
        self.reminder_client = reminder_client

    def setup_resources(self):
        self.user_field.setup()

    def shutdown_resources(self):
        self.user_field.shutdown()

    def shutdown(self):
        self.shutdown_resources()



base_telegram_client = TelegramClient(token= TOKEN,
                                      base_url = 'https://api.telegram.org')
user = User(SQLiteClient('users.db'))
base_reminder_client = Reminder(telegram_client = base_telegram_client,
                                database_client = user)
bot = MyBot(token = TOKEN,
            telegram_client = base_telegram_client,
            user_field = user,
            reminder_client = base_reminder_client)



@bot.message_handler(commands = ['start'])
def start(message: Message):

    user_id = str(message.from_user.id)
    user_name = message.from_user.username
    chat_id = message.chat.id
    created = False

    new_user = bot.user_field.get_user(user_id)
    if not new_user:
        bot.user_field.create_user(user_id = user_id, user_name = user_name, chat_id = chat_id)
        created = True
    bot.reply_to(message=message,
                        text=f'Вы {'уже ' if not created else ''}зарегистрированы, {user_name}.')


def handle_speech(message: Message):
    bot.user_field.update_date(user_id = str(message.from_user.id), updated_date = date.today())
    bot.reply_to(message=message,
                        text='Доброго дня!')


@bot.message_handler(commands = ['say_smth'])
def say_smth(message: Message):
    bot.reply_to(message=message,
                        text='Урааааа')
    bot.register_next_step_handler(message, callback= handle_speech)

def set_notifications(message: Message):
    user_notification = message.text
    bot.user_field.set_notification(user_id = str(message.from_user.id), text = user_notification)
    bot.reply_to(message=message,text='Уведомление установлено.')

def set_time(message: Message):
    user_time = message.text
    try:
        user_date = datetime.strptime(user_time, '%d:%m:%Y %H:%M')
        bot.user_field.update_date(user_id = str(message.from_user.id), updated_date = user_date)
        bot.reply_to(message=message, text='Время установлено. Теперь сделайте название для него.')
        bot.register_next_step_handler(message = message, callback=set_notifications)
    except ValueError:
        bot.reply_to(message=message, text='Неверный формат даты. Пример: 25:12:2022 18:30')

@bot.message_handler(commands = ['set_reminder'])
def set_reminder(message: Message):
    bot.reply_to(message=message,text = 'Установите напоминание в формате %d:%m:%Y %H:%M')
    bot.register_next_step_handler(message = message, callback=set_time)
    bot.reminder_client(message.chat.id)

def create_err_message(error: Exception) -> str:
    return f'{datetime.now()}\n{error.__class__}:{error}'

while True:
    try:
        bot.setup_resources()
        bot.polling()
    except JSONDecodeError as err:
        ERROR_MESSAGE = create_err_message(err)
        bot.telegram_client.post(method = 'sendMessage', params = {"text": ERROR_MESSAGE,
                                                                   "chat_id": ADMIN_CHAT_ID})
        logger.error(f'Error during polling: {ERROR_MESSAGE}')
        bot.shutdown()
