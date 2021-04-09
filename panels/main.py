import bpy

from ..core.receiver import receiver
from ..core.icon_manager import Icons
from ..operators.recorder import RecorderStart, RecorderStop
from ..operators.hands import ResetHands, LoadHands
from ..operators.receiver import ReceiverStart, ReceiverStop

row_scale = 0.75
paired_inputs = {}


# Initializes the CPTR panel in the toolbar
class ToolPanel(object):
    bl_label = 'CPTR'
    bl_idname = 'VIEW3D_TS_cptr'
    bl_category = 'CPTR'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'


def separator(layout, scale=1):
    # Add small separator
    row = layout.row(align=True)
    row.scale_y = scale
    row.label(text='')


# Main panel of the CPTR panel
class ReceiverPanel(ToolPanel, bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_cptr_receiver_v2'
    bl_label = 'CPTR Blender Plugin'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False

        col = layout.column()
        prefs = bpy.context.preferences.addons['cptr-tech'].preferences

        row = col.row(align=True)
        row.label(text='Port:')
        row.enabled = not receiver.is_running
        row.prop(prefs, 'receiver_port', text='')

        port = prefs.receiver_port
        row = col.row(align=True)
        row.operator("wm.url_open", text="Link port").url = f"https://app.cptr.tech/connect.html?port={port}"

        row = layout.row(align=True)
        row.scale_y = 1.3
        row.enabled = receiver.is_connected and not receiver.is_in_transition
        if receiver.is_running:
            row.operator(ReceiverStop.bl_idname, icon='PAUSE', depress=True)
        else:
            row.operator(ReceiverStart.bl_idname, icon='PLAY')

        row = layout.row(align=True)
        row.scale_y = 1.3
        row.enabled = receiver.is_running
        if receiver.is_recording:
            row.operator(RecorderStop.bl_idname, icon='SNAP_FACE', depress=True)
        else:
            row.operator(RecorderStart.bl_idname, icon_value=Icons.START_RECORDING.get_icon())

        row = layout.row(align=True)
        row.enabled = True
        row.operator(ResetHands.bl_idname)

        row = layout.row(align=True)
        row.enabled = True
        row.operator(LoadHands.bl_idname)


def add_indent(split, empty=False):
    row = split.row(align=True)
    row.alignment = 'LEFT'
    if empty:
        row.label(text="", icon='BLANK1')
    else:
        row.label(text="", icon_value=Icons.PAIRED.get_icon())
