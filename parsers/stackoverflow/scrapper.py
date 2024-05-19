import random

import const
from logger import logger
import models
import utils

import bs4
from concurrent.futures import ThreadPoolExecutor, as_completed
from fp.fp import FreeProxy
from random import choice
import requests
from requests.auth import HTTPProxyAuth
import time
import typing
import urllib.parse

requests.packages.urllib3.disable_warnings()

class StackOverflowScrapper:
    def __init__(
            self, filter_: models.StackOverflowParserFilter,
            config: models.StackOverflowParserConfig = (
                    models.StackOverflowParserConfig()
            ),
            delay: int = 0,
    ):
        self.filter = filter_
        self.config = config
        self.delay = delay
        self.proxy_switch_retries = 3
        self.__switch_proxy__()

        if delay < 0.05:
            logger.warn(f'You set delay {delay}. You might be'
                        f' banned soon, set the correct one please')

    def __switch_proxy__(self):
        self.session = requests.Session()
        self.session.proxies = {
            'https': f'http://{choice(const.PAID_PROXY)}'
        }
        self.session.trust_env = False

    def __get_page_url_encoded__(self, page: int = 0) -> str:
        if page < 0:
            raise Exception("Page can't be below zero")

        tags_concatenated = " ".join(map(lambda tag: tag.value, self.filter.tags))
        tags_encoded = urllib.parse.quote(tags_concatenated)
        rank_by_encoded = urllib.parse.quote(self.filter.rank_by.value)

        return const.STACKOVERFLOW_URL.format(
            tags_encoded,
            rank_by_encoded,
            page,
        )

    def __get_question_url_encoded__(self, question_id: str) -> str:
        return const.STACKOVERFLOW_QUESTION_URL.format(question_id)

    def __make_request__(self, url):
        try:
            response = self.session.get(url, timeout=3, verify=False)
            return response
        except Exception as e:
            logger.error(f'Error during request: {e}')
            return None

    def __get_source_code__(self, url):
        retries_count = 0
        response = self.__make_request__(url)
        while response is None or 'Just a moment...' in response.text:
            logger.warn('No answer from stackoverflow. Retrying in 1 sec...')
            retries_count += 1
            time.sleep(1)
            if retries_count >= self.proxy_switch_retries:
                self.__switch_proxy__()
                retries_count = 0
                logger.warn(f'Switching proxy to {self.session.proxies}, retrying...')

            response = self.__make_request__(url)

        return response.text

    def __page_soup__(self, page: int = 0) -> bs4.BeautifulSoup:
        time.sleep(self.delay)
        source_code = self.__get_source_code__(self.__get_page_url_encoded__(page))
        soup = bs4.BeautifulSoup(source_code, 'html.parser')

        return soup

    def __question_soap__(self, question_id: str) -> bs4.BeautifulSoup:
        time.sleep(self.delay)
        source_code = self.__get_source_code__(self.__get_question_url_encoded__(question_id))
        soup = bs4.BeautifulSoup(source_code, 'html.parser')

        return soup

    def __is_score_suitable__(self, score: int) -> bool:
        if self.filter.min_score > score:
            return False
        if self.filter.max_score is not None \
                and self.filter.max_score < score:
            return False
        return True

    def __is_answers_count_suitable__(self, answers_count: int) -> bool:
        if self.filter.min_answers_count > answers_count:
            return False
        if self.filter.max_answers_count is not None \
                and self.filter.max_answers_count < answers_count:
            return False
        return True

    def __is_accepted_answer_suitable__(self, has_accepted_answer: bool) -> bool:
        if self.filter.has_accepted_answer is None:
            return True

        return self.filter.has_accepted_answer == has_accepted_answer

    def __is_question_block_suitable__(
            self, question_block: bs4.element.Tag) -> bool:
        block = utils.prepare_block(question_block)
        block_id = question_block.attrs['id']
        question_id = block_id.partition('question-summary-')[2]

        if not self.__is_score_suitable__(block.score):
            logger.debug(f"{question_id} is not suitable due to score")
            return False
        if not self.__is_answers_count_suitable__(block.answers_count):
            logger.debug(f"{question_id} is not suitable due to answers count")
            return False
        if not self.__is_accepted_answer_suitable__(block.has_accepted_answer):
            logger.debug(f"{question_id} is not suitable due to accepted answers")
            return False

        return True

    def __get_question_ids_(self, count, page_limit,
                            skip_ids: typing.Optional[typing.Set] = None,
                            last_page: int = 1,
    ) -> typing.Tuple[typing.List[str], int]:
        question_ids = []
        logger.info("Starting scrapping ids")
        new_last_page = last_page

        for page_number in range(last_page, page_limit):
            new_last_page = page_number
            logger.debug(f"Moving to page {page_number}")
            soup = self.__page_soup__(page_number - 1)
            questions = soup.find('div', {'id': 'questions'})
            if not questions:
                logger.error("questions is none")
                continue
            for question_block in questions.children:
                question_block: typing.Union[bs4.element.NavigableString, bs4.element.Tag]
                if isinstance(question_block, bs4.element.NavigableString):
                    continue

                if not self.__is_question_block_suitable__(question_block):
                    continue

                block_id = question_block.attrs['id']
                question_id = block_id.partition('question-summary-')[2]

                if skip_ids and question_id in skip_ids:
                    logger.debug(f"Skipping question {question_id}")
                    continue

                question_ids.append(question_id)

            if len(question_ids) >= count:
                logger.info(f"Scrapper found {count} questions "
                            f"in first {page_number} pages. "
                            f"Stopping scrapping ids")
                question_ids = question_ids[:count]
                break
        else:
            if len(question_ids) < count:
                logger.info(f"Pages limit reached. "
                            f"Found {len(question_ids)} in {page_limit} pages")

        return question_ids, new_last_page

    def get_question(
            self, question_id: str) -> typing.Optional[models.StackOverflowQuestion]:
        soup = self.__question_soap__(question_id)
        question = utils.format_question(question_id, soup, self.config)

        if question is None:
            return None

        return question

    def get_questions(self, count: int, page_limit: int = 100, skip_ids=None, last_page=1):
        questions_ids, last_page = self.__get_question_ids_(count, page_limit, skip_ids, last_page)
        logger.info(f"Successfully extracted {len(questions_ids)} question ids")

        questions = []
        answers_quantity = 0

        # Создаем пул потоков
        with ThreadPoolExecutor() as executor:
            # Создаем future для каждого question_id
            future_to_question_id = {executor.submit(self.get_question, question_id): question_id for question_id in
                                     questions_ids}

            for future in as_completed(future_to_question_id):
                question_id = future_to_question_id[future]
                try:
                    question = future.result()
                    if question is not None:
                        questions.append(question)
                        answers_quantity += len(question.answers)
                        logger.debug(f'Question \'{question_id}\' scrapped successfully')
                    else:
                        logger.debug(f'Question \'{question_id}\' do not satisfy filters')
                except Exception as exc:
                    logger.error(f'Question id {question_id} generated an exception: {exc}')

        logger.info(f'Scrapping finished with total of {len(questions)} questions and {answers_quantity} answers for them')
        return questions, last_page

