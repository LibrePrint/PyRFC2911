import sys
sys.path.append(".")
sys.path.append("..")

from ippserver.behaviour import ModelBehaviour
from ippserver.adapter import BaseAdapterClass
from ippserver.server import IPPServer

IPPServer(
    "127.0.0.1",
    8000,
    "/controls",
    ModelBehaviour(
        True,
        ".",
        "tests/.ppd",
        BaseAdapterClass(print)
    )
).serve_forever()