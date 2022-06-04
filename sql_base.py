import sqlite3
import pandas as pd


class MySql:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.bd_name = 'zakupki.db'

    def connect_to_bd(self):
        """
        Обработка подключения к базе данных
        :return:
        """
        self.conn = sqlite3.connect(self.bd_name)
        self.cursor = self.conn.cursor()
        # Таблица со всеми объявлениями
        # all_items - таблица с данными
        # id - уникальный номер контракта
        # status - последний статус контракта
        # name - описание сути контракта
        # price - стоимость контракта
        # placed - дата размещения объявления контракта
        # updated - дата обновления данных контракта
        # ending - дата окончания подачи заявок контракта
        # customer - заказчик работы
        # url - ссылка на страницу контракта
        # target - метка о соответствии контракта запросам (0 или 1)
        command = """CREATE TABLE if not exists all_items (id TEXT, status TEXT, name TEXT, price REAL, placed TEXT, 
                    updated TEXT, ending TEXT, customer TEXT, url TEXT, target INTEGER)"""
        self.cursor.execute(command)
        self.conn.commit()
        # Таблица с новыми объявлениями
        command = """create table if not exists new_items (id TEXT, status TEXT, name TEXT, price REAL, placed TEXT, 
                    updated TEXT, ending TEXT, customer TEXT, url TEXT, target INTEGER)"""
        self.cursor.execute(command)
        self.conn.commit()

    @staticmethod
    def get_tuple_from_keys(item: dict, keys: tuple) -> tuple:
        """
        Генерация кортежа по ключам
        :param item: словарь объявления
        :param keys: кортеж с ключями
        :return: кортеж
        """
        new = ()
        for key in keys:
            if key in item:
                new += (item[key],)
            else:
                new += (None,)
        return new

    def set_target(self, id_contract: str):
        """
        Изменение метки о соответствии контракта запросу
        :param id_contract: уникальный идентификатор контракта
        :return: None
        """
        sql_select_query = """select * from all_items where id = ?"""
        self.cursor.execute(sql_select_query, (id_contract,))
        records = self.cursor.fetchall()
        # в случае наличия записей в таблице
        if len(records):
            # получаем и инвертируем метку контракта
            id_target = records[0][9]
            id_target = 0 if id_target else 1
            command = """UPDATE all_items SET target = ? where id = ?"""
            self.cursor.execute(command, (id_target, id_contract))


    def add_to_table(self, item: dict):
        """
        Добавление элемента в базу данных
        :param item: словарь с записями
        :return: None
        """
        if self.cursor:
            keys = ('id', 'status', 'name', 'price', 'placed', 'updated', 'ending', 'customer', 'url', 'target')
            new = self.get_tuple_from_keys(item, keys)
            # проверка наличия существующего элемента в базе
            sql_select_query = """select * from all_items where id = ?"""
            self.cursor.execute(sql_select_query, (item['id'],))
            records = self.cursor.fetchall()
            if len(records) == 0:
                # при отсутствии элементов с таким номер добавляеться запись в основную таблицу
                command = """INSERT INTO all_items (id, status, name, price, placed, updated, ending, 
                             customer, url, target) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                self.cursor.execute(command, new)
                # Добавление в таблицу с новыми заявками
                command = """INSERT INTO new_items (id, status, name, price, placed, updated, ending, 
                             customer, url, target) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                self.cursor.execute(command, new)
            else:
                # обновление существующей записи
                keys = ('status', 'name', 'price', 'placed', 'updated', 'ending', 'customer', 'url', 'id')
                command = """UPDATE all_items SET status = ?, name = ?, price = ?, placed = ?, updated = ?, 
                            ending = ?, customer = ?, url = ? where id = ?"""
                self.cursor.execute(command, self.get_tuple_from_keys(item, keys))

    def add_items_to_table(self, items: list):
        """
        Добавление элементов в базу данных
        :param items: список словарей
        :return: None
        """
        self.connect_to_bd()
        try:
            # Очистка таблицы с новыми объявлениями
            try:
                sql_select_query = """DELETE FROM new_items"""
                self.cursor.execute(sql_select_query)
            finally:
                self.conn.commit()
            # Сохранение в базе данных
            for item in items:
                self.add_to_table(item)
        finally:
            self.conn.commit()
            self.conn.close()

    def get_items(self, table: str = "all_items", status: str = "") -> list:
        """
        Чтение данных с базы
        :param table: название таблицы, по умолчанию чтение всех записей
        :param status: название статуса записей
        :return: список кортежей
        """
        records = []
        self.connect_to_bd()
        try:
            if status == "":
                sql_select_query = f"SELECT * FROM {table}"
            else:
                sql_select_query = f'SELECT * FROM {table} WHERE status = "{status}"'
            self.cursor.execute(sql_select_query)
            records = self.cursor.fetchall()
        finally:
            self.conn.commit()
            self.conn.close()
        return records
