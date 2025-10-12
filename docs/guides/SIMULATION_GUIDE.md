# Automated Bidding Analysis System

This system provides automated testing and LLM-powered analysis of your bridge bidding engine at scale.

## Overview

The system consists of two main components:

1. **simulation_enhanced.py** - Runs automated bidding simulations and exports results
2. **llm_analyzer.py** - Analyzes simulation results using Claude AI to identify bidding errors and patterns

## Quick Start

### 1. Run a Simulation

```bash
cd backend
source venv/bin/activate
python simulation_enhanced.py
```

This will:
- Generate 20 hands (5 scenario-based, 15 random)
- Run complete bidding auctions for each hand
- Export results to `simulation_results.json` and `simulation_results.txt`

**Output files:**
- `simulation_results.json` - Machine-readable format for LLM analysis
- `simulation_results.txt` - Human-readable format for quick review

### 2. Analyze with LLM

First, set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

Then run the analyzer:

```bash
python llm_analyzer.py
```

This will:
- Load the simulation results
- Send each hand to Claude for expert analysis
- Generate a comprehensive markdown report

**Output files:**
- `analysis_report.md` - Comprehensive analysis with ratings and recommendations
- `analysis_results.json` - Machine-readable analysis data

## Configuration

### simulation_enhanced.py

Edit these constants at the top of the file:

```python
DEAL_COUNT = 20         # Total number of hands to simulate
SCENARIO_COUNT = 5      # How many should use scenarios.json
OUTPUT_JSON = "simulation_results.json"
OUTPUT_TEXT = "simulation_results.txt"
```

### llm_analyzer.py

Edit these constants:

```python
INPUT_JSON = "simulation_results.json"
OUTPUT_REPORT = "analysis_report.md"
OUTPUT_JSON = "analysis_results.json"
HANDS_TO_ANALYZE = None  # Set to a number to limit (e.g., 5 for testing)
MODEL = "claude-3-5-sonnet-20241022"  # Or use "claude-3-opus-20240229" for best quality
```

## What the LLM Analysis Provides

For each hand, Claude analyzes:

1. **Overall Assessment** - Quality rating and summary
2. **Bid-by-Bid Analysis** - Correctness of each bid according to SAYC
3. **Critical Issues** - Serious errors or concerning patterns
4. **Final Contract Evaluation** - Whether the contract is optimal
5. **Teaching Points** - Lessons and common mistakes illustrated

## Example Workflow

### Testing a Specific Convention

1. Edit `scenarios.json` to focus on hands that test your convention
2. Set `SCENARIO_COUNT = 20` in `simulation_enhanced.py`
3. Run simulation
4. Review `simulation_results.txt` for quick overview
5. Run LLM analysis for detailed critique
6. Review `analysis_report.md` to identify issues

### Large-Scale Regression Testing

1. Set `DEAL_COUNT = 100` for comprehensive testing
2. Run simulation (takes ~30 seconds)
3. Set `HANDS_TO_ANALYZE = 10` to analyze a sample (saves API costs)
4. Run LLM analysis
5. Look for patterns in errors across multiple hands

### Debugging a Specific Issue

1. Create a scenario in `scenarios.json` that reproduces the issue
2. Set `DEAL_COUNT = 5` and `SCENARIO_COUNT = 5`
3. Run simulation multiple times to see if issue is consistent
4. Analyze with LLM to get expert explanation of what's wrong

## Cost Estimation

### Claude API Costs (approximate)

Using Claude 3.5 Sonnet:
- Input: ~2,000 tokens per hand
- Output: ~1,500 tokens per hand
- Cost: ~$0.01 per hand

Examples:
- 20 hands: ~$0.20
- 100 hands: ~$1.00

Using Claude 3 Opus (highest quality):
- Cost: ~$0.06 per hand
- 20 hands: ~$1.20

**Tip:** Use `HANDS_TO_ANALYZE` parameter to limit analysis during testing.

## Understanding the Output

### simulation_results.txt

Human-readable format showing:
- All four hands with HCP and distribution
- Complete auction sequence
- System explanations for each bid

Perfect for quick review and spotting obvious issues.

### analysis_report.md

Comprehensive markdown report with:
- Summary statistics
- Individual hand analyses with ratings
- Specific recommendations for each incorrect bid
- Teaching points

Open in any markdown viewer or IDE for formatted viewing.

### analysis_results.json

Machine-readable format containing:
- All analyses
- Token usage statistics
- Timestamps and metadata

Useful for programmatic processing or building dashboards.

## Troubleshooting

### "ANTHROPIC_API_KEY not set"

You need to set your API key:

```bash
export ANTHROPIC_API_KEY='sk-ant-...'
```

To make it permanent, add to your `~/.zshrc` or `~/.bashrc`:

```bash
echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.zshrc
source ~/.zshrc
```

### "simulation_results.json not found"

Run `simulation_enhanced.py` first to generate the simulation results.

### Analysis seems slow

Each hand takes ~2-5 seconds to analyze. For 20 hands, expect ~1-2 minutes total.

### API rate limits

If you hit rate limits with many hands:
- Reduce `DEAL_COUNT` or `HANDS_TO_ANALYZE`
- Add delays between API calls (modify `llm_analyzer.py`)
- Use a lower-tier model temporarily

## Advanced Usage

### Custom Analysis Prompts

Edit the `create_analysis_prompt()` function in `llm_analyzer.py` to:
- Focus on specific aspects (e.g., only competitive bidding)
- Change the analysis format
- Add custom evaluation criteria

### Batch Processing

Run multiple simulations with different configurations:

```bash
# Test opening bids
python simulation_enhanced.py
mv simulation_results.json results_openings.json

# Test competitive bidding
# (modify scenarios.json)
python simulation_enhanced.py
mv simulation_results.json results_competitive.json

# Analyze both
python llm_analyzer.py --input results_openings.json --output report_openings.md
python llm_analyzer.py --input results_competitive.json --output report_competitive.md
```

### Integration with CI/CD

Add to your test pipeline:

```bash
# Run quick smoke test
python simulation_enhanced.py
python llm_analyzer.py

# Check for critical issues in analysis_report.md
grep -i "critical\|serious\|error" analysis_report.md
```

## Best Practices

1. **Start small** - Test with 5-10 hands first to verify setup
2. **Review text output first** - Quick scan of `simulation_results.txt` before running LLM
3. **Use scenarios strategically** - Target specific conventions or edge cases
4. **Track improvements** - Save analysis reports with dates to track progress
5. **Combine with unit tests** - Use this for exploratory testing, unit tests for regression

## Future Enhancements

Potential additions:
- Automated issue extraction and categorization
- Trend analysis across multiple simulation runs
- Integration with GitHub issues for bug tracking
- Dashboard visualization of bidding quality metrics
- Comparison reports (before/after changes)

## Getting Help

If you encounter issues:
1. Check the error messages - they're usually informative
2. Verify all prerequisites are installed
3. Ensure API key is set correctly
4. Try with a smaller `DEAL_COUNT` first
5. Check the Claude API status page if analysis fails

---

**Happy Testing!** 🃏♠️♥️♦️♣️
