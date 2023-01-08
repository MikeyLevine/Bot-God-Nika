import asyncio
import json
import os
import platform
import random
import sys

import aiosqlite
import discord
from keep_alive import keep_alive
from discord.ext import commands, tasks
from discord.ext.commands import Bot, Context

import exceptions

if not os.path.isfile(
    f"{os.path.realpath(os.path.dirname(__file__))}/config.json"):
  sys.exit("'config.json' not found! Please add it and try again.")
else:
  with open(
      f"{os.path.realpath(os.path.dirname(__file__))}/config.json") as file:
    config = json.load(file)

intents = discord.Intents.all()

bot = Bot(command_prefix=commands.when_mentioned_or(config["prefix"]),
          intents=intents,
          help_command=None)


async def init_db():
  async with aiosqlite.connect(
      f"{os.path.realpath(os.path.dirname(__file__))}/database/database.db"
  ) as db:
    with open(
        f"{os.path.realpath(os.path.dirname(__file__))}/database/schema.sql"
    ) as file:
      await db.executescript(file.read())
    await db.commit()


bot.config = config



@bot.event
async def on_ready() -> None:

  print(f"Logged in as {bot.user.name}")
  print(f"discord.py API version: {discord.__version__}")
  print(f"Python version: {platform.python_version()}")
  print(f"Running on: {platform.system()} {platform.release()} ({os.name})")
  print("-------------------")
  status_task.start()
  if config["sync_commands_globally"]:
    print("Syncing commands globally...")
    await bot.tree.sync()


@tasks.loop(minutes=1.0)
async def status_task() -> None:

  statuses = ["In Beta v0.1.0"]
  await bot.change_presence(activity=discord.Game(random.choice(statuses)))


@bot.event
async def on_message(message: discord.Message) -> None:

  if message.author == bot.user or message.author.bot:
    return
  await bot.process_commands(message)


@bot.event
async def on_command_completion(context: Context) -> None:

  full_command_name = context.command.qualified_name
  split = full_command_name.split(" ")
  executed_command = str(split[0])
  if context.guild is not None:
    print(
      f"Executed {executed_command} command in {context.guild.name} (ID: {context.guild.id}) by {context.author} (ID: {context.author.id})"
    )
  else:
    print(
      f"Executed {executed_command} command by {context.author} (ID: {context.author.id}) in DMs"
    )


@bot.event
async def on_command_error(context: Context, error) -> None:

  if isinstance(error, commands.CommandOnCooldown):
    minutes, seconds = divmod(error.retry_after, 60)
    hours, minutes = divmod(minutes, 60)
    hours = hours % 24
    embed = discord.Embed(
      title="Hey, please slow down!",
      description=
      f"You can use this command again in {f'{round(hours)} hours' if round(hours) > 0 else ''} {f'{round(minutes)} minutes' if round(minutes) > 0 else ''} {f'{round(seconds)} seconds' if round(seconds) > 0 else ''}.",
      color=0xE02B2B)
    await context.send(embed=embed)
  elif isinstance(error, exceptions.UserBlacklisted):

    embed = discord.Embed(
      title="Error!",
      description="You are blacklisted from using the bot.",
      color=0xE02B2B)
    await context.send(embed=embed)
  elif isinstance(error, exceptions.UserNotOwner):

    embed = discord.Embed(title="Error!",
                          description="You are not the owner of the bot!",
                          color=0xE02B2B)
    await context.send(embed=embed)
  elif isinstance(error, commands.MissingPermissions):
    embed = discord.Embed(title="Error!",
                          description="You are missing the permission(s) `" +
                          ", ".join(error.missing_permissions) +
                          "` to execute this command!",
                          color=0xE02B2B)
    await context.send(embed=embed)
  elif isinstance(error, commands.BotMissingPermissions):
    embed = discord.Embed(title="Error!",
                          description="I am missing the permission(s) `" +
                          ", ".join(error.missing_permissions) +
                          "` to fully perform this command!",
                          color=0xE02B2B)
    await context.send(embed=embed)
  elif isinstance(error, commands.MissingRequiredArgument):
    embed = discord.Embed(
      title="Error!",
      # We need to capitalize because the command arguments have no capital letter in the code.
      description=str(error).capitalize(),
      color=0xE02B2B)
    await context.send(embed=embed)
  raise error

async def load_cogs() -> None:

  for file in os.listdir(
      f"{os.path.realpath(os.path.dirname(__file__))}/cogs"):
    if file.endswith(".py"):
      extension = file[:-3]
      try:
        await bot.load_extension(f"cogs.{extension}")
        print(f"Loaded extension '{extension}'")
      except Exception as e:
        exception = f"{type(e).__name__}: {e}"
        print(f"Failed to load extension {extension}\n{exception}")




keep_alive()
asyncio.run(init_db())
asyncio.run(load_cogs())
bot.run(os.getenv('TOKEN'))
