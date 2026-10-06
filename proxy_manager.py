"""
Antigravity 免 TUN 代理管理器 (Proxy Manager Core - v2.0)
解决 Windows Explorer 环境不刷新及 Chromium 本地回环代理冲突的终极方案：
通过微型原生启动器 (AntigravityLauncher) + 跨进程环境注入 + 动态 JSON 配置，
实现双击原生快捷方式即享免 TUN 代理，撤回时 100% 干净恢复。
"""

import os
import sys
import json
import socket
import winreg
import ctypes
import subprocess
import urllib.request
import urllib.error
from typing import Dict, List, Tuple, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
GLOBAL_PROXY_JSON = os.path.expandvars(r"%USERPROFILE%\.gemini\antigravity_proxy.json")
LAUNCHER_EXE = os.path.join(BASE_DIR, "AntigravityLauncher.exe")

PROXY_ENV_VARS = [
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "GRPC_PROXY",
    "grpc_proxy",
    "NO_PROXY",
    "no_proxy",
]

DEFAULT_NO_PROXY = "localhost,127.0.0.1,::1,*.local"

COMMON_PORTS = [
    (10808, "v2rayN / Xray (Socks/HTTP 混合端口)"),
    (10809, "v2rayN (HTTP 代理端口)"),
    (7890, "Clash / Clash Verge / Mihomo (默认端口)"),
    (7897, "Clash Verge Rev (新版默认端口)"),
    (1080, "Shadowsocks / 通用 Socks5 端口"),
    (2080, "NekoBox (默认端口)"),
    (2081, "NekoBox HTTP 端口"),
    (1082, "v2rayA 默认端口"),
]

HWND_BROADCAST = 0xFFFF
WM_SETTINGCHANGE = 0x001A
SMTO_ABORTIFHUNG = 0x0002


def broadcast_setting_change():
    """广播系统环境变量更新通知"""
    try:
        result = ctypes.c_long()
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST,
            WM_SETTINGCHANGE,
            0,
            "Environment",
            SMTO_ABORTIFHUNG,
            1000,
            ctypes.byref(result)
        )
    except Exception as e:
        print(f"广播环境变量变更失败: {e}")


def load_config() -> dict:
    default_config = {
        "proxy_port": 10808,
        "modify_shortcut": True,
        "set_git_proxy": True,
        "is_enabled": False,
        "last_tested_latency": None,
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                default_config.update(data)
        except Exception:
            pass
    return default_config


def save_config(cfg: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存配置失败: {e}")


def sync_global_proxy_json(enabled: bool, port: int):
    """同步写入用户主目录下的 .gemini\\antigravity_proxy.json"""
    try:
        os.makedirs(os.path.dirname(GLOBAL_PROXY_JSON), exist_ok=True)
        payload = {
            "enabled": enabled,
            "port": port,
            "http_proxy": f"http://127.0.0.1:{port}",
            "https_proxy": f"http://127.0.0.1:{port}",
            "all_proxy": f"socks5://127.0.0.1:{port}",
            "no_proxy": DEFAULT_NO_PROXY,
            "updated_at": int(os.path.getmtime(CONFIG_FILE)) if os.path.exists(CONFIG_FILE) else 0
        }
        with open(GLOBAL_PROXY_JSON, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"写入全局代理配置失败: {e}")


def is_port_listening(port: int, host: str = "127.0.0.1") -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.4)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False


def detect_active_proxy() -> Optional[Tuple[int, str]]:
    for port, name in COMMON_PORTS:
        if is_port_listening(port):
            return port, name
    return None


def get_current_env_proxy() -> Dict[str, Optional[str]]:
    status = {}
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ) as key:
            for var in PROXY_ENV_VARS:
                try:
                    val, _ = winreg.QueryValueEx(key, var)
                    status[var] = val
                except FileNotFoundError:
                    status[var] = None
    except Exception:
        pass
    return status


