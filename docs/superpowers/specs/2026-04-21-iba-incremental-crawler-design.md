# IBA Incremental University Scraper Design

## Problem
The scraper currently processes many Karachi universities in one run. The required behavior is incremental: process one university at a time (starting with Institute of Business Administration University), generate schema-aligned CSVs for that one university, then repeat for the next university in a later run.

## Scope
In scope:
- General one-by-one script mode with explicit university target.
- Per-run output package containing `universities.csv`, `programs.csv`, and `admission_requirements.csv`.
- Firecrawl + Crawl4AI usage in the same run.
- Fuzzy university resolution with explicit matched-name reporting.

Out of scope:
- Multi-university batch orchestration.
- Shared global IDs across different runs.

## CLI and Runtime Contract
Primary command:

`python DataScraping/merge_karachi_universities.py --university "<requested name>" --city Karachi`

Optional:
- `--output-dir <path>` to override default package location.

Default output path:
- `DataScraping/output/<slugified-matched-university-name>/`

## Architecture
1. **University seed collection (Firecrawl)**
   - Scrape HEC recognized list.
   - Filter by target city/province (Karachi/Sindh by default).
2. **University resolution**
   - Normalize and fuzzy-match user input to HEC candidates.
   - Require confidence above threshold; otherwise fail fast.
   - Emit selected match (requested name, matched official name, score).
3. **University enrichment**
   - Scrape selected HEC detail page for website, sector, founded year.
   - Pull ranking maps (UniRanks, QS) and attach available ranking values.
4. **Program/admission extraction**
   - Firecrawl `/v1/map` for domain URL discovery.
   - Select admission/program-relevant URLs via keyword scoring.
   - Crawl selected URLs with Crawl4AI.
   - Fallback to Firecrawl `/v1/scrape` markdown when Crawl4AI misses key page content.
5. **CSV assembly**
   - Build schema-ordered rows.
   - Write one package with deterministic per-run IDs.
   - Validate column order and FK linkage before final success output.

## Data Model and IDs
Per-run IDs are local and deterministic:
- `universities.csv`: exactly one row, `id=1`.
- `programs.csv`: `id=1..N`, `university_id=1`.
- `admission_requirements.csv`: `id=1..N`, `program_id` referencing `programs.id`.

Missing values remain empty strings and rows are retained.

## Output Files
Inside each run package:
- `universities.csv`
- `programs.csv`
- `admission_requirements.csv`
- `run_summary.json` (matched name, confidence score, URL sample, row counts, warnings)

## Error Handling
- **Hard fail** when HEC list or target university match is unavailable.
- **Soft fail** on individual site/page fetch failures; continue with remaining URLs.
- Mark run as partial in `run_summary.json` when extraction succeeded with warnings.
- Never silently switch to a different university if confidence threshold is not met.

## Test and Validation Strategy
- Keep extraction logic in pure functions for deterministic behavior.
- Keep network wrappers isolated for straightforward mocking.
- Post-write validation in script:
  - exact column order for all three CSVs,
  - `programs.university_id` references existing university row,
  - `admission_requirements.program_id` references existing program rows.

## Initial Execution Target
First run target:
- `--university "institute of business administration university"`

Expected result:
- one self-contained CSV package for IBA only, with all available program and admission rows extracted from its site ecosystem.
