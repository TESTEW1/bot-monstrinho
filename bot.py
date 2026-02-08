import discord
from discord.ext import commands, tasks
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
CANAL_DESABAFOS = "😮‍💨・desabafos"
CANAL_CHAT_ANJO = "🪽・chat-anjo"
CANAL_RANKING_MONSTRINHO = "ranking-monstrinho"

# GIFs e Imagens
BANNER_TICKET = "https://i.pinimg.com/originals/5d/92/5d/5d925dd101dba34f341148eace3cfe38.gif"
GIF_NAMORADOS = "https://i.pinimg.com/originals/f5/b8/44/f5b844675a7942e4180bb9960c3fe319.gif"
GIF_CATALOGO = "https://i.pinimg.com/originals/0a/1f/86/0a1f869c296b0c30454ffb56397b90fb.gif"
AVATAR_MONSTRINHO = "https://cdn.discordapp.com/attachments/1304658653697019964/1338274026333671485/monstrinho_avatar.png"
GIF_ACERTO_MONSTRINHO = "https://media.tenor.com/8yMrP1Cs7ykAAAAM/ninjala-ninjala-season6trailer.gif"

# Cargos
CARGO_MEMBRO_NOVO = "Membro Novo. 🦇"
CARGO_MEMBROS = "Membros. 🦇"
CARGO_MODERADOR = "Moderador. 🦇"
CARGO_RECRUTADOR = "Recrutador. 🦇"
CARGO_ANJO = "Anjo. 🦇"

CARGOS_IMUNES_NOMES = [
    "Admin", 
    "Moderador", 
    "DIRETOR", 
    "Admin. Bat", 
    "Moderador. Bat", 
    "DIRETOR. Bat",
    "Admin. 🦇",
    "Moderador. 🦇"
]


# ============== DADOS =================

tickets = {}
avisos_usuarios = {} 
pontuacao_monstrinho = {} # Guardar os pontos
jogo_em_andamento = {"pergunta": None, "resposta": None, "venceu": False}

