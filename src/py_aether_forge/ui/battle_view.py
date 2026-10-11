"""Interactive Battle View embedding Pygame combat engine inside PySide6 with rich tactical HUD."""

import logging

import pygame
from PySide6.QtCore import QPoint, QRect, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QImage, QKeyEvent, QMouseEvent, QPainter, QWheelEvent
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from py_aether_forge.core.grid import TileType
from py_aether_forge.core.state import GameState
from py_aether_forge.expansion.platform import PlatformShard
from py_aether_forge.meta.save_system import SaveData, SaveSystem
from py_aether_forge.render.battle_engine import BattleEngine
from py_aether_forge.towers.elements import ELEMENT_SPECS, ElementType
from py_aether_forge.towers.targeting import TargetMode
from py_aether_forge.towers.tower import Tower

logger = logging.getLogger(__name__)

TARGET_MODE_NAMES_DE = {
    TargetMode.FIRST: "Erster (Verhindert Leaks)",
    TargetMode.LAST: "Letzter (Bewacht Portal)",
    TargetMode.STRONGEST: "Stärkster (Fokus auf Tanks)",
    TargetMode.WEAKEST: "Schwächster (Schnelle Kills)",
    TargetMode.CLOSEST: "Nächster (Kürzeste Distanz)",
}


