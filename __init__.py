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
    "version": (1, 3, 0),
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

    _timer = None
    scene = None
    markers = None
    prevpath = None
    renderpath = None
    prevframe = None
    timeframe = None
    stop = None
    rendering = None

    def rmpre(self, dummy, thrd=None):
        self.rendering = True

    def rmpost(self, context, thrd=None):
        self.markers.pop(0)
        if len(self.markers):
            self.timeframe = self.markers[0].frame
        else:
            self.stop = True
        bpy.context.scene.frame_current = self.timeframe
        self.rendering = False

    def rmcancel(self, dummy, thrd=None):
        self.scene.frame_current = self.prevframe
        self.scene.render.filepath = self.prevpath
        print("Cancelled")
        self.stop = True

    def execute(self, context):

        bpy.app.handlers.render_pre.append(self.rmpre)
        bpy.app.handlers.render_post.append(self.rmpost)
        bpy.app.handlers.render_cancel.append(self.rmcancel)

        scene = bpy.context.scene
        self.scene = scene
        # Save current scene settings
        self.renderpath = scene.render.filepath
        self.prevpath = scene.render.filepath
        self.prevframe = scene.frame_current
        scene.frame_current
        # Get list of all markers in the scene
        mlist = scene.timeline_markers
        # sort markers by time
        self.markers = sorted(mlist, key=lambda mlist: mlist.frame)
        self.timeframe = self.markers[0].frame

        wm = bpy.context.window_manager
        self._timer = wm.event_timer_add(0.1, window=bpy.context.window)
        wm.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):

        if event.type in {'ESC'}:
            self.rmcancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            if True in (not self.markers, self.stop is True):
                bpy.app.handlers.render_pre.remove(self.rmpre)
                bpy.app.handlers.render_post.remove(self.rmpost)
                bpy.app.handlers.render_cancel.remove(self.rmcancel)
                bpy.context.window_manager.event_timer_remove(self._timer)
                bpy.context.scene.frame_current = self.prevframe
                bpy.context.scene.render.filepath = self.prevpath
                ShowMessageBox("Finished Rendering",
                               "Render Images at Markers",
                               'INFO')
                return {"FINISHED"}

            elif not self.rendering:
                scene = bpy.context.scene
                # render images holding for each marker
                scene.render.filepath = self.renderpath + "_" + \
                    str(self.timeframe).zfill(4)
                bpy.ops.render.render(animation=False,
                                      write_still=True
                                      )

        return {'PASS_THROUGH'}

    def draw(self, context):

        layout = self.layout
        row = layout.row()
        row.label(text="Output file location")

        row = layout.row()
        row.label(text="Press Esc if location is not correct.")

        file_path = bpy.context.scene.render.filepath
        box = layout.box()
        row = box.row()
        row.alignment = 'LEFT'
        row.label(text=file_path)

    def invoke(self, context, event):

        scene = bpy.context.scene
        animation_formats = ['FFMPEG', 'AVI_JPEG', 'AVI_RAW', 'FRAMESERVER']
        if scene.render.image_settings.file_format in animation_formats:
            print("Movie file formats are not supported in Render Markers.")
            ShowMessageBox("Movie file formats are not supported.",
                           "Render Images at Markers",
                           'ERROR')
            return {'FINISHED'}
        # Get list of all markers in the scene
        mlist = scene.timeline_markers
        if not mlist:
            print("No markers in the current scene.")
            ShowMessageBox("No markers in the current scene.",
                           "Viewport Render Images at Markers",
                           'ERROR')
            return {'FINISHED'}
        return context.window_manager.invoke_props_dialog(self)


class RM_OT_renderanimmarkers(Operator):
    """Render the same frame until a new marker is reached"""
    bl_idname = "render.renderanimmarkers"
    bl_label = "Render Markers"
    bl_description = "Render the same frame until a new marker is reached"

    _timer = None
    scene = None
    markers = None
    renderpath = None
    prevpath = None
    prevframe = None
    timeframe = None
    totalframe = None
    stop = None
    rendering = None

    def rampre(self, dummy, thrd=None):
        self.rendering = True

    def rampost(self, context, thrd=None):
        self.timeframe += 1
        for m in self.markers:  # check if new marker has been reached
            if self.timeframe == m.frame:
                bpy.context.scene.frame_current = self.timeframe
        if self.timeframe > bpy.context.scene.frame_end:
            self.stop = True
        self.scene.render.filepath = self.prevpath
        self.rendering = False

    def ramcancel(self, dummy, thrd=None):
        self.scene.frame_current = self.prevframe
        self.scene.render.filepath = self.prevpath
        print("Cancelled")
        self.stop = True

    def execute(self, context):

        bpy.app.handlers.render_pre.append(self.rampre)
        bpy.app.handlers.render_post.append(self.rampost)
        bpy.app.handlers.render_cancel.append(self.ramcancel)

        scene = bpy.context.scene
        # Get list of all markers in the scene
        mlist = scene.timeline_markers
        self.markers = sorted(mlist, key=lambda mlist: mlist.frame)
        self.renderpath = scene.render.filepath
        self.prevpath = scene.render.filepath
        self.prevframe = scene.frame_current
        self.timeframe = scene.frame_start
        self.totalframe = scene.frame_end - scene.frame_start
        scene.frame_current = self.timeframe

        wm = bpy.context.window_manager
        self._timer = wm.event_timer_add(0.1, window=bpy.context.window)
        wm.modal_handler_add(self)

        return {"RUNNING_MODAL"}

    def modal(self, context, event):

        if event.type in {'ESC'}:
            self.ramcancel(context)
            return {'CANCELLED'}

        if event.type == 'TIMER':
            if True in (not self.markers, self.stop is True):
                bpy.app.handlers.render_pre.remove(self.rampre)
                bpy.app.handlers.render_post.remove(self.rampost)
                bpy.app.handlers.render_cancel.remove(self.ramcancel)
                bpy.context.window_manager.event_timer_remove(self._timer)
                bpy.context.scene.frame_current = self.prevframe
                bpy.context.scene.render.filepath = self.prevpath
                ShowMessageBox("Finished Rendering",
                               "Render Holding on Markers",
                               'INFO')
                return {"FINISHED"}

            elif not self.rendering:
                scene = bpy.context.scene
                # render images holding for each marker
                scene.render.filepath = self.renderpath + "_" + \
                    str(self.timeframe).zfill(4)
                bpy.ops.render.render(animation=False,
                                      write_still=True
                                      )

        return {'PASS_THROUGH'}

    def draw(self, context):

        layout = self.layout
        row = layout.row()
        row.label(text="Output File Location")

        row = layout.row()
        row.label(text="Press Esc if location is not correct.")

        file_path = bpy.context.scene.render.filepath
        box = layout.box()
        row = box.row()
        row.alignment = 'LEFT'
        row.label(text=file_path)

    def invoke(self, context, event):

        scene = bpy.context.scene
        self.scene = scene
        # Check for not a movie format
        animation_formats = ['FFMPEG', 'AVI_JPEG', 'AVI_RAW']
        if scene.render.image_settings.file_format in animation_formats:
            print("Movie file formats are not supported in Render Markers.")
            ShowMessageBox("Movie file formats are not supported.",
                           "Render Holding on Markers",
                           'ERROR')
            return {'FINISHED'}
        # Get list of all markers in the scene
        mlist = scene.timeline_markers
        if not mlist:
            print("No markers in the current scene.")
            ShowMessageBox("No markers in the current scene.",
                           "Viewport Render Images at Markers",
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
