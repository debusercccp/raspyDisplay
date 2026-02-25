#!/usr/bin/env python3
import subprocess, time, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Configurazione Hardware
FB_DEVICE = "/dev/fb1"
WIDTH, HEIGHT = 480, 320
MAX_CHARS_TOP = 80

CLASSIC_LOGO = '''
     _,met$$$$$gg.
   ,g$$$$$$$$$$$$$$$.
  ,g$$P"       "Y$$.".
 ,$$P'           `$$$.
,$$P      ,ggs.  `$$b:
d$$'   ,$P"' .    $$$                          
$$P    d$'   ,    $$P     ##:      :##        
$$:    $$.  -   ,d$$'     ##'      `##        '#'
$$;    Y$b._  _,d$P'      ##        ##             
Y$$.  `.`"Y$$$$P"'  ,####:## ,####. ##.####. :### ,####. ###.####:
`$$b    "-.__       ##' `### ##: ## ###' `##  ##' ##: ## `###' `##:
 `Y$$b              ##   `## ##  ## ##'  `##  ##   __,##  ##:   `##
  `Y$$.             ##    ## ####:  ##    ##  ##  ######  ##'    ##
    `$$b.           ##    ## ##'    ##    ##  ##  ##'`##  ##     ##
      `Y$$b.        ##.  ,## ##     ##   ,##  ##  ##  ##  ##     ##
        `"Y$$b.     ##:._### ##:_## ##:__##' ,##. ##._##. ##     ##
            `""""    ## ###   ##'  `#####'   #### `####"# ##     ##
'''

# Storico CPU e RAM per grafico (ultimi 40 campioni)
cpu_history = [0] * 40
ram_history = [0] * 40
net_prev = None

def get_stats():
    try:
        ip = subprocess.check_output(['hostname', '-I'], timeout=2).decode().split()[0]
        temp = subprocess.check_output(['vcgencmd', 'measure_temp'], timeout=2).decode().replace('temp=', '').strip()
        return f"IP: {ip} | Temp: {temp}"
    except:
        return "Stats: Loading..."

def get_classic_text():
    try:
        kernel = subprocess.check_output(['uname', '-r'], timeout=2).decode().strip()
        mem_gb = subprocess.check_output("free -m | awk 'NR==2{printf \"%.1f\", $2/1024}'", shell=True).decode().strip()
        line1 = f"     Linux Version {kernel}, Compiled #1 SMP PREEMPT Debian"
        line2 = f"     Four 2.4GHz ARM Cortex-A76 Processors, {mem_gb}GB RAM, 432 Bogomips"
        line3 = f"                              Github: dubusercccp"
        return f"{line1}\n{line2}\n{line3}"
    except:
        return "Linux Version Error...\n \n rasp"

def get_top():
    try:
        res = subprocess.run(['top', '-bn1'], capture_output=True, text=True, timeout=3)
        return '\n'.join(res.stdout.split('\n')[:24])
    except:
        return "TOP Error"

def get_cpu_percent():
    try:
        res = subprocess.check_output("top -bn1 | grep 'Cpu' | awk '{print $2}'", shell=True).decode().strip()
        return float(res.replace(',', '.'))
    except:
        return 0.0

def get_ram_percent():
    try:
        res = subprocess.check_output("free | awk 'NR==2{printf \"%.1f\", $3*100/$2}'", shell=True).decode().strip()
        return float(res)
    except:
        return 0.0

def get_disk():
    try:
        res = subprocess.check_output("df -h / | awk 'NR==2{print $3, $4, $5}'", shell=True).decode().strip()
        used, free, pct = res.split()
        return used, free, int(pct.replace('%', ''))
    except:
        return "?", "?", 0

def get_net_speed():
    global net_prev
    try:
        with open('/proc/net/dev') as f:
            lines = f.readlines()
        rx, tx = 0, 0
        for line in lines[2:]:
            parts = line.split()
            if parts[0] not in ('lo:', 'docker0:'):
                rx += int(parts[1])
                tx += int(parts[9])
        now = time.time()
        if net_prev is None:
            net_prev = (now, rx, tx)
            return 0.0, 0.0
        dt = now - net_prev[0]
        rx_speed = (rx - net_prev[1]) / dt / 1024  # KB/s
        tx_speed = (tx - net_prev[2]) / dt / 1024  # KB/s
        net_prev = (now, rx, tx)
        return rx_speed, tx_speed
    except:
        return 0.0, 0.0

def draw_bar(draw, x, y, w, h, pct, color_fill, color_bg=(50, 50, 50)):
    draw.rectangle([x, y, x+w, y+h], fill=color_bg)
    fill_w = int(w * pct / 100)
    if fill_w > 0:
        draw.rectangle([x, y, x+fill_w, y+h], fill=color_fill)

def draw_graph(draw, x, y, w, h, history, color, label):
    # Sfondo grafico
    draw.rectangle([x, y, x+w, y+h], fill=(20, 20, 20))
    draw.rectangle([x, y, x+w, y+h], outline=(80, 80, 80))
    # Linea guida 50%
    mid_y = y + h // 2
    for gx in range(x, x+w, 4):
        draw.point((gx, mid_y), fill=(60, 60, 60))
    # Disegna il grafico
    pts = len(history)
    if pts > 1:
        step = w / (pts - 1)
        points = []
        for i, val in enumerate(history):
            px = int(x + i * step)
            py = int(y + h - (val / 100.0) * h)
            py = max(y, min(y+h, py))
            points.append((px, py))
        for i in range(len(points)-1):
            draw.line([points[i], points[i+1]], fill=color, width=2)
    draw.text((x+3, y+2), label, font=ImageFont.load_default(), fill=color)

