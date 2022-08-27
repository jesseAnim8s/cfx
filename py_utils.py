"""
General Python utility functions.
"""


# General Imports
import string
from logging import getLogger
from os.path import basename, expanduser, join, normpath, sep, splitext
from os import name as os_name
from re import search as re_search


__author__ = 'Jesse Carlson'
__email__ = 'seven6ty@hotmail.com'
__version__ = 'beta'
# Variables
logger = getLogger(__name__)
company = 'None'


def get_home_dir():
    """Gets the user's home directory on any platform."""
    home_dir = expanduser("~")
    return home_dir


def joinpath(*args):
    """
    Joins paths and standardizes separators per OS.

    Returns:
        String path of assembled pieces, with unified path separators.
    """
    if len(args) == 1:
        args = args[0]
    if os_name == 'nt':
        return join(*args).replace(sep, '/')
    else:
        return normpath(join(*args))


def file_basename(file_name):
    """
    Strips path and file extension from a file path.
    Args:
        file (str): The file path to get the basename,
            with no extension, for.
    Return (str): The file name without path and extension.
    """
    return splitext(basename(file_name))[0]


def get_next_name(name, existing_names, padding=2):
    """
    Gets the next available name, given a list/tuple of existing names.

    Args:
        name (str): The name to try to get, if not taken
        existing_names (str): List/tuple of existing names to compare against
        padding (int): The number of digits for numerical padding

    Returns:
        The next unused name, as a string
    """
    assert isinstance(name, basestring), 'Name must be a string'
    assert isinstance(existing_names, (list, tuple)), \
        'Existing names must be list or tuple'
    assert isinstance(padding, int), 'Padding must be an int'
    num = 1
    # Get the name's base, excluding trailing numbers
    name_base = name.rstrip(string.digits)
    # Get instance number from given name
    name_num_search = re_search('([0-9]+)$', name)
    if name_num_search:
        num = int(name_num_search.group())
    # Increment the name, if it exists
    new_name = '{0}{1}'.format(name_base, str(num).zfill(padding))
    if new_name in existing_names:
        while new_name in existing_names:
            new_name = '{0}{1}'.format(name_base, str(num).zfill(padding))
            num += 1
    return new_name


def hex_to_rgb(hex_str):
    """Converts a hexadecimal string into an RGB tuple."""
    h = hex_str.lstrip('#')
    rgb256 = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    rgb = [float(x)/255 for x in rgb256]
    return rgb
