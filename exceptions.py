import datetime


def input_date():
    while True:
        start_date = str(input('Введите начальную дату (в формате 01.01.0001): '))
        finish_date = str(input('Введите конечную дату (в формате 01.01.0001): '))
        try:
            s = datetime.datetime.strptime(start_date, '%d.%m.%Y').date()
            f = datetime.datetime.strptime(finish_date, '%d.%m.%Y').date()
            if f < s or datetime.date.today() < f:
                raise Exception
            break
        except ValueError:
            print('Неверно указан формат даты')
            continue
        except Exception:
            print('Неверно выбран временной период')
    return start_date, finish_date