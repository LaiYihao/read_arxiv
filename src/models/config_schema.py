"""Configuration schema for arXiv report"""

import json
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Keyword:
    """Keyword with weight and aliases"""
    term: str
    weight: int
    aliases: List[str]


@dataclass
class ConfigSchema:
    """Configuration schema for arXiv report"""
    keywords: List[Keyword]
    deep_dive_threshold: int
    arxiv_categories: List[str]
    max_papers_per_day: int

    @classmethod
    def from_json(cls, path: str) -> "ConfigSchema":
        """Load configuration from JSON file"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        keywords = [
            Keyword(
                term=k["term"],
                weight=k["weight"],
                aliases=k.get("aliases", [])
            )
            for k in data.get("keywords", [])
        ]

        return cls(
            keywords=keywords,
            deep_dive_threshold=data.get("deep_dive_threshold", 8),
            arxiv_categories=data.get("arxiv_categories", ["astro-ph.SR", "astro-ph.HE", "astro-ph.GA"]),
            max_papers_per_day=data.get("max_papers_per_day", 200),
        )

    @staticmethod
    @staticmethod
    def get_default() -> "ConfigSchema":
        """Get default configuration"""
        return ConfigSchema(
            keywords=[
                Keyword("blue loop", 10, ["blue loops"]),
                Keyword("X-ray binary", 8, ["X-ray binaries", "XRB", "HMXB", "LMXB"]),
                Keyword("mass transfer", 6, ["Roche lobe overflow", "RLOF"]),
                Keyword("binary evolution", 5, ["binary star evolution", "close binary"]),
                Keyword("stellar evolution", 4, ["stellar models", "stellar structure"]),
                Keyword("common envelope", 5, ["common-envelope", "CE evolution"]),
                Keyword("accretion", 3, ["accretion disk", "accreting"]),
                Keyword("supernova", 3, ["supernovae", "core-collapse"]),
                Keyword("neutron star", 3, ["neutron stars", "pulsar"]),
                Keyword("black hole", 3, ["black holes", "BH"]),
            ],
            deep_dive_threshold=8,
            arxiv_categories=["astro-ph.SR", "astro-ph.HE", "astro-ph.GA"],
            max_papers_per_day=200,
        )
