import discord
from discord.ext import commands
import random
import asyncio
import os
from datetime import timedelta
from datetime import datetime

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
CANAL_DESABAFOS = "😮‍💨・desabafos" # Canal onde a censura será ignorada

# GIFs e Imagens
BANNER_TICKET = "https://i.pinimg.com/originals/5d/92/5d/5d925dd101dba34f341148eace3cfe38.gif"
GIF_NAMORADOS = "https://i.pinimg.com/originals/f5/b8/44/f5b844675a7942e4180bb9960c3fe319.gif"
GIF_CATALOGO = "https://i.pinimg.com/originals/0a/1f/86/0a1f869c296b0c30454ffb56397b90fb.gif"
AVATAR_MONSTRINHO = "https://cdn.discordapp.com/attachments/1304658653697019964/1338274026333671485/monstrinho_avatar.png" # Substitua pelo link real se tiver

# Cargos
CARGO_MEMBRO_NOVO = "Membro Novo. 🦇"
CARGO_MEMBROS = "Membros. 🦇"
CARGO_MODERADOR = "Moderador. 🦇"
CARGO_RECRUTADOR = "Recrutador. 🦇"
CARGO_ANJO = "Anjo. 🦇"

# --- ADICIONADO: CARGOS IMUNES ---
CARGOS_IMUNES_NOMES = ["Admin", "Moderador", "DIRETOR", "Admin. Bat", "Moderador. Bat", "DIRETOR. Bat"]

# ============== DADOS =================

tickets = {}
avisos_usuarios = {} 

# ============== PALAVRAS PROIBIDAS =================

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
                await member.send("Oii neném 😭🐲💚 sua entrada tá sendo analisada pela staff, segura firme que já já te chamam, tá bom? 💚✨")
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
async def on_member_remove(member):
    """Evento disparado quando alguém sai do servidor"""
    try:
        mensagem_despedida = (
            f"**Ah não... minhas asinhas até murcharam agora...** 😭🐲💔\n\n"
            f"Poxa, {member.name}, o Monstrinho ficou muito, muito triste em ver você partindo da nossa família CSI. "
            f"Meu coração de código tá apertadinho aqui... 🥺💚\n\n"
            f"Saiba que enquanto você caminha por novos mundos aí fora, eu vou estar aqui cuidando de cada cantinho do nosso clã. "
            f"Vou fazer de tudo pra CSI ficar ainda mais incrível, cheia de brilho e amor, só pra que se um dia você decidir voltar, "
            f"tenha o **retorno triunfante** que você merece! ✨🐲\n\n"
            f"Vou ficar aqui torcendo muito pelo seu sucesso, tá bom? Não esquece que você já foi um pedacinho desse sonho verde! "
            f"Vai lá brilhar, mas saiba que se bater a saudade, meu abraço de monstrinho e um biscoito quentinho vão estar sempre te esperando! 🫂🍪✨\n\n"
            f"**Até logo, neném... vou sentir saudades!** 🐲💚👋"
        )
        await member.send(mensagem_despedida)
    except:
        pass

