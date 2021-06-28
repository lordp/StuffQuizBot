#Stuff Quiz Discord Bot

This is a Discord bot that brings the Stuff News daily quizzes to Discord. It's written in Python and makes use of the discord.py library, and PostgreSQL for storage.

Installation should be as simple as cloning the repo, installing the dependencies through the `requirements.txt` file and running `python quiz.py` to create the database tables and pull down the 10 most recent published quizzes. To run the bot, you'll need a token from Discord, which you paste into the relevant place in `bot.py` and run  `python bot.py` to start the bot.

Once the bot is running, go into the channel where you want the bot to live and type `+set-channel general` to set the channel where all commands will be responded to - feel free to change the prefix (in `bot.py`, line 9) to something else if you wish.