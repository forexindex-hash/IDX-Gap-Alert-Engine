# ============================================================
# 🔥 GAP MEMORY ENGINE v9.2 (SNIPER + TELEGRAM FINAL)
# ============================================================

import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime

# ============================================================
# 📦 CONFIG
# ============================================================

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

TELEGRAM_TOKEN = "8471985466:AAFDMvezU7KDQ6E9PAckDK3Z29qvyzPGC7Q"
CHAT_ID = "1546867811"

pd.set_option('display.width', 180)

print("🔥 GAP MEMORY ENGINE v9.2 (SNIPER FINAL)")

today_date = datetime.today().strftime("%Y-%m-%d")

# ============================================================
# DATA
# ============================================================

data = yf.download(TICKERS, period="200d", group_by="ticker", auto_adjust=False, progress=False)

# ============================================================
# CORE FUNCTIONS
# ============================================================

def gap_remaining(prev_close, high):
    return (high - prev_close) / prev_close

def gap_progress(init_gap, remaining):
    return min(max(1 - abs(remaining / init_gap), 0), 1)

def body_strength(o,c,h,l):
    return abs(c-o)/(h-l+1e-9)

def demand_score(o,c,h,l):
    upper = h - max(o,c)
    lower = min(o,c) - l
    return lower/(upper+lower+1e-9)

def volume_spike(df):
    return df["Volume"].iloc[-1] > df["Volume"].tail(10).mean() * 1.5

def rejection_candle(o,c,h,l):
    body = abs(c-o)
    lower = min(o,c) - l
    return lower > body*1.5

# ============================================================
# INTELLIGENCE
# ============================================================

def trend_filter(df):
    ma20 = df["Close"].rolling(20).mean().iloc[-1]
    ma50 = df["Close"].rolling(50).mean().iloc[-1]
    price = df["Close"].iloc[-1]

    if price > ma20 > ma50:
        return "UP"
    elif price < ma20 < ma50:
        return "DOWN"
    else:
        return "SIDE"

# ✅ FIXED REBOUND (STRICT)
def rebound_signal(df):
    closes = df["Close"].tail(3).values
    return (closes[-1] > closes[-2] > closes[-3])

def gap_cluster_score(df, prev_close):
    highs = df["High"].values
    return sum(abs((highs - prev_close)/prev_close) < 0.02)

# ✅ NEW: exhaustion filter
def exhaustion(df):
    return df["Close"].iloc[-1] > df["Close"].rolling(5).max().iloc[-2]

# ============================================================
# SCORING
# ============================================================

def priority_score(progress, distance, age, gap_size, cluster):
    score = 0
    score += np.exp(-distance*5) * 40
    score += progress * 25
    score += (1 - min(abs(gap_size)/0.1,1)) * 10
    score += (1 - min(age/15,1)) * 10
    score += min(cluster/5,1) * 15

    if distance < 0.01 and progress > 0.5:
        score += 10

    return round(min(score,100),2)

def confidence_score(demand, strength, vol, reject, trend):
    base = (
        demand * 0.4 +
        strength * 0.3 +
        (1 if vol else 0) * 0.2 +
        (1 if reject else 0) * 0.1
    )

    if trend == "UP":
        base += 0.1
    elif trend == "DOWN":
        base -= 0.1

    return round(base,2)

def confidence_label(conf):
    if conf >= 0.6:
        return "HIGH"
    elif conf >= 0.4:
        return "MEDIUM"
    else:
        return "LOW"

# ============================================================
# ENGINE
# ============================================================

rows = []

