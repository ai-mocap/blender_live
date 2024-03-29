# Important plugin info for Blender
bl_info = {
    'name': 'CPTR.tech plugin for Blender',
    'author': 'CPTR.TECH',
    'category': 'Animation',
    'location': 'View 3D > Tool Shelf > CPTR',
    'description': 'Realtime view and record your data from CPTR.tech',
    'version': (0, 1, 6),
    'blender': (2, 80, 0),
    'wiki_url': 'https://app.cptr.tech/faq',
}

# If first startup of this plugin, load all modules normally
# If reloading the plugin, use importlib to reload modules
# This lets you do adjustments to the plugin on the fly without having to restart Blender
import sys
import os
import logging
if "bpy" not in locals():
    import bpy
    from . import core
    from . import panels
    from . import operators
    from . import properties
else:
    import importlib
    importlib.reload(core)
    importlib.reload(panels)
    importlib.reload(operators)
    importlib.reload(properties)


# List of all buttons and panels
classes = [
    panels.main.ReceiverPanel,
    operators.receiver.ReceiverStart,
    operators.receiver.ReceiverStop,
    operators.recorder.RecorderStart,
    operators.recorder.RecorderStop,
    operators.hands.ResetHands,
    operators.hands.LoadHands,
]


def check_unsupported_blender_versions():
    # Don't allow Blender versions older than 2.80
    if bpy.app.version < (2, 80):
        unregister()
        sys.tracebacklimit = 0
        raise ImportError('Blender versions older than 2.80 are not supported by CPTR plugin'
                          'Please use Blender 2.80 or later.')

    # Versions 2.80.0 to 2.80.74 are beta versions, stable is 2.80.75
    if (2, 80, 0) <= bpy.app.version < (2, 80, 75):
        unregister()
        sys.tracebacklimit = 0
        raise ImportError('You are still on the beta version of Blender 2.80!'
                          'Please update to the release version of Blender 2.80.')


# register and unregister all classes
def register():
    logging.basicConfig(level=os.getenv('LOGGING_LEVEL'))
    logging.debug("Loading CPTR plugin")

    # Check for unsupported Blender versions
    check_unsupported_blender_versions()

    for cls in classes:
        bpy.utils.register_class(cls)

    # Register all custom properties
    properties.register()

    # Load custom icons
    core.icon_manager.load_icons()

    from .core.receiver import receiver
    receiver.start_server()

    logging.debug("Loaded CPTR plugin")


def unregister():
    logging.debug("Unloading CPTR plugin")

    # Shut down receiver if the plugin is disabled while it is running
    from .core.receiver import receiver
    receiver.stop_server()

    # Unregister all classes
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass

    # Unload all custom icons
    core.icon_manager.unload_icons()
    logging.debug("Unloaded CPTR plugin")


if __name__ == '__main__':
    register()
