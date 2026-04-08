import discord
from discord.ext import commands, tasks
import random
import asyncio
import os
import re
from datetime import timedelta
from datetime import datetime
from collections import defaultdict, deque
try:
    from deep_translator import GoogleTranslator
    from langdetect import detect as detectar_idioma
    TRADUCAO_DISPONIVEL = True
except ImportError:
    TRADUCAO_DISPONIVEL = False
# ================= INTENTS =================
# ============== BOT SETUP =================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="v!", intents=intents)

# ╔══════════════════════════════════════════════════════════════════╗
# ║          VAMPY SECURITY SYSTEM — GOD MODE v2.0             ║
# ║      Sistema completo de segurança integrado ao bot             ║
# ╚══════════════════════════════════════════════════════════════════╝

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ⚙️  CONFIGURAÇÕES DE SEGURANÇA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LOG_CHANNEL_NAME = "🗒️・monitoramento"   # Canal exclusivo de logs de segurança

COMMAND_SPAM_LIMIT    = 3       # Máximo de comandos por janela
COMMAND_SPAM_WINDOW   = 5       # Janela em segundos
COMMAND_COOLDOWN_TIME = 30      # Cooldown após spam de comandos

RAID_JOIN_LIMIT       = 8       # Entradas para acionar alerta
RAID_JOIN_WINDOW      = 5       # Janela em segundos
LOCKDOWN_THRESHOLD    = 12      # Entradas para lockdown total

MSG_SPAM_LIMIT        = 7       # Mensagens por janela
MSG_SPAM_WINDOW       = 5       # Janela em segundos
MSG_REPEAT_LIMIT      = 4       # Msgs idênticas seguidas
EMOJI_SPAM_LIMIT      = 20      # Emojis numa mensagem
MENTION_SPAM_LIMIT    = 5       # Menções numa mensagem

ADMIN_ACTION_LIMIT    = 5       # Ações admin por janela
ADMIN_ACTION_WINDOW   = 10      # Janela em segundos

RISK_SPAM_MSG         = 2
RISK_SPAM_CMD         = 3
RISK_RAID             = 5
RISK_LINK             = 4
RISK_NEW_ACCOUNT      = 2
RISK_NO_AVATAR        = 1
RISK_SUSPICIOUS_THRESHOLD = 12  # Pontuação para marcar SUSPEITO

ACCOUNT_MIN_AGE_DAYS  = 7       # Dias mínimos de conta

MALICIOUS_PATTERNS = [
    r"discord\.gift", r"discordnitro\.", r"free.*nitro",
    r"steamcommunity.*\.ru", r"bit\.ly", r"tinyurl\.com",
    r"grabify\.link", r"iplogger\.", r"discord-app\.com",
    r"dicsord\.", r"dlscord\.",
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📦  BANCO DE DADOS INTERNO DE SEGURANÇA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class SecurityDatabase:
    """Banco de dados em memória para inteligência de segurança."""
    def __init__(self):
        self.risk_scores:   dict[int, int]  = {}
        self.flagged_users: dict[int, dict] = {}
        self.alert_history: list[dict]      = []
        self.total_alerts  = 0
        self.spam_events   = 0
        self.raid_events   = 0
        self.link_events   = 0
        self.admin_events  = 0
        self.lockdown_active  = False
        self.emergency_mode   = False
        self.security_level   = "NORMAL"

    def add_risk(self, user_id: int, points: int, reason: str):
        self.risk_scores[user_id] = self.risk_scores.get(user_id, 0) + points
        if self.risk_scores[user_id] >= RISK_SUSPICIOUS_THRESHOLD:
            self.flagged_users[user_id] = {
                "reason": reason,
                "time":   datetime.utcnow(),
                "score":  self.risk_scores[user_id]
            }

    def get_risk(self, uid: int) -> int:
        return self.risk_scores.get(uid, 0)

    def is_flagged(self, uid: int) -> bool:
        return uid in self.flagged_users

    def log_alert(self, alert_type: str, details: str):
        self.total_alerts += 1
        self.alert_history.append({"type": alert_type, "details": details, "time": datetime.utcnow()})
        if len(self.alert_history) > 500:
            self.alert_history.pop(0)

    def reset(self):
        self.risk_scores.clear(); self.flagged_users.clear(); self.alert_history.clear()
        self.total_alerts = self.spam_events = self.raid_events = self.link_events = self.admin_events = 0
        self.lockdown_active = self.emergency_mode = False
        self.security_level  = "NORMAL"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🛡️  COG — VAMPY SECURITY SYSTEM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class VampyCog(commands.Cog, name="VampySecurity"):
    """VAMPY SECURITY SYSTEM — GOD MODE v2.0."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db  = SecurityDatabase()
        self._cmd_timestamps:   defaultdict[int, deque] = defaultdict(deque)
        self._msg_timestamps:   defaultdict[int, deque] = defaultdict(deque)
        self._join_timestamps:  defaultdict[int, deque] = defaultdict(deque)
        self._admin_timestamps: defaultdict[int, deque] = defaultdict(deque)
        self._last_msg:   dict[int, list[str]]       = {}
        self._cmd_cooldowns: dict[int, datetime]     = {}
        self.cleanup_task.start()

    def cog_unload(self):
        self.cleanup_task.cancel()

    # ── Utilitários ──────────────────────────────

    async def get_log_channel(self, guild: discord.Guild):
        return discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)

    def _now(self) -> float:
        return datetime.utcnow().timestamp()

    def _prune(self, dq: deque, window: float):
        cutoff = self._now() - window
        while dq and dq[0] < cutoff:
            dq.popleft()

    def _level_color(self) -> int:
        return {"NORMAL": 0x00ff99, "ALERTA": 0xffaa00, "LOCKDOWN": 0xff4400, "EMERGÊNCIA": 0xff0000}.get(self.db.security_level, 0x00ff99)

    async def send_alert(self, guild, threat_type, user, details, color=0xff4444, critical=False):
        """Envia embed de alerta para o canal de monitoramento."""
        ch = await self.get_log_channel(guild)
        if not ch:
            return
        now = datetime.utcnow()
        self.db.log_alert(threat_type, details)
        embed = discord.Embed(title=f"{'🔴' if critical else '🚨'} VAMPY SECURITY ALERT", color=color, timestamp=now)
        embed.add_field(name="⚠️ Tipo de Ameaça", value=f"`{threat_type}`",                           inline=False)
        embed.add_field(name="👤 Usuário",          value=str(user) if user else "Desconhecido",        inline=True)
        embed.add_field(name="🆔 ID",               value=str(user.id) if user else "—",                inline=True)
        embed.add_field(name="🏠 Servidor",         value=guild.name,                                    inline=True)
        embed.add_field(name="📋 Detalhes",         value=details,                                       inline=False)
        embed.add_field(name="⏰ Horário (UTC)",    value=now.strftime("%d/%m/%Y às %H:%M:%S"),          inline=False)
        if user and hasattr(user, "display_avatar"):
            embed.set_thumbnail(url=user.display_avatar.url)
        risk    = self.db.get_risk(user.id) if user else 0
        flagged = "⛔ SIM" if (user and self.db.is_flagged(user.id)) else "✅ Não"
        embed.set_footer(text=f"VAMPY SECURITY • Risco: {risk}pts | Suspeito: {flagged}",
                         icon_url=self.bot.user.display_avatar.url if self.bot.user else None)
        await ch.send(embed=embed)

    # ── 🟢 BOOT — Ficha de inicialização ─────────

    @commands.Cog.listener()
    async def on_ready(self):
        """Envia a ficha profissional de inicialização no canal de monitoramento."""
        await asyncio.sleep(3)
        for guild in self.bot.guilds:
            ch = await self.get_log_channel(guild)
            if not ch:
                continue
            now = datetime.utcnow()

            # Embed Principal de Boot
            boot = discord.Embed(
                description=(
                    "```\n"
                    "╔══════════════════════════════════════╗\n"
                    "║   VAMPY SECURITY SYSTEM         ║\n"
                    "║         — GOD MODE —                 ║\n"
                    "║       ⚡  v2.0  ONLINE  ⚡           ║\n"
                    "╚══════════════════════════════════════╝\n"
                    "```"
                ),
                color=0x00ff99, timestamp=now
            )
            boot.set_author(name="VAMPY SECURITY • Sistema Iniciado",
                            icon_url=self.bot.user.display_avatar.url if self.bot.user else None)
            boot.add_field(name="🛡️ Módulos Ativos (14/14)", inline=False, value=(
                "✅ Anti-Spam de Comandos\n✅ Detector de Raid\n✅ Auto Lockdown\n"
                "✅ Anti-Spam de Mensagens\n✅ Monitor de Ações Admin\n✅ Detector de Bot Suspeito\n"
                "✅ Detector de Links Maliciosos\n✅ Pontuação de Risco\n✅ Detecção de Script\n"
                "✅ Anti-Raid Extremo / Emergência\n✅ Contas Suspeitas\n✅ Inteligência (DB)\n"
                "✅ Monitor de Erros\n✅ Comandos Administrativos"
            ))
            boot.add_field(name="⚙️ Configuração Atual", inline=False, value=(
                f"📡 Log: `#{LOG_CHANNEL_NAME}`\n"
                f"🚫 Spam CMD: `{COMMAND_SPAM_LIMIT} cmds/{COMMAND_SPAM_WINDOW}s`\n"
                f"🚪 Raid: `{RAID_JOIN_LIMIT} entradas/{RAID_JOIN_WINDOW}s`\n"
                f"💬 Spam MSG: `{MSG_SPAM_LIMIT} msgs/{MSG_SPAM_WINDOW}s`\n"
                f"⚠️ Risco Suspeito: `≥{RISK_SUSPICIOUS_THRESHOLD} pts`"
            ))
            boot.add_field(name="🟢 Status do Sistema", inline=False, value=(
                f"**Nível:** `NORMAL` | **Servidor:** `{guild.name}`\n"
                f"**Membros:** `{guild.member_count}` | **Iniciado:** `{now.strftime('%d/%m/%Y %H:%M UTC')}`"
            ))
            boot.set_footer(text="VAMPY SECURITY SYSTEM • Todos os sistemas operacionais.",
                            icon_url=self.bot.user.display_avatar.url if self.bot.user else None)
            await ch.send(embed=boot)

            # Embed de Comandos
            cmds = discord.Embed(title="📋 Comandos — VAMPY SECURITY", color=0x5865F2, timestamp=now)
            cmds.add_field(name="🔍 Status & Info", inline=False, value=(
                "`v!security status` — Painel completo\n"
                "`v!segurança status` — Alias PT\n"
                "`v!security riskscore @user` — Risco do usuário\n"
                "`v!security flagged` — Usuários suspeitos"
            ))
            cmds.add_field(name="🔧 Administração", inline=False, value=(
                "`v!security reset` — Limpar alertas\n"
                "`v!security lockdown on/off` — Lockdown manual\n"
                "`v!security emergency on/off` — Modo emergência\n"
                "`v!security unflag @user` — Remover flag\n"
                "`v!security alerts` — Últimos 10 alertas\n"
                "`v!security stats` — Estatísticas gerais"
            ))
            cmds.add_field(name="⚠️ Permissão", value="Todos os comandos exigem **Administrador**.", inline=False)
            cmds.set_footer(text="VAMPY SECURITY SYSTEM • GOD MODE v2.0")
            await ch.send(embed=cmds)

    # ── 1️⃣ Anti-Spam de Comandos ─────────────────

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        if ctx.author.bot:
            return
        uid = ctx.author.id
        if uid in self._cmd_cooldowns:
            release = self._cmd_cooldowns[uid]
            if datetime.utcnow() < release:
                remaining = (release - datetime.utcnow()).seconds
                try: await ctx.message.delete()
                except: pass
                await ctx.send(f"⛔ {ctx.author.mention} cooldown de segurança. Aguarde `{remaining}s`.", delete_after=5)
                return
        dq = self._cmd_timestamps[uid]
        dq.append(self._now())
        self._prune(dq, COMMAND_SPAM_WINDOW)
        if len(dq) > COMMAND_SPAM_LIMIT:
            self.db.add_risk(uid, RISK_SPAM_CMD, "Spam de comandos")
            self.db.spam_events += 1
            self._cmd_cooldowns[uid] = datetime.utcnow() + timedelta(seconds=COMMAND_COOLDOWN_TIME)
            dq.clear()
            await self.send_alert(ctx.guild, "SPAM DE COMANDOS / SCRIPT", ctx.author,
                f"**{ctx.author}** executou `{COMMAND_SPAM_LIMIT}+` cmds em `{COMMAND_SPAM_WINDOW}s`.\n"
                f"Cooldown: `{COMMAND_COOLDOWN_TIME}s` | Risco: `{self.db.get_risk(uid)} pts`",
                color=0xff8800)

    # ── 2️⃣+3️⃣+🔟 Raid / Lockdown / Emergência ──

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        gid   = guild.id
        dq    = self._join_timestamps[gid]
        dq.append(self._now())
        self._prune(dq, RAID_JOIN_WINDOW)
        count = len(dq)

        if count >= LOCKDOWN_THRESHOLD and not self.db.emergency_mode:
            self.db.emergency_mode = self.db.lockdown_active = True
            self.db.security_level = "EMERGÊNCIA"
            self.db.raid_events += 1
            await self.send_alert(guild, "🔴 RAID SEVERO — MODO EMERGÊNCIA ATIVADO", None,
                f"**{count}** membros em `{RAID_JOIN_WINDOW}s`.\n⛔ Emergência ativada. Use `!security emergency off` para desativar.",
                color=0xff0000, critical=True)
            await self._apply_lockdown(guild, True)
        elif count >= RAID_JOIN_LIMIT and not self.db.lockdown_active:
            self.db.security_level = "ALERTA"
            self.db.raid_events += 1
            await self.send_alert(guild, "POSSÍVEL RAID DETECTADO", None,
                f"**{count}** membros nos últimos `{RAID_JOIN_WINDOW}s`.\n⚠️ Modo Alerta ativado.",
                color=0xff8800, critical=True)

        await self._check_suspicious_account(member)
        if member.bot:
            await self._check_suspicious_bot(member)

    async def _apply_lockdown(self, guild: discord.Guild, activate: bool):
        everyone = guild.default_role
        for ch in guild.text_channels:
            try:
                ow = ch.overwrites_for(everyone)
                ow.send_messages = False if activate else None
                await ch.set_permissions(everyone, overwrite=ow)
            except: pass

    # ── 4️⃣ Spam de Chat ──────────────────────────
    # Monitoramento restrito ao canal 💭・chat-geral.
    # O bot APENAS relata no log — nunca deleta nem toma ação automática.

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Monitora spam SOMENTE no chat-geral e apenas relata no canal de monitoramento."""
        if message.author.bot or not message.guild:
            return

        # So analisa spam no chat-geral — qualquer outro canal e ignorado
        if message.channel.name != CANAL_GERAL:
            return

        uid     = message.author.id
        content = message.content

        # Flood de mensagens — apenas relata, sem deletar
        dq = self._msg_timestamps[uid]
        dq.append(self._now())
        self._prune(dq, MSG_SPAM_WINDOW)
        if len(dq) > MSG_SPAM_LIMIT:
            self.db.add_risk(uid, RISK_SPAM_MSG, "Flood de mensagens")
            self.db.spam_events += 1
            dq.clear()
            await self.send_alert(message.guild, "FLOOD DE MENSAGENS", message.author,
                f"Mais de `{MSG_SPAM_LIMIT}` msgs em `{MSG_SPAM_WINDOW}s`.\n"
                f"Canal: {message.channel.mention}\n"
                f"Risco acumulado: `{self.db.get_risk(uid)} pts`\n"
                f"Nenhuma acao automatica — cabe a staff agir.",
                color=0xff6600)
            return

        # Mensagens repetidas — apenas relata, sem deletar
        hist = self._last_msg.setdefault(uid, [])
        hist.append(content)
        if len(hist) > MSG_REPEAT_LIMIT: hist.pop(0)
        if len(hist) == MSG_REPEAT_LIMIT and len(set(hist)) == 1:
            self.db.add_risk(uid, RISK_SPAM_MSG, "Spam repetido")
            self.db.spam_events += 1
            hist.clear()
            await self.send_alert(message.guild, "MENSAGENS REPETIDAS (SPAM)", message.author,
                f"Mesma mensagem enviada `{MSG_REPEAT_LIMIT}x` seguidas.\n"
                f"Conteudo: `{content[:100]}`\n"
                f"Canal: {message.channel.mention}\n"
                f"Nenhuma acao automatica — cabe a staff agir.",
                color=0xff6600)
            return

        # Spam de emojis — apenas relata, sem deletar
        ec = len(re.findall(r"<a?:\w+:\d+>|[\U0001F300-\U0001FAFF]", content))
        if ec >= EMOJI_SPAM_LIMIT:
            self.db.add_risk(uid, RISK_SPAM_MSG, "Spam de emojis")
            await self.send_alert(message.guild, "SPAM DE EMOJIS", message.author,
                f"**{ec}** emojis em uma unica mensagem.\n"
                f"Canal: {message.channel.mention}\n"
                f"Nenhuma acao automatica — cabe a staff agir.",
                color=0xffaa00)
            return

        # Spam de mencoes — apenas relata, sem deletar
        mc = len(message.mentions) + len(message.role_mentions)
        if mc >= MENTION_SPAM_LIMIT:
            self.db.add_risk(uid, RISK_SPAM_MSG, "Spam de mencoes")
            await self.send_alert(message.guild, "SPAM DE MENCOES", message.author,
                f"**{mc}** mencoes em uma unica mensagem.\n"
                f"Canal: {message.channel.mention}\n"
                f"Nenhuma acao automatica — cabe a staff agir.",
                color=0xff8800)
            return

        # Links maliciosos — apenas relata, sem deletar
        if re.search(r"https?://", content, re.IGNORECASE):
            await self._check_malicious_link(message)

    # ── 5️⃣ Ações Administrativas ────────────────

    @commands.Cog.listener()
    async def on_guild_channel_create(self, ch):
        await self._admin_action(ch.guild, "CANAL CRIADO", f"Canal `{ch.name}` criado.")
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, ch):
        await self._admin_action(ch.guild, "CANAL DELETADO", f"Canal `{ch.name}` deletado.")
    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        await self._admin_action(role.guild, "CARGO CRIADO", f"Cargo `{role.name}` criado.")
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        await self._admin_action(role.guild, "CARGO DELETADO", f"Cargo `{role.name}` deletado.")
    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        await self._admin_action(guild, "BANIMENTO", f"Usuário `{user}` banido.")

    async def _admin_action(self, guild, action_type, details):
        gid = guild.id
        dq  = self._admin_timestamps[gid]
        dq.append(self._now())
        self._prune(dq, ADMIN_ACTION_WINDOW)
        self.db.admin_events += 1
        if len(dq) >= ADMIN_ACTION_LIMIT:
            dq.clear()
            await self.send_alert(guild, f"AVALANCHE ADMIN — {action_type}", None,
                f"`{ADMIN_ACTION_LIMIT}+` ações em `{ADMIN_ACTION_WINDOW}s`.\nÚltima: {details}\n⚠️ Possível ataque.",
                color=0xff4400, critical=True)
        else:
            ch = await self.get_log_channel(guild)
            if ch:
                embed = discord.Embed(title="🔧 Ação Administrativa", description=details, color=0x5865F2, timestamp=datetime.utcnow())
                embed.set_footer(text=f"VAMPY SECURITY • Ações na janela: {len(dq)}/{ADMIN_ACTION_LIMIT}")
                await ch.send(embed=embed)

    # ── 6️⃣ Bot Suspeito ──────────────────────────

    async def _check_suspicious_bot(self, member: discord.Member):
        guild = member.guild
        adder = None
        try:
            async for entry in guild.audit_logs(limit=5, action=discord.AuditLogAction.bot_add):
                if entry.target.id == member.id:
                    adder = entry.user; break
        except: pass
        is_admin = adder.guild_permissions.administrator if adder else False
        await self.send_alert(guild, "BOT ADICIONADO AO SERVIDOR", member,
            f"**Bot:** `{member.name}` (ID: `{member.id}`)\n"
            f"**Por:** {adder} (`{adder.id if adder else '?'}`)\n"
            f"**Admin:** {'✅ Sim' if is_admin else '⛔ NÃO — SUSPEITO!'}",
            color=0xff0000 if not is_admin else 0xffaa00, critical=not is_admin)

    # ── 7️⃣ Links Maliciosos ──────────────────────

    async def _check_malicious_link(self, message: discord.Message):
        cl = message.content.lower()
        for pattern in MALICIOUS_PATTERNS:
            if re.search(pattern, cl, re.IGNORECASE):
                self.db.add_risk(message.author.id, RISK_LINK, "Link malicioso")
                self.db.link_events += 1
                # Apenas relata — nao deleta a mensagem
                await self.send_alert(message.guild, "LINK MALICIOSO / PHISHING", message.author,
                    f"Padrao detectado: `{pattern}`\n"
                    f"Canal: {message.channel.mention}\n"
                    f"Previa: `{message.content[:120]}`\n"
                    f"Nenhuma acao automatica — cabe a staff agir.",
                    color=0xff0000, critical=True)
                return

    # ── 11️⃣ Contas Suspeitas ─────────────────────

    async def _check_suspicious_account(self, member: discord.Member):
        uid      = member.id
        age_days = (datetime.utcnow() - member.created_at.replace(tzinfo=None)).days
        flags    = []
        if age_days < ACCOUNT_MIN_AGE_DAYS:
            self.db.add_risk(uid, RISK_NEW_ACCOUNT, "Conta recente")
            flags.append(f"🆕 Conta criada há `{age_days}` dia(s)")
        if member.display_avatar.url == member.default_avatar.url:
            self.db.add_risk(uid, RISK_NO_AVATAR, "Sem avatar")
            flags.append("🖼️ Sem avatar personalizado")
        if re.match(r"^[a-z]+\d{4,}$", member.name.lower()):
            self.db.add_risk(uid, 2, "Nome padrão bot")
            flags.append(f"🤖 Nome suspeito: `{member.name}`")
        if flags:
            await self.send_alert(member.guild, "CONTA SUSPEITA ENTROU NO SERVIDOR", member,
                "Fatores de risco:\n" + "\n".join(flags) + f"\n\n**Risco total:** `{self.db.get_risk(uid)} pts`",
                color=0xffaa00)

    # ── 13️⃣ Erros do Bot ─────────────────────────

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.CommandNotFound): return
        if isinstance(error, commands.MissingPermissions):
            await self.send_alert(ctx.guild, "USO SEM PERMISSÃO", ctx.author,
                f"Tentou usar `{ctx.command}` sem permissão.\nCanal: {ctx.channel.mention}", color=0xffaa00)
        else:
            ch = await self.get_log_channel(ctx.guild)
            if ch:
                embed = discord.Embed(title="⚠️ Erro no Bot",
                    description=f"```{type(error).__name__}: {str(error)[:300]}```",
                    color=0xff6600, timestamp=datetime.utcnow())
                embed.add_field(name="Comando", value=f"`{ctx.command}`", inline=True)
                embed.add_field(name="Usuário",  value=str(ctx.author),   inline=True)
                embed.set_footer(text="VAMPY SECURITY • Monitor de Erros")
                await ch.send(embed=embed)

    # ── 🧹 Limpeza periódica ──────────────────────

    @tasks.loop(minutes=10)
    async def cleanup_task(self):
        for uid in list(self._cmd_timestamps.keys()): self._prune(self._cmd_timestamps[uid], COMMAND_SPAM_WINDOW)
        for uid in list(self._msg_timestamps.keys()): self._prune(self._msg_timestamps[uid], MSG_SPAM_WINDOW)
        for gid in list(self._join_timestamps.keys()): self._prune(self._join_timestamps[gid], RAID_JOIN_WINDOW * 10)
        expired = [u for u, t in self._cmd_cooldowns.items() if datetime.utcnow() >= t]
        for u in expired: del self._cmd_cooldowns[u]

    @cleanup_task.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()

    # ── 14️⃣ Comandos Administrativos ─────────────

    @commands.group(name="security", aliases=["segurança"], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def security_group(self, ctx):
        await ctx.send("📋 Comandos: `status`, `reset`, `lockdown on/off`, `emergency on/off`, `alerts`, `stats`, `flagged`, `unflag @user`, `riskscore @user`.", delete_after=15)

    @security_group.command(name="status")
    @commands.has_permissions(administrator=True)
    async def security_status(self, ctx):
        db = self.db
        le = {"NORMAL":"🟢","ALERTA":"🟡","LOCKDOWN":"🔴","EMERGÊNCIA":"🆘"}.get(db.security_level,"⚪")
        embed = discord.Embed(title="🛡️ VAMPY SECURITY — Status", color=self._level_color(), timestamp=datetime.utcnow())
        embed.add_field(name="🔒 Sistema", inline=True, value=(
            f"**Nível:** {le} `{db.security_level}`\n"
            f"**Lockdown:** {'⛔ ATIVO' if db.lockdown_active else '✅ Off'}\n"
            f"**Emergência:** {'🆘 ATIVA' if db.emergency_mode else '✅ Off'}"))
        embed.add_field(name="📊 Eventos", inline=True, value=(
            f"🚨 Alertas: `{db.total_alerts}`\n💬 Spam: `{db.spam_events}`\n"
            f"🚪 Raid: `{db.raid_events}`\n🔗 Links: `{db.link_events}`\n🔧 Admin: `{db.admin_events}`"))
        embed.add_field(name="👤 Monitorados", inline=False, value=(
            f"⚠️ Com risco: `{len(db.risk_scores)}` | ⛔ Suspeitos: `{len(db.flagged_users)}` | 🕒 Cooldown: `{len(self._cmd_cooldowns)}`"))
        embed.set_footer(text="VAMPY SECURITY SYSTEM • GOD MODE v2.0")
        await ctx.send(embed=embed)

    @security_group.command(name="reset")
    @commands.has_permissions(administrator=True)
    async def security_reset(self, ctx):
        self.db.reset(); self._cmd_timestamps.clear(); self._msg_timestamps.clear()
        self._join_timestamps.clear(); self._admin_timestamps.clear()
        self._cmd_cooldowns.clear(); self._last_msg.clear()
        embed = discord.Embed(title="✅ Sistema Resetado", description="Alertas, cooldowns e pontuações limpos.", color=0x00ff99, timestamp=datetime.utcnow())
        embed.set_footer(text=f"Resetado por {ctx.author}")
        await ctx.send(embed=embed)
        await self.send_alert(ctx.guild, "SISTEMA RESETADO", ctx.author, f"Reset manual por **{ctx.author}**.", color=0x5865F2)

    @security_group.command(name="lockdown")
    @commands.has_permissions(administrator=True)
    async def security_lockdown(self, ctx, state: str = "on"):
        activate = state.lower() in ("on", "ativar", "ligar")
        self.db.lockdown_active = activate
        self.db.security_level  = "LOCKDOWN" if activate else "NORMAL"
        await self._apply_lockdown(ctx.guild, activate)
        color = 0xff4400 if activate else 0x00ff99
        await ctx.send(embed=discord.Embed(title=f"🔒 Lockdown {'⛔ ATIVADO' if activate else '✅ DESATIVADO'}",
            description=f"Por {ctx.author.mention}.", color=color, timestamp=datetime.utcnow()))
        await self.send_alert(ctx.guild, f"LOCKDOWN {'ATIVADO' if activate else 'DESATIVADO'} MANUALMENTE",
            ctx.author, f"**{ctx.author}** {'ativou' if activate else 'desativou'} o lockdown.", color=color, critical=activate)

    @security_group.command(name="emergency")
    @commands.has_permissions(administrator=True)
    async def security_emergency(self, ctx, state: str = "on"):
        activate = state.lower() in ("on", "ativar", "ligar")
        self.db.emergency_mode = self.db.lockdown_active = activate
        self.db.security_level = "EMERGÊNCIA" if activate else "NORMAL"
        if activate: await self._apply_lockdown(ctx.guild, True)
        color = 0xff0000 if activate else 0x00ff99
        await ctx.send(embed=discord.Embed(title=f"⚡ Emergência {'🆘 ATIVADA' if activate else '✅ DESATIVADA'}",
            color=color, timestamp=datetime.utcnow()))

    @security_group.command(name="alerts")
    @commands.has_permissions(administrator=True)
    async def security_alerts(self, ctx):
        recent = self.db.alert_history[-10:]
        if not recent: return await ctx.send("✅ Nenhum alerta registrado.", delete_after=10)
        embed = discord.Embed(title="📋 Últimos 10 Alertas", color=0xff8800, timestamp=datetime.utcnow())
        for i, a in enumerate(reversed(recent), 1):
            t = a["time"].strftime("%d/%m %H:%M")
            embed.add_field(name=f"#{i} [{t}] {a['type']}", value=a["details"][:100], inline=False)
        embed.set_footer(text="VAMPY SECURITY • Histórico")
        await ctx.send(embed=embed)

    @security_group.command(name="stats")
    @commands.has_permissions(administrator=True)
    async def security_stats(self, ctx):
        db = self.db
        embed = discord.Embed(title="📊 Estatísticas do Sistema", color=0x5865F2, timestamp=datetime.utcnow())
        embed.add_field(name="Alertas",   value=f"`{db.total_alerts}`",       inline=True)
        embed.add_field(name="Spam",      value=f"`{db.spam_events}`",        inline=True)
        embed.add_field(name="Raid",      value=f"`{db.raid_events}`",        inline=True)
        embed.add_field(name="Links",     value=f"`{db.link_events}`",        inline=True)
        embed.add_field(name="Admin",     value=f"`{db.admin_events}`",       inline=True)
        embed.add_field(name="Suspeitos", value=f"`{len(db.flagged_users)}`", inline=True)
        await ctx.send(embed=embed)

    @security_group.command(name="flagged")
    @commands.has_permissions(administrator=True)
    async def security_flagged(self, ctx):
        if not self.db.flagged_users: return await ctx.send("✅ Nenhum suspeito.", delete_after=10)
        embed = discord.Embed(title="⛔ Usuários Suspeitos", color=0xff4400, timestamp=datetime.utcnow())
        for uid, info in list(self.db.flagged_users.items())[:15]:
            embed.add_field(name=f"ID: {uid}",
                value=f"Motivo: `{info['reason']}`\nScore: `{info['score']} pts`\nEm: `{info['time'].strftime('%d/%m %H:%M')}`", inline=True)
        await ctx.send(embed=embed)

    @security_group.command(name="unflag")
    @commands.has_permissions(administrator=True)
    async def security_unflag(self, ctx, member: discord.Member):
        rf = self.db.flagged_users.pop(member.id, None)
        rs = self.db.risk_scores.pop(member.id, None)
        if rf or rs: await ctx.send(f"✅ Flag removido de **{member}**.", delete_after=10)
        else: await ctx.send(f"ℹ️ **{member}** não estava marcado.", delete_after=10)

    @security_group.command(name="riskscore")
    @commands.has_permissions(administrator=True)
    async def security_riskscore(self, ctx, member: discord.Member):
        score = self.db.get_risk(member.id)
        flag  = self.db.is_flagged(member.id)
        color = 0x00ff99 if score < 5 else (0xffaa00 if score < RISK_SUSPICIOUS_THRESHOLD else 0xff0000)
        embed = discord.Embed(title=f"🔎 Risco — {member.name}", color=color, timestamp=datetime.utcnow())
        embed.add_field(name="Score",    value=f"`{score} pts`",                    inline=True)
        embed.add_field(name="Limite",   value=f"`{RISK_SUSPICIOUS_THRESHOLD} pts`", inline=True)
        embed.add_field(name="Suspeito", value="⛔ SIM" if flag else "✅ Não",       inline=True)
        if flag:
            embed.add_field(name="Motivo", value=f"`{self.db.flagged_users[member.id]['reason']}`", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)

# ================= CONFIG =================

TOKEN = os.getenv("TOKEN")
DONO_ID = 769951556388257812

CANAL_GERAL = "💭・chat-geral"
CANAL_GAMES = "🎲・vampy-games"
CANAL_LIBERACAO = "✅・chat-staff-liberação"
CANAL_LOG = "❌・palavras-apagadas-bot"
CANAL_TICKET = "🎟️・ticket"
CANAL_ACESSO_FUNCOES = "🔒┃acesso-a-funções"
CANAL_EVENTO_CATALOGO = "evento-catalogo"
CANAL_ADVERTENCIAS = "⚠️・advertências" 
CANAL_DESABAFOS = "😮‍💨・desabafos"
CANAL_CHAT_ANJO = "🪽・chat-anjo"
CANAL_CHAT_CUPIDOS = "💘・chat-cupidos"
CANAL_CHAT_STAFF_GERAL = "🔰・chat-staff"
CANAL_RANKING_VAMPY = "🎰・ranking-vampy"
CANAL_LOJA_INFO = "💾・loja-vampy"
CANAL_DIRECAO = "👑・chat-direção"
CANAL_ATENCAO = "⚠️・atenção"

# GIFs e Imagens
BANNER_TICKET = "https://i.pinimg.com/originals/5d/92/5d/5d925dd101dba34f341148eace3cfe38.gif"
GIF_CATALOGO = "https://i.pinimg.com/originals/0a/1f/86/0a1f869c296b0c30454ffb56397b90fb.gif"
AVATAR_VAMPY = "https://cdn.discordapp.com/attachments/1304658653697019964/1338274026333671485/vampy_avatar.png"
GIF_ACERTO_VAMPY = "https://media.tenor.com/8yMrP1Cs7ykAAAAM/ninjala-ninjala-season6trailer.gif"

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
GIF_MONSTRO = "https://i.pinimg.com/originals/22/ba/4d/22ba4d403b0c9c172526be971b0c0ab7.gif"
GIF_VITORIA = "https://media.tenor.com/8yMrP1Cs7ykAAAAM/ninjala-ninjala-season6trailer.gif"
GIF_TAROT = "https://i.pinimg.com/originals/28/bc/9a/28bc9aad11a3d4251108c3a28fd980f3.gif"
GIF_ANIVERSARIO = "https://usagif.com/wp-content/uploads/2021/4fh5wi/flzanversariopt-7.gif"
GIF_DETETIVE = "https://i.pinimg.com/originals/d5/0c/7b/d50c7b0413ac64fd5653c6b97cef9a22.gif"
# GIFs — Novos Jogos v2.0
GIF_BLACKJACK = "https://media.tenor.com/7a2N_8jJXH0AAAAC/blackjack-casino.gif"
GIF_MINAS = "https://media.tenor.com/kEBJSwLWvZoAAAAC/minesweeper.gif"
GIF_DRAGAO = "https://media.tenor.com/OmLMoVFrGpQAAAAC/dragon-fire.gif"

# Cargos
CARGO_MEMBRO_NOVO = "Membro Novo. 🦇"
CARGO_MEMBROS = "Membros. 🦇"
CARGO_MODERADOR = "Moderador. 🦇"
CARGO_RECRUTADOR = "Recrutador. 🦇"
CARGO_ANJO = "Anjo. 🦇"
CARGO_CUPIDOS = "Cupidos"
CARGO_STAFF_EQUIPE = "Equipe Staff. 🦇"
CARGO_ADV_1 = "Advertência 1/3"
CARGO_ADV_2 = "Advertência 2/3"
CARGO_ADV_3 = "Advertência 3/3"
CARGOS_ADV_TODOS = ["Advertência 1/3", "Advertência 2/3", "Advertência 3/3"]

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

CARGOS_IMUNES_IDS = [
    1467349939922141297,  # LDT — Líder de Torcida
]

CARGO_TRANSLATE_ID = 1486130807117582416  # Translate — auto-tradução para PT

# ============== DADOS =================

tickets = {}
avisos_usuarios = {}       # user_id -> avisos atuais (0–3)
total_ciclos_usuario = {}  # user_id -> quantos ciclos completos de punição já levou
pontuacao_vampy = {}
jogo_em_andamento = {"tipo": None, "pergunta": None, "resposta": None, "venceu": False, "participantes_tentaram": []}

# Lógica Evento Silencioso
contador_mensagens_silencioso = 0
meta_mensagens_silencioso = 0
evento_silencioso_ativo = False

# ============== CARTAS DE TAROT =================

CARTAS_TAROT = [
    # 3 CARTAS SUPER SORTUDAS
    {"nome": "✨ O Sol", "mensagem": "A luz do sol ilumina seu caminho! Fortuna máxima te aguarda! 🌟", "coins": 1000, "tipo": "super_sorte"},
    {"nome": "🌟 A Estrela", "mensagem": "Os astros se alinham a seu favor! Grande riqueza te espera! ✨", "coins": 500, "tipo": "super_sorte"},
    {"nome": "🎴 O Mago", "mensagem": "O poder da manifestação está com você! Seus desejos se materializam! 🪄", "coins": 300, "tipo": "super_sorte"},
    
    # CARTAS BOAS (7 cartas)
    {"nome": "💫 A Roda da Fortuna", "mensagem": "A sorte gira a seu favor! Aproveite este momento! 🎡", "coins": 150, "tipo": "boa"},
    {"nome": "❤️ Os Enamorados", "mensagem": "O amor e a harmonia trazem prosperidade! 💕", "coins": 120, "tipo": "boa"},
    {"nome": "👑 O Imperador", "mensagem": "Poder e autoridade te recompensam! 👑", "coins": 100, "tipo": "boa"},
    {"nome": "🌙 A Lua", "mensagem": "Os mistérios noturnos revelam tesouros ocultos! 🌙", "coins": 80, "tipo": "boa"},
    {"nome": "🎭 O Louco", "mensagem": "A ousadia traz recompensas inesperadas! 🎪", "coins": 70, "tipo": "boa"},
    {"nome": "⚖️ A Justiça", "mensagem": "O equilíbrio universal te favorece! ⚖️", "coins": 60, "tipo": "boa"},
    {"nome": "🦁 A Força", "mensagem": "Sua coragem interior é recompensada! 💪", "coins": 50, "tipo": "boa"},
    
    # CARTAS NEUTRAS/ESPECIAIS (7 cartas)
    {"nome": "🔮 O Eremita", "mensagem": "A solidão traz reflexão... Escolha: DOAR 100 coins para alguém ou PEGAR 200 para você?", "coins": 0, "tipo": "escolha_doar"},
    {"nome": "🎲 A Roda do Destino", "mensagem": "O destino é incerto... Quer se ARRISCAR e puxar outra carta ou PARAR aqui?", "coins": 0, "tipo": "arriscar"},
    {"nome": "⚡ O Julgamento", "mensagem": "Seus atos retornam a você... Prepare-se para o karma!", "coins": -30, "tipo": "ruim"},
    {"nome": "🗡️ Cinco de Espadas", "mensagem": "A batalha teve um preço... Pequena perda!", "coins": -40, "tipo": "ruim"},
    {"nome": "🌊 Três de Copas", "mensagem": "Celebração moderada! Pequeno ganho!", "coins": 35, "tipo": "boa"},
    {"nome": "🏰 Quatro de Pentáculos", "mensagem": "Guarde seus recursos... Momento neutro.", "coins": 10, "tipo": "neutro"},
    {"nome": "🕊️ Dois de Copas", "mensagem": "União e parceria trazem equilíbrio.", "coins": 25, "tipo": "boa"},
    
    # 3 CARTAS BEM RUINS
    {"nome": "💀 A Morte", "mensagem": "O fim de um ciclo cobra seu preço... Grande perda te aguarda! 💀", "coins": -300, "tipo": "muito_ruim"},
    {"nome": "🗼 A Torre", "mensagem": "Tudo desmorona ao seu redor! Destruição e caos! ⚡", "coins": -200, "tipo": "muito_ruim"},
    {"nome": "😈 O Diabo", "mensagem": "As correntes da ganância te prendem! Você pagará caro! 🔗", "coins": -150, "tipo": "muito_ruim"},
]

# ============== CENÁRIOS DETETIVE =================

CENARIOS_DETETIVE = [
    {
        "caso": "O Roubo da Biblioteca",
        "personagens": ["Ana (bibliotecária)", "Bruno (estudante)", "Carlos (professor)"],
        "situacao": "Um livro raro desapareceu da biblioteca. Ana estava organizando prateleiras, Bruno estudava na mesa 5, e Carlos deu aula até às 18h. O livro sumiu entre 17h e 19h. As câmeras mostram que apenas Bruno saiu com uma mochila pesada.",
        "culpado": "bruno"
    },
    {
        "caso": "O Mistério do Bolo",
        "personagens": ["Marta (cozinheira)", "Pedro (garçom)", "Sofia (gerente)"],
        "situacao": "Um bolo de aniversário foi sabotado com sal. Marta preparou o bolo às 14h e guardou na geladeira. Pedro serviu às 18h. Sofia estava no escritório o dia todo. Só Pedro teve acesso à geladeira após Marta sair.",
        "culpado": "pedro"
    },
    {
        "caso": "O Quadro Desaparecido",
        "personagens": ["Lucas (segurança)", "Diana (curadora)", "Rafael (visitante)"],
        "situacao": "Um quadro sumiu do museu. Lucas vigiava a entrada, Diana fazia inventário no subsolo, Rafael visitava a exposição. As câmeras mostram Rafael perto do quadro minutos antes do alarme.",
        "culpado": "rafael"
    },
    {
        "caso": "A Janela Quebrada",
        "personagens": ["João (zelador)", "Carla (moradora)", "Miguel (entregador)"],
        "situacao": "A janela do apto 304 foi quebrada. João limpava o corredor, Carla estava viajando, Miguel entregou um pacote no 304. Vizinhos ouviram barulho durante a entrega de Miguel.",
        "culpado": "miguel"
    },
    {
        "caso": "O Celular Roubado",
        "personagens": ["Amanda (aluna)", "Ricardo (professor)", "Beatriz (faxineira)"],
        "situacao": "Um celular sumiu da sala de aula. Amanda saiu mais cedo, Ricardo deu aula normalmente, Beatriz limpou após todos saírem. Amanda voltou 'procurando' seu estojo e foi vista perto da mesa da vítima.",
        "culpado": "amanda"
    },
    {
        "caso": "O Veneno no Café",
        "personagens": ["Helena (secretária)", "Gustavo (estagiário)", "Patrícia (chefe)"],
        "situacao": "O café de Patrícia foi envenenado (mas ela não bebeu). Helena preparou o café às 9h. Gustavo serviu às 10h. Patrícia estava em reunião. Gustavo foi visto adicionando 'algo' na xícara.",
        "culpado": "gustavo"
    },
    {
        "caso": "A Carteira Sumida",
        "personagens": ["Felipe (taxista)", "Laura (passageira)", "Marcos (segurança)"],
        "situacao": "A carteira de Laura sumiu após táxi. Felipe dirigiu, Laura era passageira, Marcos vigiava o ponto. Laura esqueceu a carteira no banco. Felipe achou e não devolveu.",
        "culpado": "felipe"
    },
    {
        "caso": "O Documento Falsificado",
        "personagens": ["Renata (advogada)", "Thiago (cliente)", "Júlia (secretária)"],
        "situacao": "Um documento foi falsificado. Renata redigiu o original, Thiago solicitou, Júlia digitou e imprimiu. Thiago foi visto trocando páginas antes da assinatura.",
        "culpado": "thiago"
    },
    {
        "caso": "O Incêndio no Depósito",
        "personagens": ["Eduardo (gerente)", "Fernanda (estoquista)", "Roberto (ex-funcionário)"],
        "situacao": "O depósito pegou fogo. Eduardo estava de férias, Fernanda trabalhou até 17h, Roberto foi demitido semana passada. Câmeras mostram Roberto entrando no depósito às 20h.",
        "culpado": "roberto"
    },
    {
        "caso": "A Prova Vazada",
        "personagens": ["Professora Clara", "Aluno Daniel", "Monitor Vinícius"],
        "situacao": "A prova vazou antes da aplicação. Clara criou a prova, Daniel é aluno da turma, Vinícius monitora a disciplina. Vinícius teve acesso ao computador de Clara e enviou a prova para Daniel.",
        "culpado": "vinicius"
    },
    {
        "caso": "O Carro Arranhado",
        "personagens": ["Dono Sérgio", "Mecânico Luís", "Vizinho André"],
        "situacao": "O carro de Sérgio foi arranhado no estacionamento. Sérgio estava trabalhando, Luís consertava outro carro, André discutiu com Sérgio ontem. André foi visto com uma chave perto do carro.",
        "culpado": "andre"
    },
    {
        "caso": "A Joia Falsa",
        "personagens": ["Joalheiro Paulo", "Cliente Isabela", "Aprendiz Rodrigo"],
        "situacao": "Uma joia foi trocada por falsa. Paulo avaliou a joia, Isabela é a dona, Rodrigo estava aprendendo. Rodrigo trocou a joia verdadeira por falsa durante a limpeza.",
        "culpado": "rodrigo"
    },
    {
        "caso": "O Email Falso",
        "personagens": ["Gerente Camila", "TI Henrique", "Estagiária Letícia"],
        "situacao": "Um email falso foi enviado em nome de Camila. Camila estava em reunião, Henrique gerencia emails, Letícia usa computador próximo. Letícia acessou o email de Camila que estava aberto.",
        "culpado": "leticia"
    },
    {
        "caso": "O Vazamento de Água",
        "personagens": ["Encanador Fábio", "Proprietário Marcelo", "Inquilino Antônio"],
        "situacao": "O apartamento foi inundado. Fábio consertou cano ontem, Marcelo é o dono, Antônio mora lá. Fábio não apertou conexão corretamente, causando vazamento.",
        "culpado": "fabio"
    },
    {
        "caso": "A Receita Roubada",
        "personagens": ["Chef Marina", "Sous-chef Gabriel", "Crítico Raul"],
        "situacao": "A receita secreta foi roubada. Marina criou receita, Gabriel é sous-chef, Raul visitou cozinha. Gabriel fotografou receita e vendeu para concorrente.",
        "culpado": "gabriel"
    },
    {
        "caso": "O Acidente Forjado",
        "personagens": ["Motorista Alice", "Pedestre Bruno", "Testemunha Cláudia"],
        "situacao": "Acidente de trânsito foi forjado. Alice dirigia, Bruno 'foi atropelado', Cláudia viu tudo. Bruno se jogou de propósito no carro devagar para processar Alice.",
        "culpado": "bruno"
    },
    {
        "caso": "O Vírus no Sistema",
        "personagens": ["Analista Túlio", "Gerente Vanessa", "Hacker Externo Igor"],
        "situacao": "Sistema foi infectado. Túlio gerencia segurança, Vanessa aprova acessos, Igor é hacker conhecido. Túlio baixou arquivo suspeito que infectou rede.",
        "culpado": "tulio"
    },
    {
        "caso": "A Fraude no Caixa",
        "personagens": ["Caixa Simone", "Fiscal Leonardo", "Cliente Mário"],
        "situacao": "Dinheiro sumiu do caixa. Simone opera caixa, Leonardo fiscaliza, Mário era cliente. Simone desviava dinheiro e culpava sistema.",
        "culpado": "simone"
    },
    {
        "caso": "O Atestado Falso",
        "personagens": ["Médico Jorge", "Paciente Aline", "Recepcionista Bruna"],
        "situacao": "Atestado falso foi emitido. Jorge atende pacientes, Aline pediu atestado, Bruna agenda consultas. Bruna falsificou assinatura de Jorge para vender atestado para Aline.",
        "culpado": "bruna"
    },
    {
        "caso": "O Sabotador da Festa",
        "personagens": ["Organizadora Paula", "DJ Caio", "Ex-namorado Otávio"],
        "situacao": "Festa foi sabotada (som cortado, luzes apagadas). Paula organizou, Caio tocava, Otávio não foi convidado. Otávio invadiu cabine técnica e sabotou equipamentos.",
        "culpado": "otavio"
    }
]

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
"ABACAXI","VAMPY","BATMAN","CSI","DRAGAO","AVENTURA","ESTRELA",
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
"🐸","🦇","🐢","🦖","🐍","🦎","🍀",
"🐶","🐱","🐭","🐹","🐰","🦊","🐻","🐼","🐨","🐯","🦁","🐮","🐷",
"🐸","🐵","🙈","🙉","🙊","🐔","🐧","🐦","🐤","🐣","🐥","🦆","🦅",
"🦉","🦇","🐺","🐗","🐴","🦄","🐝","🐛","🦋","🐌","🐞","🐜",
"🪲","🪳","🕷","🕸","🦂","🐢","🐍","🦎","🦖","🦕",
"🐙","🦑","🦐","🦞","🦀","🐡","🐠","🐟","🐬","🐳","🐋","🦈",
"🐊","🐅","🐆","🦓","🦍","🦧","🐘","🦛","🦏","🐪","🐫","🦒",
"🦘","🦬","🐃","🐂","🐄","🐎","🐖","🐏","🐑","🦙","🐐",
"🦌","🐕","🐩","🦮","🐕‍🦺","🐈","🐓","🦃","🦚","🦜",
"🦢","🕊","🐇","🦝","🦨","🦡","🦫","🦦","🦥","🐁","🐀",
"🐿","🦔"
]


