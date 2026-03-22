# raspyDisplay — TFT Monitor per Raspberry Pi

Questo progetto fornisce una serie di script Python e Bash per monitorare le statistiche di sistema di un Raspberry Pi (IP, temperatura, carico CPU, RAM, processi attivi) direttamente su un display TFT collegato tramite interfaccia SPI.

Gli script sono stati ottimizzati e testati per due specifici pannelli TFT:

- **Display 3.5" (Driver ILI9486 — 480×320):** scrittura diretta sul framebuffer (`/dev/fb1`) in formato RGB565. Include tre schermate: terminale classico con logo Debian, monitoraggio processi (`top`) e statistiche di sistema. Richiede l'overlay del kernel attivo in `config.txt`.
- **Display 2.8" (Driver ILI9341 — 320×240):** utilizza la libreria `luma.lcd` per comunicare direttamente sul bus SPI. Progettato per operare quando il framebuffer secondario non è disponibile o non è configurato.

---

## Struttura dei File

```
raspyDisplay/
├── display_35.py          # Dashboard multi-modalità per il pannello 3.5" (framebuffer)
├── displayASCII_35.py     # ASCII art animata su pannello 3.5" (framebuffer)
├── display_28.py          # Monitor per il pannello 2.8" (luma.lcd / SPI)
└── display-switch.sh      # Script Bash per switchare tra i servizi via systemd
```

---

## Requisiti Software

```bash
sudo apt update
sudo apt install python3-numpy python3-pil fonts-dejavu-core fastfetch
```

Per il display da 2.8", è necessaria anche la libreria Luma:

```bash
pip3 install luma.lcd --break-system-packages
```

> Su Raspberry Pi OS Bookworm o successivi potrebbe essere necessario usare un ambiente virtuale o il flag `--break-system-packages`.

L'utente che esegue lo script deve avere i permessi per accedere ai pin GPIO e all'interfaccia SPI:

```bash
sudo usermod -a -G spi,gpio,video $USER
```

---

## Configurazione di Sistema (solo display 3.5")

Per far sì che il Raspberry Pi crei il dispositivo `/dev/fb1` utilizzato da `display_35.py` e `displayASCII_35.py`, è necessario attivare il driver nel file di configurazione di avvio.

Modificare `/boot/firmware/config.txt` (o `/boot/config.txt` sulle versioni più vecchie) assicurandosi che siano presenti le seguenti righe:

```
dtparam=spi=on
dtoverlay=tft35a:rotate=90
```

> Se si utilizza un driver diverso, sostituire `tft35a` con `ili9486` o l'overlay fornito dal produttore.

---

## Utilizzo degli Script Python

### display_35.py — Dashboard 3.5"

Avvia il monitor con rotazione automatica tra le tre modalità (logo, processi, dashboard):

```bash
python3 display_35.py
```

### displayASCII_35.py — ASCII Art 3.5"

Mostra un file `.txt` come ASCII art animata con scroll automatico sul display:

```bash
python3 displayASCII_35.py --art /home/noya/Progettini/radioHead/thebends.txt
```

Per forzare una modalità specifica (0 = art, 1 = lista, 2 = orologio):

```bash
python3 displayASCII_35.py --art thebends.txt --mode 0
```

Per cambiare immagine basta passare un file `.txt` diverso con `--art`, oppure modificare `DEFAULT_ART_FILE` in cima allo script.

---

## Configurazione dei Servizi systemd

I due servizi permettono l'avvio automatico all'accensione e la gestione tramite `display-switch.sh`.

### tft-display.service — display_35.py

```bash
sudo nvim /etc/systemd/system/tft-display.service
```

```ini
[Unit]
Description=RaspyDisplay — Dashboard TFT (display_35.py)
After=multi-user.target
Wants=multi-user.target

[Service]
Type=simple
User=noya
WorkingDirectory=/home/noya/raspate/raspyDisplay
ExecStart=/usr/bin/python3 /home/noya/raspate/raspyDisplay/display_35.py
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### raspydisplay-ascii.service — displayASCII_35.py

```bash
sudo nvim /etc/systemd/system/raspydisplay-ascii.service
```

```ini
[Unit]
Description=RaspyDisplay — ASCII Art TFT (displayASCII_35.py)
After=multi-user.target
Wants=multi-user.target

[Service]
Type=simple
User=noya
WorkingDirectory=/home/noya/raspate/raspyDisplay
ExecStart=/usr/bin/python3 /home/noya/raspate/raspyDisplay/displayASCII_35.py --art /home/noya/Progettini/radioHead/thebends.txt
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Abilitazione dei servizi

```bash
sudo systemctl daemon-reload
sudo systemctl enable tft-display.service
sudo systemctl start tft-display.service
```

---

## display-switch.sh — Switch tra i servizi

Lo script Bash permette di passare da un display all'altro interattivamente o da CLI, e genera i file `.service` automaticamente se non esistono.

```bash
chmod +x display-switch.sh

./display-switch.sh            # menu interattivo (loop)
./display-switch.sh classic    # attiva display_35.py
./display-switch.sh ascii      # attiva displayASCII_35.py
./display-switch.sh status     # mostra quale servizio è attivo
```

Per fermare entrambi i servizi:

```bash
sudo systemctl stop tft-display.service raspydisplay-ascii.service
```

---

## Comandi Utili

```bash
# Stato del servizio
sudo systemctl status tft-display.service
sudo systemctl status raspydisplay-ascii.service

# Log in tempo reale
sudo journalctl -u tft-display.service -f
sudo journalctl -u raspydisplay-ascii.service -f

# Log ultimi 40 eventi
sudo journalctl -u tft-display.service -n 40 --no-pager

# Riavvio dopo modifiche agli script
sudo systemctl restart tft-display.service
sudo systemctl restart raspydisplay-ascii.service
```

---

## Note

- L'utente `noya` deve far parte dei gruppi `spi`, `gpio` e `video` per accedere al framebuffer e ai pin hardware.
- I font JetBrains Mono Nerd Font usati da `display_35.py` e `displayASCII_35.py` devono essere installati in `/usr/share/fonts/truetype/JetBrainsMono/`. In assenza, lo script fa fallback al font PIL di default.
- Il file `.txt` per l'ASCII art deve usare caratteri a larghezza fissa e non contenere caratteri non-ASCII per evitare artefatti sul display.
