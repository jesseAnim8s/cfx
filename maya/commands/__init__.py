"""Maya specific commands and classes."""


# General Imports
try:
    import cpickle as pickle
except:
    import pickle
import time
from logging import getLogger
from os import environ
from os.path import exists as path_exists
from os.path import basename, dirname, splitext
from os.path import join as os_join_path
from re import search as re_search
from sys import path as sys_path
# Application Imports
from maya import cmds, mel
from maya.api import OpenMaya as om
from PySide2 import QtCore, QtWidgets, QtGui
# Package imports
from cfx.maya import maya_utils
from cfx.maya.commands import node as maya_nodes
from cfx.maya.commands import group as maya_groups
from cfx.ui import ui_utils
# Reloads (Remove before release)


__author__ = 'Jesse Carlson'
__email__ = 'seven6ty@hotmail.com'
__version__ = 'beta'
# Variables
logger = getLogger(__name__)
dyn_node_types = (
    'nucleus', 'nCloth', 'hairSystem',
    'nRigid', 'dynamicConstraint',
    'volumeAxisField'
)
yeti_plugin_name = 'pgYetiMaya'


def version_up_file(popup_confirmation=False):
    """Versions up the name of the current file and saves it.

    Args:
        popup_confirmation (bool): If true, gives a pop-up to
            confirm the saving of the file.

    Returns:
        str: The path to the newly saved file.
    """
    new_file_path = None
    dir_path = dirname(get_file_path())
    file_name, ext = splitext(basename(get_file_name()))
    # Derive the next file name to use
    num_result = re_search(r'\d+$', file_name)
    # Save the file
    if num_result:
        num_padding = len(num_result.group())
        num = int(num_result.group())
        next_num = str(num+1).zfill(num_padding)
        new_file_name = '{0}{1}{2}'.format(file_name[:-1 * num_padding], next_num, ext)
        new_file_path = os_join_path(dir_path, new_file_name)
        file_save(new_file_path)
        logger.info('File has been saved as: {0}'.format(new_file_path))
        if popup_confirmation:
            QtWidgets.QMessageBox.information(
                ui_utils.get_maya_win(),
                'File Saved',
                'File has been saved as:\n\t{0}'.format(new_file_path),
                QtWidgets.QMessageBox.Ok
            )
    else:
        logger.warning('Could not version up, file path does not have numbers at the end.')
    return new_file_path


def toggle_dev_mode():
    """Toggles between sourcing code from studio, or user dev area."""
    # Variables
    user_name = environ['USERNAME']
    dev_drive = 'C:'
    studio_drive = 'Q:'
    studio_path_start = (studio_drive, 'Tools')
    dev_path_start = (dev_drive, 'Users', user_name, 'Documents', 'zoic')
    path_end_tokens = ('maya', 'scripts', 'python')
    dividers = ('/', '\\')
    path_index = None
    # Iterate over sys paths
    for path in sys_path:
        # Try both types of dividers
        for divider in dividers:
            path_end = divider.join(path_end_tokens)
            # Check for facility scripts path
            if path.startswith(studio_drive) and path.endswith(path_end):
                dev_path = divider.join(dev_path_start + path_end_tokens)
                # Substitute studio maya path with dev path
                if path_exists(dev_path):
                    path_index = sys_path.index(path)
                    sys_path[path_index] = dev_path
                    break
                break
            # Check for personal dev scripts path
            elif path.startswith(dev_drive) and path.endswith(path_end):
                studio_path = divider.join(studio_path_start + path_end_tokens)
                if path_exists(studio_path):
                    path_index = sys_path.index(path)
                    sys_path[path_index] = studio_path
                    break
                break
    if path_index:
        logger.info('Scripts path is set to: {}'.format(sys_path[path_index]))


def conversion_factor():
    """Determines and returns the appropriate scaling factor.

    Returns:
        float: The conversion unit to use, based on Maya's current
            preferences.
    """
    units = cmds.currentUnit(querty=True, linear=True)
    if units == 'mm':
        return 0.1
    elif units == 'cm':
        return 1.0
    elif units == 'm':
        return 100.0
    elif units == 'in':
        return 2.54
    elif units == 'ft':
        return 30.48
    elif units == 'yd':
        return 91.44
    else:
        return 1.0


def load_plugin(plugin_name):
    """For loading plugins.

    Args:
        plugin_name (str): The name of the plug-in to load.

    Returns:
        bool: True is loaded, otherwise False.
    """
    plugin_filetype = '.mll'
    # Append filetype, if necessary
    if not plugin_name.endswith(plugin_filetype):
        plugin_name += plugin_filetype
    # Load plug-in, if not already loaded
    if not cmds.pluginInfo(plugin_name, query=True, loaded=True):
        cmds.loadPlugin(plugin_name)
    # Return the state of the plug-in
    return cmds.pluginInfo(plugin_name, query=True, loaded=True)


def file_dialog(mode, label='', filter_str='', default_dir=''):
    """Opens a native Maya file browsing dialog.

    Args:
        mode (str): Mode to operate in.  Either "file", "existing_file",
            "multiple_files", or "directory".
        label (str): Text to display.
        filter_str (str): String to filter files with.
        default_dir (str): The directory to start at by default.

    Returns:
        str: The user's picked file(s)/directory.
    """
    valid_modes = ('file', 'existing_file', 'multiple_files',
                   'directory')
    file_mode, user_input = None, None
    # Error check
    assert (mode in valid_modes), \
        'Specified mode must be valid: {}'.format(valid_modes)
    # Open the file dialog
    if mode == 'file':
        file_mode = 0
    elif mode == 'existing_file':
        file_mode = 1
    elif mode == 'multiple_files':
        file_mode = 4
    elif mode == 'directory':
        file_mode = 3
    if isinstance(file_mode, int):
        user_input = cmds.fileDialog2(
            buttonBoxOrientation=2,
            caption=label,
            fileFilter=filter_str,
            fileMode=mode,
            hideNameEdit=False,
            startingDirectory=default_dir
        )
    # Return user input
    return user_input


