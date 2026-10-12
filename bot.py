import os
import requests
import cloudscraper
from bs4 import BeautifulSoup
import time
import datetime
import traceback
import re
import random
import logging

# --- CONFIGURAZIONE LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- CONFIGURAZIONE TELEGRAM ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID_MIO = os.environ.get("CHAT_ID")
CHAT_ID_AMICO = os.environ.get("CHAT_ID_AA")

# --- LISTA RICERCHE VINTED ---
# IMPORTANTE: Ho ripulito gli URL da 'time', 'search_id' e altri parametri traccianti
RICERCHE = [
    {
        "nome": "Oblivion PS5",
        "url": "https://www.vinted.it/catalog?search_text=oblivion%20remastered%20ps5&catalog[]=3026&video_game_platform_ids[]=1281&order=newest_first&price_to=50&currency=EUR",
        "prezzo_max": 25,
        "prezzo_minimo_digitale": 9.99,
        "parole_obbligatorie": ["oblivion"],
        "parole_vietate": ["ps3"],
        "destinatari": ["mio"]
    },
    {
        "nome": "The Witcher 3 PS5",
        "url": "https://www.vinted.it/catalog?search_text=the%20witcher%203%20complete%20edition%20ps5&catalog[]=3026&video_game_platform_ids[]=1281&order=newest_first&currency=EUR",
        "prezzo_max": 15,  
        "prezzo_minimo_digitale": 0.0,
        "parole_obbligatorie": ["witcher"],
        "parole_vietate": ["ps4"],
        "destinatari": ["mio"]
    },
    {
        "nome": "Demon Souls PS5",
        "url": "https://www.vinted.it/catalog?search_text=Demon%20Souls%20Ps5&catalog[]=3026&video_game_platform_ids[]=1281&order=newest_first",
        "prezzo_max": 20,
        "prezzo_minimo_digitale": 40.0,
        "parole_obbligatorie": ["demon", "souls"],
        "parole_vietate": ["ps4", "ps3"],
        "destinatari": ["mio"]
    },
    {
        "nome": "Uncharted Collection PS4",
        "url": "https://www.vinted.it/catalog?search_text=uncharted%20collection%20ps4&catalog[]=3026&video_game_platform_ids[]=1280&order=newest_first",
        "prezzo_max": 7,
        "prezzo_minimo_digitale": 5.9,
        "parole_obbligatorie": ["uncharted", "collection"],
        "parole_vietate": ["ps3", "ps5", "legacy", "thieves"],
        "destinatari": ["mio"]
    },
    {
        "nome": "Gotham Knights PS5",
        "url": "https://www.vinted.it/catalog?search_text=gotham%20knights&catalog[]=3026&video_game_platform_ids[]=1281&order=newest_first",
        "prezzo_max": 8,
        "prezzo_minimo_digitale": 7.49,
        "parole_obbligatorie": ["gotham", "knights"],
        "parole_vietate": ["ps4", "xbox"],
        "destinatari": ["mio"]
    },
    {
        "nome": "Silent Hill f PS5",
        "url": "https://www.vinted.it/catalog?search_text=silent%20hill%20f&catalog[]=3026&video_game_platform_ids[]=1281&order=newest_first",
        "prezzo_max": 30,
        "prezzo_minimo_digitale": 40.0,
        "parole_obbligatorie": ["silent", "hill"], 
        "parole_vietate": ["ps4", "xbox", "steelbook", "steel-book", "townfall", "hd", "downpour", "homecoming", "origins", "shattered"], 
        "destinatari": ["mio", "amico"]
    },
    {
        "nome": "Silent Hill Townfall PS5",
        "url": "https://www.vinted.it/catalog?search_text=silent%20hill%20townfall&catalog[]=3026&video_game_platform_ids[]=1281&order=newest_first",
        "prezzo_max": 25,
        "prezzo_minimo_digitale": 50.0,
        "parole_obbligatorie": ["silent", "hill", "townfall"],
        "parole_vietate": ["ps4", "xbox", "steelbook", "steel-book"],
        "destinatari": ["mio"] 
    },
    {
        "nome": "Silent Hill 2 PS5",
        "url": "https://www.vinted.it/catalog?search_text=silent%20hill%202&catalog[]=3026&video_game_platform_ids[]=1281&order=newest_first",
        "prezzo_max": 25,
        "prezzo_minimo_digitale": 28.0,
        "parole_obbligatorie": ["silent", "hill", "2"],
        "parole_vietate": ["ps4", "xbox", "townfall", "f"], 
        "destinatari": ["mio"]
    }
]

