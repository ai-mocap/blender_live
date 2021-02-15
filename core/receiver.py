import bpy
import asyncio
import errno
import json
import logging
from datetime import datetime

from . import animations, utils, minimal_hand

from os.path import dirname, abspath, join
import sys

# Add vendor directory to module search path
parent_dir = abspath(dirname(dirname(__file__)))
vendor_dir = join(parent_dir, 'vendor')
sys.path.append(vendor_dir)

import aiohttp  # noqa
import aiohttp.web  # noqa

logger = logging.getLogger(__name__)


class CptrError(Exception):
    pass


class Receiver:
    def run(self):
        self.loop.stop()
        self.loop.run_forever()
        self.process_data()
        self.handle_ui_updates()

    def process_data(self):
        while not self.queue.empty():
            data_raw = self.queue.get_nowait()
            data = json.loads(data_raw)
            if data.get('type') == 'error':
                logger.error(f"Received error {data}")
                raise CptrError(data['message'])
            pt = datetime.fromisoformat(data['ts'])
            current_timestamp = pt.timestamp()
            if self.prev_timestamp is not None:
                timestamp_delta = int((current_timestamp - self.prev_timestamp) * 100)
            else:
                timestamp_delta = 0
            frame_idx = bpy.context.scene.frame_current + timestamp_delta
            logger.debug(f"Hands: {data['hands'].keys()}")
            if bpy.context.scene.cptr_recording:
                bpy.context.scene.frame_set(frame_idx)
                bpy.data.scenes["Scene"].frame_end = frame_idx + 1
            left = data['hands'].get('Left')
            right = data['hands'].get('Right')
            if left:
                minimal_hand.process_bones(left['theta'], root_position=left['xyz'][9], hand='left')
            if right:
                minimal_hand.process_bones(right['theta'], root_position=right['xyz'][9], hand='right')

            self.prev_timestamp = current_timestamp
            logger.debug(f"Timestamps: {timestamp_delta} {current_timestamp} {self.prev_timestamp} {data['ts']}")
            animations.animate()

    def handle_ui_updates(self):
        utils.ui_refresh_properties()
        utils.ui_refresh_view_3d()

    async def websocket_handler(self, request):
        try:
            logger.debug('ws connected')
            ws = aiohttp.web.WebSocketResponse()
            await ws.prepare(request)

            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    self.queue.put_nowait(msg.data)
                    logger.debug(f'ws message appended to queue, new size={self.queue.qsize()}')
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.debug(f'ws connection closed with exception {ws.exception()}')
        except Exception:
            logger.exception("Exception in websocket_handler")
            raise
        finally:
            logger.debug('websocket connection closed')
        return ws

    async def run_websocket_server(self, context, port):
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
                await self.run_websocket_server(context, port=None)
                context.scene.cptr_receiver_port = self.site._port
            else:
                raise

        logger.debug("Started websocket server")

    def start(self, context):
        logger.debug('Starting')
        minimal_hand.init()
        self.loop = asyncio.get_event_loop()
        self.prev_timestamp = 0
        self.queue = asyncio.Queue()
        self.loop.run_until_complete(self.run_websocket_server(context, context.scene.cptr_receiver_port))
        logger.debug(f"Started listening on port {context.scene.cptr_receiver_port}")
        logger.debug(f"Length of queue is {self.queue.qsize()}")

    async def async_stop(self):
        logger.debug("async_stop enter")
        await self.runner.shutdown()
        await self.runner.cleanup()
        logger.debug("async_stop exit")

    def stop(self):
        logger.debug("Stopping")
        self.loop.run_until_complete(self.async_stop())
        logger.debug("Stopped")
