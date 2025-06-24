import numpy as np
from PyQt5.QtCore import QAbstractTableModel, Qt, pyqtSignal, QModelIndex, QVariant

# Модель для работы с numpy-таблицей. Наследуюсь от QAbstractTableModel.
class NumpyTableModel(QAbstractTableModel):
    # Сигналы для пересчета и обновления накопленного значения
    recalculated = pyqtSignal(int)
    cumulative_updated = pyqtSignal(int)

    def __init__(self, array: np.ndarray = None, parent=None):
        super().__init__(parent)
        # Хочу всегда 5 строк и 4 столбца (или заданное пользователем количество)
        nrows = 5
        if array is None:
            # Создаю массив: первым столбцом будут случайные целые 1-5 (это категория),
            # а во втором - нули (это значение, можно менять, в том числе отрицательные)
            array = np.zeros((nrows, 4))
            array[:, 0] = np.random.randint(1, 6, size=nrows)
            array[:, 1] = 0  # Все значения по умолчанию - нули
            # Надо будет потом почитать, как еще можно инициализировать массивы в numpy
        self.array = array
        # Заголовки для столбцов. Их можно потом выводить в QTableView
        self.headers = ["Категория", "Значение", "Пересчёт", "Накопленное"]
        # Сразу пересчитываю вычисляемые столбцы при создании
        self.update_calculated_columns()

    def rowCount(self, parent=QModelIndex()):
        # Возвращаю количество строк в таблице
        return self.array.shape[0]

    def columnCount(self, parent=QModelIndex()):
        # Возвращаю количество столбцов
        return self.array.shape[1]

    def data(self, index, role=Qt.DisplayRole):
        # Этот метод отвечает за отображение данных в таблице и за редактирование
        row, col = index.row(), index.column()
        value = self.array[row, col]
        if role == Qt.DisplayRole or role == Qt.EditRole:
            # Если первый столбец, показываю как целое, а остальные — как float (округляю до двух знаков)
            if col == 0:
                return str(int(value))
            return f"{float(value):.2f}"
        if col == 1 and role == Qt.BackgroundRole:
            # Хочу, чтобы положительные значения были зелёные, а отрицательные — красные
            # Надо будет прочитать подробнее про Qt.BackgroundRole
            from PyQt5.QtGui import QColor
            if value > 0:
                return QColor(0, 255, 0, 50)
            elif value < 0:
                return QColor(255, 0, 0, 50)
        return QVariant()

    def setData(self, index, value, role=Qt.EditRole):
        # Этот метод вызывается, когда пользователь редактирует ячейку
        row, col = index.row(), index.column()
        if col == 0:
            # В первом столбце только значения 1-5 (категория)
            try:
                val = int(value)
                if 1 <= val <= 5:
                    self.array[row, col] = val
                    self.update_calculated_columns()
                    self.dataChanged.emit(index, index)
                    return True
            except Exception:
                return False
        elif col == 1:
            # Во втором столбце можно любые числа, в том числе отрицательные и ноль (округление до 2 знаков)
            try:
                val = round(float(value), 2)
                self.array[row, col] = val
                self.update_calculated_columns()
                self.dataChanged.emit(index, index)
                return True
            except Exception:
                return False
        # Остальные столбцы не редактируются напрямую
        return False

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        # Показываю заголовки столбцов (и можно строки, если надо)
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return QVariant()

    def flags(self, index):
        # Говорю Qt, что редактировать можно только первые два столбца
        col = index.column()
        if col == 0 or col == 1:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def update_calculated_columns(self):
        # Здесь делаю пересчёт вычисляемых столбцов
        # Третий столбец — "пересчёт", просто удвоенное значение второго
        self.array[:, 2] = self.array[:, 1] * 2
        self.recalculated.emit(0)  # Сигнал, если кто-то подпишется
        # Четвёртый столбец — "накопленное": сумма по строке (категория + значение + пересчёт)
        self.array[:, 3] = self.array[:, 0] + self.array[:, 1] + self.array[:, 2]
        self.cumulative_updated.emit(0)  # Сигнал, если кто-то подпишется.
        # Обновляю отображение этих столбцов.
        self.dataChanged.emit(self.index(0, 2), self.index(self.rowCount()-1, 3))

    def fill_random(self):
        # Заполняю первый столбец случайными числами от 1 до 5,
        # второй столбец — случайные значения от -100 до +100 с двумя знаками после запятой
        self.array[:, 0] = np.random.randint(1, 6, size=self.array.shape[0])
        self.array[:, 1] = np.round(np.random.uniform(-100, 100, size=self.array.shape[0]), 2)
        self.update_calculated_columns()
        self.layoutChanged.emit()

    def resize(self, new_rows):
        # Можно менять размер массива (например, через диалог). Оставляю только первые new_rows строк,
        # либо добавляю новые строки, если нужно. Новые строки — категория случайная, значение 0.
        ncols = self.array.shape[1]
        if new_rows > self.array.shape[0]:
            extra = np.zeros((new_rows - self.array.shape[0], ncols))
            extra[:, 0] = np.random.randint(1, 6, size=extra.shape[0])
            extra[:, 1] = 0
            self.array = np.vstack([self.array, extra])
        else:
            self.array = self.array[:new_rows, :]
        self.update_calculated_columns()
        self.layoutChanged.emit()

# TODO: Изучить подробнее про сигналы и слоты в PyQt (pyqtSignal и connect).
# TODO: Почитать, как можно удобно делать сортировку и фильтрацию в QTableView.
# TODO: Разобраться, как реализовать добавление и удаление строк (если потребуется).