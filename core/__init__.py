if "bpy" not in locals():
    import bpy
    from . import receiver
    from . import utils
else:
    import importlib

    importlib.reload(receiver)
    importlib.reload(utils)
