import os
import pathlib
from enum import Enum
from bpy.utils import previews

icons = None


class Icons(Enum):
    PAIRED = 'PAIRED'
    START_RECORDING = 'RECORD'
    STOP_RECORDING = 'STOP'
    RESTART = 'RESTART'

    def get_icon(self):
        return icons.get(self.value).icon_id


def load_icons():
    # Path to the icons folder
    # The path is calculated relative to this py file inside the addon folder
    icons_dir = pathlib.Path(os.path.dirname(__file__)).parent.resolve() / "resources" / "icons"

    pcoll = previews.new()

    # Load a preview thumbnail of a file and store in the previews collection
    pcoll.load('PAIRED', str(icons_dir / 'icon-paired-32.png'), 'IMAGE')
    pcoll.load('RECORD', str(icons_dir / 'icon-record-32.png'), 'IMAGE')
    pcoll.load('RESTART', str(icons_dir / 'icon-restart-32.png'), 'IMAGE')
    pcoll.load('STOP', str(icons_dir / 'icon-stop-white-32.png'), 'IMAGE')

    global icons
    icons = pcoll


def unload_icons():
    global icons
    if icons:
        previews.remove(icons)
