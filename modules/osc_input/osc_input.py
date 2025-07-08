from pythonosc import dispatcher, osc_server
import threading
import socket
from modules.module_base import BaseModule


class OSCInput(BaseModule):
    def __init__(self, config, manifest, log_callback=print):
        super().__init__(config, manifest, log_callback)
        self.server = None
        self.thread = None
        self.callback = None  # ← For message_router

    def _osc_handler(self, address, *args):
        msg = f"Received: {address} {args}"
        self.log_message(msg)
        if self.callback:
            self.callback({
                "address": address,
                "args": args
            })

    def set_event_callback(self, callback_fn):
        self.callback = callback_fn

    def start(self):
        if self.running:
            return

        self.running = True
        port = self.config.get("port", 9000)
        address = self.config.get("osc_address", "/trigger")

        disp = dispatcher.Dispatcher()
        disp.map(address, self._osc_handler)

        try:
            self.server = osc_server.ThreadingOSCUDPServer(
                (self._get_local_ip(), port),
                disp
            )
        except OSError as e:
            self.log_message(f"⚠️ Failed to bind to port {port}: {e}")
            self.running = False
            return

        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()
        self.log_message(f"OSC server listening on port {port} for address '{address}'")

    def stop(self):
        if not self.running:
            return
        self.running = False
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        if self.thread:
            self.thread.join()
            self.thread = None
        self.log_message("OSC server stopped.")

    def _get_local_ip(self):
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"
