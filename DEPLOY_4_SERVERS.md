# 4 ta serverga joylash

Loyihani 4 ta alohida kompyuterga joylash qollanmasi.

## Tuzilishi

| Server | Rol | Port | Fayl |
|--------|-----|------|------|
| Server 1 | Load Balancer | 8000 | load_balancer/main.py |
| Server 2 | Service 1 | 8001 | service_1/main.py |
| Server 3 | Service 2 | 8002 | service_2/main.py |
| Server 4 | Service 3 | 8003 | service_3/main.py |


## 1. Serverlarning IP manzilini toping

Windows: `ipconfig` buyrugi, IPv4 Address qatoriga qarang.

macOS: `ifconfig | grep "inet " | grep -v 127.0.0.1`

Linux: `hostname -I`


## 2. Tarmoqni tekshiring

Barcha serverlardan biri birini ping qiling:

```
ping 192.168.1.101
ping 192.168.1.102
ping 192.168.1.103
```

Agar javob bermasa Firewall tekshiring.


## 3. Firewall

Windows (Administrator CMD):
```
netsh advfirewall firewall add rule name="Microservice Demo" dir=in action=allow protocol=TCP localport=8000-8003
```

Linux:
```
sudo ufw allow 8000:8003/tcp
```


## 4. Kodni nusxalash

Loyiha papkasini 4 ta serverga nusxalang (USB yoki git clone).


## 5. Python o'rnatish

Har bir serverda:

```
pip install fastapi httpx uvicorn pydantic-settings matplotlib
```

Yoki poetry bilan:
```
poetry install
```


## 6. Server 1 da .env sozlash

```
cp .env.example .env
```

.env ichida real IP larni yozing:

```
HOST=0.0.0.0
PORT=8000
BACKEND_SERVICES=["http://192.168.1.101:8001","http://192.168.1.102:8002","http://192.168.1.103:8003"]
SERVICE_WEIGHTS={"http://192.168.1.101:8001": 3, "http://192.168.1.102:8002": 2, "http://192.168.1.103:8003": 1}
LB_ALGORITHM=round_robin
```


## 7. Ishga tushirish

Tartib muhim, avval backend keyin load balancer.

Server 2:
```
poetry run uvicorn service_1.main:app --host 0.0.0.0 --port 8001
```

Server 3:
```
poetry run uvicorn service_2.main:app --host 0.0.0.0 --port 8002
```

Server 4:
```
poetry run uvicorn service_3.main:app --host 0.0.0.0 --port 8003
```

Server 1 (eng oxirida):
```
poetry run uvicorn load_balancer.main:app --host 0.0.0.0 --port 8000
```


## 8. Tekshirish

Har bir servisni alohida:
```
curl http://192.168.1.101:8001/health
curl http://192.168.1.102:8002/health
curl http://192.168.1.103:8003/health
```

Load Balancer orqali:
```
curl http://192.168.1.100:8000/
```

Statistika:
```
curl http://192.168.1.100:8000/stats
```

Brauzerda: `http://192.168.1.100:8000/stats`


## Xatolar

| Xato | Yechim |
|------|--------|
| Connection refused | Servisni qayta ishga tushiring, Firewall tekshiring |
| 503 Service Unavailable | Backend servislar ishlamayapti |
| TimeoutError | ping bilan tarmoqni tekshiring |
| Address already in use | `lsof -i :8001` yoki `netstat -ano \| findstr 8001` |
