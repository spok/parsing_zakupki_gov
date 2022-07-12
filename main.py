import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QThread
from gui import MainWindow
from parser_site import ParserSite
from sql_base import *
import webbrowser


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
        self.combo_time_step.currentIndexChanged.connect(self.change_time)
        self.button_timer.clicked.connect(self.start_timer)
        self.button_manual_run.clicked.connect(self.start_parsing)
        self.button_save_keys.clicked.connect(self.save_key_from_table)
        self.button_reload.clicked.connect(self.load_key_from_bd)
        self.button_clear_keys.clicked.connect(self.clear_key_in_bd)
        self.button_search.clicked.connect(self.show_request)
        self.button_show.clicked.connect(self.show_in_table)
        self.button_del_new.clicked.connect(self.clear_new_records)
        self.clear_new.triggered.connect(self.clear_new_in_bd)
        self.clear_all.triggered.connect(self.clear_all_in_bd)
        self.save_base.triggered.connect(self.export_table_to_xls)
        self.save_key.triggered.connect(self.export_key_to_xls)
        self.import_base.triggered.connect(self.import_table_from_xls)
        self.import_key.triggered.connect(self.import_key_from_xls)
        self.to_exit.triggered.connect(self.close)
        self.parse_thread.finished.connect(self.save_bd)
        self.table.doubleClicked.connect(self.open_url)
        self.table.openAct.triggered.connect(self.open_url)
        self.items = []
        self.__pages = 0
        self.__count_new_records = 0
        self.timer_id = 0
        data = self.sql.load_settings("time_step")
        if data:
            self.step_value = int(data)
        else:
            self.step_value = 1
        self.set_combobox1()
        self.remained_time = 0
        self.run_timer = False
        self.show_count_records()
        self.load_key_from_bd()
        self.show_in_table()

    @property
    def completed_pages(self):
        return self.__pages

    @completed_pages.setter
    def completed_pages(self, count):
        self.__pages += count
        self.status_bar.showMessage(f'Количество обработанных страниц: {self.__pages} из {self.pr.count_pages}', 5)

    def export_table_to_xls(self):
        """
        Выплнение экспорта записей из базы данных в формат Excel
        :return: None
        """
        file_name = self.open_dialog.getSaveFileName(self, "Выбор файла для сохранения записей",
                                                     filter="Excel files (*.xlsx *.xls)")
        if len(file_name[0]):
            self.sql.export_table(file_name[0])

    def export_key_to_xls(self):
        """
        Выплнение экспорта ключевых запросов из базы данных в формат Excel
        :return: None
        """
        file_name = self.open_dialog.getSaveFileName(self, "Выбор файла для сохранения записей",
                                                     filter="Excel files (*.xlsx *.xls)")
        if len(file_name[0]):
            self.sql.export_key(file_name[0])

    def import_table_from_xls(self):
        """
        Импорт базы данных из файла Excel
        :return: None
        """
        file_name = self.open_dialog.getOpenFileName(self, "Импорт данных",
                                                     filter="Excel files (*.xlsx *.xls)")
        if len(file_name[0]):
            self.sql.import_table(file_name[0])
            # Вывод количества записей
            self.show_count_records()
            # Вывод в таблицу записей
            self.show_in_table()

    def import_key_from_xls(self):
        """
        Импорт базы данных из файла Excel
        :return: None
        """
        file_name = self.open_dialog.getOpenFileName(self, "Импорт данных",
                                                     filter="Excel files (*.xlsx *.xls)")
        if len(file_name[0]):
            self.sql.import_key(file_name[0])
            self.load_key_from_bd()

    def set_combobox1(self):
        """Отображения временного интервала на элементе"""
        for i in range(self.combo_time_step.count()):
            if self.step_value == self.combo_time_step.itemData(i):
                self.combo_time_step.setCurrentIndex(i)

    def change_time(self):
        """Изменение шага по времени между парсингами сайта"""
        data = self.combo_time_step.currentData()
        if isinstance(data, int):
            self.step_value = data
            self.run_timer = False
            self.set_button1()
            self.remained_time = self.step_value * 60
            self.lsd_countdown.display(str(self.remained_time))
            self.sql.save_settings("time_step", str(self.step_value))

    def set_button1(self):
        """Изменение настроек кнопки в зависимости от режима таймера"""
        if self.run_timer:
            self.button_timer.setText("Таймер ВКЛ")
            self.button_timer.setStyleSheet('background: rgb(255,0,0);')
        else:
            self.button_timer.setText("Таймер ВЫКЛ")
            self.button_timer.setStyleSheet('background: rgb(225,225,225);')
            self.setWindowTitle(f"Таймер выключен")

    def start_timer(self):
        """
        Запуск таймера для выполнения парсинга
        :return:
        """
        if not self.run_timer:
            self.run_timer = True
            self.timer_id = self.startTimer(1000, timerType=Qt.CoarseTimer)
        else:
            self.killTimer(self.timer_id)
            self.timer_id = 0
            self.run_timer = False
        self.set_button1()
        self.remained_time = self.step_value * 60

    def start_parsing(self):
        """
        Запуск парсинга сайта
        :return:
        """
        self.__pages = 0
        self.items = []
        self.parse_thread.start()

    def save_bd(self):
        """
        Сохранение в базе данных
        :return:
        """
        # Сохранение записей в базу данных
        parse_items = self.pr.items
        self.sql.add_items_to_table(parse_items)
        # Вывод количества записей
        self.show_count_records()
        # Вывод в таблицу записей
        self.show_in_table()

    def show_in_table(self):
        """
        Отображение записей базы данных в таблице в соответствии с выбранным типом
        :return:
        """
        self.status_bar.clearMessage()
        records = []
        current_typ = self.combo_what_show.currentIndex()
        # Показать все новые активные соответствующие запросам или отобразить новые активные
        if current_typ == 0 or current_typ == 1:
            records = self.sql.get_items(table="new_items")
            if current_typ == 0:
                records = self.sql.filter_items(records, status="Подача заявок", filter=True)
                if records:
                    self.__count_new_records = len(records)
            else:
                records = self.sql.filter_items(records, status="Подача заявок", filter=False)
        elif current_typ == 2 or current_typ == 3:
            records = self.sql.get_items(table="all_items")
            if current_typ == 2:
                records = self.sql.filter_items(records, status="Подача заявок", filter=True)
            else:
                records = self.sql.filter_items(records, status="Подача заявок", filter=False)
        else:
            records = self.sql.get_items(table="all_items")
        # Отрисовка таблицы
        self.show_table(records)

    def show_count_records(self):
        """
        Отображение на метке общего количества записей в таблице
        :return: None
        """
        count = self.sql.get_count_records()
        self.label_count_records.setText(f"Общее количество записей: {count}")
        count = self.sql.get_count_new_records()
        self.label_new_records.setText(f"Новых записей: {count}")

    def save_key_from_table(self):
        """
        Сохранение поисковых запросов в таблицу базы данных
        :return:
        """
        keys = self.keys_text.toPlainText()
        keys = keys.split(sep='\n')
        records = [(key, ) for key in keys]
        self.sql.save_search_key(records)

    def load_key_from_bd(self):
        """
        Загрузка в таблицу поисковых фраз из базы данных
        :return:
        """
        self.keys_text.clear()
        records = self.sql.get_search_key()
        for item in records:
            self.keys_text.insertPlainText(item[0] + "\n")

    def clear_key_in_bd(self):
        self.keys_text.clear()
        self.sql.clear_table(name_table='search_key')

    def clear_new_in_bd(self):
        self.sql.clear_table(name_table='new_items')
        self.__count_new_records = 0

    def clear_all_in_bd(self):
        self.sql.clear_table(name_table='all_items')
        self.sql.clear_table(name_table='new_items')
        self.__count_new_records = 0
        # Вывод количества записей
        self.show_count_records()
        # Вывод в таблицу записей
        self.show_in_table()

    def show_request(self):
        """
        Вывод записей соответствующих запросу
        :return: none
        """
        request = self.edit_search_text.text().lower()
        column = self.combo_source.currentData()
        records = self.sql.get_items(table="all_items")
        records = self.sql.search_items(records, request=request, column=column)
        if len(records):
            self.show_table(records)

    def clear_new_records(self):
        """
        Очистка списка новых записей
        :return: None
        """
        self.sql.clear_table(name_table='new_items')
        self.__count_new_records = 0
        self.show_in_table()
        self.show_count_records()

    def open_url(self):
        """
        Открыть в браузере ссылку на объявление
        :return: None
        """
        for idx in self.table.selectionModel().selectedIndexes():
            # Определение строки и идентификатора
            row_number = idx.row()
            select_id = self.table.item(row_number, 0).text()
            # Чтение ссылки на объявление
            url = self.sql.get_url_from_bd(select_id)
            try:
                webbrowser.open_new_tab(url)
            except:
                print(f"Ошибка при открытии ссылки {url}")

    def timerEvent(self, event) -> None:
        """
        Обработка события таймера
        :param event:
        :return:
        """
        self.lsd_countdown.display(str(self.remained_time))
        # Отрисовка на иконке количества найденных объявлений
        self.setWindowIcon(self.generate_icontext(self.__count_new_records))
        text = f'Осталось {str(self.remained_time)} сек.'
        self.setWindowTitle(text)
        self.remained_time -= 1
        if self.remained_time < 0:
            self.remained_time = self.step_value * 60
            self.start_parsing()

    def closeEvent(self, a0) -> None:
        self.sql.close_bd()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainwindow = Main()
    mainwindow.show()
    sys.exit(app.exec_())
