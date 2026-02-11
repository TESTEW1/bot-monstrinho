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
CANAL_CHAT_CUPIDOS = "💘・chat-cupidos"
CANAL_CHAT_STAFF_GERAL = "🔰・chat-staff"
CANAL_RANKING_MONSTRINHO = "ranking-monstrinho"

# GIFs e Imagens
BANNER_TICKET = "https://i.pinimg.com/originals/5d/92/5d/5d925dd101dba34f341148eace3cfe38.gif"
GIF_NAMORADOS = "https://i.pinimg.com/originals/f5/b8/44/f5b844675a7942e4180bb9960c3fe319.gif"
GIF_CATALOGO = "https://i.pinimg.com/originals/0a/1f/86/0a1f869c296b0c30454ffb56397b90fb.gif"
AVATAR_MONSTRINHO = "https://cdn.discordapp.com/attachments/1304658653697019964/1338274026333671485/monstrinho_avatar.png"
GIF_ACERTO_MONSTRINHO = "https://media.tenor.com/8yMrP1Cs7ykAAAAM/ninjala-ninjala-season6trailer.gif"

# NOVOS GIFS JOGOS
GIF_ADIVINHE_NUMERO = "https://pixmidia.com.br/wp-content/uploads/2020/08/alvo.gif"
GIF_PPT = "https://c.tenor.com/CACaU3WIOQYAAAAd/friends-monica-geller.gif"
GIF_CARA_COROA = "https://usagif.com/wp-content/uploads/gifs/coin-flip-18.gif"
GIF_DADO = "https://miro.medium.com/v2/resize:fit:1080/1*n4_Ic0t_s8YJN4YhHxb5xw.gif"
GIF_ROLETA_GIRANDO = "https://i.pinimg.com/originals/30/16/25/30162543258ca8058fe7bc4003be2a33.gif"
GIF_DERROTA = "https://i.pinimg.com/originals/ca/c9/81/cac9814161057dbc9bb2ae0ba0dbdfc0.gif"
GIF_BAU_COINS = "https://media.tenor.com/8yMrP1Cs7ykAAAAM/ninjala-ninjala-season6trailer.gif"
# Cargos
CARGO_MEMBRO_NOVO = "Membro Novo. 🦇"
CARGO_MEMBROS = "Membros. 🦇"
CARGO_MODERADOR = "Moderador. 🦇"
CARGO_RECRUTADOR = "Recrutador. 🦇"
CARGO_ANJO = "Anjo. 🦇"
CARGO_CUPIDOS = "Cupidos"
CARGO_STAFF_EQUIPE = "Equipe Staff. 🦇"

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
total_castigos_usuario = {} # Contador de castigos total
pontuacao_monstrinho = {} # Guardar os pontos
jogo_em_andamento = {"tipo": None, "pergunta": None, "resposta": None, "venceu": False, "participantes_tentaram": []}

