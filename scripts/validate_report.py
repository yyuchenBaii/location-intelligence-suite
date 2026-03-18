import sys
from pathlib import Path


def _read_text(path_str):
    path = Path(path_str).resolve()
    return path.read_text(encoding="utf-8")


def validate_single(html):
    required = [
        ("tabs-header", "missing tabs header"),
        ("switchTab(", "missing tab switch logic"),
        ("const reportData =", "missing reportData payload"),
        ("id=\"tab-macro\"", "missing macro tab"),
        ("id=\"tab-compete\"", "missing compete tab"),
        ("id=\"tab-finance\"", "missing finance tab"),
        ("id=\"tab-compliance\"", "missing compliance tab"),
        ("id=\"ui-global-conclusion-content\"", "missing conclusion container"),
        ("id=\"map-legend\"", "missing map legend"),
    ]
    return [message for needle, message in required if needle not in html]


def validate_compare(html):
    required = [
        ("tabs-header", "missing tabs header"),
        ("switchTab(", "missing tab switch logic"),
        ("const comparisonData =", "missing comparisonData payload"),
        ("id=\"loc-switcher\"", "missing location switcher"),
        ("id=\"tab-macro\"", "missing macro tab"),
        ("id=\"tab-compete\"", "missing compete tab"),
        ("id=\"tab-finance\"", "missing finance tab"),
        ("id=\"tab-compliance\"", "missing compliance tab"),
        ("id=\"ui-global-conclusion-content\"", "missing conclusion container"),
        ("id=\"map-legend\"", "missing map legend"),
    ]
    return [message for needle, message in required if needle not in html]


def main(argv):
    if len(argv) != 3:
        print("Usage: python scripts/validate_report.py <single|compare> <report.html>", file=sys.stderr)
        return 1

    mode, html_path = argv[1], argv[2]
    html = _read_text(html_path)
    errors = validate_single(html) if mode == "single" else validate_compare(html) if mode == "compare" else ["mode must be single or compare"]

    if errors:
        print("validate_report failed:", file=sys.stderr)
        for item in errors:
            print(f"- {item}", file=sys.stderr)
        return 1

    print(str(Path(html_path).resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
