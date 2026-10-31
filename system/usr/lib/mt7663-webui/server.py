#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MediaTek MT7663 Router Web UI Manager
FiberHome HG680-FJ (Amlogic S905X2 / Meson G12A)
Lightweight HTTP API & Web Dashboard using Bottle.py
"""

import os
import sys
import re
import json
import secrets
import subprocess
import platform
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

try:
    from bottle import Bottle, request, response, static_file, ServerAdapter
except ImportError:
    print("[ERROR] bottle.py not found in", BASE_DIR)
    sys.exit(1)

from wsgiref.simple_server import WSGIServer, make_server
from socketserver import ThreadingMixIn

app = Bottle()

HOSTAPD_CONF = "/etc/hostapd/hostapd-mt7663.conf"
DEFAULT_CONF = "/etc/default/mt7663-hotspot"
HOSTAPD_PID = "/run/mt7663-hostapd.pid"
DNSMASQ_PID = "/run/mt7663-dnsmasq.pid"
DNSMASQ_LEASES = "/var/lib/misc/dnsmasq.leases"
HOTSPOT_SCRIPT = "/usr/sbin/mt7663-hotspot"

SESSION_FILE = "/var/lib/misc/mt7663-sessions.json"
SESSION_EXPIRY_SEC = 86400  # 24 hours

def load_sessions():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_sessions(sessions):
    try:
        with open(SESSION_FILE, "w") as f:
            json.dump(sessions, f)
    except Exception:
        pass

# ----------------- Helper Functions -----------------

def run_cmd(cmd, timeout=15):
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout)
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def is_pid_running(pid_file):
    if not os.path.exists(pid_file):
        return False
    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        return True
    except (ValueError, OSError):
        return False

def format_bytes(bytes_count):
    if bytes_count < 1024:
        return f"{bytes_count} B"
    elif bytes_count < 1024 * 1024:
        return f"{round(bytes_count / 1024, 1)} KB"
    elif bytes_count < 1024 * 1024 * 1024:
        return f"{round(bytes_count / (1024 * 1024), 1)} MB"
    else:
        return f"{round(bytes_count / (1024 * 1024 * 1024), 2)} GB"

# ----------------- Authentication Helpers -----------------

def get_auth_credentials():
    user = "admin"
    password = "admin"
    if os.path.exists(DEFAULT_CONF):
        with open(DEFAULT_CONF, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("WEBUI_USER="):
                    user = line.split("=", 1)[1].strip().strip('"').strip("'")
                elif line.startswith("WEBUI_PASS="):
                    password = line.split("=", 1)[1].strip().strip('"').strip("'")
    return user, password

def is_authenticated():
    token = request.get_cookie("router_session")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
    
    if not token:
        return False
    
    sessions = load_sessions()
    if token not in sessions:
        return False
    
    # Check expiry
    created = sessions[token]
    if time.time() - created > SESSION_EXPIRY_SEC:
        del sessions[token]
        save_sessions(sessions)
        return False
    
    return True

# ----------------- Metrics & Config Readers -----------------

def get_system_metrics():
    # Uptime
    uptime_sec = 0
    try:
        with open("/proc/uptime", "r") as f:
            uptime_sec = int(float(f.readline().split()[0]))
    except Exception:
        pass
    
    # Loadavg
    loadavg = [0.0, 0.0, 0.0]
    try:
        with open("/proc/loadavg", "r") as f:
            parts = f.readline().split()
            loadavg = [float(parts[0]), float(parts[1]), float(parts[2])]
    except Exception:
        pass

    # RAM
    ram_total = 0
    ram_avail = 0
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    ram_total = int(line.split()[1]) * 1024
                elif line.startswith("MemAvailable:"):
                    ram_avail = int(line.split()[1]) * 1024
    except Exception:
        pass
    ram_used = ram_total - ram_avail
    ram_percent = round((ram_used / ram_total * 100), 1) if ram_total > 0 else 0

    # Temperature
    temp_c = 0.0
    for tz in ["/sys/class/thermal/thermal_zone0/temp", "/sys/class/thermal/thermal_zone1/temp"]:
        if os.path.exists(tz):
            try:
                with open(tz, "r") as f:
                    val = float(f.read().strip())
                    temp_c = round(val / 1000.0, 1) if val > 1000 else round(val, 1)
                    break
            except Exception:
                pass

    return {
        "hostname": platform.node(),
        "kernel": platform.release(),
        "uptime_sec": uptime_sec,
        "loadavg": loadavg,
        "ram_total_mb": round(ram_total / (1024 * 1024), 1),
        "ram_used_mb": round(ram_used / (1024 * 1024), 1),
        "ram_percent": ram_percent,
        "temperature_c": temp_c
    }

def read_hostapd_config():
    # Load stored width and security from default config first
    d_cfg = read_default_config()
    config = {
        "ssid": "HG680_5G_VHT80",
        "channel": 36,
        "band": "5",
        "width": d_cfg.get("width", 80),
        "security": d_cfg.get("security", "WPA2-PSK"),
        "passphrase": "password123",
        "hw_mode": "a"
    }
    has_wpa = False
    key_mgmt = "WPA-PSK"
    vht_width = None
    has_ht40 = False

    if os.path.exists(HOSTAPD_CONF):
        with open(HOSTAPD_CONF, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("ssid="):
                    config["ssid"] = line.split("=", 1)[1]
                elif line.startswith("channel="):
                    try:
                        config["channel"] = int(line.split("=", 1)[1])
                    except ValueError:
                        pass
                elif line.startswith("hw_mode="):
                    config["hw_mode"] = line.split("=", 1)[1]
                    config["band"] = "2.4" if config["hw_mode"] == "g" else "5"
                elif line.startswith("wpa_passphrase="):
                    config["passphrase"] = line.split("=", 1)[1]
                elif line.startswith("wpa="):
                    has_wpa = True
                elif line.startswith("wpa_key_mgmt="):
                    key_mgmt = line.split("=", 1)[1]
                elif line.startswith("vht_oper_chwidth="):
                    vht_width = line.split("=", 1)[1].strip()
                elif line.startswith("ht_capab="):
                    if "[HT40" in line:
                        has_ht40 = True

    # Accurately resolve bandwidth width
    if vht_width == "1":
        config["width"] = 80
    elif vht_width == "0":
        if has_ht40:
            config["width"] = 40
        else:
            config["width"] = 20

    if not has_wpa:
        config["security"] = "OPEN"
    elif "SAE" in key_mgmt and "WPA-PSK" in key_mgmt:
        config["security"] = "WPA2-WPA3"
    elif "SAE" in key_mgmt:
        config["security"] = "WPA3"
    else:
        config["security"] = "WPA2-PSK"

    return config

def read_default_config():
    config = {
        "gateway": "192.168.4.1",
        "netmask": "255.255.255.0",
        "cidr": "24",
        "dhcp_start": 10,
        "dhcp_end": 100,
        "dhcp_lease": "12h",
        "dns_servers": "1.1.1.1,8.8.8.8",
        "mtu": 1408,
        "width": 80,
        "security": "WPA2-PSK",
        "webui_user": "admin"
    }
    if os.path.exists(DEFAULT_CONF):
        with open(DEFAULT_CONF, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or not line:
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    v = v.strip().strip('"').strip("'")
                    if k == "AP_GATEWAY": config["gateway"] = v
                    elif k == "AP_NETMASK": config["netmask"] = v
                    elif k == "AP_CIDR": config["cidr"] = v
                    elif k == "DHCP_START":
                        try: config["dhcp_start"] = int(v)
                        except ValueError: pass
                    elif k == "DHCP_END":
                        try: config["dhcp_end"] = int(v)
                        except ValueError: pass
                    elif k == "DHCP_LEASE": config["dhcp_lease"] = v
                    elif k == "DNS_SERVERS": config["dns_servers"] = v
                    elif k == "AP_MTU":
                        try: config["mtu"] = int(v)
                        except ValueError: pass
                    elif k == "AP_WIDTH":
                        try: config["width"] = int(v)
                        except ValueError: pass
                    elif k == "AP_SECURITY": config["security"] = v
                    elif k == "WEBUI_USER": config["webui_user"] = v
    return config

def get_iptables_traffic():
    """Reads byte counts from iptables HOTSPOT_ACCT chain for per-client UP and DOWN stats"""
    traffic = {} # {ip: {"up_bytes": 0, "down_bytes": 0}}
    code, stdout, _ = run_cmd(["iptables", "-nvx", "-L", "HOTSPOT_ACCT"])
    if code != 0 or not stdout:
        return traffic

    for line in stdout.splitlines():
        parts = line.split()
        if len(parts) >= 9 and parts[2] == "RETURN":
            try:
                byte_count = int(parts[1])
                src = parts[7]
                dst = parts[8]
                if src != "0.0.0.0/0":
                    traffic.setdefault(src, {"up_bytes": 0, "down_bytes": 0})
                    traffic[src]["up_bytes"] = byte_count
                elif dst != "0.0.0.0/0":
                    traffic.setdefault(dst, {"up_bytes": 0, "down_bytes": 0})
                    traffic[dst]["down_bytes"] = byte_count
            except (ValueError, IndexError):
                pass

    return traffic

def ensure_client_accounting(ip):
    """Ensures iptables rules exist in HOTSPOT_ACCT for this client IP"""
    run_cmd(["iptables", "-C", "HOTSPOT_ACCT", "-s", ip, "-j", "RETURN"])
    code_up, _, _ = run_cmd(["iptables", "-C", "HOTSPOT_ACCT", "-s", ip, "-j", "RETURN"])
    if code_up != 0:
        run_cmd(["iptables", "-A", "HOTSPOT_ACCT", "-s", ip, "-j", "RETURN"])
    
    code_down, _, _ = run_cmd(["iptables", "-C", "HOTSPOT_ACCT", "-d", ip, "-j", "RETURN"])
    if code_down != 0:
        run_cmd(["iptables", "-A", "HOTSPOT_ACCT", "-d", ip, "-j", "RETURN"])

DEVICE_CACHE_FILE = "/var/lib/misc/mt7663-devices.json"

def load_device_cache():
    cache = {"82:5e:a8:d0:da:a1": "Phantom"}
    if os.path.exists(DEVICE_CACHE_FILE):
        try:
            with open(DEVICE_CACHE_FILE, "r") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    cache.update(loaded)
        except Exception:
            pass
    else:
        save_device_cache(cache)
    return cache

def save_device_cache(cache):
    try:
        with open(DEVICE_CACHE_FILE, "w") as f:
            json.dump(cache, f, indent=2)
    except Exception:
        pass

def get_connected_clients():
    clients = []
    seen_macs = set()
    traffic_data = get_iptables_traffic()
    device_cache = load_device_cache()
    cache_dirty = False
    
    # 1. Read dnsmasq leases
    if os.path.exists(DNSMASQ_LEASES):
        try:
            with open(DNSMASQ_LEASES, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        mac = parts[1].lower()
                        ip = parts[2]
                        raw_name = parts[3]
                        
                        if raw_name not in ["*", "Unknown", "?"]:
                            device_cache[mac] = raw_name
                            cache_dirty = True
                            name = raw_name
                        else:
                            name = device_cache.get(mac, "Unknown")

                        if mac not in seen_macs:
                            seen_macs.add(mac)
                            ensure_client_accounting(ip)
                            c_traf = traffic_data.get(ip, {"up_bytes": 0, "down_bytes": 0})
                            clients.append({
                                "ip": ip,
                                "mac": mac,
                                "name": name,
                                "status": "ACTIVE",
                                "up_bytes": c_traf["up_bytes"],
                                "down_bytes": c_traf["down_bytes"],
                                "up_str": format_bytes(c_traf["up_bytes"]),
                                "down_str": format_bytes(c_traf["down_bytes"])
                            })
        except Exception:
            pass

    # 2. Check ARP state via ip neigh show dev ap0
    code, stdout, _ = run_cmd(["ip", "neigh", "show", "dev", "ap0"])
    if code == 0 and stdout:
        neigh_states = {}
        for line in stdout.splitlines():
            parts = line.split()
            if len(parts) >= 4 and "lladdr" in parts:
                ip = parts[0]
                mac = parts[parts.index("lladdr") + 1].lower()
                state = parts[-1]
                neigh_states[mac] = (ip, state)

        # Update existing clients state
        for c in clients:
            if c["mac"] in neigh_states:
                c["status"] = neigh_states[c["mac"]][1]
                if c["name"] == "Unknown" and c["mac"] in device_cache:
                    c["name"] = device_cache[c["mac"]]

        # Add any ARP entries not found in leases
        for mac, (ip, state) in neigh_states.items():
            if mac not in seen_macs and state in ["REACHABLE", "DELAY", "PROBE", "STALE"]:
                seen_macs.add(mac)
                ensure_client_accounting(ip)
                c_traf = traffic_data.get(ip, {"up_bytes": 0, "down_bytes": 0})
                name = device_cache.get(mac, "Unknown")
                clients.append({
                    "ip": ip,
                    "mac": mac,
                    "name": name,
                    "status": state,
                    "up_bytes": c_traf["up_bytes"],
                    "down_bytes": c_traf["down_bytes"],
                    "up_str": format_bytes(c_traf["up_bytes"]),
                    "down_str": format_bytes(c_traf["down_bytes"])
                })

    if cache_dirty:
        save_device_cache(device_cache)

    return clients

def get_interfaces_info():
    interfaces = {}
    for iface in ["eth0", "wlan0", "ap0"]:
        code, stdout, _ = run_cmd(["ip", "-4", "-o", "addr", "show", "dev", iface])
        ip_addr = None
        if code == 0 and stdout:
            m = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+/\d+)", stdout)
            if m:
                ip_addr = m.group(1)
        
        # Link state
        code_link, stdout_link, _ = run_cmd(["ip", "link", "show", "dev", iface])
        is_up = ("state UP" in stdout_link) if code_link == 0 else False
        
        interfaces[iface] = {
            "ip": ip_addr,
            "up": is_up
        }
    
    # Get default gateway
    code, stdout, _ = run_cmd(["ip", "route", "show", "default"])
    default_route = None
    if code == 0 and stdout:
        default_route = stdout.splitlines()[0]
    
    return interfaces, default_route

def get_wifi_client_status():
    code, stdout, _ = run_cmd(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "dev", "status"])
    status = {
        "connected": False,
        "ssid": None,
        "connection": None,
        "ip": None,
        "signal": 0
    }
    if code == 0 and stdout:
        for line in stdout.splitlines():
            parts = line.split(":")
            if len(parts) >= 4 and parts[0] == "wlan0":
                state = parts[2]
                con_name = parts[3]
                if state == "connected":
                    status["connected"] = True
                    status["connection"] = con_name
                    # Query iw link for frequency and band
                    code_l, out_l, _ = run_cmd(["iw", "dev", "wlan0", "link"])
                    if code_l == 0 and out_l:
                        m_f = re.search(r"freq:\s+(\d+)", out_l)
                        if m_f:
                            f_val = int(m_f.group(1))
                            status["freq"] = f_val
                            status["band"] = "5" if f_val >= 5000 else "2.4"
                            status["channel"] = ((f_val - 5000) // 5) if f_val >= 5000 else ((f_val - 2407) // 5)
                    # Find active SSID
                    code_ap, stdout_ap, _ = run_cmd(["nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,BARS", "dev", "wifi", "list"])
                    if code_ap == 0 and stdout_ap:
                        for row in stdout_ap.splitlines():
                            cols = row.split(":")
                            if len(cols) >= 3 and cols[0] == "*":
                                status["ssid"] = cols[1]
                                try:
                                    status["signal"] = int(cols[2])
                                except ValueError:
                                    pass
                                break

    # IP of wlan0
    code_ip, stdout_ip, _ = run_cmd(["ip", "-4", "-o", "addr", "show", "dev", "wlan0"])
    if code_ip == 0 and stdout_ip:
        m = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+)", stdout_ip)
        if m:
            status["ip"] = m.group(1)

    return status

# ----------------- REST API Endpoints -----------------

@app.hook('after_request')
def enable_cors():
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'

# Auth Endpoints
@app.route('/api/auth/login', method=['POST'])
def api_auth_login():
    data = request.json or {}
    user_input = str(data.get("username", "")).strip()
    pass_input = str(data.get("password", "")).strip()
    
    stored_user, stored_pass = get_auth_credentials()
    if user_input == stored_user and pass_input == stored_pass:
        token = secrets.token_hex(24)
        sessions = load_sessions()
        sessions[token] = time.time()
        save_sessions(sessions)
        response.set_cookie("router_session", token, path="/", max_age=SESSION_EXPIRY_SEC, httponly=False)
        return {"status": "ok", "token": token, "username": stored_user}
    else:
        response.status = 401
        return {"status": "error", "message": "Invalid username or password (Username atau password salah)."}

@app.route('/api/auth/logout', method=['POST'])
def api_auth_logout():
    token = request.get_cookie("router_session")
    if token:
        sessions = load_sessions()
        if token in sessions:
            del sessions[token]
            save_sessions(sessions)
    response.delete_cookie("router_session", path="/")
    return {"status": "ok", "message": "Logged out successfully."}

@app.route('/api/auth/check', method=['GET'])
def api_auth_check():
    auth_ok = is_authenticated()
    user, _ = get_auth_credentials()
    return {"status": "ok", "authenticated": auth_ok, "username": user if auth_ok else None}

@app.route('/api/auth/change_password', method=['POST'])
def api_auth_change_password():
    if not is_authenticated():
        response.status = 401
        return {"status": "error", "message": "Unauthorized. Please log in first."}

    data = request.json or {}
    current_pass = str(data.get("current_password", "")).strip()
    new_user = str(data.get("new_username", "")).strip()
    new_pass = str(data.get("new_password", "")).strip()

    stored_user, stored_pass = get_auth_credentials()
    if current_pass != stored_pass:
        response.status = 400
        return {"status": "error", "message": "Current password is incorrect (Password saat ini salah)."}

    if not new_user or len(new_user) < 3:
        response.status = 400
        return {"status": "error", "message": "Username must be at least 3 characters."}

    if not new_pass or len(new_pass) < 4:
        response.status = 400
        return {"status": "error", "message": "Password must be at least 4 characters."}

    # Update DEFAULT_CONF
    cfg = read_default_config()
    content = f"""# MediaTek MT7663 Hotspot Network Configuration
