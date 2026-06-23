"""Tema visual e estilos Tkinter compartilhados pela interface."""

from tkinter import ttk


COLORS = {
    "bg": "#090d1f",
    "panel": "#101827",
    "panel_alt": "#172033",
    "panel_soft": "#263653",
    "line": "#4f6a9a",
    "text": "#eef6ff",
    "muted": "#b4c3d8",
    "accent": "#22d3ee",
    "accent_alt": "#f472b6",
    "gold": "#facc15",
    "danger": "#fb7185",
}


def configure_theme(root):
    style = ttk.Style(root)
    style.theme_use("clam")
    root.configure(background=COLORS["bg"])

    style.configure("TFrame", background=COLORS["bg"])
    style.configure("Panel.TFrame", background=COLORS["panel"])
    style.configure("Soft.TFrame", background=COLORS["panel_alt"])
    style.configure("Header.TLabel", background=COLORS["panel"], foreground=COLORS["text"], font=("Segoe Print", 18, "bold"))
    style.configure("Title.TLabel", background=COLORS["panel"], foreground=COLORS["text"], font=("Trebuchet MS", 13, "bold"))
    style.configure("Subheader.TLabel", background=COLORS["panel"], foreground=COLORS["muted"], font=("Segoe UI", 10))
    style.configure("Muted.TLabel", background=COLORS["panel"], foreground=COLORS["muted"], font=("Segoe UI", 9))
    style.configure("Body.TLabel", background=COLORS["panel"], foreground=COLORS["text"], font=("Segoe UI", 10))
    style.configure(
        "Badge.TLabel",
        background=COLORS["panel_soft"],
        foreground=COLORS["text"],
        font=("Segoe UI", 9, "bold"),
        padding=(10, 5),
    )

    style.configure(
        "TEntry",
        fieldbackground="#111827",
        foreground=COLORS["text"],
        bordercolor=COLORS["line"],
        lightcolor=COLORS["line"],
        darkcolor=COLORS["line"],
        insertcolor=COLORS["text"],
        padding=8,
    )
    style.configure("TSpinbox", fieldbackground="#111827", foreground=COLORS["text"], bordercolor=COLORS["line"], arrowsize=14)

    style.configure(
        "TButton",
        background=COLORS["panel_soft"],
        foreground=COLORS["text"],
        bordercolor=COLORS["line"],
        focusthickness=0,
        font=("Trebuchet MS", 10, "bold"),
        padding=(12, 8),
    )
    style.map("TButton", background=[("active", "#2f4164"), ("pressed", "#1f2a44")], foreground=[("disabled", COLORS["muted"])])
    style.configure(
        "Accent.TButton",
        background=COLORS["accent"],
        foreground="#082f38",
        bordercolor=COLORS["accent"],
        font=("Trebuchet MS", 10, "bold"),
        padding=(14, 8),
    )
    style.map("Accent.TButton", background=[("active", "#67e8f9"), ("pressed", "#0891b2")], foreground=[("active", "#082f38")])
    style.configure("Danger.TButton", background="#3b1f2a", foreground="#fecdd3", bordercolor="#713f52", font=("Trebuchet MS", 10, "bold"), padding=(12, 8))
    style.map("Danger.TButton", background=[("active", "#5c2738"), ("pressed", "#471f2e")])

    style.configure(
        "Treeview",
        background="#111827",
        fieldbackground="#111827",
        foreground=COLORS["text"],
        bordercolor=COLORS["line"],
        rowheight=31,
        font=("Segoe UI", 10),
    )
    style.configure(
        "Treeview.Heading",
        background=COLORS["panel_soft"],
        foreground=COLORS["text"],
        bordercolor=COLORS["line"],
        relief="flat",
        font=("Segoe UI", 9, "bold"),
    )
    style.map("Treeview", background=[("selected", "#155e75")], foreground=[("selected", "#ecfeff")])

    style.configure("TNotebook", background=COLORS["panel"], borderwidth=0)
    style.configure("TNotebook.Tab", background=COLORS["panel_soft"], foreground=COLORS["muted"], padding=(14, 8), font=("Segoe UI", 9, "bold"))
    style.map("TNotebook.Tab", background=[("selected", "#111827"), ("active", "#2b3b59")], foreground=[("selected", COLORS["text"]), ("active", COLORS["text"])])
    style.configure("TPanedwindow", background=COLORS["bg"])
