# Systemspezifikation: Die Äther-Schmiede

## 1. Objective (Zielsetzung)

„Die Äther-Schmiede“ ist ein taktisches Tower-Defense-Spiel in einer astralen Fantasy-Welt. Der Spieler verteidigt den astralen Weltenkern gegen einfallende Chaos-Schwärme auf schwebenden Plattformen im Äther.
Zentrale Alleinstellungsmerkmale:

- **Map-Expansion via Roguelite-Draft:** Am Ende jeder Welle wählt der Spieler aus 3 Plattform-Schollen und dockt sie an bestehende Kanten an, wodurch Pfade verlängert, Portale neu positioniert und neue Turmplätze geschaffen werden.
- **Element-TD-Fusion:** Vier Grundelemente (Feuer, Eis, Arkan, Natur) werden platziert und zu mächtigen Hybriden (Frostfeuer, Dampf, Plasma, Schlamm usw.) fusioniert.
- **Die Astrale Schmiede (Meta-Progression):** Außerhalb der Matches werden gesammelte Astral-Splitter im Forschungsbaum investiert, um dauerhaft neue Hybrid-Baupläne und Boni freizuschalten.
- **Desktop-Qualität:** Saubere Hybrid-Architektur (PySide6 Shell + Pygame-CE Renderer), Fenster- & Vollbildmodus (F11), responsive 60 FPS.

---

## 2. Tech Stack & Werkzeuge

| Komponente | Technologie / Paket | Begründung |
| :--- | :--- | :--- |
| **Sprache** | Python 3.11+ | Typ-Annotationen, Enums, Performance |
| **Paketmanager** | `uv` | Moderner Standard gemäß Workspace-Regeln |
| **Anwendungs-Shell & UI** | `PySide6` (Qt 6) | Hauptmenü, Forschungsbaum-Dialoge, Einstellungen, Fenster/Vollbild |
| **Gefechts-Engine** | `pygame-ce` (Community Edition) | 60 FPS Game-Loop, Kachel-Rendering, Partikelsystem, Kollision & Audio |
| **Linter / Formatter** | `ruff` | Schnell, strikt, Zeilenlänge 100 |
| **Test-Suite** | `pytest` | Schnelle TDD-Validierung der gesamten Spiel- und Wirtschaftssimulation |

---

## 3. Ausführbare Befehle

```bash
# Abhängigkeiten installieren & synchronisieren
uv sync

# Tests ausführen
uv run pytest -v

# Linter & Format-Check
uv run ruff check .
uv run ruff format --check .

# Spiel starten
uv run py_aether_forge
```

---

## 4. Projektstruktur

```text
py-aether-forge/
├── .agents/                    # Coding-Regeln & Skills
├── docs/                       # Dokumentation
│   ├── intent/                 # Intent-Definitionen
│   └── spec/                   # Spezifikationen
├── src/
│   └── py_aether_forge/
│       ├── __init__.py         # Paket-Root
│       ├── __main__.py         # Startpunkt
│       ├── app.py              # PySide6 Shell, Window Management (Fullscreen/Windowed)
│       ├── config.py           # Konstanten, Farben, Taktung, Bildschirmauflösungen
│       ├── core/               # Reine Spiellogik (vollständig headless testbar)
│       │   ├── grid.py         # 2D Kachel-Raster, Kanten, Schollen-Verwaltung
│       │   ├── pathfinding.py  # A*-Wegfindung vom Portal zum Kern
│       │   ├── economy.py      # Äther-Staub (Gold), Kern-Leben, Astral-Splitter
│       │   ├── state.py        # Spielstatus (Vorbereitung, Welle, Draft, Game Over)
│       │   └── wave_spawner.py # Wellen-Definitionen, Spacing, Skalierung
│       ├── towers/             # Turm-System & Fusion
│       │   ├── elements.py     # Basis- und Hybrid-Elemente (Enums, Status-Effekte)
│       │   ├── tower.py        # Turm-Datenmodell, Reichweite, Feuerrate
│       │   ├── targeting.py    # Ziel-Prioritäten: FIRST, LAST, CLOSEST, STRONGEST, WEAKEST
│       │   └── fusion.py       # Rezeptmatrix (z. B. Feuer + Eis -> Frostfeuer)
│       ├── enemies/            # Chaos-Schwärme
│       │   ├── creep.py        # Gegner-Instanz, HP, Rüstung, Speed, Debuff-Handler
│       │   └── types.py        # Gegnertypen: Läufer, Golem (Tank), Astralschwarm (Fast)
│       ├── expansion/          # Plattform-Drafting
│       │   ├── platform.py     # Schollen-Layouts (Formen, Slots, Portale)
│       │   └── drafter.py      # 3-Karten-Draft Generator & Validierung von Andockstellen
│       ├── meta/               # Persistenz & Astrale Schmiede
│       │   ├── research.py     # Forschungsbaum, Knoten-Kosten, Freischalt-Status
│       │   └── save_system.py  # Atomares Speichern/Laden von Benutzer-Fortschritt (JSON)
│       ├── render/             # Pygame-CE Renderer
│       │   ├── viewport.py     # Pygame Surface, Kamera, Koordinaten-Transformation
│       │   ├── particles.py    # Magische Partikeleffekte (Glow, Blitze, Funken)
│       │   └── starfield.py    # Parallax-Sternenhintergrund
│       └── ui/                 # PySide6 & HUD Widgets
│           ├── main_menu.py    # Startbildschirm
│           ├── sanctuary_ui.py # Astrale Schmiede UI (Forschungsbaum)
│           ├── battle_view.py  # PySide6 Widget mit eingebetteter/synchronisierter Pygame-Loop
│           └── hud_overlay.py  # Leben, Äther-Ressourcen, Welle, Bau-Auswahl
├── tests/                      # Pytest Test-Suite (TDD)
│   ├── test_grid_pathfinding.py
│   ├── test_economy_waves.py
│   ├── test_tower_fusion.py
│   ├── test_platform_draft.py
│   └── test_meta_persistence.py
└── pyproject.toml              # Projektkonfiguration mit uv
```

