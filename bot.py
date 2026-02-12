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
CANAL_LOG = "❌-palavras-apagadas-bot"
CANAL_TICKET = "🎟️・𝑻𝒊𝒄𝒌𝒆𝒕"
CANAL_EVENTO_CATALOGO = "evento-catalogo"
CANAL_ADVERTENCIAS = "⚠️・advertências" 
CANAL_DESABAFOS = "😮‍💨・desabafos"
CANAL_CHAT_ANJO = "🪽・chat-anjo"
CANAL_CHAT_CUPIDOS = "💘・chat-cupidos"
CANAL_CHAT_STAFF_GERAL = "🔰・chat-staff"
CANAL_RANKING_MONSTRINHO = "🎰・ranking-monstrinho"
CANAL_LOJA_INFO = "💾・loja-monstrinho"
CANAL_DIRECAO = "👑・chat-direção"
CANAL_ATENCAO_STAFF = "⚠️・atenção" # Canal de monitoramento silencioso

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
GIF_CAIXA_MISTERIOSA = "https://i.pinimg.com/originals/c8/54/2e/c8542e778641a29792671e6261541b63.gif"
GIF_EMBARALHADO = "https://media.tenor.com/8yMrP1Cs7ykAAAAM/ninjala-ninjala-season6trailer.gif"
GIF_SILENCIOSO = "https://media.tenor.com/On79Z_Gv08AAAAAd/shhh-quiet.gif"
GIF_BAU_PERDIDO = "https://i.pinimg.com/originals/e1/9b/6c/e19b6c086780963331a90623a6774900.gif"
GIF_MIMICO = "https://media0.giphy.com/media/v1.Y2lkPTZjMDliOTUyZnB0Y3pwdG1xMmp4YnlvaGJsZDIxb2prZnJnOHB4cmlzaGRzZzNlbCZlcD12MV9naWZzX3NlYXJjaCZjdD1n/shkh5vfrJ56BAoeWqt/200w.gif"

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

# ================= MONITORAMENTO BEM-ESTAR =================

contador_atencao = {}

GATILHOS_AJUDA = [
    "triste", "tristeza", "sozinho", "sozinha", "solidão", "vazio", "vazia", "cansado", "cansada", "desanimado", "desanimada", 
    "derrotado", "derrotada", "inútil", "inutil", "fracasso", "deprimido", "deprimida", "depressivo", "depressiva", "sem esperança", 
    "sem sentido", "acabado", "acabada", "destruído", "destruida", "quebrado", "quebrada", "perdido", "perdida", "infeliz", 
    "angustiado", "angustiada", "abatido", "abatida", "desolado", "desolada", "miserável", "miseravel", "patético", "patetico", 
    "horrível", "horrivel", "péssimo", "pessimo", "terrível", "terrivel", "podre", "ruim", "horrendo", "horrenda", "fracassado", 
    "fracassada", "ninguém liga", "ninguém se importa", "não sirvo pra nada", "não presto", "não valho nada", "sou inútil", 
    "sou um lixo", "sou um fracasso", "me odeio", "odeio minha vida", "odeio tudo", "ninguém gosta de mim", "ninguém me ama", 
    "sou um peso", "sou um problema", "só atrapalho", "sou descartável", "queria sumir", "queria desaparecer", "queria não existir", 
    "queria dormir e não acordar", "não faço falta", "ninguém sentiria minha falta", "minha vida é inútil", "minha vida não presta", 
    "minha vida não tem sentido", "vida sem sentido", "tudo dá errado", "nada presta", "nada importa", "nada vale a pena", 
    "não vale a pena viver", "não vale a pena", "cansei de tudo", "cansado de tudo", "cansada de tudo", "não aguento", 
    "não aguento mais", "não suporto mais", "não tenho forças", "sem forças", "sem energia", "esgotado", "esgotada", "exausto", 
    "exausta", "desespero", "desesperado", "desesperada", "agonia", "dor", "sofrimento", "sofrer", "sofrendo", "angústia", 
    "angustia", "tormento", "inferno", "colapso", "quero morrer", "queria morrer", "vou morrer", "vou me matar", "vou me suicidar", 
    "me matar", "me suicidar", "suicídio", "suicidio", "suicidar", "acabar com tudo", "acabar com a minha vida", "sumir pra sempre", 
    "desaparecer pra sempre", "não quero viver", "não quero mais viver", "prefiro morrer", "queria estar morto", "queria estar morta", 
    "melhor morto", "melhor morta", "adeus para sempre", "adeus mundo", "última mensagem", "último adeus", "fim de tudo", 
    "fim da minha vida", "vou partir", "vou embora pra sempre", "não volto mais", "ninguém vai sentir falta", "ninguém se importaria", 
    "ninguém notaria", "não faço diferença", "não tenho valor", "sou insignificante", "sou ninguém", "sou nada", "não sou nada", 
    "sou um erro", "sou um problema", "tudo é culpa minha", "a culpa é minha", "estraguei tudo", "não tem solução", "não tem saída", 
    "sem saída", "sem futuro", "sem motivo pra viver", "perdi tudo", "perdi a vontade", "perdi a esperança", "desistir", "desisto", 
    "vou desistir", "desistindo", "sem vontade de viver", "vontade de morrer", "querendo morrer"
]

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Lógica do mecanismo de ajuda (Canal ⚠️・atenção)
    msg_lower = message.content.lower()
    if any(palavra in msg_lower for palavra in GATILHOS_AJUDA):
        canal_atencao = discord.utils.get(message.guild.channels, name=CANAL_ATENCAO_STAFF)
        
        if canal_atencao:
            user_id = message.author.id
            contador_atencao[user_id] = contador_atencao.get(user_id, 0) + 1
            contagem = contador_atencao[user_id]
            
            ficha = (
                f"**Nome:** {message.author.name}\n"
                f"**Canal:** {message.channel.mention}\n"
                f"**Mensagem:** {message.content}\n"
                f"**Contador:** {contagem}/3"
            )
            
            if contagem >= 3:
                await canal_atencao.send(f"🚨 **SITUAÇÃO CRÍTICA** - @Equipe Staff. :bat:\n{ficha}")
            else:
                await canal_atencao.send(f"⚠️ **Novo Registro:**\n{ficha}")

    # Processa os demais comandos do bot
    await bot.process_commands(message)

