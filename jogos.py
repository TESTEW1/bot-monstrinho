import random
import discord
from datetime import datetime

# ============== CONFIGURAÇÕES DO JOGO =================

AVATAR_MONSTRINHO = "https://cdn.discordapp.com/attachments/1304658653697019964/1338274026333671485/monstrinho_avatar.png"
CANAL_RANKING_MONSTRINHO = "ranking-monstrinho"

# Banco de dados temporário (será importado pelo bot)
pontuacao_monstrinho = {}
jogo_em_andamento = {"pergunta": None, "resposta": None, "venceu": False}

# ============== LISTA DE PERGUNTAS =================
# Você pode adicionar quantas quiser aqui!

LISTA_PERGUNTAS = [
    ("Qual é o super-herói que tem medo de morcego?", "batman"),
    ("Qual é a fruta favorita do Pac-Man?", "cereja"),
    ("Quem é o melhor amigo do Bob Esponja?", "patrick"),
    ("Em qual jogo você constrói com blocos?", "minecraft")
]

# ============== FUNÇÕES DE LÓGICA =================

async def atualizar_ranking(guild, pontuacao_dict):
    """Atualiza o canal de ranking com as pontuações atuais."""
    canal_rank = discord.utils.get(guild.text_channels, name=CANAL_RANKING_MONSTRINHO)
    if not canal_rank: 
        return
    
    # Ordenar ranking do maior para o menor
    rank_ordenado = sorted(pontuacao_dict.items(), key=lambda item: item[1], reverse=True)
    
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

def sortear_pergunta():
    """Escolhe uma pergunta aleatória da lista."""
    return random.choice(LISTA_PERGUNTAS)
