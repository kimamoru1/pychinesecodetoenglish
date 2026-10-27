import logging
import os
import re
import time
from typing import List

from googletrans import Translator


class AbstractTranslator:

    def __init__(self, path: str, language: str = 'en', encoding: str = "utf8"):
        self.__content = self._read_file(path, encoding)
        self.__lang = language.lower()

    @property
    def lang(self) -> str:
        return self.__lang

    @property
    def content(self) -> str:
        return self.__content

    @staticmethod
    def _read_file(path, encoding):
        with open(path, 'r', encoding=encoding) as f:
            data = f.read()
        return data

    def get_provider_answer(self, original: str) -> str:
        raise NotImplementedError()

    def get_result(self) -> str:
        raise NotImplementedError()


class GoogleTranslator(AbstractTranslator):
    """
    Free translation by Google translate with package `googletrans`
    """

    def __init__(self, path: str, language: str = 'en', encoding: str = "utf8"):
        super().__init__(path, language, encoding)
        self._translator = Translator(service_urls=self._get_google_urls())

    @staticmethod
    def _get_google_urls() -> List[str]:
        # Prioritize translate.googleapis.com API endpoint to bypass scraping blocks
        urls = ['translate.googleapis.com']
        pth = os.path.join(os.path.dirname(__file__), 'domains.txt')
        if os.path.exists(pth):
            try:
                with open(pth) as f:
                    domains = [d.strip() for d in f.read().splitlines() if d.strip()]
                    urls.extend(domains)
            except Exception:
                pass
        return urls

    def get_provider_answer(self, original: str) -> str:
        tries = 0
        while tries < 5:
            try:
                res = self._translator.translate(original, dest=self.lang)
                if res and hasattr(res, 'text'):
                    return res.text
                return str(res)
            except Exception as e:
                logging.error(f'Tries: {tries}. Exception: {e}')
                tries += 1
                # Refresh session client on failure
                self._translator = Translator(service_urls=self._get_google_urls())
                time.sleep(2)
        
        # Fallback to original text if API fails after 5 retries to prevent endless hanging
        return original

    def translate(self, original: str) -> str:
        raise NotImplementedError()

    def get_result(self):
        res = re.sub(u'[\u4e00-\u9fff]+', lambda x: self.translate(x.group()), self.content)
        return res