# PassaportoChecker 🔔

Monitor automatico per appuntamenti passaporto — notifiche Telegram in tempo reale.

Monitora la disponibilità di appuntamenti su [Agenda Passaporti](https://passaportonline.poliziadistato.it) (Polizia di Stato) e invia notifiche Telegram quando viene trovata una data utile entro la soglia impostata.

---

## Funzionalità

- 🔔 **Notifica soglia** — avvisa se la prima data libera è entro la `DATA_MAXIMA` impostata
- 📉 **Notifica miglioramento** — avvisa se viene trovata una data migliore rispetto a quella rilevata all'avvio
- ❌ **Notifica sessione scaduta** — avvisa quando il `JSESSIONID` non è più valido
- 🔊 **Suono** — beep di notifica su Windows
- ♻️ **Loop automatico** — controllo ogni 60 secondi

---

## Requisiti

```
pip install requests
```

> ⚠️ Lo script usa `winsound` che è disponibile **solo su Windows**.

---

## Configurazione

Apri `main.py` e modifica le seguenti variabili nella sezione **CONFIGURAZIONE**.

---

### `JSESSIONID`

Cookie di sessione necessario per autenticarsi al portale.

**Come ottenerlo:**
1. Accedi con SPID su [passaportonline.poliziadistato.it](https://passaportonline.poliziadistato.it)
2. Apri i **DevTools** del browser (`F12`)
3. Vai in **Application** → **Cookies** → `https://passaportonline.poliziadistato.it`
4. Copia il valore di `JSESSIONID`

```python
JSESSIONID = "abc123xyz..."
```

> ⚠️ Il `JSESSIONID` scade periodicamente. Quando lo script notifica "SESSIONE SCADUTA", ripeti questa procedura e aggiorna il valore.

---

### `ID_QUESTURA`

ID numerico della questura/ufficio passaporti da monitorare.

**Come ottenerlo:**
1. Accedi su [passaportonline.poliziadistato.it](https://passaportonline.poliziadistato.it)
2. Naviga nel wizard fino alla pagina di selezione data/ora:
   `Nuova richiesta → Passaporto Elettronico → Passo 1 di 6 Prenota un appuntamento in Questura → Passo 2 di 6 Scegli la sede che preferisci → Passo 3 di 6 Scegli la data e l'orario` (non proseguire)
3. Apri i **DevTools** (`F12`) → tab **Network**
4. Cerca la chiamata `elenca-agenda-appuntamenti-sede-mese`
5. Clicca su **Payload** e leggi il valore di `"sede": { "objectKey": xxx }`

```python
ID_QUESTURA = 184  # esempio: Questura di Como
```

---

### `TELEGRAM_BOT_TOKEN`

Token del bot Telegram che invia le notifiche.

**Come ottenerlo:**
1. Apri Telegram e cerca [@BotFather](https://t.me/BotFather)
2. Invia `/newbot` e segui le istruzioni
3. Copia il token fornito (formato: `123456789:AAFxxxxxxx`)

```python
TELEGRAM_BOT_TOKEN = "123456789:AAFxxxxxxx"
```

---

### `TELEGRAM_CHAT_ID`

ID della chat Telegram su cui ricevere le notifiche.

**Come ottenerlo:**
1. Apri Telegram e cerca [@IDBot](https://t.me/myidbot)
2. Invia `/getid`
3. Copia l'ID fornito (formato: `987654321`)

```python
TELEGRAM_CHAT_ID = "987654321"
```

---

### `DATA_MAXIMA`

Data entro cui vuoi ricevere la notifica di disponibilità (formato `DD/MM/YYYY`).

```python
DATA_MAXIMA = "30/04/2026"
```

---

## Avvio

```
python main.py
```

Output di esempio:
```
🚀 Monitor attivo — soglia massima: 30/04/2026
Ctrl+C per fermare

✅ Sessione valida — CSRF: 7497e2c9-ccf5-...

[10:00:01] 📌 Prima data trovata all'avvio: 05/11/2026 9.00
[10:01:01] ✗ 05/11/2026 9.00 (nessun miglioramento)
[10:02:01] 📉 MIGLIORAMENTO → 03/11/2026 10.00 (prima era 05/11/2026)
[10:03:01] 🔔 ALERT SOGLIA → 28/04/2026 9.00 < 30/04/2026
```

---

## Note

- Lo script richiede un **account SPID attivo** per ottenere un `JSESSIONID` valido
- Il `JSESSIONID` ha una durata limitata — va aggiornato manualmente quando scade
- Il monitor è pensato per **uso personale** e non si occupa della prenotazione effettiva
