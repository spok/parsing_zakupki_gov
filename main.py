import os
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot
from gui import MainWindow
from parser_site import ParserSite
from sql_base import *


import requests
from bs4 import BeautifulSoup
import pandas as pd
import openpyxl
from openpyxl.styles import Alignment
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

import datetime
import sqlite3



headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
      }



def parse_zakupki(total):
    key_str = []
    page = 1
    pages = 2
    find_pages = False
    #подключение к базе данных с закупками
    conn = sqlite3.connect("zakupki.db")
    cursor = conn.cursor()
    cursor.execute(
        'create table if not exists zakupki (Number text, Status text, Name text, Price text, Razmescheno text, Obnovleno text, Konec_zayavok text, Zakazchik text)')
    conn.commit()
    # чтение ключевых слов
    with open('key.txt') as file_object:
        for line in file_object:
            buf = line.rstrip()
            if len(buf) > 0:
                key_str.append(buf)

    while page < pages:
        url = 'https://zakupki.gov.ru/epz/order/extendedsearch/results.html?morphology=on&search-filter='
        url += '%D0%94%D0%B0%D1%82%D0%B5+%D1%80%D0%B0%D0%B7%D0%BC%D0%B5%D1%89%D0%B5%D0%BD%D0%B8%D1%8F&pageNumber='
        url += str(page)
        url += "&sortDirection=false&recordsPerPage=_50&showLotsInfoHidden=false&sortBy=UPDATE_DATE&fz44=on&fz223=on'" \
               "&af=on&ca=on&pc=on&pa=on&currencyIdGeneral=-1"

        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        quotes = soup.find_all('div', class_='row no-gutters registry-entry__form mr-0')

        for quote in quotes:
            try:
                id_text = quote.find('div', class_='registry-entry__header-mid__number').get_text(strip=True)
                id_text = id_text[1:]
                id_text = id_text.lstrip()
            except Exception:
                id_text = ""
            try:
                status_text = quote.find('div', class_='registry-entry__header-mid__title text-normal').get_text(strip=True)
            except Exception:
                status_text = ""
            try:
                job_text = quote.find('div', class_='registry-entry__body-value').get_text(strip=True)
            except Exception:
                job_text = ""
            job = job_text.lower()
            # проверка на совпадение с ключевыми словами
            index = 0
            for key in key_str:
                if job.find(key) > -1:
                    index += 1
            # использовать только акутальные закупки
            if status_text != 'Подача заявок':
                index = 0
            try:
                zakaz_text = quote.find('div', class_='registry-entry__body-href').get_text(strip=True)
            except Exception:
                zakaz_text = ""
            try:
                price_text = quote.find('div', class_='price-block__value').get_text(strip=True)
                price_text = price_text[:-2]
            except Exception:
                price_text = ""
            try:
                data_text = ""
                data2_text = ""
                data3_text = ""
                data_typ = quote.find_all('div', class_='data-block__title')
                data = quote.find_all('div', class_='data-block__value')
                i = 0
                for d_typ in data_typ:
                    if d_typ.get_text() == 'Размещено':
                        data_text = data[i].get_text()
                    if d_typ.get_text() == 'Обновлено':
                        data2_text = data[i].get_text()
                    if d_typ.get_text() == 'Окончание подачи заявок':
                        data3_text = data[i].get_text()
                    i += 1
            except Exception:
                data_text = ""
                data2_text = ""
                data3_text = ""

            #сохранение записей в базе данных
            new = ((id_text, status_text, job_text, price_text, data_text, data2_text, data3_text, zakaz_text))

            # проверка наличия существующего элемента в базе
            sql_select_query = """select * from zakupki where Number = ?"""
            cursor.execute(sql_select_query, (id_text,))
            records = cursor.fetchall()
            # при отсутствии элементов с таким номер добавляеться строка в базу
            if len(records) == 0:
                cursor.execute(
                    '''INSERT INTO zakupki(Number, Status, Name, Price, Razmescheno, Obnovleno, Konec_zayavok, Zakazchik) VALUES(?, ?, ?, ?, ?, ?, ?, ?)''',
                    new)
                if index > 0:
                    total.append(new)
            else:
                for row in records:
                    # В случае если название отсутствует в базе
                    if row[2] != job_text:
                        # добавляется новая запись в базу
                        cursor.execute(
                            '''INSERT INTO zakupki(Number, Status, Name, Price, Razmescheno, Obnovleno, Konec_zayavok, Zakazchik) VALUES(?, ?, ?, ?, ?, ?, ?, ?)''',
                            new)
                        if index > 0:
                            total.append(new)
                    # если запись существует то обновляються другие поля
                    else:
                        cursor.execute('UPDATE zakupki SET Status = ? where Number = ?', (status_text, id_text,))
                        cursor.execute('UPDATE zakupki SET Price = ? where Number = ?', (price_text, id_text,))
                        cursor.execute('UPDATE zakupki SET Razmescheno = ? where Number = ?', (data_text, id_text,))
                        cursor.execute('UPDATE zakupki SET Obnovleno = ? where Number = ?', (data2_text, id_text,))
                        cursor.execute('UPDATE zakupki SET Konec_zayavok = ? where Number = ?', (data3_text, id_text,))

            #Определение количества страниц
            if find_pages == False:
                class_pages = soup.find('div', class_='paginator align-self-center m-0')
                li_pages = class_pages.find_all('span', class_='link-text')
                pages = int(li_pages[len(li_pages)-1].get_text())
                pages += 1
                find_pages = True
        print('Обработана страница: ' + str(page))
        page += 1
        time.sleep(1)

    conn.commit()
    conn.close()
    return total

