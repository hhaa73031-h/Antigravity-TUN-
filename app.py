"""
Antigravity 免 TUN 代理助手 - 现代化图形用户界面
基于 CustomTkinter 构建的高质感暗黑科技风桌面工具
"""

import os
import sys
import threading
import time
import customtkinter as ctk
import proxy_manager

# 设置外观与主题
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# 配色规范 (基于 Modern Slate Dark 调色板)
COLOR_BG_DARK = "#0f172a"        # 深蓝黑底色
COLOR_CARD_BG = "#1e293b"        # 卡片表面背景
COLOR_CARD_BORDER = "#334155"    # 卡片边框
COLOR_TEXT_PRIMARY = "#f8fafc"   # 主文本
COLOR_TEXT_MUTED = "#94a3b8"     # 次要灰字
COLOR_ACCENT = "#38bdf8"         # 亮青天蓝
COLOR_SUCCESS = "#10b981"        # 翡翠绿 (开启状态)
COLOR_SUCCESS_HOVER = "#059669"
COLOR_DANGER = "#f43f5e"         # 玫瑰红 (撤回/警示)
COLOR_DANGER_HOVER = "#e11d48"
COLOR_CONSOLE_BG = "#090d16"     # 控制台深黑背景


class AntigravityProxyApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Antigravity 免 TUN 代理助手")
        self.geometry("740x720")
        self.minsize(680, 640)
        self.configure(fg_color=COLOR_BG_DARK)

        # 读取持久化配置
        self.config = proxy_manager.load_config()

        # 初始化状态变量
        self.var_port = ctk.StringVar(value=str(self.config.get("proxy_port", 10808)))
        self.var_modify_shortcut = ctk.BooleanVar(value=self.config.get("modify_shortcut", True))
        self.var_set_git = ctk.BooleanVar(value=self.config.get("set_git_proxy", True))
        
        # 页面布局
        self._build_ui()

        # 启动后执行初次状态检查
        self.after(300, self.refresh_status)

    def _build_ui(self):
        # 主可滚动容器或整页布局
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=24, pady=20)

        # 1. 顶部 Header 标题栏
        header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 16))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left")

        title_label = ctk.CTkLabel(
            title_box,
            text="Antigravity 免 TUN 代理助手",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=22, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        title_label.pack(anchor="w")

        subtitle_label = ctk.CTkLabel(
            title_box,
            text="告别 TUN 虚拟网卡与网络冲突 · 精准代理桥接 · 一键自由启闭",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=12),
            text_color=COLOR_TEXT_MUTED
        )
        subtitle_label.pack(anchor="w", pady=(2, 0))

        # 版本 Badge
        badge = ctk.CTkLabel(
            header_frame,
            text=" v1.0 绿色版 ",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=COLOR_ACCENT,
            fg_color="#0369a1",
            corner_radius=6
        )
        badge.pack(side="right", padx=(0, 4), pady=(6, 0))

        # 2. 状态信息卡片 (Status Card)
        self.status_card = ctk.CTkFrame(
            self.main_frame,
            fg_color=COLOR_CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=COLOR_CARD_BORDER
        )
        self.status_card.pack(fill="x", pady=(0, 16), ipady=8)

        status_inner = ctk.CTkFrame(self.status_card, fg_color="transparent")
        status_inner.pack(fill="x", padx=20, pady=10)

        # 状态指示灯与主标题
        status_left = ctk.CTkFrame(status_inner, fg_color="transparent")
        status_left.pack(side="left", fill="y")

        self.status_dot = ctk.CTkLabel(
            status_left,
            text="●",
            font=ctk.CTkFont(size=26),
            text_color=COLOR_TEXT_MUTED
        )
        self.status_dot.pack(side="left", padx=(0, 10))

        status_text_box = ctk.CTkFrame(status_left, fg_color="transparent")
        status_text_box.pack(side="left")

        self.status_title = ctk.CTkLabel(
            status_text_box,
            text="正在检测代理状态...",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=16, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        self.status_title.pack(anchor="w")

        self.status_desc = ctk.CTkLabel(
            status_text_box,
            text="正在探测本地代理端口及系统环境...",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=12),
            text_color=COLOR_TEXT_MUTED
        )
        self.status_desc.pack(anchor="w")

        # 状态卡片右侧快捷操作
        status_right = ctk.CTkFrame(status_inner, fg_color="transparent")
        status_right.pack(side="right", fill="y")

        self.btn_refresh = ctk.CTkButton(
            status_right,
            text="刷新状态",
            width=80,
            height=32,
            fg_color="#334155",
            hover_color="#475569",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=12),
            command=self.refresh_status
        )
        self.btn_refresh.pack(side="right", pady=6)

        # 3. 核心大按键区域 (Two Primary Action Buttons)
        actions_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        actions_frame.pack(fill="x", pady=(0, 16))

        # 按键一：一键开启免 TUN 代理
        self.btn_enable = ctk.CTkButton(
            actions_frame,
            text="🚀  一键开启免 TUN 代理",
            height=50,
            corner_radius=10,
            fg_color=COLOR_SUCCESS,
            hover_color=COLOR_SUCCESS_HOVER,
            text_color="#ffffff",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=15, weight="bold"),
            command=self.on_enable_click
        )
        self.btn_enable.pack(side="left", fill="x", expand=True, padx=(0, 8))

        # 按键二：一键撤回代理
        self.btn_disable = ctk.CTkButton(
            actions_frame,
            text="🔄  撤回免 TUN 代理 (恢复直连)",
            height=50,
            corner_radius=10,
            fg_color=COLOR_DANGER,
            hover_color=COLOR_DANGER_HOVER,
            text_color="#ffffff",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=15, weight="bold"),
            command=self.on_disable_click
        )
        self.btn_disable.pack(side="right", fill="x", expand=True, padx=(8, 0))

        # 4. 代理端口与选项配置卡片 (Settings Card)
        config_card = ctk.CTkFrame(
            self.main_frame,
            fg_color=COLOR_CARD_BG,
            corner_radius=12,
            border_width=1,
            border_color=COLOR_CARD_BORDER
        )
        config_card.pack(fill="x", pady=(0, 16), padx=0)

        config_inner = ctk.CTkFrame(config_card, fg_color="transparent")
        config_inner.pack(fill="x", padx=20, pady=14)

        # 端口输入栏
        port_row = ctk.CTkFrame(config_inner, fg_color="transparent")
        port_row.pack(fill="x", pady=(0, 10))

        lbl_port = ctk.CTkLabel(
            port_row,
            text="本地代理端口:",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=13, weight="bold"),
            text_color=COLOR_TEXT_PRIMARY
        )
        lbl_port.pack(side="left", padx=(0, 10))

        self.entry_port = ctk.CTkEntry(
            port_row,
            textvariable=self.var_port,
            width=110,
            height=32,
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
            justify="center"
        )
        self.entry_port.pack(side="left", padx=(0, 12))

        btn_detect = ctk.CTkButton(
            port_row,
            text="🔍 智能探测端口",
            width=115,
            height=32,
            fg_color="#0284c7",
            hover_color="#0369a1",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=12),
            command=self.auto_detect_port
        )
        btn_detect.pack(side="left", padx=(0, 12))

        # 预设常用端口标签选择
        lbl_presets = ctk.CTkLabel(
            port_row,
            text="快捷设定:",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=12),
            text_color=COLOR_TEXT_MUTED
        )
        lbl_presets.pack(side="left", padx=(8, 6))

        for p, label in [(10808, "v2rayN:10808"), (10809, "HTTP:10809"), (7890, "Clash:7890")]:
            p_btn = ctk.CTkButton(
                port_row,
                text=label,
                width=80,
                height=26,
                fg_color="#334155",
                hover_color="#475569",
                font=ctk.CTkFont(family="Consolas", size=11),
                command=lambda port=p: self.set_preset_port(port)
            )
            p_btn.pack(side="left", padx=3)

        # 细项开关复选框
        opts_row = ctk.CTkFrame(config_inner, fg_color="transparent")
        opts_row.pack(fill="x", pady=(4, 0))

        chk_shortcut = ctk.CTkCheckBox(
            opts_row,
            text="更新桌面 Antigravity 快捷方式附加 --proxy-server",
            variable=self.var_modify_shortcut,
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=12),
            text_color=COLOR_TEXT_PRIMARY,
            fg_color=COLOR_ACCENT,
            hover_color="#0284c7"
        )
        chk_shortcut.pack(side="left", padx=(0, 20))

        chk_git = ctk.CTkCheckBox(
            opts_row,
            text="同步配置 Git 全局代理 (加速 GitHub 访问)",
            variable=self.var_set_git,
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=12),
            text_color=COLOR_TEXT_PRIMARY,
            fg_color=COLOR_ACCENT,
            hover_color="#0284c7"
        )
        chk_git.pack(side="left")

        # 5. 联动辅助操作按钮 (Quick Launch & Connectivity Test)
        aux_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        aux_frame.pack(fill="x", pady=(0, 12))

        self.btn_launch_app = ctk.CTkButton(
            aux_frame,
            text="⚡  直接启动 Antigravity (带代理运行)",
            height=38,
            fg_color="#4338ca",
            hover_color="#3730a3",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=13, weight="bold"),
            command=self.on_launch_antigravity
        )
        self.btn_launch_app.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.btn_test = ctk.CTkButton(
            aux_frame,
            text="🌐  测试代理连通性 (Google & Gemini API)",
            height=38,
            fg_color="#0369a1",
            hover_color="#0284c7",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=13, weight="bold"),
            command=self.on_test_connectivity
        )
        self.btn_test.pack(side="right", fill="x", expand=True, padx=(8, 0))

        # 6. 控制台操作日志 (Console Log Area)
        lbl_console = ctk.CTkLabel(
            self.main_frame,
            text="运行日志与状态输出:",
            font=ctk.CTkFont(family="Microsoft YaHei UI", size=12, weight="bold"),
            text_color=COLOR_TEXT_MUTED
        )
        lbl_console.pack(anchor="w", pady=(0, 4))

        self.log_box = ctk.CTkTextbox(
            self.main_frame,
            height=160,
            fg_color=COLOR_CONSOLE_BG,
            text_color="#e2e8f0",
            font=ctk.CTkFont(family="Consolas", size=11),
            corner_radius=10,
            border_width=1,
            border_color=COLOR_CARD_BORDER
        )
        self.log_box.pack(fill="both", expand=True)

    def log(self, text: str):
        """向日志窗口输出格式化日志"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{timestamp}] {text}\n")
        self.log_box.see("end")

    def set_preset_port(self, port: int):
        self.var_port.set(str(port))
        self.log(f"已快捷切换目标端口至: {port}")

    def get_input_port(self) -> int:
        try:
            p = int(self.var_port.get().strip())
            if 1 <= p <= 65535:
                return p
            raise ValueError
        except Exception:
            self.log("❌ 错误: 请输入有效的端口号 (1-65535)")
            return 10808

    def auto_detect_port(self):
        """后台线程自动扫描本地可用代理端口"""
        def worker():
            self.log("正在扫描本地运行的代理客户端...")
            res = proxy_manager.detect_active_proxy()
            if res:
                port, name = res
                self.var_port.set(str(port))
                self.log(f"✔ 探测成功: 发现运行中的【{name}】，已自动填入端口 {port}")
            else:
                self.log("⚠ 未扫描到常见代理端口，请确保 v2rayN / Clash 已在后台开启！")
        threading.Thread(target=worker, daemon=True).start()

    def refresh_status(self):
        """刷新当前代理状态卡片"""
        is_on, port = proxy_manager.is_proxy_enabled()
        if is_on:
            self.status_dot.configure(text_color=COLOR_SUCCESS)
            self.status_title.configure(text=f"免 TUN 代理已开启 (127.0.0.1:{port})")
            self.status_desc.configure(text="系统环境变量已就绪 · Antigravity 及所有子进程已桥接至本地代理")
            self.status_card.configure(border_color="#059669")
        else:
            self.status_dot.configure(text_color=COLOR_TEXT_MUTED)
            self.status_title.configure(text="免 TUN 代理未开启 (当前直连模式)")
            self.status_desc.configure(text="未设置代理环境变量 · 点击下方【一键开启】即可免 TUN 使用 Antigravity")
            self.status_card.configure(border_color=COLOR_CARD_BORDER)

    def on_enable_click(self):
        """一键开启免 TUN 代理"""
        port = self.get_input_port()
        modify_sc = self.var_modify_shortcut.get()
        set_git = self.var_set_git.get()

        self.btn_enable.configure(state="disabled", text="正在配置生效中...")

        def worker():
            logs = proxy_manager.enable_all(port, modify_sc, set_git)
            for l in logs:
                self.log(l)
            
            # 开启后顺便快速测试一下
            self.log("正在验证代理到 Google 网络的连通性...")
            ok, msg = proxy_manager.test_proxy_connectivity(port, timeout=3.5)
            if ok:
                self.log(f"✔ 网络连通测试: {msg}")
            else:
                self.log(f"⚠ 连通测试反馈: {msg} (请确认代理软件节点已连接)")

            self.after(0, self._after_enable)

        threading.Thread(target=worker, daemon=True).start()

    def _after_enable(self):
        self.btn_enable.configure(state="normal", text="🚀  一键开启免 TUN 代理")
        self.refresh_status()

    def on_disable_click(self):
        """一键撤回代理"""
        modify_sc = self.var_modify_shortcut.get()
        set_git = self.var_set_git.get()

        self.btn_disable.configure(state="disabled", text="正在撤回还原中...")

        def worker():
            logs = proxy_manager.disable_all(modify_sc, set_git)
            for l in logs:
                self.log(l)
            self.after(0, self._after_disable)

        threading.Thread(target=worker, daemon=True).start()

    def _after_disable(self):
        self.btn_disable.configure(state="normal", text="🔄  撤回免 TUN 代理 (恢复直连)")
        self.refresh_status()

    def on_launch_antigravity(self):
        """直接启动 Antigravity"""
        port = self.get_input_port()
        ok, msg = proxy_manager.launch_antigravity_with_proxy(port)
        if ok:
            self.log(f"✔ {msg}")
        else:
            self.log(f"❌ {msg}")

    def on_test_connectivity(self):
        """测试连通性"""
        port = self.get_input_port()
        self.btn_test.configure(state="disabled", text="正在测试网络连通...")

        def worker():
            self.log(f"正在测试通过 127.0.0.1:{port} 访问 Google 及 Gemini API...")
            ok1, msg1 = proxy_manager.test_proxy_connectivity(port, "https://www.google.com/generate_204", timeout=4.0)
            self.log(f"Google 基础连接: {'✔' if ok1 else '❌'} {msg1}")
            
            ok2, msg2 = proxy_manager.test_proxy_connectivity(port, "https://generativelanguage.googleapis.com", timeout=4.0)
            self.log(f"Gemini API 节点: {'✔' if ok2 else '❌'} {msg2}")
            
            self.after(0, lambda: self.btn_test.configure(state="normal", text="🌐  测试代理连通性 (Google & Gemini API)"))

        threading.Thread(target=worker, daemon=True).start()


def main():
    app = AntigravityProxyApp()
    app.mainloop()


if __name__ == "__main__":
    main()
