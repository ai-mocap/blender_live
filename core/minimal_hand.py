import bpy
import numpy as np
import math
from mathutils import Quaternion


def setup_joints(joint_names, prefix, mode="all"):
    bpy.ops.object.select_all(action="DESELECT")
    if mode == "all":
        for joint_name in joint_names:
            bpy.ops.mesh.primitive_uv_sphere_add(
                radius=0.04, enter_editmode=False, align="WORLD", location=(0, 0, 0)
            )
            for obj in bpy.data.objects:
                if obj.name == "Sphere":
                    obj.name = prefix + joint_name
                    if joint_name != "root":
                        obj.parent = bpy.data.objects[prefix + "root"]
    elif mode == "root":
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=0.04, enter_editmode=False, align="WORLD", location=(0, 0, 0)
        )
        bpy.data.objects["Sphere"].name = prefix + "root"
    else:
        raise ValueError("Only all or root is supported")


def create_bones(bones, coords, prefix):
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
    for j1_name, j2_name in bones:
        b = edit_bone.new(prefix + j1_name + "_" + j2_name)

        b.head = coords[j1_name]
        b.tail = coords[j2_name]
        # b.use_inherit_rotation = False

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
    armature.parent = bpy.data.objects[prefix + "root"]


def set_constraints(j1_name, j2_name, prefix):
    bpy.ops.object.select_all(action="DESELECT")
    arm_obj = bpy.data.objects[prefix + "Skeleton"]
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="POSE", toggle=False)
    arm_obj.pose.bones[prefix + j1_name + "_" + j2_name].constraints.new("COPY_LOCATION")
    arm_obj.pose.bones[prefix + j1_name + "_" + j2_name].constraints.new("DAMPED_TRACK")
    bpy.context.object.pose.bones[prefix + j1_name + "_" + j2_name].constraints[
        "Damped Track"
    ].target = bpy.data.objects[prefix + j2_name]

    bpy.context.object.pose.bones[prefix + j1_name + "_" + j2_name].constraints[
        "Copy Location"
    ].target = bpy.data.objects[prefix + j1_name]
    bpy.ops.object.mode_set(mode="OBJECT")


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


mano_joints = [
    "root",
    "point1",
    "point2",
    "point3",
    "middle1",
    "middle2",
    "middle3",
    "pinky1",
    "pinky2",
    "pinky3",
    "ring1",
    "ring2",
    "ring3",
    "thumb1",
    "thumb2",
    "thumb3",

    "point_tip",
    "middle_tip",
    "pinky_tip",
    "ring_tip",
    "thumb_tip",
]


def map_coords(coords_raw, mode="mano"):
    if mode == "mano":
        return {name: coords_raw[i] for i, name in enumerate(mano_joints)}
    elif mode == "mpii":
        return {name: coords_raw[idx] for name, idx in mpii_joints}
    elif mode == "quat_mano":
        return {
            "root": coords_raw[0],
            "root_thumb1": coords_raw[0].rotation_difference(coords_raw[13]),
            "thumb1_thumb2": coords_raw[13].rotation_difference(coords_raw[14]),
            "thumb2_thumb3": coords_raw[14].rotation_difference(coords_raw[15]),
            "thumb3_thumb_tip": coords_raw[15].rotation_difference(coords_raw[20]),
            "root_point1": coords_raw[0].rotation_difference(coords_raw[1]),
            "point1_point2": coords_raw[1].rotation_difference(coords_raw[2]),
            "point2_point3": coords_raw[2].rotation_difference(coords_raw[3]),
            "point3_point_tip": coords_raw[3].rotation_difference(coords_raw[16]),
            "root_middle1": coords_raw[0].rotation_difference(coords_raw[4]),
            "middle1_middle2": coords_raw[4].rotation_difference(coords_raw[5]),
            "middle2_middle3": coords_raw[5].rotation_difference(coords_raw[6]),
            "middle3_middle_tip": coords_raw[6].rotation_difference(coords_raw[17]),
            "root_ring1": coords_raw[0].rotation_difference(coords_raw[10]),
            "ring1_ring2": coords_raw[10].rotation_difference(coords_raw[11]),
            "ring2_ring3": coords_raw[11].rotation_difference(coords_raw[12]),
            "ring3_ring_tip": coords_raw[12].rotation_difference(coords_raw[19]),
            "root_pinky1": coords_raw[0].rotation_difference(coords_raw[7]),
            "pinky1_pinky2": coords_raw[7].rotation_difference(coords_raw[8]),
            "pinky2_pinky3": coords_raw[8].rotation_difference(coords_raw[9]),
            "pinky3_pinky_tip": coords_raw[9].rotation_difference(coords_raw[18]),
        }


bones = [
    ("root", "thumb1"),
    ("root", "point1"),
    ("root", "middle1"),
    ("root", "ring1"),
    ("root", "pinky1"),
    ("thumb1", "thumb2"),
    ("thumb2", "thumb3"),
    ("thumb3", "thumb_tip"),
    ("point1", "point2"),
    ("point2", "point3"),
    ("point3", "point_tip"),
    ("middle1", "middle2"),
    ("middle2", "middle3"),
    ("middle3", "middle_tip"),
    ("ring1", "ring2"),
    ("ring2", "ring3"),
    ("ring3", "ring_tip"),
    ("pinky1", "pinky2"),
    ("pinky2", "pinky3"),
    ("pinky3", "pinky_tip"),
]

right_hand = '/home/nb/Downloads/data(2).jsonl'
left_hand = None  # "/home/gleb/code/jupyter/hands_estim/left_hand_frames.txt"


right_hand_model = None
left_hand_model = None


