"""Tkinter GUI: paste text, tune the settings, click Start, switch to your
target window during the countdown."""
from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk, messagebox

from .core import Config


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Japanese Auto Typer")
        root.geometry("560x560")

        self.stop_event = threading.Event()
        self.worker: threading.Thread | None = None

        pad = {"padx": 8, "pady": 4}

        tk.Label(root, text="Text to type:").pack(anchor="w", **pad)
        self.text_box = tk.Text(root, height=14, wrap="word", font=("TkDefaultFont", 12))
        self.text_box.pack(fill="both", expand=True, padx=8)

        settings = ttk.LabelFrame(root, text="Settings")
        settings.pack(fill="x", padx=8, pady=8)

        self.cpm_min = self._labeled_spinbox(settings, "Min speed (chars/min)", 30, 1000, 180, 0)
        self.cpm_max = self._labeled_spinbox(settings, "Max speed (chars/min)", 30, 1000, 340, 1)
        self.typo_rate = self._labeled_spinbox(settings, "Typo chance (%)", 0, 50, 4, 2)
        self.pause_rate = self._labeled_spinbox(settings, "Random pause chance (%)", 0, 50, 3, 3)
        self.start_delay = self._labeled_spinbox(settings, "Start delay (seconds)", 1, 30, 5, 4)

        btn_frame = tk.Frame(root)
        btn_frame.pack(fill="x", padx=8, pady=8)
        self.start_btn = ttk.Button(btn_frame, text="Start", command=self.on_start)
        self.start_btn.pack(side="left", padx=4)
        self.stop_btn = ttk.Button(btn_frame, text="Stop", command=self.on_stop, state="disabled")
        self.stop_btn.pack(side="left", padx=4)

        self.status = tk.StringVar(value="Paste your text, then press Start.")
        tk.Label(root, textvariable=self.status, anchor="w", fg="#555").pack(fill="x", padx=8, pady=(0, 8))

    def _labeled_spinbox(self, parent, label, lo, hi, default, row):
        tk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=6, pady=3)
        var = tk.IntVar(value=default)
        spin = tk.Spinbox(parent, from_=lo, to=hi, textvariable=var, width=8)
        spin.grid(row=row, column=1, sticky="w", padx=6, pady=3)
        return var

    def _set_status(self, msg: str):
        self.root.after(0, lambda: self.status.set(msg))

    def on_start(self):
        text = self.text_box.get("1.0", "end-1c")
        if not text.strip():
            messagebox.showwarning("No text", "Paste some text first.")
            return
        if int(self.cpm_min.get()) > int(self.cpm_max.get()):
            messagebox.showwarning("Invalid range", "Min speed must be <= max speed.")
            return

        config = Config(
            cpm_min=int(self.cpm_min.get()),
            cpm_max=int(self.cpm_max.get()),
            typo_rate=int(self.typo_rate.get()) / 100.0,
            pause_rate=int(self.pause_rate.get()) / 100.0,
        )
        start_delay = int(self.start_delay.get())

        self.stop_event.clear()
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

        def worker():
            from . import backend

            try:
                backend.run(
                    text,
                    config,
                    stop_event=self.stop_event,
                    start_delay=start_delay,
                    on_tick=self._set_status,
                )
                if self.stop_event.is_set():
                    self._set_status("Stopped.")
                else:
                    self._set_status("Done.")
            except Exception as exc:  # surface backend errors (e.g. no display)
                self._set_status(f"Error: {exc}")
            finally:
                self.root.after(0, lambda: self.start_btn.config(state="normal"))
                self.root.after(0, lambda: self.stop_btn.config(state="disabled"))

        self.worker = threading.Thread(target=worker, daemon=True)
        self.worker.start()

    def on_stop(self):
        self.stop_event.set()
        self.status.set("Stopping...")


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
