from .parsers import Integer, Enum, Boolean
from .adapter import BaseAdapterClass
from .request import IppRequest
from threading import Thread
from .print_job import Job
from .ppd import ModelPPD
from .constants import (
    PrinterStateEnum,
    StatusCodeEnum, 
    OperationEnum, 
    JobStateEnum, 
    SectionEnum, 
    TagEnum
)


import random
import time

def get_job_id(req):
    # kept for backwards compatibility
    return Integer.from_bytes(
            req.only(
                SectionEnum.operation,
                b'job-id',
                TagEnum.integer
            )
        ).integer

def read_in_blocks(postscript_file):
    while True:
        block = postscript_file.read(1024)
        if block == b'':
            break
        else:
            yield block

class Behaviour(object):
    """Do anything in response to IPP requests"""
    version = (1, 1)

    def __init__(self, ppd=None):
        self.ppd = ppd

    def expect_page_data_follows(self, ipp_request):
        return ipp_request.opid_or_status == OperationEnum.print_job

    def handle_ipp(self, ipp_request, postscript_file):
        command_function = self.get_handle_command_function(
            ipp_request.opid_or_status
        )
        return command_function(ipp_request, postscript_file)

    def get_handle_command_function(self, opid_or_status):
        raise NotImplementedError()


class AllCommandsReturnNotImplemented(Behaviour):
    """A printer which responds to all commands with a not implemented error.

    There's no real use for this, it's just an example.
    """
    def get_handle_command_function(self, _opid_or_status):
        return self.operation_not_implemented_response

    def operation_not_implemented_response(self, req, _psfile):
        attributes = self.minimal_attributes()
        return IppRequest(
            self.version,
            StatusCodeEnum.server_error_operation_not_supported,
            req.request_id,
            attributes)


