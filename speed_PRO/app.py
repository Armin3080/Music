import os
import uuid
import yaml
from fastapi import FastAPI, Request, Response, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from typing import Optional

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(SessionMiddleware, secret_key=os.urandom(24))

templates = Jinja2Templates(directory="templates")

# تنظیمات امنیتی
security = HTTPBasic()

# تنظیمات پیش‌فرض
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "speedproxy123"
SECRET_KEY = str(uuid.uuid4())

# ذخیره‌سازی تنظیمات
settings = {
    "remote_dns": ["1.1.1.1,tls", "8.8.8.8,https"],
    "direct_dns": ["94.140.14.14", "9.9.9.9"],
    "selected_protocols": ["vless", "trojan"],
    "selected_ports": ["443", "2053", "8443"],
    "enable_udp": False,
    "use_ipv6": False,
    "speed_boost": True
}

# اعتبارسنجی کاربر
def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    if (credentials.username != ADMIN_USERNAME or 
        credentials.password != ADMIN_PASSWORD):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# صفحه لاگین
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# صفحه دشبورد
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, username: str = Depends(authenticate)):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "username": username,
        "settings": settings
    })

# دریافت تنظیمات
@app.get("/api/settings")
async def get_settings(username: str = Depends(authenticate)):
    return settings

# ذخیره تنظیمات
@app.post("/api/settings")
async def update_settings(new_settings: dict, username: str = Depends(authenticate)):
    global settings
    settings.update(new_settings)
    return {"status": "success", "message": "Settings updated"}

# تولید کانفیگ Clash
@app.get("/subscribe/clash.yaml")
async def generate_clash_config(username: str = Depends(authenticate)):
    config = {
        "port": 7890,
        "socks-port": 7891,
        "allow-lan": False,
        "mode": "rule",
        "log-level": "info",
        "proxies": [],
        "proxy-groups": [],
        "rules": [
            "DOMAIN-SUFFIX,google.com,PROXY",
            "DOMAIN-KEYWORD,facebook,PROXY",
            "GEOIP,IR,DIRECT",
            "MATCH,PROXY"
        ]
    }
    
    # اضافه کردن پروکسی‌ها بر اساس تنظیمات
    if "vless" in settings["selected_protocols"]:
        config["proxies"].append({
            "name": "VLESS-Proxy",
            "type": "vless",
            "server": "example.com",
            "port": settings["selected_ports"][0],
            "uuid": str(uuid.uuid4()),
            "tls": True
        })
    
    if "trojan" in settings["selected_protocols"]:
        config["proxies"].append({
            "name": "Trojan-Proxy",
            "type": "trojan",
            "server": "example.com",
            "port": settings["selected_ports"][1],
            "password": str(uuid.uuid4())
        })
    
    # اضافه کردن گروه‌های پروکسی
    config["proxy-groups"] = [
        {
            "name": "Auto",
            "type": "url-test",
            "proxies": [p["name"] for p in config["proxies"]],
            "url": "http://www.gstatic.com/generate_204",
            "interval": 300
        }
    ]
    
    return Response(
        content=yaml.dump(config),
        media_type="application/yaml",
        headers={"Content-Disposition": "attachment; filename=clash.yaml"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)