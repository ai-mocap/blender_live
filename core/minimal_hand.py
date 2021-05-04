import bpy
from mathutils import Quaternion

import os.path
from functools import lru_cache
from pathlib import Path


mpii_joints = [
    "root",

    "thumb1",
    "thumb2",
    "thumb3",
    "thumb4",

    "index1",
    "index2",
    "index3",
    "index4",

    "middle1",
    "middle2",
    "middle3",
    "middle4",

    "ring1",
    "ring2",
    "ring3",
    "ring4",

    "pinky1",
    "pinky2",
    "pinky3",
    "pinky4",
]

mpii_parents = dict(
    root=None,

    thumb1='root',
    thumb2='thumb1',
    thumb3='thumb2',
    thumb4='thumb3',

    index1='root',
    index2='index1',
    index3='index2',
    index4='index3',

    middle1='root',
    middle2='middle1',
    middle3='middle2',
    middle4='middle3',

    ring1='root',
    ring2='ring1',
    ring3='ring2',
    ring4='ring3',

    pinky1='root',
    pinky2='pinky1',
    pinky3='pinky2',
    pinky4='pinky3',
)


@lru_cache()
def resources() -> Path:
    return Path(os.path.dirname(__file__)).parent.resolve() / "resources"


def load_blend(filename):
    filepath = resources() / filename

    with bpy.data.libraries.load(str(filepath)) as (data_from, data_to):
        data_to.objects = data_from.objects

        objects = bpy.context.view_layer.active_layer_collection.collection.objects
        for obj in data_to.objects:
            if obj is not None:
                objects.link(obj)


def load_hands():
    load_blend("handlmoved.blend")


def load_body():
    load_blend("ue4_mannequin.blend")


class Hand:
    def __init__(self, prefix):
        self.prefix = prefix
        self.to_ref_quats = {None: Quaternion()}
        self.ref_scales = {None: 1.}
        self.enable_scale = False

    @property
    def object(self):
        name = self.prefix + "Skeleton"
        if name in bpy.data.objects:
            return bpy.data.objects[name]

    def reset_pose(self):
        if self.object is None:
            return
        for bone in self.object.pose.bones:
            bone.rotation_mode = "QUATERNION"
            bone.rotation_quaternion = Quaternion()
            bone.scale = (1, 1, 1)

    def save_pose(self):
        if self.object is None:
            return
        self.object.select_set(True)
        bpy.context.view_layer.objects.active = self.object
        bpy.ops.object.mode_set(mode="EDIT", toggle=False)
        edit_bones = self.object.data.edit_bones
        ref_quats = {None: Quaternion()}
        for joint in mpii_joints:
            parent = mpii_parents[joint]
            if joint in edit_bones:
                ref_quats[joint] = quat = edit_bones[joint].matrix.to_quaternion()
                self.ref_scales[joint] = edit_bones[joint].length
            else:
                ref_quats[joint] = quat = ref_quats[parent]
                self.ref_scales[joint] = self.ref_scales[parent]
            self.to_ref_quats[joint] = quat.inverted() @ ref_quats[parent]

    def process_bones(self, relative_rotations, relative_scales):
        bones = self.object.pose.bones
        from .receiver import receiver
        for idx, bone in enumerate(mpii_joints):
            parent = mpii_parents[bone]
            rel_quat = relative_rotations[idx]
            rel_scale = relative_scales[idx - 1] if idx else 1.

            if bone in bones:
                obj = bones[bone]
                quat = self.to_ref_quats[bone] @ Quaternion(rel_quat)
                obj.rotation_quaternion = quat
                if self.enable_scale:
                    scale = rel_scale * self.ref_scales[parent] / self.ref_scales[bone]
                    obj.scale = (scale, scale, scale)
                if receiver.is_recording:
                    obj.keyframe_insert(data_path="rotation_quaternion", index=-1)


class Body:
    def __init__(self):
        self.name = 'BodySkeleton'

    @property
    def object(self):
        if self.name in bpy.data.objects:
            return bpy.data.objects[self.name]
