import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import time
import threading
import winsound

BG    = "#F2EDE8"   # 暖白背景
CARD  = "#FFFFFF"   # 卡片白
TEXT  = "#3D322B"   # 深棕文字
SUB   = "#A09188"   # 浅灰文字
ACCENT = "#E0896A"  # 暖橘强调色
GREEN = "#7EB89C"   # 柔和绿
RED   = "#D97A6E"   # 柔和红
DARK  = "#2B2420"   # 深色（时钟数字）
RADIUS = 16


class RoundedFrame(tk.Canvas):
    """带圆角的卡片容器"""
    def __init__(self, parent, width, height, bg=CARD, **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg=BG, highlightthickness=0, **kwargs)
        self.cw = width
        self.ch = height
        self.cbg = bg
        self._draw()

    def _draw(self):
        r = RADIUS
        w, h, c = self.cw, self.ch, self.cbg
        self.create_arc(0, 0, r*2, r*2, start=90, extent=90, fill=c, outline="")
        self.create_arc(w-r*2, 0, w, r*2, start=0, extent=90, fill=c, outline="")
        self.create_arc(0, h-r*2, r*2, h, start=180, extent=90, fill=c, outline="")
        self.create_arc(w-r*2, h-r*2, w, h, start=270, extent=90, fill=c, outline="")
        self.create_rectangle(r, 0, w-r, h, fill=c, outline="")
        self.create_rectangle(0, r, w, h-r, fill=c, outline="")


