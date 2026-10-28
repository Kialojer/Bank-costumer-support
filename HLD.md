# High-Level Design — Bank Customer Support

Author: Kiarash Torabi  
Implementation: small, local educational prototype.

## Components and boundaries

| Component | Responsibility |
| --- | --- |
| main.py | HTTP adapter; accepts validated JSON and returns a typed reply |
| graph.py | Transient state, deterministic routing and explicit graph edges |
| products.py | Fictional CDB/LCI/LCA facts and financial scenario calculation |
| llm.py | Optional explanation of supplied facts; no account or tool access |
| Client | Chooses product/scenario/language; optionally supplies recent history |

No customer database is needed. Unlike the telecom sample, the bank demo receives
an explicitly selected fictional offer rather than choosing a random customer.

## Request flow

1. Client sends message, pt-BR/en, fictional product_id, scenario and optional history.
2. Pydantic validates the boundary before LangGraph receives anything.
3. classify routes to support, simulate, explain or greeting.
4. Support returns a simulated handoff flag and ends; no model call.
5. Simulation calls the Python calculator; explanation reads the fictional catalog.
6. With USE_OPENAI=true, an optional node sends bounded facts to OpenAI.
7. Missing key/provider errors preserve the deterministic answer with mode=fallback.
8. The API returns reply, route, mode, optional simulation and support metadata.

There is no model-selected tool loop or autonomous product selection. The graph
determines which node executes. The optional model only explains the supplied facts.

## Scenario and money

Amount: R$ 1–1,000,000. Horizon: 1–730 integer days. Assumed tax: 0–30%.
The product field, not free text, selects one of the three fictional offers.
Math uses a fixed effective annual rate over calendar days/365. Tax is a scenario
input applied to gain. No actual tax treatment, fees, IOF, inflation, credit risk
or reinvestment is modeled. Before unlocking or after maturity, no withdrawal
estimate is produced. Filters are not a suitability assessment.

## State and privacy

State exists only for one graph invocation. No checkpointer, database, session
store or application-level chat logs. Client-supplied history is at most six
messages, each up to 2,000 characters, restricted to user/assistant roles.
The latest question is limited to 1,500 nonblank characters.
No name, CPF, bank login or account number is requested.

Only the optional model mode transmits questions, supplied history and fictional
scenario facts to OpenAI. store=False does not promise zero provider retention.
Prompt rules are not a complete security boundary. Do not use real personal data.
External tracing is not configured and should remain disabled for private inputs.

## Errors and limits

Invalid payloads: FastAPI/Pydantic HTTP 422.
Unknown products and unsupported languages: rejected at the boundary.
Provider failure: local template response and explicit mode=fallback.
Human support: response flag, no ticket or real transfer.
Keyword routing is deliberately basic and can misclassify unusual messages.
Template mode cannot answer arbitrary questions or use history contextually.

## Deployment scope and future adapters

Only localhost execution is documented. No real WhatsApp, bank feed, UI,
database, authentication, rate limiter, trading or cross-selling is implemented.
Future WhatsApp ingress must verify signatures, deduplicate events, resolve an
authorized identity and separately implement outbound sending. A real catalog
adapter must supply provenance and freshness. These integrations are outside the
current diagram and are not claimed as completed.

See README.md for local commands and VERIFICATION.md for actual checks.