# ============== PALAVRAS PROIBIDAS =================
# Lógica: palavras soltas só disparam com boundary (\b), frases disparam por substring.
# Isso evita falsos positivos como "computar" → "puta", "burrice" → "burro", etc.

PALAVRAS_PROIBIDAS_EXATAS = [
    # palavrões isolados (serão verificados com \b word boundary)
    "porra", "caralho", "merda", "bosta", "viado", "bicha", "piranha",
    "arrombado", "buceta", "carai", "karalho",
]

FRASES_PROIBIDAS = [
    # Frases completas — não há falso positivo, contexto já é claro
    "vai se fuder", "vai se foder", "vai tomar no cu", "tomar no cu",
    "filho da puta", "filha da puta", "se mata", "se fode",
    "sua puta", "sua vadia", "puta que pariu", "puta merda",
    "vai a merda", "vai pra merda", "me fode", "me foder",
    "idiota mesmo", "idiota do",
    "que lixo você", "você é um lixo", "vc é um lixo",
    "puto da vida", "puta que", "fdp mesmo", "vsf mesmo",
]

def contem_palavra_proibida(texto: str):
    """Retorna a palavra/frase encontrada ou None. Usa boundary para palavras soltas."""
    # 1. Checar frases proibidas (substring simples — já são contextuais)
    for frase in FRASES_PROIBIDAS:
        if frase in texto:
            return frase
    # 2. Checar palavras exatas com word boundary
    for palavra in PALAVRAS_PROIBIDAS_EXATAS:
        # \b não funciona bem com acentos, mas cobre a maioria dos casos
        padrao = r'(?<![a-zA-ZÀ-ú])' + re.escape(palavra) + r'(?![a-zA-ZÀ-ú])'
        if re.search(padrao, texto):
            return palavra
    return None

# ============== PALAVRAS DE ALERTA (TRISTEZA/DEPRESSÃO) =================

PALAVRAS_ALERTA = [
    "suicidio", "suicídio", "me matar", "vou me matar", "quero morrer", "acabar com tudo",
    "depressão", "depressao", "tristeza", "triste", "sozinho", "sozinha", "vazio", "vazia",
    "não aguento", "nao aguento", "não aguento mais", "cansado de tudo", "cansada de tudo",
    "sem sentido", "ninguém se importa", "ninguem se importa", "ninguém liga", 
    "desistir", "desisti", "não vale a pena", "nao vale a pena", "melhor morrer",
    "me cortar", "auto mutilação", "automutilação", "auto mutilacao", "automutilacao",
    "nao quero mais viver", "não quero mais viver", "acabar com a vida", "tirar minha vida",
    "sem esperança", "sem esperanca", "desesperado", "desesperada", "ansiedade",
    "vontade de sumir", "quero sumir", "desaparecer", "sozinho no mundo", 
    "sem forças", "sem forcas", "exausto", "exausta", "esgotado", "esgotada",
    "angústia", "angustia", "pânico", "panico", "medo de tudo", "não consigo mais", "chorei demais", "me machucar", "Quero sair desse mundo", "me cortei", "eu me cortei", "cortei"
]

# ============== SISTEMA DE PUNIÇÕES PROGRESSIVAS =================

# Tabela de castigos por ciclo de punição (quantas vezes já completou os 3 avisos)
# Cada ciclo: [timeout_aviso1, timeout_aviso2, timeout_aviso3, timeout_banimento]
TABELA_CASTIGOS = [
    # ciclo 0 (primeira vez)
    [timedelta(minutes=5),  timedelta(minutes=15), timedelta(minutes=30), timedelta(days=1)],
    # ciclo 1 (reincidente)
    [timedelta(minutes=10), timedelta(minutes=30), timedelta(hours=1),    timedelta(days=3)],
    # ciclo 2
    [timedelta(minutes=20), timedelta(hours=1),    timedelta(hours=2),    timedelta(days=7)],
    # ciclo 3+
    [timedelta(hours=1),    timedelta(hours=3),    timedelta(hours=6),    timedelta(days=28)],
]

MSGS_AVISOS = [
    None,  # índice 0 não usado
    "Vc falou algo ruim!! infelizmente tive que te dar um aviso. cuidado com o segundo!! 🥺🦇",
    "Ai ai... **segundo aviso!!** Tá quase chegando no limite, toma muito cuidado com o terceiro, tá?? 😰🦇",
    "**TERCEIRO AVISO!!** Você tá no limite mesmo... se repetir isso vai tomar um castigo! 😱🦇 Respira fundo e volta calmo(a)!",
]

def obter_ciclo(user_id: int) -> int:
    """Retorna o índice do ciclo atual de punição (limitado ao último da tabela)."""
    ciclos = total_ciclos_usuario.get(user_id, 0)
    return min(ciclos, len(TABELA_CASTIGOS) - 1)

def obter_duracao_aviso(user_id: int, aviso: int) -> timedelta:
    ciclo = obter_ciclo(user_id)
    return TABELA_CASTIGOS[ciclo][aviso - 1]  # aviso 1→índice 0

def obter_duracao_banimento(user_id: int) -> timedelta:
    ciclo = obter_ciclo(user_id)
    return TABELA_CASTIGOS[ciclo][3]

def formatar_duracao(td: timedelta) -> str:
    total_segundos = int(td.total_seconds())
    if total_segundos < 3600:
        return f"{total_segundos // 60} minuto(s)"
    elif total_segundos < 86400:
        return f"{total_segundos // 3600} hora(s)"
    else:
        return f"{total_segundos // 86400} dia(s)"

async def gerenciar_cargo_advertencia(membro: discord.Member, qtd_avisos: int):
    """Remove todos os cargos de advertência e aplica o correto para o aviso atual."""
    guild = membro.guild
    # Remover todos os cargos de advertência existentes
    for nome_cargo in CARGOS_ADV_TODOS:
        cargo = discord.utils.get(guild.roles, name=nome_cargo)
        if cargo and cargo in membro.roles:
            try:
                await membro.remove_roles(cargo, reason="Atualização de cargo de advertência")
            except Exception:
                pass
    # Aplicar o cargo correto
    mapa = {1: CARGO_ADV_1, 2: CARGO_ADV_2, 3: CARGO_ADV_3}
    nome_novo = mapa.get(qtd_avisos)
    if nome_novo:
        cargo_novo = discord.utils.get(guild.roles, name=nome_novo)
        if cargo_novo:
            try:
                await membro.add_roles(cargo_novo, reason=f"Advertência {qtd_avisos}/3 aplicada pelo bot")
            except Exception:
                pass

async def remover_cargos_advertencia(membro: discord.Member):
    """Remove todos os cargos de advertência do membro."""
    guild = membro.guild
    for nome_cargo in CARGOS_ADV_TODOS:
        cargo = discord.utils.get(guild.roles, name=nome_cargo)
        if cargo and cargo in membro.roles:
            try:
                await membro.remove_roles(cargo, reason="Avisos zerados pela staff")
            except Exception:
                pass

async def enviar_log_palavras_apagadas(message, palavra_detectada: str, qtd_avisos: int, membro_id: int):
    """Envia a ficha completa da mensagem apagada para o canal ❌・palavras-apagadas-bot."""
    canal_log = discord.utils.get(message.guild.text_channels, name=CANAL_LOG)
    if not canal_log:
        return

    autor = message.author
    total_ciclos = total_ciclos_usuario.get(autor.id, 0)

    # Barra de avisos (bolinhas coloridas)
    avisos_emoji = ""
    cores_bola = ["🔴", "🟠", "🔴"]
    for i in range(1, 4):
        if i <= qtd_avisos:
            avisos_emoji += f"{cores_bola[i-1]} "
        else:
            avisos_emoji += "⚪ "

    # Cor do embed sobe com a gravidade
    cor_map = {1: 0xFFCC00, 2: 0xFF8800, 3: 0xFF2200}
    cor = cor_map.get(qtd_avisos, 0xFF0000)

    embed = discord.Embed(
        title="🗑️ MENSAGEM APAGADA PELO VAMPY",
        color=cor,
        timestamp=datetime.now()
    )
    embed.set_author(
        name=f"{autor.display_name}  •  @{autor.name}",
        icon_url=autor.display_avatar.url
    )
    embed.set_thumbnail(url=autor.display_avatar.url)

    # Linha separadora visual com dados principais
    embed.add_field(name="👤 Membro",       value=autor.mention,            inline=True)
    embed.add_field(name="🆔 ID",           value=f"`{autor.id}`",          inline=True)
    embed.add_field(name="📍 Canal",        value=message.channel.mention,  inline=True)

    # Conteúdo apagado
    conteudo = message.content[:900] if message.content else "*(sem texto — possível mídia)*"
    embed.add_field(
        name="💬 Mensagem apagada",
        value=f"```{conteudo}```",
        inline=False
    )
    embed.add_field(
        name="🔍 Gatilho detectado",
        value=f"```{palavra_detectada}```",
        inline=False
    )

    # Painel de status
    embed.add_field(
        name=f"⚠️ Avisos  ({qtd_avisos}/3)",
        value=avisos_emoji.strip(),
        inline=True
    )
    embed.add_field(
        name="📋 Advertências totais",
        value=f"**{total_ciclos}** vez(es) punido(a)",
        inline=True
    )

    embed.set_footer(
        text="🦇 Vampy Logs  •  Use os botões abaixo caso tenha sido engano",
        icon_url=AVATAR_VAMPY
    )

    view = DesfazerAvisoView(membro_id)
    await canal_log.send(embed=embed, view=view)

# ============== FUNÇÕES AUXILIARES =================

async def enviar_prologo_games(guild):
    """Envia um prólogo fofinho no canal de games quando o bot liga, explicando como funcionam os jogos."""
    canal_games = discord.utils.get(guild.text_channels, name=CANAL_GAMES)
    if not canal_games:
        return

    embed = discord.Embed(
        title="🦇💚 OI OI OI! O VAMPY ACORDOU! 💚🦇",
        description=(
            "AAAAA gente, eu tô de volta e tô com saudaaaaade de vocês! 🥺✨\n\n"
            "Deixa eu te contar como funcionam os meus joguinhos antes da gente começar a se divertir, tá bom? 🎮🐉"
        ),
        color=0xADFF2F
    )
    embed.set_thumbnail(url=AVATAR_VAMPY)
    embed.set_image(url=GIF_ACERTO_VAMPY)
    await canal_games.send(embed=embed)

    await asyncio.sleep(2)

    embed2 = discord.Embed(
        title="🎮 COMO FUNCIONAM OS JOGOS? 🎮",
        color=0x00FF7F
    )
    embed2.add_field(
        name="🧠 Pergunta Relâmpago",
        value="A Vampy faz uma pergunta e o primeiro que acertar ganha **80 coins**! Responda rápido no chat! ⚡ *(Sem penalidade por errar!)*",
        inline=False
    )
    embed2.add_field(
        name="🎯 Adivinhe o Número",
        value="Penso em um número de **1 a 50** — acertar vale **700 coins**! Errar custa **25 coins**. Dou dicas de **alto/baixo** a cada tentativa! 🎰",
        inline=False
    )
    embed2.add_field(
        name="✊ Pedra, Papel ou Tesoura",
        value="Me desafie digitando **pedra**, **papel** ou **tesoura**! Ganhar vale **200 coins**, perder custa **50**, empate **-25**. 🤜",
        inline=False
    )
    embed2.add_field(
        name="🪙 Cara ou Coroa",
        value="Digite **cara** ou **coroa** e torça! Acertar vale **200 coins**, errar custa **75**. 50/50 — pura sorte! 🍀",
        inline=False
    )
    embed2.add_field(
        name="🎲 Dado da Sorte",
        value="Escolha um número de **1 a 6**. Acertar vale **60 coins**, errar custa apenas **10**! Múltiplas tentativas permitidas! 🎲",
        inline=False
    )
    embed2.add_field(
        name="⚡ Palavra Rápida & Emoji Rápido",
        value="O primeiro que digitar a **palavra** ou mandar o **emoji** certo ganha **80 coins**! Velocidade é tudo! 💨",
        inline=False
    )
    embed2.set_thumbnail(url=AVATAR_VAMPY)
    await canal_games.send(embed=embed2)

    await asyncio.sleep(2)

    embed3 = discord.Embed(
        title="🌟 JOGOS ESPECIAIS DO VAMPY 🌟",
        color=0x9B59B6
    )
    embed3.add_field(
        name="🔤 Palavra Embaralhada",
        value="Vou embaralhar as letras de uma palavra e você descobre qual é! Acertar vale **150 coins**, errar custa **25**. 💡 *Dica: mostro quantas letras tem!* 🔡",
        inline=False
    )
    embed3.add_field(
        name="📦 Caixa Misteriosa",
        value="Escolha **1, 2 ou 3** e abra a caixa! Pode ter coins, prêmio raro (**450 coins!**) ou uma armadilha... 😈",
        inline=False
    )
    embed3.add_field(
        name="🏴‍☠️ Baú Perdido",
        value="Digite **ABRIR** para tentar a sorte! Pode ser um tesouro de **300 coins** ou um Mímico que te roba **100 coins**! 💀",
        inline=False
    )
    embed3.add_field(
        name="🤫 Evento Silencioso",
        value="A Vampy escolhe um **número secreto de mensagens**! Quem mandar a mensagem da sorte ganha **600 coins**! Shhh~ 🦇",
        inline=False
    )
    embed3.add_field(
        name="🎡 Roleta da Sorte Coletiva",
        value="Digite **ROLETA** para girar! TODOS podem participar ao mesmo tempo! Prêmios de **80 a 700 coins** ou chance de **DOBRAR tudo**! 🎰",
        inline=False
    )
    embed3.add_field(
        name="👹 Sobreviva ao Monstro",
        value="Enfrente o monstro com **ESCUDO** (50% de defesa, +150), **ESPADA** (1% épico, +700!) ou **FUGIR** (-50 coins mas seguro). TODOS jogam! ⚔️",
        inline=False
    )
    embed3.add_field(
        name="🔮 Tarot Místico",
        value="Digite **TAROT** e puxe sua carta do destino! Pode ganhar até **1000 coins** ou perder muito... As cartas não mentem! 🎴",
        inline=False
    )
    embed3.add_field(
        name="🕵️ Detetive",
        value="Leia o caso, descubra o culpado e escreva o **primeiro nome** do suspeito! Acertar vale **+300 coins**, errar custa **100**. 🔍",
        inline=False
    )
    embed3.add_field(
        name="🃏 Blackjack (NOVO!)",
        value="Digite **BLACKJACK** para entrar na mesa! Peça **HIT** ou pare com **STAND**. Blackjack = **+350 coins!** Perder = **-100 coins**. ♠️",
        inline=False
    )
    embed3.add_field(
        name="💣 Campo Minado (NOVO!)",
        value="Escolha uma casa de **1 a 9** num grid 3×3! 5 cofres (80-200 coins) e 4 minas escondidas (-100 coins). Confie no instinto! 💥",
        inline=False
    )
    embed3.add_field(
        name="🐉 Desafio do Dragão (NOVO!)",
        value="Um dragão apareceu! Use **CHAMA** (35%/+350), **GELO** (50%/+200) ou **OURO** (75%/+80) — cada estratégia tem seu risco! 🔥",
        inline=False
    )
    embed3.set_thumbnail(url=AVATAR_VAMPY)
    await canal_games.send(embed=embed3)

    await asyncio.sleep(2)

    embed4 = discord.Embed(
        title="💰 SISTEMA DE COINS 💰",
        description=(
            "Os **Vampy-Coins** são a moeda do servidor! Você ganha participando dos jogos e pode usar na **loja** para resgatar prêmios incríveis! 🛍️🦇\n\n"
            "🏆 Confira o ranking no canal de ranking e veja quem é o mais ricão do servidor!\n\n"
            "**Os jogos aparecem automaticamente a cada ~40 minutos, tá?** Fica de olho aqui! 👀💚\n\n"
            "*A Vampy ama cada um de vocês... agora bora jogar!* 🦇💚✨"
        ),
        color=0xFFD700
    )
    embed4.set_thumbnail(url=AVATAR_VAMPY)
    embed4.set_footer(text="Vampy-Games 🦇 | Boa sorte a todos! 💚")
    await canal_games.send(embed=embed4)

async def atualizar_ranking(guild):
    canal_rank = discord.utils.get(guild.text_channels, name=CANAL_RANKING_VAMPY)
    if not canal_rank: return
    
    rank_ordenado = sorted(pontuacao_vampy.items(), key=lambda item: item[1], reverse=True)
    
    embed = discord.Embed(
        title="🏆 RANKING VAMPY-COINS 🏆",
        description="Aqui estão os maiores gênios do nosso servidor! 🦇💚",
        color=0x00FF7F,
        timestamp=datetime.now()
    )
    embed.set_thumbnail(url=AVATAR_VAMPY)
    
    texto_rank = ""
    for i, (user_id, pontos) in enumerate(rank_ordenado[:15], 1):
        user = guild.get_member(user_id)
        nome = user.display_name if user else f"Usuário Desconhecido ({user_id})"
        texto_rank += f"**{i}º** | {nome} — `{pontos} Coins` 🦇\n"
    
    embed.description += f"\n\n{texto_rank if texto_rank else 'Ninguém pontuou ainda... 🥺'}"
    embed.set_footer(text="CSI - Sistema de Jogos")

    await canal_rank.purge(limit=5)
    await canal_rank.send(embed=embed)

async def verificar_palavras_alerta(message):
    """Verifica se a mensagem contém palavras que indicam tristeza/depressão"""
    if message.author.bot:
        return
    
    if message.channel.name == CANAL_DESABAFOS:
        return
    
    texto = message.content.lower()
    
    for palavra in PALAVRAS_ALERTA:
        if palavra in texto:
            canal_atencao = discord.utils.get(message.guild.text_channels, name=CANAL_ATENCAO)
            if canal_atencao:
                embed = discord.Embed(
                    title="⚠️ ALERTA - Possível Situação Delicada",
                    description=f"Uma mensagem com palavras de alerta foi detectada.",
                    color=0xFF6B6B,
                    timestamp=datetime.now()
                )
                embed.add_field(name="👤 Usuário", value=f"{message.author.mention} ({message.author.name})", inline=False)
                embed.add_field(name="📍 Canal", value=message.channel.mention, inline=True)
                embed.add_field(name="🔗 Link da Mensagem", value=f"[Clique aqui]({message.jump_url})", inline=True)
                embed.add_field(name="💬 Mensagem", value=f"```{message.content[:1000]}```", inline=False)
                embed.add_field(name="🔑 Palavra-chave detectada", value=f"`{palavra}`", inline=False)
                embed.set_thumbnail(url=message.author.display_avatar.url)
                embed.set_footer(text="Sistema de Monitoramento de Bem-Estar 🦇", icon_url=AVATAR_VAMPY)
                
                await canal_atencao.send(embed=embed)
            break

