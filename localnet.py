import ipaddress
import socket

def check_network_env():
    # 1. 获取本机 IP
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
    except OSError:
        local_ip = "127.0.0.1"

    is_private = ipaddress.ip_address(local_ip).is_private

    # 2. 测试外网连通性
    try:
        socket.setdefaulttimeout(3)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        internet_ok = True
    except OSError:
        internet_ok = False

    print(f"本机 IP      : {local_ip}")
    print(f"私有 IP      : {is_private}")
    print(f"外网可达     : {internet_ok}")

    if is_private and not internet_ok:
        print("结论：纯内网环境（无公网访问）")
    elif is_private and internet_ok:
        print("结论：内网 IP，但可访问公网（NAT 环境）")
    else:
        print("结论：公网 IP 环境")

check_network_env()