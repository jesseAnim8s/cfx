"""Maya commands related to cloth simulations."""


# General Imports
try:
    import cpickle as pickle
except ImportError:
    import pickle
from logging import getLogger
from re import search as re_search
from re import split as re_split
# Application Imports
from maya import cmds, mel
# Package imports
from cfx.maya.commands import group as maya_group
from cfx.maya import maya_utils
from cfx.maya import commands as mc


__author__ = 'Jesse Carlson'
__email__ = 'seven6ty@hotmail.com'
__version__ = 'beta'
# Variables
logger = getLogger(__name__)


class Hair(object):
    """For creating dynamic hairSystem simulation setups in Maya."""

    def __init__(self, prefix, description, groom, surface='', spans=32,
                 yeti_comb_nodes='', yeti_clump_nodes=''):
        """Create & encapsulates a Maya nCloth node.

        Args:
            prefix (str):  The prefix string to append to newly created nodes.
            description (str): Description string to use for hairSystem/nucleus nodes.
            groom (str): The name of the Yeti groom node to set up.
            surface (str): Name of the surface the groom is attached to.
            spans (int): Number of span CVs to create on the output curves.
            yeti_comb_nodes (list/tuple): The name of the Yeti comb nodes to connect.
            yeti_clump_nodes (list/tuple): The name of the Yeti clump nodes to connect.
        """
        super(Hair, self).__init__()
        logger.info('Initializing hair build.')
        # Arguments
        self.prefix = prefix
        self.description = description
        self.groom = groom
        self.surface = surface
        self.spans = spans
        self.comb_nodes = [x.strip() for x in yeti_comb_nodes.split(',')]
        self.clump_nodes = [y.strip() for y in yeti_clump_nodes.split(',')]
        # Variables
        self.auto_created_set = self.groom + 'Shape_strand_set'
        self.curves = []
        self.start_curves, self.rest_curves, self.output_curves = [], [], []
        self.follicles = []
        self.groom_set = None
        self.yeti_node, self.groom_shape = None, None
        self.nucleus, self._nucleus = None, None
        self._hair_system = None
        self.input_curves = None
        self._output_curve_group = None
        self._follicle_group = None
        self._set, self.set = None, None
        self.set_name = 'hair_guide_set'
        # Group names
        self.nucleus = '{}_{}_nucleus'.format(self.prefix, self.description)
        self.nucleus_group = '{}_{}_grp'.format(self.prefix, self.description)
        self.hair_system = '{}_hsys'.format(self.groom)
        self.hair_system_shape = self.hair_system + 'Shape'
        self.system_group_name = '{}_{}_grp'.format(
            self.prefix, self.description
        )
        self.rigid_group_name = '{}_nRigids_grp'.format(self.prefix)
        self.constraints_group_name = '{}_constraints_grp'.format(self.prefix)
        self.follicle_group_name = '{}_{}_follicle_grp'.format(self.prefix,
                                                               self.description)
        self.hair_group = self.groom + '_grp'
        self.input_curves = self.groom + '_input_curves'
        self.output_curve_group = self.groom + '_output_curves'
        # Error check
        if not cmds.objExists(self.groom):
            logger.error('Object does not exist, doing nothing: {}'.format(self.groom))
            return
        # Derive groom shape & transform nodes
        if cmds.nodeType(self.groom) == 'transform':
            groom_shape = cmds.listRelatives(
                self.groom,
                children=True,
                type='pgYetiGroom'
            )
            if groom_shape:
                self.groom_shape = groom_shape[0]
            else:
                logger.error('Please specify a groom node, doing nothing.')
                return
        self.yeti_node = cmds.listConnections(
            self.groom_shape + '.outputData'
        )[0]
        self.yeti_shape = cmds.listRelatives(self.yeti_node, children=True,
                                             type='pgYetiMaya')[0]

    def create_dynamics_hierarchy(self):
        """Creates a dynamic group node for each system."""
        logger.info('Creating dynamics hierarchy.')
        groups = (
            self.rigid_group_name, self.constraints_group_name,
            self.hair_group, self.follicle_group_name,
            self.output_curve_group
        )
        for group in groups:
            maya_group.Group(name=group, parent=self.system_group_name).create()

    def create_hair_system(self):
        """Creates a hairSystem from scratch."""
        # Create hairSystem
        if not cmds.objExists(self.hair_system):
            cmds.createNode('transform', name=self.hair_system,
                            parent=self.system_group_name, skipSelect=True)
            cmds.createNode('hairSystem', name=self.hair_system_shape,
                            parent=self.hair_system, skipSelect=True)
        cmds.setAttr(self.hair_system + '.active', 1)
        cmds.setAttr(self.hair_system_shape + '.clumpWidth', 0.00001)
        cmds.setAttr(self.hair_system_shape + '.hairsPerClump', 1)
        # Connections
        cmds.connectAttr('time1.outTime',
                         self.hair_system_shape + '.currentTime')
        cmds.connectAttr(self.nucleus + '.startFrame',
                         self.hair_system_shape + '.startFrame')
        index = mc.get_next_multi_index(self.nucleus + '.inputActive')
        cmds.connectAttr(self.hair_system_shape + '.currentState',
                         '{0}.inputActive[{1}]'.format(self.nucleus, index))
        index = mc.get_next_multi_index(self.nucleus + '.inputActiveStart')
        cmds.connectAttr(self.hair_system_shape + '.startState',
                         '{0}.inputActiveStart[{1}]'.format(self.nucleus, index))
        index = mc.get_next_multi_index(self.nucleus + '.outputObjects')
        cmds.connectAttr('{0}.outputObjects[{1}]'.format(self.nucleus, index),
                         self.hair_system_shape + '.nextState')

    def replace_nucleus(self):
        """Replaces the newly created nucleus with an existing one."""
        cmds.select(self._hair_system)
        mel.eval('assignNSolver "{}";'.format(self.nucleus))
        cmds.delete(self._nucleus)

    def curves_from_yeti(self):
        """Generates NURBS curves from a Yeti groom."""
        # Convert groom
        cmds.select(self.groom)
        mel.eval('pgYetiConvertGroomToCurves;')
        curves = cmds.sets(self.auto_created_set, query=True)
        # Sort curves by number
        int_numbers = lambda text: int(text) if text.isdigit() else text.lower()
        num_key = lambda key: [int_numbers(x) for x in re_split('([0-9]+)', key)]
        curves = sorted(curves, key=num_key)
        # Rename curves
        for curve in curves:
            num_search = re_search('\d+$', curve)
            if num_search:
                num = int(num_search.group(0)) + 1
                curve_name = self.groom + '_output_curve_' + str(num).zfill(3)
                self.output_curves.append(
                    cmds.rename(curve, curve_name)
                )
        # Re-parent
        cmds.parent(self.output_curves, self.output_curve_group)

    def rebuild_curves(self):
        """Rebuids curves as specified."""
        for curve in self.output_curves:
            cmds.rebuildCurve(
                curve,
                spans=self.spans,
                degree=1,
                endKnots=1,
                keepEndPoints=True,
                constructionHistory=False,
                replaceOriginal=True
            )

    def create_dynamics(self):
        """Creates the hairSystem dynamic setup."""

        # Create hairSystem
        self.create_hair_system()

        for curve in self.output_curves:
            follicle_name = curve.replace('output_curve', 'follicle')
            # TODO...  WTF is this function???
            follicle(curve, self.surface, follicle_name, self.hair_system_shape,
                     parent=self.follicle_group_name)

    def make_curves_dynamic(self):
        """Command to make hair curves dynamic.

        Returns:
            tuple:
                Name of the newly created nucleus node.
                name of the newly created hairSystem node.
                Name of the group of resulting curves
                Name of the group of resulting follicles
        """
        # Get in-scene objects before curve conversion
        pre_assemblies = cmds.ls(assemblies=True)
        pre_hair_systems = cmds.ls(type='hairSystem')

        # Moves first CV of hair to surface
        surface_attach = 0
        # Snap the curve to surface, is surface_attach is 1
        snap_to_surface = 0
        # Exactly match curve positions by making a 1 degree curve
        match_position = 1
        # Create new output curves
        create_out_curves = 1
        # Create PaintFX hair (no)
        create_pfx_hair = 0

        # Create dynamic hairs
        cmds.select(self.output_curves)
        if self.surface:
            cmds.select(self.surface, add=True)
            #surface_attach = 1
        cmd_str = (
            'makeCurvesDynamic 2 '
            '{{"{0}", "{1}", "{2}", "{3}", "{4}"}};'
        ).format(
            surface_attach,
            snap_to_surface,
            match_position,
            create_out_curves,
            create_pfx_hair
        )
        logger.info(cmd_str)
        mel.eval(cmd_str)

        # Derive newly created objects
        post_assemblies = cmds.ls(assemblies=True)
        post_hair_systems = cmds.ls(type='hairSystem')
        new_objs = list(set(post_assemblies) - set(pre_assemblies))
        hair_system_shape = list(
            set(post_hair_systems) - set(pre_hair_systems)
        )[0]
        hair_system = cmds.listRelatives(hair_system_shape, parent=True)[0]
        nucleus = cmds.listConnections(hair_system_shape + '.startFrame',
                                       source=True, type='nucleus')[0]
        groups = list(set(new_objs) - set((nucleus, hair_system)))
        curve_group, follicle_group = None, None
        for group in groups:
            if cmds.listRelatives(group, allDescendents=True, type='follicle'):
                follicle_group = group
            elif cmds.listRelatives(group, allDescendents=True, type='nurbsCurve'):
                curve_group = group

        return nucleus, hair_system, curve_group, follicle_group

    def cleanup_dynamics(self):
        """Parents & renames the newly created Maya dynamic objects."""

        # Rename & parent hair system
        self.hair_system = cmds.rename(
            self._hair_system,
            self.hair_system
        )
        cmds.parent(self.hair_system, self.hair_group)

        # Rename & parent follicle nodes
        follicle_shapes = cmds.listRelatives(self._follicle_group, allDescendents=True,
                                             type='follicle')
        follicles = cmds.listRelatives(follicle_shapes, parent=True)
        for index, follicle in enumerate(follicles):
            num = str(index + 1).zfill(3)
            new_name = self.groom + '_follicle_' + num
            self.follicles.append(
                cmds.rename(follicle, new_name)
            )
            # Set follicle attributes
            follicle_shape = cmds.listRelatives(self.follicles[-1], shapes=True)[0]
            cmds.setAttr(follicle_shape + '.pointLock', 1)
            cmds.setAttr(follicle_shape + '.restPose', 3)
        # Parent follicles and delete old group
        if cmds.objExists(self.follicle_group_name):
            cmds.parent(self.follicles, self.follicle_group_name)
            cmds.delete(self._follicle_group)

        # Rename start curves
        start_curve_shapes = cmds.listRelatives(self.follicles, allDescendents=True,
                                                type='nurbsCurve')
        start_curves = cmds.listRelatives(start_curve_shapes, parent=True)
        for index, curve in enumerate(start_curves):
            num = str(index + 1).zfill(3)
            new_name = self.groom + '_start_curve_' + num
            self.start_curves.append(
                cmds.rename(curve, new_name)
            )

        # Rename & parent output curves
        curve_shapes = cmds.listRelatives(
            self._output_curve_group,
            allDescendents=True,
            type='nurbsCurve'
        )
        curves = cmds.listRelatives(curve_shapes, parent=True)
        self.output_curves = []
        for index, curve in enumerate(curves):
            num = str(index + 1).zfill(3)
            new_name = self.groom + '_output_curve_' + num
            reparented_curve = cmds.parent(curve, self.output_curve_group)
            self.output_curves.append(
                cmds.rename(reparented_curve, new_name)
            )
        cmds.delete(self._output_curve_group)

    def hair_system_defaults(self):
        """Establishes default hair system settings."""
        cmds.setAttr(self.hair_system_shape + '.stretchResistance', 200)
        cmds.setAttr(self.hair_system_shape + '.startCurveAttract', 0.4)
        cmds.setAttr(self.hair_system_shape + '.attractionDamp', 0.2)
        cmds.setAttr(self.hair_system_shape + '.damp', 0.2)
        cmds.setAttr(self.hair_system_shape +
                     '.attractionScale[0].attractionScale_Interp', 2)
        cmds.setAttr(self.hair_system_shape + \
                     '.attractionScale[1].attractionScale_FloatValue', 0)

    def update_set(self):
        """Replaces curve set made natively by Yeti."""
        # Create a new set
        new_set = cmds.sets(self.output_curves, name=self.set_name)
        # Create new connections
        connections = cmds.getAttr(new_set + '.usedBy', size=True)
        cmds.connectAttr('{}.usedBy[{}]'.format(new_set, connections),
                         self.yeti_shape + '.guideSets', nextAvailable=True)
        # Update to get new attributes
        self.yeti_update()
        # Set defaults
        if cmds.objExists(self.set_name + '.maxNumberOfGuideInfluences'):
            cmds.setAttr(self.set_name + '.maxNumberOfGuideInfluences', 1)
        if cmds.objExists(self.set_name + '.stepSize'):
            cmds.setAttr(self.set_name + '.stepSize', 0.05)

    def generate_rest_start_curves(self):
        """Copies output hairs to use as start/rest curves."""
        # Delete curves under follicles:
        follicle_curves = cmds.listRelatives(self.follicles, allDescendents=True,
                                             type='nurbsCurve')
        curves = cmds.listRelatives(follicle_curves, parent=True)
        cmds.delete(curves)
        # Duplicate new rest/start curves
        for index, output_curve in enumerate(self.output_curves):
            start_name = output_curve.replace('_output_', '_start_')
            rest_name = output_curve.replace('_output_', '_rest_')
            start_curve = cmds.duplicate(output_curve, name=start_name)[0]
            rest_curve = cmds.duplicate(output_curve, name=rest_name)[0]
            rest_shape = cmds.listRelatives(rest_curve, shapes=True)[0]
            for crv in (start_curve, rest_curve):
                cmds.parent(crv, self.follicles[index])
            # Connect attributes
            follicle_shapes = cmds.listRelatives(self.follicles[index], shapes=True)
            cmds.connectAttr(start_curve + '.local',
                             follicle_shapes[0] + '.startPosition')
            cmds.connectAttr(start_curve + '.worldMatrix[0]',
                             follicle_shapes[0] + '.startPositionMatrix')
            cmds.hide(start_curve)
            cmds.connectAttr(rest_shape + '.worldSpace[0]',
                             follicle_shapes[0] + '.restPosition')
            cmds.setAttr(follicle_shapes[0] + '.restPose', 3)

    def create_layers(self):
        """Creates all the layers for a cloth setup."""
        logger.info('Creating display layers.')
        # Variables
        output_group = 'geometry_gp'
        yeti_group = ('yeti_grp', 'grp_yeti')
        yeti_layer = 'yeti_layer'
        output_layer = '{}_{}_out_curves_layer'.format(self.prefix, self.description)
        rest_layer = '{}_{}_rest_curves_layer'.format(self.prefix, self.description)
        start_layer = '{}_{}_start_surves_layer'.format(self.prefix, self.description)
        follicle_layer = '{}_{}_follicles_layer'.format(self.prefix, self.description)
        geo_layer = 'output_geometry_layer'
        # Create layers
        maya_utils.display_layer(output_group, geo_layer, visibility=True)
        for follicle in self.follicles:
            maya_utils.display_layer(follicle, follicle_layer, visibility=False)
        for curve in self.rest_curves:
            maya_utils.display_layer(curve, rest_layer, color=(0.66, 0.55, 0),
                                visibility=False)
        for curve in self.start_curves:
            maya_utils.display_layer(curve, start_layer, color=(0, 0.65, 0.43),
                                visibility=False)
        for curve in self.output_curves:
            maya_utils.display_layer(curve, output_layer, color=(0.84, 0.5, 0.43),
                                visibility=True)
        for group in yeti_group:
            if cmds.objExists(group):
                maya_utils.display_layer(group, yeti_layer, color=None,
                                    visibility=True)

    def reference_object(self):
        """Gets a groom's reference object, and creates one if it doesn't exist.

        Returns:
            list: List of associated reference meshes.
        """
        # Find existing reference object(s)
        ref_meshes = []
        meshes = cmds.listConnections(self.groom_shape + '.inputGeometry')
        for mesh in meshes:
            ref_meshes.append(cmds.listConnections(mesh + '.referenceObject'))

        # Create reference object, if need be
        if not ref_meshes:
            cmds.select(self.surface)
            logger.info('Creating Yeti texture reference object...')
            cmds.CreateTextureReferenceObject()
            ref_obj = cmds.ls(selection=True, long=True)[0]
            cmds.hide(ref_obj)
            yeti_group = ('yeti_grp', 'grp_yeti')
            for group in yeti_group:
                if cmds.objExists(group):
                    cmds.parent(ref_obj, group)
            logger.info('    Done creating Yeti texture reference object.')
        else:
            logger.info(
                'Texture reference object(s) already exist: {}'.format(
                    ref_meshes
                )
            )
        return ref_meshes

    def yeti_update(self):
        """Updates and redraws the Yeti graph."""
        # Update Maya viewport and attributeEditor
        mel.eval("refreshCustomTemplate")
        cmds.refresh(f=True)
        #mel.eval("updateAE %s" % set)
        # Error check that Yeti plug-in is available
        if not maya_utils.load_plugin(yeti_plugin_name):
            error_str = 'Could not load Yeti plug-in, skipping relevant steps.'
            logger.error(error_str)
            return False
        cmds.select(self.yeti_shape)
        mel.eval('pgYetiUpdateAE;')
        mel.eval('pgYetiMayaUI - graphEditorSelectionChangedCB;')

    def create_yeti_node(self, node_type, yeti_shape):
        """Ensures that a new Yeti node is created.

        Args:
            node_type (str): Yeti node type to create.
            yeti_shape (str): Name of the Yeti shape node to use.

        Returns:
            str: The newly created Yeti node name.
        """
        ls_nodes = 'pgYetiGraph -listNodes "{0}";'
        create_node = 'pgYetiGraph -type "{0}" -create "{1}";'
        existing_nodes = mel.eval(ls_nodes.format(yeti_shape))
        for num in range(99):
            logger.info(create_node.format(node_type, yeti_shape))
            new_node = mel.eval(create_node.format(node_type, yeti_shape))
            if new_node not in existing_nodes:
                return new_node

    def yeti_defaults(self):
        """Sets default Yeti rest pose.
        """
        # Error check that Yeti plug-in is available
        if not maya_utils.load_plugin(yeti_plugin_name):
            error_str = 'Could not load Yeti plug-in, skipping relevant steps.'
            logger.error(error_str)
            return

        # Add Yeti guide set, if necessary
        guide_sets = cmds.listConnections(self.yeti_shape + '.guideSets',
                                          source=True)
        if self.set_name not in guide_sets:
            logger.info('Adding guide set to Yeti node...')
            _cmd = 'pgYetiAddGuideSet("{}", "{}");'
            mel.eval(_cmd.format(self.set_name, self.yeti_shape))
            logger.info('    Done adding guide set to Yeti node!')

        # Create reference object, if one doesn't already exist
        self.reference_object()

        # Save Yeti rest poses
        logger.info('Setting guide rest position...')
        cmds.select(self.groom_set, self.yeti_node)
        mel.eval('pgYetiCommand -saveGuidesRestPosition;')
        logger.info('    Done setting guide rest position!')
        logger.info('Setting Yeti groom rest pose...')
        cmds.select(self.groom)
        mel.eval('pgYetiSaveGroomRestPoseOnSelected;')
        logger.info('    Done setting Yeti groom rest pose!')

        # Update Yeti, to ensure attributes get generated before setting
        self.yeti_update()

        # Set attributes
        missing_attrs = []
        obj_attrs = [
            self.yeti_shape + '.fileMode',
            self.set_name + '.maxNumberOfGuideInfluences',
            self.set_name + '.stepSize'
        ]
        values = [0, 1, 0.05]
        curve_shapes = cmds.listRelatives(self.output_curves, shapes=True)
        for curve_shape in curve_shapes:
            for attr in ('baseAttraction', 'tipAttraction'):
                obj_attrs.append('.'.join((curve_shape, attr)))
                values.append(1.0)
        for obj_attr, value in zip(obj_attrs, values):
            if cmds.objExists(obj_attr):
                cmds.setAttr(obj_attr, value)
            else:
                missing_attrs.append(obj_attr)
        if missing_attrs:
            logger.warning('Expected Yeti attributes do not exist:')
            for attr in missing_attrs:
                logger.warning('\t' + attr)

    def connect_yeti_graph(self):
        """Hooks up the dynamic curves to the Yeti groom."""
        # Error check that Yeti plug-in is available
        if not maya_utils.load_plugin(yeti_plugin_name):
            error_str = ('Could not load Yeti plug-in, '
                         'skipping relevant steps.')
            logger.error(error_str)
            return False

        # Get Yeti nodes
        ls_nodes = 'pgYetiGraph -listNodes {0};'
        existing_nodes = mel.eval(ls_nodes.format(self.yeti_shape))
        importers = mel.eval('pgYetiGraph -listNodes '
                             '-type "import" ' + self.yeti_shape)

        # Find the importer for the surface geometry
        surface_importer, groom_importer = None, None
        for importer in importers:
            _geo = ('pgYetiGraph -node "{}" -param "geometry" '
                    '-getParamValue {};')
            _type = ('pgYetiGraph -node "{}" -param "type" '
                     '-getParamValue {};')
            geo = mel.eval(_geo.format(importer, self.yeti_shape))
            type = mel.eval(_type.format(importer, self.yeti_shape))
            if geo in (self.surface, self.surface + 'Shape') \
                    and not surface_importer \
                    and type == 0:
                surface_importer = importer
            elif geo in (self.groom, self.groom_shape) \
                    and not groom_importer \
                    and type == 1:
                groom_importer = importer

        # Create Yeti Graph Nodes
        cmds.select(self.yeti_shape)
        import_guides = self.create_yeti_node('import', self.yeti_shape)
        convert_s2f = self.create_yeti_node('convert', self.yeti_shape)
        guide = self.create_yeti_node('guide', self.yeti_shape)
        blend_guides = self.create_yeti_node('blend', self.yeti_shape)
        convert_f2s = self.create_yeti_node('convert', self.yeti_shape)
        self.yeti_update()

        # Set Parameters
        _cmd = ('pgYetiGraph -node "{0}" -param "{1}" '
                '-setParamValue{2} {3} "{4}";')
        mel.eval(
            _cmd.format(import_guides, 'type', 'Scalar', 2, self.yeti_shape)
        )
        mel.eval(
            _cmd.format(
                import_guides, 'geometry', 'String',
                '"' + self.set_name + '"', self.yeti_shape
            )
        )
        mel.eval(_cmd.format(blend_guides, 'blend', 'Scalar', 1, self.yeti_shape))
        mel.eval(
            _cmd.format(convert_f2s, 'conversion', 'Scalar', 1, self.yeti_shape)
        )
        self.yeti_update()

        # Connect Nodes
        _cmd = 'pgYetiGraph -node "{}" -connect "{}" {} {}'
        mel.eval(_cmd.format(import_guides, guide, 1, self.yeti_shape))
        mel.eval(_cmd.format(convert_s2f, guide, 0, self.yeti_shape))
        mel.eval(_cmd.format(convert_s2f, blend_guides, 0, self.yeti_shape))
        mel.eval(_cmd.format(guide, blend_guides, 1, self.yeti_shape))
        mel.eval(_cmd.format(blend_guides, convert_f2s, 0, self.yeti_shape))
        if surface_importer:
            mel.eval(
                _cmd.format(surface_importer, convert_s2f, 1, self.yeti_shape)
            )
            mel.eval(
                _cmd.format(
                    surface_importer, convert_f2s, 1, self.yeti_shape
                )
            )
        if groom_importer:
            mel.eval(
                _cmd.format(groom_importer, convert_s2f, 0, self.yeti_shape)
            )
        # Connect to existing graph nodes
        for node in self.comb_nodes:
            if node and node in existing_nodes:
                mel.eval(_cmd.format(convert_f2s, node, 1, self.yeti_shape))
        for node in self.clump_nodes:
            if node and node in existing_nodes:
                mel.eval(_cmd.format(blend_guides, node, 1, self.yeti_shape))
        self.yeti_update()

        # Rename Nodes
        _cmd = 'pgYetiGraph -node "{}" -rename "{}" "{}";'
        mel.eval(_cmd.format(import_guides, 'import_guides', self.yeti_shape))
        mel.eval(_cmd.format(convert_s2f, 'guide_s2f', self.yeti_shape))
        mel.eval(_cmd.format(guide, 'guide_curves', self.yeti_shape))
        mel.eval(_cmd.format(blend_guides, 'guides_blend', self.yeti_shape))
        mel.eval(_cmd.format(convert_f2s, 'guide_f2s', self.yeti_shape))
        self.yeti_update()

    def execute(self):
        """Builds the Nucleus setup."""
        if not self.groom_shape:
            logger.error('Please specify a groom node, doing nothing.')
            return
        logger.info('Building hair set up.')
        # Build hierarchies
        self.create_dynamics_hierarchy()
        # Derive curves from Yeti groom
        self.curves_from_yeti()
        # Rebuild the curves
        self.rebuild_curves()
        # Create dynamic hair setup
        results = dyn_hair(self.surface, self.output_curves, self.hair_system, self.nucleus)
        self.follicles = results[0]
        self.curves = results[1]
        self.start_curves = results[2]
        self.rest_curves = results[3]
        self.nucleus = results[4]
        self.hair_system = results[5]
        cmds.parent(self.hair_system, self.system_group_name)
        cmds.parent(self.follicles, self.follicle_group_name)
        cmds.parent(self.output_curves, self.output_curve_group)
        self.hair_system_defaults()
        # Create layers
        self.create_layers()
        # Dynamics clean up
        self.update_set()
        self.yeti_defaults()
        self.connect_yeti_graph()
