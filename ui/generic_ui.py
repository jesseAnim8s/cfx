"""Generic PyQt widgets to use in creating UIs."""


# General Imports
from os.path import exists as path_exists
from collections import Mapping
from logging import getLogger
# Facility Imports
from PySide2 import QtCore, QtWidgets
# Package Imports
from cfx.beta.ui import css
from cfx.beta.maya import commands as mc
from cfx.beta.py_utils import get_home_dir
# Reloads (Remove before release)


__author__ = 'Jesse Carlson'
__email__ = 'seven6ty@hotmail.com'
__version__ = 'beta'
# Variables
logger = getLogger(__name__)
nucleus_rgb = (52, 123, 91)
cloth_rgb = (43, 114, 144)
hair_rgb = (157, 146, 83)
rigid_rgb = (72, 88, 83)


def set_layout(layout):
    """Applies default spacing & margins for a layout.

    Args:
        layout (QtWidgets.QLayout): A QLayout object
            to apply default values to.
    """
    layout.setSpacing(6)
    layout.setContentsMargins(2, 2, 2, 2)


class SpinBox(QtWidgets.QDoubleSpinBox):
    """Custom QDoubleSpinBox w/ middle mouse scroll disabled.""" s

    def wheelEvent(self, event):
        """Ignores scroll wheel events.

        Args:
            event (QtCore.QEvent): Default event passed to this function.
        """
        event.ignore()


class RightClickSpinBox(SpinBox):
    """A QDoubleSpinBox, with custom right click pop-up menu."""

    def __init__(self, parent=None):
        super(RightClickSpinBox, self).__init__(parent=parent)
        self.menu = QtWidgets.QMenu()
        self.set_to_frame_range = self.menu.addAction('Set to frame range end')
        self.set_to_time_slider = self.menu.addAction('Set to time slider end')
        line_edit = QtWidgets.QLineEdit()
        line_edit.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        line_edit.customContextMenuRequested.connect(self.mousePressEvent)

    def mousePressEvent(self, event):
        """Adds right click functionality.

        Args:
            event (QtCore.QEvent): Default event passed to this function.
        """
        if event.button() == QtCore.Qt.RightButton:
            frame_num = None
            selection = self.menu.exec_(self.mapToGlobal(event.pos()))
            if selection == self.set_to_frame_range:
                frame_num = mc.get_timeslider_end_frame()
            elif selection == self.set_to_time_slider:
                frame_num = mc.get_end_frame()
            if frame_num:
                self.setValue(float(frame_num))
        event.accept()


class Tree(QtWidgets.QTreeWidget):
    """A simple QTreeWidget that allows drag & drop operations."""

    def __init__(self, header=(), parent=None):
        super(Tree, self).__init__(parent=parent)

        # Settings
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(self.InternalMove)
        self.setAlternatingRowColors(True)
        self.setStyleSheet(css.tree_view_styelsheet)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        self._header = None
        # Header
        if header:
            self._header = self.header()
            self.setHeaderLabels(header)
            self.setUniformRowHeights(False)


class SingleSelectionUI(QtWidgets.QWidget):
    """A custom UI for getting ong single selected node."""

    def __init__(self, label='', dictionary=None, entry='', parent=None):
        """A widget for getting a single selected Maya node.

        Args:
            label (str): Text to display.
            dictionary (dict): Dictionary to populate with (optional).
            entry (str): The name of the dictionary entry to use.
            parent (QtWidgets.QWidget): Widget to parent this object to.
        """
        super(SingleSelectionUI, self).__init__(parent=parent)

        # Variables
        self.dict = dictionary
        self.entry = entry

        # Widgets
        if label:
            self.text = QtWidgets.QLabel(label)
        else:
            self.text = None
        self.widget = QtWidgets.QLineEdit()
        self.btn = QtWidgets.QPushButton()
        self.btn.setToolTip('Get the current selection')
        self.btn.setStyleSheet(css.replace_icon_stylesheet)
        self.btn.clicked.connect(self.add)
        if label:
            self.widgets = (self.text, self.widget, self.btn)
        else:
            self.widgets = (self.widget, self.btn)

        # Layouts
        self.layout = QtWidgets.QHBoxLayout(self)
        set_layout(self.layout)
        for widget in self.widgets:
            self.layout.addWidget(widget)

        # Populate node
        if self.dict and self.entry:
            self.add(self.dict[self.entry])

    def add(self, node=''):
        """Adds the current selection to the widget.

        Args:
            node (str): Node to operate on.
        """
        if node:
            self.widget.setText(node)
        else:
            selection = mc.get_selection()
            if selection:
                self.widget.setText(selection[0])
        # Update dictionary entry
        if self.entry:
            self.dict[self.entry] = self.get_input()

    def get_input(self):
        """Gets the currently input node.

        Returns:
            The input text.
        """
        return self.widget.text()