class StatelessPrinter(Behaviour):
    """
    BROKEN USE MODELBEHAVIOUR INSTEAD
    
    A minimal printer which implements all the things a printer needs to work.

    The printer calls handle_postscript() for each print job.
    It says all print jobs succeed immediately: there are some stub functions like create_job() which subclasses could use to keep track of jobs, eg: if operation_get_jobs_response wants to return something sensible.
    """

    def get_handle_command_function(self, opid_or_status):
        commands = {
            OperationEnum.get_printer_attributes: self.operation_printer_list_response,
            OperationEnum.cups_list_all_printers: self.operation_printer_list_response,
            OperationEnum.cups_get_default: self.operation_printer_list_response,
            OperationEnum.validate_job: self.operation_validate_job_response,
            OperationEnum.get_jobs: self.operation_get_jobs_response,
            OperationEnum.get_job_attributes: self.operation_get_job_attributes_response,
            OperationEnum.print_job: self.operation_print_job_response,
        }

        try:
            command_function = commands[opid_or_status]
        except KeyError:
            command_function = self.operation_not_implemented_response
        return command_function

    def operation_not_implemented_response(self, req, _psfile):
        attributes = self.minimal_attributes()
        return IppRequest(
            self.version,
            # StatusCodeEnum.server_error_operation_not_supported,
            StatusCodeEnum.server_error_internal_error,
            req.request_id,
            attributes)

    def operation_printer_list_response(self, req, _psfile):
        attributes = self.printer_list_attributes()
        return IppRequest(
            self.version,
            StatusCodeEnum.ok,
            req.request_id,
            attributes)

    def operation_validate_job_response(self, req, _psfile):
        # TODO this just pretends it's ok!
        # TODO what the fuck
        attributes = self.minimal_attributes()
        return IppRequest(
            self.version,
            StatusCodeEnum.ok,
            req.request_id,
            attributes)

    def operation_get_jobs_response(self, req, _psfile):
        # an empty list of jobs, which probably breaks the rfc 
        # god f--king damnit ipp
        # if the client asked for completed jobs
        # https://tools.ietf.org/html/rfc2911#section-3.2.6.2
        attributes = self.minimal_attributes()
        return IppRequest(
            self.version,
            StatusCodeEnum.ok,
            req.request_id,
            attributes)

    def operation_print_job_response(self, req, psfile):
        job_obj = self.create_job()
        attributes = self.print_job_attributes(
            job_obj.id, JobStateEnum.pending,
            [b'job-incoming', b'job-data-insufficient']
        )
        self.handle_postscript(job_obj, psfile)
        return IppRequest(
            self.version,
            StatusCodeEnum.ok,
            req.request_id,
            attributes)

    def operation_get_job_attributes_response(self, req, _psfile):
        # Should have all these attributes:
        # https://tools.ietf.org/html/rfc2911#section-4.3

        job_id = get_job_id(req)
        attributes = self.print_job_attributes(
            job_id,
            JobStateEnum.completed,
            [b'none']
        )
        return IppRequest(
            self.version,
            StatusCodeEnum.ok,
            req.request_id,
            attributes)

    def minimal_attributes(self):
        return {
            # This list comes from
            # https://tools.ietf.org/html/rfc2911
            # Section 3.1.4.2 Response Operation Attributes
            (
                SectionEnum.operation,
                b'attributes-charset',
                TagEnum.charset
            ): [b'utf-8'],
            (
                SectionEnum.operation,
                b'attributes-natural-language',
                TagEnum.natural_language
            ): [b'en'],
        }

    def printer_list_attributes(self):
        attr = {
            # rfc2911 section 4.4
            (
                SectionEnum.printer,
                b'printer-uri-supported',
                TagEnum.uri
            ): [self.printer_uri],
            (
                SectionEnum.printer,
                b'uri-authentication-supported',
                TagEnum.keyword
            ): [b'none'],
            (
                SectionEnum.printer,
                b'uri-security-supported',
                TagEnum.keyword
            ): [b'none'],
            (
                SectionEnum.printer,
                b'printer-name',
                TagEnum.name_without_language
            ): [b'ipp-printer.py'],
            (
                SectionEnum.printer,
                b'printer-info',
                TagEnum.text_without_language
            ): [b'Printer using ipp-printer.py'],
            (
                SectionEnum.printer,
                b'printer-make-and-model',
                TagEnum.text_without_language
            ): [b'h2g2bob\'s ipp-printer.py 0.00'],
            (
                SectionEnum.printer,
                b'printer-state',
                TagEnum.enum
            ): [Enum(3).bytes()],  # XXX 3 is idle
            (
                SectionEnum.printer,
                b'printer-state-reasons',
                TagEnum.keyword
            ): [b'none'],
            (
                SectionEnum.printer,
                b'ipp-versions-supported',
                TagEnum.keyword
            ): [b'1.1'],
            (
                SectionEnum.printer,
                b'operations-supported',
                TagEnum.enum
            ): [
                Enum(x).bytes()
                for x in (
                    OperationEnum.print_job,  # (required by cups)
                    OperationEnum.validate_job,  # (required by cups)
                    OperationEnum.cancel_job,  # (required by cups)
                    OperationEnum.get_job_attributes,  # (required by cups)
                    OperationEnum.get_printer_attributes,
                )],
            (
                SectionEnum.printer,
                b'multiple-document-jobs-supported',
                TagEnum.boolean
            ): [Boolean(False).bytes()],
            (
                SectionEnum.printer,
                b'charset-configured',
                TagEnum.charset
            ): [b'utf-8'],
            (
                SectionEnum.printer,
                b'charset-supported',
                TagEnum.charset
            ): [b'utf-8'],
            (
                SectionEnum.printer,
                b'natural-language-configured',
                TagEnum.natural_language
            ): [b'en'],
            (
                SectionEnum.printer,
                b'generated-natural-language-supported',
                TagEnum.natural_language
            ): [b'en'],
            (
                SectionEnum.printer,
                b'document-format-default',
                TagEnum.mime_media_type
            ): [b'application/pdf'],
            (
                SectionEnum.printer,
                b'document-format-supported',
                TagEnum.mime_media_type
            ): [b'application/pdf'],
            (
                SectionEnum.printer,
                b'printer-is-accepting-jobs',
                TagEnum.boolean
            ): [Boolean(True).bytes()],
            (
                SectionEnum.printer,
                b'queued-job-count',
                TagEnum.integer
            ): [b'\x00\x00\x00\x00'],
            (
                SectionEnum.printer,
                b'pdl-override-supported',
                TagEnum.keyword
            ): [b'not-attempted'],
            (
                SectionEnum.printer,
                b'printer-up-time',
                TagEnum.integer
            ): [Integer(self.printer_uptime()).bytes()],
            (
                SectionEnum.printer,
                b'compression-supported',
                TagEnum.keyword
            ): [b'none'],
        }
        attr.update(self.minimal_attributes())
        return attr

    def print_job_attributes(self, job_obj, state, state_reasons):
        # state reasons come from rfc2911 section 4.3.8
        job_uri = f"{job_obj.id}"
        attr = {
            # Required for print-job:
            (
                SectionEnum.operation,
                b'job-uri',
                TagEnum.uri
            ): [job_uri],
            (
                SectionEnum.operation,
                b'job-id',
                TagEnum.integer
            ): [Integer(job_obj.id).bytes()],
            (
                SectionEnum.operation,
                b'job-state',
                TagEnum.enum
            ): [Enum(state).bytes()],
            (
                SectionEnum.operation,
                b'job-state-reasons',
                TagEnum.keyword
            ): state_reasons,

            # Required for get-job-attributes:

            (
                SectionEnum.operation,
                b'job-printer-uri',
                TagEnum.uri
            ): [self.printer_uri],
            (
                SectionEnum.operation,
                b'job-name',
                TagEnum.name_without_language
            ): [b'Print job %s' % Integer(job_obj.id).bytes()],
            (
                SectionEnum.operation,
                b'job-originating-user-name',
                TagEnum.name_without_language
            ): [b'job-originating-user-name'],
            (
                SectionEnum.operation,
                b'time-at-creation',
                TagEnum.integer
            ): [b'\x00\x00\x00\x00'],
            (
                SectionEnum.operation,
                b'time-at-processing',
                TagEnum.integer
            ): [b'\x00\x00\x00\x00'],
            (
                SectionEnum.operation,
                b'time-at-completed',
                TagEnum.integer
            ): [b'\x00\x00\x00\x00'],
            (
                SectionEnum.operation,
                b'job-printer-up-time',
                TagEnum.integer
            ): [Integer(self.printer_uptime()).bytes()]
        }
        attr.update(self.minimal_attributes())
        return attr

    def printer_uptime(self):
        return int(time.time())

    def create_job(self):
        """Return a job id.

        The StatelessPrinter does not care about the id, but perhaps
        it can be subclassed into something that keeps track of jobs.
        """
        return random.randint(1,9999)

    def handle_postscript(self, ipp_request, postscript_file):
        raise NotImplementedError