def file_new(start=None, end=None, preroll=None):
    """Creates a new file.

    Args:
        start (int/float): Start frame.
        end (int/float): End frame.
        preroll (int/float): Number of preroll frames.
    """
    cmds.file(new=True, force=True)
    if isinstance(preroll, int) or isinstance(start, int) \
            or isinstance(end, int):
        set_frame_range(start, end, preroll)
    if preroll:
        set_current_frame(start - preroll)
    else:
        set_current_frame(start)


def file_save(filepath):
    """Saves the current scene file to the given file path.

    Args:
        filepath (str): The file path to save the current scene as.
    """
    cmds.file(rename=filepath)
    cmds.file(save=True)


def file_import(file_name, parent=None, namespace=None, delete_layers=True):
    """Imports a file, with the ability to delete layers and parent objects.

    Args:
        file_name (str): The name of the file to import.
        parent (str): Node name to parent imports under.
        namespace (str): Namespace to apply to imports.
        delete_layers (str): Deletes the imported layers, if True.
    """
    # Error checking
    assert path_exists(file_name), 'File does not exist, doing nothing'
    # Store in-scene items before importing
    pre_layers = cmds.ls(type='displayLayer')
    pre_objs = cmds.ls(assemblies=True)
    # Import
    if namespace:
        cmds.file(file_name, i=True, namespace=namespace)
    else:
        cmds.file(file_name, i=True)
    # Store in-scene items after importing
    post_layers = cmds.ls(type='displayLayer')
    post_objs = cmds.ls(assemblies=True)
    # Derive imported objects
    imported_layers = list(set(post_layers) - set(pre_layers))
    imported_objs = list(set(post_objs) - set(pre_objs))
    # Parent imported objects, if specified
    if parent and cmds.objExists(parent):
        cmds.parent(imported_objs, parent)
    # Delete imported layers, if specified
    if delete_layers:
        cmds.delete(imported_layers)


def get_file_path():
    """Gets the name of the current scene file.

    Returns:
        str: The current scene's file path.
    """
    file_path = cmds.file(query=True, sceneName=True)
    return file_path


# TODO: Move to py_utils...
def get_file_name():
    """Gets the name of the current scene file, with extension.

    Returns:
        str: The current scene file's name, without the directory path.
    """
    file_name = basename(get_file_path())
    return file_name


# TODO: Move to py_utils...
def get_file_name_no_ext():
    """Gets the name of the current scene file, with no extension.

    Returns:
        str: The current scene's file name without it's directory
            or extension.
    """
    file_name, ext = splitext(get_file_name())
    return file_name


def copy_skin_weights(source_mesh, target_mesh, prune_weights_tolerance=None):
    """Copies skin weighting from source to target mesh.

    Args:
        source_mesh (str): The mesh to copy skin weights from.
        target_mesh (str): The mesh to copy skin weights to.
        prune_weights_tolerance (float): Any vertex with a value below this number,
            will be set to 0.
    """
    # Lambda to get skin clusters for the given object - Extract to separate function??
    get_skin_clusters = lambda obj: cmds.ls(cmds.listHistory(obj), type='skinCluster')
    # Get mesh skin clusters
    source_skin_clusters = get_skin_clusters(source_mesh)
    target_skin_clusters = get_skin_clusters(target_mesh)
    # Error check
    assert source_skin_clusters, 'Source mesh has no skinClusters.'
    # Get bind joints from source mesh
    source_influences = cmds.skinCluster(
        source_skin_clusters[0], query=True, influence=True
    )
    # Bind target mesh to joints, if it has no skinCluster
    if source_skin_clusters and not target_skin_clusters:
        target_skin_cluster = cmds.skinCluster(
            source_influences,
            target_mesh,
            maximumInfluences=3,
            skinMethod=0
        )[0]
    # Add missing joint influences, for target mesh with skinCluster
    elif source_skin_clusters and target_skin_clusters:
        target_skin_cluster = target_skin_clusters[0]
        target_influences = cmds.skinCluster(
            source_skin_clusters[0], query=True, influence=True
        )
        missing_joints = [x for x in source_influences if x not in target_influences]
        for joint in missing_joints:
            cmds.skinCluster(target_skin_cluster, addInfluence=joint)
    # Copy skin weights
    cmds.copySkinWeights(
        sourceSkin=source_skin_clusters[0],
        destinationSkin=target_skin_cluster,
        noMirror=True,
        surfaceAssociation='closestPoint',
        influenceAssociation=['closestJoint', 'closestBone', 'oneToOne']
    )
    # Prune weights, if specified
    if prune_weights_tolerance and isinstance(prune_weights_tolerance, float):
        cmds.skinPercent(target_skin_cluster, target_mesh,
                         pruneWeights=prune_weights_tolerance)


def file_reference(file_path, namespace=''):
    """References a given file.

    Args:
        file_path (str): File path to reference.
        namespace (str): Namespace to apply to the reference.
    """
    if path_exists(file_path):
        if namespace:
            cmds.file(
                file_path,
                reference=True,
                usingNamespaces=True,
                namespace=namespace
            )
        else:
            cmds.file(file_path, reference=True)
    else:
        logger.error(
            'The given file path does not exist: {}'.format(file_path)
        )


def import_abc(file_path):
    """Imports an ABC file, and returns the imported objects.

    Args:
        file_path (str): ABC file path to import.

    Returns:
        list: List of all imported top level objects.
    """
    assert path_exists(file_path), 'File path does not exist.'
    pre_import_objs = list_assemblies()
    cmds.AbcImport(file_path, mode='import')
    post_import_objs = list_assemblies()
    imported_objs = list(set(post_import_objs) - set(pre_import_objs))
    logger.info('Imported the following objects: {}'.format(imported_objs))
    return imported_objs


