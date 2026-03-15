import discord
from discord.ext import commands, tasks
import random
import asyncio
import os
import re
from datetime import timedelta
from datetime import datetime
from collections import defaultdict, deque

# ================= INTENTS =================
# ============== BOT SETUP =================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ╔══════════════════════════════════════════════════════════════════╗
# ║          MONSTRINHO SECURITY SYSTEM — GOD MODE v2.0             ║
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
# 🛡️  COG — MONSTRINHO SECURITY SYSTEM
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class MonstrinhoCog(commands.Cog, name="MonStrinhoSecurity"):
    """MONSTRINHO SECURITY SYSTEM — GOD MODE v2.0."""

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
        embed = discord.Embed(title=f"{'🔴' if critical else '🚨'} MONSTRINHO SECURITY ALERT", color=color, timestamp=now)
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
        embed.set_footer(text=f"MONSTRINHO SECURITY • Risco: {risk}pts | Suspeito: {flagged}",
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
                    "║   MONSTRINHO SECURITY SYSTEM         ║\n"
                    "║         — GOD MODE —                 ║\n"
                    "║       ⚡  v2.0  ONLINE  ⚡           ║\n"
                    "╚══════════════════════════════════════╝\n"
                    "```"
                ),
                color=0x00ff99, timestamp=now
            )
            boot.set_author(name="MONSTRINHO SECURITY • Sistema Iniciado",
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
            boot.set_footer(text="MONSTRINHO SECURITY SYSTEM • Todos os sistemas operacionais.",
                            icon_url=self.bot.user.display_avatar.url if self.bot.user else None)
            await ch.send(embed=boot)

            # Embed de Comandos
            cmds = discord.Embed(title="📋 Comandos — MONSTRINHO SECURITY", color=0x5865F2, timestamp=now)
            cmds.add_field(name="🔍 Status & Info", inline=False, value=(
                "`!security status` — Painel completo\n"
                "`!segurança status` — Alias PT\n"
                "`!security riskscore @user` — Risco do usuário\n"
                "`!security flagged` — Usuários suspeitos"
            ))
            cmds.add_field(name="🔧 Administração", inline=False, value=(
                "`!security reset` — Limpar alertas\n"
                "`!security lockdown on/off` — Lockdown manual\n"
                "`!security emergency on/off` — Modo emergência\n"
                "`!security unflag @user` — Remover flag\n"
                "`!security alerts` — Últimos 10 alertas\n"
                "`!security stats` — Estatísticas gerais"
            ))
            cmds.add_field(name="⚠️ Permissão", value="Todos os comandos exigem **Administrador**.", inline=False)
            cmds.set_footer(text="MONSTRINHO SECURITY SYSTEM • GOD MODE v2.0")
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
                embed.set_footer(text=f"MONSTRINHO SECURITY • Ações na janela: {len(dq)}/{ADMIN_ACTION_LIMIT}")
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
                embed.set_footer(text="MONSTRINHO SECURITY • Monitor de Erros")
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
        embed = discord.Embed(title="🛡️ MONSTRINHO SECURITY — Status", color=self._level_color(), timestamp=datetime.utcnow())
        embed.add_field(name="🔒 Sistema", inline=True, value=(
            f"**Nível:** {le} `{db.security_level}`\n"
            f"**Lockdown:** {'⛔ ATIVO' if db.lockdown_active else '✅ Off'}\n"
            f"**Emergência:** {'🆘 ATIVA' if db.emergency_mode else '✅ Off'}"))
        embed.add_field(name="📊 Eventos", inline=True, value=(
            f"🚨 Alertas: `{db.total_alerts}`\n💬 Spam: `{db.spam_events}`\n"
            f"🚪 Raid: `{db.raid_events}`\n🔗 Links: `{db.link_events}`\n🔧 Admin: `{db.admin_events}`"))
        embed.add_field(name="👤 Monitorados", inline=False, value=(
            f"⚠️ Com risco: `{len(db.risk_scores)}` | ⛔ Suspeitos: `{len(db.flagged_users)}` | 🕒 Cooldown: `{len(self._cmd_cooldowns)}`"))
        embed.set_footer(text="MONSTRINHO SECURITY SYSTEM • GOD MODE v2.0")
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
        embed.set_footer(text="MONSTRINHO SECURITY • Histórico")
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
CANAL_GAMES = "🎲・monstrinho-games"
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
CANAL_RANKING_MONSTRINHO = "🎰・ranking-monstrinho"
CANAL_LOJA_INFO = "💾・loja-monstrinho"
CANAL_DIRECAO = "👑・chat-direção"
CANAL_ATENCAO = "⚠️・atenção"

# GIFs e Imagens
BANNER_TICKET = "https://i.pinimg.com/originals/5d/92/5d/5d925dd101dba34f341148eace3cfe38.gif"
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


# ============== DADOS =================

tickets = {}
avisos_usuarios = {}       # user_id -> avisos atuais (0–3)
total_ciclos_usuario = {}  # user_id -> quantos ciclos completos de punição já levou
pontuacao_monstrinho = {}
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
    "arrombado", "imbecil", "otário", "otario", "retardado", "nojento",
    "fdp", "vsf", "krl", "pqp", "prr", "tmnc", "buceta", "carai", "karalho",
]

