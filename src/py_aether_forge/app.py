"""Main PySide6 application window and screen stack."""

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QKeyEvent, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QStackedWidget,
)

from py_aether_forge.config import WINDOW_CONFIG
from py_aether_forge.meta.save_system import SaveSystem
from py_aether_forge.ui.battle_view import BattleViewWidget
from py_aether_forge.ui.main_menu import MainMenuWidget
from py_aether_forge.ui.sanctuary_ui import SanctuaryWidget


class AetherForgeWindow(QMainWindow):
    """Primary application window with fullscreen support and screen switching."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(WINDOW_CONFIG.title)
        self.resize(WINDOW_CONFIG.default_width, WINDOW_CONFIG.default_height)
        self.setMinimumSize(WINDOW_CONFIG.min_width, WINDOW_CONFIG.min_height)

        self.save_system = SaveSystem()

        # Screens stack
        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)

        self.main_menu = MainMenuWidget()
        self.sanctuary = SanctuaryWidget(self.save_system)
        self.battle_view = BattleViewWidget(self.save_system)

        self.stack.addWidget(self.main_menu)  # Index 0
        self.stack.addWidget(self.sanctuary)  # Index 1
        self.stack.addWidget(self.battle_view)  # Index 2

        self._connect_signals()
        self._apply_astral_palette()

    def _connect_signals(self) -> None:
        # Main Menu
        self.main_menu.start_game_requested.connect(self._start_battle)
        self.main_menu.sanctuary_requested.connect(self._open_sanctuary)
        self.main_menu.toggle_fullscreen_requested.connect(self.toggle_fullscreen)
        self.main_menu.exit_requested.connect(self.close)

        # Sanctuary
        self.sanctuary.back_requested.connect(self._open_main_menu)

        # Battle View
        self.battle_view.exit_to_menu_requested.connect(self._open_main_menu)

    def _apply_astral_palette(self) -> None:
        """Sets the application-wide dark astral color palette."""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(11, 14, 28))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(240, 245, 255))
        palette.setColor(QPalette.ColorRole.Base, QColor(19, 24, 46))
        palette.setColor(QPalette.ColorRole.Text, QColor(240, 245, 255))
        palette.setColor(QPalette.ColorRole.Button, QColor(38, 45, 74))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(240, 245, 255))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(79, 195, 247))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
        self.setPalette(palette)

    def toggle_fullscreen(self) -> None:
        """Switches between borderless fullscreen and windowed mode."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_F11:
            self.toggle_fullscreen()
            event.accept()
            return
        super().keyPressEvent(event)

    def _open_main_menu(self) -> None:
        self.stack.setCurrentWidget(self.main_menu)

    def _open_sanctuary(self) -> None:
        self.sanctuary.reload_data()
        self.stack.setCurrentWidget(self.sanctuary)

    def _start_battle(self) -> None:
        self.stack.setCurrentWidget(self.battle_view)
        self.battle_view.start_new_game()
        self.battle_view.setFocus()


def run_app() -> None:
    """Entry point creating and executing the PySide6 application."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    window = AetherForgeWindow()
    window.show()
    sys.exit(app.exec())