# Perguntas do Monstrinho
LISTA_PERGUNTAS = [
    ("Qual é o super-herói que tem medo de morcego?", "batman"),
    ("Quem é o bruxo mais famoso de Hogwarts?", "harry potter"),
    ("Qual o nome do encanador da Nintendo?", "mario"),
    ("Quem é o melhor amigo do Bob Esponja?", "patrick estrela"),
    ("Qual o filme do navio que afundou e fez todo mundo chorar?", "titanic"),
    ("Quem canta “Billie Jean”?", "michael jackson"),
    ("Qual o nome do robô dourado de Star Wars?", "c-3po"),
    ("Quem é o rival do Goku?", "vegeta"),
    ("Qual o jogo onde você constrói tudo com blocos?", "minecraft"),
    ("Quem é o personagem principal de Shrek?", "shrek"),
    ("Qual herói usa escudo?", "capitão américa"),
    ("Quem canta “Shape of You”?", "ed sheeran"),
    ("Qual o nome do dragão da Daenerys mais famoso?", "drogon"),
    ("Quem é o dono do martelo Mjölnir?", "thor"),
    ("Qual o pokémon elétrico mais famoso?", "pikachu"),
    ("Quem é o palhaço vilão do Batman?", "coringa"),
    ("Qual o nome do filme dos dinossauros?", "jurassic park"),
    ("Quem é o melhor amigo do Woody?", "buzz lightyear"),
    ("Qual o nome do vilão roxo da Marvel?", "thanos"),
    ("Quem é o personagem amarelo que mora num abacaxi?", "bob esponja"),
    ("Qual o carro mais famoso de Velozes e Furiosos?", "dodge charger"),
    ("Quem canta “Bad Romance”?", "lady gaga"),
    ("Qual o nome do mago de barba branca do Senhor dos Anéis?", "gandalf"),
    ("Quem é o líder dos Vingadores?", "capitão américa"),
    ("Qual o nome do planeta do Superman?", "krypton"),
    ("Quem é o melhor amigo do Chaves?", "quico"),
    ("Qual o nome do boneco assassino?", "chucky"),
    ("Quem canta “Blinding Lights”?", "the weeknd"),
    ("Qual o nome do detetive de chapéu e lupa?", "sherlock holmes"),
    ("Quem é o rei dos monstros?", "godzilla"),
    ("Qual o anime dos ninjas?", "naruto"),
    ("Quem canta “Thriller”?", "michael jackson"),
    ("Qual o nome do cachorro do Scooby-Doo?", "scooby-doo"),
    ("Quem é o homem mais rápido da DC?", "flash"),
    ("Qual o nome do vilão careca dos X-Men?", "magneto"),
    ("Quem canta “Rolling in the Deep”?", "adele"),
    ("Qual o nome do ogro verde famoso?", "shrek"),
    ("Quem é o pai do Simba?", "mufasa"),
    ("Qual o jogo do encanador que pula em tartarugas?", "super mario"),
    ("Quem é o rei do pop?", "michael jackson"),
    ("Qual o nome do rato mais famoso da Disney?", "mickey mouse"),
    ("Quem canta “Baby”?", "justin bieber"),
    ("Qual o nome da escola de magia do Harry Potter?", "hogwarts"),
    ("Quem é o vilão principal do Homem-Aranha?", "duende verde"),
    ("Qual o nome do robô que se apaixona no espaço?", "wall-e"),
    ("Quem canta “Uptown Funk”?", "bruno mars"),
    ("Qual o nome do amigo do Naruto que vira rival?", "sasuke"),
    ("Quem é o deus da trapaça na Marvel?", "loki"),
    ("Qual o nome do panda lutador de kung fu?", "po"),
    ("Quem canta “Firework”?", "katy perry"),
    ("Qual o nome do castelo da Disney?", "castelo da cinderela"),
    ("Quem é o protagonista de Matrix?", "neo"),
    ("Qual o nome do carro falante da Pixar?", "relâmpago mcqueen"),
    ("Quem canta “Poker Face”?", "lady gaga"),
    ("Qual o nome do alienígena azul que gosta de bicicleta?", "stitch"),
    ("Quem é o melhor amigo do Homem de Ferro nos Vingadores?", "máquina de combate"),
    ("Qual o nome do tubarão de Procurando Nemo?", "bruce"),
    ("Quem canta “Hello”?", "adele"),
    ("Qual o nome do vampiro que brilha no sol?", "edward cullen"),
    ("Quem é o maior vilão de Star Wars?", "darth vader"),
    ("Qual o nome do herói que encolhe?", "homem-formiga"),
    ("Quem canta “Levitating”?", "dua lipa"),
    ("Qual o nome do robô gigante dos Transformers?", "optimus prime"),
    ("Quem é o melhor amigo do Shrek?", "burro"),
    ("Qual o nome do desenho dos monstrinhos de bolso?", "pokémon"),
    ("Quem canta “Shake It Off”?", "taylor swift"),
    ("Qual o nome do herói cego da Marvel?", "demolidor"),
    ("Quem é o líder das Tartarugas Ninja?", "leonardo"),
    ("Qual o nome do filme do leão rei?", "o rei leão"),
    ("Quem canta “Stay”?", "the kid laroi e justin bieber"),
    ("Qual o nome do vilão verde do Homem-Aranha?", "duende verde"),
    ("Quem é o bruxo de barba longa de Harry Potter?", "dumbledore"),
    ("Qual o nome do jogo de tiro com bombinhas e parede?", "bomberman"),
    ("Quem canta “Hips Don’t Lie”?", "shakira"),
    ("Qual o nome do vilão que congela tudo?", "sr frio"),
    ("Quem é o melhor amigo do Goku?", "kuririn"),
    ("Qual o nome do planeta de Star Wars cheio de areia?", "tatooine"),
    ("Quem canta “Waka Waka”?", "shakira"),
    ("Qual o nome do filme dos carros que viram robôs?", "transformers"),
    ("Quem é o herói com garras de metal?", "wolverine"),
    ("Qual o nome do desenho dos carrinhos de corrida da Pixar?", "carros"),
    ("Quem canta “Sorry”?", "justin bieber"),
    ("Qual o nome do vilão roxo do Homem de Ferro 3?", "mandarim"),
    ("Quem é o herói com escudo de vibranium?", "capitão américa"),
    ("Qual o nome do filme do palhaço assassino do esgoto?", "it a coisa"),
    ("Quem canta “Roar”?", "katy perry"),
    ("Qual o nome do boneco de neve de Frozen?", "olaf"),
    ("Quem é a irmã da Elsa?", "anna"),
    ("Qual o nome do dragão de Como Treinar o Seu Dragão?", "banguela"),
    ("Quem canta “Counting Stars”?", "onerepublic"),
    ("Qual o nome do detetive de Pokémon?", "pikachu"),
    ("Quem é o herói com arco e flecha dos Vingadores?", "gavião arqueiro"),
    ("Qual o nome do filme do robô gigante contra monstros?", "círculo de fogo"),
    ("Quem canta “Believer”?", "imagine dragons"),
    ("Qual o nome do personagem verde que odeia o Natal?", "grinch"),
    ("Quem é o melhor amigo do Homem-Aranha?", "ned"),
    ("Qual o nome do mago de oz?", "o mágico de oz"),
    ("Quem canta “As It Was”?", "harry styles"),
    ("Qual o nome do vilão careca do Superman?", "lex luthor"),
    ("Quem é o herói bilionário da Marvel?", "homem de ferro"),
    ("Qual o nome do desenho do menino com relógio alienígena?", "ben 10"),
    ("Quem canta “Take on Me”?", "a-ha"),
    ("Qual o nome do robô de exterminador do futuro?", "t-800"),
    ("Quem é o melhor amigo do sonic?", "tails"),
    ("Qual o nome do vilão de pantera negra?", "killmonger"),
    ("Quem canta “Old Town Road”?", "lil nas x"),
    ("Qual o nome do cavaleiro negro de star wars?", "darth vader"),
    ("Quem é o rei de wakanda?", "pantera negra"),
    ("Qual o nome do jogo de batalha com 100 jogadores?", "fortnite"),
    ("Quem canta “Radioactive”?", "imagine dragons"),
    ("Qual o nome do personagem que fala “eu sou groot”?", "groot"),
    ("Quem é o vilão de vingadores ultimato?", "thanos"),
    ("Qual o nome do desenho dos heróis adolescentes da dc?", "jovens titãs"),
    ("Quem canta “senorita”?", "shawn mendes e camila cabello"),
    ("Qual o nome do alien do filme de terror no espaço?", "xenomorfo"),
    ("Quem é o herói que solta teia?", "homem-aranha"),
    ("Qual o nome do dragão de a casa do dragão mais famoso?", "vhagar"),
    ("Quem canta “happy”?", "pharrell williams"),
    ("Qual o nome do jogo do urso animatrônico de terror?", "five nights at freddy’s"),
    ("Quem é o herói que vira gigante verde quando fica bravo?", "hulk")
]

