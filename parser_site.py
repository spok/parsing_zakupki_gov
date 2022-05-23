import requests
from bs4 import BeautifulSoup
import lxml
import time
import threading
from queue import Queue
import logging


class ParserSite:
    lock_items = threading.Lock()
    q = Queue()

    def __init__(self, parent=None):
        self.main = parent
        self.headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:45.0) Gecko/20100101 Firefox/45.0'
        }
        self.items = []
        self.count_pages = 0
        logging.basicConfig(filename="info.log", filemode='w', level=logging.INFO)

    @staticmethod
    def get_page_url(page: int) -> str:
        """
        Генерация адреса для номера страницы
        :param page: номер страницы
        :return: полный url страницы
        """
        url = 'https://zakupki.gov.ru/epz/order/extendedsearch/results.html?morphology=on&search-filter='
        url += '%D0%94%D0%B0%D1%82%D0%B5+%D1%80%D0%B0%D0%B7%D0%BC%D0%B5%D1%89%D0%B5%D0%BD%D0%B8%D1%8F&pageNumber='
        url += str(page)
        url += "&sortDirection=false&recordsPerPage=_50&showLotsInfoHidden=false&sortBy=UPDATE_DATE&fz44=on&fz223=on'" \
               "&af=on&ca=on&pc=on&pa=on&currencyIdGeneral=-1"
        return url

    @staticmethod
    def get_price(text: str) -> float:
        """
        Обработка текстовой строки со стоимостью закупки
        :param text: текстовая строка
        :return: вещественное значение стоимости или None при ошибке
        """
        if not text:
            return None
        clear_text = ''.join([i for i in text if i in '0123456789,.'])
        clear_text = clear_text.replace(',', '.')
        try:
            value = float(clear_text)
        except ValueError:
            value = None
            logging.error(f'Ошибка конвертации: исходное-{text}, чистое-{clear_text}')
        return value

    @staticmethod
    def get_soup(url: str, headers: dict) -> object:
        """
        Получение структуры html страницы
        :param url: полный путь текстового формата
        :param headers: словарь с типом браузера
        :return: документ со структурой страницы
        """
        response = requests.get(url, headers=headers)
        if not response:
            return None
        soup = BeautifulSoup(response.text, 'lxml')
        return soup

    @staticmethod
    def get_guotes(soup, tag: str, class_name: str) -> list:
        """
        Чтение блоков обявлений
        :param soup: объект Beautifulsoup
        :param tag: тип тэга блока
        :param class_name: тип класса блока
        :return: список объявлений
        """
        quotes = list()
        if soup:
            quotes = soup.find_all(tag, class_name)
        if len(quotes) == 0:
            return None
        return quotes

    @staticmethod
    def get_href(quote: str, atrib1: str, atrib2: str) -> str:
        """
        Чтение данных из блока html
        :param quote: блок html страницы
        :param atrib1: название тего
        :param atrib2: название класса
        :return: искомый текст
        """
        href = quote.find(atrib1, class_=atrib2).find('a').get('href')
        href = r'https://zakupki.gov.ru' + href
        return href

    @staticmethod
    def get_field_text(quote: str, atrib1: str, atrib2: str) -> str:
        """
        Чтение данных из блока html
        :param quote: блок html страницы
        :param atrib1: название тего
        :param atrib2: название класса
        :return: искомый текст
        """
        field = quote.find(atrib1, class_=atrib2)
        if field:
            text = field.get_text(strip=True)
            return text
        else:
            return None

    @staticmethod
    def get_fields(quote: str, atrib1: str, atrib2: str) -> list:
        """
        Получение списка полей
        :param quote: блок html страницы
        :param atrib1: название тега блока
        :param atrib2: название класса
        :return: список с текстом полей
        """
        fields = quote.find_all(atrib1, class_=atrib2)
        if len(fields) > 0:
            for i in range(len(fields)):
                fields[i] = fields[i].get_text()
        return fields

    @staticmethod
    def get_id(text: str):
        """
        Получение номера объявления
        :param text: текстовое значение
        :return: очиженный номер
        """
        if text:
            clear_text = ''.join([i for i in text if i in '0123456789'])
            return clear_text
        return None

    def get_page_count(self) -> int:
        """
        Определение количества страниц
        :return: количество страниц типа int
        """
        pages = 1
        url = self.get_page_url(1)
        soup = self.get_soup(url, self.headers)
        pages_block = self.get_guotes(soup, 'div', 'paginator align-self-center m-0')
        if pages_block:
            li_pages = self.get_fields(pages_block[0], 'span', 'link-text')
            try:
                pages = int(li_pages[-1])
            except ValueError:
                pages = 1
        return pages

    def parse_one_page(self, q):
        """
        Парсинг одной страницы
        :param q: очередь заданий типа Queue
        :return: None
        """
        while True:
            # Получение задания из очереди
            number = q.get()
            find_items = []
            # Получение страницы
            url = self.get_page_url(number)
            soup = self.get_soup(url, self.headers)
            # Чтение блоков с объявлениями
            quotes = self.get_guotes(soup, 'div', 'row no-gutters registry-entry__form mr-0')
            if not quotes:
                q.task_done()
            # Перебор блоков с закупками
            for quote in quotes:
                item = dict()
                # Получение номера объявления
                text = self.get_id(self.get_field_text(quote, 'div', 'registry-entry__header-mid__number'))
                item['id'] = text
                # Получение ссылки на закупку
                text = self.get_href(quote, 'div', 'registry-entry__header-mid__number')
                item['url'] = text
                # Получение статуса
                text = self.get_field_text(quote, 'div', 'registry-entry__header-mid__title text-normal')
                item['status'] = text
                # Получение описание работ
                text = self.get_field_text(quote, 'div', 'registry-entry__body-value')
                item['name'] = text
                # Получение заказчика работ
                text = self.get_field_text(quote, 'div', 'registry-entry__body-href')
                item['customer'] = text
                # Получение цены работы
                text = self.get_field_text(quote, 'div', 'price-block__value')
                item['price'] = self.get_price(text)
                # Чтение дат объявления
                date_title = self.get_fields(quote, 'div', 'data-block__title')
                date_value = self.get_fields(quote, 'div', 'data-block__value')
                if len(date_title) == len(date_value):
                    for i, elem in enumerate(date_title):
                        if elem == 'Размещено':
                            item['placed'] = date_value[i]
                        if elem == 'Обновлено':
                            item['updated'] = date_value[i]
                        if elem == 'Окончание подачи заявок':
                            item['ending'] = date_value[i]
                find_items.append(item)

            self.lock_items.acquire()
            try:
                self.items.extend(find_items)
            finally:
                self.lock_items.release()
            print(f'Выполнена страница - {number}')
            self.main.completed_pages = 1
            q.task_done()

    def parsing(self):
        """
        Парсинг сайта
        :return: None
        """
        self.items = []
        self.count_pages = self.get_page_count()
        for x in range(self.count_pages):
            self.q.put(x + 1)
        threads = []
        for _ in range(4):
            threads.append(threading.Thread(target=self.parse_one_page, args=(self.q,), daemon=True))
        for thread in threads:
            thread.start()
        self.q.join()
        self.main.sql.add_items_to_table(self.items)
