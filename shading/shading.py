'''
Created on 7 jun. 2019

@author: jcquesada
'''
import maya.cmds as cmds

def __get_shading_groups_from_shape(shape_name):
    """
    Comment 1:
    ----------
        This method replaces "_get_materials_from_shape".
        Instead of returning the material (i.e.:"blinn1"), we return
        the Shading Group (i.e: "blinn1SG") which gathers more information
        notably the faces that have applied a current material.
        That is easy to ask with "__get_material_from_shading_group"
        
    Comment 2:
    ----------
        Replaced the old cmds.hyperShader command for dealing with materials
        and shading networks because it is not available in maya's batch mode.
        We use cmds.sets() instead and listConnections.
        
    """
    #===========================================================================
    # we get the shape_name's long path like "|cesped|cespedShape"
    #===========================================================================
    shape_name_long_name = cmds.ls(shape_name, objectsOnly=True,dagObjects=True, shape_names=True)
    
    #===========================================================================
    # shading engines (Shading Groups) like "blinn1SG"..etc
    #===========================================================================
    shading_engines = cmds.listConnections(shape_name_long_name, type='shadingEngine')
    if not shading_engines:
        return []
    
    #===========================================================================
    # avoid duplicates in the list
    #===========================================================================
    shading_engines = list(set(shading_engines))
    
    return shading_engines

def __get_materials_from_shading_groups( shading_groups ):
    """
    Description:
    ----------
        Given a shading group (i.e: "blinn1SG") we extract the material 
        (i.e.: "blinn1") in case we need it somewhere (currently it is not used)
        We have replaced the material name in the data return by the util with
        the material shading group instead because it gives more information
    
    """
    node_connections = cmds.listConnections( shading_groups )
    materials = cmds.ls(node_connections, materials = True)
    return materials

def __get_filenodes_from_shape(shape_name):
    """
        Description:
        ------------
        
            Since a shape can have multiple materials applied and each material can have
            multiple <file> nodes each with one texture we return a dictionary of the shaders
            and file nodes that this shape node has.
            
            Returns:
                - materials_with_textures (dict): <shader_name> and list of <file> nodes
    """
    shading_groups = __get_shading_groups_from_shape( shape_name )
    shaders = __get_materials_from_shading_groups(shading_groups)
    
    materials_with_textures = {}
    for shader in shaders:
        file_nodes = cmds.listConnections(shader, type='file')
        materials_with_textures[shader] = file_nodes
        
    return materials_with_textures

def __get_shading_group_from_material(material_name):
    """
        Description:
        ------------
            Given a material name we retrieve its shading group.
            If it doesnt exist, it just creates one by default
    """
    material_outColor = '{material}.outColor'.format(material=material_name)
    shading_group = cmds.listConnections(material_outColor, destination=True, source=False, exactType=True, type='shadingEngine')
    if not shading_group:
        shading_group = cmds.sets(name='{0}SG'.format(material_name),
                                  empty=True,
                                  renderable=True,
                                  noSurfaceShader=True)
    else:
        shading_group = shading_group[0]
    return shading_group

def __connect_material_with_objects(objects, material_name):
    """
        Description:
        ----------
            Apply material to objects using cmds.sets instead of cmds.hyperShade, so
            that it works in mayapy standalone (maya batch) for publishing in farm.
            
            (1) retrieve Shading Group
            (2) connect .outColor to .surfaceShader
            (3) force shading group to objects
    """
    shading_group = __get_shading_group_from_material(material_name)
    
    material_outColor = '{material}.outColor'.format(material=material_name)
    sg_surfaceShader = '{sg}.surfaceShader'.format(sg=shading_group)
    if not cmds.isConnected(material_outColor, sg_surfaceShader):
        #=======================================================================
        # if connection already exists and we try to redo the connection
        # we get a RuntimeException and the update shaders component process
        # fails. So we only connect if a previous connection doesnt exist
        #=======================================================================
        cmds.connectAttr(material_outColor, sg_surfaceShader)
    cmds.sets(clear=shading_group)
    cmds.sets(objects, e=True, forceElement=shading_group)    
    return True
