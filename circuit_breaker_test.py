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

LIMITS = httpx.Limits(max_connections=100, max_keepalive_connections=20)

bosqich_nomlari = []
ok_list = []
err_list = []
latency_list = []


async def sorov_yubor(url, soni=20, nom=""):
    print(f"\n[{nom}] {soni} ta sorov yuborilmoqda...")
    kechikishlar = []
    async with httpx.AsyncClient(limits=LIMITS, timeout=10.0) as client:
        tasks = [client.get(url) for _ in range(soni)]
        natijalar = await asyncio.gather(*tasks, return_exceptions=True)
        xatolar = [r for r in natijalar if isinstance(r, Exception)]
        yaxshi = len(natijalar) - len(xatolar)
        for r in natijalar:
            if not isinstance(r, Exception):
                kechikishlar.append(r.elapsed.total_seconds() * 1000)
        print(f"  OK: {yaxshi} | Xato: {len(xatolar)}", flush=True)

        bosqich_nomlari.append(nom)
        ok_list.append(yaxshi)
        err_list.append(len(xatolar))
        ort = sum(kechikishlar) / len(kechikishlar) if kechikishlar else 0
        latency_list.append(ort)


async def stats_chiqar(url):
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(f"{url}/stats")
            data = resp.json()
            active = data["details"]["active_connections"]
            print(f"\nServis holati:")
            for servis, cnt in active.items():
                print(f"  {servis}: aktiv={cnt}")
        except Exception as e:
            print(f"  Stats xato: {e}")


def grafik_chizar():
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    fig.suptitle("Circuit Breaker Test Natijalari", fontsize=14, fontweight="bold")

    x = range(len(bosqich_nomlari))

    ax1 = axes[0]
    bars1 = ax1.bar([i - 0.2 for i in x], ok_list, 0.4,
                    label="Muvaffaqiyatli", color="#2ecc71")
    bars2 = ax1.bar([i + 0.2 for i in x], err_list, 0.4,
                    label="Xato", color="#e74c3c")
    ax1.set_ylabel("Sorovlar soni")
    ax1.set_title("Bosqichlar boyicha natija")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(bosqich_nomlari, rotation=25, ha="right", fontsize=8)
    ax1.legend()
    ax1.grid(axis="y", alpha=0.3)

    for bar in bars1:
        h = bar.get_height()
        if h > 0:
            ax1.text(bar.get_x() + bar.get_width()/2., h, str(int(h)),
                     ha="center", va="bottom", fontsize=8)
    for bar in bars2:
        h = bar.get_height()
        if h > 0:
            ax1.text(bar.get_x() + bar.get_width()/2., h, str(int(h)),
                     ha="center", va="bottom", fontsize=8)

    ax2 = axes[1]
    ax2.plot(list(x), latency_list, marker="o", color="#3498db",
             linewidth=2, markersize=8)
    ax2.fill_between(list(x), latency_list, alpha=0.2, color="#3498db")
    ax2.set_ylabel("Ortacha kechikish (ms)")
    ax2.set_title("Kechikish dinamikasi")
    ax2.set_xticks(list(x))
    ax2.set_xticklabels(bosqich_nomlari, rotation=25, ha="right", fontsize=8)
    ax2.grid(axis="y", alpha=0.3)
    for i, lat in enumerate(latency_list):
        ax2.annotate(f"{lat:.0f}ms", (i, lat), textcoords="offset points",
                     xytext=(0, 10), ha="center", fontsize=8)

    plt.tight_layout()
    vaqt = datetime.now().strftime("%Y%m%d_%H%M%S")
    nom = f"graph_circuit_breaker_{vaqt}.png"
    plt.savefig(nom, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\nGrafik saqlandi: {nom}")


async def start_demo():
    processes = {}
    try:
        print("Servislar ishga tushirilmoqda...")
        for i in range(1, 4):
            p = subprocess.Popen(
                [UVICORN_BIN, f"service_{i}.main:app", "--host", LB_HOST, "--port", str(8000 + i)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            processes[f"http://{LB_HOST}:{8000 + i}"] = p

        lb = subprocess.Popen(
            [UVICORN_BIN, "load_balancer.main:app", "--host", LB_HOST, "--port", "8000"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        print("Tayyor bolishini kutyapmiz (7 soniya)...")
        await asyncio.sleep(7)

        # normal holat
        print("\n" + "="*50)
        print("BOSQICH 1: Normal holat, 3 ta server ishlaydi")
        print("="*50)
        await sorov_yubor(f"{LB_URL}/", soni=20, nom="Normal holat")
        await stats_chiqar(LB_URL)
        await asyncio.sleep(2)

        # 8002 ni ochiramiz
        print("\n" + "="*50)
        print("BOSQICH 2: 8002 server ochirildi")
        print("="*50)
        processes[f"http://{LB_HOST}:8002"].terminate()
        await asyncio.sleep(1)

        print("8002 ochirilgan holda sorovlar yuborilmoqda...")
        for r in range(3):
            await sorov_yubor(f"{LB_URL}/", soni=10, nom=f"8002 ochiq (round {r+1})")
            await asyncio.sleep(2)

        await stats_chiqar(LB_URL)

        print("\nHealth checker 8002 ni aniqlamoqda (6 soniya)...")
        await asyncio.sleep(6)
        print("Health checker 8002 ni royxatdan chiqardi")

        print("\n" + "="*50)
        print("BOSQICH 3: Circuit breaker + Health checker ishlayapti")
        print("="*50)
        await sorov_yubor(f"{LB_URL}/", soni=20, nom="Faqat 8001+8003")
        await stats_chiqar(LB_URL)
        await asyncio.sleep(2)

        # 8002 qaytaramiz
        print("\n" + "="*50)
        print("BOSQICH 4: 8002 qayta ishga tushirildi")
        print("="*50)
        p = subprocess.Popen(
            [UVICORN_BIN, "service_2.main:app", "--host", LB_HOST, "--port", "8002"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        processes[f"http://{LB_HOST}:8002"] = p

        print("Health checker 8002 ni qayta aniqlaydi (6 soniya)...")
        await asyncio.sleep(6)

        print("\n" + "="*50)
        print("BOSQICH 5: Hammasi tiklandi, 3 ta server yana ishlaydi")
        print("="*50)
        await sorov_yubor(f"{LB_URL}/", soni=20, nom="Hammasi tiklangan")
        await stats_chiqar(LB_URL)

        grafik_chizar()

    finally:
        print("\nTozalash, servislarni ochiramiz...")
        for p in processes.values():
            try:
                p.terminate()
            except:
                pass
        try:
            lb.terminate()
        except:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(start_demo())
    except KeyboardInterrupt:
        pass