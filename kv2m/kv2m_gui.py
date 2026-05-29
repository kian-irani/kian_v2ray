#!/usr/bin/env python3
"""
Kv2m — رابط گرافیکی (Tkinter) برای ویندوز/مک/لینوکس
اجرا:  python kv2m.py        یا       python kv2m_gui.py
Tkinter همراه پایتون استاندارد نصب است (روی ویندوز/مک پیش‌فرض).
"""
import threading
import queue
import tkinter as tk
from tkinter import ttk, messagebox

import kv2m_core as core

BG = "#0c1118"; CARD = "#131c27"; ACC = "#2ee6a6"; TXT = "#e7eef5"; MUT = "#8ba0b4"; LINE = "#283a4d"
FONT = ("Segoe UI", 10)
MONO = ("Consolas", 9)


class App:
    def __init__(self, root):
        self.root = root
        self.ssh = None
        self.q = queue.Queue()
        root.title(f"Kv2m — مدیریت Kian V2Ray  v{core.APP_VERSION}")
        root.geometry("860x620")
        root.configure(bg=BG)
        self._style()
        self._build_conn_bar()
        self._build_tabs()
        self._poll_queue()

    # ---------------- style
    def _style(self):
        s = ttk.Style()
        try:
            s.theme_use("clam")
        except Exception:
            pass
        s.configure(".", background=BG, foreground=TXT, fieldbackground=CARD, font=FONT)
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background=CARD, foreground=MUT, padding=(14, 7))
        s.map("TNotebook.Tab", background=[("selected", ACC)], foreground=[("selected", "#04130d")])
        s.configure("TFrame", background=BG)
        s.configure("TLabel", background=BG, foreground=TXT)
        s.configure("Card.TFrame", background=CARD)
        s.configure("Accent.TButton", background=ACC, foreground="#04130d", font=("Segoe UI", 10, "bold"))
        s.map("Accent.TButton", background=[("active", "#22d3ee")])
        s.configure("Treeview", background=CARD, fieldbackground=CARD, foreground=TXT, rowheight=24)
        s.configure("Treeview.Heading", background=BG, foreground=ACC)

    # ---------------- connection bar
    def _build_conn_bar(self):
        bar = ttk.Frame(self.root, style="Card.TFrame")
        bar.pack(fill="x", padx=10, pady=10)
        self.e_host = self._field(bar, "آی‌پی/دامنه", 0, 18)
        self.e_port = self._field(bar, "پورت", 1, 5, "22")
        self.e_user = self._field(bar, "کاربر", 2, 9, "root")
        self.e_pass = self._field(bar, "رمز", 3, 14, show="•")
        self.btn_conn = ttk.Button(bar, text="اتصال", style="Accent.TButton", command=self.on_connect)
        self.btn_conn.grid(row=0, column=8, padx=8, pady=8)
        self.lbl_status = ttk.Label(bar, text="● قطع", foreground="#ff6b6b", background=CARD)
        self.lbl_status.grid(row=0, column=9, padx=8)

    def _field(self, parent, label, col, width, default="", show=None):
        ttk.Label(parent, text=label, background=CARD, foreground=MUT).grid(row=0, column=col * 2, padx=(8, 2), pady=8)
        e = tk.Entry(parent, width=width, bg=BG, fg=TXT, insertbackground=TXT, relief="flat", show=show)
        e.insert(0, default)
        e.grid(row=0, column=col * 2 + 1, pady=8)
        return e

    # ---------------- tabs
    def _build_tabs(self):
        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tab_dash = ttk.Frame(nb); nb.add(self.tab_dash, text="وضعیت و کاربرها")
        self.tab_mng = ttk.Frame(nb); nb.add(self.tab_mng, text="مدیریت کاربر")
        self.tab_cfg = ttk.Frame(nb); nb.add(self.tab_cfg, text="کانفیگ‌ها")
        self.tab_prov = ttk.Frame(nb); nb.add(self.tab_prov, text="نصب تازه")
        self._build_dash(); self._build_manage(); self._build_configs(); self._build_provision()

    def _build_dash(self):
        top = ttk.Frame(self.tab_dash); top.pack(fill="x", pady=8)
        ttk.Button(top, text="↻ تازه‌سازی", command=self.refresh_dash).pack(side="left", padx=8)
        self.dash_status = tk.Label(self.tab_dash, text="—", bg=BG, fg=MUT, anchor="w", justify="left", font=MONO)
        self.dash_status.pack(fill="x", padx=10)
        cols = ("email", "active", "used", "quota", "expiry")
        self.tree = ttk.Treeview(self.tab_dash, columns=cols, show="headings", height=14)
        for c, t in zip(cols, ("ایمیل", "فعال", "مصرف", "حجم", "انقضا")):
            self.tree.heading(c, text=t); self.tree.column(c, width=150 if c == "email" else 110)
        self.tree.pack(fill="both", expand=True, padx=10, pady=8)

    def _build_manage(self):
        f = ttk.Frame(self.tab_mng); f.pack(fill="x", padx=10, pady=12)
        ttk.Label(f, text="نام کاربر:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.m_name = tk.Entry(f, width=18, bg=BG, fg=TXT, insertbackground=TXT, relief="flat"); self.m_name.grid(row=0, column=1, pady=6)
        ttk.Label(f, text="حجم (گیگ، ۰=نامحدود):").grid(row=0, column=2, sticky="e", padx=6)
        self.m_gb = tk.Entry(f, width=8, bg=BG, fg=TXT, insertbackground=TXT, relief="flat"); self.m_gb.insert(0, "100"); self.m_gb.grid(row=0, column=3)
        ttk.Label(f, text="مدت (روز، ۰=دائمی):").grid(row=0, column=4, sticky="e", padx=6)
        self.m_days = tk.Entry(f, width=8, bg=BG, fg=TXT, insertbackground=TXT, relief="flat"); self.m_days.insert(0, "30"); self.m_days.grid(row=0, column=5)
        btns = ttk.Frame(self.tab_mng); btns.pack(fill="x", padx=10)
        ttk.Button(btns, text="➕ افزودن", style="Accent.TButton",
                   command=lambda: self._mng(core.cmd_add(self.m_name.get(), self._int(self.m_gb), self._int(self.m_days)))).pack(side="left", padx=5)
        ttk.Button(btns, text="🔄 تمدید", command=lambda: self._mng(core.cmd_renew(self.m_name.get(), self._int(self.m_days)))).pack(side="left", padx=5)
        ttk.Button(btns, text="♻️ تغییر/صفر حجم", command=lambda: self._mng(core.cmd_reset(self.m_name.get(), self._int(self.m_gb)))).pack(side="left", padx=5)
        ttk.Button(btns, text="🗑️ حذف", command=self._remove_confirm).pack(side="left", padx=5)
        self.mng_out = tk.Text(self.tab_mng, height=16, bg="#080c11", fg="#bfe9d8", relief="flat", font=MONO)
        self.mng_out.pack(fill="both", expand=True, padx=10, pady=10)

    def _build_configs(self):
        f = ttk.Frame(self.tab_cfg); f.pack(fill="x", padx=10, pady=12)
        ttk.Label(f, text="نام کاربر (خالی = همه):").grid(row=0, column=0, padx=6)
        self.c_name = tk.Entry(f, width=18, bg=BG, fg=TXT, insertbackground=TXT, relief="flat"); self.c_name.grid(row=0, column=1)
        ttk.Button(f, text="نمایش کانفیگ‌ها", style="Accent.TButton", command=self.show_configs).grid(row=0, column=2, padx=8)
        ttk.Button(f, text="کپی همه", command=self.copy_links).grid(row=0, column=3)
        self.cfg_list = tk.Listbox(self.tab_cfg, bg="#080c11", fg="#a7c6d8", relief="flat", font=MONO, selectmode="extended")
        self.cfg_list.pack(fill="both", expand=True, padx=10, pady=10)

    def _build_provision(self):
        f = ttk.Frame(self.tab_prov); f.pack(fill="x", padx=10, pady=12)
        self.p_mode = tk.StringVar(value="both")
        ttk.Label(f, text="حالت:").grid(row=0, column=0, padx=6)
        ttk.Combobox(f, textvariable=self.p_mode, values=["both", "direct", "warp", "nosni"], width=10, state="readonly").grid(row=0, column=1)
        ttk.Label(f, text="تعداد SNI:").grid(row=0, column=2, padx=6)
        self.p_sni = tk.Entry(f, width=5, bg=BG, fg=TXT, relief="flat"); self.p_sni.insert(0, "2"); self.p_sni.grid(row=0, column=3)
        ttk.Label(f, text="پورت پایه:").grid(row=0, column=4, padx=6)
        self.p_base = tk.Entry(f, width=7, bg=BG, fg=TXT, relief="flat"); self.p_base.insert(0, "8443"); self.p_base.grid(row=0, column=5)
        ttk.Label(f, text="کاربر:").grid(row=1, column=0, padx=6, pady=6)
        self.p_users = tk.Entry(f, width=5, bg=BG, fg=TXT, relief="flat"); self.p_users.insert(0, "1"); self.p_users.grid(row=1, column=1)
        ttk.Label(f, text="حجم(گیگ):").grid(row=1, column=2, padx=6)
        self.p_gb = tk.Entry(f, width=7, bg=BG, fg=TXT, relief="flat"); self.p_gb.insert(0, "0"); self.p_gb.grid(row=1, column=3)
        ttk.Label(f, text="مدت(روز):").grid(row=1, column=4, padx=6)
        self.p_days = tk.Entry(f, width=7, bg=BG, fg=TXT, relief="flat"); self.p_days.insert(0, "0"); self.p_days.grid(row=1, column=5)
        ttk.Label(f, text="⚠️ اگر روی این سرور Xray دیگری داری، «پورت پایه» را عوض کن (مثلاً 9443).",
                  foreground="#f5b945", background=BG).grid(row=2, column=0, columnspan=6, sticky="w", pady=6)
        ttk.Button(self.tab_prov, text="🚀 نصب روی سرور", style="Accent.TButton", command=self.do_provision).pack(anchor="w", padx=10)
        self.prov_out = tk.Text(self.tab_prov, height=16, bg="#080c11", fg="#bfe9d8", relief="flat", font=MONO)
        self.prov_out.pack(fill="both", expand=True, padx=10, pady=10)

    # ---------------- helpers
    def _int(self, entry, default=0):
        try:
            return int(entry.get().strip() or default)
        except ValueError:
            return default

    def _need_conn(self):
        if not (self.ssh and self.ssh.client):
            messagebox.showwarning("اتصال", "اول به سرور وصل شو.")
            return False
        return True

    def _bg(self, fn):
        threading.Thread(target=fn, daemon=True).start()

    def _poll_queue(self):
        try:
            while True:
                fn = self.q.get_nowait()
                fn()
        except queue.Empty:
            pass
        self.root.after(80, self._poll_queue)

    def _ui(self, fn):
        self.q.put(fn)

    # ---------------- actions
    def on_connect(self):
        host = self.e_host.get().strip()
        if not host:
            messagebox.showwarning("اتصال", "آی‌پی سرور را وارد کن.")
            return
        self.btn_conn.config(state="disabled")
        self.lbl_status.config(text="● در حال اتصال…", foreground="#f5b945")

        def work():
            try:
                ssh = core.SSH().connect(host, self._int(self.e_port, 22), self.e_user.get().strip() or "root",
                                         password=self.e_pass.get() or None)
                self.ssh = ssh
                rc, out, _ = ssh.run(core.cmd_installed_check())
                installed = "KV2M_OK" in out
                self._ui(lambda: self.lbl_status.config(text="● متصل", foreground=ACC))
                self._ui(lambda: self.btn_conn.config(state="normal"))
                if not installed:
                    self._ui(lambda: messagebox.showinfo("نصب نشده", "روی این سرور kian-v2ray نصب نیست.\nاز تب «نصب تازه» استفاده کن."))
                else:
                    self._ui(self.refresh_dash)
            except Exception as e:
                self._ui(lambda: self.lbl_status.config(text="● قطع", foreground="#ff6b6b"))
                self._ui(lambda: self.btn_conn.config(state="normal"))
                self._ui(lambda: messagebox.showerror("خطای اتصال", str(e)))
        self._bg(work)

    def refresh_dash(self):
        if not self._need_conn():
            return
        def work():
            rc, st, _ = self.ssh.run(core.cmd_status())
            rc2, us, _ = self.ssh.run(core.cmd_users())
            rows = core.parse_users(us)
            def upd():
                self.dash_status.config(text=st.strip()[:600] or "—")
                self.tree.delete(*self.tree.get_children())
                for r in rows:
                    self.tree.insert("", "end", values=(r["email"], r["active"], r["used"], r["quota"], r["expiry"]))
            self._ui(upd)
        self._bg(work)

    def _mng(self, cmd):
        if not self._need_conn():
            return
        def work():
            rc, out, err = self.ssh.run(cmd)
            self._ui(lambda: (self.mng_out.delete("1.0", "end"), self.mng_out.insert("end", out or err or "انجام شد.")))
            self._ui(self.refresh_dash)
        self._bg(work)

    def _remove_confirm(self):
        name = self.m_name.get().strip()
        if name and messagebox.askyesno("حذف", f"کاربر «{name}» حذف شود؟"):
            self._mng(core.cmd_remove(name))

    def show_configs(self):
        if not self._need_conn():
            return
        def work():
            rc, out, err = self.ssh.run(core.cmd_configs(self.c_name.get().strip()))
            links = core.parse_links(out)
            def upd():
                self.cfg_list.delete(0, "end")
                for ln in (links or [out or err]):
                    self.cfg_list.insert("end", ln)
            self._ui(upd)
        self._bg(work)

    def copy_links(self):
        items = self.cfg_list.get(0, "end")
        if items:
            self.root.clipboard_clear()
            self.root.clipboard_append("\n".join(items))
            messagebox.showinfo("کپی", f"{len(items)} لینک کپی شد.")

    def do_provision(self):
        if not self._need_conn():
            return
        opts = {"server_ip": self.ssh.host, "mode": self.p_mode.get(), "sni_mode": "auto",
                "sni_count": self._int(self.p_sni, 2), "base_port": self._int(self.p_base, 8443),
                "num_users": self._int(self.p_users, 1), "prefix": "user",
                "quota_gb": self._int(self.p_gb, 0), "days": self._int(self.p_days, 0)}
        g = core.generate(opts)
        self.prov_out.delete("1.0", "end")
        self.prov_out.insert("end", f"کلید ساخته شد. پورت‌ها: {g['ports']}\nشروع نصب…\n\n")
        cmd = (f"export KIAN_PAYLOAD='{g['payload_b64']}'; "
               f"curl -fsSL {core.RAW_BASE}/install.sh -o /tmp/kian-v2ray.sh && bash /tmp/kian-v2ray.sh")

        def work():
            try:
                self.ssh.run_stream(cmd, lambda line: self._ui(lambda l=line: (self.prov_out.insert("end", l + "\n"), self.prov_out.see("end"))))
            except Exception as e:
                self._ui(lambda: self.prov_out.insert("end", f"\nخطا: {e}\n"))
            def done():
                self.prov_out.insert("end", "\n✔ نصب اجرا شد. لینک‌ها:\n")
                for u in g["per_user"]:
                    for it in u["items"]:
                        self.prov_out.insert("end", it["link"] + "\n")
                if g["ss_link"]:
                    self.prov_out.insert("end", g["ss_link"] + "\n")
                self.prov_out.see("end")
            self._ui(done)
            self._ui(self.refresh_dash)
        self._bg(work)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
