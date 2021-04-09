import bpy

from ..core.receiver import receiver


class RecorderStart(bpy.types.Operator):
    bl_idname = "cptr.recorder_start"
    bl_label = "Record"
    bl_description = "Start recording data from CPTR.tech"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        if receiver.is_recording:
            self.report({'ERROR'}, 'Already recording')
            return {'CANCELLED'}

        receiver.is_recording = True
        return {'FINISHED'}


class RecorderStop(bpy.types.Operator):
    bl_idname = "cptr.recorder_stop"
    bl_label = "Stop"
    bl_description = "Stop recording data from CPTR.tech"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        if not receiver.is_recording:
            self.report({'ERROR'}, 'Not recording')
            return {'CANCELLED'}

        receiver.is_recording = False
        return {'FINISHED'}
