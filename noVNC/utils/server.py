#!/usr/bin/env python
#! --encoding:utf-8--
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2012 Openstack, LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#!/usr/bin/env python

'''
Websocket proxy that is compatible with Openstack Nova.
Leverages websockify by Joel Martin
'''

import socket
import sys

import websockify


class NovaWebSocketProxy(websockify.WebSocketProxy):
    def __init__(self, *args, **kwargs):
        websockify.WebSocketProxy.__init__(self, *args, **kwargs)

    def new_client(self):
        """
        Called after a new WebSocket connection has been established.
        """
        host = "192.2.3.44"
        port = 80
        vnc_location = "/console?uuid=3e282897-9770-f843-9085-aefc7e0810ad&session_id=OpaqueRef:f5051c58-8877-023e-8a49-011ff18d0340"
         
        # Connect to the target
        self.msg("connecting to: %s:%s" % (
                 host, port))
        # 创建到XenServer的连接
        tsock = self.socket(host, port,
                connect=True)

        # 连接到XenServer并处理返回的头部
        # Handshake as necessary
        tsock.send("CONNECT %s HTTP/1.1\r\n\r\n" %
                    vnc_location)
        
        data = tsock.recv(17)
        data = tsock.recv(24)
        data = tsock.recv(35)
        data = tsock.recv(2)
        
        if self.verbose and not self.daemon:
            print(self.traffic_legend)

        # Start proxying
        try:
            # 将连接到XenServer的socket作为参数传递给do_proxy
            self.do_proxy(tsock)
        except:
            if tsock:
                tsock.shutdown(socket.SHUT_RDWR)
                tsock.close()
                self.vmsg("%s:%s: Target closed" % (host, port))
            raise


if __name__ == '__main__':
    server = NovaWebSocketProxy(listen_host="127.0.0.1", listen_port=1999, verbose=True)
    server.start_server()