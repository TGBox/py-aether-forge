# Aufgabenliste: Die Äther-Schmiede

## Phase 1: Projekt-Setup & Basisfundament

- [ ] **Task 1.1: Abhängigkeiten und Projektkonfiguration**
  - **Beschreibung:** `pyproject.toml` mit `pygame-ce` und Dev-Dependencies (`pytest`, `ruff`) ausstatten, mit `uv sync` auflösen.
  - **Akzeptanzkriterien:** `uv sync` läuft erfolgreich durch, `pygame-ce` und `pytest` sind im Virtualenv verfügbar.
  - **Verifikation:** `uv run python -c "import pygame, PySide6, pytest; print('OK')"`
  - **Dateien:** `pyproject.toml`

- [ ] **Task 1.2: Kern-Konfiguration & Spielzustand**
  - **Beschreibung:** Zentrale Konstanten (`config.py`), Spielzustände (`core/state.py`) und Wirtschaft/Weltenkern (`core/economy.py`) definieren.
  - **Akzeptanzkriterien:** Enum `GameState` (PREPARATION, WAVE, DRAFT, GAME_OVER, VICTORY), Klasse `Economy` (Äther-Staub, Weltenkern-Leben, Astral-Splitter, Belohnungsauszahlung, Leak-Strafe).
  - **Verifikation:** `uv run pytest tests/test_economy_waves.py`
  - **Dateien:** `src/py_aether_forge/config.py`, `src/py_aether_forge/core/state.py`, `src/py_aether_forge/core/economy.py`, `tests/test_economy_waves.py`

### Checkpoint 1: Setup & Basissysteme

- [ ] Alle Abhängigkeiten synchronisiert
- [ ] Tests für Economy und Kernleben bestehen

---

## Phase 2: Kachel-Raster, Schollen & A*-Wegfindung

- [ ] **Task 2.1: Diskretes Kachel-Raster & Schollen-Modell**
  - **Beschreibung:** `Tile`, `TileType` (VOID, PLATFORM_WALK, PLATFORM_BUILD, CORE, PORTAL), `Grid` und `PlatformShard` implementieren.
  - **Akzeptanzkriterien:** Kacheln können platziert und abgefragt werden. Nachbarschaftsbeziehungen (4 Richtungen) sind korrekt.
  - **Verifikation:** `uv run pytest tests/test_grid_pathfinding.py -k test_grid`
  - **Dateien:** `src/py_aether_forge/core/grid.py`, `src/py_aether_forge/expansion/platform.py`, `tests/test_grid_pathfinding.py`

- [ ] **Task 2.2: A*-Pathfinding mit Blockade-Schutz**
  - **Beschreibung:** A*-Wegfindungsalgorithmus auf begehbaren Kacheln (`PLATFORM_WALK`). Pfad vom Einfallstor zum Weltenkern berechnen.
  - **Akzeptanzkriterien:** Findet den kürzesten Pfad; gibt Fehler oder `None` zurück, falls kein Pfad existiert; `can_place_tower` verhindert Blockieren des einzigen Pfades.
  - **Verifikation:** `uv run pytest tests/test_grid_pathfinding.py -k test_pathfinding`
  - **Dateien:** `src/py_aether_forge/core/pathfinding.py`, `tests/test_grid_pathfinding.py`

- [ ] **Task 2.3: Roguelite-Schollen-Drafter & Kanten-Andocken**
  - **Beschreibung:** Generator für 3 Schollen-Fragmente mit unterschiedlichen Layouts und Boni. Validierung von Andock-Kanten an bestehende Schollen.
  - **Akzeptanzkriterien:** Generiert 3 unterschiedliche Fragmente; prüft Kanten-Nachbarschaft; stellt sicher, dass nach Anbau ein valider Pfad zum Kern existiert.
  - **Verifikation:** `uv run pytest tests/test_platform_draft.py`
  - **Dateien:** `src/py_aether_forge/expansion/drafter.py`, `tests/test_platform_draft.py`

### Checkpoint 2: Raster, Wegfindung & Schollen-Expansion

- [ ] Alle Grid-, Pathfinding- und Draft-Tests grün
- [ ] Pfade werden bei Kachelanbau deterministisch berechnet

