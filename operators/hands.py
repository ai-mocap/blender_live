import bpy

from ..core.minimal_hand import Hand, load_hands


class ResetHands(bpy.types.Operator):
    bl_idname = "cptr.reset_hands"
    bl_label = "Reset Hands"
    bl_description = "Reset hands poses"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        Hand('left_').reset_pose()
        Hand('right_').reset_pose()
        return {'FINISHED'}


class LoadHands(bpy.types.Operator):
    bl_idname = "cptr.create_hands"
    bl_label = "Create hands"
    bl_description = "Create hand rigs"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        load_hands()
        return {'FINISHED'}
