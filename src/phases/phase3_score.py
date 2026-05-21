"""Phase 3: Keyword scoring"""

import re
from typing import List, Tuple
from src.models.paper import Paper
from src.models.config_schema import ConfigSchema


class Phase3Score:
    """Phase 3: Score papers based on keyword matching"""

    def __init__(self, papers: List[Paper], config: ConfigSchema):
        self.papers = papers
        self.config = config

    def execute(self) -> Tuple[List[Paper], List[Paper]]:
        """Execute Phase 3: Score and categorize papers"""
        scored_papers = []

        for paper in self.papers:
            score = self._score_paper(paper)
            paper.score = score

            matched_keywords = self._get_matched_keywords(paper)
            paper.matched_keywords = matched_keywords

            if score > 0:
                scored_papers.append(paper)

        # Sort by score descending
        scored_papers.sort(key=lambda p: p.score, reverse=True)

        # Categorize
        deep_dive = [p for p in scored_papers if p.score >= self.config.deep_dive_threshold]
        quick_summary = [p for p in scored_papers if 0 < p.score < self.config.deep_dive_threshold]

        print(f"Scored papers: {len(scored_papers)} relevant / {len(self.papers)} total")
        print(f"  Deep Dive (score ≥ {self.config.deep_dive_threshold}): {len(deep_dive)}")
        print(f"  Quick Summary (0 < score < {self.config.deep_dive_threshold}): {len(quick_summary)}")

        return deep_dive, quick_summary

    def _score_paper(self, paper: Paper) -> float:
        """Calculate paper score based on keyword matching"""
        score = 0.0
        text_lower = (paper.title + " " + paper.abstract).lower()

        # Track which keywords we've already scored to avoid double-counting
        scored_keywords = set()

        for keyword in self.config.keywords:
            if keyword.term in scored_keywords:
                continue

            # Check title (1.5x weight)
            if self._contains_term(paper.title.lower(), keyword.term):
                score += keyword.weight * 1.5
                scored_keywords.add(keyword.term)
                continue

            # Check abstract (1.0x weight)
            if self._contains_term(paper.abstract.lower(), keyword.term):
                score += keyword.weight
                scored_keywords.add(keyword.term)
                continue

            # Check aliases (same weight, but don't double-count with main term)
            for alias in keyword.aliases:
                if self._contains_term(text_lower, alias):
                    if keyword.term not in scored_keywords:
                        score += keyword.weight
                        scored_keywords.add(keyword.term)
                    break

        return score

    def _get_matched_keywords(self, paper: Paper) -> List[str]:
        """Get list of matched keywords for a paper"""
        matched = []
        text_lower = (paper.title + " " + paper.abstract).lower()

        for keyword in self.config.keywords:
            if self._contains_term(text_lower, keyword.term):
                matched.append(keyword.term)
            else:
                for alias in keyword.aliases:
                    if self._contains_term(text_lower, alias):
                        matched.append(keyword.term)
                        break

        return list(set(matched))  # Remove duplicates

    @staticmethod
    def _contains_term(text: str, term: str) -> bool:
        """Check if term appears in text (case-insensitive, word boundaries)

        Uses custom word boundaries for terms containing hyphens, dots,
        or slashes to avoid \\b edge cases with non-word characters.
        """
        escaped = re.escape(term)
        # If term contains non-alphanumeric characters (hyphens, dots, slashes etc.),
        # use alphanumeric-only boundaries instead of \\b to handle them correctly
        if any(c in term for c in "-./"):
            pattern = r"(?<![a-zA-Z0-9])" + escaped + r"(?![a-zA-Z0-9])"
        else:
            pattern = r"\b" + escaped + r"\b"
        return bool(re.search(pattern, text, re.IGNORECASE))
