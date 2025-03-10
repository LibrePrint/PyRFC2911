from .constants import JobStateEnum,JobStateReasonEnum
from io import BytesIO
from math import floor
from time import time

class Job:
    def __init__(self,id,state:JobStateEnum = None,state_reasons:list[bytes] = None):
        self.id = id
        self.file: BytesIO = BytesIO()
        self.start_time: int = floor(time())
        self.end_time: int = 1
        self.state: JobStateEnum = state or JobStateEnum.pending
        self.state_reasons = state or [b"none"]
    def finish(self,state=JobStateEnum.completed,reason=JobStateReasonEnum.complete_success):
        self.state = JobStateEnum.completed
        self.state_reasons = [reason.encode()]
        self.end_time = floor(time())