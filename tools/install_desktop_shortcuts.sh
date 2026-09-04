#!/bin/bash
set -eu

REPO_DIR="${PAINETESTERI_REPO:-$HOME/painetesteri_hmi}"

if command -v xdg-user-dir >/dev/null 2>&1; then
    DESKTOP_DIR="$(xdg-user-dir DESKTOP)"
else
    DESKTOP_DIR="$HOME/Desktop"
fi

if [ ! -d "$REPO_DIR/desktop" ]; then
    echo "desktop-hakemistoa ei löytynyt: $REPO_DIR/desktop"
    exit 1
fi

mkdir -p "$DESKTOP_DIR"

for name in "Päivitä painetesteri.desktop" "Palauta painetesteri.desktop"; do
    src="$REPO_DIR/desktop/$name"
    dst="$DESKTOP_DIR/$name"

    cp "$src" "$dst"
    chmod +x "$dst"

    if command -v gio >/dev/null 2>&1; then
        gio set "$dst" metadata::trusted true >/dev/null 2>&1 || true
    fi
done

echo "Pikakuvakkeet asennettu: $DESKTOP_DIR"
