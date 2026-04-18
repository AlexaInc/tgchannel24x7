#!/bin/sh

# Check if COOKIES_TEXT environment variable is set
if [ -n "$COOKIES_TEXT" ]; then
    echo "Converting COOKIES_TEXT to cookies.txt..."
    echo "$COOKIES_TEXT" > cookies.txt
    echo "[✓] cookies.txt created."
else
    echo "[!] COOKIES_TEXT not found. Proceeding with existing cookies.txt if any."
fi

# Run the main application
exec python main.py