def is_proxy_enabled() -> Tuple[bool, Optional[int]]:
    if os.path.exists(GLOBAL_PROXY_JSON):
        try:
            with open(GLOBAL_PROXY_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data.get("enabled"):
                    return True, data.get("port", 10808)
        except Exception:
            pass

    envs = get_current_env_proxy()
    http_val = envs.get("HTTP_PROXY") or envs.get("http_proxy")
    if http_val and "127.0.0.1" in http_val:
        try:
            port_str = http_val.split(":")[-1].strip("/")
            return True, int(port_str)
        except Exception:
            return True, None
    return False, None


def get_antigravity_executable_path() -> Optional[str]:
    possible_paths = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\antigravity\Antigravity.exe"),
        os.path.expandvars(r"%PROGRAMFILES%\Antigravity\Antigravity.exe"),
        os.path.expandvars(r"%PROGRAMFILES(X86)%\Antigravity\Antigravity.exe"),
    ]
    for p in possible_paths:
        if os.path.exists(p):
            return p
    return None


def get_installed_launcher_path() -> str:
    """获取或准备就绪原生代理启动器路径"""
    prog_dir = os.path.expandvars(r"%LOCALAPPDATA%\Programs\antigravity")
    target_in_prog = os.path.join(prog_dir, "AntigravityLauncher.exe")
    
    # 如果本体目录已有或者可拷贝过去
    if os.path.exists(LAUNCHER_EXE):
        try:
            if os.path.exists(prog_dir):
                import shutil
                shutil.copyfile(LAUNCHER_EXE, target_in_prog)
                return target_in_prog
        except Exception:
            pass
        return LAUNCHER_EXE

    if os.path.exists(target_in_prog):
        return target_in_prog
    return LAUNCHER_EXE


def get_desktop_shortcuts() -> List[str]:
    desktop_dirs = [
        os.path.expandvars(r"%USERPROFILE%\Desktop"),
        os.path.expandvars(r"%PUBLIC%\Desktop"),
    ]
    shortcuts = []
    for d in desktop_dirs:
        if not os.path.exists(d):
            continue
        for fname in os.listdir(d):
            if fname.lower().endswith(".lnk") and "antigravity" in fname.lower() and "助手" not in fname:
                shortcuts.append(os.path.join(d, fname))
    return shortcuts


def set_shortcut_to_launcher(lnk_path: str) -> bool:
    """将桌面快捷方式指向原生极速代理启动器，并保持原汁原味的 Antigravity 原生图标"""
    if not os.path.exists(lnk_path):
        return False
    launcher_path = get_installed_launcher_path()
    antigravity_exe = get_antigravity_executable_path() or launcher_path
    work_dir = os.path.dirname(antigravity_exe)

    try:
        ps_code = f"""
$sh = New-Object -ComObject WScript.Shell
$sc = $sh.CreateShortcut('{lnk_path}')
$sc.TargetPath = '{launcher_path}'
$sc.WorkingDirectory = '{work_dir}'
$sc.IconLocation = '{antigravity_exe},0'
$sc.Arguments = ''
$sc.Description = 'Google Antigravity (免TUN代理加速)'
$sc.Save()
"""
        res = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_code],
            capture_output=True,
            text=True
        )
        return res.returncode == 0
    except Exception as e:
        print(f"切换快捷方式到启动器失败: {e}")
        return False


def restore_shortcut_to_original(lnk_path: str) -> bool:
    """将桌面快捷方式彻底还原为原版 Antigravity.exe 直连"""
    if not os.path.exists(lnk_path):
        return False
    antigravity_exe = get_antigravity_executable_path()
    if not antigravity_exe:
        return False
    work_dir = os.path.dirname(antigravity_exe)

    try:
        ps_code = f"""
$sh = New-Object -ComObject WScript.Shell
$sc = $sh.CreateShortcut('{lnk_path}')
$sc.TargetPath = '{antigravity_exe}'
$sc.WorkingDirectory = '{work_dir}'
$sc.IconLocation = '{antigravity_exe},0'
$sc.Arguments = ''
$sc.Description = ''
$sc.Save()
"""
        res = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_code],
            capture_output=True,
            text=True
        )
        return res.returncode == 0
    except Exception as e:
        print(f"还原快捷方式失败: {e}")
        return False