---

## 5. Architektur & Datenmodelle

### 5.1 Kachel-Raster & Schollen (`core/grid.py` & `expansion/platform.py`)

- Spielfeld besteht aus einem diskreten Grid (z. B. 32x32 Pixel Kacheln).
- Kacheltypen: `VOID` (Äther-Abgrund), `PLATFORM_WALK` (Begehbarer Weg), `PLATFORM_BUILD` (Turmplattform), `CORE` (Weltenkern), `PORTAL` (Einfallstor).
- Schollen (`PlatformShard`) sind Kachel-Muster (z. B. 3x3 oder 4x4), die an bestehende Schollen-Kanten angedockt werden müssen.
- **Invariante:** Eine neue Scholle oder ein Turmbau darf den Pfad zwischen mindestens einem aktiven Portal und dem Weltenkern niemals komplett versperren.

### 5.2 A*-Wegfindung (`core/pathfinding.py`)

- Gegner bewegen sich entlang von Kachelzentren auf `PLATFORM_WALK`-Kacheln.
- Wenn eine Scholle angebaut wird, berechnet der A*-Algorithmus den kürzesten Pfad neu.
- Jeder Gegner speichert seinen Wegpunkt-Pfad und interpoliert seine Position zeitbasiert mit `dt`.

### 5.3 Element- & Turm-Matrix (`towers/elements.py` & `towers/fusion.py`)

- **4 Grundelemente:**
  - `FEUER`: Hoher Direktschaden, Verbrennungs-DoT.
  - `EIS`: Verlangsamung, Kälte-Debuff.
  - `ARKAN`: Schnelle Angriffsrate, Rüstungsdurchdringung / Splash.
  - `NATUR`: Gift-DoT, Kettenreaktion / Ranken-Verwurzelung.
- **Hybrid-Türme (Beispiele):**
  - `FEUER + EIS` = **Frostfeuer-Monument** (Flächenverlangsamung + Kälteschock).
  - `FEUER + ARKAN` = **Plasma-Obelisk** (Durchdringende Strahlen mit hohem Einzelschaden).
  - `EIS + NATUR` = **Gletscher-Wurzel** (Hohe Frostverlangsamung + Fesselung).
  - `ARKAN + NATUR` = **Astral-Sporen** (Wandernde arkane Giftwolken).
  - `FEUER + NATUR` = **Dampf-Geysir** (Druckwellen-Schaden mit Rückstoß).

### 5.4 Roguelite-Schollen-Draft (`expansion/drafter.py`)

- Am Ende einer Welle wechselt das Spiel in den `DRAFT`-Zustand.
- 3 Optionen werden generiert:
  1. *Scholle A:* Fokus auf Turmbauplätze (z. B. 4 Bauplätze, 2 Wegkacheln).
  2. *Scholle B:* Wegverlängerung (z. B. Schlangenpfad, verlängert Laufzeit der Gegner um +8 Felder).
  3. *Scholle C:* Runen-Scholle (z. B. +15% Reichweite für darauf gebaute Türme oder Äther-Bonus).
