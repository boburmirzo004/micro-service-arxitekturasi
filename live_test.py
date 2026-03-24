# serverlarni ozi ochmaydi, faqat sorov yuborib turadi
# siz ozingiz serverlarni ochirb qayta yoqasiz
# Ctrl+C bilan toxtatganda grafik saqlanadi

import httpx
import asyncio
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime

LB_URL = os.getenv("LB_URL", "http://127.0.0.1:8000")
HAR_RAUNDDA = int(os.getenv("REQUESTS_PER_ROUND", "20"))
PAUZA = int(os.getenv("PAUSE_BETWEEN_ROUNDS", "2"))

LIMITS = httpx.Limits(max_connections=100, max_keepalive_connections=20)

vaqtlar = []
ok_list = []
err_list = []
latency_list = []
jami_servislar = {}


def hozir():
    return datetime.now().strftime("%H:%M:%S")


async def sorov_yubor(url, soni, nom=""):
    print(f"\n[{hozir()}] [{nom}] {soni} ta sorov yuborilmoqda...")
    
    yaxshi = 0
    xato = 0
    kechikishlar = []
    servis_soni = {}

    async with httpx.AsyncClient(limits=LIMITS, timeout=10.0) as client:
        tasks = [client.get(url) for _ in range(soni)]
        natijalar = await asyncio.gather(*tasks, return_exceptions=True)

        for r in natijalar:
            if isinstance(r, Exception):
                xato += 1
            else:
                yaxshi += 1
                kechikishlar.append(r.elapsed.total_seconds() * 1000)
                try:
                    svc = r.json().get("service", "?")
                    servis_soni[svc] = servis_soni.get(svc, 0) + 1
                except:
                    pass

    print(f"  OK: {yaxshi} | Xato: {xato}", flush=True)
    
    if servis_soni:
        print(f"  Taqsimot:")
        for svc, cnt in sorted(servis_soni.items()):
            print(f"    {svc}: {cnt} ta  {'#' * cnt}")

    vaqtlar.append(hozir())
    ok_list.append(yaxshi)
    err_list.append(xato)
    ort = sum(kechikishlar) / len(kechikishlar) if kechikishlar else 0
    latency_list.append(ort)
    for svc, cnt in servis_soni.items():
        jami_servislar[svc] = jami_servislar.get(svc, 0) + cnt
    
    return yaxshi, xato


async def stats_chiqar(url):
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(f"{url}/stats")
            data = resp.json()
            metrics = data.get("metrics", {})
            per_service = metrics.get("per_service", {})
            
            print(f"\n  LB statistikasi:")
            print(f"    Jami sorovlar:  {metrics.get('total_requests', 0)}")
            print(f"    Jami xatolar:   {metrics.get('total_errors', 0)}")
            
            for svc, info in per_service.items():
                holat = "+" if info["total"] > 0 else "-"
                print(f"    [{holat}] {svc}: jami={info['total']}, sekin={info['slow']}")
        except Exception as e:
            print(f"  Stats xato: {e}")


def grafik_chizar():
    if not vaqtlar:
        return

    fig, axes = plt.subplots(3, 1, figsize=(14, 10))
    fig.suptitle("Live Test Natijalari", fontsize=14, fontweight="bold")

    x = range(len(vaqtlar))

    ax1 = axes[0]
    ax1.plot(list(x), ok_list, marker="o", color="#2ecc71",
             label="Muvaffaqiyatli", linewidth=2, markersize=4)
    ax1.plot(list(x), err_list, marker="x", color="#e74c3c",
             label="Xato", linewidth=2, markersize=6)
    ax1.fill_between(list(x), ok_list, alpha=0.15, color="#2ecc71")
    ax1.fill_between(list(x), err_list, alpha=0.15, color="#e74c3c")
    ax1.set_ylabel("Sorovlar soni")
    ax1.set_title("Raundlar boyicha natija")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(vaqtlar, rotation=45, ha="right", fontsize=7)
    ax1.legend()
    ax1.grid(alpha=0.3)

    ax2 = axes[1]
    ax2.plot(list(x), latency_list, marker="s", color="#3498db",
             linewidth=2, markersize=5)
    ax2.fill_between(list(x), latency_list, alpha=0.2, color="#3498db")
    ax2.set_ylabel("Ortacha kechikish (ms)")
    ax2.set_title("Kechikish")
    ax2.set_xticks(list(x))
    ax2.set_xticklabels(vaqtlar, rotation=45, ha="right", fontsize=7)
    ax2.grid(alpha=0.3)

    ax3 = axes[2]
    if jami_servislar:
        ax3.pie(list(jami_servislar.values()), labels=list(jami_servislar.keys()),
                autopct="%1.1f%%", colors=["#3498db", "#2ecc71", "#e74c3c"], startangle=90)
        ax3.set_title("Servis taqsimoti")

    plt.tight_layout()
    vaqt = datetime.now().strftime("%Y%m%d_%H%M%S")
    nom = f"graph_live_test_{vaqt}.png"
    plt.savefig(nom, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\nGrafik saqlandi: {nom}")


async def main():
    print("=" * 60)
    print("  LIVE TEST BOSHLANDI")
    print("=" * 60)
    print(f"\n  LB:          {LB_URL}")
    print(f"  Har raundda: {HAR_RAUNDDA} ta sorov")
    print(f"  Pauza:       {PAUZA} soniya")
    print(f"\n  Servislarni ozingiz ochiring/yoqing")
    print(f"  Toxtatish: Ctrl+C\n")

    # avval tekshirib koramiz
    print(f"[{hozir()}] Load Balancer tekshirilmoqda...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{LB_URL}/stats")
            if resp.status_code == 200:
                print("  Load Balancer ishlayapti!\n")
    except Exception as e:
        print(f"  Ulanib bolmadi: {e}")
        print(f"  Avval servislarni ishga tushiring!")
        return

    jami_ok = 0
    jami_err = 0
    raund = 0

    try:
        while True:
            raund += 1
            print("\n" + "=" * 60)
            print(f"  RAUND {raund}  [{hozir()}]")
            print("=" * 60)

            s, e = await sorov_yubor(f"{LB_URL}/", soni=HAR_RAUNDDA, nom=f"R{raund}")
            jami_ok += s
            jami_err += e

            if raund % 3 == 0:
                await stats_chiqar(LB_URL)

            jami = jami_ok + jami_err
            foiz = round(jami_ok / jami * 100, 1) if jami > 0 else 0
            print(f"\n  Umumiy: {jami_ok} ok / {jami_err} xato  ({foiz}%)")
            
            if e > 0:
                print(f"  Xatolar bor, biror servis ochirilganmi?")

            print(f"\n  {PAUZA}s pauza...")
            await asyncio.sleep(PAUZA)

    except KeyboardInterrupt:
        pass

    jami = jami_ok + jami_err
    foiz = round(jami_ok / jami * 100, 1) if jami > 0 else 0
    print("\n" + "=" * 60)
    print("  YAKUNIY NATIJA")
    print("=" * 60)
    print(f"  Jami raundlar:   {raund}")
    print(f"  Jami sorovlar:   {jami}")
    print(f"  Muvaffaqiyatli:  {jami_ok}")
    print(f"  Xato:            {jami_err}")
    print(f"  Foiz:            {foiz}%\n")

    await stats_chiqar(LB_URL)
    grafik_chizar()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