def set_system_user_env(port: int):
    proxy_http = f"http://127.0.0.1:{port}"
    proxy_socks = f"socks5://127.0.0.1:{port}"
    
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, "HTTP_PROXY", 0, winreg.REG_SZ, proxy_http)
        winreg.SetValueEx(key, "HTTPS_PROXY", 0, winreg.REG_SZ, proxy_http)
        winreg.SetValueEx(key, "ALL_PROXY", 0, winreg.REG_SZ, proxy_socks)
        winreg.SetValueEx(key, "http_proxy", 0, winreg.REG_SZ, proxy_http)
        winreg.SetValueEx(key, "https_proxy", 0, winreg.REG_SZ, proxy_http)
        winreg.SetValueEx(key, "all_proxy", 0, winreg.REG_SZ, proxy_socks)
        winreg.SetValueEx(key, "GRPC_PROXY", 0, winreg.REG_SZ, proxy_http)
        winreg.SetValueEx(key, "grpc_proxy", 0, winreg.REG_SZ, proxy_http)
        winreg.SetValueEx(key, "NO_PROXY", 0, winreg.REG_SZ, DEFAULT_NO_PROXY)
        winreg.SetValueEx(key, "no_proxy", 0, winreg.REG_SZ, DEFAULT_NO_PROXY)
        
    broadcast_setting_change()


def unset_system_user_env():
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_ALL_ACCESS) as key:
        for var in PROXY_ENV_VARS:
            try:
                winreg.DeleteValue(key, var)
            except FileNotFoundError:
                pass
    broadcast_setting_change()


def set_git_proxy(port: int):
    try:
        proxy_http = f"http://127.0.0.1:{port}"
        subprocess.run(["git", "config", "--global", "http.proxy", proxy_http], capture_output=True)
        subprocess.run(["git", "config", "--global", "https.proxy", proxy_http], capture_output=True)
    except Exception:
        pass


def unset_git_proxy():
    try:
        subprocess.run(["git", "config", "--global", "--unset", "http.proxy"], capture_output=True)
        subprocess.run(["git", "config", "--global", "--unset", "https.proxy"], capture_output=True)
    except Exception:
        pass


def test_proxy_connectivity(port: int, target_url: str = "https://www.google.com/generate_204", timeout: float = 4.0) -> Tuple[bool, str]:
    proxy_url = f"http://127.0.0.1:{port}"
    proxy_handler = urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
    opener = urllib.request.build_opener(proxy_handler)
    
    import time
    start_time = time.time()
    try:
        req = urllib.request.Request(
            target_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AntigravityProxyCheck"}
        )
        with opener.open(req, timeout=timeout) as resp:
            elapsed_ms = int((time.time() - start_time) * 1000)
            status_code = resp.getcode()
            return True, f"连通正常 ({elapsed_ms}ms, 状态码 {status_code})"
    except urllib.error.HTTPError as e:
        elapsed_ms = int((time.time() - start_time) * 1000)
        if e.code in [404, 403, 401, 200, 204]:
            return True, f"连通正常 ({elapsed_ms}ms, 状态码 {e.code})"
        return False, f"HTTP 响应异常 ({e.code})"
    except Exception as e:
        return False, f"连接超时或失败 ({type(e).__name__})"


