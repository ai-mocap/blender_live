import bpy

from ..core.minimal_hand import Skeleton, load_body


class ResetHands(bpy.types.Operator):
    bl_idname = "cptr.reset_hands"
    bl_label = "Reset Hands"
    bl_description = "Reset hands poses"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        Skeleton('body').reset_pose()
        return {'FINISHED'}


class LoadHands(bpy.types.Operator):
    bl_idname = "cptr.create_hands"
    bl_label = "Create hands"
    bl_description = "Create hand rigs"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        load_body()
        return {'FINISHED'}
