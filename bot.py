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
CANAL_ATENCAO = "⚠️・atenção" # Canal novo para monitoramento

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


# ============== DADOS =================

tickets = {}
avisos_usuarios = {} 
total_castigos_usuario = {} # Contador de castigos total
pontuacao_monstrinho = {} # Guardar os pontos
monitoramento_stress = {} # Contador para o sistema de atenção
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
("Quem é o mago de barra branca em Senhor dos Anéis?", "gandalf"),
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

LISTA_PALAVRAS_ATENCAO = [
    "triste",
    "tristeza",
    "sozinho",
    "sozinha",
    "solidão",
    "vazio",
    "vazia",
    "cansado",
    "cansada",
    "desanimado",
    "desanimada",
    "derrotado",
    "derrotada",
    "inútil",
    "inutil",
    "fracasso",
    "deprimido",
    "deprimida",
    "depressivo",
    "depressiva",
    "sem esperança",
    "sem sentido",
    "acabado",
    "acabada",
    "destruído",
    "destruida",
    "quebrado",
    "quebrada",
    "perdido",
    "perdida",
    "infeliz",
    "angustiado",
    "angustiada",
    "abatido",
    "abatida",
    "desolado",
    "desolada",
    "miserável",
    "miseravel",
    "patético",
    "patetico",
    "horrível",
    "horrivel",
    "péssimo",
    "pessimo",
    "terrível",
    "terrivel",
    "podre",
    "ruim",
    "horrendo",
    "horrenda",
    "fracassado",
    "fracassada",
    "ninguém liga",
    "ninguém se importa",
    "não sirvo pra nada",
    "não presto",
    "não valho nada",
    "sou inútil",
    "sou um lixo",
    "sou um fracasso",
    "me odeio",
    "odeio minha vida",
    "odeio tudo",
    "ninguém gosta de mim",
    "ninguém me ama",
    "sou um peso",
    "sou um problema",
    "só atrapalho",
    "sou descartável",
    "queria sumir",
    "queria desaparecer",
    "queria não existir",
    "queria dormir e não acordar",
    "não faço falta",
    "ninguém sentiria minha falta",
    "minha vida é inútil",
    "minha vida não presta",
    "minha vida não tem sentido",
    "vida sem sentido",
    "tudo dá errado",
    "nada presta",
    "nada importa",
    "nada vale a pena",
    "não vale a pena viver",
    "não vale a pena",
    "cansei de tudo",
    "cansado de tudo",
    "cansada de tudo",
    "não aguento",
    "não aguento mais",
    "não suporto mais",
    "não tenho forças",
    "sem forças",
    "sem energia",
    "esgotado",
    "esgotada",
    "exausto",
    "exausta",
    "desespero",
    "desesperado",
    "desesperada",
    "agonia",
    "dor",
    "sofrimento",
    "sofrer",
    "sofrendo",
    "angústia",
    "angustia",
    "tormento",
    "inferno",
    "colapso",
    "quero morrer",
    "queria morrer",
    "vou morrer",
    "vou me matar",
    "vou me suicidar",
    "me matar",
    "me suicidar",
    "suicídio",
    "suicidio",
    "suicidar",
    "acabar com tudo",
    "acabar com a minha vida",
    "sumir pra sempre",
    "desaparecer pra sempre",
    "não quero viver",
    "não quero mais viver",
    "prefiro morrer",
    "queria estar morto",
    "queria estar morta",
    "melhor morto",
    "melhor morta",
    "adeus para sempre",
    "adeus mundo",
    "última mensagem",
    "último adeus",
    "fim de tudo",
    "fim da minha vida",
    "vou partir",
    "vou embora pra sempre",
    "não volto mais",
    "ninguém vai sentir falta",
    "ninguém se importaria",
    "ninguém notaria",
    "não faço diferença",
    "não tenho valor",
    "sou insignificante",
    "sou ninguém",
    "sou nada",
    "não sou nada",
    "sou um erro",
    "sou um problema",
    "tudo é culpa minha",
    "a culpa é minha",
    "estraguei tudo",
    "não tem solução",
    "não tem saída",
    "sem saída",
    "sem futuro",
    "sem motivo pra viver",
    "perdi tudo",
    "perdi a vontade",
    "perdi a esperança",
    "desistir",
    "desisto",
    "vou desistir",
    "desistindo",
    "sem vontade de viver",
    "vontade de morrer",
    "querendo morrer"
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
        jogo_em_andamento["resposta"] = palavra.lower()
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
        cargo_anjo = discord.utils.get(interaction.guild.roles, name=CARGO_ANJO)
        if cargo_anjo not in interaction.user.roles:
            return await interaction.response.send_message("❌ Apenas Anjos podem assumir chamados!", ephemeral=True)

        canal_ticket = interaction.guild.get_channel(self.canal_ticket_id)
        if not canal_ticket:
            return await interaction.response.send_message("❌ Este canal não existe mais.", ephemeral=True)

        # Atualiza permissões do canal para o Anjo ver
        await canal_ticket.set_permissions(interaction.user, read_messages=True, send_messages=True)
        
        await interaction.response.send_message(f"✅ Você assumiu o chamado! Vá para {canal_ticket.mention}", ephemeral=True)
        await canal_ticket.send(f"🪽 **{interaction.user.mention} entrou para te acolher! Sinta-se à vontade para conversar.** 🪽")
        
        # Desativa o botão após reivindicado
        button.disabled = True
        await interaction.message.edit(view=self)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.select(
        placeholder="🎟️ Como podemos te ajudar hoje?",
        custom_id="ticket_select",
        options=[
            discord.SelectOption(label="Denúncia / Suporte", value="suporte", emoji="🛠️", description="Falar com a Staff do servidor."),
            discord.SelectOption(label="Preciso de um Anjo", value="anjo", emoji="👼", description="Apoio emocional e desabafos."),
            discord.SelectOption(label="Cupidos (Correio Elegante)", value="cupido", emoji="💘", description="Mandar um recadinho especial."),
        ]
    )
    async def callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        guild = interaction.guild
        user = interaction.user
        escolha = select.values[0]

        # Criar canal de ticket
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        nome_canal = f"🎟️┃{escolha}-{user.name}"
        canal = await guild.create_text_channel(nome_canal, overwrites=overwrites)

        embed = discord.Embed(
            title=f"🎟️ Atendimento: {escolha.title()}",
            description=f"Oii {user.mention}! 🐲💚\n\nJá abri seu canal de atendimento. Aguarde um pouquinho que nossa equipe já vem te dar atenção!\n\n📝 **Não esqueça de explicar o que aconteceu.**",
            color=0xFF69B4
        )
        embed.set_image(url=BANNER_TICKET)
        
        await canal.send(embed=embed, view=FecharTicketView())
        await interaction.response.send_message(f"✅ Seu canal foi criado: {canal.mention}", ephemeral=True)

        # Lógica Extra para Anjos/Cupidos (Notificar canais internos)
        if escolha == "anjo":
            canal_anjo_staff = discord.utils.get(guild.text_channels, name=CANAL_CHAT_ANJO)
            if canal_anjo_staff:
                embed_anjo = discord.Embed(title="👼 NOVO DESABAFO", description=f"Alguém precisa de um Anjo! 🪽\n\n**Membro:** {user.mention}", color=0x87CEEB)
                await canal_anjo_staff.send(embed=embed_anjo, view=ReivindicarAnjoView(canal.id))
        
        elif escolha == "cupido":
            canal_cupido_staff = discord.utils.get(guild.text_channels, name=CANAL_CHAT_CUPIDOS)
            if canal_cupido_staff:
                await canal_cupido_staff.send(f"💘 **NOVO CORREIO ELEGANTE:** {user.mention} abriu um ticket em {canal.mention}")

# ============== EVENTOS PRINCIPAIS =================

@bot.event
async def on_ready():
    print(f'🐲 Logado como {bot.user.name}')
    loop_jogo_monstrinho.start()
    bot.add_view(TicketView())
    bot.add_view(LojaView())
    await bot.change_presence(activity=discord.Game(name="🐲 Cuidando da CSI..."))

@bot.event
async def on_member_join(member):
    canal_liberacao = discord.utils.get(member.guild.text_channels, name=CANAL_LIBERACAO)
    if canal_liberacao:
        embed = discord.Embed(
            title="🔔 NOVO MORADOR NA MANSÃO! 🔔",
            description=f"Oii {member.mention}! Que alegria ter você aqui! 🐲💚\n\nPara entrar na nossa família, a staff precisa te liberar rapidinho. Segura a ansiedade que já já você entra!",
            color=0xFFA500
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await canal_liberacao.send(content="@here", embed=embed, view=AprovarMembroView(member.id))

@bot.event
async def on_message(message):
    if message.author.bot: return

    global jogo_em_andamento, contador_mensagens_silencioso, evento_silencioso_ativo

    # --- SISTEMA DE MONITORAMENTO DE ATENÇÃO (NOVO) ---
    texto_ajuda = message.content.lower()
    
    # Verifica se alguma palavra da lista está no texto
    if any(word in texto_ajuda for word in LISTA_PALAVRAS_ATENCAO):
        canal_atencao = discord.utils.get(message.guild.text_channels, name=CANAL_ATENCAO)
        
        if canal_atencao:
            user_id = message.author.id
            monitoramento_stress[user_id] = monitoramento_stress.get(user_id, 0) + 1
            contagem = monitoramento_stress[user_id]
            
            # Lógica de Menção se chegar a 3
            mencao_staff = ""
            if contagem >= 3:
                cargo_staff_equipe = discord.utils.get(message.guild.roles, name=CARGO_STAFF_EQUIPE)
                if cargo_staff_equipe:
                    mencao_staff = cargo_staff_equipe.mention
                else:
                    mencao_staff = "@Equipe Staff. 🦇" # Fallback se o cargo não for achado pelo nome exato

            # Criação da Ficha
            embed_alerta = discord.Embed(
                title="⚠️ ALERTA DE ATENÇÃO SILENCIOSA",
                description=f"O sistema detectou palavras que podem indicar um pedido de socorro ou sofrimento.",
                color=0xFFA500 if contagem < 3 else 0xFF0000,
                timestamp=datetime.now()
            )
            embed_alerta.set_thumbnail(url=message.author.display_avatar.url)
            embed_alerta.add_field(name="👤 Usuário", value=f"{message.author.mention} (`{message.author.id}`)", inline=True)
            embed_alerta.add_field(name="📍 Canal", value=message.channel.mention, inline=True)
            embed_alerta.add_field(name="🔢 Ocorrências do Usuário", value=f"{contagem}/3 (Nível de Atenção)", inline=True)
            
            conteudo_msg = message.content
            if len(conteudo_msg) > 1000: conteudo_msg = conteudo_msg[:1000] + "..."
            embed_alerta.add_field(name="💬 Mensagem Detectada", value=f"```{conteudo_msg}```", inline=False)
            
            embed_alerta.set_footer(text="Monstrinho Care System 🐲 - Não marque o usuário publicamente.")

            # Envia para o canal de atenção
            await canal_atencao.send(content=mencao_staff if contagem >= 3 else None, embed=embed_alerta)


    # --- LÓGICA DO JOGO ---
    if jogo_em_andamento["tipo"] and message.channel.name == CANAL_GERAL:
        user_id = message.author.id
        msg_content = message.content.lower().strip()

        # Resposta Correta (Geral)
        if jogo_em_andamento["resposta"] and msg_content == jogo_em_andamento["resposta"]:
            jogo_em_andamento["venceu"] = True
            premio = 50
            
            if jogo_em_andamento["tipo"] == "numero": premio = 500
            elif jogo_em_andamento["tipo"] in ["ppt", "cara_coroa"]: premio = 150
            elif jogo_em_andamento["tipo"] == "embaralhada": premio = 100
            elif jogo_em_andamento["tipo"] == "bauperdido": premio = 200

            pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + premio
            
            embed_vitoria = discord.Embed(
                title="🎉 TEMOS UM VENCEDOR! 🎉",
                description=f"AAAA {message.author.mention} você acertou!! 🐲💚\n\nA resposta era: **{jogo_em_andamento['resposta']}**\n\n💰 Você ganhou **{premio} Monstrinho-Coins**!",
                color=0x00FF00
            )
            embed_vitoria.set_image(url=GIF_ACERTO_MONSTRINHO)
            await message.channel.send(embed=embed_vitoria)
            
            jogo_em_andamento["tipo"] = None
            jogo_em_andamento["resposta"] = None
            await atualizar_ranking(message.guild)
            return

        # Lógica Roleta
        elif jogo_em_andamento["tipo"] == "roleta" and msg_content == "roleta":
            if user_id in jogo_em_andamento["participantes_tentaram"]:
                return await message.reply("❌ Você já girou a roleta nesta rodada! Espere a próxima.", delete_after=5)
            
            jogo_em_andamento["participantes_tentaram"].append(user_id)
            opcoes = ["ganhar_50", "ganhar_100", "ganhar_500", "perder_100", "dobrar", "outro_jogo"]
            resultado = random.choice(opcoes)

            if resultado == "ganhar_50":
                pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + 50
                await message.reply("🎰 A roleta parou em... **50 COINS**! Parabéns! 🐲")
            elif resultado == "ganhar_100":
                pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + 100
                await message.reply("🎰 A roleta parou em... **100 COINS**! Uhuuu! 🐲")
            elif resultado == "ganhar_500":
                pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + 500
                await message.reply("💎 **MEU DEUS!** A roleta parou no prêmio raro de **500 COINS**! 🐲✨")
            elif resultado == "perder_100":
                pontuacao_monstrinho[user_id] = max(0, pontuacao_monstrinho.get(user_id, 0) - 100)
                await message.reply("💀 Oh não... a roleta parou em **PERDER 100 COINS**. Que azar! 🐲💔")
            elif resultado == "dobrar":
                pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) * 2
                await message.reply("🔥 **SURPRESA!** Seus pontos acabaram de **DOBRAR**! O Monstrinho está generoso! 🐲")
            elif resultado == "outro_jogo":
                await message.reply("🎲 A roleta parou em... **OUTRO JOGO IMEDIATO!** Preparem-se!")
                await disparar_pergunta(message.guild)

            await atualizar_ranking(message.guild)
            return

        # Lógica Silencioso
        elif evento_silencioso_ativo:
            contador_mensagens_silencioso += 1
            if contador_mensagens_silencioso >= meta_mensagens_silencioso:
                evento_silencioso_ativo = False
                pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + 400
                await message.channel.send(f"🤫 **BINGOOO!** {message.author.mention} enviou a mensagem número **{meta_mensagens_silencioso}** e ganhou **400 Coins**! 🐲💎")
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
                        if canal_adv:
                            embed_adv = discord.Embed(
                                title="🚨 CASTIGO AUTOMÁTICO",
                                description=f"O usuário {message.author.mention} foi silenciado por 24h após repetir palavras proibidas. 🐲😤\n\n🔢 **Total de castigos acumulados:** {total_castigos_usuario[user_id]}",
                                color=0xFF0000
                            )
                            await canal_adv.send(embed=embed_adv, view=LiberarCastigoView(user_id))
                    else:
                        await message.channel.send(f"⚠️ Ei {message.author.mention}, cuidado com as palavras! O Monstrinho fica triste e a staff está de olho. (`{qtd}/4`)", delete_after=10)
                    
                    # Log no canal de logs
                    canal_log = discord.utils.get(message.guild.text_channels, name=CANAL_LOG)
                    if canal_log:
                        await canal_log.send(f"📝 **Palavra Apagada:** `{palavra}`\n👤 **Autor:** {message.author} ({message.author.id})\n📍 **Canal:** {message.channel.mention}")
                except:
                    pass
                return

    await bot.process_commands(message)

# ============== COMANDOS ADM =================

@bot.command()
@commands.has_permissions(administrator=True)
def setup_ticket(ctx):
    embed = discord.Embed(
        title="🎟️ CENTRAL DE ATENDIMENTO - CSI 🎟️",
        description="Precisa de ajuda, fazer uma denúncia ou apenas um ombro amigo? Escolha a categoria abaixo para abrir um atendimento privado!\n\n🕒 **Horário de atendimento:** Aleatório (conforme disponibilidade da staff).\n⚠️ **Atenção:** Abuso do sistema de tickets gera advertência.",
        color=0x9400D3
    )
    embed.set_image(url=BANNER_TICKET)
    embed.set_footer(text="CSI - Sistema de Suporte")
    await ctx.send(embed=embed, view=TicketView())

@bot.command()
@commands.has_permissions(administrator=True)
async def setup_loja(ctx):
    canal_loja = discord.utils.get(ctx.guild.text_channels, name=CANAL_LOJA_INFO)
    if not canal_loja: return await ctx.send("Crie o canal da loja primeiro.")
    
    embed = discord.Embed(
        title="🪙 LOJA DO MONSTRINHO 🪙",
        description="Troque suas **Monstrinho-Coins** por prêmios incríveis! 🐲✨\n\n💰 **Como ganhar coins?**\nFique atento ao chat-geral! O Monstrinho aparece a cada 30 minutos com joguinhos e desafios. Seja o mais rápido e acumule fortuna!\n\n🎁 **Prêmios Disponíveis:**",
        color=0xFFD700
    )
    for item, preco in PRECOS_LOJA.items():
        embed.add_field(name=f"🔸 {item.replace('_', ' ').title()}", value=f"Custo: `{preco} Coins`", inline=False)
    
    embed.set_image(url=GIF_CATALOGO)
    await canal_loja.send(embed=embed, view=LojaView())

@bot.command()
@commands.has_permissions(administrator=True)
async def add_coins(ctx, membro: discord.Member, quantidade: int):
    pontuacao_monstrinho[membro.id] = pontuacao_monstrinho.get(membro.id, 0) + quantidade
    await ctx.send(f"✅ {quantidade} coins adicionados para {membro.mention}!")
    await atualizar_ranking(ctx.guild)

@bot.command()
@commands.has_permissions(administrator=True)
async def force_game(ctx, tipo=None):
    await ctx.send(f"🐲 Iniciando evento forçado: {tipo if tipo else 'Aleatório'}...")
    await disparar_pergunta(ctx.guild, tipo_escolhido=tipo)

bot.run(TOKEN)
