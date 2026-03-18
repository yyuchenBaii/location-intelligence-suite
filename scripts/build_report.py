import json
import os
import sys
from pathlib import Path

from validate_report import validate_compare, validate_single


ROOT = Path(__file__).resolve().parent.parent
SINGLE_TEMPLATE = ROOT / "resources" / "report_template.html"
COMPARE_TEMPLATE = ROOT / "resources" / "location_report_comparison.html"
MAP_KEY_PLACEHOLDER = "YOUR_AMAP_JSAPI_KEY"
MAP_SEC_PLACEHOLDER = "YOUR_AMAP_SEC_CODE"


def _read_json(path_str):
    path = Path(path_str).resolve()
    return json.loads(path.read_text(encoding="utf-8"))


def _replace_const(source, const_name, payload):
    start_token = f"const {const_name} = "
    start = source.find(start_token)
    if start == -1:
        raise ValueError(f"Failed to locate const {const_name}")

    brace_start = source.find("{", start)
    if brace_start == -1:
        raise ValueError(f"Failed to locate object start for {const_name}")

    depth = 0
    in_string = None
    escaped = False
    end = None

    for idx in range(brace_start, len(source)):
        ch = source[idx]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == in_string:
                in_string = None
            continue

        if ch in ("'", '"'):
            in_string = ch
            continue
        if ch == "{":
            depth += 1
            continue
        if ch == "}":
            depth -= 1
            if depth == 0:
                end = idx
                break

    if end is None:
        raise ValueError(f"Failed to locate object end for {const_name}")

    semicolon = source.find(";", end)
    if semicolon == -1:
        raise ValueError(f"Failed to locate trailing semicolon for {const_name}")

    replacement = f"const {const_name} = {json.dumps(payload, ensure_ascii=False, indent=8)};"
    return source[:start] + replacement + source[semicolon + 1 :]


def _inject_map_keys(source, allow_missing=False):
    jsapi_key = os.environ.get("AMAP_JSAPI_KEY")
    sec_code = os.environ.get("AMAP_SEC_CODE")
    if not jsapi_key or not sec_code:
        if allow_missing:
            return source
        missing = []
        if not jsapi_key:
            missing.append("AMAP_JSAPI_KEY")
        if not sec_code:
            missing.append("AMAP_SEC_CODE")
        raise ValueError(f"Missing required map env vars: {', '.join(missing)}")

    return source.replace(MAP_KEY_PLACEHOLDER, jsapi_key).replace(MAP_SEC_PLACEHOLDER, sec_code)


def build_single(payload, allow_missing_map_keys=False):
    template = SINGLE_TEMPLATE.read_text(encoding="utf-8")
    template = _inject_map_keys(template, allow_missing=allow_missing_map_keys)
    return _replace_const(template, "reportData", payload)


def build_compare(payload, allow_missing_map_keys=False):
    template = COMPARE_TEMPLATE.read_text(encoding="utf-8")
    template = _inject_map_keys(template, allow_missing=allow_missing_map_keys)
    return _replace_const(template, "comparisonData", payload)


def main(argv):
    allow_missing_map_keys = False
    args = argv[1:]
    if "--allow-missing-map-keys" in args:
        allow_missing_map_keys = True
        args = [arg for arg in args if arg != "--allow-missing-map-keys"]

    if len(args) != 3:
        print(
            "Usage: python scripts/build_report.py [--allow-missing-map-keys] <single|compare> <payload.json> <output.html>",
            file=sys.stderr,
        )
        return 1

    mode, payload_path, output_path = args[0], args[1], args[2]
    try:
        payload = _read_json(payload_path)

        if mode == "single":
            html = build_single(payload, allow_missing_map_keys=allow_missing_map_keys)
        elif mode == "compare":
            html = build_compare(payload, allow_missing_map_keys=allow_missing_map_keys)
        else:
            print("Mode must be single or compare", file=sys.stderr)
            return 1

        output = Path(output_path).resolve()
        output.write_text(html, encoding="utf-8")
        errors = validate_single(html) if mode == "single" else validate_compare(html)
        if errors:
            output.unlink(missing_ok=True)
            raise ValueError("validation failed after build: " + "; ".join(errors))
        print(str(output))
        return 0
    except Exception as exc:
        print(f"build_report failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