# ============== PALAVRAS PROIBIDAS =================

PALAVRAS_PROIBIDAS = [
    "porra", "caralho", "merda", "bosta", "puta", "puto", "vadia", "desgraça", 
    "idiota", "burro", "imbecil", "otário", "retardado", "lixo", "nojento", 
    "arrombado", "viado", "bicha", "piranha", "vai se fuder", "vai se foder", 
    "vai tomar no cu", "tomar no cu", "filho da puta", "se mata", "se fode", 
    "fdp", "vsf", "krl", "pqp", "prr", "tmnc", "buceta", "carai", "karalho"
]

# ============== FUNÇÕES AUXILIARES JOGO =================

async def atualizar_ranking(guild):
    canal_rank = discord.utils.get(guild.text_channels, name=CANAL_RANKING_MONSTRINHO)
    if not canal_rank: return
    
    # Ordenar ranking
    rank_ordenado = sorted(pontuacao_monstrinho.items(), key=lambda item: item[1], reverse=True)
    
    embed = discord.Embed(
        title="🏆 RANKING MONSTRINHO-COINS 🏆",
        description="Aqui estão os maiores gênios do nosso servidor! 🐲💚",
        color=0x00FF7F,
        timestamp=datetime.now()
    )
    embed.set_thumbnail(url=AVATAR_MONSTRINHO)
    
    texto_rank = ""
    for i, (user_id, pontos) in enumerate(rank_ordenado[:15], 1):
        user = guild.get_member(user_id)
        nome = user.display_name if user else f"Usuário Desconhecido ({user_id})"
        texto_rank += f"**{i}º** | {nome} — `{pontos} Coins` 🐲\n"
    
    embed.description += f"\n\n{texto_rank if texto_rank else 'Ninguém pontuou ainda... 🥺'}"
    embed.set_footer(text="CSI - Sistema de Jogos")

    # Tenta achar a última mensagem do bot para editar, ou manda uma nova e limpa o canal
    await canal_rank.purge(limit=5)
    await canal_rank.send(embed=embed)

