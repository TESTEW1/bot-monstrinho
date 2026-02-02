import discord
from discord.ext import commands
import random
import asyncio
import os
from datetime import timedelta

# ================= INTENTS =================
# ============== BOT SETUP =================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= CONFIG =================

TOKEN = os.getenv("TOKEN")
DONO_ID = 769951556388257812

CANAL_GERAL = "💭・chat-geral"
CANAL_LIBERACAO = "✅・chat-staff-liberação"
CANAL_LOG = "❌・palavras-apagadas-bot"
CANAL_TICKET = "🎟️・𝑻𝒊𝒄𝒌𝒆𝒕"
CANAL_EVENTO_CATALOGO = "evento-catalogo"
CANAL_ADVERTENCIAS = "⚠️・advertências" 

# GIFs
BANNER_TICKET = "https://i.pinimg.com/originals/5d/92/5d/5d925dd101dba34f341148eace3cfe38.gif"
GIF_NAMORADOS = "https://i.pinimg.com/originals/f5/b8/44/f5b844675a7942e4180bb9960c3fe319.gif"
GIF_CATALOGO = "https://i.pinimg.com/originals/0a/1f/86/0a1f869c296b0c30454ffb56397b90fb.gif"

# Cargos
CARGO_MEMBRO_NOVO = "Membro Novo. 🦇"
CARGO_MEMBROS = "Membros. 🦇"
CARGO_MODERADOR = "Moderador. 🦇"
CARGO_RECRUTADOR = "Recrutador. 🦇"
CARGO_ANJO = "Anjo. 🦇"

# --- ADICIONADO: CARGOS IMUNES ---
CARGOS_IMUNES = ["Admin. 🦇", "Moderador. 🦇", "DIRETOR. 🦇"]

# ============== DADOS =================

tickets = {}
avisos_usuarios = {} 

# ============== PALAVRAS PROIBIDAS (RESTAURADAS) =================

PALAVRAS_PROIBIDAS = [
    "porra", "caralho", "merda", "bosta", "puta", "puto", "vadia", "desgraça", 
    "idiota", "burro", "imbecil", "otário", "retardado", "lixo", "nojento", 
    "arrombado", "viado", "bicha", "piranha", "vai se fuder", "vai se foder", 
    "vai tomar no cu", "tomar no cu", "filho da puta", "se mata", "se fode", 
    "fdp", "vsf", "krl", "pqp", "prr", "tmnc", "buceta", "carai", "karalho"
]

# ============== VIEW DE LIBERAÇÃO DE ADVERTÊNCIA =================

