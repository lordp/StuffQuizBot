import discord
from discord.ext import commands, tasks
from terminaltables import AsciiTable
import time
import math
import random
import json

from quiz import Quiz, Player, PlayerQuiz, session, format_time, get_riddles
from sqlalchemy import func


class QuizBot(commands.Cog):
    def __init__(self, bot_obj):
        self.bot = bot_obj
        self.in_quiz = {}
        self.config = {}

        try:
            with open("config.json") as config:
                self.config = json.load(config)
        except FileNotFoundError:
            print("Config file not found!")

        self.announce.start()

    def cog_unload(self):
        self.announce.cancel()

    @commands.group()
    async def quiz(self, ctx):
        """Quiz commands"""
        if ctx.invoked_subcommand is None:
            await ctx.send_help('quiz')

    @quiz.group(name="list")
    async def list_quiz(self, ctx):
        """Show a list of the 10 most recent quizzes."""
        quizzes = session.query(Quiz).order_by(Quiz.riddle_id.desc()).limit(10)

        data = [["#", "Name", "Questions"]]
        for quiz in quizzes:
            data.append([quiz.id, quiz.name, len(quiz.questions)])

        table_instance = AsciiTable(data)
        table_instance.justify_columns[2] = "center"

        msg = f"```\n{table_instance.table}```"

        await ctx.send(msg)

    @quiz.group(name="try")
    async def try_quiz(self, ctx, quiz_id: int):
        """Try a quiz"""

        quiz = session.query(Quiz).where(Quiz.id == quiz_id).first()
        if not quiz:
            await ctx.send(f"Sorry, quiz #{quiz_id} does not exist.")
        else:
            user = ctx.author
            self.in_quiz[user] = {
                "started_at": time.time(),
                "score": 0
            }

            player = session.query(Player).where(Player.discord_id == user.id).first()
            if not player:
                player = Player(name=user.name, discord_id=user.id)
                session.add(player)
                session.commit()

            if not user.dm_channel:
                dm = await user.create_dm()
            else:
                dm = user.dm_channel

            await dm.send(quiz.name)

            correct_answer = 0
            correct_answers = []

            for question_number, question in enumerate(quiz.questions):
                msg = f"```Question #{question_number + 1}: {question.question_text}\n"
                if question.freetext_question:
                    correct_answers = [a.answer_text for a in question.answers]
                    msg += "Type your answer below"
                else:
                    for answer_number, answer in enumerate(random.sample(question.answers, len(question.answers))):
                        msg += f"{answer_number + 1} - {answer.answer_text}\n"
                        if answer.answer_correct:
                            correct_answer = answer_number + 1

                msg += "```"

                await dm.send(file=discord.File(question.question_image))
                await dm.send(msg)

                response = await self.bot.wait_for("message", check=lambda message: message.author == user)
                if (not question.freetext_question and int(response.content) == correct_answer) or response.content.lower() in correct_answers:
                    self.in_quiz[user]["score"] += 1
                    correct_msg = "Correct!"
                else:
                    correct_msg = "Incorrect!"

                await dm.send(f"{correct_msg} {self.in_quiz[user]['score']} / {len(quiz.questions)}")

            await dm.send("Done!")

            time_taken = math.floor(time.time() - self.in_quiz[user]["started_at"])
            perfect = self.in_quiz[user]['score'] == len(quiz.questions)
            pq = PlayerQuiz(player_id=player.id, quiz_id=quiz.id, score=self.in_quiz[user]['score'], time_taken=time_taken, perfect=perfect)
            session.add(pq)
            session.commit()

            await ctx.send(f"Score for {user.name}: {self.in_quiz[user]['score']} / {len(quiz.questions)} in {format_time(time_taken)}")

    @quiz.group()
    async def leaderboard(self, ctx, quiz_id: int = None):
        """Show the leaderboard for a quiz."""
        if quiz_id is None:
            lb = session.query(
                Player.name,
                func.count(PlayerQuiz.quiz_id).label('quiz_count'),
                func.sum(PlayerQuiz.time_taken).label('total_time'),
                func.count(1).filter(PlayerQuiz.perfect).label('perfect_count')
            ).join(Player).group_by(Player.name)

            data = [["Name", "Quiz Count", "Avg Time", "Perfect Count"]]
            for row in lb:
                data.append([row.name, row.quiz_count, format_time(row.total_time / row.quiz_count), row.perfect_count])

            table_instance = AsciiTable(data)
            table_instance.justify_columns[1] = "center"
            table_instance.justify_columns[2] = "center"
            table_instance.justify_columns[3] = "center"

            msg = f"```\n{table_instance.table}```\nTo view a specific quiz leaderboard, try `+quiz leaderboard <quiz number>`"
        else:
            data = [["Name", "Score", "Time", "Perfect"]]
            pq = session.query(PlayerQuiz).where(PlayerQuiz.quiz_id == quiz_id).order_by(PlayerQuiz.score.desc(), PlayerQuiz.time_taken)
            for p in pq:
                data.append([p.player.name, p.score, format_time(p.time_taken), "Yes" if p.perfect else "No"])

            table_instance = AsciiTable(data)
            table_instance.justify_columns[1] = "center"
            table_instance.justify_columns[2] = "center"

            msg = f"```\n{table_instance.table}```"

        await ctx.send(f"{msg}")

    @tasks.loop(seconds=60)
    async def announce(self):
        quizzes = get_riddles()
        if len(quizzes) > 0:
            channel_id = self.config["announce_channel"]
            channel = self.bot.get_channel(channel_id)
            for quiz in quizzes:
                await channel.send(f"New quiz posted: #{quiz.id} - {quiz.name}")

    @announce.before_loop
    async def before_announce(self):
        await self.bot.wait_until_ready()