# --- PAROLE VIETATE GLOBALI ---
PAROLE_VIETATE_GLOBALI = [
    "vuota", "vuoto", "solo-custodia", "solo-scatola", "solo-box", "senza-gioco", "no-gioco", "solo-codice",
    "vide", "boite-vide", "boitier-vide", "sans-jeu", "seul-boitier", "code-seul",
    "vacia", "vacio", "solo-caja", "sin-juego", "caja-vacia",
    "empty", "box-only", "case-only", "no-game", "code-only"
]

# --- USER AGENTS ROTANTI ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:123.0) Gecko/20100101 Firefox/123.0"
]

# Inizializza scraper come sessione globale
scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})

MEMORIA_FILE = "notified_items.txt"
LOG_FILE = "log_giornaliero.txt"
notified_items = set()

# Carica gli ID degli articoli (non gli interi URL, per risparmiare spazio)
if os.path.exists(MEMORIA_FILE):
    with open(MEMORIA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            item_id = line.strip()
            if item_id:
                notified_items.add(item_id)

def estrai_id_vinted(url):
    """Estrae l'ID numerico dall'URL dell'oggetto Vinted per un salvataggio più efficiente"""
    match = re.search(r'/items/(\d+)-', url)
    if match:
        return match.group(1)
    return url.split('/')[-1] # Fallback brutale

def salva_in_memoria(item_id):
    notified_items.add(item_id)
    with open(MEMORIA_FILE, "a", encoding="utf-8") as f:
        f.write(f"{item_id}\n")

def get_random_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
        "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "no-cache"
    }

def send_telegram_message(text, lista_destinatari=["mio"]):
    if not TELEGRAM_TOKEN:
        logging.error("Token mancante nei Secrets!")
        return
        
    for destinatario in lista_destinatari:
        id_da_usare = CHAT_ID_MIO if destinatario == "mio" else CHAT_ID_AMICO if destinatario == "amico" else None
            
        if id_da_usare:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {"chat_id": id_da_usare, "text": text, "parse_mode": "Markdown"}
            try:
                # Disabilita l'anteprima del link per messaggi più puliti
                payload["disable_web_page_preview"] = True
                requests.post(url, json=payload, timeout=10)
            except Exception as e:
                logging.error(f"Errore invio Telegram a {destinatario}: {e}")

def get_con_retry(url, max_retries=3):
    """Esegue una GET request con retry e backoff in caso di errori 403, 500, o timeout"""
    for attempt in range(max_retries):
        try:
            response = scraper.get(url, headers=get_random_headers(), timeout=15)
            
            if response.status_code == 200:
                return response
            elif response.status_code in [403, 429]:
                logging.warning(f"Ricevuto {response.status_code} su {url}. Tentativo {attempt+1}/{max_retries}")
                time.sleep(5 * (attempt + 1) + random.uniform(1, 3)) # Backoff incrementale con jitter
            else:
                logging.warning(f"Errore HTTP {response.status_code} su {url}. Tentativo {attempt+1}/{max_retries}")
                time.sleep(2 * (attempt + 1))
                
        except (requests.exceptions.RequestException, requests.exceptions.Timeout) as e:
             logging.warning(f"Errore di connessione: {e}. Tentativo {attempt+1}/{max_retries}")
             time.sleep(5)
             
    return None # Fallito dopo tutti i tentativi

