import json
import re
import pathlib
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from sqlalchemy.orm import declarative_base, relationship, Session, backref
from sqlalchemy import Table, Column, Integer, String, ForeignKey, Boolean, BigInteger, create_engine, select
from sqlalchemy.schema import Index
from sqlalchemy.sql.expression import null
from sqlalchemy.sql.sqltypes import DateTime

engine = create_engine("postgresql:///stuffquiz")

Base = declarative_base()


class Quiz(Base):
    __tablename__ = 'quizzes'

    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, index=True, nullable=False)
    riddle_id = Column(Integer, index=True, nullable=False)
    name = Column(String(250), nullable=False)
    created_at = Column(DateTime)

    questions = relationship("Question", backref=backref("quiz"))
    players = relationship("PlayerQuiz", backref=backref("quiz"))

    def __repr__(self):
       return f"Quiz(id={self.id!r}, name={self.name!r}, quiz_id={self.quiz_id!r}, riddle_id={self.riddle_id!r}, questions={len(self.questions)})"


class Question(Base):
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey('quizzes.id'), index=True)
    question_text = Column(String(250), nullable=False)
    question_image = Column(String(250))
    freetext_question = Column(Boolean, default=False)

    answers = relationship("Answer", backref=backref("question"))

    def __repr__(self):
        return f"Question(id={self.id!r}, quiz_id={self.quiz_id!r}, question_text={self.question_text!r}, answers={len(self.answers)})"


class Answer(Base):
    __tablename__ = 'answers'

    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey('questions.id'))
    answer_text = Column(String(250), nullable=False)
    answer_correct = Column(Boolean, default=False, nullable=False)

    def __repr__(self):
       return f"Answer(id={self.id!r}, question_id={self.question_id!r}, answer_text={self.answer_text!r}, correct={self.answer_correct})"


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    discord_id = Column(BigInteger, index=True)
    name = Column(String(50), nullable=False)
    ping = Column(Boolean, default=False)

    quizzes = relationship("PlayerQuiz", backref=backref("player"))


class PlayerQuiz(Base):
    __tablename__ = "player_quizzes"

    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'))
    quiz_id = Column(Integer, ForeignKey('quizzes.id'))
    score = Column(Integer)
    time_taken = Column(Integer)
    perfect = Column(Boolean, default=False)


def get_riddle(quiz):
    print(quiz.name)

    image_dir = f"images/{quiz.quiz_id}"
    if not pathlib.Path(image_dir).exists():
        pathlib.Path(image_dir).mkdir(parents=True)

    req = requests.get(f"https://www.riddle.com/a/{quiz.riddle_id}")
    soup = BeautifulSoup(req.content, features="html.parser")

    script = str(soup.find_all("script")[1])
    script = script.replace("<script>", "").replace("window.riddle_view = ", "").replace("</script>", "")
    script = script.replace("data:", '"data":').replace("translations", '"translations"').replace("questionBankData", '"questionBankData"')
    data = json.loads(script)

    quiz.created_at = datetime.fromtimestamp(data['data']['data']['published']['date'])
    session.commit()

    questions = [q for q in data['data']['data']['pageGroups'] if q['templateId'] == 'quiz-question'][0]['pages']
    for q in questions:
        freetext = False

        question_text = q['title_plain']
        question = session.query(Question).where(Question.quiz_id == quiz.id, Question.question_text == question_text).first()
        if not question:
            image = requests.get(q["image"]["srcCDN"])
            image_path = f"{image_dir}/{pathlib.Path(q['image']['srcCDN']).name}"
            with open(image_path, "wb") as image_file:
                image_file.write(image.content)

            freetext = "textAnswers" in q
            question = Question(quiz_id=quiz.id, question_text=q['title_plain'], question_image=image_path, freetext_question=freetext)
            session.add(question)
            session.commit()

        print(question.question_text)
        if freetext:
            for a in q['textAnswers']:
                answer = session.query(Answer).where(Answer.question_id == question.id, Answer.answer_text == a.lower()).first()
                if not answer:
                    answer = Answer(question_id=question.id, answer_text=a.lower(), answer_correct=False)
                    session.add(answer)
                    session.commit()
        else:
            for i, a in enumerate(q['allAnswers']):
                answer_text = a['label']
                answer_correct = q['answerIndex'] == i
                answer = session.query(Answer).where(Answer.question_id == question.id, Answer.answer_text == answer_text, Answer.answer_correct == answer_correct).first()
                if not answer:
                    answer = Answer(question_id=question.id, answer_text=answer_text, answer_correct=answer_correct)
                    session.add(answer)
                    session.commit()


def get_riddles():
    req = requests.get("https://www.stuff.co.nz/national/quizzes")
    soup = BeautifulSoup(req.content, features="html.parser")

    added_quizzes = []

    quiz_links = soup.select("a[href*='national/quizzes/']")[1:]
    quizzes = [[a.text.strip(), a['href'].replace("https://www.stuff.co.nz", "")] for a in quiz_links if a.text.strip() != ""]
    for q in quizzes[:10]:
        quiz_id = q[1].split('/')[3]
        quiz = session.query(Quiz).where(Quiz.quiz_id == quiz_id).first()
        if not quiz:
            quiz = Quiz(name=q[0], quiz_id=quiz_id)
            req = requests.get(f"https://www.stuff.co.nz{q[1]}")
            riddle_id = re.search("https://www.riddle.com/a/(\d+)", req.content.decode("utf-8"))
            quiz.riddle_id = riddle_id.group(1)

            session.add(quiz)
            session.commit()

            get_riddle(quiz)

            added_quizzes.append(quiz)

    return added_quizzes


def format_time(seconds):
    m, s = divmod(seconds, 60)
    if m > 60:
        h, m = divmod(m, 60)
        return '{h:0.0f}h{m:02.0f}m{s:02.0f}s'.format(h=h, m=m, s=s)
    elif m > 0:
        return '{m:0.0f}m{s:02.0f}s'.format(m=m, s=s)
    else:
        return '{s:0.0f}s'.format(s=s)


Base.metadata.create_all(engine)
session = Session(engine)

if __name__ == "__main__":
    get_riddles()