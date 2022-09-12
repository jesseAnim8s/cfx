"""Maya commands related to cloth simulations."""


# General Imports
try:
    import cpickle as pickle
except ImportError:
    import pickle
from logging import getLogger
from re import sub as re_sub
# Application Imports
from maya import cmds, mel
# Package imports
from cfx.maya.commands import group as maya_group
from cfx.maya import maya_utils


__author__ = 'Jesse Carlson'
__email__ = 'seven6ty@hotmail.com'
__version__ = 'beta'
# Variables
logger = getLogger(__name__)


def disable_connected_rigid_bodies():
    """Used to disable nRigids connected to selected geometry."""
    selection = cmds.ls(selection=True, long=True)
    for selected in selection:
        shapes = cmds.listRelatives(selected, shapes=True, fullPath=True) or []
        for shape in shapes:
            rigid_bodies = cmds.listConnections(shape, type='nRigid')
            for rigid_body in rigid_bodies:
                cmds.setAttr(rigid_body + '.isDynamic', False)


class Cloth(object):

    def __init__(self, prefix, description, nodes):
        """Create & encapsulates a Maya nCloth node.

        Args:
            prefix (str): Prefix string to prefix all new nodes with.
            description (str): Description token to name nodes with.
            nodes (list/tuple): List of node names to turn into cloth objects.
        """
        super(Cloth, self).__init__()
        logger.info('Initializing cloth build.')
        # Store arguments
        self.prefix = prefix
        self.description = description
        self.nodes = nodes
        # Variables
        self.sim_meshes, self.rest_meshes = [], []
        self.input_meshes, self.sculpt_meshes = [], []
        self.ncloth_nodes = []
        self.short_name = None
        self.nucleus = '{}_{}_nucleus'.format(prefix, description)
        self.system_group_name = '{}_{}_grp'.format(prefix, description)
        self.rigid_group_name = '{}_nRigids_grp'.format(self.prefix)
        self.constraints_group_name = '{}_constraints_grp'.format(self.prefix)

    def get_short_name(self, name):
        """Converts long names to short names.

        Args:
            name (str): Node name to use.

        Returns:
            str: The short name of the given node.
        """
        self.short_name = re_sub('^mesh_m_high_', 'sim_', name)
        self.short_name = re_sub('^mesh_m_', '', self.short_name)
        self.short_name = re_sub('_\d+$', '', self.short_name)
        return self.short_name

    def create_dynamics_hierarchy(self):
        """Creates a dynamic group node for each system."""
        logger.info('Creating dynamics hierarchy.')
        for group in (self.rigid_group_name, self.constraints_group_name):
              maya_group.Group(name=group, parent=self.system_group_name).create()

    def create_cloth_group(self, parent=None):
        """Creates a cloth group for the given mesh name.

        Args:
            parent (str): Name of the node to parent the cloth group under.

        Returns:
            str: The name of the group that's been created.
        """
        group_name = '{}_cloth_grp'.format(self.short_name)
        group = maya_group.Group(name=group_name, parent=parent).create()
        return group

    def create_layers(self):
        """Creates all the layers for a cloth setup."""
        logger.info('Creating display layers.')
        # Variables
        output_group = 'geometry_gp'
        output_layer = '{}_{}_output_LYR'.format(self.prefix, self.description)
        dyn_layer = '{}_{}_nDyn_LYR'.format(self.prefix, self.description)
        input_layer = '{}_{}_input_LYR'.format(self.prefix, self.description)
        sim_layer = '{}_{}_sim_LYR'.format(self.prefix, self.description)
        sculpt_layer = '{}_{}_sculpt_LYR'.format(self.prefix, self.description)
        rest_layer = '{}_{}_rest_LYR'.format(self.prefix, self.description)
        # Create layers
        self._display_layer(output_group, output_layer, color=None,
                            visibility=False)
        self._display_layer(self.nucleus, dyn_layer, color=None,
                            visibility=False)
        for ncloth_node in self.ncloth_nodes:
            maya_utils.display_layer(ncloth_node, dyn_layer, color=None,
                                visibility=False)
        for input_mesh in self.input_meshes:
            maya_utils.display_layer(input_mesh, input_layer,
                                color=(0, 0.65, 0.43),
                                visibility=False)
        for sim_mesh in self.sim_meshes:
            maya_utils.display_layer(sim_mesh, sim_layer,
                                color=(0.88, 0.52, 0))
        for sculpt_mesh in self.sculpt_meshes:
            maya_utils.display_layer(sculpt_mesh, sculpt_layer,
                                color=(0.85, 0, 0.36),
                                visibility=False)
        for rest_mesh in self.rest_meshes:
            maya_utils.display_layer(rest_mesh, rest_layer,
                                color=(0.81, 0.81, 0),
                                visibility=False)

    def _display_layer(self, obj, layer_name, color=None, visibility=True):
        """Creates a layer if it doesn't exist & adds the given object to it.

        Args:
            obj (str): The node to add to the layer.
            layer_name (str): The name to give the newly created layer.
            color (list/tuple): RGB color values to use.
            visibility (bool): Controls whether the layer will be visible/invisible.

        Returns:
            str: The name of the layer that was created.
        """
        # Create the display layer, if it doesn't exist already
        if not cmds.objExists(layer_name):
            layer = cmds.createDisplayLayer(obj, name=layer_name,
                                            noRecurse=True)
            cmds.setAttr('{}.visibility'.format(layer), visibility)
            if color:
                cmds.setAttr('{}.color'.format(layer), True)
                cmds.setAttr('{}.overrideRGBColors'.format(layer), True)
                cmds.setAttr('{}.overrideColorRGB'.format(layer), *color)
        # Add the object to the layer, if it already exists
        else:
            # TODO...  Iterate over a list of nodes as well
            layer = cmds.editDisplayLayerMembers(layer_name, obj,
                                                 noRecurse=True)
        return layer

    def _lambert(self, object, name, color):
        """Applies a material to a given node.

        Args:
            object (str): The object to add to the shader group.
            name (str): Name to give the Lambert shader.
            color (list/tuple): The RGB values to set the color to.
        """
        material_name = '{}_MTL'.format(name)
        group_name = '{}_SG'.format(name)

        # TODO: Use the lambert general function instead of this...

        if cmds.objExists(material_name) and cmds.objExists(group_name):
            cmds.sets(object, edit=True, forceElement=group_name)
            return
        elif cmds.objExists(material_name):
            return
        elif cmds.objExists(group_name):
            return
        cmds.shadingNode('lambert', name=material_name, asShader=True)
        cmds.setAttr('{}.color'.format(material_name), *color, type='double3')
        cmds.sets(name=group_name, empty=True, renderable=True,
                  noSurfaceShader=True)
        cmds.connectAttr('{}.outColor'.format(material_name),
                         '{}.surfaceShader'.format(group_name))
        cmds.sets(object, edit=True, forceElement=group_name)

    def create_duplicates(self, mesh, cloth_shape, parent=None, blend=True):
        """Creates duplicate cloth geometry.

        Args:
            mesh (str): Name of the mesh node to duplicate.
            cloth_shape (str): nCloth shape node to attach to.
            parent (str): The object o parent the duplicate under.
            blend (bool): Creates a blendShape connection, if True.
        """
        logger.info('Duplicating cloth geometry, "{}".'.format(mesh))
        # Error check
        if not cmds.objExists(mesh):
            logger.warning(
                'Cloth mesh, "{}", doesn\'t exist for duplication'.format(mesh)
            )
            return
        # Derive names
        sim_name = '{}_{}_sim'.format(self.prefix, self.short_name)
        rest_name = '{}_{}_rest'.format(self.prefix, self.short_name)
        input_name = '{}_{}_input'.format(self.prefix, self.short_name)
        sculpt_name = '{}_{}_sculpt'.format(self.prefix, self.short_name)
        self.sim_meshes.append(sim_name)
        self.rest_meshes.append(rest_name)
        self.input_meshes.append(input_name)
        self.sculpt_meshes.append(sculpt_name)
        names = (sim_name, rest_name, input_name, sculpt_name)
        # Create each group node, if it doesn't already exist
        for name in names:
            dup = cmds.duplicate(mesh, name=name)[0]
            # Parent the group node, if necessary
            if parent and cmds.objExists(parent):
                cmds.parent(dup, parent)
        # Set quadSplit on sim shape nodes
        sim_shapes = cmds.listRelatives(sim_name, shapes=True)
        for shape in sim_shapes:
            if cmds.objExists(shape + '.quadSplit'):
                try:
                    cmds.setAttr(shape + '.quadSplit', 0)
                except RuntimeError:
                    pass
        # Mesh connections
        cmds.connectAttr(
            input_name + '.worldMesh[0]',
            cloth_shape + '.inputMesh',
            force=True
        )
        cmds.connectAttr(
            cloth_shape + '.outputMesh',
            sim_name + '.inMesh'
        )
        cmds.connectAttr(
            rest_name + '.worldMesh[0]',
            cloth_shape + '.restShapeMesh',
            f=True
        )
        if not blend:
            cmds.connectAttr(
                mesh + '.worldMesh[0]',
                input_name + '.inMesh',
                force=True
            )
        else:
            bs = cmds.blendShape(mesh, input_name, origin='world')
            cmds.blendShape(bs, edit=True, weight=[0, 1.0])
        blendshape = cmds.blendShape(
            sim_name,
            sculpt_name,
            name='{}_{}_bsh'.format(self.prefix, self.short_name)
        )
        cmds.blendShape(blendshape, edit=True, weight=[0, 1.0])
        # Create/assign shaders
        self._lambert(input_name, 'clo_input', (0, 0.65, 0.43))
        self._lambert(sim_name, 'clo_sim', (0.78, 0.46, 0))
        self._lambert(sculpt_name, 'clo_sculpt', (0.67, 0, 0.29))
        self._lambert(rest_name, 'clo_rest', (0.62, 0.62, 0))

    def create_ncloth_node(self, name, parent=None):
        """Creates an nCloth node and attaches it to the given nucleus.

        Args:
            name (str): Name of the nCloth node to create.
            parent (str): Name of the node to parent the nCloth under.

        Returns:
            str: The name of the nCloth shape node that's been created.
        """
        logger.info('Creating nCloth node for {}'.format(name))
        # Create nCloth node
        if parent and cmds.objExists(parent):
            transform = cmds.group(name=name, parent=parent, empty=True)
        else:
            transform = cmds.group(name=name, empty=True)
        self.ncloth_nodes.append(transform)
        shape = cmds.createNode('nCloth', name='{}Shape'.format(name),
                                parent=transform)
        # Set nCloth attributes
        cmds.setAttr('{}.active'.format(shape), True)
        cmds.setAttr('{}.localSpaceOutput'.format(shape), 1)
        # Connect nCloth attributes
        cmds.connectAttr('time1.outTime', '{}.currentTime'.format(shape))
        # Connect nCloth node to the nucleus node
        self._connect_dyn_to_nucleus(shape)
        return shape

    def _connect_dyn_to_nucleus(self, dyn_shape_node):
        """Connects a given nCloth node to a nucleus.

        Args:
            dyn_shape_node (str): Name of the shape node to connect.
        """
        obj_attr = '{}.inputActive'.format(self.nucleus)
        index = str(get_next_multi_index(obj_attr))
        cmds.connectAttr('{}.startFrame'.format(self.nucleus),
                         '{}.startFrame'.format(dyn_shape_node))
        cmds.connectAttr('{}.currentState'.format(dyn_shape_node),
                         '{0}[{1}]'.format(obj_attr, index))
        cmds.connectAttr('{}.startState'.format(dyn_shape_node),
                         '{}.inputActiveStart[{}]'.format(self.nucleus, index))
        cmds.connectAttr('{0}.outputObjects[{1}]'.format(self.nucleus, index),
                         '{}.nextState'.format(dyn_shape_node))

    def default_settings(self, cloth):
        """Applies default nCloth settings.

        Args:
            cloth (str): nCloth node to set attributes on.
        """
        cmds.setAttr('{}.thickness'.format(cloth), 0.1)
        cmds.setAttr('{}.damp'.format(cloth), 0.15)
        cmds.setAttr('{}.stretchDamp'.format(cloth), 0.25)
        cmds.setAttr('{}.maxIterations'.format(cloth), 25)
        cmds.setAttr('{}.stretchResistance'.format(cloth), 200)
        cmds.setAttr('{}.bendResistance'.format(cloth), 0.5)
        cmds.setAttr('{}.shearResistance'.format(cloth), 0.1)
        cmds.setAttr('{}.selfCollisionFlag'.format(cloth), 2)
        cmds.setAttr('{}.inputMeshAttract'.format(cloth), 0.5)

    def execute(self):
        """Builds the Nucleus setup."""
        logger.info('Building cloth set up.')
        self.create_dynamics_hierarchy()
        for node in self.nodes:
            if not cmds.objExists(node):
                logger.warning(
                    'Node "{}", does not exist, skipping.'.format(node)
                )
                continue
            self.get_short_name(node)
            cloth_group = self.create_cloth_group(self.system_group_name)
            cloth = self.create_ncloth_node('{}_nCloth'.format(self.short_name),
                                            cloth_group)
            self.default_settings(cloth)
            self.create_duplicates(node, cloth, cloth_group)
        self.create_layers()
