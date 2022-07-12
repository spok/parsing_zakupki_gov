from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTabWidget, QLineEdit,
                             QMenuBar, QMenu, QFileDialog, QPushButton, QLabel, QLCDNumber, QComboBox, QTextEdit,
                             QSizePolicy, QTableWidget, QTableWidgetItem, QGroupBox, QPlainTextEdit, QStatusBar,
                             QAbstractItemView, QAction)
from PyQt5.QtCore import (Qt, QRect, QSize)
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter, QContextMenuEvent
from math import cos, sin, pi
import copy


class MyTable(QTableWidget):
    def __init__(self):
        super().__init__()
        self.contextMenu = QMenu(self)
        self.openAct = self.contextMenu.addAction("Открыть в браузере")

    def contextMenuEvent(self, event) -> None:
        self.contextMenu.addAction(self.openAct)
        action = self.contextMenu.exec_(self.mapToGlobal(event.pos()))


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


class MainWindow(QMainWindow):
    hor_header = ['№ закупки', 'Название', 'Стоимость, р.', 'Статус', 'Дата окончания']

    def __init__(self, parent=None):
        super().__init__(parent)
        self.central_widget = QWidget()
        self.setWindowTitle('Парсинг zakupki.gov.ru')
        self.resize(800, 600)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.button_del_new = QPushButton("Очистить список новых объявлений")
        self.open_dialog = QFileDialog()
        # self.open_dialog.setNameFilter("File Excel (*.xlsx)")
        # Настройка меню
        self.menu = QMenuBar()
        self.file_menu = QMenu('Файл')
        self.export_menu = QMenu('Экспорт')
        self.file_menu.addMenu(self.export_menu)
        self.save_base = self.export_menu.addAction('Экспорт базы данных в Excel')
        self.save_key = self.export_menu.addAction('Экспорт ключевых слов в Excel')
        self.import_menu = QMenu('Импорт')
        self.file_menu.addMenu(self.import_menu)
        self.import_base = self.import_menu.addAction('Импорт базы данных из таблицы Excel')
        self.import_key = self.import_menu.addAction('Импорт ключевых слов из таблицы Excel')
        self.to_exit = self.file_menu.addAction('Выход')
        self.settings_menu = QMenu('Настройки')
        self.clear_new = self.settings_menu.addAction('Очистка таблицы новых объявлений')
        self.clear_all = self.settings_menu.addAction('Очистка таблицы всех объявлений')
        self.menu.addMenu(self.file_menu)
        self.menu.addMenu(self.settings_menu)
        self.setMenuBar(self.menu)
        # Добавление нижней информационной панели
        self.status_bar = QStatusBar()
        self.label_new_records = QLabel()
        self.label_new_records.setText('Новых записей: 0')
        self.status_bar.addPermanentWidget(self.label_new_records)
        self.label_count_records = QLabel()
        self.label_count_records.setText('Общее количество записей: 0')
        self.status_bar.addPermanentWidget(self.label_count_records)
        self.setStatusBar(self.status_bar)
        # Компановщики основного окна
        self.vbox = QVBoxLayout()
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
        self.group_job = QGroupBox("Запуск")
        self.button_timer = QPushButton('Таймер ВЫКЛ')
        self.button_manual_run = QPushButton('Ручной запуск')
        self.lsd_countdown = QLCDNumber(5)
        self.lsd_countdown.setSegmentStyle(QLCDNumber.Flat)
        self.combo_time_step = QComboBox()
        self.combo_time_step.addItem("5 минут", userData=5)
        self.combo_time_step.addItem("15 минут", userData=15)
        self.combo_time_step.addItem("30 минут", userData=30)
        self.combo_time_step.addItem("60 минут", userData=60)
        self.combo_time_step.addItem("90 минут", userData=90)
        self.combo_time_step.addItem("120 минут", userData=120)
        self.grid1.addWidget(self.lsd_countdown, 0, 0)
        self.grid1.addWidget(self.combo_time_step, 1, 0)
        self.grid1.addWidget(self.button_timer, 0, 1)
        self.grid1.addWidget(self.button_manual_run, 1, 1)
        self.group_job.setLayout(self.grid1)
        # Область поиска контрактов по запросам
        self.group_search = QGroupBox("Поиск")
        self.vbox_2 = QVBoxLayout()
        self.hbox_2 = QHBoxLayout()
        self.edit_search_text = QLineEdit()
        self.combo_source = QComboBox()
        self.combo_source.addItem("в названии контрактов", userData="name")
        self.combo_source.addItem("в идентификаторе", userData="id")
        self.combo_source.addItem("в наименовании заказчика", userData="customer")
        self.combo_source.addItem("в статусе", userData="status")
        self.combo_source.addItem("стоимостью больше", userData="price_more")
        self.combo_source.addItem("стоимостью меньше", userData="price_less")
        self.button_search = QPushButton("Искать")
        self.vbox_2.addWidget(self.edit_search_text)
        self.hbox_2.addWidget(self.combo_source)
        self.hbox_2.addWidget(self.button_search)
        self.vbox_2.addLayout(self.hbox_2)
        self.group_search.setLayout(self.vbox_2)
        # Область настройки вывода в таблицу
        self.group = QGroupBox('Вывод в таблицу')
        self.vbox_3 = QVBoxLayout()
        self.combo_what_show = QComboBox()
        self.combo_what_show.addItem('Новые активные соответствующие запросам')
        self.combo_what_show.addItem('Новые активные')
        self.combo_what_show.addItem('Все активные соответствующие запросам')
        self.combo_what_show.addItem('Все активные')
        self.combo_what_show.addItem('Все')
        self.button_show = QPushButton("Вывести записи")
        self.vbox_3.addWidget(self.combo_what_show)
        self.vbox_3.addWidget(self.button_show)
        self.group.setLayout(self.vbox_3)
        # область вывода результата парсинга сайта
        self.table = MyTable()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(self.hor_header)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.resize_table()
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
        self.vbox_tab1.addWidget(self.button_del_new)
        self.vbox.addWidget(self.tab_widget)
        self.tab_1.setLayout(self.vbox_tab1)
        self.tab_2.setLayout(self.vbox_tab2)
        self.central_widget.setLayout(self.vbox)
        self.setCentralWidget(self.central_widget)
        self.__angle_icon = 0

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
        if items:
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
        else:
            self.table.setRowCount(0)

    def resize_table(self):
        """Изменение размеров таблицы"""
        if self.table.rowCount():
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

    def rotate_clock(self, points: list) -> list:
        """
        Вращение координат часов на иконке
        :param points: список точек
        :param angle: угол поворота
        :return: list
        """

        radian = self.__angle_icon * pi / 180
        new_points = copy.deepcopy(points)
        for i in range(len(new_points)):
            new_points[i][0] = points[i][0] * cos(radian) - points[i][1] * sin(radian)
            new_points[i][1] = points[i][0] * sin(radian) + points[i][1] * cos(radian)
        self.__angle_icon += 15
        if self.__angle_icon > 360:
            self.__angle_icon = self.__angle_icon - 360
        return new_points

    def generate_icontext(self, count):
        """
        Генерация иконки с отображениекм количества новых записей
        :return: QIcon
        """
        text = ""
        icon_size = 24
        half_icon_size = round(icon_size / 2)
        new_icon = QIcon()
        new_pixmap = QPixmap(icon_size, icon_size)
        new_font = QFont()
        new_font.setPointSize(12)
        new_pixmap.fill(color=Qt.GlobalColor.white)
        new_painter = QPainter()
        new_painter.begin(new_pixmap)
        # Вывод анимации в иконке
        clock_points = [[-4, 8],
                        [4, 8],
                        [-4, -8],
                        [4, -8],
                        [-4, 8]]
        new_points = self.rotate_clock(clock_points)
        for i in range(len(clock_points)-1):
            new_painter.drawLine(half_icon_size - new_points[i][0], half_icon_size - new_points[i][1],
                                 half_icon_size - new_points[i+1][0], half_icon_size - new_points[i+1][1])

        # Вывод количества новых объявлений
        if count:
            text = str(count)
            new_painter.setPen(Qt.red)
        else:
            text = ""
            new_painter.setPen(Qt.black)
        new_painter.setFont(new_font)
        new_painter.drawText(0, 0, icon_size, icon_size, Qt.AlignHCenter | Qt.AlignVCenter, text)
        new_painter.end()
        new_icon.addPixmap(new_pixmap)
        return new_icon

    def resizeEvent(self, event) -> None:
        """Обработка изменения размеров окна"""
        self.resize_table()




