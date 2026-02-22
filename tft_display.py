#!/usr/bin/env python3
import subprocess
import time
import re
import os
from PIL import Image, ImageDraw, ImageFont
from luma.core.interface.serial import spi

def detect_display():
    """Rileva automaticamente il tipo di display collegato."""
    try:
        with open('/boot/firmware/config.txt', 'r') as f:
            config = f.read()
        if 'tft35a' in config or 'ili9486' in config.lower():
            return '3.5inch'
    except:
        pass
    fb_devices = [f for f in os.listdir('/dev') if f.startswith('fb')]
    if len(fb_devices) >= 2:
        return '3.5inch'
    return '2.8inch'

def init_display(display_type):
    """Inizializza il display in base al tipo rilevato."""
    if display_type == '3.5inch':
        from luma.lcd.device import ili9486
        serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=27, bus_speed_hz=16000000)
        device = ili9486(serial, width=320, height=480, rotate=0)
        width, height = 320, 480
        max_chars = 52
        print("Display 3.5\" ILI9486 rilevato (480x320)")
    else:
        from luma.lcd.device import ili9341
        serial = spi(port=0, device=0, gpio_DC=25, gpio_RST=27, bus_speed_hz=16000000)
        device = ili9341(serial, width=320, height=240, rotate=2)
        width, height = 320, 240
        max_chars = 58
        print("Display 2.8\" ILI9341 rilevato (320x240)")
    return device, width, height, max_chars

def get_fastfetch():
    try:
        result = subprocess.run(['fastfetch', '--logo', 'none'],
                                capture_output=True, text=True, timeout=5)
        clean = re.sub(r'\x1b\[[0-9;]*m', '', result.stdout)
        clean = re.sub(r'\x1b[^m]*m', '', clean)
        return clean
    except Exception as e:
        return f"Errore fastfetch: {e}"

def get_top_snapshot():
    try:
        result = subprocess.run(['top', '-bn1'],
                                capture_output=True, text=True, timeout=5)
        lines = result.stdout.split('\n')[:20]
        return '\n'.join(lines)
    except:
        return "top non disponibile"

def render_text(device, width, height, max_chars, text, title="", title_color=(0, 255, 0)):
    img = Image.new('RGB', (width, height), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    font_size = 9 if height <= 240 else 11
    title_font_size = 11 if height <= 240 else 13

    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', font_size)
        font_title = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', title_font_size)
    except:
        font = ImageFont.load_default()
        font_title = font

    line_height = font_size + 2

    if title:
        draw.text((5, 2), title, font=font_title, fill=title_color)
        y = title_font_size + 6
    else:
        y = 5

    colors = [(255, 255, 255), (180, 180, 255)]
    i = 0
    for line in text.split('\n'):
        if y > height - line_height:
            break
        draw.text((5, y), line[:max_chars], font=font, fill=colors[i % 2])
        y += line_height
        i += 1

    device.display(img)

# Avvio
display_type = detect_display()
device, width, height, max_chars = init_display(display_type)

print(f"Display {display_type} pronto. Premi Ctrl+C per uscire.")

mode = 0
try:
    render_text(device, width, height, max_chars,
                get_fastfetch(), "=== FASTFETCH ===", title_color=(0, 255, 128))
    while True:
        time.sleep(10)
        if mode == 0:
            render_text(device, width, height, max_chars,
                        get_top_snapshot(), "=== TOP/HTOP ===", title_color=(255, 165, 0))
            mode = 1
        else:
            render_text(device, width, height, max_chars,
                        get_fastfetch(), "=== FASTFETCH ===", title_color=(0, 255, 128))
            mode = 0
except KeyboardInterrupt:
    print("Uscita.")
    device.cleanup()