# ================= FIM DA PRIMEIRA PARTE =================
# ============== DADOS =================

tickets = {}
avisos_usuarios = {} 
total_castigos_usuario = {} # Contador de castigos total
pontuacao_monstrinho = {} # Guardar os pontos
jogo_em_andamento = {"tipo": None, "pergunta": None, "resposta": None, "venceu": False, "participantes_tentaram": []}

# Lógica Evento Silencioso
contador_mensagens_silencioso = 0
meta_mensagens_silencioso = 0
evento_silencioso_ativo = False

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
("Quem é o rei dos monsters?", "godzilla"),
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
("Qual o nome do super-herói com acrobatas?", "falcao"),
("Quem é o herói com armadura dourada?", "homem de ferro"),
("Qual o nome do cachorro de Scooby-Doo?", "scooby"),
("Quem é o herói mais forte da Marvel?", "hulk"),
("Qual o nome do monstro do lago?", "ness"),
("Quem é o herói do anel mágico?", "lanterna verde"),
("Qual o nome do bruxo das trevas?", "voldemort"),
("Quem é o herói com traje vermelho da DC?", "flash"),
("Qual o nome do cavalo do Woody?", "bala no alvo"),
("Quem é o super-herói que vira formiga?", "homem ant-man"),
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
"🐸","🐲","🐢","REX","🐍","🦎","🍀",
"🐶","🐱","🐭","🐹","🐰","🦊","🐻","🐼","🐨","🐯","🦁","🐮","🐷",
"🐸","🐵","🙈","🙉","🙊","🐔","🐧","🐦","🐤","🐣","🐥","🦆","🦅",
"🦉","BAT","🐺","🐗","🐴","🦄","🐝","🐛","🦋","🐌","🐞","🐜",
"🪲","🪳","🕷","🕸","涼","🐢","🐍","🦎","REX","🦕",
"🐙","🦑","🦐","🦞","🦀","🐡","🐠","🐟","🐬","🐳","🐋","鯊",
"🐊","🐅","🐆","🦓","🦍","🦧","🐘","🦛","🦏","🐪","🐫","🦒",
"🦘","🦬","🐃","🐂","🐄","🐎","🐖","🐏","🐑","🦙","🐐",
"🦌","🐕","🐩","🦮","🐕‍🦺","🐈","🐓","🦃","🦚","🦜",
"Swan","Dove","Rabbit","Raccoon","Skunk","Badger","Beaver","Otter","Sloth","Mouse","Rat",
"Squirrel","Hedgehog"
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

async def disparar_roleta(guild):
    canal_geral = discord.utils.get(guild.text_channels, name=CANAL_GERAL)
    if not canal_geral: return

    jogo_em_andamento["tipo"] = "roleta"
    jogo_em_andamento["venceu"] = False # Na roleta, 'venceu' agora significa 'tempo acabou'
    jogo_em_andamento["participantes_tentaram"] = []
    jogo_em_andamento["resposta"] = "roleta"

    embed = discord.Embed(color=0xADFF2F)
    embed.set_thumbnail(url=AVATAR_MONSTRINHO)
    embed.title = "🎡 EVENTO: ROLETA DA SORTE COLETIVA!"
    embed.description = "A roleta está girando para TODOS! ✨🐲\n\nQuem escrever **ROLETA** vai girar uma vez e ganhar seu prêmio individual!\n\n🎁 **Prêmios possíveis:**\n• 500 Coins (Raro!)\n• 50 ou 100 Coins\n• Outro Jogo Aleatório\n• Perder 100 Coins\n• DOBRAR SEUS PONTOS (Chance Aumentada!)"
    embed.set_image(url=GIF_ROLETA_GIRANDO)
    embed.set_footer(text="A roleta ficará aberta por 5 minutos! Digite ROLETA para participar!")
    
    await canal_geral.send(embed=embed)

    await asyncio.sleep(300) # Mantém aberta por 5 minutos
    
    jogo_em_andamento["venceu"] = True
    jogo_em_andamento["resposta"] = None
    await canal_geral.send("🎡 A roleta parou de girar! O tempo acabou. 🐲🏁")

