from Service.Logger import error_log
import psycopg2
import Service.Variables as Var


def db_connect():
    try:
        con = psycopg2.connect(host=Var.host,
                               database=Var.database,
                               user=Var.user,
                               port=Var.port,
                               password=Var.password)
        cur = con.cursor()
        return con, cur
    except Exception as e:
        error_log(e)
        return None
