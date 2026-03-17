# Template Rules

The report quality depends on following the bundled templates, not on inventing a fresh layout.

## Read The Template First

Before generating HTML, read the relevant local file:

- single report: `resources/report_template.html`
- comparison report: `resources/location_report_comparison.html`

If the template cannot be read, warn the user clearly that the report is a degraded fallback version.

Prefer replacing the dedicated payload constant through `scripts/build_report.py` instead of asking the model to hand-edit many scattered HTML fragments.

## Single-Location Template

For single-location reports:

- preserve the existing tabs and overall page structure
- fill the intended containers instead of redesigning the page
- avoid adding floating summary panels over the map
- keep the existing dark-blue UI theme and white AMap base style
- replace the `const reportData = { ... };` payload rather than patching dozens of literals

The final conclusion belongs in the reserved conclusion container, not as a separate map overlay.

## Comparison Template

For multi-location comparison reports, the template is driven by JavaScript data.

Strict rule:

- do not manually rewrite the static HTML sections as the primary injection path
- replace the `const comparisonData = { ... };` object with the generated per-location data

If this rule is ignored, the content may disappear when the user switches locations in the UI.

Each location entry must include the fields expected by the template, including:

- `id`, `name`, `recommend`, `latlng`
- `score`, `grade`, `gradeClass`, `color`
- `radar`
- narrative insight fields
- flow counts and flow conclusion
- finance fields
- compliance / negotiation fields
- `reason`
- `circles`
- `pois`

## Map Data Injection

Use the script output to populate map content faithfully.

Requirements:

- convert all relevant competitor points from `top_competitors_for_map`
- include map circles for coverage / risk framing
- populate POI info with name, type, price band, distance, and rating
- avoid dropping most competitors and only keeping a few famous brands

## UI Constraints

Keep these stable unless the user explicitly asks for a redesign:

- overall dark-blue theme
- AMap base style fixed to the classic white map
- no map theme toggle
- no duplicate or misplaced legend
- no Markdown `**bold**` syntax inside HTML output

## End-User Reminder

When delivering the final HTML report, include this reminder once:

`💡 提示：如果要分享本地的 HTML 给他人，请检查源码中的 YOUR_AMAP_SEC_CODE 和 YOUR_AMAP_JSAPI_KEY 是否已替换为您的网页端 Key，否则其他人打开时地图可能无法显示。`