async def disparar_pergunta(guild, tipo_escolhido=None):
    canal_geral = discord.utils.get(guild.text_channels, name=CANAL_GERAL)
    if not canal_geral: return

    # Sorteio do tipo de jogo ou uso do tipo escolhido
    tipo_evento = tipo_escolhido if tipo_escolhido else random.choice(["pergunta", "numero", "ppt", "cara_coroa", "dado", "palavra", "emoji", "roleta", "embaralhada", "caixa", "silencioso", "bauperdido"])
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
        embed.description = f"Oii amiguinhos! Vamos ver quem é esperto? ✨\n\n**PERGUNTA:**\n> {pergunta}\n\nO primeiro que acertar ganha **50 monstrinho-coins**! Boa sorte! 💚🐉"

    elif tipo_evento == "numero":
        res = random.randint(1, 50)
        jogo_em_andamento["resposta"] = str(res)
        embed.title = "🎯 Evento: Adivinhe o número!"
        embed.description = "Estou pensando em um número entre **1 e 50**.\n\nQuem acertar primeiro em até 5 minutos ganha!\n💰 **Prêmio:** 500 coins | ❌ **Erro:** -25 coins"
        embed.set_image(url=GIF_ADIVINHE_NUMERO)

    elif tipo_evento == "ppt":
        jogo_em_andamento["resposta"] = "logic_ppt"
        embed.title = "✊ Evento: Pedra, Papel ou Tesoura!"
        embed.description = "Digite: **pedra, papel ou tesoura**\n\nO primeiro que vencer o bot ganha!\n💰 **Prêmio:** 150 | ❌ **Perde:** 50 | 🤝 **Empate:** -25"
        embed.set_image(url=GIF_PPT)

    elif tipo_evento == "cara_coroa":
        jogo_em_andamento["resposta"] = random.choice(["cara", "coroa"])
        embed.title = "🪙 Evento: Cara ou Coroa!"
        embed.description = "Digite **cara** ou **coroa**\n\nO primeiro que acertar vence!\n💰 **Prêmio:** 150 | ❌ **Perde:** 75"
        embed.set_image(url=GIF_CARA_COROA)

    elif tipo_evento == "dado":
        jogo_em_andamento["resposta"] = str(random.randint(1, 6))
        embed.title = "🎲 Evento: Dado da sorte!"
        embed.description = "Digite um número de **1 a 6**\n\nQuem acertar o número sorteado vence!\n💰 **Prêmio:** 35 | ❌ **Perde:** 10"
        embed.set_image(url=GIF_DADO)

    elif tipo_evento == "palavra":
        palavra = random.choice(LISTA_PALAVRAS_RAPIDAS)
        jogo_em_andamento["resposta"] = palavra.lower()
        embed.title = "⚡ Evento rápido!"
        embed.description = f"Primeiro a digitar:\n**{palavra}**\n\nvence! Ganha **50 coins**"

    elif tipo_evento == "emoji":
        emoji = random.choice(LISTA_EMOJIS_RAPIDOS)
        jogo_em_andamento["resposta"] = emoji
        embed.title = "⚡ Evento de emoji!"
        embed.description = f"Primeiro a mandar:\n\n**{emoji}**\n\nvence! Ganha **50 coins**"

    elif tipo_evento == "roleta":
        await disparar_roleta(guild)
        return

    elif tipo_evento == "embaralhada":
        palavra = random.choice(LISTA_PALAVRAS_RAPIDAS)
        jogo_em_andamento["resposta"] = word.lower()
        lista_letras = list(palavra)
        random.shuffle(lista_letras)
        palavra_shuffled = "".join(lista_letras)
        embed.title = "2️⃣ Palavra Embaralhada"
        embed.description = f"🔤 **Desembaralhe a palavra:**\n> **{palavra_shuffled}**\n\n💰 **Prêmio:** 100 coins | ❌ **Erro:** -25"
        embed.set_image(url=GIF_EMBARALHADO)

    elif tipo_evento == "caixa":
        jogo_em_andamento["resposta"] = "caixa"
        embed.title = "8️⃣ Caixa Misteriosa"
        embed.description = "📦 **Escolha um número: 1, 2 ou 3**\n\nO primeiro que digitar um número abre a caixa! O que será que tem dentro? 🐲✨\n\n🎁 **Possibilidades:**\n• Doar coins ou ganhar 50\n• Prêmio Raro (300 coins)\n• Perder 50 coins"
        embed.set_image(url=GIF_CAIXA_MISTERIOSA)

    elif tipo_evento == "bauperdido":
        jogo_em_andamento["resposta"] = "abrir"
        embed.title = "🏴‍☠️ EVENTO: O BAÚ PERDIDO!"
        embed.description = "Um baú antigo apareceu no chat! Quem será o primeiro a abrir? 🐲✨\n\nDigite **ABRIR** para tentar a sorte!\n\n💰 **Prêmio:** 200 Coins\n💀 **Cuidado:** Pode ser um Mímico e você perder 100 coins!"
        embed.set_image(url=GIF_BAU_PERDIDO)

    elif tipo_evento == "silencioso":
        global contador_mensagens_silencioso, meta_mensagens_silencioso, evento_silencioso_ativo
        contador_mensagens_silencioso = 0
        meta_mensagens_silencioso = random.randint(1, 20)
        evento_silencioso_ativo = True
        jogo_em_andamento["venceu"] = False # Controlado pela on_message
        
        embed.title = "🤫 EVENTO SILENCIOSO ATIVADO!"
        embed.description = "O Monstrinho escolher um **número secreto de mensagens**!\n\nQuem enviar a mensagem da sorte ganha o prêmio!\n\n💰 **Prêmio:** 400 Coins\n📝 **Dica:** O número está entre 1 e 20!"
        embed.set_image(url=GIF_SILENCIOSO)
        await canal_geral.send(embed=embed)
        return # Sai da função pois a on_message cuida do resto

    embed.set_footer(text="Você tem 5 minutos! Responda aqui no chat!")
    await canal_geral.send(embed=embed)

    for _ in range(300): # 300 segundos = 5 min
        if jogo_em_andamento["venceu"]: break
        await asyncio.sleep(1)
    
    if not jogo_em_andamento["venceu"]:
        jogo_em_andamento["pergunta"] = None
        jogo_em_andamento["resposta"] = None
        await canal_geral.send("🥺 Ahhh poxa, ninguém acertou a tempo... O Monstrinho queria muito te dar um prêmio! 🐲💔")

# ============== LOOP DO JOGO =================

@tasks.loop(minutes=30)
async def loop_jogo_monstrinho():
    espera_extra = random.randint(0, 300) # Pequeno atraso aleatório para não ser fixo no segundo
    await asyncio.sleep(espera_extra)
    
    for guild in bot.guilds:
        await disparar_pergunta(guild)

# ============== SISTEMA DE LOJA =================

PRECOS_LOJA = {
    "cargo_7dias": 5000,
    "cargo_colorido": 8000,
    "evento_oficial": 12000,
    "dar_apelido": 6000,
    "item_jogo": 15000,
    "robux": 30000,
    "nitro": 90000
}

class LojaSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Cargo Exclusivo (7 dias)", value="cargo_7dias", description="🏷️ 5.000 Coins"),
            discord.SelectOption(label="Cargo Colorido Personalizado", value="cargo_colorido", description="🏷️ 8.000 Coins"),
            discord.SelectOption(label="Criar Evento Oficial", value="evento_oficial", description="🎉 12.000 Coins"),
            discord.SelectOption(label="Dar Apelido em Alguém", value="dar_apelido", description="🎉 6.000 Coins"),
            discord.SelectOption(label="Item de Jogo", value="item_jogo", description="🎮 15.000 Coins"),
            discord.SelectOption(label="Robux", value="robux", description="🎮 30.000 Coins"),
            discord.SelectOption(label="Discord Nitro (1 mês)", value="nitro", description="🎮 90.000 Coins"),
        ]
        super().__init__(placeholder="🎁 Escolha seu prêmio aqui...", options=options, custom_id="loja_select")

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        item = self.values[0]
        custo = PRECOS_LOJA[item]
        saldo = pontuacao_monstrinho.get(user_id, 0)

        if saldo < custo:
            embed_erro = discord.Embed(
                description=f"🥺 Oh, meu bem... você ainda não tem coins suficientes para esse prêmio! 🐲💔\n\nVocê tem: `{saldo} Coins` | Precisa de: `{custo} Coins`",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed_erro, ephemeral=True)

        # Processar Compra
        pontuacao_monstrinho[user_id] -= custo
        await atualizar_ranking(interaction.guild)

        embed_sucesso = discord.Embed(
            title="🎁 RESGATE REALIZADO! 🐲💚",
            description=f"AAAA que felicidade, {interaction.user.mention}! ✨\n\nVocê resgatou: **{item.replace('_', ' ').title()}**!\n\nAgora é só aguardar um pouquinho que a staff já foi avisada e vai cuidar de tudo para você! Seu saldo foi atualizado. 🐲💖",
            color=0x00FF7F
        )
        await interaction.response.send_message(embed=embed_sucesso, ephemeral=True)

        # Notificar Direção (SEM MENSAGEM DE EVERYONE)
        canal_dir = discord.utils.get(interaction.guild.text_channels, name=CANAL_DIRECAO)
        if canal_dir:
            embed_staff = discord.Embed(
                title="🛍️ NOVA COMPRA NA LOJA",
                description=f"👤 **Membro:** {interaction.user.mention} ({interaction.user.id})\n🎁 **Item:** {item.replace('_', ' ').title()}\n💰 **Custo:** {custo} Coins",
                color=0xFFD700,
                timestamp=datetime.now()
            )
            await canal_dir.send(embed=embed_staff)

class LojaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(LojaSelect())

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
        # Verifica se é canal de Anjo
        if interaction.channel.name.startswith("👼┃anjos"):
            cargo_anjo = discord.utils.get(interaction.guild.roles, name=CARGO_ANJO)
            eh_staff = any(role.name in CARGOS_IMUNES_NOMES for role in interaction.user.roles)
            if (cargo_anjo not in interaction.user.roles) and not eh_staff:
                return await interaction.response.send_message("❌ Apenas os Anjos ou a Staff podem fechar este canal de acolhimento! 🪽", ephemeral=True)
        
        await interaction.response.send_message("🔒 Fechando este ticket em 5 segundinhos... tchau tchau! 🐲💚", ephemeral=True)
        await asyncio.sleep(5)
        await interaction.channel.delete()

