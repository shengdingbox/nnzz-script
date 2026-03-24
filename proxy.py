import requests
import certifi

def request_without_proxy_post(url:str,body:str):
    # # 核心：proxies参数设为空字典，禁用所有代理
    proxies = {
        "http": None,
        "https": None,
        "ftp": None
    }
    
    try:
        # 即使系统开了代理，也会直接请求，不走代理
        response = requests.post(
            url,
            data=body,
            proxies=proxies,  # 关键参数
            verify=certifi.where(),  # 仅信任官方根证书
            timeout=10
        )
        print("请求成功，状态码:", response.status_code)
        print("响应内容:", response.text)
    except requests.exceptions.SSLError:
        print("检测到伪造证书（抓包工具），请求拒绝！")
    except Exception as e:
        print("请求失败:", e)

def request_without_proxy_get(url:str):
    # # 核心：proxies参数设为空字典，禁用所有代理
    proxies = {
        "http": None,
        "https": None,
        "ftp": None
    }
    
    try:
        # 即使系统开了代理，也会直接请求，不走代理
        response = requests.get(
            url,
            proxies=proxies,  # 关键参数
            verify=certifi.where(),  # 仅信任官方根证书
            timeout=10
        )
        print("请求成功，状态码:", response.status_code)
        print("响应内容:", response.text)
    except requests.exceptions.SSLError:
        print("检测到伪造证书（抓包工具），请求拒绝！")
    except Exception as e:
        print("请求失败:", e)

if __name__ == "__main__":
    request_without_proxy()