def write_to_fb(img):
    img_array = np.array(img)
    fb_data = ((img_array[:,:,0]>>3).astype(np.uint16)<<11) | \
              ((img_array[:,:,1]>>2).astype(np.uint16)<<5) | \
               (img_array[:,:,2]>>3).astype(np.uint16)
    with open(FB_DEVICE, "wb") as f_fb:
        f_fb.write(fb_data.tobytes())

def render_to_fb(mode):
    global cpu_history, ram_history

    img = Image.new('RGB', (WIDTH, HEIGHT), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        f_tiny  = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 10)
        f_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 13)
        ft      = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 20)
        fs      = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 13)
        f_big   = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 48)
        f_med   = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 28)
    except:
        f_tiny = ft = fs = f_big = f_med = f_small = ImageFont.load_default()

    # --- Barra Stats Superiore ---
    draw.rectangle([0, 0, WIDTH, 28], fill=(35, 35, 35))
    draw.text((15, 5), get_stats(), font=fs, fill=(255, 220, 0))

    if mode == 0:
        # --- MODALITA' 1: LOGO ASCII ---
        y_pos = 35
        for line in CLASSIC_LOGO.strip('\n').split('\n'):
            draw.text((5, y_pos), line, font=f_tiny, fill=(215, 7, 81))
            y_pos += 12
        y_pos += 10
        for line in get_classic_text().split('\n'):
            draw.text((5, y_pos), line, font=f_tiny, fill=(200, 200, 200))
            y_pos += 14

    elif mode == 1:
        # --- MODALITA' 2: PROCESS MONITOR ---
        draw.text((15, 40), "== PROCESS MONITOR ==", font=ft, fill=(255, 150, 0))
        y_top = 75
        for i, line in enumerate(get_top().split('\n')):
            color = (255, 255, 255) if i % 2 == 0 else (170, 170, 255)
            draw.text((5, y_top), line[:MAX_CHARS_TOP], font=f_tiny, fill=color)
            y_top += 10

    elif mode == 2:
        # --- MODALITA' 3: DASHBOARD ---

        # Aggiorna storici
        cpu = get_cpu_percent()
        ram = get_ram_percent()
        cpu_history = cpu_history[1:] + [cpu]
        ram_history = ram_history[1:] + [ram]
        disk_used, disk_free, disk_pct = get_disk()
        rx_kb, tx_kb = get_net_speed()

        # --- ORARIO E DATA grandi ---
        now = time.localtime()
        time_str = time.strftime("%H:%M:%S", now)
        date_str = time.strftime("%a %d %b %Y", now)
        draw.text((10, 32), time_str, font=f_big, fill=(0, 220, 255))
        draw.text((18, 88), date_str, font=f_small, fill=(150, 200, 255))

        # --- GRAFICI CPU e RAM ---
        draw_graph(draw, 10, 112, 220, 55, cpu_history, (0, 255, 100), f"CPU {cpu:.0f}%")
        draw_graph(draw, 10, 175, 220, 55, ram_history, (255, 100, 0), f"RAM {ram:.0f}%")

        # --- BARRE CPU e RAM ---
        draw_bar(draw, 10, 238, 220, 14, cpu, (0, 200, 80))
        draw_bar(draw, 10, 258, 220, 14, ram, (200, 100, 0))
        draw.text((240, 238), f"CPU {cpu:.1f}%", font=f_tiny, fill=(0, 255, 100))
        draw.text((240, 258), f"RAM {ram:.1f}%", font=f_tiny, fill=(255, 150, 0))

        # --- DISCO ---
        draw.text((245, 32), "DISCO", font=fs, fill=(200, 200, 200))
        draw_bar(draw, 245, 55, 220, 18, disk_pct, (100, 180, 255))
        draw.text((245, 78), f"Usato: {disk_used}  Libero: {disk_free}", font=f_tiny, fill=(180, 180, 255))
        draw.text((245, 93), f"{disk_pct}% occupato", font=f_tiny, fill=(150, 150, 200))

        # --- RETE ---
        draw.line([245, 115, 465, 115], fill=(60, 60, 60))
        draw.text((245, 120), "RETE", font=fs, fill=(200, 200, 200))

        # Formatta velocità
        def fmt_speed(kbs):
            if kbs >= 1024:
                return f"{kbs/1024:.1f} MB/s"
            return f"{kbs:.0f} KB/s"

        draw.text((245, 145), f"▼ {fmt_speed(rx_kb)}", font=f_small, fill=(0, 255, 150))
        draw.text((245, 168), f"▲ {fmt_speed(tx_kb)}", font=f_small, fill=(255, 80, 80))

        # --- SEPARATORI ---
        draw.line([240, 28, 240, 320], fill=(60, 60, 60))
        draw.line([10, 108, 470, 108], fill=(60, 60, 60))

    write_to_fb(img)

# --- Ciclo Principale ---
mode = 0
try:
    while True:
        render_to_fb(mode)
        if mode == 2:
            time.sleep(2)  # Dashboard si aggiorna più spesso
        else:
            mode_time = 0
            while mode_time < 10:
                render_to_fb(mode)
                time.sleep(2)
                mode_time += 2
        mode = (mode + 1) % 3
except KeyboardInterrupt:
    pass
