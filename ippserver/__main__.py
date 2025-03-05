import sys, os.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .behaviour import ModelBehaviour
from .server import run_server, IPPServer, IPPRequestHandler

def main(args=None):

    server = IPPServer(
        (parsed_args.host, parsed_args.port),
        IPPRequestHandler,
        behaviour_from_parsed_args(parsed_args))
    run_server(server)

if __name__ == "__main__":
    main()