class SelectionListWidget(QtWidgets.QWidget):
    """A QListWidget for getting multiple selected items from Maya."""

    def __init__(self, label='', list_dict=None, parent=None):
        """Initializes the widget.

        Args:
            label (str): Text to display.
            list_dict (dict/OrderedDict): Dictionary to populate from &
                save to.
            parent (QtWidgets.QWidget): The widget to parent this UI to.
        """
        super(SelectionListWidget, self).__init__(parent=parent)

        # Arguments
        self.list_dict = list_dict
        # Variables
        self.use_dict = False
        if isinstance(list_dict, Mapping):
            self.use_dict = True

        # Settings
        self.setMinimumHeight(40)
        self.setMaximumHeight(60)

        # Widgets
        if label:
            text = QtWidgets.QLabel(label)
        self.list = QtWidgets.QListWidget()
        self.list.setSelectionMode(
            QtWidgets.QAbstractItemView.ExtendedSelection
        )
        self.replace = QtWidgets.QPushButton()
        self.replace.setStyleSheet(css.replace_icon_stylesheet)
        self.add = QtWidgets.QPushButton()
        self.add.setStyleSheet(css.add_icon_stylesheet)
        self.remove = QtWidgets.QPushButton()
        self.remove.setStyleSheet(css.remove_icon_stylesheet)
        buttons = (self.replace, self.add, self.remove)
        self.lists = (self.list, self.replace, self.add,
                      self.remove)
        # Widget connections
        self.replace.clicked.connect(self.replace_selection)
        self.add.clicked.connect(self.add_selected)
        self.remove.clicked.connect(self.remove_selected)

        # Populate list with dictionary items
        if self.use_dict:
            # TODO: List comprehension?...
            for item in self.list_dict.keys():
                self.list.addItem(str(item))

        # Layouts
        self.layout_text = QtWidgets.QVBoxLayout()
        if label:
            self.layout_text.addWidget(text)
        self.layout_text.addStretch()
        self.layout_buttons = QtWidgets.QVBoxLayout()
        for button in buttons:
            self.layout_buttons.addWidget(button)
        self.layout_buttons.addStretch()
        # Main layout
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.addLayout(self.layout_text)
        self.layout.addWidget(self.list)
        self.layout.addLayout(self.layout_buttons)
        set_layout(self.layout)

    def replace_nodes(self, nodes):
        """Replaces the current list of nodes with a given list.

        Args:
            nodes (list/tuple): Collection of nodes to operate on.
        """
        assert isinstance(nodes, (list, tuple)), 'Nodes must be list/tuple'
        if self.use_dict:
            self.list_dict.clear()
        self.list.clear()
        for node in nodes:
            self.list.addItem(node)
            if self.use_dict:
                self.list_dict[node] = None

    def replace_selection(self):
        """Replace current items with selection."""
        if self.use_dict:
            self.list_dict.clear()
        self.list.clear()
        self.add_selected()

    def add_selected(self):
        """Adds selected nodes."""
        selection = mc.get_selection()
        for selected in selection:
            self.list.addItem(str(selected))
            if self.use_dict:
                self.list_dict[selected] = None

    def remove_selected(self):
        """Removes selected items."""
        for item in self.list.selectedItems():
            self.list.takeItem(self.list.row(item))
            if self.use_dict:
                if item.text() in self.list_dict.keys():
                    del self.list_dict[item.text()]

    def get_items(self):
        """Gets a list of items in the list.

        Returns:
            All input text entries.
        """
        items = []
        for x in range(self.list.count()):
            items.append(self.list.item(x).text())
        return items


class SelectionTreeWidget(Tree):
    """A QTreeWidget for getting multiple selected items from Maya."""

    def __init__(self, parent=None):
        super(SelectionTreeWidget, self).__init__(parent=parent)
        pass

    def replace_nodes(self):
        pass

    def add_selection(self):
        pass

    def remove_selected(self):
        pass

    def get_items(self):
        pass