async def disparar_roleta(guild):
    canal_games = discord.utils.get(guild.text_channels, name=CANAL_GAMES)
    if not canal_games: return

    jogo_em_andamento["tipo"] = "roleta"
    jogo_em_andamento["venceu"] = False
    jogo_em_andamento["participantes_tentaram"] = []
    jogo_em_andamento["resposta"] = "roleta"

    embed = discord.Embed(color=0xADFF2F)
    embed.set_thumbnail(url=AVATAR_VAMPY)
    embed.title = "🎡 ROLETA DA SORTE COLETIVA! 🎰"
    embed.description = (
        "A roleta está girando para **TODOS**! ✨🦇\n\n"
        "Digite **ROLETA** para girar a sua!\n\n"
        "```\n"
        "🏆  TABELA DE PRÊMIOS\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💎  Jackpot     →  +700 coins  (1%)\n"
        "🥇  Grande      →  +150 coins  (25%)\n"
        "🥈  Médio       →  +80 coins   (25%)\n"
        "🎲  Bônus Jogo  →  Jogo extra  (14%)\n"
        "🔥  Dobrar!     →  x2 risco    (20%)\n"
        "💀  Azar        →  -100 coins  (15%)\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "```"
    )
    embed.set_image(url=GIF_ROLETA_GIRANDO)
    embed.set_footer(text="⏱️ Aberta por 5 minutos! Cada pessoa gira UMA vez. 🦇")
    
    await canal_games.send(embed=embed)

    await asyncio.sleep(300)
    
    jogo_em_andamento["venceu"] = True
    jogo_em_andamento["resposta"] = None
    await canal_games.send("🎡 A roleta parou de girar! Tempo encerrado! 🦇🏁")

async def disparar_tarot(guild):
    canal_games = discord.utils.get(guild.text_channels, name=CANAL_GAMES)
    if not canal_games: return

    jogo_em_andamento["tipo"] = "tarot"
    jogo_em_andamento["venceu"] = False
    jogo_em_andamento["participantes_tentaram"] = []
    jogo_em_andamento["resposta"] = "tarot"

    embed = discord.Embed(color=0x9B59B6)
    embed.set_thumbnail(url=AVATAR_VAMPY)
    embed.title = "🔮 TIRAGEM DO DESTINO — TAROT MÍSTICO 🔮"
    embed.description = (
        "As cartas ancestrais aguardam por **TODOS**! ✨🦇\n\n"
        "Digite **TAROT** para puxar sua carta do destino!\n\n"
        "```\n"
        "🎴  O que pode acontecer?\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✨  Super Sorte   →  +300 a +1000 coins\n"
        "💫  Boas Cartas   →  +35 a +150 coins\n"
        "🔮  Cartas Místicas → Escolhas especiais!\n"
        "💀  Cartas Ruins  →  -30 a -300 coins\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "```\n"
        "> ⚠️ Cada pessoa só pode puxar **UMA carta**!"
    )
    embed.set_image(url=GIF_TAROT)
    embed.set_footer(text="⏱️ 5 minutos para consultar o oráculo! As cartas não mentem... 🦇")
    
    await canal_games.send(embed=embed)

    await asyncio.sleep(300)
    
    jogo_em_andamento["venceu"] = True
    jogo_em_andamento["resposta"] = None
    await canal_games.send("🔮 As cartas se fecharam... o oráculo descansa até a próxima invocação! 🦇💫")

async def disparar_sobrevivamonstro(guild):
    canal_games = discord.utils.get(guild.text_channels, name=CANAL_GAMES)
    if not canal_games: return

    jogo_em_andamento["tipo"] = "sobrevivamonstro"
    jogo_em_andamento["venceu"] = False
    jogo_em_andamento["participantes_tentaram"] = []
    jogo_em_andamento["resposta"] = "sobrevivamonstro"

    embed = discord.Embed(color=0xFF4500)
    embed.set_thumbnail(url=AVATAR_VAMPY)
    embed.title = "👹 SOBREVIVA AO MONSTRO — HORDA APOCALÍPTICA! ⚔️"
    embed.description = (
        "Uma horda de monstros invadiu o chat! **TODOS** podem enfrentar! 🦇⚔️\n\n"
        "Escolha sua ação digitando:\n\n"
        "```\n"
        "⚔️  AÇÕES DISPONÍVEIS\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🛡️  ESCUDO  →  50% defesa  →  +150 coins\n"
        "             50% escudo quebra →  -50 coins\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚔️  ESPADA  →   1% épico   →  +700 coins\n"
        "             99% derrota   → -100 coins\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🏃  FUGIR   →  100% seguro  →  -50 coins\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "```\n"
        "> ⚠️ Você só pode participar **UMA vez** por evento!"
    )
    embed.set_image(url=GIF_MONSTRO)
    embed.set_footer(text="⏱️ 5 minutos para enfrentar seu monstro! Coragem, guerreiro! 🦇")
    
    await canal_games.send(embed=embed)

    await asyncio.sleep(300)
    
    jogo_em_andamento["venceu"] = True
    jogo_em_andamento["resposta"] = None
    await canal_games.send("👹 Os monstros recuaram! A batalha chegou ao fim! 🦇🏁")

async def disparar_detetive(guild):
    canal_games = discord.utils.get(guild.text_channels, name=CANAL_GAMES)
    if not canal_games: return

    cenario = random.choice(CENARIOS_DETETIVE)
    
    jogo_em_andamento["tipo"] = "detetive"
    jogo_em_andamento["venceu"] = False
    jogo_em_andamento["participantes_tentaram"] = []
    jogo_em_andamento["resposta"] = cenario["culpado"]
    jogo_em_andamento["pergunta"] = cenario["caso"]

    personagens_fmt = "\n".join([f"• {p}" for p in cenario["personagens"]])
    embed = discord.Embed(color=0x1E90FF)
    embed.set_thumbnail(url=AVATAR_VAMPY)
    embed.title = f"🕵️ CASO ABERTO: {cenario['caso'].upper()}"
    embed.add_field(name="👥 Suspeitos", value=personagens_fmt, inline=False)
    embed.add_field(name="📋 O que aconteceu", value=cenario["situacao"], inline=False)
    embed.add_field(
        name="🔍 Sua missão",
        value=(
            "Analise as pistas e descubra o culpado!\n"
            "Digite apenas o **PRIMEIRO NOME** do suspeito.\n\n"
            "✅ **Acertar:** +300 Coins\n"
            "❌ **Errar:** -100 Coins"
        ),
        inline=False
    )
    embed.set_image(url=GIF_DETETIVE)
    embed.set_footer(text="⏱️ 5 minutos para resolver o mistério! A Vampy acredita em você! 🦇🔍")
    
    await canal_games.send(embed=embed)

    for _ in range(300):
        if jogo_em_andamento["venceu"]: break
        await asyncio.sleep(1)
    
    if not jogo_em_andamento["venceu"]:
        jogo_em_andamento["pergunta"] = None
        jogo_em_andamento["resposta"] = None
        await canal_games.send(f"🕵️ O caso ficou sem solução... O culpado era **{cenario['culpado'].title()}**! Caso encerrado. 🦇💔")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🃏 NOVO JOGO: BLACKJACK (VINTE E UM)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _bj_card_value(card: str) -> int:
    """Retorna o valor de uma carta de blackjack (Ás = 11 inicialmente)."""
    if card in ["J", "Q", "K"]: return 10
    if card == "A": return 11
    return int(card)

def _bj_hand_value(hand: list) -> int:
    """Calcula o valor total da mão, ajustando Ás de 11→1 se necessário."""
    total = sum(_bj_card_value(c) for c in hand)
    ases = hand.count("A")
    while total > 21 and ases > 0:
        total -= 10
        ases -= 1
    return total

def _bj_draw(deck: list) -> str:
    return deck.pop(random.randint(0, len(deck) - 1))

def _bj_hand_str(hand: list) -> str:
    return "  ".join([f"`{c}`" for c in hand])

def _bj_new_deck() -> list:
    cartas = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"] * 4
    random.shuffle(cartas)
    return cartas

async def disparar_blackjack(guild):
    canal_games = discord.utils.get(guild.text_channels, name=CANAL_GAMES)
    if not canal_games: return

    jogo_em_andamento["tipo"] = "blackjack"
    jogo_em_andamento["venceu"] = False
    jogo_em_andamento["participantes_tentaram"] = []
    jogo_em_andamento["resposta"] = "blackjack"
    jogo_em_andamento["dados_blackjack"] = {}   # user_id → {"mao": [...], "deck": [...]}

    embed = discord.Embed(color=0xC0392B)
    embed.set_thumbnail(url=AVATAR_VAMPY)
    embed.title = "🃏 BLACKJACK — O DEALER ESTÁ NA MESA! 🃏"
    embed.description = (
        "A Vampy virou dealer e está distribuindo cartas! 🦇🎴\n\n"
        "Digite **BLACKJACK** para entrar e receber suas 2 cartas!\n"
        "Depois escolha:\n"
        "> 🃏 **HIT** — pedir mais uma carta\n"
        "> 🛑 **STAND** — parar e ver quem venceu\n\n"
        "```\n"
        "🏆  PAGAMENTOS\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌟  Blackjack (21 de cara) →  +350 coins\n"
        "✅  Vitória normal         →  +200 coins\n"
        "🤝  Empate                 →    +0 coins\n"
        "❌  Derrota / Estouro      →  -100 coins\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "```"
    )
    embed.set_image(url=GIF_BLACKJACK)
    embed.set_footer(text="⏱️ Mesa aberta por 5 minutos! Boa sorte! 🦇")

    await canal_games.send(embed=embed)
    await asyncio.sleep(300)

    jogo_em_andamento["venceu"] = True
    jogo_em_andamento["resposta"] = None
    jogo_em_andamento["dados_blackjack"] = {}
    await canal_games.send("🃏 A mesa de Blackjack foi encerrada! Até a próxima rodada! 🦇🏁")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💣 NOVO JOGO: CAMPO MINADO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def disparar_campominado(guild):
    canal_games = discord.utils.get(guild.text_channels, name=CANAL_GAMES)
    if not canal_games: return

    # Gera o campo: 5 cofres, 4 minas (posições 1-9)
    premios_cofres = [80, 100, 120, 150, 200]
    random.shuffle(premios_cofres)
    posicoes = list(range(1, 10))
    random.shuffle(posicoes)
    mapa_campo = {}
    for i, pos in enumerate(posicoes):
        if i < 5:
            mapa_campo[str(pos)] = ("cofre", premios_cofres[i])
        else:
            mapa_campo[str(pos)] = ("mina", -100)

    jogo_em_andamento["tipo"] = "campominado"
    jogo_em_andamento["venceu"] = False
    jogo_em_andamento["participantes_tentaram"] = []
    jogo_em_andamento["resposta"] = "campominado"
    jogo_em_andamento["dados_campo"] = mapa_campo

    embed = discord.Embed(color=0x2ECC71)
    embed.set_thumbnail(url=AVATAR_VAMPY)
    embed.title = "💣 CAMPO MINADO — CUIDADO COM AS BOMBAS! 💥"
    embed.description = (
        "A Vampy escondeu cofres e minas num campo 3×3! 🦇💰\n\n"
        "**Escolha uma casa digitando um número de 1 a 9:**\n\n"
        "```\n"
        "┌───┬───┬───┐\n"
        "│ 1 │ 2 │ 3 │\n"
        "├───┼───┼───┤\n"
        "│ 4 │ 5 │ 6 │\n"
        "├───┼───┼───┤\n"
        "│ 7 │ 8 │ 9 │\n"
        "└───┴───┴───┘\n"
        "```\n"
        "🟩 **5 cofres** escondidos (80 a 200 coins!)\n"
        "💣 **4 minas** perigosas (-100 coins)\n\n"
        "> ⚠️ Cada pessoa só pode escolher **UMA casa**!"
    )
    embed.set_image(url=GIF_MINAS)
    embed.set_footer(text="⏱️ 5 minutos para fazer sua escolha! Confie no seu instinto! 🦇")

    await canal_games.send(embed=embed)
    await asyncio.sleep(300)

    jogo_em_andamento["venceu"] = True
    jogo_em_andamento["resposta"] = None
    jogo_em_andamento["dados_campo"] = {}
    await canal_games.send("💣 Campo desarmado! Evento encerrado! 🦇🏁")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🐉 NOVO JOGO: DESAFIO DO DRAGÃO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def disparar_dragao(guild):
    canal_games = discord.utils.get(guild.text_channels, name=CANAL_GAMES)
    if not canal_games: return

    jogo_em_andamento["tipo"] = "dragao"
    jogo_em_andamento["venceu"] = False
    jogo_em_andamento["participantes_tentaram"] = []
    jogo_em_andamento["resposta"] = "dragao"

    embed = discord.Embed(color=0xFF6600)
    embed.set_thumbnail(url=AVATAR_VAMPY)
    embed.title = "🐉 DESAFIO DO DRAGÃO — ESCOLHA SUA ESTRATÉGIA! 🔥"
    embed.description = (
        "Um dragão lendário apareceu no servidor! **TODOS** podem enfrentá-lo! 🦇⚔️\n\n"
        "Escolha sua estratégia digitando:\n\n"
        "```\n"
        "🔥  ESTRATÉGIAS\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "CHAMA  →  Magia de fogo contra o dragão\n"
        "         35% ganhar +350 coins\n"
        "         65% o dragão ataca de volta -120 coins\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "GELO   →  Congelar o dragão com magia\n"
        "         50% ganhar +200 coins\n"
        "         50% o feitiço falha -100 coins\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "OURO   →  Subornar o dragão com tesouros\n"
        "         75% ele aceita +80 coins\n"
        "         25% ele fica com raiva -180 coins\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "```\n"
        "> ⚠️ Você só pode tentar **UMA vez** por evento!"
    )
    embed.set_image(url=GIF_DRAGAO)
    embed.set_footer(text="⏱️ 5 minutos para enfrentar o dragão! Seja corajoso! 🦇")

    await canal_games.send(embed=embed)
    await asyncio.sleep(300)

    jogo_em_andamento["venceu"] = True
    jogo_em_andamento["resposta"] = None
    await canal_games.send("🐉 O dragão voltou para sua caverna! Evento encerrado! 🦇🏁")

async def disparar_pergunta(guild, tipo_escolhido=None):
    canal_games = discord.utils.get(guild.text_channels, name=CANAL_GAMES)
    if not canal_games: return

    tipo_evento = tipo_escolhido if tipo_escolhido else random.choice([
        "pergunta", "numero", "ppt", "cara_coroa", "dado", "palavra", "emoji",
        "roleta", "embaralhada", "caixa", "silencioso", "bauperdido",
        "sobrevivamonstro", "tarot", "detetive",
        "blackjack", "campominado", "dragao"   # ← Novos jogos v2.0
    ])
    
    if tipo_evento == "tarot":
        await disparar_tarot(guild)
        return
    
    if tipo_evento == "sobrevivamonstro":
        await disparar_sobrevivamonstro(guild)
        return
    
    if tipo_evento == "detetive":
        await disparar_detetive(guild)
        return

    if tipo_evento == "blackjack":
        await disparar_blackjack(guild)
        return

    if tipo_evento == "campominado":
        await disparar_campominado(guild)
        return

    if tipo_evento == "dragao":
        await disparar_dragao(guild)
        return

    jogo_em_andamento["tipo"] = tipo_evento
    jogo_em_andamento["venceu"] = False
    jogo_em_andamento["participantes_tentaram"] = []

    embed = discord.Embed(color=0xADFF2F)
    embed.set_thumbnail(url=AVATAR_VAMPY)

    if tipo_evento == "pergunta":
        pergunta, response_str = random.choice(LISTA_PERGUNTAS)
        jogo_em_andamento["pergunta"] = pergunta
        jogo_em_andamento["resposta"] = response_str.lower()
        embed.title = "🦇 HORA DO JOGUINHO DO VAMPY! 🦇"
        embed.description = (
            f"Oii amiguinhos! Vamos ver quem é esperto? ✨\n\n"
            f"❓ **PERGUNTA:**\n> {pergunta}\n\n"
            f"⚡ **Seja o PRIMEIRO a acertar e ganhe 80 coins!**\n"
            f"*(Não tem penalidade por errar essa — só vai rápido! 💨)*"
        )

    elif tipo_evento == "numero":
        res = random.randint(1, 50)
        jogo_em_andamento["resposta"] = str(res)
        embed.title = "🎯 ADIVINHE O NÚMERO SECRETO!"
        embed.description = (
            "Estou pensando em um número **entre 1 e 50**...\n\n"
            "```\n"
            "💡  DICAS APÓS CADA TENTATIVA\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🔺  \"Muito alto!\"  → tente menor\n"
            "🔻  \"Muito baixo!\" → tente maior\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "```\n"
            "💰 **Acertar:** +700 coins | ❌ **Errar:** -25 coins\n"
            "*(Múltiplas tentativas permitidas!)*"
        )
        embed.set_image(url=GIF_ADIVINHE_NUMERO)

    elif tipo_evento == "ppt":
        jogo_em_andamento["resposta"] = "logic_ppt"
        embed.title = "✊ PEDRA, PAPEL OU TESOURA! ✌️"
        embed.description = (
            "Me desafie digitando: **pedra**, **papel** ou **tesoura**!\n\n"
            "```\n"
            "🏆  RESULTADOS\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "✅  Vitória  →  +200 coins\n"
            "🤝  Empate   →  -25 coins\n"
            "❌  Derrota  →  -50 coins\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "```\n"
            "A Vampy vai jogar ao mesmo tempo que você! 🦇"
        )
        embed.set_image(url=GIF_PPT)

    elif tipo_evento == "cara_coroa":
        jogo_em_andamento["resposta"] = random.choice(["cara", "coroa"])
        embed.title = "🪙 CARA OU COROA! A MOEDA ESTÁ NO AR!"
        embed.description = (
            "A moeda está girando... 🌀🪙\n\n"
            "Digite **cara** ou **coroa** — pura sorte!\n\n"
            "```\n"
            "✅  Acertar  →  +200 coins\n"
            "❌  Errar    →  -75 coins\n"
            "```\n"
            "> 50% de chance — confie no seu instinto! 🍀"
        )
        embed.set_image(url=GIF_CARA_COROA)

    elif tipo_evento == "dado":
        jogo_em_andamento["resposta"] = str(random.randint(1, 6))
        embed.title = "🎲 DADO DA SORTE — APOSTE UM NÚMERO!"
        embed.description = (
            "Estou rolando o dado... 🎲\n\n"
            "Digite um número de **1 a 6**!\n\n"
            "```\n"
            "✅  Acertar  →  +60 coins\n"
            "❌  Errar    →  -10 coins\n"
            "```\n"
            "> ~16.7% de chance. Sorte boa! 🍀\n"
            "*(Múltiplas tentativas permitidas!)*"
        )
        embed.set_image(url=GIF_DADO)

    elif tipo_evento == "palavra":
        palavra = random.choice(LISTA_PALAVRAS_RAPIDAS)
        jogo_em_andamento["resposta"] = palavra.lower()
        embed.title = "⚡ EVENTO RÁPIDO — DIGITAÇÃO VELOZ!"
        embed.description = (
            f"🏃 **VELOCIDADE É TUDO!**\n\n"
            f"O primeiro a digitar exatamente:\n\n"
            f"## ➤ **{palavra}**\n\n"
            f"vence e ganha **80 coins**! ⚡"
        )

    elif tipo_evento == "emoji":
        emoji = random.choice(LISTA_EMOJIS_RAPIDOS)
        jogo_em_andamento["resposta"] = emoji
        embed.title = "⚡ EVENTO DE EMOJI — SEJA O MAIS RÁPIDO!"
        embed.description = (
            f"🏃 **QUEM MANDA PRIMEIRO GANHA!**\n\n"
            f"Mande exatamente esse emoji:\n\n"
            f"# {emoji}\n\n"
            f"Ganha **80 coins**! ⚡"
        )

    elif tipo_evento == "roleta":
        await disparar_roleta(guild)
        return

    elif tipo_evento == "embaralhada":
        palavra = random.choice(LISTA_PALAVRAS_RAPIDAS)
        jogo_em_andamento["resposta"] = palavra.lower()
        jogo_em_andamento["pergunta"] = palavra   # Salvar original para dica
        lista_letras = list(palavra)
        random.shuffle(lista_letras)
        palavra_shuffled = "".join(lista_letras)
        embed.title = "🔤 PALAVRA EMBARALHADA — DESEMBARALHE!"
        embed.description = (
            f"A Vampy embaralhou as letras de uma palavra! 🔡\n\n"
            f"**Letras embaralhadas:**\n"
            f"# `{palavra_shuffled}`\n\n"
            f"💡 *Dica: tem {len(palavra)} letras!*\n\n"
            f"```\n"
            f"✅  Acertar  →  +150 coins\n"
            f"❌  Errar    →  -25 coins\n"
            f"```"
        )
        embed.set_image(url=GIF_EMBARALHADO)

    elif tipo_evento == "caixa":
        jogo_em_andamento["resposta"] = "caixa"
        embed.title = "📦 CAIXA MISTERIOSA — QUAL VOCÊ ESCOLHE?"
        embed.description = (
            "Três caixas estão na sua frente... O que será que tem dentro? 🦇✨\n\n"
            "Digite o número da caixa: **1**, **2** ou **3**!\n\n"
            "```\n"
            "📦 Caixa 1    →  ???\n"
            "📦 Caixa 2    →  ???\n"
            "📦 Caixa 3    →  ???\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎁  Moedas     →  +80 coins ou doação\n"
            "💎  Prêmio Raro →  +450 coins!\n"
            "💀  Armadilha  →  -50 coins\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "```\n"
            "> 🔮 Confie no seu pressentimento!"
        )
        embed.set_image(url=GIF_CAIXA_MISTERIOSA)

    elif tipo_evento == "bauperdido":
        jogo_em_andamento["resposta"] = "abrir"
        embed.title = "🏴‍☠️ O BAÚ PERDIDO APARECEU!"
        embed.description = (
            "Um baú antigo e misterioso apareceu no chat! 🦇✨\n\n"
            "Você vai arriscar? Digite **ABRIR** para descobrir!\n\n"
            "```\n"
            "🏆  Tesouro  →  +300 coins  (50%)\n"
            "💀  Mímico   →  -100 coins  (50%)\n"
            "```\n"
            "> 🎲 50/50! Você vai arriscar?\n"
            "> *(Apenas o PRIMEIRO que abrir conta!)*"
        )
        embed.set_image(url=GIF_BAU_PERDIDO)

    elif tipo_evento == "silencioso":
        global contador_mensagens_silencioso, meta_mensagens_silencioso, evento_silencioso_ativo
        contador_mensagens_silencioso = 0
        meta_mensagens_silencioso = random.randint(1, 20)
        evento_silencioso_ativo = True
        jogo_em_andamento["venceu"] = False
        
        embed.title = "🤫 EVENTO SILENCIOSO ATIVADO! SHHH..."
        embed.description = (
            "A Vampy escolheu um **número secreto de mensagens**! 🤫\n\n"
            "Continue conversando normalmente — alguém vai ter sorte!\n\n"
            "```\n"
            "💰  Prêmio: 600 coins\n"
            "📝  Dica: o número está entre 1 e 20\n"
            "```\n"
            "> *Shhh... não conta pra ninguém!* 🦇"
        )
        embed.set_image(url=GIF_SILENCIOSO)
        await canal_games.send(embed=embed)
        return

    embed.set_footer(text="⏱️ Você tem 5 minutos! Responda aqui no vampy-games! 🦇")
    await canal_games.send(embed=embed)

    for _ in range(300):
        if jogo_em_andamento["venceu"]: break
        await asyncio.sleep(1)
    
    if not jogo_em_andamento["venceu"]:
        jogo_em_andamento["pergunta"] = None
        jogo_em_andamento["resposta"] = None
        await canal_games.send("🥺 Ahhh poxa, ninguém acertou a tempo... A Vampy queria muito te dar um prêmio! 🦇💔")

# ============== LOOP DO JOGO =================

@tasks.loop(minutes=40)
async def loop_jogo_vampy():
    espera_extra = random.randint(0, 300)
    await asyncio.sleep(espera_extra)
    
    for guild in bot.guilds:
        await disparar_pergunta(guild)

# ============== SISTEMA DE LOJA =================

PRECOS_LOJA = {
    "cargo_7dias": 10000,
    "cargo_colorido": 18000,
    "evento_oficial": 25000,
    "item_jogo": 30000,
    "robux": 60000,
    "nitro": 150000
}

class LojaSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Cargo Exclusivo (7 dias)", value="cargo_7dias", description="🏷️ 10.000 Coins"),
            discord.SelectOption(label="Cargo Colorido Personalizado", value="cargo_colorido", description="🏷️ 18.000 Coins"),
            discord.SelectOption(label="Criar Evento Oficial", value="evento_oficial", description="🎉 25.000 Coins"),
            discord.SelectOption(label="Item de Jogo", value="item_jogo", description="🎮 30.000 Coins"),
            discord.SelectOption(label="Robux", value="robux", description="🎮 60.000 Coins"),
            discord.SelectOption(label="Discord Nitro (1 mês)", value="nitro", description="🎮 150.000 Coins"),
        ]
        super().__init__(placeholder="🎁 Escolha seu prêmio aqui...", options=options, custom_id="loja_select")

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        item = self.values[0]
        custo = PRECOS_LOJA[item]
        saldo = pontuacao_vampy.get(user_id, 0)

        if saldo < custo:
            embed_erro = discord.Embed(
                description=f"🥺 Oh, meu bem... você ainda não tem coins suficientes para esse prêmio! 🦇💔\n\nVocê tem: `{saldo} Coins` | Precisa de: `{custo} Coins`",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed_erro, ephemeral=True)

        pontuacao_vampy[user_id] -= custo
        await atualizar_ranking(interaction.guild)

        embed_sucesso = discord.Embed(
            title="🎁 RESGATE REALIZADO! 🦇💚",
            description=f"AAAA que felicidade, {interaction.user.mention}! ✨\n\nVocê resgatou: **{item.replace('_', ' ').title()}**!\n\nAgora é só aguardar um pouquinho que a staff já foi avisada e vai cuidar de tudo para você! Seu saldo foi atualizado. 🦇💖",
            color=0x00FF7F
        )
        await interaction.response.send_message(embed=embed_sucesso, ephemeral=True)

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

# ============== VIEWS =================

class DesfazerAvisoView(discord.ui.View):
    def __init__(self, membro_id: int):
        super().__init__(timeout=None)
        self.membro_id = membro_id

    @discord.ui.button(label="↩️ Desfazer Aviso", style=discord.ButtonStyle.success, custom_id="desfazer_aviso")
    async def desfazer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.moderate_members:
            return await interaction.response.send_message("❌ Apenas a staff pode desfazer avisos!", ephemeral=True)
        guild = interaction.guild
        membro = guild.get_member(self.membro_id)
        if not membro:
            return await interaction.response.send_message("❌ Membro não encontrado no servidor.", ephemeral=True)

        # Remove timeout se houver e zera os avisos
        try:
            await membro.timeout(None)
        except Exception:
            pass
        avisos_usuarios[self.membro_id] = 0
        total_ciclos_usuario[self.membro_id] = max(0, total_ciclos_usuario.get(self.membro_id, 0) - 1)
        await remover_cargos_advertencia(membro)

        button.label = f"✅ Desfeito por {interaction.user.display_name}"
        button.style = discord.ButtonStyle.secondary
        button.disabled = True
        await interaction.response.edit_message(view=self)

        canal_geral = discord.utils.get(guild.text_channels, name=CANAL_GERAL)
        if canal_geral:
            await canal_geral.send(
                f"✅ {membro.mention} a staff revisou e percebeu que foi sem querer! "
                f"Seus avisos foram zerados. Fica tranquilo(a)! 🦇💚"
            )

    @discord.ui.button(label="🔓 Remover Castigo/Timeout", style=discord.ButtonStyle.primary, custom_id="remover_castigo_v2")
    async def remover_castigo(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.moderate_members:
            return await interaction.response.send_message("❌ Apenas a staff pode remover castigos!", ephemeral=True)
        guild = interaction.guild
        membro = guild.get_member(self.membro_id)
        if not membro:
            return await interaction.response.send_message("❌ Membro não encontrado.", ephemeral=True)

        try:
            await membro.timeout(None)
        except Exception:
            pass
        await remover_cargos_advertencia(membro)

        button.label = f"🔓 Liberado por {interaction.user.display_name}"
        button.style = discord.ButtonStyle.secondary
        button.disabled = True
        await interaction.response.edit_message(view=self)

        canal_geral = discord.utils.get(guild.text_channels, name=CANAL_GERAL)
        if canal_geral:
            await canal_geral.send(
                f"⚠️ {membro.mention} foi liberado(a) pela staff. "
                f"Mas continue se comportando! 🦇💚"
            )

# Manter alias para compatibilidade com on_ready
LiberarCastigoView = DesfazerAvisoView

class AprovarMembroView(discord.ui.View):
    def __init__(self, membro_id: int):
        super().__init__(timeout=None)
        self.membro_id = membro_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("❌ Só a staff pode usar 😤🦇", ephemeral=True)
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
        cargo_membro = discord.utils.get(guild.roles, id=1304658653768581210)
        cargo_vampy_de = discord.utils.get(guild.roles, id=1432545143285743696)
        cargos_para_adicionar = [c for c in [cargo_membro, cargo_vampy_de] if c]
        if cargos_para_adicionar:
            await membro.add_roles(*cargos_para_adicionar)
        try: await membro.send("AAAA 😭🦇💚 Você foi APROVADO! Bem-vindo à famíliaaa!!! 💚✨")
        except: pass
        canal_geral = discord.utils.get(guild.text_channels, name=CANAL_GERAL)
        cargo_anjo = discord.utils.get(guild.roles, name=CARGO_ANJO)
        cargo_recrutador = discord.utils.get(guild.roles, name=CARGO_RECRUTADOR)
        cargo_ldt = discord.utils.get(guild.roles, id=1467349939922141297)
        mencoes = []
        if cargo_anjo: mencoes.append(cargo_anjo.mention)
        if cargo_recrutador: mencoes.append(cargo_recrutador.mention)
        if cargo_ldt: mencoes.append(cargo_ldt.mention)
        if canal_geral:
            canal_rpg = discord.utils.get(guild.text_channels, name="🌎・mundo-csi")
            canal_games = discord.utils.get(guild.text_channels, name=CANAL_GAMES)
            rpg_mention = canal_rpg.mention if canal_rpg else "#🌎・mundo-csi"
            games_mention = canal_games.mention if canal_games else "#🎲・vampy-games"
            msg_boas_vindas = (
                f"✨💚 tum tum tum… a Vampy apareceu! 💚✨\n\n"
                f"Atençãooo!! Temos alguém novo chegando no nosso cantinho 👀✨\n\n"
                f"Seja muito bem-vindo(a), {membro.mention}! 🫶 A Vampy já abriu espaço, ajeitou tudo por aqui e tá prontinha pra te acompanhar nessa nova fase.\n\n"
                f"🦇 {' 🦇 '.join(mencoes)}\n\n"
                f"Venham dar aquele abraço de boas-vindas que só a gente sabe dar 💚\n"
                f"Aqui você não entrou só em um servidor… Entrou em um lar.\n\n"
                f"A Vampy foi criada pelo Reality com um propósito simples e sincero: cuidar, proteger e lembrar que ninguém precisa enfrentar nada sozinho.\n\n"
                f"Então chega com calma, do seu jeito. Seu espaço já existe aqui. ✨\n\n"
                f"🌎 Curte RPG? Dá uma espiadinha no {rpg_mention} e entra na aventura!\n"
                f"🎲 Gosta de joguinhos? Te espero no {games_mention} pra gente se divertir!\n\n"
                f"Com carinho, Vampy. 💚"
            )
            await canal_geral.send(msg_boas_vindas)
        await interaction.followup.send("✅ Liberado com sucesso!", ephemeral=True)

    @discord.ui.button(label="⏳ Aguardar", style=discord.ButtonStyle.secondary, custom_id="aguardar_membro")
    async def aguardar(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🕒 Em análise 💚🦇", ephemeral=True)
        guild = interaction.guild
        membro = guild.get_member(self.membro_id)
        if membro:
            try: await membro.send("Oii neném 😭🦇💚 sua entrada tá sendo analisada pela staff, segura firme que já já te chamam, tá bom? 💚✨")
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
        if interaction.channel.name.startswith("👼┃anjos"):
            cargo_anjo = discord.utils.get(interaction.guild.roles, name=CARGO_ANJO)
            eh_staff = any(role.name in CARGOS_IMUNES_NOMES or role.id in CARGOS_IMUNES_IDS for role in interaction.user.roles)
            if (cargo_anjo not in interaction.user.roles) and not eh_staff:
                return await interaction.response.send_message("❌ Apenas os Anjos ou a Staff podem fechar este canal de acolhimento! 🪽", ephemeral=True)
        
        await interaction.response.send_message("🔒 Fechando este ticket em 5 segundinhos... tchau tchau! 🦇💚", ephemeral=True)
        await asyncio.sleep(5)
        await interaction.channel.delete()

class ReivindicarAnjoView(discord.ui.View):
    def __init__(self, canal_ticket_id: int):
        super().__init__(timeout=None)
        self.canal_ticket_id = canal_ticket_id

    @discord.ui.button(label="🤝 Assumir Chamado", style=discord.ButtonStyle.success, custom_id="reivindicar_anjo")
    async def reivindicar(self, interaction: discord.Interaction, button: discord.ui.Button):
        cargo_anjo = discord.utils.get(interaction.user.guild.roles, name=CARGO_ANJO)
        eh_staff = any(role.name in CARGOS_IMUNES_NOMES or role.id in CARGOS_IMUNES_IDS for role in interaction.user.roles)

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
            discord.SelectOption(label="📸 Evento Catálogo", value="catalogo"),
            discord.SelectOption(label="📣 Líder de Torcida", value="lider_torcida"),
            discord.SelectOption(label="👼 Pedir um Anjo", value="anjos"),
            discord.SelectOption(label="🔒 Acesso a Funções", value="acesso_funcoes"),
            discord.SelectOption(label="🎤 Influencer", value="influencer"),
            discord.SelectOption(label="🎬 Cineasta", value="cineasta"),
            discord.SelectOption(label="🎵 Sync", value="sync"),
        ]
        super().__init__(
            placeholder="🎟️ Selecione o tipo de ticket",
            options=options,
            custom_id="ticket_select_menu_v2"
        )

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user
        tipo = self.values[0]
        
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        }

        if tipo != "anjos":
            cargo_mod = discord.utils.get(guild.roles, name=CARGO_MODERADOR)
            if cargo_mod:
                overwrites[cargo_mod] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        categoria = interaction.channel.category
        pref = "👼┃" if tipo == "anjos" else "🎟️┃"
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
            
        elif tipo == "catalogo":
            embed_cat = discord.Embed(title="📸 EVENTO CATÁLOGO", color=0x00FFFF)
            embed_cat.description = f"{user.mention}, envie **APENAS A FOTO**."
            embed_cat.set_image(url=GIF_CATALOGO)
            await canal.send(embed=embed_cat)
            
        elif tipo == "lider_torcida":
            await canal.send(f"📣 **LÍDER DE TORCIDA**\n\n{user.mention}, conta pra staff por que você quer ser líder de torcida! 💚🦇", view=FecharTicketView())

        elif tipo == "acesso_funcoes":
            embed_acesso = discord.Embed(
                title="🔒 ACESSO A FUNÇÕES",
                description=f"{user.mention}, qual função você está solicitando acesso? Explique para a staff! 💚🦇",
                color=0xFFA500
            )
            await canal.send(embed=embed_acesso, view=FecharTicketView())

        elif tipo == "influencer":
            embed_influencer = discord.Embed(
                title="🎤 INFLUENCER",
                description=f"{user.mention}, nos conta sobre o seu perfil e por que você quer ser Influencer no servidor! 💚🦇",
                color=0xFF69B4
            )
            await canal.send(embed=embed_influencer, view=FecharTicketView())

        elif tipo == "cineasta":
            embed_cineasta = discord.Embed(
                title="🎬 CINEASTA",
                description=f"{user.mention}, nos conta sobre o seu trabalho audiovisual e por que você quer ser Cineasta no servidor! 💚🦇",
                color=0x8B0000
            )
            await canal.send(embed=embed_cineasta, view=FecharTicketView())

        elif tipo == "sync":
            embed_sync = discord.Embed(
                title="🎵 SYNC",
                description=f"{user.mention}, nos conta sobre a sua proposta de Sync e como você pode contribuir! 💚🦇",
                color=0x9B59B6
            )
            await canal.send(embed=embed_sync, view=FecharTicketView())

        else:
            await canal.send(f"🎟️ **NOVO TICKET**\n\n👤 {user.mention}", view=FecharTicketView())

        await interaction.response.send_message("✅ Ticket criado com sucesso! 💚🦇", ephemeral=True)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketSelect())

