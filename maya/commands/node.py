
# General Imports
from logging import getLogger
try:
    import cpickle as pickle
except:
    import pickle
# Application Imports
from maya import cmds, mel
from cfx import maya_utils


__author__ = 'Jesse Carlson'
__email__ = 'seven6ty@hotmail.com'
__version__ = 'beta'
# Variables
logger = getLogger(__name__)


class Node(object):
    """Python class for acting on Maya nodes."""

    def __init__(self, node):
        """Object-oriented class for Maya nodes.

        Args:
            node (str): Name of the node to act upon.
        """
        super(Node, self).__init__()
        self.node = None
        self.set_node(node)

    def set_node(self, node):
        """Sets the current node to operate on.

        Args:
            node (str): Name of the node to act upon.
        """
        assert (isinstance(node, basestring)),\
            'Argument must be a string.'
        self.node = node

    def exists(self):
        """Checks if the given node exists.

        Returns:
            bool: True if the node exists, False if not.
        """
        if self.node and cmds.objExists(self.node):
            return True
        else:
            self.node = None
            logger.info('Given node does not exist, clearing the internal node name.')
            return False

    def delete(self):
        """Deletes the node, if it exists.

        Returns:
            bool: True if deleted, otherwise False.
        """
        if self.node and cmds.objExists(self.node):
            cmds.delete(self.node)
            return True
        return False

    def full_path(self):
        """Returns the full path for a given node.

        Returns:
            str: The full path name of the current node.
        """
        assert self.exists(), 'Given node could not be found.'
        return cmds.ls(self.node, long=True)[0]

    def short_name(self):
        """Returns the short name, if a full path name is given.

        Returns:
            str: The short path name of the current node.
        """
        assert self.exists(), 'Given node could not be found.'
        return self.node.split('|')[-1]

    def attr_str(self, attribute):
        """Returns a string of the object & attribute name together.

        Args:
            attribute (str): Attribute name to act upon.

        Returns:
            str: Node name & attribute combined, with
                a period between them.
        """
        assert self.exists(), 'Given node could not be found.'
        obj_attr = '.'.join((self.node, attribute))
        if attribute and cmds.objExists(obj_attr):
            return obj_attr

    def set_attr(self, attribute, value):
        """Sets the given attribute

        Args:
            attribute (str): Attribute name.
            value (int/float/str): Value to set the attribute to.

        Returns:
            str: Node name, a period, then the attribute name that was set.
        """
        assert self.exists(), 'Given node could not be found.'
        name = self.attr_str(attribute)
        if cmds.objExists(name):
            try:
                # TODO: Pass additional arguments to the setAttr command
                cmds.setAttr(attribute, value)
                return name
            except RuntimeError:
                logger.error('Could not set {}'.format(name))

    def hide(self):
        """Hides a given node."""
        assert self.exists(), 'Given node could not be found.'
        cmds.hide(self.node)

    def show(self):
        """Un-hides a given node."""
        assert self.exists(), 'Given node could not be found.'
        cmds.showHidden(self.node)

    def children(self):
        """Gets the children of the current node.

        Returns:
            list: List of full path names for all direct children.
        """
        return cmds.listRelatives(self.node, children=True, fullPath=True) or []

    def parent(self):
        """Gets the parent of the given node.

        Returns:
            str/bool: The name of the parent of the currently set node, otherwise False.
        """
        assert self.exists(), 'Given node could not be found.'
        parents = cmds.listRelatives(self.node, parent=True)
        if parents:
            return parents[0]
        return False

    def reparent(self, parent=None):
        """Parents a node under a new parent."""
        assert self.exists(), 'Given node could not be found.'
        assert (parent and cmds.objExists(parent)), \
            'Existent parent must be given.'
        if parent and cmds.objExists(parent):
            cmds.parent(self.node, parent)

    def get_shapes(self):
        """Returns the shape for a given node.

        Returns:
            list: Shape node names of the current node.
        """
        assert self.exists(), 'Given node could not be found.'
        shapes = cmds.listRelatives(self.node, shapes=True)
        return shapes

    def lock(self, attrs=None):
        """Locks given attributes for the current node.

        Args:
            attrs (list/tuple): The string names of the attributes to lock.
        """
        assert self.exists(), 'Given node could not be found.'
        maya_utils.lock_attrs(self.node, attrs)

    def unlock(self, attrs=None):
        """Unlocks a given node.

        Args:
            attrs (list/tuple): The string names of the attributes to unlock.
        """
        assert self.exists(), 'Given node could not be found.'
        maya_utils.unlock_attrs(self.node, attrs)
