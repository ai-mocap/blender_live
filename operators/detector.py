import bpy
from ..core import animation_lists


class DetectFaceShapes(bpy.types.Operator):
    bl_idname = "rsl.detect_face_shapes"
    bl_label = "Auto Detect"
    bl_description = "Automatically detect face shape keys for supported naming schemes"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def execute(self, context):
        obj = context.object

        if not hasattr(obj.data, 'shape_keys') or not hasattr(obj.data.shape_keys, 'key_blocks'):
            self.report({'ERROR'}, 'This mesh has no shapekeys!')
            return {'CANCELLED'}

        for shape in animation_lists.face_shapes:
            if shape in obj.data.shape_keys.key_blocks:
                setattr(obj, 'rsl_face_' + shape, shape)

        return {'FINISHED'}


class DetectActorBones(bpy.types.Operator):
    bl_idname = "rsl.detect_actor_bones"
    bl_label = "Auto Detect"
    bl_description = "Automatically detect actor bones for supported naming schemes"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    def execute(self, context):
        obj = context.object

        for bone in animation_lists.actor_bones:
            bone_name = 'Character1_' + bone[0].capitalize() + bone[1:]
            print(bone_name)
            if bone_name in obj.pose.bones:
                setattr(obj, 'rsl_actor_' + bone, bone_name)

        return {'FINISHED'}