async def disparar_pergunta(guild):
    canal_geral = discord.utils.get(guild.text_channels, name=CANAL_GERAL)
    if not canal_geral: return

    pergunta, resposta = random.choice(LISTA_PERGUNTAS)
    jogo_em_andamento["pergunta"] = pergunta
    jogo_em_andamento["resposta"] = resposta.lower()
    jogo_em_andamento["venceu"] = False

    embed = discord.Embed(
        title="🐲 HORA DO JOGUINHO DO MONSTRINHO! 🐲",
        description=f"Oii amiguinhos! Vamos ver quem é esperto? ✨\n\n**PERGUNTA:**\n> {pergunta}\n\nO primeiro que acertar nos próximos **5 minutos** ganha **100 monstrinho-coins**! Boa sorte! 💚🐉",
        color=0xADFF2F
    )
    embed.set_thumbnail(url=AVATAR_MONSTRINHO)
    embed.set_footer(text="Você tem 5 minutos! Responda aqui no chat!")
    
    msg_pergunta = await canal_geral.send(embed=embed)

    # Espera 5 minutos ou até alguém ganhar
    for _ in range(300): # 300 segundos = 5 min
        if jogo_em_andamento["venceu"]: break
        await asyncio.sleep(1)
    
    if not jogo_em_andamento["venceu"]:
        jogo_em_andamento["pergunta"] = None
        await canal_geral.send("🥺 Ahhh poxa, ninguém acertou a tempo... O Monstrinho ficou triste, mas logo eu volto com outra! 🐲💔")

# ============== LOOP DO JOGO =================

@tasks.loop(hours=3) # Base de 3 horas, mas vamos variar dentro do task
async def loop_jogo_monstrinho():
    # Espera um tempo aleatório entre 0 e 2 horas extras (totalizando 3 a 5 horas)
    espera_extra = random.randint(0, 7200)
    await asyncio.sleep(espera_extra)
    
    for guild in bot.guilds:
        await disparar_pergunta(guild)

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
        cargos = [discord.utils.get(guild.roles, name=CARGO_MEMBRO_NOVO), discord.utils.get(guild.roles, name=CARGO_MEMBROS)]
        for c in cargos:
            if c: await membro.add_roles(c)
        try: await membro.send("AAAA 😭🐲💚 Você foi APROVADO! Bem-vindo à famíliaaa!!! 💚✨")
        except: pass
        canal_geral = discord.utils.get(guild.text_channels, name=CANAL_GERAL)
        cargo_anjo = discord.utils.get(guild.roles, name=CARGO_ANJO)
        cargo_recrutador = discord.utils.get(guild.roles, name=CARGO_RECRUTADOR)
        mencoes = []
        if cargo_anjo: mencoes.append(cargo_anjo.mention)
        if cargo_recrutador: mencoes.append(cargo_recrutador.mention)
        if canal_geral:
            await canal_geral.send(f"AAAA 😭🐲💚 {membro.mention} foi LIBERADO!\n{' '.join(mencoes)} venham dar boas-vindas pro neném do monstrinhooo 🐲💚✨")
        await interaction.followup.send("✅ Liberado com sucesso!", ephemeral=True)

    @discord.ui.button(label="⏳ Aguardar", style=discord.ButtonStyle.secondary, custom_id="aguardar_membro")
    async def aguardar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🕒 Em análise 💚🐲", ephemeral=True)
        guild = interaction.guild
        membro = guild.get_member(self.membro_id)
        if membro:
            try: await membro.send("Oii neném 😭🐲💚 sua entrada tá sendo analisada pela staff, segura firme que já já te chamam, tá bom? 💚✨")
            except: pass

    @discord.ui.button(label="❌ Recusar", style=discord.ButtonStyle.danger, custom_id="recusar_membro")
    async def recusar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("❌ Recusado.", ephemeral=True)
        guild = interaction.guild
        membro = guild.get_member(self.membro_id)
        if membro:
            try: await membro.kick(reason="Pedido de entrada recusado pela staff.")
            except: pass

