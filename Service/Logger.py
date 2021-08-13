import linecache
from sys import exc_info

def error_log(error):
    try:
        exc_type, exc_obj, tb = exc_info()
        _frame = tb.tb_frame
        linenos = tb.tb_lineno
        filename = _frame.f_code.co_filename
        linecache.checkcache(filename)
        line = linecache.getline(filename, linenos, _frame.f_globals)
        reason = f"EXCEPTION IN ({filename}, LINE {linenos} '{line.strip()}'): {exc_obj}"
        print(f"{reason}\n")
    except Exception as e:
        print(e)
        print("Возникла ошибка при обработке errorLog (Это вообще как?)")
