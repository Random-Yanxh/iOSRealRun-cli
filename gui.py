#!/usr/bin/env python3
"""
Basic tkinter GUI for iOSRealRun.
"""

import os
import re
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from tkinter.scrolledtext import ScrolledText

import yaml

import tools.parseRoute as parseRoute
import tools.run as run
import tools.utils as utils
from tools.config import config
from tools.paths import app_path, chdir_app_dir


class RealRunGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("iOSRealRun")
        self.root.geometry("760x560")
        self.root.minsize(680, 500)

        self.route_var = tk.StringVar(value=getattr(config, "routeConfig", ""))
        self.speed_var = tk.StringVar(value=str(getattr(config, "v", 3.3)))
        self.status_var = tk.StringVar(value="未启动")
        self.device_var = tk.StringVar(value="未检测")
        self.route_info_var = tk.StringVar(value="未读取路线")

        self.stop_event = threading.Event()
        self.worker = None
        self.closing = False
        self.route_options = self.get_route_options()

        self.build_ui()
        self.refresh_route_info()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def build_ui(self):
        outer = ttk.Frame(self.root, padding=16)
        outer.pack(fill=tk.BOTH, expand=True)
        outer.columnconfigure(1, weight=1)
        outer.rowconfigure(5, weight=1)

        ttk.Label(outer, text="路线文件").grid(row=0, column=0, sticky=tk.W, pady=6)
        self.route_combo = ttk.Combobox(
            outer,
            textvariable=self.route_var,
            values=self.route_options,
            state="readonly",
        )
        self.route_combo.grid(row=0, column=1, sticky=tk.EW, padx=(8, 8), pady=6)
        self.route_combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_route_info())
        ttk.Button(outer, text="刷新", command=self.refresh_routes).grid(row=0, column=2, sticky=tk.E, pady=6)

        ttk.Label(outer, text="速度 m/s").grid(row=1, column=0, sticky=tk.W, pady=6)
        speed_entry = ttk.Entry(outer, textvariable=self.speed_var, width=12)
        speed_entry.grid(row=1, column=1, sticky=tk.W, padx=(8, 8), pady=6)
        ttk.Button(outer, text="保存配置", command=self.save_config).grid(row=1, column=2, sticky=tk.E, pady=6)

        ttk.Label(outer, text="路线信息").grid(row=2, column=0, sticky=tk.W, pady=6)
        ttk.Label(outer, textvariable=self.route_info_var).grid(row=2, column=1, columnspan=2, sticky=tk.W, padx=(8, 0), pady=6)

        ttk.Label(outer, text="设备状态").grid(row=3, column=0, sticky=tk.W, pady=6)
        ttk.Label(outer, textvariable=self.device_var).grid(row=3, column=1, sticky=tk.W, padx=(8, 0), pady=6)
        ttk.Button(outer, text="检测设备", command=self.check_device).grid(row=3, column=2, sticky=tk.E, pady=6)

        ttk.Label(outer, text="运行状态").grid(row=4, column=0, sticky=tk.W, pady=6)
        ttk.Label(outer, textvariable=self.status_var).grid(row=4, column=1, sticky=tk.W, padx=(8, 0), pady=6)

        self.log_box = ScrolledText(outer, height=14, wrap=tk.WORD)
        self.log_box.grid(row=5, column=0, columnspan=3, sticky=tk.NSEW, pady=(12, 12))
        self.log_box.configure(state=tk.DISABLED)

        actions = ttk.Frame(outer)
        actions.grid(row=6, column=0, columnspan=3, sticky=tk.E)
        self.start_button = ttk.Button(actions, text="启动", command=self.start)
        self.start_button.pack(side=tk.LEFT, padx=(0, 8))
        self.stop_button = ttk.Button(actions, text="停止", command=self.stop, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT)

    def get_route_options(self):
        routes = sorted(path.name for path in app_path().glob("*route.txt"))
        current = self.route_var.get().strip()
        if current and current not in routes:
            routes.insert(0, current)
        return routes

    def refresh_routes(self):
        self.route_options = self.get_route_options()
        self.route_combo.configure(values=self.route_options)
        if not self.route_var.get().strip() and self.route_options:
            self.route_var.set(self.route_options[0])
        self.refresh_route_info()

    def log(self, message):
        def append():
            self.log_box.configure(state=tk.NORMAL)
            self.log_box.insert(tk.END, message + "\n")
            self.log_box.see(tk.END)
            self.log_box.configure(state=tk.DISABLED)

        self.root.after(0, append)

    def set_status(self, message):
        self.root.after(0, lambda: self.status_var.set(message))

    def set_device(self, message):
        self.root.after(0, lambda: self.device_var.set(message))

    def refresh_route_info(self):
        try:
            loc = self.load_route()
            distance = self.route_distance(loc)
            speed = self.get_speed()
            minutes = distance / speed / 60
            self.route_info_var.set("{} 个点，约 {:.0f} 米，单圈约 {:.1f} 分钟".format(len(loc), distance, minutes))
        except Exception as exc:
            self.route_info_var.set("读取失败：{}".format(exc))

    def load_route(self):
        route_path = self.route_var.get().strip()
        if not route_path:
            raise ValueError("未选择路线文件")
        with open(app_path(route_path), "r", encoding="utf-8") as route_file:
            return parseRoute.split(route_file.read())

    def route_distance(self, loc):
        if len(loc) < 2:
            return 0
        total = 0
        for index in range(len(loc)):
            total += run.geodistance(loc[index], loc[(index + 1) % len(loc)])
        return total

    def get_speed(self):
        speed = float(self.speed_var.get().strip())
        if speed <= 0:
            raise ValueError("速度必须大于 0")
        return speed

    def save_config(self):
        try:
            speed = self.get_speed()
            route_path = self.route_var.get().strip()
            if not route_path:
                raise ValueError("未选择路线文件")

            config_data = {
                "v": speed,
                "routeConfig": route_path,
                "libimobiledeviceDir": getattr(config, "libimobiledeviceDir", "libimobiledevice"),
                "imageDir": getattr(config, "imageDir", "DeveloperDiskImage"),
            }
            with open(app_path("config.yaml"), "w", encoding="utf-8") as config_file:
                yaml.safe_dump(config_data, config_file, allow_unicode=True, sort_keys=False)
            for key, value in config_data.items():
                setattr(config, key, value)
            self.refresh_route_info()
            self.log("配置已保存")
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc))

    def check_device(self):
        self.set_device("检测中")
        threading.Thread(target=self.check_device_worker, daemon=True).start()

    def check_device_worker(self):
        try:
            name, version = self.get_device_info()
            image_version = self.find_image_version(version)
            image_text = "镜像 {}".format(image_version) if image_version else "未找到匹配镜像"
            self.set_device("{}，iOS {}，{}".format(name, version, image_text))
            self.log("设备检测成功：{}，iOS {}".format(name, version))
        except Exception as exc:
            self.set_device("检测失败")
            self.log("设备检测失败：{}".format(exc))

    def get_device_info(self):
        info = utils.cmd("ideviceinfo")
        device_match = re.search(r"DeviceName: (.+)\n", info)
        version_match = re.search(r"ProductVersion: (.+)\n", info)
        if not device_match or not version_match:
            raise RuntimeError("未读取到设备信息，请确认已解锁、信任电脑并连接数据线")
        return device_match.group(1).strip(), version_match.group(1).strip()

    def find_image_version(self, version):
        image_dir = getattr(config, "imageDir", "DeveloperDiskImage")
        candidates = [version, ".".join(version.split(".")[0:2])]
        for item in candidates:
            dmg = os.path.join(image_dir, item, "DeveloperDiskImage.dmg")
            signature = os.path.join(image_dir, item, "DeveloperDiskImage.dmg.signature")
            if os.path.exists(app_path(dmg)) and os.path.exists(app_path(signature)):
                return item
        return None

    def mount_image(self, version):
        image_version = self.find_image_version(version)
        if not image_version:
            raise RuntimeError("没有找到 iOS {} 对应的 DeveloperDiskImage".format(version))
        image_dir = getattr(config, "imageDir", "DeveloperDiskImage")
        dmg = str(app_path(image_dir, image_version, "DeveloperDiskImage.dmg"))
        signature = str(app_path(image_dir, image_version, "DeveloperDiskImage.dmg.signature"))
        output = utils.cmd(["ideviceimagemounter", dmg, signature])
        if "-3" in output:
            raise RuntimeError("开发者镜像签名验证失败")
        self.log("开发者镜像已挂载：{}".format(image_version))

    def prepare_device(self):
        pair_output = utils.cmd(["idevicepair", "pair"])
        if "No device found" in pair_output:
            raise RuntimeError("没有检测到设备")
        if "passcode" in pair_output:
            raise RuntimeError("请先解锁手机或 iPad，然后重试")
        if "trust" in pair_output:
            raise RuntimeError("请在设备上信任此电脑，然后重试")
        if "SUCCESS" not in pair_output:
            self.log("配对输出：{}".format(pair_output.strip() or "无输出"))

        name, version = self.get_device_info()
        self.set_device("{}，iOS {}".format(name, version))

        if int(version.split(".")[0]) >= 16:
            dev_mode = utils.cmd(["idevicedevmodectl", "list"])
            if "disable" in dev_mode:
                utils.cmd(["idevicedevmodectl", "reveal"], False)
                raise RuntimeError("请在设备设置中打开开发者模式，重启确认后再启动")

        self.mount_image(version)

    def start(self):
        if self.worker and self.worker.is_alive():
            return
        try:
            self.save_config()
            loc = self.load_route()
            speed = self.get_speed()
        except Exception as exc:
            messagebox.showerror("启动失败", str(exc))
            return

        self.stop_event.clear()
        self.start_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        self.set_status("启动中")
        self.worker = threading.Thread(target=self.run_worker, args=(loc, speed), daemon=True)
        self.worker.start()

    def run_worker(self, loc, speed):
        try:
            self.log("正在连接设备并挂载开发者镜像")
            self.prepare_device()
            self.log("已开始模拟，速度约 {} m/s".format(speed))
            self.set_status("运行中")
            run.run(loc, speed, stop_event=self.stop_event, log_callback=self.log)
        except Exception as exc:
            self.log("运行失败：{}".format(exc))
            self.set_status("运行失败")
        finally:
            try:
                utils.resetLoc()
                self.log("已恢复设备定位")
            except Exception as exc:
                self.log("恢复定位失败：{}".format(exc))
            self.root.after(0, self.finish_run)

    def stop(self):
        self.stop_event.set()
        self.set_status("正在停止")
        self.log("正在停止，请稍候")

    def finish_run(self):
        self.start_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        if self.status_var.get() != "运行失败":
            self.status_var.set("已停止")
        if self.closing:
            self.root.destroy()

    def on_close(self):
        if self.worker and self.worker.is_alive():
            if not messagebox.askyesno("确认退出", "当前仍在运行，是否停止并退出？"):
                return
            self.closing = True
            self.stop_event.set()
            self.set_status("正在停止")
            self.log("正在停止并准备退出")
            self.start_button.configure(state=tk.DISABLED)
            self.stop_button.configure(state=tk.DISABLED)
            return
        self.root.destroy()


def main():
    chdir_app_dir()
    root = tk.Tk()
    RealRunGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
