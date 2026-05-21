"""Phase 2: Data fetching from arXiv"""

import json
import os
import time
from pathlib import Path
from typing import List

try:
    import arxiv
except ImportError:
    print("Error: arxiv package not installed. Run: pip install arxiv", flush=True)
    arxiv = None

from src.models.paper import Paper


class Phase2Fetch:
    """Phase 2: Fetch data from arXiv API"""

    def __init__(self, date: str, config, cache_dir: str = "cache"):
        self.date = date
        self.config = config
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

    def execute(self) -> List[Paper]:
        """Execute Phase 2: Fetch papers"""
        cache_file = self.cache_dir / f"{self.date}.json"

        # Check if cache exists
        if cache_file.exists():
            print(f"Loading papers from cache: {cache_file}")
            return self._load_from_cache(cache_file)

        # Fetch from arXiv
        print(f"Fetching papers from arXiv for {self.date}...")
        papers = self._fetch_from_arxiv()

        # Save to cache
        self._save_to_cache(cache_file, papers)
        return papers

    def _fetch_from_arxiv(self) -> List[Paper]:
        """Fetch papers from arXiv API"""
        if not arxiv:
            raise RuntimeError("arxiv package not installed")

        query = self._build_query()
        papers = []
        max_retries = 3

        for attempt in range(max_retries):
            try:
                client = arxiv.Client(
                    page_size=min(self.config.max_papers_per_day, 100),
                    delay_seconds=3.0,
                    num_retries=5,
                )
                search = arxiv.Search(
                    query=query,
                    max_results=self.config.max_papers_per_day,
                    sort_by=arxiv.SortCriterion.SubmittedDate,
                )

                for paper in client.results(search):
                    papers.append({
                        "arxiv_id": paper.get_short_id(),
                        "title": paper.title,
                        "authors": [a.name for a in paper.authors],
                        "abstract": paper.summary,
                        "categories": list(paper.categories),
                        "published_date": paper.published.strftime("%Y-%m-%d") if paper.published else "",
                        "link": paper.entry_id,
                    })
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt * 5
                    print(f"Request failed (attempt {attempt + 1}/{max_retries}), retrying in {wait}s: {e}")
                    time.sleep(wait)
                else:
                    raise

        print(f"Found {len(papers)} papers")
        return [Paper.from_arxiv_result(p) for p in papers]

    def _build_query(self) -> str:
        """Build arXiv query string"""
        cat_clause = " OR ".join(f"cat:{c}" for c in self.config.arxiv_categories)
        date_compact = self.date.replace("-", "")
        date_clause = f"submittedDate:[{date_compact}0000 TO {date_compact}2359]"
        return f"({cat_clause}) AND {date_clause}"

    def _save_to_cache(self, path: Path, papers: List[Paper]) -> None:
        """Save papers to cache file"""
        data = [p.to_dict() for p in papers]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(papers)} papers to cache: {path}")

    def _load_from_cache(self, path: Path) -> List[Paper]:
        """Load papers from cache file"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [Paper.from_arxiv_result(d) for d in data]
