# Antigravity 免 TUN 代理助手 (Antigravity TUN-Bypass Tool)

专为 **Google Antigravity** 打造的免 TUN 代理辅助工具。彻底解决使用代理软件（如 v2rayN / Xray / Clash 等）时必须开启 TUN 虚拟网卡透明代理、造成全系统流量被强制接管、与内网/其他软件冲突以及管理员提权的问题。

---

## 🌟 核心价值：为什么需要「免 TUN 方案」？

| 对比维度 | 原生普通代理 / 无 TUN | 开启 TUN 虚拟网卡模式 | **使用本工具（免 TUN 方案）** |
| :--- | :--- | :--- | :--- |
| **Antigravity 状态** | ❌ 无法连接 Google/Gemini 核心 | ✔ 可以使用 | **✔ 丝滑连接，体验与 TUN 完全一致** |
| **全系统流量** | 仅浏览器走代理 | ❌ 所有软件（微信/游戏/内网）被强制劫持 | **✔ 仅 Antigravity 与开发进程走代理** |
| **系统权限要求** | 普通用户 | ❌ 需管理员权限 + 安装驱动 | **✔ 无需提权，无需任何驱动** |
| **网络冲突/蓝屏风险**| 无 | ❌ 易与 Hyper-V/WSL2/VPN 冲突 | **✔ 零冲突，纯绿色安全** |

---

## 🚀 核心架构与原理 (v2.0)

Antigravity 内部采用 **Electron 前端界面 + 本地后端语言服务器 (`language_server.exe`)** 的双层架构。
* 前端 UI 通过本地回环 `https://127.0.0.1:<动态端口>/` 渲染；
* 后台 Go/gRPC 进程负责与 Google Gemini 和 Cloud Code 通讯。

本工具通过 **微型原生启动器 (`AntigravityLauncher.exe`)**，在启动瞬间向 Antigravity 及其语言服务器进程精准注入 `HTTP_PROXY`、`HTTPS_PROXY`、`ALL_PROXY`、`GRPC_PROXY` 环境变量：
1. **彻底摆脱 TUN 虚拟网卡**，AI 请求全量走本地代理端口；
2. **避免 Chromium 本地回环劫持**，杜绝 `ERR_NETWORK_CHANGED` 崩溃或白屏；
3. **保留原版高清图标与启动速度**，0 延迟、无控制台黑框。

---

## 🛠️ 软件主要功能

1. **按键一：【一键开启免 TUN 代理】**
   * **环境精准注入**：将代理地址注入 Windows 用户环境变量及全局策略文件，确保 Node.js 扩展宿主、Python 进程、Language Server（Go/gRPC）全部直连代理。
   * **原生快捷方式接管**：桌面快捷方式自动由原生启动器接管，双击即可无感带代理运行。
   * **Git 加速联动**：可选同步配置 Git 全局代理，保障在 Antigravity 内部克隆与更新 GitHub 代码不卡顿。

2. **按键二：【撤回免 TUN 代理 (恢复直连)】**
   * 一键清除注入的环境变量，广播刷新 Explorer。
   * 恢复桌面快捷方式为原版直连，撤销所有代理绑定。
   * 恢复 Git 默认直连，杜绝代理残留与断网隐患。

3. **智能辅助功能**
   * **智能端口探测**：自动识别本地正在运行的代理客户端（如当前运行的 `v2rayN / Xray` 端口 `10808` 或 Clash 端口 `7890`）。
   * **连通性测试**：一键测试 Google 基础连接与 Gemini API 连通延迟（毫秒级反馈）。
   * **一键启动 Antigravity**：支持直接在工具中带代理唤起 Antigravity。

---

## 📁 文件说明

* `Antigravity免TUN代理.exe`：打包好的**独立单文件绿色 GUI 程序**。
* `AntigravityLauncher.exe`：原生 Win32 极速环境注入启动器（由 C# 编译，5KB）。
* `Launcher.cs`：原生启动器 C# 源码。
* `app.py`：现代暗黑 UI 源代码（基于 `CustomTkinter`）。
* `proxy_manager.py`：注册表、环境变量与快捷方式管理核心代码。
* `config.json`：默认端口与用户设置存储文件。

---

## 💡 使用步骤

1. 保持你的代理软件（如 **v2rayN**）在后台正常运行（**关掉 TUN 模式**，普通模式即可）。
2. 打开 **【Antigravity免TUN代理.exe】**。
3. 点击 **【🚀 一键开启免 TUN 代理】**，状态指示灯变为绿色。
4. 直接打开桌面上的 **Antigravity** 即可畅快使用 AI 功能！
5. 需要恢复平时直连时，随时点击 **【🔄 撤回免 TUN 代理 (恢复直连)】** 即可一键复原。