initial_coords = '''-0.4783496546203587,0.03191714428730719,0.030931526400675972
-0.03786342141938446,0.005915358945289405,0.13436147158616243
0.1255310961500387,0.025962135992213912,0.14544681214135052
0.23631065758495548,0.019470023126354465,0.14487622834520336
-0.005047447661171345,0.02452232753259131,0.014143822329090873
0.1508659142620152,0.03382897012449566,-0.013828720260797647
0.265389115431465,0.027568448960906544,-0.033551290274477424
-0.13441479432093825,-0.017784499814935864,-0.18511518361574883
-0.049342753632412834,-0.017475376230939584,-0.24760905845155753
0.029991752401276762,-0.020931155703177683,-0.29926859546310863
-0.06967188247630755,0.012130038522980974,-0.102434438764765
0.07189949253375615,0.02246507481457729,-0.12792713127502736
0.18950205691790983,0.014024515690500667,-0.16609620213687365
-0.3579011206071486,-0.04569452842207133,0.15999576284108968
-0.2597349179007616,-0.041238095664356295,0.2784935290707611
-0.14864622114082912,-0.06840295147164337,0.35111412056743946
0.36192861897365536,0.014762026377023054,0.1383111690011094
0.394964106550951,0.03073324480070758,-0.06020430519157401
0.11843697978416388,-0.027646602997179616,-0.3489420729135565
0.31245949008995283,0.012134281290065078,-0.20334635476466528
-0.018578491307083174,-0.08179516657237615,0.47052484822976226'''


def init():
    # get all objects in a scene
    obs = bpy.data.objects

    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

    for ob in obs:
        if ob.type == "CAMERA":
            ob.select_set(False)

    coords_raw = np.array(
        [[float(coord) for coord in s.split(",")] for s in initial_coords.split("\n")]
    )
    print(coords_raw)

    if right_hand_model is not None:
        bpy.ops.import_scene.obj(filepath=right_hand_model)
        obj_object = bpy.context.selected_objects[0]
        obj_object.rotation_euler.rotate_axis("X", math.radians(-90))
        obj_object.name = "right_hand_mesh"
        bpy.ops.object.shade_smooth()
        obj_object.location.x -= coords_raw[0, 0]
        obj_object.location.y -= coords_raw[0, 1]
        obj_object.location.z -= coords_raw[0, 2]
        bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")

    coords_raw -= coords_raw[0]
    coords = map_coords(coords_raw, "mano")
    setup_joints(coords.keys(), prefix="right_", mode="root")
    create_bones(bones, coords, prefix="right_")

    if right_hand_model is not None:
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        obj = bpy.data.objects["right_hand_mesh"]
        armature = bpy.data.objects["right_Skeleton"]
        obj.select_set(True)
        armature.select_set(True)
        for b in armature.pose.bones:
            b.bone.select = True
        bpy.context.view_layer.objects.active = (
            armature  # the active object will be the parent of all selected object
        )
        bpy.ops.object.parent_set(type="ARMATURE_AUTO", keep_transform=True)


def process_bones(frame_idx, frame_coords):
    coords_raw = [Quaternion(quat) for quat in frame_coords]
    coords = map_coords(coords_raw, "quat_mano")

    # bpy.context.scene.frame_set(frame_idx)
    # bpy.data.scenes["Scene"].frame_end = frame_idx + 1

    obj = bpy.data.objects["right_root"]
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = coords["root"]
    # obj.keyframe_insert(data_path="rotation_quaternion", index=-1)

    for joint_name, bone_quat in list(coords.items())[1:]:
        obj = bpy.data.objects["right_Skeleton"].pose.bones["right_" + joint_name]
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = bone_quat.normalized()  # joint_coords
        # obj.keyframe_insert(data_path="rotation_quaternion", index=-1)


def add_joint(name, location):
    if name not in bpy.data.objects:
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.01)
        obj = bpy.context.object
        obj.name = name
    else:
        obj = bpy.data.objects[name]
    obj.location = location


def add_bone(name, src, dst):
    if name not in bpy.data.objects:
        bpy.ops.curve.primitive_bezier_curve_add(radius=0.1)
        obj = bpy.context.object
        obj.data.dimensions = '3D'
        obj.data.fill_mode = 'FULL'
        obj.data.bevel_depth = 0.1
        obj.data.bevel_resolution = 4
        obj.name = name
    else:
        obj = bpy.data.objects[name]
    # set first point to centre of sphere1
    obj.data.splines[0].bezier_points[0].co = src
    obj.data.splines[0].bezier_points[0].handle_left_type = 'VECTOR'
    # set second point to centre of sphere2
    obj.data.splines[0].bezier_points[1].co = dst
    obj.data.splines[0].bezier_points[1].handle_left_type = 'VECTOR'


def cylinder_between(name, src, dst, r):
    if name not in bpy.data.objects:
        bpy.ops.mesh.primitive_cylinder_add()
        obj = bpy.context.object
        obj.name = name
    else:
        obj = bpy.data.objects[name]
    diff = [b - a for a, b in zip(src, dst)]
    dist = math.sqrt(sum(c**2 for c in diff))
    obj.scale = [r, r, dist / 2]
    obj.location = [c + d/2 for c, d in zip(src, diff)]

    phi = math.atan2(diff[1], diff[0])
    theta = math.acos(diff[2] / dist)
    obj.rotation_euler[1] = theta
    obj.rotation_euler[2] = phi


def process_xyz(frame_idx, xyz):
    for name, coords in zip(mpii_joints, xyz):
        add_joint(f'joint#{name}', coords)
    xyz_map = dict(zip(mpii_joints, xyz))
    for src, dst in bones:
        cylinder_between(f'bone#{src}-{dst}', xyz_map[src], xyz_map[dst], 0.01)
