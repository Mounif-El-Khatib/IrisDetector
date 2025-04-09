import sqlite3
import os
import datetime
from kivy.utils import platform


class DBManager:
    @staticmethod
    def _init_db(db_path):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                result TEXT,
                timestamp TEXT
                )
            """
            )
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(e)

    @staticmethod
    def insert_image(db_path: str, filename: str, result: str):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO images (filename, result, timestamp) VALUES (?, ?, ?)
            """,
                (str(filename), str(result), str(timestamp)),
            )
            conn.commit()
            conn.close()
            print(f"Saved {filename} with '{result}' at {timestamp}")
            return 0
        except Exception as e:
            print(e)
            return -1

    @staticmethod
    def get_saved_data(db_path: str):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM images;
            """
        )
        data = cursor.fetchall()
        return data

    @staticmethod
    def get_storage_path():
        if platform == "android":
            from android.storage import app_storage_path  # type: ignore
            from jnius import autoclass

            context = autoclass("org.kivy.android.PythonActivity").mActivity
            return app_storage_path()
        else:
            return os.getcwd()

    @staticmethod
    def get_db_path():
        storage_path = DBManager.get_storage_path()
        db_path = os.path.join(storage_path, "iris_detector.db")
        DBManager._init_db(db_path)
        return db_path

    @staticmethod
    def delete_item(db_path: str, item_path: str):
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""DELETE FROM images WHERE filename = ?""", str(item_path))
            return 0
        except Exception as e:
            print(e)
            return -1
