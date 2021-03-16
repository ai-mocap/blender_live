from bpy.types import Scene, Object
from bpy.props import IntProperty, BoolProperty, FloatProperty

from .core import recorder


def register():
    # Receiver
    Scene.cptr_receiver_port = IntProperty(
        name='Streaming Port',
        description="The port defined in Rokoko Studio",
        default=14043,
        min=1,
        max=65535
    )
    Scene.cptr_receiver_fps = IntProperty(
        name='FPS',
        description="How often is the data received",
        default=60,
        min=1,
        max=100
    )
    Scene.cptr_scene_scaling = FloatProperty(
        name='Scene Scaling',
        description="This allows you to scale the position of props and trackers."
                    "\nUseful to align their positions with armatures",
        default=1,
        precision=3,
        step=1
    )
    Scene.cptr_reset_scene_on_stop = BoolProperty(
        name='Reset Scene on Stop',
        description='This will reset the location and position of animated objects to the state of before starting the receiver',
        default=True
    )
    Scene.cptr_recording = BoolProperty(
        name='Toggle Recording',
        description='Start and stop recording of the data from Rokoko Studio',
        default=False,
        update=recorder.toggle_recording
    )

# Objects
    Object.cptr_use_custom_scale = BoolProperty(
        name='Use Custom Scale',
        description='Select this if the objects scene scaling should be overwritten',
        default=False,
    )
    Object.cptr_custom_scene_scale = FloatProperty(
        name='Custom Scene Scaling',
        description="This allows you to scale the position independently from the scene scale.",
        default=1,
        precision=3,
        step=1
    )

    # # Face shapekeys
    # for shape in animation_lists.face_shapes:
    #     setattr(Object, 'rsl_face_' + shape, StringProperty(
    #         name=shape,
    #         description='Select the shapekey that should be animated by this shape'
    #     ))
    #
    # # Actor bones
    # for bone in animation_lists.actor_bones.keys():
    #     setattr(Object, 'rsl_actor_' + bone, StringProperty(
    #         name=bone,
    #         description='Select the bone that corresponds to the actors bone'
    #     ))
