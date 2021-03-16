if "bpy" not in locals():
    import bpy
    from . import receiver
    from . import hands
else:
    import importlib
    importlib.reload(receiver)
    importlib.reload(hands)
