#!/usr/bin/env python3
import subprocess, time, re, os
from PIL import Image, ImageDraw, ImageFont
from luma.core.interface.serial import spi, noop
from luma.lcd.device import ili9341

# Configurazione 2.8"
WIDTH, HEIGHT = 320, 240
MAX_CHARS = 58

def get_device():
    # Prova i bus SPI comuni (10 e 0)
    for bus in [10, 0]:
        try:
            serial = spi(port=bus, device=0, gpio_DC=25, gpio_RST=27, bus_speed_hz=16000000, gpio=noop())
            return ili9341(serial, width=WIDTH, height=HEIGHT, rotate=2)
        except Exception:
            continue
    raise RuntimeError("Impossibile trovare il bus SPI (testati 0 e 10)")

def get_fastfetch():
    try:
        res = subprocess.run(['fastfetch', '--logo', 'none'], capture_output=True, text=True, timeout=5)
        return re.sub(r'\x1b\[[0-9;]*m|\x1b[^m]*m', '', res.stdout)
    except: return "Errore fastfetch"

def get_top():
    try:
        res = subprocess.run(['top', '-bn1'], capture_output=True, text=True, timeout=5)
        return '\n'.join(res.stdout.split('\n')[:15])
    except: return "top error"

def render(device, text, title, color):
    img = Image.new('RGB', (WIDTH, HEIGHT), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    try:
        f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 9)
        ft = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 11)
    except: f = ft = ImageFont.load_default()
    draw.text((5, 2), title, font=ft, fill=color)
    y = 18
    for i, line in enumerate(text.split('\n')):
        if y > HEIGHT - 12: break
        draw.text((5, y), line[:MAX_CHARS], font=f, fill=(255,255,255) if i%2==0 else (180,180,255))
        y += 11
    device.display(img)

try:
    device = get_device()
    mode = 0
    while True:
        if mode == 0:
            render(device, get_fastfetch(), "=== FASTFETCH (2.8) ===", (0, 255, 128))
            mode = 1
        else:
            render(device, get_top(), "=== TOP SYSTEM ===", (255, 165, 0))
            mode = 0
        time.sleep(10)
except KeyboardInterrupt:
    pass
