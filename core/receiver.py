import bpy

import asyncio
import errno
import logging
import sys
from datetime import datetime
from os.path import dirname, abspath, join

from . import minimal_hand

logger = logging.getLogger(__name__)

# Add vendor directory to module search path
parent_dir = abspath(dirname(dirname(__file__)))
vendor_dir = join(parent_dir, 'vendor')
sys.path.append(vendor_dir)

import aiohttp  # noqa
import aiohttp.web  # noqa

try:
    import orjson as json
except ModuleNotFoundError:
    logger.info("Module orjson is not found, installing using pip")
    try:
        import pip.__main__
        pip.__main__._main(['install', 'orjson', '-t', vendor_dir])
        import orjson as json
    except Exception:
        logger.exception("Failed to install orjson, using json module")
        import json


class CptrError(Exception):
    pass


class Receiver:
    def __init__(self):
        self.websocket_connection = None
        self.reset_state()

    def reset_state(self):
        self.is_running = False
        self.is_recording = False
        self.is_in_transition = False

    def step(self):
        self.loop.stop()
        self.loop.run_forever()
        return 0.01  # 60 FPS

    def process_data(self, data):
        if isinstance(data['ts'], str):
            pt = datetime.fromisoformat(data['ts'])
            current_timestamp = pt.timestamp()
        else:
            current_timestamp = data['ts']
        if self.prev_timestamp is not None:
            timestamp_delta = int((current_timestamp - self.prev_timestamp) * 100)
        else:
            timestamp_delta = 0
        frame_idx = bpy.context.scene.frame_current + timestamp_delta
        if self.is_recording:
            bpy.context.scene.frame_set(frame_idx)
            bpy.data.scenes["Scene"].frame_end = frame_idx + 1
        if 'bones' in data:
            bones = data['bones']
            position = data['position']
            logger.debug(f"Bones: {bones.keys()}")
            self.body.process_bones(bones)
            self.body.set_position(position)
        elif 'hands' in data:
            logger.debug(f"Hands: {data['hands'].keys()}")
            left = data['hands'].get('Left')
            right = data['hands'].get('Right')
            if left:
                self.left_hand.process_bones(left['relative_rotations'], left['relative_scales'])
            if right:
                self.right_hand.process_bones(right['relative_rotations'], right['relative_scales'])

        self.prev_timestamp = current_timestamp
        logger.debug(f"Timestamps: {timestamp_delta} {current_timestamp} {self.prev_timestamp} {data['ts']}")

    async def websocket_handler(self, request):
        logger.debug('websocket connected')
        ws = aiohttp.web.WebSocketResponse()
        await ws.prepare(request)
        if self.websocket_connection is not None:
            logger.error("Websocket is already connected, dropping connection")
            return ws
        self.websocket_connection = ws

        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                    except json.JSONDecodeError:
                        logger.exception(f"Failed to decode: {msg.data}")
                    if data['type'] == 'state':
                        logger.debug(f"Received state {data}")
                        self.is_running, was_running = data['isRunning'], self.is_running
                        if self.is_running != was_running:
                            self.init()
                        self.is_in_transition = False
                    elif data['type'] == 'frame':
                        logger.info(f"Received frame {data['ts']}")
                        if self.is_running:
                            self.process_data(data)
                        else:
                            logger.warning('received ws message when we are not running. discarding')
                    elif data['type'] == 'error':
                        logger.error(f"Received error {data}")
                        raise CptrError(data['message'])
                    else:
                        logger.error(f"Unexpected data type {data['type']}")
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.debug(f'ws connection closed with exception {ws.exception()}')
        except Exception:
            logger.exception("Exception in websocket_handler")
            raise
        finally:
            logger.debug('websocket connection closed')
            self.websocket_connection = None
            self.reset_state()
        return ws

    async def run_websocket_server(self, port):
        self.app = aiohttp.web.Application()
        self.app.add_routes([aiohttp.web.get('/ws', self.websocket_handler)])
        self.runner = aiohttp.web.AppRunner(self.app)
        await self.runner.setup()
        self.site = aiohttp.web.TCPSite(
            self.runner,
            host='0.0.0.0',
            port=port,
            reuse_address=True,
            reuse_port=True if sys.platform == 'linux' else None,
            shutdown_timeout=0,
        )
        try:
            await self.site.start()
        except OSError as exc:
            if exc.errno == errno.EADDRINUSE:
                logger.debug(f"Port {port} is in use, autoselecting free port")
                await self.run_websocket_server(port=None)
            else:
                raise

        logger.debug("Started websocket server")

    def get_port(self):
        return self.site._port

    def init(self):
        if 0:
            self.left_hand = minimal_hand.Hand("left_")
            self.right_hand = minimal_hand.Hand("right_")

            if not self.left_hand.object and not self.right_hand.object:
                minimal_hand.load_hands()
            self.left_hand.save_pose()
            self.right_hand.save_pose()
        try:
            self.body = minimal_hand.Skeleton('root')
        except minimal_hand.InvalidRoot:
            self.body = minimal_hand.load_body()
        self.body.save_pose()

        if bpy.context.object is not None:
            bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")

    @property
    def is_connected(self):
        return self.websocket_connection is not None

    def start(self):
        self.is_in_transition = True
        self.loop.run_until_complete(self.send_command('start'))

    def stop(self):
        self.is_in_transition = True
        self.loop.run_until_complete(self.send_command('stop'))

    async def send_command(self, command):
        await self.websocket_connection.send_json(dict(type='command', command=command))

    def start_server(self):
        logger.debug("Starting server")
        self.loop = asyncio.get_event_loop()
        self.prev_timestamp = 0
        prefs = bpy.context.preferences.addons['cptr-tech'].preferences
        self.loop.run_until_complete(self.run_websocket_server(prefs.receiver_port))
        bpy.app.timers.register(self.step, persistent=True)
        logger.debug("Started server")

    async def async_stop_server(self):
        await self.runner.shutdown()
        await self.runner.cleanup()

    def stop_server(self):
        logger.debug("Stopping server")
        try:
            bpy.app.timers.unregister(self.step)
        except ValueError:
            pass
        self.loop.run_until_complete(self.async_stop_server())
        self.reset_state()
        logger.debug("Stopped server")

    def change_port(self, context):
        self.stop_server()
        self.start_server()


def change_port(self, context):
    receiver.change_port(context)


receiver: Receiver = Receiver()