class FilePicker(QtWidgets.QWidget):
    """Creates a UI field for specifying & browsing  files."""
    valid_modes = ('file', 'new_file', 'dir')

    def __init__(self, label='File:', mode='file',
                 browser_label='', file_filter='', btn_height=23,
                 file_path='', parent=None):
        """Initializes the UI.

        Args:
            label (str): Text to display next to the input field.
            mode (str): Either "file", "new_file", or "dir", for what you want to do.
            browser_label (str): Displays the mode the browser is operating in.
            file_filter (str): File names must have this string to be displayed.
            btn_height (int): Height of the  browse button.
            file_path (str): Default file path to start at.
            parent (QtWidgets.QWidget): QWidget to parent the UI under.
        """
        super(FilePicker, self).__init__(parent=parent)

        # Variables
        self.default_dir = get_home_dir()
        self.label = label
        self.browser_label = browser_label
        self.last_dir = None
        self.filter = file_filter
        lower_mode = mode.lower().strip()
        if isinstance(mode, basestring) and lower_mode in self.valid_modes:
            self.mode = lower_mode
        else:
            logger.error('Please specify a valid mode:')
            for mode in self.valid_modes:
                logger.info('    ' + mode)
        min_label_width = None

        # Widgets
        self.text = QtWidgets.QLabel(label)
        if min_label_width:
            self.text.setMinimumWidth(min_label_width)
        self.field = QtWidgets.QLineEdit()
        self.field.textChanged.connect(self.text_validate)
        if file_path:
            self.set_text(file_path)
        self.btn = QtWidgets.QPushButton('Browse')
        self.btn.setStyleSheet(css.orange_button_stylesheet)
        self.btn.clicked.connect(self.browser)
        if btn_height:
            self.field.setMinimumHeight(btn_height)
            self.field.setMaximumHeight(btn_height)
            self.btn.setMinimumHeight(btn_height)
            self.btn.setMaximumHeight(btn_height)
        if self.label:
            self.widgets = (self.text, self.field, self.btn)
        else:
            self.widgets = (self.field, self.btn)

        # Layouts
        self.layout = QtWidgets.QHBoxLayout(self)
        set_layout(self.layout)
        for item in self.widgets:
            self.layout.addWidget(item)

        # Validate text
        self.text_validate()

    def set_default_dir(self, dir=''):
        """Sets the default directory to use.

        Args:
            dir (str): Directory to default to.
        """
        if dir and path_exists(dir):
            self.default_dir = dir

    def browser(self):
        """Creates a pop-up browser for picking files/directories."""

        # TODO: Clean up the below - set variables, call dialog once

        # New files
        if self.mode == self.valid_modes[0]:
            if not self.browser_label:
                self.browser_label = 'File'
            user_input = cmds.fileDialog2(
                buttonBoxOrientation=2,
                caption=self.browser_label,
                fileFilter=self.filter,
                fileMode=1,
                hideNameEdit=False,
                startingDirectory=self.default_dir
            )
            if user_input:
                self.field.setText(user_input[0])
        elif self.mode == self.valid_modes[1]:
            if not self.browser_label:
                self.browser_label = 'File'
            user_input = cmds.fileDialog2(
                buttonBoxOrientation=2,
                caption=self.browser_label,
                fileFilter=self.filter,
                fileMode=0,
                hideNameEdit=False,
                startingDirectory=self.default_dir
            )
            if user_input:
                self.field.setText(user_input[0])
        # Directories
        elif self.mode == self.valid_modes[2]:
            if not self.browser_label:
                self.browser_label = 'Directory'
            user_input = cmds.fileDialog2(
                buttonBoxOrientation=2,
                caption=self.browser_label,
                fileFilter=self.filter,
                fileMode=3,
                hideNameEdit=False,
                startingDirectory=self.default_dir
            )
            if user_input:
                self.field.setText(user_input[0])
        # Check for the existence of the file
        self.text_validate()

    def text_validate(self):
        """Validates text input as a file."""
        if path_exists(self.get_text()):
            self.field.setStyleSheet('')
        else:
            self.field.setStyleSheet('border: 1px solid red')

    def set_text(self, text=''):
        """Sets the field text.

        Args:
            text (str): The string to set the field to.
        """
        try:
            self.field.setText(text)
        except TypeError:
            logger.info(type(text))
        self.text_validate()

    def get_text(self):
        """Returns the currently entered text.

        Returns:
            The text input in the field.
        """
        return self.field.text()

    def disable(self):
        """Disables the UI elements."""
        for widget in self.widgets:
            widget.setEnabled(False)

    def enable(self):
        """Enables the UI elements."""
        for widget in self.widgets:
            widget.setEnabled(True)

    def execute(self):
        """Executes the ultimate function."""
        pass
