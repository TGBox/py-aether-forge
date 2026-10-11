"""Main menu screen with astral aesthetics and navigation buttons."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class MainMenuWidget(QWidget):
    """Start screen for Die Äther-Schmiede."""

    start_game_requested = Signal()
    sanctuary_requested = Signal()
    toggle_fullscreen_requested = Signal()
    exit_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(24)

        # Title Card
        title_frame = QFrame()
        title_layout = QVBoxLayout(title_frame)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel("DIE ÄTHER-SCHMIEDE")
        title_label.setStyleSheet(
            "font-size: 42px; font-weight: bold; color: #82DCFF; letter-spacing: 4px;"
        )
        title_layout.addWidget(title_label)

        subtitle_label = QLabel("Astrale Fantasy & Elementar-Verteidigung")
        subtitle_label.setStyleSheet("font-size: 18px; color: #91A0C3; font-style: italic;")
        title_layout.addWidget(subtitle_label)

        layout.addWidget(title_frame)

        # Buttons Card
        btn_frame = QFrame()
        btn_frame.setFixedWidth(340)
        btn_layout = QVBoxLayout(btn_frame)
        btn_layout.setSpacing(14)

        btn_style = """
            QPushButton {
                background-color: #262D4A;
                color: #F0F5FF;
                border: 2px solid #54669E;
                border-radius: 8px;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #343F66;
                border-color: #82DCFF;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background-color: #1A2035;
            }
        """

        self.btn_start = QPushButton("✦  Gefecht Starten  ✦")
        self.btn_start.setStyleSheet(
            btn_style.replace("#262D4A", "#1D4260").replace("#54669E", "#4FC3F7")
        )
        self.btn_start.clicked.connect(self.start_game_requested.emit)
        btn_layout.addWidget(self.btn_start)

        self.btn_sanctuary = QPushButton("⚙  Die Astrale Schmiede  ⚙")
        self.btn_sanctuary.setStyleSheet(btn_style)
        self.btn_sanctuary.clicked.connect(self.sanctuary_requested.emit)
        btn_layout.addWidget(self.btn_sanctuary)

        self.btn_fullscreen = QPushButton("⛶  Vollbild / Fenstermodus (F11)")
        self.btn_fullscreen.setStyleSheet(btn_style)
        self.btn_fullscreen.clicked.connect(self.toggle_fullscreen_requested.emit)
        btn_layout.addWidget(self.btn_fullscreen)

        self.btn_exit = QPushButton("✕  Beenden")
        self.btn_exit.setStyleSheet(btn_style)
        self.btn_exit.clicked.connect(self.exit_requested.emit)
        btn_layout.addWidget(self.btn_exit)

        layout.addWidget(btn_frame, alignment=Qt.AlignmentFlag.AlignCenter)

        # Footer notes
        footer_label = QLabel("Warcraft 3 TD Hommage  •  Python & Pygame-CE Hybrid Engine")
        footer_label.setStyleSheet("color: #627299; font-size: 12px; margin-top: 30px;")
        layout.addWidget(footer_label, alignment=Qt.AlignmentFlag.AlignCenter)
