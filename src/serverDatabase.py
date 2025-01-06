import sqlite3
from sqlite3 import Error
# from pathlib import Path
from random import randint

"""
status:
req - requested
acc - accepted
blk - blocked
"""


class Database():
    def __init__(self, db_path: str, ) -> None:
        self.db_path = db_path
        self.conn = self.create_connection(db_path)

    def create_connection(self, db_file: str):
        """ create a database connection to a SQLite database """
        conn = None
        try:
            conn = sqlite3.connect(db_file, check_same_thread=False)
            print(
                f"\nConnected to Database\nSqlite3 Version: {sqlite3.version}\nDatabase path: {db_file}\n")
        except Error as e:
            print(e)

        return conn

    def create_table(self, sql_create_x_table):
        """Creates a table using value of sql_create_x_table as the sql code"""
        try:
            c = self.conn.cursor()
            c.execute(sql_create_x_table)
        except Error as e:
            print(e)

    def close_connection(self):
        self.conn.commit()
        self.conn.close()

    def execute_update(self, sql: str, values: tuple):
        c = self.conn.cursor()
        try:
            c.execute(sql, values)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"UPDATE SQL ERROR: {e}\nfor {sql = }\n{values = }")
            self.conn.rollback()
        finally:
            c.close()

    def execute_insert(self, sql: str, values: tuple):
        c = self.conn.cursor()
        try:
            c.execute(sql, values)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"INSERT SQL ERROR: {e}\nfor {sql = }\n{values = }")
            self.conn.rollback()
        finally:
            c.close()

    # ----------SERVER DATABASE FUNCTIONS----------

    def server_tables(self):
        sql_create_user_table = """
        CREATE TABLE IF NOT EXISTS users(
        user_id text NOT NULL PRIMARY KEY,
        screen_name text NOT NULL,
        hashed_password text NOT NULL,
        salt blob NOT NULL,
        public_key text NOT NULL,
        UNIQUE(user_id)
        );"""
        if self.conn is not None:
            self.create_table(sql_create_user_table)

    def add_user(self, user_id: str, screen_name: str, hashed_password: str, salt: bytes, public_key: str) -> bool:
        """Adds a new user to the database"""
        success = False
        values = (user_id, screen_name, hashed_password, salt, public_key)
        sql = """INSERT INTO users(user_id, screen_name, hashed_password, salt, public_key) VALUES(?,?,?,?,?)"""
        c = self.conn.cursor()
        try:
            c.execute(sql, values)
            self.conn.commit()
            print(f'\n[DB] New user {values} created\n')
            success = True
        except sqlite3.Error as e:
            print(e)
            self.conn.rollback()
        return success

    def get_user_details(self, user_id):
        """Gets user_id, screen_name and public_key"""
        c = self.conn.cursor()
        c.execute(
            "SELECT user_id, screen_name, public_key from users WHERE user_id=?", (user_id,))
        return c.fetchall()[0]

    def get_screen_name(self, user_id: str):
        """Gets the screen_name of the specified user_id"""
        c = self.conn.cursor()
        c.execute(
            "SELECT screen_name FROM users WHERE user_id=?", (user_id,))
        return c.fetchall()[0][0]

    def get_public_key(self, user_id: str):
        """Gets the public key of the specified user_id"""
        c = self.conn.cursor()
        c.execute("SELECT public_key from users WHERE user_id=?", (user_id, ))
        return c.fetchall()[0][0]

    def get_password(self, user_id: str):
        """Gets hashed password of the specified user_id"""
        c = self.conn.cursor()
        c.execute(
            "SELECT hashed_password, salt FROM users WHERE user_id=?", (user_id,))
        return c.fetchall()

    def check_user_id_exists(self, user_id: str) -> bool:
        """Returns True if user exists. False if they do not"""
        c = self.conn.cursor()
        c.execute("""SELECT COUNT(*) FROM users WHERE user_id = ? ;""", (user_id,))
        return c.fetchall()[0][0] != 0

    def update_screen_name_server(self, user_id: str, new_screen_name: str):
        values = (new_screen_name, user_id)
        sql = """
        UPDATE users
        SET screen_name = ? 
        WHERE user_id = ?;
        """
        self.execute_update(sql, values)

    def delete_account_server(self, user_id: str):
        success = False
        posfix = randint(10000000, 99999999)
        new_user_id = f"deleted account({posfix})"
        values = (new_user_id, new_user_id, user_id)
        sql = """
        UPDATE users
        SET user_id = ?, screen_name = ?
        WHERE user_id = ?;
        """
        c = self.conn.cursor()
        try:
            c.execute(sql, values)
            self.conn.commit()
            success = True
        except sqlite3.Error as e:
            print(e)
            self.conn.rollback()
            success = False
        finally:
            c.close()
            return success, new_user_id

    # ----------CLIENT DATABASE FUNCTIONS----------

    def client_tables(self):
        sql_create_messages_table = """
        CREATE TABLE IF NOT EXISTS messages (
        message_id INTEGER PRIMARY KEY,
        friend_id text NOT NULL,
        encrypted_Epk blob NOT NULL,
        message_text blob NOT NULL,
        date text NOT NULL,
        time text NOT NULL,
        from_me integer NOT NULL,
        is_image integer NOT NULL,
        FOREIGN KEY (friend_id) REFERENCES friendships(friend_id)
        );"""

        sql_create_friendships_table = """
        CREATE TABLE IF NOT EXISTS friendships (
        friend_id text NOT NULL UNIQUE,
        friend_screen_name text NOT NULL,
        public_key text NOT NULL,
        status text NOT NULL,
        specifier_id text NOT NULL,
        PRIMARY KEY (friend_id)
        );"""

        if self.conn is not None:
            self.create_table(sql_create_messages_table)
            self.create_table(sql_create_friendships_table)

    def new_blocked_friend(self, user_id: str, friend_user_id: str):
        """Sets status to blk where user_id has blocked friend_user_id"""
        values = (user_id, friend_user_id)
        sql = """
        UPDATE friendships
        SET status = 'blk', specifier_id = ?
        WHERE friend_id = ?
        """
        self.execute_update(sql, values)

    def unblocked_friend(self, user_id: str, friend_user_id: str):
        """Sets status to acc where user_id has unblocked friend_user_id"""
        values = (user_id, friend_user_id)
        sql = """
        UPDATE friendships
        SET status = 'acc', specifier_id = ?
        WHERE friend_id = ?
        """
        self.execute_update(sql, values)

    def get_friend_list(self):
        c = self.conn.cursor()
        c.execute("""
            SELECT friend_id, public_key, friend_screen_name, status, specifier_id
            FROM friendships
            WHERE status = 'acc' or status = 'blk';
            """)
        return c.fetchall()

    def get_all_acc_friends_user_ids(self):
        c = self.conn.cursor()
        c.execute("""
            SELECT friend_id
            FROM friendships
            WHERE status = 'acc';
            """)
        return c.fetchall()

    def get_friend_request_list(self, user_id: str):
        c = self.conn.cursor()
        c.execute("""
            SELECT friend_id, public_key
            FROM friendships
            WHERE status = 'req' and specifier_id != ?;
            """, (user_id,))
        return c.fetchall()

    def get_pending_friends_list(self, user_id: str):
        print(f"GETTING PENDING FRIEND LIST")
        c = self.conn.cursor()
        c.execute("""
            SELECT friend_id
            FROM friendships
            WHERE status = 'req' and specifier_id = ?;
            """, (user_id,))
        return c.fetchall()

    def add_new_friend_request(self, friend_id: str, friend_screen_name: str, public_key: str, specifier_id: str):
        print(f"Adding new friend {friend_id = }")
        data = (friend_id, friend_screen_name, public_key, 'req', specifier_id)
        sql = """INSERT INTO friendships (friend_id, friend_screen_name, public_key, status, specifier_id) VALUES (?, ?, ?, ?, ?)"""
        self.execute_insert(sql, data)

    def check_if_user_is_already_friends(self, friend_user_id: str):
        c = self.conn.cursor()
        c.execute(
            "SELECT COUNT(*) FROM friendships WHERE friend_id = ?", (friend_user_id,))
        return c.fetchall()[0][0]

    def accept_friend_request(self, friend_id: str, specifier_id: str):
        values = (specifier_id, friend_id)
        sql = """
        UPDATE friendships
        SET status = 'acc', specifier_id = ?
        WHERE friend_id = ?
        """
        self.execute_update(sql, values)

    def reject_friend_request(self, friend_id):
        c = self.conn.cursor()
        try:
            c.execute("DELETE FROM friendships WHERE friend_id = ?", (friend_id,))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"DELETION SQL ERROR: {e}")
        finally:
            c.close()

    def get_message_list(self, friend_id: str):
        c = self.conn.cursor()
        c.execute("""
        SELECT encrypted_Epk, message_text, date, time, from_me, is_image
        FROM messages
        WHERE friend_id = ?
        ORDER BY message_id ASC;
        """, (friend_id, ))
        return c.fetchall()

    def store_message(self, friend_id: str, encrypted_Epk: bytes, encrypted_message: bytes, date: str, time: str, from_me: int, is_image: int):
        values = (friend_id, encrypted_Epk,
                  encrypted_message, date, time, from_me, is_image)
        sql = """INSERT INTO messages(friend_id, encrypted_Epk, message_text, date, time, from_me, is_image) VALUES(?,?,?,?,?,?,?)"""
        self.execute_insert(sql, values)

    def update_friend_screen_name(self, friend_id: str, friend_screen_name: str):
        values = (friend_screen_name, friend_id)
        sql = """
        UPDATE friendships
        SET friend_screen_name = ?
        WHERE friend_id = ?;
        """
        self.execute_update(sql, values)

    def friend_deleted_account(self, friend_id: str, account_deletion_name: str):
        values = (account_deletion_name, account_deletion_name, friend_id)
        sql = """
        UPDATE friendships
        SET friend_screen_name = ?, friend_id = ?
        WHERE friend_id = ?;
        """
        self.execute_update(sql, values)
