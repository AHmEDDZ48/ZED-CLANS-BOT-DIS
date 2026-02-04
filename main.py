import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ {bot.user.name} جاهز للعمل!')

@bot.command()
async def clans(ctx):
    embed = discord.Embed(
        title="🏆 قائمة كلانات ZED الرسمية",
        description="إليك إحصائيات الكلانات الحالية:",
        color=discord.Color.gold()
    )
    embed.add_field(name="⚔️ كـلان الـقـمـة", value="القائد: قيد الانتظار\nالنقاط: 0", inline=False)
    embed.set_footer(text="نظام إدارة الكلانات - ZED")
    await ctx.send(embed=embed)

# التوكن سيتم سحبه من إعدادات Koyeb للأمان
token = os.environ.get('TOKEN')
bot.run(token)
