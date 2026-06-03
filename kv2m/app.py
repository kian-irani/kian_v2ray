#!/usr/bin/env python3
"""kv2m Qt UI — frameless window, icon sidebar, pages. Depends on core + i18n + theme."""
import base64, io
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QLineEdit, QComboBox, QCheckBox,
    QHBoxLayout, QVBoxLayout, QGridLayout, QFrame, QStackedWidget, QScrollArea,
    QTextEdit, QSizePolicy, QSpacerItem, QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, QThread, Signal, QPoint, QTimer, QSize
from PySide6.QtGui import QPixmap, QImage, QColor, QFont

import core, theme
from i18n import tr, set_lang, get_lang, is_rtl, load_settings, save_settings

NAV = [("nav.generate","⚡"),("nav.install","🚀"),("nav.manage","👥"),("nav.settings","⚙"),("nav.about","ℹ")]
MODES = [("both","mode.both"),("direct","mode.direct"),("warp","mode.warp"),("nosni","mode.nosni")]
TLS_ORDER = ["vless-ws","vmess-ws","vless-grpc","vmess-grpc","trojan-ws","vless-httpupgrade","vmess-httpupgrade"]


def qr_pixmap(data, size=150):
    try:
        import qrcode
        img = qrcode.make(data)
        buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
        qi = QImage.fromData(buf.read(), "PNG")
        return QPixmap.fromImage(qi).scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    except Exception:
        return None


class Worker(QThread):
    ok = Signal(object); fail = Signal(str)
    def __init__(self, fn): super().__init__(); self.fn = fn
    def run(self):
        try: self.ok.emit(self.fn())
        except Exception as e: self.fail.emit(str(e))


class StreamWorker(QThread):
    line = Signal(str); done = Signal(int); fail = Signal(str)
    def __init__(self, ssh, cmd): super().__init__(); self.ssh = ssh; self.cmd = cmd
    def run(self):
        try: self.done.emit(self.ssh.run_stream(self.cmd, lambda l: self.line.emit(l)))
        except Exception as e: self.fail.emit(str(e))


def card():
    f = QFrame(); f.setObjectName("card")
    sh = QGraphicsDropShadowEffect(); sh.setBlurRadius(24); sh.setColor(QColor(0,0,0,120)); sh.setOffset(0,4)
    f.setGraphicsEffect(sh)
    return f


