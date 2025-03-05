from constants import JobStateEnum
from io import BytesIO
from math import floor
from time import time

class Job:
    def __init__(self,id):
        self.id = id
        self.file: BytesIO = BytesIO()
        self.start_time: int = floor(time())
        self.end_time: int = 1
        self.state: JobStateEnum
    def finish(self,id):
        self.end_time = floor(time())