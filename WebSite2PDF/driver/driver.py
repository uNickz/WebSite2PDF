import requests
import logging
import json
import os

from selenium.webdriver.support.expected_conditions import staleness_of
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
from typing import Optional

from ..errors import ClientAlreadyStarted, ClientAlreadyStopped, InvalidUrl, RequestFailed, InvalidFile

log = logging.getLogger(__name__)

class Driver:
    def __init__(self) -> None:
        self.driver: webdriver.Chrome = None

    def start_client(self, options: Optional[Options] = None, service: Optional[Service] = None, install_driver: bool = True) -> None:
        if self.driver:
            raise ClientAlreadyStarted
        
        if install_driver:
            self.driver = webdriver.Chrome(executable_path = ChromeDriverManager().install(), options = options, service = service)
        else:
            self.driver = webdriver.Chrome(options = options, service = service)
    
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