# FiberHome HG680-FJ (Amlogic S905X2 / Meson G12A)

AP_GATEWAY="{cfg['gateway']}"
AP_NETMASK="{cfg['netmask']}"
AP_CIDR="{cfg['cidr']}"
DHCP_START="{cfg['dhcp_start']}"
DHCP_END="{cfg['dhcp_end']}"
DHCP_LEASE="{cfg['dhcp_lease']}"
DNS_SERVERS="{cfg['dns_servers']}"
AP_MTU="{cfg['mtu']}"
AP_WIDTH="{cfg['width']}"
AP_SECURITY="{cfg['security']}"

WEBUI_USER="{new_user}"
WEBUI_PASS="{new_pass}"
"""
    try:
        with open(DEFAULT_CONF, "w") as f:
            f.write(content)
        return {"status": "ok", "message": "Username and password updated successfully (Kredensial berhasil diperbarui)."}
    except Exception as e:
        response.status = 500
        return {"status": "error", "message": f"Failed to save credentials: {e}"}

# Main Status API
@app.route('/api/status', method=['GET'])
def api_status():
    hostapd_running = is_pid_running(HOSTAPD_PID)
    dnsmasq_running = is_pid_running(DNSMASQ_PID)
    hotspot_cfg = read_hostapd_config()
    net_cfg = read_default_config()
    clients = get_connected_clients() if (hostapd_running and dnsmasq_running) else []
    interfaces, default_route = get_interfaces_info()
    wifi_client = get_wifi_client_status()
    sys_metrics = get_system_metrics()

    # Parse Upstream WAN info
    upstream = {
        "connected": False,
        "type": "none",
        "interface": None,
        "name": "Tidak Ada Koneksi",
        "name_en": "No Connection",
        "ip": "-",
        "gateway": "-"
    }
    if default_route:
        m_dev = re.search(r"dev\s+(\w+)", default_route)
        m_gw = re.search(r"via\s+([\d\.]+)", default_route)
        m_src = re.search(r"src\s+([\d\.]+)", default_route)
        if m_dev:
            dev = m_dev.group(1)
            upstream["connected"] = True
            upstream["interface"] = dev
            upstream["gateway"] = m_gw.group(1) if m_gw else "-"
            dev_ip = interfaces.get(dev, {}).get("ip")
            upstream["ip"] = dev_ip if dev_ip else (m_src.group(1) if m_src else "-")
            if dev == "eth0":
                upstream["type"] = "ethernet"
                upstream["name"] = "Kabel LAN (eth0)"
                upstream["name_en"] = "Ethernet Cable (eth0)"
            elif dev == "wlan0":
                upstream["type"] = "wifi"
                ssid_name = wifi_client.get("ssid") or "Wi-Fi"
                upstream["name"] = f"Wi-Fi Rumah ({ssid_name})"
                upstream["name_en"] = f"Home Wi-Fi ({ssid_name})"
            else:
                upstream["type"] = "other"
                upstream["name"] = dev
                upstream["name_en"] = dev

    return {
        "status": "ok",
        "system": sys_metrics,
        "hotspot": {
            "active": hostapd_running and dnsmasq_running,
            "hostapd_running": hostapd_running,
            "dnsmasq_running": dnsmasq_running,
            "ssid": hotspot_cfg["ssid"],
            "channel": hotspot_cfg["channel"],
            "width": hotspot_cfg["width"],
            "security": hotspot_cfg["security"],
            "gateway": net_cfg["gateway"],
            "cidr": net_cfg["cidr"],
            "netmask": net_cfg["netmask"],
            "dhcp_start": net_cfg["dhcp_start"],
            "dhcp_end": net_cfg["dhcp_end"],
            "dns_servers": net_cfg["dns_servers"],
            "clients": clients,
            "client_count": len(clients)
        },
        "wifi_client": wifi_client,
        "upstream": upstream,
        "interfaces": interfaces,
        "default_route": default_route
    }

@app.route('/api/hotspot/config', method=['GET'])
def api_get_hotspot_config():
    h_cfg = read_hostapd_config()
    d_cfg = read_default_config()
    wifi_client = get_wifi_client_status()
    interfaces, _ = get_interfaces_info()
    eth_conn = (interfaces.get("eth0", {}).get("carrier") == 1) or (interfaces.get("eth0", {}).get("ip") is not None)
    return {
        "ssid": h_cfg["ssid"],
        "band": h_cfg.get("band", "5"),
        "passphrase": h_cfg["passphrase"],
        "channel": h_cfg["channel"],
        "width": h_cfg.get("width", 80),
        "security": h_cfg.get("security", "WPA2-PSK"),
        "gateway": d_cfg["gateway"],
        "netmask": d_cfg["netmask"],
        "cidr": d_cfg["cidr"],
        "dhcp_start": d_cfg["dhcp_start"],
        "dhcp_end": d_cfg["dhcp_end"],
        "dns_servers": d_cfg["dns_servers"],
        "mtu": d_cfg["mtu"],
        "wlan_connected": wifi_client.get("connected", False),
        "wlan_band": wifi_client.get("band", "none"),
        "wlan_freq": wifi_client.get("freq", 0),
        "eth_connected": eth_conn
    }

@app.route('/api/hotspot/config', method=['POST'])
def api_save_hotspot_config():
    if not is_authenticated():
        response.status = 401
        return {"status": "error", "message": "Unauthorized. Please log in first."}

    data = request.json or {}
    
    ssid = str(data.get("ssid", "")).strip()
    security = str(data.get("security", "WPA2-PSK")).strip().upper()
    passphrase = str(data.get("passphrase", "")).strip()
    band = str(data.get("band", "5")).strip()
    if band not in ["2.4", "5"]:
        band = "5"

    try:
        channel = int(data.get("channel", 6 if band == "2.4" else 36))
    except ValueError:
        channel = 6 if band == "2.4" else 36
    try:
        width = int(data.get("width", 40 if band == "2.4" else 80))
    except ValueError:
        width = 40 if band == "2.4" else 80
    gateway = str(data.get("gateway", "192.168.4.1")).strip()
    try:
        dhcp_start = int(data.get("dhcp_start", 10))
        dhcp_end = int(data.get("dhcp_end", 100))
    except ValueError:
        dhcp_start, dhcp_end = 10, 100
    dns_servers = str(data.get("dns_servers", "1.1.1.1,8.8.8.8")).strip()

    # Validation
    if not (1 <= len(ssid) <= 32):
        response.status = 400
        return {"status": "error", "message": "SSID length must be between 1 and 32 characters."}
    
    if security != "OPEN" and not (8 <= len(passphrase) <= 63):
        response.status = 400
        return {"status": "error", "message": "WPA Passphrase must be between 8 and 63 characters."}

    if band == "2.4":
        if channel not in list(range(1, 12)):
            response.status = 400
            return {"status": "error", "message": "Invalid 2.4 GHz channel selected (1-11)."}
        if width not in [20, 40]:
            width = 40
        hw_mode = "g"
        ieee80211ac_line = "ieee80211ac=0\n"
        ht_capab = "[HT40+]" if channel in list(range(1, 8)) else "[HT40-]"
        ht_line = f"ht_capab={ht_capab}\n" if width == 40 else ""
        vht_lines = ""
    else:
        if channel not in [36, 40, 44, 48, 149, 153, 157, 161]:
            response.status = 400
            return {"status": "error", "message": "Invalid 5 GHz channel selected."}
        if width not in [20, 40, 80]:
            width = 80
        hw_mode = "a"
        ieee80211ac_line = "ieee80211ac=1\n"
        if width == 80:
            vht_oper_chwidth = 1
            seg0 = 42 if channel in [36, 40, 44, 48] else 155
            ht_capab = "[HT40+]" if channel in [36, 44, 149, 157] else "[HT40-]"
            vht_capab = "[RXLDPC][SHORT-GI-80]"
        elif width == 40:
            vht_oper_chwidth = 0
            seg0 = (channel + 2) if channel in [36, 44, 149, 157] else (channel - 2)
            ht_capab = "[HT40+]" if channel in [36, 44, 149, 157] else "[HT40-]"
            vht_capab = "[RXLDPC]"
        else:
            vht_oper_chwidth = 0
            seg0 = channel
            ht_capab = ""
            vht_capab = "[RXLDPC]"
        ht_line = f"ht_capab={ht_capab}\n" if ht_capab else ""
        vht_lines = f"""vht_oper_chwidth={vht_oper_chwidth}
