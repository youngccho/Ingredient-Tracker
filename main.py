import json
import re
from pathlib import Path

# ---------- Configuration ----------
JSON_PATH = Path("foodkeeper.json")

UNIT_TO_DAYS = {
    "day": 1, "days": 1,
    "week": 7, "weeks": 7,
    "month": 30, "months": 30
}

# (prefix, storage_condition, context_label)
STORAGE_GROUPS = [
    ("DOP_Pantry",      "pantry",       "from_purchase"),
    ("DOP_Refrigerate", "refrigerated", "from_purchase"),
    ("DOP_Freeze",      "frozen",       "from_purchase"),
    ("Pantry",          "pantry",       "generic"),          # fallback if present
    ("Refrigerate",     "refrigerated", "generic"),
    ("Freeze",          "frozen",       "generic"),
    ("Pantry_After_Opening",      "pantry",       "after_opening"),
    ("Refrigerate_After_Opening", "refrigerated", "after_opening"),
    ("Refrigerate_After_Thawing", "refrigerated", "after_thawing"),
    ("Freeze_After_Opening",      "frozen",       "after_opening"),  # if such fields exist
]

# ---------- Helpers ----------
def collapse_singletons(record_like):
    """
    record_like: list of single-key dicts -> one combined dict
    """
    merged = {}
    for d in record_like:
        if isinstance(d, dict):
            merged.update(d)
    return merged

def normalize_alias(s: str) -> str:
    s = s.lower().strip()
    # simple plural -> singular: carrots -> carrot (basic rule)
    if s.endswith("s") and len(s) > 3 and not s.endswith("ss"):
        s = s[:-1]
    return s

def to_days(min_val, max_val, unit):
    if min_val is None and max_val is None:
        return None
    if unit is None:
        return None
    u = unit.strip().lower()
    factor = UNIT_TO_DAYS.get(u.rstrip("s"), UNIT_TO_DAYS.get(u, None))
    if factor is None:
        return None
    # If only one end present, copy it to both
    if min_val is None and max_val is not None:
        min_val = max_val
    if max_val is None and min_val is not None:
        max_val = min_val
    if min_val is None or max_val is None:
        return None
    return int(min_val * factor), int(max_val * factor), unit

def extract_shelf_life(rec):
    results = []
    for prefix, storage, context in STORAGE_GROUPS:
        base = f"{prefix}"
        min_key = f"{base}_Min"
        max_key = f"{base}_Max"
        metric_key = f"{base}_Metric"
        # Some tip fields vary in capitalization
        tip_key_candidates = [
            f"{base}_tips", f"{base}_Tips", f"{base}_Tip", f"{base}_TIPS"
        ]
        tip_val = None
        for tk in tip_key_candidates:
            if tk in rec and rec[tk]:
                tip_val = rec[tk]
                break

        if min_key in rec or max_key in rec:
            min_val = rec.get(min_key)
            max_val = rec.get(max_key)
            unit = rec.get(metric_key)
            converted = to_days(min_val, max_val, unit)
            if converted:
                min_days, max_days, original_unit = converted
                default_days = (min_days + max_days) // 2
                results.append({
                    "storage": storage,
                    "context": context,
                    "min_days": min_days,
                    "max_days": max_days,
                    "default_days": default_days,
                    "original_range": f"{rec.get(min_key)}–{rec.get(max_key)} {original_unit}",
                    "tips": tip_val
                })
    return results

# ---------- Load & Normalize ----------
raw = json.loads(JSON_PATH.read_text())

# If top-level is a single record (list of singleton dicts), wrap it to process uniformly
if raw and isinstance(raw, list) and raw and isinstance(raw[0], dict) and len(raw[0].keys()) == 1 and any("ID" in d for d in raw):
    records_raw = [raw]  # single item scenario
elif isinstance(raw, list):
    records_raw = raw
else:
    raise ValueError("Unexpected JSON structure.")

records = []
for r in records_raw:
    if isinstance(r, list):
        merged = collapse_singletons(r)
    elif isinstance(r, dict):
        merged = r
    else:
        continue
    records.append(merged)

# ---------- Build Alias Index ----------
alias_index = {}  # alias -> list of record indices
for idx, rec in enumerate(records):
    name = rec.get("Name") or ""
    keywords = rec.get("Keywords") or ""
    alias_candidates = []
    # From name: split on commas
    for part in name.split(","):
        p = part.strip()
        if p:
            alias_candidates.append(p)
    # From keywords: split on commas
    for k in keywords.split(","):
        k = k.strip()
        if k:
            alias_candidates.append(k)
    # Normalize & deduplicate
    seen = set()
    for a in alias_candidates:
        norm = normalize_alias(a)
        if norm and norm not in seen:
            alias_index.setdefault(norm, []).append(idx)
            seen.add(norm)

# ---------- Query Loop ----------
def format_record(rec):
    lines = []
    lines.append(rec.get("Name", "Unknown Item"))
    shelf_entries = extract_shelf_life(rec)
    if not shelf_entries:
        lines.append("  (No shelf life data available in this record.)")
    else:
        # Group by storage for readability
        for e in shelf_entries:
            lines.append(
                f"  {e['storage'].capitalize()} ({e['context']}): "
                f"{e['min_days']}–{e['max_days']} days "
                f"(~{e['default_days']}d avg) "
                f"[original: {e['original_range']}]"
            )
            if e["tips"]:
                lines.append(f"      Tips: {e['tips']}")
    return "\n".join(lines)

def lookup(query):
    qn = normalize_alias(query)
    matches = alias_index.get(qn)
    if not matches:
        return None, []
    return qn, [records[i] for i in matches]

if __name__ == "__main__":
    user = input("Ingredient: ").strip()
    key, matched_records = lookup(user)
    if not matched_records:
        print("No match found for:", user)
    else:
        # If multiple records (e.g., composite), list them
        for i, rec in enumerate(matched_records, start=1):
            print(f"\nMatch {i}:\n{format_record(rec)}")