def import_atom(file_path):
    """Imports Atom settings.

    Args:
        file_path (str): File path to import ATOM settings from.
    """
    nodes = []
    selection = cmds.ls(selection=True)
    for type in dyn_node_types:
        nodes.extend(cmds.ls(type=type))
    cmds.select(nodes)
    if file_path and path_exists(file_path):
        logger.info('Loading settings from:')
        logger.info('    {}'.format(file_path))
        cmds.loadPlugin('atomImportExport', quiet=True)
        cmds.file(
            file_path,
            i=True,
            type='atomImport',
            options=(';;targetTime=3;option=insert;'
                     'match=string;;selected=childrenToo;')
        )
        cmds.select(selection, replace=True)
    else:
        logger.warning('No existing file given, doing nothing.')


def export_atom(file_path):
    """Exports Atom settings.

    Args:
        file_path (str): File path to export ATOM settings to.
    """
    nodes = []
    selection = cmds.ls(selection=True)
    for type in dyn_node_types:
        nodes.extend(cmds.ls(type=type))
    cmds.select(nodes)
    logger.info('Exporting settings for the following nodes:')
    for node in nodes:
        logger.info('    {}'.format(node))
    logger.info('Exporting settings to:')
    logger.info('    {}'.format(file_path))
    cmds.loadPlugin('atomImportExport', quiet=True)
    cmds.file(
        file_path,
        exportSelected=True,
        force=True,
        options='statics=1',
        type='atomExport'
    )
    cmds.select(selection, replace=True)


def export_dyn_weightmaps(file_path):
    """Exports dynamic weight maps from a scene.

    Args:
        file_path (str): File path to export weight maps to.
    """
    export_dict = {}
    dyn_node_types = ('nRigid', 'nucleus', 'nCloth')
    # Iterate over all dynamic nodes in the scene
    dyn_nodes = cmds.ls(type=dyn_node_types)
    for node in dyn_nodes:
        # Get all the attributes of each node
        attrs = cmds.listAttr(node)
        # Find dynamic weight maps
        map_attrs = [x for x in attrs if x.endswith('Map')]
        vert_attrs = [x for x in attrs if x.endswith('PerVertex')]
        all_attr_weightmaps = map_attrs + vert_attrs
        # Iterate over all weight map attributes
        for attr in all_attr_weightmaps:
            obj_attr = '.'.join((node, attr))
            # If the attribute has a painted array of values, save it
            attr_value = cmds.getAttr(obj_attr)
            if isinstance(attr_value, (list, tuple)):
                export_dict[obj_attr] = attr_value
    # Error check dictionary
    if not export_dict:
        logger.info('No dynamic nodes with painted maps to export.')
        logger.info('  Doing nothing.')
    # Export the values to the given file
    else:
        pickle.dump(export_dict, open(file_path, 'wb'))


def import_dyn_weightmaps(file_path):
    """Imports dynamic weight maps to a scene.

    Args:
        file_path (str): File path to import dynamic object
            weight maps from.
    """
    # Error check
    assert path_exists(file_path), 'Path does not exist, doing nothing.'
    # Import file
    weights_dict = pickle.load(open(file_path, 'rb'))
    for obj_attr, value in weights_dict.items():
        cmds.setAttr(obj_attr, value, type='doubleArray')


def node_type(node=''):
    """Gets the node type of a given node.

    Args:
        node (str): The node to get the type of.

    Returns:
        str: The node type of the given node.
    """
    if node and cmds.objExists(node):
        return cmds.nodeType(node)


def get_value(node='', attr=''):
    """Gets the value, for a given node's attribute.

    Args:
        node (str): Node name.
        attr (str): Attribute name.

    Returns:
        str: The node name + attribute with a period separating them.
    """
    if node_exists('{}.{}'.format(node, attr)):
        return cmds.getAttr('{}.{}'.format(node, attr))


def get_start_frame():
    """Gets the start of the timeline frame range.

    Returns:
        float: The timeline's outermost start frame.
    """
    return cmds.playbackOptions(query=True, animationStartTime=True)


def get_timeslider_start_frame():
    """Gets the start of the time slider frame range.

    Returns:
        float: The timeline's innermost start frame.
    """
    return cmds.playbackOptions(query=True, minTime=True)


def get_timeslider_end_frame():
    """Gets the end of the time slider frame range.

    Returns:
        float: The timeline's outermost end frame.
    """
    return cmds.playbackOptions(query=True, maxTime=True)


def get_end_frame():
    """Gets the end of the timeline frame range.

    Returns:
        float: The timeline's innermost end frame.
    """
    return cmds.playbackOptions(query=True, animationEndTime=True)


def get_workspace_dir():
    """Gets the current workspace directory.

    Returns:
        str: The current project directory.
    """
    return cmds.workspace(query=True, rootDirectory=True)


def get_scene_name():
    """Gets the name of the current Maya file.

    The current scene file's full path.
    """
    return cmds.file(query=True, sceneName=True, shortName=True)


def get_selection():
    """
    Gets selected nodes.

    Returns:
        A tuple of the selected nodes.
    """
    return cmds.ls(selection=True)


def get_hierarchy_meshes(nodes):
    """Gets all polygon transform nodes under a given node.

    Args:
        nodes (list/tuple): List of node names to search the hierarchies of.

    Returns:
        list: List of transform nodes for all polygons in the hierarchy.
    """
    assert cmds.objExists(nodes)
    mesh_shapes = cmds.listRelatives(nodes, type='mesh', allDescendents=True)
    return cmds.listRelatives(mesh_shapes, parent=True)


def get_connections(node='', type=''):
    """Gets a node's connections, of a given type."""
    nodes = []
    if node and node_exists(node) and type in cmds.allNodeTypes():
        connections = cmds.listConnections(node, type=type) or []
        for object in connections:
            if cmds.nodeType(object) != type:
                children = cmds.listRelatives(object, type=type,
                                              children=True) or []
                nodes.extend(children)
            else:
                nodes.append(object)
    return nodes


