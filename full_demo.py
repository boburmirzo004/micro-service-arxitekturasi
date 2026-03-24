import subprocess
import httpx
import asyncio
import os

LB_URL = os.getenv("LB_URL", "http://127.0.0.1:8000")
LB_HOST = os.getenv("LB_HOST", "127.0.0.1")

VENV_PATH = os.path.join(os.path.dirname(__file__), ".venv", "bin")
UVICORN_BIN = os.path.join(VENV_PATH, "uvicorn")

LIMITS = httpx.Limits(max_connections=1200, max_keepalive_connections=200)


async def sorovlar_yuborish(url):
    print(f"1000 ta sorov yuborilmoqda...")
    async with httpx.AsyncClient(limits=LIMITS, timeout=60.0) as client:
        tasks = [client.get(url) for _ in range(1000)]
        natijalar = await asyncio.gather(*tasks, return_exceptions=True)
        xatolar = len([r for r in natijalar if isinstance(r, Exception)])
        print(f"1000 ta sorov yakunlandi. (Xatoliklar: {xatolar})")


async def stats_tekshir(url):
    async with httpx.AsyncClient(timeout=10.0) as client:
        oldingi_jami = {}
        oldingi_sekin = {}

        for i in range(15):
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    active = data["details"]["active_connections"]
                    metrics = data.get("metrics", {})
                    per_service = metrics.get("per_service", {})

                    print(f"Vaqt: {i*1.0}s | Serverlardagi yuk:")

                    for service, active_count in active.items():
                        m = per_service.get(service, {})
                        total_now = m.get("total", 0)
                        slow_now = m.get("slow", 0)

                        prev_total = oldingi_jami.get(service, 0)
                        prev_slow = oldingi_sekin.get(service, 0)

                        yangi = total_now - prev_total
                        yangi_sekin = slow_now - prev_slow

                        print(
                            f"   {service}: aktiv={active_count}, "
                            f"bu_soniyada={yangi}, sekin={yangi_sekin}"
                        )
                        oldingi_jami[service] = total_now
                        oldingi_sekin[service] = slow_now
            except Exception:
                pass

            await asyncio.sleep(1.0)


async def start_demo():
    processes = []
    try:
        print("Servislar ishga tushirilmoqda...")
        for i in range(1, 4):
            p = subprocess.Popen(
                [UVICORN_BIN, f"service_{i}.main:app", "--host", LB_HOST, "--port", str(8000+i)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            processes.append(p)
        
        lb = subprocess.Popen(
            [UVICORN_BIN, "load_balancer.main:app", "--host", LB_HOST, "--port", "8000"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        processes.append(lb)
        
        print("Tayyor bolishini kutyapmiz (7 soniya)")
        await asyncio.sleep(7) 
        
        print("Demo boshlandi!")
        stats_task = asyncio.create_task(stats_tekshir(f"{LB_URL}/stats"))
        
        await asyncio.sleep(0.5)
        await sorovlar_yuborish(f"{LB_URL}/")
        
        await stats_task
        
    finally:
        print("\nTozalash, servislarni ochiramiz...")
        for p in processes:
            try:
                p.terminate()
            except:
                pass


if __name__ == "__main__":
    try:
        asyncio.run(start_demo())
    except KeyboardInterrupt:
        pass
