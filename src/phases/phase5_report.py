"""Phase 5: Report generation"""

from datetime import datetime
from pathlib import Path
from typing import List
from src.models.paper import Paper


class Phase5Report:
    """Phase 5: Generate Markdown report"""

    def __init__(self, date: str, deep_dive: List[Paper], quick_summary: List[Paper], output_dir: str = "outputs", config=None):
        self.date = date
        self.deep_dive = deep_dive
        self.quick_summary = quick_summary
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.config = config

    def execute(self) -> str:
        """Execute Phase 5: Generate report"""
        total_papers = len(self.deep_dive) + len(self.quick_summary)

        if total_papers == 0:
            print("No relevant papers found for today.")
            return self._generate_empty_report()

        report = self._generate_report()
        report_path = self._save_report(report)
        print(f"\nReport saved to: {report_path}")
        return str(report_path)

    def _generate_report(self) -> str:
        """Generate full report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_relevant = len(self.deep_dive) + len(self.quick_summary)

        # Build keywords and scoring info
        keywords_info = ""
        if self.config:
            threshold = self.config.deep_dive_threshold
            kw_parts = []
            for kw in self.config.keywords:
                kw_parts.append(f"{kw.term}({kw.weight})")
            keywords_info = ", ".join(kw_parts)
        else:
            threshold = 8
            keywords_info = ""

        kw_threshold_line = ""
        if keywords_info:
            kw_threshold_line = f"- 关键词:{keywords_info}  /  阈值:≥ {threshold} 分 → Deep Dive\n"

        report = f"""# arXiv 天体物理日报 — {self.date}

[TOC]

## 今日概况
- 检索论文总数:{total_relevant} / 相关:{total_relevant} 篇
- Deep Dive (methodology-focus): {len(self.deep_dive)} 篇
- Quick Summary (quick): {len(self.quick_summary)} 篇
{kw_threshold_line}
---

## 深度解读

"""

        if self.deep_dive:
            for i, paper in enumerate(self.deep_dive, 1):
                report += self._format_deep_dive_entry(paper, i)
        else:
            report += "*无深度解读论文*\n\n"

        report += "\n---\n\n## 快速扫描\n\n"

        if self.quick_summary:
            for i, paper in enumerate(self.quick_summary, 1):
                report += self._format_quick_summary_entry(paper, i)
        else:
            report += "*无快速扫描论文*\n\n"

        report += f"\n---\n\n*由 arxiv-report 自动生成于 {timestamp}*\n"
        return report

    def _format_deep_dive_entry(self, paper: Paper, index: int) -> str:
        """Format a deep dive entry with full EIC assessment"""
        result = paper.review_result or {}
        review_failed = result.get("review_failed", False)
        authors_str = ", ".join(paper.authors[:3]) if paper.authors else ""
        if paper.authors and len(paper.authors) > 3:
            authors_str += " et al."
        score_str = f"{paper.score:.1f}" if paper.score else "N/A"
        keywords_str = ", ".join(paper.matched_keywords) if paper.matched_keywords else ""
        rating = "★★★★★" if paper.score and paper.score >= 15 else "★★★★☆" if paper.score and paper.score >= 10 else "★★★☆☆"

        review_mode = result.get("review_mode", "methodology-focus")
        review_note = " （摘要评审）" if result.get("is_abstract_only") else ""

        entry = f"""### [{index}] {paper.title}

- **arXiv ID**: [{paper.arxiv_id}](https://arxiv.org/abs/{paper.arxiv_id})
- **作者**: {authors_str}
- **匹配关键词**: {keywords_str}（{score_str} 分）
- **评审模式**: {review_mode}{review_note}

**相关度**: {rating}

"""

        if review_failed:
            entry += "> ⚠️ 评审失败\n\n"
        else:
            # Core contribution
            if "core_contribution" in result and result["core_contribution"]:
                entry += f"#### 核心贡献\n\n{result['core_contribution']}\n\n"

            # Method highlights
            if "method_highlight" in result and result["method_highlight"]:
                entry += f"#### 方法亮点\n\n{result['method_highlight']}\n\n"

            # Methodology quality
            if "methodology_quality" in result and result["methodology_quality"]:
                entry += f"#### 方法论质量评估\n\n{result['methodology_quality']}\n\n"

            # Relevance
            if "relevance" in result and result["relevance"]:
                entry += f"#### 与你的研究方向关联\n\n{result['relevance']}\n\n"
            elif "interest_relevance" in result and result["interest_relevance"]:
                entry += f"#### 与你的研究方向关联\n\n{result['interest_relevance']}\n\n"

            # Insights
            if "insights" in result and result["insights"]:
                entry += f"#### 可借鉴的具体内容\n\n{result['insights']}\n\n"

            # Limitations
            if "limitations" in result and result["limitations"]:
                entry += f"#### 潜在问题 & 局限性\n\n{result['limitations']}\n\n"

            # Fallback: use quick_summary fields for abstract-based deep dive
            if not any(k in result and result[k] for k in ("core_contribution", "method_highlight")):
                if "eic_assessment" in result and result["eic_assessment"]:
                    entry += f"#### EIC 评估\n\n{result['eic_assessment']}\n\n"

                if "interest_relevance" in result and result["interest_relevance"]:
                    entry += f"#### 与你的研究方向关联\n\n{result['interest_relevance']}\n\n"

                if "abstract_zh" in result and result["abstract_zh"]:
                    entry += f"#### 中文摘要\n\n{result['abstract_zh']}\n\n"

        entry += "\n"
        return entry

    def _format_quick_summary_entry(self, paper: Paper, index: int) -> str:
        """Format a quick summary entry with complete EIC assessment"""
        result = paper.review_result or {}
        review_failed = result.get("review_failed", False)
        authors_str = ", ".join(paper.authors[:3]) if paper.authors else ""
        if paper.authors and len(paper.authors) > 3:
            authors_str += " et al."
        score_str = f"{paper.score:.1f}" if paper.score else "N/A"
        keywords_str = ", ".join(paper.matched_keywords) if paper.matched_keywords else ""

        entry = f"""### [{index}] {paper.title}

- **arXiv ID**: [{paper.arxiv_id}](https://arxiv.org/abs/{paper.arxiv_id})
- **作者**: {authors_str}
- **匹配关键词**: {keywords_str}（{score_str} 分）
- **评审模式**: quick

"""

        if review_failed:
            entry += "> ⚠️ 评审失败\n\n"
        else:
            if "eic_assessment" in result and result["eic_assessment"]:
                entry += f"#### EIC 快速评估\n\n{result['eic_assessment']}\n\n"

            if "interest_relevance" in result and result["interest_relevance"]:
                entry += f"#### 与你的兴趣关联\n\n{result['interest_relevance']}\n\n"

            if "abstract_zh" in result and result["abstract_zh"]:
                entry += f"#### 中文摘要\n\n{result['abstract_zh']}\n\n"

        entry += "\n"
        return entry

    def _generate_empty_report(self) -> str:
        """Generate empty report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            f"# arXiv Report - {self.date}",
            "",
            "## Summary",
            "",
            "No relevant papers found on arXiv for today.",
            "",
            "---",
            "",
            f"*Generated by arxiv-report at {timestamp}*",
        ]
        return "\n".join(lines)

    def _save_report(self, report: str) -> Path:
        """Save report to file"""
        output_path = self.output_dir / f"arxiv-report-{self.date}.md"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report)
        return output_path
