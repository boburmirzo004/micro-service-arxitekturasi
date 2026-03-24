## Microservice Load Balancing Demo

Bu loyiha FastAPI asosidagi oddiy mikroxizmatlar to‘plami va ular orasida yukni taqsimlovchi (load balancer) moduldan iborat. Maqsad – mikroxizmatlar arxitekturasi sharoitida turli load balancing algoritmlarini amaliy jihatdan ko‘rsatish va ularning farqlarini tajriba orqali tahlil qilish.

### Arxitektura

- **Load balancer**: `load_balancer/main.py`
  - Klientlardan kelgan barcha so‘rovlarni qabul qiladi.
  - So‘rovni qaysi servisga yuborishni `LoadBalancer` sinfi va tanlangan algoritm (`round_robin`, `random`, `least_connections`, `weighted_round_robin`) yordamida aniqlaydi.
  - `/stats` endpointi orqali hozirgi sog‘lom servislar, ulanishlar soni va boshqa statistikani qaytaradi.
- **Health check**: `load_balancer/health_check.py`
  - Har bir backend servisni ma’lum intervalda `/health` endpointi orqali tekshiradi.
  - Sog‘lom bo‘lmagan servislarni avtomatik ravishda rotatsiyadan chiqarib, sog‘lom bo‘lsa qayta qo‘shadi.
- **Yuk taqsimlash algoritmlari**: `load_balancer/algorithms.py`
  - Round robin
  - Weighted round robin
  - Random
  - Least connections
- **Mikroxizmatlar**: `service_1/main.py`, `service_2/main.py`, `service_3/main.py`
  - Har biri `/` endpointida kichik kechikish bilan javob qaytaradi (real tizimdagi turli ishlash tezliklarini simulyatsiya qiladi).
  - `/health` endpointi monitoring uchun ishlatiladi.
- **Demo va yuk testlari**:
  - `demo_monitoring.py` – real vaqtda `/stats` ni kuzatib, faol ulanishlar sonini chiqaradi.
  - `load_test.py`, `test_load.py` – turli hajmdagi so‘rovlar bilan yuk testi.
  - `full_demo.py` – barcha servislar va load balancerni ishga tushirish, so‘rov yuborish va statistikani ko‘rsatishni avtomatlashtirgan ssenariy.

### Mahalliy ishga tushirish (Poetry bilan)

1. Python 3.12 o‘rnatilganligiga ishonch hosil qiling.
2. Loyihaning ildiz papkasiga keling:

```bash
cd microservice_demo
```

3. Poetry orqali kutubxonalarni o‘rnating:

```bash
poetry install
```

4. Virtual muhitga kiring:

```bash
poetry shell
```

5. Uchta servisni alohida portlarda ishga tushiring:

```bash
uvicorn service_1.main:app --host 127.0.0.1 --port 8001
uvicorn service_2.main:app --host 127.0.0.1 --port 8002
uvicorn service_3.main:app --host 127.0.0.1 --port 8003
```

6. Load balancerni ishga tushiring:

```bash
uvicorn load_balancer.main:app --host 127.0.0.1 --port 8000
```

7. Endi barcha so‘rovlarni faqat balancerga yuborasiz:

```bash
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/stats
```

### Yuk testi va monitoring ssenariylari

- **Faol ulanishlarni ko‘rish uchun demo**:

```bash
python demo_monitoring.py
```

- **Katta hajmli yuk testi**:

```bash
python load_test.py
```

- **Teng taqsimlanishni tekshirish**:

```bash
python test_load.py
```

- **To‘liq avtomatlashtirilgan demo** (servislarni o‘zi ko‘taradi va yakunda o‘chiradi):

```bash
python full_demo.py
```

### Docker va Docker Compose bilan ishga tushirish

1. `Dockerfile` va `docker-compose.yml` fayllari yordamida barcha servislarni konteynerlarda ko‘tarish mumkin:

```bash
docker compose up --build
```

2. Load balancer tashqi porti `8000` ga map qilingan bo‘ladi:

```bash
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/stats
```

3. Konteynerlarni to‘xtatish:

```bash
docker compose down
```

### Testlarni ishga tushirish

Loyihadagi asosiy algoritmlar uchun unit testlar `tests/` papkasida joylashgan. Ulardan foydalanib, yuk taqsimlash logikasining to‘g‘riligini tekshirish mumkin.

```bash
poetry run pytest
```

### Asosiy g‘oya (qisqacha)

Loyiha mikroxizmatlar arxitekturasida:
- yukni turli algoritmlar yordamida taqsimlash;
- sog‘lom bo‘lmagan instanslarni avtomatik aniqlash va ularni yo‘ldan olish;
- real yuk ostida tizimning o‘zini qanday tutishini kuzatish

imkonini beradi. Shu orqali nazariy qismdagi load balancing konsepsiyalari amaliy misol orqali ko‘rsatib beriladi.