def scansiona_singolo_url(ricerca):
    items_found = 0
    new_alerts = 0
    
    response = get_con_retry(ricerca["url"])
    
    if not response:
        return items_found, new_alerts, "Fallito"
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Cerca i contenitori dei prodotti, questo è più sicuro di cercare solo tag <a>
        # Vinted cambia spesso layout, ma solitamente i feed hanno attributi specifici
        feed_items = soup.find_all("div", attrs={"data-testid": lambda value: value and "item-box" in value})
        
        # Fallback se non trova 'item-box' (cerca tag <a> con /items/)
        if not feed_items:
             feed_items = []
             for a_tag in soup.find_all("a", href=True):
                 if "/items/" in a_tag["href"]:
                     # Cerca il div genitore che racchiude l'oggetto
                     parent = a_tag.find_parent("div", class_=lambda c: c and "feed" in c)
                     if parent and parent not in feed_items:
                         feed_items.append(parent)
                         
        if not feed_items:
             # Secondo Fallback: itera direttamente sui link come nel tuo script originale
             for a_tag in soup.find_all("a", href=True):
                 if "/items/" in a_tag["href"]:
                     href = a_tag["href"]
                     full_link = href if href.startswith("http") else f"https://www.vinted.it{href}"
                     item_id = estrai_id_vinted(href)
                     
                     if item_id in notified_items:
                         continue
                         
                     testo_completo = f"{href} {a_tag.get('title', '')} {a_tag.get_text()}".lower()
                     
                     if controlla_testo(testo_completo, ricerca):
                         prezzo = estrai_prezzo_da_testo(a_tag.parent.text if a_tag.parent else "")
                         if prezzo and prezzo <= ricerca["prezzo_max"]:
                              items_found += 1
                              invia_alert(ricerca, prezzo, full_link, item_id)
                              new_alerts += 1
             return items_found, new_alerts, response.status_code

        for item in feed_items:
            # Estrai Link
            link_tag = item.find("a", href=True)
            if not link_tag or "/items/" not in link_tag["href"]:
                continue
                
            href = link_tag["href"]
            full_link = href if href.startswith("http") else f"https://www.vinted.it{href}"
            item_id = estrai_id_vinted(href)
            
            if item_id in notified_items:
                continue

            testo_completo = item.get_text(" ").lower()
            
            # Filtro Parole
            if not controlla_testo(testo_completo, ricerca):
                continue
                
            # Estrai Prezzo (Cerchiamo testo che contiene € e convertiamo)
            prezzo_float = estrai_prezzo_da_testo(item.get_text(" "))
            
            if prezzo_float and prezzo_float <= ricerca["prezzo_max"]:
                items_found += 1
                invia_alert(ricerca, prezzo_float, full_link, item_id)
                new_alerts += 1
                
    return items_found, new_alerts, response.status_code

def controlla_testo(testo, ricerca):
    """Verifica se il testo rispetta i criteri di parole obbligatorie e vietate"""
    manca_parola = False
    for parola in ricerca["parole_obbligatorie"]:
        if len(parola) <= 2:
            if not re.search(rf'\b{re.escape(parola)}\b', testo):
                return False
        else:
            if parola not in testo:
                return False

    vietate_specifiche = ricerca.get("parole_vietate", [])
    tutte_le_vietate = vietate_specifiche + PAROLE_VIETATE_GLOBALI
    
    for vietata in tutte_le_vietate:
        if len(vietata) <= 2:
            if re.search(rf'\b{re.escape(vietata)}\b', testo):
                return False
        else:
            if vietata in testo:
                return False
                
    return True

def estrai_prezzo_da_testo(testo):
    """Estrae un valore numerico vicino al simbolo €"""
    match = re.search(r'([\d.,]+)\s*€', testo)
    if match:
        price_str = match.group(1).replace(".", "").replace(",", ".")
        try:
            return float(price_str)
        except ValueError:
            return None
    return None

def invia_alert(ricerca, prezzo, link, item_id):
    minimo_str = ""
    min_digitale = ricerca.get("prezzo_minimo_digitale")
    if min_digitale and min_digitale > 0:
        minimo_str = f"\n📉 Minimo storico digitale: {min_digitale}€"
    
    messaggio = f"🔥 *NUOVO AFFARE [{ricerca['nome']}]!*\nPrezzo Vinted: *{prezzo}€*{minimo_str}\n[🔗 Clicca qui per l'annuncio]({link})"
    
    chi_lo_riceve = ricerca.get("destinatari", ["mio"])
    send_telegram_message(messaggio, chi_lo_riceve)
    salva_in_memoria(item_id)

