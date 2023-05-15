import discord
import asyncio
import json
import os
from discord.ext import commands

# Define your bot's token and intents
TOKEN = ''
intents = discord.Intents.all()
intents.members = True
intents.typing = True
intents.presences = True

# Create a new instance of the commands.Bot class
bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_message(message):
    if message.content.startswith('/'):
        await bot.process_commands(message)
        
@bot.command()
async def match(ctx, player: discord.Member):
    # Send a message to the mentioned player
    await ctx.send(f"{ctx.author.mention} has requested a 1v1 match with {player.mention}. Do you accept? (Type /accept or /decline)")

    # Wait for the player's response
    def check(message):
        return message.author == player and message.content.lower() in ['/accept', '/decline']

    try:
        message = await bot.wait_for('message', timeout=300.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send(f"{player.mention} did not respond in time. Match request declined.")
        return

    # Check if the player accepted or declined
    if message.content.lower() == '/accept':
        await ctx.send(f"{player.mention} has accepted the match request. The match will begin shortly.")
        await ctx.send(f"Both players can now enter their scores using the /score command.")

        # Store the match details in the matches dictionary
        players = (ctx.author, player)
        matches[players] = (None, None)
    else:
        await ctx.send(f"{player.mention} has declined the match request.")

matches = {}

@bot.command()
async def score(ctx, score1: int, score2: int):
    if score1 < 0 or score2 < 0:
        await ctx.send("Invalid scores. Scores must be non-negative.")
        return

    players = None
    for k, v in matches.items():
        if ctx.author in k:
            if None in v:
                players = k
                break
            else:
                await ctx.send("You have already entered your scores for this match.")
                return

    if players is None:
        await ctx.send("No ongoing match found for you.")
        return

    player1_id = players[0].id
    player2_id = players[1].id

    if ctx.author.id == player1_id:
        matches[players] = (score1, score2, None)
    else:
        matches[players] = (matches[players][0], matches[players][1], score1, score2)

    if len(matches[players]) == 4:
        score1, score2, score3, score4 = matches[players]
        if None in (score3, score4):
            await ctx.send("One of the players has not reported their score yet.")
            return

        if score1 != score3 or score2 != score4:
            await ctx.send("There's a mismatch in score reporting. Opening up a dispute channel...")

            winner, loser = players[0], players[1]
            del matches[players]

            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                winner: discord.PermissionOverwrite(read_messages=True),
                loser: discord.PermissionOverwrite(read_messages=True),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True)
            }
            dispute_channel = await ctx.guild.create_text_channel(
                name=f"{winner.display_name}-vs-{loser.display_name}", overwrites=overwrites)
            await dispute_channel.send(f"There is a dispute in the match between {winner.mention} and {loser.mention}.")
            await dispute_channel.send(f"{winner.mention} entered a score of {score1}-{score2}.")
            await dispute_channel.send(f"{loser.mention} entered a score of {score3}-{score4}.")
            await dispute_channel.send("Admin will review the scores and make a decision.")
        else:
            await ctx.send(f"The match between {players[0].mention} and {players[1].mention} ended in a tie with a score of {score1}-{score2}.")
            del matches[players]

        return
    
# Start the bot
bot.run(TOKEN)