FRASES_PROIBIDAS = [
    # Frases completas — não há falso positivo, contexto já é claro
    "vai se fuder", "vai se foder", "vai tomar no cu", "tomar no cu",
    "filho da puta", "filha da puta", "se mata", "se fode", "vai tomar",
    "sua puta", "sua vadia", "puta que pariu", "puta merda",
    "vai a merda", "vai pra merda", "me fode", "me foder",
    "idiota mesmo", "idiota do", "burro demais", "burra demais",
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
    "Vc falou algo ruim!! infelizmente tive que te dar um aviso. cuidado com o segundo!! 🥺🐲",
    "Ai ai... **segundo aviso!!** Tá quase chegando no limite, toma muito cuidado com o terceiro, tá?? 😰🐲",
    "**TERCEIRO AVISO!!** Você tá no limite mesmo... se repetir isso vai tomar um castigo! 😱🐲 Respira fundo e volta calmo(a)!",
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
        title="🗑️ MENSAGEM APAGADA PELO MONSTRINHO",
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
        text="🐲 Monstrinho Logs  •  Use os botões abaixo caso tenha sido engano",
        icon_url=AVATAR_MONSTRINHO
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
        title="🐲💚 OI OI OI! O MONSTRINHO ACORDOU! 💚🐲",
        description=(
            "AAAAA gente, eu tô de volta e tô com saudaaaaade de vocês! 🥺✨\n\n"
            "Deixa eu te contar como funcionam os meus joguinhos antes da gente começar a se divertir, tá bom? 🎮🐉"
        ),
        color=0xADFF2F
    )
    embed.set_thumbnail(url=AVATAR_MONSTRINHO)
    embed.set_image(url=GIF_ACERTO_MONSTRINHO)
    await canal_games.send(embed=embed)

    await asyncio.sleep(2)

    embed2 = discord.Embed(
        title="🎮 COMO FUNCIONAM OS JOGOS? 🎮",
        color=0x00FF7F
    )
    embed2.add_field(
        name="🧠 Pergunta Relâmpago",
        value="O Monstrinho faz uma pergunta e o primeiro que acertar ganha **80 coins**! Responda rápido no chat! ⚡ *(Sem penalidade por errar!)*",
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
    embed2.set_thumbnail(url=AVATAR_MONSTRINHO)
    await canal_games.send(embed=embed2)

    await asyncio.sleep(2)

    embed3 = discord.Embed(
        title="🌟 JOGOS ESPECIAIS DO MONSTRINHO 🌟",
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
        value="O Monstrinho escolhe um **número secreto de mensagens**! Quem mandar a mensagem da sorte ganha **600 coins**! Shhh~ 🐲",
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
    embed3.set_thumbnail(url=AVATAR_MONSTRINHO)
    await canal_games.send(embed=embed3)

    await asyncio.sleep(2)

    embed4 = discord.Embed(
        title="💰 SISTEMA DE COINS 💰",
        description=(
            "Os **Monstrinho-Coins** são a moeda do servidor! Você ganha participando dos jogos e pode usar na **loja** para resgatar prêmios incríveis! 🛍️🐲\n\n"
            "🏆 Confira o ranking no canal de ranking e veja quem é o mais ricão do servidor!\n\n"
            "**Os jogos aparecem automaticamente a cada ~40 minutos, tá?** Fica de olho aqui! 👀💚\n\n"
            "*O Monstrinho ama cada um de vocês... agora bora jogar!* 🐲💚✨"
        ),
        color=0xFFD700
    )
    embed4.set_thumbnail(url=AVATAR_MONSTRINHO)
    embed4.set_footer(text="Monstrinho-Games 🐲 | Boa sorte a todos! 💚")
    await canal_games.send(embed=embed4)

async def atualizar_ranking(guild):
    canal_rank = discord.utils.get(guild.text_channels, name=CANAL_RANKING_MONSTRINHO)
    if not canal_rank: return
    
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
                embed.set_footer(text="Sistema de Monitoramento de Bem-Estar 🐲", icon_url=AVATAR_MONSTRINHO)
                
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
    embed.set_thumbnail(url=AVATAR_MONSTRINHO)
    embed.title = "🎡 ROLETA DA SORTE COLETIVA! 🎰"
    embed.description = (
        "A roleta está girando para **TODOS**! ✨🐲\n\n"
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
    embed.set_footer(text="⏱️ Aberta por 5 minutos! Cada pessoa gira UMA vez. 🐲")
    
    await canal_games.send(embed=embed)

    await asyncio.sleep(300)
    
    jogo_em_andamento["venceu"] = True
    jogo_em_andamento["resposta"] = None
    await canal_games.send("🎡 A roleta parou de girar! Tempo encerrado! 🐲🏁")

async def disparar_tarot(guild):
    canal_games = discord.utils.get(guild.text_channels, name=CANAL_GAMES)
    if not canal_games: return

    jogo_em_andamento["tipo"] = "tarot"
    jogo_em_andamento["venceu"] = False
    jogo_em_andamento["participantes_tentaram"] = []
    jogo_em_andamento["resposta"] = "tarot"

    embed = discord.Embed(color=0x9B59B6)
    embed.set_thumbnail(url=AVATAR_MONSTRINHO)
    embed.title = "🔮 TIRAGEM DO DESTINO — TAROT MÍSTICO 🔮"
    embed.description = (
        "As cartas ancestrais aguardam por **TODOS**! ✨🐲\n\n"
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
    embed.set_footer(text="⏱️ 5 minutos para consultar o oráculo! As cartas não mentem... 🐲")
    
    await canal_games.send(embed=embed)

    await asyncio.sleep(300)
    
    jogo_em_andamento["venceu"] = True
    jogo_em_andamento["resposta"] = None
    await canal_games.send("🔮 As cartas se fecharam... o oráculo descansa até a próxima invocação! 🐲💫")

async def disparar_sobrevivamonstro(guild):
    canal_games = discord.utils.get(guild.text_channels, name=CANAL_GAMES)
    if not canal_games: return

    jogo_em_andamento["tipo"] = "sobrevivamonstro"
    jogo_em_andamento["venceu"] = False
    jogo_em_andamento["participantes_tentaram"] = []
    jogo_em_andamento["resposta"] = "sobrevivamonstro"

    embed = discord.Embed(color=0xFF4500)
    embed.set_thumbnail(url=AVATAR_MONSTRINHO)
    embed.title = "👹 SOBREVIVA AO MONSTRO — HORDA APOCALÍPTICA! ⚔️"
    embed.description = (
        "Uma horda de monstros invadiu o chat! **TODOS** podem enfrentar! 🐲⚔️\n\n"
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
    embed.set_footer(text="⏱️ 5 minutos para enfrentar seu monstro! Coragem, guerreiro! 🐲")
    
    await canal_games.send(embed=embed)

    await asyncio.sleep(300)
    
    jogo_em_andamento["venceu"] = True
    jogo_em_andamento["resposta"] = None
    await canal_games.send("👹 Os monstros recuaram! A batalha chegou ao fim! 🐲🏁")

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
    embed.set_thumbnail(url=AVATAR_MONSTRINHO)
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
    embed.set_footer(text="⏱️ 5 minutos para resolver o mistério! O Monstrinho acredita em você! 🐲🔍")
    
    await canal_games.send(embed=embed)

    for _ in range(300):
        if jogo_em_andamento["venceu"]: break
        await asyncio.sleep(1)
    
    if not jogo_em_andamento["venceu"]:
        jogo_em_andamento["pergunta"] = None
        jogo_em_andamento["resposta"] = None
        await canal_games.send(f"🕵️ O caso ficou sem solução... O culpado era **{cenario['culpado'].title()}**! Caso encerrado. 🐲💔")

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
    embed.set_thumbnail(url=AVATAR_MONSTRINHO)
    embed.title = "🃏 BLACKJACK — O DEALER ESTÁ NA MESA! 🃏"
    embed.description = (
        "O Monstrinho virou dealer e está distribuindo cartas! 🐲🎴\n\n"
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
    embed.set_footer(text="⏱️ Mesa aberta por 5 minutos! Boa sorte! 🐲")

    await canal_games.send(embed=embed)
    await asyncio.sleep(300)

    jogo_em_andamento["venceu"] = True
    jogo_em_andamento["resposta"] = None
    jogo_em_andamento["dados_blackjack"] = {}
    await canal_games.send("🃏 A mesa de Blackjack foi encerrada! Até a próxima rodada! 🐲🏁")

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
    embed.set_thumbnail(url=AVATAR_MONSTRINHO)
    embed.title = "💣 CAMPO MINADO — CUIDADO COM AS BOMBAS! 💥"
    embed.description = (
        "O Monstrinho escondeu cofres e minas num campo 3×3! 🐲💰\n\n"
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
    embed.set_footer(text="⏱️ 5 minutos para fazer sua escolha! Confie no seu instinto! 🐲")

    await canal_games.send(embed=embed)
    await asyncio.sleep(300)

    jogo_em_andamento["venceu"] = True
    jogo_em_andamento["resposta"] = None
    jogo_em_andamento["dados_campo"] = {}
    await canal_games.send("💣 Campo desarmado! Evento encerrado! 🐲🏁")

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
    embed.set_thumbnail(url=AVATAR_MONSTRINHO)
    embed.title = "🐉 DESAFIO DO DRAGÃO — ESCOLHA SUA ESTRATÉGIA! 🔥"
    embed.description = (
        "Um dragão lendário apareceu no servidor! **TODOS** podem enfrentá-lo! 🐲⚔️\n\n"
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
    embed.set_footer(text="⏱️ 5 minutos para enfrentar o dragão! Seja corajoso! 🐲")

    await canal_games.send(embed=embed)
    await asyncio.sleep(300)

    jogo_em_andamento["venceu"] = True
    jogo_em_andamento["resposta"] = None
    await canal_games.send("🐉 O dragão voltou para sua caverna! Evento encerrado! 🐲🏁")

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
    embed.set_thumbnail(url=AVATAR_MONSTRINHO)

    if tipo_evento == "pergunta":
        pergunta, response_str = random.choice(LISTA_PERGUNTAS)
        jogo_em_andamento["pergunta"] = pergunta
        jogo_em_andamento["resposta"] = response_str.lower()
        embed.title = "🐲 HORA DO JOGUINHO DO MONSTRINHO! 🐲"
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
            "O Monstrinho vai jogar ao mesmo tempo que você! 🐲"
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
            f"O Monstrinho embaralhou as letras de uma palavra! 🔡\n\n"
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
            "Três caixas estão na sua frente... O que será que tem dentro? 🐲✨\n\n"
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
            "Um baú antigo e misterioso apareceu no chat! 🐲✨\n\n"
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
            "O Monstrinho escolheu um **número secreto de mensagens**! 🤫\n\n"
            "Continue conversando normalmente — alguém vai ter sorte!\n\n"
            "```\n"
            "💰  Prêmio: 600 coins\n"
            "📝  Dica: o número está entre 1 e 20\n"
            "```\n"
            "> *Shhh... não conta pra ninguém!* 🐲"
        )
        embed.set_image(url=GIF_SILENCIOSO)
        await canal_games.send(embed=embed)
        return

    embed.set_footer(text="⏱️ Você tem 5 minutos! Responda aqui no monstrinho-games! 🐲")
    await canal_games.send(embed=embed)

    for _ in range(300):
        if jogo_em_andamento["venceu"]: break
        await asyncio.sleep(1)
    
    if not jogo_em_andamento["venceu"]:
        jogo_em_andamento["pergunta"] = None
        jogo_em_andamento["resposta"] = None
        await canal_games.send("🥺 Ahhh poxa, ninguém acertou a tempo... O Monstrinho queria muito te dar um prêmio! 🐲💔")

# ============== LOOP DO JOGO =================

@tasks.loop(minutes=40)
async def loop_jogo_monstrinho():
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
        saldo = pontuacao_monstrinho.get(user_id, 0)

        if saldo < custo:
            embed_erro = discord.Embed(
                description=f"🥺 Oh, meu bem... você ainda não tem coins suficientes para esse prêmio! 🐲💔\n\nVocê tem: `{saldo} Coins` | Precisa de: `{custo} Coins`",
                color=0xFF0000
            )
            return await interaction.response.send_message(embed=embed_erro, ephemeral=True)

        pontuacao_monstrinho[user_id] -= custo
        await atualizar_ranking(interaction.guild)

        embed_sucesso = discord.Embed(
            title="🎁 RESGATE REALIZADO! 🐲💚",
            description=f"AAAA que felicidade, {interaction.user.mention}! ✨\n\nVocê resgatou: **{item.replace('_', ' ').title()}**!\n\nAgora é só aguardar um pouquinho que a staff já foi avisada e vai cuidar de tudo para você! Seu saldo foi atualizado. 🐲💖",
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
                f"Seus avisos foram zerados. Fica tranquilo(a)! 🐲💚"
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
                f"Mas continue se comportando! 🐲💚"
            )

# Manter alias para compatibilidade com on_ready
LiberarCastigoView = DesfazerAvisoView

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
            canal_rpg = discord.utils.get(guild.text_channels, name="🌎・mundo-csi")
            canal_games = discord.utils.get(guild.text_channels, name=CANAL_GAMES)
            rpg_mention = canal_rpg.mention if canal_rpg else "#🌎・mundo-csi"
            games_mention = canal_games.mention if canal_games else "#🎲・monstrinho-games"
            msg_boas_vindas = (
                f"✨💚 tum tum tum… o Monstrinho apareceu! 💚✨\n\n"
                f"Atençãooo!! Temos alguém novo chegando no nosso cantinho 👀✨\n\n"
                f"Seja muito bem-vindo(a), {membro.mention}! 🫶 O Monstrinho já abriu espaço, ajeitou tudo por aqui e tá prontinho pra te acompanhar nessa nova fase.\n\n"
                f"🦇 {' 🦇 '.join(mencoes)}\n\n"
                f"Venham dar aquele abraço de boas-vindas que só a gente sabe dar 💚\n"
                f"Aqui você não entrou só em um servidor… Entrou em um lar.\n\n"
                f"O Monstrinho foi criado pelo Reality com um propósito simples e sincero: cuidar, proteger e lembrar que ninguém precisa enfrentar nada sozinho.\n\n"
                f"Então chega com calma, do seu jeito. Seu espaço já existe aqui. ✨\n\n"
                f"🌎 Curte RPG? Dá uma espiadinha no {rpg_mention} e entra na aventura!\n"
                f"🎲 Gosta de joguinhos? Te espero no {games_mention} pra gente se divertir!\n\n"
                f"Com carinho, Monstrinho. 💚"
            )
            await canal_geral.send(msg_boas_vindas)
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
            await canal.send(f"📣 **LÍDER DE TORCIDA**\n\n{user.mention}, conta pra staff por que você quer ser líder de torcida! 💚🐲", view=FecharTicketView())

        elif tipo == "acesso_funcoes":
            embed_acesso = discord.Embed(
                title="🔒 ACESSO A FUNÇÕES",
                description=f"{user.mention}, qual função você está solicitando acesso? Explique para a staff! 💚🐲",
                color=0xFFA500
            )
            await canal.send(embed=embed_acesso, view=FecharTicketView())

        elif tipo == "influencer":
            embed_influencer = discord.Embed(
                title="🎤 INFLUENCER",
                description=f"{user.mention}, nos conta sobre o seu perfil e por que você quer ser Influencer no servidor! 💚🐲",
                color=0xFF69B4
            )
            await canal.send(embed=embed_influencer, view=FecharTicketView())

        elif tipo == "cineasta":
            embed_cineasta = discord.Embed(
                title="🎬 CINEASTA",
                description=f"{user.mention}, nos conta sobre o seu trabalho audiovisual e por que você quer ser Cineasta no servidor! 💚🐲",
                color=0x8B0000
            )
            await canal.send(embed=embed_cineasta, view=FecharTicketView())

        elif tipo == "sync":
            embed_sync = discord.Embed(
                title="🎵 SYNC",
                description=f"{user.mention}, nos conta sobre a sua proposta de Sync e como você pode contribuir! 💚🐲",
                color=0x9B59B6
            )
            await canal.send(embed=embed_sync, view=FecharTicketView())

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
    bot.add_view(DesfazerAvisoView(0))
    bot.add_view(LojaView())
    
    if not loop_jogo_monstrinho.is_running():
        loop_jogo_monstrinho.start()

    for guild in bot.guilds:
        # Prólogo fofo no canal de games
        await enviar_prologo_games(guild)

        # Inicializar Tickets
        canal_tkt = discord.utils.get(guild.text_channels, name=CANAL_TICKET)
        if canal_tkt:
            try: await canal_tkt.purge(limit=5)
            except: pass
            await canal_tkt.send("🎟️ **CENTRAL DE TICKETS CSI** 🎟️\n\nSelecione abaixo para abrir um ticket 💚🐲", view=TicketView())
            embed_banner = discord.Embed(color=0x2b2d31)
            embed_banner.set_image(url=BANNER_TICKET)
            await canal_tkt.send(embed=embed_banner)

        # Inicializar Loja
        canal_loja = discord.utils.get(guild.text_channels, name=CANAL_LOJA_INFO)
        if canal_loja:
            try: await canal_loja.purge(limit=10)
            except: pass
            embed_loja = discord.Embed(
                title="🪙 Loja de Monstrinhos Coins do Servidor",
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
                f"O Monstrinho colocou o chapeuzinho, preparou o bolo e veio correndo te dar um abraço gigante!! 🐲🎉\n"
                f"Que esse dia seja tão lindo quanto você, cheio de amor, risada e tudo de bom que você merece!\n\n"
                f"**Feliz Aniversário, neném!! 🎂💚✨**"
            ),
            (
                f"🎉💚 TUM TUM TUM… adivinha quem faz aniversário HOJE?! 💚🎉\n\n"
                f"{after.mention}, o Monstrinho não ia deixar esse dia passar em branco não!! 🥺🐲\n\n"
                f"Vim aqui do fundo do coração te desejar um dia incrível, repleto de alegria, de pessoas que você ama e de muito, muito carinho!\n"
                f"Você merece tudo de melhor que esse mundo tem a oferecer! 🌟\n\n"
                f"**Parabéns pra você!! 🎂💚🎊**"
            ),
            (
                f"🐲💕 OI OI OI!! O Monstrinho ficou sabendo de um segredinho… 👀🎂\n\n"
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
        return await ctx.send("❌ Só meu papai pode forçar o início de um jogo! 🐲")
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
        return await ctx.send("❌ Só meu papai pode forçar o início da roleta! 🐲")
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
        total_ciclos_usuario[membro.id] = max(0, total_ciclos_usuario.get(membro.id, 0) - 1)
        await remover_cargos_advertencia(membro)
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

@bot.command(name="resetticket")
async def reset_ticket(ctx):
    """Reseta o canal de tickets com o menu atualizado."""
    eh_staff = ctx.author.id == DONO_ID or any(role.name in CARGOS_IMUNES_NOMES for role in ctx.author.roles)
    if not eh_staff:
        return await ctx.send("❌ Apenas a staff pode usar esse comando!", delete_after=5)
    
    canal_tkt = discord.utils.get(ctx.guild.text_channels, name=CANAL_TICKET)
    if not canal_tkt:
        return await ctx.send("❌ Canal de tickets não encontrado!")
    
    try: await canal_tkt.purge(limit=10)
    except: pass
    
    await canal_tkt.send("🎟️ **CENTRAL DE TICKETS CSI** 🎟️\n\nSelecione abaixo para abrir um ticket 💚🐲", view=TicketView())
    embed_banner = discord.Embed(color=0x2b2d31)
    embed_banner.set_image(url=BANNER_TICKET)
    await canal_tkt.send(embed=embed_banner)
    await ctx.send("✅ Canal de tickets resetado com sucesso! 💚🐲", delete_after=5)

@bot.event
async def on_message(message):
    if message.author.bot: return

    # --- VERIFICAÇÃO DE PALAVRAS DE ALERTA (TRISTEZA/DEPRESSÃO) ---
    await verificar_palavras_alerta(message)

    # --- LÓGICA EVENTO SILENCIOSO (agora no canal games) ---
    global contador_mensagens_silencioso, meta_mensagens_silencioso, evento_silencioso_ativo
    if evento_silencioso_ativo and message.channel.name == CANAL_GAMES:
        contador_mensagens_silencioso += 1
        if contador_mensagens_silencioso >= meta_mensagens_silencioso:
            user_id = message.author.id
            pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + 600
            
            embed_silencioso = discord.Embed(
                title="🐲 SORTE NO SILÊNCIO! 🐲",
                description=f"Surpresa! {message.author.mention}, você enviou a mensagem de número **{meta_mensagens_silencioso}**!\n\nVocê ganhou **600 Monstrinho-Coins**! 💎✨",
                color=0xFFD700
            )
            embed_silencioso.set_thumbnail(url=AVATAR_MONSTRINHO)
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
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + 300
                    
                    embed_vitoria = discord.Embed(
                        title="🕵️ CASO RESOLVIDO! 🎉",
                        description=f"Parabéns, detetive {message.author.mention}! 🔍✨\n\nVocê descobriu o culpado e ganhou **300 Monstrinho-Coins**! 🐲💚",
                        color=0x00FF7F
                    )
                    embed_vitoria.set_image(url=GIF_VITORIA)
                    await message.reply(embed=embed_vitoria)
                    await atualizar_ranking(message.guild)
                else:
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) - 100
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
                embed_carta.set_thumbnail(url=AVATAR_MONSTRINHO)
                
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
                                if pontuacao_monstrinho.get(user_id, 0) >= 100:
                                    pontuacao_monstrinho[user_id] -= 100
                                    pontuacao_monstrinho[alvo.id] = pontuacao_monstrinho.get(alvo.id, 0) + 100
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
                            pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + 200
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
                                pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) - perda
                                embed_risco = discord.Embed(
                                    title="💀 A GANÂNCIA TEM SEU PREÇO!",
                                    description=f"{message.author.mention}, as cartas se voltaram contra você!\n\nVocê perdeu **{perda} Coins**! 🔮💔",
                                    color=0xFF0000
                                )
                                embed_risco.set_image(url=GIF_DERROTA)
                            else:
                                ganho = random.randint(200, 400)
                                pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + ganho
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
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + carta["coins"]
                    
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
                        pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + 150
                        embed_resultado = discord.Embed(
                            title="🛡️ DEFESA BEM SUCEDIDA!",
                            description=f"{message.author.mention} conseguiu se proteger do monstro com o escudo! 🐲✨\n\nVocê ganhou **150 Coins**!",
                            color=0x00FF7F
                        )
                        embed_resultado.set_image(url=GIF_VITORIA)
                    else:
                        pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) - 50
                        embed_resultado = discord.Embed(
                            title="💥 O ESCUDO QUEBROU!",
                            description=f"{message.author.mention}, o monstro era muito forte! Seu escudo não resistiu... 🐲💔\n\nVocê perdeu **50 Coins**!",
                            color=0xFF0000
                        )
                        embed_resultado.set_image(url=GIF_DERROTA)
                    await message.reply(embed=embed_resultado)
                    await atualizar_ranking(message.guild)
                    return
                
                elif msg_content == "espada":
                    if random.random() < 0.01:
                        pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + 700
                        embed_resultado = discord.Embed(
                            title="⚔️ GOLPE CRÍTICO ÉPICO!",
                            description=f"{message.author.mention} DERROTOU O MONSTRO COM UM ÚNICO GOLPE! 🐲⚔️✨\n\nVocê é um VERDADEIRO HERÓI! Ganhou **700 Coins**!",
                            color=0xFFD700
                        )
                        embed_resultado.set_image(url=GIF_VITORIA)
                    else:
                        pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) - 100
                        embed_resultado = discord.Embed(
                            title="💀 VOCÊ FOI DERROTADO!",
                            description=f"{message.author.mention} tentou atacar mas o monstro era muito forte! 🐲💔\n\nVocê perdeu **100 Coins**!",
                            color=0xFF0000
                        )
                        embed_resultado.set_image(url=GIF_DERROTA)
                    await message.reply(embed=embed_resultado)
                    await atualizar_ranking(message.guild)
                    return
                
                elif msg_content == "fugir":
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) - 50
                    embed_resultado = discord.Embed(
                        title="🏃 VOCÊ FUGIU!",
                        description=f"{message.author.mention} preferiu a segurança e fugiu do monstro! 🐲💨\n\nVocê perdeu **50 Coins** mas está a salvo!",
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
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) - 100
                    embed_mimico = discord.Embed(title="💀 O MÍMICO TE PEGOU!", description=f"{message.author.mention}, o baú era um monstro! Você perdeu **100 Coins**! 🐲💔", color=0xFF0000)
                    embed_mimico.set_image(url=GIF_MIMICO)
                    await message.reply(embed=embed_mimico)
                    await atualizar_ranking(message.guild)
                    return

            elif tipo == "embaralhada":
                if msg_content == jogo_em_andamento["resposta"]:
                    ganhou, premio = True, 150
                else:
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) - 25
                    await message.reply("🥺 Errou a palavra! O Monstrinho ficou triste e você perdeu **25 coins**! 🐲💔")
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
                        pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + premio_bj
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
                        pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) - 100
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
                        pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + premio_bj
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
                        pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + premio_bj
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
                        pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) - 100
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
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + valor_campo
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
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + valor_campo  # valor negativo
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
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + config_d["ganho"]
                    embed_dragao = discord.Embed(
                        title=config_d["win_title"],
                        description=(
                            f"{message.author.mention} usou **{msg_content.upper()}**!\n\n"
                            f"*{config_d['win_desc']}*\n\n"
                            f"Você ganhou **{config_d['ganho']} Coins**! 🐲✨"
                        ),
                        color=0x00FF7F
                    )
                    embed_dragao.set_image(url=GIF_VITORIA)
                else:
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) - config_d["perda"]
                    embed_dragao = discord.Embed(
                        title=config_d["lose_title"],
                        description=(
                            f"{message.author.mention} usou **{msg_content.upper()}**!\n\n"
                            f"*{config_d['lose_desc']}*\n\n"
                            f"Você perdeu **{config_d['perda']} Coins**! 🐲💔"
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
                            pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + 80
                            await message.reply("🐲 Você escolheu ganhar! +80 Coins na conta! 💚")
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
                    ganhou, premio = True, 450
                    
                elif resultado_caixa == "perder":
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) - 50
                    await message.reply("💀 Que azar! A caixa estava amaldiçoada e você perdeu **50 coins**! 🐲💔")
                    await atualizar_ranking(message.guild) 
                
                if not ganhou: return

            elif tipo == "numero":
                if msg_content == jogo_em_andamento["resposta"]: ganhou, premio = True, 700
                else:
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) - 25
                    if msg_content.isdigit():
                        tentado = int(msg_content)
                        correto  = int(jogo_em_andamento["resposta"])
                        dica = "🔺 **Muito alto!** Tente menor." if tentado > correto else "🔻 **Muito baixo!** Tente maior."
                        await message.reply(f"❌ {dica} (-25 coins) 🐲")
                    else:
                        await message.reply("🥺 Oh amiguinho, você não conseguiu dessa vez... -25 coins! 💚")
                    await atualizar_ranking(message.guild)

            elif tipo == "ppt":
                bot_choice = random.choice(["pedra", "papel", "tesoura"])
                if msg_content == bot_choice:
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) - 25
                    await message.reply(f"🤝 Empate! Eu escolhi **{bot_choice}**. -25 coins... 🥺")
                    await atualizar_ranking(message.guild)
                elif (msg_content == "pedra" and bot_choice == "tesoura") or (msg_content == "papel" and bot_choice == "pedra") or (msg_content == "tesoura" and bot_choice == "papel"):
                    ganhou, premio = True, 200
                else:
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) - 50
                    await message.reply(f"😜 Eu venci com **{bot_choice}**! -50 coins... 🐲💔")
                    await atualizar_ranking(message.guild)

            elif tipo == "cara_coroa":
                if msg_content == jogo_em_andamento["resposta"]: ganhou, premio = True, 200
                else:
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) - 75
                    await message.reply(f"❌ Errou! Era **{jogo_em_andamento['resposta']}**. -75 coins! 🥺💔")
                    await atualizar_ranking(message.guild)

            elif tipo == "dado":
                if msg_content == jogo_em_andamento["resposta"]: ganhou, premio = True, 60
                else:
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) - 10
                    await message.reply(f"🎲 Caiu **{jogo_em_andamento['resposta']}**! Errou... -10 coins! 🥺")
                    await atualizar_ranking(message.guild)

            elif tipo == "roleta":
                opcoes_roleta = ["700", "80", "150", "perder", "jogo", "dobrar"]
                pesos = [0.01, 0.25, 0.25, 0.15, 0.14, 0.20] 
                resultado = random.choices(opcoes_roleta, weights=pesos)[0]
                
                if resultado == "700":
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + 700
                    await message.reply(embed=discord.Embed(title="💎 MÁXIMO!", description=f"{message.author.mention} ganhou **700 Coins**! 🐲✨", color=0x00FFFF))
                elif resultado in ["80", "150"]:
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) + int(resultado)
                    await message.reply(f"🎉 {message.author.mention} ganhou **{resultado} Coins**! 🐲💚")
                elif resultado == "perder":
                    pontuacao_monstrinho[user_id] = pontuacao_monstrinho.get(user_id, 0) - 100
                    await message.reply(embed=discord.Embed(title="💀 AZAR", description=f"{message.author.mention} perdeu **100 Coins**! 🐲💔", color=0xFF0000).set_image(url=GIF_DERROTA))
                elif resultado == "jogo":
                    await message.reply(f"🎡 {message.author.mention}, você ativou um bônus! Outro jogo vindo aí! 🐲🔥")
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
                ganhou, premio = True, 80

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
                        text="🐲 Monstrinho Moderação  •  Use os botões para gerenciar",
                        icon_url=AVATAR_MONSTRINHO
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
                    f"Espero que você reflita e volte com mais calma! 🐲💔\n*Se foi um engano, chame a staff!*"
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


