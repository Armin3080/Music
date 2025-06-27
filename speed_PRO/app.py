import os
import uuid
import yaml
import json
import subprocess
from fastapi import FastAPI, Request, Response, Depends, HTTPException, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from typing import Optional, List, Dict
from pydantic import BaseModel

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(SessionMiddleware, secret_key=os.urandom(24))

templates = Jinja2Templates(directory="templates")

# Security settings
security = HTTPBasic()

# Default admin credentials (should be hashed in production)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "speedproxy123"
SECRET_KEY = str(uuid.uuid4())

# Server settings
class Server(BaseModel):
    name: str
    address: str
    port: int
    protocol: str
    uuid: str = str(uuid.uuid4())
    alter_id: int = 64
    security: str = "auto"
    network: str = "tcp"
    is_active: bool = True

# Storage for settings and servers
settings = {
    "remote_dns": ["1.1.1.1,tls", "8.8.8.8,https"],
    "direct_dns": ["94.140.14.14", "9.9.9.9"],
    "selected_protocols": ["vless", "vmess", "trojan"],
    "selected_ports": [443, 2053, 8443],
    "enable_udp": False,
    "use_ipv6": False,
    "speed_boost": True,
    "bypass_china": True,
    "enable_ping": True,
    "custom_rules": []
}

servers: List[Server] = [
    Server(name="USA-1", address="us.example.com", port=443, protocol="vmess"),
    Server(name="Germany-1", address="de.example.com", port=443, protocol="vless"),
    Server(name="Japan-1", address="jp.example.com", port=2053, protocol="trojan")
]

# Authentication
def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    if (credentials.username != ADMIN_USERNAME or 
        credentials.password != ADMIN_PASSWORD):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Routes
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        response = RedirectResponse(url="/dashboard", status_code=303)
        return response
    return RedirectResponse(url="/?error=1", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, username: str = Depends(authenticate)):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "username": username,
        "settings": settings,
        "servers": servers,
        "protocols": ["vmess", "vless", "trojan", "shadowsocks", "hysteria"]
    })

@app.get("/api/settings")
async def get_settings(username: str = Depends(authenticate)):
    return settings

@app.post("/api/settings")
async def update_settings(new_settings: dict, username: str = Depends(authenticate)):
    global settings
    settings.update(new_settings)
    return {"status": "success", "message": "Settings updated"}

@app.get("/api/servers")
async def get_servers(username: str = Depends(authenticate)):
    return servers

@app.post("/api/servers")
async def add_server(server: Server, username: str = Depends(authenticate)):
    servers.append(server)
    return {"status": "success", "message": "Server added"}

@app.post("/api/ping")
async def ping_server(server: dict, username: str = Depends(authenticate)):
    try:
        result = subprocess.run(
            ["ping", "-c", "4", server["address"]],
            capture_output=True,
            text=True,
            timeout=10
        )
        return {"status": "success", "output": result.stdout}
    except Exception as e:
        return {"status": "error", "message": str(e)}

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
            "GEOIP,IR,DIRECT" if settings["bypass_china"] else "GEOIP,IR,PROXY",
            "MATCH,PROXY"
        ]
    }
    
    # Add proxies based on active servers
    for server in servers:
        if server.is_active:
            proxy = {
                "name": f"{server.name}-{server.protocol.upper()}",
                "type": server.protocol,
                "server": server.address,
                "port": server.port,
                "uuid": server.uuid if server.protocol in ["vmess", "vless"] else "",
                "password": server.uuid if server.protocol == "trojan" else "",
                "tls": True,
                "network": server.network
            }
            config["proxies"].append(proxy)
    
    # Add proxy groups
    config["proxy-groups"] = [
        {
            "name": "Auto-Select",
            "type": "url-test",
            "proxies": [p["name"] for p in config["proxies"]],
            "url": "http://www.gstatic.com/generate_204",
            "interval": 300
        },
        {
            "name": "Bypass-CN",
            "type": "select",
            "proxies": [p["name"] for p in config["proxies"]] + ["DIRECT"]
        }
    ]
    
    return Response(
        content=yaml.dump(config),
        media_type="application/yaml",
        headers={"Content-Disposition": "attachment; filename=clash.yaml"}
    )

@app.get("/subscribe/v2ray.txt")
async def generate_v2ray_config(username: str = Depends(authenticate)):
    config = {
        "inbounds": [],
        "outbounds": [
            {
                "protocol": "freedom",
                "tag": "direct"
            }
        ],
        "routing": {
            "domainStrategy": "IPIfNonMatch",
            "rules": []
        }
    }
    
    # Add routing rules for bypass
    if settings["bypass_china"]:
        config["routing"]["rules"].append({
            "type": "field",
            "outboundTag": "direct",
            "domain": ["geosite:cn"],
            "ip": ["geoip:cn", "geoip:ir"]
        })
    
    # Add outbound servers
    for server in servers:
        if server.is_active:
            outbound = {
                "tag": server.name,
                "protocol": server.protocol,
                "settings": {
                    "vnext" if server.protocol in ["vmess", "vless"] else "servers": [
                        {
                            "address": server.address,
                            "port": server.port,
                            "users": [{"id": server.uuid, "alterId": server.alter_id}]
                        }
                    ]
                },
                "streamSettings": {
                    "network": server.network,
                    "security": "tls"
                }
            }
            config["outbounds"].append(outbound)
    
    return Response(
        content=json.dumps(config, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=v2ray.json"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, ssl_keyfile="./key.pem", ssl_certfile="./cert.pem")