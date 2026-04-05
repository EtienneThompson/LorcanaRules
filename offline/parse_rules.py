"""
Parse the Disney Lorcana Comprehensive Rules PDF into individual rules.

Each rule starts with a hierarchical number (e.g., 1.2.3) followed by its text.
Continuation text (examples, clarifications) that doesn't start with a new number
is appended to the preceding rule.

Output: one rule per line in the format: <number>\t<text>
"""

import json
import re
import sys
from datetime import date

import pdfplumber


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using pdfplumber, preserving layout."""
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text(layout=True)
            if text:
                pages.append(text)
    return "\n".join(pages)


def parse_glossary(pdf_path: str) -> list[tuple[str, str]]:
    """
    Parse the glossary section from the PDF using character-level font data.

    Glossary terms are rendered in bold (BrandonTextCond-Bold) and definitions
    in regular weight. We group lines by vertical position, classify each line
    as bold (term) or regular (definition), and pair them up.
    """
    entries: list[tuple[str, str]] = []
    in_glossary = False
    current_term: str | None = None
    current_def_parts: list[str] = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text(layout=True) or ""
            if not in_glossary:
                # Look for "GLOSSARY" as a standalone line (not in the TOC)
                page_lines = [l.strip() for l in page_text.split("\n")]
                if "GLOSSARY" in page_lines:
                    in_glossary = True
                else:
                    continue

            # Build a mapping from vertical position to the layout-extracted
            # text line. extract_text(layout=True) preserves spaces properly.
            layout_lines = page_text.split("\n")

            # Group characters by vertical position to detect bold vs regular
            line_chars: dict[float, list[dict]] = {}
            for c in page.chars:
                if not c["text"].strip():
                    continue
                top = round(c["top"], 0)
                if top not in line_chars:
                    line_chars[top] = []
                line_chars[top].append(c)

            # Map each char-group top position to the closest layout line
            # by matching content. Build ordered list of (is_bold, text).
            glossary_lines: list[tuple[bool, str]] = []
            sorted_tops = sorted(line_chars.keys())

            # Use layout lines for readable text; char data only for bold detection
            layout_idx = 0
            for top in sorted_tops:
                chars = line_chars[top]
                # Find the matching layout line (skip blanks)
                line_text = ""
                while layout_idx < len(layout_lines):
                    candidate = layout_lines[layout_idx].strip()
                    layout_idx += 1
                    if not candidate:
                        continue
                    line_text = candidate
                    break

                if not line_text:
                    continue

                # Skip footer lines and the GLOSSARY header itself
                if (
                    line_text.startswith("disneylorcana.com")
                    or line_text.startswith("©Disney")
                    or line_text == "GLOSSARY"
                    or re.match(r"^\d+$", line_text)
                ):
                    continue

                fonts = {c["fontname"] for c in chars if c["text"].strip()}
                is_bold = all("Bold" in f for f in fonts)
                glossary_lines.append((is_bold, line_text))

            for is_bold, line_text in glossary_lines:
                if is_bold:
                    # Save previous entry
                    if current_term is not None:
                        definition = " ".join(current_def_parts)
                        entries.append((current_term, definition))
                    current_term = line_text
                    current_def_parts = []
                else:
                    # Continuation of definition
                    if current_term is not None:
                        current_def_parts.append(line_text)

    # Save the last entry
    if current_term is not None:
        definition = " ".join(current_def_parts)
        entries.append((current_term, definition))

    return entries


# Matches lines that start a new rule: e.g. "1.1.1." or "10.2." at the start
# of a line (possibly with leading whitespace). The number pattern is one or more
# groups of digits separated by dots, with a trailing dot.
RULE_NUMBER_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)+)\.\s+(.*)", re.MULTILINE
)


def is_footer_line(line: str) -> bool:
    """Return True if this line is a page footer/header to skip."""
    stripped = line.strip()
    return (
        stripped.startswith("disneylorcana.com")
        or stripped.startswith("©Disney")
        or stripped == ""
    )


TOP_LEVEL_SECTION_RE = re.compile(r"^\s*(\d+)\.\s+([A-Z][A-Z ,]+)$")


def is_section_header(line: str) -> bool:
    """Return True if this line is a top-level section header like '1. CONCEPTS'."""
    return bool(TOP_LEVEL_SECTION_RE.match(line))


TOC_ENTRY_RE = re.compile(r"^(\d+(?:\.\d+)*)\.\s+(.+)$")


def parse_toc(text: str) -> str:
    """
    Extract the table of contents as a single string.

    The TOC sits between the "CONTENTS" header and the first actual rule (1.1.1).
    Because the PDF renders the TOC in two columns, we split each line on runs
    of whitespace and extract TOC entries from each segment.
    """
    lines = text.split("\n")
    in_toc = False
    toc_entries: list[tuple[str, str]] = []

    for line in lines:
        stripped = line.strip()

        if "CONTENTS" in stripped:
            in_toc = True

        # Stop at the first actual rule (1.1.1.)
        if in_toc and re.match(r"^\s*1\.1\.1\.", stripped):
            break

        if not in_toc:
            continue

        if is_footer_line(line):
            continue

        # Split on 2+ spaces to separate two-column entries, then also
        # split on boundaries where a word is followed by a space and a
        # new numbered entry (handles single-space column gaps).
        segments = re.split(r"\s{2,}", stripped)
        expanded: list[str] = []
        for segment in segments:
            # Further split on "<non-digit> <digit>." boundary
            parts = re.split(r"(?<=[A-Za-z])\s+(?=\d+\.)", segment)
            expanded.extend(parts)
        for segment in expanded:
            segment = segment.strip()
            match = TOC_ENTRY_RE.match(segment)
            if match:
                number = match.group(1)
                title = match.group(2).strip()
                toc_entries.append((number, title))

    # Sort entries by their hierarchical number for clean ordering
    def sort_key(entry: tuple[str, str]) -> list[int]:
        return [int(x) for x in entry[0].split(".")]

    toc_entries.sort(key=sort_key)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_entries: list[tuple[str, str]] = []
    for entry in toc_entries:
        if entry[0] not in seen:
            seen.add(entry[0])
            unique_entries.append(entry)

    # Build a clean TOC string with one entry per line
    toc_lines = [f"{number}. {title}" for number, title in unique_entries]
    return "\n".join(toc_lines)


def parse_rules(text: str) -> tuple[list[tuple[str, str]], dict[str, str]]:
    """
    Parse extracted PDF text into rules and a section-title lookup.

    Returns:
        rules: list of (rule_number, rule_text) tuples
        section_titles: dict mapping every number seen (both top-level section
            headers and sub-concept headers) to its human-readable title, used
            to build ancestry chains for each rule.
    """
    lines = text.split("\n")

    rules: list[tuple[str, str]] = []
    section_titles: dict[str, str] = {}
    current_number: str | None = None
    current_text_parts: list[str] = []
    in_glossary = False
    found_first_rule = False

    for line in lines:
        # Skip footer lines
        if is_footer_line(line):
            continue

        stripped = line.strip()

        # Detect when we've entered the glossary (stop parsing rules)
        if stripped == "GLOSSARY":
            in_glossary = True
            continue

        if in_glossary:
            continue

        # Capture top-level section headers like "1. CONCEPTS" into the lookup.
        # These appear as standalone lines (nothing else on the line after the title).
        # TOC lines share the line with other content, so matching the full stripped
        # line ensures we only capture the real headers, not TOC entries.
        section_match = TOP_LEVEL_SECTION_RE.match(stripped)
        if section_match:
            section_titles[section_match.group(1)] = section_match.group(2).strip().title()
            continue

        # Try to match a rule number at the start of this line
        match = RULE_NUMBER_RE.match(stripped)
        if match:
            # Skip TOC entries: don't start parsing until we see "1.1.1"
            if not found_first_rule:
                if match.group(1) == "1.1.1":
                    found_first_rule = True
                else:
                    continue

            # Save previous rule if any
            if current_number is not None:
                rules.append((current_number, " ".join(current_text_parts)))

            current_number = match.group(1)
            rule_text = match.group(2).strip()
            current_text_parts = [rule_text]

            # If this entry has only a short title (no sentence-ending punctuation
            # and no lowercase words beyond the first), treat it as a section header
            # and record its title for ancestry lookups.
            words = rule_text.split()
            is_title_only = (
                len(words) <= 5
                and not rule_text.endswith(".")
                and not any(w[0].islower() for w in words[1:])
            )
            if is_title_only:
                section_titles[current_number] = rule_text
        elif found_first_rule and current_number is not None and stripped:
            # Skip diagram labels and annotations from card layout diagrams:
            # - All-caps lines (e.g., "READY", "CARD ORIENTATION")
            # - Numbered diagram annotations (e.g., "1       Cost & Inkwell")
            # - Standalone digits from diagram overlays (e.g., "1", "1 3 7")
            if re.match(r"^[A-Z\s]+$", stripped):
                continue
            if re.match(r"^\d+\s{2,}", stripped):
                continue
            if re.match(r"^[\d\s]+$", stripped):
                continue
            # Continuation text for the current rule
            current_text_parts.append(stripped)

    # Don't forget the last rule
    if current_number is not None:
        rules.append((current_number, " ".join(current_text_parts)))

    return rules, section_titles


def get_ancestry(number: str, section_titles: dict[str, str]) -> list[str]:
    """
    Return the ordered list of section titles that contain this rule.

    For rule "1.3.5.1", returns the titles for "1", "1.3", and "1.3.5"
    (skipping any prefix that isn't in the section_titles lookup).
    """
    parts = number.split(".")
    ancestry: list[str] = []
    for i in range(1, len(parts)):  # exclude the number itself
        prefix = ".".join(parts[:i])
        if prefix in section_titles:
            ancestry.append(section_titles[prefix])
    return ancestry


def write_rules_jsonl(
    rules: list[tuple[str, str]],
    section_titles: dict[str, str],
    output_path: str,
) -> None:
    """Write each rule as a JSON object on its own line to output_path."""
    today = date.today().isoformat()
    with open(output_path, "w", encoding="utf-8") as f:
        for rule_id, rule_text in rules:
            ancestry = get_ancestry(rule_id, section_titles)
            record = {
                "rule_id": rule_id,
                "sections": ancestry,
                "rule_text": rule_text,
                "date": today,
            }
            f.write(json.dumps(record) + "\n")


def main():
    pdf_path = "offline/data/Disney-Lorcana-Comprehensive-Rules-020526-EN-Edited.pdf"
    jsonl_path = "offline/data/rules.jsonl"

    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    if len(sys.argv) > 2:
        jsonl_path = sys.argv[2]

    text = extract_text_from_pdf(pdf_path)

    toc = parse_toc(text)
    print("=== TABLE OF CONTENTS ===")
    print(toc)
    print()

    rules, section_titles = parse_rules(text)
    print("=== RULES ===")
    for number, rule_text in rules:
        ancestry = get_ancestry(number, section_titles)
        sections = " > ".join(ancestry) if ancestry else ""
        print(f"{number}\t{sections}\t{rule_text}")
    print()

    glossary = parse_glossary(pdf_path)
    print("=== GLOSSARY ===")
    for term, definition in glossary:
        print(f"{term} - {definition}")

    write_rules_jsonl(rules, section_titles, jsonl_path)

    print(f"\n# Total rules parsed: {len(rules)}", file=sys.stderr)
    print(f"# Total glossary entries: {len(glossary)}", file=sys.stderr)
    print(f"# Rules written to: {jsonl_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