- Der Spieler wählt ein Fragment und platziert es per Maus an einer gültigen Kante.

### 5.5 Die Astrale Schmiede (`meta/research.py`)

- Runs bringen permanente **Astral-Splitter** (basierend auf überlebten Wellen und besiegten Elite-Gegnern).
- Forschungs-Knoten schalten:
  - Neue Hybrid-Rezepte (z. B. „Schalte Plasma-Obelisk frei“).
  - Neue Schollen-Formen für den Draft.
  - Startboni (z. B. +2 Weltenkern-Leben, +50 Start-Äther).
- Daten werden in `~/.aether_forge/save_data.json` atomar gespeichert.

---

## 6. Code-Stil & Konventionen

- **Sprachen-Trennung:**
  - Variablen, Funktionsnamen, Klassen, Bezeichner und Code-Kommentare auf **Englisch**.
  - Sämtliche Texte der Benutzeroberfläche (Menüs, Tooltips, Statusanzeigen, Buttons) auf **Deutsch**.
- **Typsicherheit:** Alle Funktionen und Methoden müssen typisiert sein (`-> None`, `-> list[Tile]`).
- **Data Encapsulation:** Nutze `dataclass` für reine Datenträger (`Tile`, `PlatformShard`, `CreepData`, `TowerStats`).
- **Simulations-Unabhängigkeit:** Die Spiellogik in `core/` darf keine harten Abhängigkeiten zu Pygame-Rendering haben, damit sie mit `pytest` headless und blitzschnell getestet werden kann.

---

## 7. Test-Strategie (TDD)

Gemäß `/test-driven-development` schreiben wir Tests vor bzw. parallel zur Implementierung:

1. `test_grid_pathfinding.py`:
   - Validiert Kachelplatzierung, Nachbarschaftsberechnung und Kanten-Andocken.
   - Validiert A*-Pfadfindung und Verhindern von Pfad-Blockaden.
2. `test_tower_fusion.py`:
   - Prüft Upgrade-Kosten, Element-Kombinationen und Fehlverhalten bei gesperrten Hybriden.
   - Prüft Targeting-Prioritäten (FIRST, STRONGEST etc.).
3. `test_economy_waves.py`:
   - Prüft HP-Wachstum der Wellen, Belohnungsauszahlung und Lebensabzug bei Leaks.
4. `test_platform_draft.py`:
   - Validiert Zufallsgenerierung von 3 Optionen und Andock-Validierung.
5. `test_meta_persistence.py`:
   - Validiert Laden, Speichern, Splitter-Ausgabe und Freischalt-Zustände.

---

## 8. Projekt-Grenzen (Boundaries)

- **Immer tun:**
  - Vollbild (F11 / Button) und Fenstermodus unterstützen.
  - Tests vor größeren Commits mit `pytest` verifizieren.
  - Saubere Trennung zwischen Headless-Core und UI/Rendering.
- **Erst nachfragen:**
  - Grundlegende Änderungen an den 4 Hauptelementen oder dem A*-Pfadkonzept.
  - Hinzufügen weiterer schwerer Drittanbieter-Bibliotheken.
- **Niemals tun:**
  - Pygame-Renderaufrufe tief in die Core-Spiellogik verflechten.
  - UI-Texte auf Englisch mischen.
  - Fehlgeschlagene Tests einfach löschen oder auskommentieren.

---

## 9. Success Criteria (Erfolgskriterien)

1. `uv run py_aether_forge` startet die Anwendung in einem eleganten PySide6-Hauptmenü mit nahtlosem Wechsel ins Spielfeld.
2. Vollbild- und Fenstermodus lassen sich fehlerfrei umschalten.
3. Kacheln, schwebende Schollen, Türme und Gegner laufen bei stabilen 60 FPS mit flüssiger Wegfindung.
4. Nach jeder Welle erscheint der Schollen-Draft und erweitert das Spielfeld valide.
5. Türme können platziert, angeklickt und bei freigeschaltetem Rezept zu Hybriden fusioniert werden.
6. Astral-Splitter werden gespeichert und können in der „Astralen Schmiede“ ausgegeben werden.
7. Alle Unit- und Integrationstests laufen unter `pytest` grün durch.