class LiberarCastigoView(discord.ui.View):
    def __init__(self, membro_id: int):
        super().__init__(timeout=None)
        self.membro_id = membro_id

    @discord.ui.button(label="🔓 Remover Castigo", style=discord.ButtonStyle.success, custom_id="remover_castigo")
    async def remover(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.moderate_members:
            return await interaction.response.send_message("❌ Apenas a staff pode remover castigos!", ephemeral=True)
        
        guild = interaction.guild
        membro = guild.get_member(self.membro_id)
        
        if membro:
            await membro.timeout(None)
            avisos_usuarios[self.membro_id] = 0 
            await interaction.response.send_message(f"✅ Castigo de {membro.mention} removido com sucesso!", ephemeral=True)
            
            canal_geral = discord.utils.get(guild.text_channels, name=CANAL_GERAL)
            if canal_geral:
                await canal_geral.send(f"⚠️ **{membro.mention} foi liberado pela staff, mas continue se comportando! 🐲💚**")
        else:
            await interaction.response.send_message("❌ Membro não encontrado no servidor.", ephemeral=True)

# ============== VIEW DE APROVAÇÃO =================

class AprovarMembroView(discord.ui.View):
    def __init__(self, membro_id: int):
        super().__init__(timeout=None)
        self.membro_id = membro_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ Só a staff pode usar 😤🐲", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="✅ Liberar", style=discord.ButtonStyle.success, custom_id="liberar_membro")
    async def liberar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        membro = guild.get_member(self.membro_id)

        if not membro:
            await interaction.followup.send("❌ Membro não encontrado.", ephemeral=True)
            return

        cargos = [
            discord.utils.get(guild.roles, name=CARGO_MEMBRO_NOVO),
            discord.utils.get(guild.roles, name=CARGO_MEMBROS),
        ]

        for c in cargos:
            if c:
                await membro.add_roles(c)

        try:
            await membro.send("AAAA 😭🐲💚 Você foi APROVADO! Bem-vindo à famíliaaa!!! 💚✨")
        except:
            pass

        canal_geral = discord.utils.get(guild.text_channels, name=CANAL_GERAL)
        cargo_anjo = discord.utils.get(guild.roles, name=CARGO_ANJO)
        cargo_recrutador = discord.utils.get(guild.roles, name=CARGO_RECRUTADOR)

        mencoes = []
        if cargo_anjo:
            mencoes.append(cargo_anjo.mention)
        if cargo_recrutador:
            mencoes.append(cargo_recrutador.mention)

        if canal_geral:
            await canal_geral.send(
                f"AAAA 😭🐲💚 {membro.mention} foi LIBERADO!\n"
                f"{' '.join(mencoes)} venham dar boas-vindas pro neném do monstrinhooo 🐲💚✨"
            )

        await interaction.followup.send("✅ Liberado com sucesso!", ephemeral=True)

    @discord.ui.button(label="⏳ Aguardar", style=discord.ButtonStyle.secondary, custom_id="aguardar_membro")
    async def aguardar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🕒 Em análise 💚🐲", ephemeral=True)

        guild = interaction.guild
        membro = guild.get_member(self.membro_id)
        if membro:
            try:
                await membro.send("Oii neném 😭🐲💚 sua entrada tá sendo analisada pela staff, segura firme que já já te chamam, tá bom? 💚✨")
            except:
                pass

    @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.danger, custom_id="recusar_membro")
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("❌ Recusado.", ephemeral=True)
        guild = interaction.guild
        membro = guild.get_member(self.membro_id)
        if membro:
            try:
                await membro.kick(reason="Pedido de entrada recusado pela staff.")
            except:
                pass

# ============== TICKET =================

class FecharTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Fechar Ticket", style=discord.ButtonStyle.danger, custom_id="fechar_ticket")
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Fechando em 5s...", ephemeral=True)
        await asyncio.sleep(5)
        await interaction.channel.delete()

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🛠️ Suporte", value="suporte"),
            discord.SelectOption(label="🚨 Denúncia", value="denuncia"),
            discord.SelectOption(label="👮 Falar com Staff", value="staff"),
            discord.SelectOption(label="💘 Evento dos Namorados", value="namorados"),
            discord.SelectOption(label="📸 Evento Catálogo", value="catalogo"),
            discord.SelectOption(label="📣 Líder de Torcida", value="lider_torcida"),
        ]
        super().__init__(
            placeholder="🎟️ Selecione o tipo de ticket",
            options=options,
            custom_id="ticket_select_menu"
        )

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        tipo = self.values[0]
        cargo_mod = discord.utils.get(guild.roles, name=CARGO_MODERADOR)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }
        if cargo_mod:
            overwrites[cargo_mod] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        categoria = interaction.channel.category
        canal = await guild.create_text_channel(
            name=f"🎟️┃{tipo}-{user.name}".lower(),
            category=categoria,
            overwrites=overwrites
        )

        tickets[canal.id] = {"user": user.id, "tipo": tipo}

        if tipo == "namorados":
            await canal.send(f"💘 **EVENTO DOS NAMORADOS**\n\n{user.mention}")
            await canal.send(GIF_NAMORADOS)
        elif tipo == "catalogo":
            await canal.send(f"📸 **EVENTO CATÁLOGO**\n\n{user.mention}, envie **APENAS A FOTO**.")
            await canal.send(GIF_CATALOGO)
        elif tipo == "lider_torcida":
            await canal.send(f"📣 **LÍDER DE TORCIDA**\n\n{user.mention}, conta pra staff por que você quer ser líder de torcida! 💚🐲", view=FecharTicketView())
        else:
            await canal.send(f"🎟️ **NOVO TICKET**\n\n👤 {user.mention}", view=FecharTicketView())

        await interaction.response.send_message("✅ Ticket criado! Veja o novo canal 😎🐲", ephemeral=True)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

