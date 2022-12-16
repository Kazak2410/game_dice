import sqlite3 as sq
import random
import os
import disnake
from disnake.ext import commands
from disnake.ui import Button, View
from dotenv import load_dotenv, find_dotenv


load_dotenv(find_dotenv())

bot = commands.Bot(command_prefix="/", intents=disnake.Intents.all())


@bot.event
async def on_ready():
    print("bot connected")

    with sq.connect("database.db") as db:
        cursor = db.cursor()

        cursor.execute("""CREATE TABLE IF NOT EXISTS players(
        id INTEGER PRIMARY KEY,
        name TEXT,
        games INTEGER NOT NULL DEFAULT 0, 
        victories INTEGER NOT NULL DEFAULT 0,
        draws INTEGER NOT NULL DEFAULT 0,
        defeats INTEGER NOT NULL DEFAULT 0
        )""")

    if db:
        print("database connected")


class MyButton(Button):
    async def callback(self, interaction: disnake.ApplicationCommandInteraction):
        await interaction.response.defer()


@bot.command()
async def play(ctx):
    button_launch = MyButton(style=disnake.ButtonStyle.green, label='Join game✅')
    button_play = MyButton(style=disnake.ButtonStyle.red, label='Roll the dice🎲')

    view = View()
    view.add_item(button_launch)
    main = await ctx.send(view=view, embed=disnake.Embed(title="Invite a person to start a game!🙂"))

    def check_1(m):
        return m.channel == ctx.channel and m.author == ctx.author

    def check_2(m):
        return m.channel == ctx.channel and m.author != ctx.author

    second_players = await bot.wait_for("button_click", check=check_2)

    def check_3(m):
        return m.channel == ctx.channel and m.author == second_players.author

    view = View()
    view.add_item(button_play)
    await main.edit(view=view, embed=disnake.Embed(title="Roll the dice..."))

    try:
        db = sq.connect("database.db")
        cursor = db.cursor()
        game_field = ""

        player_1 = await bot.wait_for("button_click", check=check_1)
        res_1 = str(random.randint(1, 6))

        game_field += f"{player_1.author.mention}: **{res_1}**"
        await main.edit(embed=disnake.Embed(title="The field of war🛡", description=game_field, colour=disnake.Colour.red()))

        player_2 = await bot.wait_for("button_click", check=check_3)
        res_2 = str(random.randint(1, 6))

        game_field += f"⚔**{res_2}** :{player_2.author.mention}"
        await main.edit(embed=disnake.Embed(title="The field of war🛡", description=game_field, colour=disnake.Colour.red()))

        if cursor.execute("SELECT name FROM players WHERE name = ?", [str(player_1.author)]).fetchone() is None:
            cursor.execute("INSERT INTO players(name) VALUES(?)", [str(player_1.author)])

        if cursor.execute("SELECT name FROM players WHERE name = ?", [str(player_2.author)]).fetchone() is None:
            cursor.execute("INSERT INTO players(name) VALUES(?)", [str(player_2.author)])

        cursor.execute("UPDATE players SET games = games + ? WHERE name = ?", [1, str(player_1.author)])
        cursor.execute("UPDATE players SET games = games + ? WHERE name = ?", [1, str(player_2.author)])
        db.commit()

        if int(res_1) > int(res_2):
            game_field += f"\n{'-'* 40}\n{player_1.author.mention} **Won!**🏆"
            await main.edit(embed=disnake.Embed(title="The field of war🛡", description=game_field, colour=disnake.Colour.green()), view=None)
            cursor.execute("UPDATE players SET victories = victories + ? WHERE name = ?", [1, str(player_1.author)])
            cursor.execute("UPDATE players SET defeats = defeats + ? WHERE name = ?", [1, str(player_2.author)])
            db.commit()

        elif int(res_1) < int(res_2):
            game_field += f"\n{'-'* 40}\n{player_2.author.mention} **Won!**🏆"
            await main.edit(embed=disnake.Embed(title="The field of war🛡", description=game_field, colour=disnake.Colour.green()), view=None)
            cursor.execute("UPDATE players SET victories = victories + ? WHERE name = ?", [1, str(player_2.author)])
            cursor.execute("UPDATE players SET defeats = defeats + ? WHERE name = ?", [1, str(player_1.author)])
            db.commit()
        else:
            game_field += f"\n{'-'* 40}\n**Draw!**🤝"
            await main.edit(embed=disnake.Embed(title="The field of war🛡", description=game_field, colour=disnake.Colour.blurple()), view=None)
            cursor.execute("UPDATE players SET draws = draws + ? WHERE name in (?, ?)", [1, str(player_1.author), str(player_2.author)])
            db.commit()

    except sq.Error as e:
        print("Error", e)
    finally:
        cursor.close()
        db.close()


@bot.command()
async def stat(ctx):
    try:
        db = sq.connect("database.db")
        cursor = db.cursor()

        stat_field = "Enter the name of player"
        await ctx.send(embed=disnake.Embed(title="The statistics📚", description=stat_field, colour=disnake.Colour.red()))

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        event = await bot.wait_for("message", check=check)
        inf_players = cursor.execute("SELECT name, victories, draws, defeats FROM players WHERE name == ?", [str(event.content)]).fetchall()

        stat_field = ['**Name**', "**Victories**", "**Draws**", "**Defeats**"]
        for i in range(len(inf_players[0])):
            stat_field[i] += f": {inf_players[0][i]}"

        stat_field = ''.join(f"{i}\n" for i in stat_field)

        await ctx.send(embed=disnake.Embed(title="The statistics📚", description=stat_field, colour=disnake.Colour.red()))

    except sq.Error as e:
        print("Error", e)
    finally:
        cursor.close()
        db.close()


def run_bot():
    bot.run(os.getenv('TOKEN'))