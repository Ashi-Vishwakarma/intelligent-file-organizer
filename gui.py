
import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

sys.path.insert(0, os.path.dirname(__file__))
from organizer import FileOrganizer


class App(tk.Tk):
    """Main application window."""

    PRIMARY   = "#2563EB"
    SUCCESS   = "#16A34A"
    DANGER    = "#DC2626"
    BG        = "#F1F5F9"
    CARD      = "#FFFFFF"
    TEXT      = "#1E293B"
    MUTED     = "#64748B"

    def __init__(self):
        super().__init__()
        self.title("Intelligent File Organizer")
        self.geometry("720x580")
        self.resizable(True, True)
        self.configure(bg=self.BG)

        self._build_ui()
        self._organizer: FileOrganizer | None = None

    # ── UI construction ────────────────────────────────────────────────────────

    def _build_ui(self):
        self._header()
        self._path_section()
        self._options_section()
        self._action_buttons()
        self._log_section()
        self._status_bar()

    def _header(self):
        hdr = tk.Frame(self, bg=self.PRIMARY, height=56)
        hdr.pack(fill="x")
        tk.Label(
            hdr,
            text="🗂  Intelligent File Organizer",
            font=("Segoe UI", 15, "bold"),
            fg="white", bg=self.PRIMARY,
        ).pack(side="left", padx=16, pady=12)

    def _path_section(self):
        card = self._card()
        tk.Label(card, text="Directories", font=("Segoe UI", 10, "bold"),
                 fg=self.TEXT, bg=self.CARD).grid(row=0, column=0, columnspan=3,
                                                   sticky="w", pady=(0, 8))

        # Source
        tk.Label(card, text="Source Folder:", fg=self.MUTED, bg=self.CARD,
                 font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w")
        self._src_var = tk.StringVar()
        tk.Entry(card, textvariable=self._src_var, width=52,
                 font=("Segoe UI", 9)).grid(row=1, column=1, padx=6)
        tk.Button(card, text="Browse", command=self._browse_src,
                  bg=self.PRIMARY, fg="white", relief="flat",
                  padx=8).grid(row=1, column=2)

        # Output (optional)
        tk.Label(card, text="Output Folder:", fg=self.MUTED, bg=self.CARD,
                 font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", pady=(6, 0))
        self._out_var = tk.StringVar()
        tk.Entry(card, textvariable=self._out_var, width=52,
                 font=("Segoe UI", 9)).grid(row=2, column=1, padx=6, pady=(6, 0))
        tk.Button(card, text="Browse", command=self._browse_out,
                  bg=self.PRIMARY, fg="white", relief="flat",
                  padx=8).grid(row=2, column=2, pady=(6, 0))

    def _options_section(self):
        card = self._card()
        tk.Label(card, text="Options", font=("Segoe UI", 10, "bold"),
                 fg=self.TEXT, bg=self.CARD).pack(anchor="w", pady=(0, 6))

        row = tk.Frame(card, bg=self.CARD)
        row.pack(anchor="w")

        self._dry_var = tk.BooleanVar(value=False)
        self._dup_var = tk.BooleanVar(value=True)

        tk.Checkbutton(row, text="Dry Run (preview only)",
                       variable=self._dry_var, bg=self.CARD,
                       font=("Segoe UI", 9)).pack(side="left", padx=(0, 20))
        tk.Checkbutton(row, text="Detect Duplicates",
                       variable=self._dup_var, bg=self.CARD,
                       font=("Segoe UI", 9)).pack(side="left")

    def _action_buttons(self):
        frame = tk.Frame(self, bg=self.BG, pady=6)
        frame.pack(fill="x", padx=16)

        self._run_btn = tk.Button(
            frame, text="▶  Organize Files",
            command=self._run,
            bg=self.SUCCESS, fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat", padx=16, pady=6,
        )
        self._run_btn.pack(side="left")

        tk.Button(
            frame, text="✕  Clear Log",
            command=self._clear_log,
            bg=self.MUTED, fg="white",
            font=("Segoe UI", 9),
            relief="flat", padx=10, pady=6,
        ).pack(side="left", padx=8)

    def _log_section(self):
        frame = tk.Frame(self, bg=self.BG)
        frame.pack(fill="both", expand=True, padx=16, pady=(0, 4))

        tk.Label(frame, text="Activity Log", font=("Segoe UI", 9, "bold"),
                 fg=self.MUTED, bg=self.BG).pack(anchor="w")

        self._log = scrolledtext.ScrolledText(
            frame,
            font=("Consolas", 9),
            wrap="word",
            bg="#0F172A", fg="#94A3B8",
            insertbackground="white",
            relief="flat", bd=0,
            state="disabled",
        )
        self._log.pack(fill="both", expand=True)

    def _status_bar(self):
        self._status_var = tk.StringVar(value="Ready.")
        tk.Label(
            self,
            textvariable=self._status_var,
            font=("Segoe UI", 8), fg=self.MUTED,
            bg=self.BG, anchor="w",
        ).pack(fill="x", padx=16, pady=(0, 6))

    def _card(self) -> tk.Frame:
        card = tk.Frame(self, bg=self.CARD, padx=14, pady=10,
                        relief="flat", bd=0)
        card.pack(fill="x", padx=16, pady=(8, 0))
        return card

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _browse_src(self):
        d = filedialog.askdirectory(title="Select Source Folder")
        if d:
            self._src_var.set(d)

    def _browse_out(self):
        d = filedialog.askdirectory(title="Select Output Folder")
        if d:
            self._out_var.set(d)

    def _log_msg(self, msg: str):
        self._log.configure(state="normal")
        self._log.insert("end", msg + "\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def _clear_log(self):
        self._log.configure(state="normal")
        self._log.delete("1.0", "end")
        self._log.configure(state="disabled")

    def _set_status(self, msg: str):
        self._status_var.set(msg)

    # ── Run logic (threaded so UI stays responsive) ────────────────────────────

    def _run(self):
        src = self._src_var.get().strip()
        if not src:
            messagebox.showwarning("Missing Input", "Please select a source folder.")
            return

        self._run_btn.configure(state="disabled", text="⏳ Running…")
        self._set_status("Organizing…")

        thread = threading.Thread(target=self._do_organize, daemon=True)
        thread.start()

    def _do_organize(self):
        src = self._src_var.get().strip()
        out = self._out_var.get().strip() or None

        import logging, io

        # Capture log output into the GUI
        log_stream = io.StringIO()
        handler = logging.StreamHandler(log_stream)
        handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

        try:
            organizer = FileOrganizer(
                source_dir        = src,
                output_dir        = out,
                handle_duplicates = self._dup_var.get(),
                dry_run           = self._dry_var.get(),
            )
            organizer.logger.addHandler(handler)
            report = organizer.organize()

            # Flush captured logs to GUI
            for line in log_stream.getvalue().splitlines():
                self.after(0, self._log_msg, line)

            s = report["stats"]
            summary = (
                f"\n Done  |  Moved: {s['moved']}  "
                f"Duplicates: {s['duplicates_found']}  "
                f"Errors: {s['errors']}"
            )
            self.after(0, self._log_msg, summary)
            self.after(0, self._set_status, f"Complete — {s['moved']} file(s) organized.")

        except NotADirectoryError as e:
            self.after(0, messagebox.showerror, "Error", str(e))
            self.after(0, self._set_status, "Error — see message.")

        finally:
            self.after(0, self._run_btn.configure,
                       {"state": "normal", "text": "▶  Organize Files"})


if __name__ == "__main__":
    app = App()
    app.mainloop()