for t in TICKERS:
    try:
        df = data[t].dropna()
        if len(df) < 60:
            continue

        trend = trend_filter(df)
        rebound = rebound_signal(df)

        for i in range(1,len(df)):

            prev_close = df.iloc[i-1]["Close"]
            gap_day = df.iloc[i]

            gap = (gap_day["Open"] - prev_close)/prev_close

            if gap > -0.01:
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

            if filled:
                continue

            progress = gap_progress(init_gap, remaining)
            age = len(df) - i - 1
            distance = abs(remaining)

            last = df.iloc[-1]
            o,c,h,l = last["Open"],last["Close"],last["High"],last["Low"]

            strength = body_strength(o,c,h,l)
            demand = demand_score(o,c,h,l)
            vol = volume_spike(df)
            reject = rejection_candle(o,c,h,l)

            cluster = gap_cluster_score(df.tail(30), prev_close)

            # =================================================
            # 🎯 SNIPER ZONE (FIXED)
            # =================================================

            sniper_zone = (
                (distance < 0.01) and
                (progress > 0.5) and
                (demand > 0.3) and
                ((trend == "UP") or (trend == "SIDE" and distance < 0.007))
            )

            trigger = (
                (
                    (demand > 0.6 and reject and vol) or
                    (vol and demand > 0.5)
                )
                and (strength > 0.2)
                and rebound
                and not exhaustion(df)
            )

            if sniper_zone and trigger:
                action = "🔥 SNIPER ENTRY"
            elif sniper_zone:
                action = "⚡ SNIPER READY"
            elif trend == "DOWN" and demand < 0.3:
                action = "❌ STRONG AVOID"
            elif progress > 0.3:
                action = "WAIT PULLBACK"
            else:
                action = "MONITOR"

            # ✅ FIXED ENTRY
            entry_zone = last["Close"] * (1 - distance*0.3)

            pscore = priority_score(progress, distance, age, init_gap, cluster)
            conf = confidence_score(demand, strength, vol, reject, trend)

            rows.append({
                "Ticker": t,
                "EventDate": df.index[i],
                "GapInit%": round(init_gap*100,2),
                "GapNow%": round(remaining*100,2),
                "Progress%": round(progress*100,1),
                "Distance%": round(distance*100,2),
                "Age": age,
                "Trend": trend,
                "Rebound": rebound,
                "Cluster": cluster,
                "Demand": round(demand,2),
                "Strength": round(strength,2),
                "VolSpike": vol,
                "Rejection": reject,
                "EntryZone": round(entry_zone,2),
                "PriorityScore": pscore,
                "Confidence": conf,
                "ConfLabel": confidence_label(conf),
                "SniperZone": sniper_zone,
                "Action": action
            })

    except:
        continue

df = pd.DataFrame(rows)

# ============================================================
# FILTER + PRIMARY
# ============================================================

if not df.empty:
    df = df[df["Age"] <= 15]

    df["Primary"] = False
    idx = df.groupby("Ticker")["PriorityScore"].idxmax()
    df.loc[idx, "Primary"] = True

# ============================================================
# 🛡️ MASTER GUARDRAIL
# ============================================================

elite = df[
    (df["Primary"] == True) &
    (df["SniperZone"] == True) &
    (df["Confidence"] >= 0.5) &
    (df["Distance%"] <= 1.2) &
    (df["Progress%"] >= 40)
].copy()

elite = elite.sort_values("PriorityScore", ascending=False).head(5)

# ============================================================
# TELEGRAM FORMAT
# ============================================================

def format_telegram(df):

    if df.empty:
        return "😴 No Sniper Setup Today"

    msg = "🔥 *GAP SNIPER ALERT*\n"
    msg += f"📅 {today_date}\n"
    msg += "━━━━━━━━━━━━━━━\n"

    for _, r in df.iterrows():
        msg += (
            f"\n🔥 *{r['Ticker']}*\n"
            f"Dist: `{r['Distance%']}%` | Prog: `{r['Progress%']}%`\n"
            f"Demand: `{r['Demand']}` | Conf: `{r['ConfLabel']}`\n"
            f"Score: `{r['PriorityScore']}`\n"
            f"Entry: `{r['EntryZone']}`\n"
        )

    msg += "\n━━━━━━━━━━━━━━━"
    msg += "\n⚠️ Sniper Mode Active"

    return msg

# ============================================================
# SEND TELEGRAM
# ============================================================

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "Markdown"
    }

    requests.post(url, data=payload)

# ============================================================
# EXECUTE
# ============================================================

msg = format_telegram(elite)
print(msg)

send_telegram(msg)
