import requests
import re
import json
from datetime import datetime, timezone
import time
import winsound

########### CONFIGURAZIONE ###########
JSESSIONID         = "abc123xyz..."
ID_QUESTURA        = 000
TELEGRAM_BOT_TOKEN = "123456789:AAFxxxxxxx"
TELEGRAM_CHAT_ID   = "987654321"
DATA_MAXIMA        = "31/12/2026"
######################################

BASE = "https://passaportonline.poliziadistato.it"

# Session requests — mantiene cookie tra le chiamate
session = requests.Session()
session.cookies.set("JSESSIONID", JSESSIONID, domain="passaportonline.poliziadistato.it", path="/")
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0",
    "Accept-Language": "it-IT,it;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
})


def ts_to_date(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000).strftime("%d/%m/%Y")

def parse_data_maxima(data_str: str) -> float:
    dt = datetime.strptime(data_str, "%d/%m/%Y").replace(tzinfo=timezone.utc)
    return dt.timestamp() * 1000

def ottieni_csrf() -> str | None:
    """GET della pagina wizard per estrarre il CSRF dal meta tag."""
    try:
        r = session.get(
            f"{BASE}/cittadino/a/sc/wizardAppuntamentoCittadino/sceltaComune",
            timeout=30,
        )
        if not r.ok:
            print(f"  ⚠️ GET pagina fallito: HTTP {r.status_code}")
            return None

        # Controlla se siamo stati reindirizzati al login
        if "login" in r.url.lower():
            return None

        m = re.search(r'<meta[^>]+name="_csrf"[^>]+content="([^"]+)"', r.text)
        if not m:
            # Prova anche nell'ordine inverso degli attributi
            m = re.search(r'<meta[^>]+content="([^"]+)"[^>]+name="_csrf"', r.text)
        return m.group(1) if m else None

    except Exception as e:
        print(f"  ⚠️ Errore GET csrf: {e}")
        return None

def chiama_endpoint(csrf: str) -> dict | None:
    """POST all'endpoint disponibilità."""
    oggi_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00:00Z")
    body = {
        "sede": {"objectKey": ID_QUESTURA},
        "dataRiferimento": oggi_iso,
        "indietro": False,
    }
    try:
        r = session.post(
            f"{BASE}/cittadino/n/rc/v1/utility/elenca-agenda-appuntamenti-sede-mese",
            headers={
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
                "X-CSRF-TOKEN": csrf,
                "Origin": BASE,
                "Referer": f"{BASE}/cittadino/a/sc/wizardAppuntamentoCittadino/sceltaComune",
            },
            data=json.dumps(body),
            timeout=30,
        )
        return {"ok": r.ok, "status": r.status_code, "data": r.json() if r.ok else r.text[:300]}
    except Exception as e:
        print(f"  ⚠️ Errore POST: {e}")
        return None

def riproduci_suono_alert():
    try:
        winsound.Beep(600, 300); time.sleep(0.1)
        winsound.Beep(800, 300); time.sleep(0.1)
        winsound.Beep(1000, 500)
    except Exception as e:
        print(f"  ⚠️ Suono non disponibile: {e}")

def riproduci_suono_miglioramento():
    try:
        for _ in range(5):
            winsound.Beep(1200, 100)
            time.sleep(0.05)
    except Exception as e:
        print(f"  ⚠️ Suono non disponibile: {e}")

def invia_telegram(messaggio: str):
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": messaggio, "parse_mode": "HTML"},
            timeout=10,
        )
        if not resp.ok:
            print(f"  ⚠️ Telegram error: {resp.status_code} {resp.text[:200]}")
    except Exception as e:
        print(f"  ⚠️ Telegram exception: {e}")


# ─── AVVIO ───────────────────────────────────────────────────────
data_maxima_ts = parse_data_maxima(DATA_MAXIMA)
prima_data_trovata_ms: int | None = None

print(f"🚀 Monitor attivo — soglia massima: {DATA_MAXIMA}")
print("Ctrl+C per fermare\n")

# Verifica sessione iniziale
csrf = ottieni_csrf()
if not csrf:
    print("❌ SESSIONE SCADUTA all'avvio! Aggiorna JSESSIONID.")
    exit()
print(f"✅ Sessione valida — CSRF: {csrf}\n")

# ─── LOOP ────────────────────────────────────────────────────────
try:
    while True:
        now_str = datetime.now().strftime("%H:%M:%S")

        # Rinnova CSRF ogni ciclo (costa poco, evita problemi)
        csrf = ottieni_csrf()
        if not csrf:
            msg = f"[{now_str}] ❌ SESSIONE SCADUTA! Aggiorna JSESSIONID."
            print(msg)
            riproduci_suono_alert()
            invia_telegram(msg)
            break

        result = chiama_endpoint(csrf)
        if result is None:
            print(f"[{now_str}] ⚠️ Chiamata fallita, riprovo al prossimo ciclo")
            time.sleep(60)
            continue

        if result["ok"]:
            elenco = result["data"].get("elenco", [])
            if elenco:
                primo = elenco[0]
                giorno_ms = primo["giorno"]
                data_utile_str = f"{ts_to_date(giorno_ms)} {primo['ora']}"
                comune = primo["comune"]
                indirizzo = primo["indrizzo"]

                # Prima volta → memorizza riferimento
                if prima_data_trovata_ms is None:
                    prima_data_trovata_ms = giorno_ms
                    print(f"[{now_str}] 📌 Prima data trovata all'avvio: {data_utile_str}")

                # Caso 1: data entro soglia massima
                if giorno_ms < data_maxima_ts:
                    print(f"[{now_str}] 🔔 ALERT SOGLIA → {data_utile_str} < {DATA_MAXIMA}")
                    riproduci_suono_alert()
                    invia_telegram(
                        f"🔔 <b>Passaporto disponibile!</b>\n"
                        f"📅 Prima data: <b>{data_utile_str}</b>\n"
                        f"🏛 Questura di {comune} - {indirizzo} \n"
                        f"⏰ Rilevato alle {now_str}"
                    )

                # Caso 2: data migliorata rispetto all'avvio
                elif giorno_ms < prima_data_trovata_ms:
                    print(f"[{now_str}] 📉 MIGLIORAMENTO → {data_utile_str} (prima era {ts_to_date(prima_data_trovata_ms)})")
                    riproduci_suono_miglioramento()
                    invia_telegram(
                        f"📉 <b>Data migliorata!</b>\n"
                        f"📅 Nuova: <b>{data_utile_str}</b>\n"
                        f"📆 Precedente: <b>{ts_to_date(prima_data_trovata_ms)}</b>\n"
                        f"🏛 Questura di {comune} - {indirizzo} \n"
                        f"⏰ Rilevato alle {now_str}"
                    )
                    prima_data_trovata_ms = giorno_ms

            else:
                print(f"[{now_str}] Nessun slot libero")
        else:
            print(f"[{now_str}] HTTP {result['status']}: {result['data'][:100]}")

        time.sleep(60)

except KeyboardInterrupt:
    print("\n⏹️ Monitor fermato dall'utente")