def get_next_multi_index(obj_attr):
    """Gets the next available indice for a multi attribute.

    Args:
        obj_attr (str): Node name, period, & attribute name to search.

    Returns:
        int: 0 if no connected items found, otherwise, the number of
            valid connections.
    """
    attr_list = cmds.getAttr(obj_attr, multiIndices=True)
    if attr_list:
        for count, item in enumerate(attr_list):
            if count != item:
                return count
            else:
                if count + 1 == len(attr_list):
                    return len(attr_list)
    else:
        return 0


def get_cache_file_connections(node_name=''):
    """Gets cacheFile nodes connected to the given node.

    Args:
        node_name (str): The node name to get connections for.

    Returns:
        list: List of cacheFile node type connections.
    """
    cache_nodes = cmds.listConnections(
        node_name, type='cacheFile', source=True
    ) or []
    return cache_nodes


def get_nearest_uv_on_mesh(mesh, position):
    """Gets the UV for the closest given point on a mesh.


    Args:
        mesh (str): Mesh node name.
        position (list/tuple): XYZ coordinates to find the nearest UV
            position for, on the given mesh.

    Returns:
        MPoint: UV coordinates of the given mesh.
    """
    selection = om.MSelectionList()
    selection.add(mesh)
    mesh_dag = selection.getDagPath(0)
    mesh_pointer = om.MFnMesh(mesh_dag)
    point_position = om.MPoint(position[0], position[1], position[2])
    world_space = om.MSpace.kWorld
    return mesh_pointer.getUVAtPoint(point_position, world_space,)


def get_curve_base_uv(curve, mesh):
    """Gets the position of a curves base CV (0).

    Args:
        curve (str): The curve node name to search.
        mesh (str): The mesh node name to search.

    Returns:
        tuple: UV coordinates that were found.
    """
    assert cmds.objExists(curve), 'Given curve does not exist.'
    # Variables
    curve_shapes = cmds.listRelatives(curve, shapes=True, type='nurbsCurve')
    mesh_shapes = cmds.listRelatives(mesh, shapes=True, type='mesh')
    assert len(curve_shapes), 'Curve argument does not have a nurbsCurve shape node.'
    assert len(mesh_shapes), 'Mesh argument does not have a mesh shape node.'
    # Get curve base position
    position = cmds.pointPosition(curve_shapes[0] + '.cv[0]', world=True)
    # Find the nearest point on the mesh
    load_plugin('nearestPointOnMesh')
    util_node = cmds.createNode('nearestPointOnMesh', name=curve + '_nearest_point_util')
    cmds.connectAttr(mesh_shapes[0] + '.worldMesh', util_node + '.inMesh')
    cmds.setAttr(util_node + '.inPosition', position[0], position[1], position[2], type='double3')
    u = cmds.getAttr(util_node + '.parameterU')
    v = cmds.getAttr(util_node + '.parameterV')
    cmds.delete(util_node)
    return (u, v)


def ls(*args, **kwargs):
    """Lists nodes with the given arguments.

    Args:
        args (dict): Arguments to pass to the ls command.
        kwargs (dict): Keyword arguments to pass to the ls command.

    Returns:
        list: List of given nodes matching the arguments given.
    """
    return cmds.ls(*args, **kwargs)


def list_assemblies():
    """Lists all top level nodes in a Maya scene.

    Returns:
        list: All top level assembly nodes.
    """
    return cmds.ls(assemblies=True, long=True)


def list_script_jobs():
    """Lists all scriptJob nodes in the current scene file.

    Returns:
        list: List of scriptJob names.
    """
    return cmds.scriptJob(listJobs=True)


def ls_all_transforms_by_type(type='mesh'):
    """Returns parent transform nodes for all of a given node type.

    Args:
        type (str): Node type to list the shapes of.

    Returns:
        list: List of transform nodes for the given type nodes.
    """
    shapes = cmds.ls(type=type)
    transforms = cmds.listRelatives(shapes, parent=True)
    return transforms


def select(*args, **kwargs):
    """Selects given nodes.

    Args:
        args (dict): Dictionary of arguments.
        kwargs (dict): Dictionary of key word arguments.
    """
    cmds.select(*args, **kwargs)


def parent(*args, **kwargs):
    """Re-parents object(s).

    Args:
        args (dict): Dictionary of arguments.
        kwargs (dict): Dictionary of key word arguments.

    Returns:
        list: List of re-parented nodes.
    """
    return cmds.parent(*args, **kwargs)


def delete(*args, **kwargs):
    """Delete object(s).

    Args:
        args (dict): Dictionary of arguments.
        kwargs (dict): Dictionary of key word arguments.
    """
    cmds.delete(*args, **kwargs)


def set_current_frame(frame):
    """Sets the current frame.

    Args:
        frame (int/float): Frame to set to.
    """
    cmds.currentTime(frame, edit=True)


def set_frame_range(start=None, end=None, preroll=None):
    """Sets the Maya timeline frame range.

    Args:
        start (float/int): Start frame.
        end (float/int): End frame.
        preroll (float/int): Number of preroll frames to add.
    """
    if isinstance(start, int):
        cmds.playbackOptions(edit=True, animationStartTime=start)
        if isinstance(preroll, int):
            cmds.playbackOptions(edit=True, minTime=start - preroll)
        else:
            cmds.playbackOptions(edit=True, minTime=start)
    if isinstance(end, int):
        cmds.playbackOptions(edit=True, animationEndTime=end)
        cmds.playbackOptions(edit=True, maxTime=end)


