from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    app_title: str = "GestFiles Organizer"
    brand_name: str = "Gestinem"
    brand_tagline: str = "Gestión documental de despacho"
    window_min_width: int = 1420
    window_min_height: int = 860
    colors: dict[str, str] = None
    fonts: dict[str, int] = None

    def __post_init__(self) -> None:
        if self.colors is None:
            object.__setattr__(
                self,
                "colors",
                {
                    "bg": "#EEF2F6",
                    "surface": "#FFFFFF",
                    "surface_alt": "#F5F8FB",
                    "surface_dark": "#0F2741",
                    "surface_deep": "#0A1A2E",
                    "primary": "#1F4D7A",
                    "primary_dark": "#163652",
                    "primary_soft": "#DDE8F2",
                    "accent": "#6E8EAA",
                    "text": "#1A2733",
                    "muted": "#667788",
                    "border": "#D4DEE7",
                    "pending": "#8C6A19",
                    "pending_soft": "#F3E9C8",
                    "selected": "#234E78",
                    "selected_soft": "#DDE8F2",
                    "processing": "#215F93",
                    "processing_soft": "#D6E7F6",
                    "processed": "#26634E",
                    "processed_soft": "#D9ECE4",
                    "error": "#A24034",
                    "error_soft": "#F4DBD7",
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
        font-family: 'Segoe UI', 'Bahnschrift', 'Calibri', sans-serif;
        font-size: 10pt;
    }}
    QMainWindow {{
        background: {c['bg']};
    }}
    QFrame#HeroCard {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 {c['surface_deep']}, stop:0.55 {c['surface_dark']}, stop:1 {c['primary']});
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 18px;
    }}
    QLabel#HeroLogo {{
        background: rgba(255,255,255,0.95);
        color: {c['surface_dark']};
        border-radius: 16px;
        font-size: 24pt;
        font-weight: 800;
    }}
    QLabel#HeroEyebrow {{
        color: rgba(255,255,255,0.74);
        font-size: 9.5pt;
        font-weight: 600;
        text-transform: uppercase;
    }}
    QLabel#HeroTitle {{
        color: white;
        font-size: 22pt;
        font-weight: 700;
    }}
    QLabel#HeroSubtitle {{
        color: rgba(255,255,255,0.86);
        font-size: 10.5pt;
    }}
    QLabel#HeroChip {{
        background: rgba(255,255,255,0.12);
        color: white;
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 12px;
        padding: 6px 10px;
        font-size: 9pt;
        font-weight: 600;
    }}
    QFrame#HeroSideCard {{
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 14px;
        min-width: 210px;
    }}
    QFrame#MetricCard,
    QFrame#InlineMetricCard,
    QFrame#PanelCard {{
        background: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 16px;
    }}
    QLabel#MetricTitle,
    QLabel#MiniMetricTitle,
    QLabel#FieldLabel {{
        color: {c['muted']};
        font-size: 8.8pt;
        font-weight: 600;
        text-transform: uppercase;
    }}
    QLabel#MetricValue {{
        color: {c['primary_dark']};
        font-size: 20pt;
        font-weight: 700;
    }}
    QLabel#MetricSubtitle {{
        color: {c['muted']};
        font-size: 9pt;
    }}
    QLabel#MiniMetricValue {{
        color: {c['text']};
        font-size: 12pt;
        font-weight: 700;
    }}
    QLabel#SectionTitle {{
        font-size: 11.5pt;
        font-weight: 700;
        color: {c['text']};
    }}
    QLabel#MutedLabel {{
        color: {c['muted']};
    }}
    QLabel#StatusBadgeNeutral,
    QLabel#StatusBadgeInfo,
    QLabel#StatusBadgeSuccess,
    QLabel#StatusBadgeError {{
        padding: 6px 10px;
        border-radius: 11px;
        font-size: 9pt;
        font-weight: 700;
    }}
    QLabel#StatusBadgeNeutral {{
        background: {c['surface_alt']};
        color: {c['muted']};
        border: 1px solid {c['border']};
    }}
    QLabel#StatusBadgeInfo {{
        background: {c['processing_soft']};
        color: {c['processing']};
        border: 1px solid {c['processing']};
    }}
    QLabel#StatusBadgeSuccess {{
        background: {c['processed_soft']};
        color: {c['processed']};
        border: 1px solid {c['processed']};
    }}
    QLabel#StatusBadgeError {{
        background: {c['error_soft']};
        color: {c['error']};
        border: 1px solid {c['error']};
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
        background: #F9FBFD;
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
        background: {c['surface_dark']};
        color: white;
        border-color: {c['surface_dark']};
    }}
    QPushButton#AccentButton:hover {{
        background: {c['primary_dark']};
    }}
    QLineEdit, QPlainTextEdit, QTreeWidget {{
        background: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 12px;
        padding: 8px;
    }}
    QLineEdit:focus, QPlainTextEdit:focus, QTreeWidget:focus {{
        border: 1px solid {c['primary']};
    }}
    QTreeWidget {{
        alternate-background-color: {c['surface_alt']};
        padding: 6px;
    }}
    QTreeWidget::item {{
        height: 34px;
    }}
    QTreeWidget::item:selected {{
        background: {c['primary_soft']};
        color: {c['text']};
    }}
    QHeaderView::section {{
        background: {c['surface_alt']};
        color: {c['text']};
        border: none;
        border-bottom: 1px solid {c['border']};
        padding: 10px 8px;
        font-weight: 700;
    }}
    QProgressBar {{
        background: {c['surface_alt']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        text-align: center;
        min-height: 20px;
    }}
    QProgressBar::chunk {{
        background-color: {c['primary']};
        border-radius: 6px;
    }}
    QCheckBox {{
        spacing: 8px;
        color: {c['text']};
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
    QSplitter::handle {{
        background: transparent;
        width: 8px;
    }}
    """
