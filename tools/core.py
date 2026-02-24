"""Shared core for website editor: YAML I/O, card operations, and git helpers."""

import io
import os
import subprocess
import textwrap
from pathlib import Path

from ruamel.yaml import YAML

SITE_ROOT = Path(__file__).resolve().parent.parent
CARDS_PATH = SITE_ROOT / "_data" / "cards.yml"
ASSETS_IMG = SITE_ROOT / "assets" / "img"


def _yaml():
    """Create a ruamel.yaml instance configured for round-trip preservation."""
    y = YAML()
    y.preserve_quotes = True
    y.width = 4096  # prevent line wrapping
    y.indent(mapping=2, sequence=4, offset=2)
    return y


def load_cards():
    """Load cards from _data/cards.yml and return as a ruamel.yaml list."""
    y = _yaml()
    with open(CARDS_PATH, "r") as f:
        return y.load(f)


def save_cards(cards):
    """Save cards back to _data/cards.yml preserving formatting."""
    y = _yaml()
    buf = io.BytesIO()
    y.dump(cards, buf)
    # The indent settings add a 2-space indent to the top-level sequence.
    # Remove it to match the original file format.
    text = textwrap.dedent(buf.getvalue().decode())
    with open(CARDS_PATH, "w") as f:
        f.write(text)


def card_to_dict(card):
    """Convert a ruamel.yaml CommentedMap to a plain dict for JSON serialization."""
    d = {}
    for key in card:
        val = card[key]
        if hasattr(val, "items"):
            d[key] = dict(val)
        elif isinstance(val, list):
            d[key] = [str(item) for item in val]
        else:
            d[key] = val
    return d


def cards_to_dicts(cards):
    """Convert all cards to plain dicts."""
    return [card_to_dict(c) for c in cards]


def add_card(cards, logo="", title="", content="", center=False, partition=False):
    """Add a new card to the list and return it."""
    from ruamel.yaml.comments import CommentedMap
    from ruamel.yaml.scalarstring import LiteralScalarString

    card = CommentedMap()
    if logo:
        card["logo"] = logo
    if center:
        card["center"] = True
    if partition:
        card["partition"] = True
    if title:
        card["title"] = title
    if content:
        card["content"] = [LiteralScalarString(content)]
    else:
        card["content"] = [LiteralScalarString("")]
    cards.append(card)
    return card


def remove_card(cards, index):
    """Remove a card by index. Returns the removed card."""
    if 0 <= index < len(cards):
        return cards.pop(index)
    raise IndexError(f"Card index {index} out of range (0-{len(cards) - 1})")


def reorder_card(cards, from_idx, to_idx):
    """Move a card from one position to another."""
    if not (0 <= from_idx < len(cards)):
        raise IndexError(f"from index {from_idx} out of range")
    if not (0 <= to_idx < len(cards)):
        raise IndexError(f"to index {to_idx} out of range")
    card = cards.pop(from_idx)
    cards.insert(to_idx, card)


def update_card(cards, index, logo=None, title=None, content=None, center=None, partition=None):
    """Update fields of an existing card."""
    from ruamel.yaml.scalarstring import LiteralScalarString

    if not (0 <= index < len(cards)):
        raise IndexError(f"Card index {index} out of range")
    card = cards[index]
    if logo is not None:
        card["logo"] = logo
    if title is not None:
        if title:
            card["title"] = title
        elif "title" in card:
            del card["title"]
    if content is not None:
        card["content"] = [LiteralScalarString(content)]
    if center is not None:
        if center:
            card["center"] = True
        elif "center" in card:
            del card["center"]
    if partition is not None:
        if partition:
            card["partition"] = True
        elif "partition" in card:
            del card["partition"]


def list_images():
    """List available images in assets/img/."""
    if ASSETS_IMG.exists():
        return sorted(f.name for f in ASSETS_IMG.iterdir() if f.is_file())
    return []


def git_publish(message="Update cards"):
    """Stage _data/cards.yml, commit, and push."""
    cwd = str(SITE_ROOT)
    subprocess.run(["git", "add", "_data/cards.yml"], cwd=cwd, check=True)
    subprocess.run(["git", "commit", "-m", message], cwd=cwd, check=True)
    subprocess.run(["git", "push"], cwd=cwd, check=True)


def content_preview(card, max_len=80):
    """Get a short text preview of a card's content."""
    raw = card.get("content", "")
    if isinstance(raw, list):
        text = " ".join(str(item) for item in raw)
    else:
        text = str(raw)
    # Strip HTML tags for preview
    import re

    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&#x2022;", "*").replace("\n", " ").strip()
    text = re.sub(r"\s+", " ", text)
    if len(text) > max_len:
        text = text[:max_len] + "..."
    return text