vht_oper_centr_freq_seg0_idx={seg0}
vht_capab={vht_capab}\n"""

    ip_pattern = r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$"
    m = re.match(ip_pattern, gateway)
    if not m or not all(0 <= int(x) <= 255 for x in m.groups()):
        response.status = 400
        return {"status": "error", "message": "Invalid IPv4 Gateway address."}
    
    if not (1 <= dhcp_start < dhcp_end <= 254):
        response.status = 400
        return {"status": "error", "message": "Invalid DHCP range (Start must be less than End, 1-254)."}

    # Security configuration blocks
    if security == "OPEN":
        sec_block = "auth_algs=1"
    elif security == "WPA3":
        sec_block = f"""wpa=2
wpa_passphrase={passphrase}
wpa_key_mgmt=SAE
rsn_pairwise=CCMP
ieee80211w=2
sae_require_mfp=2"""
    elif security == "WPA2-WPA3":
        sec_block = f"""wpa=2
wpa_passphrase={passphrase}
wpa_key_mgmt=WPA-PSK SAE
rsn_pairwise=CCMP
ieee80211w=1
sae_require_mfp=1"""
    else:  # WPA2-PSK
        sec_block = f"""auth_algs=1
wpa=2
wpa_passphrase={passphrase}
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP"""

    hostapd_content = f"""# MT7663 SoftAP Configuration