def format_table(file_table):
    wb = openpyxl.load_workbook(file_table)
    sheet = wb.active
    sheet.column_dimensions['A'].width = 5
    sheet.column_dimensions['B'].width = 22
    sheet.column_dimensions['C'].width = 22
    sheet.column_dimensions['D'].width = 74
    sheet.column_dimensions['E'].width = 14
    sheet.column_dimensions['F'].width = 12
    sheet.column_dimensions['G'].width = 12
    sheet.column_dimensions['H'].width = 12
    sheet.column_dimensions['I'].width = 70
    max_row = sheet.max_row
    for i in range(2, max_row + 1):
        sheet['D' + str(i)].alignment = Alignment(wrap_text=True)
    wb.save(file_table)

def send_mail(send_file):
    email = 'vyacheslaw.vlasow@yandex.ru'
    password = 'krevedko78'
    address = "spok78@gmail.com"

    part = MIMEBase('application', "octet-stream")
    part.set_payload(open(send_file, "rb").read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % os.path.basename(send_file))

    msg = MIMEMultipart()
    msg['From'] = email
    msg['To'] = address
    msg.attach(part)

    server = smtplib.SMTP('smtp.yandex.ru', 587)
    server.ehlo()
    server.starttls()
    server.login(email, password)

    server.set_debuglevel(1)  # Необязательно; так будут отображаться данные с сервера в консоли
    server.sendmail(email, address, msg.as_string())
    server.quit()

def save_new_table(total):
    if len(total) > 0:
        name_table = 'zakupki'
        name_table += datetime.datetime.today().strftime("%Y_%m_%d_%H_%M")
        name_table += '.xlsx'

        # создание таблицы с новыми записями
        df = pd.DataFrame(total, columns=['Number', 'Status', 'Name', 'Price', 'Razmescheno', 'Obnovleno', 'Konec zajavok',
                                          'Zakazchik'])
    
        # сохранение выборки
        df = df.drop_duplicates(subset=['Number', 'Name'], keep='first')
        df.to_excel(name_table)

        # форматирование таблицы после сохранения
        format_table(name_table)

        #отправка файла почтой
        send_mail(name_table)

