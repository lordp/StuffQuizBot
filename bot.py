import discord
from discord.ext import commands
from cogs.quizbot import QuizBot
import os

if 'BOT_TOKEN' not in os.environ:
    exit("BOT_TOKEN env variable must be set")

bot_prefix = os.environ.get("BOT_PREFIX", "+")

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(bot_prefix),
    description="Quiz Bot",
    intents=intents
)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} using prefix {bot_prefix}")


bot.add_cog(QuizBot(bot))
bot.run(os.environ.get('BOT_TOKEN'), reconnect=True)
