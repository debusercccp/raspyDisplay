TFT Monitor per Raspberry Pi

Questo progetto fornisce una serie di script in Python e Bash per monitorare le statistiche di sistema di un Raspberry Pi (IP, Temperatura, Carico CPU, RAM, processi attivi) direttamente su un display TFT collegato tramite interfaccia SPI.

Gli script sono stati ottimizzati e testati per due specifici pannelli TFT:

    Display 3.5" (Driver ILI9486 - 480x320)

        Utilizza un approccio di scrittura diretta sul framebuffer (/dev/fb1) in formato RGB565.

        Include tre schermate: un terminale classico TTY con logo Debian, monitoraggio processi (top) e statistiche di sistema.

        Richiede che l'overlay del kernel sia attivo nel config.txt.

    Display 2.8" (Driver ILI9341 - 320x240)

        Utilizza la libreria luma.lcd per comunicare direttamente sul bus SPI.

        Progettato per operare quando il framebuffer secondario non è disponibile o non è configurato.

Requisiti Software

Assicurarsi che il sistema disponga dei seguenti pacchetti installati:
Bash

sudo apt update
sudo apt install python3-numpy python3-pil fonts-dejavu-core fastfetch

Per il display da 2.8", è necessaria anche la libreria Luma:
Bash

pip3 install luma.lcd --break-system-packages

(Nota: su Raspberry Pi OS Bookworm o successivi, potrebbe essere necessario usare un ambiente virtuale o il flag --break-system-packages).

L'utente che esegue lo script deve avere i permessi per accedere ai pin GPIO e all'interfaccia SPI:
Bash

sudo usermod -a -G spi,gpio,video $USER

Configurazione di Sistema (Solo per 3.5")

Per far sì che il Raspberry Pi crei il dispositivo /dev/fb1 utilizzato dallo script display_35.py, è necessario attivare il driver nel file di configurazione di avvio.

Modificare il file /boot/firmware/config.txt (o /boot/config.txt sulle versioni più vecchie) assicurandosi che siano presenti le seguenti righe:
Plaintext

dtparam=spi=on
dtoverlay=tft35a:rotate=90

(Se si utilizza un driver diverso, sostituire tft35a con ili9486 o l'overlay fornito dal produttore).
Struttura dei File

    display_35.py: Script Python per il pannello da 3.5 pollici (scrittura su Framebuffer).

    display_28.py: Script Python per il pannello da 2.8 pollici (gestione SPI via Luma).

Configurazione del Demone (Avvio Automatico)

Per far sì che il monitoraggio parta automaticamente all'accensione del Raspberry Pi, è necessario configurare un servizio systemd.

    Creare il file del servizio:

Bash

sudo nano /etc/systemd/system/tft-display.service

    Inserire la seguente configurazione (verificare che i percorsi corrispondano a quelli reali, in questo caso /home/noya/scripts):

Ini, TOML

[Unit]
Description=TFT Display Auto-Detection Monitor
After=network.target

[Service]
Type=simple
User=noya
WorkingDirectory=/home/$USER/raspyDisplay
# Un ritardo di 5 secondi assicura che il driver del framebuffer sia caricato
ExecStartPre=/bin/sleep 5
ExecStart=/home/$USER/raspyDisplay/display_35.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

    Ricaricare i demoni di sistema e abilitare il servizio:

Bash

sudo systemctl daemon-reload
sudo systemctl enable tft-display.service
sudo systemctl start tft-display.service

Comandi Utili per il Servizio

    Per controllare lo stato del display:
    systemctl status tft-display.service

    Per leggere i log in caso di errori:
    journalctl -u tft-display.service -f

    Per riavviare il monitor dopo aver modificato gli script:
    sudo systemctl restart tft-display.service
