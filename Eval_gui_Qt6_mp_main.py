#
# Использует ComboBoxColorDelegate, ComboBoxFixStyle через PopupComboBox
# Применение
# В дизайнере QComboBox меняем на PopupComboBox
# Есть прокрутка
from pathlib import Path
import ast
import re
from mpmath import mp
import sys
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QTextCursor
from PyQt6.QtCore import QTranslator, QLibraryInfo, QSettings, Qt
from functools import wraps
from PyQt6 import QtWidgets  # Для обработчика Qt сообщений
from register_resources_fun import register_resources
from Eval_gui_Qt6_mp import Ui_MainWindow
from Qt6_palette import BasePaletteManagerCombo, APP_STYLE
from Qt6_palette_colors import dict_colors

mp.dps = 0
ORGANIZATION_NAME = "isva_company"
APPLICATION_NAME = "Eval_gui_mp"
f_degrees = False  # признак расчета тригонометрических функции в градусах
f_factorial = True  # признак расчета факториала для не целых чисел


def decorator_direct_tg_function(func):
    # Декоратор для выполнения прямой тригонометрической функции
    @wraps(func)
    def wrapper(x):
        if f_degrees:
            # Преобразуем x (который уже является объектом mpf) в радианы
            res = func(mp.radians(x))
        else:
            res = func(x)
        return res

    return wrapper


def decorator_inverse_tg_function(func):
    # Декоратор для выполнения обратной тригонометрической функции
    @wraps(func)
    def wrapper(*args):
        if f_degrees:
            # Преобразуем результат в градусы
            res = mp.degrees(func(*args))
        else:
            res = func(*args)
        return res

    return wrapper


@decorator_direct_tg_function
def custom_ctg(x):
    # Функция для расчета котангенса
    return 1.0 / mp.tan(x)


@decorator_inverse_tg_function
def custom_arcctg(x):
    # Функция для расчета арктангенса
    return mp.pi / 2.0 - mp.atan(x)


def custom_log2(x):
    # Функция для расчета логарифма по основанию 2
    return mp.log(x) / mp.log(2)


def custom_cth(x):
    # Функция для расчета гиперболического котангенса
    return 1 / mp.tanh(x)


def custom_arcth(x):
    # Функция для расчета гиперболического арккотангенса
    return mp.ln((x + 1) / (x - 1)) / 2


def custom_factorial(x):
    # Функция для расчета факториала в зависимости от признака расчета для не целых чисел
    if f_factorial:
        # Разрешен расчет факториала для не целых чисел.
        return mp.factorial(x)
    else:
        # Запрещен расчет факториала для не целых чисел.
        # Превращаем в строку для безопасной проверки на комплексность
        x_str = str(x)

        # 1. Проверяем на комплексность (если в строке числа есть 'j' или 'i')
        if 'j' in x_str or 'i' in x_str:
            raise ValueError("Факториал комплексного числа запрещен")

        # 2. Проверяем на дробность через остаток от деления на 1
        # Если x % 1 не равен 0 (например, 5.3 % 1 = 0.3), значит число дробное
        if x % 1 != 0:
            raise ValueError("Факториал дробного числа запрещен")

        # 3. Проверяем на отрицательность
        if x < 0:
            raise ValueError("Факториал отрицательного числа не существует")

        # Если все проверки успешно пройдены
        return mp.factorial(x)


# --- Модификация окружения для eval ---

# Берем стандартное окружение mpmath
mpmath_env = {name: getattr(mp, name) for name in dir(mp) if not name.startswith('_')}
mpmath_env['mpf'] = mp.mpf

