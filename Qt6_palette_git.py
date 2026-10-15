from PyQt6.QtWidgets import QStyleFactory, QProxyStyle, QComboBox, QStyle, QApplication, QStyledItemDelegate, QTabBar, \
    QStyleOption, QMenu, QAbstractItemView
from PyQt6 import QtGui, QtWidgets
from PyQt6.QtCore import QSettings, Qt, QSize, QCoreApplication, QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QAction, QActionGroup, QPalette, QColor, QScreen
from typing import cast, Dict

SAFE_ROLES = {
    "Window",
    "WindowText",
    "Base",
    "AlternateBase",
    "ToolTipBase",
    "ToolTipText",
    "Text",
    "Button",
    "ButtonText",
    "BrightText",
    "Highlight",
    "HighlightedText",
    "Link",
    "LinkVisited",
    "Shadow",
    "PlaceholderText",
    "Accent",
    "Light",
    "Dark",
    "Mid",
    "Midlight"}

APP_STYLE = "Fusion"



class PaletteManagerSimple:
    # Новый класс, без промежуточного словаря
    def __init__(self, p_app, p_dict_colors, palette_them, inactive=True):
        self.app = p_app
        self.inactive = inactive
        self.themes = {}
        self.palette_them = palette_them
        self.color_themes = dict()
        self.set_dict(p_dict_colors)
        style = QApplication.style()
        if style:
            self.initial_style_name = style.objectName()
        else:
            self.initial_style_name = "default"  # или любая заглушка
        self.initial_palette = QPalette(QApplication.palette())
        self.update_theme(palette_them)

    def set_dict(self, p_dict_colors):
        color_themes_dict = dict()
        for theme, palette in p_dict_colors.items():
            colors_dict = dict()
            for role, color in palette.items():
                c_color = color
                if not self.inactive:
                    color_group = c_color.get("Active", None)
                    if color_group:
                        c_color['Inactive'] = color_group
                colors_dict[role] = c_color
            color_themes_dict[theme] = colors_dict
        for theme, palette in color_themes_dict.items():
            self.color_themes[theme] = self.create_palette(color_themes_dict, theme)

    def create_palette(self, color_themes_dict, theme: str = "1") -> QtGui.QPalette:
        self.app.setStyle(APP_STYLE)
        p_palette = QtGui.QPalette()
        colors = color_themes_dict[theme]
        for role_name, state_colors in colors.items():
            # Получаем enum роли
            if role_name in SAFE_ROLES:
                role = getattr(QtGui.QPalette.ColorRole, role_name)
                for state_name, color_value in state_colors.items():
                    # Получаем enum группы
                    group = getattr(QtGui.QPalette.ColorGroup, state_name)
                    p_palette.setColor(group, role, QtGui.QColor(color_value))
        return p_palette

    def reset_theme(self):
        QApplication.setPalette(self.initial_palette)
        QApplication.setStyle(QStyleFactory.create(self.initial_style_name))
        QtWidgets.QToolTip.setPalette(self.initial_palette)

    def update_theme(self, palette_them):  # !!!
        if palette_them == "Системная":
            self.reset_theme()
        else:
            self.apply_palette(palette_them)  # !!!

    def apply_palette(self, palette_them):
        self.app.setPalette(self.color_themes[palette_them])
        p_palette = self.get_palette(palette_them)
        QtWidgets.QToolTip.setPalette(p_palette)

    def get_palette(self, name: str) -> QtGui.QPalette:
        """Получить палитру по имени"""
        self.app.setStyle(APP_STYLE)
        # noinspection bad-return
        return self.color_themes.get(name)


