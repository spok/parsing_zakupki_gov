from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QCheckBox, QLineEdit, QLabel,
                             QMenuBar, QMenu, QFileDialog, QPushButton, QLabel, QLCDNumber, QComboBox, QTextEdit,
                             QSizePolicy, QTableWidget, QTableWidgetItem, QGroupBox, QPlainTextEdit)
from PyQt5.QtCore import (Qt, QRect, QSize)
from PyQt5.QtGui import QFont


class NameText(QPlainTextEdit):
    """
    Класс для отображения названия закупки с переносом строк
    """
    def __init__(self, text: str):
        super().__init__()
        self.setPlainText(text)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWordWrapMode(1)
        self.setReadOnly(True)
        self.setStyleSheet('border-style: solid; border-width: 0px; border-color: white;')
        self.updateRequest.connect(self.handle_updateRequest)
        self.handle_updateRequest(QRect(), 0)

    def handle_updateRequest(self, rect, dy):
        doc = self.document()
        tb = doc.findBlockByNumber(doc.blockCount() - 1)
        h = self.blockBoundingGeometry(tb).bottom() + 2 * doc.documentMargin()
        self.setFixedHeight(h)


class MainWindow(QWidget):
    hor_header = ['№ закупки', 'Название', 'Стоимость, р.', 'Статус', 'Дата окончания']

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Парсинг zakupki.gov.ru')
        self.resize(800, 600)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Настройка меню
        self.menu = QMenuBar(self)
        self.file_menu = QMenu('Файл')
        self.save_base = self.file_menu.addAction('Экспорт базы данных в Excel')
        self.to_exit = self.file_menu.addAction('Выход')
        self.menu.addMenu(self.file_menu)
        # Компановщики основного окна
        self.vbox = QVBoxLayout(self)
        self.vbox_tab1 = QVBoxLayout()
        self.vbox_tab2 = QVBoxLayout()
        self.hbox = QHBoxLayout()
        self.tab_widget = QTabWidget()
        self.tab_1 = QWidget()
        self.tab_2 = QWidget()
        self.tab_widget.addTab(self.tab_1, "База данных")
        self.tab_widget.addTab(self.tab_2, "Запросы")

        # Область управления временем запуска парсинга
        self.grid1 = QGridLayout()
        self.group_job = QGroupBox("Запуск сканирования")
        self.button1 = QPushButton('Таймер\nВЫКЛ')
        self.button1.setSizePolicy(sizePolicy)
        self.button1.setFixedSize(QSize(60, 60))
        self.button2 = QPushButton('Ручной запуск')
        self.countdown = QLCDNumber(5)
        self.countdown.display(120)
        self.countdown.setSegmentStyle(QLCDNumber.Flat)
        self.grid1.addWidget(self.countdown, 0, 0)
        self.grid1.addWidget(self.button2, 1, 0)
        self.grid1.addWidget(self.button1, 0, 1, 2, 1)
        self.group_job.setLayout(self.grid1)
        # Область поиска контрактов по запросам
        self.group_search = QGroupBox("Поиск по контрактам")
        self.vbox_2 = QVBoxLayout()
        self.hbox_2 = QHBoxLayout()
        self.search_text = QLineEdit()
        self.label_source = QLabel("Искать в:")
        self.combo_source = QComboBox()
        self.combo_source.addItem("названии контрактов")
        self.combo_source.addItem("идентификаторе")
        self.combo_source.addItem("заказчике")
        self.combo_source.addItem("статусе")
        self.combo_source.addItem("стоимостью больше")
        self.combo_source.addItem("стоимостью меньше")
        self.hbox_2.addWidget(self.label_source)
        self.hbox_2.addWidget(self.combo_source)
        self.button_search = QPushButton("Искать")
        self.vbox_2.addWidget(self.search_text)
        self.vbox_2.addLayout(self.hbox_2)
        self.vbox_2.addWidget(self.button_search)
        self.group_search.setLayout(self.vbox_2)
        # Область настройки вывода в таблицу
        self.group = QGroupBox('База данных')
        self.vbox_3 = QVBoxLayout()
        self.combo = QComboBox()
        self.combo.addItem('Все новые активные')
        self.combo.addItem('Все новые')
        self.combo.addItem('Все активные')
        self.combo.addItem('Все')
        self.show_target = QCheckBox("соответсвующие запросам")
        self.button_show = QPushButton("Вывести записи")
        self.vbox_3.addWidget(self.combo)
        self.vbox_3.addWidget(self.show_target)
        self.vbox_3.addWidget(self.button_show)
        self.group.setLayout(self.vbox_3)
        # область вывода результата парсинга сайта
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(self.hor_header)
        self.resize_table()
        # информационная область внизу экрана
        self.bottom_panel = QHBoxLayout()
        self.status_label = QLabel()
        self.status_label.setText('Количество обработанных страниц: 0 из 0')
        self.count_records = QLabel()
        self.count_records.setText('Количество записей: 0')
        self.bottom_panel.addWidget(self.status_label)
        self.bottom_panel.addStretch(0)
        self.bottom_panel.addWidget(self.count_records)
        # вторая вкладка с запросами
        self.label_keys = QLabel("Ключевые слова для выбора контрактов")
        self.keys_text = QTextEdit()
        self.keys_text.setFont(QFont("Times", 12, QFont.Bold))
        self.keys_text.setLineWrapMode(0)
        self.hbox_button = QHBoxLayout()
        self.button_save_keys = QPushButton("Сохранить изменения")
        self.button_reload = QPushButton("Отменить изменения")
        self.button_clear_keys = QPushButton("Очистить ключевые слова")
        self.hbox_button.addWidget(self.button_save_keys)
        self.hbox_button.addWidget(self.button_reload)
        self.hbox_button.addWidget(self.button_clear_keys)
        self.vbox_tab2.addWidget(self.label_keys)
        self.vbox_tab2.addWidget(self.keys_text)
        self.vbox_tab2.addLayout(self.hbox_button)

        # Настройка размещения компонентов
        self.hbox.addWidget(self.group_job)
        self.hbox.addWidget(self.group_search)
        self.hbox.addWidget(self.group)
        self.vbox_tab1.addLayout(self.hbox)
        self.vbox_tab1.addWidget(self.table)
        self.vbox_tab1.addLayout(self.bottom_panel)
        self.vbox.addSpacing(20)
        self.vbox.addWidget(self.tab_widget)
        self.tab_1.setLayout(self.vbox_tab1)
        self.tab_2.setLayout(self.vbox_tab2)

    def show_table2(self, items: list):
        """
        Заполнение таблицы данными из списка со словарями
        :param items: список словарей
        :return: None
        """
        self.table.clear()
        self.table.setHorizontalHeaderLabels(self.hor_header)
        self.table.setRowCount(len(items))
        sizepolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        keys = ['id', 'name', 'price', 'status', 'ending']
        for i, item in enumerate(items):
            for j, key in enumerate(keys):
                if key in item:
                    if type(item[key]) == str:
                        if key == 'name':
                            elem = NameText(item[key])
                            self.table.setCellWidget(i, j, elem)
                        else:
                            elem = QTableWidgetItem(item[key])
                            self.table.setItem(i, j, elem)
                    else:
                        elem = QTableWidgetItem(str(item[key]))
                        self.table.setItem(i, j, elem)
        rect = self.rect()
        self.resize(rect.width(), rect.height() - 1)

    def show_table(self, items: list):
        """
        Заполнение таблицы данными из списка с кортежами
        :param items: список кортежей
        :return: None
        """
        self.table.clear()
        self.table.setHorizontalHeaderLabels(self.hor_header)
        self.table.setRowCount(len(items))
        sizepolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        indexs = [0, 2, 3, 1, 6]
        for i, item in enumerate(items):
            for j, index in enumerate(indexs):
                if type(item[index]) == str:
                    if index == 2:
                        elem = NameText(item[index])
                        self.table.setCellWidget(i, j, elem)
                    else:
                        elem = QTableWidgetItem(item[index])
                        self.table.setItem(i, j, elem)
                else:
                    elem = QTableWidgetItem(str(item[index]))
                    self.table.setItem(i, j, elem)
        rect = self.rect()
        self.resize(rect.width(), rect.height() - 1)

    def resize_table(self):
        """Изменение размеров таблицы"""
        # Изменение ширины столбцов
        w_1 = round(self.table.width() * 0.1)
        if w_1 < 140:
            w_1 = 140
        w_2 = self.table.width() - w_1 * 4 - 20
        self.table.setColumnWidth(0, w_1)
        self.table.setColumnWidth(1, w_2)
        self.table.setColumnWidth(2, w_1)
        self.table.setColumnWidth(3, w_1)
        # Изменение высоты строк под высоту текста
        for i in range(self.table.rowCount()):
            elem = self.table.cellWidget(i, 1)
            if elem:
                self.table.setRowHeight(i, elem.height() + 5)

    def resizeEvent(self, event) -> None:
        """Обработка изменения размеров окна"""
        self.resize_table()




