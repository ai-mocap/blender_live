import bpy
from mathutils import Quaternion


mpii_joints = [
    "root",
    "thumb1",
    "thumb2",
    "thumb3",
    "thumb_tip",
    "point1",
    "point2",
    "point3",
    "point_tip",
    "middle1",
    "middle2",
    "middle3",
    "middle_tip",
    "ring1",
    "ring2",
    "ring3",
    "ring_tip",
    "pinky1",
    "pinky2",
    "pinky3",
    "pinky_tip",
]


def map_mpii_coords(coord_list):
    return {name: coord_list[idx] for idx, name in enumerate(mpii_joints)}


def map_mpii_bones(coord_list):
    coords = map_mpii_coords(coord_list)
    return {(src, dst): (coords[src], coords[dst]) for src, dst in bones}


# Should be in MPII order
bones = [
    ("root", "thumb1"),
    ("thumb1", "thumb2"),
    ("thumb2", "thumb3"),
    ("thumb3", "thumb_tip"),
    ("root", "point1"),
    ("point1", "point2"),
    ("point2", "point3"),
    ("point3", "point_tip"),
    ("root", "middle1"),
    ("middle1", "middle2"),
    ("middle2", "middle3"),
    ("middle3", "middle_tip"),
    ("root", "ring1"),
    ("ring1", "ring2"),
    ("ring2", "ring3"),
    ("ring3", "ring_tip"),
    ("root", "pinky1"),
    ("pinky1", "pinky2"),
    ("pinky2", "pinky3"),
    ("pinky3", "pinky_tip"),
]


def create_hands():
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    if not bpy.context.scene.objects.get("left_Skeleton"):
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete()

        for ob in bpy.data.objects:
            if ob.type == "CAMERA":
                ob.select_set(False)

        left = Hand('left_')
        left.create_bones()
        right = Hand('right_')
        right.create_bones()
        return left, right


class Hand:
    def __init__(self, prefix):
        self.prefix = prefix
        self.ref_quats = {'root': Quaternion()}
        self.ref_scales = {'root': 1.}
        self.enable_scale = False

    def save_pose(self):
        prefix = self.prefix
        arm_obj = bpy.data.objects[prefix + "Skeleton"]
        arm_obj.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT", toggle=False)
        edit_bone = arm_obj.data.edit_bones
        for src, dst in bones:
            bone_name = f"{src}_{dst}"
            self.ref_quats[dst] = edit_bone[f"{prefix}{bone_name}"].matrix.to_quaternion()
            self.ref_scales[dst] = edit_bone[f"{prefix}{bone_name}"].length
        bpy.ops.object.mode_set(mode="OBJECT")

    def process_bones(self, relative_rotations, relative_scales):
        prefix = self.prefix
        coords = map_mpii_bones(list(zip(relative_rotations, [1] + relative_scales)))
        obj = bpy.data.objects[f"{prefix}Skeleton"]
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = relative_rotations[0]
        for (src, dst), ((parent_rel_quat, parent_rel_scale), (rel_quat, rel_scale)) in coords.items():
            obj = bpy.data.objects[f"{prefix}Skeleton"].pose.bones[f"{prefix}{src}_{dst}"]
            obj.rotation_mode = "QUATERNION"
            obj.rotation_quaternion = self.ref_quats[dst].inverted() @ self.ref_quats[src] @ Quaternion(rel_quat)
            scale = rel_scale * self.ref_scales[src] / self.ref_scales[dst] if self.enable_scale else 1
            obj.scale = (scale, scale, scale)

    def create_bones(self):
        prefix = self.prefix
        bpy.ops.object.select_all(action="DESELECT")
        bpy.ops.object.armature_add(
            enter_editmode=False, align="WORLD", location=(0, 0, 0), scale=(1, 1, 1)
        )
        armature = bpy.data.objects["Armature"]
        armature.name = prefix + "Skeleton"
        bpy.ops.object.select_all(action="DESELECT")
        arm_obj = bpy.data.objects[prefix + "Skeleton"]
        arm_obj.select_set(True)
        bpy.context.view_layer.objects.active = arm_obj
        bpy.ops.object.mode_set(mode="EDIT", toggle=False)

        edit_bone = arm_obj.data.edit_bones
        edit_bone.remove(edit_bone[0])
        parent_coords = {'root': 0}
        for j1_name, j2_name in bones:
            b = edit_bone.new(f"{prefix}{j1_name}_{j2_name}")
            b.head = (0, parent_coords[j1_name], 0)
            parent_coords[j2_name] = b.head[1] + 1
            b.tail = (0, parent_coords[j2_name], 0)

        # TODO add proper DFS, but we'll have to decide on the tree root first
        edit_bone[prefix + "thumb3_thumb_tip"].parent = edit_bone[prefix + "thumb2_thumb3"]
        edit_bone[prefix + "thumb2_thumb3"].parent = edit_bone[prefix + "thumb1_thumb2"]
        edit_bone[prefix + "thumb1_thumb2"].parent = edit_bone[prefix + "root_thumb1"]
        edit_bone[prefix + "point3_point_tip"].parent = edit_bone[prefix + "point2_point3"]
        edit_bone[prefix + "point2_point3"].parent = edit_bone[prefix + "point1_point2"]
        edit_bone[prefix + "point1_point2"].parent = edit_bone[prefix + "root_point1"]
        edit_bone[prefix + "middle3_middle_tip"].parent = edit_bone[prefix + "middle2_middle3"]
        edit_bone[prefix + "middle2_middle3"].parent = edit_bone[prefix + "middle1_middle2"]
        edit_bone[prefix + "middle1_middle2"].parent = edit_bone[prefix + "root_middle1"]
        edit_bone[prefix + "ring3_ring_tip"].parent = edit_bone[prefix + "ring2_ring3"]
        edit_bone[prefix + "ring2_ring3"].parent = edit_bone[prefix + "ring1_ring2"]
        edit_bone[prefix + "ring1_ring2"].parent = edit_bone[prefix + "root_ring1"]
        edit_bone[prefix + "pinky3_pinky_tip"].parent = edit_bone[prefix + "pinky2_pinky3"]
        edit_bone[prefix + "pinky2_pinky3"].parent = edit_bone[prefix + "pinky1_pinky2"]
        edit_bone[prefix + "pinky1_pinky2"].parent = edit_bone[prefix + "root_pinky1"]
        bpy.ops.object.mode_set(mode="OBJECT")