class BasePaletteManager(QObject):
    # Новый класс, без промежуточного словаря аналог PaletteManagerSimple
    theme_not_found = pyqtSignal(str)

    def __init__(self, app, p_dict_colors: dict, default_palette: str, inactive=False):
        super().__init__()
        """
        :param app: ссылка на приложение 
        :param p_dict_colors: dict, словарь цветовых палитр Тема: {Роль: {Группа: Цвет, ...},
            роли SAFE_ROLES, группы: 'Active', 'Inactive', 'Disabled'
        :param default_palette: str, начальная тема палитры
        :param inactive: bool: если False, то группы 'Active' и 'Inactive' совпадают, 'Inactive' берется из 'Active'
            если True, то группы 'Active' и 'Inactive' разные
        """
        self.app = app
        self.current_palette_dict = dict()
        self.inactive = inactive
        self.dict_colors = p_dict_colors
        style = QApplication.style()
        if style:
            self.initial_style_name = style.objectName()
        else:
            self.initial_style_name = "default"  # или любая заглушка

        self.initial_palette = QPalette(QApplication.palette())
        QTimer.singleShot(0, lambda: self.update_theme(default_palette))
        self.update_theme(default_palette)

    def initialize_palette(self, external_dict=None):
        if external_dict:
            # обновляем роли целиком
            for role, groups in external_dict.items():
                if role in self.current_palette_dict:
                    self.current_palette_dict[role].update(groups)
                else:
                    self.current_palette_dict[role] = groups
        self.apply_current_palette()

    def reset_theme(self):
        QApplication.setStyle(QStyleFactory.create(self.initial_style_name))
        QApplication.setPalette(self.initial_palette)
        QtWidgets.QToolTip.setPalette(self.initial_palette)
        self.app.setStyle(APP_STYLE)

    def update_theme(self, new_palette: str):
        if new_palette == "Системная":
            self.reset_theme()
        else:
            current_palette_dict = self.dict_colors.get(new_palette)
            if current_palette_dict:
                self.current_palette_dict = current_palette_dict
                self.apply_current_palette()
            else:
                # Сначала отправляем сигнал GUI-окну, передавая имя потерянной темы
                self.theme_not_found.emit(new_palette)
                # Затем сбрасываем тему на дефолтную
                self.reset_theme()

    def update_color(self, role: str, group: str, value: str):
        """
        role = "Window"
        group = "Active"
        """
        if role in self.current_palette_dict:
            self.current_palette_dict[role][group] = value
        else:
            self.current_palette_dict[role] = {group: value}
        self.apply_current_palette()

    def apply_current_palette(self):
        palette = QPalette()
        for role_name in SAFE_ROLES:
            role = QPalette.ColorRole[role_name]
            groups = cast(Dict[str, str], self.current_palette_dict.get(role_name))
            if not groups:
                continue
            # Active
            if "Active" in groups:
                c = QColor(groups["Active"])
                palette.setColor(QPalette.ColorGroup.Active, role, c)

            # Inactive
            if self.inactive:
                if "Inactive" in groups:
                    c = QColor(groups["Inactive"])
                    palette.setColor(QPalette.ColorGroup.Inactive, role, c)
            else:
                # Inactive = Active
                if "Active" in groups:
                    c = QColor(groups["Active"])
                    palette.setColor(QPalette.ColorGroup.Inactive, role, c)

            # Disabled
            if "Disabled" in groups:
                c = QColor(groups["Disabled"])
                palette.setColor(QPalette.ColorGroup.Disabled, role, c)

        self.app.setPalette(palette)
        QtWidgets.QToolTip.setPalette(palette)
        self.app.setStyle(APP_STYLE)


class BasePaletteManagerCombo(BasePaletteManager):
    # Основан на BasePaletteManager, предназначен для выбора палитры через ComboBox
    def __init__(self, p_app, p_dict_colors, combo, setting, setting_key, inactive=False):
        """
        :param p_app: как в базовом классе
        :param p_dict_colors: как в базовом классе
        :param combo: QComboBox, ссылка на Combobox, содержащий перечень тем цветовых палитр
        :param setting: QSettings, для настройки параметров в реестре
            пример self.settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)
        :param setting_key: str, секция реестра в виде 'Название секции'/'Название параметра'
            пример self.values_section + "/Palette"
        :param inactive: как в базовом классе
        """
        self.dict_colors = p_dict_colors  # !!! Уточнить
        self.palette_combo = combo
        self.palette_combo_themes()
        self.setting = setting
        self.setting_key = setting_key
        # settings_value = self._load_theme_from_settings()
        settings_value = self.setting.value(self.setting_key, "Системная", type=str)
        self.old_setting_value = settings_value
        self.palette_combo.setCurrentText(settings_value)
        self.palette_combo.currentTextChanged.connect(self.set_palette)
        super().__init__(p_app, p_dict_colors, settings_value, inactive=inactive)

    def palette_combo_themes(self):
        for key in self.dict_colors:
            self.palette_combo.addItem(key)
        self.palette_combo.addItem("Системная")

    def set_palette(self):
        theme = self.palette_combo.currentText()
        self.update_theme(theme)

    def save_setting(self):
        setting_value = self.palette_combo.currentText()
        if self.old_setting_value != setting_value:
            self.old_setting_value = setting_value
            self.setting.setValue(self.setting_key, setting_value)