def gestisci_resoconto_mezzanotte():
    ora_attuale = datetime.datetime.now()
    if ora_attuale.hour == 0 and ora_attuale.minute < 10: # Finestra allargata a 10 min
        try:
            # Verifica se abbiamo già inviato il resoconto oggi (creando un file marcatore)
            marker_oggi = f"resoconto_inviato_{ora_attuale.strftime('%Y%m%d')}.txt"
            if not os.path.exists(marker_oggi):
                if os.path.exists(LOG_FILE):
                    with open(LOG_FILE, "r", encoding="utf-8") as file_log:
                        contenuto_diario = file_log.read()
                else:
                    contenuto_diario = "Nessuna scansione registrata nel file log."
                
                messaggio_resoconto = (
                    "📊 *RESOCONTO GIORNALIERO VINTED*\n\n"
                    f"{contenuto_diario[:3000]}\n" # Tronca per evitare limiti Telegram se file enorme
                    "🦉 Resoconto di mezzanotte completato!"
                )
                send_telegram_message(messaggio_resoconto, ["mio"])
                
                # Svuota il diario 
                open(LOG_FILE, "w", encoding="utf-8").close()
                
                # Crea marcatore e pulisci i vecchi
                with open(marker_oggi, 'w') as f: f.write('ok')
                for file in os.listdir("."):
                    if file.startswith("resoconto_inviato_") and file != marker_oggi:
                        os.remove(file)
                        
        except Exception as e:
            logging.error(f"Errore resoconto: {e}")

def check_vinted():
    gestisci_resoconto_mezzanotte()
    
    orario_attuale_str = datetime.datetime.now().strftime("%H:%M")
    totale_visti = 0
    totale_novita = 0
    stato_run = "✅ Ok"
    errori_riscontrati = []
    
    logging.info("Avvio scansione multi-articolo Vinted...")
    
    # Shuffle delle ricerche per variare i pattern di richiesta
    random.shuffle(RICERCHE)
    
    try:
        for idx, ricerca in enumerate(RICERCHE):
            if idx > 0:
                attesa = random.uniform(3, 7)
                logging.info(f"Pausa di {attesa:.2f}s anti-ban...")
                time.sleep(attesa)
                
            visti, novita, status = scansiona_singolo_url(ricerca)
            
            if status == "Fallito" or status != 200:
                stato_run = f"⚠️ Errori parziali"
                errori_riscontrati.append(f"{ricerca['nome']}: HTTP {status}")
            
            totale_visti += visti
            totale_novita += novita

    except Exception as e:
        stato_run = "❌ Errore Generale"
        logging.error(f"Errore critico durante lo scraping: {traceback.format_exc()}")
        send_telegram_message(f"⚠️ ATTENZIONE: Errore durante la scansione delle {orario_attuale_str}!\n\n`{str(e)}`", ["mio"])

    if errori_riscontrati:
        logging.warning(f"Errori parziali: {', '.join(errori_riscontrati)}")
        # Opzionale: decommenta la riga sotto se vuoi un messaggio Telegram per i 403 transitori
        # send_telegram_message(f"⚠️ Alert: Rilevati blocchi/errori su Vinted.\nDettagli: {', '.join(errori_riscontrati)}", ["mio"])

    # --- REGISTRAZIONE LOG (Solo l'ultima esecuzione del minuto) ---
    riga_log = f"🕒 {orario_attuale_str} | {stato_run} | Visti: {totale_visti} | Novità: {totale_novita}\n"
    
    gia_registrato = False
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            # Leggi dal fondo per essere veloce
            linee = f.readlines()
            if linee:
                ultima_riga = linee[-1]
                if f"🕒 {orario_attuale_str}" in ultima_riga:
                    gia_registrato = True

    if not gia_registrato:
        with open(LOG_FILE, "a", encoding="utf-8") as file_log:
            file_log.write(riga_log)

if __name__ == "__main__":
    print("=======================================")
    print("   Bot Vinted Action Avviato!          ")
    print("=======================================")
    check_vinted()
