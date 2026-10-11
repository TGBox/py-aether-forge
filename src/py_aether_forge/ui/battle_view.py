"""Interactive Battle View embedding Pygame combat engine inside PySide6 with rich tactical HUD."""

import pygame
from PySide6.QtCore import QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QImage, QKeyEvent, QMouseEvent, QPainter
from PySide6.QtWidgets import (
    QComboBox,
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
from py_aether_forge.towers.elements import ELEMENT_SPECS, ElementType
from py_aether_forge.towers.targeting import TargetMode

TARGET_MODE_NAMES_DE = {
    TargetMode.FIRST: "Erster (Verhindert Leaks)",
    TargetMode.LAST: "Letzter (Bewacht Portal)",
    TargetMode.STRONGEST: "Stärkster (Fokus auf Tanks)",
    TargetMode.WEAKEST: "Schwächster (Schnelle Kills)",
    TargetMode.CLOSEST: "Nächster (Kürzeste Distanz)",
}


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

        main_layout.addWidget(self.draft_container)
        self.draft_container.hide()

        # 4. Inspector Panel (Appears when a tower is selected)
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

        # 5. Build Bar (Visible during standard build/combat phases)
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
        lbl_tm = QLabel("Zielpriorität:")
        lbl_tm.setStyleSheet("color: #91A0C3; font-weight: bold;")
        row2.addWidget(lbl_tm)

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

        # Sell Button
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
            self.engine.selected_build_element = element
        for elem, btn in self.elem_buttons.items():
            btn.setChecked(elem == element)

        spec = ELEMENT_SPECS.get(element)
        if spec:
            self.lbl_build_info.setText(
                f"Auswahl: {spec.name_de} ({spec.cost} ✨) • Reichweite: {spec.range_radius} Felder • {spec.effect_name_de}"
            )

    def _deselect_tower(self) -> None:
        if self.engine:
            self.engine.selected_tower = None
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

        # State Handling
        if ms.current_state == GameState.DRAFT:
            self.lbl_wave.setText("✦ Rundenbelohnung: Wähle eine Scholle! ✦")
            self.btn_start_wave.setEnabled(False)
            self.inspector_panel.hide()
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

            # Inspector vs Build Bar
            if self.engine.selected_tower:
                self.build_bar.hide()
                self._update_inspector()
                self.inspector_panel.show()
            else:
                self.inspector_panel.hide()
                self.build_bar.show()

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
                    f"👉 Ausgewählt: '{shard.name}'. Klicke jetzt auf das Spielfeld, um die Scholle an einer grünen Kante anzudocken!"
                )

    def _update_inspector(self) -> None:
        if not self.engine or not self.engine.selected_tower:
            return

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

        # Fusions
        while self.fusion_layout.count():
            item = self.fusion_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

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
                can_fuse = self.engine.fusion_registry.can_fuse(
                    t.element, other_elem, self.engine.unlocked_hybrids
                )
                has_gold = self.engine.economy.can_afford(cost)

                if can_fuse:
                    btn_fuse.setEnabled(has_gold)
                    btn_fuse.setStyleSheet("""
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
                    btn_fuse.clicked.connect(lambda _, e=other_elem: self._on_fuse_clicked(e))
                else:
                    btn_fuse.setEnabled(False)
                    btn_fuse.setText(f"🔒 {hname} (In Schmiede erforschen)")
                    btn_fuse.setStyleSheet("""
                        QPushButton {
                            background: #201726;
                            color: #7A6588;
                            border: 1px solid #443350;
                            padding: 6px 10px;
                            border-radius: 6px;
                        }
                    """)

                self.fusion_layout.addWidget(btn_fuse)

    def _on_fuse_clicked(self, second_elem: ElementType) -> None:
        if self.engine:
            self.engine.fuse_selected_tower(second_elem)
            self._update_inspector()

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

        self.engine.draw(self.pygame_surface)

        raw_data = pygame.image.tobytes(self.pygame_surface, "RGBA")
        qimage = QImage(raw_data, w, h, QImage.Format.Format_RGBA8888)

        painter = QPainter(self)
        painter.drawImage(QPoint(0, 0), qimage)
        painter.end()
