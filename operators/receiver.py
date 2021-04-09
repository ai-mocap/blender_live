import bpy
import logging

from ..core.receiver import receiver

logger = logging.getLogger(__name__)


class ReceiverStart(bpy.types.Operator):
    bl_idname = "cptr.receiver_start"
    bl_label = "Start"
    bl_description = "Start receiving data from cptr.tech"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        try:
            receiver.start()
        except Exception as exc:
            logger.exception("Exception while starting receiver")
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}

        # If animation is currently playing, stop it
        if context.screen.is_animation_playing:
            bpy.ops.screen.animation_play()

        return {'FINISHED'}


class ReceiverStop(bpy.types.Operator):
    bl_idname = "cptr.receiver_stop"
    bl_label = "Stop"
    bl_description = "Stop receiving data from cptr.tech"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        receiver.stop()
        return {'FINISHED'}