class AlarmClock:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("闹钟")
        self.root.geometry("400x540")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        self.alarm_time = None
        self.running = False
        self.triggered = False
        self._blink_on = True
        self._blink_job = None

        self._build_ui()
        self._update_clock()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    # ── UI 构建 ────────────────────────────────────────────
    def _build_ui(self):
        # 顶部留白
        tk.Frame(self.root, height=36, bg=BG).pack()

        # 标题
        tk.Label(self.root, text="闹 钟", font=("Microsoft YaHei", 13),
                 fg=SUB, bg=BG).pack()

        # ── 时钟卡片 ──
        clock_card = RoundedFrame(self.root, 300, 140)
        clock_card.pack(pady=(18, 0))

        self.clock_label = tk.Label(clock_card, text="",
                                     font=("Helvetica", 48, "bold"),
                                     fg=DARK, bg=CARD)
        clock_card.create_window(150, 50, window=self.clock_label)

        self.date_label = tk.Label(clock_card, text="",
                                    font=("Microsoft YaHei", 11),
                                    fg=SUB, bg=CARD)
        clock_card.create_window(150, 108, window=self.date_label)

        # ── 闹钟设置卡片 ──
        set_card = RoundedFrame(self.root, 300, 200)
        set_card.pack(pady=18)

        tk.Label(set_card, text="设置闹钟时间",
                 font=("Microsoft YaHei", 11), fg=SUB, bg=CARD).place(x=150, y=22, anchor="center")

        # 时间选择器
        self.hour_var   = tk.StringVar(value="07")
        self.min_var    = tk.StringVar(value="00")
        self.sec_var    = tk.StringVar(value="00")

        picker_y = 78
        self._make_picker(set_card, 60,  picker_y, "时", self.hour_var,   0, 23)
        self._make_picker(set_card, 150, picker_y, "分", self.min_var,    0, 59)
        self._make_picker(set_card, 240, picker_y, "秒", self.sec_var,    0, 59)

        # 分隔冒号
        tk.Label(set_card, text=":", font=("Helvetica", 22, "bold"),
                 fg=DARK, bg=CARD).place(x=103, y=picker_y-3)
        tk.Label(set_card, text=":", font=("Helvetica", 22, "bold"),
                 fg=DARK, bg=CARD).place(x=193, y=picker_y-3)

        # ── 按钮区 ──
        btn_frame = tk.Frame(self.root, bg=BG)
        btn_frame.pack(pady=16)

        self.start_btn = tk.Canvas(btn_frame, width=130, height=42,
                                    bg=BG, highlightthickness=0)
        self._draw_btn(self.start_btn, "启 动", GREEN)
        self.start_btn.bind("<Button-1>", lambda e: self._start_alarm())
        self.start_btn.pack(side="left", padx=8)

        self.stop_btn = tk.Canvas(btn_frame, width=130, height=42,
                                   bg=BG, highlightthickness=0)
        self._draw_btn(self.stop_btn, "关 闭", "#DDD")
        self.stop_btn.bind("<Button-1>", lambda e: self._stop_alarm())
        self.stop_btn.pack(side="left", padx=8)

        # 状态文字
        self.status_label = tk.Label(self.root, text="",
                                      font=("Microsoft YaHei", 10),
                                      fg=SUB, bg=BG)
        self.status_label.pack(pady=(2, 0))

    def _make_picker(self, parent, cx, y, label_text, var, lo, hi):
        """在卡片上放置一组 数值/加减按钮"""
        val_label = tk.Label(parent, textvariable=var,
                              font=("Helvetica", 28, "bold"),
                              fg=DARK, bg=CARD, width=2)
        val_label.place(x=cx, y=y, anchor="center")

        unit = tk.Label(parent, text=label_text,
                         font=("Microsoft YaHei", 9), fg=SUB, bg=CARD)
        unit.place(x=cx, y=y + 28, anchor="center")

        # 上箭头
        up = tk.Label(parent, text="▲", font=("SimHei", 8),
                       fg=SUB, bg=CARD, cursor="hand2")
        up.place(x=cx + 24, y=y - 12, anchor="center")
        up.bind("<Button-1>", lambda e, v=var, l=lo, h=hi: self._spin(v, 1, l, h))

        # 下箭头
        dn = tk.Label(parent, text="▼", font=("SimHei", 8),
                       fg=SUB, bg=CARD, cursor="hand2")
        dn.place(x=cx + 24, y=y + 12, anchor="center")
        dn.bind("<Button-1>", lambda e, v=var, l=lo, h=hi: self._spin(v, -1, l, h))

    def _spin(self, var, delta, lo, hi):
        try:
            v = int(var.get()) + delta
        except ValueError:
            return
        if v > hi: v = lo
        if v < lo: v = hi
        var.set(str(v).zfill(2))

    def _draw_btn(self, canvas, text, color):
        canvas.delete("all")
        w, h = 130, 42
        r = 21
        canvas.create_arc((0, 0, r*2, r*2), start=90, extent=90, fill=color, outline="")
        canvas.create_arc((w-r*2, 0, w, r*2), start=0, extent=90, fill=color, outline="")
        canvas.create_arc((0, h-r*2, r*2, h), start=180, extent=90, fill=color, outline="")
        canvas.create_arc((w-r*2, h-r*2, w, h), start=270, extent=90, fill=color, outline="")
        canvas.create_rectangle((r, 0, w-r, h), fill=color, outline="")
        canvas.create_rectangle((0, r, w, h-r), fill=color, outline="")
        fg = "#FFF" if color != "#DDD" else "#AAA"
        canvas.create_text(w//2, h//2, text=text, font=("Microsoft YaHei", 12, "bold"), fill=fg)

    # ── 时钟更新 ──────────────────────────────────────────
    def _update_clock(self):
        now = datetime.datetime.now()
        self.clock_label.config(text=now.strftime("%H:%M:%S"))
        weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        wd = weekdays[now.weekday()]
        self.date_label.config(text=f"{now.month}月{now.day}日  {wd}")

        if self.running and self.alarm_time and not self.triggered:
            if (now.hour == self.alarm_time.hour and
                now.minute == self.alarm_time.minute and
                now.second == self.alarm_time.second):
                self._trigger()

        self.root.after(200, self._update_clock)

    # ── 闹钟控制 ──────────────────────────────────────────
    def _start_alarm(self):
        try:
            h = int(self.hour_var.get())
            m = int(self.min_var.get())
            s = int(self.sec_var.get())
        except ValueError:
            return

        if not (0 <= h <= 23 and 0 <= m <= 59 and 0 <= s <= 59):
            return

        self.alarm_time = datetime.time(h, m, s)
        self.running = True
        self.triggered = False

        self._draw_btn(self.start_btn, "运 行 中", ACCENT)
        self._draw_btn(self.stop_btn, "关 闭", RED)
        self._toggle_pickers(False)

        self.status_label.config(
            text=f"●  已设置  {self.alarm_time.strftime('%H:%M:%S')}",
            fg=GREEN)

    def _stop_alarm(self):
        self.running = False
        self.triggered = False
        self.alarm_time = None

        if self._blink_job:
            self.root.after_cancel(self._blink_job)
            self._blink_job = None

        self._draw_btn(self.start_btn, "启 动", GREEN)
        self._draw_btn(self.stop_btn, "关 闭", "#DDD")
        self._toggle_pickers(True)

        self.status_label.config(text="○  未设置闹钟", fg=SUB)

    def _toggle_pickers(self, enabled):
        """启用/禁用时间选择器的箭头 (遍历卡片子控件)"""
        state = "normal" if enabled else "disabled"
        fg = SUB if enabled else "#D0CBC6"
        # 找到设置卡片内的所有箭头 label
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Canvas):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label) and child.cget("text") in ("▲", "▼"):
                        child.config(fg=fg, cursor="hand2" if enabled else "arrow")
                        # 解绑/重新绑定
                        if enabled:
                            # 保持原绑定 — 这里简化处理，不重新绑定
                            pass

    # ── 触发响铃 ──────────────────────────────────────────
    def _trigger(self):
        self.triggered = True
        threading.Thread(target=self._play_alarm_sound, daemon=True).start()
        self._blink()
        messagebox.showinfo("闹钟", f"⏰ 时间到了！\n{self.alarm_time.strftime('%H:%M:%S')}")
        self._stop_alarm()

    def _blink(self):
        if not self.triggered:
            return
        self._blink_on = not self._blink_on
        bg = "#FFF0E8" if self._blink_on else BG
        self.root.configure(bg=bg)
        self.status_label.config(
            text="🔔 时间到！", fg=RED if self._blink_on else ACCENT,
            bg=bg)
        self._blink_job = self.root.after(400, self._blink)

    def _play_alarm_sound(self):
        for _ in range(6):
            if not self.triggered:
                break
            winsound.Beep(1000, 250)
            time.sleep(0.15)
            winsound.Beep(1200, 250)
            time.sleep(0.15)

    def _on_close(self):
        self.running = False
        self.triggered = False
        self.root.destroy()


if __name__ == "__main__":
    AlarmClock()