class ModelBehaviour(StatelessPrinter):
    """
        Base Behaviour class intended for actual printers
    """
    def __init__(
        self,
        color_supported: bool,
        directory: str, 
        ppd_path: str,
        adapter: BaseAdapterClass = BaseAdapterClass,
        branding: str = None,
    ):
        self.color_supported = color_supported
        self.address = ["127.0.0.1",0]
        self.directory = directory
        self.jobs: dict[Job] = {}
        self.adapter = adapter
        
        if not adapter and branding:
            self.printer_make_and_model,self.printer_info,self.printer_name,self.printer_model,self.state,self.state_reasons,self.accepting = [
                "none","none","none","none",PrinterStateEnum.idle,["none"],True
            ]
        
        ppd = ModelPPD(ppd_path)

        super(ModelBehaviour, self).__init__(ppd=ppd)
    
    @property
    def queue(self):
        return len([i for i in self.jobs.values() if i.state != JobStateEnum.completed])
    
    @property
    def printer_uri(self):
        return f"ipp://{self.get_address()}/printer".encode()
    @property
    def base_uri(self):
        return f"ipp://{self.get_address()}/".encode()
    
    def get_address(self):
        return f"{self.address[0]}:{self.address[1]}"
    
    def handle_postscript(self, job_obj: Job, postscript_file):
        for block in read_in_blocks(postscript_file):
            job_obj.write(block)

    def printer_list_attributes(self):
        attr = {
            # rfc2911 section 4.4
            (
                SectionEnum.printer,
                b'printer-uri-supported',
                TagEnum.uri
            ): [self.printer_uri],
            (
                SectionEnum.printer,
                b'uri-authentication-supported',
                TagEnum.keyword
            ): [b'none'],
            (
                SectionEnum.printer,
                b'uri-security-supported',
                TagEnum.keyword
            ): [b'none'],
            (
                SectionEnum.printer,
                b'printer-name',
                TagEnum.name_without_language
            ): [self.printer_name.encode()],
            (
                SectionEnum.printer,
                b'printer-info',
                TagEnum.text_without_language
            ): [self.printer_info.encode()],
            (
                SectionEnum.printer,
                b'printer-make-and-model',
                TagEnum.text_without_language
            ): [self.printer_make_and_model.encode()],
            (
                SectionEnum.printer,
                b'printer-state',
                TagEnum.enum
            ): [Enum(self.state).bytes()],
            (
                SectionEnum.printer,
                b'printer-state-reasons',
                TagEnum.keyword
            ): [i.encode() for i in self.state_reasons],
            (
                SectionEnum.printer,
                b'ipp-versions-supported',
                TagEnum.keyword
            ): [b'1.1'], # god fucking damn it
            (
                SectionEnum.printer,
                b'operations-supported',
                TagEnum.enum
            ): [
                Enum(x).bytes()
                for x in (
                    OperationEnum.print_job,  # (required by cups)
                    OperationEnum.validate_job,  # (required by cups)
                    OperationEnum.cancel_job,  # (required by cups)
                    OperationEnum.get_job_attributes,  # (required by cups)
                    OperationEnum.get_printer_attributes,
                    # TODO: add get jobs
                )],
            (
                SectionEnum.printer,
                b'multiple-document-jobs-supported',
                TagEnum.boolean
            ): [Boolean(False).bytes()],
            (
                SectionEnum.printer,
                b'charset-configured',
                TagEnum.charset
            ): [b'utf-8'],
            (
                SectionEnum.printer,
                b'charset-supported',
                TagEnum.charset
            ): [b'utf-8'],
            (
                SectionEnum.printer,
                b'natural-language-configured',
                TagEnum.natural_language
            ): [b'en'],
            (
                SectionEnum.printer,
                b'generated-natural-language-supported',
                TagEnum.natural_language
            ): [b'en'],
            (
                SectionEnum.printer,
                b'document-format-default',
                TagEnum.mime_media_type
            ): [b'application/pdf'],
            (
                SectionEnum.printer,
                b'document-format-supported',
                TagEnum.mime_media_type
            ): [b'application/pdf'],
            (
                SectionEnum.printer,
                b'printer-is-accepting-jobs',
                TagEnum.boolean
            ): [Boolean(self.accepting).bytes()],
            (
                SectionEnum.printer,
                b'queued-job-count',
                TagEnum.integer
            ): [Integer(self.queue).bytes()],
            (
                SectionEnum.printer,
                b'pdl-override-supported',
                TagEnum.keyword
            ): [b'not-attempted'],
            (
                SectionEnum.printer,
                b'printer-up-time',
                TagEnum.integer
            ): [Integer(self.printer_uptime()).bytes()],
            (
                SectionEnum.printer,
                b'compression-supported',
                TagEnum.keyword
            ): [b'none'],
        }
        attr.update(self.minimal_attributes())
        return attr
    
    def print_job_attributes(self, job: Job):
        # state reasons come from rfc2911 section 4.3.8
        job_uri = b'%sjob/%d' % (self.base_uri, job.id,)
        attr = {
            # Required for print-job:
            (
                SectionEnum.operation,
                b'job-uri',
                TagEnum.uri
            ): [job_uri],
            (
                SectionEnum.operation,
                b'job-id',
                TagEnum.integer
            ): [Integer(job.id).bytes()],
            (
                SectionEnum.operation,
                b'job-state',
                TagEnum.enum
            ): [Enum(job.state).bytes()],
            (
                SectionEnum.operation,
                b'job-state-reasons',
                TagEnum.keyword
            ): job.state_reasons,
            (
                SectionEnum.operation,
                b'job-printer-uri',
                TagEnum.uri
            ): [self.printer_uri],
            (
                SectionEnum.operation,
                b'job-name',
                TagEnum.name_without_language
            ): [b'Job ID:%s' % Integer(job.id).bytes()],
            (
                SectionEnum.operation,
                b'job-originating-user-name',
                TagEnum.name_without_language
            ): [b'unknown'],
            (
                SectionEnum.operation,
                b'time-at-creation',
                TagEnum.integer
            ): [Integer(job.start_time).bytes()],
            (
                SectionEnum.operation,
                b'time-at-processing',
                TagEnum.integer
            ): [Integer(job.start_time).bytes()],
            (
                SectionEnum.operation,
                b'time-at-completed',
                TagEnum.integer
            ): [Integer(job.end_time).bytes() if job.end_time != 1 else b"\x00\x00\x00\x00"],
            (
                SectionEnum.operation,
                b'job-printer-up-time',
                TagEnum.integer
            ): [Integer(self.printer_uptime()).bytes()]
        }
        attr.update(self.minimal_attributes())
        return attr
    
    def routine_job_list_check(self):
        for job_obj in self.jobs.values():
            if job_obj.state == JobStateEnum.completed:
                self.jobs[job_obj.id].file.close()
                
    def create_job(self):
        routine_check_thread = Thread(target=self.routine_job_list_check)
        routine_check_thread.start()
        job_obj = Job(len(self.jobs.keys()))
        self.jobs[job_obj.id] = job_obj
        routine_check_thread.join()
        return self.jobs[job_obj.id]

    def operation_get_jobs_response(self, req: IppRequest, _psfile):
        # rfc 2911 is dogshit
        # TODO: Fix this shit
        
        attributes = self.minimal_attributes()
        
        attributes.update({
            
        })
        
        return IppRequest(
            self.version,
            StatusCodeEnum.ok,
            req.request_id,
            attributes)

    def get_handle_command_function(self, opid_or_status):
        commands = {
            OperationEnum.get_printer_attributes: self.operation_printer_list_response,
            OperationEnum.cups_list_all_printers: self.operation_printer_list_response,
            OperationEnum.cups_get_default: self.operation_printer_list_response,
            OperationEnum.validate_job: self.operation_validate_job_response,
            OperationEnum.get_jobs: self.operation_get_jobs_response,
            OperationEnum.get_job_attributes: self.operation_get_job_attributes_response,
            OperationEnum.print_job: self.operation_print_job_response,
            # TODO: Add operation get ppds
            # OperationEnum.cups_get_ppds: self.operation_get_ppds_response
        }

        try:
            command_function = commands[opid_or_status]
        except KeyError:
            command_function = self.operation_not_implemented_response
        return command_function
    
    def operation_print_job_response(self, req, psfile):
        job_obj = self.create_job()
        attributes = self.print_job_attributes(
            job_obj
        )
        self.handle_postscript(job_obj, psfile)
        return IppRequest(
            self.version,
            StatusCodeEnum.ok,
            req.request_id,
            attributes
        )