# ============== EVENTOS =================

@bot.event
async def on_ready():
    print(f"🐲 Ligado como {bot.user}")
    bot.add_view(TicketView())
    bot.add_view(FecharTicketView())
    bot.add_view(LiberarCastigoView(0))

    for guild in bot.guilds:
        canal = discord.utils.get(guild.text_channels, name=CANAL_TICKET)
        if canal:
            try: await canal.purge(limit=5)
            except: pass
            await canal.send("🎟️ **CENTRAL DE TICKETS CSI** 🎟️\n\nSelecione abaixo para abrir um ticket 💚🐲", view=TicketView())
            await canal.send(BANNER_TICKET)

@bot.event
async def on_member_join(member):
    canal_lib = discord.utils.get(member.guild.text_channels, name=CANAL_LIBERACAO)
    if canal_lib:
        await canal_lib.send(f"🔔 **NOVO MEMBRO**\n👤 {member.mention}\n\nA staff autoriza?", view=AprovarMembroView(member.id))

@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    canal_log = discord.utils.get(message.guild.text_channels, name=CANAL_LOG)
    if canal_log:
        embed = discord.Embed(title="🗑️ Mensagem Deletada", color=discord.Color.red())
        embed.add_field(name="Autor:", value=message.author.mention, inline=True)
        embed.add_field(name="Canal:", value=message.channel.mention, inline=True)
        embed.add_field(name="Conteúdo:", value=message.content or "Nenhum conteúdo de texto.", inline=False)
        await canal_log.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.bot: return

    # --- TICKET / CATALOGO ---
    if message.channel.id in tickets:
        info = tickets.get(message.channel.id)
        if info["tipo"] == "catalogo" and message.author.id == info["user"]:
            if message.attachments:
                canal_evento = discord.utils.get(message.guild.text_channels, name=CANAL_EVENTO_CATALOGO)
                if canal_evento:
                    await canal_evento.send(f"📸 Foto enviada por {message.author.mention}")
                    for at in message.attachments:
                        file = await at.to_file()
                        await canal_evento.send(file=file)
                await message.channel.send("✅ Foto enviada! Fechando ticket...")
                await asyncio.sleep(3)
                await message.channel.delete()
                tickets.pop(message.channel.id, None)
                return

    # --- CENSURA COM FILTRO DE STAFF ---
    texto = message.content.lower()
    
    # Verifica se o autor possui algum dos cargos imunes
    eh_staff = any(role.name in CARGOS_IMUNES for role in message.author.roles)

    # Só processa a censura se NÃO for staff
    if not eh_staff:
        for palavra in PALAVRAS_PROIBIDAS:
            if palavra in texto:
                await message.delete()
                user_id = message.author.id
                avisos_usuarios[user_id] = avisos_usuarios.get(user_id, 0) + 1
                qtd = avisos_usuarios[user_id]
                canal_adv = discord.utils.get(message.guild.text_channels, name=CANAL_ADVERTENCIAS)

                if qtd == 1:
                    await message.channel.send(f"⚠️ {message.author.mention} você recebeu o **1º AVISO**. Xingamentos não são permitidos! 😭💚")
                elif qtd == 2:
                    await message.channel.send(f"⚠️ {message.author.mention} você recebeu o **2º AVISO**. Se continuar, será silenciado por 1 dia! 😡🐲")
                elif qtd >= 3:
                    try:
                        await message.author.timeout(timedelta(days=1), reason="3 advertências por palavreado.")
                        if canal_adv:
                            await canal_adv.send(f"🚨 **USUÁRIO PUNIDO**\nO membro {message.author.mention} foi silenciado por 1 dia.", view=LiberarCastigoView(user_id))
                        await message.channel.send(f"❌ {message.author.mention} atingiu o limite de avisos e foi colocado de castigo por 1 dia! 🐲🔥")
                    except: pass
                return

    await bot.process_commands(message)

# ============== START =================
bot.run(TOKEN)
