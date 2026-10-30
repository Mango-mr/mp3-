"""MP3 批量工坊 —— 启动入口。"""
from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

from tagstudio.runtime import bundle_dir

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def _run_selftest() -> int:
    """无界面自检：把诊断结果写到程序目录的 selftest.log。"""
    from tagstudio import selftest

    try:
        log_path = selftest.run()
        text = log_path.read_text(encoding="utf-8")
    except Exception:  # noqa: BLE001
        print(traceback.format_exc())
        return 1
    try:
        sys.stdout.write(text + "\n")
        sys.stdout.flush()
    except Exception:  # noqa: BLE001
        pass
    if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        return 0
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox

        app = QApplication(sys.argv)
        box = QMessageBox()
        box.setWindowTitle("自检结果")
        box.setIcon(QMessageBox.Information if "全部通过" in text else QMessageBox.Warning)
        box.setText("自检完成，详情已保存到：\n" + str(log_path))
        box.setDetailedText(text)
        box.exec()
        del app
    except Exception:  # noqa: BLE001
        pass
    return 0


def _set_windows_app_id() -> None:
    if os.name != "nt":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("MP3TagStudio.1")
    except Exception:  # noqa: BLE001
        pass


def main() -> int:
    _set_windows_app_id()

    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont, QIcon
    from PySide6.QtWidgets import QApplication, QMessageBox

    from tagstudio import __app_name__
    from tagstudio.ui.main_window import MainWindow
    from tagstudio.ui.qss import stylesheet

    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    except Exception:  # noqa: BLE001
        pass

    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setApplicationDisplayName(__app_name__)
    app.setOrganizationName("MP3TagStudio")
    app.setStyle("Fusion")
    app.setStyleSheet(stylesheet())

    font = QFont("Microsoft YaHei UI")
    font.setPointSizeF(9.6)
    app.setFont(font)

    icon_path = bundle_dir() / "assets" / "icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    def _excepthook(exc_type, exc_value, exc_tb):
        text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        try:
            box = QMessageBox()
            box.setWindowTitle("程序出现异常")
            box.setIcon(QMessageBox.Critical)
            box.setText("发生了未预期的错误，可把下面的信息反馈给开发者：")
            box.setDetailedText(text)
            box.exec()
        except Exception:  # noqa: BLE001
            sys.stderr.write(text)

    sys.excepthook = _excepthook

    window = MainWindow()
    # 支持「把文件/文件夹拖到 exe 图标上」直接导入
    try:
        from tagstudio import tags as _tags

        args = [Path(a) for a in sys.argv[1:] if Path(a).exists()]
        initial: list[Path] = []
        for p in args:
            if p.is_dir():
                initial.extend(sorted(x for x in p.rglob("*")
                                      if x.is_file() and x.suffix.lower() in _tags.AUDIO_EXTS))
            else:
                initial.append(p)
        if initial:
            window._add_paths(initial)
    except Exception:  # noqa: BLE001
        pass
    window.show()
    return app.exec()


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_run_selftest())
    sys.exit(main())
