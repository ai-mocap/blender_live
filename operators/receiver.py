import bpy
import logging

from ..core.receiver import Receiver
from ..core.utils import ui_refresh_all

timer = None
receiver: Receiver = Receiver()
receiver_enabled = False
logger = logging.getLogger(__name__)


class ReceiverStart(bpy.types.Operator):
    bl_idname = "cptr.receiver_start"
    bl_label = "Start Receiver"
    bl_description = "Start receiving data from cptr.tech"
    bl_options = {'INTERNAL'}

    def modal(self, context, event):
        if not receiver_enabled:
            return self.cancel(context)

        # This gets run every frame
        if event.type == 'TIMER':
            if bpy.context.screen.is_animation_playing:
                return self.cancel(context)

            try:
                receiver.run()
            except Exception as exc:
                logger.exception("Exception while running receiver")
                self.report({'ERROR'}, str(exc))

        return {'PASS_THROUGH'}

    def execute(self, context):
        global receiver_enabled, receiver, timer

        # Start the receiver
        try:
            receiver.start(context)
        except Exception as exc:
            logger.exception("Exception while starting receiver")
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}

        receiver_enabled = True

        # If animation is currently playing, stop it
        if context.screen.is_animation_playing:
            bpy.ops.screen.animation_play()

        # Register this classes modal operator in Blenders event handling system and execute it at the specified fps
        context.window_manager.modal_handler_add(self)
        timer = context.window_manager.event_timer_add(1 / context.scene.cptr_receiver_fps, window=bpy.context.window)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        ReceiverStart.force_disable()
        ui_refresh_all()
        return {'CANCELLED'}

    @classmethod
    def force_disable(cls):
        global receiver_enabled, receiver, timer

        receiver_enabled = False
        receiver.stop()

        bpy.context.window_manager.event_timer_remove(timer)

        # If the recording is still running, let it load the scene afterwards with a delay
        if bpy.context.scene.cptr_recording:
            bpy.context.scene.cptr_recording = False


class ReceiverStop(bpy.types.Operator):
    bl_idname = "cptr.receiver_stop"
    bl_label = "Stop Receiver"
    bl_description = "Stop receiving data from cptr.tech"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        global receiver_enabled
        receiver_enabled = False
        return {'FINISHED'}
