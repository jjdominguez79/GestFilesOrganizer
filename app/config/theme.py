from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    app_title: str = "GestFiles Organizer"
    brand_name: str = "Gest2A3Eco"
    brand_tagline: str = "Gestión documental de despacho"
    window_min_width: int = 1360
    window_min_height: int = 820
    colors: dict[str, str] = None
    fonts: dict[str, int] = None

    def __post_init__(self) -> None:
        if self.colors is None:
            object.__setattr__(
                self,
                "colors",
                {
                    "bg": "#EEF1F3",
                    "surface": "#FFFFFF",
                    "surface_alt": "#F4F7F8",
                    "surface_dark": "#2D343B",
                    "primary": "#5AA332",
                    "primary_dark": "#3C7C1B",
                    "accent": "#1F7A8C",
                    "text": "#1F2B33",
                    "muted": "#64737D",
                    "border": "#CCD5DB",
                    "brand_soft": "#DFF0D3",
                    "pending": "#B58A00",
                    "processing": "#1F7A8C",
                    "processed": "#0D7C66",
                    "error": "#A33A2B",
                },
            )
        if self.fonts is None:
            object.__setattr__(
                self,
                "fonts",
                {"title": 22, "subtitle": 11, "body": 10, "small": 9},
            )


THEME = Theme()


def build_stylesheet(theme: Theme = THEME) -> str:
    c = theme.colors
    return f"""
    QWidget {{
        background: {c['bg']};
        color: {c['text']};
        font-family: 'Segoe UI', 'Calibri', sans-serif;
        font-size: 10pt;
    }}
    QMainWindow {{
        background: {c['bg']};
    }}
    QFrame#Sidebar,
    QFrame#TopCard,
    QFrame#PanelCard,
    QFrame#SummaryCard {{
        background: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 14px;
    }}
    QFrame#BrandBlock {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {c['surface_dark']}, stop:1 {c['primary']});
        border-radius: 18px;
        color: white;
    }}
    QFrame#BrandInfoCard {{
        background: rgba(255, 255, 255, 0.12);
        border: 1px solid rgba(255, 255, 255, 0.16);
        border-radius: 12px;
    }}
    QLabel#BrandLogo {{
        background: white;
        border: none;
        border-radius: 10px;
        color: {c['primary_dark']};
        font-size: 21pt;
        font-weight: 700;
        padding: 8px 12px;
    }}
    QLabel#BrandPill {{
        background: {c['brand_soft']};
        color: {c['primary_dark']};
        border-radius: 10px;
        padding: 4px 8px;
        font-size: 9pt;
        font-weight: 700;
    }}
    QLabel#Headline {{
        font-size: 18pt;
        font-weight: 700;
        color: {c['text']};
    }}
    QLabel#SectionTitle {{
        font-size: 11pt;
        font-weight: 600;
        color: {c['text']};
    }}
    QLabel#MutedLabel {{
        color: {c['muted']};
    }}
    QLabel#BrandOwner {{
        color: rgba(255,255,255,0.82);
        font-size: 9pt;
        font-weight: 600;
    }}
    QLabel#BrandProduct {{
        color: white;
        font-size: 19pt;
        font-weight: 700;
    }}
    QLabel#BrandTagline {{
        color: rgba(255,255,255,0.88);
        font-size: 10pt;
    }}
    QLabel#InfoTitle {{
        color: white;
        font-size: 8.5pt;
        font-weight: 700;
        text-transform: uppercase;
    }}
    QLabel#InfoValue {{
        color: white;
        font-size: 10pt;
    }}
    QPushButton {{
        background: {c['surface_alt']};
        border: 1px solid {c['border']};
        border-radius: 10px;
        padding: 10px 14px;
        font-weight: 600;
    }}
    QPushButton:hover {{
        border-color: {c['primary']};
    }}
    QPushButton:disabled {{
        color: #8D9AA4;
        background: #EFF2F5;
        border-color: #D8E0E6;
    }}
    QPushButton#PrimaryButton {{
        background: {c['primary']};
        color: white;
        border-color: {c['primary_dark']};
    }}
    QPushButton#PrimaryButton:hover {{
        background: {c['primary_dark']};
    }}
    QPushButton#AccentButton {{
        background: {c['accent']};
        color: white;
        border-color: {c['accent']};
    }}
    QLineEdit, QTextEdit, QPlainTextEdit, QTreeWidget, QTableWidget, QComboBox {{
        background: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 10px;
        padding: 8px;
    }}
    QTreeWidget {{
        padding: 6px;
    }}
    QHeaderView::section {{
        background: {c['surface_alt']};
        color: {c['text']};
        border: none;
        border-bottom: 1px solid {c['border']};
        padding: 10px 8px;
        font-weight: 600;
    }}
    QProgressBar {{
        background: {c['surface_alt']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        text-align: center;
        min-height: 18px;
    }}
    QProgressBar::chunk {{
        background-color: {c['primary']};
        border-radius: 6px;
    }}
    QCheckBox {{
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
    }}
    QCheckBox::indicator:unchecked {{
        border: 1px solid {c['border']};
        border-radius: 5px;
        background: {c['surface']};
    }}
    QCheckBox::indicator:checked {{
        border: 1px solid {c['primary']};
        border-radius: 5px;
        background: {c['primary']};
    }}
    """