# ============== TICKET =================

class FecharTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Fechar Ticket", style=discord.ButtonStyle.danger, custom_id="fechar_ticket")
    async def fechar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔒 Fechando em 5s...", ephemeral=True)
        await asyncio.sleep(5)
        await interaction.channel.delete()

class ReivindicarAnjoView(discord.ui.View):
    def __init__(self, canal_ticket_id: int):
        super().__init__(timeout=None)
        self.canal_ticket_id = canal_ticket_id

    @discord.ui.button(label="🤝 Assumir Chamado", style=discord.ButtonStyle.success, custom_id="reivindicar_anjo")
    async def reivindicar(self, interaction: discord.Interaction, button: discord.ui.Button):
        cargo_anjo = discord.utils.get(interaction.guild.roles, name=CARGO_ANJO)
        eh_staff = any(role.name in CARGOS_IMUNES_NOMES for role in interaction.user.roles)
        
        if cargo_anjo not in interaction.user.roles and not eh_staff:
            return await interaction.response.send_message("❌ Apenas um Anjo ou Staff pode fazer isso! 🪽", ephemeral=True)

        canal_ticket = interaction.guild.get_channel(self.canal_ticket_id)
        if not canal_ticket:
            return await interaction.response.send_message("❌ Este ticket já foi fechado ou não existe mais.", ephemeral=True)

        await canal_ticket.set_permissions(interaction.user, view_channel=True, send_messages=True)
        
        embed_no_ticket = discord.Embed(
            description=f"✨ **O Anjo {interaction.user.mention} abriu as asinhas e chegou para te ajudar!** 🪽💚\n\nFique tranquilo(a), agora você está sob a proteção desse anjinho!",
            color=0x00FF7F
        )
        await canal_ticket.send(embed=embed_no_ticket)
        
        button.label = f"Assumido por {interaction.user.display_name}"
        button.style = discord.ButtonStyle.secondary
        button.disabled = True
        await interaction.response.edit_message(view=self)

class TicketSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="🛠️ Suporte", value="suporte"),
            discord.SelectOption(label="🚨 Denúncia", value="denuncia"),
            discord.SelectOption(label="👮 Falar com Staff", value="staff"),
            discord.SelectOption(label="💘 Evento dos Namorados", value="namorados"),
            discord.SelectOption(label="📸 Evento Catálogo", value="catalogo"),
            discord.SelectOption(label="📣 Líder de Torcida", value="lider_torcida"),
            discord.SelectOption(label="👼 Pedir um Anjo", value="anjos"), 
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
        
        if tipo == "anjos":
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            }
        else:
            cargo_mod = discord.utils.get(guild.roles, name=CARGO_MODERADOR)
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            }
            if cargo_mod:
                overwrites[cargo_mod] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        categoria = interaction.channel.category
        canal = await guild.create_text_channel(
            name=f"👼┃{tipo}-{user.name}".lower() if tipo == "anjos" else f"🎟️┃{tipo}-{user.name}".lower(),
            category=categoria,
            overwrites=overwrites
        )

        tickets[canal.id] = {"user": user.id, "tipo": tipo}

        if tipo == "anjos":
            embed_user = discord.Embed(
                description=f"✨ **Segura o coração, {user.mention}!** ✨\n\nUm anjinho já foi avisado e logo, logo ele vai aparecer voando aqui para te dar todo o carinho e suporte do mundo! 🪽💚",
                color=0xFFB6C1
            )
            await canal.send(embed=embed_user, view=FecharTicketView())
            
            canal_anjo_logs = discord.utils.get(guild.text_channels, name=CANAL_CHAT_ANJO)
            if canal_anjo_logs:
                cargo_anjo_mencao = discord.utils.get(guild.roles, name=CARGO_ANJO)
                embed_anjo = discord.Embed(
                    title="🪽 Novo Chamado Angelical!",
                    description=f"O(A) pequeno(a) {user.mention} abriu um ticket e precisa de acolhimento!\n\n📍 **Canal do Ticket:** {canal.mention}",
                    color=0x87CEEB,
                    timestamp=datetime.now()
                )
                embed_anjo.set_footer(text="CSI - Sistema de Anjos")
                await canal_anjo_logs.send(content=cargo_anjo_mencao.mention if cargo_anjo_mencao else None, embed=embed_anjo, view=ReivindicarAnjoView(canal.id))

        elif tipo == "namorados":
            embed_namo = discord.Embed(title="💘 EVENTO DOS NAMORADOS", color=0xFF69B4)
            embed_namo.description = f"{user.mention}"
            embed_namo.set_image(url=GIF_NAMORADOS)
            await canal.send(embed=embed_namo)
            
        elif tipo == "catalogo":
            embed_cat = discord.Embed(title="📸 EVENTO CATÁLOGO", color=0x00FFFF)
            embed_cat.description = f"{user.mention}, envie **APENAS A FOTO**."
            embed_cat.set_image(url=GIF_CATALOGO)
            await canal.send(embed=embed_cat)
            
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
    
    if not loop_jogo_monstrinho.is_running():
        loop_jogo_monstrinho.start()

    for guild in bot.guilds:
        canal = discord.utils.get(guild.text_channels, name=CANAL_TICKET)
        if canal:
            try: await canal.purge(limit=5)
            except: pass
            await canal.send("🎟️ **CENTRAL DE TICKETS CSI** 🎟️\n\nSelecione abaixo para abrir um ticket 💚🐲", view=TicketView())
            
            # Banner enviado em Embed para esconder o link
            embed_banner = discord.Embed(color=0x2b2d31)
            embed_banner.set_image(url=BANNER_TICKET)
            await canal.send(embed=embed_banner)

@bot.event
async def on_member_join(member):
    canal_lib = discord.utils.get(member.guild.text_channels, name=CANAL_LIBERACAO)
    if canal_lib:
        await canal_lib.send(f"🔔 **NOVO MEMBRO**\n👤 {member.mention}\n\nA staff autoriza?", view=AprovarMembroView(member.id))

