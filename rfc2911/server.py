from http.server import BaseHTTPRequestHandler
from .behaviour import Behaviour
from .request import IppRequest
from pathlib import Path
from io import BytesIO

import socketserver
import requests
import os

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
        www_default = os.path.join(os.path.abspath(os.path.dirname(__file__)),"www_default")
        if "CUPS" in self.headers["User-Agent"]:
            if self.path.endswith(".ppd"):
                self.send_headers(status=200, content_type='text/plain')
                self.wfile.write(self.behaviour.ppd.encode())
        try:
            response: requests.Response = requests.get(url="http://"+self.www_url+self.path,headers=self.headers)
        except:
            self.send_headers(status=200, content_type='text/html')
            self.end_headers()
            self.wfile.write(self.internal_error_html("Exception occurred when contacting WWW control panel.","None"))
            return
        if response.status_code == 200:
            for key, value in response.headers:
                self.send_headers(key,value)
            self.end_headers()
            self.wfile.write(response.content)
        else: 
            self.send_headers(status=200, content_type='text/html')
            self.end_headers()
            self.wfile.write(self.internal_error_html(response.status_code,response.headers))
        
    def internal_error_html(self,status_code,headers):
        headers = str(self.headers)        
        www_default = os.path.join(os.path.abspath(os.path.dirname(__file__)),"www_default") # i hope this fucking works
        return Path(www_default,"internal_error.html").read_text().replace("%%STATUSCODE",status_code).replace("%%HEADERS",headers).encode()
        
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
        self.address = (host,port)
        self.behaviour.address = (host,port)
        socketserver.ThreadingTCPServer.__init__(self, (host,port), IPPRequestHandler)
        self.RequestHandlerClass.www_url = www_url.lstrip("http://")
        self.RequestHandlerClass.behaviour = behaviour
    def run(self):
        print(" * Serving PyRFC2911 printer")
        print(f" * You can visit the web page you provided on http://{self.address[0]}:{self.address[1]}")
        print(" * You can also add the printer with the same URL")
        self.serve_forever()
        
    def __getattr__(self):
        return "hi"