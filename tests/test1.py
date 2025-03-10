import sys
sys.path.append(".")
sys.path.append("..")

from rfc2911.behaviour import ModelBehaviour
from rfc2911.adapter import BaseAdapterClass
from rfc2911.server import IPPServer

IPPServer(
    "127.0.0.1",
    8000,
    "/controls",
    ModelBehaviour(
        True,
        ".",
        BaseAdapterClass(print)
    )
).serve_forever()