@bot.event
async def on_member_remove(member):
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
        embed = discord.Embed(
            title="📝 Mensagem de texto deletada", 
            description=f"**Canal de texto:** {message.channel.mention}\n\n**Mensagem:**",
            color=0xFF0000,
            timestamp=datetime.now()
        )
        conteudo = message.content or "Mensagem sem texto (verifique se há mídia abaixo)"
        embed.add_field(name="\u200b", value=f"```\n{conteudo}\n```", inline=False)
        if message.attachments:
            anexo = message.attachments[0]
            if any(anexo.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg', 'gif', 'webp']):
                embed.set_image(url=anexo.proxy_url)
        embed.set_author(name=f"{message.author}", icon_url=message.author.display_avatar.url)
        embed.set_thumbnail(url=AVATAR_MONSTRINHO)
        info_footer = (
            f"ID do usuário\n{message.author.id}\n\n"
            f"ID do servidor\n{message.guild.id}\n\n"
            f"ID do canal\n{message.channel.id}\n\n"
            f"ID da mensagem\n{message.id}"
        )
        embed.add_field(name="\u200b", value=f"**{info_footer}**", inline=False)
        embed.set_footer(text=f"Feito com carinho pelo Monstrinho 🐲 • ID do usuário: {message.author.id}")
        await canal_log.send(embed=embed)

# ============== COMANDO JOGO (DONO) =================
@bot.command()
async def jogo(ctx):
    if ctx.author.id != DONO_ID:
        return await ctx.send("❌ Só meu papai pode forçar o início de um jogo! 🐲")
    await ctx.send("🐲 Iniciando rodada de teste para você, papai!")
    await disparar_pergunta(ctx.guild)

@bot.command()
async def testepv(ctx):
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

    # --- LÓGICA DO JOGUINHO ---
    if jogo_em_andamento["pergunta"] and message.channel.name == CANAL_GERAL:
        if message.content.lower() == jogo_em_andamento["resposta"]:
            jogo_em_andamento["venceu"] = True
            jogo_em_andamento["pergunta"] = None
            
            user_id = message.author.id
            pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + 100
            
            embed_acerto = discord.Embed(
                title="🎉 PARABÉNS NENÉM! 🎉",
                description=f"{message.author.mention}, você foi muito rápido(a) e acertou!\nO Monstrinho está muito orgulhoso! 🐲💚\n\nVocê ganhou **100 Monstrinho-Coins**!",
                color=0x00FF7F
            )
            embed_acerto.set_image(url=GIF_ACERTO_MONSTRINHO)
            await message.reply(embed=embed_acerto)

            await atualizar_ranking(message.guild)
            return

    # --- TICKET CATALOGO ---
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

    # --- PALAVRAS PROIBIDAS ---
    texto = message.content.lower()
    eh_dono = message.author.id == DONO_ID
    eh_staff = any(role.name in CARGOS_IMUNES_NOMES for role in message.author.roles)
    eh_canal_desabafo = message.channel.name == CANAL_DESABAFOS
    if not eh_dono and not eh_staff and not eh_canal_desabafo:
        for palavra in PALAVRAS_PROIBIDAS:
            if palavra in texto:
                try:
                    await message.delete()
                    user_id = message.author.id
                    avisos_usuarios[user_id] = avisos_usuarios.get(user_id, 0) + 1
                    qtd = avisos_usuarios[user_id]
                    if qtd == 1:
                        await message.channel.send(f"⚠️ {message.author.mention} você recebeu o **1º AVISO**. Xingamentos não são permitidos! 😭💚")
                    elif qtd == 2:
                        await message.channel.send(f"⚠️ {message.author.mention} você recebeu o **2º AVISO**. Se continuar, será silenciado por 1 dia! 😡🐲")
                    elif qtd >= 3:
                        try:
                            await message.author.send(
                                "**Poxa vida... o Monstrinho tá MUITO triste com você!** 😡🐲🔥\n\n"
                                "Eu já tinha avisado que falar essas coisas feias não pode aqui na CSI! "
                                "Agora você vai ter que ficar de castigo por 1 dia pra pensar no que fez... "
                                "Poxa, o monstrinho só quer dar carinho e biscoitos, não me faça ficar bravo de novo, tá bom? 😭💚✨\n\n"
                                "*Espero que quando você voltar, seu coração esteja limpinho de palavras ruins!*"
                            )
                        except: pass
                        await message.author.timeout(timedelta(days=1), reason="3 advertências por palavreado")
                        
                        canal_staff = discord.utils.get(message.guild.text_channels, name=CANAL_LIBERACAO)
                        if canal_staff:
                            await canal_staff.send(f"🚨 **MEMBRO EM CASTIGO**\n👤 {message.author.mention} atingiu 3 avisos.\n\nDeseja liberar antes do tempo?", view=LiberarCastigoView(message.author.id))
                    return
                except: pass

    await bot.process_commands(message)

bot.run(TOKEN)
