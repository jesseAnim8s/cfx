"""
Creates a generic UI template.
"""


# General Imports
import logging
try:
    from PySide2 import QtCore, QtGui, QtWidgets
except ImportError:
    from PySide import QtCore, QtGui, QtWidgets
# Package imports
from cfx import ui_utils as ui_utils
# Reloads (to be taken out upon release)


__author__ = 'Jesse Carlson'
__email__ = 'seven6ty@hotmail.com'
__version__ = 'beta'
# Variables
logger = logging.getLogger(__name__)
company = 'Jesse'
win_title = 'Template UI'
win_class = 'TemplateUI'
min_width = 325


def show_ui():
    path = __name__
    ui_utils.show_ui(path, win_class)


class TemplateUI(QtWidgets.QDialog):

    def __init__(self, parent=ui_utils.get_maya_win()):
        """Creates the UI."""
        super(TemplateUI, self).__init__(parent=parent)

        # QDialog settings
        self.setWindowTitle(win_title)
        self.setWindowFlags(
            self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint
        )
        self.setMinimumWidth(min_width)

        # Widgets
        text = QtWidgets.QLabel('Here is some text')
        btn = QtWidgets.QPushButton('Test')
        widgets = (text, btn)

        # Layouts
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(2)
        setContentsMargins(2, 2, 2, 2)
        for widget in widgets:
            layout.addWidget(widget)

        # Settings
        try:
            self.settings = QtCore.QSettings(company, win_class)
            if self.settings.contains('geometry'):
                self.restoreGeometry(self.settings.value('geometry', ''))
        except Exception as e:
            logger.warning('Applying settings failed.')
            user_input = QtWidgets.QMessageBox.question(
                self,
                'Clear Settings?',
                'Could not apply settings, would you like to clear them?',
                QtWidgets.QMessageBox.Yes,
                QtWidgets.QMessageBox.No
            )
            if user_input == QtWidgets.QMessageBox.Yes:
                self.settings = QtCore.QSettings(company, win_class)
                self.settings.clear()

    def closeEvent(self, event):
        """Saves UI settings, before triggering the default closeEvent."""
        self.settings.setValue('geometry', self.saveGeometry())
        event.accept()