class BasePaletteManagerComboMultilingual(BasePaletteManagerCombo):
    def __init__(self, p_app, p_dict_colors, combo, setting, setting_key, inactive=False):
        super().__init__(p_app, p_dict_colors, combo, setting, setting_key, inactive=inactive)
        self.old_setting_value = None

    def palette_combo_themes(self):
        for role_name in self.dict_colors:
            translated_text = self.palette_combo.tr(role_name)
            self.palette_combo.addItem(translated_text, role_name)
        self.palette_combo.addItem("Системная", "Системная")

    def set_palette(self):
        theme = self.palette_combo.currentData()
        self.update_theme(theme)

    def save_setting(self):
        setting_value = self.palette_combo.currentData()
        if self.old_setting_value != setting_value:
            self.old_setting_value = setting_value
            self.setting.setValue(self.setting_key, setting_value)

    def retranslate(self):
        context = "MainWindow"  # !!! Уточнить
        # translated_text = self.tr(original_text)
        # или
        # translated_text = QCoreApplication.translate(context, original_text)
        # QCoreApplication.translate("MainWindow", ...) найдет
        # перевод в .qm файле независимо от того, из какого класса или файла вызван этот код.

        # Проходим циклом по всем элементам комбобокса
        for index in range(self.palette_combo.count()):
            original_text = self.palette_combo.itemData(index)
            # Переводим ОРИГИНАЛЬНЫЙ текст
            translated_text = QCoreApplication.translate(context, original_text)
            # Обновляем только видимый текст
            self.palette_combo.setItemText(index, translated_text)


class BasePaletteManagerMenu(BasePaletteManager):
    def __init__(self, p_app, p_dict_colors: dict, palette_menu, setting, setting_key, inactive=False):
        """
        :param p_app: как в базовом классе
        :param p_dict_colors: как в базовом классе
        :param palette_menu: QMenu, меню для управления палитрой
        :param setting: QSettings, для настройки параметров в реестре
            пример self.settings = QSettings(ORGANIZATION_NAME, APPLICATION_NAME)
        :param setting_key: str, секция реестра в виде 'Название секции'/'Название параметра'
            пример self.values_section + "/Palette"
        :param inactive: как в базовом классе
        """
        self.palette_group = None
        self.save_color_action = None
        self.dict_colors = p_dict_colors
        self.setting = setting
        self.setting_key = setting_key
        self.palette_menu = palette_menu
        self._create_palette_menu()
        settings_value = self._load_theme_from_settings()
        self.old_setting_value = settings_value
        super().__init__(p_app, p_dict_colors, settings_value, inactive=inactive)

    def _create_palette_menu(self):
        # Создаем меню для работы с палитрой цветов
        # noinspection unresolved-references
        self.save_color_action = self._create_palette_action("Сохранить палитру")
        # noinspection unresolved-references
        self.save_color_action.triggered.connect(self.save_theme_to_settings)
        # Визуальный разделитель под кнопкой сохранения
        self.palette_menu.addSeparator()
        # Создаем эксклюзивную группу для переключения радио-кнопок в меню
        self.palette_group = QActionGroup(self.palette_menu)
        self.palette_group.setExclusive(True)
        # Подключаем сигнал всей группы к обработчику (срабатывает при выборе любого action)
        self.palette_group.triggered.connect(self._set_palette_from_action)
        for name in self.dict_colors.keys():
            # Создаем action внутри нужного меню
            action = self._create_palette_action(name)
            action.setCheckable(True)
            self.palette_group.addAction(action)
        action = self._create_palette_action("Системная")
        action.setCheckable(True)
        self.palette_group.addAction(action)

    def _create_palette_action(self, name: str) -> QAction:
        # Переводим имя палитры (если "Системная" или ключи тоже требуют перевода)
        action = self.palette_menu.addAction(name)
        return action

    def _set_palette_from_action(self, action):
        # Изменяем палитру
        # Сигнал triggered от QActionGroup автоматически передает выбранный action в аргумент
        if action:
            palette_key = action.text()
            self.update_theme(palette_key)

    def save_theme_to_settings(self):
        # Сохраняем тему палитры в реестр.
        checked_action = self.palette_group.checkedAction()
        if checked_action:
            setting_value = checked_action.text()
            if self.old_setting_value != setting_value:
                self.old_setting_value = setting_value
                self.setting.setValue(self.setting_key, setting_value)

    def _load_theme_from_settings(self):
        # Получаем тему палитры из реестра или берем по умолчанию
        # Читаем настройку по ключу "Values/Palette". По умолчанию — "Системная"
        saved_theme = self.setting.value(self.setting_key, "Системная")
        # Ищем команду меню, ставим галочку и применяем тему
        for action in self.palette_group.actions():
            if action.text() == saved_theme:  # сравниваем с не переведенным текстом
                action.setChecked(True)
                break
        return saved_theme