---

## Phase 3: Turmarchitektur, Element-TD-Fusion & Wellenspawner

- [ ] **Task 3.1: Element-System & Fusionsmatrix**
  - **Beschreibung:** Enums für 4 Basiselemente (Feuer, Eis, Arkan, Natur) und Hybride (Frostfeuer, Plasma, Dampf etc.). Rezept-Registry zur Überprüfung von Fusionskombinationen.
  - **Akzeptanzkriterien:** `can_fuse(elem1, elem2, unlocked_hybrids)` liefert korrektes Hybridelement zurück; Fusionsmatrix ist symmetrisch.
  - **Verifikation:** `uv run pytest tests/test_tower_fusion.py -k test_fusion_matrix`
  - **Dateien:** `src/py_aether_forge/towers/elements.py`, `src/py_aether_forge/towers/fusion.py`, `tests/test_tower_fusion.py`

- [ ] **Task 3.2: Turm-Klasse & Zielerfassung**
  - **Beschreibung:** `Tower`-Klasse mit Reichweite, Schaden, Feuerrate und Zielprioritäten (`FIRST`, `LAST`, `CLOSEST`, `STRONGEST`, `WEAKEST`).
  - **Akzeptanzkriterien:** Turm wählt zielsicher den richtigen Gegner in Reichweite basierend auf Modus; Upgrade- und Fusionsmethoden aktualisieren Werte.
  - **Verifikation:** `uv run pytest tests/test_tower_fusion.py -k test_targeting`
  - **Dateien:** `src/py_aether_forge/towers/tower.py`, `src/py_aether_forge/towers/targeting.py`, `tests/test_tower_fusion.py`

- [ ] **Task 3.3: Creeps, Status-Effekte & Wellen-Spawner**
  - **Beschreibung:** Gegner-Klassen (`Creep`), Debuff-System (Verbrennung, Verlangsamung, Rüstungsminderung) und Wellen-Generator mit geometrischer Skalierung (~1.12x HP).
  - **Akzeptanzkriterien:** Creep bewegt sich entlang Pfad-Wegpunkten; Status-Effekte ticken mit `dt`; Wellenspawner emittiert geordnete Gegner-Gruppen.
  - **Verifikation:** `uv run pytest tests/test_economy_waves.py -k test_waves`
  - **Dateien:** `src/py_aether_forge/enemies/creep.py`, `src/py_aether_forge/enemies/types.py`, `src/py_aether_forge/core/wave_spawner.py`, `tests/test_economy_waves.py`

### Checkpoint 3: Vollständige Kampf- & Wellensimulation

- [ ] Headless-Simulation läuft fehlerfrei: Wellen starten, Gegner laufen Pfad, Türme feuern, Gegner sterben oder leaken.
- [ ] 100% Tests grün

---

## Phase 4: Die Astrale Schmiede (Meta-Progression & Persistenz)

- [ ] **Task 4.1: Atomares Speichersystem**
  - **Beschreibung:** Savegame-Manager für persistente Spieldaten (gesammelte Astral-Splitter, freigeschaltete Hybrid-Rezepte, Highscore).
  - **Akzeptanzkriterien:** Atomares Schreiben via Temp-Datei verhindert Korruption; Standard-Profil bei Erststart.
  - **Verifikation:** `uv run pytest tests/test_meta_persistence.py -k test_save`
  - **Dateien:** `src/py_aether_forge/meta/save_system.py`, `tests/test_meta_persistence.py`

- [ ] **Task 4.2: Forschungsbaum-Logik**
  - **Beschreibung:** Modell für den Forschungsbaum der Astralen Schmiede mit Freischalt-Voraussetzungen und Kosten in Astral-Splittern.
  - **Akzeptanzkriterien:** Knoten schalten erst frei, wenn Eltern-Knoten erforscht sind und genügend Splitter vorhanden sind.
  - **Verifikation:** `uv run pytest tests/test_meta_persistence.py -k test_research`
  - **Dateien:** `src/py_aether_forge/meta/research.py`, `tests/test_meta_persistence.py`

### Checkpoint 4: Meta-Progression