# FiberHome HG680-FJ (Amlogic S905X2 / Meson G12A)
interface=ap0
driver=nl80211
ssid={ssid}
hw_mode={hw_mode}
channel={channel}
wmm_enabled=1
ieee80211n=1
{ieee80211ac_line}{ht_line}{vht_lines}{sec_block}
"""
    try:
        with open(HOSTAPD_CONF, "w") as f:
            f.write(hostapd_content)
    except Exception as e:
        response.status = 500
        return {"status": "error", "message": f"Failed writing {HOSTAPD_CONF}: {e}"}

    # Write DEFAULT_CONF preserving credentials
    user_cred, pass_cred = get_auth_credentials()
    default_content = f"""# MediaTek MT7663 Hotspot Network Configuration
# FiberHome HG680-FJ (Amlogic S905X2 / Meson G12A)

AP_GATEWAY="{gateway}"
AP_NETMASK="255.255.255.0"
AP_CIDR="24"
DHCP_START="{dhcp_start}"
DHCP_END="{dhcp_end}"
DHCP_LEASE="12h"
DNS_SERVERS="{dns_servers}"
AP_MTU="1408"
AP_WIDTH="{width}"
AP_SECURITY="{security}"

WEBUI_USER="{user_cred}"
WEBUI_PASS="{pass_cred}"
"""
    try:
        with open(DEFAULT_CONF, "w") as f:
            f.write(default_content)
    except Exception as e:
        response.status = 500
        return {"status": "error", "message": f"Failed writing {DEFAULT_CONF}: {e}"}

    # Restart hotspot service
    subprocess.Popen(["systemctl", "restart", "mt7663-hotspot"])

    return {"status": "ok", "message": "Configuration saved! Hotspot is restarting..."}

@app.route('/api/hotspot/action', method=['POST'])
def api_hotspot_action():
    if not is_authenticated():
        response.status = 401
        return {"status": "error", "message": "Unauthorized. Please log in first."}

    data = request.json or {}
    action = data.get("action", "")
    if action not in ["start", "stop", "restart"]:
        response.status = 400
        return {"status": "error", "message": "Invalid action (choose: start, stop, restart)."}

    code, stdout, stderr = run_cmd(["systemctl", action, "mt7663-hotspot"], timeout=20)
    if code == 0:
        return {"status": "ok", "message": f"Action '{action}' executed successfully."}
    else:
        response.status = 500
        return {"status": "error", "message": f"Failed executing '{action}': {stderr or stdout}"}

@app.route('/api/wifi/scan', method=['GET'])
def api_wifi_scan():
    code, stdout, stderr = run_cmd([
        "nmcli", "-t", "-f", "IN-USE,SSID,CHAN,SIGNAL,SECURITY",
        "dev", "wifi", "list", "--rescan", "yes"
    ], timeout=15)
    
    if code != 0:
        return {"status": "error", "message": stderr or "Failed scanning Wi-Fi.", "networks": []}

    networks = []
    seen = set()
    for line in stdout.splitlines():
        parts = re.split(r'(?<!\\):', line)
        if len(parts) >= 5:
            in_use = ("*" in parts[0])
            ssid = parts[1].replace(r"\:", ":").strip()
            chan_str = parts[2].strip()
            try:
                chan = int(chan_str)
            except ValueError:
                chan = 0
            try:
                signal = int(parts[3].strip())
            except ValueError:
                signal = 0
            security = parts[4].replace(r"\:", ":").strip() if parts[4] else "Open"
            
            if not ssid:
                continue
                
            freq = "5 GHz" if chan >= 36 else "2.4 GHz"

            if ssid not in seen:
                seen.add(ssid)
                networks.append({
                    "in_use": in_use,
                    "ssid": ssid,
                    "channel": chan,
                    "freq": freq,
                    "signal": signal,
                    "security": security
                })

    networks.sort(key=lambda x: (not x["in_use"], -x["signal"]))
    return {"status": "ok", "networks": networks}

@app.route('/api/wifi/connect', method=['POST'])
def api_wifi_connect():
    if not is_authenticated():
        response.status = 401
        return {"status": "error", "message": "Unauthorized. Please log in first."}

    data = request.json or {}
    ssid = data.get("ssid", "").strip()
    password = data.get("password", "").strip()

    if not ssid:
        response.status = 400
        return {"status": "error", "message": "SSID cannot be empty."}

    # Clean up any stale profile for this SSID
    run_cmd(["nmcli", "con", "delete", ssid], timeout=5)

    # Explicitly target wlan0 and allow 60s for handshake + DHCP
    cmd = ["nmcli", "dev", "wifi", "connect", ssid, "ifname", "wlan0"]
    if password:
        cmd.extend(["password", password])

    code, stdout, stderr = run_cmd(cmd, timeout=60)
    if code == 0:
        return {"status": "ok", "message": f"Successfully connected to Wi-Fi '{ssid}'!"}
    else:
        err_msg = stderr or stdout or "Connection timed out or failed"
        response.status = 500
        return {"status": "error", "message": f"Failed connecting to '{ssid}': {err_msg}"}

@app.route('/api/wifi/disconnect', method=['POST'])
def api_wifi_disconnect():
    if not is_authenticated():
        response.status = 401
        return {"status": "error", "message": "Unauthorized. Please log in first."}

    code, stdout, stderr = run_cmd(["nmcli", "dev", "disconnect", "wlan0"], timeout=15)
    if code == 0:
        return {"status": "ok", "message": "Wi-Fi wlan0 disconnected."}
    else:
        response.status = 500
        return {"status": "error", "message": f"Failed disconnecting: {stderr or stdout}"}

@app.post('/api/devices/rename')
def api_rename_device():
    check_auth()
    try:
        data = request.json or {}
        mac = str(data.get("mac", "")).lower().strip()
        name = str(data.get("name", "")).strip()
        if not mac or not name:
            response.status = 400
            return {"status": "error", "message": "MAC and Name are required"}
        
        cache = load_device_cache()
        cache[mac] = name
        save_device_cache(cache)
        return {"status": "ok", "message": f"Device {mac} renamed to {name}"}
    except Exception as e:
        response.status = 500
        return {"status": "error", "message": str(e)}

# ----------------- Static Frontend -----------------

STATIC_ROOT = str(BASE_DIR / "static")

@app.route('/')
def serve_index():
    res = static_file("index.html", root=STATIC_ROOT)
    res.set_header("Cache-Control", "no-cache, no-store, must-revalidate, max-age=0")
    res.set_header("Pragma", "no-cache")
    res.set_header("Expires", "0")
    return res

@app.route('/static/<filepath:path>')
def serve_static(filepath):
    res = static_file(filepath, root=STATIC_ROOT)
    res.set_header("Cache-Control", "no-cache, no-store, must-revalidate, max-age=0")
    res.set_header("Pragma", "no-cache")
    res.set_header("Expires", "0")
    return res

class ThreadedWSGIServer(ThreadingMixIn, WSGIServer):
    daemon_threads = True

class ThreadedServer(ServerAdapter):
    def run(self, handler):
        server = make_server(self.host, self.port, handler, server_class=ThreadedWSGIServer)
        server.serve_forever()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    print(f"[*] Starting MT7663 Router Web UI on port {port} (Multi-threaded)...")
    app.run(host='0.0.0.0', port=port, server=ThreadedServer, quiet=True)