@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    canal_log = discord.utils.get(message.guild.text_channels, name=CANAL_LOG)
    if canal_log:
        # Layout Estilo Loritta / Aprimorado
        embed = discord.Embed(
            title="📝 Mensagem de texto deletada", 
            description=f"**Canal de texto:** {message.channel.mention}\n\n**Mensagem:**",
            color=0xFF0000, # Vermelho Loritta
            timestamp=datetime.now()
        )
        
        # O "quadro" de visualização da mensagem
        conteudo = message.content or "Mensagem sem texto (verifique se há mídia abaixo)"
        embed.add_field(name="\u200b", value=f"```\n{conteudo}\n```", inline=False)
        
        # --- ADICIONADO: SUPORTE PARA IMAGEM APAGADA ---
        if message.attachments:
            # Pega a URL da primeira imagem anexada
            anexo = message.attachments[0]
            if any(anexo.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg', 'gif', 'webp']):
                embed.set_image(url=anexo.proxy_url)

        # Miniatura do Monstrinho ou Autor (estilo Loritta usa o autor no topo)
        embed.set_author(name=f"{message.author}", icon_url=message.author.display_avatar.url)
        embed.set_thumbnail(url=AVATAR_MONSTRINHO) # Foto do monstrinho no canto
        
        # Informações técnicas igual a imagem da Loritta
        info_footer = (
            f"ID do usuário\n{message.author.id}\n\n"
            f"ID do servidor\n{message.guild.id}\n\n"
            f"ID do canal\n{message.channel.id}\n\n"
            f"ID da mensagem\n{message.id}"
        )
        embed.add_field(name="\u200b", value=f"**{info_footer}**", inline=False)
        
        # Rodapé final
        embed.set_footer(text=f"Feito com carinho pelo Monstrinho 🐲 • ID do usuário: {message.author.id}")
        
        await canal_log.send(embed=embed)

# ============== COMANDOS ADICIONAIS =================

@bot.command()
async def testepv(ctx):
    """Comando para testar a mensagem de adeus no PV"""
    mensagem_despedida = (
        f"**Ah não... minhas asinhas até murcharam agora...** 😭🐲💔\n\n"
        f"Poxa, {ctx.author.name}, o Monstrinho ficou muito, muito triste em ver você partindo da nossa família CSI. "
        f"Meu coração de código tá apertadinho aqui... 🥺💚\n\n"
        f"Saiba que enquanto você caminha por novos mundos aí fora, eu vou estar aqui cuidando de cada cantinho do nosso clã. "
        f"Vou fazer de tudo pra CSI ficar ainda mais incrível, cheia de brilho e amor, só pra que se um dia você decidir voltar, "
        f"tenha o **retorno triunfante** que você merece! ✨🐲\n\n"
        f"Vou ficar aqui torcendo muito pelo seu sucesso, tá bom? Não esquece que você já foi um pedacinho desse sonho verde! "
        f"Vai lá brilhar, mas saiba que se bater a saudade, meu abraço de monstrinho e um biscoito quentinho vão estar sempre te esperando! 🫂🍪✨\n\n"
        f"**Até logo, neném... vou sentir saudades!** 🐲💚👋"
    )
    try:
        await ctx.author.send(mensagem_despedida)
        await ctx.send("✅ Enviei a mensagem no seu PV! Dá uma olhadinha lá 🐲💚")
    except:
        await ctx.send("❌ Não consegui enviar! Verifique se seu privado está aberto nas configurações de privacidade. 😭")

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

    # --- CENSURA COM FILTRO DE STAFF E CANAL EXCEÇÃO ---
    texto = message.content.lower()
    eh_dono = message.author.id == DONO_ID
    eh_staff = any(role.name in CARGOS_IMUNES_NOMES for role in message.author.roles)
    eh_canal_desabafo = message.channel.name == CANAL_DESABAFOS

    # Só aplica censura se NÃO for dono, NÃO for staff e NÃO for no canal de desabafos
    if not eh_dono and not eh_staff and not eh_canal_desabafo:
        for palavra in PALAVRAS_PROIBIDAS:
            if palavra in texto:
                try:
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
                            try:
                                await message.author.send(
                                    "**Poxa vida... o Monstrinho tá MUITO triste com você!** 😡🐲🔥\n\n"
                                    "Eu já tinha avisado que falar essas coisas feias não pode aqui na CSI! "
                                    "Agora você vai ter que ficar de castigo por 1 dia pra pensar no que fez... "
                                    "Poxa, o monstrinho só quer dar carinho e biscoitos, não me faça ficar bravo de novo, tá bom? 😭💚✨\n\n"
                                    "*Espero que quando você voltar, seu coração esteja limpinho de palavras ruins!*"
                                )
                            except: pass
                            await message.author.timeout(timedelta(days=1), reason="3 advertências por palavreado.")
                            if canal_adv:
                                await canal_adv.send(f"🚨 **USUÁRIO PUNIDO**\nO membro {message.author.mention} foi silenciado por 1 dia.", view=LiberarCastigoView(user_id))
                            await message.channel.send(f"❌ {message.author.mention} atingiu o limite de avisos e foi colocado de castigo por 1 dia! 🐲🔥")
                        except: pass
                    return
                except: pass

    await bot.process_commands(message)

# ============== START =================
bot.run(TOKEN)
