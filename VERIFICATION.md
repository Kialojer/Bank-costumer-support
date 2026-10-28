# Verification

Date: 2026-10-28

## Executed locally

- Python compilation/import checks for all five Python modules.
- `python graph.py`: real compiled LangGraph workflow returned the fictional CDB
  scenario total R$ 5287.40.
- `python -m unittest discover -s bank-customer-support -v`: **14 tests passed**.
  Covers real graph routes in both languages, financial arithmetic, maturity
  boundaries, liquidity filters, invalid payloads, API response model, state
  isolation, support priority and optional-model success/fallback behavior.
- Generated FastAPI OpenAPI schema and validated the editable draw.io XML.

Installed versions used: LangGraph 1.0.6, FastAPI 0.128.0, Pydantic 2.12.5,
OpenAI 2.37.0. Dependency ranges are not a resolved lockfile.

## Not executed or claimed

No live OpenAI calls, real-bank connections, WhatsApp traffic, database access,
public deployment or end-to-end HTTP server/browser test. OpenAI tests use mocks;
they verify adapter behavior, not model quality or access to a model.

Financial data is synthetic. Scenario tax inputs are assumptions, not a tax-law
implementation. These checks do not certify financial suitability or regulatory
compliance.
