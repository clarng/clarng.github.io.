#!/usr/bin/env python3
"""CLI tool for editing clarence.ng homepage cards."""

import os
import subprocess
import sys
import tempfile

import click

from core import (
    SITE_ROOT,
    add_card,
    content_preview,
    git_publish,
    list_images,
    load_cards,
    remove_card,
    reorder_card,
    save_cards,
    update_card,
)


@click.group()
def main():
    """Website editor for clarence.ng homepage cards."""
    pass


@main.group()
def cards():
    """Manage homepage cards."""
    pass


@cards.command("list")
def cards_list():
    """Display all cards with index, logo, and content preview."""
    data = load_cards()
    for i, card in enumerate(data):
        logo = card.get("logo", "(no logo)")
        title = card.get("title", "")
        preview = content_preview(card)
        center = " [centered]" if card.get("center") else ""
        partition = " [partition]" if card.get("partition") else ""
        click.echo(f"  [{i}] {logo}{center}{partition}")
        if title:
            click.echo(f"      Title: {title}")
        click.echo(f"      {preview}")
        click.echo()


@cards.command("add")
def cards_add():
    """Interactively add a new card."""
    images = list_images()
    if images:
        click.echo("Available images:")
        for img in images:
            click.echo(f"  {img}")
    logo = click.prompt("Logo path (e.g. /assets/img/flower.svg)", default="")
    title = click.prompt("Title (leave empty for none)", default="")
    center = click.confirm("Center this card?", default=False)
    partition = click.confirm("Add partition line?", default=False)

    click.echo("Enter content (HTML allowed). Press Ctrl-D when done:")
    content_lines = []
    try:
        while True:
            line = input()
            content_lines.append(line)
    except EOFError:
        pass
    content = "\n".join(content_lines) + "\n"

    data = load_cards()
    add_card(data, logo=logo, title=title, content=content, center=center, partition=partition)
    save_cards(data)
    click.echo(f"Card added at index {len(data) - 1}.")


@cards.command("edit")
@click.argument("index", type=int)
def cards_edit(index):
    """Edit an existing card by index."""
    data = load_cards()
    if not (0 <= index < len(data)):
        click.echo(f"Error: index {index} out of range (0-{len(data) - 1})")
        sys.exit(1)

    card = data[index]
    click.echo(f"Editing card [{index}]: {card.get('logo', '(no logo)')}")

    logo = click.prompt("Logo", default=card.get("logo", ""))
    title = click.prompt("Title", default=card.get("title", ""))
    center = click.confirm("Center?", default=card.get("center", False))
    partition = click.confirm("Partition?", default=card.get("partition", False))

    # Get existing content
    raw = card.get("content", "")
    if isinstance(raw, list):
        existing = str(raw[0]) if raw else ""
    else:
        existing = str(raw)

    editor = os.environ.get("EDITOR", "")
    if editor:
        use_editor = click.confirm(f"Edit content in {editor}?", default=True)
    else:
        use_editor = False

    if use_editor:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(existing)
            tmp = f.name
        subprocess.run([editor, tmp])
        with open(tmp, "r") as f:
            content = f.read()
        os.unlink(tmp)
    else:
        click.echo("Enter new content (HTML allowed). Press Ctrl-D when done:")
        click.echo("--- Current content ---")
        click.echo(existing)
        click.echo("--- Enter new content (or Ctrl-D to keep current) ---")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        if lines:
            content = "\n".join(lines) + "\n"
        else:
            content = None  # keep existing

    update_card(data, index, logo=logo, title=title, content=content, center=center, partition=partition)
    save_cards(data)
    click.echo(f"Card [{index}] updated.")


@cards.command("remove")
@click.argument("index", type=int)
def cards_remove(index):
    """Remove a card by index (with confirmation)."""
    data = load_cards()
    if not (0 <= index < len(data)):
        click.echo(f"Error: index {index} out of range (0-{len(data) - 1})")
        sys.exit(1)

    card = data[index]
    click.echo(f"Card [{index}]: {card.get('logo', '(no logo)')}")
    click.echo(f"  {content_preview(card)}")
    if not click.confirm("Remove this card?"):
        click.echo("Cancelled.")
        return

    remove_card(data, index)
    save_cards(data)
    click.echo(f"Card [{index}] removed.")


@cards.command("reorder")
@click.argument("from_idx", type=int)
@click.argument("to_idx", type=int)
def cards_reorder(from_idx, to_idx):
    """Move a card from one position to another."""
    data = load_cards()
    try:
        reorder_card(data, from_idx, to_idx)
    except IndexError as e:
        click.echo(f"Error: {e}")
        sys.exit(1)
    save_cards(data)
    click.echo(f"Card moved from [{from_idx}] to [{to_idx}].")


@main.command()
def preview():
    """Run Jekyll local server for preview."""
    click.echo("Starting Jekyll server...")
    subprocess.run(["bundle", "exec", "jekyll", "serve"], cwd=str(SITE_ROOT))


@main.command()
@click.option("-m", "--message", default="Update cards", help="Commit message")
def publish(message):
    """Git add, commit, and push to deploy."""
    if not click.confirm(f"Publish with message: '{message}'?"):
        click.echo("Cancelled.")
        return
    try:
        git_publish(message)
        click.echo("Published successfully!")
    except subprocess.CalledProcessError as e:
        click.echo(f"Git error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
