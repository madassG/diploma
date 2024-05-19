from exceptions import SkipQuestionException
from logger import logger
import models

import bs4
import typing


def prepare_block(
        question_block: bs4.element.Tag,
) -> models.StackOverflowQuestionBlock:
    block = models.StackOverflowQuestionBlock()

    block_score = question_block.find(
        'span',
        {
            'class': 's-post-summary--stats-item-number',
        },
    )

    block.score = int(block_score.text)

    block_answers_count = block_score.find_next(
        'span',
        {
            'class': 's-post-summary--stats-item-number',
        },
    )

    block.answers_count = int(block_answers_count.text)

    block_has_accepted_answer = question_block.find(
        'div',
        {
            'class': 'has-accepted-answer',
        },
    )

    if block_has_accepted_answer is not None:
        block.has_accepted_answer = True

    return block


def format_question_title(soap: bs4.BeautifulSoup) -> dict:
    header = soap.find(
        'div',
        {
            'id': 'question-header',
        },
    )

    question_title = header.find(
        'a',
        {
            'class': 'question-hyperlink',
        },
    )

    return question_title.text


def format_question_score(tag: bs4.element.Tag) -> int:
    votes_count = tag.attrs.get('data-score')
    return int(votes_count)


def format_body_text(tag: bs4.element.Tag) -> str:
    return tag.text


def format_body_code(
        tag: bs4.element.Tag, code_policy: models.StackOverflowParserPolicy,
        code_embedding: str) -> str:
    if code_policy == models.StackOverflowParserPolicy.leave_as_is:
        return tag.text
    elif code_policy == models.StackOverflowParserPolicy.skip:
        return ""
    elif code_policy == models.StackOverflowParserPolicy.embed:
        return code_embedding.replace('|', tag.text)
    elif code_policy == models.StackOverflowParserPolicy.drop:
        raise SkipQuestionException()

    raise Exception(f"Can't process '{code_policy.name}' code policy")


def format_body_table(
        tag: bs4.element.Tag, table_policy: models.StackOverflowParserPolicy,
        table_embedding: str) -> str:
    if table_policy == models.StackOverflowParserPolicy.parse:
        table_rows = tag.find_all('tr')
        table_data = []

        for table_row in table_rows:
            cols = table_row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            table_data.append([ele for ele in cols if ele])
        return table_embedding.replace('|', str(table_data))
    elif table_policy == models.StackOverflowParserPolicy.leave_as_is:
        return tag.text
    elif table_policy == models.StackOverflowParserPolicy.skip:
        return ""
    elif table_policy == models.StackOverflowParserPolicy.embed:
        return table_embedding.replace('|', tag.text)
    elif table_policy == models.StackOverflowParserPolicy.drop:
        raise SkipQuestionException()

    raise Exception(f"Can't process '{table_policy.name}' table policy")


def format_any_body_part(
        body_part: bs4.element.Tag,
        config: models.StackOverflowParserConfig) -> typing.Optional[str]:
    if body_part.name == 'p':
        return format_body_text(body_part)
    if body_part.name == 'blockquote':
        return format_body_text(body_part)
    if body_part.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        return format_body_text(body_part)
    if body_part.name in ['ol', 'ul', 'sub', 'strong']:
        return format_body_text(body_part)
    if body_part.name in ['pre', 'code']:
        return format_body_code(
            body_part, config.code_policy, config.code_embedding)
    if body_part.name == 'div' and (
            's-table-container' in body_part.attrs.get('class', [])):
        return format_body_table(
            body_part, config.tables_policy, config.table_embedding)
    if body_part.name in ['hr', 'div', 'img', 'br']:
        return ""

    logger.error(f"Unexpected body part: {body_part}."
                 f"Raw body can be seen in next debug log.")
    logger.debug(body_part.text)
    raise SkipQuestionException()


def format_body(tag: bs4.element.Tag,
                config: models.StackOverflowParserConfig) -> str:
    body = tag.find(
        'div',
        {
            'class': 's-prose',
        },
    )

    body_parts_formatted = []

    for body_part in body.children:
        body_part: typing.Union[bs4.element.NavigableString, bs4.element.Tag]
        if isinstance(body_part, bs4.element.NavigableString):
            continue
        body_part_formatted = format_any_body_part(body_part, config)
        body_parts_formatted.append(body_part_formatted)

    return "\n".join(body_parts_formatted)


def format_question_answer(
        tag: bs4.element.Tag, config: models.StackOverflowParserConfig,
) -> typing.Optional[models.StackOverflowAnswer]:
    answer = models.StackOverflowAnswer()
    answer.id = tag.attrs.get('data-answerid')
    answer.score = int(tag.attrs.get('data-score', 0))
    answer.has_accepted = 'js-accepted-answer' in tag.attrs.get('class', [])

    try:
        answer.body = format_body(tag, config)
    except SkipQuestionException:
        return None

    return answer


def is_answer_fits_config(
        answer: models.StackOverflowAnswer,
        config: models.StackOverflowParserConfig):
    if answer.score < config.min_answer_score:
        return False
    if config.max_answer_score is not None and (
            answer.score > config.max_answer_score
    ):
        return False
    if config.only_accepted_answers:
        return answer.has_accepted

    return True


def format_question_answers(
        soap: bs4.BeautifulSoup, config: models.StackOverflowParserConfig,
) -> typing.List[models.StackOverflowAnswer]:
    answers = []

    all_answers = soap.find_all(
        'div',
        {
            'class': 'answer',
        },
    )

    for answer in all_answers:
        answer_formatted = format_question_answer(answer, config)
        if answer_formatted is None:
            continue
        if is_answer_fits_config(answer_formatted, config):
            answers.append(answer_formatted)

    return answers[:config.answers_limit]


def format_answers_count(
        soap: bs4.BeautifulSoup):
    answers_count_block = soap.find(
        'span',
        {
            'itemprop': 'answerCount',
        },
    )

    return int(answers_count_block.text)


def format_question(
        question_id: str,
        soap: bs4.BeautifulSoup,
        config: models.StackOverflowParserConfig
) -> typing.Optional[models.StackOverflowQuestion]:
    question = models.StackOverflowQuestion()
    question.id = question_id
    question.title = format_question_title(soap)

    question_tag = soap.find(
        'div',
        {
            'class': 'question',
        },
    )

    question.score = format_question_score(question_tag)

    try:
        question.body = format_body(question_tag, config)
    except SkipQuestionException:
        return None

    answers_tag = soap.find(
        'div',
        {
            'id': 'answers',
        },
    )

    question.answers_count = format_answers_count(answers_tag)
    question.answers = format_question_answers(answers_tag, config)

    if len(question.answers) == 0:
        logger.debug(f'Cant find suitable answers for {question_id}')
        return None

    return question
