"""Atomic save/load system for persistent game progression."""

import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SaveData:
    """Persistent player profile data."""

    total_astral_shards: int = 0
    highest_wave: int = 0
    unlocked_hybrids: set[str] = field(default_factory=set)
    unlocked_research_nodes: set[str] = field(default_factory=lambda: {"root_affinity"})
    core_health_bonus: int = 0
    starting_aether_bonus: int = 0


class SaveSystem:
    """Handles reading and atomic writing of profile save data."""

    def __init__(self, save_path: Path | None = None) -> None:
        if save_path is None:
            home = Path.home()
            self.save_path = home / ".aether_forge" / "profile.json"
        else:
            self.save_path = save_path

    def load(self) -> SaveData:
        """Loads save data from disk, or returns fresh defaults if file doesn't exist."""
        if not self.save_path.exists():
            return SaveData()

        try:
            with open(self.save_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            return SaveData(
                total_astral_shards=raw.get("total_astral_shards", 0),
                highest_wave=raw.get("highest_wave", 0),
                unlocked_hybrids=set(raw.get("unlocked_hybrids", [])),
                unlocked_research_nodes=set(raw.get("unlocked_research_nodes", ["root_affinity"])),
                core_health_bonus=raw.get("core_health_bonus", 0),
                starting_aether_bonus=raw.get("starting_aether_bonus", 0),
            )
        except (json.JSONDecodeError, OSError):
            # Fallback to defaults on read error
            return SaveData()

    def save(self, data: SaveData) -> None:
        """Atomically saves progression data to disk."""
        self.save_path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "total_astral_shards": data.total_astral_shards,
            "highest_wave": data.highest_wave,
            "unlocked_hybrids": sorted(data.unlocked_hybrids),
            "unlocked_research_nodes": sorted(data.unlocked_research_nodes),
            "core_health_bonus": data.core_health_bonus,
            "starting_aether_bonus": data.starting_aether_bonus,
        }

        # Atomic write pattern: write to tmp file in same directory, then rename
        dir_name = self.save_path.parent
        with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False, encoding="utf-8") as tf:
            json.dump(payload, tf, indent=2)
            tmp_path = tf.name

        os.replace(tmp_path, self.save_path)