def remove_unknown_plugins():
    """Removes unknown plugins from the scene."""
    unknown_plugins = cmds.unknownPlugin(query=True, list=True)
    if unknown_plugins:
        logger.info('Found unknown plugins, removing them...')
        for unknown_plugin in unknown_plugins:
            cmds.unknownPlugin(unknown_plugin, remove=True)
        logger.info('    Done removing unknown plugins!')


def delete_unused_shaders():
    """Deletes unused shaders, from the Hypergraph window menu."""
    logger.info('Removing unused shader nodes...')
    mel.eval('MLdeleteUnused')
    logger.info('    Done removing unused shader nodes!')


def delete_all_layers():
    """Deletes all layers in a file."""
    default_layer = 'defaultLayer'
    all_layers = cmds.ls(type='displayLayer')
    cmds.delete([x for x in all_layers if x != default_layer])


def wrap(*args, **kwargs):
    """Updated Maya wrap command, returning wrap + base node names.

    Args:
        args (dict): Arguments.
        kwargs (dict): Key word arguments.

    Returns:
        tuple: First element is the wrap name, and the second is
            the name of the resulting base mesh duplicate.
    """
    influence = args[0]
    surface = args[1]
    # Get arguments
    weight_threshold = kwargs.get('weight_threshold', 0.0)
    max_distance = kwargs.get('max_distance', 1.0)
    exclusive_bind = kwargs.get('exclusive_bind', True)
    autoweight_threshold = kwargs.get('autoweight_threshold', True)
    falloff_mode = kwargs.get('falloff_mode', 0)
    # Get shapes
    influence_shape = maya_nodes.Node(influence).get_shapes()[0]
    # Create wrap deformer
    wrap_deformer = cmds.deformer(surface, type='wrap')[0]
    wrap_node = maya_nodes.Node(wrap_deformer)
    cmds.connectAttr('{}.worldMatrix[0]'.format(surface),
                     wrap_node.attr_str('geomMatrix'))
    # Apply settings
    cmds.setAttr(wrap_node.attr_str('weightThreshold'), weight_threshold)
    cmds.setAttr(wrap_node.attr_str('maxDistance'), max_distance)
    cmds.setAttr(wrap_node.attr_str('exclusiveBind'), exclusive_bind)
    cmds.setAttr(wrap_node.attr_str('autoWeightThreshold'), autoweight_threshold)
    cmds.setAttr(wrap_node.attr_str('falloffMode'), falloff_mode)
    # Create base shape
    base = cmds.duplicate(influence, name='{}Base'.format(influence))[0]
    base_shape = maya_nodes.Node(base).get_shapes()[0]
    cmds.hide(base)
    # Create attributes
    if not cmds.attributeQuery('dropoff', node=influence, exists=True):
        cmds.addAttr(influence, shortName='dr', longName='dropoff',
                     defaultValue=4.0, minValue=0.0, maxValue=20.0)
        cmds.setAttr('{}.dropoff'.format(influence), keyable=True)
    # Deal with meshes
    if cmds.nodeType(influence_shape) == 'mesh':
        # Create smoothness attribute
        _query = cmds.attributeQuery(
            'smoothness', node=influence, exists=True
        )
        if not _query:
            cmds.addAttr(influence, shortName='smt', longName='smoothness',
                         defaultValue=0.0, minValue=0.0)
            cmds.setAttr('{}.smt'.format(influence), k=True)
        # Create influence type attribute
        _query = cmds.attributeQuery(
            'inflType', node=influence, exists=True
        )
        if not _query:
            cmds.addAttr(influence, shortName='ift', longName='inflType',
                         defaultValue=2, minValue=1, maxValue=2,
                         attributeType='short')
        # Connect mesh attributes
        cmds.connectAttr('{}.worldMesh'.format(influence_shape),
                         wrap_node.attr_str('driverPoints[0]'))
        cmds.connectAttr('{}.worldMesh'.format(base_shape),
                         wrap_node.attr_str('basePoints[0]'))
        cmds.connectAttr('{}.inflType'.format(influence),
                         wrap_node.attr_str('inflType[0]'))
        cmds.connectAttr('{}.smoothness'.format(influence),
                         wrap_node.attr_str('smoothness[0]'))
    elif cmds.nodeType(influence_shape) in ('nurbsCurve', 'nurbsSurface'):
        # Create wrapSamples attribute
        _query = cmds.attributeQuery(
            'wrapSamples', node=influence, exists=True
        )
        if not _query:
            cmds.addAttr(influence, shortName='wsm', longName='wrapSamples',
                         defaultValue=10, minValue=1, attributeType='short')
            cmds.setAttr('{}.wsm'.format(influence), keyable=True)
        # Connect NURBS attributes
        cmds.connectAttr('{}.ws'.format(influence_shape),
                         wrap_node.attr_str('driverPoints[0]'))
        cmds.connectAttr('{}.ws'.format(base_shape),
                         wrap_node.attr_str('basePoints[0]'))
        cmds.connectAttr('{}.wsm'.format(influence),
                         wrap_node.attr_str('nurbsSamples[0]'))
    # Connect dropoff attribute
    cmds.connectAttr('{}.dropoff'.format(influence),
                     wrap_node.attr_str('dropoff[0]'))
    # Lock wrap node
    cmds.setAttr('{}.input[0].inputGeometry'.format(wrap),
                 lock=True)
    return wrap, base


