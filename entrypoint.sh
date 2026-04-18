#!/bin/sh

# Check if COOKIES_TEXT environment variable is set
if [ -n "$COOKIES_TEXT" ]; then
    echo "Converting COOKIES_TEXT to cookies.txt..."
    # Ensure it starts with the correct Netscape header if missing
    if ! echo "$COOKIES_TEXT" | grep -q "# Netscape HTTP Cookie File"; then
        echo "# Netscape HTTP Cookie File" > cookies.txt
        echo "$COOKIES_TEXT" >> cookies.txt
        echo "[!] Missing Netscape header added."
    else
        echo "$COOKIES_TEXT" > cookies.txt
    fi
    echo "[✓] cookies.txt created."
else
    echo "[!] COOKIES_TEXT not found. Proceeding with existing cookies.txt if any."
fi

# Run the main application
exec python main.py
