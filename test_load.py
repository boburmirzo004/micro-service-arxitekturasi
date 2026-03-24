# 200 ta sorov yuborib servislar taqsimoti va kechikishni analiz qiladi

import asyncio
import time
import os
from collections import Counter
from statistics import mean

import httpx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import datetime

LB_URL = os.getenv("LB_URL", "http://127.0.0.1:8000")
URL = f"{LB_URL}/"
NUM_REQUESTS = 200


async def sorovni_yuborish(client):
    start = time.time()
    try:
        response = await client.get(URL, timeout=5.0)
        latency = time.time() - start
        data = response.json()
        return {
            "status": "ok",
            "service": data.get("service", "Unknown"),
            "latency": latency,
        }
    except Exception as e:
        latency = time.time() - start
        return {
            "status": "error",
            "error": str(e),
            "latency": latency,
        }


def percentile(values, q):
    if not values:
        return None
    values_sorted = sorted(values)
    k = int(0.01 * q * (len(values_sorted) - 1))
    return values_sorted[k]


def grafik_chizar(servis_soni, kechikishlar, ok_soni, xato_soni, umumiy_vaqt, tezlik):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Load Test Natijalari", fontsize=14, fontweight="bold")

    ax1 = axes[0][0]
    nomlar = list(servis_soni.keys())
    qiymatlar = list(servis_soni.values())
    bars = ax1.bar(nomlar, qiymatlar, color=["#3498db", "#2ecc71", "#e74c3c"][:len(nomlar)])
    ax1.set_title("Servislar boyicha taqsimot")
    ax1.set_ylabel("Sorovlar soni")
    for bar, val in zip(bars, qiymatlar):
        ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                 str(val), ha="center", va="bottom", fontweight="bold")
    ax1.grid(axis="y", alpha=0.3)

    ax2 = axes[0][1]
    ax2.pie([ok_soni, xato_soni],
            labels=["Muvaffaqiyatli", "Xato"],
            autopct="%1.1f%%",
            colors=["#2ecc71", "#e74c3c"],
            startangle=90, explode=(0, 0.1))
    ax2.set_title("Natija nisbati")

    ax3 = axes[1][0]
    if kechikishlar:
        ax3.hist([l * 1000 for l in kechikishlar], bins=20, color="#3498db",
                 edgecolor="white", alpha=0.8)
        ort = mean(kechikishlar) * 1000
        ax3.axvline(ort, color="#e74c3c", linestyle="--", linewidth=2,
                    label=f"Ortacha: {ort:.1f}ms")
        p95 = percentile(kechikishlar, 95) * 1000
        ax3.axvline(p95, color="#f39c12", linestyle="--", linewidth=2,
                    label=f"P95: {p95:.1f}ms")
        ax3.legend()
    ax3.set_title("Kechikish taqsimoti")
    ax3.set_xlabel("Kechikish (ms)")
    ax3.set_ylabel("Sorovlar soni")
    ax3.grid(axis="y", alpha=0.3)

    ax4 = axes[1][1]
    ax4.axis("off")
    matn = (
        f"  Jami sorovlar:     {NUM_REQUESTS}\n"
        f"  Muvaffaqiyatli:    {ok_soni}\n"
        f"  Xato:              {xato_soni}\n"
        f"  Umumiy vaqt:       {umumiy_vaqt:.2f} s\n"
        f"  Tezlik:            {tezlik:.1f} sorov/s\n"
        f"  Ortacha kechikish: {mean(kechikishlar)*1000:.1f} ms\n"
        f"  P95:               {percentile(kechikishlar, 95)*1000:.1f} ms\n"
        f"  P99:               {percentile(kechikishlar, 99)*1000:.1f} ms"
    )
    ax4.text(0.1, 0.5, matn, transform=ax4.transAxes, fontsize=11,
             verticalalignment="center", fontfamily="monospace",
             bbox=dict(boxstyle="round,pad=0.5", facecolor="#ecf0f1", alpha=0.8))

    plt.tight_layout()
    vaqt = datetime.now().strftime("%Y%m%d_%H%M%S")
    nom = f"graph_load_test_{vaqt}.png"
    plt.savefig(nom, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\nGrafik saqlandi: {nom}")


async def main():
    print(f"Load Test: {NUM_REQUESTS} ta sorov yuborilmoqda...")
    print(f"Manzil: {URL}\n")

    async with httpx.AsyncClient() as client:
        tasks = [sorovni_yuborish(client) for _ in range(NUM_REQUESTS)]

        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()

    ok_natijalar = [r for r in results if r["status"] == "ok"]
    xato_natijalar = [r for r in results if r["status"] == "error"]

    servis_soni = Counter(r["service"] for r in ok_natijalar)

    print("--- Yuk taqsimlanishi ---")
    for service, count in sorted(servis_soni.items()):
        foiz = (count / NUM_REQUESTS) * 100
        print(f"| {service:15} | {count:3} ta | {foiz:5.1f}% |")

    umumiy_vaqt = end_time - start_time
    tezlik = NUM_REQUESTS / umumiy_vaqt

    kechikishlar = [r["latency"] for r in ok_natijalar]
    ort_kechikish = mean(kechikishlar) if kechikishlar else None
    p95 = percentile(kechikishlar, 95)
    p99 = percentile(kechikishlar, 99)

    print("-" * 45)
    print(f"Umumiy vaqt: {umumiy_vaqt:.2f} soniya")
    print(f"Tezlik: {tezlik:.2f} sorov/sek")
    print(f"Xato foizi: {(len(xato_natijalar) / NUM_REQUESTS) * 100:.2f}%")
    if ort_kechikish is not None:
        print(f"Ortacha kechikish: {ort_kechikish*1000:.1f} ms")
        print(f"95-percentil: {p95*1000:.1f} ms")
        print(f"99-percentil: {p99*1000:.1f} ms")
    print("-" * 45)

    if kechikishlar:
        grafik_chizar(dict(servis_soni), kechikishlar, len(ok_natijalar),
                      len(xato_natijalar), umumiy_vaqt, tezlik)


if __name__ == "__main__":
    asyncio.run(main())
