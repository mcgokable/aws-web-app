from datetime import datetime
from typing import Any
import psycopg2
import os


def get_db_connection():
    try:
        connection = psycopg2.connect(
            user=os.getenv("username"),
            password=os.getenv("password"),
            database=os.getenv("db_name"),
            host=os.getenv("host"),
            port=os.getenv("port"),
        )
    except Exception as err:
        print("Error occured: ", err)
        raise
    print("Connected to db ....")
    return connection


def build_response(data: tuple[str, str, int, datetime]) -> dict[str, Any]:
    return {
        "name": data[0],
        "extension": data[1],
        "size": data[2],
        "date": data[3].strftime("%m/%d/%Y, %H:%M:%S"),
    }


def lambda_handler(event, context):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM metadata")
    res = [build_response(el) for el in cursor.fetchall()]

    print("All metadata: ", res)
    cursor.close()
    return res
