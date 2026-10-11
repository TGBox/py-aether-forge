# Implementierungsplan: Die Äther-Schmiede

## Übersicht

Ein modulares, hochperformantes 2D Astral-Fantasy Tower-Defense-Spiel mit PySide6-Shell und Pygame-CE-Schlachtfeld.
Die Entwicklung folgt strengem Test-Driven-Development (TDD), sauberer Kapselung der Simulationslogik (headless testbar ohne Pygame-Fenster) und schrittweiser vertikaler Integration.

## Architekturentscheidungen

- **Headless-First Kernlogik:** Das Spielfeld, Kacheln, A*-Wegfindung, Turmfusion, Gegner und Wellen leben in `core/`, `towers/`, `enemies/` und `expansion/`. Keine Grafik- oder Pygame-Abhängigkeiten in den reinen Daten- und Simulationsklassen.
- **Hybrid-Shell:** PySide6 steuert Fensterverwaltung, Vollbild/Fenstermodus, Hauptmenü und die Astrale Schmiede (Meta-Progression). Das Schlachtfeld wird über Pygame-CE gerendert.
- **TDD:** Jeder Simulationsbaustein erhält vor bzw. parallel zur Implementierung umfassende Unit-Tests in `tests/`.

---

## Phasenübersicht

### Phase 1: Projekt-Setup & Fundament

- `pyproject.toml` um `pygame-ce` und Dev-Dependencies (`pytest`, `ruff`) erweitern.
- Konfiguration (`config.py`), Spielzustände (`core/state.py`) und Wirtschaft/Kern (`core/economy.py`).

### Phase 2: Kachel-Grid, A*-Pathfinding & Roguelite-Draft

- Diskretes Kachel-Raster (`core/grid.py`) und schwebende Schollen (`expansion/platform.py`).
- A*-Wegfindung (`core/pathfinding.py`) mit dynamischer Pfadberechnung und Blockade-Schutz.
- 3-Karten-Schollen-Draft (`expansion/drafter.py`) mit Kantenvalidierung.

### Phase 3: Turmarchitektur, Elementar-Fusion & Wellenspawner

- 4 Grundelemente & Status-Effekte (`towers/elements.py`).
- Element-TD-Fusionsmatrix (`towers/fusion.py`) für freischaltbare Hybride.
- Turm-Modell & Zielprioritäten (`towers/tower.py`, `towers/targeting.py`).
- Creeps, Rüstungsarten & Wellen-Logik (`enemies/creep.py`, `core/wave_spawner.py`).

### Phase 4: Die Astrale Schmiede (Meta-Progression & Speichersystem)

- Atomares JSON-Speichersystem (`meta/save_system.py`).
- Forschungsbaum für Hybrid-Unlocks und Kern-Upgrades (`meta/research.py`).

### Phase 5: Pygame-CE Schlachtfeld-Engine & Effekte

- Parallax-Sternenhintergrund (`render/starfield.py`) & Magie-Partikelsystem (`render/particles.py`).
- Viewport, Kamera und Kachel-Renderer (`render/viewport.py`).
- Interaktive Steuerung (Klick-zu-Bauen, Schollen-Platzierung, Reichweitenanzeige).

### Phase 6: PySide6 Shell, UI-Widgets & End-to-End Polish

- Hauptmenü & Vollbild/Fenster-Umschaltung via F11 (`app.py`, `ui/main_menu.py`).
- Astrale Schmiede Sanktuarium-UI (`ui/sanctuary_ui.py`).
- Schlachtfeld-HUD (`ui/hud_overlay.py`) & Battle-View-Einbettung (`ui/battle_view.py`).

---

## Risiken & Gegenmaßnahmen

| Risiko | Auswirkung | Gegenmaßnahme |
| :--- | :--- | :--- |
| Pfad-Blockade durch Schollenanbau oder Turmbau | Hoch | Strikte Validierungsregel: Vor Platzierung prüfen, ob A* weiterhin einen gültigen Pfad zum Kern findet. |
| Event-Konflikte zwischen PySide6 und Pygame | Mittel | Saubere Entkopplung: Pygame-Loop im eigenen Update-Zyklus oder QTimer-getriebenem Frame-Blitting. |
| Performance bei vielen Partikeln & Gegnern | Gering | Objekt-Pooling für Partikel, Vektor-basierte Berechnungen, Pygame-CE Hardware-beschleunigtes Blitting. |