def recursive_hierarchy(dictionary, parent=None):
    """Iterates over a converted dictionary to create a hierarchy.

    Args:
        dictionary (dict): Dictionary to iterate over.
        parent (QtWidgets.QWidget): UI element to use as a parent.
    """
    path_str = 'full_path'
    type_str = 'type'
    geo_set_name = 'zoic_anm_abc_set'
    top_str = 'top_nodes'
    child_str = 'children'
    viz_str = 'visibility'
    geo_groups = ('geometry_grp', 'geometry_gp')
    reserved_strs = (top_str, child_str, path_str, type_str)
    # Iterate dictionary
    for key, value in dictionary.items():
        if key == top_str:
            recursive_hierarchy(value)
        elif key not in reserved_strs:
            # Create groups that don't yet exist
            if not cmds.objExists(key):
                group_inst = maya_groups.Group(name=key, parent=parent)
                group_inst.create()
                group = group_inst.name
                # Set node's visibility
                if viz_str in dictionary[key].keys():
                    viz = dictionary[key][viz_str]
                    if not viz:
                        cmds.hide(key)
            # Store groups that already exist
            else:
                group = key
                group_inst = maya_nodes.Node(key)
                # Parent orphaned hierarchy nodes
                if parent and group_inst.parent() != parent:
                    group_inst.reparent(parent)
            # Create geometry set, if needed
            if key in geo_groups \
                    and not cmds.objExists(geo_set_name):
                cmds.sets(key, name=geo_set_name)
            # Store type
            dictionary[key][type_str] = 'group'
            # Store full paths
            dictionary[key][path_str] = cmds.ls(group, long=True)[0]
            # Recurse over child nodes
            if child_str in dictionary[key].keys():
                child_dict = dictionary[key][child_str]
                recursive_hierarchy(child_dict, key)


def node_exists(node):
    """Queries if a given node name exists.

    Args:
        node (str): Does this node name exist?

    Returns:
        bool: True if the node name exists, otherwise False.
    """
    return cmds.objExists(node)


def dyn_hair(mesh, curves, hsys='hairSystem1', nucleus='nucleus1',
             make_rest_curve=True, make_start_curve=True):
    """Creates a dynamic hair setup from a curve and mesh surface.

    Args:
        mesh (str):
        curves (list/tuple):
        hsys (str): Name of the hairSystem transform node.
        nucleus (str): Name of the nucleus transform node.
        make_rest_curve (bool): If True, generates rest curve duplicates.
        make_start_curve (bool): If True, generates start curve duplicates.

    Returns:
        list: A list of follicles, curves, start_curves, rest_curves,
            nucleus and hairSystem nodes that get created.
    """
    start_time = time.time()
    curves = [x for x in curves if cmds.objExists(x)]
    curves = [x for x in curves if cmds.listRelatives(x, shapes=True, type='nurbsCurve')]
    start_curves, rest_curves = [], []
    follicles = []

    # Error checks
    assert (len(curves) >= 1), 'Curve nodes must be of "nurbsCurve" type.'
    assert cmds.objExists(mesh), 'Mesh must exist.'
    mesh_shapes = cmds.listRelatives(mesh, shapes=True, type='mesh')
    assert len(mesh_shapes), 'Mesh argument does not have a mesh shape node.'
    uv_set = cmds.polyUVSet(mesh, query=True, currentUVSet=True)

    # Nucleus
    if not cmds.objExists(nucleus):
        nucleus = cmds.createNode('nucleus', name=nucleus)
        cmds.connectAttr('time1.outTime', nucleus + '.currentTime')

    # Hair system
    if not hsys or not cmds.objExists(hsys):
        hsys = cmds.createNode('hairSystem', name=hsys + 'Shape')
        cmds.connectAttr('time1.outTime', hsys + '.currentTime')
    cmds.setAttr(hsys + '.active', 1)
    cmds.setAttr(hsys + '.clumpWidth', 0)
    cmds.setAttr(hsys + '.hairsPerClump', 1)

    # Nucleus/Hair system connections
    if not cmds.listConnections(hsys + '.startFrame', source=True):
        cmds.connectAttr(nucleus + '.startFrame', hsys + '.startFrame')
    index = get_next_multi_index(nucleus + '.inputActive')
    cmds.connectAttr(hsys + '.currentState', '{0}.inputActive[{1}]'.format(nucleus, index))
    index = get_next_multi_index(nucleus + '.inputActiveStart')
    cmds.connectAttr(hsys + '.startState', '{0}.inputActiveStart[{1}]'.format(nucleus, index))
    if not cmds.listConnections(hsys + '.nextState'):
        index = get_next_multi_index(nucleus + '.outputObjects')
        cmds.connectAttr('{0}.outputObjects[{1}]'.format(nucleus, index), hsys + '.nextState')

    for curve in curves:
        curve_degree = cmds.getAttr(curve + '.degree')
        u, v = get_curve_base_uv(curve, mesh)
        start_name, rest_name = None, None
        if make_start_curve:
            if '_output_curve_' in curve:
                start_name = curve.replace('_output_curve_', '_start_curve_')
            elif curve.startswith('curve'):
                start_name = curve + '_start'
            else:
                start_name = curve + '_start_curve'
        if make_rest_curve:
            if '_output_curve_' in curve:
                rest_name = curve.replace('_output_curve_', '_rest_curve_')
            elif curve.startswith('curve'):
                rest_name = curve + '_rest'
            else:
                rest_name = curve + '_rest_curve'
        follicle_name = curve + '_follicle'

        # Curve duplicates
        if make_rest_curve:
            rest_curve = cmds.duplicate(curve, name=rest_name)[0]
            rest_curve_shape = cmds.listRelatives(rest_curve, shapes=True)[0]
        if make_start_curve:
            start_curve = cmds.duplicate(curve, name=start_name)[0]
            start_curve_shape = cmds.listRelatives(start_curve, shapes=True)[0]

        # Follicle
        follicle = cmds.createNode('transform', name=follicle_name, skipSelect=True)
        follicles.append(str(follicle))
        follicle_shape = cmds.createNode('follicle', name=follicle + 'Shape', parent=follicle)
        cmds.setAttr(follicle_shape + '.degree', curve_degree)
        cmds.setAttr(follicle_shape + '.parameterU', u)
        cmds.setAttr(follicle_shape + '.parameterV', v)
        cmds.setAttr(follicle_shape + '.pointLock', 1)
        cmds.setAttr(follicle_shape + '.restPose', 1)
        cmds.setAttr(follicle_shape + '.startDirection', 1)
        cmds.connectAttr(mesh_shapes[0] + '.worldMatrix[0]',
                         follicle_shape + '.inputWorldMatrix')
        if mesh_shapes:
            cmds.setAttr(follicle_shape + '.mapSetName', uv_set[0], type='string')
            cmds.connectAttr(mesh_shapes[0] + '.outMesh',
                             follicle_shape + '.inputMesh')
        cmds.connectAttr(follicle_shape + '.outTranslate',
                         follicle + '.translate')
        cmds.connectAttr(follicle_shape + '.outRotate',
                         follicle + '.rotate')
        cmds.setAttr(follicle + '.translate', lock=True)
        cmds.setAttr(follicle + '.rotate', lock=True)
        index = get_next_multi_index(hsys + '.inputHair')
        cmds.connectAttr(follicle_shape + '.outHair', '{}.inputHair[{}]'.format(hsys, index))
        cmds.connectAttr('{}.outputHair[{}]'.format(hsys, index),
                         follicle_shape + '.currentPosition')

        # Rebuild curve
        new_transform, rebuild_node = cmds.rebuildCurve(
            curve,
            constructionHistory=True,
            replaceOriginal=False,
            rebuildType=0,
            endKnots=1,
            keepRange=0,
            keepControlPoints=0,
            keepEndPoints=1,
            keepTangents=0,
            spans=0,
            degree=1,
            tolerance=0.1
        )
        new_shape = cmds.listRelatives(new_transform, shapes=True)[0]
        cmds.parent(new_shape, curve, relative=True, shape=True)
        cmds.delete(new_transform)

        # Curve connections
        if make_start_curve:
            cmds.connectAttr(start_curve_shape + '.local',
                             follicle_shape + '.startPosition')
            cmds.connectAttr(start_curve + '.worldMatrix[0]',
                             follicle_shape + '.startPositionMatrix')
            start_curve = cmds.parent(start_curve, follicle)[0]
            start_curves.append(str(start_curve))
        else:
            cmds.connectAttr(new_shape + '.local',
                             follicle_shape + '.startPosition')
            cmds.connectAttr(new_shape + '.worldMatrix[0]',
                             follicle_shape + '.startPositionMatrix')

        # Output curve
        new_curve_shape = cmds.createNode('nurbsCurve')
        cmds.connectAttr(follicle_shape + '.outCurve', new_curve_shape + '.create')
        new_curve = cmds.listRelatives(new_curve_shape, parent=True)[0]
        cmds.delete(curve)
        curve = cmds.rename(new_curve, curve)

        # Rest curve
        if make_rest_curve:
            cmds.connectAttr(rest_curve_shape + '.worldSpace[0]',
                             follicle_shape + '.restPosition')
            rest_curve = cmds.parent(rest_curve, follicle)[0]
            rest_curves.append(str(rest_curve))
        cmds.setAttr(follicle_shape + '.restPose', 3)

    end_time = time.time()
    logger.info('Created dynamic hairs in {:.2f} seconds'.format((end_time - start_time)))

    return follicles, curves, start_curves, rest_curves, nucleus, hsys


