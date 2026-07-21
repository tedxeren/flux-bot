import discord
from discord.ext import commands, tasks
import asyncio
import random
import os
import time
from keep_alive import keep_alive
from datetime import datetime, timedelta
from keep_alive import keep_alive


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

hosgeldin_kanali = None
otorol_rolu = None
seviye_kanali = None
otorol_kanali = None
uyarilar = {}
user_xp = {}
user_para = {}
user_pet = {}
gunluk_cooldowns = {}
user_envanter = {} # Kullanıcıların envanterlerini tutar (Örn: {user_id: {"Mama": 2, "VIP Kart": 1}})

# Mağazada satılacak eşyalar (İsim: [Fiyat, Açıklama])
magaza_esyalari = {
    "mama": [50, "Petinin açlığını giderir ve seviye atlatır."],
    "olta": [250, "Balık tutarak ekstra coin kazanmanı sağlar."],
    "vip": [1000, "Sunucuda havalı bir rozet kazandırır."]
}



def set_footer(embed, ctx):
    embed.set_footer(
        text=f"Flux Bot • {ctx.author.name} tarafından istendi",
        icon_url=bot.user.display_avatar.url
    )
    return embed

durum_listesi = [
    ("!yardım | Flux Bot", discord.ActivityType.playing),
    ("sunucuları koruyorum ⚡", discord.ActivityType.watching),
    ("komutlarını bekliyorum", discord.ActivityType.listening),
    ("Flux Bot v1.0", discord.ActivityType.playing),
]
durum_index = 0

@tasks.loop(seconds=10)
async def durum_degistir():
    global durum_index
    metin, tip = durum_listesi[durum_index]
    await bot.change_presence(activity=discord.Activity(type=tip, name=metin))
    durum_index = (durum_index + 1) % len(durum_listesi)

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

        category = guild.get_channel(self.category_id) if self.category_id else discord.utils.get(guild.categories, name="Destek Talepleri")
        yetkili_rol = guild.get_role(self.yetkili_rol_id) if self.yetkili_rol_id else None

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        }
        if yetkili_rol:
            overwrites[yetkili_rol] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(name=f"talep-{interaction.user.name}", category=category, overwrites=overwrites)
        await interaction.response.send_message(f"✅ Destek talebin açıldı: {channel.mention}", ephemeral=True)
        mesaj = f"{interaction.user.mention}"
        if yetkili_rol:
            mesaj += f" ve {yetkili_rol.mention}"
        mesaj += ", destek başladı."
        await channel.send(mesaj, view=KapatView())

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

@bot.command()
async def yardım(ctx):
    embed = discord.Embed(title="🤖 Flux Yardım Menüsü", color=discord.Color.blue())
    embed.add_field(name="🛡️ Moderasyon", value="`!sil <miktar>`, `!uyar @üye <sebep>`, `!at @üye <sebep>`", inline=False)
    embed.add_field(name="📢 Duyuru & Kanal", value="`!duyur #kanal <mesaj>`, `!kanaloluştur <isim>`, `!kanalkilitle`, `!kilitsiz`", inline=False)
    embed.add_field(name="🎭 Rol & Panel", value="`!rololuştur <isim>`, `!panel @rol`", inline=False)
    embed.add_field(name="⚙️ Sunucu Ayarları", value="`!otorolkanal #kanal`, `!otorolayarla @rol`, `!seviyekanali #kanal`", inline=False)
    embed.add_field(name="🎵 Müzik", value="`!gir`, `!çal <şarkı adı>`, `!dur`, `!cik`", inline=False)
    embed.add_field(name="💰 Ekonomi & Banka", value="`!bakiye`, `!günlük`, `!çalış`, `!yatır`, `!çek`, `!gönder`, `!zenginler`", inline=False)
    embed.add_field(name="🛒 Mağaza & Envanter", value="`!magaza`, `!satınal <eşya>`, `!envanter`, `!balıktut`", inline=False)
    embed.add_field(name="🐾 Pet Sistemi", value="`!pet`, `!petismi <isim>`, `!petbesle`", inline=False)
    embed.add_field(name="🎮 Eğlence & Şans", value="`!rank`, `!topxp`, `!rulet <miktar> <renk>`, `!kazıkazan`, `!yazıtura`, `!söz`", inline=False)
    set_footer(embed, ctx)
    await ctx.send(embed=embed)


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

