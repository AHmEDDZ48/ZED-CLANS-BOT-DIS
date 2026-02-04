import discord
from discord import app_commands
from discord.ext import commands
import os

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True # للسماح للبوت بإدارة الأعضاء
        super().__init__(command_prefix='.', intents=intents)

    async def setup_hook(self):
        # هذه الوظيفة هي التي تظهر الـ 12 أمراً في ديسكورد
        await self.tree.sync()
        print(f"✅ تم مزامنة {len(self.tree.get_commands())} أمراً بنجاح!")

bot = MyBot()
clans = {} # قاعدة البيانات المؤقتة

@bot.event
async def on_ready():
    print(f'🚀 {bot.user} جاهز للعمل بجميع الأوامر!')

# 1. معلومات الكلان
@bot.tree.command(name="clan-info", description="عرض معلومات الكلان بالتفصيل")
async def info(interaction: discord.Interaction, name: str):
    if name not in clans:
        return await interaction.response.send_message("❌ الكلان غير موجود.", ephemeral=True)
    d = clans[name]
    embed = discord.Embed(title=f"🛡️ كلان {name}", color=discord.Color.blue())
    embed.add_field(name="القائد", value=f"<@{d['owner']}>")
    embed.add_field(name="النائب", value=f"<@{d['coleader']}>" if d.get('coleader') else "لا يوجد")
    embed.add_field(name="النقاط", value=d.get('points', 0))
    embed.add_field(name="الأعضاء", value=len(d['members']) + 1)
    await interaction.response.send_message(embed=embed)

# 2. قائمة الكلانات
@bot.tree.command(name="clan-list", description="عرض قائمة بكل الكلانات في السيرفر")
async def list_clans(interaction: discord.Interaction):
    if not clans: return await interaction.response.send_message("📭 لا توجد كلانات حالياً.")
    msg = "\n".join([f"🔹 **{n}** | النقاط: {d.get('points', 0)}" for n, d in clans.items()])
    await interaction.response.send_message(f"📋 **قائمة الكلانات:**\n{msg}")

# 3. إنشاء كلان
@bot.tree.command(name="clan-create", description="إنشاء كلان جديد")
async def create(interaction: discord.Interaction, name: str):
    if any(d['owner'] == interaction.user.id for d in clans.values()):
        return await interaction.response.send_message("❌ أنت قائد كلان بالفعل!", ephemeral=True)
    clans[name] = {'owner': interaction.user.id, 'members': [], 'points': 0, 'coleader': None}
    await interaction.response.send_message(f"🎊 تم إنشاء كلان **{name}** بنجاح!")

# 4. طرد عضو
@bot.tree.command(name="clan-remove-mem", description="طرد عضو من الكلان (للقائد)")
async def remove_mem(interaction: discord.Interaction, member: discord.Member):
    clan = next((n for n, d in clans.items() if d['owner'] == interaction.user.id), None)
    if not clan or member.id not in clans[clan]['members']:
        return await interaction.response.send_message("❌ ليس لديك صلاحية أو العضو غير موجود.", ephemeral=True)
    clans[clan]['members'].remove(member.id)
    await interaction.response.send_message(f"👞 تم طرد {member.mention} من الكلان.")

# 5. إضافة عضو
@bot.tree.command(name="clan-add-mem", description="إضافة عضو للكلان")
async def add_mem(interaction: discord.Interaction, member: discord.Member):
    clan = next((n for n, d in clans.items() if d['owner'] == interaction.user.id), None)
    if not clan: return await interaction.response.send_message("❌ يجب أن تكون القائد لإضافة أعضاء.", ephemeral=True)
    clans[clan]['members'].append(member.id)
    await interaction.response.send_message(f"✅ تمت إضافة {member.mention} بنجاح.")

# 6. تعيين قائد جديد (نقل الملكية)
@bot.tree.command(name="clan-s-leader", description="نقل ملكية الكلان لشخص آخر")
async def s_leader(interaction: discord.Interaction, member: discord.Member):
    clan = next((n for n, d in clans.items() if d['owner'] == interaction.user.id), None)
    if not clan: return await interaction.response.send_message("❌ لست القائد!", ephemeral=True)
    clans[clan]['owner'] = member.id
    await interaction.response.send_message(f"👑 تم نقل القيادة إلى {member.mention}.")

# 7. تعيين نائب قائد
@bot.tree.command(name="clan-s-coleader", description="تعيين نائب للقائد")
async def s_coleader(interaction: discord.Interaction, member: discord.Member):
    clan = next((n for n, d in clans.items() if d['owner'] == interaction.user.id), None)
    if not clan: return await interaction.response.send_message("❌ لست القائد!", ephemeral=True)
    clans[clan]['coleader'] = member.id
    await interaction.response.send_message(f"⚔️ تم تعيين {member.mention} نائباً للكلان.")

# 8. حذف الكلان
@bot.tree.command(name="clan-delete", description="حذف الكلان نهائياً")
async def delete(interaction: discord.Interaction):
    clan = next((n for n, d in clans.items() if d['owner'] == interaction.user.id), None)
    if clan:
        del clans[clan]
        await interaction.response.send_message(f"🗑️ تم حذف الكلان بنجاح.")
    else:
        await interaction.response.send_message("❌ لست صاحب كلان.", ephemeral=True)

# 9. مغادرة الكلان
@bot.tree.command(name="clan-leave", description="مغادرة كلانك الحالي")
async def leave(interaction: discord.Interaction):
    for n, d in clans.items():
        if interaction.user.id in d['members']:
            d['members'].remove(interaction.user.id)
            return await interaction.response.send_message(f"👋 غادرت كلان {n}.")
    await interaction.response.send_message("❌ أنت لست عضواً في أي كلان.", ephemeral=True)

# 10. الترتيب (Leaderboard)
@bot.tree.command(name="clan-leaderboard", description="ترتيب الكلانات حسب النقاط")
async def leaderboard(interaction: discord.Interaction):
    if not clans: return await interaction.response.send_message("❌ لا توجد بيانات.")
    sorted_clans = sorted(clans.items(), key=lambda x: x[1].get('points', 0), reverse=True)
    msg = "\n".join([f"🏆 **{n}** - {d['points']} نقطة" for n, d in sorted_clans[:10]])
    await interaction.response.send_message(f"📊 **ترتيب الكلانات:**\n{msg}")

# 11. إضافة نقاط
@bot.tree.command(name="clan-add-points", description="إضافة نقاط لكلان محدد")
async def add_points(interaction: discord.Interaction, name: str, points: int):
    if name not in clans: return await interaction.response.send_message("❌ الكلان غير موجود.")
    clans[name]['points'] = clans[name].get('points', 0) + points
    await interaction.response.send_message(f"➕ تم إضافة {points} نقطة لكلان {name}.")

# 12. خصم نقاط
@bot.tree.command(name="clan-remove-points", description="خصم نقاط من كلان محدد")
async def remove_points(interaction: discord.Interaction, name: str, points: int):
    if name not in clans: return await interaction.response.send_message("❌ الكلان غير موجود.")
    clans[name]['points'] = max(0, clans[name].get('points', 0) - points)
    await interaction.response.send_message(f"➖ تم خصم {points} نقطة من كلان {name}.")

bot.run(os.getenv('TOKEN'))
