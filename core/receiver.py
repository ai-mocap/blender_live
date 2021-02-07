import bpy
import asyncio
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

error_temp = ''
show_error = []
logger = logging.getLogger(__name__)


class Receiver:
    # Redraw counters
    i = -1    # Number of continuous received packets
    i_np = 0  # Number of continuous no packets

    # Error counters
    error_temp = []
    error_count = 0

    def run(self):
        received = True
        error = []
        force_error = False

        # Try to receive a packet
        try:
            self.loop.stop()
            self.loop.run_forever()
        except Exception as err:
            error = [f'Error while running: {err}']
            logger.exception("Error in run_forever")
            force_error = True

        if self.data_list:
            error, force_error = self.process_data()

        self.handle_ui_updates(received)
        self.handle_error(error, force_error)

    def process_data(self):
        try:
            for data_raw in self.data_list:
                data = json.loads(data_raw)
                pt = datetime.fromisoformat(data['ts'])
                current_timestamp = pt.timestamp()
                if self.prev_timestamp is not None:
                    timestamp_delta = current_timestamp - self.prev_timestamp
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
                    minimal_hand.process_bones(left['theta'], root_position=left['xyz'][0], hand='left')
                if right:
                    minimal_hand.process_bones(right['theta'], root_position=right['xyz'][0], hand='right')

                self.prev_timestamp = current_timestamp
                logger.debug(f"Timestamps: {timestamp_delta} {current_timestamp} {self.prev_timestamp} {data['ts']}")
        except Exception:
            logger.exception("Unexpected error")
            return ['Error processing data'], False
        else:
            animations.animate()
            return '', False
        finally:
            self.data_list = []

    def handle_ui_updates(self, received):
        # Update UI every 5 seconds when packets are received continuously
        if received:
            self.i += 1
            self.i_np = 0
            if self.i % (bpy.context.scene.cptr_receiver_fps * 5) == 0:
                utils.ui_refresh_properties()
                utils.ui_refresh_view_3d()
            return

        # If receiving a packet after one second of no packets, update UI with next packet
        self.i_np += 1
        if self.i_np == bpy.context.scene.cptr_receiver_fps:
            self.i = -1

    def handle_error(self, error, force_error):
        global show_error
        if not error:
            self.error_count = 0
            if not show_error:
                return
            self.error_temp = []
            show_error = []
            utils.ui_refresh_view_3d()
            logger.debug('REFRESH')
            return

        if not self.error_temp:
            self.error_temp = error
            if force_error:
                self.error_count = bpy.context.scene.cptr_receiver_fps - 1
            return

        if error == self.error_temp:
            self.error_count += 1
        else:
            self.error_temp = error
            if force_error:
                self.error_count = bpy.context.scene.cptr_receiver_fps
            else:
                self.error_count = 0

        if self.error_count == bpy.context.scene.cptr_receiver_fps:
            show_error = self.error_temp
            utils.ui_refresh_view_3d()
            logger.debug('REFRESH')

    async def websocket_handler(self, request):
        logger.debug('ws connected')
        ws = aiohttp.web.WebSocketResponse()
        await ws.prepare(request)

        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                self.data_list.append(msg.data)
                logger.debug(f'ws message appended to datalist, new size={len(self.data_list)}')
            elif msg.type == aiohttp.WSMsgType.ERROR:
                logger.debug('ws connection closed with exception %s' % ws.exception())

        logger.debug('websocket connection closed')

        return ws

    async def run_websocket_server(self):
        self.app = aiohttp.web.Application()
        self.app.add_routes([aiohttp.web.get('/ws', self.websocket_handler)])
        self.runner = aiohttp.web.AppRunner(self.app)
        await self.runner.setup()
        self.site = aiohttp.web.TCPSite(
            self.runner,
            host='0.0.0.0',
            port=12345,
            reuse_address=True,
            reuse_port=True,
        )
        await self.site.start()

    def start(self, port):
        logger.debug('started')
        minimal_hand.init()
        self.loop = asyncio.get_event_loop()
        self.prev_timestamp = 0
        self.data_list = []
        self.loop.create_task(self.run_websocket_server())
        self.loop.stop()
        self.loop.run_forever()

        self.i = -1
        self.i_np = 0

        self.error_temp = []
        self.error_count = 0

        global show_error
        show_error = False

        logger.debug("CPTR started listening on port " + str(port))
        logger.debug(f"Length of queue is {len(self.data_list)}")

    async def async_stop(self):
        await self.app.shutdown()
        await self.app.cleanup()

    def stop(self):
        logger.debug("CPTR stopping")
        self.loop.run_until_complete(self.async_stop())
        logger.debug("CPTR stopped")
