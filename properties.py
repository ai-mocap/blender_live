from bpy.props import IntProperty
from bpy.types import AddonPreferences
from bpy.utils import register_class

from .core import receiver


class CptrPreferences(AddonPreferences):
    bl_idname = 'cptr-tech'
    receiver_port: IntProperty(
        name='Streaming Port',
        description="The port defined to accept data",
        default=14043,
        min=1,
        max=65535,
        update=receiver.change_port,
    )


def register():
    register_class(CptrPreferences)