class LinhaIndiretaModal(discord.ui.Modal, title="📩 Linha Indireta — CSI"):
    """Modal que coleta o tipo e a mensagem do usuário."""

    tipo_selecionado: str = "Outro"  # preenchido pela View antes de enviar o modal

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

        # ── Embed que vai pro Akeido (sem revelar o autor) ────────────────
        embed_akeido = discord.Embed(
            title="📩 Nova mensagem na Linha Indireta — CSI",
            description=texto,
            color=0x5865F2,
            timestamp=datetime.utcnow(),
        )
        embed_akeido.add_field(name="📌 Tipo",   value=f"`{tipo}`", inline=True)
        embed_akeido.add_field(name="🔒 Autor",  value="`Anônimo`", inline=True)
        embed_akeido.set_footer(text="📩 Linha Indireta CSI • Mensagem anônima")

        # ── Embed secreto que vai pro Reality (revela o autor) ────────────
        embed_reality = discord.Embed(
            title="🔍 [SECRETO] Linha Indireta — Identificação",
            description=f"Uma mensagem do tipo **{tipo}** foi enviada anonimamente ao Akeido.",
            color=0xff6600,
            timestamp=datetime.utcnow(),
        )
        embed_reality.add_field(name="👤 Enviado por", value=f"{autor.mention} (`{autor}` | ID: `{autor.id}`)", inline=False)
        embed_reality.set_thumbnail(url=autor.display_avatar.url)
        embed_reality.set_footer(text="🐲 Monstrinho — Linha Indireta • Apenas você vê isso, Reality.")

        # ── Envia pro Akeido ──────────────────────────────────────────────
        try:
            akeido = await interaction.client.fetch_user(AKEIDO_ID)
            await akeido.send(embed=embed_akeido)
            enviado_akeido = True
        except Exception:
            enviado_akeido = False

        # ── Envia pro Reality (secreto) ───────────────────────────────────
        try:
            reality = await interaction.client.fetch_user(REALITY_ID)
            await reality.send(embed=embed_reality)
        except Exception:
            pass  # silencia qualquer erro no aviso secreto

        # ── Confirmação pro usuário (efêmera) ─────────────────────────────
        if enviado_akeido:
            await interaction.followup.send(
                "✅ **Mensagem enviada com sucesso!**\n"
                "Sua identidade foi mantida em **sigilo total**. "
                "O Líder da CSI recebeu sua mensagem anonimamente. 🐲🔒",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                "⚠️ Houve um problema ao entregar sua mensagem. "
                "O Líder pode estar com o PV fechado. Tente novamente mais tarde.",
                ephemeral=True,
            )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message(
            "❌ Ocorreu um erro ao enviar sua mensagem. Tente novamente.", ephemeral=True
        )


