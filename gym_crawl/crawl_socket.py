'''
DCSS socket connections
'''
from abc import ABC, abstractmethod
import asyncio
import json
import logging
import os
import socket
import time
import websockets
import zlib


logger = logging.getLogger('crawl-socket')
decomp = zlib.decompressobj(-zlib.MAX_WBITS)

def pretty_json_custom(msg):
    result = ''
    indent = 0
    prev = None
    quote = None
    for c in msg:
        if quote:
            if c == quote:
                quote = None
        elif c == '"' or c == "'":
            quote = c
        elif c == '{' or c == '[':
            if result != '':
                indent += 2
                result += '\n'
                result += ' ' * indent
        elif c == '}' or c == ']':
            if prev == '}' or prev == ']':
                result += '\n'
                result += ' ' * indent
            indent -= 2
        
        if quote or c != '\n':
            result += c
            prev = c
            
    return result

   
def pretty_json(msg):
    if '"msg":"map"' in msg:
    #if False:
        return pretty_json_custom(msg)
    else:
        return json.dumps(json.loads(msg), indent=2)

class Socket(ABC):
    '''Abstract base class'''
    
    sock = None
            
    def __init__(self):
        pass
    
    @abstractmethod
    def open(self):
        pass
    
    @abstractmethod
    def close(self):
        pass
    
    @abstractmethod
    def send(self, msg):
        pass
    
    @abstractmethod
    def receive(self):
        pass
    
    def send_json(self, msg):
        '''Encode json message and send'''
        if logger.isEnabledFor(logging.INFO):
            logger.info('Sending:\n' + json.dumps(msg, indent=2))
        json_msg = json.dumps(msg).replace("</", "<\\/")
        self.send(json_msg)

    def receive_json(self, timeout=0.5):
        '''Receive and decode json message'''
        json_msg = self.receive(timeout)
        if json_msg is None or json_msg == '':
            return None
        prefix = ''
        if json_msg[0] == '*':
            prefix = json_msg[0]
            json_msg = json_msg[1:]
        msg = json.loads(json_msg)
        if logger.isEnabledFor(logging.INFO):
            logger.info('Received:\n' + prefix + pretty_json(json_msg))
        return msg

class UnixSocket(Socket):
    ''' Unix socket connection'''

    # constants
    SERVER_SOCKET_PATH = '/var/tmp/crawl_server.sock'
    CLIENT_SOCKET_PATH = '/var/tmp/crawl_client.sock'
    SEND_BUFFER_LEN = 2048
    RCV_BUFFER_LEN = 208 * 1024

    def __init__(self):
        pass
    
    def open(self):
        self.close()
        
        # create a datagram (connectionless) socket    
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.sock.settimeout(10)

        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # set send buffer size
        if (self.sock.getsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF) < self.SEND_BUFFER_LEN):
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, self.SEND_BUFFER_LEN)

        # set receive buffer size
        if (self.sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF) < self.RCV_BUFFER_LEN):
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.RCV_BUFFER_LEN)

        self.sock.bind(self.CLIENT_SOCKET_PATH)
    
    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None
            
        if os.path.exists(self.CLIENT_SOCKET_PATH):
            os.unlink(self.CLIENT_SOCKET_PATH)
   
    def send(self, msg):
        try:
            data = msg.encode('utf-8')
            self.sock.sendto(data, self.SERVER_SOCKET_PATH)
        except socket.timeout:
            logger.error("Socket send timeout", exc_info=True)
            self.close()
   
    def receive(self):
        data = ''
        tries = 0
        while len(data) == 0 or data[-1] != '\n':
            tries += 1
            try:
                chunk = self.sock.recv(self.RCV_BUFFER_LEN, socket.MSG_DONTWAIT)
                if isinstance(chunk, bytes):
                    chunk = chunk.decode("utf-8")
                #logger.info("Got data chunk: " + chunk)
                data += chunk
            except socket.timeout:
                if tries < 5:
                    time.sleep(0.01)
                else:
                    logger.error("Socket receive timeout")
                    self.close()
                    return ''
    
        if tries > 1:
            logger.info("Took {} tries to get data".format(tries))
    
        return data


# Because Python 3.6 doesn't have async.run()
def run_async(function, timeout=0.5):
    future = asyncio.wait_for(function, timeout=timeout)
    loop = asyncio.get_event_loop()
    try:
        return loop.run_until_complete(future)
    except asyncio.TimeoutError:
        pass


class WebSocket(Socket):
    '''Websocket connection'''
    
    def __init__(self, server_uri='localhost:8080'):
        server_uri = server_uri.replace('http://', '')
        self.websocket_uri = 'ws://' + server_uri + '/socket'
    
    async def _open_impl(self):
        self.sock = await websockets.connect(self.websocket_uri)

    def open(self):
        self.close()
        
        #futures = [asyncio.wait_for(self._open_impl(), timeout=0.5)]
        #loop = asyncio.get_event_loop()
        #loop.run_until_complete(asyncio.wait(futures))
        run_async(self._open_impl())

        if not self.sock or not self.sock.open:
            errmsg = 'Unable to open connection to ' + self.websocket_uri
            logger.critical(errmsg)
            raise RuntimeError(errmsg)
    
    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None

    async def _send_impl(self, msg):
        await self.sock.send(msg)

    def send(self, msg):
        run_async(self._send_impl(msg))

    async def _receive_impl(self):
        data = await self.sock.recv()
        return data

    def receive(self, timeout=0.5):
        logger.debug('Receive started')
        data = run_async(self._receive_impl(), timeout)
        
        msg = None
        if data is None or data == '':
            logger.warn('No response received')
        else:

            # why do we do this???
            data += bytes([0, 0, 255, 255])
            
            msg = decomp.decompress(data)
            msg = msg.decode("utf-8")

        logger.debug('Receive finished')
        return msg

        