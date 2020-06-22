# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


import bpy
from bpy.types import Operator


bl_info = {
    "name": "Render Markers",
    "author": "Edward S. White",
    "description": "Renders only frames with timeline markers",
    "blender": (2, 80, 0),
    "version": (1, 0, 0),
    "location": "Render Menu > Render Markers",
    "category": "Render"
}


def ShowMessageBox(message="", title="Message Box", icon='INFO'):

    def draw(self, context):
        self.layout.label(text=message)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


class RM_OT_rendermarkers(Operator):
    """Render images only at timeline marker positions"""
    bl_idname = "render.rendermarkers"
    bl_label = "Render Markers"
    bl_description = "Render images only at timeline marker positions"

    def execute(self, context):
        scene = bpy.context.scene
        # Save current scene settings
        prev_timeline = scene.frame_current
        prev_filepath = scene.render.filepath
        # Use path from Output Settings
        render_path = scene.render.filepath
        animation_formats = ['FFMPEG', 'AVI_JPEG', 'AVI_RAW', 'FRAMESERVER']
        if scene.render.image_settings.file_format in animation_formats:
            print("Movie file formats are not supported in Render Markers.")
            ShowMessageBox("Movie file formats are not supported.",
                           "Render Images at Markers",
                           'ERROR')
            return {"FINISHED"}
        # Get list of all markers in the scene
        mlist = scene.timeline_markers
        # sort markers by time
        markerlist = sorted(mlist, key=lambda mlist: mlist.frame)
        # step through markers and render an image
        for m in markerlist:
            scene.frame_current = m.frame
            # set render filepath
            scene.render.filepath = render_path + "_" + \
                str(scene.frame_current).zfill(4)
            bpy.ops.render.render(animation=False,
                                  write_still=True
                                  )
        # Restore previous settings
        scene.frame_current = prev_timeline
        scene.render.filepath = prev_filepath
        ShowMessageBox("Finished Rendering",
                       "Render Images at Markers",
                       'INFO')

        return {'FINISHED'}

    def draw(self, context):

        layout = self.layout
        row = layout.row()
        row.label(text="Output file location")

        file_path = bpy.context.scene.render.filepath
        box = layout.box()
        row = box.row()
        row.alignment = 'LEFT'
        row.label(text=file_path)

        layout = self.layout
        row = layout.row()
        row.alignment = 'CENTER'
        row.label(text="(Blender may appear to be frozen during render)")

    def invoke(self, context, event):

        scene = bpy.context.scene
        animation_formats = ['FFMPEG', 'AVI_JPEG', 'AVI_RAW', 'FRAMESERVER']
        if scene.render.image_settings.file_format in animation_formats:
            print("Movie file formats are not supported in Render Markers.")
            ShowMessageBox("Movie file formats are not supported.",
                           "Render Images at Markers",
                           'ERROR')
            return {'FINISHED'}
        return context.window_manager.invoke_props_dialog(self)


class RM_OT_renderanimmarkers(Operator):
    """Render the same frame until a new marker is reached"""
    bl_idname = "render.renderanimmarkers"
    bl_label = "Render Markers"
    bl_description = "Render the same frame until a new marker is reached"

    def execute(self, context):

        scene = bpy.context.scene
        # Save current scene settings
        prev_timeline = scene.frame_current
        prev_filepath = scene.render.filepath

        # Get list of all markers in the scene
        mlist = scene.timeline_markers
        if not mlist:
            print("No markers in current scene.")
            ShowMessageBox("No markers in current scene.",
                           "Render Holding on Markers",
                           'ERROR')
            return {'FINISHED'}

        # sort markers by time
        markerlist = sorted(mlist, key=lambda mlist: mlist.frame)

        # Use path from Output Settings
        render_path = scene.render.filepath
        scene.frame_current = scene.frame_start

        movie_formats = ['FFMPEG', 'AVI_JPEG', 'AVI_RAW', 'FRAMESERVER']
        if not scene.render.image_settings.file_format in movie_formats:
            # render images holding for each marker
            for f in range(scene.frame_start, (scene.frame_end + 1)):
                scene.render.filepath = render_path + "_" + \
                    str(f).zfill(4)
                bpy.ops.render.render(animation=False,
                                      write_still=True
                                      )
                # check if new marker has been reached
                for m in markerlist:
                    if m.frame == (f + 1):
                        scene.frame_current = m.frame

        # Restore previous settings
        scene.frame_current = prev_timeline
        scene.render.filepath = prev_filepath
        ShowMessageBox("Finished Rendering",
                       "Render Holding on Markers",
                       'INFO')

        return {'FINISHED'}

    def draw(self, context):

        layout = self.layout
        row = layout.row()
        row.label(text="Output file location")

        file_path = bpy.context.scene.render.filepath
        box = layout.box()
        row = box.row()
        row.alignment = 'LEFT'
        row.label(text=file_path)

        layout = self.layout
        row = layout.row()
        row.alignment = 'CENTER'
        row.label(text="(Blender may appear to be frozen during render)")

    def invoke(self, context, event):

        scene = bpy.context.scene
        animation_formats = ['FFMPEG', 'AVI_JPEG', 'AVI_RAW', 'FRAMESERVER']
        if scene.render.image_settings.file_format in animation_formats:
            print("Movie file formats are not supported in Render Markers.")
            ShowMessageBox("Movie file formats are not supported.",
                           "Render Holding on Markers",
                           'ERROR')
            return {'FINISHED'}
        return context.window_manager.invoke_props_dialog(self)


classes = (
    RM_OT_rendermarkers,
    RM_OT_renderanimmarkers,
)


def menu_func_render(self, context):
    self.layout.operator(RM_OT_rendermarkers.bl_idname,
                         text="Render Images at Markers",
                         icon='RENDER_STILL'
                         )


def menu_func_animrender(self, context):
    self.layout.operator(RM_OT_renderanimmarkers.bl_idname,
                         text="Render Holding on Markers",
                         icon='RENDER_ANIMATION'
                         )


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_render.append(menu_func_render)
    bpy.types.TOPBAR_MT_render.append(menu_func_animrender)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.TOPBAR_MT_render.remove(menu_func_render)
    bpy.types.TOPBAR_MT_render.remove(menu_func_animrender)


if __name__ == "__main__":
    register()
