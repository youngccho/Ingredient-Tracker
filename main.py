import json
from pathlib import Path

JSON_PATH = Path("data/foodkeeper.json")

UNIT_TO_DAYS = {
    "day":1, "days":1,
    "week":7, "weeks":7,
    "month":30, "months":30
}

STORAGE_GROUPS = [
    # (prefix, storage, context)
    ("DOP_Pantry",      "pantry",       "from_purchase"),
    ("DOP_Refrigerate", "refrigerated", "from_purchase"),
    ("DOP_Freeze",      "frozen",       "from_purchase"),
    ("Pantry",          "pantry",       "generic"),
    ("Refrigerate",     "refrigerated", "generic"),
    ("Freeze",          "frozen",       "generic"),
    ("Pantry_After_Opening",      "pantry",       "after_opening"),
    ("Refrigerate_After_Opening", "refrigerated", "after_opening"),
    ("Refrigerate_After_Thawing", "refrigerated", "after_thawing"),
    ("Freeze_After_Opening",      "frozen",       "after_opening"),
]

def collapse(row):
    merged = {}
    for d in row:
        if isinstance(d, dict):
            merged.update(d)
    return merged

def normalize_alias(s: str) -> str:
    s = s.lower().strip()
    if s.endswith("s") and len(s) > 3 and not s.endswith("ss"):
        s = s[:-1]
    return s

def to_days(min_val, max_val, unit):
    if unit is None: return None
    u = unit.lower().strip()
    factor = UNIT_TO_DAYS.get(u, UNIT_TO_DAYS.get(u.rstrip("s")))
    if not factor: return None
    if min_val is None and max_val is None: return None
    if min_val is None: min_val = max_val
    if max_val is None: max_val = min_val
    return int(min_val * factor), int(max_val * factor), unit

def extract_shelf_life(rec):
    entries = []
    for prefix, storage, context in STORAGE_GROUPS:
        min_key = f"{prefix}_Min"
        max_key = f"{prefix}_Max"
        unit_key = f"{prefix}_Metric"
        if (rec.get(min_key) is None) and (rec.get(max_key) is None):
            continue
        converted = to_days(rec.get(min_key), rec.get(max_key), rec.get(unit_key))
        if not converted:
            continue
        min_d, max_d, unit = converted
        default = (min_d + max_d) // 2
        entries.append({
            "storage": storage,
            "context": context,
            "min_days": min_d,
            "max_days": max_d,
            "default_days": default,
            "original": f"{rec.get(min_key)}–{rec.get(max_key)} {unit}"
        })
    return entries

raw = json.loads(JSON_PATH.read_text())
sheets = raw.get("sheets", [])
if len(sheets) < 3:
    raise SystemExit("Product sheet (index 2) not present.")

product_sheet = sheets[2]
rows = product_sheet.get("data") or []

records = []
for row in rows:
    merged = collapse(row)
    if merged.get("Name"):
        records.append(merged)

alias_index = {}
for idx, rec in enumerate(records):
    name = rec.get("Name") or ""
    kws = rec.get("Keywords") or ""
    alias_candidates = []
    for part in name.split(","):
        p = part.strip()
        if p:
            alias_candidates.append(p)
    for kw in kws.split(","):
        kw = kw.strip()
        if kw:
            alias_candidates.append(kw)
    seen = set()
    for a in alias_candidates:
        norm = normalize_alias(a)
        if norm and norm not in seen:
            alias_index.setdefault(norm, []).append(idx)
            seen.add(norm)

def lookup(query: str):
    return alias_index.get(normalize_alias(query), [])

def show_record(rec):
    print(rec.get("Name", "(Unnamed Item)"))
    shelf = extract_shelf_life(rec)
    if not shelf:
        print("  (No shelf life durations found)")
        return
    for e in shelf:
        print(f"  {e['storage'].capitalize()} ({e['context']}): "
              f"{e['min_days']}–{e['max_days']} days (~{e['default_days']}d) [{e['original']}]")

if __name__ == "__main__":
    print(f"Loaded {len(records)} product records.")
    while True:
        q = input("\nIngredient (blank to exit): ").strip()
        if not q:
            break
        matches = lookup(q)
        if not matches:
            print("No match for:", q)
            continue
        for i, idx in enumerate(matches, 1):
            print(f"\nMatch {i}:")
            show_record(records[idx])
