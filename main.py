import get_data
import datetime
import re
import xlsxwriter
import time


def get_period():
    check_date = False
    print("Нужно указать период. Даты вводить в формате ГГГГ-ММ-ДД. Выбирать можно не более месяца")
    while check_date == False:
        date_from = input("Введите дату начала периода:")

        date_to = input("Введите дату окончания периода:")
        if date_from == '':
            print('Укажите дату начала периода')
            continue
        if date_to == '':
            print('Укажите дату окончания периода')
            continue
        tpl = r'\d\d\d\d\-\d\d\-\d\d'
        if re.match(tpl, date_from) is None:
            print('Неверный формат даты начала периода')
            continue
        if re.match(tpl, date_to) is None:
            print('Неверный формат даты окончания периода')
            continue
        try:
            date_from_dt = datetime.datetime.strptime(date_from, '%Y-%m-%d').date()
            date_to_dt = datetime.datetime.strptime(date_to, '%Y-%m-%d').date()
            timedelta = (date_to_dt - date_from_dt).days
        except:
            print('Неверно указан период')
            continue
        if timedelta < 0 :
            print('Дата начала периода должна бать меньше или равна дате окончания периода ')
            continue
        if timedelta> 31:
            print('Выбран период больше месяца')
            continue
        check_date = True
    return {'date_from': date_from, 'date_to': date_to}

def write_to_excel(period):
    metka = int( time.time())
    filename = f"report_{period['date_from']}_{period['date_to']}_{metka}.xlsx"
    header = ["ИНН","Аптека","рег№ ККТ","ФН","Дата время чека","Адрес аптеки","Товар","Цена","Колво","Сумма","ФД","ФПД","Доп свойство","Рассчетное кол-во"]
    wb = xlsxwriter.Workbook(filename)
    sheet = wb.add_worksheet()
    sheet.write_row(0, 0, header)
    num_row = 1
    with open('tmp','r') as file:
        for row in file:
            colls = row.split('|')
            sheet.write_row(num_row, 0, colls)
            num_row += 1
    wb.close()
    print(f'Файл {filename} сохранен')

with open("tmp", "w") as file:
        file.write("");
period = get_period()
accounts = get_data.get_sid()
if accounts!= False:
    for account in accounts:
        keys = get_data.get_keys(account)
        if len(keys) == 0:
            print(f"По логину {account['login']} ключи не найдены")
            continue
        for key in keys:
            get_data.get_receipts(key,account['sid'], period)
    write_to_excel(period)
input('Программа завершила работу. Нажмите любую клавишу')



