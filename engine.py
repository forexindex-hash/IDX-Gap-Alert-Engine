# ============================================================
# 🔥 GAP MEMORY ENGINE v8.5 (ALERT ENGINE FINAL)
# ============================================================

import yfinance as yf
import pandas as pd
import numpy as np
import os
import requests
from datetime import datetime

# ============================================================
# 📦 CONFIG
# ============================================================

STATE_FILE = "alert_state.csv"

TICKERS = [
"AADI.JK","ACES.JK","ADMR.JK","ADRO.JK","AKRA.JK","AMMN.JK","AMRT.JK","ANTM.JK","ARTO.JK","ASII.JK",
"BBCA.JK","BBNI.JK","BBRI.JK","BBTN.JK","BMRI.JK","BREN.JK","BRMS.JK","BRPT.JK","BSDE.JK","BTPS.JK",
"BUKA.JK","BUMI.JK","CMRY.JK","CPIN.JK","CTRA.JK","CUAN.JK","DSNG.JK","DSSA.JK","ELSA.JK","EMTK.JK",
"ENRG.JK","ERAA.JK","ESSA.JK","EXCL.JK","GOTO.JK","HEAL.JK","HRTA.JK","HRUM.JK","ICBP.JK","INCO.JK",
"INDF.JK","INDY.JK","INKP.JK","INTP.JK","ISAT.JK","ITMG.JK","JPFA.JK","JSMR.JK","KIJA.JK","KLBF.JK",
"KPIG.JK","MAPA.JK","MAPI.JK","MBMA.JK","MDKA.JK","MEDC.JK","MIKA.JK","MTEL.JK","MYOR.JK","NCKL.JK",
"PANI.JK","PGAS.JK","PGEO.JK","PNLF.JK","PTBA.JK","PTRO.JK","PWON.JK","RAJA.JK","RATU.JK","SCMA.JK",
"SIDO.JK","SMGR.JK","SMRA.JK","SSIA.JK","TAPG.JK","TLKM.JK","TOWR.JK","UNTR.JK","UNVR.JK","WIFI.JK"
]

# 🔔 TELEGRAM CONFIG
TOKEN = "8471985466:AAFDMvezU7KDQ6E9PAckDK3Z29qvyzPGC7Q"
CHAT_ID = "1546867811"

# ============================================================
# 📲 TELEGRAM FUNCTION
# ============================================================

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# ============================================================
# 🚀 START
# ============================================================

print("🔥 GAP MEMORY ENGINE v8.5 ALERT ENGINE")

today = datetime.today().strftime("%Y-%m-%d")
print(f"\n📅 Date: {today}")

# ============================================================
# LOAD STATE
# ============================================================

if os.path.exists(STATE_FILE):
    prev = pd.read_csv(STATE_FILE)
else:
    prev = pd.DataFrame(columns=["Ticker","Status","Progress"])

# ============================================================
# DATA
# ============================================================

data = yf.download(TICKERS, period="120d", group_by="ticker", auto_adjust=False, progress=False)

# ============================================================
# FUNCTIONS
# ============================================================

def gap_remaining(prev_close, high):
    return (high - prev_close)/prev_close

def gap_progress(init_gap, remaining):
    return min(max(1 - abs(remaining/init_gap),0),1)

def demand(o,c,h,l):
    return (min(o,c)-l)/(h-l+1e-9)

def strength(o,c,h,l):
    return abs(c-o)/(h-l+1e-9)

def rejection(o,c,h,l):
    return (min(o,c)-l) > abs(c-o)*1.5

# ============================================================
# ENGINE
# ============================================================

rows = []

for t in TICKERS:
    try:
        df = data[t].dropna()
        if len(df) < 60:
            continue

        for i in range(1,len(df)):

            prev_close = df.iloc[i-1]["Close"]
            gap = (df.iloc[i]["Open"] - prev_close)/prev_close

            # 👉 GAP DOWN ONLY
            if gap > -0.02:
                continue

            init_gap = gap
            remaining = init_gap
            filled = False

            for j in range(i,len(df)):
                high = df.iloc[j]["High"]
                remaining = gap_remaining(prev_close, high)

                if remaining >= 0:
                    filled = True
                    break

            # 👉 SKIP FILLED
            if filled:
                continue

            prog = gap_progress(init_gap, remaining)

            last = df.iloc[-1]
            o,c,h,l = last["Open"],last["Close"],last["High"],last["Low"]

            d = demand(o,c,h,l)
            r = rejection(o,c,h,l)

            # ====================================================
            # 🔥 FLOW CLASSIFICATION
            # ====================================================

            if d < 0.2 and prog < 0.1:
                status = "DUMP"

            elif prog > 0.7 and d > 0.6 and r:
                status = "SNIPER"

            elif prog > 0.4:
                status = "SETUP"

            else:
                status = "EARLY"

            rows.append({
                "Ticker": t,
                "Status": status,
                "Progress": round(prog,2)
            })

    except:
        continue

df = pd.DataFrame(rows)

# ============================================================
# CURRENT STATE
# ============================================================

current = df.groupby("Ticker").last().reset_index()

# ============================================================
# MERGE PREVIOUS
# ============================================================

merged = current.merge(prev, on="Ticker", how="left", suffixes=("_now","_prev"))

# ============================================================
# ALERT ENGINE
# ============================================================

alerts_sniper = []
alerts_setup = []
alerts_danger = []

for _, r in merged.iterrows():

    prev_s = r["Status_prev"]
    now_s  = r["Status_now"]

    # 🔥 SNIPER ENTRY
    if now_s == "SNIPER" and prev_s != "SNIPER":
        alerts_sniper.append(r["Ticker"])

    # ⚡ SETUP UPGRADE
    if now_s == "SETUP" and prev_s == "EARLY":
        alerts_setup.append(r["Ticker"])

    # 💀 DANGER
    if now_s == "DUMP" and prev_s in ["SETUP","EARLY"]:
        alerts_danger.append(r["Ticker"])

# ============================================================
# SAVE STATE
# ============================================================

save = current.rename(columns={
    "Status":"Status",
    "Progress":"Progress"
})

save.to_csv(STATE_FILE, index=False)

# ============================================================
# OUTPUT + TELEGRAM
# ============================================================

print("\n🚨 ALERT SUMMARY")
print("="*60)

print("\n🔥 SNIPER TRIGGER:", alerts_sniper)
print("\n⚡ SETUP UPGRADE:", alerts_setup)
print("\n💀 DANGER:", alerts_danger)

# ============================================================
# SEND TELEGRAM
# ============================================================

if alerts_sniper:
    msg = "🔥 SNIPER ALERT\n" + "\n".join(alerts_sniper)
    send_telegram(msg)

if alerts_setup:
    msg = "⚡ SETUP UPGRADE\n" + "\n".join(alerts_setup)
    send_telegram(msg)

if alerts_danger:
    msg = "💀 DANGER\n" + "\n".join(alerts_danger)
    send_telegram(msg)
