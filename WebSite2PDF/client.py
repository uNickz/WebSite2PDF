import logging
import base64
import os
import re

from selenium.webdriver.chrome.options import Options
from typing import Optional, Iterable, Union, List
from .driver import Driver

log = logging.getLogger(__name__)

class Client:

    def __init__(
        self,
        pdfOptions: Optional[dict] = {
            "displayHeaderFooter": True,
            "printBackground": True,
            "preferCSSPageSize": True,
        },
        seleniumOptions: Optional[List[str]] = [
            "--no-sandbox",
            "--headless",
            "--enable-multiprocess",
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--instant-process",
            "--fast",
            "--fast-start",
        ],
        delay: Optional[int] = 0,
    ) -> None:
        self.client: Driver = Driver()
        self.pdfOptions: dict = pdfOptions
        self.seleniumOptions: List[str] = seleniumOptions
        self.delay = delay

    def pdf(self, url: Union[str, Iterable[str]], filename: Optional[Union[str, Iterable[str]]] = None, pdfOptions: Optional[dict] = None, seleniumOptions: Optional[List[str]] = None, delay: Optional[int] = 0) -> Union[bytes, Iterable[bytes], str, Iterable[str]]:
        __url = [url] if isinstance(url, str) else url
        if any([not isinstance(_, str) for _ in __url]):
            raise TypeError("You must pass an argument of type string or an iterable of strings.")
        
        __pdfOptions = pdfOptions if pdfOptions else self.pdfOptions
        __seleniumOptions = seleniumOptions if seleniumOptions else self.seleniumOptions
        __delay = delay if delay else self.delay

        __opts: Options = self.__FormatOptions(__seleniumOptions)
        self.client.start_client(__opts)
        if isinstance(url, str):
            self.client.connect(url)
            __resp: dict = self.client.send_DevTool("Page.printToPDF", __pdfOptions, __delay)["data"]
            self.client.stop_client()
            if isinstance(filename, list):
                filename = filename[0]
            if not filename:
                return base64.b64decode(__resp)
            filename = filename.format(title = self.client.driver.title)
            __fn = filename + (".pdf" if not filename.lower().endswith(".pdf") else "")
            __fn = re.sub("(\/|\\|\?|%|\*|:|\||\"|<|>)", "", __fn)
            with open(__fn, "wb+") as file:
                file.write(base64.b64decode(__resp))
            return os.path.abspath(__fn)
        
        if not filename:
            __gresp: List[bytes] = []
            for u in url:
                self.client.connect(u)
                __gresp += [base64.b64decode(self.client.send_DevTool("Page.printToPDF", __pdfOptions, __delay)["data"])]
            self.client.stop_client()
            return __gresp
        
        if isinstance(filename, str):
            filename = [filename]
        __gresp: List[str] = []
        for i, u in enumerate(url):
            self.client.connect(u)
            if i < len(filename):
                if filename[i]:
                    filename = filename.format(title = self.client.driver.title)
                    __fn = filename[i] + (".pdf" if not filename[i].lower().endswith(".pdf") else "")
                else:
                    __fn = self.client.driver.title + ".pdf"
            else:
                __fn = self.client.driver.title + ".pdf"
            __fn = re.sub("(\/|\\|\?|%|\*|:|\||\"|<|>)", "", __fn)
            with open(__fn, "wb+") as file:
                file.write(base64.b64decode(__resp))
            __gresp += [os.path.abspath(__fn)]
        self.client.stop_client()
        return __gresp

    def __FormatOptions(self, seleniumOptions: List[str]) -> Options:
        __opts = Options()
        for _ in seleniumOptions:
            __opts.add_argument(_)
        __opts.add_experimental_option("prefs", {"profile.managed_default_content_settings.images" : 2})
        return __opts