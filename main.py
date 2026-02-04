import discord
from discord import app_commands
from discord.ext import commands
import os

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True 
        super().__init__(command_prefix='.', intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"✅ تم تحديث أوامر Slash!")

bot = MyBot()

# قاعدة البيانات
clans = {} 

@bot.event
async def on_ready():
    print(f'🚀 {bot.user} جاهز للعمل!')

# --- الأوامر المحدثة ---

# 1. أمر حذف الكلان (للقائد فقط)
@bot.tree.command(name="clan-delete", description="حذف الكلان الخاص بك نهائياً")
async def clan_delete(interaction: discord.Interaction):
    user_id = interaction.user.id
    clan_to_delete = None
    
    # البحث عن الكلان الذي يملكه المستخدم
    for name, data in clans.items():
        if data['owner'] == user_id:
            clan_to_delete = name
            break
    
    if clan_to_delete:
        del clans[clan_to_delete]
        await interaction.response.send_message(f"🗑️ تم حذف كلان **{clan_to_delete}** بنجاح.")
    else:
        await interaction.response.send_message("❌ أنت لا تملك كلان لتحذفه.", ephemeral=True)

# 2. أمر معلومات الكلان
@bot.tree.command(name="clan-info", description="عرض معلومات الكلان")
async def clan_info(interaction: discord.Interaction, name: str):
    if name not in clans:
        return await interaction.response.send_message("❌ الكلان غير موجود.", ephemeral=True)
    
    data = clans[name]
    embed = discord.Embed(title=f"🛡️ معلومات كلان {name}", color=discord.Color.green())
    embed.add_field(name="القائد", value=f"<@{data['owner']}>")
    embed.add_field(name="النقاط", value=data.get('points', 0))
    embed.add_field(name="الأعضاء", value=len(data['members']) + 1)
    await interaction.response.send_message(embed=embed)

# 3. أمر إضافة عضو
@bot.tree.command(name="clan-add-mem", description="إضافة عضو للكلان (للقائد)")
async def add_member(interaction: discord.Interaction, member: discord.Member):
    user_clan = next((n for n, d in clans.items() if d['owner'] == interaction.user.id), None)
    if not user_clan:
        return await interaction.response.send_message("❌ يجب أن تكون قائد كلان لإضافة أعضاء.", ephemeral=True)
    
    clans[user_clan]['members'].append(member.id)
    await interaction.response.send_message(f"✅ تم إضافة {member.mention} إلى كلان **{user_clan}**.")

# 4. أمر ترتيب التحديات
@bot.tree.command(name="leaderboard-challenges", description="ترتيب انتصارات التحديات")
async def challenge_lb(interaction: discord.Interaction):
    embed = discord.Embed(title="🏆 إحصائيات التحديات", description="لم يتم تسجيل تحديات بعد.", color=discord.Color.gold())
    await interaction.response.send_message(embed=embed)

# (تم حذف أوامر الـ War بناءً على طلبك)

bot.run(os.getenv('TOKEN'))
