#
#    MakeMhc2 - Utility for making mhc2 meshes.
#    Like MakeClothes but slightly newer
#    Copyright (C) Thomas Larsson 2014
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

bl_info = {
    "name": "Make MHC2",
    "author": "Thomas Larsson",
    "version": (0,10),
    "blender": (2,7,1),
    "location": "View3D > Properties > Make MH clothes",
    "description": "Make clothes and UVs for MHX2 characters",
    "warning": "",
    'wiki_url': "",
    "category": "MakeHuman"}


if "bpy" in locals():
    print("Reloading main v %d.%d" % bl_info["version"])
    import imp
    imp.reload(maketarget)
    imp.reload(mc)
    imp.reload(error)
    imp.reload(save_json)
    imp.reload(objects)
    imp.reload(hair)
    imp.reload(write)
    imp.reload(materials)
    imp.reload(main)
    imp.reload(project)
else:
    print("Loading main v %d.%d" % bl_info["version"])
    import bpy
    import os
    from bpy.props import *
    import maketarget
    from .error import MHError, handleMHError, initWarnings, handleWarnings
    from maketarget.utils import drawFileCheck
    from makeclothes import mc
    from . import save_json
    from . import objects
    from . import hair
    from . import write
    from . import materials
    from . import main
    from makeclothes import project


def setObjectMode(context):
    if context.object:
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            return


def invokeWithFileCheck(self, context, ftypes):
    try:
        ob = main.getMhc2(context)
        scn = context.scene
        for ftype in ftypes:
            (outpath, outfile) = mc.getFileName(ob, scn.MHCDir, ftype)
            filepath = os.path.join(outpath, outfile)
            if os.path.exists(filepath):
                break
        return maketarget.utils.invokeWithFileCheck(self, context, filepath)
    except MHError:
        handleMHError(context)
        return {'FINISHED'}

#
#    class MakeMhc2Panel(bpy.types.Panel):
#


def inset(layout):
    split = layout.split(0.05)
    split.label("")
    return split.column()


class MakeMhc2Panel(bpy.types.Panel):
    bl_label = "Make Mhc2 version %d.%d" % bl_info["version"]
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "MakeMhc2"

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        ob = context.object

        #layout.operator("mhc2.snap_selected_verts")

        layout.prop(scn, "MHCBodyType", text="Type")
        layout.operator("mhc2.load_human")

        if not (ob and ob.type == 'MESH'):
            return

        layout.separator()
        row = layout.row()
        row.label("Mesh Type:")
        if ob and ob.MhHuman:
            row.operator("mhc2.set_human", text="Human").isHuman = False
            layout.separator()
            layout.operator("mhc2.auto_vertex_groups", text="Create Vertex Groups From Selection")
        else:
            row.operator("mhc2.set_human", text="Proxy").isHuman = True
            layout.separator()
            layout.operator("mhc2.auto_vertex_groups")

        layout.separator()
        layout.operator("mhc2.make_clothes")
        layout.separator()
        layout.operator("mhc2.test_clothes")
        layout.separator()


class SelectionPanel(bpy.types.Panel):
    bl_label = "Selection"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "MakeMhc2"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        props = layout.operator("mhc2.select_human_part", text="Select Body")
        props.btype = 'Body'

        for helper in ["Tights", "Skirt", "Coat", "Hair", "Joints"]:
            props = layout.operator("mhc2.select_human_part", text="Select %s" % helper)
            props.btype = 'Helpers'
            props.htype = helper


class MaterialsPanel(bpy.types.Panel):
    bl_label = "Materials"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "MakeMhc2"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.operator("mhc2.export_material")
        layout.separator()


class ProjectPanel(bpy.types.Panel):
    bl_label = "Project"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "MakeMhc2"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        layout.operator("mhc2.create_seam_object")
        layout.operator("mhc2.auto_seams")
        layout.operator("mhc2.project_uvs")
        layout.operator("mhc2.reexport_files")


class ZDepthPanel(bpy.types.Panel):
    bl_label = "Z Depth"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "MakeMhc2"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        layout.prop(scn, "MHCZDepthName")
        layout.operator("mhc2.set_zdepth")
        layout.prop(scn, "MHCZDepth")


