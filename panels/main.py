import bpy
import datetime

from ..core import recorder as recorder_manager
from ..core.icon_manager import Icons
from ..operators import receiver, recorder, hands

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

        row = col.row(align=True)
        row.label(text='Port:')
        row.enabled = not receiver.receiver_enabled
        row.prop(context.scene, 'cptr_receiver_port', text='')

        port = context.scene.cptr_receiver_port
        row = col.row(align=True)
        row.operator("wm.url_open", text="Link port").url = f"https://app.cptr.tech/connect.html?port={port}"

        row = layout.row(align=True)
        row.scale_y = 1.3
        if receiver.receiver_enabled:
            row.operator(receiver.ReceiverStop.bl_idname, icon='PAUSE', depress=True)
        else:
            row.operator(receiver.ReceiverStart.bl_idname, icon='PLAY')

        row = layout.row(align=True)
        row.scale_y = 1.3
        row.enabled = receiver.receiver_enabled
        if not context.scene.cptr_recording:
            row.operator(recorder.RecorderStart.bl_idname, icon_value=Icons.START_RECORDING.get_icon())
        else:
            row.operator(recorder.RecorderStop.bl_idname, icon='SNAP_FACE', depress=True)

            # Calculate recording time
            timestamps = list(recorder_manager.recorded_timestamps.keys())
            if timestamps:
                time_recorded = int(timestamps[-1] - timestamps[0])
                row = layout.row(align=True)
                row.label(text='Recording time: ' + str(datetime.timedelta(seconds=time_recorded)))

        row = layout.row(align=True)
        row.enabled = True
        row.operator(hands.ResetHands.bl_idname)

        row = layout.row(align=True)
        row.enabled = True
        row.operator(hands.LoadHands.bl_idname)


def add_indent(split, empty=False):
    row = split.row(align=True)
    row.alignment = 'LEFT'
    if empty:
        row.label(text="", icon='BLANK1')
    else:
        row.label(text="", icon_value=Icons.PAIRED.get_icon())
