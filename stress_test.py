import subprocess
import httpx
import asyncio
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime

LB_URL = os.getenv("LB_URL", "http://127.0.0.1:8000")
LB_HOST = os.getenv("LB_HOST", "127.0.0.1")

VENV_PATH = os.path.join(os.path.dirname(__file__), ".venv", "bin")
UVICORN_BIN = os.path.join(VENV_PATH, "uvicorn")

LIMITS = httpx.Limits(max_connections=1200, max_keepalive_connections=200)

bosqich_nomlari = []
ok_list = []
err_list = []
latency_list = []
servis_taqsimot = {}


async def sorov_yubor(url, soni=100, nom=""):
    print(f"\n[{nom}] {soni} ta sorov yuborilmoqda...")
    kechikishlar = []
    servislar = {}
    async with httpx.AsyncClient(limits=LIMITS, timeout=30.0) as client:
        tasks = [client.get(url) for _ in range(soni)]
        natijalar = await asyncio.gather(*tasks, return_exceptions=True)
        xatolar = [r for r in natijalar if isinstance(r, Exception)]
        yaxshi = len(natijalar) - len(xatolar)
        for r in natijalar:
            if not isinstance(r, Exception):
                kechikishlar.append(r.elapsed.total_seconds() * 1000)
                try:
                    svc = r.json().get("service", "?")
                    servislar[svc] = servislar.get(svc, 0) + 1
                except:
                    pass
        print(f"  OK: {yaxshi} | Xato: {len(xatolar)}", flush=True)

        bosqich_nomlari.append(nom)
        ok_list.append(yaxshi)
        err_list.append(len(xatolar))
        ort = sum(kechikishlar) / len(kechikishlar) if kechikishlar else 0
        latency_list.append(ort)
        servis_taqsimot[nom] = servislar

        return yaxshi, len(xatolar)


async def stats_chiqar(url, label=""):
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(f"{url}/stats")
            data = resp.json()
            active = data["details"]["active_connections"]
            per_service = data.get("metrics", {}).get("per_service", {})
            total_req = data.get("metrics", {}).get("total_requests", 0)
            total_err = data.get("metrics", {}).get("total_errors", 0)

            print(f"\n{label} Statistika:")
            print(f"  Jami sorovlar: {total_req} | Xatoliklar: {total_err}")
            for service, info in per_service.items():
                a = active.get(service, 0)
                print(f"  {service}: aktiv={a}, jami={info['total']}, sekin={info['slow']}")
        except Exception as e:
            print(f"  Stats xato: {e}")


