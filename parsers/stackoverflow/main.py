import models
from models import StackOverflowParserFilter
from models import StackOverflowParserRanking
from models import StackOverflowParserTag
from models import StackOverflowParserConfig
from models import StackOverflowParserPolicy
from scrapper import StackOverflowScrapper

from pprint import pprint
import typing
import json


def get_question_dicts(questions: typing.List[models.StackOverflowQuestion]):
    return list(map(lambda q: q.dict(), questions))


def extract_ids(questions_file_data):
    ids_ = set([])
    for question_data in questions_file_data:
        ids_.add(question_data['id'])
    return ids_


def get_all_questions(file_name_: str):
    file = open(file_name_, 'r')
    all_ = json.loads(file.read())
    file.close()

    return all_


if __name__ == '__main__':
    filter = StackOverflowParserFilter(
        [StackOverflowParserTag.cpp],
        rank_by=StackOverflowParserRanking.votes,
        has_accepted_answer=True)
    config = StackOverflowParserConfig(answers_limit=3, only_accepted_answers=True,
                                       code_policy=StackOverflowParserPolicy.embed)
    scrapper = StackOverflowScrapper(filter, config)

    questions_limit = 1000000
    questions_batch = 500
    file_name = 'data.json'

    all_questions = get_all_questions(file_name)
    current_last_page = 1

    for i in range(0, questions_limit, questions_batch):
        ids = extract_ids(all_questions)
        questions, last_page = scrapper.get_questions(questions_batch, 100000, ids, current_last_page)
        current_last_page = last_page
        all_questions.extend(get_question_dicts(questions))
        with open(file_name, 'w') as f:
            json.dump(all_questions, f)


