import requests
import selenium
import logging
import json
import os

from selenium.webdriver.firefox.options import Options as FireFoxOptions
from selenium.webdriver.firefox.service import Service as FireFoxService
from selenium.webdriver.support.expected_conditions import staleness_of
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from typing import Optional, Tuple
from selenium import webdriver

from ..errors import ClientAlreadyStarted, ClientAlreadyStopped, InvalidUrl, RequestFailed, InvalidFile

log = logging.getLogger(__name__)

class Driver:
    def __init__(self) -> None:
        self.driver: webdriver.Chrome = None
        self.browser = "Chrome"

    def start_client(self, options: Optional[Tuple[ChromeOptions, FireFoxOptions]] = None, service: Optional[Tuple[FireFoxService, ChromeService]] = None, install_driver: bool = True) -> None:
        if self.driver:
            raise ClientAlreadyStarted

        if install_driver:
            if tuple(map(int, selenium.__version__.split("."))) >= (4, 10, 0):
                try:
                    self.driver = webdriver.Chrome(options = options[0] if options else None, service = ChromeService(executable_path = ChromeDriverManager().install()))
                except AttributeError:
                    self.browser = "FireFox"
                    self.driver = webdriver.Firefox(options = options[1] if options else None, service = FireFoxService(executable_path = GeckoDriverManager().install()))
            else:
                try:
                    self.driver = webdriver.Chrome(executable_path = ChromeDriverManager().install(), options = options[0] if options else None, service = service[0] if service else None)
                except AttributeError:
                    self.browser = "FireFox"
                    self.driver = webdriver.Firefox(executable_path = GeckoDriverManager().install(), options = options[1] if options else None, service = service[1] if service else None)
        else:
            try:
                self.driver = webdriver.Chrome(options = options[0] if options else None, service = service[0] if service else None)
            except AttributeError:
                self.browser = "FireFox"
                self.driver = webdriver.Firefox(options = options[1] if options else None, service = service[1] if service else None)
    
    def stop_client(self) -> None:
        if not self.driver:
            raise ClientAlreadyStopped
        
        self.driver.quit()
    
    def connect(self, url: str, cookies: Optional[dict] = None) -> None:
        if url.lower().startswith("file:///") and url.lower().endswith(".html"):
            if not self.__isCorrectFile(url):
                raise InvalidFile

        elif not url or not requests.get(url, cookies = cookies).ok:
            raise InvalidUrl
        
        if cookies:
            self.driver.add_cookie(cookies)
        self.driver.get(url)
    
    def send_DevTool(self, command_line: str, params: Optional[dict] = None, delay: Optional[int] = 0):
        try:
            WebDriverWait(self.driver, delay).until(
                staleness_of(self.driver.find_element(by = By.TAG_NAME, value = "html"))
            )
        except TimeoutException:
            pass

        __url = f"{self.driver.command_executor._url}/session/{self.driver.session_id}/chromium/send_command_and_get_result"
        __r = self.driver.command_executor._request("POST", __url, json.dumps({"cmd": command_line, "params": params}))

        if __r.get("status"):
            raise RequestFailed(__r.get("value"))

        return __r.get("value")
    
    def __isCorrectFile(self, url: str) -> bool:
        return os.path.isfile(url[len("file:///"):])