def save_base_in_table():
    name_table = 'zakupki_baza_full_'
    name_table += datetime.datetime.today().strftime("%Y_%m_%d_%H_%M")
    name_table += '.xlsx'

    #подключение к базе данных с закупками
    conn = sqlite3.connect("zakupki.db")
    cursor = conn.cursor()
    cursor.execute(
        'create table if not exists zakupki (Number text, Status text, Name text, Price text, Razmescheno text, Obnovleno text, Konec_zayavok text, Zakazchik text)')
    conn.commit()

    # получение всех записей в базе
    cursor.execute("""select * from zakupki""")
    records = cursor.fetchall()

    # создание таблицы с новыми записями
    df = pd.DataFrame(records,
                      columns=['Number', 'Status', 'Name', 'Price', 'Razmescheno', 'Obnovleno', 'Konec zajavok',
                               'Zakazchik'])

    # сохранение выборки
    df.to_excel(name_table)

    # форматирование таблицы после сохранения
    format_table(name_table)

    conn.close()

def save_key_in_table():
    key_str = []
    # чтение ключевых слов
    with open('key.txt') as file_object:
        for line in file_object:
            buf = line.rstrip()
            if len(buf) > 0:
                key_str.append(buf)
    # генерация имени таблицы
    name_table = 'zakupki_key_full_'
    name_table += datetime.datetime.today().strftime("%Y_%m_%d_%H_%M")
    name_table += '.xlsx'

    #подключение к базе данных с закупками
    conn = sqlite3.connect("zakupki.db")
    cursor = conn.cursor()
    cursor.execute(
        'create table if not exists zakupki (Number text, Status text, Name text, Price text, Razmescheno text, Obnovleno text, Konec_zayavok text, Zakazchik text)')
    conn.commit()

    # получение всех записей в базе
    sql_select_query = """select * from zakupki where Status = ?"""
    sql_status = 'Подача заявок'
    cursor.execute(sql_select_query, (sql_status,))
    records = cursor.fetchall()

    table = []
    for rec in records:
        for key in key_str:
            if rec[2].find(key) > -1:
                table.append(rec)

    # создание таблицы с новыми записями
    df = pd.DataFrame(table,
                      columns=['Number', 'Status', 'Name', 'Price', 'Razmescheno', 'Obnovleno', 'Konec zajavok',
                               'Zakazchik'])

    # сохранение выборки
    df.to_excel(name_table)

    # форматирование таблицы после сохранения
    format_table(name_table)

    conn.close()

# # получаем аргументы при запуске
# script, first = argv
# total = []
#
# if first == 'p':
#     #парсинг сайта
#     total = parse_zakupki(total)
#     # сохранение результата
#     save_new_table(total)
#
# elif first == 's':
#     # сохранение всей базы в экселе
#     save_base_in_table()
#
# elif first == 'r':
#     # сохранение всех записей с совпадение в экселе
#     save_key_in_table()



class ParseThread(QThread):
    def __init__(self, parent=None):
        super().__init__()
        self.main = parent

    def run(self):
        self.main.pr.parsing()


class Main(MainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parse_thread = ParseThread(self)
        self.pr = ParserSite(self)
        self.sql = MySql()
        self.button2.clicked.connect(self.start_parsing)
        self.parse_thread.finished.connect(self.show_all_items)
        self.items = []
        self.__pages = 0

    @property
    def completed_pages(self):
        return self.__pages

    @completed_pages.setter
    def completed_pages(self, count):
        self.__pages += count
        self.status_label.setText(f'Количество обработанных страниц: {self.__pages} из {self.pr.count_pages}')

    def start_parsing(self):
        """
        Запуск парсинга сайта
        :return:
        """
        self.__pages = 0
        self.items = []
        self.parse_thread.start()

    def show_all_items(self):
        """
        Отображение в таблице всех записей базы данных
        :return:
        """
        self.show_table(self.pr.items)

    def closeEvent(self, a0) -> None:
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainwindow = Main()
    mainwindow.show()
    sys.exit(app.exec_())
