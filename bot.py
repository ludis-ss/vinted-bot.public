import os
import requests
import cloudscraper
from bs4 import BeautifulSoup
import time
import datetime
import traceback

# --- CONFIGURAZIONE TELEGRAM ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID_MIO = os.environ.get("CHAT_ID")
CHAT_ID_AMICO = os.environ.get("CHAT_ID_AA") # <-- Carica l'ID del secondo utente dai Secrets

# --- LISTA RICERCHE VINTED ---
RICERCHE = [
    {
        "nome": "Oblivion PS5",
        "url": "https://www.vinted.it/catalog?search_text=oblivion%20remastered%20ps5&search_id=1264195745&catalog[]=3026&page=1&time=1784735308&video_game_platform_ids[]=1281&order=newest_first&price_to=50&currency=EUR",
        "prezzo_max": 25,
        "parole_obbligatorie": ["oblivion"],
        "parole_vietate": ["ps3"],
        "destinatari": ["mio"]
    },
    {
        "nome": "The Witcher 3 PS5",
        "url": "https://www.vinted.it/catalog?search_text=the%20witcher%203%20complete%20edition%20ps5&search_id=1367909452&catalog[]=3026&page=1&time=1785054873&video_game_platform_ids[]=1281&order=newest_first&currency=EUR",
        "prezzo_max": 15,  
        "parole_obbligatorie": ["witcher"],
        "parole_vietate": ["ps4"],
        "destinatari": ["mio"]
    },
    {
        "nome": "Demon Souls PS5",
        "url": "https://www.vinted.it/catalog?search_text=Demon%20Souls%20Ps5&search_id=1633776199&search_by_image_uuid=&search_by_image_id=&page=1&time=1785781545&catalog[]=3026&video_game_platform_ids[]=1281&order=newest_first",
        "prezzo_max": 20,
        "parole_obbligatorie": ["demon", "souls"],
        "parole_vietate": ["ps4", "ps3"],
        "destinatari": ["mio"]
    },
    {
        "nome": "Uncharted Collection PS4",
        "url": "https://www.vinted.it/catalog?search_text=uncharted%20collection%20ps4&search_id=1639015118&catalog[]=3026&page=1&time=1785789669&video_game_platform_ids[]=1280&order=newest_first",
        "prezzo_max": 7,
        "parole_obbligatorie": ["uncharted", "collection"],
        "parole_vietate": ["ps3", "ps5", "legacy", "thieves"],
        "destinatari": ["mio"]
    },
    {
        "nome": "Gotham Knights PS5",
        "url": "https://www.vinted.it/catalog?search_text=gotham%20knights%20&catalog[]=3026&page=1&time=1789121005&video_game_platform_ids[]=1281&order=newest_first",
        "prezzo_max": 8,
        "parole_obbligatorie": ["gotham", "knights"],
        "parole_vietate": ["ps4", "xbox"],
        "destinatari": ["mio"]
    },
    {
        "nome": "Silent Hill Townfall PS5",
        "url": "https://www.vinted.it/catalog?search_text=silent%20hill%20townfall&catalog[]=3026&page=1&time=1790504239&video_game_platform_ids[]=1281&order=newest_first",
        "prezzo_max": 35,
        "parole_obbligatorie": ["silent", "hill", "townfall"],
        "parole_vietate": ["ps4", "xbox", "steelbook", "steel-book"],
        "destinatari": ["mio"] 
    },
    {
        "nome": "Silent Hill 2 PS5",
        "url": "https://www.vinted.it/catalog?search_text=silent%20hill%202&catalog[]=3026&page=1&time=1790504392&video_game_platform_ids[]=1281&order=newest_first&search_by_image_uuid=&search_by_image_id=",
        "prezzo_max": 25,
        "parole_obbligatorie": ["silent", "hill", "2"],
        "parole_vietate": ["ps4", "xbox", "townfall"],
        "destinatari": ["mio"]
    },
    {
        "nome": "Silent Hill f PS5",
        "url": "https://www.vinted.it/catalog?search_text=silent%20hill%20f&catalog[]=3026&page=1&time=1790518114&video_game_platform_ids[]=1281&order=newest_first",
        "prezzo_max": 35,
        "parole_obbligatorie": ["silent", "hill"], 
        "parole_vietate": ["ps4", "xbox", "steelbook", "steel-book", "2", "townfall", "hd", "downpour", "homecoming", "origins", "shattered"], 
        "destinatari": ["mio", "amico"]
    }
]

# --- PAROLE VIETATE GLOBALI ---
PAROLE_VIETATE_GLOBALI = [
    # Italiano
    "vuota", "vuoto", "solo-custodia", "solo-scatola", "solo-box", "senza-gioco", "no-gioco", "solo-codice",
    # Francese 
    "vide", "boite-vide", "boitier-vide", "sans-jeu", "seul-boitier", "code-seul",
    # Spagnolo
    "vacia", "vacio", "solo-caja", "sin-juego", "caja-vacia",
    # Inglese
    "empty", "box-only", "case-only", "no-game", "code-only"
]

# Cloudscraper configurato
scraper = cloudscraper.create_scraper(
    browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True}
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1"
}

MEMORIA_FILE = "notified_items.txt"
LOG_FILE = "log_giornaliero.txt"
notified_items = set()

