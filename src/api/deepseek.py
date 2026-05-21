"""DeepSeek API client using official OpenAI SDK"""

import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI


class DeepSeekClient:
    """Client for DeepSeek API using official OpenAI SDK"""

    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "")
        self.api_base = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com").rstrip("/")
        self.model_flash = os.getenv("DEEPSEEK_MODEL_FLASH", "deepseek-v4-flash")
        self.model_pro = os.getenv("DEEPSEEK_MODEL_PRO", "deepseek-v4-pro")

        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY not set in environment or .env file")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_base,
        )

    def _call(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        max_tokens: int = 2048,
        reasoning_effort: str = "high",
        enable_thinking: bool = False,
    ) -> str:
        """Call DeepSeek API using OpenAI SDK"""
        extra_body = {}
        if enable_thinking:
            extra_body["thinking"] = {"type": "enabled"}

        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            stream=False,
            max_tokens=max_tokens,
            reasoning_effort=reasoning_effort,
            extra_body=extra_body if extra_body else None,
        )
        return response.choices[0].message.content

    def deep_dive_review(
        self,
        paper_title: str,
        paper_abstract: str,
        paper_content: str,
        matched_keywords: List[str],
        arxiv_id: str,
        authors: List[str] = None,
    ) -> dict:
        """Generate deep dive review for a paper"""
        system_prompt = """你是一位天体物理期刊主编 (Editor-in-Chief, EIC)，同时兼任方法论评审专家。你的任务是通读论文全文，从以下角度产出结构化的深度评审报告。

评审维度：
1. **核心贡献** - 论文的主要科学创新点
2. **方法亮点** - 使用的新方法或改进之处
3. **方法论质量评估** - 研究设计、数值方法/数据分析、统计处理的严谨性
4. **与研究方向关联** - 与双星演化、恒星物理、致密天体等领域的关联
5. **可借鉴的具体内容** - 对自己研究的启发和可复用方法
6. **潜在问题 & 局限性** - 论文存在的不足或局限

输出格式为结构化 JSON。

所有描述内容使用中文。论文标题、作者名、arXiv ID、学术术语保留英文。"""

        authors_str = ", ".join(authors) if authors else ""
        user_content = f"""请深度评审这篇论文：

**标题**: {paper_title}
**arXiv ID**: {arxiv_id}
{f"**作者**: {authors_str}" if authors_str else ""}
**匹配关键词**: {', '.join(matched_keywords)}

**摘要**:
{paper_abstract}

**全文**:
{paper_content[:8000]}...（省略）

请以 JSON 格式返回评审结果，包含以下字段：
- summary (string): 一句话总结
- core_contribution (string): 核心贡献（150-300字）
- method_highlight (string): 方法亮点（列举3-5个要点，用有序列表）
- methodology_quality (string): 方法论质量评估（包含研究设计、数值方法/数据分析、统计处理三个方面的逐一点评，以及总体严谨性星级评分 ★★★★☆）
- relevance (string): 与双星演化/恒星物理/致密天体研究方向的关联
- insights (string): 可借鉴的具体内容（列举3-5个要点）
- limitations (string): 潜在问题 & 局限性（列举3-6个要点）
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        response = self._call(
            model=self.model_pro,
            messages=messages,
            max_tokens=4096,
            reasoning_effort="high",
            enable_thinking=True,
        )

        # Parse JSON response
        return self._parse_json_response(response)

    def _parse_json_response(self, response: str) -> dict:
        """Robustly parse JSON from LLM response, handling markdown wrapping"""
        import re

        # Try direct parse first
        try:
            result = json.loads(response)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code blocks
        patterns = [
            r'```(?:json)?\s*\n?(.*?)\n?```',  # ```json ... ```
            r'```(.*?)```',                       # ``` ... ```
        ]
        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                try:
                    result = json.loads(match.group(1).strip())
                    if isinstance(result, dict):
                        return result
                except json.JSONDecodeError:
                    continue

        # Try to find and parse a JSON object directly
        brace_start = response.find('{')
        brace_end = response.rfind('}')
        if brace_start != -1 and brace_end > brace_start:
            try:
                return json.loads(response[brace_start:brace_end + 1])
            except json.JSONDecodeError:
                pass

        # Fallback: return raw response with error flag
        return {
            "raw_response": response[:500],
            "review_failed": True,
        }

    def quick_summary(
        self,
        paper_title: str,
        paper_abstract: str,
        matched_keywords: List[str],
        arxiv_id: str,
        authors: List[str] = None,
        is_deep_dive: bool = False,
    ) -> dict:
        """Generate quick summary for a paper.

        When is_deep_dive=True, returns full methodology review fields
        (core_contribution, method_highlight, methodology_quality,
        insights, limitations) in addition to eic_assessment.
        """

        authors_str = ", ".join(authors) if authors else ""

        if is_deep_dive:
            system_prompt = """你是一位天体物理期刊主编 (Editor-in-Chief, EIC)，同时兼任方法论评审专家。你的任务是通读论文摘要，从以下角度产出结构化的深度评审报告。

