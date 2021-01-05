import bpy
import asyncio
import json

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
        except BlockingIOError:
            error = ['Receiving no data!']
        except OSError as e:
            print('Packet error:', e.strerror)
            error = ['Packets too big!']
            force_error = True
        except AttributeError as e:
            print('Socket error:', e)
            error = ['Socket not running!']
            force_error = True

        if self.data_list:
            # Process animation data
            error, force_error = self.process_data()

        self.handle_ui_updates(received)
        self.handle_error(error, force_error)

    def process_data(self):
        try:
            for data_raw in self.data_list:
                data = json.loads(data_raw)
                minimal_hand.process_bones(self.line_no, data['theta'])
                minimal_hand.process_xyz(self.line_no, data['xyz'])
                self.line_no += 1
        except ValueError as exc:
            print('Packet contained no data', exc)
            return ['Packets contain no data!'], False
        except (UnicodeDecodeError, TypeError) as e:
            print('Wrong live data format! Use JSON v2!')
            print(e)
            return ['Wrong data format!', 'Use JSON v2 or higher!'], True
        except KeyError as e:
            print('KeyError:', e)
            return ['Incompatible JSON version!', 'Use the latest Studio', 'and plugin versions.'], True
        finally:
            self.data_list = []

        animations.animate()

        return '', False

    def handle_ui_updates(self, received):
        # Update UI every 5 seconds when packets are received continuously
        if received:
            self.i += 1
            self.i_np = 0
            if self.i % (bpy.context.scene.rsl_receiver_fps * 5) == 0:
                utils.ui_refresh_properties()
                utils.ui_refresh_view_3d()
            return

        # If receiving a packet after one second of no packets, update UI with next packet
        self.i_np += 1
        if self.i_np == bpy.context.scene.rsl_receiver_fps:
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
            print('REFRESH')
            return

        if not self.error_temp:
            self.error_temp = error
            if force_error:
                self.error_count = bpy.context.scene.rsl_receiver_fps - 1
            return

        if error == self.error_temp:
            self.error_count += 1
        else:
            self.error_temp = error
            if force_error:
                self.error_count = bpy.context.scene.rsl_receiver_fps
            else:
                self.error_count = 0

        if self.error_count == bpy.context.scene.rsl_receiver_fps:
            show_error = self.error_temp
            utils.ui_refresh_view_3d()
            print('REFRESH')

    async def websocket_handler(self, request):
        print('ws connected')
        ws = aiohttp.web.WebSocketResponse()
        await ws.prepare(request)

        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                self.data_list.append(msg.data)
                print(f'ws message appended to datalist, new size={len(self.data_list)}')
            elif msg.type == aiohttp.WSMsgType.ERROR:
                print('ws connection closed with exception %s' % ws.exception())

        print('websocket connection closed')

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
        minimal_hand.init()
        self.loop = asyncio.get_event_loop()
        self.line_no = 0
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

        print("Rokoko Studio Live started listening on port " + str(port))

    async def async_stop(self):
        await self.app.shutdown()
        await self.app.cleanup()

    def stop(self):
        print("CPTR stopping")
        self.loop.run_until_complete(self.async_stop())
        print("CPTR stopped")
