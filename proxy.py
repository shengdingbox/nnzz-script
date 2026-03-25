import urllib.request

import psutil

def check_proxy_processes() -> list:
    PROXY_PROCESSES = {
        # Clash 系
        "clash.exe", "clash-windows.exe", "clashx",
        # V2Ray / Xray
        "v2ray.exe", "xray.exe", "v2rayN.exe",
        # Shadowsocks
        "shadowsocks.exe", "ss-local.exe", "sslocal",
        # Trojan
        "trojan.exe", "trojan-go.exe",
        # Surge / Quantumult
        "surge", "quantumultx",
        # 通用代理
        "proxifier.exe", "privoxy.exe", "squid.exe",
        "netch.exe", "nekoray.exe", "mihomo.exe",

        # ══════════════════════════════
        #  抓包 / 流量分析工具
        # ══════════════════════════════

        # Wireshark 系
        "wireshark.exe", "tshark.exe", "dumpcap.exe", "rawshark.exe",

        # Fiddler 系
        "fiddler.exe", "fiddler4.exe", "fiddlercore.exe",
        "fiddlercap.exe", "fiddler everywhere.exe",

        # Burp Suite
        "burpsuite.exe", "burp-loader.exe",
        "burpsuite_community.exe", "burpsuite_pro.exe",

        # mitmproxy 系
        "mitmproxy.exe", "mitmdump.exe", "mitmweb.exe",

        # Charles
        "charles.exe",

        # HTTP Toolkit
        "httptoolkit.exe", "httptoolkit-server.exe",

        # Proxyman (macOS)
        "proxyman",

        # Packet capture (macOS / Linux)
        "tcpdump", "termshark",

        # HTTP 调试
        "httpwatch.exe",

        # 网络嗅探 / 分析
        "networkminer.exe",       # NetworkMiner
        "capsa.exe",              # Capsa
        "omnipeek.exe",           # OmniPeek
        "colasoft.exe",           # Colasoft Capsa
        "glasswire.exe",          # GlassWire
        "netmon.exe",             # Microsoft Network Monitor
        "messageanalyzer.exe",    # Microsoft Message Analyzer
        "etl2pcapng.exe",

        # 移动端抓包
        "stream",                 # Stream (iOS)
        "packetsender.exe",       # Packet Sender

        # 其他
        "apidog.exe",             # Apidog
        "postman.exe",            # Postman（含抓包功能）
        "insomnia.exe",           # Insomnia
        "reqable.exe",            # Reqable
    }

    found = []
    for proc in psutil.process_iter(["name", "exe"]):
        name = (proc.info["name"] or "").lower()
        if name in PROXY_PROCESSES:
            found.append({
                "name": name,
                "pid": proc.pid,
                "exe": proc.info["exe"]
            })
    return found

def get_system_proxy() -> dict:
    proxies = urllib.request.getproxies()
    return {
        "detected": bool(proxies),
        "proxies": proxies
    }

if __name__ == "__main__":
    print(check_proxy_processes())
    print(get_system_proxy())