def grafik_chizar():
    fig, axes = plt.subplots(3, 1, figsize=(14, 12))
    fig.suptitle("Stress Test Natijalari", fontsize=14, fontweight="bold")

    x = range(len(bosqich_nomlari))

    ax1 = axes[0]
    ax1.bar(list(x), ok_list, label="Muvaffaqiyatli", color="#2ecc71")
    ax1.bar(list(x), err_list, bottom=ok_list, label="Xato", color="#e74c3c")
    ax1.set_ylabel("Sorovlar soni")
    ax1.set_title("Bosqichlar boyicha natija")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(bosqich_nomlari, rotation=30, ha="right", fontsize=7)
    ax1.legend()
    ax1.grid(axis="y", alpha=0.3)

    ax2 = axes[1]
    ranglar = ["#e74c3c" if lat > 500 else "#f39c12" if lat > 200 else "#2ecc71"
               for lat in latency_list]
    bars = ax2.bar(list(x), latency_list, color=ranglar)
    ax2.set_ylabel("Ortacha kechikish (ms)")
    ax2.set_title("Kechikish (qizil=sekin, yashil=tez)")
    ax2.set_xticks(list(x))
    ax2.set_xticklabels(bosqich_nomlari, rotation=30, ha="right", fontsize=7)
    ax2.grid(axis="y", alpha=0.3)
    for bar, lat in zip(bars, latency_list):
        ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                 f"{lat:.0f}ms", ha="center", va="bottom", fontsize=7)

    ax3 = axes[2]
    jami = {}
    for dist in servis_taqsimot.values():
        for svc, cnt in dist.items():
            jami[svc] = jami.get(svc, 0) + cnt
    if jami:
        ax3.pie(list(jami.values()), labels=list(jami.keys()),
                autopct="%1.1f%%", colors=["#3498db", "#2ecc71", "#e74c3c"], startangle=90)
        ax3.set_title("Umumiy servis taqsimoti")

    plt.tight_layout()
    vaqt = datetime.now().strftime("%Y%m%d_%H%M%S")
    nom = f"graph_stress_test_{vaqt}.png"
    plt.savefig(nom, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\nGrafik saqlandi: {nom}")


async def start_demo():
    processes = {}
    jami_ok = 0
    jami_err = 0

    try:
        print("Servislar ishga tushirilmoqda...")
        for i in range(1, 4):
            p = subprocess.Popen(
                [UVICORN_BIN, f"service_{i}.main:app", "--host", LB_HOST, "--port", str(8000 + i)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            processes[f"service_{i}"] = p

        lb = subprocess.Popen(
            [UVICORN_BIN, "load_balancer.main:app", "--host", LB_HOST, "--port", "8000"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        processes["lb"] = lb

        print("Tayyor bolishini kutyapmiz (7 soniya)...")
        await asyncio.sleep(7)

        print("\n" + "="*55)
        print("  BOSQICH 1: Normal holat, 3 ta server")
        print("="*55)
        s, e = await sorov_yubor(f"{LB_URL}/", soni=300, nom="Normal 300 ta")
        jami_ok += s; jami_err += e
        await stats_chiqar(LB_URL, "Bosqich 1")
        await asyncio.sleep(2)

        print("\n" + "="*55)
        print("  BOSQICH 2: 8001 server ochirildi!")
        print("="*55)
        processes["service_1"].terminate()
        print("8001 ochirildi, sorovlar yuborilmoqda...")
        await asyncio.sleep(1)

        s, e = await sorov_yubor(f"{LB_URL}/", soni=200, nom="8001 ochiq")
        jami_ok += s; jami_err += e

        print("Health checker 8001 ni aniqlamoqda (6 soniya)...")
        await asyncio.sleep(6)

        s, e = await sorov_yubor(f"{LB_URL}/", soni=200, nom="HC ochirgandan keyin")
        jami_ok += s; jami_err += e
        await stats_chiqar(LB_URL, "Bosqich 2")
        await asyncio.sleep(2)

        print("\n" + "="*55)
        print("  BOSQICH 3: 8002 ham ochirildi (faqat 8003 qoldi)")
        print("="*55)
        processes["service_2"].terminate()
        print("8002 ochirildi, faqat 8003 ishlaydi...")
        await asyncio.sleep(1)

        s, e = await sorov_yubor(f"{LB_URL}/", soni=200, nom="Faqat 8003")
        jami_ok += s; jami_err += e

        print("Health checker 8002 ni aniqlamoqda (6 soniya)...")
        await asyncio.sleep(6)

        s, e = await sorov_yubor(f"{LB_URL}/", soni=200, nom="HC 8002 ochirdi")
        jami_ok += s; jami_err += e
        await stats_chiqar(LB_URL, "Bosqich 3")
        await asyncio.sleep(2)

        print("\n" + "="*55)
        print("  BOSQICH 4: 8001 va 8002 qayta ishga tushirildi")
        print("="*55)
        for i in [1, 2]:
            p = subprocess.Popen(
                [UVICORN_BIN, f"service_{i}.main:app", "--host", LB_HOST, "--port", str(8000 + i)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            processes[f"service_{i}"] = p

        print("Health checker ularni qayta aniqlaydi (7 soniya)...")
        await asyncio.sleep(7)

        s, e = await sorov_yubor(f"{LB_URL}/", soni=300, nom="Hammasi tiklangan")
        jami_ok += s; jami_err += e
        await stats_chiqar(LB_URL, "Bosqich 4")
        await asyncio.sleep(2)

        print("\n" + "="*55)
        print("  BOSQICH 5: 600 ta request, yuk testi")
        print("="*55)
        s, e = await sorov_yubor(f"{LB_URL}/", soni=600, nom="600 ta parallel")
        jami_ok += s; jami_err += e
        await stats_chiqar(LB_URL, "Bosqich 5")

        jami = jami_ok + jami_err
        print("\n" + "="*55)
        print("  YAKUNIY NATIJA")
        print("="*55)
        print(f"  Jami yuborilgan:   {jami} ta")
        print(f"  Muvaffaqiyatli:    {jami_ok} ta")
        print(f"  Xato:              {jami_err} ta")
        print(f"  Foiz:              {round(jami_ok/jami*100, 1) if jami else 0}%")

        grafik_chizar()

    finally:
        print("\nTozalash, servislar ochirilmoqda...")
        for p in processes.values():
            try:
                p.terminate()
            except:
                pass


if __name__ == "__main__":
    try:
        asyncio.run(start_demo())
    except KeyboardInterrupt:
        pass