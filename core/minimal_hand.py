import bpy
from mathutils import Quaternion

import logging
import os.path
from functools import lru_cache
from pathlib import Path


logger = logging.getLogger(__name__)


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


class InvalidRoot(Exception):
    pass


def load_blend(filename):
    filepath = resources() / filename

    with bpy.data.libraries.load(str(filepath)) as (data_from, data_to):
        data_to.objects = data_from.objects

    objects = bpy.context.view_layer.active_layer_collection.collection.objects
    for obj in data_to.objects:
        if obj is not None:
            objects.link(obj)


def load_hands():
    load_blend("hands.blend")
    return Skeleton("hand_l"), Skeleton("hand_r")


def load_body():
    load_blend("body.blend")
    return Skeleton("body")


class Skeleton:
    def __init__(self, name):
        if name not in bpy.data.objects:
            raise InvalidRoot(f"<{name}> was not found")
        self.object = bpy.data.objects[name]
        self.to_ref_quats = {None: Quaternion()}
        self.ref_scales = {None: 1.}
        self.enable_scale = False

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
        for bone in self.object.pose.bones[0].children_recursive:
            if bone.name in edit_bones:
                ref_quats[bone.name] = quat = edit_bones[bone.name].matrix.to_quaternion()
                self.ref_scales[bone.name] = edit_bones[bone.name].length
            else:
                ref_quats[bone.name] = quat = ref_quats[bone.parent.name]
                self.ref_scales[bone.name] = self.ref_scales[bone.parent.name]
            self.to_ref_quats[bone.name] = quat.inverted() @ ref_quats[bone.parent.name]

    def process_bones(self, received_bones):
        bones = self.object.pose.bones
        from .receiver import receiver
        for bone_name, bone_info in received_bones.items():
            if bone_name not in bones:
                logger.warning(f"Received unknown bone <{bone_name}>")
                continue
            bone = bones[bone_name]
            rel_quat = bone_info['o']
            rel_scale = bone_info.get('s', 1.)

            quat = self.to_ref_quats[bone_name] @ Quaternion(rel_quat)
            bone.rotation_quaternion = quat
            if self.enable_scale:
                scale = rel_scale * self.ref_scales[bone.parent.name] / self.ref_scales[bone]
                bone.scale = (scale, scale, scale)
            if receiver.is_recording:
                bone.keyframe_insert(data_path="rotation_quaternion", index=-1)
