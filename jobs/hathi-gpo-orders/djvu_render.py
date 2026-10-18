"""Thin binding to the installed DjVuLibre C API; render bundled local scans."""
import ctypes as C
import os
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent


class Rect(C.Structure):
    _fields_ = [("x", C.c_int), ("y", C.c_int), ("w", C.c_uint), ("h", C.c_uint)]


class DjvuBook:
    def __init__(self, path):
        bindir = HERE / ".cache/djvu/ucrt64/bin"
        self.dll_directory = os.add_dll_directory(str(bindir)) if os.name == "nt" else None
        self.lib = C.CDLL(str(bindir / "libdjvulibre-21.dll") if os.name == "nt" else "libdjvulibre.so.21")
        p, i = C.c_void_p, C.c_int
        signatures = {
            "ddjvu_context_create": ([C.c_char_p], p),
            "ddjvu_document_create_by_filename_utf8": ([p, C.c_char_p, i], p),
            "ddjvu_document_job": ([p], p), "ddjvu_page_job": ([p], p),
            "ddjvu_job_status": ([p], i), "ddjvu_job_release": ([p], None),
            "ddjvu_message_peek": ([p], p), "ddjvu_message_pop": ([p], None),
            "ddjvu_document_get_pagenum": ([p], i),
            "ddjvu_page_create_by_pageno": ([p, i], p),
            "ddjvu_page_get_width": ([p], i), "ddjvu_page_get_height": ([p], i),
            "ddjvu_page_get_resolution": ([p], i),
            "ddjvu_format_create": ([i, i, C.POINTER(C.c_uint)], p),
            "ddjvu_format_set_row_order": ([p, i], None),
            "ddjvu_page_render": ([p, i, C.POINTER(Rect), C.POINTER(Rect), p, C.c_ulong, p], i),
            "ddjvu_format_release": ([p], None), "ddjvu_context_release": ([p], None),
        }
        for name, (args, result) in signatures.items():
            fn = getattr(self.lib, name)
            fn.argtypes, fn.restype = args, result
        self.ctx = self.lib.ddjvu_context_create(b"executive-order-ocr")
        self.doc = self.lib.ddjvu_document_create_by_filename_utf8(self.ctx, str(Path(path).resolve()).encode("utf-8"), 1)
        if not self.doc:
            raise ValueError("DjVu document could not be opened")
        self.wait(self.lib.ddjvu_document_job(self.doc))
        self.pages = self.lib.ddjvu_document_get_pagenum(self.doc)

    def wait(self, job):
        deadline = time.monotonic() + 60
        while self.lib.ddjvu_job_status(job) < 2:
            while self.lib.ddjvu_message_peek(self.ctx):
                self.lib.ddjvu_message_pop(self.ctx)
            if time.monotonic() > deadline:
                raise TimeoutError("DjVu page decode exceeded 60 seconds")
            time.sleep(0.01)
        if self.lib.ddjvu_job_status(job) != 2:
            raise ValueError("DjVu page decode failed")

    def render(self, page_number, dpi=200):
        page = self.lib.ddjvu_page_create_by_pageno(self.doc, page_number - 1)
        if not page:
            raise ValueError("No DjVu page " + str(page_number))
        job = self.lib.ddjvu_page_job(page)
        try:
            self.wait(job)
            w, h = self.lib.ddjvu_page_get_width(page), self.lib.ddjvu_page_get_height(page)
            resolution = self.lib.ddjvu_page_get_resolution(page) or 300
            scale = min(1, dpi / resolution)
            w, h = max(1, round(w * scale)), max(1, round(h * scale))
            assert 0 < w * h <= 30_000_000
            rect = Rect(0, 0, w, h)
            form = self.lib.ddjvu_format_create(4, 0, None)  # DDJVU_FORMAT_GREY8
            self.lib.ddjvu_format_set_row_order(form, 1)
            raw = C.create_string_buffer(w * h)
            try:
                okay = self.lib.ddjvu_page_render(page, 0, C.byref(rect), C.byref(rect), form, w, raw)
                if not okay:
                    raise ValueError("DjVu page render returned no image")
                return f"P5\n{w} {h}\n255\n".encode() + raw.raw
            finally:
                self.lib.ddjvu_format_release(form)
        finally:
            self.lib.ddjvu_job_release(job)

    def close(self):
        self.lib.ddjvu_job_release(self.lib.ddjvu_document_job(self.doc))
        self.lib.ddjvu_context_release(self.ctx)
        if self.dll_directory:
            self.dll_directory.close()