# Listas de Jogos
LISTA_PERGUNTAS = [
("Qual o nome do bruxo de Harry Potter?", "harry potter"),
("Qual herói usa escudo?", "capitao america"),
("Quem é o encanador da Nintendo?", "mario"),
("Qual é o planeta vermelho?", "marte"),
("Quem mora em uma casa no fundo do mar?", "bob esponja"),
("Qual o nome do rato da Disney?", "mickey"),
("Quem é o parceiro do Batman?", "robin"),
("Qual o nome do ogro verde?", "shrek"),
("Quem é o deus do trovão da Marvel?", "thor"),
("Qual o nome do robô do Star Wars que faz bip bip?", "r2d2"),
("Quem vive no abacaxi no fundo do mar?", "bob esponja"),
("Qual é o carro do Batman?", "batmovel"),
("Quem é o rival do Mario?", "bowser"),
("Qual herói é feito de ferro?", "homem de ferro"),
("Qual o nome do boneco do Toy Story?", "woody"),
("Quem é o vilão roxo da Marvel?", "thanos"),
("Qual o nome do leão da Disney?", "simba"),
("Qual herói solta teia?", "homem aranha"),
("Quem é o melhor amigo do Shrek?", "burro"),
("Qual o nome do ninja de laranja?", "naruto"),
("Quem é o treinador do Pikachu?", "ash"),
("Qual o nome do dragão de Como Treinar Seu Dragão?", "banguela"),
("Quem é o alienígena azul da Disney?", "stitch"),
("Qual o nome do palhaço do IT?", "pennywise"),
("Quem é o rei da selva?", "leao"),
("Qual o nome do filme dos dinossauros?", "jurassic park"),
("Quem é o herói de capa vermelha e azul?", "superman"),
("Qual o nome da princesa de gelo?", "elsa"),
("Quem vive com o Pateta?", "mickey"),
("Qual o nome do robô amarelo de Transformers?", "bumblebee"),
("Quem é o herói com garras de metal?", "wolverine"),
("Qual o nome do navio pirata do Jack Sparrow?", "perola negra"),
("Quem é o melhor amigo do Harry Potter?", "rony"),
("Qual o nome da escola de magia?", "hogwarts"),
("Quem é o deus da trapaça da Marvel?", "loki"),
("Qual o nome do pokémon elétrico?", "pikachu"),
("Quem é o cowboy do Toy Story?", "woody"),
("Qual o nome do peixe do filme Procurando Nemo?", "nemo"),
("Quem é o inimigo do Sonic?", "eggman"),
("Qual o nome da princesa da Bela e a Fera?", "bela"),
("Quem é o super-herói verde gigante?", "hulk"),
("Qual o nome do boneco espacial do Toy Story?", "buzz"),
("Quem é o mago de barba branca em Senhor dos Anéis?", "gandalf"),
("Qual o nome do dragão do filme Shrek?", "dragao"),
("Quem é o melhor amigo do Bob Esponja?", "patrick"),
("Qual o nome do gato preguiçoso dos quadrinhos?", "garfield"),
("Quem é o detetive amarelo da Disney?", "pikachu"),
("Qual o nome do monstro azul da Pixar?", "sulley"),
("Quem é o vilão do Batman com sorriso?", "coringa"),
("Qual o nome do filme do leãozinho da Disney?", "rei leao"),
("Quem é o herói do escudo vermelho e azul?", "capitao america"),
("Qual o nome do carro vermelho do filme Carros?", "relampago mcqueen"),
("Quem é o vilão do Homem-Aranha com tentáculos?", "doutor octopus"),
("Qual o nome da princesa da torre?", "rapunzel"),
("Quem é o herói com martelo?", "thor"),
("Qual o nome do robô do filme Wall-E?", "walle"),
("Quem é o melhor amigo do Naruto?", "sasuke"),
("Qual o nome do vilão do Rei Leão?", "scar"),
("Quem é o herói que corre rápido?", "flash"),
("Qual o nome do cachorro da família Simpson?", "ajudante de papai noel"),
("Quem é o vampiro famoso de Crepúsculo?", "edward"),
("Qual o nome do castelo da Disney?", "cinderela"),
("Quem é o herói com arco e flecha dos Vingadores?", "gaviao arqueiro"),
("Qual o nome da boneca do Toy Story?", "jessie"),
("Quem é o capitão dos Vingadores?", "capitao america"),
("Qual o nome do filme do robô gigante?", "transformers"),
("Quem é o rei dos monstros?", "godzilla"),
("Qual o nome do dinossauro verde do Mario?", "yoshi"),
("Quem é o herói de Wakanda?", "pantera negra"),
("Qual o nome do robô vilão de Transformers?", "megatron"),
("Quem é o vampiro clássico?", "dracula"),
("Qual o nome do super-herói com anel verde?", "lanterna verde"),
("Quem é o herói cego da Marvel?", "demolidor"),
("Qual o nome do vilão gelado do Batman?", "senhor frio"),
("Quem é o robô dourado do Star Wars?", "c3po"),
("Qual o nome da princesa sereia?", "ariel"),
("Quem é o herói com escudo de vibranium?", "capitao america"),
("Qual o nome do dragão de Mulan?", "mushu"),
("Quem é o vilão do Aladdin?", "jafar"),
("Qual o nome do monstro verde da Pixar?", "mike"),
("Quem é o herói da máscara preta?", "pantera negra"),
("Qual o nome do leão vilão do Rei Leão?", "scar"),
("Quem é o super-herói adolescente da Marvel?", "homem aranha"),
("Qual o nome do rato cozinheiro?", "remy"),
("Quem é o vilão do Thor?", "loki"),
("Qual o nome do super-herói com asas?", "falcao"),
("Quem é o herói com armadura dourada?", "homem de ferro"),
("Qual o nome do cachorro de Scooby-Doo?", "scooby"),
("Quem é o herói mais forte da Marvel?", "hulk"),
("Qual o nome do monstro do lago?", "ness"),
("Quem é o herói do anel mágico?", "lanterna verde"),
("Qual o nome do bruxo das trevas?", "voldemort"),
("Quem é o herói com traje vermelho da DC?", "flash"),
("Qual o nome do cavalo do Woody?", "bala no alvo"),
("Quem é o super-herói que vira formiga?", "homem formiga"),
("Qual o nome do vilão verde do Homem-Aranha?", "duende verde"),
("Quem é o herói das garras?", "wolverine"),
("Qual o nome do pokémon de fogo inicial?", "charmander"),
("Quem é o herói da capa preta?", "batman")
]
LISTA_PALAVRAS_RAPIDAS = [
"ABACAXI","MONSTRINHO","BATMAN","CSI","DRAGAO","AVENTURA","ESTRELA",
"FOGUETE","TROVAO","RELAMPAGO","MISTÉRIO","CAVERNA","FANTASMA",
"ZUMBI","ESQUELETO","CASTELO","PRINCESA","CAVALEIRO","ESPADA",
"ESCUDO","MAGIA","FEITICO","POCAO","VULCAO","NEVASCA","TEMPESTADE",
"METEORO","GALAXIA","PLANETA","COMETA","ASTEROIDE","NINJA",
"SAMURAI","ROBÔ","ANDROID","CYBORG","LASER","BOMBA","EXPLOSAO",
"TORNADO","FURACAO","TSUNAMI","LABIRINTO","TESOURO","MAPA",
"PIRATA","NAVIO","ANCORA","ILHA","SELVA","MACACO","TIGRE",
"LEOPARDO","PANTERA","COBRA","ESCORPIAO","ARANHA","FORMIGA",
"GIGANTE","MINIATURA","MISTERIOSO","SECRETO","OCULTO","SOMBRA",
"NOITE","LUAR","SOLAR","FUTURO","PASSADO","TEMPO","DIMENSAO",
"PORTAL","MAGICO","ENCANTADO","DOURADO","PRATEADO","CRISTAL",
"DIAMANTE","RUBI","SAFIRA","ESMERALDA","FANTASIA","HERÓI",
"VILAO","BATALHA","GUERRA","ARENA","CAMPEAO","TROFEU",
"MEDALHA","CORRIDA","VELOCIDADE","TURBO","MOTOR","ENGRENAGEM",
"CIRCUITO","ENERGIA","ELETRICO","PLASMA","NEON","PIXEL",
"AVATAR","QUEST","LEVEL","XP","BONUS","LOOT","RARE",
"EPICO","LENDARIO","MISTICO","ARCANO","RITUAL","TOTEM"
]
LISTA_EMOJIS_RAPIDOS = [
"🐸","🐲","🐢","🦖","🐍","🦎","🍀",
"🐶","🐱","🐭","🐹","🐰","🦊","🐻","🐼","🐨","🐯","🦁","🐮","🐷",
"🐸","🐵","🙈","🙉","🙊","🐔","🐧","🐦","🐤","🐣","🐥","🦆","🦅",
"🦉","🦇","🐺","🐗","🐴","🦄","🐝","🐛","🦋","🐌","🐞","🐜",
"🪲","🪳","🕷","🕸","涼","🐢","🐍","🦎","🦖","🦕",
"🐙","🦑","🦐","🦞","🦀","🐡","🐠","🐟","🐬","🐳","🐋","鯊",
"🐊","🐅","🐆","🦓","🦍","🦧","🐘","🦛","🦏","🐪","🐫","🦒",
"🦘","🦬","🐃","🐂","🐄","🐎","🐖","🐏","🐑","🦙","🐐",
"🦌","🐕","🐩","🦮","🐕‍🦺","🐈","🐓","🦃","🦚","🦜",
"🦢","🕊","🐇","🦝","🦨","🦡","🦫","🦦","🦥","🐁","🐀",
"🐿","🦔"
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

    await canal_rank.purge(limit=5)
    await canal_rank.send(embed=embed)

async def disparar_pergunta(guild):
    canal_geral = discord.utils.get(guild.text_channels, name=CANAL_GERAL)
    if not canal_geral: return

    # Sorteio do tipo de jogo (Adicionado ROLETA)
    tipo_evento = random.choice(["pergunta", "numero", "ppt", "cara_coroa", "dado", "palavra", "emoji", "roleta"])
    jogo_em_andamento["tipo"] = tipo_evento
    jogo_em_andamento["venceu"] = False
    jogo_em_andamento["participantes_tentaram"] = []

    embed = discord.Embed(color=0xADFF2F)
    embed.set_thumbnail(url=AVATAR_MONSTRINHO)

    if tipo_evento == "pergunta":
        pergunta, response_str = random.choice(LISTA_PERGUNTAS)
        jogo_em_andamento["pergunta"] = pergunta
        jogo_em_andamento["resposta"] = response_str.lower()
        embed.title = "🐲 HORA DO JOGUINHO DO MONSTRINHO! 🐲"
        embed.description = f"Oii amiguinhos! Vamos ver quem é esperto? ✨\n\n**PERGUNTA:**\n> {pergunta}\n\nO primeiro que acertar ganha **100 monstrinho-coins**! Boa sorte! 💚🐉"

    elif tipo_evento == "numero":
        res = random.randint(1, 50)
        jogo_em_andamento["resposta"] = str(res)
        embed.title = "🎯 Evento: Adivinhe o número!"
        embed.description = "Estou pensando em um número entre **1 e 50**.\n\nQuem acertar primeiro em até 5 minutos ganha!\n💰 **Prêmio:** 500 coins | ❌ **Erro:** -50 coins"
        embed.set_image(url=GIF_ADIVINHE_NUMERO)

    elif tipo_evento == "ppt":
        jogo_em_andamento["resposta"] = "logic_ppt"
        embed.title = "✊ Evento: Pedra, Papel ou Tesoura!"
        embed.description = "Digite: **pedra, papel ou tesoura**\n\nO primeiro que vencer o bot ganha!\n💰 **Prêmio:** 300 | ❌ **Perde:** 100 | 🤝 **Empate:** -50"
        embed.set_image(url=GIF_PPT)

    elif tipo_evento == "cara_coroa":
        jogo_em_andamento["resposta"] = random.choice(["cara", "coroa"])
        embed.title = "🪙 Evento: Cara ou Coroa!"
        embed.description = "Digite **cara** ou **coroa**\n\nO primeiro que acertar vence!\n💰 **Prêmio:** 300 | ❌ **Perde:** 150"
        embed.set_image(url=GIF_CARA_COROA)

    elif tipo_evento == "dado":
        jogo_em_andamento["resposta"] = str(random.randint(1, 6))
        embed.title = "🎲 Evento: Dado da sorte!"
        embed.description = "Digite um número de **1 a 6**\n\nQuem acertar o número sorteado vence!\n💰 **Prêmio:** 70 | ❌ **Perde:** 20"
        embed.set_image(url=GIF_DADO)

    elif tipo_evento == "palavra":
        palavra = random.choice(LISTA_PALAVRAS_RAPIDAS)
        jogo_em_andamento["resposta"] = palavra.lower()
        embed.title = "⚡ Evento rápido!"
        embed.description = f"Primeiro a digitar:\n**{palavra}**\n\nvence! Ganha **100 coins**"

    elif tipo_evento == "emoji":
        emoji = random.choice(LISTA_EMOJIS_RAPIDOS)
        jogo_em_andamento["resposta"] = emoji
        embed.title = "⚡ Evento de emoji!"
        embed.description = f"Primeiro a mandar:\n\n**{emoji}**\n\nvence! Ganha **100 coins**"

    elif tipo_evento == "roleta":
        jogo_em_andamento["resposta"] = "roleta"
        embed.title = "🎡 EVENTO: ROLETA DA SORTE!"
        embed.description = "O primeiro que escrever **ROLETA** vai girar e ver o que o destino reserva! 🐲✨\n\n🎁 **Prêmios possíveis:**\n• 1000 Coins (Raro!)\n• 100 ou 200 Coins\n• Outro Jogo Aleatório\n• Perder 200 Coins\n• ROUBAR 300 Coins de alguém!"
        embed.set_image(url=GIF_ROLETA_GIRANDO)

    embed.set_footer(text="Você tem 5 minutos! Responda aqui no chat!")
    await canal_geral.send(embed=embed)

    for _ in range(300): # 300 segundos = 5 min
        if jogo_em_andamento["venceu"]: break
        await asyncio.sleep(1)
    
    if not jogo_em_andamento["venceu"]:
        jogo_em_andamento["pergunta"] = None
        jogo_em_andamento["resposta"] = None
        await canal_geral.send("🥺 Ahhh poxa, ninguém acertou a tempo... O Monstrinho ficou triste, mas logo eu volto com outra! 🐲💔")

# ============== LOOP DO JOGO =================

@tasks.loop(hours=3)
async def loop_jogo_monstrinho():
    espera_extra = random.randint(0, 7200)
    await asyncio.sleep(espera_extra)
    
    for guild in bot.guilds:
        await disparar_pergunta(guild)

# ============== VIEWS =================

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

class ReivindicarCupidoView(discord.ui.View):
    def __init__(self, canal_ticket_id: int):
        super().__init__(timeout=None)
        self.canal_ticket_id = canal_ticket_id

    @discord.ui.button(label="🏹 Assumir Ticket", style=discord.ButtonStyle.danger, custom_id="reivindicar_cupido")
    async def reivindicar(self, interaction: discord.Interaction, button: discord.ui.Button):
        cargo_cupido = discord.utils.get(interaction.guild.roles, name=CARGO_CUPIDOS)
        eh_staff = any(role.name in CARGOS_IMUNES_NOMES for role in interaction.user.roles)
        
        if cargo_cupido not in interaction.user.roles and not eh_staff:
            return await interaction.response.send_message("❌ Apenas um Cupido ou Staff pode fazer isso! 🏹💘", ephemeral=True)

        canal_ticket = interaction.guild.get_channel(self.canal_ticket_id)
        if not canal_ticket:
            return await interaction.response.send_message("❌ Este ticket já foi fechado ou não existe mais.", ephemeral=True)

        await canal_ticket.set_permissions(interaction.user, view_channel=True, send_messages=True)
        
        embed_no_ticket = discord.Embed(
            description=f"🏹 **O Cupido {interaction.user.mention} preparou o arco e chegou para te ajudar com o amor!** 💘✨\n\nAguarde, o romance está no ar!",
            color=0xFF69B4
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
         import discord
from discord.ext import commands, tasks
import random
import asyncio
import os
from datetime import timedelta
from datetime import datetime

# ================= INTENTS =================
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
CANAL_CHAT_CUPIDOS = "💘・chat-cupidos"
CANAL_CHAT_STAFF_GERAL = "🔰・chat-staff"
CANAL_RANKING_MONSTRINHO = "ranking-monstrinho"

# GIFs e Imagens
BANNER_TICKET = "https://i.pinimg.com/originals/5d/92/5d/5d925dd101dba34f341148eace3cfe38.gif"
GIF_NAMORADOS = "https://i.pinimg.com/originals/f5/b8/44/f5b844675a7942e4180bb9960c3fe319.gif"
GIF_CATALOGO = "https://i.pinimg.com/originals/0a/1f/86/0a1f869c296b0c30454ffb56397b90fb.gif"
AVATAR_MONSTRINHO = "https://cdn.discordapp.com/attachments/1304658653697019964/1338274026333671485/monstrinho_avatar.png"
GIF_ACERTO_MONSTRINHO = "https://media.tenor.com/8yMrP1Cs7ykAAAAM/ninjala-ninjala-season6trailer.gif"

# NOVOS GIFS JOGOS
GIF_ADIVINHE_NUMERO = "https://pixmidia.com.br/wp-content/uploads/2020/08/alvo.gif"
GIF_PPT = "https://c.tenor.com/CACaU3WIOQYAAAAd/friends-monica-geller.gif"
GIF_CARA_COROA = "https://usagif.com/wp-content/uploads/gifs/coin-flip-18.gif"
GIF_DADO = "https://miro.medium.com/v2/resize:fit:1080/1*n4_Ic0t_s8YJN4YhHxb5xw.gif"
GIF_ROLETA_GIRANDO = "https://i.pinimg.com/originals/30/16/25/30162543258ca8058fe7bc4003be2a33.gif"
GIF_DERROTA = "https://i.pinimg.com/originals/ca/c9/81/cac9814161057dbc9bb2ae0ba0dbdfc0.gif"
GIF_BAU_COINS = "https://media.tenor.com/8yMrP1Cs7ykAAAAM/ninjala-ninjala-season6trailer.gif"

# Cargos
CARGO_MEMBRO_NOVO = "Membro Novo. 🦇"
CARGO_MEMBROS = "Membros. 🦇"
CARGO_MODERADOR = "Moderador. 🦇"
CARGO_RECRUTADOR = "Recrutador. 🦇"
CARGO_ANJO = "Anjo. 🦇"
CARGO_CUPIDOS = "Cupidos"
CARGO_STAFF_EQUIPE = "Equipe Staff. 🦇"

CARGOS_IMUNES_NOMES = ["Admin", "Moderador", "DIRETOR", "Admin. Bat", "Moderador. Bat", "DIRETOR. Bat", "Admin. 🦇", "Moderador. 🦇"]

# ============== DADOS =================
tickets = {}
avisos_usuarios = {} 
total_castigos_usuario = {}
pontuacao_monstrinho = {} 
jogo_em_andamento = {"tipo": None, "pergunta": None, "resposta": None, "venceu": False, "participantes_tentaram": []}

LISTA_PERGUNTAS = [
    ("Qual o nome do bruxo de Harry Potter?", "harry potter"), ("Qual herói usa escudo?", "capitao america"),
    ("Quem é o encanador da Nintendo?", "mario"), ("Qual é o planeta vermelho?", "marte"),
    ("Quem mora em uma casa no fundo do mar?", "bob esponja"), ("Qual o nome do rato da Disney?", "mickey"),
    ("Quem é o parceiro do Batman?", "robin"), ("Qual o nome do ogro verde?", "shrek"),
    ("Quem é o deus do trovão da Marvel?", "thor"), ("Qual o nome do robô do Star Wars que faz bip bip?", "r2d2"),
    ("Quem vive no abacaxi no fundo do mar?", "bob esponja"), ("Qual é o carro do Batman?", "batmovel"),
    ("Quem é o rival do Mario?", "bowser"), ("Qual herói é feito de ferro?", "homem de ferro"),
    ("Qual o nome do boneco do Toy Story?", "woody"), ("Quem é o vilão roxo da Marvel?", "thanos"),
    ("Qual o nome do leão da Disney?", "simba"), ("Qual herói solta teia?", "homem aranha"),
    ("Quem é o melhor amigo do Shrek?", "burro"), ("Qual o nome do ninja de laranja?", "naruto"),
    ("Quem é o treinador do Pikachu?", "ash"), ("Qual o nome do dragão de Como Treinar Seu Dragão?", "banguela"),
    ("Quem é o alienígena azul da Disney?", "stitch"), ("Qual o nome do palhaço do IT?", "pennywise"),
    ("Quem é o rei da selva?", "leao"), ("Qual o nome do filme dos dinossauros?", "jurassic park"),
    ("Quem é o herói de capa vermelha e azul?", "superman"), ("Qual o nome da princesa de gelo?", "elsa"),
    ("Quem vive com o Pateta?", "mickey"), ("Qual o nome do robô amarelo de Transformers?", "bumblebee"),
    ("Quem é o herói com garras de metal?", "wolverine"), ("Qual o nome do navio pirata do Jack Sparrow?", "perola negra"),
    ("Quem é o melhor amigo do Harry Potter?", "rony"), ("Qual o nome da escola de magia?", "hogwarts"),
    ("Quem é o deus da trapaça da Marvel?", "loki"), ("Qual o nome do pokémon elétrico?", "pikachu"),
    ("Quem é o cowboy do Toy Story?", "woody"), ("Qual o nome do peixe do filme Procurando Nemo?", "nemo"),
    ("Quem é o inimigo do Sonic?", "eggman"), ("Qual o nome da princesa da Bela e a Fera?", "bela"),
    ("Quem é o super-herói verde gigante?", "hulk"), ("Qual o nome do boneco espacial do Toy Story?", "buzz"),
    ("Quem é o mago de barba branca em Senhor dos Anéis?", "gandalf"), ("Qual o nome do dragão do filme Shrek?", "dragao"),
    ("Quem é o melhor amigo do Bob Esponja?", "patrick"), ("Qual o nome do gato preguiçoso dos quadrinhos?", "garfield"),
    ("Quem é o detetive amarelo da Disney?", "pikachu"), ("Qual o nome do monstro azul da Pixar?", "sulley"),
    ("Quem é o vilão do Batman com sorriso?", "coringa"), ("Qual o nome do filme do leãozinho da Disney?", "rei leao"),
    ("Quem é o herói do escudo vermelho e azul?", "capitao america"), ("Qual o nome do carro vermelho do filme Carros?", "relampago mcqueen"),
    ("Quem é o vilão do Homem-Aranha com tentáculos?", "doutor octopus"), ("Qual o nome da princesa da torre?", "rapunzel"),
    ("Quem é o herói com martelo?", "thor"), ("Qual o nome do robô do filme Wall-E?", "walle"),
    ("Quem é o melhor amigo do Naruto?", "sasuke"), ("Qual o nome do vilão do Rei Leão?", "scar"),
    ("Quem é o herói que corre rápido?", "flash"), ("Qual o nome do cachorro da família Simpson?", "ajudante de papai noel"),
    ("Quem é o vampiro famoso de Crepúsculo?", "edward"), ("Qual o nome do castelo da Disney?", "cinderela"),
    ("Quem é o herói com arco e flecha dos Vingadores?", "gaviao arqueiro"), ("Qual o nome da boneca do Toy Story?", "jessie"),
    ("Quem é o capitão dos Vingadores?", "capitao america"), ("Qual o nome do filme do robô gigante?", "transformers"),
    ("Quem é o rei dos monstros?", "godzilla"), ("Qual o nome do dinossauro verde do Mario?", "yoshi"),
    ("Quem é o herói de Wakanda?", "pantera negra"), ("Qual o nome do robô vilão de Transformers?", "megatron"),
    ("Quem é o vampiro clássico?", "dracula"), ("Qual o nome do super-herói com anel verde?", "lanterna verde"),
    ("Quem é o herói cego da Marvel?", "demolidor"), ("Qual o nome do vilão gelado do Batman?", "senhor frio"),
    ("Quem é o robô dourado do Star Wars?", "c3po"), ("Qual o nome da princesa sereia?", "ariel"),
    ("Quem é o herói com escudo de vibranium?", "capitao america"), ("Qual o nome do dragão de Mulan?", "mushu"),
    ("Quem é o vilão do Aladdin?", "jafar"), ("Qual o nome do monstro verde da Pixar?", "mike"),
    ("Quem é o herói da máscara preta?", "pantera negra"), ("Qual o nome do leão vilão do Rei Leão?", "scar"),
    ("Quem é o super-herói adolescente da Marvel?", "homem aranha"), ("Qual o nome do rato cozinheiro?", "remy"),
    ("Quem é o vilão do Thor?", "loki"), ("Qual o nome do super-herói com asas?", "falcao"),
    ("Quem é o herói com armadura dourada?", "homem de ferro"), ("Qual o nome do cachorro de Scooby-Doo?", "scooby"),
    ("Quem é o herói mais forte da Marvel?", "hulk"), ("Qual o nome do monstro do lago?", "ness"),
    ("Quem é o herói do anel mágico?", "lanterna verde"), ("Qual o nome do bruxo das trevas?", "voldemort"),
    ("Quem é o herói com traje vermelho da DC?", "flash"), ("Qual o nome do cavalo do Woody?", "bala no alvo"),
    ("Quem é o super-herói que vira formiga?", "homem formiga"), ("Qual o nome do vilão verde do Homem-Aranha?", "duende verde"),
    ("Quem é o herói das garras?", "wolverine"), ("Qual o nome do pokémon de fogo inicial?", "charmander"),
    ("Quem é o herói da capa preta?", "batman")
]

LISTA_PALAVRAS_RAPIDAS = [
"ABACAXI","MONSTRINHO","BATMAN","CSI","DRAGAO","AVENTURA","ESTRELA",
"FOGUETE","TROVAO","RELAMPAGO","MISTÉRIO","CAVERNA","FANTASMA",
"ZUMBI","ESQUELETO","CASTELO","PRINCESA","CAVALEIRO","ESPADA",
"ESCUDO","MAGIA","FEITICO","POCAO","VULCAO","NEVASCA","TEMPESTADE",
"METEORO","GALAXIA","PLANETA","COMETA","ASTEROIDE","NINJA",
"SAMURAI","ROBÔ","ANDROID","CYBORG","LASER","BOMBA","EXPLOSAO",
"TORNADO","FURACAO","TSUNAMI","LABIRINTO","TESOURO","MAPA",
"PIRATA","NAVIO","ANCORA","ILHA","SELVA","MACACO","TIGRE",
"LEOPARDO","PANTERA","COBRA","ESCORPIAO","ARANHA","FORMIGA",
"GIGANTE","MINIATURA","MISTERIOSO","SECRETO","OCULTO","SOMBRA",
"NOITE","LUAR","SOLAR","FUTURO","PASSADO","TEMPO","DIMENSAO",
"PORTAL","MAGICO","ENCANTADO","DOURADO","PRATEADO","CRISTAL",
"DIAMANTE","RUBI","SAFIRA","ESMERALDA","FANTASIA","HERÓI",
"VILAO","BATALHA","GUERRA","ARENA","CAMPEAO","TROFEU",
"MEDALHA","CORRIDA","VELOCIDADE","TURBO","MOTOR","ENGRENAGEM",
"CIRCUITO","ENERGIA","ELETRICO","PLASMA","NEON","PIXEL",
"AVATAR","QUEST","LEVEL","XP","BONUS","LOOT","RARE",
"EPICO","LENDARIO","MISTICO","ARCANO","RITUAL","TOTEM"
]

LISTA_EMOJIS_RAPIDOS = ["🐸","🐲","🐢","Rex","🐍","🦎","🍀","🐶","🐱","🐭","🐹","🐰","🦊","🐻","🐼","🐨","🐯","🦁","🐮","🐷","🐵","🐔","🐧","🐦","🐤","🐣","🐥","🦆","🦅","🦉","🦇","🐺","🐗","🐴","🦄","🐝","🐛","🦋","🐌","🐞","🐜","🐙","🦑","🦐","🦞","🦀","🐡","🐠","🐟","🐬","🐳","🐋","🐊","🐅","🐆","🦓","🦍","🐘","🦛","🦏","🦒","🦘","🐎","🐖","🐏","🐑","🐐","🦌","🐕","🐩","🐈","🐓","🦃","🦚","🦜","🦢","🕊","🐇","🦝"]

PALAVRAS_PROIBIDAS = ["porra", "caralho", "merda", "bosta", "puta", "puto", "vadia", "desgraça", "idiota", "burro", "imbecil", "otário", "retardado", "lixo", "nojento", "arrombado", "viado", "bicha", "piranha", "vai se fuder", "vai se foder", "vai tomar no cu", "tomar no cu", "filho da puta", "se mata", "se fode", "fdp", "vsf", "krl", "pqp", "prr", "tmnc", "buceta", "carai", "karalho"]

# ============== FUNÇÕES AUXILIARES =================

async def atualizar_ranking(guild):
    canal_rank = discord.utils.get(guild.text_channels, name=CANAL_RANKING_MONSTRINHO)
    if not canal_rank: return
    rank_ordenado = sorted(pontuacao_monstrinho.items(), key=lambda item: item[1], reverse=True)
    embed = discord.Embed(title="🏆 RANKING MONSTRINHO-COINS 🏆", description="Aqui estão os maiores gênios do nosso servidor! 🐲💚", color=0x00FF7F, timestamp=datetime.now())
    embed.set_thumbnail(url=AVATAR_MONSTRINHO)
    texto_rank = ""
    for i, (user_id, pontos) in enumerate(rank_ordenado[:15], 1):
        user = guild.get_member(user_id)
        nome = user.display_name if user else f"Usuário Desconhecido ({user_id})"
        texto_rank += f"**{i}º** | {nome} — `{pontos} Coins` 🐲\n"
    embed.description += f"\n\n{texto_rank if texto_rank else 'Ninguém pontuou ainda... 🥺'}"
    embed.set_footer(text="CSI - Sistema de Jogos")
    await canal_rank.purge(limit=5)
    await canal_rank.send(embed=embed)

async def disparar_pergunta(guild):
    canal_geral = discord.utils.get(guild.text_channels, name=CANAL_GERAL)
    if not canal_geral: return
    tipo_evento = random.choice(["pergunta", "numero", "ppt", "cara_coroa", "dado", "palavra", "emoji", "roleta"])
    jogo_em_andamento["tipo"] = tipo_evento
    jogo_em_andamento["venceu"] = False
    jogo_em_andamento["participantes_tentaram"] = []
    embed = discord.Embed(color=0xADFF2F).set_thumbnail(url=AVATAR_MONSTRINHO)

    if tipo_evento == "pergunta":
        pergunta, resp = random.choice(LISTA_PERGUNTAS)
        jogo_em_andamento["pergunta"], jogo_em_andamento["resposta"] = pergunta, resp.lower()
        embed.title = "🐲 HORA DO JOGUINHO!"
        embed.description = f"**PERGUNTA:**\n> {pergunta}\n\nO primeiro que acertar ganha **100 coins**!"
    elif tipo_evento == "numero":
        res = random.randint(1, 50)
        jogo_em_andamento["resposta"] = str(res)
        embed.title = "🎯 Adivinhe o número!"
        embed.description = "Número entre **1 e 50**.\nPrêmio: 500 coins | Erro: -50"
        embed.set_image(url=GIF_ADIVINHE_NUMERO)
    elif tipo_evento == "ppt":
        jogo_em_andamento["resposta"] = "logic_ppt"
        embed.title = "✊ Pedra, Papel ou Tesoura!"
        embed.description = "Digite: **pedra, papel ou tesoura**\nPrêmio: 300 | Perde: 100"
        embed.set_image(url=GIF_PPT)
    elif tipo_evento == "cara_coroa":
        jogo_em_andamento["resposta"] = random.choice(["cara", "coroa"])
        embed.title = "🪙 Cara ou Coroa!"
        embed.description = "Digite **cara** ou **coroa**\nPrêmio: 300 | Perde: 150"
        embed.set_image(url=GIF_CARA_COROA)
    elif tipo_evento == "dado":
        jogo_em_andamento["resposta"] = str(random.randint(1, 6))
        embed.title = "🎲 Dado da sorte!"
        embed.description = "Digite de **1 a 6**\nPrêmio: 70 | Perde: 20"
        embed.set_image(url=GIF_DADO)
    elif tipo_evento == "palavra":
        palavra = random.choice(LISTA_PALAVRAS_RAPIDAS)
        jogo_em_andamento["resposta"] = palavra.lower()
        embed.title = "⚡ Rápido!"
        embed.description = f"Digite: **{palavra}**"
    elif tipo_evento == "emoji":
        emoji = random.choice(LISTA_EMOJIS_RAPIDOS)
        jogo_em_andamento["resposta"] = emoji
        embed.title = "⚡ Emoji!"
        embed.description = f"Mande: **{emoji}**"
    elif tipo_evento == "roleta":
        jogo_em_andamento["resposta"] = "roleta"
        embed.title = "🎡 ROLETA DA SORTE!"
        embed.description = "O primeiro que escrever **ROLETA** vai girar!\nPrêmios: 1000 Coins (Raro), Roubo, Perda..."
        embed.set_image(url=GIF_ROLETA_GIRANDO)

    embed.set_footer(text="Você tem 5 minutos!")
    await canal_geral.send(embed=embed)
    for _ in range(300):
        if jogo_em_andamento["venceu"]: break
        await asyncio.sleep(1)
    if not jogo_em_andamento["venceu"]:
        jogo_em_andamento["resposta"] = None
        await canal_geral.send("🥺 Ninguém acertou a tempo... O Monstrinho ficou triste! 🐲💔")

# ============== VIEWS =================

class LiberarCastigoView(discord.ui.View):
    def __init__(self, membro_id: int):
        super().__init__(timeout=None)
        self.membro_id = membro_id
    @discord.ui.button(label="🔓 Remover Castigo", style=discord.ButtonStyle.success, custom_id="remover_castigo")
    async def remover(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.moderate_members:
            return await interaction.response.send_message("❌ Só staff!", ephemeral=True)
        membro = interaction.guild.get_member(self.membro_id)
        if membro:
            await membro.timeout(None)
            avisos_usuarios[self.membro_id] = 0
            await interaction.response.send_message(f"✅ Castigo removido!", ephemeral=True)

class AprovarMembroView(discord.ui.View):
    def __init__(self, membro_id: int):
        super().__init__(timeout=None)
        self.membro_id = membro_id
    @discord.ui.button(label="✅ Liberar", style=discord.ButtonStyle.success)
    async def liberar(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        membro = guild.get_member(self.membro_id)
        if membro:
            c1 = discord.utils.get(guild.roles, name=CARGO_MEMBRO_NOVO)
            c2 = discord.utils.get(guild.roles, name=CARGO_MEMBROS)
            if c1: await membro.add_roles(c1)
            if c2: await membro.add_roles(c2)
            await interaction.response.send_message("✅ Aprovado!", ephemeral=True)

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
    @discord.ui.button(label="🤝 Assumir Chamado", style=discord.ButtonStyle.success)
    async def reivindicar(self, interaction: discord.Interaction, button: discord.ui.Button):
        canal = interaction.guild.get_channel(self.canal_ticket_id)
        await canal.set_permissions(interaction.user, view_channel=True, send_messages=True)
        await canal.send(f"✨ O Anjo {interaction.user.mention} chegou!")
        button.disabled = True
        await interaction.response.edit_message(view=self)

class ReivindicarCupidoView(discord.ui.View):
    def __init__(self, canal_ticket_id: int):
        super().__init__(timeout=None)
        self.canal_ticket_id = canal_ticket_id
    @discord.ui.button(label="🏹 Assumir Ticket", style=discord.ButtonStyle.danger)
    async def reivindicar(self, interaction: discord.Interaction, button: discord.ui.Button):
        canal = interaction.guild.get_channel(self.canal_ticket_id)
        await canal.set_permissions(interaction.user, view_channel=True, send_messages=True)
        await canal.send(f"🏹 O Cupido {interaction.user.mention} chegou!")
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
        super().__init__(placeholder="🎟️ Selecione o tipo de ticket", options=options, custom_id="ticket_select_menu")

    async def callback(self, interaction: discord.Interaction):
        guild, user, tipo = interaction.guild, interaction.user, self.values[0]
        overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=False), user: discord.PermissionOverwrite(view_channel=True, send_messages=True)}
        
        pref = "👼┃" if tipo == "anjos" else "💘┃" if tipo == "namorados" else "🎟️┃"
        canal = await guild.create_text_channel(name=f"{pref}{tipo}-{user.name}".lower(), overwrites=overwrites)
        tickets[canal.id] = {"user": user.id, "tipo": tipo}

        if tipo == "anjos":
            await canal.send(f"✨ {user.mention}, um anjinho logo vem!", view=FecharTicketView())
            log = discord.utils.get(guild.text_channels, name=CANAL_CHAT_ANJO)
            if log: await log.send(f"🪽 Novo chamado: {canal.mention}", view=ReivindicarAnjoView(canal.id))
        elif tipo == "namorados":
            embed = discord.Embed(title="💘 NAMORADOS", color=0xFF69B4).set_image(url=GIF_NAMORADOS)
            await canal.send(embed=embed, view=FecharTicketView())
            log = discord.utils.get(guild.text_channels, name=CANAL_CHAT_CUPIDOS)
            if log: await log.send(f"🏹 Cupido necessário: {canal.mention}", view=ReivindicarCupidoView(canal.id))
        elif tipo == "catalogo":
            await canal.send(f"📸 {user.mention}, envie **APENAS A FOTO**.")
        else:
            await canal.send(f"🎟️ Ticket de {tipo} aberto!", view=FecharTicketView())
        
        await interaction.response.send_message("✅ Ticket criado!", ephemeral=True)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

# ============== EVENTOS E COMANDOS =================

@bot.event
async def on_ready():
    print(f"🐲 {bot.user} online!")
    bot.add_view(TicketView())
    bot.add_view(FecharTicketView())
    bot.add_view(LiberarCastigoView(0))
    if not loop_jogo_monstrinho.is_running(): loop_jogo_monstrinho.start()

@bot.command()
async def jogo(ctx):
    if ctx.author.id == DONO_ID: await disparar_pergunta(ctx.guild)

@bot.command()
async def roleta(ctx):
    if ctx.author.id == DONO_ID: 
        jogo_em_andamento["tipo"] = "roleta"
        jogo_em_andamento["resposta"] = "roleta"
        await ctx.send("🎡 Roleta forçada!")

@bot.event
async def on_message(message):
    if message.author.bot: return

    # JOGOS
    if jogo_em_andamento["resposta"] and message.channel.name == CANAL_GERAL:
        uid, msg = message.author.id, message.content.lower().strip()
        tipo = jogo_em_andamento["tipo"]
        
        if tipo == "roleta" and msg == "roleta":
            jogo_em_andamento["venceu"] = True
            jogo_em_andamento["resposta"] = None
            # ROLETA CHANCE 1% PARA 1000
            res = random.choices(["1000", "100", "200", "perder", "jogo", "roubar"], weights=[0.01, 0.39, 0.20, 0.15, 0.10, 0.15])[0]
            
            if res == "1000":
                pontuacao_monstrinho[uid] = pontuacao_monstrinho.get(uid, 0) + 1000
                emb = discord.Embed(title="💎 SURREAL!", description=f"{message.author.mention} ganhou 1000 coins!", color=0x00FFFF).set_image(url=GIF_BAU_COINS)
                await message.reply(embed=emb)
            elif res == "roubar":
                await message.reply("🥷 Mencione alguém para roubar 300 coins em 30s!")
                def check(m): return m.author == message.author and m.mentions
                try:
                    m2 = await bot.wait_for("message", check=check, timeout=30)
                    alvo = m2.mentions[0]
                    if random.choice([True, False]):
                        pontuacao_monstrinho[uid] = pontuacao_monstrinho.get(uid, 0) + 300
                        pontuacao_monstrinho[alvo.id] = pontuacao_monstrinho.get(alvo.id, 0) - 300
                        await message.channel.send(f"💰 Roubou o {alvo.mention}!")
                    else:
                        pontuacao_monstrinho[uid] = pontuacao_monstrinho.get(uid, 0) - 300
                        await message.channel.send("❌ Falhou e pagou multa!")
                except: await message.channel.send("⏰ Tempo esgotado.")
            # ... (Lógica simplificada dos outros resultados)
            await atualizar_ranking(message.guild)
            return

        elif msg == jogo_em_andamento["resposta"]:
            jogo_em_andamento["venceu"] = True
            jogo_em_andamento["resposta"] = None
            pontuacao_monstrinho[uid] = pontuacao_monstrinho.get(uid, 0) + 100
            emb = discord.Embed(title="🎉 ACERTOU!", color=0x00FF7F).set_image(url=GIF_ACERTO_MONSTRINHO)
            await message.reply(embed=emb)
            await atualizar_ranking(message.guild)

    # CATALOGO
    if message.channel.id in tickets:
        if tickets[message.channel.id]["tipo"] == "catalogo" and message.attachments:
            c = discord.utils.get(message.guild.text_channels, name=CANAL_EVENTO_CATALOGO)
            if c: await c.send(f"📸 De {message.author.mention}", file=await message.attachments[0].to_file())
            await message.channel.delete()
            return

    # PALAVRAS PROIBIDAS
    if not any(r.name in CARGOS_IMUNES_NOMES for r in message.author.roles) and message.channel.name != CANAL_DESABAFOS:
        if any(p in message.content.lower() for p in PALAVRAS_PROIBIDAS):
            await message.delete()
            avisos_usuarios[message.author.id] = avisos_usuarios.get(message.author.id, 0) + 1
            if avisos_usuarios[message.author.id] >= 4:
                await message.author.timeout(timedelta(days=1))
                avisos_usuarios[message.author.id] = 0
                await message.channel.send(f"🚨 {message.author.mention} castigado!")

    await bot.process_commands(message)

@tasks.loop(hours=3)
async def loop_jogo_monstrinho():
    await asyncio.sleep(random.randint(0, 7200))
    for g in bot.guilds: await disparar_pergunta(g)

bot.run(TOKEN)
