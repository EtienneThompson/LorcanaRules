"""
Parse allCards.json into a deduplicated JSONL file.

- Drops unused fields: externalLinks, subtypesText, fullIdentifier, artistsText
- Transforms reprintedAsIds into a list of {id, setCode} objects
- Drops reprinted cards (those referenced in another card's reprintedAsIds),
  keeping only the original printing which carries the reprint references
"""

import json
import sys
from datetime import date

FIELDS_TO_DROP = {"externalLinks", "subtypesText", "fullIdentifier", "artistsText"}


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
    written = 0

    with open(output_path, "w", encoding="utf-8") as out:
        for card in cards:
            # Drop reprinted cards — the original card carries the reprint info
            if card["id"] in reprint_ids:
                continue

            record = {k: v for k, v in card.items() if k not in FIELDS_TO_DROP}

            # Transform reprintedAsIds -> list of {id, setCode} objects
            if "reprintedAsIds" in record:
                record["reprintedAsIds"] = [
                    {"id": rid, "setCode": id_to_set[rid]}
                    for rid in record["reprintedAsIds"]
                ]

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

            out.write(json.dumps(record) + "\n")
            written += 1

    print(f"Total cards in source: {len(cards)}", file=sys.stderr)
    print(f"Dropped as reprints:   {len(reprint_ids)}", file=sys.stderr)
    print(f"Cards written:         {written}", file=sys.stderr)
    print(f"Output:                {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
