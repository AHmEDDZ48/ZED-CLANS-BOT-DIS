import discord
from discord import app_commands
from discord.ext import commands, tasks
import os

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True 
        intents.guilds = True
        intents.voice_states = True # ضروري لمراقبة الصوت
        super().__init__(command_prefix='.', intents=intents)

    async def setup_hook(self):
        self.voice_points_task.start() # تشغيل عداد النقاط تلقائياً
        await self.tree.sync()
        print(f"✅ تم مزامنة الأوامر وتشغيل نظام النقاط التلقائي!")

bot = MyBot()
clans = {} 

# --- نظام حساب نقاط الفويس كل دقيقة ---
@tasks.loop(minutes=1.0)
async def voice_points_task():
    for guild in bot.guilds:
        for vc in guild.voice_channels:
            # فلترة الأعضاء (بدون بوتات)
            real_members = [m for m in vc.members if not m.bot]
            for member in real_members:
                # البحث عن كلان العضو (سواء كان قائد أو عضو أو نائب)
                for clan_name, data in clans.items():
                    if member.id == data['owner'] or member.id in data['members'] or member.id == data.get('coleader'):
                        clans[clan_name]['points'] += 1
                        break

# 1. إنشاء كلان (ينشئ رتبة وفويس خاص)
@bot.tree.command(name="clan-create", description="إنشاء كلان جديد (رتبة + فويس خاص)")
async def create(interaction: discord.Interaction, name: str):
    if any(d['owner'] == interaction.user.id for d in clans.values()):
        return await interaction.response.send_message("❌ أنت قائد كلان بالفعل!", ephemeral=True)
    
    await interaction.response.defer() # للانتظار حتى ينتهي إنشاء الرتب والقنوات

    # إنشاء الرتبة (Role)
    clan_role = await interaction.guild.create_role(name=f"Clan {name}", color=discord.Color.random(), mentionable=True)
    await interaction.user.add_roles(clan_role)

    # إنشاء فويس خاص (Voice Channel)
    overwrites = {
        interaction.guild.default_role: discord.PermissionOverwrite(connect=False),
        clan_role: discord.PermissionOverwrite(connect=True, view_channel=True)
    }
    voice_chan = await interaction.guild.create_voice_channel(name=f"🔊 | {name}", overwrites=overwrites)

    clans[name] = {
        'owner': interaction.user.id, 
        'members': [], 
        'points': 0, 
        'coleader': None,
        'role_id': clan_role.id,
        'voice_id': voice_chan.id
    }
    
    await interaction.followup.send(f"🎊 تم إنشاء كلان **{name}**!\n✅ مُنحت رتبة {clan_role.mention}\n✅ تم إنشاء فويس {voice_chan.mention}")

# 2. معلومات الكلان (للجميع)
@bot.tree.command(name="clan-info", description="عرض معلومات الكلان بالتفصيل")
async def info(interaction: discord.Interaction, name: str):
    if name not in clans:
        return await interaction.response.send_message("❌ الكلان غير موجود.", ephemeral=True)
    d = clans[name]
    embed = discord.Embed(title=f"🛡️ معلومات كلان {name}", color=discord.Color.blue())
    embed.add_field(name="القائد", value=f"<@{d['owner']}>")
    embed.add_field(name="النائب", value=f"<@{d['coleader']}>" if d.get('coleader') else "لا يوجد")
    embed.add_field(name="النقاط", value=f"`{d.get('points', 0):,}`")
    embed.add_field(name="الأعضاء", value=f"`{len(d['members']) + 1}`")
    await interaction.response.send_message(embed=embed)

# 3. قائمة الكلانات (للجميع)
@bot.tree.command(name="clan-list", description="عرض قائمة بكل الكلانات")
async def list_clans(interaction: discord.Interaction):
    if not clans: return await interaction.response.send_message("📭 لا توجد كلانات حالياً.")
    msg = "\n".join([f"🔹 **{n}** | النقاط: `{d.get('points', 0):,}`" for n, d in clans.items()])
    await interaction.response.send_message(f"📋 **قائمة الكلانات:**\n{msg}")

# 4. إضافة عضو (للقائد)
@bot.tree.command(name="clan-add-mem", description="إضافة عضو للكلان")
async def add_mem(interaction: discord.Interaction, member: discord.Member):
    clan = next((n for n, d in clans.items() if d['owner'] == interaction.user.id), None)
    if not clan: return await interaction.response.send_message("❌ يجب أن تكون القائد!", ephemeral=True)
    
    clans[clan]['members'].append(member.id)
    # إضافة رتبة الكلان للعضو الجديد
    role = interaction.guild.get_role(clans[clan]['role_id'])
    if role: await member.add_roles(role)
    
    await interaction.response.send_message(f"✅ تمت إضافة {member.mention} إلى الكلان.")

