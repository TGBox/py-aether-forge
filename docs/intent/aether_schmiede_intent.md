# Statement of Intent: Die Äther-Schmiede

## Vision & Ziel

Ein taktisches Astral-Fantasy Tower-Defense-Spiel in Python mit Elementar-Fusion (Element TD / Warcraft-3-Hommage) und dynamischer Plattform-Expansion via Roguelite-Draft im schwebenden Äther.

## Eckdaten & Architekturentscheidungen

| Dimension | Spezifikation |
| :--- | :--- |
| **Ergebnis (Outcome)** | Vollwertiges 2D Tower-Defense mit strategischer Wegverlängerung, Elementar-Turmfusion und persistenter Meta-Progression. |
| **Zielgruppe (User)** | TD- und Roguelite-Fans, die Spaß an Labyrinthbau (Mazing), Elementarsynergien und strategischem Ausbau haben. |
| **Technischer Stack** | **PySide6** (Anwendungs-Shell, Hauptmenü, Astrale Schmiede Forschungsbaum, Fenster- und Vollbildmodus) + **Pygame-CE** (performante 60-FPS-Schlachtfeld-Engine mit Partikeln, Grid-System und A*-Pathfinding). |
| **Spielfeld & Wegfindung** | Schwebendes 2D-Kachel-Raster im Astralraum. Chaos-Schwärme strömen aus Portalen zum astralen Weltenkern und nutzen dynamisches A*-Pathfinding über begehbare Pfade. |
| **Map-Expansion** | Roguelite-Draft nach jeder Welle: Auswahl aus 3 zufälligen Schollen-Fragmenten (verschiedene Formen, Turmplätze, Portalpunkte) zum Andocken an offene Kanten. |
| **Turm-Arsenal** | 4 Grundelemente (Feuer, Eis, Arkan, Natur). Im Gefecht zu Hybriden fusionierbar (z. B. Frostfeuer, Dampf, Plasma), sobald das Rezept in der Schmiede erforscht wurde. |
| **Meta-Progression** | „Die Astrale Schmiede“: Persistente Astral-Splitter aus Runs schalten im Forschungsbaum neue Hybrid-Rezepte, Schollentypen und Kern-Upgrades dauerhaft frei. |
| **Grafik & Audio** | Top-Down Astral-Glow: Draufsicht, Parallax-Sternennebel, leuchtende Partikeleffekte (Projektile, Feuer/Eis-Auren) und dynamische Sound-Effekte. |
| **Erfolgskriterien** | 60 FPS, vollständige Spielschleife, responsive Kachel-Interaktion, saubere Wegfindung, Fenster- & Vollbildmodus, hohe Testabdeckung (`pytest`). |
| **Out of Scope** | 3D-Rendering, Netzwerk-Multiplayer, freies Einheiten-Mikromanagement jenseits von Turm-Prioritäten. |
