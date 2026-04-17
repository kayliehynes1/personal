# theme.py — want to allow the user to toggle between 2 colour themes (dark/light), text/fonts are fixed

THEMES: dict[str, dict[str, str]] = {
    "dark": {
        "bg":           "#1a1a2e",
        "bg_secondary": "#16213e",
        "accent":       "#e94560",
        "accent2":      "#f5a623",
        "text":         "#eaeaea",
        "text_dim":     "#8888aa",
        "entry_bg":     "#0f3460",
        "entry_fg":     "#eaeaea",
        "btn_bg":       "#e94560",
        "btn_fg":       "#eaeaea",
    },
    "light": {
        "bg":           "#fdf6e3",
        "bg_secondary": "#eee8d5",
        "accent":       "#cb4b16",
        "accent2":      "#b58900",
        "text":         "#282828",
        "text_dim":     "#888888",
        "entry_bg":     "#ffffff",
        "entry_fg":     "#282828",
        "btn_bg":       "#cb4b16",
        "btn_fg":       "#fdf6e3",
    },
}

FONT_TITLE  = ("Courier", 28, "bold")
FONT_HEADER = ("Courier", 16, "bold")
FONT_BODY   = ("Courier", 12)
FONT_SMALL  = ("Courier", 10)
FONT_CELL   = ("Courier", 18, "bold")
FONT_BTN    = ("Courier", 11, "bold")