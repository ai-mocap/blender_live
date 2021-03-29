import bpy


def ui_refresh_all():
    # Refreshes all panels
    for windowManager in bpy.data.window_managers:
        for window in windowManager.windows:
            for area in window.screen.areas:
                area.tag_redraw()
