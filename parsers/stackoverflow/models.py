import typing
import enum


class StackOverflowParserTag(enum.Enum):
    python = 'python'
    python3x = 'python-3.x'
    python2x = 'python-2.7'
    postgresql = 'postgresql'
    cpp = 'c++'
    django = 'django'
    linux = 'linux'


class StackOverflowParserRanking(enum.Enum):
    newest = 'newest'
    featured = 'featured'
    frequent = 'frequent'
    votes = 'votes'
    active = 'active'
    unanswered = 'unanswered'


class StackOverflowParserPolicy(enum.Enum):
    leave_as_is = 0
    skip = 1
    drop = 2
    embed = 3
    parse = 4


class StackOverflowParserFilter:
    def __init__(
        self, tags: typing.List[StackOverflowParserTag],
        rank_by: StackOverflowParserRanking = StackOverflowParserRanking.newest,
        min_score: int = 0,
        max_score: typing.Optional[int] = None,
        min_answers_count: int = 0,
        max_answers_count: typing.Optional[int] = None,
        has_accepted_answer: typing.Optional[bool] = None,
    ):
        self.tags = tags
        self.rank_by = rank_by
        self.min_score = min_score
        self.max_score = max_score
        self.min_answers_count = min_answers_count
        self.max_answers_count = max_answers_count
        self.has_accepted_answer = has_accepted_answer


class StackOverflowParserConfig:
    def __init__(
        self, answers_limit: int = 1,
        only_accepted_answers: bool = False,
        min_answer_score: int = 0,
        max_answer_score: typing.Optional[int] = None,
        images_policy: StackOverflowParserPolicy = (
            StackOverflowParserPolicy.leave_as_is
        ),
        image_embedding='<IMAGE>|</IMAGE>',
        tables_policy: StackOverflowParserPolicy = (
            StackOverflowParserPolicy.leave_as_is
        ),
        table_embedding='<TABLE>|</TABLE>',
        code_policy: StackOverflowParserPolicy = (
            StackOverflowParserPolicy.leave_as_is
        ),
        code_embedding='<CODE>|</CODE>',
    ):
        self.answers_limit = answers_limit
        self.only_accepted_answers = only_accepted_answers
        self.min_answer_score = min_answer_score
        self.max_answer_score = max_answer_score
        self.images_policy = images_policy
        self.image_embedding = image_embedding
        self.tables_policy = tables_policy
        self.table_embedding = table_embedding
        self.code_policy = code_policy
        self.code_embedding = code_embedding


class StackOverflowQuestionBlock:
    score: int
    answers_count: int
    has_accepted_answer: bool = False


class StackOverflowAnswer:
    id: str
    score: int
    has_accepted: bool = False
    body: str

    def dict(self):
        return {
            'id': self.id,
            'score': self.score,
            'has_accepted': self.has_accepted,
            'body': self.body,
        }


class StackOverflowQuestion:
    id: str
    title: str
    score: int
    answers_count: int
    body: str

    answers: typing.List[StackOverflowAnswer]

    def dict(self):
        answers_list = list(map(lambda answer: answer.dict(), self.answers))
        return {
            'id': self.id,
            'title': self.title,
            'score': self.score,
            'answers_count': self.answers_count,
            'body': self.body,
            'answers': answers_list,
        }
