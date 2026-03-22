#!/usr/bin/env python3
"""
displayASCII_35.py — Mostra un'immagine ASCII da file su display TFT via framebuffer.
Struttura multi-modalità: modalità 0 = ASCII art animata, modalità 1/2 = personalizzabili.

Uso:
    python3 displayASCII_35.py --art /home/noya/Progettini/radioHead/thebends.txt
    python3 displayASCII_35.py --mode 0    # forza modalità ASCII
"""

import subprocess
import time
import argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# =============================================================================
# CONFIGURAZIONE HARDWARE
# =============================================================================
FB_DEVICE     = "/dev/fb1"
WIDTH, HEIGHT = 480, 320

NUM_MODES      = 3
MODE_DURATIONS = [15, 10, 4]   # secondi per modalità 0, 1, 2

# =============================================================================
# ASCII ART
# =============================================================================
DEFAULT_ART_FILE = "/home/noya/Progettini/radioHead/thebends.txt"

VISIBLE_ROWS = 38      # righe visibili contemporaneamente
FONT_SIZE_ART = 8      # font piccolo per far stare più righe
ROW_H         = 8      # altezza riga in pixel (uguale al font size)

ART_COLOR    = (215, 7, 81)   # rosso Debian
ART_BG_COLOR = (0, 0, 0)

# =============================================================================
# FONT
# =============================================================================
FONT_PATH_THIN     = '/usr/share/fonts/truetype/JetBrainsMono/JetBrainsMonoNLNerdFontMono-Thin.ttf'
FONT_PATH_SEMIBOLD = '/usr/share/fonts/truetype/JetBrainsMono/JetBrainsMonoNLNerdFontPropo-SemiBold.ttf'

def load_fonts():
    try:
        return {
            'art':    ImageFont.truetype(FONT_PATH_THIN,     FONT_SIZE_ART),
            'tiny':   ImageFont.truetype(FONT_PATH_THIN,     10),
            'small':  ImageFont.truetype(FONT_PATH_THIN,     13),
            'normal': ImageFont.truetype(FONT_PATH_THIN,     20),
            'big':    ImageFont.truetype(FONT_PATH_SEMIBOLD, 48),
            'med':    ImageFont.truetype(FONT_PATH_SEMIBOLD, 28),
        }
    except OSError:
        d = ImageFont.load_default()
        return {k: d for k in ('art', 'tiny', 'small', 'normal', 'big', 'med')}

# =============================================================================
# LETTURA FILE ASCII ART
# =============================================================================
def load_art(filepath: str) -> list[str]:
    try:
        with open(filepath, "r") as f:
            return [line.rstrip('\n') for line in f.readlines()]
    except FileNotFoundError:
        return [f"File non trovato: {filepath}"]
    except Exception as e:
        return [f"Errore: {e}"]

# =============================================================================
# STATO GLOBALE
# =============================================================================
art_lines:  list[str] = []
art_offset: int       = 0
scroll_dir: int       = 1   # +1 giù, -1 su (bounce)

# =============================================================================
# BARRA SUPERIORE
# =============================================================================
def get_topbar_text() -> str:
    try:
        ip = subprocess.check_output(['hostname', '-I'], timeout=2).decode().split()[0]
        return f"IP: {ip} | {time.strftime('%H:%M:%S')}"
    except Exception:
        return time.strftime('%H:%M:%S')

def draw_topbar(draw, fonts):
    draw.rectangle([0, 0, WIDTH, 20], fill=(35, 35, 35))
    draw.text((8, 3), get_topbar_text(), font=fonts['tiny'], fill=(255, 220, 0))

