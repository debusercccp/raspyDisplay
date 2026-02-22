#!/usr/bin/env python3
import subprocess, time, re, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Configurazione Hardware
FB_DEVICE = "/dev/fb1"
WIDTH, HEIGHT = 480, 320 
MAX_CHARS_TOP = 80

CLASSIC_LOGO = '''
       _,met$$$$$gg.                                                    
    ,g$$$$$$$$$$$$$$$P.                                                 
  ,g$$P""       """Y$$.".                                               
 ,$$P'              `$$$.                                               
',$$P       ,ggs.     `$$b:                                             
`d$$'     ,$P"'   .    $$$                                ,#.           
 $$P      d$'     ,    $$P      ##:          :##        :###:           
 $$:      $$.   -    ,d$$'      ##'          `##         `#'            
 $$;      Y$b._   _,d$P'    __  ##    __     ##  __      _     __       _   
 Y$$.    `.`"Y$$$$P"'     ,####:##  ,######.  ##.#####. :### ,######. ###.####: 
 `$$b      "-.__         ,##' `###  ##:  :##  ###' `###  ##' #:   `## `###' `##:
  `Y$$b                  ##    `##  ##    ##  ##'   `##  ##    ___,##  ##:   `##
   `Y$$.                 ##     ##  #######:  ##     ##  ##  .#######  ##'    ##
     `$$b.               ##     ##  ##'       ##     ##  ##  ##'  `##  ##     ##
       `Y$$b.            ##.   ,##  ##        ##    ,##  ##  ##    ##  ##     ##
         `"Y$b._         :#:._,###  ##:__,##  ##:__,##' ,##. ##.__:##. ##     ##
             `""""       `:#### ###  ######'  `######'  #### `#####"## ##     ##
'''

def get_stats():
    """Recupera IP e Temperatura per la barra in alto"""
    try:
        ip = subprocess.check_output(['hostname', '-I'], timeout=2).decode('utf-8').split()[0]
        temp = subprocess.check_output(['vcgencmd', 'measure_temp'], timeout=2).decode('utf-8').replace('temp=', '').strip()
        return f"IP: {ip} | Temp: {temp}"
    except:
        return "Stats: Loading..."

def get_classic_text():
    """Genera il testo di sistema in stile terminale TTY"""
    try:
        kernel = subprocess.check_output(['uname', '-r'], timeout=2).decode('utf-8').strip()
        mem_gb = subprocess.check_output("free -m | awk 'NR==2{printf \"%.1f\", $2/1024}'", shell=True).decode('utf-8').strip()
        hostname = os.uname().nodename
        
        line1 = f"Linux Version {kernel}, Compiled #1 SMP PREEMPT Debian"
        line2 = f"         Four 2.4GHz ARM Cortex-A76 Processors, {mem_gb}GB RAM, 432 Bogomips"
        line3 = f"                                                         Github: dubusercccp"
        return f"{line1}\n{line2}\n{line3}"
    except:
        return "Linux Version Error...\n \n rasp"

def get_top():
    try:
        res = subprocess.run(['top', '-bn1'], capture_output=True, text=True, timeout=3)
        return '\n'.join(res.stdout.split('\n')[:24])
    except:
        return "TOP Error"

def render_to_fb(mode):
    img = Image.new('RGB', (WIDTH, HEIGHT), (0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    try:
        f_tiny = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 10)
        ft = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 20)
        fs = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf', 13)
    except:
        f_tiny = ft = fs = ImageFont.load_default()

    # --- Barra Stats Superiore ---
    draw.rectangle([0, 0, WIDTH, 28], fill=(35, 35, 35))
    draw.text((15, 5), get_stats(), font=fs, fill=(255, 220, 0))

    if mode == 0:
        # --- MODALITÀ CLASSIC TTY ---
        y_pos = 35
        
        for line in CLASSIC_LOGO.strip('\n').split('\n'):
            draw.text((5, y_pos), line, font=f_tiny, fill=(215, 7, 81))
            y_pos += 12
            
        y_pos += 10 
        
        for line in get_classic_text().split('\n'):
            draw.text((5, y_pos), line, font=f_tiny, fill=(200, 200, 200))
            y_pos += 14
            
    else:
        # --- MODALITÀ PROCESS MONITOR ---
        draw.text((15, 40), "== PROCESS MONITOR ==", font=ft, fill=(255, 150, 0))
        y_top = 75
        for i, line in enumerate(get_top().split('\n')):
            color = (255, 255, 255) if i % 2 == 0 else (170, 170, 255)
            draw.text((5, y_top), line[:MAX_CHARS_TOP], font=f_tiny, fill=color)
            y_top += 10

    # Conversione in RGB565 per /dev/fb1
    img_array = np.array(img)
    fb_data = ((img_array[:,:,0]>>3).astype(np.uint16)<<11) | \
              ((img_array[:,:,1]>>2).astype(np.uint16)<<5) | \
               (img_array[:,:,2]>>3).astype(np.uint16)
    
    with open(FB_DEVICE, "wb") as f_fb:
        f_fb.write(fb_data.tobytes())

# --- Ciclo Principale ---
mode = 0
try:
    while True:
        render_to_fb(mode)
        mode = 1 if mode == 0 else 0
        time.sleep(5)
except KeyboardInterrupt:
    pass