class BoundaryPanel(bpy.types.Panel):
    bl_label = "Boundary"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "MakeMhc2"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        layout.prop(scn, "MHCUseShearing")
        layout.prop(scn, "MHCUseBoundaryMirror")
        layout.separator()
        layout.prop(scn, "MHCBodyPart")
        vnums = main.getBodyPartVerts(scn)
        self.drawXYZ(vnums[0], "X", layout)
        self.drawXYZ(vnums[1], "Y", layout)
        self.drawXYZ(vnums[2], "Z", layout)
        layout.operator("mhc2.examine_boundary")

        layout.separator()
        layout.label("Custom Boundary")
        row = layout.row()
        row.prop(scn, "MHCCustomX1")
        row.prop(scn, "MHCCustomX2")
        row = layout.row()
        row.prop(scn, "MHCCustomY1")
        row.prop(scn, "MHCCustomY2")
        row = layout.row()
        row.prop(scn, "MHCCustomZ1")
        row.prop(scn, "MHCCustomZ2")
        layout.separator()
        layout.operator("mhc2.print_vnums")
        layout.separator()

    def drawXYZ(self, pair, name, layout):
        m,n = pair
        row = layout.row()
        row.label("%s1:   %d" % (name,m))
        row.label("%s2:   %d" % (name,n))


class SettingsPanel(bpy.types.Panel):
    bl_label = "Settings"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "MakeMhc2"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        layout.operator("mhc2.factory_settings").prefix = "MHC"
        layout.operator("mhc2.read_settings").tool = "make_clothes"
        props = layout.operator("mhc2.save_settings")
        props.tool = "make_clothes"
        props.prefix = "MHC"
        layout.label("Output Directory")
        layout.prop(scn, "MHCDir", text="")
        layout.separator()


class LicencePanel(bpy.types.Panel):
    bl_label = "Licence"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"
    bl_category = "MakeMhc2"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        layout.prop(scn, "MHCAuthor")
        layout.prop(scn, "MHCLicense")
        layout.prop(scn, "MHCHomePage")
        layout.label("Tags")
        layout.prop(scn, "MHCTag1")
        layout.prop(scn, "MHCTag2")
        layout.prop(scn, "MHCTag3")
        layout.prop(scn, "MHCTag4")
        layout.prop(scn, "MHCTag5")
        layout.separator()


#----------------------------------------------------------
#   Settings buttons
#----------------------------------------------------------

class OBJECT_OT_FactorySettingsButton(bpy.types.Operator):
    bl_idname = "mhc2.factory_settings"
    bl_label = "Restore Factory Settings"

    prefix = StringProperty()

    def execute(self, context):
        maketarget.settings.restoreFactorySettings(context, self.prefix)
        return{'FINISHED'}


class OBJECT_OT_SaveSettingsButton(bpy.types.Operator):
    bl_idname = "mhc2.save_settings"
    bl_label = "Save Settings"

    tool = StringProperty()
    prefix = StringProperty()

    def execute(self, context):
        maketarget.settings.saveDefaultSettings(context, self.tool, self.prefix)
        return{'FINISHED'}


class OBJECT_OT_ReadSettingsButton(bpy.types.Operator):
    bl_idname = "mhc2.read_settings"
    bl_label = "Read Settings"

    tool = StringProperty()

    def execute(self, context):
        maketarget.settings.readDefaultSettings(context, self.tool)
        return{'FINISHED'}

#----------------------------------------------------------
#
#----------------------------------------------------------
#
#    class OBJECT_OT_SnapSelectedVertsButton(bpy.types.Operator):
#

class OBJECT_OT_SnapSelectedVertsButton(bpy.types.Operator):
    bl_idname = "mhc2.snap_selected_verts"
    bl_label = "Snap Selected"
    bl_options = {'UNDO'}

    def execute(self, context):
        setObjectMode(context)
        main.snapSelectedVerts(context)
        return{'FINISHED'}

#
#    class OBJECT_OT_MakeMhc2Button(bpy.types.Operator):
#

class OBJECT_OT_MakeMhc2Button(bpy.types.Operator):
    bl_idname = "mhc2.make_clothes"
    bl_label = "Make Mhc2"
    bl_options = {'UNDO'}

    filepath = StringProperty(default="")

    def execute(self, context):
        from .main import makeMhc2
        from .materials import writeMaterial
        from .write import buildMhc2, writeMhc2, exportObjFile

        setObjectMode(context)
        scn = context.scene
        try:
            initWarnings()
            hum,pxy,data = makeMhc2(context, True)
            if True:
                buildMhc2(context, hum, pxy, data)
            else:
                matfile = writeMaterial(pxy, scn.MHCDir)
                writeMhc2(context, hum, pxy, data, matfile)
                exportObjFile(context)
            handleWarnings()
        except MHError:
            handleMHError(context)
        return{'FINISHED'}

    def invoke(self, context, event):
        return invokeWithFileCheck(self, context, ["mhc2", "obj"])

    def draw(self, context):
        drawFileCheck(self)


