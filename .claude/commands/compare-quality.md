Compare quality scores before and after changes: $ARGUMENTS

Usage: /project:compare-quality [baseline_file] [new_file]

If no arguments provided:
1. List available baseline files in quality_scores/ and project root
2. Ask user which baseline to compare against (or use most recent)
3. Ask for the new file to compare (or use most recent)

Then:
4. Run comparison scripts:
   - For bidding: `python3 compare_scores.py [baseline] [new]`
   - For play: `python3 compare_play_scores.py [baseline] [new]`
5. Analyze results and identify:
   - ⛔ BLOCKING regressions (>2% drop in composite, <100% legality)
   - ⚠️  Warning regressions (>5% drop in appropriateness)
   - ✅ Improvements (>2% increase)
   - 📊 Specific error categories that changed
6. Display summary table with deltas
7. Recommend: COMMIT (if no blocking issues), ITERATE (if warnings), or ROLLBACK (if blocking)

Reference: CLAUDE.md Quality Assurance Protocols section
