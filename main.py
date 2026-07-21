import discord
from discord.ext import commands, tasks
import asyncio
import random
import os
import time
from keep_alive import keep_alive

# --- AYARLAR ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Veri depoları
hosgeldin_kanali = None
otorol_rolu = None
seviye_kanali = None
otorol_kanali = None
uyarilar = {}
user_xp = {}

# --- FOOTER YARDIMCI ---
def set_footer(embed, ctx):
    embed.set_footer(
        text=f"Flux Bot • {ctx.author.name} tarafından istendi",
        icon_url=bot.user.display_avatar.url
    )
    return embed

# --- DURUM DÖNGÜSÜ ---
durum_listesi = [
    ("!yardım | Flux Bot", discord.ActivityType.playing),
    ("sunucuları koruyorum ⚡", discord.ActivityType.watching),
    (f"komutlarını bekliyorum", discord.ActivityType.listening),
    ("Flux Bot v1.0", discord.ActivityType.playing),
]
durum_index = 0

@tasks.loop(seconds=10)
async def durum_degistir():
    global durum_index
    metin, tip = durum_listesi[durum_index]
    await bot.change_presence(activity=discord.Activity(type=tip, name=metin))
    durum_index = (durum_index + 1) % len(durum_listesi)

# --- BUTONLAR ---
class KapatView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Talebi Kapat", style=discord.ButtonStyle.red, custom_id="kapat_button")
    async def kapat_buton(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.delete()

class DestekView(discord.ui.View):
    def __init__(self, category_id=None, yetkili_rol_id=None):
        super().__init__(timeout=None)
        self.category_id = category_id
        self.yetkili_rol_id = yetkili_rol_id

    @discord.ui.button(label="🎫 Destek Aç", style=discord.ButtonStyle.green, custom_id="destek_button")
    async def destek_buton(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild

        mevcut = discord.utils.get(guild.text_channels, name=f"talep-{interaction.user.name}")
        if mevcut:
            await interaction.response.send_message(f"⚠️ Zaten açık bir talebin var: {mevcut.mention}", ephemeral=True)
            return

        category = guild.get_channel(self.category_id) if self.category_id else \
                   discord.utils.get(guild.categories, name="Destek Talepleri")
        yetkili_rol = guild.get_role(self.yetkili_rol_id) if self.yetkili_rol_id else None

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        if yetkili_rol:
            overwrites[yetkili_rol] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(
            name=f"talep-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )
        await interaction.response.send_message(f"✅ Destek talebin açıldı: {channel.mention}", ephemeral=True)
        mesaj = f"{interaction.user.mention}"
        if yetkili_rol:
            mesaj += f" ve {yetkili_rol.mention}"
        mesaj += ", destek başladı."
        await channel.send(mesaj, view=KapatView())

# --- MESAJ XP ---
@bot.event
async def on_member_join(member):
    if otorol_rolu:
        try:
            await member.add_roles(otorol_rolu)
        except discord.Forbidden:
            pass

    if otorol_kanali:
        embed = discord.Embed(
            title="👋 Hoş Geldin!",
            description=f"Merhaba {member.mention}! **{member.guild.name}** sunucusuna hoş geldin.",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Flux Bot • {member.guild.member_count}. üye")
        await otorol_kanali.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    uid = message.author.id
    if uid not in user_xp:
        user_xp[uid] = [0, 1]
    user_xp[uid][0] += random.randint(5, 10)
    if user_xp[uid][0] >= user_xp[uid][1] * 100:
        user_xp[uid][1] += 1
        user_xp[uid][0] = 0
        hedef = seviye_kanali if seviye_kanali else message.channel
        await hedef.send(f"🎉 Tebrikler {message.author.mention}, **{user_xp[uid][1]}. seviyeye** ulaştın!")
    await bot.process_commands(message)

# --- KOMUTLAR ---

@bot.command()
async def yardım(ctx):
    embed = discord.Embed(title="🤖 Flux Yardım Menüsü", color=discord.Color.blue())
    embed.add_field(name="🛡️ Moderasyon", value="`!sil <miktar>`, `!uyar @üye <sebep>`, `!at @üye <sebep>`", inline=False)
    embed.add_field(name="📢 Duyuru & Kanal", value="`!duyur #kanal <mesaj>`, `!kanaloluştur <isim>`, `!kanalkilitle`, `!kilitsiz`", inline=False)
    embed.add_field(name="🎭 Rol & Panel", value="`!rololuştur <isim>`, `!panel @rol`", inline=False)
    embed.add_field(name="⚙️ Sunucu Ayarları", value="`!otorolkanal #kanal`, `!otorolayarla @rol`, `!seviyekanali #kanal`", inline=False)
    embed.add_field(name="🎵 Müzik", value="`!gir`, `!çal <şarkı adı>`, `!dur`, `!cik`", inline=False)
    embed.add_field(name="🎮 Eğlence & Seviye", value="`!rank @üye`, `!yazıtura`, `!düello @üye`, `!söz`", inline=False)
    embed.add_field(name="ℹ️ Bilgi", value="`!ping`, `!avatar @üye`, `!kullanıcıbilgi @üye`, `!sunucubilgi`", inline=False)
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

# Moderasyon
@bot.command()
@commands.has_permissions(manage_messages=True)
async def sil(ctx, miktar: int):
    await ctx.channel.purge(limit=miktar + 1)
    embed = discord.Embed(description=f"✅ {miktar} adet mesaj silindi.", color=discord.Color.green())
    set_footer(embed, ctx)
    await ctx.send(embed=embed, delete_after=5)

@bot.command()
@commands.has_permissions(kick_members=True)
async def at(ctx, member: discord.Member, *, sebep="Belirtilmemiş"):
    await member.kick(reason=sebep)
    embed = discord.Embed(description=f"✅ {member.mention} sunucudan atıldı.\n**Sebep:** {sebep}", color=discord.Color.red())
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_roles=True)
async def uyar(ctx, member: discord.Member, *, sebep="Belirtilmemiş"):
    embed = discord.Embed(description=f"⚠️ {member.mention} uyarıldı!\n**Sebep:** {sebep}", color=discord.Color.yellow())
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

# Ayarlar
@bot.command()
@commands.has_permissions(administrator=True)
async def seviyekanali(ctx, kanal: discord.TextChannel):
    global seviye_kanali
    seviye_kanali = kanal
    embed = discord.Embed(description=f"✅ Seviye kanalı {kanal.mention} olarak ayarlandı.", color=discord.Color.green())
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def otorolkanal(ctx, kanal: discord.TextChannel):
    global otorol_kanali
    otorol_kanali = kanal
    embed = discord.Embed(description=f"✅ Otorol kanalı {kanal.mention} yapıldı.", color=discord.Color.green())
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(administrator=True)
async def otorolayarla(ctx, rol: discord.Role):
    global otorol_rolu
    otorol_rolu = rol
    embed = discord.Embed(description=f"✅ Otorol {rol.mention} olarak ayarlandı.", color=discord.Color.green())
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

# --- MÜZİK KOMUTLARI ---
@bot.command(name="gir")
async def ses_gir(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        embed = discord.Embed(description=f"🎤 **{channel.name}** kanalına katıldım!", color=discord.Color.green())
        set_footer(embed, ctx)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(description="❌ Önce bir ses kanalına girmelisin!", color=discord.Color.red())
        set_footer(embed, ctx)
        await ctx.send(embed=embed)

@bot.command(name="çal")
async def ses_cal(ctx, *, arama: str):
    if not ctx.author.voice:
        embed = discord.Embed(description="❌ Önce bir ses kanalına girmelisin!", color=discord.Color.red())
        set_footer(embed, ctx)
        await ctx.send(embed=embed)
        return

    channel = ctx.author.voice.channel
    if ctx.voice_client is None:
        await channel.connect()
    elif ctx.voice_client.channel != channel:
        await ctx.voice_client.move_to(channel)

    embed = discord.Embed(description=f"🎶 **{arama}** aranıyor ve çalınıyor...", color=discord.Color.blue())
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

    YDL_OPTIONS = {
        'format': 'bestaudio',
        'noplaylist': 'True',
        'default_search': 'scsearch',
        'source_address': '0.0.0.0',
        'geo_bypass': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['mweb', 'android']
            }
        }
    }
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

    import yt_dlp
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            info = ydl.extract_info(f"scsearch:{arama}", download=False)
            if 'entries' in info:
                info = info['entries'][0]
            url = info['url']
            title = info.get('title', 'Bilinmeyen Şarkı')
            
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()

            ctx.voice_client.play(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS))
            
            success_embed = discord.Embed(description=f"▶️ Şimdi Çalınıyor: **{title}**", color=discord.Color.green())
            set_footer(success_embed, ctx)
            await ctx.send(embed=success_embed)
        except Exception as e:
            err_embed = discord.Embed(description=f"❌ Şarkı oynatılırken bir hata oluştu: {e}", color=discord.Color.red())
            set_footer(err_embed, ctx)
            await ctx.send(embed=err_embed)

@bot.command(name="dur")
async def ses_dur(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        embed = discord.Embed(description="⏸️ Müzik duraklatıldı.", color=discord.Color.yellow())
        set_footer(embed, ctx)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(description="❌ Şu an çalan bir müzik yok.", color=discord.Color.red())
        set_footer(embed, ctx)
        await ctx.send(embed=embed)

@bot.command(name="cik")
async def ses_cik(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        embed = discord.Embed(description="👋 Ses kanalından ayrıldım.", color=discord.Color.red())
        set_footer(embed, ctx)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(description="❌ Zaten bir ses kanalında değilim!", color=discord.Color.red())
        set_footer(embed, ctx)
        await ctx.send(embed=embed)

# Bilgi
@bot.command()
async def ping(ctx):
    embed = discord.Embed(description=f"🏓 Pong! **{round(bot.latency * 1000)}ms**", color=discord.Color.blue())
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

@bot.command()
async def sunucubilgi(ctx):
    embed = discord.Embed(title=f"🏠 {ctx.guild.name}", color=discord.Color.blue())
    embed.add_field(name="Üye Sayısı", value=ctx.guild.member_count)
    embed.add_field(name="Kuruluş", value=ctx.guild.created_at.strftime('%d.%m.%Y'))
    if ctx.guild.icon:
        embed.set_thumbnail(url=ctx.guild.icon.url)
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

@bot.command()
async def kullanıcıbilgi(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"👤 {member.name}", color=discord.Color.blue())
    embed.add_field(name="Katılım Tarihi", value=member.joined_at.strftime('%d.%m.%Y'))
    embed.add_field(name="Hesap Oluşturma", value=member.created_at.strftime('%d.%m.%Y'))
    embed.set_thumbnail(url=member.display_avatar.url)
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

# Eğlence
@bot.command()
async def rank(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = user_xp.get(member.id, [0, 1])
    embed = discord.Embed(title=f"📊 {member.name} Seviye Bilgisi", color=discord.Color.purple())
    embed.add_field(name="Seviye", value=data[1])
    embed.add_field(name="XP", value=f"{data[0]} / {data[1] * 100}")
    embed.set_thumbnail(url=member.display_avatar.url)
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

@bot.command()
async def yazıtura(ctx):
    sonuc = random.choice(['Yazı', 'Tura'])
    embed = discord.Embed(description=f"🪙 Sonuç: **{sonuc}**", color=discord.Color.gold())
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

@bot.command()
async def düello(ctx, üye: discord.Member):
    kazanan = random.choice([ctx.author, üye])
    embed = discord.Embed(description=f"⚔️ **{ctx.author.name}** vs **{üye.name}**\n\n🏆 Kazanan: **{kazanan.name}**!", color=discord.Color.red())
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

@bot.command()
async def söz(ctx):
    sozler = [
        "Başarı, pes etmeyenlerindir.",
        "Flux seninle!",
        "Yeni bir gün, yeni bir seviye.",
        "Güçlü ol, Flux yanında.",
        "Her engel, daha büyük bir başarının habercisidir."
    ]
    embed = discord.Embed(description=f"✨ *{random.choice(sozler)}*", color=discord.Color.blurple())
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

# --- DİĞER KOMUTLAR ---

@bot.command()
@commands.has_permissions(administrator=True)
async def duyur(ctx, kanal: discord.TextChannel, *, mesaj: str):
    embed = discord.Embed(
        title="📢 Duyuru",
        description=mesaj,
        color=discord.Color.orange()
    )
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.display_avatar.url)
    set_footer(embed, ctx)
    await kanal.send(embed=embed)
    onay = discord.Embed(description=f"✅ Duyuru {kanal.mention} kanalına gönderildi.", color=discord.Color.green())
    set_footer(onay, ctx)
    await ctx.send(embed=onay, delete_after=5)

@bot.command()
async def avatar(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"🖼️ {member.name} Avatarı", color=discord.Color.blurple())
    embed.set_image(url=member.display_avatar.url)
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def kanaloluştur(ctx, *, isim: str):
    kanal = await ctx.guild.create_text_channel(name=isim)
    embed = discord.Embed(description=f"✅ {kanal.mention} kanalı oluşturuldu.", color=discord.Color.green())
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def kanalkilitle(ctx, kanal: discord.TextChannel = None):
    kanal = kanal or ctx.channel
    await kanal.set_permissions(ctx.guild.default_role, send_messages=False)
    embed = discord.Embed(description=f"🔒 {kanal.mention} kanalı kilitlendi.", color=discord.Color.red())
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_channels=True)
async def kilitsiz(ctx, kanal: discord.TextChannel = None):
    kanal = kanal or ctx.channel
    await kanal.set_permissions(ctx.guild.default_role, send_messages=True)
    embed = discord.Embed(description=f"🔓 {kanal.mention} kanalının kilidi açıldı.", color=discord.Color.green())
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_roles=True)
async def rololuştur(ctx, *, isim: str):
    rol = await ctx.guild.create_role(name=isim)
    embed = discord.Embed(description=f"✅ **{rol.name}** rolü oluşturuldu.", color=discord.Color.green())
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

# Panel
@bot.command()
@commands.has_permissions(administrator=True)
async def panel(ctx, rol: discord.Role):
    category = discord.utils.get(ctx.guild.categories, name="Destek Talepleri")
    if not category:
        category = await ctx.guild.create_category("Destek Talepleri")

    view = DestekView(category_id=category.id, yetkili_rol_id=rol.id)
    embed = discord.Embed(title="🎫 Destek Merkezi", description="Aşağıdaki butona tıklayarak destek talebi açabilirsin.", color=discord.Color.blue())
    set_footer(embed, ctx)
    await ctx.send(embed=embed, view=view)

# --- BAŞLANGIÇ ---
@bot.event
async def on_ready():
    bot.add_view(DestekView())
    bot.add_view(KapatView())
    durum_degistir.start()
    print(f'{bot.user} başlatıldı!')

keep_alive()
time.sleep(2)
bot.run(os.environ['DISCORD_TOKEN'])
    