# ============== EVENTOS =================

@bot.event
async def on_ready():
    print(f"🦇 Ligado como {bot.user}")
    bot.add_view(TicketView())
    bot.add_view(FecharTicketView())
    bot.add_view(DesfazerAvisoView(0))
    bot.add_view(LojaView())
    bot.add_view(BanirMembroView())   # intercepta "Revogar banimento" + "Pronto" existentes
    
    if not loop_jogo_vampy.is_running():
        loop_jogo_vampy.start()

    for guild in bot.guilds:
        # Prólogo fofo no canal de games
        await enviar_prologo_games(guild)

        # Inicializar Tickets
        canal_tkt = discord.utils.get(guild.text_channels, name=CANAL_TICKET)
        if canal_tkt:
            try: await canal_tkt.purge(limit=5)
            except: pass
            await canal_tkt.send("🎟️ **CENTRAL DE TICKETS CSI** 🎟️\n\nSelecione abaixo para abrir um ticket 💚🦇", view=TicketView())
            embed_banner = discord.Embed(color=0x2b2d31)
            embed_banner.set_image(url=BANNER_TICKET)
            await canal_tkt.send(embed=embed_banner)

        # Inicializar Loja
        canal_loja = discord.utils.get(guild.text_channels, name=CANAL_LOJA_INFO)
        if canal_loja:
            try: await canal_loja.purge(limit=10)
            except: pass
            embed_loja = discord.Embed(
                title="🪙 Loja de Vampys Coins do Servidor",
                description=(
                    "🏷️ **Cargos**\n"
                    "• Cargo exclusivo por 7 dias — `10.000 coins`\n"
                    "• Cargo colorido personalizado — `18.000 coins`\n\n"
                    "🎉 **Interações**\n"
                    "• Criar um evento oficial (analisado pela staff) — `25.000 coins`\n\n"
                    "🎮 **Recompensas externas**\n"
                    "• Item de jogo (dependendo do jogo) — `30.000 coins`\n"
                    "• Robux — `60.000 coins`\n"
                    "• Discord Nitro (1 mês) — `150.000 coins`"
                ),
                color=0xFFD700
            )
            embed_loja.set_thumbnail(url=AVATAR_VAMPY)
            embed_loja.set_footer(text="Escolha seu item no menu abaixo! 🦇💚")
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
            f"**Ah não... minhas asinhas até murcharam agora...** 😭🦇💔\n\n"
            f"Poxa, {member.name}, a Vampy ficou muito, muito triste em ver você partindo da nossa família CSI. "
            f"Meu coração de código tá apertadinho aqui... 🥺💚\n\n"
            f"**Até logo, neném... vou sentir saudades!** 🦇💚👋"
        )
        await member.send(mensagem_despedida)
    except: pass

@bot.event
async def on_member_update(before, after):
    cargo_aniver = discord.utils.get(after.guild.roles, name="🎂 Aniversariante")
    if cargo_aniver and cargo_aniver not in before.roles and cargo_aniver in after.roles:
        canal_geral = discord.utils.get(after.guild.text_channels, name="🎉・aniversariante")
        if not canal_geral:
            return
        msgs_aniversario = [
            (
                f"✨🎂 ESPERA, ESPERA, ESPERA!! 🎂✨\n\n"
                f"Hoje é o dia mais especial do ano pra {after.mention}!! 🥳💚\n\n"
                f"A Vampy colocou o chapeuzinho, preparou o bolo e veio correndo te dar um abraço gigante!! 🦇🎉\n"
                f"Que esse dia seja tão lindo quanto você, cheio de amor, risada e tudo de bom que você merece!\n\n"
                f"**Feliz Aniversário, neném!! 🎂💚✨**"
            ),
            (
                f"🎉💚 TUM TUM TUM… adivinha quem faz aniversário HOJE?! 💚🎉\n\n"
                f"{after.mention}, a Vampy não ia deixar esse dia passar em branco não!! 🥺🦇\n\n"
                f"Vim aqui do fundo do coração te desejar um dia incrível, repleto de alegria, de pessoas que você ama e de muito, muito carinho!\n"
                f"Você merece tudo de melhor que esse mundo tem a oferecer! 🌟\n\n"
                f"**Parabéns pra você!! 🎂💚🎊**"
            ),
            (
                f"🦇💕 OI OI OI!! A Vampy ficou sabendo de um segredinho… 👀🎂\n\n"
                f"Hoje é o aniversário da nossa querida {after.mention}!! 🥳✨\n\n"
                f"Que a vida te presenteie com dias leves, sorrisos verdadeiros e muita coisa boa chegando por aí!\n"
                f"Aqui na nossa família a gente torce muito por você, saiba disso! 💚🫶\n\n"
                f"**Feliz Aniversário!! Seja muito feliz sempre!! 🎉🎂💚**"
            ),
        ]
        import random as _random
        mensagem = _random.choice(msgs_aniversario)
        embed_aniver = discord.Embed(description=mensagem, color=0x00FF7F)
        embed_aniver.set_image(url=GIF_ANIVERSARIO)
        await canal_geral.send(embed=embed_aniver)

@bot.event
async def on_message_delete(message):
    # Mensagens apagadas pelo bot por palavras proibidas são logadas diretamente na função de moderação.
    # Aqui só logamos deleções feitas manualmente por moderadores (não pelo bot).
    if message.author.bot:
        return

# ============== COMANDOS DE JOGOS INDIVIDUAIS =================

@bot.command()
async def jogo(ctx):
    if ctx.author.id != DONO_ID:
        return await ctx.send("❌ Só meu papai pode forçar o início de um jogo! 🦇")
    canal_games = discord.utils.get(ctx.guild.text_channels, name=CANAL_GAMES)
    if not canal_games:
        return await ctx.send(f"❌ Canal `{CANAL_GAMES}` não encontrado! Verifique o nome exato.")
    try:
        await ctx.message.delete()
    except Exception:
        pass
    await disparar_pergunta(ctx.guild)

@bot.command()
async def pergunta(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    try: await ctx.message.delete()
    except: pass
    await disparar_pergunta(ctx.guild, "pergunta")

@bot.command()
async def numero(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    try: await ctx.message.delete()
    except: pass
    await disparar_pergunta(ctx.guild, "numero")

@bot.command()
async def ppt(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    try: await ctx.message.delete()
    except: pass
    await disparar_pergunta(ctx.guild, "ppt")

@bot.command()
async def caracoroa(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    try: await ctx.message.delete()
    except: pass
    await disparar_pergunta(ctx.guild, "cara_coroa")

@bot.command()
async def dado(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    try: await ctx.message.delete()
    except: pass
    await disparar_pergunta(ctx.guild, "dado")

@bot.command()
async def palavra(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    try: await ctx.message.delete()
    except: pass
    await disparar_pergunta(ctx.guild, "palavra")

@bot.command()
async def emoji(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    try: await ctx.message.delete()
    except: pass
    await disparar_pergunta(ctx.guild, "emoji")

@bot.command()
async def embaralhada(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    try: await ctx.message.delete()
    except: pass
    await disparar_pergunta(ctx.guild, "embaralhada")

@bot.command()
async def caixa(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    try: await ctx.message.delete()
    except: pass
    await disparar_pergunta(ctx.guild, "caixa")

@bot.command()
async def bauperdido(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    try: await ctx.message.delete()
    except: pass
    await disparar_pergunta(ctx.guild, "bauperdido")

@bot.command()
async def roleta(ctx):
    if ctx.author.id != DONO_ID:
        return await ctx.send("❌ Só meu papai pode forçar o início da roleta! 🦇")
    try: await ctx.message.delete()
    except: pass
    await disparar_roleta(ctx.guild)

@bot.command()
async def silencioso(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    try: await ctx.message.delete()
    except: pass
    await disparar_pergunta(ctx.guild, "silencioso")

@bot.command()
async def sobrevivamonstro(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    try: await ctx.message.delete()
    except: pass
    await disparar_pergunta(ctx.guild, "sobrevivamonstro")

@bot.command()
async def tarot(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    try: await ctx.message.delete()
    except: pass
    await disparar_pergunta(ctx.guild, "tarot")

@bot.command()
async def detetive(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    try: await ctx.message.delete()
    except: pass
    await disparar_pergunta(ctx.guild, "detetive")

@bot.command(name="blackjack")
async def cmd_blackjack(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    canal_games = discord.utils.get(ctx.guild.text_channels, name=CANAL_GAMES)
    if not canal_games:
        return await ctx.send(f"❌ Canal `{CANAL_GAMES}` não encontrado! Verifique o nome.")
    try: await ctx.message.delete()
    except: pass
    await disparar_blackjack(ctx.guild)

@bot.command(name="campominado")
async def cmd_campominado(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    canal_games = discord.utils.get(ctx.guild.text_channels, name=CANAL_GAMES)
    if not canal_games:
        return await ctx.send(f"❌ Canal `{CANAL_GAMES}` não encontrado! Verifique o nome.")
    try: await ctx.message.delete()
    except: pass
    await disparar_campominado(ctx.guild)

@bot.command(name="dragao")
async def cmd_dragao(ctx):
    if ctx.author.id != DONO_ID: return await ctx.send("❌ Apenas o ADM pode usar!")
    canal_games = discord.utils.get(ctx.guild.text_channels, name=CANAL_GAMES)
    if not canal_games:
        return await ctx.send(f"❌ Canal `{CANAL_GAMES}` não encontrado! Verifique o nome.")
    try: await ctx.message.delete()
    except: pass
    await disparar_dragao(ctx.guild)

# ============== COMANDOS ADMINISTRATIVOS =================

@bot.command()
async def resetar_ranking(ctx):
    if ctx.author.id != DONO_ID:
        return await ctx.send("❌ Só meu papai pode resetar o ranking! 🦇😤")
    global pontuacao_vampy
    pontuacao_vampy = {}
    await atualizar_ranking(ctx.guild)
    await ctx.send("✅ **O Ranking de Vampy-Coins foi resetado com sucesso!** 🦇✨ Todos voltam ao zero!")

@bot.command()
async def bauadm(ctx):
    if ctx.author.id != DONO_ID:
        return await ctx.send("❌ Só meu papai pode abrir o Baú do ADM! 🦇💎")
    
    await ctx.send("💰 **BAÚ DO ADM!** 💰\n\nMeu papai, para quem você quer abrir o baú? Mencione (@) a pessoa sortuda agora! 🦇✨")
    
    def check_user(m):
        return m.author == ctx.author and m.channel == ctx.channel and len(m.mentions) > 0
    
    try:
        msg_user = await bot.wait_for("message", check=check_user, timeout=30)
        alvo = msg_user.mentions[0]
        
        await ctx.send(f"💎 Entendido! E quantos **Vampy-Coins** você quer dar para o(a) {alvo.mention}? 🦇💰")
        
        def check_quant(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()
        
        msg_quant = await bot.wait_for("message", check=check_quant, timeout=30)
        quantidade = int(msg_quant.content)
        
        pontuacao_vampy[alvo.id] = pontuacao_vampy.get(alvo.id, 0) + quantidade
        
        embed = discord.Embed(
            title="💎 O BAÚ DO ADM FOI ABERTO! 💎",
            description=f"O meu papai escolheu você, {alvo.mention}!\n\nVocê acaba de receber **{quantidade} Vampy-Coins** diretamente do tesouro real! 🦇💚✨",
            color=0xFFD700
        )
        embed.set_image(url="https://media.tenor.com/8yMrP1Cs7ykAAAAM/ninjala-ninjala-season6trailer.gif")
        
        await ctx.send(embed=embed)
        await atualizar_ranking(ctx.guild)
        
    except asyncio.TimeoutError:
        await ctx.send("⏰ O tempo acabou e o baú se fechou! 🦇")

@bot.command(name="removercastigo")
async def remover_castigo_manual(ctx, membro: discord.Member):
    eh_staff = any(role.name in CARGOS_IMUNES_NOMES or role.id in CARGOS_IMUNES_IDS for role in ctx.author.roles) or ctx.author.id == DONO_ID
    if not eh_staff:
        return await ctx.send("❌ Você não tem permissão para usar esse comando! 🦇😤")
    try:
        await membro.timeout(None)
        avisos_usuarios[membro.id] = 0
        total_ciclos_usuario[membro.id] = max(0, total_ciclos_usuario.get(membro.id, 0) - 1)
        await remover_cargos_advertencia(membro)
        embed = discord.Embed(
            title="🔓 CASTIGO REMOVIDO MANUALMENTE",
            description=f"O membro {membro.mention} teve seus avisos resetados e o castigo removido por {ctx.author.mention}. 🦇💚",
            color=0x00FF7F,
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=AVATAR_VAMPY)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Ocorreu um erro ao tentar remover o castigo: {e}")

@bot.command(name="resetticket")
async def reset_ticket(ctx):
    """Reseta o canal de tickets com o menu atualizado."""
    eh_staff = ctx.author.id == DONO_ID or any(role.name in CARGOS_IMUNES_NOMES or role.id in CARGOS_IMUNES_IDS for role in ctx.author.roles)
    if not eh_staff:
        return await ctx.send("❌ Apenas a staff pode usar esse comando!", delete_after=5)
    
    canal_tkt = discord.utils.get(ctx.guild.text_channels, name=CANAL_TICKET)
    if not canal_tkt:
        return await ctx.send("❌ Canal de tickets não encontrado!")
    
    try: await canal_tkt.purge(limit=10)
    except: pass
    
    await canal_tkt.send("🎟️ **CENTRAL DE TICKETS CSI** 🎟️\n\nSelecione abaixo para abrir um ticket 💚🦇", view=TicketView())
    embed_banner = discord.Embed(color=0x2b2d31)
    embed_banner.set_image(url=BANNER_TICKET)
    await canal_tkt.send(embed=embed_banner)
    await ctx.send("✅ Canal de tickets resetado com sucesso! 💚🦇", delete_after=5)

# ══════════════════════════════════════════════════════════════════
# 🌐 AUTO-TRADUÇÃO — Cargo Translate
# Quem tiver o cargo CARGO_TRANSLATE_ID e falar em outro idioma
# recebe uma tradução automática que some após 60 segundos.
# Dependências: pip install deep-translator langdetect
# ══════════════════════════════════════════════════════════════════

async def auto_traduzir_mensagem(message: discord.Message):
    """Detecta idioma da mensagem; se não for PT, traduz e envia embed temporário."""
    if not TRADUCAO_DISPONIVEL:
        print("[TRANSLATE] ❌ Bibliotecas não instaladas (deep-translator / langdetect)")
        return
    if message.author.bot:
        return

    tem_cargo = any(role.id == CARGO_TRANSLATE_ID for role in message.author.roles)
    if not tem_cargo:
        return

    texto = message.content.strip()
    if not texto or len(texto) < 2:
        return

    print(f"[TRANSLATE] 🔍 Verificando mensagem de {message.author}: '{texto[:60]}'")

    try:
        loop = asyncio.get_running_loop()
        idioma = await loop.run_in_executor(None, detectar_idioma, texto)
        print(f"[TRANSLATE] 🌍 Idioma detectado: {idioma}")
    except Exception as e:
        print(f"[TRANSLATE] ❌ Erro ao detectar idioma: {e}")
        return

    if idioma in ("pt",):
        print("[TRANSLATE] ✅ Já é português, sem tradução.")
        return

    try:
        loop = asyncio.get_running_loop()
        traduzido = await loop.run_in_executor(
            None,
            lambda: GoogleTranslator(source="auto", target="pt").translate(texto)
        )
        print(f"[TRANSLATE] ✅ Traduzido: '{traduzido[:60]}'")
    except Exception as e:
        print(f"[TRANSLATE] ❌ Erro ao traduzir: {e}")
        return

    if not traduzido or traduzido.strip().lower() == texto.lower():
        print("[TRANSLATE] ⚠️ Tradução igual ao original, ignorando.")
        return

    embed = discord.Embed(
        description=f"🌐 **Tradução automática** de {message.author.mention}:\n\n{traduzido}",
        color=0x5865F2,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="🦇 Vampy Translate • Esta mensagem some em 1 minuto")
    msg_traduzida = await message.channel.send(embed=embed)
    await asyncio.sleep(60)
    try:
        await msg_traduzida.delete()
    except Exception:
        pass

# ══════════════════════════════════════════════════════════════════
# 🇺🇸 AUTO-TRADUÇÃO PARA INGLÊS — Respostas ao membro específico
# Quando alguém responder ao membro MEMBRO_EN_ID, o bot traduz
# automaticamente a mensagem de PT-BR para inglês.
# A mensagem do bot some após 60 segundos.
# ══════════════════════════════════════════════════════════════════

async def traduzir_resposta_para_ingles(message: discord.Message):
    """Se a mensagem for uma resposta a alguém com o cargo Translate, traduz PT→EN e envia embed temporário."""
    if not TRADUCAO_DISPONIVEL:
        print("[TRANSLATE-EN] ❌ Bibliotecas não instaladas (deep-translator / langdetect)")
        return
    if message.author.bot:
        return

    # Verifica se é uma resposta (reply) a outra mensagem
    ref = message.reference
    if not ref:
        return

    # Obtém o membro autor da mensagem original
    autor_original = None
    if ref.resolved and isinstance(ref.resolved, discord.Message):
        autor_original = ref.resolved.author
    elif ref.message_id:
        try:
            msg_original = await message.channel.fetch_message(ref.message_id)
            autor_original = msg_original.author
        except Exception:
            return

    if not autor_original or autor_original.bot:
        return

    # Verifica se o autor original tem o cargo Translate
    membro_original = message.guild.get_member(autor_original.id)
    if not membro_original:
        return
    tem_cargo_translate = any(role.id == CARGO_TRANSLATE_ID for role in membro_original.roles)
    if not tem_cargo_translate:
        return

    texto = message.content.strip()
    if not texto or len(texto) < 2:
        return

    print(f"[TRANSLATE-EN] 🔍 Traduzindo resposta de {message.author}: '{texto[:60]}'")

    try:
        loop = asyncio.get_running_loop()
        idioma = await loop.run_in_executor(None, detectar_idioma, texto)
        print(f"[TRANSLATE-EN] 🌍 Idioma detectado: {idioma}")
    except Exception as e:
        print(f"[TRANSLATE-EN] ❌ Erro ao detectar idioma: {e}")
        idioma = "pt"  # assume PT e tenta traduzir mesmo assim

    # Se já estiver em inglês, não precisa traduzir
    if idioma in ("en",):
        print("[TRANSLATE-EN] ✅ Já é inglês, sem tradução.")
        return

    try:
        loop = asyncio.get_running_loop()
        traduzido = await loop.run_in_executor(
            None,
            lambda: GoogleTranslator(source="auto", target="en").translate(texto)
        )
        print(f"[TRANSLATE-EN] ✅ Traduzido para EN: '{traduzido[:60]}'")
    except Exception as e:
        print(f"[TRANSLATE-EN] ❌ Erro ao traduzir: {e}")
        return

    if not traduzido or traduzido.strip().lower() == texto.lower():
        print("[TRANSLATE-EN] ⚠️ Tradução igual ao original, ignorando.")
        return

    embed = discord.Embed(
        description=(
            f"🇺🇸 **Auto-translation** of {message.author.mention}'s message:\n\n"
            f"{traduzido}"
        ),
        color=0x57F287,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="🦇 Vampy Translate • This message disappears in 1 minute")
    msg_traduzida = await message.channel.send(embed=embed)
    await asyncio.sleep(60)
    try:
        await msg_traduzida.delete()
    except Exception:
        pass

@bot.event
async def on_message(message):
    if message.author.bot: return

    # --- VERIFICAÇÃO DE PALAVRAS DE ALERTA (TRISTEZA/DEPRESSÃO) ---
    await verificar_palavras_alerta(message)

    # --- AUTO-TRADUÇÃO (cargo Translate) ---
    asyncio.create_task(auto_traduzir_mensagem(message))

    # --- AUTO-TRADUÇÃO PT→EN para respostas ao membro que só fala inglês ---
    asyncio.create_task(traduzir_resposta_para_ingles(message))

    # --- APRESENTAÇÃO DA VAMPY QUANDO MARCADA ---
    if bot.user in message.mentions and len(message.content.strip().split()) <= 3:
        apresentacoes = [
            "oi oi!! me chamou?? 🦇💚",
            "aaaa me marcou!! tô aqui sim!! 🦇✨",
            "oiê!! foi mal tava de cabeça pra baixo 🦇😭",
            "ei ei!! a Vampy apareceu!! 💚🦇",
        ]
        embed = discord.Embed(
            title="🦇 Oi, eu sou a Vampy!!",
            description=(
                f"Oii {message.author.mention}!! 💚✨\n\n"
                f"Sou a **Vampy**, a morcega mascote desse servidor!! 🦇\n\n"
                f"**O que eu faço por aqui?**\n"
                f"🛡️ Cuido da segurança do servidor\n"
                f"🎲 Organizo os joguinhos e eventos\n"
                f"🌐 Traduzo mensagens em outros idiomas\n"
                f"💚 Acolho todo mundo com carinho\n"
                f"🎂 Celebro aniversários\n"
                f"🎙️ Gerencio as calls de voz\n\n"
                f"Qualquer dúvida é só me chamar!! Tô sempre de olho!! 🦇💜"
            ),
            color=0x7c3aed,
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=AVATAR_VAMPY)
        embed.set_footer(text="🦇 Vampy • Morcega do servidor")
        await message.reply(embed=embed, mention_author=False)
        return

    # --- LÓGICA EVENTO SILENCIOSO (agora no canal games) ---
    global contador_mensagens_silencioso, meta_mensagens_silencioso, evento_silencioso_ativo
    if evento_silencioso_ativo and message.channel.name == CANAL_GAMES:
        contador_mensagens_silencioso += 1
        if contador_mensagens_silencioso >= meta_mensagens_silencioso:
            user_id = message.author.id
            pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) + 600
            
            embed_silencioso = discord.Embed(
                title="🦇 SORTE NO SILÊNCIO! 🦇",
                description=f"Surpresa! {message.author.mention}, você enviou a mensagem de número **{meta_mensagens_silencioso}**!\n\nVocê ganhou **600 Vampy-Coins**! 💎✨",
                color=0xFFD700
            )
            embed_silencioso.set_thumbnail(url=AVATAR_VAMPY)
            await message.channel.send(embed=embed_silencioso)
            
            evento_silencioso_ativo = False
            jogo_em_andamento["venceu"] = True
            await atualizar_ranking(message.guild)

    # --- LÓGICA DO JOGUINHO (apenas no canal games) ---
    if jogo_em_andamento["resposta"] and message.channel.name == CANAL_GAMES:
        user_id = message.author.id
        msg_content = message.content.lower().strip()
        tipo = jogo_em_andamento["tipo"]
        ganhou = False
        premio = 0

        if user_id in jogo_em_andamento["participantes_tentaram"]:
            if tipo in ["roleta", "tarot", "sobrevivamonstro", "campominado", "dragao"]:
                return 
            elif tipo == "blackjack":
                pass   # Blackjack: HIT/STAND permitidos após entrar
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
            "bauperdido": lambda m: m == "abrir",
            "sobrevivamonstro": lambda m: m in ["escudo", "espada", "fugir"],
            "tarot": lambda m: m == "tarot",
            "detetive": lambda m: True,
            # Novos jogos v2.0
            "blackjack": lambda m: m in ["blackjack", "hit", "stand"],
            "campominado": lambda m: m.isdigit() and 1 <= int(m) <= 9,
            "dragao": lambda m: m in ["chama", "gelo", "ouro"],
        }

        if filtros.get(tipo, lambda m: False)(msg_content):
            jogo_em_andamento["participantes_tentaram"].append(user_id)

            if tipo == "detetive":
                if msg_content == jogo_em_andamento["resposta"]:
                    jogo_em_andamento["venceu"] = True
                    jogo_em_andamento["resposta"] = None
                    pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) + 300
                    
                    embed_vitoria = discord.Embed(
                        title="🕵️ CASO RESOLVIDO! 🎉",
                        description=f"Parabéns, detetive {message.author.mention}! 🔍✨\n\nVocê descobriu o culpado e ganhou **300 Vampy-Coins**! 🦇💚",
                        color=0x00FF7F
                    )
                    embed_vitoria.set_image(url=GIF_VITORIA)
                    await message.reply(embed=embed_vitoria)
                    await atualizar_ranking(message.guild)
                else:
                    pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) - 100
                    await message.reply("❌ Não foi esse! Você perdeu **100 Coins**! Continue investigando... 🔍💔")
                    await atualizar_ranking(message.guild)
                return

            if tipo == "tarot":
                carta = random.choice(CARTAS_TAROT)
                
                embed_carta = discord.Embed(
                    title="🔮 SUA CARTA FOI REVELADA! 🔮",
                    description=f"**{carta['nome']}**\n\n*{carta['mensagem']}*",
                    color=0x9B59B6
                )
                embed_carta.set_thumbnail(url=AVATAR_VAMPY)
                
                if carta["tipo"] == "escolha_doar":
                    await message.reply(embed=embed_carta)
                    await message.channel.send(f"{message.author.mention}, escolha: **DOAR** ou **PEGAR**?")
                    
                    def check_escolha(m):
                        return m.author == message.author and m.content.lower() in ["doar", "pegar"]
                    
                    try:
                        resposta = await bot.wait_for("message", check=check_escolha, timeout=30)
                        if resposta.content.lower() == "doar":
                            await message.channel.send(f"😇 Que alma generosa! Mencione quem receberá os 100 coins!")
                            
                            def check_mencao(m):
                                return m.author == message.author and len(m.mentions) > 0
                            
                            try:
                                msg_alvo = await bot.wait_for("message", check=check_mencao, timeout=30)
                                alvo = msg_alvo.mentions[0]
                                if pontuacao_vampy.get(user_id, 0) >= 100:
                                    pontuacao_vampy[user_id] -= 100
                                    pontuacao_vampy[alvo.id] = pontuacao_vampy.get(alvo.id, 0) + 100
                                    embed_final = discord.Embed(
                                        title="💖 BONDADE RECOMPENSADA",
                                        description=f"{message.author.mention} doou 100 coins para {alvo.mention}!\n\nAs cartas sorriem para o generoso! 🔮✨",
                                        color=0x00FF7F
                                    )
                                    await message.channel.send(embed=embed_final)
                                else:
                                    await message.channel.send("❌ Você não tem coins suficientes para doar!")
                            except asyncio.TimeoutError:
                                await message.channel.send("⏰ Tempo esgotado!")
                        else:
                            pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) + 200
                            embed_final = discord.Embed(
                                title="💰 GANÂNCIA PREMIADA",
                                description=f"{message.author.mention} escolheu o caminho da ambição e ganhou **200 Coins**! 🔮",
                                color=0xFFD700
                            )
                            embed_final.set_image(url=GIF_VITORIA)
                            await message.channel.send(embed=embed_final)
                        await atualizar_ranking(message.guild)
                    except asyncio.TimeoutError:
                        await message.channel.send("⏰ As cartas se fecharam pelo silêncio...")
                    return
                
                elif carta["tipo"] == "arriscar":
                    await message.reply(embed=embed_carta)
                    await message.channel.send(f"{message.author.mention}, você quer **ARRISCAR** outra carta ou **PARAR** aqui?")
                    
                    def check_risco(m):
                        return m.author == message.author and m.content.lower() in ["arriscar", "parar"]
                    
                    try:
                        resposta = await bot.wait_for("message", check=check_risco, timeout=30)
                        if resposta.content.lower() == "arriscar":
                            if random.random() < 0.7:
                                perda = random.randint(100, 250)
                                pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) - perda
                                embed_risco = discord.Embed(
                                    title="💀 A GANÂNCIA TEM SEU PREÇO!",
                                    description=f"{message.author.mention}, as cartas se voltaram contra você!\n\nVocê perdeu **{perda} Coins**! 🔮💔",
                                    color=0xFF0000
                                )
                                embed_risco.set_image(url=GIF_DERROTA)
                            else:
                                ganho = random.randint(200, 400)
                                pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) + ganho
                                embed_risco = discord.Embed(
                                    title="✨ A CORAGEM FOI RECOMPENSADA!",
                                    description=f"{message.author.mention}, os deuses da sorte te favorecem!\n\nVocê ganhou **{ganho} Coins**! 🔮✨",
                                    color=0x00FF7F
                                )
                                embed_risco.set_image(url=GIF_VITORIA)
                            await message.channel.send(embed=embed_risco)
                        else:
                            await message.channel.send(f"🛡️ {message.author.mention} escolheu a prudência! As cartas respeitam sua decisão.")
                        await atualizar_ranking(message.guild)
                    except asyncio.TimeoutError:
                        await message.channel.send("⏰ As cartas se fecharam...")
                    return
                
                else:
                    pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) + carta["coins"]
                    
                    if carta["coins"] > 0:
                        embed_carta.set_image(url=GIF_VITORIA)
                        embed_carta.add_field(name="💰 Recompensa", value=f"+{carta['coins']} Coins", inline=False)
                    elif carta["coins"] < 0:
                        embed_carta.set_image(url=GIF_DERROTA)
                        embed_carta.add_field(name="💀 Perda", value=f"{carta['coins']} Coins", inline=False)
                    else:
                        embed_carta.add_field(name="⚖️ Neutro", value="Nenhuma mudança nos coins", inline=False)
                    
                    await message.reply(embed=embed_carta)
                    await atualizar_ranking(message.guild)
                    return

            elif tipo == "sobrevivamonstro":
                if msg_content == "escudo":
                    if random.random() < 0.5:
                        pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) + 150
                        embed_resultado = discord.Embed(
                            title="🛡️ DEFESA BEM SUCEDIDA!",
                            description=f"{message.author.mention} conseguiu se proteger do monstro com o escudo! 🦇✨\n\nVocê ganhou **150 Coins**!",
                            color=0x00FF7F
                        )
                        embed_resultado.set_image(url=GIF_VITORIA)
                    else:
                        pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) - 50
                        embed_resultado = discord.Embed(
                            title="💥 O ESCUDO QUEBROU!",
                            description=f"{message.author.mention}, o monstro era muito forte! Seu escudo não resistiu... 🦇💔\n\nVocê perdeu **50 Coins**!",
                            color=0xFF0000
                        )
                        embed_resultado.set_image(url=GIF_DERROTA)
                    await message.reply(embed=embed_resultado)
                    await atualizar_ranking(message.guild)
                    return
                
                elif msg_content == "espada":
                    if random.random() < 0.01:
                        pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) + 700
                        embed_resultado = discord.Embed(
                            title="⚔️ GOLPE CRÍTICO ÉPICO!",
                            description=f"{message.author.mention} DERROTOU O MONSTRO COM UM ÚNICO GOLPE! 🦇⚔️✨\n\nVocê é um VERDADEIRO HERÓI! Ganhou **700 Coins**!",
                            color=0xFFD700
                        )
                        embed_resultado.set_image(url=GIF_VITORIA)
                    else:
                        pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) - 100
                        embed_resultado = discord.Embed(
                            title="💀 VOCÊ FOI DERROTADO!",
                            description=f"{message.author.mention} tentou atacar mas o monstro era muito forte! 🦇💔\n\nVocê perdeu **100 Coins**!",
                            color=0xFF0000
                        )
                        embed_resultado.set_image(url=GIF_DERROTA)
                    await message.reply(embed=embed_resultado)
                    await atualizar_ranking(message.guild)
                    return
                
                elif msg_content == "fugir":
                    pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) - 50
                    embed_resultado = discord.Embed(
                        title="🏃 VOCÊ FUGIU!",
                        description=f"{message.author.mention} preferiu a segurança e fugiu do monstro! 🦇💨\n\nVocê perdeu **50 Coins** mas está a salvo!",
                        color=0xFFA500
                    )
                    await message.reply(embed=embed_resultado)
                    await atualizar_ranking(message.guild)
                    return

            elif tipo == "bauperdido":
                jogo_em_andamento["venceu"] = True
                jogo_em_andamento["resposta"] = None
                sorte = random.random()
                if sorte < 0.5:
                    ganhou, premio = True, 300
                else:
                    pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) - 100
                    embed_mimico = discord.Embed(title="💀 O MÍMICO TE PEGOU!", description=f"{message.author.mention}, o baú era um monstro! Você perdeu **100 Coins**! 🦇💔", color=0xFF0000)
                    embed_mimico.set_image(url=GIF_MIMICO)
                    await message.reply(embed=embed_mimico)
                    await atualizar_ranking(message.guild)
                    return

            elif tipo == "embaralhada":
                if msg_content == jogo_em_andamento["resposta"]:
                    ganhou, premio = True, 150
                else:
                    pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) - 25
                    await message.reply("🥺 Errou a palavra! A Vampy ficou triste e você perdeu **25 coins**! 🦇💔")
                    await atualizar_ranking(message.guild) 
                    return

            elif tipo == "blackjack":
                dados_bj = jogo_em_andamento.setdefault("dados_blackjack", {})

                # ── ENTRADA: jogador ainda não iniciou ──────────────────────
                if msg_content == "blackjack" and user_id not in dados_bj:
                    deck = _bj_new_deck()
                    mao  = [_bj_draw(deck), _bj_draw(deck)]
                    dados_bj[user_id] = {"mao": mao, "deck": deck}
                    val = _bj_hand_value(mao)

                    if val == 21:
                        # Blackjack de cara!
                        premio_bj = 350
                        pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) + premio_bj
                        embed_bj = discord.Embed(
                            title="🌟 BLACKJACK! 21 DE CARA!",
                            description=(
                                f"{message.author.mention} tirou **Blackjack** imediato!\n\n"
                                f"Mão: {_bj_hand_str(mao)} — Total: **{val}**\n\n"
                                f"Você ganhou **{premio_bj} Coins**! 🃏✨"
                            ),
                            color=0xFFD700
                        )
                        embed_bj.set_image(url=GIF_VITORIA)
                        await message.reply(embed=embed_bj)
                        await atualizar_ranking(message.guild)
                        return
                    else:
                        embed_bj = discord.Embed(
                            title="🃏 SUAS CARTAS FORAM DISTRIBUÍDAS!",
                            description=(
                                f"{message.author.mention}, suas cartas:\n\n"
                                f"Mão: {_bj_hand_str(mao)} — Total: **{val}**\n\n"
                                f"Digite **HIT** para pedir mais uma carta ou **STAND** para parar!"
                            ),
                            color=0xC0392B
                        )
                        await message.reply(embed=embed_bj)
                        return

                # ── HIT: pede mais uma carta ─────────────────────────────────
                elif msg_content == "hit" and user_id in dados_bj:
                    estado = dados_bj[user_id]
                    nova_carta = _bj_draw(estado["deck"])
                    estado["mao"].append(nova_carta)
                    val = _bj_hand_value(estado["mao"])

                    if val > 21:
                        # Estourou
                        pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) - 100
                        embed_bj = discord.Embed(
                            title="💥 ESTOUROU! PASSOU DE 21!",
                            description=(
                                f"{message.author.mention}, você pediu demais!\n\n"
                                f"Mão: {_bj_hand_str(estado['mao'])} — Total: **{val}**\n\n"
                                f"Você perdeu **100 Coins**! 🃏💔"
                            ),
                            color=0xFF0000
                        )
                        embed_bj.set_image(url=GIF_DERROTA)
                        await message.reply(embed=embed_bj)
                        del dados_bj[user_id]
                        await atualizar_ranking(message.guild)
                        return
                    elif val == 21:
                        # Acertou 21 com HIT
                        ganhou_bj = True
                        premio_bj = 200
                        pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) + premio_bj
                        embed_bj = discord.Embed(
                            title="🎯 21! PERFEITO!",
                            description=(
                                f"{message.author.mention} acertou 21!\n\n"
                                f"Mão: {_bj_hand_str(estado['mao'])} — Total: **{val}**\n\n"
                                f"Você ganhou **{premio_bj} Coins**! 🃏✨"
                            ),
                            color=0x00FF7F
                        )
                        embed_bj.set_image(url=GIF_VITORIA)
                        await message.reply(embed=embed_bj)
                        del dados_bj[user_id]
                        await atualizar_ranking(message.guild)
                        return
                    else:
                        embed_bj = discord.Embed(
                            title="🃏 CARTA COMPRADA!",
                            description=(
                                f"{message.author.mention}\n\n"
                                f"Mão: {_bj_hand_str(estado['mao'])} — Total: **{val}**\n\n"
                                f"Digite **HIT** para mais uma ou **STAND** para parar!"
                            ),
                            color=0xC0392B
                        )
                        await message.reply(embed=embed_bj)
                        return

                # ── STAND: para e compara com o dealer ──────────────────────
                elif msg_content == "stand" and user_id in dados_bj:
                    estado = dados_bj[user_id]
                    val_jogador = _bj_hand_value(estado["mao"])
                    # Dealer compra até 17+
                    deck_dealer = _bj_new_deck()
                    mao_dealer  = [_bj_draw(deck_dealer), _bj_draw(deck_dealer)]
                    while _bj_hand_value(mao_dealer) < 17:
                        mao_dealer.append(_bj_draw(deck_dealer))
                    val_dealer = _bj_hand_value(mao_dealer)

                    dealer_str = _bj_hand_str(mao_dealer)
                    jogador_str = _bj_hand_str(estado["mao"])

                    if val_dealer > 21 or val_jogador > val_dealer:
                        # Jogador venceu
                        premio_bj = 200
                        pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) + premio_bj
                        embed_bj = discord.Embed(
                            title="✅ VOCÊ VENCEU O DEALER!",
                            description=(
                                f"{message.author.mention}\n\n"
                                f"Sua mão: {jogador_str} — **{val_jogador}**\n"
                                f"Dealer: {dealer_str} — **{val_dealer}** {'(estourou!)' if val_dealer > 21 else ''}\n\n"
                                f"Você ganhou **{premio_bj} Coins**! 🃏✨"
                            ),
                            color=0x00FF7F
                        )
                        embed_bj.set_image(url=GIF_VITORIA)
                    elif val_jogador == val_dealer:
                        embed_bj = discord.Embed(
                            title="🤝 EMPATE!",
                            description=(
                                f"{message.author.mention}\n\n"
                                f"Sua mão: {jogador_str} — **{val_jogador}**\n"
                                f"Dealer: {dealer_str} — **{val_dealer}**\n\n"
                                f"Empate! Nenhum coin foi perdido ou ganho. 🃏"
                            ),
                            color=0xFFA500
                        )
                    else:
                        pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) - 100
                        embed_bj = discord.Embed(
                            title="❌ O DEALER VENCEU!",
                            description=(
                                f"{message.author.mention}\n\n"
                                f"Sua mão: {jogador_str} — **{val_jogador}**\n"
                                f"Dealer: {dealer_str} — **{val_dealer}**\n\n"
                                f"Você perdeu **100 Coins**! 🃏💔"
                            ),
                            color=0xFF0000
                        )
                        embed_bj.set_image(url=GIF_DERROTA)

                    await message.reply(embed=embed_bj)
                    del dados_bj[user_id]
                    await atualizar_ranking(message.guild)
                    return
                else:
                    return  # Ignorar mensagem inválida no blackjack

            elif tipo == "campominado":
                mapa_campo = jogo_em_andamento.get("dados_campo", {})
                if not mapa_campo:
                    return
                resultado_campo = mapa_campo.get(msg_content)
                if not resultado_campo:
                    return
                tipo_campo, valor_campo = resultado_campo
                if tipo_campo == "cofre":
                    pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) + valor_campo
                    embed_campo = discord.Embed(
                        title="🟩 COFRE ENCONTRADO!",
                        description=(
                            f"🎉 {message.author.mention} escolheu a casa **{msg_content}**!\n\n"
                            f"Era um **COFRE** cheio de tesouros! 💰\n\n"
                            f"Você ganhou **{valor_campo} Coins**! 💚✨"
                        ),
                        color=0x00FF7F
                    )
                    embed_campo.set_image(url=GIF_VITORIA)
                else:
                    pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) + valor_campo  # valor negativo
                    embed_campo = discord.Embed(
                        title="💣 BOOM! VOCÊ PISOU NUMA MINA!",
                        description=(
                            f"💥 {message.author.mention} escolheu a casa **{msg_content}**!\n\n"
                            f"Era uma **MINA**! Que azar!\n\n"
                            f"Você perdeu **{abs(valor_campo)} Coins**! 💔"
                        ),
                        color=0xFF0000
                    )
                    embed_campo.set_image(url=GIF_DERROTA)
                await message.reply(embed=embed_campo)
                await atualizar_ranking(message.guild)
                return

            elif tipo == "dragao":
                resultados_dragao = {
                    "chama": {"chance": 0.35, "ganho": 350, "perda": 120,
                              "win_title": "🔥 CHAMA DEVASTADORA!", "win_desc": "Sua magia de fogo queimou o dragão!",
                              "lose_title": "🐉 O DRAGÃO CONTRA-ATACOU!", "lose_desc": "O dragão absorveu suas chamas e soltou fogo de volta!"},
                    "gelo":  {"chance": 0.50, "ganho": 200, "perda": 100,
                              "win_title": "❄️ DRAGÃO CONGELADO!", "win_desc": "Sua magia de gelo paralisou a besta!",
                              "lose_title": "💧 O FEITIÇO FALHOU!", "lose_desc": "O calor do dragão derreteu seu gelo!"},
                    "ouro":  {"chance": 0.75, "ganho": 80, "perda": 180,
                              "win_title": "✨ O DRAGÃO ACEITOU O OURO!", "win_desc": "Ele ficou satisfeito e foi embora.",
                              "lose_title": "😡 ELE FICOU COM RAIVA!", "lose_desc": "O dragão achou seu ouro uma ofensa!"},
                }
                config_d = resultados_dragao.get(msg_content)
                if not config_d:
                    return
                if random.random() < config_d["chance"]:
                    pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) + config_d["ganho"]
                    embed_dragao = discord.Embed(
                        title=config_d["win_title"],
                        description=(
                            f"{message.author.mention} usou **{msg_content.upper()}**!\n\n"
                            f"*{config_d['win_desc']}*\n\n"
                            f"Você ganhou **{config_d['ganho']} Coins**! 🦇✨"
                        ),
                        color=0x00FF7F
                    )
                    embed_dragao.set_image(url=GIF_VITORIA)
                else:
                    pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) - config_d["perda"]
                    embed_dragao = discord.Embed(
                        title=config_d["lose_title"],
                        description=(
                            f"{message.author.mention} usou **{msg_content.upper()}**!\n\n"
                            f"*{config_d['lose_desc']}*\n\n"
                            f"Você perdeu **{config_d['perda']} Coins**! 🦇💔"
                        ),
                        color=0xFF0000
                    )
                    embed_dragao.set_image(url=GIF_DERROTA)
                await message.reply(embed=embed_dragao)
                await atualizar_ranking(message.guild)
                return

            elif tipo == "caixa":
                jogo_em_andamento["venceu"] = True
                jogo_em_andamento["resposta"] = None
                resultado_caixa = random.choice(["coins", "raro", "perder"])
                
                if resultado_caixa == "coins":
                    await message.reply(f"🎁 {message.author.mention}, a caixa tem **moedas**!\nVocê quer ganhar **80 coins** ou prefere **doar 100 coins** de si mesmo para alguém? (Responda **GANHAR** ou **DOAR**)")
                    def check_caixa(m):
                        return m.author == message.author and m.content.lower() in ["ganhar", "doar"]
                    try:
                        resp = await bot.wait_for("message", check=check_caixa, timeout=30)
                        if resp.content.lower() == "ganhar":
                            pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) + 80
                            await message.reply("🦇 Você escolheu ganhar! +80 Coins na conta! 💚")
                        else:
                            await message.reply("😇 Que generoso! Mencione para quem você quer doar 100 coins agora!")
                            def check_doacao(m):
                                return m.author == message.author and len(m.mentions) > 0
                            try:
                                msg_alvo = await bot.wait_for("message", check=check_doacao, timeout=30)
                                alvo = msg_alvo.mentions[0]
                                if pontuacao_vampy.get(user_id, 0) >= 100:
                                    pontuacao_vampy[user_id] -= 100
                                    pontuacao_vampy[alvo.id] = pontuacao_vampy.get(alvo.id, 0) + 100
                                    await message.reply(f"💖 Você doou 100 coins para {alvo.mention}! A Vampy amou sua bondade! 🦇✨")
                                else:
                                    await message.reply("❌ Você não tem coins suficientes para doar! A Vampy ficou confuso. 🦇")
                            except asyncio.TimeoutError:
                                await message.reply("⏰ Tempo de doação acabou!")
                        await atualizar_ranking(message.guild)
                    except asyncio.TimeoutError:
                        await message.reply("⏰ Você demorou demais e a caixa se fechou! 🦇")

                elif resultado_caixa == "raro":
                    ganhou, premio = True, 450
                    
                elif resultado_caixa == "perder":
                    pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) - 50
                    await message.reply("💀 Que azar! A caixa estava amaldiçoada e você perdeu **50 coins**! 🦇💔")
                    await atualizar_ranking(message.guild) 
                
                if not ganhou: return

            elif tipo == "numero":
                if msg_content == jogo_em_andamento["resposta"]: ganhou, premio = True, 700
                else:
                    pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) - 25
                    if msg_content.isdigit():
                        tentado = int(msg_content)
                        correto  = int(jogo_em_andamento["resposta"])
                        dica = "🔺 **Muito alto!** Tente menor." if tentado > correto else "🔻 **Muito baixo!** Tente maior."
                        await message.reply(f"❌ {dica} (-25 coins) 🦇")
                    else:
                        await message.reply("🥺 Oh amiguinho, você não conseguiu dessa vez... -25 coins! 💚")
                    await atualizar_ranking(message.guild)

            elif tipo == "ppt":
                bot_choice = random.choice(["pedra", "papel", "tesoura"])
                if msg_content == bot_choice:
                    pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) - 25
                    await message.reply(f"🤝 Empate! Eu escolhi **{bot_choice}**. -25 coins... 🥺")
                    await atualizar_ranking(message.guild)
                elif (msg_content == "pedra" and bot_choice == "tesoura") or (msg_content == "papel" and bot_choice == "pedra") or (msg_content == "tesoura" and bot_choice == "papel"):
                    ganhou, premio = True, 200
                else:
                    pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) - 50
                    await message.reply(f"😜 Eu venci com **{bot_choice}**! -50 coins... 🦇💔")
                    await atualizar_ranking(message.guild)

            elif tipo == "cara_coroa":
                if msg_content == jogo_em_andamento["resposta"]: ganhou, premio = True, 200
                else:
                    pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) - 75
                    await message.reply(f"❌ Errou! Era **{jogo_em_andamento['resposta']}**. -75 coins! 🥺💔")
                    await atualizar_ranking(message.guild)

            elif tipo == "dado":
                if msg_content == jogo_em_andamento["resposta"]: ganhou, premio = True, 60
                else:
                    pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) - 10
                    await message.reply(f"🎲 Caiu **{jogo_em_andamento['resposta']}**! Errou... -10 coins! 🥺")
                    await atualizar_ranking(message.guild)

            elif tipo == "roleta":
                opcoes_roleta = ["700", "80", "150", "perder", "jogo", "dobrar"]
                pesos = [0.01, 0.25, 0.25, 0.15, 0.14, 0.20] 
                resultado = random.choices(opcoes_roleta, weights=pesos)[0]
                
                if resultado == "700":
                    pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) + 700
                    await message.reply(embed=discord.Embed(title="💎 MÁXIMO!", description=f"{message.author.mention} ganhou **700 Coins**! 🦇✨", color=0x00FFFF))
                elif resultado in ["80", "150"]:
                    pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) + int(resultado)
                    await message.reply(f"🎉 {message.author.mention} ganhou **{resultado} Coins**! 🦇💚")
                elif resultado == "perder":
                    pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) - 100
                    await message.reply(embed=discord.Embed(title="💀 AZAR", description=f"{message.author.mention} perdeu **100 Coins**! 🦇💔", color=0xFF0000).set_image(url=GIF_DERROTA))
                elif resultado == "jogo":
                    await message.reply(f"🎡 {message.author.mention}, você ativou um bônus! Outro jogo vindo aí! 🦇🔥")
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
                                    await message.reply(f"💥 **PERDEU TUDO!** A Vampy engoliu suas moedas! 🦇💔")
                                    premio_atual = 0
                                    continuar = False
                            else:
                                await message.reply(f"💰 Sábia escolha! Você garantiu **{premio_atual}** coins! 🦇💚")
                                continuar = False
                        except asyncio.TimeoutError:
                            await message.reply(f"⏰ Tempo acabou! Você parou com **{premio_atual}** coins.")
                            continuar = False
                    pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) + premio_atual
                
                await atualizar_ranking(message.guild); return

            elif msg_content == jogo_em_andamento["resposta"]:
                ganhou, premio = True, 80

            if ganhou:
                jogo_em_andamento["venceu"] = True
                jogo_em_andamento["resposta"] = None
                pontuacao_vampy[user_id] = pontuacao_vampy.get(user_id, 0) + premio
                embed_acerto = discord.Embed(title="🎉 PARABÉNS NENÉM! 🎉", description=f"{message.author.mention}, você acertou!\nVocê ganhou **{premio} Vampy-Coins**! 🦇💚", color=0x00FF7F)
                embed_acerto.set_image(url=GIF_ACERTO_VAMPY)
                await message.reply(embed=embed_acerto)
                await atualizar_ranking(message.guild) 
            return

    # --- PALAVRAS PROIBIDAS ---
    texto = message.content.lower()
    eh_imune = message.author.id == DONO_ID or any(role.name in CARGOS_IMUNES_NOMES or role.id in CARGOS_IMUNES_IDS for role in message.author.roles)
    if not eh_imune and message.channel.name != CANAL_DESABAFOS:
        palavra_encontrada = contem_palavra_proibida(texto)
        if palavra_encontrada:
            try:
                await message.delete()
            except Exception:
                pass

            user_id = message.author.id
            membro = message.author
            guild = message.guild

            avisos_usuarios[user_id] = avisos_usuarios.get(user_id, 0) + 1
            qtd = avisos_usuarios[user_id]
            total_adv = total_ciclos_usuario.get(user_id, 0)

            canal_adv = discord.utils.get(guild.text_channels, name=CANAL_ADVERTENCIAS)
            cargo_staff = discord.utils.get(guild.roles, name=CARGO_STAFF_EQUIPE)

            # ── Ficha no canal de log (sempre) ──────────────────────────────
            await enviar_log_palavras_apagadas(message, palavra_encontrada, qtd, user_id)

            # ── CICLO COMPLETO → CASTIGO ─────────────────────────────────────
            if qtd >= 4:
                duracao_ban = obter_duracao_banimento(user_id)
                duracao_str = formatar_duracao(duracao_ban)
                total_ciclos_usuario[user_id] = total_adv + 1
                avisos_usuarios[user_id] = 0
                novo_total_adv = total_ciclos_usuario[user_id]

                try:
                    await membro.timeout(duracao_ban)
                except Exception:
                    pass

                # Aplica o cargo de advertência correto baseado no total de castigos
                mapa_cargos_adv = {1: CARGO_ADV_1, 2: CARGO_ADV_2, 3: CARGO_ADV_3}
                nome_cargo_adv = mapa_cargos_adv.get(min(novo_total_adv, 3))
                await remover_cargos_advertencia(membro)
                if nome_cargo_adv:
                    cargo_adv = discord.utils.get(guild.roles, name=nome_cargo_adv)
                    if cargo_adv:
                        try:
                            await membro.add_roles(cargo_adv, reason=f"Castigo nº {novo_total_adv} aplicado pelo bot")
                        except Exception:
                            pass

                # Embed da ficha de castigo no canal advertências — apenas a partir do 2º castigo
                if canal_adv and novo_total_adv >= 2:
                    embed_castigo = discord.Embed(
                        title="🚨 CASTIGO APLICADO — CICLO COMPLETO",
                        color=0xCC0000,
                        timestamp=datetime.now()
                    )
                    embed_castigo.set_author(
                        name=f"{membro.display_name}  •  @{membro.name}",
                        icon_url=membro.display_avatar.url
                    )
                    embed_castigo.set_thumbnail(url=membro.display_avatar.url)

                    embed_castigo.add_field(name="👤 Membro",              value=membro.mention,            inline=True)
                    embed_castigo.add_field(name="🆔 ID",                  value=f"`{membro.id}`",          inline=True)
                    embed_castigo.add_field(name="📍 Canal da infração",   value=message.channel.mention,   inline=True)
                    embed_castigo.add_field(name="⏱️ Duração do castigo",  value=f"**{duracao_str}**",      inline=True)
                    embed_castigo.add_field(name="📋 Advertências totais", value=f"**{novo_total_adv}x**",  inline=True)
                    embed_castigo.add_field(name="🔑 Gatilho",             value=f"```{palavra_encontrada}```", inline=False)
                    embed_castigo.add_field(
                        name="ℹ️ Informação",
                        value=(
                            f"Este membro ignorou **3 avisos** e acumulou seu **{novo_total_adv}º** ciclo de punição.\n"
                            f"O próximo ciclo terá castigos ainda mais severos."
                        ),
                        inline=False
                    )
                    embed_castigo.set_footer(
                        text="🦇 Vampy Moderação  •  Use os botões para gerenciar",
                        icon_url=AVATAR_VAMPY
                    )

                    mencao_staff = cargo_staff.mention if cargo_staff else ""
                    await canal_adv.send(
                        content=mencao_staff if mencao_staff else None,
                        embed=embed_castigo,
                        view=DesfazerAvisoView(user_id)
                    )

                # Mensagem simples no canal da infração
                await message.channel.send(
                    f"😢 {membro.mention} você ignorou todos os meus avisos... terei que te castigar por **{duracao_str}**. "
                    f"Espero que você reflita e volte com mais calma! 🦇💔\n*Se foi um engano, chame a staff!*"
                )

            # ── AVISOS 1 / 2 / 3 ─────────────────────────────────────────────
            else:
                duracao_aviso = obter_duracao_aviso(user_id, qtd)
                duracao_str = formatar_duracao(duracao_aviso)

                try:
                    await membro.timeout(duracao_aviso)
                except Exception:
                    pass

                msg_aviso = MSGS_AVISOS[qtd]

                # ── Mensagem fofa no canal da infração (fica permanente) ──────
                await message.channel.send(f"{membro.mention} {msg_aviso}")

            return

    await bot.process_commands(message)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🚀  INICIALIZAÇÃO — Carrega o Security COG e sobe o bot
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ╔══════════════════════════════════════════════════════════════════╗
# ║              📩  LINHA INDIRETA — CSI  (Anônimo)                ║
# ║   Sugestões/Reclamações enviadas anonimamente ao Líder (Akeido) ║
# ╚══════════════════════════════════════════════════════════════════╝

