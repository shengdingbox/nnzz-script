#!/usr/bin/env python3
"""
AutoGLM-GUI Electron 一键构建脚本

功能：
1. 检查环境依赖
2. 同步 Python 开发依赖
3. 构建前端
4. 下载 ADB 工具
5. 打包 Python 后端
6. 构建 Electron 应用

用法：
    uv run python scripts/build_electron.py [--skip-frontend] [--skip-adb] [--skip-backend]
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

# 修复 Windows 编码问题
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")


class Color:
    """终端颜色"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"

    # Windows cmd 不支持 ANSI 转义码时禁用颜色
    @classmethod
    def disable_colors(cls):
        cls.RESET = ""
        cls.BOLD = ""
        cls.RED = ""
        cls.GREEN = ""
        cls.YELLOW = ""
        cls.BLUE = ""
        cls.CYAN = ""


def print_step(step: str, total: int, current: int):
    """打印步骤信息"""
    print(f"\n{Color.CYAN}{Color.BOLD}[{current}/{total}] {step}{Color.RESET}")
    print("=" * 60)


def print_success(message: str):
    """打印成功信息"""
    print(f"{Color.GREEN}✓ {message}{Color.RESET}")


def print_error(message: str):
    """打印错误信息"""
    print(f"{Color.RED}✗ {message}{Color.RESET}", file=sys.stderr)


def print_warning(message: str):
    """打印警告信息"""
    print(f"{Color.YELLOW}⚠ {message}{Color.RESET}")


