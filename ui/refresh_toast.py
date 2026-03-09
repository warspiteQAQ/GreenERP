from PySide6.QtCore import QPoint, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtWidgets import QLabel, QWidget


def show_refresh_success(host: QWidget, text: str = "刷新成功"):
    if host is None:
        return

    label = getattr(host, "_refresh_success_label", None)
    if label is None:
        label = QLabel(host)
        label.setObjectName("refreshSuccessToast")
        label.setStyleSheet(
            "QLabel#refreshSuccessToast {"
            "color: #2e7d32;"
            "background: rgba(232, 245, 233, 230);"
            "border: 1px solid #a5d6a7;"
            "border-radius: 10px;"
            "padding: 4px 10px;"
            "font-weight: 600;"
            "}"
        )
        setattr(host, "_refresh_success_label", label)

    # Stop previous animation/timer if repeated quickly.
    old_anim = getattr(host, "_refresh_success_anim", None)
    if old_anim is not None:
        old_anim.stop()
    old_timer = getattr(host, "_refresh_success_timer", None)
    if old_timer is not None:
        old_timer.stop()

    label.setText(text)
    label.adjustSize()
    margin = 14
    y = 10
    end_x = max(margin, host.width() - label.width() - margin)
    start_x = host.width() + label.width()
    label.move(start_x, y)
    label.show()
    label.raise_()

    anim = QPropertyAnimation(label, b"pos", host)
    anim.setDuration(420)
    anim.setStartValue(QPoint(start_x, y))
    anim.setEndValue(QPoint(end_x, y))
    anim.setEasingCurve(QEasingCurve.OutCubic)
    anim.start()
    setattr(host, "_refresh_success_anim", anim)

    timer = QTimer(host)
    timer.setSingleShot(True)

    def _hide():
        label.hide()

    timer.timeout.connect(_hide)
    timer.start(1300)
    setattr(host, "_refresh_success_timer", timer)
