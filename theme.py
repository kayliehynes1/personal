# theme.py — want to allow the user to toggle between 2 colour themes (dark/light), text/fonts are fixed

THEMES: dict[str, dict[str, str]] = {
    "dark": {
        "bg":           "#1a1a2e",   # main background
        "bg_secondary": "#16213e",   # panels, top bar
        "accent":       "#e94560",   # primary accent - buttons, titles, thick grid border
        "accent2":      "#f5a623",   # secondary accent - timer, user-entered numbers
        "text":         "#eaeaea",   # primary text
        "text_dim":     "#4a4a6a",   # secondary text, thin grid lines
        "entry_bg":     "#0f3460",   # input and cell background
        "entry_fg":     "#eaeaea",   # input text
        "btn_bg":       "#e94560",   # button background
        "btn_fg":       "#eaeaea",   # button text
        "cell_fixed":   "#e94560",   # pre-filled clue numbers
        "cell_user":    "#f5a623",   # user-entered numbers
        "cell_hint":    "#00d4aa",   # hint-filled numbers
        "cell_error":   "#ff2244",   # incorrect number highlight 
    },
    "light": {
        "bg":           "#fdf6e3",
        "bg_secondary": "#eee8d5",
        "accent":       "#cb4b16",
        "accent2":      "#b58900",
        "text":         "#282828",
        "text_dim":     "#bbbbaa",
        "entry_bg":     "#ffffff",  
        "entry_fg":     "#282828",
        "btn_bg":       "#cb4b16",
        "btn_fg":       "#fdf6e3",
        "cell_fixed":   "#cb4b16",
        "cell_user":    "#2a6496",
        "cell_hint":    "#2aa198",
        "cell_error":   "#dc322f",
    },
}
 
FONT_TITLE  = ("Courier", 28, "bold")
FONT_HEADER = ("Courier", 16, "bold")
FONT_BODY   = ("Courier", 12)
FONT_SMALL  = ("Courier", 10)
FONT_CELL   = ("Courier", 18, "bold")
FONT_BTN    = ("Courier", 11, "bold")