@bot.command(name="bakiye", aliases=["cüzdan", "para"])
async def bakiye(ctx, member: discord.Member = None):
    member = member or ctx.author
    if member.id not in user_para:
        user_para[member.id] = [100, 0]
    cüzdan, banka = user_para[member.id]
    embed = discord.Embed(title=f"💰 {member.name} - Bakiye Bilgisi", color=discord.Color.gold())
    embed.add_field(name="Cüzdan", value=f"💵 {cüzdan} Coin", inline=True)
    embed.add_field(name="Banka", value=f"🏦 {banka} Coin", inline=True)
    embed.add_field(name="Toplam", value=f"💎 {cüzdan + banka} Coin", inline=False)
    set_footer(embed, ctx)
    await ctx.send(embed=embed)
    
@bot.command(name="günlük", aliases=["daily"])
@commands.cooldown(1, 86400, commands.BucketType.user)
async def günlük(ctx):
    uid = ctx.author.id
    if uid not in user_para:
        user_para[uid] = [100, 0]
        
    odul = random.randint(250, 500)
    user_para[uid][0] += odul
    
    embed = discord.Embed(description=f"🎁 Günlük ödülünü aldın! Cüzdanına **{odul} Coin** eklendi.", color=discord.Color.green())
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

@günlük.error
async def günlük_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        # Kalan süreyi saat ve dakikaya çevir
        toplam_saniye = int(error.retry_after)
        saat = toplam_saniye // 3600
        dakika = (toplam_saniye % 3600) // 60
        
        embed = discord.Embed(description=f"⏳ Günlük ödülünü zaten almışsın!\nTekrar alabilmek için **{saat} saat {dakika} dakika** beklemelisin.", color=discord.Color.red())
        set_footer(embed, ctx)
        await ctx.send(embed=embed, delete_after=10)



@bot.command(name="çalış", aliases=["work"])
async def çalış(ctx):
    uid = ctx.author.id
    if uid not in user_para:
        user_para[uid] = [100, 0]
    meslekler = [
        ("Discord Botu kodladın ve telif aldın", 150),
        ("Beşiktaş stadyumunda çim biçtin", 80),
        ("Yazılım şirketinde bug çözdün", 200),
        ("Kafede garsonluk yaptın", 100)
    ]
    is_adi, kazanc = random.choice(meslekler)
    user_para[uid][0] += kazanc
    embed = discord.Embed(description=f"💼 {is_adi} ve karşılığında **{kazanc} Coin** kazandın!", color=discord.Color.blue())
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

@bot.command(name="yatır")
async def yatir(ctx, miktar: str):
    uid = ctx.author.id
    if uid not in user_para:
        user_para[uid] = [100, 0]
    cüzdan = user_para[uid][0]
    tutar = cüzdan if miktar.lower() == "hepsi" else int(miktar)
    if tutar <= 0 or tutar > cüzdan:
        await ctx.send("❌ Geçersiz miktar veya yetersiz cüzdan!")
        return
    user_para[uid][0] -= tutar
    user_para[uid][1] += tutar
    embed = discord.Embed(description=f"🏦 Başarıyla **{tutar} Coin** bankaya yatırıldı.", color=discord.Color.green())
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

@bot.command(name="çek")
async def cek(ctx, miktar: str):
    uid = ctx.author.id
    if uid not in user_para:
        user_para[uid] = [100, 0]
    banka = user_para[uid][1]
    tutar = banka if miktar.lower() == "hepsi" else int(miktar)
    if tutar <= 0 or tutar > banka:
        await ctx.send("❌ Geçersiz miktar veya yetersiz banka!")
        return
    user_para[uid][1] -= tutar
    user_para[uid][0] += tutar
    embed = discord.Embed(description=f"💵 Başarıyla **{tutar} Coin** çekildi.", color=discord.Color.green())
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

