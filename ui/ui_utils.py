"""General UI utilities."""


# Imports
from logging import getLogger
from PySide2 import QtCore, QtGui, QtWidgets
try:
    import shiboken2 as shiboken
except ImportError:
    import shiboken
from maya import cmds
from maya import OpenMayaUI as omui


__author__ = 'Jesse Carlson'
__email__ = 'seven6ty@hotmail.com'
__version__ = 'beta'
# Variables
logger = getLogger(__name__)
rgb_colors = {
    'grey': (80, 80, 80),
    'default_grey': (68, 68, 68),
    'blue': (55, 70, 105),
    'green': (60, 80, 60),
    'purple': (88, 60, 88),
    'brown': (101, 72, 57),
    'red': (98, 35, 35)
}


def get_maya_win():
    """
    Gets a Qt pointer object to the Maya UI.

    Returns:
        A shiboken wrapper around the main Maya window.
    """
    maya_win_pointer = omui.MQtUtil.mainWindow()
    return shiboken.wrapInstance(long(maya_win_pointer), QtWidgets.QWidget)


def color_maya_ui(rgb_colors):
    """
    Colors the Maya UI interface a given RGB value.

    Args:
        rgb_colors (tuple/list): RGB values to color the Maya UI.
    """
    # Error checking
    assert isinstance(rgb_colors, (tuple, list)), 'Please give RGB values.'
    assert (len(rgb_colors) == 3), 'Must provide 3 RGB values.'
    # Arguments
    r, g, b = rgb_colors[0], rgb_colors[1], rgb_colors[2]
    # Get main Maya window
    maya_win = get_maya_win()
    # Convert RGB to QColor
    q_colors = QtGui.QColor(r, g, b)
    palette = maya_win.palette()
    # Assign color to Maya window
    palette.setColor(maya_win.backgroundRole(), q_colors)
    win_widgets = maya_win.findChildren(QtWidgets.QWidget)
    for child in win_widgets:
        child.setPalette(palette)
    # Convert colors
    total_color = r + g + b * 1.0
    ratio_r = r / total_color
    ratio_g = g / total_color
    ratio_b = b / total_color
    outliner = 1.2
    hypergraph = 0.5
    node = 0.6
    graph = 0.9
    desaturation_r = (r + total_color) / 4.0 / total_color
    desaturation_g = (g + total_color) / 4.0 / total_color
    desaturation_b = (b + total_color) / 4.0 / total_color
    names = ('outlinerInvisibleColor', 'hyperBackgroundColor',
             'nodeEditorBackground', 'graphEditorBackground')
    # Color windows
    for name in names:
        if name in names[0:2]:
            for multiplier in (outliner, hypergraph, node):
                cmds.displayRGBColor(
                    name,
                    ratio_r * multiplier,
                    ratio_g * multiplier,
                    ratio_b * multiplier
                )
        else:
            cmds.displayRGBColor(
                name,
                desaturation_r * graph,
                desaturation_g * graph,
                desaturation_b * graph
            )


def show_ui(path, class_name):
    """
    Singleton method to display only one UI.

    Args:
        path (str): Path to import.
        class_name (str): Class name to call.
    """
    for win in get_maya_win().children():
        if win.__class__.__name__ == class_name:
            win.hide()
            win.deleteLater()
    ui_cmd = 'import {0}\n{0}.{1}().show()'.format(path, class_name)
    exec ui_cmd
