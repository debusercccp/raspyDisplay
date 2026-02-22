#!/bin/bash
DIR="/home/noya/scripts"

echo "--- Analisi Hardware Display ---"

# Se esiste fb1, è quasi certamente il 3.5" (driver ili9486 attivo)
if [ -e /dev/fb1 ]; then
    echo "Rilevato Framebuffer secondario. Avvio script 3.5\"..."
    /usr/bin/python3 $DIR/display_35.py
else
    echo "Nessun framebuffer extra. Provo il display 2.8\"..."
    /usr/bin/python3 $DIR/display_28.py
fi
