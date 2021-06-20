import discord
from discord.ext import commands
from cogs.quizbot import QuizBot

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("+"),
    description="Quiz Bot",
    intents=intents
)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")


bot.add_cog(QuizBot(bot))
bot.run("TOKEN", reconnect=True)