def run_command(
    cmd: list[str],
    cwd: Path | None = None,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> bool:
    """执行命令"""
    cmd_str = " ".join(str(c) for c in cmd)
    print(f"{Color.BLUE}$ {cmd_str}{Color.RESET}")

    try:
        # Windows 下 pnpm/npm 等命令需要通过 shell 执行
        use_shell = sys.platform == "win32" and cmd[0] in ["pnpm", "npm", "uv"]

        result = subprocess.run(
            cmd,
            cwd=cwd,
            check=check,
            capture_output=False,
            text=True,
            shell=use_shell,
            env=env,
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print_error(f"命令执行失败: {e.stderr if e.stderr else str(e)}")
        return False
    except FileNotFoundError:
        print_error(f"命令未找到: {cmd[0]}")
        return False
    except Exception as e:
        print_error(f"执行命令时发生异常: {str(e)}")
        return False


def check_command(cmd: str) -> bool:
    """检查命令是否可用"""
    try:
        # Windows 下某些命令（如 pnpm）需要通过 shell 执行
        subprocess.run(
            [cmd, "--version"],
            capture_output=True,
            check=True,
            shell=(sys.platform == "win32"),
            timeout=10,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_backend_version(root_dir: Path) -> str:
    """读取后端版本号（用于前端构建注入）。"""
    pyproject_path = root_dir / "pyproject.toml"
    try:
        with pyproject_path.open("rb") as file:
            data = tomllib.load(file)
        return str(data.get("project", {}).get("version") or "unknown")
    except Exception as e:
        print_warning(f"读取版本号失败: {str(e)}")
        return "unknown"


class ElectronBuilder:
    def __init__(self, args):
        self.args = args
        # 修正：脚本在 scripts 目录下，项目根目录需要向上一级
        self.script_dir = Path(__file__).resolve().parent
        self.root_dir = self.script_dir.parent
        self.os_name = platform.system().lower()
        
        # Windows 禁用 ANSI 颜色
        if self.os_name == "windows":
            Color.disable_colors()

    def check_environment(self) -> bool:
        """检查环境依赖"""
        print_step("检查环境依赖", 7, 1)

        required_tools = {
            "uv": "Python 包管理器",
            "python": "Python 解释器"
        }

        # 根据系统补充必要工具
        if self.os_name == "windows":
            required_tools["where"] = "Windows 路径查找工具"
        else:
            required_tools["which"] = "Unix 路径查找工具"

        missing_tools = []
        for tool, description in required_tools.items():
            if check_command(tool):
                print_success(f"{description} ({tool}) 已安装")
            else:
                print_error(f"{description} ({tool}) 未安装")
                missing_tools.append(tool)

        if missing_tools:
            print_error(f"\n缺少必需工具: {', '.join(missing_tools)}")
            print("\n安装指南:")
            if "uv" in missing_tools:
                if self.os_name == "windows":
                    print("  uv: powershell -c \"irm https://astral.sh/uv/install.ps1 | iex\"")
                else:
                    print("  uv: curl -LsSf https://astral.sh/uv/install.sh | sh")
            return False

        return True

    def sync_python_deps(self) -> bool:
        """同步 Python 开发依赖"""
        print_step("同步 Python 开发依赖", 7, 2)
        return run_command(["uv", "sync", "--dev"], cwd=self.root_dir)
    
    def build_backend(self) -> bool:
        """打包 Python 后端"""
        if self.args.skip_backend:
            print_warning("跳过后端打包")
            return True
            
        print_step("打包 Python 后端", 7, 5)

        # 定义路径
        entry_point = self.root_dir / "main.py"
        output_dir = self.root_dir / "dist"
        
        # 检查入口文件是否存在
        if not entry_point.exists():
            print_error(f"入口文件不存在: {entry_point}")
            return False

        # 清理旧的构建输出
        try:
            # 清理 PyInstaller 残留
            pyinstaller_dist = self.root_dir / "dist" / "main"
            pyinstaller_build = self.root_dir / "build" / "main"
            if pyinstaller_dist.exists():
                shutil.rmtree(pyinstaller_dist)
                print_success("清理旧的 PyInstaller dist 输出")
            if pyinstaller_build.exists():
                shutil.rmtree(pyinstaller_build)
                print_success("清理旧的 PyInstaller build 输出")
            
            # 清理 Nuitka 输出
            nuitka_output = output_dir / "main.dist"
            if nuitka_output.exists():
                shutil.rmtree(nuitka_output)
                print_success("清理旧的 Nuitka 输出")
                
        except Exception as e:
            print_error(f"清理旧文件失败: {str(e)}")
            return False

        # 准备 Nuitka 命令参数（跨平台兼容）
        nuitka_cmd = [
            "uv", "run", "python", "-m", "nuitka",
            "--standalone",
            f"--output-dir={output_dir}",
            "--follow-imports",
            "--nofollow-import-to=tkinter,matplotlib,numpy",
            "--assume-yes-for-downloads",
            "--show-progress",
            "--show-memory",
            str(entry_point),
        ]

        # 根据系统设置输出文件名
        if self.os_name == "windows":
            nuitka_cmd.insert(nuitka_cmd.index("--output-dir=") + 1, "--output-filename=main.exe")
            # Windows 特有的参数
            nuitka_cmd.extend([
                "--windows-disable-console",  # 禁用控制台窗口
                "--windows-icon-from-ico=" + str(self.root_dir / "assets" / "icon.ico")
            ])
        else:
            nuitka_cmd.insert(nuitka_cmd.index("--output-dir=") + 1, "--output-filename=main")

        # 添加数据文件（检查文件是否存在）
        tafangmonitor_exe = self.root_dir / "tafangmonitor.exe"
        if tafangmonitor_exe.exists():
            nuitka_cmd.append(f"--include-data-files={tafangmonitor_exe}=tafangmonitor.exe")
        else:
            print_warning(f"未找到 tafangmonitor.exe: {tafangmonitor_exe}，跳过包含")

        # 运行 Nuitka
        print("\n运行 Nuitka 打包后端...")
        if not run_command(nuitka_cmd, cwd=self.root_dir):
            print_error("Nuitka 打包失败")
            return False

        return True
    
    def build(self) -> bool:
        """执行完整构建流程"""
        print(f"\n{Color.BOLD}AutoGLM-GUI Electron 构建工具{Color.RESET}")
        print(f"项目根目录: {self.root_dir}")
        print(f"当前系统: {self.os_name}\n") 
        
        total_steps = 3
        current_step = 1
        
        steps = [
            ("环境检查", lambda: self.check_environment()),
            ("Python 依赖同步", lambda: self.sync_python_deps()),
            ("后端打包", lambda: self.build_backend())
        ]

        for step_name, step_func in steps:
            print_step(step_name, total_steps, current_step)
            if not step_func():
                print_error(f"\n构建失败: {step_name}")
                return False
            current_step += 1

        print_success("\n✅ 所有构建步骤完成！")
        return True


def main():
    parser = argparse.ArgumentParser(description="AutoGLM-GUI Electron 一键构建脚本")
    # 添加跳过参
    args = parser.parse_args()

    builder = ElectronBuilder(args)

    try:
        success = builder.build()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_error("\n\n构建已被用户取消")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\n构建失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()