@bot.command(name="gönder", aliases=["transfer"])
async def gonder(ctx, member: discord.Member, miktar: int):
    uid = ctx.author.id
    if uid not in user_para or user_para[uid][0] < miktar or miktar <= 0:
        await ctx.send("❌ Yetersiz bakiye veya geçersiz miktar!")
        return
    if member.id not in user_para:
        user_para[member.id] = [100, 0]
    user_para[uid][0] -= miktar
    user_para[member.id][0] += miktar
    embed = discord.Embed(description=f"💸 {member.mention} kullanıcısına **{miktar} Coin** gönderildi.", color=discord.Color.green())
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

@bot.command(name="zenginler", aliases=["top", "leaderboard"])
async def zenginler(ctx):
    if not user_para:
        await ctx.send("❌ Kayıt yok!")
        return
    sirali_liste = sorted(user_para.items(), key=lambda x: x[1][0] + x[1][1], reverse=True)[:10]
    embed = discord.Embed(title="🏆 Zenginler Listesi", color=discord.Color.gold())
    aciklama = ""
    for sira, (uid, para) in enumerate(sirali_liste, 1):
        member = ctx.guild.get_member(uid)
        isim = member.name if member else f"Kullanıcı"
        toplam = para[0] + para[1]
        aciklama += f"`#{sira}` **{isim}** — 💎 {toplam} Coin\n"
    embed.description = aciklama
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

@bot.command(name="pet")
async def pet(ctx):
    uid = ctx.author.id
    if uid not in user_pet:
        user_pet[uid] = ["Minik Kartal", 1, 50]
    p_isim, p_sev, p_aclik = user_pet[uid]
    embed = discord.Embed(title=f"🐾 {ctx.author.name} - Pet", color=discord.Color.purple())
    embed.add_field(name="İsim", value=p_isim)
    embed.add_field(name="Seviye", value=str(p_sev))
    embed.add_field(name="Açlık", value=f"%{p_aclik}")
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

@bot.command(name="petbesle")
async def petbesle(ctx):
    uid = ctx.author.id
    if uid not in user_pet:
        user_pet[uid] = ["Minik Kartal", 1, 50]
        
    # Envanterinde mama var mı kontrol et
    if uid not in user_envanter or user_envanter[uid].get("mama", 0) <= 0:
        await ctx.send("❌ Petini beslemek için envanterinde **Mama** yok! `!magaza` üzerinden mama satın almalısın.")
        return
        
    # Mamayı 1 adet düş
    user_envanter[uid]["mama"] -= 1
    
    # Peti güçlendir
    user_pet[uid][1] += 1
    user_pet[uid][2] = min(100, user_pet[uid][2] + 25)
    
    embed = discord.Embed(description=f"🍖 Mamayı yedirdin, petin seviye atladı ve çok mutlu! (Kalan Mama: {user_envanter[uid]['mama']})", color=discord.Color.green())
    set_footer(embed, ctx)
    await ctx.send(embed=embed)


@bot.command(name="rulet")
async def rulet(ctx, miktar: int, renk: str):
    uid = ctx.author.id
    if uid not in user_para or user_para[uid][0] < miktar or miktar <= 0:
        await ctx.send("❌ Yetersiz bakiye!")
        return
    renk = renk.lower()
    kazanan = random.choice(["kırmızı", "siyah", "yeşil"])
    carpan = 14 if kazanan == "yeşil" else 2
    if renk == kazanan:
        user_para[uid][0] += miktar * carpan
        embed = discord.Embed(description=f"🎡 Kazandın! +{miktar * carpan} Coin", color=discord.Color.green())
    else:
        user_para[uid][0] -= miktar
        embed = discord.Embed(description=f"🎡 Kaybettin! -{miktar} Coin", color=discord.Color.red())
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

@bot.command(name="kazıkazan", aliases=["kazikazan"])
async def kazikazan(ctx):
    uid = ctx.author.id
    if uid not in user_para or user_para[uid][0] < 30:
        await ctx.send("❌ 30 Coin lazım!")
        return
    user_para[uid][0] -= 30
    semboller = ["💎", "💰", "🍒", "⭐"]
    cekilis = [random.choice(semboller) for _ in range(3)]
    if cekilis[0] == cekilis[1] == cekilis[2]:
        user_para[uid][0] += 300
        embed = discord.Embed(description=f"🎉 {' '.join(cekilis)} - Üçlü! +300 Coin", color=discord.Color.gold())
    else:
        user_para[uid][0] += 40
        embed = discord.Embed(description=f"✨ {' '.join(cekilis)} - Teselli! +40 Coin", color=discord.Color.green())
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

