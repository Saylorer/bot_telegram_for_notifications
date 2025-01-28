import sqlite3
from datetime import date

class SQLiteClient:

    CREATE_QUERY = """
        CREATE TABLE IF NOT EXISTS users (
            user_id INT PRIMARY KEY,
            user_name TEXT,
            chat_id INT
            );
    """

    INSERTION = """
        INSERT INTO users
        VALUES(1,'saylorer',123);
    """

    def __init__(self, path: str):
        self.path = path
        self.conn = None

    def create_conn(self):
        self.conn = sqlite3.connect(self.path, check_same_thread = False)

    def close_conn(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def execute_command(self, command: str, params: tuple):
        if self.conn:
            self.conn.execute(command, params)
            self.conn.commit()
        else:
            raise ConnectionError('Needs a creation of connection')

    def execute_select(self, command: str):
        if self.conn:
            cur = self.conn.cursor()
            cur.execute(command)
            return cur.fetchall()
        raise ConnectionError('Needs a creation of connection')


class User:
    GET = """
        SELECT * FROM users WHERE user_id = %s;
    """

    CREATE_USER = """
    INSERT INTO users VALUES(?, ?, ?);
    """

    UPDATE_LAST_DATE = """
        UPDATE users
        SET last_updated_date = ?
        WHERE user_id =?;
    """

    UPDATE_NOTIFICATION = """
        UPDATE users
        SET notification =?
        WHERE user_id =?;
    """""

    GET_REMINDERS = """
            SELECT last_updated_date, notification
            FROM users
            WHERE last_updated_date IS NOT NULL AND user_id = %s;
        """

    UPDATE_REMINDER = """
            UPDATE users SET last_updated_date = NULL, notification = NULL WHERE user_id =?;
        """

    def __init__(self, database_client: SQLiteClient):
        self.database_client = database_client

    def setup(self):
        self.database_client.create_conn()

    def shutdown(self):
        self.database_client.close_conn()

    def get_user(self, user_id: str):
        user = self.database_client.execute_select(self.GET % user_id)
        return user[0] if user else user

    def create_user(self, user_id: str, user_name: str, chat_id: int):
        self.database_client.execute_command(self.CREATE_USER, (user_id,user_name, chat_id))

    def update_date(self, user_id: str, updated_date: date):
        self.database_client.execute_command(self.UPDATE_LAST_DATE, (updated_date, user_id))

    def set_notification(self, user_id: str, text: str):
        self.database_client.execute_command(self.UPDATE_NOTIFICATION, (text, user_id))

    def get_notification(self, user_id: str):
        user_date, notification = self.database_client.execute_select(self.GET_REMINDERS % user_id)[0]
        return user_date, notification

    def update_notification(self, user_id: str):
        self.database_client.execute_command(self.UPDATE_REMINDER, (user_id,))
