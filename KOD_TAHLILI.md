# Loyihadagi Har Bir Fayl va Ularning Kodlari Tahlili

Sizning so'rovingizga binoan, loyihangizning eng muhim yuragi hisoblangan **`load_balancer`** papkasidagi har bir fayl, undagi **har bir Class (Sinf)** va **har bir Funksiyaning** nima vazifa bajarishi, nima uchun kerakligi va aniq qanday ishlashi o'ta chuqur tahlil qilib chiqildi. Boshqa fayllar ham shunday batafsillikda yoritilgan.

---

## 1. `load_balancer/settings.py` (Loyiha Yuragi - Konfiguratsiya)

Bu fayl dastur ishlashi uchun barcha konstanstalar (o'zgarmaslar) saqlandigan mexanizm.

### `BaseSettings` dan olingan `Settings` klassi
**Nima ish bajaradi?** Barcha o'zgaruvchilarni bitta klass ichida birlashtirib, pydantic yordamida tiplarini (string, int) avtomatik tekshiradigan forma.
**Nima uchun kerak?** Atrof-muhit o'zgaruvchilarini (masalan `.env` dagi maxfiy va o'zgaruvchan IP manzillarni) avtomatik ravishda dastur xotirasiga tortib ishlata olish uchun.

**Ichki O'zgaruvchilar bo'yicha tushuntirish:**
- `HOST = "0.0.0.0"`: Load Balancer'ning server tarmog'ini belgilaydi. "0.0.0.0" bo'lgani unga nafaqat o'z kompyuteringizdan (localhost), balki butun ochiq tarmoqdan (internet, Wi-Fi) kirishga huquq (ruxsat) beradi.
- `PORT = 8000`: Qabul qilinadigan eshik posti.
- `BACKEND_SERVICES`: Ichida uchta server manzili tiqilgan `List` (ro'yxat). Load Balancer doimiy ularning tepasida boshqaruvchi sifatida turadi. Nima sababdan kerak? Agar server buzilsa va yangisi qo'shilsa kodni emas, faqat shu listni almashtirish kifoya.
- `SERVICE_WEIGHTS`: (Vaznlar) Bu Dict (lug'at) bo'lib har bir server qanday "kuchga" ekanini bildiradi (8001 ga 3 kuch, 8003 ga 1 kuch).
- `LB_ALGORITHM = "round_robin"`: Tizim qaysi matematik formula bilan tarqatadi. (Bu nom algorithms.py da o'qiladi).
- `HEALTH_CHECK_INTERVAL = 5`: Tizim har necha soniyada backend serverlarga xabar yozib eshik qoqib tekshirisini ko'rsatadigan qiymat (5 soniya).
- `MAX_RETRY_ATTEMPTS = 2`: Biror serverga ulanish o'xshamasa (masalan timeout qilsa), u o'zini yoqotib qoymasdan qancha marta uzatishga urinib ko'rish limiti (2 marta).
- `METRICS_WINDOW = 1000`: Eng oxirgi necha mingta request larning vaqti xotirada eslab qolinishligini saqlash chegarasi.
- `class Config`: Xuddi shu nomdagi qoida. Barcha parollar agar `.env` fayl tabiatida bo'lsa uni ko'ra olishi kerakligini Pydantic'ga buyuradi.

`settings = Settings()` — Bu kod so'ngiga borib barcha sozlamani o'rab olib faol obyektga yig'adi. Endi istalgan dastur faylimiz shunchaki `settings.PORT` qilib oson ma'lumotni o'qiydi.

---

## 2. `load_balancer/algorithms.py` (Mantiq va Matematika Markazi)

So'rovlarni to'g'ri taqsimlovchi algoritmlar arxitekturasi yozilgan joy. Bu fayl mutlaqo FastApi ga yohud networkka aralashmaydi, u quruq hisobchi (matematik logic).

### `LoadBalancer` Klassi
Tizim holatlari taqsimotini o'sish dinamikasida ushlab turuvchi Ob'yekt.

- **`__init__(self, services, weights)` funksiyasi:**
  - **Vazifasi:** Qachonki dastur ishlashni boshlasa o'z ichiga sog'lom serverlarni oladi (`self.services`).
  - **Nega kerak?** `self._connections` degan o'zgaruvchi yaratib, qaysi server hozir nechtata request ushlab turganini nol (0) taga o'rnatadi. 
  - Shuningdek, `self._build_weighted_pool()` ni birdaniga ishga tushiradi.
- **`_build_weighted_pool(self)` funksiyasi:**
  - **Vazifasi:** Agar 8001 server "3 vaznga", 8003 "1 vaznga" ega bo'lsa. Bu kod oddiy `[8001, 8002, 8003]` ro'yxatni -> `[8001, 8001, 8001, 8002, 8002, 8003]` ko'rinishida hovuz - list (pool) ga saqlaydi. 
  - **Nega kerak?** Chunki og'irlik (vazn) berilganda kod ichida murakkab qoldiq hisobga kirmaslik uchun tayyor sun'iy hovuz yaratiladi.
- **`update_services(self, healthy_services)` funksiyasi:**
  - **Vazifasi:** Health_check fayli yuborgan xabar, misol u 8002 o'ldi dsa, ro'yxatni yangolaydi (`self.services = healthy_services`).
  - **Qanday ishlaydi:** Eski va yangi ro'yxatni solishtiradi. O'zgargan bo'lsa hovuzlarni va taymer indekslarni nollab hammasini qayta ishga monand qiladi.
- **`get_next_service_round_robin(self)` funksiyasi:**
  - **Vazifasi:** 3 ta server tursa, index=0 degan joyini indeks=1 keyin indeks=2 keyin yana 0 qilib aylana bo'ylab qaytaradi.
  - **Asosiy Kod siri:** `(self._current_index + 1) % len(self.services)` - Ushbu mudol formulasi `%` indek va hovuz xajmidan chiqib ketmasin u doim 0,1,2,0,1,2 deya cheksiz xatosizlik sikliga tushushni ko'rsatib kelgan matematik formuladir.
- **`get_next_service_least_connections(self)` funksiyasi:**
  - **Vazifasi:** Eng kam yuk olganini izlaydi.
  - **Kod qanday ishladi:** `self._connections` bazasidan hamma qiymatlarini min() bilan eng minimum raqamini topib usha qiymati min ga teng serverlarni ro'yxatini shakllantirib uni yuboradi.
- **`increment_connection / decrement_connection` funksiyalari:**
  - So'rov ketdi: server yukini `+1` qilib oshirib qo'yadi. So'rov qaytdi (bitdi): uni yukidan `-1` ayirib qo'yadi. Tizim aniq bilib keladi kimda hozir haqiqatdan nechta connection "osilib" turibdi.

---

## 3. `load_balancer/health_check.py` (Salomatlik Nazorati va Tizim Sanitar O'qi)

Bu faylda maxsus asinxron jarayon orqali real rejimda (haqiqiy vaqtda backgroundda aylanib turgan) funksiya ishlaydi. 

### `HealthChecker` Klassi
- **`__init__(self, load_balancer)` funksiyasi:**
  - Klassni e'lon vaqti uning qo'liga qullik asosi - `LoadBalancer` matematik boshqaruvini tutqazadi. Sababi, biror server o'lsa borib uni aytib qo'yishi shart (`self.all_services`). `self.is_running` degan bayroqni saqlaydi.
- **`check_service(self, service_url)` funksiyasi:**
  - **Vazifasi:** Yakkalik so'rov beradi. `httpx.AsyncClient` orqali ikkinchi servering `/health` joyiga kiradi va uni 2 soniya (timeout=2) kutadi.
  - Agar javob kelsa 200 deb = `True` qaytaradi, javob unuman kelmay exception urilsa yoki tok uchgan bo'lsa = `False`.
- **`run_checks(self)` asinxron funksiyasi:**
  - Barcha muvaffaqiyat garovi: `while self.is_running:` kodi. Shu erda to'xtovchi tsikl ishga tushadi. 
  - `asyncio.gather(*tasks)` bir vaqtning o'zida parallel parallel orqa fondan o'sha 3ta serverni chaqirib natijani yig'adi.
  - Diqqat bilan kod kuzatsangiz agar natija `current_healthy != self.healthy_services` deylik bitta eskisi kasallanganu bu gap isbotini aniqlasa u daxol Load Balancerni `load_balancer.update_services` orqali urib uyg'otib ro'yxatni olib tashlatib qayta shakillantrishga maxkum etadi! Tizim endi yashashda davom etadi. Keyin `asyncio.sleep` olib aytilgan vaqt yana uxlaydi. 
- **`start(self)` funksiya:**
  - Boshlang'ich funksiyani shunchak `asyncio.create_task` fon madorida erkin suzishdaka oqim ko'rinishida yuborib dushni ishlatib yuboradi.

---

## 4. `load_balancer/circuit_breaker.py` (Zanjir Uzgich yoki Bloklash Tizimi)

Server ishlayaotsa-yu, lekin judayam uzoq o'ylanib turib va ishlatavermaydiga holatni payqab darmonsiz (charchagan) serverga bir mualiya (ja'zo/dam) vaqti beradigan funksional logika kodi.

### `CircuitBreaker` Klassi
- **`__init__` funksiyasi:** Unda 3 ta parametr e'tibor markazi: `failure_threshold=5` (5 marta xato yoki sekin ishlash sabrini ushlash), `recovery_time=30` (ja'zolansa 30 sekunt dam qay tarzda tuzaladi), `slow_threshold=2.0` (2 sekuntdown oshgan xar bir request ayblanadi). Shuningdek har bi server uchun axtalangan daftarlar dictionary (`_failures`, `_slow_count`, `_open_until`).
- **`is_open(self, service)` funksiyasi:**
  - **Vazofasi:** Dastur markazi "bu server bo'shku unga ma'lumot jo'naturingmi" deb so'rab keladi. Kold shunda `_open_until[service]` daftarga qarab e'tiborni beradi. (Agar time hozirgi xolatidan avvalgi 30 minut to'lgan bo'lsa ja'zo ochilgan hisobi va u loglar orqali "Ochildi" deydi - True/False qiymat tasdiqlaydi.
- **`record_slow(self, service, duration)` funksiyasi:**
  - So'rov bajarilgach 3 soniya ketsa. Bu funksiyaga tushadi `duration > self.slow_threshold` ekan!. Bu degani 3 katta 2 dan. Daftarni +1 qil. Qarab ko'radi ro'yxat daftari (limitiga etmadi? (5-taga). Etgan zahoti kod: `self._open_until = time.time() + self.recovery_time` qilib o'sha ondayoq uni tormozga otib bloklashi va ro'yhat serverlardan uni o'chirib ishlashini ma'ns qiladi.
- **`record_failure, record_success`:** Ish xaqiqiy buzuldimi failure += 1 e'lon deydi. Muvfoqyaikli keldmi unda ro'yxat kodi = 0 holiga garchi ja'zosi bitgan paytni ham tasdiqlaydi.

---

## 5. `load_balancer/main.py` (Magistral Qabulxona va Marshrutizatsiya)

Bu API Routerlaring fastApi mantiqlarga to'lgn obyekti. 

- **`lifespan` asinxron manager mantiq funksiyasi:** FastApidagi mutloq yangi amalyot. Ilova server yonib start olganda ishlashini bildiradi. Qarab ko'rsangiz eng boshida bu Load Balancer o'zining algoritmlari, tormozlari obyektlari yig'ib e'lon qilshdan `health_checker.start()` kabi amallar yoqib borib yuragini urib keladi. Yield so'zi server yotib to'xtagan vaqtda `aclose` ulashlarni chiroyli manzarali yopilishni o'rnatadi. 
- **`get_lb_stats` funksiyasi (stats ruti):** Siz `http://host/stats` ga kirsangi kod barcha Loadbalacger daftarlari (`get_stats()`) ko'radi. Ulardagi qator percentillar o'rtalama 95% - idx kabi maxsus tartiblar tortib ma'lumot JSON holda uzatarkan.
- **`proxy` asosiy marshrutlash (@app.api_route) funksiyasi:**
  1. Hamma kelgan signal ({path}), request GET/POST umuman farqi yq hamma shu proxy dominga ilinadi. Mantiqi:
  2. Mijoz yo'li `perf_counter()` bilan vaqt olyapti. 
  3. `for attempt in range(...)`: Bu for mantiq qachonki xoxlagn tarmoq xatoli bo'lib timout olingach uzilib qolaman demaslihi, ushbi for bir necha marta aylanb beradi.
  4. Ichida `circuit_breaker.is_open()` surab serverni yo'yadi. Yopiq bolsa tashlaydi. Open bolsa -> Algorimtz `get_next_service` orqali yengi server kordinatasini oladi.
  5. `load_balancer.increment_connection()` qilib Serverni yukini ko'paytrivolib uyoqga async o'zi httpx request otib so'raydi (qarab tursangiz client u yoq bilan oraliqqa tegmaydi o'rniga proxy beryatgan).
  6. Javob keldi: vaqtni qo'lida ushladi. Endi `circuit_breaker.record_slow` va `decrement` xolat ishlarni saqlab hammani ogohlantirib yopilmaydiku mijozga u o'ziniki bo'lgan `Response` mantiqin qaytarib ko'radi. 
  

#### XULOSA 
Bu tarmoq yondashivi, mantiqan har bir kod qatorli bir maxsus o'rinda har xil javobgar rol uchun terib chiqilgan. Yaxshi texnologiyalar aslo bir varroqqa mujjasam kilinmaydilar (Solid va clean architecture). Shu erda settings dan tortiv algorithms dagi nolik foiz bular faqat qoida - qiyomat ishlarni bajarishi evaziga main file hechqana obyeklar boshqarishiga bosh qottirmas ekanligin to'liq bayonnomasidir.