# =============================================================================
# MODALITÀ 0 — ASCII ART con scroll bounce
# =============================================================================
def render_mode_0(draw, fonts):
    global art_offset, scroll_dir

    if not art_lines:
        draw.text((10, 30), "Nessuna art caricata.", font=fonts['small'], fill=(255, 80, 80))
        return

    y = 22   # subito sotto la topbar (20px)
    visible = art_lines[art_offset : art_offset + VISIBLE_ROWS]
    for line in visible:
        draw.text((0, y), line, font=fonts['art'], fill=ART_COLOR)
        y += ROW_H

    # Scroll bounce
    max_offset = max(0, len(art_lines) - VISIBLE_ROWS)
    art_offset += scroll_dir
    if art_offset >= max_offset:
        art_offset = max_offset
        scroll_dir = -1
    elif art_offset <= 0:
        art_offset = 0
        scroll_dir = 1

# =============================================================================
# MODALITÀ 1 — personalizza qui
# =============================================================================
def render_mode_1(draw, fonts):
    draw.text((15, 30), "== MODE 1 ==", font=fonts['normal'], fill=(255, 150, 0))

    y = 60
    for line in art_lines[:28]:
        draw.text((0, y), line, font=fonts['art'], fill=(100, 100, 200))
        y += ROW_H
        if y > HEIGHT - 10:
            break

# =============================================================================
# MODALITÀ 2 — personalizza qui
# =============================================================================
def render_mode_2(draw, fonts):
    now      = time.localtime()
    time_str = time.strftime("%H:%M:%S", now)
    date_str = time.strftime("%a %d %b %Y", now)

    draw.text((10, 28), time_str, font=fonts['big'],   fill=(0, 220, 255))
    draw.text((18, 82), date_str, font=fonts['small'], fill=(150, 200, 255))

    draw.line([10, 110, WIDTH - 10, 110], fill=(60, 60, 60))
    draw.text((10, 116), f"{DEFAULT_ART_FILE}  ({len(art_lines)} righe)",
              font=fonts['tiny'], fill=(200, 200, 200))

# =============================================================================
# SCRITTURA FRAMEBUFFER (RGB → RGB565)
# =============================================================================
def write_to_fb(img: Image.Image):
    arr   = np.array(img)
    fb565 = ((arr[:,:,0] >> 3).astype(np.uint16) << 11) | \
            ((arr[:,:,1] >> 2).astype(np.uint16) <<  5) | \
             (arr[:,:,2] >> 3).astype(np.uint16)
    with open(FB_DEVICE, "wb") as fb:
        fb.write(fb565.tobytes())

# =============================================================================
# RENDER PRINCIPALE
# =============================================================================
_fonts = None   # cache font per non ricaricarli ogni frame

def render(mode: int):
    global _fonts
    if _fonts is None:
        _fonts = load_fonts()

    img  = Image.new('RGB', (WIDTH, HEIGHT), ART_BG_COLOR)
    draw = ImageDraw.Draw(img)

    draw_topbar(draw, _fonts)

    if   mode == 0: render_mode_0(draw, _fonts)
    elif mode == 1: render_mode_1(draw, _fonts)
    elif mode == 2: render_mode_2(draw, _fonts)

    write_to_fb(img)

# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Display ASCII art su TFT framebuffer")
    parser.add_argument('--art',  default=DEFAULT_ART_FILE, help="File .txt con l'ASCII art")
    parser.add_argument('--mode', type=int, default=None,   help="Forza una modalità (0/1/2)")
    args = parser.parse_args()

    art_lines = load_art(args.art)
    print(f"[+] Caricato '{args.art}': {len(art_lines)} righe")

    if args.mode is not None:
        print(f"[+] Modalità fissa: {args.mode}")
        try:
            while True:
                render(args.mode)
                time.sleep(0.08)
        except KeyboardInterrupt:
            pass
    else:
        mode = 0
        try:
            while True:
                duration = MODE_DURATIONS[mode]
                elapsed  = 0.0

                if mode == 0:
                    step = 0.10   # scroll fluido
                else:
                    step = 2.0

                while elapsed < duration:
                    render(mode)
                    time.sleep(step)
                    elapsed += step

                mode = (mode + 1) % NUM_MODES

        except KeyboardInterrupt:
            pass
