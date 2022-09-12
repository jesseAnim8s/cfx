"""Tools for creating Maya groups, & encapsulating them in a Python class."""

# General Imports
try:
    import cpickle as pickle
except:
    import pickle
# Application Imports
from maya import cmds, mel
# Package Imports
from cfx.maya.commands import node as maya_node


__author__ = 'Jesse Carlson'
__email__ = 'seven6ty@hotmail.com'
__version__ = 'beta'
# Variables
logger = getLogger(__name__)


class Group(maya_node.Node):

    def __init__(self, name, nodes=None, parent=None,
                 lock=True, visibility=True):
        """Object-oriented class for creating Maya nodes.

        Args:
            name (str): Name of the newly created group node.
            nodes (list/tuple): List of nodes to group.
            parent (str): Name of the node to parent the group under.
            lock (bool): If True, locks the t/r/s channels of the group.
            visibility (bool): Makes resulting group visible/invisible.
        """
        super(Group, self).__init__(name)
        self.name = name
        self.nodes = nodes
        self.parent = parent
        self.lock_attrs = lock
        self.viz = visibility

    def create(self):
        """Creates the group node.

        Returns:
            str: The name of the group that got created.
        """
        group = None

        # Create group
        if not cmds.objExists(self.name):
            if not self.nodes and not self.parent:
                group = cmds.group(
                    name=self.name, world=True, empty=True
                )
            elif not self.nodes and self.parent:
                group = cmds.group(
                    name=self.name, parent=self.parent, empty=True
                )
            elif self.nodes and self.parent:
                group = cmds.group(
                    self.nodes, name=self.name, parent=self.parent
                )
            elif self.nodes and not self.parent:
                group = cmds.group(
                    self.nodes, name=self.name, world=True
                )
            if group:
                logger.info('Created group "{}"'.format(group))
        else:
            group = self.name

        # Lock group attributes, if specified
        if group and self.lock_attrs:
            self.lock()

        # Hide the group, if specified
        if group and not self.viz:
            self.hide()

        return group