class TitleBar(QWidget):
    def __init__(self, win):
        super().__init__(); self.win = win; self.setObjectName("titlebar"); self.setFixedHeight(42)
        self._drag = None
        lay = QHBoxLayout(self); lay.setContentsMargins(14,0,8,0); lay.setSpacing(8)
        dot = QLabel("⚡"); dot.setStyleSheet("color:#76B900;font-size:16px")
        title = QLabel("Kv2m")
        lay.addWidget(dot); lay.addWidget(title); lay.addStretch(1)
        mn = QPushButton("—"); mn.setObjectName("winbtn"); mn.setFixedSize(34,28); mn.clicked.connect(win.showMinimized)
        cl = QPushButton("✕"); cl.setObjectName("winbtn"); cl.setProperty("class","close"); cl.setFixedSize(34,28)
        cl.setObjectName("winclose"); cl.clicked.connect(win.close)
        lay.addWidget(mn); lay.addWidget(cl)
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton: self._drag = e.globalPosition().toPoint() - self.win.frameGeometry().topLeft()
    def mouseMoveEvent(self, e):
        if self._drag and e.buttons() & Qt.LeftButton:
            self.win.move(e.globalPosition().toPoint() - self._drag)
    def mouseReleaseEvent(self, e): self._drag = None


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("root")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.resize(1120, 720); self.setMinimumSize(980, 640)
        self.ssh = core.SSH(); self.connected = False
        self._workers = []
        self._outer = QVBoxLayout(self); self._outer.setContentsMargins(0,0,0,0); self._outer.setSpacing(0)
        self._build()

    # ---- (re)build entire UI (used on language switch) ----
    def _build(self):
        while self._outer.count():
            it = self._outer.takeAt(0)
            if it.widget(): it.widget().deleteLater()
        QApplication.instance().setLayoutDirection(Qt.RightToLeft if is_rtl() else Qt.LeftToRight)
        self.setWindowTitle(tr("app.title"))

        self._outer.addWidget(TitleBar(self))

        body = QWidget(); bl = QHBoxLayout(body); bl.setContentsMargins(0,0,0,0); bl.setSpacing(0)
        self._outer.addWidget(body, 1)

        # sidebar
        sb = QWidget(); sb.setObjectName("sidebar"); sb.setFixedWidth(210)
        sbl = QVBoxLayout(sb); sbl.setContentsMargins(14,16,14,14); sbl.setSpacing(6)
        brand = QLabel("Kv2m"); brand.setObjectName("brand")
        sub = QLabel(f"v{core.APP_VERSION}  ·  kian_v2ray"); sub.setObjectName("brandsub")
        sbl.addWidget(brand); sbl.addWidget(sub); sbl.addSpacing(14)
        self._navbtns = []
        for i,(key,icon) in enumerate(NAV):
            b = QPushButton(f"  {icon}   {tr(key)}"); b.setObjectName("navbtn"); b.setCheckable(False)
            b.clicked.connect(lambda _,n=i: self._nav(n))
            sbl.addWidget(b); self._navbtns.append(b)
        sbl.addStretch(1)
        bl.addWidget(sb)

        # content
        content = QWidget(); content.setObjectName("content")
        cl = QVBoxLayout(content); cl.setContentsMargins(0,0,0,0); cl.setSpacing(0)
        cl.addWidget(self._conn_bar())
        self.stack = QStackedWidget()
        self.stack.addWidget(self._page_generate())
        self.stack.addWidget(self._page_install())
        self.stack.addWidget(self._page_manage())
        self.stack.addWidget(self._page_settings())
        self.stack.addWidget(self._page_about())
        cl.addWidget(self.stack, 1)
        bl.addWidget(content, 1)

        self._nav(0)
        self.setStyleSheet(theme.qss())

    # ---- connection bar ----
    def _conn_bar(self):
        w = QWidget(); w.setObjectName("connbar"); w.setFixedHeight(58)
        l = QHBoxLayout(w); l.setContentsMargins(18,0,18,0); l.setSpacing(8)
        def lab(t):
            x = QLabel(t); x.setObjectName("muted"); return x
        self.e_host = QLineEdit(); self.e_host.setPlaceholderText("1.2.3.4"); self.e_host.setFixedWidth(150)
        self.e_user = QLineEdit("root"); self.e_user.setFixedWidth(90)
        self.e_pass = QLineEdit(); self.e_pass.setEchoMode(QLineEdit.Password); self.e_pass.setPlaceholderText("••••"); self.e_pass.setFixedWidth(120)
        self.e_port = QLineEdit("22"); self.e_port.setFixedWidth(55)
        l.addWidget(lab(tr("conn.host"))); l.addWidget(self.e_host)
        l.addWidget(lab(tr("conn.user"))); l.addWidget(self.e_user)
        l.addWidget(lab(tr("conn.pass"))); l.addWidget(self.e_pass)
        l.addWidget(lab(tr("conn.port"))); l.addWidget(self.e_port)
        self.b_conn = QPushButton(tr("conn.connect")); self.b_conn.setObjectName("primary"); self.b_conn.clicked.connect(self._do_connect)
        l.addWidget(self.b_conn)
        self.l_status = QLabel("● " + tr("conn.disconnected")); self.l_status.setObjectName("status_off")
        l.addStretch(1); l.addWidget(self.l_status)
        return w

    # ---- generate page ----
    def _page_generate(self):
        page = QScrollArea(); page.setWidgetResizable(True)
        host = QWidget(); v = QVBoxLayout(host); v.setContentsMargins(22,18,22,18); v.setSpacing(12)
        page.setWidget(host)

        v.addWidget(self._h1(tr("gen.title")))

        c = card(); g = QGridLayout(c); g.setContentsMargins(16,14,16,14); g.setSpacing(10)
        def mut(t): x=QLabel(t); x.setObjectName("muted"); return x
        self.g_ip = QLineEdit(); self.g_ip.setPlaceholderText("1.2.3.4")
        self.g_mode = QComboBox(); [self.g_mode.addItem(tr(m[1]), m[0]) for m in MODES]
        self.g_users = QLineEdit("1"); self.g_users.setFixedWidth(70)
        self.g_prefix = QLineEdit("user")
        self.g_quota = QLineEdit("0"); self.g_quota.setFixedWidth(80)
        self.g_days = QLineEdit("0"); self.g_days.setFixedWidth(80)
        g.addWidget(mut(tr("gen.serverip")),0,0); g.addWidget(self.g_ip,0,1)
        g.addWidget(mut(tr("gen.mode")),0,2); g.addWidget(self.g_mode,0,3)
        g.addWidget(mut(tr("gen.users")),1,0); g.addWidget(self.g_users,1,1)
        g.addWidget(mut(tr("gen.prefix")),1,2); g.addWidget(self.g_prefix,1,3)
        g.addWidget(mut(tr("gen.quota")),2,0); g.addWidget(self.g_quota,2,1)
        g.addWidget(mut(tr("gen.days")),2,2); g.addWidget(self.g_days,2,3)
        v.addWidget(c)

        # advanced
        adv = card(); av = QVBoxLayout(adv); av.setContentsMargins(16,12,16,12); av.setSpacing(8)
        self.adv_btn = QPushButton("▸  " + tr("gen.advanced")); self.adv_btn.setObjectName("ghost")
        self.adv_body = QWidget(); self.adv_body.setVisible(False)
        ab = QGridLayout(self.adv_body); ab.setContentsMargins(0,8,0,0); ab.setSpacing(10)
        self.a_ss = QCheckBox(tr("gen.ss"))
        self.a_ssport = QLineEdit("8388"); self.a_ssport.setFixedWidth(90)
        self.a_base = QLineEdit(); self.a_base.setPlaceholderText("8443"); self.a_base.setFixedWidth(90)
        ab.addWidget(self.a_ss,0,0,1,2)
        ab.addWidget(mut(tr("gen.ssport")),0,2); ab.addWidget(self.a_ssport,0,3)
        ab.addWidget(mut(tr("gen.baseport")),1,0); ab.addWidget(self.a_base,1,1)
        # SNI selection (parity with web page)
        self.a_snimode = QComboBox(); self.a_snimode.addItem(tr("sni.auto"),"auto"); self.a_snimode.addItem(tr("sni.manual"),"manual")
        self.a_snicount = QComboBox(); [self.a_snicount.addItem(str(n),n) for n in (1,2,3)]; self.a_snicount.setCurrentIndex(1)
        self.a_snicustom = QLineEdit(); self.a_snicustom.setPlaceholderText("www.icloud.com"); self.a_snicustom.setEnabled(False)
        ab.addWidget(mut(tr("sni.mode")),1,2); ab.addWidget(self.a_snimode,1,3)
        ab.addWidget(mut(tr("sni.count")),2,0); ab.addWidget(self.a_snicount,2,1)
        ab.addWidget(mut(tr("sni.custom")),2,2); ab.addWidget(self.a_snicustom,2,3)
        def _sni_sync():
            man = self.a_snimode.currentData()=="manual"
            self.a_snicustom.setEnabled(man); self.a_snicount.setEnabled(not man)
        self.a_snimode.currentIndexChanged.connect(lambda _: _sni_sync())
        # TLS
        self.a_tls = QCheckBox(tr("gen.tls")); ab.addWidget(self.a_tls,3,0,1,4)
        tlshelp = QLabel(tr("gen.tlshelp")); tlshelp.setObjectName("muted"); tlshelp.setWordWrap(True)
        ab.addWidget(tlshelp,4,0,1,4)
        self.a_domain = QLineEdit(); self.a_domain.setPlaceholderText("vpn.example.com")
        self.a_chan = QComboBox()
        self.a_chan.addItem(tr("ch.direct"),"direct"); self.a_chan.addItem(tr("ch.warp"),"warp"); self.a_chan.addItem(tr("ch.both"),"both")
        ab.addWidget(mut(tr("gen.domain")),5,0); ab.addWidget(self.a_domain,5,1,1,2); ab.addWidget(self.a_chan,5,3)
        protrow = QWidget(); pr = QGridLayout(protrow); pr.setContentsMargins(0,0,0,0); pr.setSpacing(6)
        pr.addWidget(mut(tr("gen.protocols")),0,0,1,4)
        self.a_protos = {}
        for i,k in enumerate(TLS_ORDER):
            cb = QCheckBox(core.TLS_PROTOS[k]["label"]); self.a_protos[k]=cb
            if k=="vless-ws": cb.setChecked(True)
            pr.addWidget(cb, 1+i//4, i%4)
        ab.addWidget(protrow,6,0,1,4)
        av.addWidget(self.adv_btn); av.addWidget(self.adv_body)
        self.adv_btn.clicked.connect(self._toggle_adv)
        v.addWidget(adv)

        # generate button
        row = QWidget(); rl = QHBoxLayout(row); rl.setContentsMargins(0,0,0,0)
        gb = QPushButton(tr("gen.button")); gb.setObjectName("primary"); gb.setFixedHeight(40); gb.clicked.connect(self._do_gen)
        hint = QLabel(tr("gen.hint")); hint.setObjectName("muted"); hint.setWordWrap(True)
        rl.addWidget(gb); rl.addSpacing(12); rl.addWidget(hint,1)
        v.addWidget(row)

        self.gen_result = QVBoxLayout(); self.gen_result.setSpacing(10)
        rw = QWidget(); rw.setLayout(self.gen_result); v.addWidget(rw)
        v.addStretch(1)
        return page

    def _toggle_adv(self):
        vis = not self.adv_body.isVisible()
        self.adv_body.setVisible(vis)
        self.adv_btn.setText(("▾  " if vis else "▸  ") + tr("gen.advanced"))

    def _clear_layout(self, lay):
        while lay.count():
            it = lay.takeAt(0)
            if it.widget(): it.widget().deleteLater()
            elif it.layout(): self._clear_layout(it.layout())

    def _do_gen(self):
        ip = self.g_ip.text().strip() or self.e_host.text().strip()
        if not ip: return self._toast(tr("toast.noip"), True)
        def num(le, d):
            t = le.text().strip(); return int(t) if t.isdigit() else d
        opts = {
            "server_ip": ip, "mode": self.g_mode.currentData(),
            "num_users": max(1,min(50,num(self.g_users,1))), "prefix": (self.g_prefix.text().strip() or "user"),
            "quota_gb": num(self.g_quota,0), "days": num(self.g_days,0),
            "sni_mode": self.a_snimode.currentData(),
            "sni_count": self.a_snicount.currentData(),
            "sni_manual": self.a_snicustom.text().strip(),
            "ss_enabled": self.a_ss.isChecked(), "ss_port": num(self.a_ssport,8388),
            "base_port": num(self.a_base,8443) if self.a_base.text().strip() else None,
            "tls_enabled": self.a_tls.isChecked(), "tls_domain": self.a_domain.text().strip().lower(),
            "tls_channel": self.a_chan.currentData(),
            "tls_protos": [k for k,cb in self.a_protos.items() if cb.isChecked()],
        }
        try: g = core.generate(opts)
        except Exception as e: return self._toast(f"{tr('toast.err')}: {e}", True)
        self._last = g
        self._render_gen(g)
        self._sync_gists(g)

    def _sync_gists(self, g):
        iid = g.get("install_id"); items = g.get("sub_items") or {}
        if not iid or not items: return
        def job(): return core.sync_gists(iid, items)
        w = Worker(job)
        def on_ok(urls):
            if urls:
                g["_gist"] = urls
                if self._last is g: self._render_gen(g)
        w.ok.connect(on_ok); w.fail.connect(lambda e: None)
        self._workers.append(w); w.start()

    def _render_gen(self, g):
        self._clear_layout(self.gen_result)
        # install command card
        ic = card(); il = QVBoxLayout(ic); il.setContentsMargins(16,12,16,12); il.setSpacing(8)
        hdr = QHBoxLayout()
        hdr.addWidget(self._h2(tr("gen.installcmd"))); hdr.addStretch(1)
        cp = QPushButton("📋 "+tr("gen.copy")); cp.setObjectName("info"); cp.clicked.connect(lambda: self._copy(g["install_cmd"]))
        rn = QPushButton("🚀 "+tr("gen.runserver")); rn.setObjectName("primary"); rn.clicked.connect(lambda: self._run_install(g))
        hdr.addWidget(rn); hdr.addWidget(cp)
        il.addLayout(hdr)
        box = QTextEdit(); box.setReadOnly(True); box.setFixedHeight(58); box.setPlainText(g["install_cmd"])
        il.addWidget(box)
        self.gen_result.addWidget(ic)
        # per user
        for pu in g["per_user"]:
            uc = card(); ul = QVBoxLayout(uc); ul.setContentsMargins(16,12,16,12); ul.setSpacing(6)
            uh = QHBoxLayout()
            t = QLabel(f"👤 {tr('gen.user')}: {pu['local']}"); t.setObjectName("h2")
            uh.addWidget(t); uh.addStretch(1)
            links = [it["link"] for it in pu["items"]] + [x["link"] for x in pu.get("tlsLinks",[])]
            if g["ss_link"]: links.append(g["ss_link"])
            ca = QPushButton("📋 "+tr("gen.copyall")); ca.setObjectName("ghost"); ca.clicked.connect(lambda _,ls=links: self._copy("\n".join(ls)))
            uh.addWidget(ca); ul.addLayout(uh)
            for it in pu["items"]: ul.addWidget(self._link_row(it["link"], f"{tr('ch.'+it['channel'])} · {it['sni']}"))
            for x in pu.get("tlsLinks",[]): ul.addWidget(self._link_row(x["link"], f"🌐 {x['label']}"))
            gist = (g.get("_gist") or {}).get(pu["subToken"])
            sub_url = gist or (pu.get("subUrls") or [""])[0]
            if sub_url:
                sub = QHBoxLayout(); sl = QLabel(("🔗 HTTPS " if gist else "") + tr("gen.sublink")); sl.setObjectName("muted")
                su = QLabel(sub_url); su.setStyleSheet("color:#76B900" if gist else "color:#E3B341")
                cpy = QPushButton("📋"); cpy.setObjectName("mini"); cpy.clicked.connect(lambda _,u=sub_url: self._copy(u))
                sub.addWidget(sl); sub.addWidget(su); sub.addStretch(1); sub.addWidget(cpy); ul.addLayout(sub)
            self.gen_result.addWidget(uc)

    def _link_row(self, link, title):
        f = QFrame(); f.setObjectName("mono"); l = QHBoxLayout(f); l.setContentsMargins(10,6,8,6)
        t = QLabel(title); t.setObjectName("chip")
        v = QLabel(link[:64]+("…" if len(link)>64 else "")); v.setStyleSheet("color:#8A94A6;font-family:'Cascadia Code',monospace;font-size:11px")
        cp = QPushButton("📋"); cp.setObjectName("mini"); cp.clicked.connect(lambda: self._copy(link))
        qr = QPushButton("QR"); qr.setObjectName("mini"); qr.clicked.connect(lambda: self._show_qr(link))
        l.addWidget(t); l.addWidget(v,1); l.addWidget(qr); l.addWidget(cp)
        return f

    def _show_qr(self, link):
        pm = qr_pixmap(link, 220)
        dlg = QFrame(self); dlg.setObjectName("card"); dlg.setFixedSize(260,300)
        dlg.move(self.width()//2-130, self.height()//2-150)
        dl = QVBoxLayout(dlg); dl.setAlignment(Qt.AlignCenter)
        if pm: img = QLabel(); img.setPixmap(pm); dl.addWidget(img, alignment=Qt.AlignCenter)
        cl = QPushButton(tr("common.close")); cl.setObjectName("ghost"); cl.clicked.connect(dlg.deleteLater)
        dl.addWidget(cl, alignment=Qt.AlignCenter); dlg.show()

    # ---- install page ----
    def _page_install(self):
        page = QWidget(); v = QVBoxLayout(page); v.setContentsMargins(22,18,22,18); v.setSpacing(12)
        v.addWidget(self._h1(tr("nav.install")))
        c = card(); cl = QVBoxLayout(c); cl.setContentsMargins(16,12,16,12)
        self.inst_log = QTextEdit(); self.inst_log.setReadOnly(True); self.inst_log.setMinimumHeight(380)
        cl.addWidget(self.inst_log); v.addWidget(c,1)
        return page

    def _run_install(self, g):
        if not self.connected: return self._toast(tr("conn.disconnected"), True)
        self.stack.setCurrentIndex(1); self.inst_log.clear()
        cmd = f"export KIAN_PAYLOAD='{g['payload_b64']}'\ncurl -fsSL {core.RAW_BASE}/install.sh -o /tmp/kian-v2ray.sh && bash /tmp/kian-v2ray.sh"
        w = StreamWorker(self.ssh, cmd)
        w.line.connect(lambda l: self.inst_log.append(l))
        w.fail.connect(lambda e: self.inst_log.append(f"\n{tr('toast.err')}: {e}"))
        self._workers.append(w); w.start()

    # ---- manage page ----
    def _page_manage(self):
        page = QWidget(); v = QVBoxLayout(page); v.setContentsMargins(22,18,22,18); v.setSpacing(12)
        v.addWidget(self._h1(tr("manage.title")))
        c = card(); g = QGridLayout(c); g.setContentsMargins(16,14,16,14); g.setSpacing(10)
        def mut(t): x=QLabel(t); x.setObjectName("muted"); return x
        self.m_action = QComboBox()
        for val,lab in [("status","📊 status"),("users","📋 users"),("add","➕ add"),("configs","🔗 configs"),
                        ("sub","⭐ sub"),("renew","🔄 renew"),("reset","♻️ reset"),("remove","🗑️ remove"),
                        ("update","⬆️ update"),("uninstall","❌ uninstall")]:
            self.m_action.addItem(lab, val)
        self.m_name = QLineEdit(); self.m_name.setPlaceholderText("ali")
        self.m_gb = QLineEdit("100"); self.m_gb.setFixedWidth(80)
        self.m_days = QLineEdit("30"); self.m_days.setFixedWidth(80)
        g.addWidget(mut(tr("manage.action")),0,0); g.addWidget(self.m_action,0,1,1,3)
        g.addWidget(mut(tr("manage.name")),1,0); g.addWidget(self.m_name,1,1)
        g.addWidget(mut("GB"),1,2); g.addWidget(self.m_gb,1,3)
        g.addWidget(mut("Days"),2,2); g.addWidget(self.m_days,2,3)
        v.addWidget(c)
        c2 = card(); c2l = QVBoxLayout(c2); c2l.setContentsMargins(16,12,16,12)
        lbl = QLabel(tr("manage.run")); lbl.setObjectName("muted"); c2l.addWidget(lbl)
        self.m_out = QTextEdit(); self.m_out.setReadOnly(True); self.m_out.setFixedHeight(54); c2l.addWidget(self.m_out)
        rowb = QHBoxLayout()
        cp = QPushButton("📋 "+tr("gen.copy")); cp.setObjectName("info"); cp.clicked.connect(lambda: self._copy(self.m_out.toPlainText()))
        rn = QPushButton("🚀 "+tr("gen.runserver")); rn.setObjectName("primary"); rn.clicked.connect(self._run_manage)
        rowb.addStretch(1); rowb.addWidget(rn); rowb.addWidget(cp); c2l.addLayout(rowb)
        v.addWidget(c2); v.addStretch(1)
        self.m_action.currentIndexChanged.connect(self._upd_manage); self.m_name.textChanged.connect(self._upd_manage)
        self.m_gb.textChanged.connect(self._upd_manage); self.m_days.textChanged.connect(self._upd_manage)
        self._upd_manage()
        return page

    def _manage_cmd(self):
        a = self.m_action.currentData(); n = self.m_name.text().strip()
        def num(le,d): t=le.text().strip(); return int(t) if t.isdigit() else d
        m = {"status":core.cmd_status,"users":core.cmd_users,"update":core.cmd_update,"uninstall":core.cmd_uninstall}
        if a in m: return m[a]()
        if a=="add": return core.cmd_add(n,num(self.m_gb,100),num(self.m_days,30))
        if a=="configs": return core.cmd_configs(n)
        if a=="sub": return core.cmd_sub(n)
        if a=="renew": return core.cmd_renew(n,num(self.m_days,30))
        if a=="reset": return core.cmd_reset(n,num(self.m_gb,0))
        if a=="remove": return core.cmd_remove(n)
        return ""

    def _upd_manage(self): self.m_out.setPlainText(self._manage_cmd())

    def _run_manage(self):
        if not self.connected: return self._toast(tr("conn.disconnected"), True)
        cmd = self._manage_cmd()
        def job(): return self.ssh.run(cmd)
        w = Worker(job); w.ok.connect(lambda r: self._toast((r[1] or r[2])[:80] or tr("toast.copied")))
        w.fail.connect(lambda e: self._toast(f"{tr('toast.err')}: {e}", True))
        self._workers.append(w); w.start()

    # ---- settings page ----
    def _page_settings(self):
        page = QWidget(); v = QVBoxLayout(page); v.setContentsMargins(22,18,22,18); v.setSpacing(12)
        v.addWidget(self._h1(tr("settings.title")))
        # General
        c = card(); g = QGridLayout(c); g.setContentsMargins(16,14,16,14); g.setSpacing(12)
        g.addWidget(self._h2(tr("set.section.general")),0,0,1,2)
        lab = QLabel(tr("settings.language")); lab.setObjectName("muted")
        self.s_lang = QComboBox(); self.s_lang.addItem("English","en"); self.s_lang.addItem("فارسی","fa")
        self.s_lang.setCurrentIndex(0 if get_lang()=="en" else 1)
        self.s_lang.currentIndexChanged.connect(self._change_lang)
        g.addWidget(lab,1,0); g.addWidget(self.s_lang,1,1); g.setColumnStretch(2,1)
        hint = QLabel(tr("set.langhint")); hint.setObjectName("muted"); hint.setWordWrap(True)
        g.addWidget(hint,2,0,1,3)
        v.addWidget(c)
        # Paths & info
        c2 = card(); g2 = QVBoxLayout(c2); g2.setContentsMargins(16,14,16,14); g2.setSpacing(6)
        g2.addWidget(self._h2(tr("set.section.paths")))
        for txt in [f"📦 {tr('set.config')}: /etc/kian-v2ray/config.json",
                    "🐳 Xray: docker (kian-xray, --network host)",
                    "🌐 Caddy (TLS): /etc/caddy/Caddyfile",
                    "⚙ kv2m settings: %APPDATA%/kv2m/settings.json"]:
            l=QLabel(txt); l.setObjectName("muted"); l.setStyleSheet("font-family:'Cascadia Code',monospace;font-size:11px"); g2.addWidget(l)
        v.addWidget(c2)
        # Channels
        c3 = card(); g3 = QVBoxLayout(c3); g3.setContentsMargins(16,14,16,14); g3.setSpacing(8)
        g3.addWidget(self._h2(tr("set.channels")))
        row = QHBoxLayout()
        for label,url in [("📢 @kian_irani_cdn_f","https://t.me/kian_irani_cdn_f"),
                          ("💬 @Kian_irani_t","https://t.me/Kian_irani_t"),
                          ("⭐ GitHub","https://github.com/kian-irani/kian_v2ray")]:
            b=QPushButton(label); b.setObjectName("ghost"); b.clicked.connect(lambda _,u=url: self._copy(u)); row.addWidget(b)
        row.addStretch(1); g3.addLayout(row)
        tip=QLabel(tr("about.tip")); tip.setObjectName("muted"); tip.setWordWrap(True); g3.addWidget(tip)
        v.addWidget(c3); v.addStretch(1)
        return page

    def _change_lang(self):
        code = self.s_lang.currentData()
        if code == get_lang(): return
        set_lang(code); s = load_settings(); s["lang"] = code; save_settings(s)
        self._build()

    # ---- about page ----
    def _page_about(self):
        page = QScrollArea(); page.setWidgetResizable(True)
        host = QWidget(); v = QVBoxLayout(host); v.setContentsMargins(22,18,22,18); v.setSpacing(12); page.setWidget(host)
        v.addWidget(self._h1(tr("about.title")))
        c = card(); cl = QVBoxLayout(c); cl.setContentsMargins(18,16,18,16); cl.setSpacing(8)
        d = QLabel(tr("about.desc")); d.setObjectName("muted"); d.setWordWrap(True); cl.addWidget(d)
        ver = QLabel(f"⚡ Kv2m v{core.APP_VERSION}  ·  github.com/kian-irani/kian_v2ray"); ver.setStyleSheet("color:#76B900;font-weight:700")
        cl.addWidget(ver)
        v.addWidget(c)
        # Features
        cf = card(); fl = QVBoxLayout(cf); fl.setContentsMargins(18,14,18,14); fl.setSpacing(5)
        fl.addWidget(self._h2(tr("about.features")))
        for f in ["🛡️ VLESS Reality + Vision (well-known ports, auto SNI)",
                  "☁️ WARP outbound (WireGuard/MASQUE + auto fallback)",
                  "🔒 Shadowsocks (chacha20-ietf-poly1305)",
                  "🌐 Domain TLS: WS/gRPC/Trojan/HTTPUpgrade behind Caddy (direct/WARP/both)",
                  "⭐ HTTPS Subscription link (Cloudflare Worker + Gist)",
                  "👥 Multi-user, quota & expiry, QR codes"]:
            l=QLabel(f); l.setObjectName("muted"); l.setWordWrap(True); fl.addWidget(l)
        v.addWidget(cf)
        # Donate
        cd = card(); dl = QVBoxLayout(cd); dl.setContentsMargins(18,14,18,14); dl.setSpacing(6)
        dl.addWidget(self._h2("💝 "+tr("about.donate")))
        trc = QLabel("Tron (TRC20) — USDT/TRX:"); trc.setObjectName("muted"); dl.addWidget(trc)
        addr = "TEVuoZ7574341zbc8pc5jrrBrgqGGMys5q"
        arow = QHBoxLayout()
        al = QLabel(addr); al.setStyleSheet("font-family:'Cascadia Code',monospace;color:#E3B341"); al.setTextInteractionFlags(Qt.TextSelectableByMouse)
        ab2 = QPushButton("📋"); ab2.setObjectName("mini"); ab2.clicked.connect(lambda: self._copy(addr))
        arow.addWidget(al); arow.addStretch(1); arow.addWidget(ab2); dl.addLayout(arow)
        v.addWidget(cd); v.addStretch(1)
        return page

    # ---- helpers ----
    def _h1(self,t): x=QLabel(t); x.setObjectName("h1"); return x
    def _h2(self,t): x=QLabel(t); x.setObjectName("h2"); return x

    def _nav(self, idx):
        self.stack.setCurrentIndex(idx)
        for i,b in enumerate(self._navbtns):
            b.setProperty("active","true" if i==idx else "false")
            b.style().unpolish(b); b.style().polish(b)

    def _copy(self, text):
        QApplication.clipboard().setText(text); self._toast(tr("toast.copied"))

    def _toast(self, msg, err=False):
        t = QLabel(msg, self); t.setObjectName("toasterr" if err else "toast")
        t.adjustSize(); t.move(self.width()-t.width()-26, self.height()-t.height()-26); t.show()
        QTimer.singleShot(2200, t.deleteLater)

    def _do_connect(self):
        if self.connected:
            self.ssh.close(); self.connected=False
            self.b_conn.setText(tr("conn.connect")); self.l_status.setText("● "+tr("conn.disconnected")); self.l_status.setObjectName("status_off")
            self.l_status.style().unpolish(self.l_status); self.l_status.style().polish(self.l_status); return
        host=self.e_host.text().strip()
        if not host: return self._toast(tr("toast.noip"), True)
        self.b_conn.setText(tr("conn.connecting")); self.b_conn.setEnabled(False)
        port=self.e_port.text().strip() or "22"; user=self.e_user.text().strip() or "root"; pw=self.e_pass.text()
        def job(): return self.ssh.connect(host, port, user, pw or None)
        w = Worker(job)
        w.ok.connect(self._on_conn); w.fail.connect(self._on_conn_fail)
        self._workers.append(w); w.start()

    def _on_conn(self, _):
        self.connected=True; self.b_conn.setText(tr("conn.disconnect")); self.b_conn.setEnabled(True)
        self.l_status.setText("● "+tr("conn.connected")); self.l_status.setObjectName("status_ok")
        self.l_status.style().unpolish(self.l_status); self.l_status.style().polish(self.l_status)
        self._toast(tr("toast.connected"))

    def _on_conn_fail(self, e):
        self.connected=False; self.b_conn.setText(tr("conn.connect")); self.b_conn.setEnabled(True)
        self._toast(f"{tr('toast.err')}: {e}", True)


def run():
    import sys
    settings = load_settings()
    app = QApplication(sys.argv)
    if not settings.get("lang"):
        code = _ask_language(app); settings["lang"]=code; save_settings(settings)
    set_lang(settings.get("lang","en"))
    win = MainWindow(); win.show()
    sys.exit(app.exec())


def _ask_language(app):
    from PySide6.QtWidgets import QDialog
    app.setStyleSheet(theme.qss())
    dlg = QDialog(); dlg.setObjectName("root"); dlg.setWindowFlags(Qt.FramelessWindowHint); dlg.setFixedSize(360,220)
    v = QVBoxLayout(dlg); v.setContentsMargins(24,24,24,24); v.setSpacing(16)
    t = QLabel("⚡  Choose language / زبان را انتخاب کن"); t.setObjectName("h1"); t.setWordWrap(True); t.setAlignment(Qt.AlignCenter)
    v.addWidget(t)
    row = QHBoxLayout(); choice={"v":"en"}
    be = QPushButton("English"); be.setObjectName("primary"); be.setFixedHeight(44)
    bf = QPushButton("فارسی"); bf.setObjectName("ghost"); bf.setFixedHeight(44)
    be.clicked.connect(lambda: (choice.__setitem__("v","en"), dlg.accept()))
    bf.clicked.connect(lambda: (choice.__setitem__("v","fa"), dlg.accept()))
    row.addWidget(be); row.addWidget(bf); v.addLayout(row); v.addStretch(1)
    dlg.exec()
    return choice["v"]