# 5. الترتيب الاحترافي (للجميع)
@bot.tree.command(name="clan-leaderboard", description="ترتيب الكلانات حسب نقاط الفويس")
async def leaderboard(interaction: discord.Interaction):
    if not clans: return await interaction.response.send_message("❌ لا توجد بيانات للترتيب.")
    
    sorted_clans = sorted(clans.items(), key=lambda x: x[1].get('points', 0), reverse=True)
    embed = discord.Embed(title="🏆 HYPE CLANS LEADERBOARD", color=discord.Color.gold())
    medals = {0: "🥇", 1: "🥈", 2: "🥉"}

    for index, (name, data) in enumerate(sorted_clans[:10]):
        emoji = medals.get(index, "🏅")
        details = (
            f"└─ **Leader:** <@{data['owner']}>\n"
            f"└─ **Points:** `{data.get('points', 0):,}` | **Members:** `{len(data['members']) + 1}`"
        )
        embed.add_field(name=f"{emoji} | {name.upper()}", value=details, inline=False)
    await interaction.response.send_message(embed=embed)

# 6. حذف الكلان (للقائد)
@bot.tree.command(name="clan-delete", description="حذف الكلان والرتبة والفويس نهائياً")
async def delete(interaction: discord.Interaction):
    clan = next((n for n, d in clans.items() if d['owner'] == interaction.user.id), None)
    if clan:
        # حذف الرول والفويس من السيرفر قبل حذف البيانات
        role = interaction.guild.get_role(clans[clan]['role_id'])
        vc = interaction.guild.get_channel(clans[clan]['voice_id'])
        if role: await role.delete()
        if vc: await vc.delete()
        
        del clans[clan]
        await interaction.response.send_message(f"🗑️ تم حذف الكلان وتوابعه بنجاح.")
    else:
        await interaction.response.send_message("❌ لا تملك كلان.", ephemeral=True)

# 7. إضافة نقاط (للإدارة فقط)
@bot.tree.command(name="clan-add-points", description="إضافة نقاط لكلان (للإدارة)")
@app_commands.checks.has_permissions(administrator=True)
async def add_points(interaction: discord.Interaction, name: str, points: int):
    if name not in clans: return await interaction.response.send_message("❌ الكلان غير موجود.")
    clans[name]['points'] += points
    await interaction.response.send_message(f"➕ تم إضافة {points} نقطة لكلان {name}.")

# 8. خصم نقاط (للإدارة فقط)
@bot.tree.command(name="clan-remove-points", description="خصم نقاط من كلان (للإدارة)")
@app_commands.checks.has_permissions(administrator=True)
async def remove_points(interaction: discord.Interaction, name: str, points: int):
    if name not in clans: return await interaction.response.send_message("❌ الكلان غير موجود.")
    clans[name]['points'] = max(0, clans[name]['points'] - points)
    await interaction.response.send_message(f"➖ تم خصم {points} نقطة من كلان {name}.")

# 9. تعيين نائب (للقائد)
@bot.tree.command(name="clan-s-coleader", description="تعيين نائب للقائد")
async def s_coleader(interaction: discord.Interaction, member: discord.Member):
    clan = next((n for n, d in clans.items() if d['owner'] == interaction.user.id), None)
    if not clan: return await interaction.response.send_message("❌ لست القائد!", ephemeral=True)
    clans[clan]['coleader'] = member.id
    await interaction.response.send_message(f"⚔️ تم تعيين {member.mention} نائباً.")

# 10. طرد عضو (للقائد)
@bot.tree.command(name="clan-remove-mem", description="طرد عضو من الكلان")
async def remove_mem(interaction: discord.Interaction, member: discord.Member):
    clan = next((n for n, d in clans.items() if d['owner'] == interaction.user.id), None)
    if not clan or member.id not in clans[clan]['members']:
        return await interaction.response.send_message("❌ لا تملك صلاحية.", ephemeral=True)
    clans[clan]['members'].remove(member.id)
    # سحب الرتبة
    role = interaction.guild.get_role(clans[clan]['role_id'])
    if role: await member.remove_roles(role)
    await interaction.response.send_message(f"👞 تم طرد {member.mention}.")

# 11. نقل ملكية (للقائد)
@bot.tree.command(name="clan-s-leader", description="نقل ملكية الكلان")
async def s_leader(interaction: discord.Interaction, member: discord.Member):
    clan = next((n for n, d in clans.items() if d['owner'] == interaction.user.id), None)
    if not clan: return await interaction.response.send_message("❌ لست القائد!", ephemeral=True)
    clans[clan]['owner'] = member.id
    await interaction.response.send_message(f"👑 انتقلت القيادة إلى {member.mention}.")

# 12. مغادرة (للأعضاء)
@bot.tree.command(name="clan-leave", description="مغادرة كلانك الحالي")
async def leave(interaction: discord.Interaction):
    for n, d in clans.items():
        if interaction.user.id in d['members']:
            d['members'].remove(interaction.user.id)
            role = interaction.guild.get_role(d['role_id'])
            if role: await interaction.user.remove_roles(role)
            return await interaction.response.send_message(f"👋 غادرت كلان {n}.")
    await interaction.response.send_message("❌ لست في كلان.", ephemeral=True)

bot.run(os.getenv('TOKEN'))
