import random
import discord
import asyncio
from datetime import datetime

# ============== CONFIGURAÇÕES DO JOGO =================

AVATAR_MONSTRINHO = "https://cdn.discordapp.com/attachments/1304658653697019964/1338274026333671485/monstrinho_avatar.png"
CANAL_RANKING_MONSTRINHO = "ranking-monstrinho"
CANAL_GERAL = "💭・chat-geral"
GIF_ACERTO_MONSTRINHO = "https://media.tenor.com/8yMrP1Cs7ykAAAAM/ninjala-ninjala-season6trailer.gif"

# Banco de dados temporário e controle
pontuacao_monstrinho = {}
jogo_em_andamento = {"pergunta": None, "resposta": None, "venceu": False}

# ============== LISTA DE PERGUNTAS =================

LISTA_PERGUNTAS = [
    ("Qual é o super-herói que tem medo de morcego?", "batman"),
    ("Qual é a fruta favorita do Pac-Man?", "cereja"),
    ("Quem é o melhor amigo do Bob Esponja?", "patrick"),
    ("Em qual jogo você constrói com blocos?", "minecraft"),
    ("Qual a cor da esmeralda?", "verde"),
    ("Quem é o encanador mais famoso dos games?", "mario"),
    ("Qual o nome do vilão que estalou os dedos e sumiu com metade do universo?", "thanos"),
    ("Em qual desenho existe um cachorro medroso que mora no Meio do Nada?", "coragem")
]

# ============== FUNÇÕES DE LÓGICA =================

async def atualizar_ranking(guild):
    """Atualiza o canal de ranking com as pontuações atuais."""
    canal_rank = discord.utils.get(guild.text_channels, name=CANAL_RANKING_MONSTRINHO)
    if not canal_rank: 
        return
    
    # Ordenar ranking do maior para o menor
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

    try:
        await canal_rank.purge(limit=5)
        await canal_rank.send(embed=embed)
    except:
        pass

async def disparar_pergunta(guild):
    """Envia a pergunta no Chat Geral e aguarda resposta."""
    canal_geral = discord.utils.get(guild.text_channels, name=CANAL_GERAL)
    if not canal_geral:
        return

    pergunta, resposta_correta = random.choice(LISTA_PERGUNTAS)
    jogo_em_andamento["pergunta"] = pergunta
    jogo_em_andamento["resposta"] = resposta_correta.lower()
    jogo_em_andamento["venceu"] = False

    embed = discord.Embed(
        title="🐲 HORA DO JOGUINHO DO MONSTRINHO! 🐲",
        description=f"Oii amiguinhos! Vamos ver quem é esperto? ✨\n\n**PERGUNTA:**\n> {pergunta}\n\nO primeiro que acertar nos próximos **5 minutos** ganha **100 monstrinho-coins**! Boa sorte! 💚🐉",
        color=0xADFF2F
    )
    embed.set_thumbnail(url=AVATAR_MONSTRINHO)
    embed.set_footer(text="Você tem 5 minutos! Responda aqui no chat!")
    
    await canal_geral.send(embed=embed)

    # Espera de 5 minutos (300 segundos)
    for _ in range(300):
        if jogo_em_andamento["venceu"]:
            return
        await asyncio.sleep(1)
    
    if not jogo_em_andamento["venceu"]:
        jogo_em_andamento["pergunta"] = None
        await canal_geral.send("🥺 Ahhh poxa, ninguém acertou a tempo... O Monstrinho ficou triste! 🐲💔")

async def verificar_resposta(message):
    """Verifica se a mensagem é a resposta correta para o jogo ativo."""
    if (jogo_em_andamento["pergunta"] and 
        message.channel.name == CANAL_GERAL and 
        message.content.lower() == jogo_em_andamento["resposta"]):
        
        jogo_em_andamento["venceu"] = True
        jogo_em_andamento["pergunta"] = None
        
        user_id = message.author.id
        pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + 100
        
        embed_acerto = discord.Embed(
            title="🎉 PARABÉNS NENÉM! 🎉",
            description=f"{message.author.mention}, você acertou!\nVocê ganhou **100 Monstrinho-Coins**! 🐲💚",
            color=0x00FF7F
        )
        embed_acerto.set_image(url=GIF_ACERTO_MONSTRINHO)
        
        await message.reply(embed=embed_acerto)
        await atualizar_ranking(message.guild)
        return True
    return False
