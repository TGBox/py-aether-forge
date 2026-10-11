"""The Astral Forge sanctuary UI for meta-progression research."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from py_aether_forge.meta.research import ResearchTree
from py_aether_forge.meta.save_system import SaveData, SaveSystem


class SanctuaryWidget(QWidget):
    """Interactive research tree in the Astral Forge."""

    back_requested = Signal()

    def __init__(self, save_system: SaveSystem, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.save_system = save_system
        self.save_data: SaveData = self.save_system.load()
        self.research_tree = ResearchTree(self.save_data.unlocked_research_nodes)
        self._init_ui()

    def reload_data(self) -> None:
        """Refreshes save data and research tree state."""
        self.save_data = self.save_system.load()
        self.research_tree = ResearchTree(self.save_data.unlocked_research_nodes)
        self.shards_label.setText(f"💎  Astral-Splitter: {self.save_data.total_astral_shards}")
        self._refresh_nodes()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)

        # Header Bar
        header = QHBoxLayout()
        title = QLabel("⚙  DIE ASTRALE SCHMIEDE")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #82DCFF;")
        header.addWidget(title)

        header.addStretch()

        self.shards_label = QLabel(f"💎  Astral-Splitter: {self.save_data.total_astral_shards}")
        self.shards_label.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #FFCD3C; background: #1C223A; padding: 8px 16px; border-radius: 6px; border: 1px solid #FFCD3C;"
        )
        header.addWidget(self.shards_label)

        btn_back = QPushButton("← Zurück")
        btn_back.setStyleSheet(
            "background: #262D4A; color: #FFF; font-weight: bold; padding: 8px 20px; border-radius: 6px; border: 1px solid #54669E;"
        )
        btn_back.clicked.connect(self.back_requested.emit)
        header.addWidget(btn_back)

        layout.addLayout(header)

        # Subtitle
        sub = QLabel(
            "Investiere gesammelte Astral-Splitter, um neue Elementar-Hybride und dauerhafte Verstärkungen freizuschalten."
        )
        sub.setStyleSheet("color: #91A0C3; font-size: 14px;")
        layout.addWidget(sub)

        # Scroll Area with Nodes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        container = QWidget()
        self.grid_layout = QGridLayout(container)
        self.grid_layout.setSpacing(18)

        self._refresh_nodes()

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _refresh_nodes(self) -> None:
        # Clear existing widgets
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        row, col = 0, 0
        for node in self.research_tree.nodes.values():
            card = self._create_node_card(node)
            self.grid_layout.addWidget(card, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1

    def _create_node_card(self, node) -> QFrame:
        card = QFrame()
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)

        # Status badge & style
        if node.is_unlocked:
            border_color = "#4FC3F7"
            bg_color = "#14283C"
            status_text = "✓ ERFORSCHT"
        elif self.research_tree.can_unlock(node.node_id, self.save_data.total_astral_shards):
            border_color = "#FFCD3C"
            bg_color = "#242A1D"
            status_text = f"FORSCHEN ({node.cost_shards} 💎)"
        else:
            border_color = "#444B66"
            bg_color = "#161A29"
            status_text = f"GESPERRT ({node.cost_shards} 💎)"

        card.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: 2px solid {border_color};
                border-radius: 10px;
                padding: 16px;
            }}
        """)

        # Title
        lbl_title = QLabel(node.name_de)
        lbl_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
        card_layout.addWidget(lbl_title)

        # Description
        lbl_desc = QLabel(node.description_de)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet("color: #91A0C3; font-size: 13px;")
        card_layout.addWidget(lbl_desc)

        # Action / Status Button
        btn = QPushButton(status_text)
        if node.is_unlocked:
            btn.setEnabled(False)
            btn.setStyleSheet(
                "background: #0E1A29; color: #82DCFF; border: 1px solid #4FC3F7; border-radius: 6px; padding: 8px;"
            )
        elif self.research_tree.can_unlock(node.node_id, self.save_data.total_astral_shards):
            btn.setStyleSheet(
                "background: #FFCD3C; color: #111; font-weight: bold; border-radius: 6px; padding: 8px;"
            )
            btn.clicked.connect(lambda _, nid=node.node_id: self._on_unlock_clicked(nid))
        else:
            btn.setEnabled(False)
            btn.setStyleSheet(
                "background: #1C2030; color: #626A85; border: 1px solid #333950; border-radius: 6px; padding: 8px;"
            )

        card_layout.addWidget(btn)
        return card

    def _on_unlock_clicked(self, node_id: str) -> None:
        cost = self.research_tree.unlock(node_id, self.save_data.total_astral_shards)
        if cost > 0:
            self.save_data.total_astral_shards -= cost
            self.save_data.unlocked_research_nodes.add(node_id)

            node = self.research_tree.nodes[node_id]
            if node.unlocked_element:
                self.save_data.unlocked_hybrids.add(node.unlocked_element.name)
            if node.core_hp_bonus:
                self.save_data.core_health_bonus += node.core_hp_bonus
            if node.starting_aether_bonus:
                self.save_data.starting_aether_bonus += node.starting_aether_bonus

            self.save_system.save(self.save_data)
            self.reload_data()
