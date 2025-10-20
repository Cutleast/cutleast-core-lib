"""
Copyright (c) Cutleast
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap, QTransform


def rotated_icon(icon: QIcon, angle: float, size: int = 64) -> QIcon:
    """
    Rotates a QIcon by a given angle and returns a new QIcon.

    Args:
        icon (QIcon): The original icon to rotate.
        angle (float): Rotation angle in degrees (clockwise).
        size (int, optional): Size of the rotated icon. Defaults to 64.

    Returns:
        QIcon: A new icon rotated by the given angle.
    """

    pixmap: QPixmap = icon.pixmap(size, size)

    transform = QTransform()
    transform.rotate(angle)

    rotated_pixmap = pixmap.transformed(
        transform, mode=Qt.TransformationMode.SmoothTransformation
    )

    return QIcon(rotated_pixmap)
