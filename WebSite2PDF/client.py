import logging
import base64
import time
import os
import re

from selenium.webdriver.firefox.options import Options as FireFoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from typing import Optional, Iterable, Union, List, Tuple
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
            "--disable-infobars",
            "--disable-extensions",
            "--disable-popup-blocking",
        ],
        delay: Optional[int] = 0,
    ) -> None:
        self.client: Driver = Driver()
        self.pdfOptions: dict = pdfOptions
        self.seleniumOptions: List[str] = seleniumOptions
        self.delay: int = delay

    def pdf(self, url: Union[str, Iterable[str]], filename: Optional[Union[str, Iterable[str]]] = None, pdfOptions: Optional[dict] = None, seleniumOptions: Optional[List[str]] = None, delay: Optional[int] = 0) -> Union[bytes, Iterable[bytes], str, Iterable[str]]:
        __url = [url] if isinstance(url, str) else url
        if any([not isinstance(_, str) for _ in __url]):
            raise TypeError("You must pass an argument of type string or an iterable of strings.")

        __pdfOptions: dict = pdfOptions if pdfOptions else self.pdfOptions
        __seleniumOptions: List[str] = seleniumOptions if seleniumOptions else self.seleniumOptions
        __delay: int = delay if delay else self.delay

        __opts: Tuple[ChromeOptions, FireFoxOptions] = self.__FormatOptions(__seleniumOptions)
        self.client.start_client(__opts)
        if isinstance(url, str):
            self.client.connect(url)
            __title: str = self.client.driver.title

            if self.client.browser == "Chrome":
                __resp: dict = self.client.send_DevTool("Page.printToPDF", __pdfOptions, __delay)["data"]
                self.client.stop_client()
                if isinstance(filename, list):
                    filename = filename[0]
                if not filename:
                    return base64.b64decode(__resp)
                filename = filename.format(title = __title)
                __fn = filename + (".pdf" if not filename.lower().endswith(".pdf") else "")
                __fn = re.sub("(\/|\\|\?|%|\*|:|\||\"|<|>)", "", __fn)
                with open(__fn, "wb+") as file:
                    file.write(base64.b64decode(__resp))
                return os.path.abspath(__fn)

            self.client.driver.execute_script("window.print();")
            __file_path = os.path.join(os.getcwd(), "WebSite2PDF.pdf")
            while not os.path.isfile(__file_path) or os.path.getsize(__file_path) == 0:
                time.sleep(0.1)
            self.client.stop_client()
            if isinstance(filename, list):
                filename = filename[0]
            if not filename:
                with open(__file_path, "rb") as file:
                    __content = file.read()
                os.remove(__file_path)
                return __content
            filename = filename.format(title = __title)
            __fn = filename + (".pdf" if not filename.lower().endswith(".pdf") else "")
            __fn = re.sub("(\/|\\|\?|%|\*|:|\||\"|<|>)", "", __fn)
            os.rename(__file_path, __fn)
            return os.path.abspath(__fn)

        if not filename:
            __gresp: List[bytes] = []
            for u in url:
                self.client.connect(u)
                if self.client.browser == "Chrome":
                    __gresp += [base64.b64decode(self.client.send_DevTool("Page.printToPDF", __pdfOptions, __delay)["data"])]
                else:
                    self.client.driver.execute_script("window.print();")
                    __file_path = os.path.join(os.getcwd(), "WebSite2PDF.pdf")
                    while not os.path.isfile(__file_path) or os.path.getsize(__file_path) == 0:
                        time.sleep(0.1)
                    with open(__file_path, "rb") as file:
                        __gresp += [file.read()]
                    os.remove(__file_path)
            self.client.stop_client()
            return __gresp

        if isinstance(filename, str):
            filename = [filename]
        __gresp: List[str] = []
        for i, u in enumerate(url):
            self.client.connect(u)
            __title: str = self.client.driver.title
            if i < len(filename):
                if filename[i]:
                    filename[i] = filename[i].format(title = __title)
                    __fn = filename[i] + (".pdf" if not filename[i].lower().endswith(".pdf") else "")
                else:
                    __fn = __title + ".pdf"
            else:
                __fn = __title + ".pdf"
            __fn = re.sub("(\/|\\|\?|%|\*|:|\||\"|<|>)", "", __fn)
            if self.client.browser == "Chrome":
                with open(__fn, "wb+") as file:
                    file.write(base64.b64decode(self.client.send_DevTool("Page.printToPDF", __pdfOptions, __delay)["data"]))
                __gresp += [os.path.abspath(__fn)]
            else:
                self.client.driver.execute_script("window.print();")
                __file_path = os.path.join(os.getcwd(), "WebSite2PDF.pdf")
                while not os.path.isfile(__file_path) or os.path.getsize(__file_path) == 0:
                    time.sleep(0.1)
                os.rename(__file_path, __fn)
                __gresp += [os.path.abspath(__fn)]
        self.client.stop_client()
        return __gresp

    def __FormatOptions(self, seleniumOptions: List[str]) -> Tuple[ChromeOptions, FireFoxOptions]:
        __chrome_opts = ChromeOptions()
        __firefox_opts = FireFoxOptions()
        for _ in seleniumOptions:
            __chrome_opts.add_argument(_)
            __firefox_opts.add_argument(_)
        __chrome_opts.add_experimental_option("prefs", {"profile.managed_default_content_settings.images" : 2})
        __firefox_opts.set_preference("browser.aboutConfig.showWarning", False)
        __firefox_opts.set_preference("print.save_as_pdf.links.enabled", True)
        __firefox_opts.set_preference("services.sync.prefs.sync.browser.download.manager.showWhenStarting", False)
        __firefox_opts.set_preference("pdfjs.disabled", False)
        __firefox_opts.set_preference("print.always_print_silent", True)
        __firefox_opts.set_preference("print.show_print_progress", False)
        __firefox_opts.set_preference("browser.download.show_plugins_in_list", False)
        __firefox_opts.set_preference("browser.download.folderList", 2)
        __firefox_opts.set_preference("browser.download.manager.showWhenStarting", False)
        __firefox_opts.set_preference("print_printer", "Microsoft Print to PDF")
        __firefox_opts.set_preference("print.printer_Microsoft_Print_to_PDF.print_to_file", True)
        __firefox_opts.set_preference("print.printer_Microsoft_Print_to_PDF.print_bgcolor", True)
        __firefox_opts.set_preference("print.printer_Microsoft_Print_to_PDF.print_shrink_to_fit", True)
        __firefox_opts.set_preference("print.save_as_pdf.internal_destinations.enabled", True)
        __firefox_opts.set_preference("print.printer_Microsoft_Print_to_PDF.print_bgimages", True)
        __firefox_opts.set_preference("print.printer_Microsoft_Print_to_PDF.show_print_progress", True)
        __firefox_opts.set_preference("print.printer_Microsoft_Print_to_PDF.print_to_filename", os.path.join(os.getcwd(), "WebSite2PDF.pdf"))
        return (__chrome_opts, __firefox_opts)