class PlatformMiniPreview(QWidget):
    """Renders a miniature blueprint preview of a platform shard prior to purchase."""

    def __init__(self, shard: PlatformShard, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.shard = shard
        self.tile_px = 22
        cols = max(1, shard.width)
        rows = max(1, shard.height)
        self.setFixedSize(cols * self.tile_px + 8, rows * self.tile_px + 8)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        tp = self.tile_px
        for r, row in enumerate(self.shard.layout):
            for c, tile_type in enumerate(row):
                x = 4 + c * tp
                y = 4 + r * tp
                rect = QRect(x, y, tp - 2, tp - 2)

                if tile_type == TileType.VOID:
                    painter.fillRect(rect, QColor(14, 18, 32))
                    painter.setPen(QColor(30, 38, 60))
                    painter.drawRect(rect)
                elif tile_type == TileType.PLATFORM_WALK:
                    painter.fillRect(rect, QColor(52, 63, 102))
                    painter.setPen(QColor(84, 102, 158))
                    painter.drawRect(rect)
                elif tile_type == TileType.PLATFORM_BUILD:
                    painter.fillRect(rect, QColor(70, 85, 135))
                    painter.setPen(QColor(130, 220, 255))
                    painter.drawRect(rect)
                    # Rune pedestal center dot
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.setBrush(QColor(240, 248, 255, 230))
                    painter.drawEllipse(x + tp // 2 - 3, y + tp // 2 - 3, 5, 5)

        painter.end()


class BattleViewWidget(QWidget):
    """Integrates Pygame-CE tactical canvas with a comprehensive PySide6 HUD."""

    exit_to_menu_requested = Signal()

    def __init__(self, save_system: SaveSystem, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.save_system = save_system
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)

        self.engine: BattleEngine | None = None
        self.pygame_surface: pygame.Surface | None = None
        self._last_draft_wave: int = -1

        # Camera pan and drag state
        self._pan_start_pos = QPoint()
        self._is_panning = False
        self._pan_active_btn: Qt.MouseButton | None = None

        # Inspector cache
        self._fusion_buttons: list[tuple[QPushButton, ElementType, int, str]] = []
        self._last_inspected_signature: tuple | None = None

        self._setup_hud_overlay()

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
        self.engine.viewport.center_on_grid(w, h, self.engine.grid)
        self._last_draft_wave = -1
        self.timer.start(16)
        self._update_hud_display()

    def _setup_hud_overlay(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 10, 14, 10)
        main_layout.setSpacing(8)

        # 1. Top Status Bar
        top_bar = QFrame()
        top_bar.setStyleSheet("""
            QFrame {
                background-color: rgba(14, 19, 36, 0.94);
                border: 1px solid #54669E;
                border-radius: 8px;
                padding: 6px 12px;
            }
            QLabel {
                font-weight: bold;
                font-size: 14px;
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

        # Speed controls (Pause, 1x, 2x, 3x)
        self.btn_pause = QPushButton("⏸ Pause (P)")
        self.btn_pause.setToolTip("Zeit anhalten / fortsetzen (Taste P)")
        self.btn_speed_1x = QPushButton("1x (1)")
        self.btn_speed_1x.setToolTip("Normale Spielgeschwindigkeit (Taste 1)")
        self.btn_speed_2x = QPushButton("2x (2)")
        self.btn_speed_2x.setToolTip("Doppelte Spielgeschwindigkeit (Taste 2)")
        self.btn_speed_3x = QPushButton("3x (3)")
        self.btn_speed_3x.setToolTip("Dreifache Spielgeschwindigkeit (Taste 3)")

        for btn in (self.btn_pause, self.btn_speed_1x, self.btn_speed_2x, self.btn_speed_3x):
            btn.setStyleSheet("""
                QPushButton {
                    background: #1C2338; color: #82DCFF; border: 1px solid #4A5B82;
                    font-weight: bold; padding: 5px 8px; border-radius: 4px; font-size: 12px;
                }
                QPushButton:hover { background: #2A3654; }
            """)
            top_layout.addWidget(btn)

        self.btn_pause.clicked.connect(self._toggle_pause)
        self.btn_speed_1x.clicked.connect(lambda: self._set_speed(1.0))
        self.btn_speed_2x.clicked.connect(lambda: self._set_speed(2.0))
        self.btn_speed_3x.clicked.connect(lambda: self._set_speed(3.0))

        # Camera controls (Zoom & Center)
        self.btn_zoom_out = QPushButton("➖")
        self.btn_zoom_out.setToolTip("Herauszoomen (Mausrad runter)")
        self.btn_zoom_out.setStyleSheet("""
            QPushButton {
                background: #1C2338; color: #82DCFF; border: 1px solid #4A5B82;
                font-weight: bold; padding: 5px 10px; border-radius: 4px; font-size: 13px;
            }
            QPushButton:hover { background: #2A3654; }
        """)
        self.btn_zoom_out.clicked.connect(lambda: self._zoom_step(0.85))
        top_layout.addWidget(self.btn_zoom_out)

        self.btn_zoom_in = QPushButton("➕")
        self.btn_zoom_in.setToolTip("Heranzoomen (Mausrad hoch)")
        self.btn_zoom_in.setStyleSheet("""
            QPushButton {
                background: #1C2338; color: #82DCFF; border: 1px solid #4A5B82;
                font-weight: bold; padding: 5px 10px; border-radius: 4px; font-size: 13px;
            }
            QPushButton:hover { background: #2A3654; }
        """)
        self.btn_zoom_in.clicked.connect(lambda: self._zoom_step(1.18))
        top_layout.addWidget(self.btn_zoom_in)

        self.btn_center = QPushButton("🔍 Zentrieren (C)")
        self.btn_center.setToolTip("Kamera auf das Spielfeld zentrieren (Taste C)")
        self.btn_center.setStyleSheet("""
            QPushButton {
                background: #1C2338; color: #E2E8F0; border: 1px solid #4A5B82;
                font-weight: bold; padding: 5px 10px; border-radius: 4px; font-size: 12px;
            }
            QPushButton:hover { background: #2A3654; }
        """)
        self.btn_center.clicked.connect(self._center_camera)
        top_layout.addWidget(self.btn_center)

        self.btn_start_wave = QPushButton("▶ Welle Starten (Leertaste)")
        self.btn_start_wave.setStyleSheet("""
            QPushButton {
                background: #1D5E3A;
                color: #FFFFFF;
                border: 1px solid #4CAF50;
                font-weight: bold;
                padding: 6px 16px;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover { background: #2E7D32; }
            QPushButton:disabled { background: #1B2920; color: #557755; border-color: #334433; }
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
                font-size: 13px;
            }
            QPushButton:hover { background: #404B75; }
        """)
        self.btn_menu.clicked.connect(self._on_exit_to_menu)
        top_layout.addWidget(self.btn_menu)

        main_layout.addWidget(top_bar)

        # 2. Middle Spacer
        main_layout.addStretch()

        # 3. Draft Overlay Container (Prominent across center-bottom when in DRAFT phase)
        self.draft_container = QFrame()
        self.draft_container.setStyleSheet("""
            QFrame {
                background-color: rgba(14, 22, 42, 0.96);
                border: 2px solid #82DCFF;
                border-radius: 10px;
                padding: 12px;
            }
        """)
        self.draft_vlayout = QVBoxLayout(self.draft_container)
        self.draft_title = QLabel("✦ RUNDENBELOHNUNG: WÄHLE EINE PLATTFORM-SCHOLLE ✦")
        self.draft_title.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #82DCFF; text-align: center;"
        )
        self.draft_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.draft_vlayout.addWidget(self.draft_title)

        self.draft_instruction = QLabel(
            "Wähle ein Fragment und klicke anschließend auf eine Kante im Spielfeld zum Andocken."
        )
        self.draft_instruction.setStyleSheet("color: #FFD54F; font-size: 13px; font-weight: bold;")
        self.draft_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.draft_vlayout.addWidget(self.draft_instruction)

        self.draft_cards_layout = QHBoxLayout()
        self.draft_cards_layout.setSpacing(14)
        self.draft_vlayout.addLayout(self.draft_cards_layout)

        draft_actions_row = QHBoxLayout()
        draft_actions_row.addStretch()
        self.btn_rotate_shard = QPushButton("🔄 Scholle drehen (Taste R / Rechtsklick)")
        self.btn_rotate_shard.setStyleSheet("""
            QPushButton {
                background: #1C334E;
                color: #82DCFF;
                border: 1px solid #4FC3F7;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background: #2A4D75; }
        """)
        self.btn_rotate_shard.clicked.connect(self._on_rotate_shard)
        draft_actions_row.addWidget(self.btn_rotate_shard)

        self.btn_skip_draft = QPushButton("⏭ Auf Plattform verzichten (Doppelter Bonus)")
        self.btn_skip_draft.setToolTip(
            "Verzichte auf den Plattform-Bau und erhalte stattdessen den doppelten Äther-Bonus der besten Scholle!"
        )
        self.btn_skip_draft.setStyleSheet("""
            QPushButton {
                background: #3A2A10;
                color: #FFD54F;
                border: 1px solid #FFC107;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background: #553E17; }
        """)
        self.btn_skip_draft.clicked.connect(self._on_skip_draft)
        draft_actions_row.addWidget(self.btn_skip_draft)

        draft_actions_row.addStretch()
        self.draft_vlayout.addLayout(draft_actions_row)

        main_layout.addWidget(self.draft_container)
        self.draft_container.hide()

        # 4. Creep Inspector Panel (Appears when a creep is clicked/inspected)
        self.creep_inspector_panel = QFrame()
        self.creep_inspector_panel.setStyleSheet("""
            QFrame {
                background-color: rgba(22, 16, 28, 0.95);
                border: 2px solid #FF7043;
                border-radius: 8px;
                padding: 8px 14px;
            }
        """)
        self._setup_creep_inspector_ui()
        main_layout.addWidget(self.creep_inspector_panel)
        self.creep_inspector_panel.hide()

        # 5. Inspector Panel (Appears when a tower is selected)
        self.inspector_panel = QFrame()
        self.inspector_panel.setStyleSheet("""
            QFrame {
                background-color: rgba(14, 20, 38, 0.95);
                border: 2px solid #4FC3F7;
                border-radius: 8px;
                padding: 8px 14px;
            }
        """)
        self._setup_inspector_ui()
        main_layout.addWidget(self.inspector_panel)
        self.inspector_panel.hide()

        # 6. Build Bar (Visible during standard build/combat phases)
        self.build_bar = QFrame()
        self.build_bar.setStyleSheet("""
            QFrame {
                background-color: rgba(14, 20, 38, 0.95);
                border: 1px solid #54669E;
                border-radius: 8px;
                padding: 8px 12px;
            }
        """)
        self._setup_build_bar_ui()
        main_layout.addWidget(self.build_bar)

    def _setup_build_bar_ui(self) -> None:
        vbox = QVBoxLayout(self.build_bar)
        vbox.setContentsMargins(4, 4, 4, 4)
        vbox.setSpacing(6)

        # Top line: Title & Live preview
        header_row = QHBoxLayout()
        lbl_head = QLabel(
            "TURM-ARSENAL (Klicke zum Auswählen • Klicke auf freie Sockel zum Bauen):"
        )
        lbl_head.setStyleSheet("color: #82DCFF; font-weight: bold; font-size: 13px;")
        header_row.addWidget(lbl_head)

        header_row.addStretch()

        self.lbl_build_info = QLabel("")
        self.lbl_build_info.setStyleSheet("color: #E2E8F0; font-size: 12px; font-style: italic;")
        header_row.addWidget(self.lbl_build_info)
        vbox.addLayout(header_row)

        # Buttons row
        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(10)
        self.elem_buttons: dict[ElementType, QPushButton] = {}

        for elem in (ElementType.FIRE, ElementType.ICE, ElementType.ARCANE, ElementType.NATURE):
            spec = ELEMENT_SPECS[elem]
            btn = QPushButton()
            btn.setCheckable(True)

            text = (
                f"{spec.name_de} ({spec.cost} ✨)\n"
                f"⚔ Dmg: {spec.damage:.0f}  |  ⏱ {spec.fire_rate}/s  |  🎯 {spec.range_radius:.1f}\n"
                f"[{spec.effect_name_de}]"
            )
            btn.setText(text)
            btn.setToolTip(f"{spec.name_de}\n\n{spec.description_de}")

            btn.setStyleSheet(f"""
                QPushButton {{
                    background: #1B2238;
                    color: #FFFFFF;
                    border: 2px solid {spec.color_hex};
                    padding: 8px 12px;
                    border-radius: 6px;
                    text-align: left;
                    font-size: 12px;
                }}
                QPushButton:hover {{
                    background: #253050;
                }}
                QPushButton:checked {{
                    background: #2B3D66;
                    border: 2px solid #FFCD3C;
                    font-weight: bold;
                }}
            """)
            btn.clicked.connect(lambda _, e=elem: self._set_build_element(e))
            buttons_row.addWidget(btn)
            self.elem_buttons[elem] = btn

        # Barrier wall button for mazing
        self.btn_barrier = QPushButton()
        self.btn_barrier.setCheckable(True)
        self.btn_barrier.setText("🛡 Äther-Wand (20 ✨)\nPfadsperre & Mazing\n[100% Rückerstattung]")
        self.btn_barrier.setToolTip(
            "Äther-Wand (20 ✨)\n\n"
            "Errichtet eine kristallisierte Barriere auf einer Gehweg-Kachel, um Chaos-Schwärme auf Umwege zu lenken.\n"
            "Rechtsklick auf eine gebaute Wand reißt sie sofort ab (+20 ✨ Rückerstattung)."
        )
        self.btn_barrier.setStyleSheet("""
            QPushButton {
                background: #142838;
                color: #E0F7FA;
                border: 2px solid #4FC3F7;
                padding: 8px 12px;
                border-radius: 6px;
                text-align: left;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #1D3B52;
            }
            QPushButton:checked {
                background: #25587D;
                border: 2px solid #FFCD3C;
                font-weight: bold;
            }
        """)
        self.btn_barrier.clicked.connect(self._set_barrier_mode)
        buttons_row.addWidget(self.btn_barrier)

        vbox.addLayout(buttons_row)
        self._set_build_element(ElementType.FIRE)

    def _setup_inspector_ui(self) -> None:
        layout = QVBoxLayout(self.inspector_panel)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(8)

        # Top row: Name, Level, Close button
        row1 = QHBoxLayout()
        self.lbl_insp_title = QLabel("🔥 Turm")
        self.lbl_insp_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #82DCFF;")
        row1.addWidget(self.lbl_insp_title)

        self.lbl_insp_stats = QLabel("Werte")
        self.lbl_insp_stats.setStyleSheet("color: #E2E8F0; font-size: 13px; font-weight: bold;")
        row1.addWidget(self.lbl_insp_stats)

        row1.addStretch()

        btn_close_insp = QPushButton("✕ Abwählen")
        btn_close_insp.setStyleSheet("""
            QPushButton {
                background: #2E3654;
                color: #DDD;
                border: 1px solid #66759E;
                padding: 4px 10px;
                border-radius: 4px;
            }
        """)
        btn_close_insp.clicked.connect(self._deselect_tower)
        row1.addWidget(btn_close_insp)
        layout.addLayout(row1)

        # Bottom row: Target mode, Upgrade button, Fusion buttons, Sell button
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        # Target Mode combo
        self.lbl_target_mode = QLabel("Zielpriorität:")
        self.lbl_target_mode.setStyleSheet("color: #91A0C3; font-weight: bold;")
        row2.addWidget(self.lbl_target_mode)

        self.combo_target_mode = QComboBox()
        for mode, name in TARGET_MODE_NAMES_DE.items():
            self.combo_target_mode.addItem(name, mode)
        self.combo_target_mode.setStyleSheet("""
            QComboBox {
                background: #1B2238;
                color: #FFF;
                border: 1px solid #54669E;
                border-radius: 4px;
                padding: 4px 8px;
            }
        """)
        self.combo_target_mode.currentIndexChanged.connect(self._on_target_mode_changed)
        row2.addWidget(self.combo_target_mode)

        # Upgrade Button
        self.btn_upgrade = QPushButton("▲ Upgrade")
        self.btn_upgrade.setStyleSheet("""
            QPushButton {
                background: #1D5E3A;
                color: #FFF;
                border: 1px solid #4CAF50;
                font-weight: bold;
                padding: 6px 14px;
                border-radius: 6px;
            }
            QPushButton:hover { background: #2E7D32; }
            QPushButton:disabled { background: #1B2920; color: #667; border-color: #334; }
        """)
        self.btn_upgrade.clicked.connect(self._on_upgrade_clicked)
        row2.addWidget(self.btn_upgrade)

        # Fusion Container
        self.fusion_container = QWidget()
        self.fusion_layout = QHBoxLayout(self.fusion_container)
        self.fusion_layout.setContentsMargins(0, 0, 0, 0)
        row2.addWidget(self.fusion_container)

        row2.addStretch()

        # Sell / Demolish Button
        self.btn_sell = QPushButton("✕ Abreißen (+?? ✨)")
        self.btn_sell.setStyleSheet("""
            QPushButton {
                background: #5A1E24;
                color: #FFAAA0;
                border: 1px solid #E53935;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 6px;
            }
            QPushButton:hover { background: #7A2830; }
        """)
        self.btn_sell.clicked.connect(self._on_sell_clicked)
        row2.addWidget(self.btn_sell)

        layout.addLayout(row2)

    def _set_build_element(self, element: ElementType) -> None:
        if self.engine:
            self.engine.build_mode = "TOWER"
            self.engine.selected_build_element = element
        if hasattr(self, "btn_barrier"):
            self.btn_barrier.setChecked(False)
        for elem, btn in self.elem_buttons.items():
            btn.setChecked(elem == element)

        spec = ELEMENT_SPECS.get(element)
        if spec:
            self.lbl_build_info.setText(
                f"Auswahl: {spec.name_de} ({spec.cost} ✨) • Reichweite: {spec.range_radius} Felder • {spec.effect_name_de}"
            )

    def _set_barrier_mode(self) -> None:
        if self.engine:
            self.engine.build_mode = "BARRIER"
        for btn in self.elem_buttons.values():
            btn.setChecked(False)
        self.btn_barrier.setChecked(True)
        self.lbl_build_info.setText(
            "Auswahl: Äther-Wand (20 ✨) • Klicke auf Gehwege zum Platzieren (Rechtsklick reißt Wand ab)!"
        )

    def _deselect_tower(self) -> None:
        if self.engine:
            self.engine.selected_tower = None
            self.engine.selected_barrier = None
        self._last_inspected_signature = None
        self.inspector_panel.hide()
        self.build_bar.show()

    def _on_target_mode_changed(self, index: int) -> None:
        if self.engine and self.engine.selected_tower:
            mode = self.combo_target_mode.itemData(index)
            if mode:
                self.engine.selected_tower.target_mode = mode

    def _on_upgrade_clicked(self) -> None:
        if self.engine:
            self.engine.upgrade_selected_tower()
            self._update_inspector()

    def _on_sell_clicked(self) -> None:
        if self.engine:
            if self.engine.selected_barrier:
                self.engine.remove_barrier(*self.engine.selected_barrier)
                self.engine.selected_barrier = None
            elif self.engine.selected_tower:
                self.engine.sell_selected_tower()
            self._deselect_tower()

    def _on_start_wave_clicked(self) -> None:
        if self.engine:
            self.engine.start_next_wave()
            self._update_hud_display()

    def _on_exit_to_menu(self) -> None:
        self.timer.stop()
        if self.engine:
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
        self.update()

    def _update_hud_display(self) -> None:
        if not self.engine:
            return

        eco = self.engine.economy
        ms = self.engine.match_state

        self.lbl_core.setText(f"❤️ Weltenkern: {eco.core_health} / {eco.max_core_health}")
        self.lbl_aether.setText(f"✨ Äther: {eco.aether_dust}")
        self.lbl_shards.setText(f"💎 Splitter: +{eco.astral_shards}")

        self._update_speed_buttons_style()

        # State Handling
        if ms.current_state == GameState.DRAFT:
            self.lbl_wave.setText("✦ Rundenbelohnung: Wähle eine Scholle! ✦")
            self.btn_start_wave.setEnabled(False)
            self.inspector_panel.hide()
            self.creep_inspector_panel.hide()
            self.build_bar.hide()
            self._check_and_show_draft()
        else:
            self.draft_container.hide()
            if ms.current_state == GameState.PREPARATION:
                self.lbl_wave.setText(f"⚔ Welle {ms.wave_number + 1} vorbereiten")
                self.btn_start_wave.setEnabled(True)
            elif ms.current_state == GameState.WAVE:
                self.lbl_wave.setText(f"⚔ Welle {ms.wave_number} aktiv")
                self.btn_start_wave.setEnabled(False)
            elif ms.current_state == GameState.GAME_OVER:
                self.lbl_wave.setText("💀 Weltenkern Zerstört (Game Over) 💀")
                self.btn_start_wave.setEnabled(False)

            # Inspector vs Build Bar vs Creep Inspector
            if self.engine.selected_creep:
                self.build_bar.hide()
                self.inspector_panel.hide()
                self._update_creep_inspector()
                self.creep_inspector_panel.show()
            elif self.engine.selected_tower or self.engine.selected_barrier:
                self.creep_inspector_panel.hide()
                self.build_bar.hide()
                self._update_inspector()
                self.inspector_panel.show()
            else:
                self.creep_inspector_panel.hide()
                self.inspector_panel.hide()
                self.build_bar.show()

                if self.engine.warning_message:
                    self.lbl_build_info.setStyleSheet(
                        "color: #FF5A70; font-size: 13px; font-weight: bold;"
                    )
                    self.lbl_build_info.setText(f"⚠ {self.engine.warning_message}")
                elif self.engine.build_mode == "BARRIER":
                    self.lbl_build_info.setStyleSheet(
                        "color: #82DCFF; font-size: 12px; font-style: italic;"
                    )
                    self.lbl_build_info.setText(
                        "Auswahl: Äther-Wand (20 ✨) • Klicke auf Gehwege zum Platzieren (Rechtsklick reißt Wand ab)!"
                    )

    def _check_and_show_draft(self) -> None:
        """Ensures draft options for the current wave are displayed."""
        if not self.engine:
            return

        # Refresh cards if entering draft for a new wave or if layout empty
        if (
            self._last_draft_wave != self.engine.match_state.wave_number
            or self.draft_cards_layout.count() == 0
        ):
            self._last_draft_wave = self.engine.match_state.wave_number
            self._build_draft_cards()

        self.draft_container.show()

    def _build_draft_cards(self) -> None:
        # Clear existing cards
        while self.draft_cards_layout.count():
            item = self.draft_cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.engine or not self.engine.draft_options:
            return

        max_bonus = max((s.bonus_aether for s in self.engine.draft_options), default=30)
        self.btn_skip_draft.setText(
            f"⏭ Auf Plattform verzichten (Doppelter Bonus: +{max_bonus * 2} ✨)"
        )

        for idx, shard in enumerate(self.engine.draft_options):
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: #172138;
                    border: 2px solid #54669E;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(6)

            lbl_name = QLabel(f"Scholle {idx + 1}: {shard.name}")
            lbl_name.setStyleSheet("font-size: 15px; font-weight: bold; color: #82DCFF;")
            card_layout.addWidget(lbl_name)

            # Miniature tactical layout preview
            preview = PlatformMiniPreview(shard)
            card_layout.addWidget(preview, alignment=Qt.AlignmentFlag.AlignCenter)

            walk_count = sum(row.count(TileType.PLATFORM_WALK) for row in shard.layout)
            build_count = sum(row.count(TileType.PLATFORM_BUILD) for row in shard.layout)
            lbl_stats = QLabel(
                f"📐 {shard.width}×{shard.height} Kacheln  |  🛡 {build_count} Bauplätze  |  🚶 {walk_count} Gehwege"
            )
            lbl_stats.setStyleSheet("color: #82DCFF; font-size: 11px; font-weight: bold;")
            lbl_stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
            card_layout.addWidget(lbl_stats)

            lbl_desc = QLabel(shard.description)
            lbl_desc.setWordWrap(True)
            lbl_desc.setStyleSheet("color: #BAC7E0; font-size: 12px;")
            card_layout.addWidget(lbl_desc)

            bonus_txt = f"✨ +{shard.bonus_aether} Äther-Belohnung"
            if shard.rune_affinity:
                bonus_txt += f"  •  ⚡ Rune: {shard.rune_affinity}"
            lbl_bonus = QLabel(bonus_txt)
            lbl_bonus.setStyleSheet("color: #FFCD3C; font-weight: bold; font-size: 12px;")
            card_layout.addWidget(lbl_bonus)

            btn_pick = QPushButton("Diese Scholle wählen")
            btn_pick.setStyleSheet("""
                QPushButton {
                    background: #1D4260;
                    color: #FFFFFF;
                    border: 1px solid #4FC3F7;
                    border-radius: 6px;
                    padding: 8px;
                    font-weight: bold;
                }
                QPushButton:hover { background: #2E6594; }
            """)
            btn_pick.clicked.connect(lambda _, i=idx: self._select_draft_option(i))
            card_layout.addWidget(btn_pick)

            self.draft_cards_layout.addWidget(card)

    def _select_draft_option(self, index: int) -> None:
        if self.engine:
            self.engine.select_draft_shard(index)
            shard = self.engine.selected_draft_shard
            if shard:
                self.draft_instruction.setText(
                    f"👉 Ausgewählt: '{shard.name}' ({shard.width}×{shard.height}). Klicke auf das Spielfeld zum Andocken • Drehen: Taste [R] oder Rechtsklick!"
                )

    def _update_inspector(self) -> None:
        if not self.engine:
            return

        if self.engine.selected_barrier:
            gx, gy = self.engine.selected_barrier
            self.lbl_insp_title.setText("🛡 Äther-Barriere (Wand)")
            self.lbl_insp_stats.setText(
                f"Position: ({gx}, {gy}) • Blockiert Wegpunkt • 100% Rückerstattung (20 ✨)"
            )
            self.lbl_target_mode.hide()
            self.combo_target_mode.hide()
            self.btn_upgrade.hide()
            self.fusion_container.hide()
            self.btn_sell.setText("✕ Wand abreißen (+20 ✨)")
            self.btn_sell.show()
            return

        if not self.engine.selected_tower:
            return

        self.lbl_target_mode.show()
        self.combo_target_mode.show()
        self.btn_upgrade.show()
        self.fusion_container.show()
        self.btn_sell.show()

        t = self.engine.selected_tower
        spec = ELEMENT_SPECS.get(t.element)
        name = spec.name_de if spec else t.element.name

        self.lbl_insp_title.setText(f"{name} (Stufe {t.level})")
        self.lbl_insp_stats.setText(
            f"⚔ Schaden: {t.damage:.1f}  |  ⏱ Rate: {t.fire_rate:.1f}/s  |  🎯 Reichweite: {t.range_radius:.1f} Felder"
        )

        up_cost = self.engine.get_upgrade_cost(t)
        self.btn_upgrade.setText(f"▲ Upgrade auf Stufe {t.level + 1} ({up_cost} ✨)")
        self.btn_upgrade.setEnabled(self.engine.economy.can_afford(up_cost))

        refund = self.engine.get_sell_refund(t)
        self.btn_sell.setText(f"✕ Abreißen (+{refund} ✨)")

        # Target mode combo
        idx = self.combo_target_mode.findData(t.target_mode)
        if idx >= 0:
            self.combo_target_mode.blockSignals(True)
            self.combo_target_mode.setCurrentIndex(idx)
            self.combo_target_mode.blockSignals(False)

        # Fusions: rebuild only when inspected tower signature changes
        current_signature = (id(t), t.element, t.level, t.is_hybrid)
        if getattr(self, "_last_inspected_signature", None) != current_signature:
            self._last_inspected_signature = current_signature
            self._rebuild_fusion_buttons(t)
        else:
            self._refresh_fusion_buttons(t)

    def _rebuild_fusion_buttons(self, t: Tower) -> None:
        """Constructs fusion buttons once per tower selection/transformation."""
        while self.fusion_layout.count():
            item = self.fusion_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._fusion_buttons.clear()

        if not t.is_hybrid:
            for other_elem in (
                ElementType.FIRE,
                ElementType.ICE,
                ElementType.ARCANE,
                ElementType.NATURE,
            ):
                if other_elem == t.element:
                    continue
                hybrid = self.engine.fusion_registry.get_recipe(t.element, other_elem)
                if hybrid is None:
                    continue
                hspec = ELEMENT_SPECS.get(hybrid)
                hname = hspec.name_de if hspec else hybrid.name
                cost = 120

                btn_fuse = QPushButton(f"⚡ Fusion: {hname} ({cost} ✨)")
                btn_fuse.clicked.connect(lambda _, e=other_elem: self._on_fuse_clicked(e))
                self.fusion_layout.addWidget(btn_fuse)
                self._fusion_buttons.append((btn_fuse, other_elem, cost, hname))

        self._refresh_fusion_buttons(t)

    def _refresh_fusion_buttons(self, t: Tower) -> None:
        """Lightweight tick update of button enabled state without destroying Qt widgets."""
        if not self.engine:
            return
        for btn, other_elem, cost, hname in self._fusion_buttons:
            can_fuse = self.engine.fusion_registry.can_fuse(
                t.element, other_elem, self.engine.unlocked_hybrids
            )
            has_gold = self.engine.economy.can_afford(cost)
            if can_fuse:
                btn.setEnabled(has_gold)
                btn.setText(f"⚡ Fusion: {hname} ({cost} ✨)")
                if has_gold:
                    btn.setToolTip(
                        f"Klicke, um Turm zu {hname} zu verschmelzen (+{cost} ✨ Investition)!"
                    )
                    btn.setStyleSheet("""
                        QPushButton {
                            background: #4A1D5E;
                            color: #E2B6FF;
                            border: 1px solid #BA68C8;
                            padding: 6px 12px;
                            border-radius: 6px;
                            font-weight: bold;
                        }
                        QPushButton:hover { background: #6A2D8E; }
                    """)
                else:
                    btn.setToolTip(f"Nicht genügend Äther-Staub ({cost} ✨ benötigt)!")
                    btn.setStyleSheet("""
                        QPushButton {
                            background: #2D1A38;
                            color: #9977AA;
                            border: 1px solid #664477;
                            padding: 6px 12px;
                            border-radius: 6px;
                            font-weight: bold;
                        }
                    """)
            else:
                btn.setEnabled(False)
                btn.setText(f"🔒 {hname} (In Schmiede erforschen)")
                btn.setToolTip(
                    f"{hname} muss im Hauptmenü (Heiligtum / Astrale Schmiede) erforscht werden!"
                )
                btn.setStyleSheet("""
                    QPushButton {
                        background: #201726;
                        color: #7A6588;
                        border: 1px solid #443350;
                        padding: 6px 10px;
                        border-radius: 6px;
                    }
                """)

    def _on_fuse_clicked(self, second_elem: ElementType) -> None:
        if self.engine:
            success = self.engine.fuse_selected_tower(second_elem)
            if success:
                self._last_inspected_signature = None
                self._update_inspector()
                self._update_hud_display()

    def _on_skip_draft(self) -> None:
        """Forgoes platform shard drafting and claims double dust bonus instead."""
        if self.engine:
            self.engine.skip_draft()
            self._update_hud_display()

    def _toggle_pause(self) -> None:
        if self.engine:
            self.engine.toggle_pause()
            self._update_speed_buttons_style()
            self._update_hud_display()

    def _set_speed(self, scale: float) -> None:
        if self.engine:
            self.engine.set_time_scale(scale)
            if self.engine.is_paused:
                self.engine.is_paused = False
            self._update_speed_buttons_style()
            self._update_hud_display()

    def _update_speed_buttons_style(self) -> None:
        if not self.engine:
            return
        is_paused = self.engine.is_paused
        speed = self.engine.time_scale

        active_style = (
            "background: #25587D; color: #FFD54F; border: 1px solid #FFCD3C; "
            "font-weight: bold; padding: 5px 8px; border-radius: 4px; font-size: 12px;"
        )
        pause_active_style = (
            "background: #5A1E24; color: #FFAAA0; border: 1px solid #E53935; "
            "font-weight: bold; padding: 5px 8px; border-radius: 4px; font-size: 12px;"
        )
        normal_style = (
            "background: #1C2338; color: #82DCFF; border: 1px solid #4A5B82; "
            "font-weight: bold; padding: 5px 8px; border-radius: 4px; font-size: 12px;"
        )

        self.btn_pause.setStyleSheet(pause_active_style if is_paused else normal_style)
        self.btn_pause.setText("▶ Weiter (P)" if is_paused else "⏸ Pause (P)")

        self.btn_speed_1x.setStyleSheet(
            active_style if (not is_paused and abs(speed - 1.0) < 0.1) else normal_style
        )
        self.btn_speed_2x.setStyleSheet(
            active_style if (not is_paused and abs(speed - 2.0) < 0.1) else normal_style
        )
        self.btn_speed_3x.setStyleSheet(
            active_style if (not is_paused and abs(speed - 3.0) < 0.1) else normal_style
        )

    def _setup_creep_inspector_ui(self) -> None:
        layout = QVBoxLayout(self.creep_inspector_panel)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # Header row: Icon & Name, Boss tag, Close
        header_row = QHBoxLayout()
        self.lbl_creep_name = QLabel("👾 Gegner-Information")
        self.lbl_creep_name.setStyleSheet("font-size: 16px; font-weight: bold; color: #FF7043;")
        header_row.addWidget(self.lbl_creep_name)

        self.lbl_creep_type_badge = QLabel("Kategorie")
        self.lbl_creep_type_badge.setStyleSheet(
            "background: #2A1810; color: #FFAB91; border: 1px solid #FF7043; "
            "border-radius: 4px; padding: 2px 6px; font-size: 11px; font-weight: bold;"
        )
        header_row.addWidget(self.lbl_creep_type_badge)

        header_row.addStretch()

        btn_close = QPushButton("✕ Abwählen")
        btn_close.setStyleSheet("""
            QPushButton {
                background: #2E3654;
                color: #DDD;
                border: 1px solid #66759E;
                padding: 4px 10px;
                border-radius: 4px;
            }
            QPushButton:hover { background: #404B75; }
        """)
        btn_close.clicked.connect(self._deselect_creep)
        header_row.addWidget(btn_close)
        layout.addLayout(header_row)

        # Stats row: HP, Speed, Bounty
        stats_row = QHBoxLayout()
        self.lbl_creep_hp = QLabel("❤️ Leben: -- / --")
        self.lbl_creep_hp.setStyleSheet("color: #FF5252; font-weight: bold; font-size: 13px;")
        stats_row.addWidget(self.lbl_creep_hp)

        self.lbl_creep_speed = QLabel("⚡ Tempo: --")
        self.lbl_creep_speed.setStyleSheet("color: #82DCFF; font-weight: bold; font-size: 13px;")
        stats_row.addWidget(self.lbl_creep_speed)

        self.lbl_creep_bounty = QLabel("✨ Kopfgeld: +--")
        self.lbl_creep_bounty.setStyleSheet("color: #FFD54F; font-weight: bold; font-size: 13px;")
        stats_row.addWidget(self.lbl_creep_bounty)

        stats_row.addStretch()
        layout.addLayout(stats_row)

        # Tactical strengths & weaknesses
        tactical_row = QHBoxLayout()
        self.lbl_creep_weakness = QLabel("⚡ Schwächen: --")
        self.lbl_creep_weakness.setStyleSheet("color: #81C784; font-size: 12px; font-weight: bold;")
        tactical_row.addWidget(self.lbl_creep_weakness)

        self.lbl_creep_resistance = QLabel("🛡 Resistenzen: --")
        self.lbl_creep_resistance.setStyleSheet(
            "color: #E57373; font-size: 12px; font-weight: bold;"
        )
        tactical_row.addWidget(self.lbl_creep_resistance)

        self.lbl_creep_special = QLabel("✨ Besonderheit: --")
        self.lbl_creep_special.setStyleSheet("color: #BA68C8; font-size: 12px; font-weight: bold;")
        tactical_row.addWidget(self.lbl_creep_special)

        tactical_row.addStretch()
        layout.addLayout(tactical_row)

        # Status effects row
        self.lbl_creep_effects = QLabel("🔮 Aktive Statuseffekte: Keine")
        self.lbl_creep_effects.setStyleSheet("color: #E2E8F0; font-size: 12px; font-style: italic;")
        layout.addWidget(self.lbl_creep_effects)

    def _deselect_creep(self) -> None:
        if self.engine:
            self.engine.selected_creep = None
        self._update_hud_display()

    def _update_creep_inspector(self) -> None:
        if not self.engine or not self.engine.selected_creep:
            return
        creep = self.engine.selected_creep
        try:
            boss_prefix = "👑 BOSS: " if creep.is_boss else ""
            self.lbl_creep_name.setText(f"{boss_prefix}{creep.name}")
            self.lbl_creep_type_badge.setText(creep.armor_type.name)

            hp_val = getattr(creep, "hp", getattr(creep, "current_health", 0.0))
            max_hp_val = getattr(creep, "max_hp", hp_val)
            self.lbl_creep_hp.setText(f"❤️ Leben: {max(0, int(hp_val))} / {int(max_hp_val)}")
            self.lbl_creep_speed.setText(f"⚡ Tempo: {creep.speed:.1f}")
            self.lbl_creep_bounty.setText(f"✨ Kopfgeld: +{creep.bounty}")

            self.lbl_creep_weakness.setText(f"⚡ Schwächen: {creep.weaknesses_text}")
            self.lbl_creep_resistance.setText(f"🛡 Resistenzen: {creep.resistances_text}")

            special_desc = []
            if creep.regen_per_second > 0:
                if creep.is_burning:
                    special_desc.append(
                        f"Regeneration (+{creep.regen_per_second:.0f}/s) BLOCKIERT durch Verbrennung!"
                    )
                else:
                    special_desc.append(f"Regeneration (+{creep.regen_per_second:.0f}/s HP)")
            if creep.is_boss:
                special_desc.append("Immense Lebenskraft")
            self.lbl_creep_special.setText(
                f"✨ Besonderheit: {', '.join(special_desc) if special_desc else 'Standard'}"
            )

            effects_strs = []
            for eff in creep.active_effects:
                name = getattr(eff, "name", str(getattr(eff, "effect_type", "Status")))
                dur = getattr(eff, "duration_remaining", getattr(eff, "duration", 0.0))
                icon = getattr(eff, "icon", "✨")
                effects_strs.append(f"{icon} {name} ({dur:.1f}s)")
            if effects_strs:
                self.lbl_creep_effects.setText(
                    f"🔮 Aktive Statuseffekte: {' • '.join(effects_strs)}"
                )
                self.lbl_creep_effects.setStyleSheet(
                    "color: #FFD54F; font-size: 12px; font-weight: bold;"
                )
            else:
                self.lbl_creep_effects.setText("🔮 Aktive Statuseffekte: Keine")
                self.lbl_creep_effects.setStyleSheet(
                    "color: #91A0C3; font-size: 12px; font-style: italic;"
                )
        except (AttributeError, KeyError, TypeError, ValueError) as err:
            logger.debug("Exception updating creep inspector: %s", err)

    def _zoom_step(self, factor: float) -> None:
        if self.engine:
            cx, cy = self.width() // 2, self.height() // 2
            self.engine.viewport.zoom_at(cx, cy, factor)
            self.update()

    def _center_camera(self) -> None:
        if self.engine:
            w, h = max(1, self.width()), max(1, self.height())
            self.engine.viewport.zoom = 1.0
            self.engine.viewport.center_on_grid(w, h, self.engine.grid)
            self.update()

    def _on_rotate_shard(self) -> None:
        if self.engine and self.engine.selected_draft_shard:
            self.engine.rotate_selected_draft_shard()
            shard = self.engine.selected_draft_shard
            self.draft_instruction.setText(
                f"🔄 Gedreht: '{shard.name}' ({shard.width}×{shard.height}). Klicke auf das Spielfeld zum Andocken • Drehen: Taste [R] oder Rechtsklick!"
            )
            self.update()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.engine:
            pos = event.position().toPoint()
            delta = event.angleDelta().y()
            factor = 1.15 if delta > 0 else 0.87
            self.engine.viewport.zoom_at(pos.x(), pos.y(), factor)
            self.update()
        super().wheelEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        pos = event.position().toPoint()
        if event.button() in (Qt.MouseButton.MiddleButton, Qt.MouseButton.RightButton):
            self._pan_start_pos = pos
            self._is_panning = False
            self._pan_active_btn = event.button()
            if event.button() == Qt.MouseButton.MiddleButton:
                self._is_panning = True
                return

        if event.button() == Qt.MouseButton.LeftButton and self.engine:
            self.engine.handle_mouse_click(pos.x(), pos.y(), 1)
            self._update_hud_display()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pos = event.position().toPoint()
        if hasattr(self, "_pan_active_btn") and self._pan_active_btn:
            delta = pos - self._pan_start_pos
            if not self._is_panning and delta.manhattanLength() > 5:
                self._is_panning = True
            if self._is_panning and self.engine:
                self.engine.viewport.pan(delta.x(), delta.y())
                self._pan_start_pos = pos
                self.update()
                return

        if self.engine:
            gx, gy = self.engine.viewport.screen_to_grid(pos.x(), pos.y())
            self.engine.hover_tile = (gx, gy)
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if hasattr(self, "_pan_active_btn") and event.button() == self._pan_active_btn:
            was_panning = getattr(self, "_is_panning", False)
            self._is_panning = False
            self._pan_active_btn = None
            if was_panning:
                return

            # Clean right-click without drag -> execute right-click action (e.g. rotate shard or demolish)
            if event.button() == Qt.MouseButton.RightButton and self.engine:
                pos = event.position().toPoint()
                self.engine.handle_mouse_click(pos.x(), pos.y(), 3)
                self._update_hud_display()
                self.update()
                return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Space:
            self._on_start_wave_clicked()
        elif event.key() == Qt.Key.Key_R:
            self._on_rotate_shard()
        elif event.key() == Qt.Key.Key_C:
            self._center_camera()
        elif event.key() == Qt.Key.Key_P:
            self._toggle_pause()
        elif event.key() == Qt.Key.Key_1:
            self._set_speed(1.0)
        elif event.key() == Qt.Key.Key_2:
            self._set_speed(2.0)
        elif event.key() == Qt.Key.Key_3:
            self._set_speed(3.0)
        super().keyPressEvent(event)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.engine:
            w, h = max(1, self.width()), max(1, self.height())
            if not self.pygame_surface or self.pygame_surface.get_size() != (w, h):
                self.pygame_surface = pygame.Surface((w, h))
                self.engine.width = w
                self.engine.height = h
                self.engine.starfield.resize(w, h)

    def paintEvent(self, event) -> None:
        if not self.engine or not self.pygame_surface:
            return

        w, h = max(1, self.width()), max(1, self.height())
        if self.pygame_surface.get_size() != (w, h):
            self.pygame_surface = pygame.Surface((w, h))
            self.engine.starfield.resize(w, h)

        try:
            self.engine.draw(self.pygame_surface)
        except (pygame.error, RuntimeError) as err:
            logger.debug("Render exception caught in paintEvent: %s", err)

        raw_data = pygame.image.tobytes(self.pygame_surface, "RGBA")
        qimage = QImage(raw_data, w, h, QImage.Format.Format_RGBA8888)

        painter = QPainter(self)
        painter.drawImage(QPoint(0, 0), qimage)
        painter.end()