def cache_sim(start_frame=1001, end_frame=1020, nodes=[],
              cache_dir='', file_name_prefix='', cache_file_ext='mcx',
              sim_rate=1.0, sim_rate_multiplier=1.0, refresh_ui=False):
    """Caches out in-scene simulations.

    Args:
        start_frame (int/float): Start frame number.
        end_frame (int/float): End frame number.
        nodes (list/tuple): Node names to cache.
        cache_dir (str): Directory to cache to.
        file_name_prefix (str): Prefix every file name with this string.
        cache_file_ext (str): File type extension to use for the cache (mcc/mcx).
        sim_rate (float): Sample rate per frame.
        sim_rate_multiplier (float): Sample rate per frame multiplier.
        refresh_ui (bool): If true, refreshes the UI with each step of caching.
    """

    # Error check
    assert all([isinstance(x, (float, int)) for x in (start_frame, end_frame)]), \
        'Start & end frames must be floats or integers'
    assert (nodes and all([cmds.objExists(x) for x in nodes])), \
        'Specified nodes do not exist'
    assert cache_file_ext in ('mcx', 'mcc'), 'File extension must be mcx/mcc'

    # Derive arguments
    use_file_prefix = 1 if file_name_prefix else 0

    # Get current selection
    current_selection = cmds.ls(selection=True)
    # Select nodes to cache
    cmds.select(nodes)
    # TODO: verify only hairSystem, nCloth, etc nodes...

    # Cache nodes
    clear_cache_cmd = 'deleteCacheFile 2 { "keep", ""}'
    cache_cmd = (
        'doCreateNclothCache 5 {{ "3", "{start}", "{end}", "OneFile", '
        '"{update}", "{dir}", "1", "{pfx}", "{use_pfx}", "replace", "1", '
        '"{rate}", "{mult}", "0", "1", "{ext}"}}'
    ).format(
        start=start_frame,
        end=end_frame,
        update=int(refresh_ui),
        dir=cache_dir,
        pfx=file_name_prefix,
        use_pfx=use_file_prefix,
        rate=sim_rate,
        mult=sim_rate_multiplier,
        ext=cache_file_ext
    )
    logger.info('Running command...\n\t{}'.format(cache_cmd))
    mel.eval('; '.join((clear_cache_cmd, cache_cmd)))
    logger.info('    ....Done caching simulation!')

    # Revert selection
    cmds.select(current_selection)


def create_script_job(obj_attr='', func=None):
    """Creates a script job for the given object/attribute.

    Args:
        obj_attr (str): <object name>.<attribute name>
        func (str): Function to run when the given object/attribute changes.
    """
    if cmds.objExists(obj_attr):
        cmds.scriptJob(
            killWithScene=True,
            attributeChange=[
                obj_attr,
                func
            ]
        )


