import requests
import time
import sqlite3


def get_sid():
    connection = sqlite3.connect("db.db")
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM connection')
    rows = cursor.fetchall()
    accounts = []
    for row in rows:
        accounts.append({'login': row[0], 'password': row[1]})
    cursor.close()
    connection.close()
    if len(accounts) == 0:
        print('Не найдено ни одного аккаунта в настройках!')
        return False
    for account in accounts:
        url = f"https://api.kontur.ru/auth/authenticate-by-pass?login={account['login']}"
        res = requests.post(url, data=account['password'])
        json = res.json()
        if res.status_code != 200 or json.get('ErrorMessage', False):
            print(f"Ошибка получения доступа для аккаунта {account['login']}  - код ответа сервера {res.status_code}")
            print(json['ErrorMessage'])
            return False
        else:
            account['sid'] = f"auth.sid {json['Sid']}"
    return accounts


def get_keys(account):
    connection = sqlite3.connect("db.db")
    cursor = connection.cursor()
    cursor.execute(f"SELECT `key_val` from `keys` where `login`='{account['login']}'")
    rows = cursor.fetchall()
    keys = []
    for row in rows:
        keys.append(row[0])
    cursor.close()
    connection.close()
    return keys


def get_organization(p_key_, p_sid):
    url = "https://ofd-api.kontur.ru/v2/organizations"
    header_ = {"X-Kontur-Ofd-ApiKey": p_key_, 'Authorization': p_sid}
    response = requests.get(url, headers=header_)
    if response:
        orgs = response.json()
    else:
        orgs = None
    return orgs


def get_cashboxes(p_key_, p_sid, org):
    url = f"https://ofd-api.kontur.ru/v2/organizations/{org['id']}/cashboxes"
    header_ = {"X-Kontur-Ofd-ApiKey": p_key_, 'Authorization': p_sid}
    response = requests.get(url, headers=header_)
    if response:
        cashboxes = response.json()
    else:
        cashboxes = None
    return cashboxes


def get_docs(p_key_, p_sid, org, cashbox, period):
    date_from = period['date_from']+"T00:00:00"
    date_to = period['date_to']+"T23:59:59"
    current_offset = ''
    fl_exit = False
    limit = 1000
    while fl_exit is False:
        url = f"https://ofd-api.kontur.ru/v2/organizations/{org['id']}/cashboxes/{cashbox['regNumber']}/documents/by-period?dateFrom={date_from}&dateTo={date_to}&types=receipt&offset={current_offset}&limit={limit}"
        header_ = {"X-Kontur-Ofd-ApiKey": p_key_, 'Authorization': p_sid}
        response = requests.get(url, headers=header_)
        if response:
            res_js = response.json()
            if len(res_js['documents']) > 0:
                current_offset = res_js['paging']['nextOffset']
                time.sleep(1)
                write_docs(org, cashbox, res_js['documents'])
            else:
                fl_exit = True
                current_offset = ''
        else:
            print(f"error {response.status_code} get {url} ")


def write_docs(org, cashbox, docs):
    """ИНН|Аптека|рег№ ККТ|ФН|Дата время чека|Адрес аптеки|Товар|Цена|Колво|Сумма|ФД|ФПД|Доп свойство|Рассчетное кол-во"""
    for doc in docs:
        for good in doc['receipt']['items']:
            try:
                prop = good['additionalProperty']
                prop_ = good['additionalProperty']
                prop = prop.replace('mdlp', '').replace('&', '').strip()
            except:
                prop = ''
                prop_ = ''
            if prop == '' or prop.find("/") == -1:
                calc_q = good['quantity']
            else:
                prop = prop.split("/")
                p1 = int(prop[0])
                p2 = int(prop[1])
                if p1 == p2:
                    calc_q = int(good['quantity'])*p1
                else:
                    calc_q = good['quantity']
            with open("tmp", "a") as file:
                line = [
                       org['inn'],
                       org['shortName'].replace("|", ""),
                       doc['receipt']['kktRegId'],
                       doc['receipt']['fiscalDriveNumber'],
                       doc['receipt']['dateTime'],
                       doc['receipt']['retailPlaceAddress'].replace("|", ""),
                       good['name'].replace("|", ""),
                       good['price']/100.0,
                       good['quantity'],
                       doc['receipt']['totalSum']/100.0,
                       doc['receipt']['fiscalDocumentNumber'],
                       doc['receipt']['fiscalSign'],
                       prop_,
                       calc_q

                ]
                file.write("|".join(map(str, line)))
                file.write("\n")


def get_receipts(p_key, p_sid, period):
    orgs = get_organization(p_key, p_sid)
    if orgs is None:
        print(f"Нет организаций по ключу {p_key}")
        return False
    for org in orgs:
        cashboxes = get_cashboxes(p_key, p_sid, org)
        if cashboxes is None:
            print(f"Нет касс по организации {org}")
            continue
        for cashbox in cashboxes:
            get_docs(p_key, p_sid, org, cashbox, period)
