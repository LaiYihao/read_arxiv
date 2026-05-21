"""Paper data model for arXiv report"""

from dataclasses import dataclass, asdict
from typing import Optional, List
import json


@dataclass
class Paper:
    """ArXiv paper with scoring information"""
    arxiv_id: str
    title: str
    authors: List[str]
    abstract: str
    categories: List[str]
    published_date: str
    link: str
    matched_keywords: Optional[List[str]] = None
    score: Optional[float] = None
    review_result: Optional[dict] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_arxiv_result(cls, arxiv_entry: dict) -> "Paper":
        """Create Paper from arXiv API result"""
        return cls(
            arxiv_id=arxiv_entry["arxiv_id"],
            title=arxiv_entry["title"],
            authors=arxiv_entry.get("authors", []),
            abstract=arxiv_entry.get("abstract", ""),
            categories=arxiv_entry.get("categories", []),
            published_date=arxiv_entry.get("published_date", ""),
            link=arxiv_entry.get("link", ""),
        )
