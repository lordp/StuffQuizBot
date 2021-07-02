# Stuff Quiz Discord Bot
This is a Discord bot that brings the Stuff News daily quizzes to Discord. It's written in Python and makes use of the discord.py library, and PostgreSQL for storage.

## Installation
1. Clone the repo
1. Install dependencies - `pip install -r requirements.txt`
1. Create the database - `createdb stuffquiz`
1. Create database structure and download recently published quizzes - `python quiz.py`
1. Obtain a Discord token and paste into `bot.py`
1. Run the bot - `python bot.py`

## Bot setup
Once the bot is running, and invited to the server, go into the channel where you want the bot to live and type `+set-channel general` to set the channel where all commands will be responded to - if you wish to change the prefix, edit `bot.py` on line 9 to choose.
