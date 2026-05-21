"""arXiv Report — Main orchestrator for 5-phase pipeline"""

import argparse
import sys
from datetime import datetime, timedelta

from src.phases.phase1_config import Phase1Config
from src.phases.phase2_fetch import Phase2Fetch
from src.phases.phase3_score import Phase3Score
from src.phases.phase4_agent import Phase4Agent
from src.phases.phase5_report import Phase5Report


def main():
    parser = argparse.ArgumentParser(
        description="arXiv Report — 天体物理日报生成器"
    )
    parser.add_argument(
        "-d", "--date",
        type=str,
        default=None,
        help="Target date in YYYY-MM-DD format (default: yesterday)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.json",
        help="Path to configuration file (default: config.json)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print execution plan without calling DeepSeek API",
    )
    parser.add_argument(
        "--no-review",
        action="store_true",
        help="Skip DeepSeek API review phase",
    )

    # Use parse_known_args to tolerate extra args injected by IPython/py launcher
    args, _ = parser.parse_known_args()
    date_str = args.date or (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    try:
        print(f"\n{'='*60}")
        print(f"arXiv Report — {date_str}")
        print(f"{'='*60}\n")

        # Phase 1: Load configuration
        print("Phase 1: Loading configuration...")
        phase1 = Phase1Config(config_path=args.config, date_str=date_str)
        phase1_result = phase1.execute()
        config = phase1_result["config"]
        print(f"✓ Loaded config: {len(config.keywords)} keywords, threshold={config.deep_dive_threshold}\n")

        # Phase 2: Fetch data
        print("Phase 2: Fetching data from arXiv...")
        phase2 = Phase2Fetch(date=date_str, config=config)
        papers = phase2.execute()
        print(f"✓ Fetched {len(papers)} papers\n")

        # Phase 3: Score papers
        print("Phase 3: Scoring papers by keywords...")
        phase3 = Phase3Score(papers=papers, config=config)
        deep_dive, quick_summary = phase3.execute()
        print()

        if args.dry_run or args.no_review:
            print(f"Dry run / No review mode: skipping Phase 4 (DeepSeek API)")
            print(f"Would process:")
            print(f"  - {len(deep_dive)} Deep Dive papers")
            print(f"  - {len(quick_summary)} Quick Summary papers\n")

            # Still generate report for dry-run
            if deep_dive or quick_summary:
                print("Phase 5: Generating report...")
                phase5 = Phase5Report(
                    date=date_str,
                    deep_dive=deep_dive,
                    quick_summary=quick_summary,
                    config=config,
                )
                phase5.execute()
                print()
        else:
            # Phase 4: Agent-based review
            print("Phase 4: Processing papers with DeepSeek API...")
            phase4 = Phase4Agent(
                deep_dive_papers=deep_dive,
                quick_summary_papers=quick_summary,
                max_workers=5,
            )
            deep_dive, quick_summary = phase4.execute()
            print()

            # Phase 5: Generate report
            print("Phase 5: Generating report...")
            phase5 = Phase5Report(
                date=date_str,
                deep_dive=deep_dive,
                quick_summary=quick_summary,
                config=config,
            )
            phase5.execute()

        print(f"\n{'='*60}")
        print("✓ arXiv Report generation completed!")
        print(f"{'='*60}\n")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