@bot.command(name="gir")
async def ses_gir(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
        await ctx.send("🎤 Ses kanalına katıldım!")

@bot.command(name="çal")
async def ses_cal(ctx, *, arama: str):
    if not ctx.author.voice:
        await ctx.send("❌ Önce ses kanalına gir!")
        return
    channel = ctx.author.voice.channel
    if not ctx.voice_client:
        await channel.connect()
    YDL_OPTIONS = {'format': 'bestaudio', 'default_search': 'scsearch', 'noplaylist': True}
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1', 'options': '-vn'}
    import yt_dlp
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            info = ydl.extract_info(arama, download=False)
            if 'entries' in info: info = info['entries'][0]
            url = info['url']
            if ctx.voice_client.is_playing(): ctx.voice_client.stop()
            ctx.voice_client.play(discord.FFmpegPCMAudio(url, **FFMPEG_OPTIONS))
            await ctx.send(f"▶️ Çalınıyor: {info.get('title')}")
        except Exception as e:
            await ctx.send(f"❌ Hata: {e}")

@bot.command(name="dur")
async def ses_dur(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Duraklatıldı.")

@bot.command(name="cik")
async def ses_cik(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Ayrıldım.")

@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! {round(bot.latency * 1000)}ms")

@bot.command()
async def rank(ctx, member: discord.Member = None):
    member = member or ctx.author
    data = user_xp.get(member.id, [0, 1])
    await ctx.send(f"📊 Seviye: {data[1]} | XP: {data[0]}/{data[1]*100}")

@bot.command(name="topxp")
async def topxp(ctx):
    if not user_xp:
        await ctx.send("❌ Kayıt yok!")
        return
    sirali = sorted(user_xp.items(), key=lambda x: (x[1][1], x[1][0]), reverse=True)[:10]
    aciklama = "".join([f"`#{i}` <@{uid}> — Seviye: {d[1]}\n" for i, (uid, d) in enumerate(sirali, 1)])
    await ctx.send(embed=discord.Embed(title="🏆 Seviye Sıralaması", description=aciklama, color=discord.Color.purple()))

@bot.command()
async def yazıtura(ctx):
    await ctx.send(f"🪙 Sonuç: {random.choice(['Yazı', 'Tura'])}")

@bot.command()
async def söz(ctx):
    await ctx.send(f"✨ *{random.choice(['Başarı pes etmeyenlerindir.', 'Flux seninle!', 'Güçlü ol!'])}*")

@bot.command(name="balıktut", aliases=["balık", "fish", "baliktut"])
@commands.cooldown(1, 20, commands.BucketType.user)
async def baliktut(ctx):
    uid = ctx.author.id
    
    # Envanterde olta var mı kontrol et
    if uid not in user_envanter or user_envanter[uid].get("olta", 0) <= 0:
        await ctx.send("❌ Balık tutabilmek için önce mağazadan **Olta** satın almalısın! (`!magaza`)")
        return
        
    if uid not in user_para:
        user_para[uid] = [100, 0]
        
    # (Balık Adı, Kazanç, Çıkma Ağırlığı/Şansı)
    baliklar = [
        ("Çöp / Eski Bot", 0, 30),
        ("Küçük İstavrit", 25, 25),
        ("Sazangiller", 50, 20),
        ("Somon Balığı", 100, 12),
        ("Dev Levrek", 200, 7),
        ("Kılıç Balığı", 400, 3),
        ("Nadir Altın Balık", 750, 2),
        ("Efsanevi Mavi Balina", 1500, 1)
    ]
    
    # random.choices ile ağırlıklı (şanslı) seçim yapma
    secilen = random.choices(baliklar, weights=[b[2] for b in baliklar], k=1)[0]
    balik_adi, kazanc, _ = secilen
    
    user_para[uid][0] += kazanc
    
    if kazanc > 0:
        embed = discord.Embed(description=f"🎣 Denize oltanı attın ve bir **{balik_adi}** yakaladın! Satarak **{kazanc} Coin** kazandın.", color=discord.Color.blue())
    else:
        embed = discord.Embed(description=f"🎣 Oltanı attın ama denizden sadece **{balik_adi}** çıktığı için para kazanamadın.", color=discord.Color.red())
        
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

@baliktut.error
async def baliktut_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        kalan = round(error.retry_after, 1)
        embed = discord.Embed(description=f"⏳ Oltanı yeniden atmak için **{kalan} saniye** beklemelisin!", color=discord.Color.red())
        set_footer(embed, ctx)
        await ctx.send(embed=embed, delete_after=5)


@bot.command(name="satınal", aliases=["satyal", "buy"])
async def satınal(ctx, esya_adi: str):
    uid = ctx.author.id
    esya_adi = esya_adi.lower()
    
    if esya_adi not in magaza_esyalari:
        await ctx.send("❌ Mağazada böyle bir eşya yok! `!magaza` yazarak listeye bakabilirsin.")
        return
        
    fiyat = magaza_esyalari[esya_adi][0]
    
    if uid not in user_para or user_para[uid][0] < fiyat:
        await ctx.send(f"❌ Yeterli cüzdan bakiyen yok! Bu eşya **{fiyat} Coin**.")
        return
        
    # Parayı düş
    user_para[uid][0] -= fiyat
    
    # Envantere ekle
    if uid not in user_envanter:
        user_envanter[uid] = {}
    if esya_adi not in user_envanter[uid]:
        user_envanter[uid][esya_adi] = 0
        
    user_envanter[uid][esya_adi] += 1
    
    embed = discord.Embed(description=f"✅ Başarıyla **{esya_adi.capitalize()}** satın aldın! Envanterine eklendi.", color=discord.Color.green())
    set_footer(embed, ctx)
    await ctx.send(embed=embed)
    

@bot.command(name="envanter", aliases=["env", "inventory"])
async def envanter(ctx, member: discord.Member = None):
    member = member or ctx.author
    uid = member.id
    
    embed = discord.Embed(title=f"🎒 {member.name} - Envanter", color=discord.Color.purple())
    
    if uid not in user_envanter or not user_envanter[uid]:
        embed.description = "Envanterin bomboş! Mağazadan bir şeyler alabilirsin (`!magaza`)."
    else:
        aciklama = ""
        for esya, adet in user_envanter[uid].items():
            if adet > 0:
                aciklama += f"• **{esya.capitalize()}**: {adet} adet\n"
        embed.description = aciklama if aciklama else "Envanterin bomboş!"
        
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

@bot.command(name="mağaza", aliases=["magaza", "shop"])
async def magaza(ctx):
    embed = discord.Embed(title="🛒 Flux Mağaza", description="Satın almak için `!satınal <eşya_adı>` yazabilirsin.", color=discord.Color.blue())
    for esya, bilgi in magaza_esyalari.items():
        embed.add_field(name=f"{esya.capitalize()} — 💵 {bilgi[0]} Coin", value=bilgi[1], inline=False)
    set_footer(embed, ctx)
    await ctx.send(embed=embed)

@bot.command(name="petismi", aliases=["pet-isim"])
async def petismi(ctx, *, yeni_isim: str):
    uid = ctx.author.id
    if uid not in user_pet:
        user_pet[uid] = ["Minik Kartal", 1, 50]
    
    # İsmi güncelle (Sadece ilk eleman isim)
    user_pet[uid][0] = yeni_isim
    
    embed = discord.Embed(description=f"🐾 Petinin ismi başarıyla **{yeni_isim}** olarak değiştirildi!", color=discord.Color.green())
    set_footer(embed, ctx)
    await ctx.send(embed=embed)
    
    
    

@bot.event
async def on_ready():
    bot.add_view(DestekView())
    bot.add_view(KapatView())
    durum_degistir.start()
    print(f'{bot.user} başlatıldı!')

keep_alive()
time.sleep(2)
bot.run(os.environ['DISCORD_TOKEN'])
                       