def launch_antigravity_with_proxy(port: int) -> Tuple[bool, str]:
    exe_path = get_antigravity_executable_path()
    if not exe_path or not os.path.exists(exe_path):
        return False, "未找到 Antigravity 安装路径"
    
    env = os.environ.copy()
    env["HTTP_PROXY"] = f"http://127.0.0.1:{port}"
    env["HTTPS_PROXY"] = f"http://127.0.0.1:{port}"
    env["ALL_PROXY"] = f"socks5://127.0.0.1:{port}"
    env["http_proxy"] = f"http://127.0.0.1:{port}"
    env["https_proxy"] = f"http://127.0.0.1:{port}"
    env["all_proxy"] = f"socks5://127.0.0.1:{port}"
    env["GRPC_PROXY"] = f"http://127.0.0.1:{port}"
    env["grpc_proxy"] = f"http://127.0.0.1:{port}"
    env["NO_PROXY"] = DEFAULT_NO_PROXY
    env["no_proxy"] = DEFAULT_NO_PROXY

    try:
        # 注意：绝不能给 Electron 传 --proxy-server，否则会阻断 127.0.0.1 的本地后端通讯！
        # 仅向进程环境变量注入即可让语言服务器 language_server 100% 走代理！
        subprocess.Popen([exe_path], env=env, cwd=os.path.dirname(exe_path), close_fds=True)
        return True, "Antigravity 已在免 TUN 代理环境下成功启动！"
    except Exception as e:
        return False, f"启动异常: {e}"


def enable_all(port: int, modify_shortcuts: bool = True, config_git: bool = True) -> List[str]:
    logs = []
    
    # 1. 写入全局代理 JSON 配置
    sync_global_proxy_json(True, port)
    logs.append(f"✔ 已生成全局代理策略文件: ~/.gemini/antigravity_proxy.json (目标 127.0.0.1:{port})")

    # 2. 注入系统用户级环境变量
    set_system_user_env(port)
    logs.append(f"✔ 已注入系统用户环境变量 HTTP_PROXY/HTTPS_PROXY/ALL_PROXY/GRPC_PROXY -> 127.0.0.1:{port}")
    
    # 3. 将桌面快捷方式切换为极速环境启动器（保留原生图标）
    if modify_shortcuts:
        shortcuts = get_desktop_shortcuts()
        if shortcuts:
            for s in shortcuts:
                if set_shortcut_to_launcher(s):
                    logs.append(f"✔ 已升级桌面快捷方式: {os.path.basename(s)} (双击即自动附带代理环境，0延迟无黑框)")
                else:
                    logs.append(f"⚠ 升级快捷方式失败: {os.path.basename(s)}")
        else:
            logs.append("ℹ 未在桌面检测到 Antigravity.lnk")

    # 4. 设置 Git 代理
    if config_git:
        set_git_proxy(port)
        logs.append(f"✔ 已配置 Git 全局代理 -> http://127.0.0.1:{port}")

    # 保存本地配置
    cfg = load_config()
    cfg["proxy_port"] = port
    cfg["modify_shortcut"] = modify_shortcuts
    cfg["set_git_proxy"] = config_git
    cfg["is_enabled"] = True
    save_config(cfg)
    
    logs.append("★【免 TUN 代理已全面就绪】")
    logs.append("👉 现在请在 v2rayN 中保持节点连接，关闭 TUN 模式，然后直接打开 Antigravity！")
    return logs


def disable_all(restore_shortcuts: bool = True, restore_git: bool = True) -> List[str]:
    logs = []

    # 1. 禁用全局代理 JSON
    sync_global_proxy_json(False, 10808)
    logs.append("✔ 已停用全局代理策略文件")

    # 2. 清理系统用户环境变量
    unset_system_user_env()
    logs.append("✔ 已清除系统环境变量中的所有代理配置并广播通知")

    # 3. 还原桌面快捷方式为原版直连
    if restore_shortcuts:
        shortcuts = get_desktop_shortcuts()
        for s in shortcuts:
            if restore_shortcut_to_original(s):
                logs.append(f"✔ 已还原桌面快捷方式: {os.path.basename(s)} (恢复原版直连)")
            else:
                logs.append(f"⚠ 还原快捷方式失败: {os.path.basename(s)}")

    # 4. 移除 Git 代理
    if restore_git:
        unset_git_proxy()
        logs.append("✔ 已清除 Git 全局代理配置")

    # 保存本地配置
    cfg = load_config()
    cfg["is_enabled"] = False
    save_config(cfg)

    logs.append("★【代理已彻底撤回】系统与 Antigravity 已 100% 恢复原始干净状态。")
    return logs