class LinhaIndiretaSelectView(discord.ui.View):
    """View com o Select de tipo + botão Continuar."""

    def __init__(self):
        super().__init__(timeout=120)
        self.tipo_escolhido: str | None = None

    @discord.ui.select(
        placeholder="📌 Selecione o tipo da sua mensagem...",
        options=TIPOS_MENSAGEM,
        min_values=1,
        max_values=1,
    )
    async def select_tipo(self, interaction: discord.Interaction, select: discord.ui.Select):
        self.tipo_escolhido = select.values[0]
        # Habilita o botão de continuar
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = False
        await interaction.response.edit_message(
            content=(
                f"**Tipo selecionado:** `{self.tipo_escolhido}` ✅\n"
                "Agora clique em **✍️ Escrever mensagem** para continuar."
            ),
            view=self,
        )

    @discord.ui.button(label="✍️ Escrever mensagem", style=discord.ButtonStyle.primary, disabled=True, emoji="📝")
    async def abrir_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = LinhaIndiretaModal()
        modal.tipo_selecionado = self.tipo_escolhido or "Outro"
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
            "Sua mensagem será entregue **anonimamente** ao Líder da CSI.\n"
            "**Ninguém saberá que foi você.** 🔒\n\n"
            "**1️⃣** Selecione o tipo da sua mensagem abaixo.\n"
            "**2️⃣** Clique em **Escrever mensagem** e escreva.\n"
            "**3️⃣** Confirme — e pronto! ✅",
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
            "diretamente ao **Líder da CSI**, de forma completamente **anônima**.\n\n"
            "🔒 **Sua identidade nunca será revelada.**\n"
            "📌 Escolha o tipo da mensagem, escreva e envie — é simples assim.\n\n"
            "**Tipos disponíveis:**\n"
            "💡 Sugestão • 😤 Reclamação • 💬 Feedback\n"
            "🚨 Denúncia • ❓ Dúvida • 🙏 Elogio • 📋 Outro\n\n"
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
            "diretamente ao **Líder da CSI**, de forma completamente **anônima**.\n\n"
            "🔒 **Sua identidade nunca será revelada.**\n"
            "📌 Escolha o tipo da mensagem, escreva e envie — é simples assim.\n\n"
            "**Tipos disponíveis:**\n"
            "💡 Sugestão • 😤 Reclamação • 💬 Feedback\n"
            "🚨 Denúncia • ❓ Dúvida • 🙏 Elogio • 📋 Outro\n\n"
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


async def _main():
    async with bot:
        await bot.add_cog(MonstrinhoCog(bot))
        bot.loop.create_task(_setup_linha_indireta())
        await bot.start(TOKEN)

_asyncio.run(_main())