class ReivindicarAnjoView(discord.ui.View):
    def __init__(self, canal_ticket_id: int):
        super().__init__(timeout=None)
        self.canal_ticket_id = canal_ticket_id

    @discord.ui.button(label="🤝 Assumir Chamado", style=discord.ButtonStyle.success, custom_id="reivindicar_anjo")
    async def reivindicar(self, interaction: discord.Interaction, button: discord.ui.Button):
        cargo_anjo = discord.utils.get(interaction.user.guild.roles, name=CARGO_ANJO)
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
        cargo_cupido = discord.utils.get(interaction.user.guild.roles, name=CARGO_CUPIDOS)
        eh_staff = any(role.name in CARGOS_IMUNES_NOMES for role in interaction.user.roles)
        
        if cargo_cupido not in interaction.user.roles and not eh_staff:
            return await interaction.response.send_message("❌ Apenas um Cupido ou Staff pode fazer isso! 🏹💘", ephemeral=True)

        canal_ticket = interaction.guild.get_channel(self.canal_ticket_id)
        if not canal_ticket:
            return await interaction.response.send_message("❌ Este ticket já foi fechado ou não existe mais.", ephemeral=True)

        await canal_ticket.set_permissions(interaction.user, view_channel=True, send_messages=True)
        
        embed_no_ticket = discord.Embed(
            description=f"🏹 **O Cupido {interaction.user.mention} preparou o arco e chegou para te ajudar com o amor!** 💘✨\n\nAguarde, o romance está no ar!",
            color=0xFF1493
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
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        if tipo != "anjos" and tipo != "namorados":
            cargo_mod = discord.utils.get(guild.roles, name=CARGO_MODERADOR)
            if cargo_mod:
                overwrites[cargo_mod] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        categoria = interaction.channel.category
        pref = "👼┃" if tipo == "anjos" else "💘┃" if tipo == "namorados" else "🎟️┃"
        canal = await guild.create_text_channel(
            name=f"{pref}{tipo}-{user.name}".lower(),
            category=categoria,
            overwrites=overwrites
        )

        tickets[canal.id] = {"user": user.id, "tipo": tipo}

        if tipo == "anjos":
            embed_user = discord.Embed(
                description=f"✨ **Segura o coração, {user.mention}!** ✨\n\nUm anjinho já foi avisado e logo ele vai aparecer aqui para te dar todo o carinho do mundo! 🪽💚",
                color=0xFFB6C1
            )
            await canal.send(embed=embed_user, view=FecharTicketView())
            
            canal_anjo_logs = discord.utils.get(guild.text_channels, name=CANAL_CHAT_ANJO)
            if canal_anjo_logs:
                cargo_anjo_mencao = discord.utils.get(guild.roles, name=CARGO_ANJO)
                embed_anjo = discord.Embed(
                    title="🪽 Alerta de Proteção Angelical!",
                    description=f"Um neném está precisando de acolhimento!\n👤 **Membro:** {user.mention}\n📍 **Ticket:** {canal.mention}\n\nAlgum anjinho pode assumir esse chamado? 💚",
                    color=0x87CEEB,
                    timestamp=datetime.now()
                )
                await canal_anjo_logs.send(content=cargo_anjo_mencao.mention if cargo_anjo_mencao else None, embed=embed_anjo, view=ReivindicarAnjoView(canal.id))

        elif tipo == "namorados":
            embed_namo = discord.Embed(title="💘 EVENTO DOS NAMORADOS", description=f"Oii {user.mention}! Um Cupido foi chamado para te flechar! ✨🏹", color=0xFF69B4)
            embed_namo.set_image(url=GIF_NAMORADOS)
            await canal.send(embed=embed_namo, view=FecharTicketView())
            
            canal_cupido_logs = discord.utils.get(guild.text_channels, name=CANAL_CHAT_CUPIDOS)
            if canal_cupido_logs:
                cargo_cupido_mencao = discord.utils.get(guild.roles, name=CARGO_CUPIDOS)
                embed_cupido = discord.Embed(
                    title="🏹 Novo Ticket de Amor!",
                    description=f"O(A) {user.mention} abriu um ticket dos namorados! Vá espalhar o amor! 💘\n📍 **Canal:** {canal.mention}",
                    color=0xFF1493,
                    timestamp=datetime.now()
                )
                await canal_cupido_logs.send(content=cargo_cupido_mencao.mention if cargo_cupido_mencao else None, embed=embed_cupido, view=ReivindicarCupidoView(canal.id))
            
        elif tipo == "catalogo":
            embed_cat = discord.Embed(title="📸 EVENTO CATÁLOGO", color=0x00FFFF)
            embed_cat.description = f"{user.mention}, envie **APENAS A FOTO**."
            embed_cat.set_image(url=GIF_CATALOGO)
            await canal.send(embed=embed_cat)
            
        elif tipo == "lider_torcida":
            await canal.send(f"📣 **LÍDER DE TORCIDA**\n\n{user.mention}, conta pra staff por que você quer ser líder de torcida! 💚🐲", view=FecharTicketView())
        else:
            await canal.send(f"🎟️ **NOVO TICKET**\n\n👤 {user.mention}", view=FecharTicketView())

        await interaction.response.send_message("✅ Ticket criado com sucesso! 💚🐲", ephemeral=True)

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
    bot.add_view(LojaView())
    
    if not loop_jogo_monstrinho.is_running():
        loop_jogo_monstrinho.start()

    for guild in bot.guilds:
        # Inicializar Tickets
        canal_tkt = discord.utils.get(guild.text_channels, name=CANAL_TICKET)
        if canal_tkt:
            try: await canal_tkt.purge(limit=5)
            except: pass
            await canal_tkt.send("🎟️ **CENTRAL DE TICKETS CSI** 🎟️\n\nSelecione abaixo para abrir um ticket 💚🐲", view=TicketView())
            embed_banner = discord.Embed(color=0x2b2d31)
            embed_banner.set_image(url=BANNER_TICKET)
            await canal_tkt.send(embed=banner)

        # Inicializar Loja
        canal_loja = discord.utils.get(guild.text_channels, name=CANAL_LOJA_INFO)
        if canal_loja:
            try: await canal_loja.purge(limit=10)
            except: pass
            embed_loja = discord.Embed(
                title="🪙 Loja de Monstrinhos Coins do Servidor",
                description=(
                    "🏷️ **Cargos**\n"
                    "• Cargo exclusivo por 7 dias — `5.000 coins`\n"
                    "• Cargo colorido personalizado — `8.000 coins`\n\n"
                    "🎉 **Interações**\n"
                    "• Criar um evento oficial (analisado pela staff) — `12.000 coins`\n"
                    "• Dar apelido em alguém (com regras) — `6.000 coins`\n\n"
                    "🎮 **Recompensas externas**\n"
                    "• Item de jogo (dependendo do jogo) — `15.000 coins`\n"
                    "• Robux — `30.000 coins`\n"
                    "• Discord Nitro (1 mês) — `90.000 coins`"
                ),
                color=0xFFD700
            )
            embed_loja.set_thumbnail(url=AVATAR_MONSTRINHO)
            embed_loja.set_footer(text="Escolha seu item no menu abaixo! 🐲💚")
            await canal_loja.send(embed=embed_loja, view=LojaView())

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
            f"**Até logo, neném... vou sentir saudades!** 🐲💚👋"
        )
        await member.send(mensagem_despedida)
    except: pass

