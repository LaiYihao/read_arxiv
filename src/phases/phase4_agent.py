"""Phase 4: Agent-based review using DeepSeek API"""

import os
import subprocess
import time
from typing import List, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.models.paper import Paper
from src.api.deepseek import DeepSeekClient


class Phase4Agent:
    """Phase 4: Process papers using DeepSeek API"""

    def __init__(self, deep_dive_papers: List[Paper], quick_summary_papers: List[Paper], max_workers: int = 5):
        self.deep_dive_papers = deep_dive_papers
        self.quick_summary_papers = quick_summary_papers
        self.max_workers = max_workers
        self.client = DeepSeekClient()
        self.cache_dir = Path(".cache/arxiv")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def execute(self) -> Tuple[List[Paper], List[Paper]]:
        """Execute Phase 4: Review papers"""
        print(f"\nProcessing {len(self.deep_dive_papers)} Deep Dive papers...")
        self._process_deep_dive_batch()

        print(f"\nProcessing {len(self.quick_summary_papers)} Quick Summary papers...")
        self._process_quick_summary_batch()

        return self.deep_dive_papers, self.quick_summary_papers

    def _process_deep_dive_batch(self) -> None:
        """Process Deep Dive papers in batches"""
        batch_size = 50
        for i in range(0, len(self.deep_dive_papers), batch_size):
            batch = self.deep_dive_papers[i:i+batch_size]
            self._process_papers_parallel(batch, review_type="deep_dive")

    def _process_quick_summary_batch(self) -> None:
        """Process Quick Summary papers in batches"""
        batch_size = 50
        for i in range(0, len(self.quick_summary_papers), batch_size):
            batch = self.quick_summary_papers[i:i+batch_size]
            self._process_papers_parallel(batch, review_type="quick_summary")

    def _process_papers_parallel(self, papers: List[Paper], review_type: str) -> None:
        """Process papers in parallel"""
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._review_paper, paper, review_type): paper
                for paper in papers
            }

            for future in as_completed(futures):
                paper = futures[future]
                try:
                    result = future.result()
                    paper.review_result = result
                    status = "✓" if result and "error" not in result else "✗"
                    print(f"{status} {paper.arxiv_id}: {paper.title[:50]}...")
                except Exception as e:
                    print(f"✗ {paper.arxiv_id}: Error - {e}")
                    paper.review_result = {"error": str(e), "review_failed": True}

    def _review_paper(self, paper: Paper, review_type: str) -> dict:
        """Review a single paper"""
        try:
            if review_type == "deep_dive":
                return self._deep_dive_review(paper)
            else:
                return self._quick_summary_review(paper)
        except Exception as e:
            print(f"Error reviewing {paper.arxiv_id}: {e}")
            return {"error": str(e), "review_failed": True}

    def _deep_dive_review(self, paper: Paper) -> dict:
        """Generate Deep Dive review (abstract-based by default)"""
        # Skip TeX download (too slow/unreliable), use abstract-based review
        try:
            result = self.client.quick_summary(
                paper_title=paper.title,
                paper_abstract=paper.abstract,
                matched_keywords=paper.matched_keywords or [],
                arxiv_id=paper.arxiv_id,
                authors=paper.authors or [],
                is_deep_dive=True,
            )
            result["review_mode"] = "methodology-focus"
            result["is_abstract_only"] = True
            return result
        except Exception as e:
            print(f"  Error in deep dive review for {paper.arxiv_id}: {e}")
            return {"error": str(e), "review_failed": True}

    def _quick_summary_review(self, paper: Paper) -> dict:
        """Generate Quick Summary review"""
        result = self.client.quick_summary(
            paper_title=paper.title,
            paper_abstract=paper.abstract,
            matched_keywords=paper.matched_keywords or [],
            arxiv_id=paper.arxiv_id,
            authors=paper.authors or [],
            is_deep_dive=False,
        )
        result["review_mode"] = "quick"
        return result

    def _download_paper_content(self, arxiv_id: str, max_retries: int = 3) -> str:
        """Download paper content from arXiv with retry logic"""
        cache_file = self.cache_dir / f"{arxiv_id}.txt"

        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

        for attempt in range(max_retries):
            try:
                # Download tar.gz
                tar_path = self.cache_dir / f"{arxiv_id}.tar.gz"
                extract_dir = self.cache_dir / arxiv_id

                url = f"https://arxiv.org/src/{arxiv_id}"
                result = subprocess.run(
                    ["curl", "-sL", "--connect-timeout", "5", "--max-time", "15", "-o", str(tar_path), url],
                    timeout=20,
                    capture_output=True,
                )

                if result.returncode != 0:
                    raise Exception(f"curl failed: {result.stderr.decode()}")

                # Extract tar
                extract_dir.mkdir(exist_ok=True)
                subprocess.run(
                    ["tar", "-xzf", str(tar_path), "-C", str(extract_dir)],
                    timeout=10,
                    capture_output=True,
                )

                # Read content from tex files
                content = self._extract_tex_content(extract_dir)
                if content:
                    with open(cache_file, "w", encoding="utf-8") as f:
                        f.write(content)
                    return content

            except Exception as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt * 3
                    print(f"  Retry {attempt + 1}/{max_retries} for {arxiv_id} in {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"  Failed to download {arxiv_id} after {max_retries} attempts")

        return ""

    @staticmethod
    def _extract_tex_content(extract_dir: Path) -> str:
        """Extract text content from TeX files"""
        content = []
        for tex_file in extract_dir.glob("*.tex"):
            try:
                with open(tex_file, "r", encoding="utf-8", errors="ignore") as f:
                    content.append(f.read())
            except Exception:
                pass
        return "\n".join(content)
