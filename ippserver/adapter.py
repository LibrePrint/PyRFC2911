"""
    Adapter class 
    Control simple printer functions like print() or scan()
"""

from types import FunctionType
from io import BytesIO

class PrintResult:
    success = 0
    malfunction_ink_supply_empty_error = 1
    malfunction_waste_full_error = 2

class BaseBranding:
    PRINTER_NAME = "A1"
    PRINTER_INFO = "LibrePrint InkJet A1"
    PRINTER_MAKE_AND_MODEL = "InkJet A1"

class BaseAdapterClass:
    def __init__(self,warnings_function: FunctionType):pass
    def get_ink_level_max(self) -> int:
        """
            Returns maximum ink level.
        """
    def get_ink_level_current(self) -> int:
        """
            Returns current ink level.
        """
    def print_job_finished(self) -> bool:
        """
            Returns whether the last printing job has finished or not.
        """
    def print_postscript(self,postscript_data: BytesIO) -> PrintResult:
        """
            Print postscript data into paper and return result.
            Should warn about low ink or almost full waste sponge.
        """
    def return_branding(self) -> BaseBranding:
        """
            Should return branding information about the printer.
        """
        