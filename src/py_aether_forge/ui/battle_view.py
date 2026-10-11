"""Interactive Battle View embedding Pygame combat engine inside PySide6 with Qt HUD."""

import pygame
from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QImage, QKeyEvent, QMouseEvent, QPainter
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from py_aether_forge.core.state import GameState
from py_aether_forge.meta.save_system import SaveData, SaveSystem
from py_aether_forge.render.battle_engine import BattleEngine
from py_aether_forge.towers.elements import ELEMENT_NAMES_DE, ElementType


class BattleViewWidget(QWidget):
    """Integrates Pygame-CE tactical canvas and rich PySide6 HUD overlay."""

    exit_to_menu_requested = Signal()

    def __init__(self, save_system: SaveSystem, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.save_system = save_system
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)

        self.engine: BattleEngine | None = None
        self.pygame_surface: pygame.Surface | None = None

        self._setup_hud_overlay()

        # 60 FPS update timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._game_tick)

    def start_new_game(self) -> None:
        """Initializes a fresh match with meta-progression bonuses."""
        save_data: SaveData = self.save_system.load()
        unlocked_hybrids = {
            ElementType[name]
            for name in save_data.unlocked_hybrids
            if name in ElementType.__members__
        }

        w = max(1024, self.width())
        h = max(600, self.height())

        self.engine = BattleEngine(
            width=w,
            height=h,
            unlocked_hybrids=unlocked_hybrids,
            starting_aether_bonus=save_data.starting_aether_bonus,
            core_health_bonus=save_data.core_health_bonus,
        )
        self.pygame_surface = pygame.Surface((w, h))
        self.timer.start(16)  # ~60 FPS
        self._update_hud_display()

    def _setup_hud_overlay(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 12)

        # Top status bar
        top_bar = QFrame()
        top_bar.setStyleSheet("""
            QFrame {
                background-color: rgba(18, 24, 45, 0.90);
                border: 1px solid #54669E;
                border-radius: 8px;
                padding: 6px;
            }
            QLabel {
                font-weight: bold;
                font-size: 15px;
            }
        """)
        top_layout = QHBoxLayout(top_bar)

        self.lbl_core = QLabel("❤️ Weltenkern: --")
        self.lbl_core.setStyleSheet("color: #FF5A70;")
        top_layout.addWidget(self.lbl_core)

        self.lbl_aether = QLabel("✨ Äther-Staub: --")
        self.lbl_aether.setStyleSheet("color: #FFD54F;")
        top_layout.addWidget(self.lbl_aether)

        self.lbl_wave = QLabel("⚔ Welle: Vorbereitung")
        self.lbl_wave.setStyleSheet("color: #82DCFF;")
        top_layout.addWidget(self.lbl_wave)

        self.lbl_shards = QLabel("💎 Astral-Splitter: +0")
        self.lbl_shards.setStyleSheet("color: #E082FF;")
        top_layout.addWidget(self.lbl_shards)

        top_layout.addStretch()

        self.btn_start_wave = QPushButton("▶ Welle Starten (Leertaste)")
        self.btn_start_wave.setStyleSheet("""
            QPushButton {
                background: #1D5E3A;
                color: #FFFFFF;
                border: 1px solid #4CAF50;
                font-weight: bold;
                padding: 6px 16px;
                border-radius: 6px;
            }
            QPushButton:hover { background: #2E7D32; }
        """)
        self.btn_start_wave.clicked.connect(self._on_start_wave_clicked)
        top_layout.addWidget(self.btn_start_wave)

        self.btn_menu = QPushButton("Zurück zum Menü")
        self.btn_menu.setStyleSheet("""
            QPushButton {
                background: #2E3654;
                color: #DDD;
                border: 1px solid #66759E;
                padding: 6px 14px;
                border-radius: 6px;
            }
            QPushButton:hover { background: #404B75; }
        """)
        self.btn_menu.clicked.connect(self._on_exit_to_menu)
        top_layout.addWidget(self.btn_menu)

        main_layout.addWidget(top_bar)
        main_layout.addStretch()

        # Bottom Bar: Element selector & Draft cards
        self.bottom_bar = QFrame()
        self.bottom_bar.setStyleSheet("""
            QFrame {
                background-color: rgba(18, 24, 45, 0.90);
                border: 1px solid #54669E;
                border-radius: 8px;
                padding: 6px;
            }
        """)
        self.bottom_layout = QHBoxLayout(self.bottom_bar)
        self._setup_element_buttons()
        main_layout.addWidget(self.bottom_bar)

    def _setup_element_buttons(self) -> None:
        lbl = QLabel("Bauturm-Element:")
        lbl.setStyleSheet("color: #91A0C3; font-weight: bold;")
        self.bottom_layout.addWidget(lbl)

        self.elem_buttons: dict[ElementType, QPushButton] = {}
        for elem in (ElementType.FIRE, ElementType.ICE, ElementType.ARCANE, ElementType.NATURE):
            btn = QPushButton(ELEMENT_NAMES_DE[elem])
            btn.setStyleSheet("""
                QPushButton {
                    background: #262D4A;
                    color: #FFFFFF;
                    border: 1px solid #54669E;
                    padding: 6px 12px;
                    border-radius: 4px;
                }
                QPushButton:checked {
                    background: #4FC3F7;
                    color: #000000;
                    font-weight: bold;
                }
            """)
            btn.setCheckable(True)
            btn.clicked.connect(lambda _, e=elem: self._set_build_element(e))
            self.bottom_layout.addWidget(btn)
            self.elem_buttons[elem] = btn

        self.elem_buttons[ElementType.FIRE].setChecked(True)
        self.bottom_layout.addStretch()

        # Draft options layout
        self.draft_container = QWidget()
        self.draft_layout = QHBoxLayout(self.draft_container)
        self.draft_layout.setContentsMargins(0, 0, 0, 0)
        self.bottom_layout.addWidget(self.draft_container)
        self.draft_container.hide()

    def _set_build_element(self, element: ElementType) -> None:
        if self.engine:
            self.engine.selected_build_element = element
        for elem, btn in self.elem_buttons.items():
            btn.setChecked(elem == element)

    def _on_start_wave_clicked(self) -> None:
        if self.engine:
            self.engine.start_next_wave()
            self._update_hud_display()

    def _on_exit_to_menu(self) -> None:
        self.timer.stop()
        if self.engine:
            # Persist earned shards
            save_data = self.save_system.load()
            save_data.total_astral_shards += self.engine.economy.astral_shards
            save_data.highest_wave = max(
                save_data.highest_wave, self.engine.match_state.wave_number
            )
            self.save_system.save(save_data)
        self.exit_to_menu_requested.emit()

    def _game_tick(self) -> None:
        if not self.engine:
            return

        dt = 0.016
        self.engine.update(dt)
        self._update_hud_display()
        self.update()  # Trigger Qt paintEvent

    def _update_hud_display(self) -> None:
        if not self.engine:
            return

        eco = self.engine.economy
        ms = self.engine.match_state

        self.lbl_core.setText(f"❤️ Weltenkern: {eco.core_health} / {eco.max_core_health}")
        self.lbl_aether.setText(f"✨ Äther: {eco.aether_dust}")
        self.lbl_shards.setText(f"💎 Splitter: +{eco.astral_shards}")

        if ms.current_state == GameState.PREPARATION:
            self.lbl_wave.setText(f"⚔ Welle {ms.wave_number + 1} vorbereiten")
            self.btn_start_wave.setEnabled(True)
            self.draft_container.hide()
        elif ms.current_state == GameState.WAVE:
            self.lbl_wave.setText(f"⚔ Welle {ms.wave_number} aktiv")
            self.btn_start_wave.setEnabled(False)
            self.draft_container.hide()
        elif ms.current_state == GameState.DRAFT:
            self.lbl_wave.setText("✦ Wähle eine Scholle zum Anbauen! ✦")
            self.btn_start_wave.setEnabled(False)
            self._update_draft_cards()
        elif ms.current_state == GameState.GAME_OVER:
            self.lbl_wave.setText("💀 Weltenkern Zerstört (Game Over) 💀")
            self.btn_start_wave.setEnabled(False)

    def _update_draft_cards(self) -> None:
        if not self.engine:
            return

        # Build cards if not built
        if self.draft_layout.count() == 0 and self.engine.draft_options:
            self.draft_container.show()
            for idx, shard in enumerate(self.engine.draft_options):
                btn = QPushButton(f"Scholle {idx + 1}: {shard.name}\n(+{shard.bonus_aether} Äther)")
                btn.setStyleSheet("""
                    QPushButton {
                        background: #1C334D;
                        color: #82DCFF;
                        border: 2px solid #4FC3F7;
                        border-radius: 6px;
                        padding: 6px 12px;
                        font-weight: bold;
                    }
                    QPushButton:hover { background: #2A4B70; }
                """)
                btn.clicked.connect(lambda _, i=idx: self._select_draft_option(i))
                self.draft_layout.addWidget(btn)

    def _select_draft_option(self, index: int) -> None:
        if self.engine:
            self.engine.select_draft_shard(index)
            # Clear buttons
            while self.draft_layout.count():
                item = self.draft_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            self.draft_container.hide()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.engine:
            pos = event.position().toPoint()
            gx, gy = self.engine.viewport.screen_to_grid(pos.x(), pos.y())
            self.engine.hover_tile = (gx, gy)
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self.engine:
            pos = event.position().toPoint()
            btn = 1 if event.button() == Qt.MouseButton.LeftButton else 3
            self.engine.handle_mouse_click(pos.x(), pos.y(), btn)
            self._update_hud_display()
        super().mousePressEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Space:
            self._on_start_wave_clicked()
        super().keyPressEvent(event)

    def paintEvent(self, event) -> None:
        if not self.engine or not self.pygame_surface:
            return

        w, h = self.width(), self.height()
        if self.pygame_surface.get_size() != (w, h):
            self.pygame_surface = pygame.Surface((w, h))
            self.engine.starfield.resize(w, h)

        # Draw Pygame tactical arena
        self.engine.draw(self.pygame_surface)

        # Convert Pygame surface buffer to QImage and draw
        raw_data = pygame.image.tobytes(self.pygame_surface, "RGBA")
        qimage = QImage(raw_data, w, h, QImage.Format.Format_RGBA8888)

        painter = QPainter(self)
        painter.drawImage(QPoint(0, 0), qimage)
        painter.end()
