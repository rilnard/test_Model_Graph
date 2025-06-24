from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QTableView, QPushButton, QHBoxLayout,
    QFileDialog, QComboBox, QInputDialog, QLabel, QStyledItemDelegate
)
from PyQt5.QtCore import Qt
import numpy as np
import h5py
import pyqtgraph as pg
from model import NumpyTableModel

# Делегат для первого столбца, чтобы там были только значения от 1 до 5 (выпадающий список).
# Без него не отображались значения, но графики строились и все считалось.
# Подсказал Copilot, воспользовался читерством, чтобы он проверил код.
# Изменений не много, но про delegate он подсказал.
# Раньше я его отдельным файлом делал и импортировал во view, но потом определил прямо во view.
class ComboBoxDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems([str(i) for i in range(1, 6)])
        return editor
    def setEditorData(self, editor, index):
        value = str(index.model().data(index, Qt.EditRole))
        idx = editor.findText(value)
        if idx >= 0:
            editor.setCurrentIndex(idx)
    def setModelData(self, editor, model, index):
        value = editor.currentText()
        model.setData(index, value, Qt.EditRole)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Numpy Table + Graph")
        self.resize(800, 600)
        self.model = NumpyTableModel()  # Модель данных
        self.init_ui()

    def init_ui(self):
        widget = QWidget()
        layout = QVBoxLayout()

        # Таблица с данными
        self.table = QTableView()
        self.table.setModel(self.model)
        self.table.setItemDelegateForColumn(0, ComboBoxDelegate(self.table))  # Только первый столбец — выпадающий список
        layout.addWidget(self.table)

        # Кнопки для сохранения/загрузки, изменения размера и случайного заполнения
        btn_layout = QHBoxLayout()
        btn_save_txt = QPushButton("Сохранить в txt")
        btn_save_txt.clicked.connect(self.save_txt)
        btn_load_txt = QPushButton("Загрузить из txt")
        btn_load_txt.clicked.connect(self.load_txt)
        btn_save_hdf = QPushButton("Сохранить в hdf5")
        btn_save_hdf.clicked.connect(self.save_hdf)
        btn_load_hdf = QPushButton("Загрузить из hdf5")
        btn_load_hdf.clicked.connect(self.load_hdf)
        btn_resize = QPushButton("Изменить размер")
        btn_resize.clicked.connect(self.change_size)
        btn_fill = QPushButton("Заполнить случайно")
        btn_fill.clicked.connect(self.fill_random)
        btn_layout.addWidget(btn_save_txt)
        btn_layout.addWidget(btn_load_txt)
        btn_layout.addWidget(btn_save_hdf)
        btn_layout.addWidget(btn_load_hdf)
        btn_layout.addWidget(btn_resize)
        btn_layout.addWidget(btn_fill)
        layout.addLayout(btn_layout)

        # Два выпадающих списка для выбора столбцов для графика
        col_graph_layout = QHBoxLayout()
        col_graph_layout.addWidget(QLabel("X:"))
        self.x_col_combo = QComboBox()
        col_graph_layout.addWidget(self.x_col_combo)
        col_graph_layout.addWidget(QLabel("Y:"))
        self.y_col_combo = QComboBox()
        col_graph_layout.addWidget(self.y_col_combo)
        layout.addLayout(col_graph_layout)

        # График
        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)

        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Заполняю выпадающие списки названиями столбцов (можно сделать универсально через self.model.headers)
        for h in self.model.headers:
            self.x_col_combo.addItem(h)
            self.y_col_combo.addItem(h)
        self.x_col_combo.setCurrentIndex(0)
        self.y_col_combo.setCurrentIndex(1)

        # Подключаю сигналы к обновлению графика
        self.x_col_combo.currentIndexChanged.connect(self.update_plot)
        self.y_col_combo.currentIndexChanged.connect(self.update_plot)
        self.model.dataChanged.connect(self.update_plot)
        self.model.layoutChanged.connect(self.update_plot)

        self.update_plot()

    def save_txt(self):
        # Сохраняю массив в текстовый файл через numpy.savetxt
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как txt", "", "Текстовые файлы (*.txt);;Все файлы (*)"
        )
        if path:
            np.savetxt(path, self.model.array, fmt="%.2f")

    def load_txt(self):
        # Загружаю массив из текстового файла и пересоздаю модель (оставляю только нужное количество строк)
        path, _ = QFileDialog.getOpenFileName(self, "Загрузить txt")
        if path:
            arr = np.loadtxt(path)
            if arr.ndim == 1:
                arr = arr.reshape(-1, 4)
            self.model = NumpyTableModel(arr)
            self.table.setModel(self.model)
            self.table.setItemDelegateForColumn(0, ComboBoxDelegate(self.table))
            self.x_col_combo.clear()
            self.y_col_combo.clear()
            for h in self.model.headers:
                self.x_col_combo.addItem(h)
                self.y_col_combo.addItem(h)
            self.x_col_combo.setCurrentIndex(0)
            self.y_col_combo.setCurrentIndex(1)
            self.x_col_combo.currentIndexChanged.connect(self.update_plot)
            self.y_col_combo.currentIndexChanged.connect(self.update_plot)
            self.model.dataChanged.connect(self.update_plot)
            self.model.layoutChanged.connect(self.update_plot)
            self.update_plot()

    def save_hdf(self):
        # Сохраняю массив в HDF5 через h5py (надо будет потом почитать про HDF5 и h5py)
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить как hdf5", "", "HDF5 файлы (*.hdf5);;Все файлы (*)"
        )
        if path:
            with h5py.File(path, "w") as f:
                f.create_dataset("data", data=self.model.array)

    def load_hdf(self):
        # Загружаю массив из HDF5, только нужное количество строк
        path, _ = QFileDialog.getOpenFileName(self, "Загрузить hdf5")
        if path:
            with h5py.File(path, "r") as f:
                arr = f["data"][:]
            self.model = NumpyTableModel(arr)
            self.table.setModel(self.model)
            self.table.setItemDelegateForColumn(0, ComboBoxDelegate(self.table))
            self.x_col_combo.clear()
            self.y_col_combo.clear()
            for h in self.model.headers:
                self.x_col_combo.addItem(h)
                self.y_col_combo.addItem(h)
            self.x_col_combo.setCurrentIndex(0)
            self.y_col_combo.setCurrentIndex(1)
            self.x_col_combo.currentIndexChanged.connect(self.update_plot)
            self.y_col_combo.currentIndexChanged.connect(self.update_plot)
            self.model.dataChanged.connect(self.update_plot)
            self.model.layoutChanged.connect(self.update_plot)
            self.update_plot()

    def change_size(self):
        # Диалог для изменения размера массива (от 1 до 20 строк)
        rows, ok = QInputDialog.getInt(self, "Изменить размер", "Количество строк (1-20):", value=self.model.rowCount(), min=1, max=20)
        if ok:
            self.model.resize(rows)
            self.update_plot()

    def fill_random(self):
        # Случайные значения в первом и втором столбце (категория 1-5, значение -100..100 с округлением)
        self.model.fill_random()
        self.update_plot()

    def update_plot(self):
        # Рисую график: по выбранным столбцам, соединяю точки линией (pen='b'), точки - кружочки (symbol='o')
        self.plot_widget.clear()
        x_col = self.x_col_combo.currentIndex()
        y_col = self.y_col_combo.currentIndex()
        x = self.model.array[:, x_col]
        y = self.model.array[:, y_col]
        self.plot_widget.plot(x, y, pen='b', symbol='o')

# TODO: Разобраться, как подписываться на сигналы (pyqtSignal) в других виджетах.
# TODO: Изучить pyqtgraph подробнее (можно настраивать оси, подписи, цвета и т.д.).
# TODO: Посмотреть, как можно сделать сортировку и фильтрацию в QTableView.
# TODO: Можно реализовать добавление/удаление строк, если захочу.