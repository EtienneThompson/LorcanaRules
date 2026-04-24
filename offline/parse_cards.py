"""
Parse allCards.json into a deduplicated JSONL file.

- Drops unused fields: externalLinks, subtypesText, fullIdentifier, artistsText
- Also drops duplicate fields: version, simpleName, fullTextSections, fullText, abilities
- Drops reprinted cards (those referenced in another card's reprintedAsIds),
  keeping only the original printing which carries the reprint references
- Merges specialty reprints and promos with the same fullName into one record,
  with per-printing details captured in a `variants` array and foilTypes merged
"""

import json
import sys
from datetime import date

FIELDS_TO_DROP = {
    "externalLinks",
    "subtypesText",
    "fullIdentifier",
    "artistsText",
    "version",
    "simpleName",
    "fullTextSections",
    "fullText",
    "abilities",
}

# Fields that are printing-specific and belong in each variant object
VARIANT_KEYS = {
    "id", "code", "number", "rarity", "setCode", "setName",
    "foilTypes", "images", "flavorText", "artists", "baseId",
    "promoGrouping", "promoSource", "promoSourceCategory", "varnishType",
}


def merge_group(records: list[dict]) -> dict:
    """Merge multiple printings of the same card (same fullName) into one record.

    The base card (no baseId) provides all canonical top-level fields.
    foilTypes is merged into a deduplicated union.
    A `variants` list captures every printing's per-variant fields.
    Relationship fields (promoIds, reprintedAsIds) are dropped since the
    variants list captures the same information.
    """
    # Base card is the canonical printing — no baseId field
    base = next((r for r in records if "baseId" not in r), records[0])

    # Start from the base card; remove relationship fields subsumed by variants
    merged = {k: v for k, v in base.items() if k not in {"promoIds", "reprintedAsIds"}}

    # Merge foilTypes: deduplicated union, preserving encounter order
    seen: set[str] = set()
    merged_foil: list[str] = []
    for r in records:
        for ft in r.get("foilTypes", []):
            if ft not in seen:
                seen.add(ft)
                merged_foil.append(ft)
    merged["foilTypes"] = merged_foil

    # variants list captures per-printing fields for every record
    merged["variants"] = [
        {k: r[k] for k in VARIANT_KEYS if k in r}
        for r in records
    ]

    return merged


def main():
    input_path = "offline/data/allCards.json"
    output_path = "offline/data/cards.jsonl"

    if len(sys.argv) > 1:
        input_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]

    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    cards: list[dict] = data["cards"]
    sets: dict[str, dict] = data["sets"]

    # Build a lookup from setCode -> setName
    set_name: dict[str, str] = {code: s["name"] for code, s in sets.items()}

    # Build a lookup from id -> setCode for transforming reprintedAsIds
    id_to_set: dict[int, str] = {c["id"]: c["setCode"] for c in cards}

    # Collect all ids that are reprints (referenced in another card's reprintedAsIds).
    # These are the duplicate entries we want to drop.
    reprint_ids: set[int] = {
        rid
        for c in cards
        if "reprintedAsIds" in c
        for rid in c["reprintedAsIds"]
    }

    today = date.today().isoformat()

    # First pass: build all records (same logic as before)
    records: list[dict] = []

    for card in cards:
        # Drop reprinted cards — the original card carries the reprint info
        if card["id"] in reprint_ids:
            continue

        record = {k: v for k, v in card.items() if k not in FIELDS_TO_DROP}

        record["setName"] = set_name.get(record["setCode"], "")

        # Build completeCardText from the original card data (before field drops)
        # so subtypesText is still available. Omit stat lines when not present.
        text_parts = [card["fullName"]]
        if card.get("subtypesText"):
            text_parts.append(card["subtypesText"])
        if card.get("cost") is not None:
            inkable = "Inkable" if card.get("inkwell") else "Uninkable"
            text_parts.append(f"Cost: {card['cost']} {inkable}")
        if card.get("fullText"):
            text_parts.append(card["fullText"])
        if card.get("strength") is not None:
            text_parts.append(f"Strength: {card['strength']}")
        if card.get("willpower") is not None:
            text_parts.append(f"Willpower: {card['willpower']}")
        if card.get("lore") is not None:
            text_parts.append(f"Lore: {card['lore']}")
        record["completeCardText"] = (
            "\n".join(text_parts)
            .replace("⬡", "ink")
            .replace("◊", "lore")
            .replace("¤", "strength")
            .replace("⟳", "exert")
            .replace("⛉", "willpower")
            .replace("◉", "inkwell")
            .replace("\u2013", "\u2014")  # en dash -> em dash
        )

        record["date"] = today
        records.append(record)

    # Second pass: group by fullName and merge same-name cards
    # (promos and specialty reprints of the same card)
    groups: dict[str, list[dict]] = {}
    for r in records:
        groups.setdefault(r["fullName"], []).append(r)

    written = 0
    with open(output_path, "w", encoding="utf-8") as out:
        for group in groups.values():
            if len(group) == 1:
                out.write(json.dumps(group[0]) + "\n")
            else:
                out.write(json.dumps(merge_group(group)) + "\n")
            written += 1

    print(f"Total cards in source:  {len(cards)}", file=sys.stderr)
    print(f"Dropped as reprints:    {len(reprint_ids)}", file=sys.stderr)
    print(f"Pre-merge records:      {len(records)}", file=sys.stderr)
    print(f"Records after merge:    {written}", file=sys.stderr)
    print(f"Output:                 {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
