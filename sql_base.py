import sqlite3


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
        command = """CREATE TABLE if not exists all_items (id TEXT, status TEXT, name TEXT, price REAL, placed TEXT, 
                    updated TEXT, ending TEXT, customer TEXT, url TEXT)"""
        self.cursor.execute(command)
        self.conn.commit()
        # Таблица с новыми объявлениями
        command = """create table if not exists new_items (id TEXT, status TEXT, name TEXT, price REAL, placed TEXT, 
                    updated TEXT, ending TEXT, customer TEXT, url TEXT)"""
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

    def add_to_table(self, item: dict):
        """
        Добавление элемента в базу данных
        :param item: словарь с записями
        :return: None
        """
        # проверка наличия существующего элемента в базе
        if self.cursor:
            keys = ('id', 'status', 'name', 'price', 'placed', 'updated', 'ending', 'customer', 'url')
            new = self.get_tuple_from_keys(item, keys)
            sql_select_query = """select * from all_items where id = ?"""
            self.cursor.execute(sql_select_query, (item['id'],))
            records = self.cursor.fetchall()
            if len(records) == 0:
                # при отсутствии элементов с таким номер добавляеться запись в основную таблицу
                command = """INSERT INTO all_items (id, status, name, price, placed, updated, ending, customer, url) 
                            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                self.cursor.execute(command, new)
                # Добавление в таблицу новых заявок только в статусе подачи
                if item['status'] == 'Подача заявок':
                    command = """INSERT INTO new_items (id, status, name, price, placed, updated, ending, customer, url) 
                                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)"""
                    self.cursor.execute(command, new)
            else:
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

