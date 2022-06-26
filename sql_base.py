import sqlite3
import re


class MySql:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.bd_name = 'zakupki.db'
        self.connect_to_bd()

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
        command = """CREATE TABLE if not exists all_items (id TEXT NOT NULL, status TEXT, name TEXT, 
                     price REAL, placed TEXT, updated TEXT, ending TEXT, customer TEXT, url TEXT, target INTEGER, 
                     PRIMARY KEY ( id ) );"""
        self.cursor.execute(command)
        self.conn.commit()
        # Таблица с новыми объявлениями
        command = """CREATE TABLE if not exists new_items (id TEXT NOT NULL, PRIMARY KEY ( id ), 
                     FOREIGN KEY ( id ) REFERENCES all_items ( id ) ON DELETE CASCADE);"""
        self.cursor.execute(command)
        self.conn.commit()
        # Таблица с ключами заросов
        command = """CREATE TABLE if not exists search_key (name TEXT NOT NULL);"""
        self.cursor.execute(command)
        self.conn.commit()
        # Таблица с настройками программы
        command = """CREATE TABLE if not exists settings (name TEXT NOT NULL, value TEXT);"""
        self.cursor.execute(command)
        self.conn.commit()

    def save_settings(self, name: str, value: str):
        """
        Сохранение настройки программы в таблице
        :param name: название параметра
        :param value: текстовое значение параметра
        :return: None
        """
        if isinstance(name, str) and isinstance(value, str):
            # Проверка на наличие записанного ранее значения
            check = self.load_settings(name)
            if check:
                try:
                    command = "UPDATE settings SET value = ? WHERE name = ?"
                    self.cursor.execute(command, (value, name))
                except sqlite3.Error as error:
                    print(f"Ошибка при обновлении значения в таблице settings", error)
                finally:
                    self.conn.commit()
            else:
                try:
                    command = """INSERT INTO settings (name, value) VALUES(?, ?);"""
                    self.cursor.execute(command, (name, value))
                except sqlite3.Error as error:
                    print(f"Ошибка при добавлении значения в таблицу settings", error)
                finally:
                    self.conn.commit()
        else:
            print("Значения должны быть строкового типа")

    def load_settings(self, name: str) -> str:
        """
        Загрузка параметра из таблицы
        :param name: название параметра строкового типа
        :return: str
        """
        try:
            sql_select_query = """SELECT * FROM settings WHERE name = ?;"""
            self.cursor.execute(sql_select_query, (name, ))
            records = self.cursor.fetchone()
        except sqlite3.Error as error:
            print(f"Ошибка при чтении данных из таблицы", error)
        if records:
            return records[1]
        else:
            return None

    def close_bd(self):
        """
        Закрыть соединение с базой данной
        :return: None
        """
        if self.conn:
            self.conn.close()

    def clear_table(self, name_table: str):
        """
        Очистка таблицы от записей
        :param name_table: наименование таблицы
        :return: None
        """
        try:
            sql_select_query = f"DELETE FROM {name_table};"
            self.cursor.execute(sql_select_query)
        except sqlite3.Error as error:
            print(f"Ошибка при удалении все значений таблицы {name_table}", error)
        finally:
            self.conn.commit()

    @staticmethod
    def search_words(text: str, pattern: str) -> bool:
        """
        Определение соответствия ключевым словам
        :param text: название объявления строкового типа
        :param pattern: ключевые фразы строкового типа
        :return: True или False
        """
        if text and pattern:
            words = [w for w in pattern.split() if len(w) > 0 and w[0] not in "-"]
            words_not = [w[1:] for w in pattern.split() if len(w) > 0 and w[0] == "-"]
            result = [re.search(r'(\b%s\w*\b)' % re.escape(word), text, re.I) for word in words]
            result2 = [re.search(r'(\b%s\w*\b)' % re.escape(word), text, re.I) for word in words_not]
            if all(result) and not any(result2):
                return True
            else:
                return False
        else:
            return False

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
        sql_select_query = """SELECT * FROM all_items WHERE id = ?;"""
        self.cursor.execute(sql_select_query, (id_contract,))
        records = self.cursor.fetchall()
        # в случае наличия записей в таблице
        if len(records):
            # получаем и инвертируем метку контракта
            id_target = records[0][9]
            id_target = 0 if id_target else 1
            command = """UPDATE all_items SET target = ? WHERE id = ?;"""
            self.cursor.execute(command, (id_target, id_contract))

    def get_count_records(self) -> int:
        """
        Возвращает общее количество записей в базе данных
        :return: общее количество записей в базе данных
        """
        count = 0
        if self.conn:
            sql_query = """SELECT count(*) FROM all_items;"""
            self.cursor.execute(sql_query)
            count = self.cursor.fetchone()[0]
        return count

    def get_count_new_records(self) -> int:
        """
        Возвращает общее количество записей в базе данных
        :return: общее количество записей в базе данных
        """
        count = 0
        if self.conn:
            sql_query = """SELECT count(*) FROM new_items;"""
            self.cursor.execute(sql_query)
            count = self.cursor.fetchone()[0]
        return count

    def add_to_table(self, item: dict):
        """
        Добавление одного элемента в базу данных
        :param item: словарь с записями
        :return: None
        """
        if self.cursor:
            keys = ('id', 'status', 'name', 'price', 'placed', 'updated', 'ending', 'customer', 'url', 'target')
            new = self.get_tuple_from_keys(item, keys)
            # проверка наличия существующего элемента в базе
            sql_select_query = """select * from all_items where id = ?;"""
            self.cursor.execute(sql_select_query, (item['id'],))
            records = self.cursor.fetchall()
            if len(records) == 0:
                # при отсутствии элементов с таким номер добавляеться запись в основную таблицу
                command = """INSERT INTO all_items (id, status, name, price, placed, updated, ending, 
                             customer, url, target) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
                self.cursor.execute(command, new)
                # Добавление в таблицу с новыми заявками
                command = """INSERT INTO new_items (id) VALUES(?);"""
                self.cursor.execute(command, (item['id'], ))
            else:
                # обновление существующей записи
                keys = ('status', 'name', 'price', 'placed', 'updated', 'ending', 'customer', 'url', 'id')
                command = """UPDATE all_items SET status = ?, name = ?, price = ?, placed = ?, updated = ?, 
                            ending = ?, customer = ?, url = ? where id = ?;"""
                self.cursor.execute(command, self.get_tuple_from_keys(item, keys))

    def add_items_to_table(self, items: list):
        """
        Добавление нескольких элементов в базу данных
        :param items: список словарей
        :return: None
        """
        if not self.conn:
            self.connect_to_bd()
        try:
            # Сохранение в базе данных
            for item in items:
                self.add_to_table(item)
        finally:
            self.conn.commit()

    def get_items(self, table: str = "all_items", status: str = "") -> list:
        """
        Чтение данных с базы
        :param table: название таблицы, по умолчанию чтение всех записей
        :param status: название статуса записей
        :return: список кортежей
        """
        records = []
        if not self.conn:
            self.connect_to_bd()
        try:
            if table == "all_items":
                if status == "":
                    sql_select_query = f"SELECT * FROM {table};"
                else:
                    sql_select_query = f'SELECT * FROM {table} WHERE status = "{status}";'
            else:
                if status == "":
                    sql_select_query = f"""SELECT a.id, a.status, a.name, a.price, a.placed, a.updated, 
                                       a.ending, a.customer, a.url FROM all_items AS a JOIN new_items As n 
                                       ON n.id = a.id ;"""
                else:
                    sql_select_query = f"""SELECT a.id, a.status, a.name, a.price, a.placed, a.updated, a.ending, 
                                           a.customer, a.url FROM all_items AS a JOIN new_items As n ON n.id = a.id 
                                           WHERE a.status = '{status}';"""
            self.cursor.execute(sql_select_query)
            records = self.cursor.fetchall()
        except sqlite3.Error as error:
            print(f"Ошибка чтения из таблицы {table}", error)
        return records

    def filter_items(self, items: list, status: str = "", filter: bool = False) -> list:
        """
        Фильтрация списка объявлений на соответствие запросам и статуса
        :param items: список кортежей объявления
        :param status: строка, статус для фильтрации записей
        :return: список объявлений
        """
        filter_records = []
        filter_keys = self.get_search_key()
        for i in items:
            if i[2]:
                find_key = True
                # Проверка на соответствие записи ключевым словам
                if filter and len(filter_keys) > 0:
                    find_key = False
                    for key in filter_keys:
                        find_key = self.search_words(i[2], key[0])
                        if find_key:
                            break
                # Проверка нужного статуса у записи
                if i[1] == status and find_key:
                    filter_records.append(i)
                elif status == "" and find_key:
                    filter_records.append(i)
        return filter_records

    def search_items(self, items: list, request: str, column: str) -> list:
        """
        Фильтрация списка объявлений на соответствие запросам и статуса
        :param items: список кортежей объявления
        :param status: строка, статус для фильтрации записей
        :return: список объявлений
        """
        filter_records = []
        if len(request):
            for i in items:
                # Поиск в названии объявления
                if column == "name":
                    # Проверка на соответствие записи ключевым словам
                    find_key = False
                    if len(request) > 0:
                        find_key = self.search_words(i[2], request)
                    if find_key:
                        filter_records.append(i)
                # Поиск в статусе объявления
                if column == "status":
                    # Проверка на соответствие записи ключевым словам
                    find_key = False
                    if len(request) > 0:
                        find_key = self.search_words(i[1], request)
                    if find_key:
                        filter_records.append(i)
                # Поиск в заказчике объявления
                if column == "customer":
                    # Проверка на соответствие записи ключевым словам
                    find_key = False
                    if len(request) > 0:
                        find_key = self.search_words(i[7], request)
                    if find_key:
                        filter_records.append(i)
                # Поиск в идентификаторе объявления
                if column == "id":
                    # Проверка на соответствие записи ключевым словам
                    find_key = False
                    if len(request) > 0:
                        find_key = self.search_words(i[0], request)
                    if find_key:
                        filter_records.append(i)
                # Поиск по цене
                if column == "price_more" or column == "price_less":
                    try:
                        search_price = float(request)
                    except:
                        return []
                    if not self.conn:
                        self.connect_to_bd()
                    if column == "price_more":
                        sql_select_query = f'SELECT * FROM all_table WHERE price > "{search_price}";'
                    if column == "price_less":
                        sql_select_query = f'SELECT * FROM all_table WHERE price < "{search_price}";'
                    self.cursor.execute(sql_select_query)
                    filter_records = self.cursor.fetchall()
        return filter_records

    def get_items_on_request(self, request: str) -> list:
        """
        Чтение данных с базы соответствующих запросу
        :param request: строковая переменная с ключевыми словами
        :return: список кортежей
        """
        records = []
        if not self.conn:
            self.connect_to_bd()
        try:
            sql_select_query = f'SELECT * FROM all_items;'
            self.cursor.execute(sql_select_query)
            all_records = self.cursor.fetchall()
        except sqlite3.Error as error:
            print(f"Ошибка чтения из таблицы", error)
        if len(all_records):
            for elem in all_records:
                if isinstance(elem[2], str) and request in elem[2].lower():
                    records.append(elem)
            return records
        else:
            return []

    def get_search_key(self) -> list:
        """
        Чтение из базы данных ключевых фраз
        :return: список записей с поисковыми ключами
        """
        records = []
        if not self.conn:
            self.connect_to_bd()
        try:
            sql_select_query = f"SELECT * FROM search_key;"
            self.cursor.execute(sql_select_query)
            records = self.cursor.fetchall()
        except sqlite3.Error as error:
            print("Ошибка чтения из таблицы search_key", error)
        return records

    def save_search_key(self, records: list):
        """
        Сохранение в базе данных поисковых фраз
        :param records: список из поисковых фраз
        :return:
        """
        if not self.conn:
            self.connect_to_bd()
        try:
            # Очистка таблицы с новыми объявлениями
            self.clear_table(name_table="search_key")
            # Сохранение в базе данных
            command = """INSERT INTO search_key (name) VALUES (?);"""
            self.cursor.executemany(command, records)
        except sqlite3.Error as error:
            print("Ошибка записи в таблицу search_key", error)
        finally:
            self.conn.commit()