@bot.event
async def on_message_delete(message):
    if message.author.bot: return
    canal_log = discord.utils.get(message.guild.text_channels, name=CANAL_LOG)
    if canal_log:
        embed = discord.Embed(
            title="📝 Mensagem Deletada", 
            color=0xFF0000,
            timestamp=datetime.now()
        )
        embed.set_author(name=f"Autor: {message.author.name}", icon_url=message.author.display_avatar.url)
        embed.add_field(name="📍 Canal", value=message.channel.mention, inline=True)
        embed.add_field(name="👤 ID do Autor", value=f"`{message.author.id}`", inline=True)
        
        conteudo = message.content or "Mensagem sem texto ou apenas mídia."
        embed.add_field(name="💬 Conteúdo", value=f"```\n{conteudo}\n```", inline=False)
        
        if message.attachments:
            anexo = message.attachments[0]
            if any(anexo.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg', 'gif', 'webp']):
                embed.set_image(url=anexo.proxy_url)

        embed.set_thumbnail(url=AVATAR_MONSTRINHO)
        embed.set_footer(text=f"Monstrinho Logs 🐲")
        await canal_log.send(embed=embed)

# ============== COMANDOS DE JOGOS INDIVIDUAIS =================

@bot.command()
async def jogo(ctx):
    if ctx.author.id != DONO_ID:
        return await ctx.send("❌ Só meu papai pode forçar o início de um jogo! 🐲")
    await ctx.send("🐲 Iniciando rodada aleatória para você, papai!")
    await disparar_pergunta(ctx.guild)

@bot.command()
async def pergunta(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    await disparar_pergunta(ctx.guild, "pergunta")

@bot.command()
async def numero(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    await disparar_pergunta(ctx.guild, "numero")

@bot.command()
async def ppt(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    await disparar_pergunta(ctx.guild, "ppt")

@bot.command()
async def caracoroa(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    await disparar_pergunta(ctx.guild, "cara_coroa")

@bot.command()
async def dado(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    await disparar_pergunta(ctx.guild, "dado")

@bot.command()
async def palavra(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    await disparar_pergunta(ctx.guild, "palavra")

@bot.command()
async def emoji(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    await disparar_pergunta(ctx.guild, "emoji")

@bot.command()
async def embaralhada(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    await disparar_pergunta(ctx.guild, "embaralhada")

@bot.command()
async def caixa(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    await disparar_pergunta(ctx.guild, "caixa")

@bot.command()
async def bauperdido(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    await disparar_pergunta(ctx.guild, "bauperdido")

@bot.command()
async def roleta(ctx):
    if ctx.author.id != DONO_ID:
        return await ctx.send("❌ Só meu papai pode forçar o início da roleta! 🐲")
    await ctx.send("🐲 Iniciando rodada de Roleta Coletiva para você, papai!")
    await disparar_roleta(ctx.guild)

@bot.command()
async def silencioso(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    await disparar_pergunta(ctx.guild, "silencioso")

# ============== COMANDOS ADMINISTRATIVOS =================

@bot.command()
async def resetar_ranking(ctx):
    if ctx.author.id != DONO_ID:
        return await ctx.send("❌ Só meu papai pode resetar o ranking! 🐲😤")
    global pontuacao_monstrinho
    pontuacao_monstrinho = {}
    await atualizar_ranking(ctx.guild)
    await ctx.send("✅ **O Ranking de Monstrinho-Coins foi resetado com sucesso!** 🐲✨ Todos voltam ao zero!")

@bot.command()
async def bauadm(ctx):
    if ctx.author.id != DONO_ID:
        return await ctx.send("❌ Só meu papai pode abrir o Baú do ADM! 🐲💎")
    
    await ctx.send("💰 **BAÚ DO ADM!** 💰\n\nMeu papai, para quem você quer abrir o baú? Mencione (@) a pessoa sortuda agora! 🐲✨")
    
    def check_user(m):
        return m.author == ctx.author and m.channel == ctx.channel and len(m.mentions) > 0
    
    try:
        msg_user = await bot.wait_for("message", check=check_user, timeout=30)
        alvo = msg_user.mentions[0]
        
        await ctx.send(f"💎 Entendido! E quantos **Monstrinho-Coins** você quer dar para o(a) {alvo.mention}? 🐲💰")
        
        def check_quant(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()
        
        msg_quant = await bot.wait_for("message", check=check_quant, timeout=30)
        quantidade = int(msg_quant.content)
        
        pontuacao_monstrinho[alvo.id] = pontuacao_monstrinho.get(alvo.id, 0) + quantidade
        
        embed = discord.Embed(
            title="💎 O BAÚ DO ADM FOI ABERTO! 💎",
            description=f"O meu papai escolheu você, {alvo.mention}!\n\nVocê acaba de receber **{quantidade} Monstrinho-Coins** diretamente do tesouro real! 🐲💚✨",
            color=0xFFD700
        )
        embed.set_image(url="https://media.tenor.com/8yMrP1Cs7ykAAAAM/ninjala-ninjala-season6trailer.gif")
        
        await ctx.send(embed=embed)
        await atualizar_ranking(ctx.guild)
        
    except asyncio.TimeoutError:
        await ctx.send("⏰ O tempo acabou e o baú se fechou! 🐲")

@bot.command(name="removercastigo")
async def remover_castigo_manual(ctx, membro: discord.Member):
    eh_staff = any(role.name in CARGOS_IMUNES_NOMES for role in ctx.author.roles) or ctx.author.id == DONO_ID
    if not eh_staff:
        return await ctx.send("❌ Você não tem permissão para usar esse comando! 🐲😤")
    try:
        await membro.timeout(None)
        avisos_usuarios[membro.id] = 0
        embed = discord.Embed(
            title="🔓 CASTIGO REMOVIDO MANUALMENTE",
            description=f"O membro {membro.mention} teve seus avisos resetados e o castigo removido por {ctx.author.mention}. 🐲💚",
            color=0x00FF7F,
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=AVATAR_MONSTRINHO)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Ocorreu um erro ao tentar remover o castigo: {e}")

@bot.event
async def on_message(message):
    if message.author.bot: return

    # --- LÓGICA EVENTO SILENCIOSO ---
    global contador_mensagens_silencioso, meta_mensagens_silencioso, evento_silencioso_ativo
    if evento_silencioso_ativo and message.channel.name == CANAL_GERAL:
        contador_mensagens_silencioso += 1
        if contador_mensagens_silencioso >= meta_mensagens_silencioso:
            user_id = message.author.id
            pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + 400
            
            embed_silencioso = discord.Embed(
                title="🐲 SORTE NO SILÊNCIO! 🐲",
                description=f"Surpresa! {message.author.mention}, você enviou a mensagem de número **{meta_mensagens_silencioso}**!\n\nVocê ganhou **400 Monstrinho-Coins**! 💎✨",
                color=0xFFD700
            )
            embed_silencioso.set_thumbnail(url=AVATAR_MONSTRINHO)
            await message.channel.send(embed=embed_silencioso)
            
            # Reset do evento
            evento_silencioso_ativo = False
            jogo_em_andamento["venceu"] = True
            await atualizar_ranking(message.guild)

    # --- LÓGICA DO JOGUINHO ---
    if jogo_em_andamento["resposta"] and message.channel.name == CANAL_GERAL:
        user_id = message.author.id
        msg_content = message.content.lower().strip()
        tipo = jogo_em_andamento["tipo"]
        ganhou = False
        premio = 0

        # Filtro de participação: na roleta, só uma vez por evento. Nos outros, só um vencedor total.
        if user_id in jogo_em_andamento["participantes_tentaram"]:
            if tipo == "roleta":
                # Resposta silenciosa ou aviso rápido se já jogou na roleta
                return 
            elif tipo not in ["caixa"]:
                return

        filtros = {
            "numero": lambda m: m.isdigit(),
            "ppt": lambda m: m in ["pedra", "papel", "tesoura"],
            "cara_coroa": lambda m: m in ["cara", "coroa"],
            "dado": lambda m: m.isdigit() and 1 <= int(m) <= 6,
            "pergunta": lambda m: True, "palavra": lambda m: True, "emoji": lambda m: True,
            "roleta": lambda m: m == "roleta",
            "embaralhada": lambda m: True,
            "caixa": lambda m: m in ["1", "2", "3"],
            "bauperdido": lambda m: m == "abrir"
        }

        if filtros.get(tipo, lambda m: False)(msg_content):
            jogo_em_andamento["participantes_tentaram"].append(user_id)

            if tipo == "bauperdido":
                jogo_em_andamento["venceu"] = True
                jogo_em_andamento["resposta"] = None
                sorte = random.random()
                if sorte < 0.5: # 50% de chance para cada
                    ganhou, premio = True, 200
                else:
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) - 100
                    embed_mimico = discord.Embed(title="💀 O MÍMICO TE PEGOU!", description=f"{message.author.mention}, o baú era um monstro! Você perdeu **100 Coins**! 🐲💔", color=0xFF0000)
                    embed_mimico.set_image(url=GIF_MIMICO)
                    await message.reply(embed=embed_mimico)
                    await atualizar_ranking(message.guild)
                    return

            elif tipo == "embaralhada":
                if msg_content == jogo_em_andamento["resposta"]:
                    ganhou, premio = True, 100
                else:
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) - 25
                    await message.reply("🥺 Errou a palavra! O Monstrinho ficou triste e você perdeu **25 coins**! 🐲💔")
                    await atualizar_ranking(message.guild) 
                    return

            elif tipo == "caixa":
                jogo_em_andamento["venceu"] = True
                jogo_em_andamento["resposta"] = None
                resultado_caixa = random.choice(["coins", "raro", "perder"])
                
                if resultado_caixa == "coins":
                    await message.reply(f"🎁 {message.author.mention}, a caixa tem **moedas**!\nVocê quer ganhar **50 coins** ou prefere **doar 100 coins** de si mesmo para alguém? (Responda **GANHAR** ou **DOAR**)")
                    def check_caixa(m):
                        return m.author == message.author and m.content.lower() in ["ganhar", "doar"]
                    try:
                        resp = await bot.wait_for("message", check=check_caixa, timeout=30)
                        if resp.content.lower() == "ganhar":
                            pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + 50
                            await message.reply("🐲 Você escolheu ganhar! +50 Coins na conta! 💚")
                        else:
                            await message.reply("😇 Que generoso! Mencione para quem você quer doar 100 coins agora!")
                            def check_doacao(m):
                                return m.author == message.author and len(m.mentions) > 0
                            try:
                                msg_alvo = await bot.wait_for("message", check=check_doacao, timeout=30)
                                alvo = msg_alvo.mentions[0]
                                if pontuacao_monstrinho.get(user_id, 0) >= 100:
                                    pontuacao_monstrinho[user_id] -= 100
                                    pontuacao_monstrinho[alvo.id] = pontuacao_monstrinho.get(alvo.id, 0) + 100
                                    await message.reply(f"💖 Você doou 100 coins para {alvo.mention}! O Monstrinho amou sua bondade! 🐲✨")
                                else:
                                    await message.reply("❌ Você não tem coins suficientes para doar! O Monstrinho ficou confuso. 🐲")
                            except asyncio.TimeoutError:
                                await message.reply("⏰ Tempo de doação acabou!")
                        await atualizar_ranking(message.guild)
                    except asyncio.TimeoutError:
                        await message.reply("⏰ Você demorou demais e a caixa se fechou! 🐲")

                elif resultado_caixa == "raro":
                    ganhou, premio = True, 300
                    
                elif resultado_caixa == "perder":
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) - 50
                    await message.reply("💀 Que azar! A caixa estava amaldiçoada e você perdeu **50 coins**! 🐲💔")
                    await atualizar_ranking(message.guild) 
                
                if not ganhou: return

            elif tipo == "numero":
                if msg_content == jogo_em_andamento["resposta"]: ganhou, premio = True, 500
                else:
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) - 25
                    await message.reply("🥺 Oh amiguinho, você não conseguiu dessa vez... -25 coins! 💚")
                    await atualizar_ranking(message.guild)

            elif tipo == "ppt":
                bot_choice = random.choice(["pedra", "papel", "tesoura"])
                if msg_content == bot_choice:
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) - 25
                    await message.reply(f"🤝 Empate! Eu escolhi **{bot_choice}**. -25 coins... 🥺")
                    await atualizar_ranking(message.guild)
                elif (msg_content == "pedra" and bot_choice == "tesoura") or (msg_content == "papel" and bot_choice == "pedra") or (msg_content == "tesoura" and bot_choice == "papel"):
                    ganhou, premio = True, 150
                else:
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) - 50
                    await message.reply(f"😜 Eu venci com **{bot_choice}**! -50 coins... 🐲💔")
                    await atualizar_ranking(message.guild)

            elif tipo == "cara_coroa":
                if msg_content == jogo_em_andamento["resposta"]: ganhou, premio = True, 150
                else:
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) - 75
                    await message.reply(f"❌ Errou! Era **{jogo_em_andamento['resposta']}**. -75 coins! 🥺💔")
                    await atualizar_ranking(message.guild)

            elif tipo == "dado":
                if msg_content == jogo_em_andamento["resposta"]: ganhou, premio = True, 35
                else:
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) - 10
                    await message.reply(f"🎲 Caiu **{jogo_em_andamento['resposta']}**! Errou... -10 coins! 🥺")
                    await atualizar_ranking(message.guild)

            elif tipo == "roleta":
                # Na roleta, não paramos o jogo global, apenas processamos o giro do usuário
                opcoes_roleta = ["500", "50", "100", "perder", "jogo", "dobrar"]
                pesos = [0.01, 0.25, 0.25, 0.15, 0.14, 0.20] 
                resultado = random.choices(opcoes_roleta, weights=pesos)[0]
                
                if resultado == "500":
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + 500
                    await message.reply(embed=discord.Embed(title="💎 MÁXIMO!", description=f"{message.author.mention} ganhou **500 Coins**! 🐲✨", color=0x00FFFF))
                elif resultado in ["50", "100"]:
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + int(resultado)
                    await message.reply(f"🎉 {message.author.mention} ganhou **{resultado} Coins**! 🐲💚")
                elif resultado == "perder":
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) - 100
                    await message.reply(embed=discord.Embed(title="💀 AZAR", description=f"{message.author.mention} perdeu **100 Coins**! 🐲💔", color=0xFF0000).set_image(url=GIF_DERROTA))
                elif resultado == "jogo":
                    await message.reply(f"🎡 {message.author.mention}, você ativou um bônus! Outro jogo vindo aí para todos! 🐲🔥")
                    await asyncio.sleep(2); await disparar_pergunta(message.guild)
                elif resultado == "dobrar":
                    premio_atual = 100
                    continuar = True
                    while continuar:
                        await message.reply(f"🔥 **LOUCURA!** {message.author.mention} caiu na chance de **DOBRAR!**\nVocê tem **{premio_atual}** coins agora. Quer arriscar dobrar para **{premio_atual * 2}**?\nDigite **SIM** para arriscar ou **NAO** para parar!")
                        def check_dobro(m): return m.author == message.author and m.content.lower() in ["sim", "nao"]
                        try:
                            msg_resp = await bot.wait_for("message", check=check_dobro, timeout=20)
                            if msg_resp.content.lower() == "sim":
                                if random.random() < 0.5: 
                                    premio_atual *= 2
                                    await message.reply(f"✅ **CONSEGUIU!** Agora você tem **{premio_atual}** coins!")
                                else:
                                    await message.reply(f"💥 **PERDEU TUDO!** O Monstrinho engoliu suas moedas! 🐲💔")
                                    premio_atual = 0
                                    continuar = False
                            else:
                                await message.reply(f"💰 Sábia escolha! Você garantiu **{premio_atual}** coins! 🐲💚")
                                continuar = False
                        except asyncio.TimeoutError:
                            await message.reply(f"⏰ Tempo acabou! Você parou com **{premio_atual}** coins.")
                            continuar = False
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + premio_atual
                
                await atualizar_ranking(message.guild); return

            elif msg_content == jogo_em_andamento["resposta"]:
                ganhou, premio = True, 50

            if ganhou:
                jogo_em_andamento["venceu"] = True
                jogo_em_andamento["resposta"] = None
                pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + premio
                embed_acerto = discord.Embed(title="🎉 PARABÉNS NENÉM! 🎉", description=f"{message.author.mention}, você acertou!\nVocê ganhou **{premio} Monstrinho-Coins**! 🐲💚", color=0x00FF7F)
                embed_acerto.set_image(url=GIF_ACERTO_MONSTRINHO)
                await message.reply(embed=embed_acerto)
                await atualizar_ranking(message.guild) 
            return

    # --- PALAVRAS PROIBIDAS ---
    texto = message.content.lower()
    eh_imune = message.author.id == DONO_ID or any(role.name in CARGOS_IMUNES_NOMES for role in message.author.roles)
    if not eh_imune and message.channel.name != CANAL_DESABAFOS:
        for palavra in PALAVRAS_PROIBIDAS:
            if palavra in texto:
                try:
                    await message.delete()
                    user_id = message.author.id
                    avisos_usuarios[user_id] = avisos_usuarios.get(user_id, 0) + 1
                    qtd = avisos_usuarios[user_id]
                    if qtd >= 4:
                        total_castigos_usuario[user_id] = total_castigos_usuario.get(user_id, 0) + 1
                        avisos_usuarios[user_id] = 0
                        await message.author.timeout(timedelta(days=1))
                        canal_adv = discord.utils.get(message.guild.text_channels, name=CANAL_ADVERTENCIAS)
                        if canal_adv: await canal_adv.send(embed=discord.Embed(title="🚨 CASTIGO", description=f"{message.author.mention} silenciado.", color=0xFF0000), view=LiberarCastigoView(user_id))
                    else:
                        await message.channel.send(f"⚠️ {message.author.mention} aviso {qtd}/3!", delete_after=10)
                    return
                except: pass

    await bot.process_commands(message)

bot.run(TOKEN)
