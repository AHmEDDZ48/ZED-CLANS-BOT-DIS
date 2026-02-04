import discord
from discord import app_commands
from discord.ext import commands
import os

# 1. إعداد البوت الأساسي
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix='.', intents=intents)

    # هذا الجزء ضروري لمزامنة أوامر Slash مع ديسكورد
    async def setup_hook(self):
        await self.tree.sync()
        print(f"✅ تم مزامنة أوامر Slash بنجاح!")

bot = MyBot()

# قاعدة بيانات وهمية (للتجربة)
clans = {} # {clan_name: {"owner": id, "points": 0, "members": []}}

@bot.event
async def on_ready():
    print(f'🚀 {bot.user} متصل الآن!')

# --- أوامر الكلانات المتقدمة (Slash Commands) ---

# 1. أمر إنشاء كلان
@bot.tree.command(name="clan-create", description="إنشاء كلان جديد")
async def clan_create(interaction: discord.Interaction, name: str):
    user_id = interaction.user.id
    if name in clans:
        return await interaction.response.send_message("❌ هذا الاسم موجود مسبقاً!", ephemeral=True)
    
    clans[name] = {"owner": user_id, "points": 0, "members": []}
    await interaction.response.send_message(f"✅ تم إنشاء كلان **{name}** بنجاح!")

# 2. أمر قائمة الكلانات
@bot.tree.command(name="clan-list", description="عرض قائمة الكلانات")
async def clan_list(interaction: discord.Interaction):
    if not clans:
        return await interaction.response.send_message("📭 لا توجد كلانات حالياً.")
    
    embed = discord.Embed(title="📋 قائمة الكلانات", color=discord.Color.blue())
    for name, data in clans.items():
        embed.add_field(name=name, value=f"النقاط: {data['points']} | الأعضاء: {len(data['members'])+1}", inline=False)
    
    await interaction.response.send_message(embed=embed)

# 3. أمر الترتيب (Leaderboard)
@bot.tree.command(name="clan-leaderboard", description="عرض ترتيب الكلانات حسب النقاط")
async def leaderboard(interaction: discord.Interaction):
    if not clans:
        return await interaction.response.send_message("❌ لا توجد بيانات للترتيب.")
    
    # ترتيب الكلانات حسب النقاط
    sorted_clans = sorted(clans.items(), key=lambda x: x[1]['points'], reverse=True)
    
    leaderboard_text = ""
    for i, (name, data) in enumerate(sorted_clans[:10], 1):
        leaderboard_text += f"**#{i} {name}** — {data['points']} نقطة\n"
    
    embed = discord.Embed(title="🏆 ترتيب أفضل الكلانات", description=leaderboard_text, color=discord.Color.gold())
    await interaction.response.send_message(embed=embed)

# 4. أمر إضافة نقاط (للمشرفين فقط أو لتجربتك)
@bot.tree.command(name="clan-addpoints", description="إضافة نقاط لكلان محدد")
async def add_points(interaction: discord.Interaction, name: str, points: int):
    if name not in clans:
        return await interaction.response.send_message("❌ الكلان غير موجود.", ephemeral=True)
    
    clans[name]['points'] += points
    await interaction.response.send_message(f"➕ تم إضافة {points} نقطة لكلان **{name}**. المجموع الآن: {clans[name]['points']}")

# تشغيل البوت
bot.run(os.getenv('TOKEN'))