class BasePaletteManagerMenuMultilingual(BasePaletteManagerMenu):  # Добавить в модуль!!!
    def __init__(self, p_app, p_dict_colors: dict, palette_menu, setting, setting_key, inactive=False):
        super().__init__(p_app, p_dict_colors, palette_menu, setting, setting_key, inactive=inactive)

    def _create_palette_action(self, name: str) -> QAction:
        # Переводим имя палитры (если "Системная" или ключи тоже требуют перевода)
        action = self.palette_menu.addAction(self.palette_menu.tr(name))
        action.setData(name)
        return action

    def _set_palette_from_action(self, action):
        # Изменяем палитру
        # Сигнал triggered от QActionGroup автоматически передает выбранный action в аргумент
        if action:
            palette_key = action.data()
            self.update_theme(palette_key)

    def save_theme_to_settings(self):
        # Сохраняем тему палитры в реестр.
        checked_action = self.palette_group.checkedAction()
        if checked_action:
            setting_value = checked_action.data()
            if self.old_setting_value != setting_value:
                self.old_setting_value = setting_value
                self.setting.setValue(self.setting_key, setting_value)

    def _load_theme_from_settings(self):
        # Получаем тему палитры из реестра или берем по умолчанию
        # Читаем настройку по ключу "Values/Palette". По умолчанию — "Системная"
        saved_theme = self.setting.value(self.setting_key, "Системная")
        # Ищем команду меню, ставим галочку и применяем тему
        for action in self.palette_group.actions():
            if action.data() == saved_theme:  # сравниваем с не переведенным текстом
                action.setChecked(True)
                break
        return saved_theme

    def retranslate_menu_actions(self):
        context = "MainWindow"  # !!! Уточнить
        # self.save_color_action.setText(self.tr("Сохранить палитру"))
        # или
        # self.save_color_action.setText(QCoreApplication.translate(context, "Сохранить палитру"))
        # QCoreApplication.translate("MainWindow", ...) найдет
        # перевод в .qm файле независимо от того, из какого класса или файла вызван этот код.
        if hasattr(self, 'save_color_action'):
            # Явно указываем контекст для кнопки сохранения
            self.save_color_action.setText(QCoreApplication.translate(context, "Сохранить палитру"))

        for action in self.palette_group.actions():
            raw_theme_name = action.data()
            if raw_theme_name:
                # !!! Явно берем перевод из контекста "MainWindow"
                new_translated_text = QCoreApplication.translate(context, raw_theme_name)
                action.setText(new_translated_text)


