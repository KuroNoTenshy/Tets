import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import math
import winsound
import os
import sys

# ── Tentar importar pygame para sons MP3 ──────────────────────────────────────
try:
    import pygame
    pygame.mixer.init()
    PYGAME_OK = True
except ImportError:
    PYGAME_OK = False

# ── Constantes ────────────────────────────────────────────────────────────────
DEFAULT_MINUTES = 20
BG        = "#1e1e1e"
BG_DARK   = "#141414"
BG_PANEL  = "#252525"
BG_BTN    = "#2a2a2a"
BG_BTN_H  = "#3a3a3a"
FG        = "#e0e0e0"
FG_DIM    = "#888888"
FG_RED    = "#e74c3c"
ACCENT    = "#3d5a8a"
BORDER    = "#333333"
BORDER_D  = "#1a1a1a"

# ── App ───────────────────────────────────────────────────────────────────────
class TimerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Timer")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_PANEL)
        self.root.attributes("-topmost", True)         # sempre acima
        self.root.overrideredirect(True)               # sem barra do Windows

        # Estado
        self.remaining  = DEFAULT_MINUTES * 60
        self.running    = False
        self.muted      = False
        self.hidra      = 0
        self.sound_path = None
        self.after_id   = None
        self._drag_x = 0
        self._drag_y = 0

        self._build_ui()
        self._update_display()

        # Centrar janela
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Titlebar ──────────────────────────────────────────────────────────
        tb = tk.Frame(self.root, bg="#2e2e2e", height=30)
        tb.pack(fill="x")
        tb.bind("<ButtonPress-1>",   self._drag_start)
        tb.bind("<B1-Motion>",       self._drag_motion)

        tk.Label(tb, text="⏱ Timer", bg="#2e2e2e", fg="#cccccc",
                 font=("Segoe UI", 10)).pack(side="left", padx=8)

        for txt, cmd in [("—", self._minimize), ("✕", self._close)]:
            btn = tk.Button(tb, text=txt, bg="#2e2e2e", fg="#bbbbbb",
                            font=("Segoe UI", 11), bd=0, padx=8,
                            activebackground="#555555", activeforeground="#ffffff",
                            cursor="hand2", command=cmd, relief="flat")
            btn.pack(side="right")
            if txt == "✕":
                btn.config(activebackground="#c0392b")

        # ── Separador ─────────────────────────────────────────────────────────
        tk.Frame(self.root, bg=BORDER_D, height=1).pack(fill="x")

        # ── Client area ───────────────────────────────────────────────────────
        client = tk.Frame(self.root, bg=BG, padx=14, pady=12)
        client.pack(fill="both")

        # Linha principal: timer + imagem
        top = tk.Frame(client, bg=BG)
        top.pack(fill="x")

        # Timer label
        self.timer_lbl = tk.Label(top, text="20:00", bg=BG, fg=FG,
                                  font=("Consolas", 46, "bold"))
        self.timer_lbl.pack(side="left")

        # Painel imagem
        img_frame = tk.Frame(top, bg=BG_DARK, width=88, height=88,
                             highlightbackground=BORDER, highlightthickness=1,
                             cursor="hand2")
        img_frame.pack(side="right")
        img_frame.pack_propagate(False)
        img_frame.bind("<Button-1>", lambda e: self._pick_image())

        self.img_label = tk.Label(img_frame, text="🐉", font=("Segoe UI", 34),
                                  bg=BG_DARK, fg="#4fc3f7", cursor="hand2")
        self.img_label.place(relx=0.5, rely=0.5, anchor="center")
        self.img_label.bind("<Button-1>", lambda e: self._pick_image())
        self._photo = None

        # Duração
        dur_row = tk.Frame(client, bg=BG)
        dur_row.pack(fill="x", pady=(6, 0))
        tk.Label(dur_row, text="Duração:", bg=BG, fg=FG_DIM,
                 font=("Segoe UI", 10)).pack(side="left")
        self.dur_var = tk.StringVar(value=str(DEFAULT_MINUTES))
        dur_entry = tk.Entry(dur_row, textvariable=self.dur_var, width=4,
                             bg=BG_DARK, fg=FG, insertbackground=FG,
                             font=("Consolas", 12), relief="flat",
                             highlightbackground=BORDER, highlightthickness=1,
                             justify="center")
        dur_entry.pack(side="left", padx=(6, 4))
        tk.Label(dur_row, text="min", bg=BG, fg=FG_DIM,
                 font=("Segoe UI", 10)).pack(side="left")

        # Separador
        tk.Frame(client, bg=BORDER, height=1).pack(fill="x", pady=10)

        # Linha: Hidra + Iniciar
        bot = tk.Frame(client, bg=BG)
        bot.pack(fill="x")

        hidra_frame = tk.Frame(bot, bg=BG)
        hidra_frame.pack(side="left")
        tk.Label(hidra_frame, text="Hidra:", bg=BG, fg=FG_DIM,
                 font=("Segoe UI", 11)).pack(side="left")

        spin_outer = tk.Frame(hidra_frame, bg=BORDER, bd=1)
        spin_outer.pack(side="left", padx=(6, 0))

        self.hidra_lbl = tk.Label(spin_outer, text="0", bg=BG_DARK, fg=FG,
                                  font=("Consolas", 13), width=3)
        self.hidra_lbl.pack(side="left")

        spin_col = tk.Frame(spin_outer, bg=BG_DARK)
        spin_col.pack(side="left")
        for txt, delta in [("▲", 1), ("▼", -1)]:
            b = tk.Button(spin_col, text=txt, bg=BG_BTN, fg="#aaaaaa",
                          font=("Segoe UI", 6), bd=0, relief="flat",
                          activebackground=BG_BTN_H, activeforeground=FG,
                          cursor="hand2",
                          command=lambda d=delta: self._change_hidra(d))
            b.pack(fill="x")

        self.iniciar_btn = tk.Button(bot, text="Iniciar", bg=BG_BTN, fg=FG,
                                     font=("Segoe UI", 11), bd=0, relief="flat",
                                     padx=18, pady=4, cursor="hand2",
                                     activebackground=BG_BTN_H,
                                     activeforeground="#ffffff",
                                     command=self._toggle_timer)
        self.iniciar_btn.pack(side="right")

        # Som
        snd_row = tk.Frame(client, bg=BG)
        snd_row.pack(fill="x", pady=(10, 0))
        tk.Label(snd_row, text="Som final:", bg=BG, fg=FG_DIM,
                 font=("Segoe UI", 10)).pack(side="left")
        tk.Button(snd_row, text="📂 Escolher", bg=BG_BTN, fg="#aaaaaa",
                  font=("Segoe UI", 9), bd=0, relief="flat", padx=8, pady=2,
                  activebackground=BG_BTN_H, activeforeground=FG,
                  cursor="hand2", command=self._pick_sound).pack(side="left", padx=(6,6))
        self.snd_lbl = tk.Label(snd_row, text="beep do sistema", bg=BG,
                                 fg="#555555", font=("Segoe UI", 9))
        self.snd_lbl.pack(side="left")

        # Mute toggle
        self.mute_btn = tk.Button(snd_row, text="🔊", bg=BG, fg="#888",
                                   font=("Segoe UI", 11), bd=0, relief="flat",
                                   cursor="hand2", activebackground=BG,
                                   command=self._toggle_mute)
        self.mute_btn.pack(side="right")

        # ── Statusbar ─────────────────────────────────────────────────────────
        tk.Frame(self.root, bg=BORDER_D, height=1).pack(fill="x")
        status_bar = tk.Frame(self.root, bg="#252525", pady=3)
        status_bar.pack(fill="x")
        self.status_lbl = tk.Label(status_bar, text="⬤  Pronto", bg="#252525",
                                    fg="#666666", font=("Segoe UI", 9), padx=10)
        self.status_lbl.pack(side="left")

    # ── Drag ──────────────────────────────────────────────────────────────────
    def _drag_start(self, e):
        self._drag_x = e.x_root - self.root.winfo_x()
        self._drag_y = e.y_root - self.root.winfo_y()

    def _drag_motion(self, e):
        self.root.geometry(f"+{e.x_root - self._drag_x}+{e.y_root - self._drag_y}")

    # ── Janela ────────────────────────────────────────────────────────────────
    def _minimize(self):
        self.root.iconify()

    def _close(self):
        if self.after_id:
            self.root.after_cancel(self.after_id)
        self.root.destroy()

    # ── Timer ─────────────────────────────────────────────────────────────────
    def _toggle_timer(self):
        if not self.running:
            if self.remaining <= 0:
                try:
                    mins = int(self.dur_var.get())
                except ValueError:
                    mins = DEFAULT_MINUTES
                self.remaining = mins * 60
            self.running = True
            self.iniciar_btn.config(text="Parar", fg=FG_RED)
            self.status_lbl.config(text="▶  A correr...")
            self._tick()
        else:
            self.running = False
            if self.after_id:
                self.root.after_cancel(self.after_id)
            self.iniciar_btn.config(text="Retomar", fg=FG)
            self.status_lbl.config(text="⏸  Pausado")

    def _tick(self):
        if not self.running:
            return
        if self.remaining <= 0:
            self.running = False
            self.iniciar_btn.config(text="Iniciar", fg=FG)
            self.status_lbl.config(text="⬛  Terminado!")
            self._play_sound()
            return
        self.remaining -= 1
        self._update_display()
        self.after_id = self.root.after(1000, self._tick)

    def _update_display(self):
        m = self.remaining // 60
        s = self.remaining % 60
        txt = f"{m:02d}:{s:02d}"
        self.timer_lbl.config(text=txt)
        if self.remaining <= 60 and self.remaining > 0:
            self.timer_lbl.config(fg=FG_RED)
        else:
            self.timer_lbl.config(fg=FG)

    # ── Hidra ─────────────────────────────────────────────────────────────────
    def _change_hidra(self, delta):
        self.hidra = max(0, self.hidra + delta)
        self.hidra_lbl.config(text=str(self.hidra))

    # ── Som ───────────────────────────────────────────────────────────────────
    def _pick_sound(self):
        path = filedialog.askopenfilename(
            title="Escolher som",
            filetypes=[("Áudio", "*.wav *.mp3 *.ogg"), ("Todos", "*.*")]
        )
        if path:
            self.sound_path = path
            self.snd_lbl.config(text=os.path.basename(path), fg="#aaaaaa")

    def _toggle_mute(self):
        self.muted = not self.muted
        self.mute_btn.config(text="🔇" if self.muted else "🔊")

    def _play_sound(self):
        if self.muted:
            return
        if self.sound_path and os.path.exists(self.sound_path):
            try:
                if PYGAME_OK:
                    pygame.mixer.music.load(self.sound_path)
                    pygame.mixer.music.play()
                else:
                    if self.sound_path.endswith(".wav"):
                        winsound.PlaySound(self.sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception:
                pass
        # Beep do sistema sempre
        threading.Thread(target=self._beep, daemon=True).start()

    def _beep(self):
        for _ in range(3):
            try:
                winsound.Beep(880, 300)
            except Exception:
                pass
            import time; time.sleep(0.15)

    # ── Imagem ────────────────────────────────────────────────────────────────
    def _pick_image(self):
        path = filedialog.askopenfilename(
            title="Escolher imagem",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.gif *.bmp"), ("Todos", "*.*")]
        )
        if not path:
            return
        try:
            from PIL import Image, ImageTk
            img = Image.open(path).resize((88, 88), Image.LANCZOS)
            self._photo = ImageTk.PhotoImage(img)
            self.img_label.config(image=self._photo, text="")
        except ImportError:
            # sem Pillow, mostra só o nome
            name = os.path.basename(path)[:10]
            self.img_label.config(text=name, font=("Segoe UI", 8))


# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = TimerApp(root)
    root.mainloop()
