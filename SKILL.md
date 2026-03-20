---
name: location-scout-ultimate
description: Use for commercial site selection, multi-location comparison, district exploration, and reverse workflows that must combine AMap-backed data, upstream AMap skills when available, fallback local adapters, and the bundled HTML report templates.
---

# Location Scout Ultimate

Use this skill when the user wants a commercial real-estate style site-selection assessment, competitor scan, multi-location comparison, vague district exploration, or reverse recommendation.

The value of this skill is not generic analysis. It is a strict workflow:

1. Route the request into the correct scenario.
2. Prefer upstream AMap skills when available; use local scripts only as fallback adapters.
3. Normalize all upstream results into one provider-agnostic contract before analysis.
4. Follow the bundled HTML templates instead of inventing a new layout.
5. Clearly separate confirmed API facts from model inference.

## First Response

Before doing analysis, perform a short preflight:

1. check whether upstream AMap skills are available in the environment
2. check whether `AMAP_WEB_KEY` is available
3. if the task will end in a full HTML report, also verify whether the JS map placeholders can be replaced with the user's real web key and security code

Target upstream skills:

- `amap-lbs-skill`: https://ai.skillatlas.cn/skills/amap-maps
- `amap-jsapi-skill`: https://ai.skillatlas.cn/skills/amap-jsapi-skill

If either upstream skill is missing, do not pretend it was installed automatically.

- explain that this orchestration skill works best when those upstream skills are already installed
- provide the install links above
- if the user wants to continue immediately, use the local Python adapters as fallback where possible

Do not block the user unnecessarily when fallback scripts can complete the job.

Required env vars for full real-data HTML delivery:

- `AMAP_WEB_KEY`
- `AMAP_JSAPI_KEY`
- `AMAP_SEC_CODE`

- If the key is missing, tell the user that real AMap-backed analysis is unavailable and offer two paths:
  - provide the key so the skill can fetch real location data
  - continue in demo mode with clearly labeled mock data
- If the user chooses demo mode, do not run the scripts. Make it explicit that all numeric results are illustrative.
- If the key exists, continue with real-data mode.

## Route The Request

Classify the request into one of these four scenarios before generating a report:

- `single-defense`: one concrete address or coordinate plus business type
- `multi-compare`: multiple candidate locations to compare
- `fuzzy-explore`: no exact location yet, only budget / city / business intent
- `reverse-leasing`: an idle storefront that needs a recommended business type

See [references/routing-and-output.md](references/routing-and-output.md) for the detailed routing rules, required follow-up questions, and expected deliverable shape for each scenario.

## Upstream Policy

This skill is an orchestration layer, not the preferred place to reimplement generic AMap access.

If upstream skills such as `amap-lbs-skill` or `amap-jsapi-skill` are available in the environment:

- use them first for geocoding, POI search, routing, or map artifacts
- normalize their outputs into the unified upstream contract
- only use the local Python scripts if the upstream skills are unavailable, unsupported, or fail

If they are not available:

- say so plainly
- give the install links
- continue with fallback local adapters if the user still wants the result now

Do not imply that installing this skill automatically installs those upstream skills unless the platform explicitly guarantees that behavior.

Do not let downstream business analysis depend directly on provider-specific field names.

See [references/upstream-output-contract.md](references/upstream-output-contract.md).

## Real Data Workflow

When working in real-data mode and the location has been identified, do not invent numeric facts. Run the local scripts in this order:

1. If the user gives a vague address or mall name, resolve it first:
   `python scripts/resolve_location.py "<query>" "<city>"`
2. Run location context:
   `python scripts/fetch_location_context.py "<lng,lat>"`
3. Run the relevant POI scan:
   - point scan: `python scripts/fetch_amap_poi.py "<lng,lat>" "<business_keyword>"`
   - district scan: `python scripts/fetch_amap_poi.py "<business_keyword>" --mode text --adcode <adcode>`
   - bounded commercial body scan: `python scripts/fetch_amap_poi.py "<lng,lat>" "<business_keyword>" --mode polygon --polygon "<polyline>"`

After raw data collection, normalize the result into a unified contract:

- `python scripts/build_upstream_contract.py contract.json --context-path context.json --poi-path poi.json --lnglat "<lng,lat>"`

If raw data came from upstream AMap skills instead of local scripts, convert those skill outputs into the same contract before continuing.

If a script fails, a path is wrong, or the API returns insufficient data, explain the limitation to the user instead of fabricating numbers.

See [references/data-contracts.md](references/data-contracts.md) for:

- which output fields must be quoted directly
- which conclusions are allowed only as inference
- how to handle uncertainty in the report

## Report Generation Rules

Every full assessment should end in an HTML report, not just a plain Markdown summary.

Do not freehand-edit large sections of HTML when the report can be generated from structured data.

Before generating any HTML, read the relevant local template:

- single-location report: `resources/report_template.html`
- multi-location comparison: `resources/location_report_comparison.html`

If the template cannot be read, warn the user that the report will be a degraded fallback HTML version.

Do not casually redesign the UI. Prefer filling the existing template structure and reserved containers.

See [references/template-rules.md](references/template-rules.md) for:

- required template-reading behavior
- single-report injection rules
- strict multi-location `locationData` replacement rules
- map data injection requirements
- final reminder text about JSAPI key / security code

Use [references/report-payloads.md](references/report-payloads.md), [references/upstream-output-contract.md](references/upstream-output-contract.md), and the local builder:

1. gather upstream facts from upstream skills or fallback local scripts
2. normalize to one contract JSON per location
3. run `python scripts/assemble_report_payload.py single spec.json payload.json` or `python scripts/assemble_report_payload.py compare spec.json payload.json`
4. run `python scripts/build_report.py single payload.json output.html` or `python scripts/build_report.py compare payload.json output.html`
5. if build validation fails, fix the payload or template issue and rebuild; do not deliver the broken HTML
6. return the absolute output path

For new single-location specs, prefer:

- `upstream_contract_path`

For new compare specs, prefer:

- `locations[].upstream_contract_path`

Success means the final HTML passes template-structure validation. A file that does not preserve the tabbed layout or required payload markers is not an acceptable deliverable.

## Output Standard

Preferred delivery order:

1. write an HTML file locally and return the absolute path
2. if file writing is blocked, output complete HTML source

Do not return meaningless `localhost` links.

Before final output, run through the quality checks in [references/report-checklist.md](references/report-checklist.md).

## Style

Maintain a professional commercial real-estate tone. Be concise, specific, and numerically grounded. Avoid hype when presenting conclusions; the strength of the report should come from the data, the structure, and the template fidelity.