LINHA_INDIRETA_CANAL_ID = 1482855537086304446   # 📩・linha-indireta
AKEIDO_ID               = 445937581566197761    # Líder CSI — recebe a msg anônima
WLU_ID                  = 940036086074343505    # Vice-líder wlu — recebe a msg anônima
AMBER_ID                = 918222382840291369    # Vice-líder Amber — recebe a msg anônima
REALITY_ID              = 769951556388257812    # Dono — recebe quem enviou (secreto)

TIPOS_MENSAGEM = [
    discord.SelectOption(label="💡 Sugestão",       value="Sugestão",       description="Tem uma ideia pra melhorar a CSI?"),
    discord.SelectOption(label="😤 Reclamação",      value="Reclamação",     description="Algo te incomodou? Fala com a gente."),
    discord.SelectOption(label="💬 Feedback Geral",  value="Feedback Geral", description="Opinião geral sobre o servidor/CSI."),
    discord.SelectOption(label="🚨 Denúncia",        value="Denúncia",       description="Algo errado acontecendo? Avise anonimamente."),
    discord.SelectOption(label="❓ Dúvida",          value="Dúvida",         description="Alguma dúvida sobre a CSI?"),
    discord.SelectOption(label="🙏 Elogio",          value="Elogio",         description="Quer elogiar alguém ou algo?"),
    discord.SelectOption(label="📋 Outro",           value="Outro",          description="Qualquer outra coisa que queira dizer."),
]

DESTINATARIOS = [
    discord.SelectOption(label="👑 Akeido (Líder)",       value="akeido", description="Enviar para o Líder da CSI."),
    discord.SelectOption(label="🥈 wlu (Vice-líder)",     value="wlu",    description="Enviar para o Vice-líder wlu."),
    discord.SelectOption(label="🥈 Amber (Vice-líder)",   value="amber",  description="Enviar para a Vice-líder Amber."),
]

# Mapeamento: valor do select → (ID do usuário, nome de exibição)
DESTINATARIO_MAP = {
    "akeido": (AKEIDO_ID, "Akeido (Líder)"),
    "wlu":    (WLU_ID,    "wlu (Vice-líder)"),
    "amber":  (AMBER_ID,  "Amber (Vice-líder)"),
}