if os.path.exists(MEMORIA_FILE):
    with open(MEMORIA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            notified_items.add(line.strip())

def salva_in_memoria(link):
    notified_items.add(link)
    with open(MEMORIA_FILE, "a", encoding="utf-8") as f:
        f.write(link + "\n")

# --- NUOVA FUNZIONE DI INVIO SMISTATO ---
def send_telegram_message(text, lista_destinatari=["mio"]):
    if not TELEGRAM_TOKEN:
        print("⚠️ Token mancante nei Secrets!")
        return
        
    for destinatario in lista_destinatari:
        id_da_usare = None
        
        if destinatario == "mio" and CHAT_ID_MIO:
            id_da_usare = CHAT_ID_MIO
        elif destinatario == "amico" and CHAT_ID_AMICO:
            id_da_usare = CHAT_ID_AMICO
            
        if id_da_usare:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": id_da_usare, "text": text}
            try:
                requests.post(url, json=payload, timeout=10)
            except Exception as e:
                print(f"Errore invio Telegram a {destinatario}: {e}")

def scansiona_singolo_url(ricerca):
    items_found = 0
    new_alerts = 0
    
    response = scraper.get(ricerca["url"], headers=HEADERS, timeout=15)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            
            if "/items/" in href:
                # ⚡ RADAR TOTALE: Legge URL, attributo title (titolo originale) e testo visibile!
                testo_completo = f"{href} {a_tag.get('title', '')} {a_tag.get_text()}".lower()
                
                # 1. Controlla che ci siano TUTTE le parole obbligatorie
                if not all(parola in testo_completo for parola in ricerca["parole_obbligatorie"]):
                    continue
                
                # 2. CONTROLLO PAROLE VIETATE (Specifiche + Globali)
                vietate_specifiche = ricerca.get("parole_vietate", [])
                tutte_le_vietate = vietate_specifiche + PAROLE_VIETATE_GLOBALI
                
                if any(vietata in testo_completo for vietata in tutte_le_vietate):
                    continue  
                
                items_found += 1
                
                if href in notified_items:
                    continue
                    
                parent = a_tag.find_parent("div", class_=lambda c: c and "feed" in c) or a_tag.parent.parent
                price_text = ""
                
                if parent:
                    for child in parent.stripped_strings:
                        if "€" in child:
                            price_text = child
                            break
                
                if price_text:
                    price_str = price_text.replace("€", "").replace(".", "").replace(",", ".").replace(" ", "").replace("\xa0", "").strip()
                    
                    try:
                        price_float = float(price_str)
                        
                        if price_float <= ricerca["prezzo_max"]:
                            full_link = href if href.startswith("http") else f"https://www.vinted.it{href}"
                            messaggio = f"🔥 NUOVO AFFARE [{ricerca['nome']}]!\nPrezzo: {price_float}€\nLink: {full_link}"
                            
                            # Cerca chi deve ricevere questo annuncio
                            chi_lo_riceve = ricerca.get("destinatari", ["mio"])
                            send_telegram_message(messaggio, chi_lo_riceve)
                            
                            salva_in_memoria(href)
                            new_alerts += 1
                            
                    except ValueError:
                        pass
                        
    return items_found, new_alerts, response.status_code

def check_vinted():
    orario_attuale_str = datetime.datetime.now().strftime("%H:%M")
    ora_attuale = datetime.datetime.now()
    
    totale_visti = 0
    totale_novita = 0
    stato_run = "✅ Ok"
    
    try:
        print("-> Avvio scansione multi-articolo Vinted...")
        
        for idx, ricerca in enumerate(RICERCHE):
            if idx > 0:
                time.sleep(4)  # Pausa di cortesia anti-ban
                
            visti, novita, status = scansiona_singolo_url(ricerca)
            
            if status != 200:
                stato_run = f"❌ Errore HTTP {status}"
                # Invia l'errore solo a te
                send_telegram_message(f"⚠️ Errore Vinted su {ricerca['nome']} alle {orario_attuale_str}: HTTP {status}", ["mio"])
            
            totale_visti += visti
            totale_novita += novita

    except Exception as e:
        stato_run = "❌ Errore Generale"
        errore_dettagliato = traceback.format_exc()
        print(f"-> Errore durante lo scraping: {e}")
        send_telegram_message(f"⚠️ ATTENZIONE: Errore durante la scansione delle {orario_attuale_str}!\n\nDettaglio:\n{str(e)}", ["mio"])

    # --- CONTROLLO ED ELIMINAZIONE RIGHE DOPPIE ---
    riga_log = f"🕒 {orario_attuale_str} | {stato_run} | Visti: {totale_visti} | Novità: {totale_novita}\n"
    
    gia_registrato = False
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            righe = f.readlines()
            if righe and f"🕒 {orario_attuale_str}" in righe[-1]:
                gia_registrato = True

    if not gia_registrato:
        with open(LOG_FILE, "a", encoding="utf-8") as file_log:
            file_log.write(riga_log)

    # --- RESOCONTO DI FINE GIORNATA (Scatta a mezzanotte 00:00 - 00:04) ---
    if ora_attuale.hour == 0 and ora_attuale.minute < 5:
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as file_log:
                contenuto_diario = file_log.read()
        except FileNotFoundError:
            contenuto_diario = "Nessuna scansione registrata oggi."
        
        messaggio_resoconto = (
            "📊 *RESOCONTO GIORNALIERO VINTED*\n\n"
            f"{contenuto_diario}\n"
            "🦉 Resoconto di mezzanotte completato! Il bot continua a scansionare 24/7."
        )
        
        # Il resoconto giornaliero viene inviato SOLO a te
        send_telegram_message(messaggio_resoconto, ["mio"])
        
        # Svuota il diario per prepararlo al nuovo giorno
        open(LOG_FILE, "w", encoding="utf-8").close()

if __name__ == "__main__":
    print("=======================================")
    print("   Bot Vinted Action Avviato!          ")
    print("=======================================")

    check_vinted()
