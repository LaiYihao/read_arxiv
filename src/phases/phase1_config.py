"""Phase 1: Configuration loading and date determination"""

import os
from pathlib import Path
from datetime import datetime, timedelta
from src.models.config_schema import ConfigSchema


class Phase1Config:
    """Phase 1: Load configuration and determine target date"""

    def __init__(self, config_path: str = None, date_str: str = None):
        self.config_path = config_path or "config.json"
        self.date_str = date_str or (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    def execute(self) -> dict:
        """Execute Phase 1"""
        # Validate date format
        try:
            datetime.strptime(self.date_str, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: {self.date_str}. Use YYYY-MM-DD.")

        # Load configuration
        config = self._load_config()

        return {
            "date": self.date_str,
            "config": config,
        }

    def _load_config(self) -> ConfigSchema:
        """Load configuration from file or use default"""
        config_path = Path(self.config_path)

        if config_path.exists():
            try:
                return ConfigSchema.from_json(str(config_path))
            except Exception as e:
                print(f"Warning: Failed to load config from {config_path}: {e}")
                print("Using default configuration.")
                return ConfigSchema.get_default()
        else:
            return ConfigSchema.get_default()
