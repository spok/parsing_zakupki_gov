from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QCheckBox,
                             QMenuBar, QMenu, QFileDialog, QPushButton, QLabel, QLCDNumber,
                             QSizePolicy, QTableWidget, QTableWidgetItem, QGroupBox, QPlainTextEdit)
from PyQt5.QtCore import Qt, QRect


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
        self.vbox = QVBoxLayout()
        self.hbox = QHBoxLayout()
        self.grid1 = QGridLayout()
        # Область управления временем запуска парсинга
        self.button1 = QPushButton('Таймер\nВЫКЛ')
        self.button1.setSizePolicy(sizePolicy)
        self.button2 = QPushButton('Ручной запуск')
        self.countdown = QLCDNumber(5)
        self.countdown.display(120)
        self.countdown.setSegmentStyle(QLCDNumber.Flat)
        self.grid1.addWidget(self.countdown, 0, 0)
        self.grid1.addWidget(self.button2, 1, 0)
        self.grid1.addWidget(self.button1, 0, 1, 2, 1)
        # Область настройки вывода в таблицу
        self.group = QGroupBox('Вывод результата')
        self.group_vbox = QVBoxLayout()
        self.status1 = QCheckBox("новые соответствующие запросу")
        self.status2 = QCheckBox("только новые")
        self.status3 = QCheckBox("все соответствующие запросу")
        self.status4 = QCheckBox("все")
        self.button_show = QPushButton("Вывести результат")
        self.group_vbox.addWidget(self.status1)
        self.group_vbox.addWidget(self.status2)
        self.group_vbox.addWidget(self.status3)
        self.group_vbox.addWidget(self.status4)
        self.group_vbox.addWidget(self.button_show)
        self.group.setLayout(self.group_vbox)
        # область вывода результата парсинга сайта
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(self.hor_header)
        self.resize_table()
        self.status_label = QLabel()
        self.status_label.setText('Количество обработанных страниц: 0 из 0')
        # Настройка размещения компонентов
        self.hbox.addLayout(self.grid1)
        self.hbox.addWidget(self.group)
        self.vbox.addLayout(self.hbox)
        self.vbox.addWidget(self.table)
        self.vbox.addWidget(self.status_label)
        self.setLayout(self.vbox)

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




