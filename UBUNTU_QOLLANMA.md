# 🐧 Ubuntu Server uchun Maxsus Qollanma (Himoya Kuni Uchun)

Agar komissiya yoki ustozingiz sizga bom-bo'sh, yangi o'rnatilgan Windows kompyuterga qilingan **Ubuntu Server** ni berishsa, vahimaga tushmang! Loyihani ishga tushirish atigi 3 ta asosiy qadamdan iborat. Bu yerda siz yozishingiz kerak bo'lgan tayyor termin buyruqlari keltirilgan.

Barcha kompyuterlarga (Load Balancer uchun ham, 3 ta Service kompyuterlari uchun ham) bir xil ishlarni qilasiz.

---

## 1-QADAM: Eng kerakli dasturlarni Ubuntu-ga o'rnatish

Yangi Ubuntu serverda odatda eng so'nggi Python bo'ladi, lekin uning muhit yaratuvchisi (`venv`) bo'lmasligi mumkin. O'rnatish uchun terminalda quyidagi buyruqlarni yozasiz:

```bash
# Avval Ubuntu tizim paketlarini yangilab olamiz
sudo apt update

# Python muhitlari va pip ni o'rnatamiz
sudo apt install python3-venv python3-pip curl -y
```

---

## 2-QADAM: Loyiha kodlarini serverga tashlash va muhit tayyorlash

Loyihalik fleshkangizdan kodlarni (shu `microservice_demo` papkasini) Ubuntu kompyuterga nusxalaysiz. Keyin terminal orqali o'sha papkani ichiga kirasiz:

```bash
# Papka ichiga kirish (fleshkangiz yoki papkangiz nomiga qarab)
cd /home/user/microservice_demo

# Maxsus Python muhitini (Virtual Environment) yaratamiz:
python3 -m venv .venv

# Muhitni faollashtiramiz (ishga tushiramiz):
source .venv/bin/activate

# Barcha kerakli modullarni kompyuterga o'rnatamiz:
pip install fastapi httpx uvicorn pydantic-settings matplotlib
```

*(Eslatma: Agar shunga qadar xatosiz kelgan bo'lsangiz, demak ilova to'liq tayyor!)*

---

## 3-QADAM: IP manzilni aniqlash va xavfsizlik (Firewall) teshigini ochish

Ubuntu serverining IP manzilini bilishingiz muhim, chunki testlarni shunga qarab yuborasiz:

```bash
# Pk (shaxsiy IP) manzilni ko'rish:
hostname -I
# Natija shunga o'xshash chiqadi: 192.168.1.100
```

Agar universitet tarmog'ida kompyuterlar bir-birini ko'ra olmasa, himoyani (Firewall) ochish kerak bo'ladi. Bitta komanda kifoya:

```bash
# Load Balancer uchun (8000), Service'lar uchun (8001, 8002, 8003) portlarni ochiq qoldiramiz:
sudo ufw allow 8000/tcp
sudo ufw allow 8001/tcp
sudo ufw allow 8002/tcp
sudo ufw allow 8003/tcp
```

---

## 4-QADAM: Serverni ishga tushirish (FINISH)

Kodni o'zining roli bo'yicha ishga tushirasiz. (Komanda yozgandan keyin u fonda ishlashda davom etadi)

**Mabodo siz 1-kompyuterda bo'lsangiz (Service 1 roli uchun):**
```bash
uvicorn service_1.main:app --host 0.0.0.0 --port 8001
```

**Mabodo siz 2-kompyuterda bo'lsangiz (Service 2 roli uchun):**
```bash
uvicorn service_2.main:app --host 0.0.0.0 --port 8002
```

**Mabodo siz 3-kompyuterda bo'lsangiz (Service 3 roli uchun):**
```bash
uvicorn service_3.main:app --host 0.0.0.0 --port 8003
```

**Va nihoyat MARKAZ (Load Balancer) o'rnatilgan kompyuterda bo'lsangiz:**
```bash
uvicorn load_balancer.main:app --host 0.0.0.0 --port 8000
```

*Bo'ldi! Endi test faylingizdagi qaysi URLga test qilib (`live_test.py` yoki shunchaki darchada) yuborsangiz kompyuterlar go'zal tarzda integratsiyada ishlaydi.*
