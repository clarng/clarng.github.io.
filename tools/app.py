#!/usr/bin/env python3
"""Flask web UI for editing clarence.ng homepage cards."""

import json

from flask import Flask, jsonify, render_template, request, send_from_directory

from core import (
    ASSETS_IMG,
    SITE_ROOT,
    add_card,
    cards_to_dicts,
    git_publish,
    list_images,
    load_cards,
    remove_card,
    reorder_card,
    save_cards,
    update_card,
)

app = Flask(__name__)


@app.route("/assets/<path:filename>")
def serve_assets(filename):
    """Serve static assets from the Jekyll site root."""
    return send_from_directory(str(SITE_ROOT / "assets"), filename)


@app.route("/")
def index():
    cards = load_cards()
    images = list_images()
    return render_template("index.html", cards=cards_to_dicts(cards), images=images)


@app.route("/api/cards", methods=["GET"])
def api_cards_get():
    cards = load_cards()
    return jsonify(cards_to_dicts(cards))


@app.route("/api/cards", methods=["POST"])
def api_cards_add():
    data = request.json
    cards = load_cards()
    add_card(
        cards,
        logo=data.get("logo", ""),
        title=data.get("title", ""),
        content=data.get("content", ""),
        center=data.get("center", False),
        partition=data.get("partition", False),
    )
    save_cards(cards)
    return jsonify({"ok": True, "count": len(cards)})


@app.route("/api/cards/<int:idx>", methods=["PUT"])
def api_cards_update(idx):
    data = request.json
    cards = load_cards()
    try:
        update_card(
            cards,
            idx,
            logo=data.get("logo"),
            title=data.get("title"),
            content=data.get("content"),
            center=data.get("center"),
            partition=data.get("partition"),
        )
        save_cards(cards)
        return jsonify({"ok": True})
    except IndexError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/cards/<int:idx>", methods=["DELETE"])
def api_cards_delete(idx):
    cards = load_cards()
    try:
        remove_card(cards, idx)
        save_cards(cards)
        return jsonify({"ok": True})
    except IndexError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/cards/reorder", methods=["POST"])
def api_cards_reorder():
    data = request.json
    cards = load_cards()
    try:
        reorder_card(cards, data["from"], data["to"])
        save_cards(cards)
        return jsonify({"ok": True})
    except (IndexError, KeyError) as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/publish", methods=["POST"])
def api_publish():
    data = request.json or {}
    message = data.get("message", "Update cards")
    try:
        git_publish(message)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/images", methods=["GET"])
def api_images():
    return jsonify(list_images())


if __name__ == "__main__":
    app.run(port=5050, debug=True)
