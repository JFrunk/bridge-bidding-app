Run comprehensive baseline quality score testing workflow:

1. Check current branch (should be on main/development)
2. Run bidding quality score: `python3 backend/test_bidding_quality_score.py --hands 500 --output baseline_$(date +%Y%m%d_%H%M%S).json`
3. Run play quality score: `python3 backend/test_play_quality_integrated.py --hands 500 --level 8 --output play_baseline_$(date +%Y%m%d_%H%M%S).json`
4. Display summary of scores with key metrics:
   - Bidding: Legality, Appropriateness, Composite
   - Play: Legality, Success Rate, Composite
5. Save baseline files to quality_scores/ directory (create if not exists)
6. Update quality_scores/README.md with new baseline entry

Do NOT modify any code. This is purely for establishing baseline metrics.

Reference: CLAUDE.md Quality Assurance Protocols section
