# Stuff Quiz Discord Bot
This is a Discord bot that brings the Stuff News daily quizzes to Discord. It's written in Python and makes use of the discord.py library, and PostgreSQL for storage.

## Installation
1. Clone the repo
1. Make sure you have Docker and Docker Compose installed - 20.10.7 and 1.29.2 respectively were used during development.
1. Obtain a token from Discord and paste it into `bot.env`. You might want to change the prefix in the same file as well.
1. Set the database values as required in `database.env`
1. Run `docker-compose build` and `docker-compose up` to get things running

## Bot setup
Once the bot is running, and invited to the server, go into the channel where you want the bot to live and type `+set-channel general` to set the channel where all commands will be responded to.
