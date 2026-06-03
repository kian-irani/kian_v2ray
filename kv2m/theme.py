#!/usr/bin/env python3
"""kv2m theme — Termius layout + NVIDIA green accent. Returns a Qt stylesheet."""

C = {
    "bg":"#0B0F14","panel":"#12181F","card":"#161D26","card2":"#1B232E","border":"#222B36",
    "accent":"#76B900","accent_hi":"#8FD400","accent_dim":"#3d6100","accent2":"#1F6FEB",
    "text":"#E6EDF3","muted":"#8A94A6","error":"#F85149","warn":"#E3B341",
}

def qss():
    c = C
    return f"""
* {{ font-family: "Segoe UI","Vazirmatn",sans-serif; color: {c['text']}; font-size: 13px; }}
#root {{ background: {c['bg']}; border: 1px solid {c['border']}; border-radius: 14px; }}
#titlebar {{ background: {c['panel']}; border-top-left-radius: 14px; border-top-right-radius: 14px; }}
#titlebar QLabel {{ color: {c['text']}; font-weight: 600; }}
#winbtn {{ background: transparent; border: none; color: {c['muted']}; font-size: 15px; border-radius: 6px; }}
#winbtn:hover {{ background: {c['card2']}; color: {c['text']}; }}
#winclose:hover {{ background: {c['error']}; color: white; }}

#sidebar {{ background: {c['panel']}; }}
#navbtn {{ background: transparent; border: none; color: {c['muted']}; text-align: left;
          padding: 10px 14px; border-radius: 9px; font-size: 13px; }}
#navbtn:hover {{ background: {c['card2']}; color: {c['text']}; }}
#navbtn[active="true"] {{ background: {c['accent_dim']}; color: {c['accent_hi']}; font-weight: 600; }}
#brand {{ color: {c['text']}; font-size: 17px; font-weight: 700; }}
#brandsub {{ color: {c['muted']}; font-size: 10px; }}

#content {{ background: {c['bg']}; }}
#connbar {{ background: {c['panel']}; border-bottom: 1px solid {c['border']}; }}

QLabel#h1 {{ font-size: 18px; font-weight: 700; color: {c['text']}; }}
QLabel#h2 {{ font-size: 14px; font-weight: 600; color: {c['accent2']}; }}
QLabel#muted {{ color: {c['muted']}; }}
QLabel#chip {{ background: {c['card2']}; color: {c['muted']}; border-radius: 10px; padding: 2px 10px; }}

QFrame#card {{ background: {c['card']}; border: 1px solid {c['border']}; border-radius: 12px; }}
QFrame#mono {{ background: #070A0E; border: 1px solid {c['border']}; border-radius: 8px; }}

QLineEdit, QComboBox, QSpinBox {{ background: {c['card2']}; border: 1px solid {c['border']};
    border-radius: 8px; padding: 7px 10px; color: {c['text']}; selection-background-color: {c['accent']}; }}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{ border: 1px solid {c['accent']}; }}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{ background: {c['card2']}; border: 1px solid {c['border']};
    selection-background-color: {c['accent_dim']}; outline: none; }}

QPushButton#primary {{ background: {c['accent']}; color: #0B0F14; border: none; border-radius: 9px;
    padding: 9px 18px; font-weight: 700; }}
QPushButton#primary:hover {{ background: {c['accent_hi']}; }}
QPushButton#primary:disabled {{ background: {c['accent_dim']}; color: {c['muted']}; }}
QPushButton#ghost {{ background: {c['card2']}; color: {c['text']}; border: 1px solid {c['border']};
    border-radius: 9px; padding: 8px 14px; }}
QPushButton#ghost:hover {{ border: 1px solid {c['accent']}; color: {c['accent_hi']}; }}
QPushButton#info {{ background: {c['accent2']}; color: white; border: none; border-radius: 9px; padding: 8px 14px; font-weight: 600; }}
QPushButton#info:hover {{ background: #2b7cf0; }}
QPushButton#mini {{ background: {c['card2']}; color: {c['muted']}; border: 1px solid {c['border']}; border-radius: 6px; padding: 4px 8px; }}
QPushButton#mini:hover {{ color: {c['accent_hi']}; border-color: {c['accent']}; }}

QCheckBox {{ color: {c['text']}; spacing: 8px; }}
QCheckBox::indicator {{ width: 17px; height: 17px; border-radius: 5px; border: 1px solid {c['border']}; background: {c['card2']}; }}
QCheckBox::indicator:checked {{ background: {c['accent']}; border: 1px solid {c['accent']}; }}

QTextEdit, QPlainTextEdit {{ background: #070A0E; border: 1px solid {c['border']}; border-radius: 8px;
    color: #A5D6A7; font-family: "Cascadia Code","Consolas",monospace; font-size: 12px; }}
QScrollArea {{ background: transparent; border: none; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {c['border']}; border-radius: 5px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {c['muted']}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
#toast {{ background: {c['card2']}; border: 1px solid {c['accent']}; border-radius: 10px; color: {c['text']}; padding: 10px 16px; }}
#toasterr {{ background: {c['card2']}; border: 1px solid {c['error']}; border-radius: 10px; color: {c['text']}; padding: 10px 16px; }}
#status_ok {{ color: {c['accent_hi']}; font-weight: 600; }}
#status_off {{ color: {c['muted']}; }}
"""