# Перезаписываем в этом окружении стандартные тригонометрические функции на наши задекорированные
mpmath_env['sin'] = decorator_direct_tg_function(mp.sin)
mpmath_env['cos'] = decorator_direct_tg_function(mp.cos)
mpmath_env['tg'] = decorator_direct_tg_function(mp.tan)
mpmath_env['arcsin'] = decorator_inverse_tg_function(mp.asin)
mpmath_env['arccos'] = decorator_inverse_tg_function(mp.acos)
mpmath_env['arctg'] = decorator_inverse_tg_function(mp.atan)
mpmath_env['atan2'] = decorator_inverse_tg_function(mp.atan2)
# Перезаписываем в этом окружении стандартные тригонометрические функции на наши
mpmath_env['ctg'] = custom_ctg
mpmath_env['arcctg'] = custom_arcctg
# Перезаписываем в этом окружении константы
mpmath_env['pi'] = mp.pi
mpmath_env['e'] = mp.e
# Перезаписываем в этом окружении стандартные гиперболические функции на наши
mpmath_env['sh'] = mp.sinh
mpmath_env['ch'] = mp.cosh
mpmath_env['th'] = mp.tanh
mpmath_env['cth'] = custom_cth
mpmath_env['arsh'] = mp.asinh
mpmath_env['arch'] = mp.acosh
mpmath_env['arth'] = mp.atanh
mpmath_env['arcth'] = custom_arcth
# Перезаписываем в этом окружении прочие стандартные функции на наши
mpmath_env['abs'] = mp.fabs
mpmath_env['log2'] = custom_log2
mpmath_env['factorial'] = custom_factorial


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.lst_functions = []
        self.add_functions()
        self.settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)
        self.window_section = "Window"  # Секция параметров окна
        self.values_section = "Values"  # Секция параметров переменных
        self.precision_spinbox.setValue(self.settings.value(self.values_section + "/Precision", 16, type=int))
        self.select_checkbox.setChecked(self.settings.value(self.values_section + "/Select", True, type=bool))
        self.radian_radio.setChecked(self.settings.value(self.values_section + "/Rad_Deg", True, type=bool))
        self.degree_radio.setChecked(not self.radian_radio.isChecked())
        self.complex_checkbox.setChecked(self.settings.value(self.values_section + "/Complex", True, type=bool))
        self.factorial_checkbox.setChecked(self.settings.value(self.values_section + "/Factorial", True, type=bool))
        self.calc_text.installEventFilter(self)
        self.save_geometry = self.settings.value(self.window_section + "/geometry")
        self.save_windowState = self.settings.value(self.window_section + "/windowState")
        # Проверяем, что данные не None и восстанавливаем
        if self.save_geometry is not None:
            self.restoreGeometry(self.save_geometry)
        if self.save_windowState is not None:
            self.restoreState(self.save_windowState)
        # Параметры для manager
        # app: ссылка на приложение,
        # dict_themes: словарь цветовых палитр,
        # default_palette: начальная тема палитры
        # combo: ссылка на Combobox, содержащий перечень тем цветовых палитр,
        # setting: QSettings, для настройки параметров в реестре
        # setting_key: str, секция реестра в виде 'Название секции'/'Название параметра'
        # inactive: по умолчанию False, 'Inactive' берется из 'Active'
        self.manager = BasePaletteManagerCombo(app, dict_colors, self.palette_combo, self.settings,
                                               self.values_section + "/Palette")
        self.precision_spinbox.valueChanged.connect(self.calculate)
        self.complex_checkbox.clicked.connect(self.calculate)
        self.factorial_checkbox.clicked.connect(self.calculate)
        self.exit_button.clicked.connect(self.close)
        self.clear_button.clicked.connect(self.calc_text.clear)
        self.save_button.clicked.connect(self.save_ini)
        self.calculate_button.clicked.connect(self.calculate)
        self.calc_text.setFocus()

    # noinspection pep8-naming
    def eventFilter(self, obj, event):
        if obj is self.calc_text and event.type() == event.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                # Прямое сравнение отлично работает в PyQt6 и не вызывает ошибок типов
                if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                    return super().eventFilter(obj, event)
                self.calculate()
                return True
        return super().eventFilter(obj, event)

    def add_functions(self):
        # Назначаем слоты для обработки нажатия на кнопки с названиями начинающимся с 'function_button_' или
        # с 'const_button_'. Эти кнопки служат для ввода цифр, знаков, операций, констант и функций.
        button: QPushButton
        self.lst_functions = []
        for button in self.findChildren(QPushButton):  # просматриваем все кнопки
            if button.objectName().startswith(
                    "function_button_"):  # если имя кнопки начинается с function_button_ (это кнопки функций),
                button.clicked.connect(self.add_function)  # то подключаем обработчик при нажатии (add_txt)
                txt = button.text()  # type: ignore # получаем текст кнопки
                txt_f = txt.split("(")[0]  # получаем название функции
                if txt_f:
                    self.lst_functions.append(txt_f)  # добавляем название функции в список разрешенных
        for button in self.findChildren(QPushButton):  # просматриваем все кнопки
            if button.objectName().startswith(
                    "const_button_"):  # если имя кнопки начинается с const_button (это кнопки констант),
                button.clicked.connect(self.add_constant)  # то подключаем обработчик при нажатии (add_txtc)

    def closeEvent(self, event):
        # Ваше действие при закрытии окна
        # Если размер окна изменился, то сохраняем.
        if self.save_geometry != self.saveGeometry():
            self.settings.setValue(self.window_section + "/geometry",
                                   self.saveGeometry())  # Сохранение размера окна
        # Если состояние окна изменилось, то сохраняем
        if self.save_windowState != self.saveState():
            self.settings.setValue(self.window_section + "/windowState",
                                   self.saveState())  # Сохранение состояния окна
        event.accept()  # Закрываем окно

    def save_ini(self):
        # сохранение настроек
        self.settings.setValue(self.values_section + "/Precision", self.precision_spinbox.value())
        self.settings.setValue(self.values_section + "/Select", str(self.select_checkbox.isChecked()))
        self.settings.setValue(self.values_section + "/Rad_Deg", str(self.radian_radio.isChecked()))
        self.settings.setValue(self.values_section + "/Palette", self.palette_combo.currentText())
        self.manager.save_setting()
        self.settings.setValue(self.values_section + "/Factorial", str(self.factorial_checkbox.isChecked()))

    def add_function(self):  # обработчик при нажатии кнопки функции
        txt = self.sender().text()  # type: ignore # получаем текст кнопки
        txt_f = txt.split("(")[0] + (
            "()")  # из текста выделяем название функции, т.е. текст до открывающей скобки, к этому названию
        # добавляем скобки
        selected_text = self.calc_text.textCursor().selectedText()  # и полученный текст добавляем в позицию курсора
        # Если есть выделенный текст, заменяем его новым текстом
        if selected_text:
            self.calc_text.insertPlainText(txt_f)
            # Удаляем выделенный текст
            self.calc_text.textCursor().removeSelectedText()
        else:
            self.calc_text.insertPlainText(txt_f)  # и полученный текст добавляем в позицию курсора
        cursor = self.calc_text.textCursor()
        # Перемещаем курсор на одну позицию влево
        cursor.movePosition(QTextCursor.MoveOperation.Left)
        # Устанавливаем обновленный курсор в QPlainTextEdit
        self.calc_text.setTextCursor(cursor)
        self.calc_text.setFocus()

    def add_constant(self):  # обработчик при нажатии кнопки констант
        txt = self.sender().text()  # type: ignore # получаем текст кнопки
        txt_f = txt.split(" ")[0]  # из текста выделяем название константы, т.е. текст до пробела,
        selected_text = self.calc_text.textCursor().selectedText()
        if selected_text:
            self.calc_text.insertPlainText(txt_f)
            # Удаляем выделенный текст
            self.calc_text.textCursor().removeSelectedText()
        else:
            self.calc_text.insertPlainText(txt_f)
        self.calc_text.setFocus()

    def validate_expression_functions(self, expression: str):
        # Проверяет функции по динамическому белому списку класса
        try:
            node = ast.parse(expression, mode='eval')
            for subnode in ast.walk(node):
                if isinstance(subnode, ast.Call):
                    if isinstance(subnode.func, ast.Name):
                        func_name = subnode.func.id
                        # Проверяем по списку, собранному из кнопок
                        if func_name not in self.lst_functions:
                            raise ValueError(f"Функция '{func_name}' запрещена")
        except SyntaxError:
            pass

    def calculate_f(self, expression: str) -> str:
        # 1. Валидация по динамическому списку кнопок
        global f_degrees, f_factorial
        f_degrees = self.degree_radio.isChecked()  # Признак расчета в градусах
        f_factorial = self.factorial_checkbox.isChecked()
        if not self.complex_checkbox.isChecked() and 'j' in expression:
            raise ValueError("Комплексные числа отключены")
        self.validate_expression_functions(expression)
        # 2. Настройка точности и вычисление
        precision = self.precision_spinbox.value()
        mp.dps = precision
        pattern = r'(?<![a-zA-Z0-9_])(\d+\.\d+|\d+)(?![a-zA-Z0-9_])'
        processed_expr = re.sub(pattern, r"mpf('\1')", expression)

        # Вычисление в изолированном контексте
        result = eval(processed_expr, {"__builtins__": None}, mpmath_env)

        # Очистка микропогрешностей
        # 1. Порог для очистки хвостов (mp.chop)
        # Берём 80% от текущей точности.
        # При precision=10 порог будет 1e-8. При precision=50 порог будет 1e-40.
        chop_digits = int(precision * 0.8)
        chopped_result = mp.chop(result, tol=10 ** -chop_digits)

        # --- ДОБАВЛЕННЫЙ БЛОК: Проверка на экстремально большие числа (Тангенс 90) ---
        # Если число превышает порог точности (например, для 50 знаков это > 10^45),
        # мы принудительно приравниваем его к математической бесконечности.
        # 2. Проверка на бесконечность (для тангенса 90 градусов)
        # Если число превышает порядок 80% от выбранной точности, считаем его бесконечностью.
        # При precision=10 это > 10^8. При precision=50 это > 10^40.
        if abs(chopped_result) > 10 ** chop_digits:
            chopped_result = mp.inf if chopped_result > 0 else -mp.inf
        # ----------------------------------------------------------------------------

        # Форматирование результата
        result_str = mp.nstr(chopped_result, precision, strip_zeros=True)

        # Если это бесконечность, nstr вернет '+inf' или '-inf'
        # Сделаем вывод более дружелюбным для пользователя калькулятора
        if result_str == '+inf' or result_str == '-inf':
            return "Значение не существует (∞)"
        # 1. Если число комплексное (содержит 'j')
        # --- НОВЫЙ БЛОК КОМПЛЕКСНОГО ФОРМАТИРОВАНИЯ ---
        # Проверяем, есть ли у числа мнимая часть (комплексное ли оно)
        # Мы используем mp.im(x), чтобы получить мнимую часть в mpmath
        # --- НОВЫЙ БЛОК КОМПЛЕКСНОГО ФОРМАТИРОВАНИЯ ---
        # Проверяем, есть ли у числа мнимая часть (комплексное ли оно)
        # Мы используем mp.im(x), чтобы получить мнимую часть в mpmath
        # --- БЕЗОПАСНОЕ КОМПЛEСКНОЕ ФОРМАТИРОВАНИЯ БЕЗ REGEX ---
        # Проверяем наличие мнимой части через mp.im
        if mp.im(chopped_result) != 0:
            if self.complex_checkbox.isChecked():
                real_part = mp.re(chopped_result)
                imag_part = mp.im(chopped_result)

                # Форматируем каждую часть как отдельное независимое число
                real_str = mp.nstr(real_part, precision, strip_zeros=True)
                imag_str = mp.nstr(imag_part, precision, strip_zeros=True)

                # Срезаем ".0" у вещественной части, только если это чистый ноль или целое число (например, "1.0" -> "1")
                if '.' in real_str and 'e' not in real_str:
                    real_str = real_str.rstrip('0').rstrip('.')

                # Срезаем ".0" у мнимой части (например, "2.0" -> "2", но "2.1" и "2.11" останутся нетронутыми!)
                if '.' in imag_str and 'e' not in imag_str:
                    imag_str = imag_str.rstrip('0').rstrip('.')

                # Собираем итоговую строку
                if imag_part > 0:
                    if real_str == "0":
                        result_str = f"{imag_str}i"
                    else:
                        result_str = f"{real_str} + {imag_str}i"
                else:
                    # Если мнимая часть отрицательная, убираем дублирующий минус для красоты
                    imag_str_positive = imag_str.lstrip('-')
                    if real_str == "0":
                        result_str = f"-{imag_str_positive}i"
                    else:
                        result_str = f"{real_str} - {imag_str_positive}i"

                # Убираем лишнюю единицу перед мнимой единицей (например, "1i" -> "i", "2 + 1i" -> "2 + i")
                # Используем простые строковые замены вместо регулярных выражений
                if result_str == "1i":
                    result_str = "i"
                elif result_str == "-1i":
                    result_str = "-i"
                else:
                    result_str = result_str.replace(" + 1i", " + i").replace(" - 1i", " - i")
                return result_str
            else:
                raise ValueError(f"Работа с комплексными числами запрещена!")
        # 2. Если число СТРОГО ВЕЩЕСТВЕННОЕ
        result_str = mp.nstr(chopped_result, precision, strip_zeros=True)
        if '.' in result_str and 'e' not in result_str:
            result_str = result_str.rstrip('0').rstrip('.')
        return result_str

    def calculate(self):
        expression = self.calc_text.toPlainText().strip().lower()
        if expression:

            # 1. Приводим к нижнему регистру и убираем пробелы
            expression = expression.lower()
            expression = re.sub(r'\s', '', expression)

            # 2. Умные исправления для мнимой единицы
            expression = re.sub(r'\)([ij])', r')*\1', expression)
            expression = re.sub(r'(\d)([ij])', r'\1*\2', expression)
            expression = re.sub(r'\bi\b', 'j', expression)
            expression = expression.replace("^", "**")

            # --- НОВЫЙ НАДЕЖНЫЙ АЛГОРИТМ ДЛЯ ФАКТОРИАЛА (!) ---
            # Повторяем цикл, пока в строке есть восклицательные знаки
            while '!' in expression:
                idx = expression.find('!')

                # Если перед '!' стоит закрывающая скобка, ищем её пару (в начале выражения)
                if idx > 0 and expression[idx - 1] == ')':
                    balance = 0
                    start_idx = -1
                    # Идем в обратную сторону от скобки, чтобы найти парную открывающуюся
                    for i in range(idx - 1, -1, -1):
                        if expression[i] == ')':
                            balance += 1
                        elif expression[i] == '(':
                            balance -= 1

                        if balance == 0:
                            # Мы нашли начало блока в скобках.
                            # Но нужно проверить, не является ли это вызовом функции, например sin(...)! или sqrt(...)!
                            # Отматываем назад, если перед скобкой идут буквы названия функции
                            func_start = i
                            while func_start > 0 and expression[func_start - 1].isalnum():
                                func_start -= 1
                            start_idx = func_start
                            break

                    if start_idx != -1:
                        # Вырезаем всё выражение (вместе с функцией, если она была) и оборачиваем в factorial()
                        target = expression[start_idx:idx]
                        expression = expression[:start_idx] + f"factorial({target})" + expression[idx + 1:]
                    else:
                        break  # Защита от бесконечного цикла, если скобки расставлены неверно
                else:
                    # Если перед '!' стоит не скобка, а обычное число или буква (например, 5! или j!)
                    # Находим границы этого аргумента (все буквы и цифры перед знаком)
                    start_idx = idx - 1
                    while start_idx > 0 and (expression[start_idx - 1].isalnum() or expression[start_idx - 1] == '.'):
                        start_idx -= 1

                    target = expression[start_idx:idx]
                    expression = expression[:start_idx] + f"factorial({target})" + expression[idx + 1:]
            # --------------------------------------------------

            try:
                res_str = self.calculate_f(expression)
                self.result_label_value.setText(res_str)
            except (Exception,):
                self.result_label_value.setText("Ошибка в выражении и/или аргументах")

            if self.select_checkbox.isChecked():
                self.calc_text.selectAll()
            self.calc_text.setFocus()
        else:
            self.result_label_value.setText("....")
        self.calc_text.setFocus()


if __name__ == '__main__':
    register_resources("Eval_gui_Qt6_mp.rcc", Path(__file__).parent)
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle(APP_STYLE)
    qt_translator = QTranslator()
    qt_translator.load(
        "qtbase_ru",
        QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    )
    app.installTranslator(qt_translator)
    Window = MainWindow()
    Window.show()
    sys.exit(app.exec())