class OBJECT_OT_ExportMaterialButton(bpy.types.Operator):
    bl_idname = "mhc2.export_material"
    bl_label = "Export Material Only"
    bl_options = {'UNDO'}

    filepath = StringProperty(default="")

    def execute(self, context):
        setObjectMode(context)
        try:
            matfile = materials.writeMaterial(context.object, context.scene.MHCDir)
            print("Exported \"%s\"" % matfile)
        except MHError:
            handleMHError(context)
        return{'FINISHED'}

    def invoke(self, context, event):
        return invokeWithFileCheck(self, context, ["mhmat"])

    def draw(self, context):
        drawFileCheck(self)

#
#   class OBJECT_OT_CopyVertLocsButton(bpy.types.Operator):
#

class OBJECT_OT_CopyVertLocsButton(bpy.types.Operator):
    bl_idname = "mhc2.copy_vert_locs"
    bl_label = "Copy Vertex Locations"
    bl_options = {'UNDO'}

    def execute(self, context):
        setObjectMode(context)
        src = context.object
        for trg in context.scene.objects:
            if trg != src and trg.select and trg.type == 'MESH':
                print("Copy vertex locations from %s to %s" % (src.name, trg.name))
                for n,sv in enumerate(src.data.vertices):
                    tv = trg.data.vertices[n]
                    tv.co = sv.co
                print("Vertex locations copied")
        return{'FINISHED'}


#
#   class OBJECT_OT_ExportBaseUvsPyButton(bpy.types.Operator):
#   class OBJECT_OT_SplitHumanButton(bpy.types.Operator):
#

class OBJECT_OT_ExportBaseUvsPyButton(bpy.types.Operator):
    bl_idname = "mhc2.export_base_uvs_py"
    bl_label = "Export Base UV Py File"
    bl_options = {'UNDO'}

    def execute(self, context):
        setObjectMode(context)
        try:
            main.exportBaseUvsPy(context)
        except MHError:
            handleMHError(context)
        return{'FINISHED'}

class OBJECT_OT_SelectHelpersButton(bpy.types.Operator):
    bl_idname = "mhc2.select_helpers"
    bl_label = "Select Helpers"
    bl_options = {'UNDO'}

    def execute(self, context):
        setObjectMode(context)
        try:
            main.selectHelpers(context)
        except MHError:
            handleMHError(context)
        return{'FINISHED'}

#
#    class OBJECT_OT_MakeHumanButton(bpy.types.Operator):
#

class OBJECT_OT_MakeHumanButton(bpy.types.Operator):
    bl_idname = "mhc2.set_human"
    bl_label = "Make Human"
    bl_options = {'UNDO'}
    isHuman = BoolProperty()

    def execute(self, context):
        setObjectMode(context)
        try:
            ob = context.object
            if self.isHuman:
                nverts = len(ob.data.vertices)
                okVerts = main.getLastVertices()
                if nverts in okVerts:
                    ob.MhHuman = True
                else:
                    raise MHError(
                        "Illegal number of vertices: %d\n" % nverts +
                        "An MakeHuman human must have\n" +
                        "".join(["  %d\n" % n for n in okVerts]) +
                        "vertices"
                        )
            else:
                ob.MhHuman = False
            print("Object %s: Human = %s" % (ob.name, ob.MhHuman))
        except MHError:
            handleMHError(context)
        return{'FINISHED'}

#
#    class OBJECT_OT_LoadHumanButton(bpy.types.Operator):
#

class OBJECT_OT_LoadHumanButton(bpy.types.Operator):
    bl_idname = "mhc2.load_human"
    bl_label = "Load Human Mesh"
    bl_options = {'UNDO'}
    helpers = BoolProperty()

    def execute(self, context):
        setObjectMode(context)
        try:
            main.loadHuman(context)
        except MHError:
            handleMHError(context)
        return{'FINISHED'}

#
#    class OBJECT_OT_ExamineBoundaryButton(bpy.types.Operator):
#

class OBJECT_OT_ExamineBoundaryButton(bpy.types.Operator):
    bl_idname = "mhc2.examine_boundary"
    bl_label = "Examine Boundary"
    bl_options = {'UNDO'}

    @classmethod
    def poll(self, context):
        return context.object and context.object.MhHuman

    def execute(self, context):
        setObjectMode(context)
        try:
            main.examineBoundary(context.object, context.scene)
        except MHError:
            handleMHError(context)
        return{'FINISHED'}

#
#    class OBJECT_OT_SetZDepthButton(bpy.types.Operator):
#