评审维度：
1. **核心贡献** - 论文的主要科学创新点
2. **方法亮点** - 使用的新方法或改进之处
3. **方法论质量评估** - 研究设计、数值方法/数据分析、统计处理的严谨性，含星级评分 ★★★★☆
4. **与研究方向关联** - 与双星演化、恒星物理、致密天体等领域的关联
5. **可借鉴的具体内容** - 对自己研究的启发和可复用方法
6. **潜在问题 & 局限性** - 论文存在的不足或局限

输出格式为结构化 JSON。
所有描述内容使用中文。论文标题、作者名、arXiv ID、学术术语保留英文。"""

            user_content = f"""请深度评审这篇论文（基于摘要）：

**标题**: {paper_title}
**arXiv ID**: {arxiv_id}
{f"**作者**: {authors_str}" if authors_str else ""}
**匹配关键词**: {', '.join(matched_keywords)}

**摘要**:
{paper_abstract}

请以 JSON 格式返回评审结果，包含以下字段：
- eic_assessment (string): EIC 总体评估（100-200字）
- core_contribution (string): 核心贡献（100-200字）
- method_highlight (string): 方法亮点（列举2-4个要点，用有序列表）
- methodology_quality (string): 方法论质量评估（含星级评分 ★★★★☆）
- relevance (string): 与双星演化/恒星物理/致密天体研究方向的关联
- insights (string): 可借鉴的具体内容（列举2-4个要点）
- limitations (string): 潜在问题 & 局限性（列举1-3个要点）
- interest_relevance (string): 与你的兴趣关联 — 高/中等/低（一句话说明原因）
- abstract_zh (string): 中文摘要（100-200字）
"""

            max_tokens = 4096
            model = self.model_pro
        else:
            system_prompt = """你是一位天体物理期刊 Editor-in-Chief (EIC)，负责快速评估 arXiv 论文。

基于题目、摘要和匹配关键词，生成结构化的快速评估（EIC 快速评估 + 与兴趣关联 + 中文摘要）。

所有描述内容使用中文。论文标题、作者名、arXiv ID、学术术语保留英文。"""

            user_content = f"""请快速评估这篇论文：

**标题**: {paper_title}
**arXiv ID**: {arxiv_id}
{f"**作者**: {authors_str}" if authors_str else ""}
**匹配关键词**: {', '.join(matched_keywords)}

**摘要**:
{paper_abstract}

请以 JSON 格式返回评估结果，包含以下字段：
- eic_assessment (string): EIC 快速评估（80-150字，评价科学贡献、方法质量和潜在影响）
- interest_relevance (string): 与你的兴趣关联 — 高/中等/低（一句话说明原因）
- abstract_zh (string): 中文摘要（80-120字，2-3句）
- recommendation (string): 建议阅读价值（low/medium/high）
"""

            max_tokens = 2048
            model = self.model_flash

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        response = self._call(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            reasoning_effort="high" if is_deep_dive else "medium",
            enable_thinking=is_deep_dive,
        )

        # Parse JSON response
        return self._parse_json_response(response)
