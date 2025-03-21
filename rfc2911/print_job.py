from .constants import JobStateEnum,JobStateReasonEnum
from io import BytesIO
from math import floor
from time import time

class Job:
    def __init__(self,id,state:JobStateEnum = None,reasons:list[bytes] = None):
        self.id = id
        self.file: BytesIO = BytesIO()
        self.start_time: int = floor(time())
        self.end_time: int = 1
        self.state: JobStateEnum = [state] or [JobStateEnum.pending]
        self.state_reasons = reasons or [b"none"]
    def finish(self,state=JobStateEnum.completed,reasons=None):
        if reasons == None: 
            reasons = [JobStateReasonEnum.complete_success]
        self.state = [state]
        self.state_reasons = [i.encode() for i in reasons]
        self.file.close()
        self.end_time = floor(time())