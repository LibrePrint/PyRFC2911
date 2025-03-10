from http.server import BaseHTTPRequestHandler
from .behaviour import Behaviour
from .request import IppRequest
from io import BytesIO

import socketserver
import requests

def read_chunked(rfile):
    def _get_next_chunk(rfile):
        while True:
            chunk_size_s = rfile.readline()
            if not chunk_size_s:
                raise RuntimeError(
                    'Socket closed in the middle of a chunked request'
                )
            if chunk_size_s.strip() != b'':
                break

        chunk_size = int(chunk_size_s, 16)
        if chunk_size == 0:
            return b''
        chunk = rfile.read(chunk_size)
        return chunk
    while True:
        chunk = _get_next_chunk(rfile)
        if chunk == b'':
            rfile.close()
            break
        else:
            yield chunk


class IPPRequestHandler(BaseHTTPRequestHandler):
    default_request_version = "HTTP/1.1"
    protocol_version = "HTTP/1.1"

    def parse_request(self):
        ret = BaseHTTPRequestHandler.parse_request(self)
        if 'chunked' in self.headers.get('transfer-encoding', ''):
            self.rfile = BytesIO(b"".join(read_chunked(self.rfile)))
        self.close_connection = True
        return ret

    if not hasattr(BaseHTTPRequestHandler, "send_response_only"):
        def send_response_only(self, code, message=None):
            """Send the response header only."""
            if message is None:
                if code in self.responses:
                    message = self.responses[code][0]
                else:
                    message = ''
            if not hasattr(self, '_headers_buffer'):
                self._headers_buffer = []
            self._headers_buffer.append(
                (
                    "%s %d %s\r\n" % (self.protocol_version, code, message)
                ).encode('latin-1', 'strict')
            )

    def send_headers(self, status=200, content_type='text/plain',
                     content_length=None):
        self.log_request(status)
        self.send_response_only(status, None)
        self.send_header('Server', 'pyrfc2911')
        self.send_header('Date', self.date_time_string())
        self.send_header('Content-Type', content_type)
        if content_length:
            self.send_header('Content-Length', '%u' % content_length)
        self.send_header('Connection', 'close')
        self.end_headers()

    def do_POST(self):
        self.handle_ipp()

    def do_GET(self):
        self.handle_www()

    def handle_www(self):
        response: requests.Response = requests.get(url=self.www_url+self.path,headers=self.headers)
        for key, value in response.headers:
            self.send_headers(key,value)
        self.end_headers()
        self.wfile.write(response.content.decode())
        

    def handle_expect_100(self):
        return True

    def handle_ipp(self):
        self.ipp_request = IppRequest.from_file(self.rfile)
        
        if self.server.behaviour.expect_page_data_follows(self.ipp_request):
            self.send_headers(
                status=100, content_type='application/ipp'
            )
            postscript_file = self.rfile
        else:
            postscript_file = None

        ipp_response = self.server.behaviour.handle_ipp(
            self.ipp_request, postscript_file
        ).to_string()
        self.send_headers(
            status=200, content_type='application/ipp',
            content_length=len(ipp_response)
        )
        self.wfile.write(ipp_response)
        

class IPPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    def __init__(self, host: str, port: int, www_url: str, behaviour: Behaviour):
        """
            Create IPP server
            
            Args:
                host (str): Hostname e.g. 127.0.0.1 or 0.0.0.0
                
                port (int): Port e.g. 
                
                www_url (str): URL for HTML GET requests e.g. 127.0.0.1:8080
                    
                    This should be a control panel
        """
        self.behaviour = behaviour
        self.behaviour.address = (host,port)
        socketserver.ThreadingTCPServer.__init__(self, (host,port), IPPRequestHandler)
        self.RequestHandlerClass.www_url = www_url
    def run(self):
        self.server_forever()