# ============================================================
# Классы связанные с PopupComboBox
# ============================================================

class ComboBoxFixStyle(QProxyStyle):
    # Используется в PopupComboBox
    def __init__(self, base_style=None):
        super().__init__(base_style)

    def styleHint(self, hint, option=None, widget=None, return_data=None):
        # Отключаем полноэкранный попап
        if hint == QStyle.StyleHint.SH_ComboBox_Popup:
            return 0
        return super().styleHint(hint, option, widget, return_data)


class ComboBoxColorDelegate(QStyledItemDelegate):
    # Используется в PopupComboBox
    def __init__(self, parent=None):
        super().__init__(parent)

    def paint(self, painter, option, index):
        # PyCharm-friendly типизация
        from PyQt6.QtGui import QPainter
        painter: QPainter

        from PyQt6.QtWidgets import QWidget
        widget: QWidget = option.widget

        top_window = widget.window()
        assert top_window is not None

        window_color = top_window.palette().color(QPalette.ColorRole.Window)

        if not (option.state & QStyle.StateFlag.State_Selected):
            painter.fillRect(option.rect, window_color)

        super().paint(painter, option, index)


class PopupComboBox(QComboBox):
    # Умный ComboBox с автоматическим ограничением высоты выпадающего списка.
    # Более красивый вариант

    def __init__(self, parent=None):
        super().__init__(parent)
        # self._initialized = False

        self.setStyle(ComboBoxFixStyle(self.style()))
        self.setItemDelegate(ComboBoxColorDelegate(self))


# ============================================================


# ============================================================
# Классы связанные с FixedPopupComboBox
# ============================================================

class CompactPaddingDelegate(QStyledItemDelegate):
    # Используется в FixedPopupComboBox
    def __init__(self, parent=None, padding_px=0):
        super().__init__(parent)
        self.padding_px = padding_px

    def sizeHint(self, option, index):
        s = super().sizeHint(option, index)
        # уменьшаем расстояние между строками, но НЕ трогаем высоту текста
        return QSize(s.width(), s.height() - self.padding_px)


class FixedPopupComboBox(QComboBox):
    # Умный ComboBox с автоматическим ограничением высоты выпадающего списка.
    # Более простой вариант
    def __init__(self, parent=None, padding_px=0):
        super().__init__(parent)
        self.padding_px = padding_px
        self.setItemDelegate(CompactPaddingDelegate(self, padding_px))

    def set_row_padding(self, padding_px):
        self.padding_px = padding_px
        self.setItemDelegate(CompactPaddingDelegate(self, padding_px))

    def showPopup(self):
        original_max = self.maxVisibleItems()
        rows = min(original_max, self.count())
        self.setMaxVisibleItems(rows)

        super().showPopup()

        # view всегда существует после showPopup()
        view = self.view()
        assert view is not None
        view: QAbstractItemView

        popup = view.window()
        assert popup is not None

        row_h = view.sizeHintForRow(0)
        desired_h = row_h * rows

        view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # QScreen → берем availableGeometry() как QRect
        screen = QApplication.primaryScreen()
        assert screen is not None
        screen: QScreen

        available = screen.availableGeometry()  # QRect

        # теперь используем available (QRect), а НЕ screen
        screen_max_h = int(available.height() * 0.9)
        real_h = min(desired_h, screen_max_h)

        popup.setMinimumHeight(0)
        popup.setMaximumHeight(real_h)
        view.setFixedHeight(real_h)

        combo_bottom = self.mapToGlobal(self.rect().bottomLeft())
        combo_top = self.mapToGlobal(self.rect().topLeft())

        # используем available.top/bottom — это корректно
        space_down = available.bottom() - combo_bottom.y()
        space_up = combo_top.y() - available.top()

        if space_down >= real_h:
            popup.move(combo_bottom.x(), combo_bottom.y())
        elif space_up >= real_h:
            popup.move(combo_top.x(), combo_top.y() - real_h)
        else:
            final_h = max(100, space_up)
            popup.setMaximumHeight(final_h)
            popup.move(combo_top.x(), combo_top.y() - final_h)

        self.setMaxVisibleItems(original_max)


