from Service.Logger import error_log
import psycopg2
import os


def db_connect():
    try:
        con = psycopg2.connect(
            host=os.environ.get('host'),
            database=os.environ.get('database'),
            user=os.environ.get('user'),
            port=os.environ.get('port'),
            password=os.environ.get('password'))
        cur = con.cursor()
        return con, cur
    except Exception as e:
        error_log(e)
        return None
