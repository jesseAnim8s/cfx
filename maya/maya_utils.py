"""General Maya python utilities."""


# General Imports
import logging
from collections import OrderedDict, Mapping
from functools import wraps
# Application Imports
from maya import cmds


__author__ = 'Jesse Carlson'
__email__ = 'seven6ty@hotmail.com'
__version__ = 'beta'
# Variables
logger = logging.getLogger(__name__)
default_attrs = (
    'tx', 'ty', 'tz',
    'rx', 'ry', 'rz',
    'sx', 'sy', 'sz'
)


def load_plugin(plugin_name):
    """Loads the given plug-in.

    Args:
        plugin_name (str): Name of the plug-in to load.

    Returns:
        bool: True if the plug-in has been loaded, otherwise,
            returns False.
    """
    file_type = '.mll'
    if not isinstance(plugin_name, basestring):
        logger.error('Plug-in name must be a string')
        return
    # Ensure filetype is included
    if not plugin_name.endswith(file_type):
        plugin_name += file_type
    # Load the plug-in, if not already loaded
    if not cmds.pluginInfo(plugin_name, query=True, loaded=True):
        cmds.loadPlugin(plugin_name)
    # Return boolean showing if the plug-in has been loaded
    return cmds.pluginInfo(plugin_name, query=True, loaded=True)


def rename(search_str, replace_str):
    """Search and replace strings in selected node names.

    Args:
        search_str (str): What to search for.
        replace_str (str): What to replace with.

    Returns:
        list: A list of the newly named nodes.
    """
    rename_objs = []
    selection = cmds.ls(selection=True, long=True)
    objs = cmds.listRelatives(selection, allDescendents=True, type='transform')
    # TODO: Add top level nodes to object list
    for obj in objs:
        if search_str in obj:
            new_name = obj.replace(search_str, replace_str)
            rename_objs.append(cmds.rename(obj, new_name))
    return rename_objs


def check_mesh_postfix():
    """Ensures the correct postfix on geometry nodes.

    Returns:
        list: A list of newly renamed objects.
    """
    rename_objs = []
    selection = cmds.ls(selection=True, long=True)
    poly_shapes = cmds.listRelatives(selection, allDescendents=True, type='mesh')
    polys = cmds.listRelatives(poly_shapes, parent=True, type='transform')
    for poly in polys:
        if not poly.endswith('_geo'):
            rename_objs.append(cmds.rename(poly, poly + '_geo'))
    return rename_objs


def unlock_attrs(objs, attrs=default_attrs):
    """
    Unlocks given channels for selected objects.

    Args:
        objs (tuple/list/string): The objects to act upon.
        attrs (tuple/list): Attributes to unlock.
    """
    assert objs, 'No objects specified.'
    lock_attrs(objs, attrs, True)


def lock_attrs(objs, attrs=default_attrs, unlock=False):
    """
    Locks given channels for selected objects.

    Args:
        objs (tuple/list/string): The objects to act upon.
        attrs (tuple/list): Attributes to lock.
    """
    assert objs, 'No objects specified.'
    # Convert attributes, if needed
    if attrs == 't' or attrs == ('t'):
        attrs = ('tx', 'ty', 'tz')
    elif attrs == 'r' or attrs == ('r'):
        attrs = ('rx', 'ry', 'rz')
    elif attrs == 's' or attrs == ('s'):
        attrs = ('sx', 'sy', 'sz')
    elif not attrs:
        attrs = default_attrs
    # Convert strings to tuples
    if isinstance(objs, basestring):
        objs = (objs,)
    # Get selection, if necessary
    if not objs:
        objs = cmds.ls(selection=True, long=True)
    for obj in objs:
        for attr in attrs:
            obj_attr = '.'.join((obj, attr))
            if cmds.objExists(obj_attr):
                if not unlock:
                    cmds.setAttr(obj_attr, lock=True, keyable=False)
                else:
                    cmds.setAttr(obj_attr, lock=False, keyable=True)


def undo(func):
    """A decorator that allows undoing multiple steps with one undo.

    Returns:
        The internally defined function.
    """
    @wraps(func)
    def _undofunc(*args, **kwargs):
        try:
            cmds.undoInfo(openChunk=True)
            return func(*args, **kwargs)
        finally:
            cmds.undoInfo(closeChunk=True)
    return _undofunc


def disconnect_attr(obj_attr, skip_connection_type=''):
    """Disconnects any connections to a given object + attribute string.

    Args:
        obj_attr (str): Object + attribute to disconnect.
        skip_connection_type (str): Node types to skip disconnections of.
    """
    # Error checking
    assert isinstance(obj_attr, basestring), 'Argument must be a string'
    assert ('.' in obj_attr), 'String argument must be object + attribute'
    # Get attribute connections
    input_connections = cmds.listConnections(obj_attr, source=True, plugs=True) or []
    # Iterate connections and disconnect them
    for connection in input_connections:
        if connection and cmds.objExists(connection):
            if skip_connection_type \
                    and cmds.nodeType(connection) == skip_connection_type:
                continue
            else:
                cmds.disconnectAttr(connection, obj_attr)


def dict_sdk(sdk_dict):
    """Helper utility for setting numerous Set Driven Keys from a dictionary.

    Args:
        sdk_dict (dict): Dictionary of values to operate upon.
    """
    assert isinstance(sdk_dict, Mapping), 'Argument must be a dictionary'
    for value in sdk_dict['driver_values'].keys():
        for attr in sdk_dict['driver_values'][value].keys():
            obj_attr = '.'.join((sdk_dict['driven'], attr))
            attr_value = sdk_dict['driver_values'][value][attr]
            disconnect_attr(obj_attr, 'animCurveUU')
            cmds.setDrivenKeyframe(
                sdk_dict['driven'],
                attribute=attr,
                currentDriver=sdk_dict['driver'],
                driverValue=float(value),
                value=float(attr_value)
            )


def display_layer(obj, layer_name, color=None, visibility=True):
    """Creates a layer if it doesn't exist & adds the given object to it.

    Args:
        obj (str): Node to apply to a layer.
        layer_name (str): Name of the layer to create.
        color (list/tuple): List of RGB values to set the color to.
        visibility (bool): If True, makes the layer visible,
            invisible if False.
    """
    # Create the display layer, if it doesn't exist already
    if not cmds.objExists(layer_name):
        layer = cmds.createDisplayLayer(obj, name=layer_name,
                                        noRecurse=True)
        cmds.setAttr(layer + '.visibility', visibility)
    # Add the object to the layer, if it already exists
    else:
        if obj and cmds.objExists(obj):
            layer = cmds.editDisplayLayerMembers(
                layer_name,
                obj,
                noRecurse=True
            )
    # Set layer color, if given
    if color:
        cmds.setAttr(layer_name + '.color', True)
        cmds.setAttr(layer_name + '.overrideRGBColors', True)
        cmds.setAttr(layer_name + '.overrideColorRGB', *color)
    return layer_name


def blur_relax():
    """Loads the Blur Relax plug-in, and applies it to selected nodes."""
    if 'BlurRelax' not in cmds.pluginInfo(q=True, listPlugins=True):
        cmds.loadPlugin('BlurRelax')
    if cmds.ls(selection=True):
        cmds.deformer(type='BlurRelax')
    else:
        logger.warning('Nothing selected, doing nothing.')