def kill_script_job_id(job_id):
    """Deletes a given script job ID, provided it exists.

    Args:
        job_id (str/int): The ID of the scriptJob to search for.
    """
    if cmds.scriptJob(exists=int(job_id)):
        cmds.scriptJob(kill=int(job_id), force=True)


def lambert_shader(name, color, nodes):
    """Creates & assigns a lambert shader to given nodes.

    Args:
        name (str):
        color (list/tuple):
        nodes (list/tuple):

    Returns:
        tuple: Two elements, the first is the name of the newly created
            shader, the second, the name of the resulting shader set.
    """
    if isinstance(nodes, basestring):
        nodes = (nodes,)
    assert isinstance(nodes, (list, tuple)), 'Nodes must be string/list/tuple.'
    existing_nodes = [x for x in nodes if cmds.objExists(x)]
    # Lambert material
    if not cmds.objExists(name):
        shader = cmds.shadingNode('lambert', name=name, asShader=True)
    else:
        shader = name
    # Set lambert color
    cmds.setAttr('{}.color'.format(name), *color, type='double3')
    # Shader set
    shader_set_name = name + '_shaderSet'
    if not cmds.objExists(shader_set_name):
        cmds.sets(name=shader_set_name, empty=True,
                  renderable=True, noSurfaceShader=True)
    cmds.sets(existing_nodes, edit=True, forceElement=shader_set_name)
    # Create connections
    shader_connections = cmds.listConnections('{}.outColor'.format(shader))
    if not shader_connections or shader_connections[0] != shader_set_name:
        cmds.connectAttr('{}.outColor'.format(shader),
                         '{}.surfaceShader'.format(shader_set_name))
    return shader, shader_set_name


@maya_utils.undo
def nucleus_constraint_transform(name='', parent=None):
    """Creates a Nucleus transform constraint.

    Args:
        name (str): Name of the resulting transform constraint.
        parent (str): Name of the node to parent the constraint under.

    Returns:
        str: The name of the constraint that gets created.
    """
    # Create the constraint
    result = mel.eval('createNConstraint transform 0;')
    if result and len(result):
        shape = result[0]
        constraint = cmds.listRelatives(shape, parent=True, type='transform')[0]
        # Parent the constraint, if applicable
        if parent:
            cmds.parent(constraint, parent)
        # Rename the constraint, if applicable
        if name:
            constraint = cmds.rename(constraint, name)
        logger.info('Created nucleus constraint "{}".'.format(constraint))
        return constraint


@maya_utils.undo
def nucleus_constraint_point_on_surface(name='', parent=None):
    """Creates a Nucleus point on surface constraint.

    Args:
        name (str): Name of the resulting POS constraint.
        parent (str): Name of the node to parent the constraint under.

    Returns:
        str: The name of the constraint that gets created.
    """
    # Create the constraint
    result = mel.eval('createNConstraint pointToSurface 0;')
    if result and len(result):
        shape = result[0]
        constraint = cmds.listRelatives(shape, parent=True, type='transform')[0]
        # Parent the constraint, if applicable
        if parent:
            cmds.parent(constraint, parent)
        # Rename the constraint, if applicable
        if name:
            constraint = cmds.rename(constraint, name)
        logger.info('Created nucleus constraint "{}".'.format(constraint))
        return constraint


@maya_utils.undo
def nucleus_constraint_slide_on_surface(name='', parent=None):
    """Creates a Nucleus slide on surface constraint.

    Args:
        name (str): Name of the resulting SOS constraint.
        parent (str): Name of the node to parent the constraint under.

    Returns:
        str: THe name of the constraint that gets created.
    """
    # Create the constraint
    result = mel.eval('createNConstraint slideOnSurface 0;')
    if result and len(result):
        shape = result[0]
        constraint = cmds.listRelatives(shape, parent=True, type='transform')[0]
        # Parent the constraint, if applicable
        if parent:
            cmds.parent(constraint, parent)
        # Rename the constraint, if applicable
        if name:
            constraint = cmds.rename(constraint, name)
        logger.info('Created nucleus constraint "{}".'.format(constraint))
        return constraint


@maya_utils.undo
def nucleus_constraint_component_to_component(name='', parent=None):
    """Creates a Nucleus component to component constraint.

    Args:
        name (str): Name of the resulting CTC constraint.
        parent (str): Name of the node to parent the constraint under.

    Returns:
        str: THe name of the constraint that gets created.
    """
    # Create the constraint
    result = mel.eval('createNConstraint pointToPoint 0;')
    if result and len(result):
        shape = result[0]
        constraint = cmds.listRelatives(shape, parent=True, type='transform')[0]
        # Parent the constraint, if applicable
        if parent:
            cmds.parent(constraint, parent)
        # Rename the constraint, if applicable
        if name:
            constraint = cmds.rename(constraint, name)
        logger.info('Created nucleus constraint "{}".'.format(constraint))
        return constraint


@maya_utils.undo
def nucleus_constraint_component(name='', parent=None):
    """Creates a Nucleus component constraint.

    Args:
        name (str): Name of the resulting component constraint.
        parent (str): Name of the node to parent the constraint under.

    Returns:
        str: THe name of the constraint that gets created.
    """
    # Get list of top level nodes in the scene already
    pre_objs = cmds.ls(assemblies=True, long=True)
    # Create the constraint (which doesn't return the created node name(s)
    mel.eval('createComponentNConstraint 1 0 0 0;')
    # Derive what nodes have been created
    post_objs = cmds.ls(assemblies=True, long=True)
    result = list(set(post_objs) - set(pre_objs))
    if result and len(result):
        constraint = result[0]
        # Parent the constraint, if applicable
        if parent:
            constraint = cmds.parent(constraint, parent)
        # Rename the constraint, if applicable
        if name:
            constraint = cmds.rename(constraint, name)
        logger.info('Created nucleus constraint "{}".'.format(constraint))
        return constraint
