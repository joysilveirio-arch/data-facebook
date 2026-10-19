"""
Inspect the actual Facebook comments JSON dataset.

This script is the source of truth for the real schema.
It DOES NOT modify the dataset.

Usage (from project root, venv active):
    python scripts/inspect_dataset.py path/to/dataset.json
    python scripts/inspect_dataset.py path/to/dataset.json --sample 5
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------
def _flatten_keys(obj: Any, prefix: str = "", depth: int = 0, max_depth: int = 2) -> set[str]:
    """Collect top-level and one-level nested keys."""
    keys: set[str] = set()
    if depth > max_depth or not isinstance(obj, dict):
        return keys
    for k, v in obj.items():
        full = f"{prefix}{k}"
        keys.add(full)
        if isinstance(v, dict):
            keys |= _flatten_keys(v, prefix=f"{full}.", depth=depth + 1, max_depth=max_depth)
    return keys


def _is_empty(v: Any) -> bool:
    if v is None:
        return True
    if isinstance(v, str) and v.strip() == "":
        return True
    return False


def _char_class_census(texts: list[str]) -> dict[str, int]:
    """Count how many texts contain various character classes."""
    import re

    url_re = re.compile(r"https?://\S+", re.IGNORECASE)
    mention_re = re.compile(r"@\w+")
    hashtag_re = re.compile(r"#\w+")
    emoji_re = re.compile(
        "[" 
        "\U0001F300-\U0001FAFF"
        "\U0001F600-\U0001F64F"
        "\U00002600-\U000027BF"
        "\U0001F1E6-\U0001F1FF"
        "\u2764\u2665\u2666\u2663"
        "]",
        flags=re.UNICODE,
    )
    non_ascii_re = re.compile(r"[^\x00-\x7F]")

    counts = {
        "contains_url": 0,
        "contains_mention": 0,
        "contains_hashtag": 0,
        "contains_emoji": 0,
        "contains_non_ascii": 0,
        "contains_newline": 0,
    }
    for t in texts:
        if url_re.search(t):
            counts["contains_url"] += 1
        if mention_re.search(t):
            counts["contains_mention"] += 1
        if hashtag_re.search(t):
            counts["contains_hashtag"] += 1
        if emoji_re.search(t):
            counts["contains_emoji"] += 1
        if non_ascii_re.search(t):
            counts["contains_non_ascii"] += 1
        if "\n" in t:
            counts["contains_newline"] += 1
    return counts


# ---------------------------------------------------------------
# Main inspection
# ---------------------------------------------------------------
def inspect(path: Path, sample_size: int = 3) -> None:
    if not path.exists():
        print(f"[ERROR] File not found: {path}", file=sys.stderr)
        sys.exit(2)

    print("=" * 72)
    print(f"DATASET INSPECTION: {path.name}")
    print("=" * 72)

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print(f"[WARN] Top-level JSON is not a list (got {type(data).__name__}).")

    total = len(data)
    print(f"\nTotal records: {total}")

    # --- Key frequency across records ---
    key_counter: Counter[str] = Counter()
    nested_keys: set[str] = set()
    for rec in data:
        if isinstance(rec, dict):
            key_counter.update(rec.keys())
            nested_keys |= _flatten_keys(rec, max_depth=2)

    print("\n--- Top-level key frequency ---")
    for k, c in key_counter.most_common():
        pct = 100 * c / total if total else 0
        print(f"  {k:<28} {c:>6}  ({pct:5.1f}%)")

    print("\n--- Nested keys observed (depth 2) ---")
    for k in sorted(nested_keys):
        if "." in k:
            print(f"  {k}")

    # --- Missing / empty analysis ---
    print("\n--- Missing & empty value analysis ---")
    for k in key_counter:
        missing = sum(1 for rec in data if k not in rec)
        empty = sum(1 for rec in data if k in rec and _is_empty(rec.get(k)))
        print(f"  {k:<28} missing={missing:>6}  empty={empty:>6}")

    # --- text-specific analysis ---
    texts_present = [rec.get("text") for rec in data if "text" in rec]
    texts_non_empty = [t for t in texts_present if isinstance(t, str) and t.strip() != ""]
    no_text_key = sum(1 for rec in data if "text" not in rec)
    empty_text = sum(1 for t in texts_present if _is_empty(t))

    print("\n--- Text field analysis ---")
    print(f"  Records with 'text' key:         {len(texts_present)}")
    print(f"  Records WITHOUT 'text' key:      {no_text_key}")
    print(f"  Records with empty/null 'text':  {empty_text}")
    print(f"  Records with usable text:        {len(texts_non_empty)}")

    if texts_non_empty:
        lengths = [len(t) for t in texts_non_empty]
        lengths_sorted = sorted(lengths)
        n = len(lengths_sorted)
        print(f"  Text length min/median/max:      "
              f"{lengths_sorted[0]} / {lengths_sorted[n // 2]} / {lengths_sorted[-1]}")

        print("\n--- Character-class census (usable text only) ---")
        for k, v in _char_class_census(texts_non_empty).items():
            print(f"  {k:<24} {v:>6}")

        print("\n--- Language-ish hints (top tokens, no translation) ---")
        # NOT a language detector. Just shows frequent short tokens.
        from collections import Counter as C2
        tok = C2()
        for t in texts_non_empty:
            for w in t.lower().split():
                w = "".join(ch for ch in w if ch.isalpha())
                if 2 <= len(w) <= 20:
                    tok[w] += 1
        print("  (informational only)")
        for w, c in tok.most_common(15):
            print(f"    {w:<20} {c}")

    # --- Duplicates ---
    ids = [rec.get("commentId") or rec.get("id") for rec in data if isinstance(rec, dict)]
    dup_ids = [k for k, v in Counter(ids).items() if v > 1 and k]
    dup_texts = [t for t, c in Counter(texts_non_empty).items() if c > 1]
    print("\n--- Duplicate analysis ---")
    print(f"  Duplicate commentId/id values:   {len(dup_ids)}")
    print(f"  Duplicate text values:           {len(dup_texts)}")
    if dup_texts[:3]:
        print("  Example duplicated texts:")
        for t in dup_texts[:3]:
            print(f"    - {t[:60]!r}")

    # --- Categorical uniques ---
    print("\n--- Categorical uniques ---")
    for field in ("facebookId", "postTitle", "inputUrl"):
        vals = {rec.get(field) for rec in data if isinstance(rec, dict) and rec.get(field)}
        print(f"  {field:<16} unique={len(vals)}")

    genders = Counter(
        (rec.get("author") or {}).get("gender", "N/A")
        for rec in data
        if isinstance(rec, dict)
    )
    print(f"  author.gender    unique={len(genders)}")
    for g, c in genders.most_common():
        print(f"    - {g}: {c}")

    authors = Counter(
        (rec.get("author") or {}).get("name", "N/A")
        for rec in data
        if isinstance(rec, dict)
    )
    print(f"  author.name      unique={len(authors)}  (top 5)")
    for a, c in authors.most_common(5):
        print(f"    - {a}: {c}")

    # --- Label check ---
    print("\n--- Label presence ---")
    label_like = [k for k in key_counter if "label" in k.lower() or "sentiment" in k.lower()
                  or "class" in k.lower() or "category" in k.lower()]
    if label_like:
        print(f"  Possible label-like keys: {label_like}")
    else:
        print("  No obvious label column found. Manual labeling will be required.")

    # --- Sample records ---
    if sample_size > 0:
        print(f"\n--- Sample records (first {min(sample_size, total)}) ---")
        for i, rec in enumerate(data[:sample_size]):
            print(f"\n  [{i}] commentId={rec.get('commentId')!r}  date={rec.get('date')!r}")
            print(f"      author={rec.get('profileName')!r}  gender={(rec.get('author') or {}).get('gender')!r}")
            print(f"      text={rec.get('text', '<<MISSING>>')!r}")
            print(f"      facebookId={rec.get('facebookId')!r}")
            print(f"      postTitle={ (rec.get('postTitle') or '')[:60]!r}")

    # --- Warnings ---
    print("\n--- Data quality warnings ---")
    warnings: list[str] = []
    if no_text_key:
        warnings.append(f"{no_text_key} record(s) have NO `text` key (sticker/GIF-only).")
    if empty_text:
        warnings.append(f"{empty_text} record(s) have empty/whitespace `text`.")
    if dup_ids:
        warnings.append(f"{len(dup_ids)} duplicate commentId/id value(s) — enforce uniqueness on import.")
    if not label_like:
        warnings.append("No label column detected — supervised training is blocked until labeled.")
    if total < 100:
        warnings.append(f"Only {total} record(s) — stratified split may be unreliable.")
    if not warnings:
        warnings.append("None detected.")
    for w in warnings:
        print(f"  [!] {w}")

    print("\n" + "=" * 72)
    print("Inspection complete. Original file NOT modified.")
    print("=" * 72)


# ---------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect the Facebook comments dataset.")
    parser.add_argument("path", type=Path, help="Path to the JSON dataset file.")
    parser.add_argument("--sample", type=int, default=3, help="Number of sample records to print.")
    args = parser.parse_args()
    inspect(args.path, sample_size=args.sample)


if __name__ == "__main__":
    main()