class OBJECT_OT_SetZDepthButton(bpy.types.Operator):
    bl_idname = "mhc2.set_zdepth"
    bl_label = "Set Z Depth"
    bl_options = {'UNDO'}

    def execute(self, context):
        setObjectMode(context)
        try:
            main.setZDepth(context.scene)
        except MHError:
            handleMHError(context)
        return{'FINISHED'}

#
#    class VIEW3D_OT_SelectHumanPartButton(bpy.types.Operator):
#

class VIEW3D_OT_SelectHumanPartButton(bpy.types.Operator):
    bl_idname = "mhc2.select_human_part"
    bl_label = "Select Human Part"
    bl_options = {'UNDO'}

    btype = StringProperty()
    htype = StringProperty()

    @classmethod
    def poll(self, context):
        return context.object and context.object.MhHuman

    def execute(self, context):
        setObjectMode(context)
        try:
            main.selectHumanPart(context.object, self.btype, self.htype)
        except MHError:
            handleMHError(context)
        return{'FINISHED'}

#
#    class VIEW3D_OT_PrintVnumsButton(bpy.types.Operator):
#

class VIEW3D_OT_PrintVnumsButton(bpy.types.Operator):
    bl_idname = "mhc2.print_vnums"
    bl_label = "Print Vertex Numbers"
    bl_options = {'UNDO'}

    def execute(self, context):
        setObjectMode(context)
        try:
            main.printVertNums(context)
        except MHError:
            handleMHError(context)
        return{'FINISHED'}

#
#    class VIEW3D_OT_DeleteHelpersButton(bpy.types.Operator):
#

class VIEW3D_OT_DeleteHelpersButton(bpy.types.Operator):
    bl_idname = "mhc2.delete_helpers"
    bl_label = "Delete Helpers Until Above"
    bl_options = {'UNDO'}
    answer = StringProperty()

    def execute(self, context):
        setObjectMode(context)
        ob = context.object
        scn = context.scene
        if main.isHuman(ob):
            main.deleteHelpers(context)
        return{'FINISHED'}

#
#   class VIEW3D_OT_AutoVertexGroupsButton(bpy.types.Operator):
#

class VIEW3D_OT_AutoVertexGroupsButton(bpy.types.Operator):
    bl_idname = "mhc2.auto_vertex_groups"
    bl_label = "Create Vertex Groups"
    bl_options = {'UNDO'}

    def execute(self, context):
        setObjectMode(context)
        try:
            main.autoVertexGroups(context.object, 'Selected', None)
        except MHError:
            handleMHError(context)
        return{'FINISHED'}

#
#    class OBJECT_OT_RecoverSeamsButton(bpy.types.Operator):
#

class OBJECT_OT_CreateSeamObjectButton(bpy.types.Operator):
    bl_idname = "mhc2.create_seam_object"
    bl_label = "Recover Seams"
    bl_options = {'UNDO'}

    def execute(self, context):
        setObjectMode(context)
        try:
            project.createSeamObject(context)
        except MHError:
            handleMHError(context)
        return{'FINISHED'}


class OBJECT_OT_AutoSeamsButton(bpy.types.Operator):
    bl_idname = "mhc2.auto_seams"
    bl_label = "Auto Seams"
    bl_options = {'UNDO'}

    def execute(self, context):
        setObjectMode(context)
        try:
            project.autoSeams(context)
        except MHError:
            handleMHError(context)
        return{'FINISHED'}

#
#    class OBJECT_OT_ProjectUVsButton(bpy.types.Operator):
#

class OBJECT_OT_ProjectUVsButton(bpy.types.Operator):
    bl_idname = "mhc2.project_uvs"
    bl_label = "Project UVs"
    bl_options = {'UNDO'}

    def execute(self, context):
        from .main import getObjectPair
        setObjectMode(context)
        try:
            (human, clothing) = getObjectPair(context)
            project.unwrapObject(clothing, context)
            project.projectUVs(human, clothing, context)
            print("UVs projected")
        except MHError:
            handleMHError(context)
        return{'FINISHED'}

#
#   class OBJECT_OT_ReexportMhcloButton(bpy.types.Operator):
#

class OBJECT_OT_ReexportFilesButton(bpy.types.Operator):
    bl_idname = "mhc2.reexport_files"
    bl_label = "Reexport Files"
    bl_options = {'UNDO'}

    def execute(self, context):
        setObjectMode(context)
        try:
            project.reexportMhclo(context)
            write.exportObjFile(context)
        except MHError:
            handleMHError(context)
        return{'FINISHED'}

#
#    Init and register
#

def register():
    main.init()
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)
    maketarget.unregister()

if __name__ == "__main__":
    register()

print("MakeMhc2 loaded")
