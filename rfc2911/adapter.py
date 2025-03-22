"""
    Adapter class 
    Control simple printer functions like print() or scan()
"""

from .constants import JobStateEnum, PrinterStateEnum,PrintWarningEnum,PrintErrorEnum
from types import FunctionType
from random import randint
from io import FileIO, IOBase

import time
import re

class PrintResult:
    success = 0
    malfunction_ink_supply_empty_error = 1
    malfunction_waste_full_error = 2

class BaseBrandingClass:
    PRINTER_NAME = "InkJet-A1"
    PRINTER_INFO = "LibrePrint InkJet A1"
    PRINTER_MAKE_AND_MODEL = "InkJet A1"
    @classmethod
    def from_ppd(cls,ppd:str|FileIO):
        """
            Create branding class from PPD
            
            ppd: Can be either the ppd file as a string, or a file descriptor-like object supporting .read()
        """
        if hasattr(ppd,"read"):
            data = ppd.read()
        elif type(ppd) == str:
            data = ppd
        else:
            raise TypeError(f"ppd argument must be readable or str, not {type(ppd)}")
        printer_name = re.search("\\*Product\\:.*",data)[0]
        printer_name = printer_name.split("\"")[1]
        printer_name = re.sub("[\\(\\)]","",printer_name)
        printer_make_and_model = printer_name
        printer_info = re.search("\\*ModelName\\:.*",data)[0]
        printer_info = printer_info.split("\"")[1]
        
        class PPD_Branding(cls):
            PRINTER_NAME = printer_name.replace(" ","-")
            PRINTER_INFO = printer_info
            PRINTER_MAKE_AND_MODEL = printer_make_and_model
        
        return PPD_Branding
        
        
        
def base_warning_function(warning_type: PrintWarningEnum,string):
    print("warning")
    print(warning_type)
    print(string)

class BaseAdapterClass:
    """
        Base class only suitable for testing or as a base for adapters, 
        
        please do not use directly.
    """
    def __init__(self,ppd:str,warnings_function: FunctionType = base_warning_function):
        self.ppd = ppd
        self.warnings = warnings_function
    def get_ink_level_max(self) -> int:
        """
            Returns maximum ink level.
        """
        return 100
    def get_ink_level_current(self) -> int:
        """
            Returns current ink level.
        """
        return 100
    def print_job_finished(self) -> bool:
        """
            Returns whether the last printing job has finished or not.
        """
        return True

    def print_postscript(self, fp:FileIO):
        with open(f"/tmp/pyrfc2911-{randint(11111111,99999999)}.ps","wb") as file:
            file.write(fp.read())

    def receive_job(self,job):
        """
            Should receive and process job.
            Should warn about low ink or almost full waste sponge.
            Should print postscript data into paper and return result.
            
            Alternatively, this function can be split to multiple functions.
        """
        
        # self.warnings(PrintWarningEnum.low_ink_supply,"yo bro ink low")
        self.print_postscript(job.file)
        job.state = JobStateEnum.processing
        time.sleep(5) # Emulate printing
        job.finish()
        job.file.close()
        
    def get_branding(self) -> BaseBrandingClass:
        """
            Should return branding information about the printer.
        """
        return BaseBrandingClass.from_ppd(self.ppd)
    
    @property
    def state(self):
        return PrinterStateEnum.idle
    
    @property
    def state_reasons(self):
        return [b"none"]
    
    @property
    def accepting(self):
        return True