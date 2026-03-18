from __future__ import annotations

from app.config.app_settings import SETTINGS
from app.ui.main_window import MainWindow, build_application


def main() -> int:
    application = build_application(SETTINGS)
    window = MainWindow(SETTINGS)
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())
