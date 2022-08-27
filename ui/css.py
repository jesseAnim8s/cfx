"""
A container for CSS stylesheets for use in UIs.
"""


# General Imports
from os.path import dirname
# Package Imports
from cfx.py_utils import joinpath


__author__ = 'Jesse Carlson'
__email__ = 'seven6ty@hotmail.com'
__version__ = 'beta'
# Variables
package_dir = dirname(dirname(__file__))
icon_path = joinpath(package_dir, 'icons')
max_button_size = 20


# Stylesheet strings
generic_button_icon_stylesheet = '''
    QPushButton {{
        border-style: outset;
        border-width: 0px;
        image: url({});
    }}
    QPushButton:hover {{
        image: url({});
    }}
    QPushButton:disabled {{
        image: url({});
    }}
'''
icon_button_stylesheet = '''
    QPushButton {
        border-style: outset;
        border-width: 0px;
    }
    QPushButton:hover {
        border-color: yellow;
        border-width: 1px;
        border-radius: 6px;
    }
'''
refresh_icon_stylesheet = '''
    QPushButton {{
        image: url({});
        border-style: outset;
        border-width: 0px;
    }}
'''.format(
    joinpath(icon_path, 'refresh_icon.png')
)
version_up_icon_stylesheet = '''
    QPushButton {{
        image: url({});
        border-style: outset;
        border-width: 0px;
    }}
'''.format(
    joinpath(icon_path, 'version_up_icon.png')
)
explorer_icon_stylesheet = '''
    QPushButton {{
        image: url({});
        border-style: outset;
        border-width: 0px;
    }}
'''.format(
    joinpath(icon_path, 'windows_explorer_icon_42px.png')
)
orange_button_stylesheet = '''
    QPushButton {
        color: orange;
        background-color: black;
        border-style: outset;
        border-color: white;
        border-width: 1px;
        border-radius: 6px;
        padding: 6px;
        min-height: 10px;
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
            stop: 0 rgb(71, 71, 71), stop: 0.5 rgb(25, 25, 25),
            stop: 1.0 rgb(71, 71, 71)
        )
    }
    QPushButton:hover {
        color: white;
        border-color: orange;
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
            stop: 0 rgb(25, 25, 25), stop: 0.5 rgb(71, 71, 71),
            stop: 1.0 rgb(25, 25, 25)
        )
    }
'''
blue_button_stylesheet = '''
    QPushButton {
        color: white;
        border-style: outset;
        border-color: white;
        border-width: 1px;
        border-radius: 6px;
        padding: 6px;
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
            stop: 0 rgb(53, 159, 204), stop: 0.5 rgb(32, 94, 121),
            stop: 1.0 rgb(53, 159, 204)
        )
    }
    QPushButton:hover {
        color: orange;
        border-color: black;
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
            stop: 0 rgb(32, 94, 121), stop: 0.5 rgb(53, 159, 204),
            stop: 1.0 rgb(32, 94, 121)
        )
    }
    QPushButton:pressed {
        color: yellow;
        border-color: yellow;
        background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
            stop: 0 rgb(32, 94, 121), stop: 0.5 rgb(53, 159, 204),
            stop: 1.0 rgb(32, 94, 121)
        )
    }
'''
checkbox_stylesheet = '''
    QCheckBox::indicator {{
        width: 20px;
        height: 20px;
    }}
    QCheckBox::indicator:checked {{
        image: url({0});
    }}
    QCheckBox::indicator:checked:hover {{
        image: url({1});
    }}
    QCheckBox::indicator:checked:disabled {{
        image: url({2});
    }}
    QCheckBox::indicator:unchecked {{
        image: url({3});
    }}
    QCheckBox::indicator:unchecked:hover {{
        image: url({4});
    }}
    QCheckBox::indicator:unchecked:disabled {{
        image: url({5});
    }}
'''.format(
    joinpath(icon_path, 'check_green_icon.png'),
    joinpath(icon_path, 'check_green_hilite_icon.png'),
    joinpath(icon_path, 'check_green_disabled_icon.png'),
    joinpath(icon_path, 'x_red_icon.png'),
    joinpath(icon_path, 'x_red_hilite_icon.png'),
    joinpath(icon_path, 'x_red_disabled_icon.png')
)
add_icon_stylesheet = generic_button_icon_stylesheet.format(
    joinpath(icon_path, 'plus_green_icon.png'),
    joinpath(icon_path, 'plus_green_hilite_icon.png'),
    joinpath(icon_path, 'plus_green_disabled_icon.png')

)
remove_icon_stylesheet = generic_button_icon_stylesheet.format(
    joinpath(icon_path, 'minus_red_icon.png'),
    joinpath(icon_path, 'minus_red_hilite_icon.png'),
    joinpath(icon_path, 'minus_red_disabled_icon.png')
)
replace_icon_stylesheet = generic_button_icon_stylesheet.format(
    joinpath(icon_path, 'double_left_arrow_icon.png'),
    joinpath(icon_path, 'double_left_arrow_hilite_icon.png'),
    joinpath(icon_path, 'double_left_arrow_disabled_icon.png')
)
checkbox_stylsheet = '''
    color: white;
'''
black_combo_stylesheet = '''
    QComboBox {
        background-color: rgb(26, 26, 26);
        color: rgb(0, 199, 192);
        border: 1px solid rgb(229, 199, 0);
        border-radius: 5px;
        padding: 0 0 0 4;
    }
    QAbstractItemView {
        color: rgb(0, 221, 213);
    }
    QComboBox::drop-down {
        color: red;
        background-color: black;
        border-radius: 5px;
        image: url(./down.png);
    }
'''
tree_view_styelsheet = '''
    QTreeView::item {
        min-height:22 px
    }
'''