- [ ] Persistenz- und Forschungslogik vollständig getestet

---

## Phase 5: Pygame-CE Schlachtfeld-Engine & Visuelle Effekte

- [ ] **Task 5.1: Parallax-Sternennebel & Magie-Partikelsystem**
  - **Beschreibung:** Animierter Sternenhintergrund mit Tiefenwirkung und Vektor-/Glow-Partikelemitter für Projektile, Einschläge und Turm-Auren.
  - **Akzeptanzkriterien:** 60 FPS Partikelsimulation mit Lebensdauer, Fade-Out und Leuchteffekten.
  - **Dateien:** `src/py_aether_forge/render/starfield.py`, `src/py_aether_forge/render/particles.py`

- [ ] **Task 5.2: Kachel- & Schlachtfeld-Viewport**
  - **Beschreibung:** Rendering des Grids, schwebender Schollen, Portale, des Weltenkerns, Reichweitenkreise und Gegner-Lebensbalken.
  - **Akzeptanzkriterien:** Präzise Projektion von Grid-Koordinaten zu Bildschirm-Pixeln; flüssiges Scrolling/Kameraführung.
  - **Dateien:** `src/py_aether_forge/render/viewport.py`

- [ ] **Task 5.3: Interaktive Gefechtssteuerung & Audio-Effekte**
  - **Beschreibung:** Maus- und Tastaturinteraktion (Klick zum Platzieren, Auswählen, Fusionieren, Wellenstart per Leertaste) und Pygame Mixer Sound-Cues.
  - **Akzeptanzkriterien:** Intuitive Steuerung mit optischem Hover-Feedback, Reichweitenanzeige und Sounds.
  - **Dateien:** `src/py_aether_forge/render/battle_engine.py`, `src/py_aether_forge/render/audio.py`

### Checkpoint 5: Flüssiges Schlachtfeld

- [ ] Visuell ansprechende 60 FPS Darstellung mit Partikeln und direktem Feedback

---

## Phase 6: PySide6 Hybrid-Shell & End-to-End Polish

- [ ] **Task 6.1: Anwendungs-Shell & Hauptmenü mit Vollbild/Fenstermodus**
  - **Beschreibung:** PySide6 Hauptfenster mit Startmenü, Optionen, Beenden und F11/Button-Umschaltung für Vollbild und Fenstermodus.
  - **Akzeptanzkriterien:** Vollbild- und Fenstermodus schalten ohne Bildfehler oder Absturz um; Tastenkürzel F11 funktioniert.
  - **Dateien:** `src/py_aether_forge/app.py`, `src/py_aether_forge/ui/main_menu.py`

- [ ] **Task 6.2: Astrale Schmiede (Sanktuarium UI)**
  - **Beschreibung:** Interaktiver Forschungsbaum in PySide6 mit Tooltips, Statusanzeigen (Gesperrt, Verfügbar, Erforscht) und Splitter-Konto.
  - **Akzeptanzkriterien:** Visuell eleganter Forschungsbaum; Klicks schalten Technologien frei und persistieren sofort.
  - **Dateien:** `src/py_aether_forge/ui/sanctuary_ui.py`

- [ ] **Task 6.3: Schlachtfeld-HUD & Nahtlose PySide6/Pygame-Integration**
  - **Beschreibung:** Einbettung des Pygame-Schlachtfelds mit HUD-Overlay für Kernleben, Äther, Welle und Roguelite-Schollen-Draft.
  - **Akzeptanzkriterien:** Nahtloser Übergang Hauptmenü -> Schlachtfeld -> Draft -> Game Over / Sieg; Deutsche UI-Texte; F11 Vollbild-Support.
  - **Dateien:** `src/py_aether_forge/ui/battle_view.py`, `src/py_aether_forge/ui/hud_overlay.py`, `src/py_aether_forge/__init__.py`

### Checkpoint 6: Finale Abnahme

- [ ] Spiel startet mit `uv run py_aether_forge`
- [ ] Sämtliche Tests laufen unter `uv run pytest` grün durch
- [ ] Linter & Formatter (`uv run ruff check .`) sauber
- [ ] Vollbild- und Fenstermodus funktionieren makellos