class LinhaIndiretaModal(discord.ui.Modal, title="📩 Linha Indireta — CSI"):
    """Modal que coleta o tipo e a mensagem do usuário."""

    tipo_selecionado: str  = "Outro"   # preenchido pela View antes de enviar o modal
    destinatario_key: str  = "akeido"  # preenchido pela View antes de enviar o modal

    mensagem = discord.ui.TextInput(
        label="✍️ Sua mensagem",
        style=discord.TextStyle.paragraph,
        placeholder="Escreva aqui sua sugestão, reclamação, elogio... Seja claro e respeitoso.",
        min_length=10,
        max_length=1500,
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        tipo   = self.tipo_selecionado
        texto  = self.mensagem.value
        autor  = interaction.user

        # ── Resolve destinatário ──────────────────────────────────────────
        dest_id, dest_nome = DESTINATARIO_MAP.get(self.destinatario_key, (AKEIDO_ID, "Akeido (Líder)"))

        # ── Embed que vai ao destinatário (sem revelar o autor) ───────────
        embed_dest = discord.Embed(
            title="📩 Nova mensagem na Linha Indireta — CSI",
            description=texto,
            color=0x5865F2,
            timestamp=datetime.utcnow(),
        )
        embed_dest.add_field(name="📌 Tipo",          value=f"`{tipo}`",      inline=True)
        embed_dest.add_field(name="🔒 Autor",         value="`Anônimo`",      inline=True)
        embed_dest.add_field(name="📬 Destinatário",  value=f"`{dest_nome}`", inline=True)
        embed_dest.set_footer(text="📩 Linha Indireta CSI • Mensagem anônima")

        # ── Embed secreto que vai pro Reality (revela o autor) ────────────
        embed_reality = discord.Embed(
            title="🔍 [SECRETO] Linha Indireta — Identificação",
            description=f"Uma mensagem do tipo **{tipo}** foi enviada anonimamente para **{dest_nome}**.",
            color=0xff6600,
            timestamp=datetime.utcnow(),
        )
        embed_reality.add_field(name="👤 Enviado por",    value=f"{autor.mention} (`{autor}` | ID: `{autor.id}`)", inline=False)
        embed_reality.add_field(name="📬 Destinatário",   value=dest_nome,                                         inline=False)
        embed_reality.set_thumbnail(url=autor.display_avatar.url)
        embed_reality.set_footer(text="🦇 Vampy — Linha Indireta • Apenas você vê isso, Reality.")

        # ── Envia ao destinatário escolhido ───────────────────────────────
        enviado = False
        try:
            dest_user = await interaction.client.fetch_user(dest_id)
            await dest_user.send(embed=embed_dest)
            enviado = True
        except Exception:
            enviado = False

        # ── Envia pro Reality (secreto) ───────────────────────────────────
        try:
            reality = await interaction.client.fetch_user(REALITY_ID)
            await reality.send(embed=embed_reality)
        except Exception:
            pass  # silencia qualquer erro no aviso secreto

        # ── Confirmação pro usuário (efêmera) ─────────────────────────────
        if enviado:
            await interaction.followup.send(
                f"✅ **Mensagem enviada com sucesso!**\n"
                f"Sua identidade foi mantida em **sigilo total**. "
                f"**{dest_nome}** recebeu sua mensagem anonimamente. 🦇🔒",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                f"⚠️ Houve um problema ao entregar sua mensagem para **{dest_nome}**. "
                "Essa pessoa pode estar com o PV fechado. Tente novamente mais tarde.",
                ephemeral=True,
            )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message(
            "❌ Ocorreu um erro ao enviar sua mensagem. Tente novamente.", ephemeral=True
        )


class LinhaIndiretaSelectView(discord.ui.View):
    """View com o Select de tipo + Select de destinatário + botão Continuar."""

    def __init__(self):
        super().__init__(timeout=120)
        self.tipo_escolhido:        str | None = None
        self.destinatario_escolhido: str | None = None

    def _atualizar_botao(self):
        """Habilita o botão apenas quando tipo E destinatário estiverem escolhidos."""
        pronto = self.tipo_escolhido is not None and self.destinatario_escolhido is not None
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = not pronto

    def _status_text(self) -> str:
        tipo  = f"`{self.tipo_escolhido}`" if self.tipo_escolhido else "*(aguardando...)*"
        dest  = f"`{DESTINATARIO_MAP[self.destinatario_escolhido][1]}`" if self.destinatario_escolhido else "*(aguardando...)*"
        return (
            f"**Tipo:** {tipo}\n"
            f"**Destinatário:** {dest}\n\n"
            "Clique em **✍️ Escrever mensagem** para continuar."
            if (self.tipo_escolhido and self.destinatario_escolhido)
            else f"**Tipo:** {tipo}\n**Destinatário:** {dest}"
        )

    @discord.ui.select(
        placeholder="📌 Selecione o tipo da sua mensagem...",
        options=TIPOS_MENSAGEM,
        min_values=1,
        max_values=1,
    )
    async def select_tipo(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.tipo_escolhido = select.values[0]
        self._atualizar_botao()
        await interaction.response.edit_message(content=self._status_text(), view=self)

    @discord.ui.select(
        placeholder="📬 Para quem deseja enviar?",
        options=DESTINATARIOS,
        min_values=1,
        max_values=1,
    )
    async def select_destinatario(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.destinatario_escolhido = select.values[0]
        self._atualizar_botao()
        await interaction.response.edit_message(content=self._status_text(), view=self)

    @discord.ui.button(label="✍️ Escrever mensagem", style=discord.ButtonStyle.primary, disabled=True, emoji="📝")
    async def abrir_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = LinhaIndiretaModal()
        modal.tipo_selecionado  = self.tipo_escolhido or "Outro"
        modal.destinatario_key  = self.destinatario_escolhido or "akeido"
        await interaction.response.send_modal(modal)


class LinhaIndiretaInicioView(discord.ui.View):
    """View permanente no canal com o botão de abertura."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Enviar mensagem anônima",
        style=discord.ButtonStyle.danger,
        emoji="📩",
        custom_id="linha_indireta_abrir",
    )
    async def abrir(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = LinhaIndiretaSelectView()
        await interaction.response.send_message(
            "## 📩 Linha Indireta — CSI\n"
            "Sua mensagem será entregue **anonimamente** ao destinatário escolhido.\n"
            "**Ninguém saberá que foi você.** 🔒\n\n"
            "**1️⃣** Selecione o **tipo** da sua mensagem.\n"
            "**2️⃣** Selecione o **destinatário** (Líder ou Vice-líder).\n"
            "**3️⃣** Clique em **Escrever mensagem**, escreva e confirme. ✅",
            view=view,
            ephemeral=True,
        )


@bot.command(name="linha_indireta")
async def setup_linha_indireta(ctx: commands.Context):
    """Posta o embed da Linha Indireta no canal correto. Apenas o dono pode usar."""
    if ctx.author.id != REALITY_ID:
        return await ctx.send("❌ Apenas o Reality pode configurar a Linha Indireta.", delete_after=5)

    canal = bot.get_channel(LINHA_INDIRETA_CANAL_ID)
    if canal is None:
        return await ctx.send("❌ Canal da Linha Indireta não encontrado.", delete_after=5)

    embed = discord.Embed(
        title="📩 Linha Indireta — CSI",
        description=(
            "Aqui você pode enviar **sugestões, reclamações, feedbacks, denúncias ou elogios** "
            "diretamente ao **Líder ou Vice-líder da CSI**, de forma completamente **anônima**.\n\n"
            "🔒 **Sua identidade nunca será revelada.**\n"
            "📌 Escolha o tipo da mensagem, o destinatário, escreva e envie — é simples assim.\n\n"
            "**Tipos disponíveis:**\n"
            "💡 Sugestão • 😤 Reclamação • 💬 Feedback\n"
            "🚨 Denúncia • ❓ Dúvida • 🙏 Elogio • 📋 Outro\n\n"
            "**Quem pode receber:**\n"
            "👑 Akeido (Líder) • 🥈 wlu (Vice-líder) • 🥈 Amber (Vice-líder)\n\n"
            "> *Use com responsabilidade. Mensagens ofensivas ou de má-fé serão ignoradas.*"
        ),
        color=0x5865F2,
    )
    embed.set_footer(text="📩 Linha Indireta CSI • Anônimo & Seguro 🔒")

    await canal.send(embed=embed, view=LinhaIndiretaInicioView())
    await ctx.send("✅ Linha Indireta configurada com sucesso!", delete_after=5)

    # Registra a view persistente para sobreviver a restarts
    bot.add_view(LinhaIndiretaInicioView())


import asyncio as _asyncio

async def _setup_linha_indireta():
    """Aguarda o bot ficar pronto e posta/atualiza o embed da Linha Indireta automaticamente."""
    await bot.wait_until_ready()

    # Registra a view persistente (necessário para os botões funcionarem após restart)
    bot.add_view(LinhaIndiretaInicioView())

    canal = bot.get_channel(LINHA_INDIRETA_CANAL_ID)
    if canal is None:
        return

    embed = discord.Embed(
        title="📩 Linha Indireta — CSI",
        description=(
            "Aqui você pode enviar **sugestões, reclamações, feedbacks, denúncias ou elogios** "
            "diretamente ao **Líder ou Vice-líder da CSI**, de forma completamente **anônima**.\n\n"
            "🔒 **Sua identidade nunca será revelada.**\n"
            "📌 Escolha o tipo da mensagem, o destinatário, escreva e envie — é simples assim.\n\n"
            "**Tipos disponíveis:**\n"
            "💡 Sugestão • 😤 Reclamação • 💬 Feedback\n"
            "🚨 Denúncia • ❓ Dúvida • 🙏 Elogio • 📋 Outro\n\n"
            "**Quem pode receber:**\n"
            "👑 Akeido (Líder) • 🥈 wlu (Vice-líder) • 🥈 Amber (Vice-líder)\n\n"
            "> *Use com responsabilidade. Mensagens ofensivas ou de má-fé serão ignoradas.*"
        ),
        color=0x5865F2,
    )
    embed.set_footer(text="📩 Linha Indireta CSI • Anônimo & Seguro 🔒")

    # Procura se já existe uma mensagem do bot com o embed no canal
    mensagem_existente = None
    async for msg in canal.history(limit=30):
        if msg.author.id == bot.user.id and msg.embeds and msg.embeds[0].title == "📩 Linha Indireta — CSI":
            mensagem_existente = msg
            break

    if mensagem_existente:
        # Atualiza a mensagem existente (garante botão funcionando após restart)
        try:
            await mensagem_existente.edit(embed=embed, view=LinhaIndiretaInicioView())
        except Exception:
            pass
    else:
        # Limpa mensagens antigas do bot no canal e posta novo embed
        try:
            await canal.purge(limit=20, check=lambda m: m.author.id == bot.user.id)
        except Exception:
            pass
        await canal.send(embed=embed, view=LinhaIndiretaInicioView())


# ╔══════════════════════════════════════════════════════════════════╗
# ║         VAMPY BANIR — Painel de Banimento v1.0             ║
# ║   Bane o membro + painel com Revogar → votação da direção       ║
# ╚══════════════════════════════════════════════════════════════════╝

def _extrair_membro_do_embed(message: discord.Message) -> tuple[int | None, str]:
    """Lê o membro_id e membro_nome do embed da mensagem de banimento."""
    if not message or not message.embeds:
        return None, "Desconhecido"
    embed = message.embeds[0]
    for field in embed.fields:
        # Campo "👤 Membro" tem formato "**nome** (`id`)"
        if "Membro" in (field.name or ""):
            import re
            match = re.search(r"`(\d{15,20})`", field.value or "")
            if match:
                uid = int(match.group(1))
                nome_match = re.match(r"\*\*(.+?)\*\*", field.value or "")
                nome = nome_match.group(1) if nome_match else "Desconhecido"
                return uid, nome
    return None, "Desconhecido"


class BanirMembroView(discord.ui.View):
    """Painel pós-banimento — view persistente (stateless).
    Lê membro_id/nome do embed da mensagem ao clicar, sem precisar de estado."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Revogar banimento",
        style=discord.ButtonStyle.danger,
        custom_id="revogar_banimento"
    )
    async def revogar(self, interaction: discord.Interaction, button: discord.ui.Button):
        # ── Responde IMEDIATAMENTE para o Discord não cancelar a interação ──
        await interaction.response.defer(ephemeral=True)

        # Verifica permissão
        eh_votante = any(r.id in CARGOS_VOTANTES_IDS for r in interaction.user.roles)
        if not interaction.user.guild_permissions.ban_members and not eh_votante:
            await interaction.followup.send(
                "❌ Você não tem permissão para solicitar a revogação do banimento!",
                ephemeral=True
            )
            return

        guild    = interaction.guild
        guild_id = guild.id

        # Lê membro_id e nome do embed da própria mensagem
        membro_id, membro_nome = _extrair_membro_do_embed(interaction.message)
        if membro_id is None:
            await interaction.followup.send(
                "❌ Não consegui identificar o membro nessa mensagem. "
                "Use `!votobanner <id>` manualmente.",
                ephemeral=True
            )
            return

        # Verifica se já tem votação ativa
        if guild_id in _active_votes and membro_id in _active_votes[guild_id]:
            await interaction.followup.send(
                "⏳ Já existe uma votação ativa para esse membro!", ephemeral=True
            )
            return

        direcao_ch = guild.get_channel(DIRECAO_CHANNEL_ID)
        if direcao_ch is None:
            await interaction.followup.send(
                "❌ Canal da direção não encontrado!", ephemeral=True
            )
            return

        embed_dir = discord.Embed(
            title="🗳️ Votação — Solicitação de Revogação de Ban",
            description=(
                f"**{interaction.user.mention}** solicitou a revogação do banimento de "
                f"**{membro_nome}** (`{membro_id}`).\n\n"
                f"Os membros da **direção** devem votar abaixo.\n"
                f"⏱️ Duração: **{VOTE_TIMEOUT_HOURS} horas** ou até todos votarem."
            ),
            color=0xffaa00,
            timestamp=datetime.utcnow()
        )
        embed_dir.set_footer(text="🦇 Vampy • Ban Appeal System")

        vote_view = VotacaoBanView(guild, membro_id, membro_nome)
        msg       = await direcao_ch.send(embed=embed_dir, view=vote_view)
        vote_view.message = msg

        if guild_id not in _active_votes:
            _active_votes[guild_id] = {}
        _active_votes[guild_id][membro_id] = vote_view

        # Desabilita o botão Revogar na mensagem original
        button.label    = "⏳ Votação Iniciada"
        button.disabled = True
        try:
            await interaction.message.edit(view=self)
        except Exception:
            pass

        await interaction.followup.send(
            "✅ Votação de revogação iniciada no canal da direção!! 🦇",
            ephemeral=True
        )

    @discord.ui.button(
        label="Pronto",
        style=discord.ButtonStyle.primary,
        custom_id="banir_pronto"
    )
    async def pronto(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.ban_members:
            await interaction.followup.send("❌ Sem permissão!", ephemeral=True)
            return
        for item in self.children:
            item.disabled = True  # type: ignore
        try:
            await interaction.message.edit(view=self)
        except Exception:
            pass
        await interaction.followup.send("✅ Ação concluída! 🦇", ephemeral=True)


@bot.command(name="banir", aliases=["ban"])
@commands.has_permissions(ban_members=True)
async def cmd_banir(ctx: commands.Context, membro: discord.Member, *, motivo: str = "Sem motivo informado."):
    """Bana um membro e posta painel com opção de revogar. Uso: v!banir @membro [motivo]"""
    if membro.id == ctx.author.id:
        await ctx.send("❌ Você não pode banir você mesmo! 🥺🦇", delete_after=8)
        return
    if membro.top_role >= ctx.author.top_role and ctx.author.id != DONO_ID:
        await ctx.send("❌ Você não pode banir alguém com cargo igual ou superior ao seu! 🦇", delete_after=8)
        return

    guild = ctx.guild
    nome  = membro.display_name
    uid   = membro.id

    # Tenta avisar o banido por DM
    try:
        embed_dm = discord.Embed(
            title="🚨 Você foi banido(a)!",
            description=(
                f"Você foi banido(a) do servidor **{guild.name}**.\n\n"
                f"**📋 Motivo:** {motivo}\n\n"
                f"Se quiser apelar, envie uma mensagem diretamente para este bot explicando o motivo."
            ),
            color=0xff4444,
            timestamp=datetime.utcnow()
        )
        embed_dm.set_footer(text="🦇 Vampy • Sistema de Moderação")
        await membro.send(embed=embed_dm)
    except Exception:
        pass

    # Aplica o ban
    try:
        await guild.ban(membro, reason=f"{motivo} — Banido por {ctx.author}", delete_message_days=0)
    except discord.Forbidden:
        await ctx.send("❌ Não tenho permissão para banir esse membro! 😢🦇", delete_after=8)
        return

    # Embed de confirmação no canal atual
    embed_conf = discord.Embed(
        title="🔨 Membro Banido",
        color=0xff4444,
        timestamp=datetime.utcnow()
    )
    embed_conf.add_field(name="👤 Membro",    value=f"**{nome}** (`{uid}`)",  inline=True)
    embed_conf.add_field(name="🛡️ Banido por", value=ctx.author.mention,       inline=True)
    embed_conf.add_field(name="📋 Motivo",     value=motivo,                    inline=False)
    embed_conf.set_footer(
        text="🦇 Vampy Moderação • Use os botões abaixo para gerenciar",
        icon_url=AVATAR_VAMPY
    )

    view = BanirMembroView()
    await ctx.send(embed=embed_conf, view=view)

    # Log no canal de advertências
    canal_adv = discord.utils.get(guild.text_channels, name=CANAL_ADVERTENCIAS)
    if canal_adv:
        embed_log = discord.Embed(
            title="🔨 BAN APLICADO",
            color=0xCC0000,
            timestamp=datetime.utcnow()
        )
        embed_log.set_author(name=f"{nome}  •  ID: {uid}", icon_url=AVATAR_VAMPY)
        embed_log.add_field(name="👤 Membro",     value=f"**{nome}** (`{uid}`)", inline=True)
        embed_log.add_field(name="🛡️ Staff",      value=ctx.author.mention,       inline=True)
        embed_log.add_field(name="📋 Motivo",      value=motivo,                   inline=False)
        embed_log.set_footer(text="🦇 Vampy Moderação")
        await canal_adv.send(embed=embed_log)

    try:
        await ctx.message.delete()
    except Exception:
        pass


@cmd_banir.error
async def cmd_banir_error(ctx: commands.Context, error: Exception):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Apenas staff com permissão de ban pode usar esse comando! 🦇", delete_after=8)
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Membro não encontrado! Menciona ele ou usa o ID. 🦇", delete_after=8)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Uso correto: `!banir @membro [motivo]` 🦇", delete_after=8)


# ╔══════════════════════════════════════════════════════════════════╗
# ║        VAMPY BAN APPEAL — Sistema de Votação v1.0          ║
# ║   Votação da direção pra desbanir membros • Estila Vampy   ║
# ╚══════════════════════════════════════════════════════════════════╝

DIRECAO_CHANNEL_ID  = 1320160118771290133   # Canal da direção onde a votação é postada
BOT_EXCLUIDO_ID     = 1304927837341618338   # ID do bot que NÃO vota
VOTE_TIMEOUT_HOURS  = 48                    # Horas até a votação expirar automaticamente

# Cargos que têm direito de voto no ban appeal
CARGOS_VOTANTES_IDS = {
    1304658653839888438,
    1304658653839888436,
    1304658653839888439,
    1305223009619152957,
    1387928444418916543,
}

# active_votes: {guild_id: {user_id: VotacaoBanView}}
_active_votes: dict[int, dict[int, "VotacaoBanView"]] = {}


def _get_direcao_members(guild: discord.Guild) -> list[discord.Member]:
    """Retorna todos os membros com cargo de votação (sem bots e sem o bot excluído)."""
    result = []
    for member in guild.members:
        if member.bot or member.id == BOT_EXCLUIDO_ID:
            continue
        if any(role.id in CARGOS_VOTANTES_IDS for role in member.roles):
            result.append(member)
    return result


class VotacaoBanView(discord.ui.View):
    """View de votação para desbanir um membro."""

    def __init__(self, guild: discord.Guild, user_id: int, user_name: str):
        super().__init__(timeout=VOTE_TIMEOUT_HOURS * 3600)
        self.guild     = guild
        self.user_id   = user_id
        self.user_name = user_name
        self.votos_sim: set[int] = set()
        self.votos_nao: set[int] = set()
        self.encerrado = False
        self.message: discord.Message | None = None

    def _elegivel(self, member: discord.Member) -> bool:
        if member.bot or member.id == BOT_EXCLUIDO_ID:
            return False
        return any(role.id in CARGOS_VOTANTES_IDS for role in member.roles)

    def _build_embed(self, encerrado: bool = False) -> discord.Embed:
        membros_dir = _get_direcao_members(self.guild)
        total    = len(membros_dir)
        sim      = len(self.votos_sim)
        nao      = len(self.votos_nao)
        pendente = max(0, total - sim - nao)

        if encerrado:
            aprovado = sim > nao
            cor   = 0x00cc66 if aprovado else 0xff4444
            title = "🗳️ Votação Encerrada"
            resultado = (
                "✅ **APROVADO — Usuário será desbanido!**"
                if aprovado else
                "❌ **NEGADO — Ban mantido.**"
            )
        else:
            cor   = 0xffaa00
            title = "🗳️ Votação — Pedido de Retorno"
            resultado = "⏳ Em andamento..."

        embed = discord.Embed(title=title, color=cor, timestamp=datetime.utcnow())
        embed.add_field(
            name="👤 Usuário",
            value=f"**{self.user_name}** (`{self.user_id}`)",
            inline=False
        )
        embed.add_field(name="✅ Aprovar", value=f"`{sim}`",      inline=True)
        embed.add_field(name="❌ Manter",  value=f"`{nao}`",      inline=True)
        embed.add_field(name="⏳ Faltam",  value=f"`{pendente}`", inline=True)
        if encerrado:
            embed.add_field(name="📊 Resultado", value=resultado, inline=False)
        else:
            embed.add_field(
                name="ℹ️ Info",
                value=(
                    f"Todos os membros da direção devem votar.\n"
                    f"A votação encerra em **{VOTE_TIMEOUT_HOURS}h** ou quando a maioria for atingida."
                ),
                inline=False
            )
        embed.set_footer(text="🦇 Vampy • Sistema de Votação de Ban Appeal")
        return embed

    @discord.ui.button(label="✅ Aprovar Retorno", style=discord.ButtonStyle.success, emoji="✅")
    async def vote_sim(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._elegivel(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas membros da direção podem votar!", ephemeral=True
            )
            return
        if self.encerrado:
            await interaction.response.send_message("❌ Essa votação já foi encerrada!", ephemeral=True)
            return
        if interaction.user.id in self.votos_sim:
            await interaction.response.send_message("Você já votou a favor! 😊", ephemeral=True)
            return
        self.votos_nao.discard(interaction.user.id)
        self.votos_sim.add(interaction.user.id)
        await interaction.response.send_message(
            "✅ Voto registrado: **Aprovar Retorno** 🦇", ephemeral=True
        )
        if self.message:
            await self.message.edit(embed=self._build_embed())
        await self._verificar_resultado()

    @discord.ui.button(label="❌ Manter Ban", style=discord.ButtonStyle.danger, emoji="❌")
    async def vote_nao(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._elegivel(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas membros da direção podem votar!", ephemeral=True
            )
            return
        if self.encerrado:
            await interaction.response.send_message("❌ Essa votação já foi encerrada!", ephemeral=True)
            return
        if interaction.user.id in self.votos_nao:
            await interaction.response.send_message("Você já votou contra! 😔", ephemeral=True)
            return
        self.votos_sim.discard(interaction.user.id)
        self.votos_nao.add(interaction.user.id)
        await interaction.response.send_message(
            "❌ Voto registrado: **Manter Ban** 🦇", ephemeral=True
        )
        if self.message:
            await self.message.edit(embed=self._build_embed())
        await self._verificar_resultado()

    async def _verificar_resultado(self):
        membros = _get_direcao_members(self.guild)
        total   = len(membros)
        if total == 0:
            return
        sim = len(self.votos_sim)
        nao = len(self.votos_nao)
        # Encerra se todos votaram OU maioria absoluta atingida
        if sim + nao >= total or sim > total // 2 or nao > total // 2:
            await self._encerrar()

    async def _encerrar(self):
        if self.encerrado:
            return
        self.encerrado = True
        self.stop()

        # Limpa do registro ativo
        guild_votes = _active_votes.get(self.guild.id, {})
        guild_votes.pop(self.user_id, None)

        sim      = len(self.votos_sim)
        nao      = len(self.votos_nao)
        aprovado = sim > nao

        # Desabilita botões
        for item in self.children:
            item.disabled = True  # type: ignore

        if self.message:
            await self.message.edit(embed=self._build_embed(encerrado=True), view=self)

            if aprovado:
                try:
                    await self.guild.unban(
                        discord.Object(id=self.user_id),
                        reason="✅ Votação da direção aprovada — Vampy Ban Appeal"
                    )
                    await self.message.channel.send(
                        f"🎉 **{self.user_name}** (`{self.user_id}`) foi desbanido(a) com sucesso!! "
                        f"Bem-vindo(a) de volta!! 🦇"
                    )
                except discord.Forbidden:
                    await self.message.channel.send(
                        "❌ Votação aprovada, mas não consegui desbanir — sem permissão de banimento!! 😢🦇"
                    )
                except discord.NotFound:
                    await self.message.channel.send(
                        f"⚠️ **{self.user_name}** não estava mais banido(a)."
                    )
            else:
                await self.message.channel.send(
                    f"🔒 Votação encerrada: ban de **{self.user_name}** (`{self.user_id}`) mantido pela direção. 🦇"
                )

    async def on_timeout(self):
        await self._encerrar()


class BanAppealCog(commands.Cog, name="VampyBanAppeal"):
    """Sistema de votação para ban appeal via DM."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Escuta DMs de usuários banidos que querem apelar."""
        # Ignora mensagens em servidores, bots e o próprio bot
        if message.guild or message.author.bot:
            return

        content = message.content.strip()

        # Procura em qual servidor o usuário está banido
        guild_encontrado: discord.Guild | None = None
        for guild in self.bot.guilds:
            try:
                await guild.fetch_ban(message.author)
                guild_encontrado = guild
                break
            except discord.NotFound:
                continue
            except discord.Forbidden:
                continue
            except Exception:
                continue

        if guild_encontrado is None:
            await message.channel.send(
                "❌ Você não está banido de nenhum servidor gerenciado pela Vampy! 🦇\n"
                "Se acha que é um erro, entre em contato com a administração."
            )
            return

        guild_id = guild_encontrado.id
        user_id  = message.author.id

        # Verifica se já tem votação ativa pra esse usuário
        if guild_id in _active_votes and user_id in _active_votes[guild_id]:
            await message.channel.send(
                "⏳ **Já existe uma votação ativa para você!**\n"
                "Aguarde o resultado antes de enviar outro pedido. 🦇"
            )
            return

        direcao_ch = guild_encontrado.get_channel(DIRECAO_CHANNEL_ID)
        if direcao_ch is None:
            await message.channel.send(
                "❌ Não consegui encontrar o canal da direção. Tente mais tarde. 🦇"
            )
            return

        motivo = content if content else "Sem motivo informado."

        embed_direcao = discord.Embed(
            title="🗳️ Novo Pedido de Retorno — Ban Appeal",
            description=(
                f"O usuário **{message.author.name}** (ID: `{user_id}`) está banido e quer voltar!!\n\n"
                f"**📝 Mensagem enviada:**\n> {motivo[:500]}\n\n"
                f"Os membros da **direção** devem votar abaixo.\n"
                f"⏱️ A votação dura **{VOTE_TIMEOUT_HOURS} horas** ou até a maioria votar."
            ),
            color=0xffaa00,
            timestamp=datetime.utcnow()
        )
        embed_direcao.set_footer(text="🦇 Vampy • Ban Appeal System")
        try:
            embed_direcao.set_thumbnail(url=message.author.display_avatar.url)
        except Exception:
            pass

        view = VotacaoBanView(guild_encontrado, user_id, message.author.name)
        msg  = await direcao_ch.send(embed=embed_direcao, view=view)
        view.message = msg

        if guild_id not in _active_votes:
            _active_votes[guild_id] = {}
        _active_votes[guild_id][user_id] = view

        await message.channel.send(
            "✅ **Seu pedido foi enviado para votação da direção!!** 🦇\n"
            f"Aguarde o resultado — a votação dura até **{VOTE_TIMEOUT_HOURS} horas**.\n\n"
            "💡 *Dica: inclua uma mensagem explicando por que quer voltar.*"
        )

    @commands.command(name="votobanner", aliases=["apelar", "votoban"])
    @commands.has_permissions(administrator=True)
    async def votobanner(self, ctx: commands.Context, user_id: int, *, motivo: str = "Pedido de retorno."):
        """Inicia manualmente uma votação de ban appeal. Uso: v!votobanner <user_id> [motivo]"""
        guild    = ctx.guild
        guild_id = guild.id

        if guild_id in _active_votes and user_id in _active_votes[guild_id]:
            await ctx.send("⏳ Já existe uma votação ativa para esse usuário!", delete_after=10)
            return

        direcao_ch = guild.get_channel(DIRECAO_CHANNEL_ID)
        if direcao_ch is None:
            await ctx.send("❌ Canal da direção não encontrado!", delete_after=10)
            return

        # Verifica se o usuário está de fato banido
        user_name = str(user_id)
        try:
            ban_entry = await guild.fetch_ban(discord.Object(id=user_id))
            user_name = ban_entry.user.name
        except discord.NotFound:
            await ctx.send("❌ Esse usuário não está banido no servidor!", delete_after=10)
            return
        except discord.Forbidden:
            await ctx.send("❌ Sem permissão para verificar bans!", delete_after=10)
            return

        embed_dir = discord.Embed(
            title="🗳️ Votação — Ban Appeal (Manual)",
            description=(
                f"Votação iniciada por {ctx.author.mention} para desbanir **{user_name}** (`{user_id}`).\n\n"
                f"**📝 Motivo:**\n> {motivo[:500]}\n\n"
                f"Os membros da **direção** devem votar abaixo.\n"
                f"⏱️ Duração: **{VOTE_TIMEOUT_HOURS} horas** ou até a maioria votar."
            ),
            color=0xffaa00,
            timestamp=datetime.utcnow()
        )
        embed_dir.set_footer(text="🦇 Vampy • Ban Appeal System")

        view = VotacaoBanView(guild, user_id, user_name)
        msg  = await direcao_ch.send(embed=embed_dir, view=view)
        view.message = msg

        if guild_id not in _active_votes:
            _active_votes[guild_id] = {}
        _active_votes[guild_id][user_id] = view

        await ctx.send(
            f"✅ Votação iniciada para **{user_name}** no canal da direção!! 🦇",
            delete_after=10
        )

    @votobanner.error
    async def votobanner_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Apenas admins podem iniciar votações manualmente!", delete_after=8)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❌ Uso: `!votobanner <user_id> [motivo]`", delete_after=8)


# ╔══════════════════════════════════════════════════════════════════╗
# ║         VAMPY VOICEMASTER — Calls Fofas v1.0               ║
# ║   Sistema completo de calls temporárias • Estila Vampy     ║
# ╚══════════════════════════════════════════════════════════════════╝

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ⚙️  CONFIGURAÇÕES DO VOICEMASTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

VM_LOBBY_NAME        = "🎙️ Criar Call"       # Nome do canal lobby
VM_DEFAULT_NAME      = "🦇 Call da {user}"   # Nome padrão da call criada
VM_DEFAULT_LIMIT     = 0                      # 0 = sem limite
VM_EMPTY_DELAY       = 3                      # Segundos antes de deletar call vazia
VM_CATEGORY_ID       = 1304658655026741260    # ID da categoria onde o lobby e as calls serão criados

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💬  MENSAGENS FOFAS DO VOICEMASTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

_VM_MSGS = {
    "sem_call":            "Você não tem uma call ativa ainda, {user}!! Entra no 🎙️ Criar Call pra começar!! 🦇",
    "renomeada":           "Prontinha!! Renomeei sua call pra **{nome}**!! Ficou lindo!! ✨🦇",
    "limite_set":          "Ok!! Agora sua call aceita até **{limite}** pessoas!! 🎯🦇",
    "limite_removido":     "Removido!! Qualquer quantidade de pessoas pode entrar agora!! 🥳🦇",
    "trancada":            "Call trancada!! Só quem você convidar pode entrar agora!! 🔒🦇",
    "destrancada":         "Call aberta!! Qualquer pessoa pode entrar agora!! 🔓🦇",
    "invisivel":           "Agora sua call tá oculta!! Ninguém vai saber que ela existe!! 👻🦇",
    "visivel":             "Sua call voltou a aparecer pra todo mundo!! 👁️🦇",
    "usuario_kickado":     "Tchau tchau, **{user}**!! O dono te pediu pra sair da call!! 👋🦇",
    "usuario_banido":      "**{user}** foi banido(a) da call!! Não pode mais entrar!! 🚫🦇",
    "usuario_permitido":   "**{user}** agora pode entrar na sua call!! Bem-vindo(a)!! 💕🦇",
    "dono_transferido":    "Transferido!! Agora **{user}** é o(a) novo(a) dono(a) da call!! 👑🦇",
    "dono_reivindicado":   "Você assumiu o controle da call!! Agora é sua!! 👑🥳🦇",
    "bitrate_set":         "Qualidade de áudio atualizada pra **{bitrate}kbps**!! Ficou top!! 🎧🦇",
    "permanente":          "Sua call agora é **permanente**!! Não vai sumir mesmo vazia!! 💎🦇",
    "temporaria":          "Sua call voltou a ser **temporária**!! Vai sumir quando ficar vazia!! 🕐🦇",
    "nao_na_call":         "Você precisa tá dentro da call pra usar isso, {user}!! 🥺🦇",
    "user_nao_na_call":    "Esse(a) usuário(a) não tá na sua call!! 🤔🦇",
    "ja_dono":             "Você já é o(a) dono(a) dessa call!! 😄🦇",
    "dono_ainda_na_call":  "O dono ainda tá na call!! Só dá pra reivindicar quando ele sair!! 🥺🦇",
    "setup_existe":        "Já existe um canal lobby VoiceMaster aqui!! Use v!vm reset pra recriar!! 🤔🦇",
}

def _vm_msg(key: str, **kwargs) -> str:
    m = _VM_MSGS.get(key, "Algo deu errado... 🥺")
    return m.format(**kwargs)

# Cores do VoiceMaster
_VM_COR_FOFA  = 0xFF69B4
_VM_COR_OK    = 0x00ff99
_VM_COR_ERRO  = 0xFF6B6B

def _vm_embed_ok(titulo: str, desc: str) -> discord.Embed:
    e = discord.Embed(title=titulo, description=desc, color=_VM_COR_OK, timestamp=datetime.utcnow())
    e.set_footer(text="🦇 Vampy VoiceMaster")
    return e

def _vm_embed_erro(desc: str) -> discord.Embed:
    e = discord.Embed(title="❌ Eita!!", description=desc, color=_VM_COR_ERRO, timestamp=datetime.utcnow())
    e.set_footer(text="🦇 Vampy VoiceMaster")
    return e

def _vm_embed_info(titulo: str, desc: str) -> discord.Embed:
    e = discord.Embed(title=titulo, description=desc, color=_VM_COR_FOFA, timestamp=datetime.utcnow())
    e.set_footer(text="🦇 Vampy VoiceMaster")
    return e

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📝  MODAIS DO VOICEMASTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class VMModalRenomear(discord.ui.Modal, title="✏️ Renomear Sua Call"):
    nome = discord.ui.TextInput(label="Novo nome da call", placeholder="Ex: 🎮 Call dos Gamers", min_length=1, max_length=100, required=True)

    def __init__(self, cog, channel):
        super().__init__()
        self.cog = cog
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        try:
            await self.channel.edit(name=self.nome.value)
            await interaction.response.send_message(embed=_vm_embed_ok("✏️ Renomeada!!", _vm_msg("renomeada", nome=self.nome.value)), ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(embed=_vm_embed_erro("Não consegui renomear... sem permissão!! 😢🦇"), ephemeral=True)


class VMModalLimite(discord.ui.Modal, title="👥 Limite de Usuários"):
    limite = discord.ui.TextInput(label="Limite (0 = sem limite, máx 99)", placeholder="Ex: 5", min_length=1, max_length=2, required=True)

    def __init__(self, cog, channel):
        super().__init__()
        self.cog = cog
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        try:
            n = int(self.limite.value)
            if n < 0 or n > 99:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(embed=_vm_embed_erro("Número inválido!! Coloca entre 0 e 99!! 🥺🦇"), ephemeral=True)
            return
        try:
            await self.channel.edit(user_limit=n)
            txt = _vm_msg("limite_removido") if n == 0 else _vm_msg("limite_set", limite=n)
            titulo = "👥 Limite Removido!!" if n == 0 else "👥 Limite Definido!!"
            await interaction.response.send_message(embed=_vm_embed_ok(titulo, txt), ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(embed=_vm_embed_erro("Sem permissão pra alterar o limite!! 😢🦇"), ephemeral=True)


class VMModalBitrate(discord.ui.Modal, title="🎙️ Qualidade de Áudio"):
    bitrate = discord.ui.TextInput(label="Bitrate em kbps (8–384)", placeholder="Ex: 64, 96, 128", min_length=1, max_length=3, required=True)

    def __init__(self, cog, channel):
        super().__init__()
        self.cog = cog
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        try:
            n = int(self.bitrate.value)
            if n < 8 or n > 384:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(embed=_vm_embed_erro("Coloca um bitrate entre 8 e 384 kbps!! 🥺🦇"), ephemeral=True)
            return
        try:
            await self.channel.edit(bitrate=n * 1000)
            await interaction.response.send_message(embed=_vm_embed_ok("🎙️ Bitrate Atualizado!!", _vm_msg("bitrate_set", bitrate=n)), ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(embed=_vm_embed_erro("Sem permissão pra mudar o bitrate!! 😢🦇"), ephemeral=True)


class VMModalStatus(discord.ui.Modal, title="📝 Status da Call"):
    status = discord.ui.TextInput(
        label="Status (deixe vazio pra remover)",
        placeholder="Ex: 🎮 Jogando Valorant • 🎵 Ouvindo música",
        min_length=0,
        max_length=500,
        required=False,
        style=discord.TextStyle.short
    )

    def __init__(self, cog, channel):
        super().__init__()
        self.cog = cog
        self.channel = channel

    async def on_submit(self, interaction: discord.Interaction):
        novo_status = self.status.value.strip()
        try:
            await self.channel.edit(status=novo_status if novo_status else None)
            if novo_status:
                await interaction.response.send_message(
                    embed=_vm_embed_ok("📝 Status Atualizado!!", f"Status da call agora é: **{novo_status}** ✨🦇"),
                    ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    embed=_vm_embed_ok("📝 Status Removido!!", "O status da call foi removido!! 🧹🦇"),
                    ephemeral=True
                )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=_vm_embed_erro("Sem permissão pra mudar o status!! 😢🦇"), ephemeral=True
            )
        except Exception:
            await interaction.response.send_message(
                embed=_vm_embed_erro("Não consegui mudar o status... tenta de novo!! 🥺🦇"), ephemeral=True
            )


class VMModalConvidar(discord.ui.Modal, title="💌 Convidar para a Call"):
    usuario = discord.ui.TextInput(
        label="Nome ou ID do usuário",
        placeholder="Ex: fulano ou 123456789",
        required=True
    )

    def __init__(self, cog, channel, guild):
        super().__init__()
        self.cog     = cog
        self.channel = channel
        self.guild   = guild

    async def on_submit(self, interaction: discord.Interaction):
        target = _vm_find_member(self.guild, self.usuario.value)
        if not target:
            await interaction.response.send_message(embed=_vm_embed_erro("Não achei esse usuário!! 🔍🦇"), ephemeral=True)
            return
        if target.id == interaction.user.id:
            await interaction.response.send_message(embed=_vm_embed_erro("Você não pode se convidar, bobão(a)!! 🥺🦇"), ephemeral=True)
            return
        if target.bot:
            await interaction.response.send_message(embed=_vm_embed_erro("Não dá pra convidar bots!! 🤖🦇"), ephemeral=True)
            return
        # Criar link de convite temporário (1h, 1 uso) pro canal de voz
        try:
            invite = await self.channel.create_invite(max_age=3600, max_uses=1, unique=True, reason="Vampy VoiceMaster — convite da call")
        except discord.Forbidden:
            await interaction.response.send_message(embed=_vm_embed_erro("Sem permissão pra criar convite!! 😢🦇"), ephemeral=True)
            return
        # Enviar DM pro usuário convidado
        try:
            embed_inv = discord.Embed(
                title="💌 Você foi convidado(a) para uma call!!",
                description=(
                    f"**{interaction.user.display_name}** te convidou pra entrar na call "
                    f"**{self.channel.name}** no servidor **{self.guild.name}**!! 🥳🦇\n\n"
                    f"🔗 **Clique para entrar:** {invite.url}\n\n"
                    f"> *Este convite expira em 1 hora e pode ser usado 1 vez.*"
                ),
                color=_VM_COR_FOFA,
                timestamp=datetime.utcnow()
            )
            embed_inv.set_thumbnail(url=interaction.user.display_avatar.url)
            embed_inv.set_footer(text="🦇 Vampy VoiceMaster")
            await target.send(embed=embed_inv)
            await interaction.response.send_message(
                embed=_vm_embed_ok("💌 Convite Enviado!!", f"**{target.display_name}** recebeu o convite na DM!! 🦇"),
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                embed=_vm_embed_erro(f"**{target.display_name}** tá com a DM fechada... não consegui enviar!! 😢🦇"),
                ephemeral=True
            )


def _vm_find_member(guild: discord.Guild, texto: str):
    texto = texto.strip().lstrip("<@!>").rstrip(">")
    try:
        return guild.get_member(int(texto))
    except ValueError:
        return discord.utils.find(lambda m: m.name.lower() == texto.lower() or m.display_name.lower() == texto.lower(), guild.members)


class VMModalKick(discord.ui.Modal, title="👋 Kickar da Call"):
    usuario = discord.ui.TextInput(label="Nome ou ID do usuário", placeholder="Ex: fulano ou 123456789", required=True)

    def __init__(self, cog, channel, guild):
        super().__init__()
        self.cog = cog
        self.channel = channel
        self.guild = guild

    async def on_submit(self, interaction: discord.Interaction):
        target = _vm_find_member(self.guild, self.usuario.value)
        if not target:
            await interaction.response.send_message(embed=_vm_embed_erro("Não achei esse usuário!! 🔍🦇"), ephemeral=True)
            return
        if target not in self.channel.members:
            await interaction.response.send_message(embed=_vm_embed_erro(_vm_msg("user_nao_na_call")), ephemeral=True)
            return
        if target.id == interaction.user.id:
            await interaction.response.send_message(embed=_vm_embed_erro("Você não pode kickar você mesmo, bobão(a)!! 🥺🦇"), ephemeral=True)
            return
        try:
            await target.move_to(None, reason="Kickado da call pelo dono — Vampy VoiceMaster")
            await interaction.response.send_message(embed=_vm_embed_ok("👋 Kickado!!", _vm_msg("usuario_kickado", user=target.display_name)), ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(embed=_vm_embed_erro("Não consegui kickar... sem permissão!! 😢🦇"), ephemeral=True)


class VMModalBanir(discord.ui.Modal):
    usuario = discord.ui.TextInput(label="Nome ou ID do usuário", placeholder="Ex: fulano ou 123456789", required=True)

    def __init__(self, cog, channel, guild, ban: bool = True):
        super().__init__(title="🚫 Banir da Call" if ban else "✅ Permitir na Call")
        self.cog = cog
        self.channel = channel
        self.guild = guild
        self.ban = ban

    async def on_submit(self, interaction: discord.Interaction):
        target = _vm_find_member(self.guild, self.usuario.value)
        if not target:
            await interaction.response.send_message(embed=_vm_embed_erro("Não achei esse usuário!! 🔍🦇"), ephemeral=True)
            return
        info = self.cog.vm_channels.get(self.channel.id, {})
        if self.ban:
            info.setdefault("banned", [])
            if target.id not in info["banned"]:
                info["banned"].append(target.id)
            await self.channel.set_permissions(target, connect=False, view_channel=False)
            if target in self.channel.members:
                try:
                    await target.move_to(None)
                except Exception:
                    pass
            await interaction.response.send_message(embed=_vm_embed_ok("🚫 Banido!!", _vm_msg("usuario_banido", user=target.display_name)), ephemeral=True)
        else:
            if "banned" in info and target.id in info["banned"]:
                info["banned"].remove(target.id)
            await self.channel.set_permissions(target, connect=True, view_channel=True)
            await interaction.response.send_message(embed=_vm_embed_ok("✅ Permitido!!", _vm_msg("usuario_permitido", user=target.display_name)), ephemeral=True)


class VMModalTransferir(discord.ui.Modal, title="👑 Transferir Dono"):
    usuario = discord.ui.TextInput(label="Nome ou ID do novo dono", placeholder="Ex: fulano ou 123456789", required=True)

    def __init__(self, cog, channel, guild):
        super().__init__()
        self.cog = cog
        self.channel = channel
        self.guild = guild

    async def on_submit(self, interaction: discord.Interaction):
        target = _vm_find_member(self.guild, self.usuario.value)
        if not target:
            await interaction.response.send_message(embed=_vm_embed_erro("Não achei esse usuário!! 🔍🦇"), ephemeral=True)
            return
        if target.id == interaction.user.id:
            await interaction.response.send_message(embed=_vm_embed_erro("Você já é o(a) dono(a)!! 😄🦇"), ephemeral=True)
            return
        if target not in self.channel.members:
            await interaction.response.send_message(embed=_vm_embed_erro(_vm_msg("user_nao_na_call")), ephemeral=True)
            return
        info = self.cog.vm_channels.get(self.channel.id, {})
        info["owner"] = target.id
        await interaction.response.send_message(embed=_vm_embed_ok("👑 Dono Transferido!!", _vm_msg("dono_transferido", user=target.display_name)), ephemeral=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎛️  PAINEL DE CONTROLE (View com Botões)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class VMPainelView(discord.ui.View):
    """Painel de controle fofo das calls — botões persistentes."""

    def __init__(self, cog: "VoiceMasterCog"):
        super().__init__(timeout=None)
        self.cog = cog

    def _get_owner_channel(self, interaction: discord.Interaction):
        """Retorna o canal do qual o usuário é dono E está dentro, ou None."""
        for ch_id, info in self.cog.vm_channels.items():
            if info["owner"] == interaction.user.id:
                ch = interaction.guild.get_channel(ch_id)
                if ch and interaction.user in ch.members:
                    return ch
        return None

    async def _check(self, interaction: discord.Interaction):
        ch = self._get_owner_channel(interaction)
        if not ch:
            await interaction.response.send_message(embed=_vm_embed_erro(_vm_msg("sem_call", user=interaction.user.mention)), ephemeral=True)
        return ch

    # ── Linha 1 ──────────────────────────────────

    @discord.ui.button(label="✏️ Renomear", style=discord.ButtonStyle.primary, custom_id="vm_renomear", row=0)
    async def btn_renomear(self, interaction: discord.Interaction, button: discord.ui.Button):
        ch = await self._check(interaction)
        if ch:
            await interaction.response.send_modal(VMModalRenomear(self.cog, ch))

    @discord.ui.button(label="👥 Limite", style=discord.ButtonStyle.primary, custom_id="vm_limite", row=0)
    async def btn_limite(self, interaction: discord.Interaction, button: discord.ui.Button):
        ch = await self._check(interaction)
        if ch:
            await interaction.response.send_modal(VMModalLimite(self.cog, ch))

    @discord.ui.button(label="🔒 Trancar", style=discord.ButtonStyle.secondary, custom_id="vm_trancar", row=0)
    async def btn_trancar(self, interaction: discord.Interaction, button: discord.ui.Button):
        ch = await self._check(interaction)
        if not ch:
            return
        info = self.cog.vm_channels[ch.id]
        everyone = interaction.guild.default_role
        if info.get("locked"):
            await ch.set_permissions(everyone, connect=None)
            info["locked"] = False
            await interaction.response.send_message(embed=_vm_embed_ok("🔓 Destrancada!!", _vm_msg("destrancada")), ephemeral=True)
        else:
            await ch.set_permissions(everyone, connect=False)
            info["locked"] = True
            await interaction.response.send_message(embed=_vm_embed_ok("🔒 Trancada!!", _vm_msg("trancada")), ephemeral=True)

    @discord.ui.button(label="👻 Ocultar", style=discord.ButtonStyle.secondary, custom_id="vm_ocultar", row=0)
    async def btn_ocultar(self, interaction: discord.Interaction, button: discord.ui.Button):
        ch = await self._check(interaction)
        if not ch:
            return
        info = self.cog.vm_channels[ch.id]
        everyone = interaction.guild.default_role
        if info.get("hidden"):
            # ── Revelar: remove só o view_channel do everyone, preserva connect (lock) ──
            ow = ch.overwrites_for(everyone)
            ow.view_channel = None
            if ow.is_empty():
                await ch.set_permissions(everyone, overwrite=None)
            else:
                await ch.set_permissions(everyone, overwrite=ow)
            # Remove o override de view_channel dos membros que estavam dentro
            for membro in ch.members:
                ow_m = ch.overwrites_for(membro)
                ow_m.view_channel = None
                ow_m.connect      = None
                if ow_m.is_empty():
                    await ch.set_permissions(membro, overwrite=None)
                else:
                    await ch.set_permissions(membro, overwrite=ow_m)
            info["hidden"] = False
            await interaction.response.send_message(embed=_vm_embed_ok("👁️ Visível!!", _vm_msg("visivel")), ephemeral=True)
        else:
            # ── Ocultar: esconde do everyone, garante view+connect pra quem já está dentro ──
            ow = ch.overwrites_for(everyone)
            ow.view_channel = False
            await ch.set_permissions(everyone, overwrite=ow)
            # Explicitamente view_channel=True e connect=True pra cada membro dentro
            for membro in ch.members:
                ow_m = ch.overwrites_for(membro)
                ow_m.view_channel = True
                ow_m.connect      = True
                await ch.set_permissions(membro, overwrite=ow_m)
            info["hidden"] = True
            await interaction.response.send_message(embed=_vm_embed_ok("👻 Oculta!!", _vm_msg("invisivel")), ephemeral=True)

    # ── Linha 2 ──────────────────────────────────

    @discord.ui.button(label="👋 Kickar", style=discord.ButtonStyle.danger, custom_id="vm_kickar", row=1)
    async def btn_kickar(self, interaction: discord.Interaction, button: discord.ui.Button):
        ch = await self._check(interaction)
        if ch:
            await interaction.response.send_modal(VMModalKick(self.cog, ch, interaction.guild))

    @discord.ui.button(label="🚫 Banir", style=discord.ButtonStyle.danger, custom_id="vm_banir", row=1)
    async def btn_banir(self, interaction: discord.Interaction, button: discord.ui.Button):
        ch = await self._check(interaction)
        if ch:
            await interaction.response.send_modal(VMModalBanir(self.cog, ch, interaction.guild, ban=True))

    @discord.ui.button(label="✅ Permitir", style=discord.ButtonStyle.success, custom_id="vm_permitir", row=1)
    async def btn_permitir(self, interaction: discord.Interaction, button: discord.ui.Button):
        ch = await self._check(interaction)
        if ch:
            await interaction.response.send_modal(VMModalBanir(self.cog, ch, interaction.guild, ban=False))

    @discord.ui.button(label="👑 Transferir", style=discord.ButtonStyle.success, custom_id="vm_transferir", row=1)
    async def btn_transferir(self, interaction: discord.Interaction, button: discord.ui.Button):
        ch = await self._check(interaction)
        if ch:
            await interaction.response.send_modal(VMModalTransferir(self.cog, ch, interaction.guild))

    @discord.ui.button(label="💌 Convidar", style=discord.ButtonStyle.primary, custom_id="vm_convidar", row=1)
    async def btn_convidar(self, interaction: discord.Interaction, button: discord.ui.Button):
        ch = await self._check(interaction)
        if ch:
            await interaction.response.send_modal(VMModalConvidar(self.cog, ch, interaction.guild))

    # ── Linha 3 ──────────────────────────────────

    @discord.ui.button(label="📝 Status", style=discord.ButtonStyle.secondary, custom_id="vm_status", row=2)
    async def btn_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        ch = await self._check(interaction)
        if ch:
            await interaction.response.send_modal(VMModalStatus(self.cog, ch))

    @discord.ui.button(label="📊 Info", style=discord.ButtonStyle.secondary, custom_id="vm_info", row=2)
    async def btn_info(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        if not user.voice or not user.voice.channel:
            await interaction.response.send_message(embed=_vm_embed_erro("Você não tá em nenhuma call!! 🥺🦇"), ephemeral=True)
            return
        ch = user.voice.channel
        info = self.cog.vm_channels.get(ch.id)
        if not info:
            await interaction.response.send_message(embed=_vm_embed_erro("Essa call não é gerenciada pela Vampy!! 🤔🦇"), ephemeral=True)
            return
        dono = interaction.guild.get_member(info["owner"])
        banidos = ", ".join(f"<@{uid}>" for uid in info.get("banned", [])) or "Ninguém"
        embed = discord.Embed(title=f"📊 Info: {ch.name}", color=_VM_COR_FOFA, timestamp=datetime.utcnow())
        embed.add_field(name="👑 Dono(a)", value=dono.mention if dono else "Desconhecido", inline=True)
        embed.add_field(name="👥 Membros", value=f"`{len(ch.members)}`" + (f"/{ch.user_limit}" if ch.user_limit else " (sem limite)"), inline=True)
        embed.add_field(name="🎧 Bitrate", value=f"`{ch.bitrate // 1000}kbps`", inline=True)
        embed.add_field(name="🔒 Trancada", value="Sim 🔒" if info.get("locked") else "Não 🔓", inline=True)
        embed.add_field(name="👻 Oculta", value="Sim 👻" if info.get("hidden") else "Não 👁️", inline=True)
        embed.add_field(name="💎 Permanente", value="Sim 💎" if info.get("permanent") else "Não 🕐", inline=True)
        embed.add_field(name="🚫 Banidos", value=banidos, inline=False)
        embed.set_footer(text="🦇 Vampy VoiceMaster")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🎙️ Bitrate", style=discord.ButtonStyle.secondary, custom_id="vm_bitrate", row=2)
    async def btn_bitrate(self, interaction: discord.Interaction, button: discord.ui.Button):
        ch = await self._check(interaction)
        if ch:
            await interaction.response.send_modal(VMModalBitrate(self.cog, ch))

    @discord.ui.button(label="🏳️ Reivindicar", style=discord.ButtonStyle.success, custom_id="vm_reivindicar", row=2)
    async def btn_reivindicar(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        if not user.voice or not user.voice.channel:
            await interaction.response.send_message(embed=_vm_embed_erro(_vm_msg("nao_na_call", user=user.mention)), ephemeral=True)
            return
        ch = user.voice.channel
        info = self.cog.vm_channels.get(ch.id)
        if not info:
            await interaction.response.send_message(embed=_vm_embed_erro("Essa call não é gerenciada pela Vampy!! 🤔🦇"), ephemeral=True)
            return
        if info["owner"] == user.id:
            await interaction.response.send_message(embed=_vm_embed_erro(_vm_msg("ja_dono")), ephemeral=True)
            return
        dono_atual = interaction.guild.get_member(info["owner"])
        if dono_atual and dono_atual in ch.members:
            await interaction.response.send_message(embed=_vm_embed_erro(_vm_msg("dono_ainda_na_call")), ephemeral=True)
            return
        info["owner"] = user.id
        await interaction.response.send_message(embed=_vm_embed_ok("👑 Reivindicado!!", _vm_msg("dono_reivindicado")), ephemeral=True)

    # ── Linha 4 — Spotyvampy ─────────────────────

    @discord.ui.button(label="🎵 Spotyvampy", style=discord.ButtonStyle.primary, custom_id="vm_spotyvampy", row=3)
    async def btn_spotyvampy(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Abre o painel de música Spotyvampy diretamente do painel da call."""
        sv_cog = interaction.client.cogs.get("SpotyvampyCog")
        if not sv_cog:
            await interaction.response.send_message("❌ Spotyvampy não está disponível no momento!! 🥺🦇", ephemeral=True)
            return
        guild  = interaction.guild
        player = sv_cog.players.get(guild.id)
        embed  = sv_cog._embed_painel(player)
        view   = MusicControlView(sv_cog, guild.id)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🦇  COG — VOICEMASTER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class VoiceMasterCog(commands.Cog, name="VampyVoiceMaster"):
    """VAMPY VOICEMASTER — Calls Fofas v1.0 🦇"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.vm_channels: dict[int, dict] = {}   # {ch_id: {owner, locked, hidden, permanent, banned, lobby_id}}
        self.vm_lobbies:  dict[int, int]  = {}   # {guild_id: lobby_ch_id}
        self._painel_view = VMPainelView(self)
        bot.add_view(self._painel_view)

    # ── Utilitário ────────────────────────────────

    async def _log(self, guild: discord.Guild) -> discord.TextChannel | None:
        return discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)

    def _nome(self, member: discord.Member) -> str:
        return VM_DEFAULT_NAME.format(user=member.display_name)

    # ── 🟢 Boot ───────────────────────────────────

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(6)  # ligeiramente após o Security
        for guild in self.bot.guilds:
            # ── Verificar se já existe o lobby pelo nome na categoria ──
            categoria = guild.get_channel(VM_CATEGORY_ID)
            existing  = discord.utils.get(guild.voice_channels, name=VM_LOBBY_NAME)

            if existing:
                # Já existe — só registrar
                self.vm_lobbies[guild.id] = existing.id
            else:
                # Não existe — criar automaticamente na categoria certa
                try:
                    lobby = await guild.create_voice_channel(
                        name=VM_LOBBY_NAME,
                        category=categoria,
                        reason="Vampy VoiceMaster — criação automática no boot"
                    )
                    self.vm_lobbies[guild.id] = lobby.id
                except discord.Forbidden:
                    pass

            log_ch = await self._log(guild)
            if not log_ch:
                continue
            lobby_id = self.vm_lobbies.get(guild.id)
            lobby    = guild.get_channel(lobby_id) if lobby_id else None
            embed = discord.Embed(
                title="🎙️ Vampy VoiceMaster Online!!",
                description=(
                    "```\n"
                    "╔══════════════════════════════════════╗\n"
                    "║   VAMPY VOICEMASTER  🦇          ║\n"
                    "║     — Calls Fofas v1.0 —            ║\n"
                    "║       ✅  ONLINE  ✅                 ║\n"
                    "╚══════════════════════════════════════╝\n"
                    "```"
                ),
                color=_VM_COR_OK,
                timestamp=datetime.utcnow()
            )
            embed.add_field(
                name="🎙️ Status",
                value=(
                    f"**Lobby:** {lobby.mention if lobby else '❌ Sem permissão pra criar!!'}\n"
                    f"**Categoria:** {categoria.name if categoria else '❌ ID não encontrado'}\n"
                    f"**Servidor:** `{guild.name}` | **Membros:** `{guild.member_count}`"
                ),
                inline=False
            )
            embed.add_field(
                name="📋 Comandos",
                value="`v!vm painel` • `!vm reset` • `!vm info`",
                inline=False
            )
            embed.set_footer(text="🦇 Vampy VoiceMaster • Calls com muito amor!!")
            await log_ch.send(embed=embed)

    # ── 🎙️ Entrou/saiu de voz ─────────────────────

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        guild = member.guild

        # Entrou em um canal
        if after.channel:
            lobby_id = self.vm_lobbies.get(guild.id)
            if lobby_id and after.channel.id == lobby_id:
                await self._criar_call(member, after.channel)

        # Saiu de um canal gerenciado
        if before.channel and before.channel.id in self.vm_channels:
            ch   = before.channel
            info = self.vm_channels[ch.id]
            await asyncio.sleep(VM_EMPTY_DELAY)
            ch = guild.get_channel(ch.id)
            if ch and len(ch.members) == 0 and not info.get("permanent"):
                await self._deletar_call(ch)

    async def _criar_call(self, member: discord.Member, lobby: discord.VoiceChannel):
        guild = member.guild
        try:
            categoria = guild.get_channel(VM_CATEGORY_ID) or lobby.category
            novo = await guild.create_voice_channel(
                name=self._nome(member),
                category=categoria,
                user_limit=VM_DEFAULT_LIMIT,
                reason=f"Vampy VoiceMaster: call de {member}"
            )
            await novo.set_permissions(member, connect=True, manage_channels=True, move_members=True)
            self.vm_channels[novo.id] = {
                "owner": member.id, "locked": False, "hidden": False,
                "permanent": False, "banned": [], "lobby_id": lobby.id,
                "created_at": datetime.utcnow()
            }
            try:
                await member.move_to(novo, reason="Vampy VoiceMaster")
            except discord.HTTPException:
                pass

            # ── Enviar painel de controle no chat de texto da call ──
            try:
                embed_call = discord.Embed(
                    title="🎙️ Painel de Controle — Calls da Vampy",
                    description=(
                        f"Oi, {member.mention}!! Sua call foi criada!! 🥳🦇\n"
                        "Use os botões abaixo pra gerenciar ela!! 💕\n\n"
                        "```\n"
                        "╔══════════════════════════════════════╗\n"
                        "║   VAMPY VOICEMASTER  🦇          ║\n"
                        "║     — Calls Fofas v1.0 —            ║\n"
                        "╚══════════════════════════════════════╝\n"
                        "```"
                    ),
                    color=_VM_COR_FOFA,
                    timestamp=datetime.utcnow()
                )
                campos_call = [
                    ("✏️ Renomear",    "Muda o nome da call"),
                    ("👥 Limite",      "Define qtd máxima de pessoas"),
                    ("🔒 Trancar",     "Bloqueia novas entradas"),
                    ("👻 Ocultar",     "Esconde a call de todos"),
                    ("👋 Kickar",      "Remove alguém da call"),
                    ("🚫 Banir",       "Bloqueia alguém de entrar"),
                    ("✅ Permitir",    "Desbanir / liberar alguém"),
                    ("👑 Transferir",  "Passa o dono pra outra pessoa"),
                    ("💌 Convidar",    "Envia convite na DM de alguém"),
                    ("📝 Status",      "Define o status/tema da call"),
                    ("📊 Info",        "Mostra detalhes da call"),
                    ("🎙️ Bitrate",     "Muda a qualidade do áudio"),
                    ("🏳️ Reivindicar", "Assume a call se o dono saiu"),
                ]
                for titulo, desc in campos_call:
                    embed_call.add_field(name=titulo, value=desc, inline=True)
                embed_call.set_footer(text="🦇 Vampy VoiceMaster • Feito com muito amor!!")
                # Envia no chat de texto interno do canal de voz
                await novo.send(embed=embed_call, view=VMPainelView(self))
            except (discord.Forbidden, discord.HTTPException):
                pass  # sem permissão ou canal sem chat — ignora

            # Log
            log_ch = await self._log(guild)
            if log_ch:
                embed = discord.Embed(
                    title="🎙️ Nova Call Criada!!",
                    description=f"{member.mention} criou a call **{novo.name}**!! 🥳🦇",
                    color=_VM_COR_OK, timestamp=datetime.utcnow()
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text="🦇 Vampy VoiceMaster")
                await log_ch.send(embed=embed)
        except discord.Forbidden:
            pass

    async def _deletar_call(self, channel: discord.VoiceChannel):
        self.vm_channels.pop(channel.id, None)
        try:
            await channel.delete(reason="Vampy VoiceMaster: call vazia")
        except (discord.NotFound, discord.Forbidden):
            pass

    # ── 🎛️ Painel ─────────────────────────────────

    async def _enviar_painel(self, channel: discord.TextChannel):
        embed = discord.Embed(
            title="🎙️ Painel de Controle — Calls da Vampy",
            description=(
                "Gerencie sua call com os botinhos aqui embaixo!! 🦇\n"
                "Você precisa ser **dono(a)** de uma call e estar **dentro dela** pra usar!! 💕\n\n"
                "```\n"
                "╔══════════════════════════════════════╗\n"
                "║   VAMPY VOICEMASTER  🦇          ║\n"
                "║     — Calls Fofas v1.0 —            ║\n"
                "╚══════════════════════════════════════╝\n"
                "```"
            ),
            color=_VM_COR_FOFA, timestamp=datetime.utcnow()
        )
        campos = [
            ("✏️ Renomear",    "Muda o nome da call"),
            ("👥 Limite",      "Define qtd máxima de pessoas"),
            ("🔒 Trancar",     "Bloqueia novas entradas"),
            ("👻 Ocultar",     "Esconde a call de todos"),
            ("👋 Kickar",      "Remove alguém da call"),
            ("🚫 Banir",       "Bloqueia alguém de entrar"),
            ("✅ Permitir",    "Desbanir / liberar alguém"),
            ("👑 Transferir",  "Passa o dono pra outra pessoa"),
            ("💌 Convidar",    "Envia convite na DM de alguém"),
            ("📊 Info",        "Mostra detalhes da call"),
            ("🎙️ Bitrate",     "Muda a qualidade do áudio"),
            ("📝 Status",      "Define o status/tema da call"),
            ("🏳️ Reivindicar", "Assume a call se o dono saiu"),
        ]
        for titulo, desc in campos:
            embed.add_field(name=titulo, value=desc, inline=True)
        embed.set_footer(text="🦇 Vampy VoiceMaster • Feito com muito amor!!")
        view = VMPainelView(self)
        return await channel.send(embed=embed, view=view)

    # ── 🔧 Comandos !vm ───────────────────────────

    @commands.group(name="vm", aliases=["voicemaster", "call"], invoke_without_command=True)
    async def vm_group(self, ctx: commands.Context):
        await ctx.send(embed=_vm_embed_info(
            "🎙️ Vampy VoiceMaster",
            "`v!vm setup` • `!vm painel` • `!vm reset` • `!vm info`\n\nOu use os botões no painel de controle!! 🦇"
        ), delete_after=15)

    @vm_group.command(name="setup")
    @commands.has_permissions(administrator=True)
    async def vm_setup(self, ctx: commands.Context):
        guild = ctx.guild
        if guild.id in self.vm_lobbies:
            existing = guild.get_channel(self.vm_lobbies[guild.id])
            if existing:
                await ctx.send(embed=_vm_embed_erro(_vm_msg("setup_existe")), delete_after=10)
                return
        try:
            categoria = guild.get_channel(VM_CATEGORY_ID)
            lobby = await guild.create_voice_channel(name=VM_LOBBY_NAME, category=categoria, reason="Vampy VoiceMaster Setup")
            self.vm_lobbies[guild.id] = lobby.id
            await self._enviar_painel(ctx.channel)
            embed = discord.Embed(
                title="🎉 VoiceMaster Configurado!!",
                description=f"Tudo prontinha!! 🥳🦇\n\n**Canal Lobby:** {lobby.mention}\n\nPeça pras pessoas entrarem em {lobby.mention} pra criar uma call!!",
                color=_VM_COR_OK, timestamp=datetime.utcnow()
            )
            embed.set_footer(text="🦇 Vampy VoiceMaster")
            await ctx.send(embed=embed, delete_after=20)
            log_ch = await self._log(guild)
            if log_ch:
                await log_ch.send(embed=discord.Embed(
                    title="✅ VoiceMaster Ativado!!",
                    description=f"Configurado por **{ctx.author.mention}**!! Lobby: {lobby.mention} 🎙️🦇",
                    color=_VM_COR_OK, timestamp=datetime.utcnow()
                ))
        except discord.Forbidden:
            await ctx.send(embed=_vm_embed_erro("Sem permissão pra criar canais!! 😢🦇"), delete_after=10)

    @vm_group.command(name="painel")
    @commands.has_permissions(manage_channels=True)
    async def vm_painel(self, ctx: commands.Context):
        await self._enviar_painel(ctx.channel)
        try:
            await ctx.message.delete()
        except Exception:
            pass

    @vm_group.command(name="reset")
    @commands.has_permissions(administrator=True)
    async def vm_reset(self, ctx: commands.Context):
        guild   = ctx.guild
        deletadas = 0
        lobby_id  = self.vm_lobbies.pop(guild.id, None)
        for ch_id in list(self.vm_channels.keys()):
            info = self.vm_channels.get(ch_id, {})
            if info.get("lobby_id") == lobby_id:
                ch = guild.get_channel(ch_id)
                if ch:
                    try:
                        await ch.delete(reason="Vampy VoiceMaster Reset")
                        deletadas += 1
                    except Exception:
                        pass
                self.vm_channels.pop(ch_id, None)
        if lobby_id:
            old = guild.get_channel(lobby_id)
            if old:
                try:
                    await old.delete(reason="Vampy VoiceMaster Reset")
                except Exception:
                    pass
        await ctx.send(embed=_vm_embed_ok("🧹 Resetado!!", f"Limpei **{deletadas}** call(s)!! Use `!vm setup` pra configurar de novo!! 🦇"), delete_after=15)

    @vm_group.command(name="info")
    @commands.has_permissions(manage_channels=True)
    async def vm_info(self, ctx: commands.Context):
        guild    = ctx.guild
        lobby_id = self.vm_lobbies.get(guild.id)
        lobby    = guild.get_channel(lobby_id) if lobby_id else None
        ativas   = sum(1 for ch_id in self.vm_channels if guild.get_channel(ch_id))
        perms    = sum(1 for ch_id, i in self.vm_channels.items() if i.get("permanent") and guild.get_channel(ch_id))
        tran     = sum(1 for ch_id, i in self.vm_channels.items() if i.get("locked")    and guild.get_channel(ch_id))
        embed = discord.Embed(title="📊 Vampy VoiceMaster — Info", color=_VM_COR_FOFA, timestamp=datetime.utcnow())
        embed.add_field(name="🎙️ Canal Lobby",  value=lobby.mention if lobby else "❌ Não configurado", inline=False)
        embed.add_field(name="📞 Calls Ativas", value=f"`{ativas}`",  inline=True)
        embed.add_field(name="💎 Permanentes",  value=f"`{perms}`",   inline=True)
        embed.add_field(name="🔒 Trancadas",    value=f"`{tran}`",    inline=True)
        embed.set_footer(text="🦇 Vampy VoiceMaster")
        await ctx.send(embed=embed)

    @vm_group.error
    async def vm_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=_vm_embed_erro("Você não tem permissão pra usar esse comando!! 🥺🦇"), delete_after=8)


# ══════════════════════════════════════════════════════════════════
# FIM DO VOICEMASTER
# ══════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════
# 🧹 COMANDO — LIMPAR CANAL COMPLETO
# ══════════════════════════════════════════════════════════════════

@bot.command(name="ativarlimpezacanal", aliases=["limparchat", "clearchat", "purgecanal"])
@commands.has_permissions(manage_messages=True)
async def ativar_limpeza_canal(ctx: commands.Context):
    """Apaga TODAS as mensagens do canal onde o comando foi executado."""

    canal = ctx.channel

    # ── Confirmação antes de limpar ──────────────────────────────
    embed_confirm = discord.Embed(
        title="🧹 Limpar Canal — Confirmação",
        description=(
            f"Você tem certeza que quer apagar **TODAS** as mensagens de {canal.mention}??\n\n"
            "⚠️ **Essa ação não pode ser desfeita!!** 🦇\n\n"
            "Responda com `sim` nos próximos **15 segundos** pra confirmar!!"
        ),
        color=0xffaa00,
        timestamp=datetime.utcnow()
    )
    embed_confirm.set_footer(text="🦇 Vampy Security • Limpeza de Canal")
    await ctx.send(embed=embed_confirm)

    def check(m):
        return m.author == ctx.author and m.channel == canal and m.content.lower() in ("sim", "não", "nao", "cancelar")

    try:
        resposta = await bot.wait_for("message", timeout=15.0, check=check)
    except asyncio.TimeoutError:
        await ctx.send(embed=discord.Embed(
            title="⏰ Tempo esgotado!!",
            description="Limpeza cancelada por falta de confirmação!! 🦇",
            color=0x888888,
            timestamp=datetime.utcnow()
        ), delete_after=8)
        return

    if resposta.content.lower() not in ("sim",):
        await ctx.send(embed=discord.Embed(
            title="❌ Limpeza Cancelada!!",
            description="Operação cancelada!! Nenhuma mensagem foi apagada!! 🦇",
            color=0xff4444,
            timestamp=datetime.utcnow()
        ), delete_after=8)
        return

    # ── Executar a limpeza ────────────────────────────────────────
    await ctx.send(embed=discord.Embed(
        title="⏳ Limpando canal...",
        description="Aguarda um segundo, tô apagando tudo!! 🧹🦇",
        color=0xffaa00,
        timestamp=datetime.utcnow()
    ))

    try:
        deletadas = await canal.purge(limit=None, bulk=True)
        total = len(deletadas)

        embed_ok = discord.Embed(
            title="✅ Canal Limpo!!",
            description=(
                f"🧹 **{total} mensagens** foram apagadas de {canal.mention}!!\n\n"
                f"👤 Executado por: {ctx.author.mention}\n"
                f"📅 Horário (UTC): `{datetime.utcnow().strftime('%d/%m/%Y às %H:%M:%S')}`"
            ),
            color=0x00ff99,
            timestamp=datetime.utcnow()
        )
        embed_ok.set_footer(text="🦇 Vampy Security • Limpeza Concluída")
        await canal.send(embed=embed_ok, delete_after=10)

    except discord.Forbidden:
        await ctx.send(embed=discord.Embed(
            title="❌ Sem Permissão!!",
            description="Não tenho permissão pra apagar mensagens nesse canal!! 😢🦇",
            color=0xff4444,
            timestamp=datetime.utcnow()
        ), delete_after=10)

    except discord.HTTPException as e:
        await ctx.send(embed=discord.Embed(
            title="⚠️ Erro ao Limpar!!",
            description=f"Ocorreu um erro durante a limpeza!!\n`{e}`\n\nTenta de novo!! 🦇",
            color=0xff8800,
            timestamp=datetime.utcnow()
        ), delete_after=10)


@ativar_limpeza_canal.error
async def limpeza_canal_error(ctx: commands.Context, error: Exception):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=discord.Embed(
            title="🚫 Sem Permissão!!",
            description="Você precisa da permissão **Gerenciar Mensagens** pra usar esse comando!! 🥺🦇",
            color=0xff4444,
            timestamp=datetime.utcnow()
        ), delete_after=8)


# ══════════════════════════════════════════════════════════════════
# FIM DA LIMPEZA DE CANAL
# ══════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════
# 🔄 COMANDO — CLONAR / RECRIAR CANAL (NUKE + CLONE)
# ══════════════════════════════════════════════════════════════════

@bot.command(name="clonarcanal", aliases=["nukechannel", "recriarcanal", "resetcanal"])
@commands.has_permissions(manage_channels=True)
async def clonar_canal(ctx: commands.Context):
    """
    Apaga o canal atual e recria uma cópia EXATA no mesmo lugar.
    Preserva: nome, categoria, posição, tópico, slowmode, NSFW e permissões.
    """

    canal = ctx.channel

    # Garante que é um canal de texto
    if not isinstance(canal, discord.TextChannel):
        await ctx.send(embed=discord.Embed(
            title="❌ Canal Incompatível!!",
            description="Esse comando só funciona em canais de texto!! 🥺🦇",
            color=0xff4444,
            timestamp=datetime.utcnow()
        ), delete_after=8)
        return

    # ── Confirmação ──────────────────────────────────────────────
    embed_confirm = discord.Embed(
        title="🔄 Recriar Canal — Confirmação",
        description=(
            f"Você tem certeza que quer **apagar e recriar** {canal.mention}??\n\n"
            "🧹 Todas as mensagens serão **permanentemente apagadas**!!\n"
            "✅ O canal será recriado **exatamente igual** no mesmo lugar!!\n\n"
            "⚠️ **Essa ação não pode ser desfeita!!** 🦇\n\n"
            "Responda com `sim` nos próximos **20 segundos** pra confirmar!!"
        ),
        color=0xffaa00,
        timestamp=datetime.utcnow()
    )
    embed_confirm.set_footer(text="🦇 Vampy Security • Recriar Canal")
    msg_confirm = await ctx.send(embed=embed_confirm)

    def check(m):
        return (
            m.author == ctx.author
            and m.channel == canal
            and m.content.lower() in ("sim", "não", "nao", "cancelar")
        )

    try:
        resposta = await bot.wait_for("message", timeout=20.0, check=check)
    except asyncio.TimeoutError:
        await msg_confirm.delete()
        await ctx.send(embed=discord.Embed(
            title="⏰ Tempo esgotado!!",
            description="Operação cancelada por falta de confirmação!! 🦇",
            color=0x888888,
            timestamp=datetime.utcnow()
        ), delete_after=8)
        return

    if resposta.content.lower() not in ("sim",):
        await msg_confirm.delete()
        await ctx.send(embed=discord.Embed(
            title="❌ Operação Cancelada!!",
            description="O canal **não** foi modificado!! 🦇",
            color=0xff4444,
            timestamp=datetime.utcnow()
        ), delete_after=8)
        return

    # ── Salvar todas as configurações do canal ───────────────────
    nome         = canal.name
    topico       = canal.topic
    slowmode     = canal.slowmode_delay
    nsfw         = canal.is_nsfw()
    categoria    = canal.category
    posicao      = canal.position
    overwrites   = canal.overwrites   # todas as permissões de cargos/membros
    guild        = canal.guild
    executador   = ctx.author

    # Avisa que vai começar
    await ctx.send(embed=discord.Embed(
        title="⏳ Recriando canal...",
        description="Salvei as configurações, vou apagar e recriar agora!! 🔄🦇",
        color=0xffaa00,
        timestamp=datetime.utcnow()
    ))

    await asyncio.sleep(1.5)  # pequena pausa pra mensagem ser vista

    try:
        # ── 1. Apagar o canal original ───────────────────────────
        await canal.delete(reason=f"Vampy ClonarCanal — executado por {executador}")

        # ── 2. Recriar o canal com as configs salvas ─────────────
        novo_canal = await guild.create_text_channel(
            name         = nome,
            topic        = topico,
            slowmode_delay = slowmode,
            nsfw         = nsfw,
            category     = categoria,
            overwrites   = overwrites,
            reason       = f"Vampy ClonarCanal — recriado por {executador}"
        )

        # ── 3. Ajustar a posição exata ───────────────────────────
        await novo_canal.edit(position=posicao)

        # ── 4. Enviar confirmação no novo canal ──────────────────
        embed_ok = discord.Embed(
            title="✅ Canal Recriado com Sucesso!!",
            description=(
                f"🔄 O canal foi **apagado e recriado** com a configuração original!!\n\n"
                f"📛 **Nome:** `{nome}`\n"
                f"📁 **Categoria:** `{categoria.name if categoria else 'Sem categoria'}`\n"
                f"📍 **Posição:** `{posicao}`\n"
                f"🐢 **Slowmode:** `{slowmode}s`\n"
                f"🔞 **NSFW:** `{'Sim' if nsfw else 'Não'}`\n"
                f"🔒 **Permissões:** `{len(overwrites)} cargo(s)/membro(s) copiado(s)`\n\n"
                f"👤 Executado por: {executador.mention}\n"
                f"📅 Horário (UTC): `{datetime.utcnow().strftime('%d/%m/%Y às %H:%M:%S')}`"
            ),
            color=0x00ff99,
            timestamp=datetime.utcnow()
        )
        embed_ok.set_footer(text="🦇 Vampy Security • Canal Recriado")
        await novo_canal.send(embed=embed_ok)

    except discord.Forbidden:
        # Se falhar, tenta mandar no log
        log_ch = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
        target = log_ch or guild.system_channel
        if target:
            await target.send(embed=discord.Embed(
                title="❌ Erro ao Recriar Canal!!",
                description=f"Não tenho permissão pra apagar/criar canais!! 😢🦇\nCanal original: `{nome}`",
                color=0xff4444,
                timestamp=datetime.utcnow()
            ))

    except discord.HTTPException as e:
        log_ch = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
        target = log_ch or guild.system_channel
        if target:
            await target.send(embed=discord.Embed(
                title="⚠️ Erro HTTP ao Recriar Canal!!",
                description=f"Ocorreu um erro inesperado!!\n`{e}`\n\nTenta de novo!! 🦇",
                color=0xff8800,
                timestamp=datetime.utcnow()
            ))


@clonar_canal.error
async def clonar_canal_error(ctx: commands.Context, error: Exception):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(embed=discord.Embed(
            title="🚫 Sem Permissão!!",
            description="Você precisa da permissão **Gerenciar Canais** pra usar esse comando!! 🥺🦇",
            color=0xff4444,
            timestamp=datetime.utcnow()
        ), delete_after=8)


# ══════════════════════════════════════════════════════════════════
# FIM DO CLONAR CANAL
# ══════════════════════════════════════════════════════════════════


# ╔══════════════════════════════════════════════════════════════════╗
# ║          🎵 SPOTYVAMPY — SISTEMA DE MÚSICA v2.0             ║
# ║   Powered by Lavalink + Wavelink — Sem bot-detection do YT!    ║
# ╚══════════════════════════════════════════════════════════════════╝

import wavelink  # pip install wavelink

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ⚙️  CONFIGURAÇÕES DO PLAYER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SV_COR_PRIMARIA  = 0x1db954   # verde spotify
SV_COR_ERRO      = 0xff4444
SV_COR_AVISO     = 0xffaa00
SV_VOLUME_PADRAO = 50         # 50% (escala 0-100)
SV_FILA_MAX      = 50         # máximo de músicas na fila

LAVALINK_URI      = os.getenv("LAVALINK_URI",      "http://lavalink:2333")
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD", "vampypassword")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎮  VIEW — CONTROLES DE MÚSICA (botões)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class MusicControlView(discord.ui.View):
    """Painel de botões de controle do Spotyvampy."""

    def __init__(self, cog: "SpotyvampyCog", guild_id: int):
        super().__init__(timeout=120)
        self.cog      = cog
        self.guild_id = guild_id

    def _player(self) -> wavelink.Player | None:
        guild = self.cog.bot.get_guild(self.guild_id)
        return guild.voice_client if guild else None

    @discord.ui.button(emoji="⏸️", label="Pausar", style=discord.ButtonStyle.secondary, row=0)
    async def btn_pausar(self, interaction: discord.Interaction, button: discord.ui.Button):
        p = self._player()
        if not p or not p.connected:
            return await interaction.response.send_message("❌ Não há nada tocando!!", ephemeral=True)
        if p.paused:
            await p.pause(False)
            button.label = "Pausar"; button.emoji = "⏸️"
        else:
            await p.pause(True)
            button.label = "Continuar"; button.emoji = "▶️"
        await interaction.response.edit_message(view=self)

    @discord.ui.button(emoji="⏭️", label="Pular", style=discord.ButtonStyle.primary, row=0)
    async def btn_pular(self, interaction: discord.Interaction, button: discord.ui.Button):
        p = self._player()
        if not p or not p.playing:
            return await interaction.response.send_message("❌ Não há nada tocando!!", ephemeral=True)
        await p.skip(force=True)
        await interaction.response.send_message(embed=discord.Embed(
            description="⏭️ Pulei a música!! 🦇", color=SV_COR_PRIMARIA), ephemeral=True)

    @discord.ui.button(emoji="⏹️", label="Parar", style=discord.ButtonStyle.danger, row=0)
    async def btn_parar(self, interaction: discord.Interaction, button: discord.ui.Button):
        p = self._player()
        if not p:
            return await interaction.response.send_message("❌ Não há nada tocando!!", ephemeral=True)
        p.queue.clear()
        p.queue.mode = wavelink.QueueMode.normal
        await p.stop()
        await interaction.response.send_message(embed=discord.Embed(
            description="⏹️ Música parada e fila limpa!! 🦇", color=SV_COR_ERRO), ephemeral=True)

    @discord.ui.button(emoji="🔁", label="Loop", style=discord.ButtonStyle.secondary, row=0)
    async def btn_loop(self, interaction: discord.Interaction, button: discord.ui.Button):
        p = self._player()
        if not p:
            return await interaction.response.send_message("❌ Não há player ativo!!", ephemeral=True)
        if p.queue.mode == wavelink.QueueMode.loop:
            p.queue.mode = wavelink.QueueMode.normal
            status = "❌ desativado"
        else:
            p.queue.mode = wavelink.QueueMode.loop
            status = "✅ ativado (música)"
        await interaction.response.send_message(embed=discord.Embed(
            description=f"🔁 Loop {status}!! 🦇", color=SV_COR_PRIMARIA), ephemeral=True)

    @discord.ui.button(emoji="📋", label="Fila", style=discord.ButtonStyle.secondary, row=1)
    async def btn_fila(self, interaction: discord.Interaction, button: discord.ui.Button):
        p = self._player()
        embed = self.cog._embed_fila(p)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(emoji="🔀", label="Embaralhar", style=discord.ButtonStyle.secondary, row=1)
    async def btn_shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):
        p = self._player()
        if not p or not p.queue:
            return await interaction.response.send_message("❌ A fila está vazia!!", ephemeral=True)
        p.queue.shuffle()
        await interaction.response.send_message(embed=discord.Embed(
            description=f"🔀 Fila embaralhada com `{len(p.queue)}` músicas!! 🦇", color=SV_COR_PRIMARIA), ephemeral=True)

    @discord.ui.button(emoji="🎵", label="Tocando Agora", style=discord.ButtonStyle.primary, row=1)
    async def btn_nowplaying(self, interaction: discord.Interaction, button: discord.ui.Button):
        p = self._player()
        if not p or not p.current:
            return await interaction.response.send_message("❌ Nada tocando agora!!", ephemeral=True)
        embed = self.cog._embed_nowplaying(p.current, p)
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🦇  COG — SPOTYVAMPY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class SpotyvampyCog(commands.Cog, name="SpotyvampyCog"):
    """🎵 SPOTYVAMPY — Sistema de Música v2.0 powered by Lavalink 🦇"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ── Helpers ──────────────────────────────────

    def _fmt_duration(self, ms: int) -> str:
        if not ms:
            return "∞"
        s = ms // 1000
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    def _embed_nowplaying(self, track: wavelink.Playable, player: wavelink.Player) -> discord.Embed:
        requester = getattr(track.extras, "requester", None)
        embed = discord.Embed(
            title="🎵 Tocando Agora",
            description=f"**[{track.title}]({track.uri})**",
            color=SV_COR_PRIMARIA,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="⏱️ Duração",    value=f"`{self._fmt_duration(track.length)}`",  inline=True)
        embed.add_field(name="🎤 Artista",    value=f"`{track.author}`",                       inline=True)
        embed.add_field(name="👤 Pedido por", value=requester.mention if requester else "—",   inline=True)
        loop_status = {"loop": "🔂 Música", "loop_all": "🔁 Fila", "normal": "❌ Off"}.get(player.queue.mode.name, "❌ Off")
        embed.add_field(name="🔁 Loop",    value=loop_status,                              inline=True)
        embed.add_field(name="🔊 Volume",  value=f"`{player.volume}%`",                    inline=True)
        embed.add_field(name="📋 Na fila", value=f"`{len(player.queue)}` músicas",         inline=True)
        if track.artwork:
            embed.set_thumbnail(url=track.artwork)
        embed.set_footer(text="🦇 Spotyvampy • Powered by Lavalink • Feito com muito amor!!")
        return embed

    def _embed_fila(self, player: wavelink.Player | None) -> discord.Embed:
        embed = discord.Embed(title="📋 Fila de Músicas — Spotyvampy", color=SV_COR_PRIMARIA, timestamp=datetime.utcnow())
        if not player or (not player.current and not player.queue):
            embed.description = "😴 A fila está vazia!! Use `v!play` pra adicionar músicas!! 🦇"
            return embed
        if player.current:
            embed.add_field(
                name="🎵 Tocando Agora",
                value=f"**{player.current.title}** `{self._fmt_duration(player.current.length)}`",
                inline=False
            )
        if player.queue:
            linhas = []
            for i, t in enumerate(list(player.queue)[:10], 1):
                linhas.append(f"`{i}.` **{t.title}** `{self._fmt_duration(t.length)}`")
            if len(player.queue) > 10:
                linhas.append(f"... e mais `{len(player.queue) - 10}` músicas")
            embed.add_field(name=f"📋 Próximas ({len(player.queue)})", value="\n".join(linhas), inline=False)
        else:
            embed.add_field(name="📋 Fila", value="Sem próximas músicas na fila!!", inline=False)
        embed.set_footer(text="🦇 Spotyvampy • Feito com muito amor!!")
        return embed

    async def _get_or_create_player(self, ctx: commands.Context) -> wavelink.Player | None:
        """Garante que o bot está na call e retorna o player."""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send(embed=discord.Embed(
                description="❌ Você precisa estar em um canal de voz pra usar o Spotyvampy!! 🦇",
                color=SV_COR_ERRO))
            return None

        player: wavelink.Player | None = ctx.guild.voice_client

        if player and player.connected:
            # Já conectado — só atualiza text_channel
            player.text_channel = ctx.channel
            return player

        # Conectar no canal do usuário
        try:
            player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
            player.text_channel = ctx.channel
            player.autoplay = wavelink.AutoPlayMode.disabled  # CRÍTICO: desativa autoplay interno
            player.inactive_timeout = None                    # sem timeout automático
            await player.set_volume(SV_VOLUME_PADRAO)
            return player
        except Exception as e:
            print(f"[Spotyvampy] Erro ao conectar: {e}")
            await ctx.send(embed=discord.Embed(
                description="❌ Não consegui entrar na call!! 😢🦇", color=SV_COR_ERRO))
            return None

    # ── 🟢 Boot ───────────────────────────────────

    @commands.Cog.listener()
    async def on_ready(self):
        await asyncio.sleep(5)
        # Conectar ao Lavalink
        try:
            nodes = [wavelink.Node(uri=LAVALINK_URI, password=LAVALINK_PASSWORD)]
            await wavelink.Pool.connect(nodes=nodes, client=self.bot, cache_capacity=100)
            print(f"[Spotyvampy] ✅ Conectado ao Lavalink em {LAVALINK_URI}")
        except Exception as e:
            print(f"[Spotyvampy] ❌ Erro ao conectar ao Lavalink: {e}")

        await asyncio.sleep(3)
        for guild in self.bot.guilds:
            log_ch = discord.utils.get(guild.text_channels, name=LOG_CHANNEL_NAME)
            if not log_ch:
                continue
            embed = discord.Embed(
                title="🎵 Spotyvampy Online!!",
                description=(
                    "```\n"
                    "╔══════════════════════════════════════╗\n"
                    "║   SPOTYVAMPY  🦇  v2.0           ║\n"
                    "║    — Powered by Lavalink —          ║\n"
                    "║       ✅  ONLINE  ✅                 ║\n"
                    "╚══════════════════════════════════════╝\n"
                    "```"
                ),
                color=SV_COR_PRIMARIA,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="🎵 Comandos",
                            value="`v!play` `v!pular` `v!parar` `v!fila` `v!tocando` `v!volume` `v!loop` `v!embaralhar` `v!sair`",
                            inline=False)
            embed.add_field(name="🎧 Fontes Suportadas",
                            value="YouTube • Spotify • SoundCloud • Bandcamp • Vimeo • Radio",
                            inline=False)
            embed.add_field(name="📖 Ajuda Completa", value="`v!sv` ou `v!spotyvampy`", inline=False)
            embed.set_footer(text="🦇 Spotyvampy v2.0 • Música com muito amor!!")
            await log_ch.send(embed=embed)

    # ── 🎵 Eventos Wavelink ───────────────────────

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        player: wavelink.Player = payload.player
        track  = payload.track
        ch     = getattr(player, "text_channel", None)
        if not ch:
            return
        embed = self._embed_nowplaying(track, player)
        view  = MusicControlView(self, player.guild.id)
        try:
            await ch.send(embed=embed, view=view)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        player: wavelink.Player = payload.player
        reason = payload.reason

        # Loop de música única — re-toca a mesma
        if player.queue.mode == wavelink.QueueMode.loop and payload.track:
            await player.play(payload.track)
            return

        # Loop de fila — coloca a música no fim e pega a próxima
        if player.queue.mode == wavelink.QueueMode.loop_all and payload.track:
            player.queue.put(payload.track)

        if player.queue:
            next_track = player.queue.get()
            await player.play(next_track)
        elif reason == "finished":
            ch = getattr(player, "text_channel", None)
            if ch:
                try:
                    await ch.send(embed=discord.Embed(
                        description="📭 A fila acabou!! Obrigada por usar o Spotyvampy!! 🦇💚",
                        color=SV_COR_PRIMARIA))
                except Exception:
                    pass

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        print(f"[Spotyvampy] Lavalink node pronto: {payload.node.uri} | Sessão: {payload.session_id}")

    # ── 🎵 COMANDOS ───────────────────────────────

    @commands.command(name="play", aliases=["tocar", "p"])
    async def play(self, ctx: commands.Context, *, query: str):
        """Toca música ou playlist do YouTube/Spotify/SoundCloud. Uso: v!play <nome ou URL>"""
        async with ctx.typing():
            player = await self._get_or_create_player(ctx)
            if not player:
                return

            msg_busca = await ctx.send(embed=discord.Embed(
                description=f"🔎 Buscando: **{query}**... 🦇", color=SV_COR_AVISO))

            try:
                # ── Detectar fonte correta ──────────────────────────────
                # URL Spotify  → passa direto (LavaSrc resolve via "sp:" prefix)
                # Busca texto  → YouTube Music (sem bot-detection do YouTube)
                # Outra URL    → passa direto (YouTube, SoundCloud, etc.)
                q_lower = query.lower()
                is_url = q_lower.startswith("http://") or q_lower.startswith("https://")

                if is_url and "spotify.com" in q_lower:
                    # URL Spotify — LavaSrc converte automaticamente
                    tracks = await wavelink.Playable.search(query)
                elif is_url:
                    # URL do YouTube, SoundCloud, etc. — passa direto
                    tracks = await wavelink.Playable.search(query)
                else:
                    # Busca por nome — usa YouTube Music (sem bot-detection)
                    tracks = await wavelink.Playable.search(query, source=wavelink.TrackSource.YouTubeMusic)

            except Exception as e:
                print(f"[Spotyvampy] Erro ao buscar '{query}': {e}")
                return await msg_busca.edit(embed=discord.Embed(
                    description="❌ Erro ao buscar no Lavalink!! 😢🦇", color=SV_COR_ERRO))

            if not tracks:
                return await msg_busca.edit(embed=discord.Embed(
                    description="❌ Não encontrei nada com essa busca!! 😢🦇", color=SV_COR_ERRO))

            adicionadas = 0
            ja_tocando_antes = player.playing

            if isinstance(tracks, wavelink.Playlist):
                # Playlist inteira
                for t in tracks:
                    t.extras = wavelink.ExtrasNamespace({"requester": ctx.author})
                    if len(player.queue) < SV_FILA_MAX:
                        player.queue.put(t)   # síncrono — evita race condition
                        adicionadas += 1
                await msg_busca.edit(embed=discord.Embed(
                    description=f"📋 Playlist **{tracks.name}** adicionada com **{adicionadas}** músicas!! 🦇",
                    color=SV_COR_PRIMARIA))
            else:
                # Música única
                track = tracks[0]
                track.extras = wavelink.ExtrasNamespace({"requester": ctx.author})
                if len(player.queue) >= SV_FILA_MAX:
                    return await msg_busca.edit(embed=discord.Embed(
                        description=f"❌ A fila está cheia!! Máximo de **{SV_FILA_MAX}** músicas!! 🦇",
                        color=SV_COR_ERRO))
                player.queue.put(track)  # síncrono — evita race condition
                adicionadas = 1
                if ja_tocando_antes:
                    await msg_busca.edit(embed=discord.Embed(
                        description=f"📋 **{track.title}** adicionada à fila!! 🦇",
                        color=SV_COR_PRIMARIA))
                else:
                    await msg_busca.delete()

            # Iniciar reprodução se não estava tocando antes
            if not ja_tocando_antes:
                next_track = player.queue.get()
                await player.play(next_track)

    @commands.command(name="pausar", aliases=["pause"])
    async def pausar(self, ctx: commands.Context):
        """Pausa ou continua a música. Uso: v!pausar"""
        player: wavelink.Player | None = ctx.guild.voice_client
        if not player or not player.connected:
            return await ctx.send(embed=discord.Embed(description="❌ Não estou em nenhuma call!! 🦇", color=SV_COR_ERRO))
        if player.paused:
            await player.pause(False)
            desc = "▶️ Música continuada!! 🦇"
        else:
            await player.pause(True)
            desc = "⏸️ Música pausada!! 🦇"
        await ctx.send(embed=discord.Embed(description=desc, color=SV_COR_PRIMARIA), delete_after=8)

    @commands.command(name="continuar", aliases=["resume", "r"])
    async def continuar(self, ctx: commands.Context):
        """Continua a música se estiver pausada. Uso: v!continuar"""
        player: wavelink.Player | None = ctx.guild.voice_client
        if not player or not player.paused:
            return await ctx.send(embed=discord.Embed(description="❌ A música não está pausada!! 🦇", color=SV_COR_ERRO))
        await player.pause(False)
        await ctx.send(embed=discord.Embed(description="▶️ Música continuada!! 🦇", color=SV_COR_PRIMARIA), delete_after=8)

    @commands.command(name="pular", aliases=["skip", "s"])
    async def pular(self, ctx: commands.Context):
        """Pula para a próxima música. Uso: v!pular"""
        player: wavelink.Player | None = ctx.guild.voice_client
        if not player or not player.playing:
            return await ctx.send(embed=discord.Embed(description="❌ Não há nada tocando!! 🦇", color=SV_COR_ERRO))
        await player.skip(force=True)
        await ctx.send(embed=discord.Embed(
            description=f"⏭️ Pulei!! 🦇 — pedido por {ctx.author.mention}",
            color=SV_COR_PRIMARIA), delete_after=8)

    @commands.command(name="parar", aliases=["stop"])
    async def parar(self, ctx: commands.Context):
        """Para a música e limpa a fila. Uso: v!parar"""
        player: wavelink.Player | None = ctx.guild.voice_client
        if not player:
            return await ctx.send(embed=discord.Embed(description="❌ Não estou em nenhuma call!! 🦇", color=SV_COR_ERRO))
        player.queue.clear()
        player.queue.mode = wavelink.QueueMode.normal
        await player.stop()
        await ctx.send(embed=discord.Embed(
            description=f"⏹️ Música parada e fila limpa por {ctx.author.mention}!! 🦇",
            color=SV_COR_ERRO))

    @commands.command(name="fila", aliases=["queue", "q"])
    async def fila(self, ctx: commands.Context):
        """Mostra a fila de músicas. Uso: v!fila"""
        player: wavelink.Player | None = ctx.guild.voice_client
        embed = self._embed_fila(player)
        await ctx.send(embed=embed)

    @commands.command(name="tocando", aliases=["nowplaying", "np"])
    async def tocando(self, ctx: commands.Context):
        """Mostra a música tocando agora. Uso: v!tocando"""
        player: wavelink.Player | None = ctx.guild.voice_client
        if not player or not player.current:
            return await ctx.send(embed=discord.Embed(description="❌ Nada tocando agora!! 🦇", color=SV_COR_ERRO))
        embed = self._embed_nowplaying(player.current, player)
        view  = MusicControlView(self, ctx.guild.id)
        await ctx.send(embed=embed, view=view)

    @commands.command(name="volume", aliases=["vol"])
    async def volume(self, ctx: commands.Context, vol: int):
        """Ajusta o volume (1-100). Uso: v!volume 80"""
        if not 1 <= vol <= 100:
            return await ctx.send(embed=discord.Embed(
                description="❌ Volume deve ser entre **1** e **100**!! 🦇", color=SV_COR_ERRO))
        player: wavelink.Player | None = ctx.guild.voice_client
        if not player:
            return await ctx.send(embed=discord.Embed(description="❌ Não há player ativo!! 🦇", color=SV_COR_ERRO))
        await player.set_volume(vol)
        await ctx.send(embed=discord.Embed(
            description=f"🔊 Volume ajustado para **{vol}%** por {ctx.author.mention}!! 🦇",
            color=SV_COR_PRIMARIA), delete_after=8)

    @commands.command(name="loop")
    async def loop(self, ctx: commands.Context, modo: str = "musica"):
        """Ativa loop. Modos: musica | fila | off. Uso: v!loop fila"""
        player: wavelink.Player | None = ctx.guild.voice_client
        if not player:
            return await ctx.send(embed=discord.Embed(description="❌ Não há player ativo!! 🦇", color=SV_COR_ERRO))
        modo = modo.lower()
        if modo in ("off", "desligar", "0"):
            player.queue.mode = wavelink.QueueMode.normal
            desc = "🔁 Loop **desativado**!! 🦇"
        elif modo in ("fila", "queue", "all"):
            player.queue.mode = wavelink.QueueMode.loop_all
            desc = "🔁 Loop de **fila** ativado!! 🦇"
        else:
            player.queue.mode = wavelink.QueueMode.loop
            desc = "🔂 Loop de **música** ativado!! 🦇"
        await ctx.send(embed=discord.Embed(description=desc, color=SV_COR_PRIMARIA), delete_after=10)

    @commands.command(name="embaralhar", aliases=["shuffle"])
    async def embaralhar(self, ctx: commands.Context):
        """Embaralha a fila. Uso: v!embaralhar"""
        player: wavelink.Player | None = ctx.guild.voice_client
        if not player or not player.queue:
            return await ctx.send(embed=discord.Embed(description="❌ A fila está vazia!! 🦇", color=SV_COR_ERRO))
        player.queue.shuffle()
        await ctx.send(embed=discord.Embed(
            description=f"🔀 Fila embaralhada com **{len(player.queue)}** músicas por {ctx.author.mention}!! 🦇",
            color=SV_COR_PRIMARIA), delete_after=8)

    @commands.command(name="remover", aliases=["remove", "rm"])
    async def remover(self, ctx: commands.Context, pos: int):
        """Remove uma música da fila pela posição. Uso: v!remover 3"""
        player: wavelink.Player | None = ctx.guild.voice_client
        if not player or not player.queue:
            return await ctx.send(embed=discord.Embed(description="❌ A fila está vazia!! 🦇", color=SV_COR_ERRO))
        fila = list(player.queue)
        if not 1 <= pos <= len(fila):
            return await ctx.send(embed=discord.Embed(
                description=f"❌ Posição inválida!! A fila tem **{len(fila)}** músicas!! 🦇", color=SV_COR_ERRO))
        removida = fila.pop(pos - 1)
        player.queue.clear()
        for t in fila:
            player.queue.put(t)
        await ctx.send(embed=discord.Embed(
            description=f"🗑️ **{removida.title}** removida da fila por {ctx.author.mention}!! 🦇",
            color=SV_COR_PRIMARIA), delete_after=8)

    @commands.command(name="limparfila", aliases=["clearqueue", "cq"])
    async def limparfila(self, ctx: commands.Context):
        """Limpa a fila sem parar a música atual. Uso: v!limparfila"""
        player: wavelink.Player | None = ctx.guild.voice_client
        if not player or not player.queue:
            return await ctx.send(embed=discord.Embed(description="❌ A fila já está vazia!! 🦇", color=SV_COR_ERRO))
        qtd = len(player.queue)
        player.queue.clear()
        await ctx.send(embed=discord.Embed(
            description=f"🧹 **{qtd}** músicas removidas da fila por {ctx.author.mention}!! 🦇",
            color=SV_COR_PRIMARIA), delete_after=8)

    @commands.command(name="sair", aliases=["dc", "disconnect", "desconectar"])
    async def sair(self, ctx: commands.Context):
        """Desconecta o bot do canal de voz. Uso: v!sair"""
        player: wavelink.Player | None = ctx.guild.voice_client
        if not player or not player.connected:
            return await ctx.send(embed=discord.Embed(description="❌ Não estou em nenhum canal de voz!! 🦇", color=SV_COR_ERRO))
        player.queue.clear()
        await player.disconnect()
        await ctx.send(embed=discord.Embed(
            description=f"👋 Saí do canal de voz!! Tchau tchau, {ctx.author.mention}!! 🦇💚",
            color=SV_COR_PRIMARIA))

    @commands.command(name="spotyvampy", aliases=["sv", "musicahelp", "mhelp"])
    async def spotyvampy_help(self, ctx: commands.Context):
        """Mostra todos os comandos do Spotyvampy. Uso: v!sv"""
        embed = discord.Embed(
            title="🎵 Spotyvampy — Comandos de Música",
            description=(
                "```\n"
                "╔══════════════════════════════════════╗\n"
                "║   SPOTYVAMPY  🦇  v2.0           ║\n"
                "║    — Powered by Lavalink! —         ║\n"
                "╚══════════════════════════════════════╝\n"
                "```"
            ),
            color=SV_COR_PRIMARIA,
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="▶️  Tocar",       value="`v!play <nome/URL>` `v!p` `v!tocar`\nYouTube, Spotify, SoundCloud, Radio...", inline=False)
        embed.add_field(name="⏸️  Pausar",      value="`v!pausar` `v!pause`",        inline=True)
        embed.add_field(name="▶️  Continuar",   value="`v!continuar` `v!resume`",    inline=True)
        embed.add_field(name="⏭️  Pular",       value="`v!pular` `v!skip`",          inline=True)
        embed.add_field(name="⏹️  Parar",       value="`v!parar` `v!stop`",          inline=True)
        embed.add_field(name="📋  Fila",        value="`v!fila` `v!queue`",          inline=True)
        embed.add_field(name="🎵  Tocando",     value="`v!tocando` `v!np`",          inline=True)
        embed.add_field(name="🔊  Volume",      value="`v!volume <1-100>`",          inline=True)
        embed.add_field(name="🔁  Loop",        value="`v!loop musica/fila/off`",    inline=True)
        embed.add_field(name="🔀  Embaralhar",  value="`v!embaralhar` `v!shuffle`",  inline=True)
        embed.add_field(name="🗑️  Remover",     value="`v!remover <pos>`",           inline=True)
        embed.add_field(name="🧹  Limpar Fila", value="`v!limparfila` `v!cq`",       inline=True)
        embed.add_field(name="👋  Sair",        value="`v!sair` `v!dc`",             inline=True)
        embed.add_field(
            name="🎧 Fontes Suportadas",
            value="YouTube • **Spotify** • SoundCloud • Bandcamp • Vimeo • Rádio Online",
            inline=False
        )
        embed.set_footer(text="🦇 Spotyvampy v2.0 • Powered by Lavalink • Use v!sv pra ver esse menu")
        view = MusicControlView(self, ctx.guild.id)
        await ctx.send(embed=embed, view=view)

    # ── Auto-desconectar se canal vazio ──────────

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return
        guild  = member.guild
        player: wavelink.Player | None = guild.voice_client
        if not player or not player.connected:
            return
        vc_channel = player.channel
        if vc_channel and len([m for m in vc_channel.members if not m.bot]) == 0:
            await asyncio.sleep(60)
            player = guild.voice_client
            if player and player.connected:
                if len([m for m in player.channel.members if not m.bot]) == 0:
                    player.queue.clear()
                    await player.disconnect()
                    ch = getattr(player, "text_channel", None)
                    if ch:
                        try:
                            await ch.send(embed=discord.Embed(
                                description="👋 Saí do canal de voz por inatividade!! 🦇💚",
                                color=SV_COR_AVISO))
                        except Exception:
                            pass




async def _main():
    async with bot:
        await bot.add_cog(VampyCog(bot))
        await bot.add_cog(VoiceMasterCog(bot))
        await bot.add_cog(BanAppealCog(bot))
        await bot.add_cog(SpotyvampyCog(bot))
        bot.add_view(BanirMembroView())          # intercepta botões existentes no Discord
        bot.loop.create_task(_setup_linha_indireta())
        await bot.start(TOKEN)

_asyncio.run(_main())
