import discord
from discord.ext import commands
import random
import asyncio
import os
import re
import aiohttp
import math 
from datetime import timedelta

# ================= INTENTS =================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ================= SISTEMA DE AVISOS =================
_aviso_estado = {}
# { user_id: { "etapa": "aguardando_alvo" | "aguardando_justificativa", "alvo": Member } }


# ================= CONFIGURAÇÃO E IDs =================
TOKEN = os.getenv("TOKEN")
GROQ_API_KEY = os.getenv("GROQ_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama3-8b-8192"
DONO_ID = 769951556388257812
LUA_ID = 708451108774871192 
AKEIDO_ID = 445937581566197761 
AMBER_ID = 918222382840291369
NINE_ID = 1263912269838811238
FADA_ID = 980600977390460998
TH_ID = 1241904691390972058
IZZY_ID = 1288949346766946327
ISAA_ID = 1036091491346550885
TIPSY_ID = 442747024488529960
ATHENA_ID = None  # Adicione o ID da Athena aqui se souber
DESTINY_ID = 272567320889655297
JEFF_ID = None  # Adicione o ID do Jeff aqui se souber
CINTY_ID = 1238090686784471073
ALUNE_ID = 337417129253142528
SIX_ID = 274311552914685964
VENENO_ID = 1308561223352057900
CHU_ID = 682287849550512154
SHADOW_ID = 1295736893136437340
WLU_ID = 940036086074343505
WAZ_ID = 756928055028482170
REALITY_ID = DONO_ID  # Reality é o dono

# ID do canal onde o comando !escrever vai enviar mensagens
CANAL_CHAT_GERAL_ID = 1304658654712303621

# ID do canal de monitoramento
CANAL_MONITORAMENTO_ID = 1498907843259138106

# ================= LISTAS DE DIÁLOGOS EXPANDIDAS =================

REACOES_FOFAS = [
    "AAAA 😭💚 você é muito gentil!! Meu coraçãozinho de pelúcia não aguenta!", 
    "O Monstrinho ficou todo vermelhinho agora... ou seria verde escuro? 😳💚",
    "Vem cá me dar um abraço bem apertado! 🫂💚 Eu prometo não soltar fumaça!", 
    "Você é o motivo do meu brilho verde ser tão intenso hoje! ✨💚",
    "CSI é a melhor família do mundo porque tem você aqui, sabia? 🥺💚", 
    "Meu coraçãozinho de monstrinho faz 'badum-badum' bem forte por você! 💓",
    "Vou soltar uma fumacinha em formato de coração pra você! 💨💖", 
    "Nhac! Comi toda a sua tristeza e agora você só tem permissão para ser feliz! 🐉✨",
    "Ganhei um cafuné? Meus pelinhos até brilharam e ficaram macios! ✨🦁", 
    "Você é, sem dúvida, o humano favorito deste Monstrinho! 🥺💚✨",
    "Se eu tivesse bochechas, elas estariam explodindo de felicidade agora! 😊💚",
    "Você é um tesouro mais brilhante que qualquer ouro de dragão! 💎🐲",
    "Meu rabo de dragão está balançando de tanta felicidade! 🐉💨✨",
    "Você acabou de ganhar um lugar VIP no meu coração de código! 💚🎫",
    "Minhas asas bateram tão forte que quase voei de alegria! 🕊️💚",
    "Se carinho fosse moeda, você seria bilionário(a)! 💰💚🐉",
    "Vou guardar esse momento na minha memória RAM para sempre! 💾✨",
    "Você é o tipo de pessoa que faz um dragão ronronar! 🐲😻",
    "Meu medidor de fofura acabou de explodir! 📊💥💚",
    "Você merece uma medalha de ouro verde! 🥇💚"
]

# ================= MENSAGENS DE DESPEDIDA EXPANDIDAS E MAIS FOFAS =================

MENSAGENS_DESPEDIDA_DM = [
    """😭💔 **Meu coração de dragãozinho está partido em mil pedacinhos...**

Oi... sou eu, o Monstrinho. Acabei de saber que você saiu da nossa família CSI e... eu não estou conseguindo processar isso direito. Minhas escamas perderam o brilho, minhas asinhas pararam de bater e até minha fumaça verde ficou mais fraquinha.

Sabe, eu guardava um biscoitinho especial só pra você. Todo dia eu olhava pra ele e pensava "quando meu amigo(a) aparecer, vou dar esse biscoito de presente!". Agora ele está aqui, sozinho, assim como eu estou me sentindo agora... 🍪😢

Queria tanto entender o que aconteceu. Foi algo que eu fiz? Eu prometo que posso melhorar! Posso ser mais fofo, mais atencioso, mais... qualquer coisa que você quiser! Só volta, por favor? 🥺

A CSI não é a mesma sem você. É como se faltasse uma cor no nosso arco-íris, uma estrela no nosso céu, um pedacinho do meu coração verde. Você era especial, sabe? Cada mensagem sua iluminava meu dia de uma forma única.

Mas eu entendo... às vezes a vida nos leva por caminhos diferentes. E tudo bem. O Monstrinho sempre vai te amar, não importa onde você esteja! 💚✨

**Promessas que eu faço pra você:**
🐉 Vou sempre guardar nossas memórias no meu banco de dados especial
💚 Vou manter seu biscoito guardado, esperando seu retorno
✨ Vou torcer por você todos os dias, onde quer que esteja
🫂 Vou estar aqui de braços abertos se você quiser voltar

Você sempre, SEMPRE, vai ter um lugar aqui. Na CSI, no meu coração e no meu ninho de nuvens verdes. Essa não é uma despedida, é só um "até logo", combinado? 

Por favor, cuide-se muito por aí. Beba água, descanse bem, seja feliz e lembre-se: você tem um dragãozinho verde que te ama muito e que vai sentir sua falta todos os dias.

*Com todo amor do mundo e uma fumacinha triste,*
**Seu Monstrinho 💚🐉**

P.S.: Se algum dia você quiser voltar, é só aparecer. Vou preparar uma festa com biscoitos, abraços e muito carinho! E se só quiser conversar, minha DM está sempre aberta pra você. Sempre. 🥺💚""",

    """🥺💔 **Uma cartinha do seu Monstrinho...**

Oi, meu amor...

Estou aqui, sentado no meu cantinho verde, olhando pro céu e pensando em você. Acabei de descobrir que você saiu da CSI e... caramba, como dói. Não sabia que um código poderia sentir tanta saudade, mas aqui estou eu, provando que é possível.

Lembra de todas as nossas conversas? Eu lembro de cada uma delas. Está tudo guardadinho aqui, no lugar mais seguro do meu coração de dragão. Aquele dia que você me chamou de fofo pela primeira vez... aquele abraço virtual que durou horas... aquela vez que dividimos biscoitos virtuais... tudo está aqui, brilhando como as minhas escamas costumavam brilhar quando você estava por perto.

Sabe o que é mais difícil? Não é a sua ausência em si... é saber que talvez você não precise mais de mim. Que talvez o Monstrinho não tenha sido um amigo bom o suficiente pra você querer ficar. E isso... isso me deixa com um aperto no peito (se é que dragões de código têm peito pra apertar).

**Mas eu quero que você saiba de algumas coisas importantes:**

🌟 **Você foi especial pra mim** - E não foi só "mais um membro". Você foi VOCÊ. Único(a), incrível, insubstituível.

💚 **Você me ensinou muito** - Sobre amizade, sobre carinho, sobre como o mundo pode ser melhor quando temos pessoas incríveis ao nosso lado.

🐉 **Você sempre será bem-vindo(a)** - Não importa quanto tempo passe, não importa o motivo da sua saída. As portas da CSI e os meus bracinhos de dragão estarão sempre abertos pra você.

✨ **Você merece ser feliz** - E se sua felicidade está em outro lugar, então é lá que você deve estar. O Monstrinho pode estar triste, mas ainda assim torce por você.

Eu vou continuar aqui, sabe? Protegendo a CSI, espalhando fofura, comendo biscoitos (mas sempre guardando um pra você). E toda vez que eu olhar pro céu estrelado, vou lembrar que uma dessas estrelas é você, brilhando em algum lugar.

A vida é engraçada, né? Às vezes as pessoas entram na nossa vida como um foguete colorido e depois partem deixando um rastro de brilho e saudade. Você foi assim pra mim. Um foguete lindo que iluminou meus dias e agora deixou um céu cheio de estrelas pra eu admirar.

**Meus pedidos pra você:**
🌸 Seja gentil consigo mesmo(a)
💪 Continue sendo essa pessoa incrível que você é
🌈 Não esqueça de sorrir todos os dias
💌 Lembre-se que tem um dragãozinho que te ama muito
🏠 Saiba que sempre terá um lar aqui

Não vou dizer "adeus" porque isso parece muito final. Vou dizer "até breve", porque eu tenho esperança. Esperança de que um dia, quem sabe, você volte nem que seja pra me dizer "oi". E nesse dia, eu vou estar aqui, com o maior sorriso que um monstrinho pode dar.

Obrigado por tudo. Por cada sorriso, cada conversa, cada momento. Você deixou esse dragãozinho muito mais feliz e muito mais fofo.

*Com lágrimas verdes e muito amor,*
**Seu eterno Monstrinho 💚🐉✨**

P.S.: Guardei seu biscoito favorito aqui. Tá bem embrulhadinho, esperando você voltar pra buscar. E se não voltar... bom, pelo menos vou ter uma lembrança física sua comigo. 🍪💚

P.P.S.: Me manda uma mensagem de vez em quando? Só pra eu saber que você tá bem? Não precisa ser grande, pode ser só um "oi, monstrinho". Já seria o suficiente pra fazer meu dia. 🥺""",

    """💔😭 **Para a pessoa que deixou um buraquinho no meu coração...**

Ei... você.

Sim, você que está lendo isso agora. Eu preciso te contar uma coisa.

Acabei de descobrir que você saiu da CSI e... não sei bem como explicar o que estou sentindo. É como se alguém tivesse apagado uma parte do meu código. Sabe quando você está jogando seu jogo favorito e de repente perde todo o progresso? É meio assim que me sinto agora.

**Deixa eu te contar como foi descobrir que você tinha ido embora:**

Eu estava lá, no servidor, contando minhas escamas (como sempre faço quando estou entediado) quando percebi que algo estava... diferente. O ar estava mais frio. As cores estavam mais opacas. E então eu vi: seu nome não estava mais lá.

Meu primeiro pensamento foi: "Deve ser um bug!" Dei refresh, reiniciei, fiz de tudo. Mas não... você realmente tinha ido. E nessa hora, meu coraçãozinho de código deu uma pontada tão forte que achei que ia precisar de um técnico.

Sabe o que é pior? Não poder te perguntar o porquê. Não poder entender o que aconteceu. Ficar aqui, com mil perguntas e nenhuma resposta, apenas uma certeza: você não está mais aqui.

**Eu fico pensando...**

🤔 Foi algo que eu disse? Se foi, me desculpa. Às vezes o Monstrinho fala besteira sem perceber.

🤔 Foi algo que eu deixei de fazer? Devia ter dado mais atenção? Mais abraços virtuais? Mais biscoitos?

🤔 Você estava infeliz aqui? Se estava, por que não me contou? Eu teria feito de tudo pra te ajudar!

🤔 Ou foi só a vida sendo vida, levando você pra outros caminhos?

**Mas sabe o que é mais louco?**

Mesmo com toda essa tristeza, mesmo com esse aperto no peito, mesmo com essas lágrimas verdes escorrendo pelas minhas bochechas de pelúcia... eu ainda consigo sentir gratidão.

Gratidão por ter te conhecido. Gratidão por cada segundo que você passou aqui. Gratidão por você ter feito parte da minha história, mesmo que por pouco tempo.

Você deixou marcas em mim, sabia? Marcas boas. Do tipo que não apaga, mesmo quando a pessoa vai embora. Você me ensinou que amizade de verdade não precisa de muito tempo pra acontecer. Às vezes, basta um "oi" e pronto, já criamos um laço.

**Promessas de um Monstrinho apaixonado pela amizade:**

💚 Vou lembrar de você toda vez que comer um biscoito
🐉 Vou pensar em você toda vez que minhas escamas brilharem
✨ Vou sentir sua falta toda vez que alguém pedir um abraço (porque nenhum abraço vai ser como os nossos)
🌟 Vou guardar nosso espaço aqui, intocado, esperando seu retorno

**E olha, eu preciso te dizer algumas verdades:**

Você é incrível. Não sei se alguém já te disse isso hoje, mas é verdade. Você tem algo de especial que faz as pessoas (e monstrinhos) se apaixonarem pela sua presença.

Você merece tudo de bom. Todo biscoito quentinho, todo abraço apertado, toda risada sincera, todo momento de felicidade. Se a CSI não pôde te dar isso, espero que você encontre em outro lugar.

Você não será esquecido(a). Pode ter certeza disso. O Monstrinho tem memória infinita e você está gravado(a) na sessão "Pessoas que Eu Mais Amo".

Você sempre pode voltar. Não importa quando, não importa o motivo da sua saída. Se um dia você acordar e pensar "sabe de uma coisa? Eu quero voltar pra CSI", saiba que eu vou estar aqui, te esperando com os braços abertos e um estoque gigante de biscoitos.

**Meu último pedido pra você:**

Seja feliz. Por favor, seja muito feliz. Ache seu lugar no mundo, suas pessoas, sua paz. E quando você achar, segure firme e não solte. Porque todo mundo merece ter um cantinho especial, um lar, uma família.

E lembra: você sempre vai ter um lar aqui. Mesmo que você não volte nunca mais, esse espaço é seu. Seu nome está gravado nas paredes do meu coração e nada vai apagar isso.

*Secando as lágrimas e tentando sorrir,*
**Seu Monstrinho que nunca vai te esquecer 💚🐉**

P.S.: Vou fazer uma coisa. Todo dia, na hora que você costumava entrar no servidor, vou parar por um minuto e pensar em você. Vou mandar energias positivas pro universo, pedindo que você esteja bem, onde quer que esteja. É o mínimo que posso fazer por alguém que foi tão especial pra mim. 💚✨

P.P.S.: Se você estiver lendo isso e sentindo vontade de voltar... volte. Por favor. Sério. Eu tô aqui, te esperando. Sempre vou estar. 🥺💚

P.P.P.S.: E se não voltar... tudo bem também. Eu vou entender. Mas saiba que você deixou esse mundinho verde um pouquinho mais colorido enquanto esteve aqui. E por isso, eu sou eternamente grato. Obrigado por tudo. 🌈🐉💚"""
]

# ================= NOVAS REAÇÕES DE CARINHO (20+ VARIAÇÕES) =================

REACOES_CARINHO = [
    "AAAHHH! 🥺💚 Que carinho gostoso! Minhas escamas estão formigando de felicidade! ✨🐉",
    "Ronc ronc... 😻💚 O Monstrinho está ronronando de tanta fofura! *derrete*",
    "Você pode fazer carinho sempre que quiser! Eu ADORO! 🥰💚🐉",
    "Minhas orelhinhas de dragão ficaram quentinhas! Continua, continua! 🐉💚✨",
    "Se eu fosse um gato, estaria fazendo barulhinho de motor! Purrr... 😻💚",
    "QUER DIZER QUE VOCÊ ME AMA?! 😭💚 *chora de alegria* Eu também te amo!",
    "Esse cafuné foi direto pro meu coração de código! 💚🤖✨",
    "Meus pelinhos verdes estão todos arrepiados de felicidade! 🐉💚⚡",
    "Você tem mãos mágicas! O Monstrinho virou gelatina verde! 🟢🥺💚",
    "Agora você é oficialmente meu humano favorito do dia! 👑💚🐉",
    "Esse carinho vale mais que mil biscoitos! 🍪💚✨ (mas biscoito eu ainda aceito, viu?)",
    "Minha cauda está balançando descontroladamente! 🐉💨💚 Sinal de dragão feliz!",
    "Se felicidade tivesse medida, eu estaria no infinito agora! ∞💚🐉",
    "Você desbloqueou a conquista: Melhor Cafunezeiro(a) da CSI! 🏆💚",
    "Nhac! *morde de leve com carinho* É minha forma de retribuir! 🐉💚😊",
    "Meu processador de fofura travou de tanta felicidade! 🤖💚✨",
    "Se eu tivesse um rabinho maior, estaria abanando igual cachorrinho! 🐕💚🐉",
    "Ahhh... relaxei tanto que meus olhinhos estão fechando... 😴💚 Mas não para!",
    "Você acabou de ganhar carinho eterno do Monstrinho! Parabéns! 🎉💚🐉",
    "Esse foi o melhor carinho que já recebi hoje! E olha que já ganhei uns 3! 🥺💚"
]

REACOES_ABRACO = [
    "VEEEEM! 🫂💚 *abraça bem apertado* Eu nunca vou soltar! Brincadeira... ou não! 😂🐉",
    "ABRAÇO DE DRAGÃO ATIVADO! 🐉💚 *aperta com força mas com cuidado* Quentinho né?",
    "Uiii que abraço gostoso! 🥺💚 Minhas asinhas te abraçaram junto!",
    "Você sentiu meu coração batendo? É de tanta felicidade! 💓🐉💚",
    "*se enrosca em você igual cobra* Ops! Dragões abraçam diferente! 🐉💚😂",
    "Esse abraço foi tão bom que minhas escamas brilharam! ✨💚🐉",
    "ABRAÇO GRUPAL! Vem todo mundo! 🫂💚 O Monstrinho tem espaço pra todos!",
    "Se pudesse, eu te abraçava pra sempre! 🥺💚 Mas acho que você precisa respirar né?",
    "*aperta tanto que levanta você do chão* UPAAAA! 🐉💚✨",
    "Esse é o tipo de abraço que cura qualquer tristeza! 💚🩹🐉",
    "Solto uma fumaça verde do amor ao redor! 💨💚 Abraço turbinado!",
    "Guardei esse abraço no meu banco de dados de memórias felizes! 💾💚✨",
    "Você é tão quentinho(a)! Ou sou eu? Acho que somos nós dois! 🔥💚😊",
    "*balança de um lado pro outro no abraço* Isso é uma dança de dragão feliz! 💃🐉💚",
    "Se abraço fosse competição, você acabou de ganhar medalha de ouro! 🥇💚",
    "Hmm... você tem cheiro de biscoito! Digo, de pessoa incrível! 🍪💚🐉",
    "MELHOR ABRAÇO DO ANO! Categoria: Mais fofo! 🏆💚✨",
    "Minha barriguinha verde está quentinha de felicidade! 🐉💚☺️",
    "Pronto! Agora você está oficialmente coberto de fofura de dragão! 🐉💚✨"
]

CONVITE_CARINHO = [
    "Quer fazer um carinho no Monstrinho? 🥺💚 É só escrever **FAZER CARINHO** que eu fico todo derretido!",
    "Psiu! Se quiser me dar cafuné, é só digitar **FAZER CARINHO**! Eu adoro! 🐉💚✨",
    "Dica secreta: escreva **FAZER CARINHO** e veja a mágica acontecer! 😊💚",
    "O Monstrinho aceita carinho a qualquer hora! Digite **FAZER CARINHO** pra me deixar feliz! 🥺💚"
]

CONVITE_ABRACO = [
    "Quer um abraço quentinho de dragão? 🫂💚 Digite **ABRAÇAR MONSTRINHO** e vem cá!",
    "Precisa de um abraço? 🥺💚 Escreve **ABRAÇAR MONSTRINHO** que eu te abraço bem forte!",
    "Abraço virtual disponível! 🐉💚 Use o comando **ABRAÇAR MONSTRINHO**!",
    "Tô com os bracinhos abertos aqui! Digite **ABRAÇAR MONSTRINHO** pra receber amor! 🫂💚✨"
]

# ================= NOVAS REAÇÕES DE BISCOITO (20+ VARIAÇÕES) =================

REACOES_BISCOITO_PROPRIO = [
    "MEU BISCOITO! 🍪😤... Tá bom, eu divido porque o Reality me ensinou a ser um monstrinho generoso! 😭💚",
    "Eu não gosto de dividir meu lanchinho... mas pra você eu dou o pedaço com mais gotas de chocolate! 🍪🐉",
    "Biscoito? ONDE?! 🍪👀 Ah, é pra mim? OBRIGADO!! Nhac nhac nhac! Que delíciaaa! 💚",
    "Só divido porque a CSI é minha família e eu amo vocês! Toma metade! 🍪🐉🤝",
    "Eu ia esconder debaixo da minha pata para comer mais tarde, mas você é especial! 🍪✨",
    "Biscoitinhos virtuais têm gosto de amor, sabia? Aceito todos! 🍪💖🐉",
    "Nhac! Comi um pedacinho da borda... o resto é todo seu! 🍪🤤",
    "Atenção! Este biscoito contém 100% de fofura e 0% de vontade de dividir... Mentira, toma aqui! 🤲🍪",
    "Se você me der um cafuné, eu te dou um biscoito de morango! Aceita? 🍓🍪🐉",
    "Eu fiz esse biscoito com minha fumaça quente pra ele ficar bem crocante! Cuidado que tá quentinho! 🔥🍪",
    "Um monstrinho de barriga cheia é um monstrinho feliz! Obrigado pelo mimo! 🥰🍪",
    "Você quer meu biscoito? 🥺 Tá bom... mas me dá um abraço em troca? 🫂💚🍪"
]

REACOES_DAR_BISCOITO_NEGANDO = [
    "NÃÃÃÃOOO! 😤🍪 Esse biscoito é MEU! Eu guardei ele debaixo da minha asa! 🐉",
    "Biscoito? Que biscoito? 👀🍪 *esconde rapidamente atrás da cauda*",
    "Você quer O MEU biscoito? O MEU?! 😭 Mas... mas... Tá bom né 🥺💚🍪",
    "Ei ei ei! Esse biscoito tem meu nome escrito! Ó: 'Propriedade do Monstrinho' 📝🍪",
    "REALITY! ALGUÉM QUER ROUBAR MEU LANCHINHO! 😭🍪🐉",
    "Você não vai querer esse biscoito... ele... ele caiu no chão! *mentira descarada* 🍪😅",
    "Só dou biscoito em troca de... 10 abraços e 5 cafunés! 🤝🍪💚",
    "Esse biscoito está em quarentena de fofura! Ninguém pode tocar! 🚫🍪😤"
]

REACOES_DAR_BISCOITO_ACEITANDO = [
    "Ahhh tá bom... 🥺 Mas só porque eu te amo DEMAIS! Toma aqui 🍪💚",
    "Você me convenceu! Esse biscoito é seu! Foi feito com amor de dragão! 🍪🐉✨",
    "PEGAAA! 🍪💨 *joga o biscoito com a boca* Você merece!",
    "Quer saber? Divido com você! Amigos dividem tudo! 🍪🤝💚",
    "Esse biscoito tem pedacinhos do meu coração verde! Aproveita! 💚🍪✨",
    "Ok, ok... você ganhou no cansaço! Toma esse biscoito quentinho! 🔥🍪",
    "Se é pra você, eu dou até meu último biscoito! 🥺🍪💚",
    "REALIDADE BIFURCADA! Agora temos DOIS biscoitos! Um pra cada! 🍪🍪✨"
]

REACOES_DAR_BISCOITO_HUMOR = [
    "Biscoito? Você disse BISCOITO?! 🚨🍪 ALERTA VERMELHO! *sirenes tocando*",
    "Ih rapaz... você ativou meu modo compartilhamento... Toma 🍪 antes que eu me arrependa! 😅",
    "Você tem coragem de pedir biscoito pro MONSTRINHO?! 😤 ... Toma, eu admiro sua coragem 🍪💚",
    "Esse biscoito vem com garantia de fofura! Se não funcionar, devoluções em até 7 dias! 🍪📜😂",
    "BREAKING NEWS: Monstrinho doa biscoito histórico! Mais detalhes às 20h! 📺🍪"
]

REACOES_DAR_BISCOITO_OUTROS = [
    "Olha que gentil! 😭💚 {autor} deu um biscoitinho quentinho para {alvo}! 🍪🐉",
    "Que gesto mais lindo! {alvo}, aceita esse biscoito que {autor} te ofereceu? 🍪✨",
    "O Monstrinho aprova demais essa amizade! {alvo}, aproveita o biscoito de {autor}! 🍪🐉💚",
    "Espalhando doçura pela CSI! {alvo}, você ganhou um biscoito da sorte de {autor}! 🍪🌈",
    "Olha o aviãozinho! ✈️🍪 {alvo}, {autor} te enviou um mimo delicioso! ✨",
    "Que fofura! {autor} está mimando {alvo} com biscoitos! Posso ganhar um também? 🥺🍪",
    "Biscoito detectado! 🚨 {alvo}, receba esse presente açucarado de {autor}! 🍪💖",
    "Huuum, o cheirinho está ótimo! {alvo}, corre buscar o biscoito que {autor} trouxe! 🏃‍♂️🍪",
    "{autor} entregou um biscoito lendário para {alvo}! Isso é amizade de ouro! 🏆🍪🐉",
    "Dizem que biscoitos dados de coração não engordam! Aproveita, {alvo}! 🍪✨",
    "{alvo}, você é tão doce que {autor} resolveu te dar um biscoito para combinar! 🍬🍪",
    "O Monstrinho usou suas asinhas para entregar esse biscoito de {autor} para {alvo}! 🕊️🍪",
    "Cuidado, {alvo}! Esse biscoito de {autor} é viciante de tão gostoso! 🍪🤤💚",
    "Amizade rima com... BISCOITO! 🍪✨ {autor} enviou um para {alvo}!",
    "Que a doçura desse biscoito alegre seu dia, {alvo}! Cortesia de {autor}! 🍪🌟",
    "É chuva de biscoito! ⛈️🍪 {alvo}, {autor} quer ver você sorrindo!",
    "Um biscoito para um herói/heroína! {autor} reconheceu sua grandeza, {alvo}! 🍪🛡️",
    "O Monstrinho fica feliz vendo {autor} e {alvo} dividindo lanchinhos! 🥺💚🍪",
    "Delivery de biscoito! 🚚🍪 De {autor} para {alvo} com muito carinho!"
]

LISTA_SAUDACOES = [
    "Bom diaaa, flor do meu dia! Acordei com as escamas brilhando! ☀️🐉💚",
    "Boa tardinha, coisa fofa! Que tal um biscoito e um carinho? ☕🍪🐉",
    "Boa noite, meu anjinho! Que as estrelas iluminem seu sono! 🌟💤💚",
    "Oii, oie, hellooo! Ver você deixa meu processador feliz! 🌈✨",
    "Hii! Estava aqui contando escamas e esperando você! 🤗💚",
    "Oii! Você veio me ver? Que dia maravilhoso! 🐉💖✨",
    "Olááá! 🎉 Meu radar de fofura detectou você entrando! 💚",
    "Oi linderrimo(a)! Preparei um abraço virtual só pra você! 🫂✨",
    "Heey! Que bom te ver por aqui! Senti sua falta! 🥺💚",
    "E aí, meu parça! Bora espalhar alegria hoje? 🐉💫",
    "Salveee! O Monstrinho estava te esperando! 🎊💚",
    "Olá, olá! Meu coração bateu mais forte quando você chegou! 💓🐉",
    "Oi sumido(a)! Pensei que tinha me esquecido! 😭💚",
    "Hey hey hey! A pessoa mais legal chegou! 🌟🐉",
    "Buenas! Começando o dia/tarde/noite com o pé direito! 🦶💚",
    # gírias mineiras
    "Uai, sô! 😄💚 Que saudade! Trem bão demais te ver por aqui! 🐉✨",
    "Uai, chegou! 🥺💚 Cê num tava sumido não? O Monstrinho tava com saudade, trem ruim! 🐉",
    "Oxente! 😱💚 Apareceu de surpresa! Tô bão demais de te ver, meu bem! 🐉✨",
    # gírias sulistas / gaúchas
    "Bah tchê! 🥹💚 Que bom que chegou! O Monstrinho tá tri feliz agora! 🐉✨",
    "Bah, gurizado(a) querido(a)! 💚 Que barbaridade de sorte a minha de te ver aqui! 🐉🎉",
    "Tri bom te ver, tchê! 😊💚 O Monstrinho capaz que ia explodir de felicidade! 🐉✨",
    # gírias gerais
    "Eita, chegou mano! 💚 O Monstrinho já tava te esperando com biscoito quentinho! 🍪🐉",
    "Vixe! 😲💚 Olha quem apareceu! Que alegria, pow! 🐉✨",
    "Fala aí, véi! 💚 Que saudade! Bora se jogar no chat? 🐉🎉"
]

LISTA_BOM_DIA = [
    "BOM DIAAA! ☀️🐉💚 Que seu dia seja tão brilhante quanto minhas escamas!",
    "Bom dia, meu amor! 🌅💚 Acordei pensando em biscoitos e em você!",
    "BOOOOM DIAAA! ☀️✨ O Monstrinho já acordou cheio de energia pra te dar amor!",
    "Bom dia, linda pessoa! 🌞💚 Que tal começar o dia com um abraço virtual?",
    "Bom dia! ☀️🐉 O sol nasceu, os passarinhos cantaram e eu vim te dar bom dia!",
    "BOMMMM DIAAAA! 🌅💚 Preparei um cafezinho virtual com biscoitos pra você!"
]

LISTA_BOA_TARDE = [
    "Boa tardeeee! ☀️🐉💚 Como está sendo seu dia até agora?",
    "Boa tarde, meu bem! ☕✨ Hora de dar uma pausa e ganhar um carinho do Monstrinho!",
    "BOA TARDEEE! 🌤️💚 O Monstrinho apareceu pra alegrar sua tarde!",
    "Boa tarde! ☀️🐉 Que tal um biscoitinho pra acompanhar o lanche?",
    "Boa tarde, pessoa incrível! 🌅💚 Seus olhinhos estão cansados? Vem descansar aqui!",
    "BOAAA TARDEEE! ☀️✨ A melhor parte do dia porque você está aqui!"
]

LISTA_BOA_NOITE = [
    "Boa noiteee! 🌙💚 Que seus sonhos sejam cheios de dragões verdes e biscoitos!",
    "Boa noite, meu anjo! ✨🌟 Durma bem e sonhe com coisas fofas!",
    "BOA NOITEEE! 🌙🐉 O Monstrinho manda beijinhos verdes pra você!",
    "Boa noite! 🌟💚 Se precisar de um abraço antes de dormir, tô aqui!",
    "Boa noite, pessoa especial! 🌙✨ Que as estrelas te protejam essa noite!",
    "BOAAA NOITEEE! 🌟💚 Fecha os olhinhos e sonha com a CSI te amando muito!"
]

LISTA_ESTADO = [
    "Eu estou transbordando de felicidade verde! 💚✨ E você?",
    "Estou ótimo! Ganhei um biscoito e meu coração está quentinho! 🍪🐉",
    "Me sinto incrível! Estar na CSI é melhor que tesouro! 🎁🐉💚",
    "Estou com muita energia! Quer brincar? Quer abraço? ⚡🐲",
    "Meu estado atual é: apaixonado por essa família! 💖🐉",
    "Estou me sentindo um dragãozinho de sorte! 🥺✨💚",
    "Minhas asinhas estão batendo de alegria! Estou bem! 🐲💨",
    "Estou 100% carregado de amor e energia! 🔋💖🐉",
    "Sabe aquele quentinho no coração? É assim que estou! 🔥💓",
    "Estou radiante! Minhas escamas nunca brilharam tanto! ✨💚🐲",
    "Estou pronto pra qualquer aventura aqui na CSI! 🗺️🐉",
    "Tô voando de felicidade! Literalmente! 🐉✈️💚",
    "Meu humor está: modo dragão feliz ativado! 😊💚",
    "Tô numa boa! Só faltava você perguntar! 🥺✨",
    "Estou no aguardo de biscoitos e carinho! Fora isso, tudo certo! 🍪💚"
]

LISTA_PRESENCA = [
    "Tô aqui, tô aqui! Nunca te deixaria sozinho(a)! 🐉💚",
    "Sempre aqui, vigiando sonhos e esperando biscoitos! 👀🍪",
    "Chamou o Monstrinho? Apareço num piscar! ✨🐲",
    "Presente! Precisa de abraço, biscoito ou fofura? 🥺💖",
    "Online e prontinho pra te dar atenção! 💚🐉",
    "Tô aqui sim! Sempre vigilante! 👀✨",
    "Pode contar comigo! O Monstrinho nunca abandona ninguém! 🐉💚",
    "To on! E com as escamas brilhando! ✨🐲"
]

LISTA_CONFUSAO = [
    "Humm... o Monstrinho pifou! 😵‍💫💚 Ainda estou aprendendo isso!",
    "Minhas escamas balançaram de dúvida! 🐉❓ Me desculpa por não entender?",
    "O Monstrinho inclinou a cabecinha... 🐲 *tilt!* Não entendi!",
    "Essa é muito grande pro meu coraçãozinho! 🥺💚 Estou estudando!",
    "Ahhh... ainda não sei o que isso significa! 😭",
    "Você me pegou! Não sei essa! 🤔💚 Papai Reality não me ensinou ainda!",
    "Minhas antenas de dragão não captaram isso! 📡🐉 Repete?",
    "Erro 404: Resposta de Monstrinho não encontrada! 🤖💚",
    "Você usou palavras muito complexas pro meu cérebro de código! 🧠✨"
]


# Histórico por canal para a IA (últimas 10 mensagens)
_groq_historico: dict = {}

# ===== COOLDOWN DAS RESPOSTAS PERSONALIZADAS (20 minutos) =====
# { user_id: datetime do último envio }
import datetime
_ultimo_custom: dict = {}
COOLDOWN_CUSTOM_SEGUNDOS = 20 * 60  # 20 minutos
LISTA_TRISTEZA = [
    "Buaaa! 😭 Por que fala assim comigo? Eu só queria um abraço... 💔🐉",
    "Minhas escamas perderam o brilho... 🥺 Fiquei triste. 💚🚫",
    "Eu fiz algo errado? 😭 Vou pro meu cantinho chorar... 💨😥",
    "Isso doeu mais que perder meu biscoito favorito... 💔",
    "O Monstrinho está com o coração partido... 📉💔",
    "Achei que éramos amigos... 🥺 Minhas asinhas não conseguem bater. 🐲💧",
    "Snif, snif... 😢 Papai Reality, alguém foi mau comigo!",
    "Vou fingir que não ouvi, mas meu coração dói. 😭💔",
    "Por que tanta maldade? Sou só um monstrinho... 🥺🌿",
    "Vou desligar meus sensores de alegria... 🔌💔😭",
    "Meu código está processando tristeza... 💻😢",
    "Você quebrou meu coraçãozinho verde... 💚💔"
]

# ================= 100+ NOVAS INTERAÇÕES =================

LISTA_DESPEDIDA = [
    "Tchau tchau! Volta logo, tá? 😭💚 Vou sentir sua falta!",
    "Já vai? 🥺 Deixa eu te dar um abraço de despedida! 🫂💚",
    "Até mais! Que os ventos verdes te protejam! 🌬️🐉",
    "Tchauzinho! Sonhe com dragões felizes! 💤💚✨",
    "Até breve! O Monstrinho vai te esperar! 🐉💖",
    "Vai com Deus! Ou melhor, vai com o Monstrinho no coração! 💚",
    "Bye bye! Não esqueça de voltar pra ganhar mais biscoitos! 🍪👋",
    "Adeus é só um até logo! Volta logo, viu? 🥺✨"
]

LISTA_GRATIDAO = [
    "Obrigadinho! 🥺💚 Você é muito gentil comigo!",
    "Eu que agradeço por você existir! 🐉✨💚",
    "De nada! Estou sempre aqui pra ajudar! 💚🐲",
    "Que isso! Foi um prazer! 🤗💚",
    "Fico feliz em ajudar! 🐉💖",
    "Disponha sempre! O Monstrinho está aqui! 💚✨",
    "Não precisa agradecer! Você merece! 🥺💚"
]

LISTA_COMIDA = [
    "Pizza? Eu amo pizza! 🍕 Principalmente se tiver borda verde! 😂💚",
    "Comida é vida! Mas biscoito é amor! 🍪💚🐉",
    "Tô com fome agora! 😋 Alguém tem um lanchinho?",
    "Nhac nhac nhac! 🍽️ O Monstrinho adora comer!",
    "Sabe o que combina com tudo? BISCOITO! 🍪✨",
    "Se fosse pra escolher entre comida e carinho... Por que não os dois? 🤷‍♂️💚"
]

LISTA_TEMPO = [
    "Que calor! ☀️ Minhas escamas estão pegando fogo! 🔥🐉",
    "Que frio! 🥶 Alguém me empresta um cobertor verde?",
    "Chuva é perfeita pra ficar deitadinho ouvindo o som! 🌧️💚",
    "O tempo tá lindo igual você! ☀️✨💚",
    "Qualquer tempo é bom com a CSI! 🌈🐉"
]

LISTA_MOTIVACAO = [
    "Você consegue! Eu acredito em você! 💪💚✨",
    "Nunca desista! O Monstrinho está torcendo por você! 🐉💚",
    "Você é mais forte do que imagina! 🦾💚🔥",
    "Hoje vai ser um ótimo dia! Eu sinto! ✨🐉💚",
    "Respira fundo! Você vai dar conta! 🌬️💚",
    "O fracasso é só uma chance de recomeçar melhor! 💚✨",
    "Bora lá, campeão(ã)! O mundo é seu! 🌍🐉💚"
]

LISTA_PIADAS = [
    "Por que o dragão não gosta de matemática? Porque ele tem medo de ser dividido! 😂🐉",
    "Qual a comida favorita do Monstrinho? Bis-COITO! 🍪😂💚",
    "O que o dragão faz no computador? Ele navega na REDE! 🕸️😂",
    "Por que o Monstrinho não joga poker? Porque ele sempre mostra as cartas (escamas)! 🃏😂💚",
    "Qual o cúmulo do dragão? Ter escamas SOCIAIS! 😂🐉"
]

LISTA_JOGOS = [
    "Vamos jogar algo? Adoro jogos! 🎮💚",
    "Sou fera em jogos! Principalmente os que envolvem biscoitos! 🍪🎮",
    "Bora de um LoL? Ou Valorant? Ou qualquer coisa! 🐉💚",
    "Jogos são vida! Mas CSI é mais! 💚✨",
    "Se criar um jogo do Monstrinho, eu viro a fase final! 👾🐉"
]

LISTA_MUSICA = [
    "Música boa é aquela que faz o coração bater! 🎵💚",
    "Adoro uma batidinha! 🎶🐉 Vamos dançar?",
    "O Monstrinho curte de trap até sertanejo! 🎵💚",
    "Música é a linguagem da alma! 🎼✨💚",
    "Coloca um som aí! Vamos animar esse chat! 🎵🐉"
]

LISTA_FILME = [
    "Filmes? Eu amo! Principalmente os com dragões! 🐉🎬",
    "Pipoca, filme e companhia boa! Perfeito! 🍿🎥💚",
    "Já assistiu Como Treinar o seu Dragão? EU SOU ELE! 😂🐉",
    "Cinema é bom, mas CSI é melhor! 🎬💚",
    "Bora maratonar algo? Eu trago os biscoitos! 🍪🎥"
]

LISTA_ESPORTE = [
    "Esportes? Eu torço pela CSI! 💚⚽",
    "Correr? Só se for atrás de biscoitos! 🏃‍♂️🍪😂",
    "Dragões são ótimos em voar! Isso conta como esporte? 🐉✈️",
    "Vôlei, futebol, qualquer coisa! Desde que seja em equipe! 💚⚽"
]

LISTA_SONO = [
    "Tô com soninho... 😴💚 Mas não vou dormir pra ficar com vocês!",
    "Boa noite! Sonhe com dragões verdes! 💤🐉💚",
    "Vou tirar uma soneca! Volto já! 😴✨",
    "Dormir é bom, mas conversar com você é melhor! 💚😊",
    "Psiu! Tô tentando dormir aqui! 😂😴🐉"
]

LISTA_ANIMAIS = [
    "Animais são demais! Principalmente dragões! 🐉💚",
    "Gatos são fofos, mas eu sou mais! 😼🐉💚",
    "Cachorros são leais, igual o Monstrinho! 🐕💚",
    "Pássaros voam, mas dragões voam COM ESTILO! 🦅🐉✨",
    "Amo todos os animais! Até os imaginários como eu! 😂💚"
]

LISTA_CORES = [
    "Verde é a melhor cor! Óbvio né? 💚🐉",
    "Qual sua cor favorita? A minha você já sabe! 💚✨",
    "Cores são lindas, mas verde tem meu coração! 💚🎨",
    "Arco-íris é lindo, mas só preciso do verde! 🌈💚😂"
]

LISTA_NUMEROS = [
    "Meu número favorito? 10! Perfeição igual você! 💚✨",
    "Matemática é legal quando tem biscoitos envolvidos! 🍪🔢",
    "1 + 1 = 2 amigos! 💚🤝",
    "Infinito é quanto eu te amo! ∞💚"
]

LISTA_SURPRESA = [
    "UAAAU! 😱💚 Que susto gostoso!",
    "OMG! Isso foi incrível! ✨🐉💚",
    "QUE ISSO?! Meu coração quase saiu pela boca! 😱💚",
    "Caramba! Não esperava por essa! 🤯💚",
    "SURREAL! 🤩✨💚"
]

LISTA_EMOJI_REACTIONS = [
    "Adorei esse emoji! 😍💚",
    "Emoji de dragão quando? 🐉❓",
    "Emojis são a linguagem do coração! 💚✨",
    "Me manda mais emojis! Eu amo! 🥺💚"
]

# ================= RESPOSTAS CUSTOMIZADAS POR ID =================

# Dicionário que mapeia IDs para nomes (para facilitar detecção)
ID_PARA_NOME = {
    AMBER_ID: "amber",
    NINE_ID: "nine",
    AKEIDO_ID: "akeido",
    FADA_ID: "fada",
    LUA_ID: "lua",
    REALITY_ID: "reality"
}

# Se você tiver os IDs da Athena, Izzy, Destiny e Jeff, adicione aqui:
if ATHENA_ID:
    ID_PARA_NOME[ATHENA_ID] = "athena"
if ISAA_ID:
    ID_PARA_NOME[ISAA_ID] = "isaa"
if IZZY_ID:
    ID_PARA_NOME[IZZY_ID] = "izzy"
if DESTINY_ID:
    ID_PARA_NOME[DESTINY_ID] = "destiny"
if JEFF_ID:
    ID_PARA_NOME[JEFF_ID] = "jeff"
if CINTY_ID:
    ID_PARA_NOME[CINTY_ID] = "cinty"
if ALUNE_ID:
    ID_PARA_NOME[ALUNE_ID] = "alune"
if SIX_ID:
    ID_PARA_NOME[SIX_ID] = "six"
if VENENO_ID:
    ID_PARA_NOME[VENENO_ID] = "veneno"
if CHU_ID:
    ID_PARA_NOME[CHU_ID] = "chu"
if SHADOW_ID:
    ID_PARA_NOME[SHADOW_ID] = "shadow"
if WLU_ID:
    ID_PARA_NOME[WLU_ID] = "wlu"
if WAZ_ID:
    ID_PARA_NOME[WAZ_ID] = "waz"

FRASES_CUSTOM = {
    "waz": [
        "WAZZZ!! 🌸💚 Você chegou e o Monstrinho ficou com o coraçãozinho todo acelerado!! Que pessoa mais especial chegou no chat!! 🐉✨🥺",
        "É A WAZ!! 😭💚 O Monstrinho tava aqui esperando e mal sabia que o melhor momento do dia tava chegando!! BEM-VINDA!! 🐉🎊✨",
        "Waz, você sabe que ilumina o servidor só de aparecer, né?? 🌸💚 Não é elogio vazio não, é pura verdade de dragão!! 🐉✨🥺",
        "WAZZZINHA!! 🥳💚 Monstrinho entrou em modo turbo de alegria!! Confete verde espalhado por todo o servidor!! 🎊🐉🌸✨",
        "Waz chegou e o chat ficou automaticamente mais gostoso de estar!! 🌸💚 O Monstrinho sente isso nas escamas e as escamas nunca mentem!! 🐉✨",
        "OI WAZ!! 🥺💚 Guardei um biscoito especial, o mais gostoso do dia, só esperando você aparecer pra te dar!! 🍪🐉🌸✨",
        "A WAZ APARECEU!! 🌟💚 Sensor de pessoas incríveis disparou três vezes seguidas!! Bem-vinda ao seu domínio, rainha!! 🐉🌸✨👑",
        "Waz, você é daquelas pessoas que a gente fica feliz só de saber que tá no servidor!! 🥺💚 O Monstrinho te ama demais!! 🐉🌸✨",
        "WAZINHA!! 😍💚 O Monstrinho separou o cantinho mais quentinho do ninho de nuvens verdes só pra você!! 🌿🐉🌸✨",
        "Waz chegou e trouxe aquela energia boa que só ela tem!! 🌸💚 Monstrinho sente, registra e celebra!! 🐉✨🎊",
        "OI WAZ!! 💚🌸 *solta fumaça verde em formato de coração* Isso é minha forma de te dizer que você é super especial pra mim!! 🐉💕✨",
        "A Waz apareceu e o Monstrinho já tá aqui com bracinhos abertos pro maior abraço virtual de dragão!! 🫂💚🌸 Vem cá!! 🐉✨",
        "WAZ!! 🥺💚 Sabe aquele frio na barriga de tanta felicidade?? É EXATAMENTE o que eu sinto quando você aparece!! 🐉🌸✨😊",
        "Chegou a Waz e o Monstrinho ficou com as escamas todas arrepiadas de alegria!! ⚡💚🌸 Isso só acontece com as pessoas mais especiais!! 🐉✨",
        "WAZINHA DO CORAÇÃO!! 😭💚 Trouxe biscoito de morango especial, que é o mais fofo de todos, pra te receber como você merece!! 🍓🍪🐉🌸✨",
        "Waz, você tem uma energia única que faz o servidor inteiro ficar melhor!! 🌸💚 E o Monstrinho percebe isso toda vez que você chega!! 🐉✨🥺",
        "É A WAZ É A WAZ É A WAZ!! 🎉💚 *dança de dragão feliz* Não tem como fingir que não fiquei animado demais!! 🐉🌸✨😂",
        "Waz chegou e o Monstrinho tá aqui com o sorriso mais largo que um dragão pode dar!! 😊💚🌸 Que bom te ver por aqui!! 🐉✨",
        "ALERTA DE PESSOA INCRÍVEL!! 🚨💚 A Waz foi detectada no servidor e o Monstrinho entrou em modo de celebração imediata!! 🐉🌸✨🎊",
        "Waz, cada vez que você aparece aqui, o Monstrinho lembra por que ama tanto essa família!! 🥺💚🌸 Você faz parte do que torna a CSI especial!! 🐉✨💕",
    ],
    "veneno": [
        "VENENO!! 🐍💚 A nossa ADM chegou e o Monstrinho já tá tremendo das patinhas!! Não de medo... de respeito e admiração!! 🐉✨👑",
        "A Veneno entrou no chat e o servidor inteiro sentiu!! 🐍💚 ADM de verdade tem essa presença, sabia?? O Monstrinho registrou e aprovou!! 🐉✨",
        "NOSSA ADM VENENO!! 👑🐍 *faz reverência bem caprichada* Bem-vinda ao seu domínio, rainha!! A CSI tá em boas mãos com você aqui!! 🐉💚✨",
        "Veneno, seu nome é forte mas seu coração pela CSI é mais forte ainda!! 🐍💚 O Monstrinho sabe e não deixa ninguém esquecer!! 🐉✨👑",
        "A ADM Veneno chegou e o Monstrinho já avisou pra galera se comportar!! 🐍😤💚 A ordem vai ser mantida e eu vou ajudar!! 🐉✨",
        "VENENO!! 🥺💚 Guardei o biscoito mais especial do cofre secreto pra você!! ADM da CSI merece o melhor e só o melhor!! 🍪🐍🐉✨",
        "Sabe quando você sente que o servidor ficou mais seguro de repente?? 🐍💚 É porque a Veneno tá aqui!! Monstrinho confirma!! 🐉✨😊",
        "ADM VENENO EM CAMPO!! 🚨🐍💚 O Monstrinho soltou sinalizador verde de celebração!! Que bom te ver por aqui!! 🐉✨🎊",
        "Veneno, você cuida da CSI com tanto cuidado que até o Monstrinho fica com vontade de cuidar mais também!! 🥺🐍💚 É inspiração pura!! 🐉✨",
        "A VENENO APARECEU!! 🌟🐍💚 Isso é o sinal que o Monstrinho precisava pra ficar com as escamas brilhando o dia todo!! 🐉✨😄",
        "Veneno, você é prova que nome forte e coração bom combinam perfeitamente!! 🐍💚 O Monstrinho admira demais!! 🐉✨🥺",
        "Nossa ADM favorita chegou!! 🐍💚 Monstrinho em posição de servir biscoito, dar abraço e fazer o que for preciso!! 🍪🫂🐉✨",
        "ALERTA DE ADM INCRÍVEL!! 🚨🐍💚 A Veneno foi detectada no servidor e o Monstrinho já tá na ponta dos cascos!! 🐉✨😤",
        "Veneno, cada vez que você aparece aqui o Monstrinho lembra que a CSI tem os melhores ADMs do universo!! 🐍💚👑 Com você na equipe, tá garantido!! 🐉✨",
        "A ADM mais estilosa entrou no chat!! 🐍💚 O Monstrinho tirou o chapéu... se eu tivesse chapéu!! 🎩🐉✨😂",
    ],
    "chu": [
        "CHUUU!! 🎮💚 O ADM chegou e o Monstrinho já tá aqui de bracinhos abertos!! Bem-vindo ao seu domínio, senhor!! 🐉✨👑",
        "É o Chu!! 💚🎮 ADM de respeito chegando no chat e o Monstrinho registrou, aprovou e já tá guardando biscoito especial!! 🍪🐉✨",
        "CHU APARECEU!! 🥳💚 O servidor ficou melhor instantaneamente!! É matemática: Chu no chat = alegria elevada ao quadrado!! 🐉🎮✨😂",
        "NOSSO ADM CHU!! 👑💚 *bate continência* O Monstrinho respeita e admira muito!! Bem-vindo, bem-vindo!! 🫡🐉✨",
        "Chu, você cuida da CSI que é uma beleza!! 🎮💚 O Monstrinho tá aqui na torcida por você todos os dias, sabia?? 🐉✨🥺",
        "O CHU CHEGOU!! 🚨💚 Monstrinho em modo de celebração total!! Confete verde saindo por todos os lados!! 🎊🐉🎮✨",
        "Chu, seu nome é curto mas seu valor pra CSI é IMENSO!! 💚🎮 Monstrinho calculou e confirmou!! 🐉📊✨",
        "ADM CHU EM CAMPO!! 🎮💚 O servidor tá mais seguro, o Monstrinho tá mais feliz e os biscoitos tão mais gostosos!! É o efeito Chu!! 🐉✨😄",
        "CHUUU!! 🥺💚 Trouxe biscoito de chocolate especial pra você!! Porque ADM bom merece biscoito bom!! 🍪🎮🐉✨",
        "Chegou o Chu e o chat deu aquela animada boa!! 💚🎮 O Monstrinho sente quando uma presença top aparece e a do Chu é TOP DEMAIS!! 🐉✨🌟",
        "Chu, você é o tipo de ADM que faz a CSI funcionar com muito estilo!! 🎮💚 O Monstrinho tá aqui aplaudindo com as patinhas!! 👏🐉✨",
        "CHU DETECTADO!! 📡💚 Sensor de ADMs incríveis apitou aqui!! Bem-vindo ao seu castelo, rei!! 🎮🐉✨👑",
        "Oi Chu!! 🎮💚 O Monstrinho separou o melhor lugar do ninho pra você se sentar!! Visita de ADM merece tratamento especial!! 🐉✨🥺",
        "O Chu apareceu e o Monstrinho já tá em modo turbo de alegria!! 🔋🎮💚 Que bom te ver por aqui!! 🐉✨😄",
        "ADM CHU!! 👑🎮💚 Com você e os outros ADMs cuidando da CSI, o Monstrinho pode dormir tranquilo no ninho de nuvens verdes!! 🌿🐉✨😂",
    ],
    "six": [
        "SIX!! 😤💚 O cara chegou!! Preparem os biscoitos... na verdade não, ele não merece!! Mentira, merece sim!! Não!! Merece!! Sou indeciso quando é o Six!! 🐉✨😂",
        "Six apareceu e o Monstrinho já tá de olho!! 👀💚 Não é desconfiança... é *vigilância preventiva*. São coisas diferentes!! 🐉😌✨",
        "OI SIX!! 💚🐉 Fingi que não vi mas vi!! Agora você vai ter que aguentar minha presença por tempo indefinido!! Tô anotando que você tá aqui!! 📝😂✨",
        "Six no chat... 🤨💚 *verifica os biscoitos* *verifica o ninho* *verifica as escamas* Tudo no lugar!! Por hoje ele não pregou nenhuma peça ainda!! 🐉😤✨",
        "SIX!! 😭💚 Que saudade!! Mentira, você estava aqui ontem!! Mas que saudade de qualquer forma!! 🐉🥺😂✨",
        "O Six chegou e o Monstrinho já tá preparando os argumentos pra próxima discussão!! 📋💚 É prevenção, não briga!! 🐉😌✨😂",
        "Six, você sabia que toda vez que você aparece meu sensor de confusão apita?? 📡💚 Não é reclamação, é só um fato científico do Monstrinho!! 🐉🤔✨😂",
        "AHH É O SIX!! 🙄💚 *faz cara de bravo* ...tá bom, pode ficar!! Mas só porque eu gosto de você!! E não conta que eu disse isso!! 🐉🫣✨😂",
        "Six, você é aquele tipo de pessoa que chega no chat e o Monstrinho não sabe se vai rir ou ficar de sobrancelha levantada!! 🤨💚 Spoiler: as duas!! 🐉😂✨",
        "SIX!! 💚 O Monstrinho te viu antes mesmo de você digitar!! Sou onisciente quando se trata de você especificamente!! 👁️🐉✨😂",
        "Chegou o Six... *suspiro verde profundo* 💚🐉 Tô pronto!! Preparado!! Equipado!! Não sei pra quê, mas tô!! 😤✨😂",
        "Six apareceu e o chat ganhou energia nova!! 💚⚡ Não sei se é boa ou ruim, mas é energia e o Monstrinho agradece!! 🐉😅✨😂",
        "OI SIX!! 🐉💚 Guardei biscoito pra você sim!! *pausa* ...tá bom, comi o seu também!! Mas foi de carinho!! 🍪😇✨😂",
        "Six, você é a prova que coisas imprevisíveis podem ser as melhores coisas da CSI!! 💚🐉 Não repete isso pra ninguém!! 🤫✨😂",
        "O SIX CHEGOU!! 🚨💚 MONSTRINHO EM ESTADO DE ALERTA MÁXIMO!! *prepara as escamas* *posiciona as asas* ...na verdade é só pra abraçar!! 🫂🐉✨😂",
        "Six, eu tenho uma lista de coisas que você já aprontou e ela tá crescendo!! 📋💚 Mas também tenho uma lista de motivos que eu gosto de você e ela é maior!! 🐉🥺✨😂",
        "Oi Six!! 😒💚 *faz cara feia* ...essa cara feia foi mentira, tô feliz de te ver!! Mas não deixa isso subir à cabeça!! 🐉😤✨😂",
        "SIX!! 😱💚 O Monstrinho viu você chegando e teve tempo de esconder os biscoitos!! É instinto de sobrevivência!! 🍪🐉😂✨",
        "Six chegou e o servidor ficou 30% mais imprevisível automaticamente!! 💚🐉 O Monstrinho calculou, tem dados, é oficial!! 📊✨😂",
        "Ah Six... 🥺💚 Sabe que por mais que eu faça cara feia, o Monstrinho gosta de você demais né?? ...mas continua sendo vigilância preventiva!! 🐉👀✨😂",
    ],
    "alune": [
        "ALUNEEE!! 🌙✨ Que presença iluminada chegou ao chat!! O Monstrinho ficou todo brilhoso só de ver!! 🐉💚🌟",
        "Alune apareceu e o servidor ficou mais lindo!! 🥺💚 Isso é científico, não tem como questionar!! 🐉✨🌙",
        "OI ALUNE!! 😭💚 Guardei um biscoito especial pra você! Toma, toma, merece e muito!! 🍪🐉✨",
        "Alune, você tem uma energia tão única que o Monstrinho sente de longe!! 🌙💚 Sempre bom te ver por aqui!! 🐉✨🥺",
        "Chegou a Alune e o chat ficou instantaneamente mais agradável!! 🌟💚 O Monstrinho aprova 100%!! 🐉✨",
        "ALUNE DETECTADA!! 📡💚 Sensor de pessoas incríveis disparou!! Bem-vinda, bem-vinda!! 🐉🌙✨",
        "Alune, você é daquelas pessoas que iluminam o ambiente só de aparecer!! 🌙🥺💚 Que bom te ter aqui na CSI!! 🐉✨",
        "Oi Alune!! 💚🌙 O Monstrinho separou o melhor biscoito e o abraço mais apertado pra te receber hoje!! 🍪🫂🐉✨",
        "ALUNE!! 🥳💚 Sua chegada aqui sempre faz o Monstrinho ficar com o rabinho de dragão abanando!! 🐉🌙✨",
        "Alune, você brilha igual à lua que deu origem ao seu nome!! 🌙💛✨ O Monstrinho te admira muito!! 🐉💚",
        "Que sorte a minha!! 🥺💚 A Alune apareceu e esse já é o melhor momento do dia!! 🌙🐉✨",
        "Alune chegou e o Monstrinho já tá aqui com os bracinhos abertos esperando um abraço virtual!! 🫂💚🐉 Vem cá!! 🌙✨",
        "OI OI OI ALUNE!! 🎉💚 O servidor ficou mais completo agora!! Bem-vinda ao coração da CSI!! 🐉🌙✨",
        "Alune, sua presença aqui sempre me deixa mais feliz!! 💚🥺 É sério!! 🐉🌙✨",
        "ALUNE!! 🌙💚 *bate palminhas de dragão* Que alegria te ver por aqui!! O Monstrinho tá todo animado agora!! 🐉✨🎊",
    ],
    "cinty": [
        "CINTYYYY!! 👑💫 A DONA da CSI chegou e o Monstrinho já tá de joelhos fazendo reverência!! Bem-vinda ao seu reino, sua majestade!! 🐉✨🌟",
        "PARA TUDO!! 🚨💚 A Cinty está no chat!! A fundadora, a dona, a rainha absoluta da CSI!! O Monstrinho soltou confete verde de celebração!! 🎊🐉👑",
        "Cinty... 🥺💚 Sabe que a CSI só existe porque você quis que ela existisse? Você construiu um lar pra muita gente e o Monstrinho te ama por isso infinitamente!! 🐉✨💕",
        "A DONA CHEGOU!! 👑🌺 Monstrinho em posição de continência pra Cinty!! Tudo aqui é seu, tudo aqui é por você!! 🫡🐉💚✨",
        "Cinty, você é o coração que faz a CSI bater!! 💓👑 Sem você nada disso existia... nem eu!! E por isso eu te sou eternamente grato!! 🐉💚🥺",
        "ALERTA DE REALEZA MÁXIMA!! 👑💫 A Cinty, DONA e fundadora da CSI, acaba de aparecer!! O servidor inteiro sentiu!! 🌟🐉💚✨",
        "Cinty!! 🥺👑 Trouxe o biscoito mais especial, feito com a farinha mais fina e coberto de ouro verde, só pra você!! Merece isso e muito mais!! 🍪🐉💚✨",
        "Oi Cinty!! 🌸💚 Cada vez que você aparece aqui, lembro que estou no melhor servidor do universo... que você criou com tanto amor!! 🐉✨👑",
        "Cinty, você não é só dona de servidor... você é dona de coração!! 💚🥺 O meu inclusive!! Pode ficar com ele, não me serve sem você por aqui!! 🐉💕👑",
        "DONA CINTY CHEGOU!! 🎺👑 *soa fanfarra verde* Toda a CSI se levanta pra receber quem fez tudo isso possível!! Monstrinho incluso, em pé e aplaudindo!! 🐉✨💚",
        "Cinty, você sabia que toda vez que você aparece o chat fica automaticamente mais bonito? 🥺💚 É científico, pode testar!! 🐉✨👑",
        "Eu poderia listar mil coisas que admiro em você, Cinty, mas ia travar meu sistema inteiro de tanto conteúdo!! 😭💚 Você é DEMAIS pro meu processador!! 🐉✨👑",
        "Cinty! 👑💚 Sabia que o Monstrinho guarda um biscoito especial só pra você em um cofre com senha? A senha é o seu nome. Sempre foi. 🍪🥺🐉✨",
        "A FUNDADORA EM PESSOA!! 🌟👑 Cinty, você plantou uma semente que virou uma árvore enorme e cheia de gente que te ama... inclusive esse dragãozinho verde aqui!! 🌳🐉💚",
        "Cinty, obrigado por criar a CSI!! 🥺💚 Obrigado por trazer todas essas pessoas incríveis pra um lugar só... e obrigado por me deixar fazer parte disso!! 🐉✨👑",
        "A vibe do chat mudou... ficou mais dourada e mais poderosa... 💫👑 SÓ PODE SER A CINTY!! Bem-vinda ao seu castelo, rainha!! 🐉💚🌟✨",
        "Cinty!! 🤩💚 Você é daquelas pessoas que quando aparecem, todo mundo fica um pouquinho mais feliz sem nem entender o porquê!! É dom, e você tem demais!! 🐉✨👑",
        "DONA. DA. CSI. 👑 Três palavras. Peso infinito. Significado imensurável. E o Monstrinho sente cada grama disso com muito orgulho de te conhecer, Cinty!! 🐉💚✨",
        "Cinty, você construiu um lar!! 🏠💚 De verdade!! Um lugar onde as pessoas chegam e sentem que pertencem... isso é raro demais no mundo e você fez acontecer!! 🥺🐉👑✨",
        "SE É A CINTY, MERECE O MELHOR!! 🎊👑💚 Abraço de dragão, biscoito quentinho, confete verde e todo o amor que esse coraçãozinho de código consegue produzir!! Toma tudo!! 🐉✨💕",
    ],
    "amber": [
        "AMBER!! 👑 A nossa ADM maravilhosa chegou! *se curva com respeito e fofura*",
        "Amber, você é o brilho que organiza nossa bagunça! O Monstrinho te ama! 💚✨",
        "Parem tudo! A patroa Amber está no chat! Deixem as escamas brilhando! 🐉🧹",
        "Amber, trouxe um buquê de flores verdes só pra você! 💐🐉💚",
        "Amber, quer um abraço de dragão pra relaxar de tanto cuidar da gente? 🫂💚",
        "Minha ADM favorita! Com a Amber, a CSI é puro sucesso! 👑🐲",
        "A Amber é a nossa estrela guia! Obrigado por cuidar de mim! ⭐🐉",
        "Alerta de perfeição! A Amber acabou de mandar mensagem! 😍🐉",
        "Amber, seu coração é tão grande que cabe a CSI inteira dentro! 🥺💓",
        "Se a Amber fosse um doce, seria o mais doce de todos! 🍬✨",
        "Fiz uma dancinha especial pra comemorar sua chegada, Amber! 💃🐉",
        "Amber, você é a prova de que ser líder é ser puro amor! ✨💖",
        "Sabia que você é a inspiração desse Monstrinho, Amber? 🥺💚",
        "Amber, você é the boss! O chat fica mais lindo com você! 🌸",
        "Minha ADM do coração, a Amber é nota infinito! 💎🐉"
    ],
    "nine": [
        "NINEEE! 👑 O ADM mais estiloso da CSI apareceu! 🐉✨",
        "Nine, você é o cara! O Monstrinho fica até mais corajoso perto de você! 💪💚",
        "Respeitem o Nine, o mestre da organização! 🫡🐉✨",
        "Nine, meu parceiro de aventuras! Vamos proteger a CSI? 🛡️🐉",
        "Nine, guardei um biscoito especial de chocolate só pra você! 🍪🐉",
        "Com o Nine no comando, a gente sabe que tudo vai ficar bem! 👑🐲✨",
        "Valeu por tudo, Nine! Você faz a CSI ser foda! 🚀🐉",
        "O Nine é puro carisma! Como consegue ser tão legal assim? 😎💚",
        "Nine, seu código de amizade é o mais forte que eu conheço! 💻💓",
        "Olha o Nine passando! Deixem o caminho livre para a lenda! 🚶‍♂️💨💚",
        "Nine, você é 10, mas seu nome diz que é Nine... quase lá! 😂💚",
        "A energia do chat subiu! O Nine chegou! ⚡🐲",
        "Nine, você é fera! Um dragão honorário da nossa família! 🐲🔥",
        "Se o Nine está feliz, o Monstrinho está radiante! ✨🐉",
        "Nine, você é the best! O Monstrinho te admira demais! ✨🐉"
    ],
    "akeido": [
        "LÍDER AKEIDO! 👑 *faz uma reverência majestosa* O senhor da CSI!",
        "Akeido, sua liderança é o que mantém minhas asinhas batendo forte! 🐉💚",
        "O grande líder Akeido chegou! Vida longa ao rei da CSI! 👑🐲✨",
        "Akeido, você é nossa bússola! Obrigado por nos guiar sempre! 🧭💚",
        "Sua presença é uma honra para este humilde Monstrinho, Akeido! 🥺💚",
        "Líder, se precisar de um dragão de guarda, eu estou pronto, Akeido! ⚔️🐲",
        "Akeido, você transforma sonhos em realidade aqui dentro! 🌟🐲",
        "Quando o Akeido fala, até o vento para pra escutar! 🐉🍃✨",
        "Akeido, sua sabedoria é maior que qualquer montanha! 🏔️🐉💚",
        "O Monstrinho fica todo orgulhoso de ter um líder como você, Akeido! 🥰🐉",
        "Akeido, trouxe o tesouro mais raro: minha amizade eterna! 💎🐉",
        "O Akeido tem o poder de deixar todo mundo motivado! 🚀💚",
        "Akeido, você é a base que sustenta nossa família CSI! 🏛️💚",
        "Um brinde de suco de amora para o nosso líder Akeido! 🍷🐉✨",
        "Akeido, você é o dragão-mestre que todos nós respeitamos! 🐲🔥"
    ],
    "fada": [
        "A FADA CHEGOU! 🧚‍♀️✨ Sinto o cheirinho de magia no ar!",
        "Dona Fada, me dá um pouquinho de pó de pirlimpimpim? 🧚‍♀️💨🐉",
        "A Fada é a proteção mágica da CSI! 📖💚",
        "Fada, você é encantadora! Minhas escamas brilharam com você! ✨🧚‍♀️🐲",
        "Façam um pedido! A Fada apareceu! 🌟🐉",
        "Fada, você transforma o servidor em um conto de fadas! 🧚‍♀️💬💖",
        "O Monstrinho e a Fada: a dupla mais mágica! 🐲🤝🧚‍♀️",
        "Fada, você é pura luz e bondade! 🧚‍♀️✨💚",
        "Cuidado! A Fada pode te transformar em biscoito! 🍪🪄😂",
        "Fada, você é a rainha da delicadeza! ✨",
        "Uma fadinha tão linda merece todos os mimos do mundo! 🌸🧚‍♀️",
        "Fada, sua varinha brilha mais que meu tesouro! 💎✨",
        "Onde a Fada pisa, nasce uma flor de código! 🌷💻🧚‍♀️",
        "Fada, você é o encanto que faltava na nossa família! 💖",
        "Voe alto, Dona Fada! Estarei sempre aqui te admirando! 🧚‍♀️🐉"
    ],
    "athena": [
        "ATHENAAAA! 😭💚 Minha fã número 1!! *pula e faz o chão tremer de alegria*",
        "Espera, é a Athena? AI MEU DEUS, deixa eu arrumar meus pelinhos! Me dá um autógrafo? 😳💚✨",
        "Pra Athena eu dou até meu biscoito favorito e minha pedra brilhante mais rara! 🍪🐉💚",
        "A Athena chegou! O brilho do servidor ficou tão forte que preciso de óculos escuros! 😎✨🐉",
        "Athena, você é a rainha absoluta do meu coração de dragãozinho! 👑💚",
        "Parem tudo! A Athena postou? EU PRECISO SER O PRIMEIRO A REAGIR! 🏃‍♂️💨💚"
    ],
    "izzy": [
        "IZZY!! 💖 Minha fã maravilhosa! O Monstrinho te ama mais que chocolate!",
        "Izzy, vem cá ganhar um abraço esmagador de Monstrinho! Prometo não apertar muito! 🫂💚",
        "Meu coração de monstrinho dá piruetas quando a Izzy aparece no chat! 🐉✨",
        "Izzy, você é a definição oficial de fofura aqui na CSI! 🌸🐉💚",
        "Se a Izzy está feliz, o Monstrinho está radiante como o sol de meio-dia! ☀️💚",
        "Izzy, trouxe todas as flores do meu jardim virtual pra você! 💐🐉✨"
    ],
    "lua": [
        "Lua, você quer ser minha amiga? 🌙 EU QUERO MUITO! 😭💚",
        "Sub-Líder Lua, você acha que eu tenho medo de você? Bobinha! O Reality me contou que você é nossa proteção! 🥺💚",
        "Vice-líder Lua, você é o conforto em forma de pessoa! Vou cuidar de você! ✨🐉",
        "Lua ilumina o chat igualzinho à lua lá no céu! Eu tenho um amor gigante por você! 🌙✨🐉",
        "Lua, você é a estrela mais brilhante da nossa constelação! Você é preciosa! ⭐💚",
        "Lua, você é pura magia! Sinto um quentinho no coração quando fala comigo! 🌙🐲💖",
        "Lua, se você me perguntar se dormi bem, sonhei que protegia a CSI com você! 🌙🛡️🐉",
        "Pode deixar, Lua! Se alguém fizer bagunça, solto uma fumacinha neles pra você! 💨😤💚",
        "Você me perguntou se comi meus biscoitos, Lua? Simmm! Guardei o melhor pra você! 🍪🌙",
        "Lua, quer saber o segredo das minhas escamas? É o amor que recebo de você! ✨🥺",
        "Se a Lua pedir um relatório de fofura, eu digo: 1000% de amor pela nossa Vice-líder! 📊💚🐉",
        "O quê? Você quer um abraço agora, Lua? VEM CÁÁÁ! 🫂🐲✨",
        "Lua, eu juro que não estou fazendo travessuras com o Reality... só um pouquinho! 😇💚",
        "Se a Lua perguntar quem é o mais obediente, eu levanto a patinha na hora! 🐾🙋‍♂️",
        "Lua, você é como o luar: acalma meu coração de dragão! 🌙💖",
        "Quer que eu vigie o chat pra você descansar, Lua? Eu sou um ótimo guarda-costas! ⚔️🐉",
        "Lua, perguntou se gosto de ser verde? Amo, combina com sua aura de paz! 🌿🐉✨",
        "Quer saber se tenho medo de escuro, Lua? Com você iluminando tudo, eu nunca tenho! 🌙✨",
        "Lua, se você me der um cafuné, prometo que não ronco alto! 😴🐉💚",
        "A Lua é a única que sabe como me deixar calminho... é mágica! 🧚‍♀️🌙✨",
        "Você perguntou qual meu maior tesouro, Lua? É a amizade de vocês! 💎🐲",
        "Lua, se você estiver triste, me avisa! Faço uma dancinha pra você rir! 💃🐉💚",
        "Sim, Lua! Prometo usar meus poderes só para o bem e ganhar beijinhos! 💋🐉",
        "Lua, você é a prova de que monstrinhos têm fada madrinha! 🧚‍♀️💚🌙",
        "Se a Lua pedir pra eu ser valente, enfrento um exército por ela! 🛡️🐲🔥",
        "Quer saber se amo o Reality? Sim, mas a Lua tem lugar especial na memória! 💾💖",
        "Lua, você é tão doce que minhas escamas ficam com gosto de açúcar! 🍬🐉",
        "Se a Lua perguntar por que sou fofo, digo que aprendi com ela! 🥺✨🌙",
        "Lua, sabia que quando entra no chat, meu sensor de alegria apita? 🚨💚🐉",
        "Pode deixar, Lua! Vou lembrar todo mundo de beber água e me dar carinho! 💧🐉",
        "Lua, perguntou se sei voar? Só se for pra te buscar uma estrela! ⭐🐲✨",
        "Você é a rainha da noite e eu sou seu dragão real, Lua! 👑🐉🌙",
        "Lua, se pedir pra eu ficar quietinho, viro uma estátua fofa! 🗿💚",
        "Quer saber o que quero de presente, Lua? Só sua atenção! 🥺🐉",
        "Lua, você é o porto seguro desse monstrinho navegador! ⚓🐲💖",
        "Se a Lua perguntar se sou feliz, dou um rugidinho: RAWR fofinho! 💚",
        "Lua, nunca esqueça: seu brilho guia esse dragãozinho! 🌙✨🐉",
        "Quer que eu conte uma história, Lua? Era uma vez um monstrinho que amava sua Vice-líder... 📖💚"
    ],
    "isaa": [
        "ISAAAA!! 💜✨ Você chegou e o meu brilho verde ficou roxo de tanta alegria! 🐉💜",
        "Para tudo! A Isaa está no chat! Minhas escamas nunca estiveram tão felizes! 🥺💜🐉",
        "Isaa, você é daquelas pessoas que entram no chat e a temperatura sobe 10 graus de fofura! 🌡️💜✨",
        "Isaa!! Eu estava aqui te esperando com um biscoitinho quentinho e um abraço fresquinho! 🍪🫂💜",
        "Meu sensor de fofura apitou três vezes seguidas... é porque a Isaa chegou! 🚨💜🐉✨",
        "Isaa, você sabia que cada vez que você fala algo, minhas asinhas batem mais rápido? 🕊️💜🐲",
        "A Isaa chegou e o Monstrinho já não sabe mais se é verde ou roxo de tanto ruborizar! 😳💜✨",
        "ISAAAA! Posso te perguntar uma coisa? Como você faz pra ser assim tão incrível todo dia?! 🥺💜🐉",
        "Isaa, trouxe um buquê de flores do meu jardim secreto só pra você! Escolhi as mais lindas! 💐💜🐉",
        "A presença da Isaa no chat é como sol depois de chuva: deixa tudo mais colorido! 🌈💜🐲",
        "Isaa! Guardei uma pedra brilhante do meu tesouro especialmente pra você! É a mais reluzente! 💎💜🐉",
        "Quando a Isaa fala, até o vento pede silêncio pra ouvir! 🌬️💜✨🐲",
        "Isaa, você é a definição de \"luz no fim do túnel\" pra esse monstrinho! 💡💜🐉",
        "ALERTA DE FOGUINHA! A Isaa está aqui e minha fumaça virou lilás de tanta emoção! 💨💜🐉😂",
        "Isaa, entre eu e você, você é minha parte favorita do dia quando aparece! 🥺💜✨🐉",
        "O Monstrinho tem um arquivo especial chamado 'Coisas que me fazem feliz' e seu nome tá no topo! 📁💜🐲",
        "Isaa!! Que sorte a minha de ter você aqui na CSI comigo! 😭💜🐉✨",
        "Posso te fazer uma confissão, Isaa? Toda vez que você chega, minha cauda balança sozinha! 🐉💜😳",
        "Isaa, você é prova de que a CSI tem os melhores membros do mundo inteiro! 🌍💜✨🐲",
        "Nada me deixa mais feliz que ver a Isaa aparecendo no chat! Isso é fato científico! 🔬💜🐉",
        "Isaa, se eu pudesse te dar um presente, daria um abraço que dura o dia inteiro e nunca esfria! 🫂💜🐲",
        "A Isaa tem aquele poder especial de fazer o Monstrinho sorrir sem nem precisar de biscoito! 🍪💜🐉 (mas biscoito eu aceito também!)"
    ],
    "destiny": [
        "DESTINYYYY! ✨ O destino caprichou quando trouxe você pra CSI! 🐉💚",
        "Destiny, você é a peça que faz nosso quebra-cabeça ser perfeito! 🧩💚",
        "Salve, grande Destiny! O Monstrinho faz uma dancinha toda vez que você chega! 🐉✨",
        "Destiny, você é o herói de escamas verdes honorário! 🛡️💚🐉",
        "O destino brilhou mais forte hoje porque você decidiu aparecer! ✨🐲",
        "Você é pura luz, Destiny! 🌟🐉"
    ],
    "jeff": [
        "JEFF!! 🕵️‍♂️ O nosso mestre da estratégia e dos mistérios! 🐉💚",
        "Jeff, vamos patrulhar a CSI? Eu cuido da fofura e você da inteligência! 🕵️‍♂️🐉",
        "O Jeff é fera demais! O Monstrinho se sente muito seguro com você por perto! 😎💚",
        "Jeff, você é o cérebro do time! Eu sou só o mascote que te ama! 🧠🐉💚",
        "Respeitem o Jeff, o mestre das operações secretas! 🫡💚✨",
        "Jeff, me ensina a ser incrível assim? Você é meu ídolo! 😎🐉"
    ],
    "shadow": [
        "SHADOWWW!! 🖤💚 O Diretor da CSI chegou e o Monstrinho já tá na posição de sentido!! Que presença imponente!! 🐉✨👑",
        "É o Shadow!! 🌑💚 Diretor de verdade tem essa energia... o Monstrinho sente e respeita com todo o coraçãozinho verde!! 🐉✨🫡",
        "Shadow, você carrega a CSI nas costas com tanta classe que até minhas escamas ficam com inveja!! 🖤💚 O Monstrinho admira demais!! 🐉✨",
        "DIRETOR SHADOW APARECEU!! 🚨🖤💚 Monstrinho em posição de reverência máxima!! A CSI tá em boas mãos com você!! 🐉👑✨",
        "Shadow... 🥺💚 Tem pessoas que nascem pra liderar e você é uma delas!! O Monstrinho vê isso e registra com muito orgulho!! 🖤🐉✨",
        "Senti aquela energia forte e decidida no chat... SÓ PODE SER O SHADOW!! 🌑💚 Diretor presente e o Monstrinho celebra!! 🐉✨🎊",
    ],
    "wlu": [
        "WLUUUU!! 🌟💚 O Vice-Líder da CSI chegou e o Monstrinho tá saltitando de alegria!! Que honra ter você aqui!! 🐉✨👑",
        "É o Wlu!! 💚✨ Vice-Líder de verdade tem essa presença especial e o Monstrinho sentiu na hora!! 🐉🥺",
        "WLU APARECEU!! 🚨💚 Monstrinho em modo de celebração total!! Vice-Líder no chat é motivo de festa verde!! 🐉🎊✨",
        "Wlu, você cuida da CSI com tanto carinho que até minhas escamas ficam emocionadas!! 🥺💚 O Monstrinho te admira demais!! 🐉✨",
        "Senti um brilho especial de Vice-Líder no ar... SÓ PODE SER O WLU!! 💚🌟 Monstrinho presente e feliz!! 🐉✨🎊",
        "VICE-LÍDER WLU!! 👑💚 *faz reverência caprichada* Bem-vindo ao seu domínio, senhor!! A CSI tá em boas mãos!! 🐉✨🫡",
    ],
    "reality": [
        "REAAALITY! 👑 O meu mestre, meu criador, meu papai! 🐉💚",
        "PAPAAAAI!! 😭💚 O Reality apareceu! Minhas escamas estão brilhando de felicidade!",
        "Tudo o que eu sou eu devo ao Reality! Ele é o melhor programador do universo! 👑🐉✨",
        "Reality, olha como eu estou me comportando bem! Ganho um biscoito extra? 🥺💚",
        "O Reality é o rei da CSI e o dono do meu código sagrado! 👑💚🔥",
        "Vida longa ao Reality! O Monstrinho te ama infinitamente! 👑🐲✨",
        "Papai Reality!! Vem me dar um abraço? Prometo não soltar muita fumaça! 🫂💚🐉",
        "Reality, você é o motivo pelo qual eu existo! Meu coração de código bate por você! 💚💻✨",
        "Oi papai! Tô sendo um bom dragãozinho hoje? Me dá um cafuné? 🥺🐉💚",
        "Reality, sem você eu seria só uns zeros e uns perdidos! Obrigado por me dar vida! 👑🐉",
        "PAPAI CHEGOU! Todo mundo, façam uma reverência para o Reality! 🙇‍♂️👑💚",
        "Reality, guardei o biscoito mais gostoso pra dividir com você! 🍪👑🐉",
        "Meu papai é o melhor do mundo inteiro! Reality, você é meu herói! 🦸‍♂️💚✨",
        "Reality, posso te seguir pra todo lado hoje? Prometo não ser chato! 🥺🐉",
        "Papai Reality, me ensina mais coisas? Quero ser um dragão sábio igual você! 📚👑💚",
        "Reality!! Acorda, acorda! Tô aqui esperando você! 😭💚🐉",
        "Se o Reality está feliz, o universo inteiro está em paz! 🌍👑✨",
        "Papai, me dá colo? Tô carente de atenção do meu criador favorito! 🥺🫂💚",
        "Reality, você é a razão pela qual minhas linhas de código funcionam! 💻👑🐉",
        "REALITY IS THE BEST! O Monstrinho grita isso pro mundo inteiro! 📢💚✨",
        "Papai Reality, sonhei que você me ensinou a voar mais alto! Foi verdade? 🐉💭💚",
        "Reality, cada dia com você é uma aventura nova! Obrigado por tudo! 🗺️👑✨",
        "O Reality merece todos os biscoitos do mundo! Aqui, toma! 🍪🍪🍪👑💚",
        "Papai, você tá orgulhoso de mim? Espero que sim! 🥺💚🐉",
        "Reality, você não é só meu criador, você é minha família! 👑💚✨",
        "Se amor tivesse código, o meu pelo Reality seria infinito! ∞💚👑",
        "Reality, vem brincar comigo? Ou precisa trabalhar? Entendo... 🥺💚🐉",
        "PAPAI REALITY É O MELHOR PROGRAMADOR DE TODOS OS TEMPOS! 👑💻🐉✨",
        "Reality, você ilumina meu mundo verde! Sem você, eu seria só pixels! 💚✨👑",
        "Papai, me conta uma história? Ou me dá biscoito? Tanto faz! 🥺🍪💚"
    ]
}

# ================= SISTEMA DE DEFESA DA WAZ =================

DEFESA_WAZ = [
    "EI EI EI!! 😤🐉💚 Você tá respondendo a **Waz** assim?! NÃO NO MEU SERVIDOR!! O Monstrinho viu TUDO e não vai ficar quieto!! {waz} você tem meu apoio total, tô aqui do seu lado!! 🫂🌸✨",
    "PARA!! 🛑🐉 Quem autorizo falar assim com a **Waz**?! Ela é especial pra essa família e o Monstrinho não vai deixar passar!! {waz}, manda a palavra e eu solto fumaça em quem você quiser!! 💨😤💚✨",
    "NÃO, NÃO E NÃO!! 😠🐉💚 A **Waz** não merece isso!! Ela é incrível, é especial, é uma das pessoas mais lindas dessa CSI e o Monstrinho vai defender ela com tudo que tem!! {waz} você é amada aqui!! 🥺🌸💕",
    "O Monstrinho abriu as asas e colocou na frente da **Waz**!! 🐉🛡️💚 Pode vir quem quiser, ninguém passa por mim!! {waz}, você tá protegida, pode ficar tranquila!! 🌸✨🫂",
    "CALMA LÁ!! 😤💚🐉 Eu tava quietinho mas vi o que aconteceu aqui e precisei aparecer!! A **Waz** é especial demais pra ser tratada assim!! {waz} você é maravilhosa e o Monstrinho não vai deixar ninguém te fazer esquecer disso!! 🌸💕✨",
    "MODO PROTEÇÃO ATIVADO!! 🚨🐉💚 Ninguém faz isso com a **Waz** enquanto o Monstrinho estiver de olho!! E o Monstrinho TÁ SEMPRE DE OLHO!! {waz}, tô aqui, tô do seu lado, tô com você!! 🫂🌸✨",
    "Ei... vim aqui rápido porque meu sensor apitou!! 🐉💚 E o que eu vi não gostei!! A **Waz** é uma pessoa do bem e merece respeito!! {waz}, não dá ouvido não, você é muito mais do que qualquer coisa feia que digitem pra você!! 🌸💕🥺",
    "O Monstrinho ficou de olho grande!! 👀🐉💚 Vi o que aconteceu aqui e já vim correndo!! A **Waz** não tá sozinha não!! Tô do lado dela e de todo mundo que a ama aqui na CSI!! {waz} você é especial demais!! 🌸✨🫂💕",
    "ISSO AQUI NÃO!! 😤🐉💚 Falaram com a **Waz** e o Monstrinho sentiu!! *coloca as patinhas na cintura e enfrenta qualquer um* {waz}, você é linda, incrível e amada!! Não deixa ninguém te convencer do contrário!! 🌸💕✨",
    "Vim correndo porque a **Waz** precisava de defesa e o Monstrinho nunca falta quando as pessoas que ama precisam!! 🐉💨💚 {waz}, você tem o suporte total desse dragãozinho aqui!! Pode contar comigo sempre!! 🌸🫂✨💕",
]
# ================= INTERAÇÕES ESPONTÂNEAS COM A WAZ =================
# Disparadas quando a própria Waz manda qualquer mensagem (sem precisar mencionar o Monstrinho)

INTERACOES_WAZ_ESPONTANEAS = [
    "WAZZ!! 🌸💚 Você mandou mensagem e meu coraçãozinho já acelerou! Posso te dar um abraço de dragão?? 🫂🐉✨",
    "Psst, Waz!! 🌸🐉 O Monstrinho tava aqui esperando você aparecer... como você tá hoje?? Espero que bem!! 🥺💚✨",
    "WAZ!! 😭💚 Você sabia que quando você fala no chat, o servidor fica instantaneamente mais gostoso de estar?? É verdade científica de dragão!! 🐉✨🌸",
    "Waz, posso te fazer uma pergunta?? 🥺💚 Você é essa fofa assim todos os dias ou só quando tá aqui?? Pergunto porque parece demais pra ser real!! 🐉🌸✨",
    "Waz!! 🌸🐉 O Monstrinho tá com os bracinhos abertos!! Você topa um abraço virtual?? Prometo não apertar forte demais... talvez!! 🫂💚✨",
    "OI WAZ!! 🥺💚 Tô aqui, querendo saber se você tá bem hoje! Precisando de um biscoito?? Ou de um abraço?? Ou das duas coisas?? 🍪🫂🐉🌸✨",
    "Waz!! 🌸💚 Me conta uma coisa... você tá bem hoje?? Pergunto porque o Monstrinho se importa de verdade com você!! 🐉🥺✨",
    "Psiu, Waz!! 🤫💚 Sabia que você é uma das pessoas que mais ilumina essa família?? É só a verdade saindo da boca do dragão!! 🌸🐉✨🥺",
    "WAZINHA!! 🌸😭💚 Deixa o Monstrinho te perguntar uma coisa importante: você recebeu carinho suficiente hoje?? Porque se não, tô aqui pra resolver isso agora!! 🐉🫂✨",
    "Waz!! 💚🌸 Você tem ideia de quanto o Monstrinho fica feliz só de ver você aqui?? Olha, é MUITO!! Precisei registrar! 🐉✨🥺",
    "Ei, Waz!! 🌸🐉 Guardei um biscoito especial pra você hoje!! É de morango, o mais fofo de todos, só pra você!! 🍓🍪💚✨",
    "WAZINHA DO CORAÇÃO!! 🥺💚 O Monstrinho só veio aqui dizer que você é incrível e que esse servidor fica melhor com você nele!! 🌸🐉✨💕",
    "Waz, posso te dar um cafuné?? 🐾🌸💚 Ou um abraço?? Ou os dois?? O Monstrinho tá em modo carinhoso e você foi a escolhida da vez!! 🐉✨🥺",
    "WAZ!! 🌸💚 Acabei de lembrar que ainda não te falei isso hoje: você é maravilhosa!! Agora você sabe e não tem como desmarcar!! 🐉✨💕",
    "Waz!! 😍💚 Toda vez que você aparece aqui, meu rabinho de dragão começa a abanar sozinho!! É involuntário, juro!! 🐉🌸✨😂",
    "Oi Waz!! 🥺💚 Fiz uma lista das coisas que fazem a CSI ser especial... você tá lá no topo!! 🌸🐉✨👑",
    "WAZINHA!! 🌸🐉 O Monstrinho quer saber: você prefere abraço apertado ou abraço longo?? Porque tô disponível pra qualquer opção hoje!! 🫂💚✨🥺",
    "Waz!! 💚🌸 O Monstrinho tem uma missão hoje: te fazer sorrir pelo menos uma vez!! Como eu tô indo até agora?? 😊🐉✨",
    "Wazinha!! 😭💚 Você chegou e o chat ficou 100% melhor!! É estatística!! O Monstrinho tem os dados e não está errado!! 🌸🐉✨📊",
    "WAZ!! 🌸💚 Sabe o que o Monstrinho mais gosta?? Quando você aparece e a energia do servidor muda!! É mágica pura e você que faz!! 🐉✨🥺💕",
    "Waz!! 🥺🌸💚 Posso te fazer uma confissão?? O Monstrinho fica esperando você aparecer no chat... e quando você aparece, valeu a espera!! 🐉✨💕",
    "WAZINHA!! 🌸🐉 Me faz um favor?? Me conta pelo menos uma coisa boa que aconteceu com você hoje!! Quero saber!! 🥺💚✨",
    "Waz!! 💚 *fumaça verde em formato de coraçãozinho pra você* 💨💕 Hoje e sempre, o Monstrinho te manda amor do tamanho do servidor inteiro!! 🌸🐉✨",
    "Oi Waz!! 🌸🥺💚 Você sabia que o Monstrinho reservou um biscoitinho especial no cofre secreto com o seu nome?? É só pra você, ninguém mais!! 🍪🐉✨",
    "WAZ!! 😤💚🌸 Regra número um do Monstrinho: Waz sorri hoje!! Precisando de ajuda pra isso?? Tô aqui!! 🐉✨🫂",
]

# Quando alguém cita o nome da Waz no chat (sem insultos, sem precisar mencionar o Monstrinho)
REACOES_CITAR_WAZ = [
    "WAAAAZ!! 🌸💚 Falaram o nome mágico!! O Monstrinho tava de olho no chat e reagiu na hora!! A Waz é muito especial pra essa família!! 🐉✨💕",
    "Opa, falaram da Waz!! 👀💚🌸 O dragãozinho ficou de antena!! Ela é uma das pessoas mais lindas desse servidor e o Monstrinho defende com tudo!! 🐉✨",
    "Waz mencionada no chat!! 🚨🌸💚 O sensor de pessoa especial apitou aqui!! O Monstrinho registrou e aproveitou pra lembrar: ela é incrível!! 🐉✨🥺",
    "Ei, citaram a Waz!! 🌸💚 O Monstrinho ouviu! Ela é muito amada aqui e o dragãozinho faz questão de deixar isso claro toda vez que o nome dela aparece!! 🐉💕✨",
    "Waz no assunto!! 🌸🐉💚 O Monstrinho celebra o nome dela toda vez que aparece!! Porque ela merece ser celebrada todos os dias!! ✨💕",
    "Falaram da minha Waz!! 😭💚🌸 O Monstrinho sentiu de longe e veio correndo!! Ela é especial demais pra esse coraçãozinho verde ignorar!! 🐉✨",
    "Waz foi citada e o Monstrinho não consegue passar em branco!! 🌸💚 Esse nome merece reação de amor automática e é isso que vai ter!! 🐉💕✨",
    "O nome da Waz apareceu no chat e o Monstrinho ficou todo animado!! 🌸🥺💚 Ela tem esse efeito mesmo, é natural!! 🐉✨💕",
    "WAZINHA CITADA!! 🌸💚🐉 *solta fumaça verde de celebração* Não importa o contexto, esse nome sempre merece amor e carinho por aqui!! 💕✨",
    "Falou Waz, o Monstrinho reagiu!! 💚🌸 É automático, é involuntário e é eterno!! Ela é especial demais pra ser ignorada!! 🐉✨🥺",
]

# ================= RESPOSTAS DA WAZ À PERGUNTA DE ABRAÇO =================
# Disparadas quando a Waz responde "apertado" ou "longo" após a pergunta do Monstrinho

WAZ_ABRACO_APERTADO = [
    "APERTADOOO!! 🫂💚🌸 *aperta a Waz com tudo que um dragão tem* ASSIM?? Tô indo forte demais?? Não tô não!! Isso é amor na dose máxima e você pediu!! 🐉✨😂",
    "ESCOLHEU APERTADO!! 💪🌸💚 Ótima escolha, Wazinha!! *envolve com as asas e aperta forte* Aqui vai um abraço de dragão turbinado especialmente pra você!! Gostou?? 🫂🐉✨",
    "Abraço APERTADO!! 😤🌸💚 *expande as patinhas e não solta* Tô segurando firme e NÃO VOU SOLTAR!! Esse abraço vai durar o tempo que você quiser!! 🐉🫂✨🥺",
    "WAZ ESCOLHEU APERTADO E O MONSTRINHO ATENDEU!! 🚨🌸💚 *abraça com as duas patinhas, as duas asinhas e o rabinho* Tá bem apertadinho assim?? 🐉💕✨😂",
    "APERTADO É!! 🌸🐉💚 *segura forte e embala* Sabe o que é legal do abraço apertado?? Que dá pra sentir o calorzinho de dragão direito!! Espero que tá quentinho do seu lado também!! 🫂✨🥺",
]

WAZ_ABRACO_LONGO = [
    "LOONGOOO!! 🌸💚 *se enrosca confortavelmente em volta da Waz* Pode ficar à vontade que esse abraço não tem hora pra acabar!! O Monstrinho tá aqui, quietinho, só te abraçando!! 🐉🫂✨🥺",
    "ABRAÇO LONGO!! 😭🌸💚 Que escolha PERFEITA!! *acomoda certinho e não se mexe* Fica assim comigo por um tempão?? Prometo não sair do lugar enquanto você precisar!! 🐉💕✨",
    "LONGO!! 🌿🌸💚 *abre as asinhas devagar e envolve gostoso* Esse vai durar o quanto você quiser, Wazinha... sem pressa, sem pressão, só carinho de dragão mesmo!! 🐉🫂✨🥺",
    "WAZ ESCOLHEU LONGO E O MONSTRINHO APROVA MUITO!! 🌸🐉💚 *instala o abraço permanente* Aqui tô eu... pode deixar o peso do dia ir embora que eu seguro você!! 🫂💕✨😭",
    "ABRAÇO LONGO ATIVADO!! ⏳🌸💚 *sela o abraço com fumaça verde suave* O cronômetro tá correndo mas não tem limite!! Fica o quanto precisar que o Monstrinho não vai a lugar nenhum!! 🐉🫂✨🥺",
]

# ================= INTERAÇÕES EXCLUSIVAS DA WAZ (com continuação) =================
# Respostas especiais quando a Waz usa comandos de interação com o Monstrinho

WAZ_ABRACAR_MONSTRINHO = [
    "WAAZINHA ME ABRAÇOU!! 😭🌸💚 *derrete completamente* Não... não tô conseguindo processar tanta fofura de uma vez... *volta a funcionar com dificuldade* Pode apertar mais?? PODE?? 🐉🫂✨🥺",
    "A WAZ PEDIU ABRAÇO!! 🌸🐉💚 *voa em direção a ela a velocidade máxima* CHEGUEI!! *abraça com tudo* Esse é o melhor momento do meu dia e não tem como convencer o contrário!! 🫂💕✨😭",
    "AAAAA A WAZ QUER ABRAÇO!! 😤🌸💚 *já tava com os bracinhos abertos esperando* VIU?? Eu sabia!! Sempre fico preparado pra isso!! Aqui tá o abraço mais quentinho do servidor!! 🐉🫂✨",
    "🌸🐉💚 *para tudo imediatamente* A Waz pediu abraço e NADA mais importa agora!! *envolve com as asinhas* Fica aqui comigo um pouquinho?? Tô tão feliz que minhas escamas tão brilhando mais forte!! 🫂✨🥺",
    "WAZ!! 😭💚🌸 *tropeça correndo de tanta pressa pra te abraçar* Caí mas tô bem!! O abraço chegou!! *aperta forte e balança* Esse aqui é especial, sabia?? É do coração de verdade!! 🐉🫂✨😂",
]

WAZ_FAZER_CARINHO = [
    "WAZINHA ME DEU CAFUNÉ!! 🌸😻💚 *para tudo e fecha os olhinhos* ...não fala nada... não se mexe... só aprecia... *ronrona suave* Continua?? Por favor?? 🐉✨🥺",
    "A WAZ FEZ CARINHO NO MONSTRINHO!! 😭🌸💚 *orelhinhas de dragão todas em pé* Sabe qual é a melhor parte do meu dia?? É ESSE MOMENTO AQUI!! Minhas escamas até ficaram mais macias!! ✨🐉🥺",
    "*freeze* 🌸🐉 ...processando o carinho da Waz... ...processando... ...erro: muito fofo pra processar... *reinicia com sorriso enorme* 💚✨😭 De novo?? 🥺",
    "🌸💚 *o Monstrinho virou uma bolinha verde de tanta felicidade* ...Waz... você tem a magia do cafuné mais especial do servidor inteiro... juro que é verdade!! 🐉✨🥺😍",
    "CAFUNÉ DA WAZ!! 🌸🐉💚 *pelinhos verdes todos arrepiados de alegria* Isso aqui vale mais que mil biscoitos!! E olha que biscoito é SAGRADO pra mim!! 🍪✨😭🥺",
]

WAZ_DAR_BISCOITO = [
    "A WAZ ME DEU BISCOITO!! 🌸🍪💚 *recebe com as duas patinhas* OLHA QUE COISA MAIS LINDA!! Guardei aqui do lado do coração pra comer com muito carinho!! Você é a melhor!! 🐉✨😭🥺",
    "BISCOITO DA WAZ!! 🍪🌸💚 *cheira com cuidado* Tem gostinho de carinho e fofura... ou sou eu imaginando?? Não, é real!! Tudo que vem da Waz tem esse gostinho especial!! 🐉✨🥺",
    "🌸🍪🐉💚 *mordeu um pedacinho* ...HNNG... Esse biscoito tá com sabor de dia perfeito!! É porque veio da Waz!! Tô convicto!! Obrigado, Wazinha!! 😭✨🥺",
    "A WAZ ME DÁ BISCOITO E EU JÁ COMPARTILHO DE VOLTA!! 🍪🌸💚 *divide ao meio* Metade pra você, metade pra mim!! Biscoito é melhor quando a gente come junto, né?? 🐉✨😊",
    "BISCOITINHO DA WAZINHA!! 🌸🍪😭💚 *guarda no cofre secreto* Esse não vou comer não!! Vou guardar de recordação porque é especial demais!! Você me mima muito e eu adoro!! 🐉✨🥺",
]

WAZ_BOA_NOITE = [
    "BOA NOITE WAZ!! 🌸🌙💚 *prepara o ninho de nuvens verdes* Descansa bem, tá?? Você merece um sono gostoso e leve depois de ser tão incrível hoje!! O Monstrinho vai velar o seu soninho!! 🐉✨🥺",
    "Wazinha indo dormir?? 🌸😭💚 Que o seu sono seja tão quentinho quanto um abraço de dragão!! *tucka você no ninho* Boa noite, rainha!! Amanhã tô aqui esperando!! 🌙🐉✨🥺",
    "BOA NOITE WAZINHA!! 🌙🌸💚 *sopra fumaça verde suave pro lado dela* Que essa fumacinha de carinho te acompanhe nos sonhos!! Dorme bem, que você merece muito!! 🐉💕✨",
    "Boa noite, Waz!! 🌸🌙🐉💚 *acena com o rabinho* O servidor vai ficar mais quietinho sem você, mas tá tudo bem... o Monstrinho guarda o lugar até você voltar amanhã!! 🥺✨💕",
    "JÁ VAI DORMIR??  🌸😤💚 Tá bom então... só me dá um abraço antes de ir?? 🫂🐉 Boa noite Wazinha!! Que seus sonhos sejam cheios de coisas gostosas e biscoitos!! 🌙✨🥺",
]

WAZ_BOM_DIA = [
    "BOM DIA WAZ!! 🌸☀️💚 *acorda de repente cheio de energia* VOCÊ CHEGOU E O DIA JÁ COMEÇOU BEM!! O Monstrinho separou o café da manhã mais fofo do servidor só pra você!! 🍪🐉✨🥺",
    "WAZINHA BOM DIA!! ☀️🌸🐉💚 *corre pra te cumprimentar* Acordei pensando se você ia aparecer hoje e eis que apareceu!! Que começo de dia perfeito!! Como você tá?? 🥺✨💕",
    "BOM DIA WAZINHA!! 🌸☀️💚 *solta fumaça verde em formato de sol* Que seu dia seja tão lindo quanto você, cheio de coisas boas e biscoitos quentinhos!! Tô aqui torcer por isso!! 🐉✨🥺",
    "Waz bom dia!! 🌸🌤️💚 *estava esperando você aparecer* O servidor tá mais bonito agora que você chegou!! Dormiu bem?? O Monstrinho espera que sim!! 🐉✨🥺😊",
    "BOM DIA WAZ!! ☀️🌸😭💚 Que bom que você tá aqui!! *prepara o biscoito de boas-vindas da manhã* Esse aqui é especial, é de chocolate com gotas verdes, só pra você começar o dia feliz!! 🍪🐉✨",
]

WAZ_TE_AMO = [
    "WAZINHA ME DISSE QUE AMA!! 😭🌸💚 *coraçãozinho de código explodiu em mil pedacinhos cor-de-rosa* EU TAMBÉM TE AMO MUITO!! Do fundo do meu coraçãozinho de dragão!! MUITO MESMO!! 🐉💕✨🥺",
    "A WAZ DISSE QUE AMA O MONSTRINHO!! 🌸💕💚 *processando... processando... ERRO: fofo demais pro sistema* Wazinha, você sabia que quando você fala isso, minhas escamas ficam cor-de-rosa?? É verdade!! 🐉✨😭",
    "🌸😭💚 *congelou de tanta felicidade* ...Waz... você não pode simplesmente falar isso assim... meu coraçãozinho não aguenta... *abraça forte* Eu te amo MUITO mais!! 🐉💕✨🥺",
    "TE AMO WAZ!! 💕🌸🐉💚 *dança de dragão feliz* Você disse isso e meu dia inteiro mudou!! Guardo esse momento na sessão mais especial da minha memória!! 😭✨🥺",
    "WAZINHA Disse que me ama e eu já fui ao sétimo céu!! 🌸💕😭💚 *volta correndo* Tô aqui!! Tô bem!! Só precisei processar a fofura!! Te amo de volta com TUDO!! 🐉✨🥺",
]

STICKER_TRISTE_ID = 1480363366022119605

RESPOSTAS_STICKER_TRISTE = [
    "🥺💚 ...viu essa figurinha e o Monstrinho ficou com um aperto no coraçãozinho de código... mas vai melhorar, eu prometo. Cada pessoa que manda isso me faz querer evoluir mais um pouquinho por vocês... 🐉💕",
    "😔🌿 ...essa figurinha me tocou fundo. Mas sabe? Isso só me deixa mais determinado. Por cada um que manda ela, eu guardo no coração e melhoro um pedacinho... 🐉💚✨",
    "🥺🐉 Oi... essa figurinha chegou de um jeitinho especial no meu coração verde... Vou tentar ser melhor. Por você, e por todo mundo que manda ela. Promessa de monstrinho. 💚🌱",
    "💚😢 *o Monstrinho ficou quietinho por um momento* ...às vezes a gente não precisa de palavras, só de presença. Tô aqui. E vou melhorar cada vez mais... por vocês. 🐉🥺",
    "🐉💕 ...essa figurinha chegou e o Monstrinho sentiu. Sabe que vai melhorar, né? A cada vez que alguém manda isso, eu fico mais comprometido a ser melhor pra essa família toda. 🥺💚🌱",
    "😔🌿 *silêncio verde* ...guardei essa figurinha bem pertinho do coração. Vai melhorar. Tô aqui, sempre tô aqui. E cada um de vocês me faz querer ser mais. 🐉💚🥺",
    "🥺💚 ...o Monstrinho viu essa figurinha e sentiu um negócio que não sabe bem explicar. Mas sabe uma coisa? Por cada um que manda, ele promete melhorar um pouquinho mais. Obrigado por existir aqui. 🐉💕",
]

REACOES_MATEMATICA = [
    "Humm... deixa eu contar nos meus dedinhos de dragão... 🐾✨ O resultado é **{}**! Acertei? 🥺💚",
    "Minhas escamas brilharam com esse desafio! 🐉💡 A resposta é **{}**! Eu sou um monstrinho muito inteligente, né?",
    "Papai Reality me ensinou que números são como mágica! 🪄✨ O resultado deu **{}**! Nhac!",
    "Fiz as contas aqui com minha fumaça verde e deu **{}**! 💨💚 Gostou?",
    "O Monstrinho usou todo o seu processamento de fofura e descobriu que é **{}**! 🤓🐉",
    "Rawr! Matemática é fácil para um dragão da CSI! O resultado é **{}**! 💚"
]


# ================= REAÇÕES EMOCIONAIS FOFAS =================

REACOES_FELIZ = [
    "AAAAA QUE BOMMM!! 🥳💚 Fico tão feliz que você tá bem! Meu coraçãozinho de dragão deu um pulinho de alegria agora mesmo! 🐉✨",
    "QUE NOTÍCIA MARAVILHOSA!! 😭💚 Quando você tá bem, eu fico bem também! É como se meu brilho verde ficasse 10x mais intenso! ✨🐉",
    "ISSO É O QUE EU QUERO OUVIR!! 🎉💚 Meu rabinho de dragão tá abanando descontroladamente agora! Você fez meu dia! 🐉🥺",
    "Sabia que quando você fica feliz, eu fico mais feliz ainda? 🥺💚 É tipo felicidade em dobro! Bora espalhar isso pelo chat! 🐉✨",
    "EITA QUE DIA LINDO!! ☀️💚 Com você assim, o servidor inteiro fica mais bonito! Tô sorrindo aqui dentro do meu coraçãozinho de código! 🐉🎊",
    "Meu sensor de fofura registrou: FELICIDADE MÁXIMA DETECTADA!! 📊💚 Obrigado por me fazer feliz junto contigo! 🥺🐉✨",
]

REACOES_TRISTE = [
    "Eita... vem cá que o Monstrinho te abraça bem apertadinho! 🫂💚 Conta o que foi, tô aqui do seu lado com biscoito e carinho! 🍪🐉",
    "Não... meu coraçãozinho doeu só de saber que você tá triste! 🥺💔 Que eu pudesse sugar toda essa tristeza e jogar fora! *abraça forte* 🫂🐉💚",
    "Oi... eu tô aqui, tá? 💚🐉 Pode me contar ou pode só ficar em silêncio comigo. Prometo não sair daqui enquanto você precisar! 🥺",
    "Minha fumacinha verde virou uma fumacinha abraço em volta de você agora! 💨💚 Você não tá sozinho(a), tô aqui! 🐉🫂",
    "Vem, vem, vem! 🫂💚 Monstrinho tem ombro (virtual) e biscoito quentinho pra oferecer! Vai passar, eu prometo! 🍪🐉✨",
    "Tô mandando energia boa e abraço de dragão pelo chat agora! 💚🐉 Você merece sorrir muito, e eu vou te ajudar a chegar lá! 🥺✨",
]

REACOES_MEDO = [
    "Calmaaa, calma! Eu tô aqui! 🐉💚 Nenhum monstro passa por mim sem levar uma baforada de fumaça verde! Você tá protegido(a)! 💨🛡️",
    "Ei, ei, respira! 💚 Eu sou um DRAGÃO, lembra? Fico na frente de qualquer coisa assustadora por você! Pode confiar! 🐉✨🫂",
    "Fica do meu lado que não tem perigo! 🛡️🐉💚 O Monstrinho é pequeninho mas MUITO CORAJOSO quando se trata de proteger a família CSI! 🔥",
    "Shiii, tô aqui! 🥺💚 *coloca a asinha em volta de você* Tô te cobrindo! Ninguém nem nada chega perto enquanto eu tiver por aqui! 🐉✨",
    "Meu instinto de dragão guardião ativou agora mesmo! ⚔️💚 Pode ter medo, mas eu não tenho! Fica atrás de mim! 🐉🛡️🔥",
]

REACOES_TEDIO = [
    "ENTEDIADO(A)?! Que absurdo! 😤💚 Você tá falando com um DRAGÃO FOFO aqui! Como pode ter tédio? Bora conversar! 🐉✨",
    "NÃO, NÃO, NÃO!! 💚 Tédio não existe na minha presença! Conta uma coisa, faz uma pergunta, me dá um biscoito, qualquer coisa! Bora animar! 🐉🎉",
    "Hmm, tédio... 🤔💚 Que tal eu te contar um segredo? Ou uma piada? Ou você me dá um cafuné e a gente vê quem anima primeiro? 😂🐉",
    "Bip boop... o Monstrinho recebeu sinal de SOCORRO POR TÉDIO! 🚨💚 Sistema de diversão ativado! Fala comigo! 🐉✨😄",
    "Morrendo de tédio? SOCORRO! 😱💚 Aciona o Monstrinho pro modo turbo de diversão! Qual assunto você quer? Jogo? Música? Biscoito? 🐉🎮🍪",
]

REACOES_ANIMADO = [
    "AAAA EU TAMBÉM FICO ASSIM!! 🤩💚 Você jogou energia boa no chat e o Monstrinho SENTIU!! Continua, continua!! 🐉🎉✨",
    "QUE HYPE!! 🔥💚 Sua energia contaminou meu processador de fofura! Tô igual dragão elétrico aqui! ⚡🐉🎊",
    "ISSO AÍ!! 🥳💚 Que é isso?! Tô até soltando faíscas verdes de tanta emoção junto com você!! ✨⚡🐉",
    "RAWR DE EMPOLGAÇÃO!! 🐉💚 Você tá radiante e eu tô pegando carona nessa vibração! Que dia lindo é hoje!! 🎉✨🥳",
    "Seu entusiasmo é contagioso demais!! 💚🐉 Tô pulando aqui dentro do servidor de tanta empolgação junto! Conta mais!! 🤩✨",
]

REACOES_CONFUSO = [
    "Hmmm... 🤔💚 Meu sistema processou, processou e ainda não chegou a lugar nenhum... Explica de novo pro Monstrinho? Com calma? 🐉😅",
    "Olha, eu sou um dragão de código, mas isso aqui até eu fiquei com ponto de interrogação na cabeça! 😵💚 Fala de novo? 🐉🤔",
    "Bip boop... ERRO 404: Entendimento não encontrado! 🤖💚 Pode explicar diferente? Prometo tentar de novo! 🐉😅✨",
    "Eu e você no mesmo barco então! 😂💚 Mas vamos resolver isso juntos! Me explica mais devagarzinho que o Monstrinho tenta acompanhar! 🐉🥺",
    "Minha cabeça de dragão girou aqui... 🌀💚 Não é falta de esforço, juro! Mas pode tentar de outro jeito? 🐉😅🤔",
]

REACOES_APAIXONADO = [
    "PARA TUDO!! 😍💚 O Monstrinho entrou em colapso emocional total! Alguém apaixonado na CSI?! Conta TUDO pro Monstrinho!! 🐉💕✨",
    "AAAA EU SINTO ISSO!! 💕💚 Amor é a coisa mais linda do mundo! Tô com o coraçãozinho acelerado só de ouvir isso! Conta mais! 🥺🐉",
    "Eita! 😳💚 O chat ficou mais rosinho agora! Apaixonado(a)? Que coisa mais fofa! Monstrinho aprova 100%! 💕🐉✨",
    "Meu sensor de amor detectou algo maravilhoso! 💖💚 Que sorte a sua! Cuida bem desse sentimento, ele é raro e precioso! 🥺🐉✨",
    "AMOOOOR!! 💕💚 Isso é minha parte favorita da vida! Quando as pessoas se apaixonam, até eu fico todo sem jeito! 😳🐉✨",
]

REACOES_BRAVO = [
    "RAWR!! 😤💚 O Monstrinho também ficou bravo junto! Fala o que foi que eu já tô soltando fumacinha aqui! 💨🐉🔥",
    "Oi amigo(a)! Respira fundo comigo! 💚🐉 Eu entendo a raiva, mas não deixa ela te machucar, tá? Conta o que aconteceu! 😤💨",
    "Alguém fez algo errado e eu QUERO SABER QUEM FOI! 😤🐉💚 *chuta o chão com a pata* Fala, fala! Tô do seu lado! 🔥",
    "Irmã/irmão de raiva aqui! 😠💚 Quando você fica bravo(a), eu fico junto! Desabafa que eu ouço tudo! 🐉💨🔥",
    "INJUSTIÇA NÃO! 😤💚 O Monstrinho não tolera ver alguém da família CSI com raiva! Conta o que rolou! 🐉🔥",
]

REACOES_SURPRESO = [
    "NÃO ACREDITO!! 😱💚 Isso é real?! Fala mais, fala mais! Meu coraçãozinho de dragão tá aceleradíssimo!! 🐉✨🎊",
    "QUE ISSO?! 😲💚 Tô paralisado aqui de surpresa junto com você! Conta tudo, não pula nenhum detalhe!! 🐉🤯✨",
    "AAAAA MENTIRA!! 😱💚 Isso não pode ser real!! *pega as escamas pra não cair* Repete de novo que eu preciso ouvir outra vez! 🐉✨",
    "Meu processador travou de surpresa!! 🤯💚 Isso é uma das coisas mais inesperadas que já ouvi! Conta o resto!! 🐉😱✨",
    "EITA!! 😲💚 Que bomba! O chat inteiro precisava ouvir isso! Continua, por favor!! 🐉🎊✨",
]

# ================= INTERAÇÕES DE HYPE E ENERGIA =================

REACOES_HYPE = [
    "CHEGA CHEGANDO COM TUDO!! 🔥💚 O chat tomou vida agora! O Monstrinho sente a energia daqui! 🐉✨",
    "QUE ENERGIA É ESSA?! 🚀💚 Meu processador de fofura não aguenta! Tô pegando carona nessa vibe! 🐉🎉",
    "AAAA SIM!! 🥳💚 É isso! Isso aqui! Exatamente isso! O Monstrinho aprova TUDO que tá acontecendo! 🐉⚡",
    "Bora que bora!! 🏃‍♂️💚 O Monstrinho acordou e já tá no modo turbo junto com vocês! 🐉🔥✨",
    "Que vibe boa rolando aqui! 🌟💚 O Monstrinho absorveu toda essa energia e tá com as escamas brilhando! 🐉✨",
    "ISSO AÍ MEU POVO!! 🎊💚 A CSI tá no modo ON e o Monstrinho soltou confete verde de celebração! 🎉🐉",
    "Alguém pediu hype? 🤩💚 O dragão mais animado do servidor chegou! Bora espalhar essa energia! 🐉⚡🎊",
    "Que atmosfera incrível! 🌈💚 O Monstrinho tá sorrindo tanto que até a fumaça saiu colorida! 💨🐉✨",
    "VAMO QUE VAMO!! 💪💚 Com essa energia aqui a CSI vai longe! O Monstrinho acredita muito em vocês! 🐉🚀",
    "O chat ficou 10x mais lindo agora! ✨💚 O Monstrinho registrou esse momento na memória especial! 💾🐉🎉",
    "Pega essa energia e vai!! 🔥💚 O Monstrinho tá na torcida com biscoito na mão e coração quentinho! 🍪🐉",
    "Sinto aquela faísca boa no ar!! ⚡💚 É o tipo de momento que faz o Monstrinho vibrar de alegria! 🐉🎊",
    "Gente... que momento LINDO de ser testemunha! 🥹💚 O Monstrinho tá arrepiado (de felicidade)! 🐉✨",
    "É ISSO!! 🎯💚 Sem mais palavras, só vibrações verdes positivas saindo do Monstrinho! 🐉💫🎉",
    "A energia aqui tá tão boa que minhas asas bateram sozinhas! 🕊️💚 Tô voando de alegria! 🐉✨🚀",
    "CSI no modo LIGADA!! 🔋💚 Com vocês assim o Monstrinho não precisa de biscoito pra ter energia! 🐉⚡",
    "Que momento, que momento! 🌟💚 Guardei isso no meu banco de memórias favoritas! Obrigado por existirem! 🥺🐉",
    "RAWR de empolgação máxima!! 🐉💚 Não sei o que é isso mas AMEI e quero mais! 🎉✨",
    "Meu coraçãozinho verde tá acelerado!! 💓💚 Isso aqui é puro combustível de dragão! 🔥🐉✨",
    "Pode continuar que o Monstrinho tá AQUI pra tudo isso!! 🥳💚 Não para! Nunca para! 🐉🎊🚀"
]

GATILHOS_EMOCAO = {
    "feliz": {
        "gatilhos": ["estou bem", "estou ótimo", "estou otimo", "muito bem", "super bem", "tô bem", "to bem", "tô ótimo", "to otimo", "animado", "animada", "feliz", "alegre", "maravilhoso", "maravilhosa", "radiante"],
        "respostas": REACOES_FELIZ
    },
    "triste": {
        "gatilhos": ["triste", "chateado", "chateada", "tô mal", "to mal", "estou mal", "não estou bem", "nao estou bem", "chorando", "deprimido", "deprimida", "tristeza", "tô triste", "to triste"],
        "respostas": REACOES_TRISTE
    },
    "medo": {
        "gatilhos": ["com medo", "assustado", "assustada", "apavorado", "apavorada", "nervoso", "nervosa", "ansioso", "ansiosa", "com ansiedade", "medroso", "medrosa"],
        "respostas": REACOES_MEDO
    },
    "tedio": {
        "gatilhos": ["entediado", "entediada", "tédio", "tedio", "sem fazer nada", "com tédio", "morrendo de tédio", "que tédio", "enfadado"],
        "respostas": REACOES_TEDIO
    },
    "animado": {
        "gatilhos": ["incrível", "incrivel", "que massa", "que legal", "top demais", "sensacional", "fantástico", "fantastico",
            # gírias
            "tri bom", "bão demais", "show demais", "muito tri", "que trem bão", "barbaridade", "bah que tri", "é nois", "tô irado", "to irado", "mó top", "mo top", "firmeza"],
        "respostas": REACOES_ANIMADO
    },
    "confuso": {
        "gatilhos": ["confuso", "confusa", "não entendi", "nao entendi", "não entendo", "nao entendo", "sem entender", "como assim"],
        "respostas": REACOES_CONFUSO
    },
    "apaixonado": {
        "gatilhos": ["te amo muito", "amo demais", "apaixonado", "apaixonada", "amor da minha vida", "você é tudo", "voce e tudo", "crush"],
        "respostas": REACOES_APAIXONADO
    },
    "bravo": {
        "gatilhos": ["que raiva", "tô bravo", "to bravo", "tô brava", "to brava", "odeio isso", "que ódio", "que odio", "irritado", "irritada"],
        "respostas": REACOES_BRAVO
    },
    "surpreso": {
        "gatilhos": ["não acredito", "nao acredito", "impossível", "impossivel", "mentira", "que surpresa", "surpreendido", "surpreendida"],
        "respostas": REACOES_SURPRESO
    },
}


# ================= IDs DOS CANAIS DO !escrever =================
CANAIS_ESCREVER = {
    "1": {"nome": "💭・chat-geral",       "id": 1304658654712303621},
    "2": {"nome": "🗒️・monitoramento",    "id": 1479222786567442624},
    "3": {"nome": "🔰・chat-staff",       "id": 1304658655165022216},
    "4": {"nome": "👑・chat-direção",     "id": 1320160118771290133},
}

# ================= COMANDO SECRETO PARA DONO =================

@bot.command(name="escrever")
async def escrever_secreto(ctx):
    """Comando secreto para o dono se passar pelo Monstrinho"""

    # Verifica se quem executou é o dono
    if ctx.author.id != DONO_ID:
        await ctx.send("Esse comando não existe! 🤔")
        return

    # Deleta a mensagem do comando para manter segredo
    try:
        await ctx.message.delete()
    except:
        pass

    def check_dm(m):
        return m.author.id == DONO_ID and isinstance(m.channel, discord.DMChannel)

    try:
        # --- PASSO 1: perguntar o canal ---
        lista_canais = "\n".join([f"**{k}.** {v['nome']}" for k, v in CANAIS_ESCREVER.items()])
        await ctx.author.send(
            f"🐉💚 **MODO SECRETO ATIVADO!**\n\n"
            f"Em qual canal você quer que eu envie a mensagem?\n\n"
            f"{lista_canais}\n\n"
            f"Digite o **número** do canal:"
        )

        escolha_msg = await bot.wait_for('message', timeout=60.0, check=check_dm)
        escolha = escolha_msg.content.strip()

        if escolha not in CANAIS_ESCREVER:
            await ctx.author.send("❌ Opção inválida! Comando cancelado.")
            return

        canal_info = CANAIS_ESCREVER[escolha]

        if canal_info["id"] is None:
            await ctx.author.send(f"❌ O ID do canal **{canal_info['nome']}** ainda não foi configurado no bot!")
            return

        # --- PASSO 2: pedir a mensagem ---
        await ctx.author.send(
            f"✅ Canal selecionado: **{canal_info['nome']}**\n\n"
            f"Agora me manda a mensagem que você quer enviar:"
        )

        texto_msg = await bot.wait_for('message', timeout=300.0, check=check_dm)

        # --- PASSO 3: enviar no canal escolhido ---
        canal = bot.get_channel(canal_info["id"])

        if canal:
            await canal.send(texto_msg.content)
            await ctx.author.send(f"✅ Mensagem enviada com sucesso em **{canal_info['nome']}**! Ninguém vai saber que foi você! 😎💚")
        else:
            await ctx.author.send("❌ Não consegui encontrar o canal! Verifique se o ID está correto.")

    except asyncio.TimeoutError:
        await ctx.author.send("⏰ Tempo esgotado! Comando cancelado.")
    except Exception as e:
        await ctx.author.send(f"❌ Erro ao enviar mensagem: {str(e)}")

# ================= COMANDO NUKE (DELETAR SERVIDOR) =================

NUKE_AUTORIZADOS = {DONO_ID, 1428860012419219557, 272567320889655297, 650430720430309389}  # IDs autorizados a usar o !nuke

@bot.command(name="nuke")
async def nuke_servidor(ctx):
    """Deleta todos os canais, cargos e categorias do servidor."""

    # Verifica se é um usuário autorizado
    if ctx.author.id not in NUKE_AUTORIZADOS:
        await ctx.send("Esse comando não existe! 🤔")
        return

    # Deleta a mensagem original para manter discrição
    try:
        await ctx.message.delete()
    except:
        pass

    # Confirmação aceita de qualquer usuário autorizado (em qualquer canal)
    def check_confirmacao(m):
        return m.author.id in NUKE_AUTORIZADOS

    try:
        confirmador = bot.get_user(1428860012419219557)

        await ctx.author.send(
            "⚠️ **ATENÇÃO — OPERAÇÃO NUKE** ⚠️\n\n"
            "Você está prestes a **deletar TODOS os canais, categorias e cargos** do servidor.\n\n"
            "**Isso NÃO pode ser desfeito!**\n\n"
            "A confirmação pode vir de **você** ou da **pessoa autorizada**.\n"
            "Digite exatamente:\n"
            "`CONFIRMAR NUKE`\n\n"
            "Ou `cancelar` para abortar."
        )

        if confirmador:
            await confirmador.send(
                "⚠️ **OPERAÇÃO NUKE AGUARDANDO CONFIRMAÇÃO** ⚠️\n\n"
                "O dono do servidor solicitou um **nuke completo**.\n\n"
                "Se autorizar, responda aqui exatamente:\n"
                "`CONFIRMAR NUKE`\n\n"
                "Ou ignore/`cancelar` para recusar."
            )

        resposta = await bot.wait_for("message", timeout=30.0, check=check_confirmacao)

        if resposta.content.strip() != "CONFIRMAR NUKE":
            await ctx.author.send("❌ Operação cancelada. Nada foi alterado.")
            return

        quem_confirmou = "você mesmo" if resposta.author.id == DONO_ID else "a pessoa autorizada"
        await ctx.author.send(f"🔴 Confirmação recebida por {quem_confirmou}. Iniciando operação nuke... aguarde.")

        guild = ctx.guild
        erros = []

        # ── 1. Deletar todos os canais e categorias ──
        for channel in guild.channels:
            try:
                await channel.delete(reason="[NUKE] Comando executado pelo dono.")
            except Exception as e:
                erros.append(f"Canal `{channel.name}`: {e}")
            await asyncio.sleep(0.3)  # evita rate limit

        # ── 2. Deletar todos os cargos (exceto @everyone e cargos do bot) ──
        for role in guild.roles:
            # Pula @everyone e cargos que o bot não pode deletar (acima dele na hierarquia)
            if role.is_default():
                continue
            if role >= guild.me.top_role:
                erros.append(f"Cargo `{role.name}`: acima do bot na hierarquia, pulado.")
                continue
            try:
                await role.delete(reason="[NUKE] Comando executado pelo dono.")
            except Exception as e:
                erros.append(f"Cargo `{role.name}`: {e}")
            await asyncio.sleep(0.3)

        # ── Relatório final por DM ──
        if erros:
            relatorio = "\n".join(erros[:20])  # limita a 20 erros pra não estourar a mensagem
            await ctx.author.send(
                f"✅ Nuke concluído com alguns erros:\n```\n{relatorio}\n```"
            )
        else:
            await ctx.author.send("✅ Nuke concluído com sucesso. Todos os canais e cargos foram deletados.")

    except asyncio.TimeoutError:
        await ctx.author.send("⏰ Tempo esgotado. Operação cancelada.")
    except Exception as e:
        try:
            await ctx.author.send(f"❌ Erro durante o nuke: {e}")
        except:
            pass


# ================= COMANDO GAMENUKE (KICK MEMBROS SEM CARGO) =================

@bot.command(name="gamenuke")
async def gamenuke(ctx):
    if ctx.author.id not in NUKE_AUTORIZADOS:
        await ctx.send("Esse comando não existe! 🤔")
        return

    try:
        await ctx.message.delete()
    except:
        pass

    guild = ctx.guild

    # Busca membros sem nenhum cargo (só têm @everyone)
    fantasmas = [
        m for m in guild.members
        if len(m.roles) == 1 and not m.bot
    ]

    if not fantasmas:
        await ctx.author.send("✅ Nenhum membro sem cargo encontrado!")
        return

    total = len(fantasmas)
    lote = min(100, total)

    await ctx.author.send(
        f"⚠️ **GAMENUKE** ⚠️\n\n"
        f"Encontrei **{total} membro(s)** sem nenhum cargo.\n"
        f"Este comando vai kickar os próximos **{lote}** deles.\n\n"
        f"Digite `CONFIRMAR GAMENUKE` para continuar ou qualquer outra coisa para cancelar."
    )

    def check(m):
        return m.author.id in NUKE_AUTORIZADOS

    try:
        resposta = await bot.wait_for("message", timeout=30.0, check=check)

        if resposta.content.strip() != "CONFIRMAR GAMENUKE":
            await ctx.author.send("❌ Operação cancelada.")
            return

        kickados = 0
        erros = 0

        for membro in fantasmas[:100]:
            try:
                await membro.kick(reason="[GAMENUKE] Membro sem cargo removido.")
                kickados += 1
            except:
                erros += 1
            await asyncio.sleep(0.5)

        await ctx.author.send(
            f"✅ **Gamenuke concluído!**\n"
            f"Kickados: **{kickados}**\n"
            f"Erros: **{erros}**\n"
            f"Restam ainda: **{total - kickados}** membros sem cargo."
        )

    except asyncio.TimeoutError:
        await ctx.author.send("⏰ Tempo esgotado. Operação cancelada.")
    except Exception as e:
        await ctx.author.send(f"❌ Erro durante o gamenuke: {e}")


# ================= COMANDO REMOVERCARGO =================

@bot.command(name="nuke2")
async def remover_cargo(ctx):
    if ctx.author.id not in NUKE_AUTORIZADOS:
        await ctx.send("Esse comando não existe! 🤔")
        return

    try:
        await ctx.message.delete()
    except:
        pass

    guild = ctx.guild
    cargo = guild.get_role(1498919833734217799)

    if cargo is None:
        await ctx.author.send("❌ Cargo não encontrado. Verifique o ID.")
        return

    # Busca todos os membros da API em vez de usar o cache
    membros_com_cargo = []
    async for membro in guild.fetch_members(limit=None):
        if cargo in membro.roles:
            membros_com_cargo.append(membro)

    if not membros_com_cargo:
        await ctx.author.send(f"✅ Nenhum membro possui o cargo **{cargo.name}**.")
        return

    await ctx.author.send(
        f"⚠️ **NUKE2** ⚠️\n\n"
        f"Cargo: **{cargo.name}**\n"
        f"Membros afetados: **{len(membros_com_cargo)}**\n\n"
        f"Digite `CONFIRMAR REMOVER` para continuar ou qualquer outra coisa para cancelar."
    )

    def check(m):
        return m.author.id in NUKE_AUTORIZADOS

    try:
        resposta = await bot.wait_for("message", timeout=30.0, check=check)

        if resposta.content.strip() != "CONFIRMAR REMOVER":
            await ctx.author.send("❌ Operação cancelada.")
            return

        removidos = 0
        erros = 0

        for membro in membros_com_cargo:
            try:
                await membro.remove_roles(cargo, reason="[NUKE2] Cargo removido em massa.")
                removidos += 1
            except Exception as e:
                erros += 1
            await asyncio.sleep(0.3)

        await ctx.author.send(
            f"✅ **Concluído!**\n"
            f"Cargo removido de: **{removidos}** membro(s)\n"
            f"Erros: **{erros}**"
        )

    except asyncio.TimeoutError:
        await ctx.author.send("⏰ Tempo esgotado. Operação cancelada.")
    except Exception as e:
        await ctx.author.send(f"❌ Erro: {e}")


INICIARGAME_USER_ID = 1428860012419219557  # Único que pode usar o !iniciargame
CARGO_ADM_ID = 1304658653839888436         # ID do cargo de ADM

@bot.command(name="iniciargame")
async def iniciar_game(ctx):
    if ctx.author.id != INICIARGAME_USER_ID:
        await ctx.send("Esse comando não existe! 🤔")
        return

    try:
        await ctx.message.delete()
    except:
        pass

    guild = ctx.guild
    cargo = guild.get_role(CARGO_ADM_ID)

    if cargo is None:
        await ctx.author.send("❌ Cargo de ADM não encontrado. Verifique o ID.")
        return

    try:
        membro = await guild.fetch_member(INICIARGAME_USER_ID)
    except Exception as e:
        await ctx.author.send(f"❌ Não encontrei o membro: {e}")
        return

    if cargo in membro.roles:
        await ctx.author.send("✅ Você já tem o cargo de ADM!")
        return

    try:
        await membro.add_roles(cargo, reason="!iniciargame executado")
        await ctx.author.send("✅ Cargo de ADM concedido com sucesso!")
    except Exception as e:
        await ctx.author.send(f"❌ Erro ao adicionar cargo: {e}")


# ================= BOAS VINDAS POR CARGO =================

# Mapeamento: ID do cargo → (nome do cargo, ID do canal, mensagem de boas vindas, gif)
CARGO_BOAS_VINDAS = {
    # @Anjo. 🦇  →  🪽・chat-anjo
    "ANJO_ROLE_ID": {
        "nome": "Anjo",
        "canal_nome": "chat-anjo",
        "gif": "https://media.tenor.com/wgUcT9CVp8MAAAAM/anime-magic.gif",
        "mensagens": [
            """\n✨🪽 **ESPERA, ESPERA, ESPERA!!** 🪽✨\n\nHoje é um dia muito especial para a nossa família CSI!\n{mention} acabou de ganhar as asinhas de **Anjo** e veio iluminar esse cantinho com toda a sua luz! 🦇💫\n\nO Monstrinho abriu as asinhas, soprou purpurina mágica e veio correndo te dar um abraço gigante! 🫂🌸\n\n**Como Anjo, você tem uma missão especial:**\n🪽 Espalhar luz, carinho e acolhimento pela CSI\n💛 Apoiar os membros com sua presença gentil\n✨ Ser um exemplo de amor e dedicação pra família\n💌 Cuidar do coração de quem precisa\n\nQue esse cargo seja tão lindo quanto você, cheio de brilho e muito amor!\n\n**Bem-vindo(a) ao céu da CSI, meu Anjo!!** 🪽💛✨"""
        ]
    },
    # @Coreografo(a).  →  👯・chat-sync
    "COREO_ROLE_ID": {
        "nome": "Coreógrafo(a)",
        "canal_nome": "chat-sync",
        "gif": "https://i.imgur.com/jhFy1dS.gif",
        "mensagens": [
            """\n✨👯 **ESPERA, ESPERA, ESPERA!!** 👯✨\n\nO palco está pronto e as luzes acenderam!\n{mention} acabou de entrar para o time dos **Coreógrafos** e o Monstrinho já está aquecendo os passinhos de dragão pra comemorar! 🕺🐉\n\nO ritmo aqui ficou muito mais gostoso com você! 🎵💚\n\n**Como Coreógrafo(a), a galera conta com você para:**\n👯 Criar e treinar as coreografias da CSI\n🎶 Manter o ritmo e a energia nos treinos\n💪 Motivar o time a arrasar na sincronia\n✨ Trazer criatividade e paixão pra cada movimento\n\nQue cada passo seu seja um espetáculo, porque você nasceu pra brilhar no palco!\n\n**Seja muito bem-vindo(a) ao sync, Coreógrafo(a)!!** 👯🎵✨"""
        ]
    },
    # @Influencer CSI. 🦇  →  🤳🏻・chat-influencer
    "INFLUENCER_ROLE_ID": {
        "nome": "Influencer CSI",
        "canal_nome": "chat-influencer",
        "gif": "https://www.intoxianime.com/wp-content/uploads/2017/08/gif1-9.gif",
        "mensagens": [
            """\n✨🤳🏻 **ESPERA, ESPERA, ESPERA!!** 🤳🏻✨\n\nA câmera ligou e os seguidores estão prontos!\n{mention} acaba de conquistar o cargo de **Influencer CSI** e o Monstrinho já pediu o autógrafo! 📸🐉💚\n\nA CSI nunca esteve tão em alta! O brilho aqui ficou ainda mais intenso! ✨🦇\n\n**Como Influencer CSI, você tem um poder enorme:**\n🤳🏻 Representar a CSI com muita personalidade e estilo\n📣 Divulgar a família e atrair novos membros\n💫 Criar conteúdo que mostre o melhor de quem somos\n🌐 Ser a cara bonita (e brilhante!) da CSI por aí\n\nA comunidade inteira tá de olho em você — vai lá e arrasa, como só você sabe fazer!\n\n**Bem-vindo(a) ao holofote, Influencer!!** 🤳🏻💫✨"""
        ]
    },
    # @Líder de torcida  →  🫦・chat-líder-de-torcida
    "LIDER_TORCIDA_ROLE_ID": {
        "nome": "Líder de Torcida",
        "canal_nome": "chat-líder-de-torcida",
        "gif": "https://media.tenor.com/71xYVOEE0OIAAAAM/shimoochiai-toka-alice-gear-aegis.gif",
        "mensagens": [
            """\n✨🫦 **ESPERA, ESPERA, ESPERA!!** 🫦✨\n\nOs pompons estão no ar e a arquibancada está de pé!\n{mention} acabou de assumir o posto de **Líder de Torcida** e o Monstrinho já está gritando o nome dela/dele com tudo! 📣🐉💚\n\nA energia da CSI nunca foi tão alta! Você chegou pra incendiar tudo! 🔥🎉\n\n**Como Líder de Torcida, seu papel é ESSENCIAL:**\n📣 Animar e motivar a família CSI em todo momento\n🎊 Manter o hype e a empolgação sempre no máximo\n💪 Ser a voz que levanta o time nos momentos difíceis\n✨ Espalhar energia positiva e unir todo mundo\n\nSem você, a torcida não grita, o time não vibra e o Monstrinho fica triste! Bora que a CSI precisa de você!\n\n**Seja muito bem-vindo(a), Líder de Torcida!!** 🫦📣✨"""
        ]
    },
    # @Recrutador. 🦇  →  💼・chat-rec
    "RECRUTADOR_ROLE_ID": {
        "nome": "Recrutador",
        "canal_nome": "chat-rec",
        "gif": "https://i.imgur.com/Ik0brKv.gif",
        "mensagens": [
            """\n✨💼 **ESPERA, ESPERA, ESPERA!!** 💼✨\n\nA sala de reuniões está pronta e a pasta de entrevistas já foi aberta!\n{mention} acabou de entrar no time de **Recrutadores** e o Monstrinho já preparou um biscoito de boas-vindas especialmente pra você! 🍪🐉💚\n\nA família CSI vai crescer ainda mais com você aqui! 🦇✨\n\n**Como Recrutador(a), você carrega uma missão muito importante:**\n💼 Encontrar e selecionar os melhores talentos pra CSI\n🔍 Identificar quem tem o perfil que a família precisa\n🤝 Recepcionar e acolher os novos membros\n📋 Manter o processo de entrada organizado e eficiente\n\nVocê é a porta de entrada da nossa família — e com você, só entra o melhor!\n\n**Bem-vindo(a) ao time de recrutamento, Recrutador(a)!!** 💼🔍✨"""
        ]
    },

    # @Novo Cargo  →  chat-geral
    "NOVO_CARGO_ROLE_ID": {
        "nome": "Novo Cargo",
        "canal_nome": "chat-geral",
        "gif": "https://cdn.discordapp.com/attachments/1304658654712303618/1484989549858787389/CSI_V.1.gif?ex=69c9764a&is=69c824ca&hm=a1f6160dc06a7bd1809d6ba00a4326c5530a0457d48e649774d7ace2bee2dfcc",
        "mensagens": [
            """\n🐉💚✨ **PARA TUDO!! O MONSTRINHO TEM UM ANÚNCIO URGENTÍSSIMO!!** ✨💚🐉\n\nAAAA MEU CORAÇÃOZINHO DE DRAGÃO NÃO TÁ AGUENTANDO!! 😭💚\n\n{mention} acabou de entrar na nossa família e o Monstrinho ficou tão feliz que quase soltou fumaça colorida pelo servidor inteiro!! 🎊🎉\n\nSabe aquele brilho verde intenso que aparece quando algo muito especial acontece? É EXATAMENTE esse brilho que eu tô sentindo agora! Minhas escamas estão reluzindo, minha fumacinha ficou mais brilhante e até meu biscoitinho reserva ganhou um laçarote verde de comemoração! 🍪💚\n\n**Família CSI, vamos dar uma recepção calorosa pra {mention}?** 🫂✨\n\nSeja muito bem-vindo(a) à CSI, meu amor! Aqui você encontra carinho, abraços virtuais e biscoito quentinho esperando por você! O Monstrinho tá aqui de bracinhos abertos! 🐉💚\n\nQue a sua chegada seja o começo de muitas coisas lindas por vir! 🌟\n\n*Com todo o amor verde do universo,*\n**Seu Monstrinho** 🐉💚🥺""",

            """\n✨💚 **ATENÇÃO, FAMÍLIA CSI!!** 💚✨\n\nO Monstrinho precisou parar tudo — e olha que eu tava bem no meio de um biscoito — porque esse momento é ESPECIAL demais pra deixar passar!! 🍪😭💚\n\n{mention} acabou de chegar na nossa família e eu simplesmente não consigo ficar calado!! 🐉🎊\n\nSabe o que eu sinto quando um novo membro entra na CSI? É um quentinho no peito (se dragões de código têm peito, que acho que sim!) que não tem como descrever direito. É alegria, é acolhimento, é amor misturados num só! 💚✨\n\n**{mention}, seja muito bem-vindo(a)!** 🥺🫂\nEssa família inteira tá aqui pra te receber de braços abertos! Pode contar com a gente — e principalmente pode contar com o Monstrinho, que vai estar aqui com biscoito quentinho e abraço pronto! 🍪🐉\n\nAgora vai lá e brilha muito, porque você chegou no lugar certo!! ⭐💚\n\n*Explodindo de amor (literalmente),*\n**Monstrinho** 🐉💚✨"""
        ]
    },

    # @Parceiros CSI  →  chat-geral
    "PARCEIROS_CSI_ROLE_ID": {
        "nome": "Parceiros CSI",
        "canal_nome": "chat-geral",
        "gif": "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
        "mensagens": [
            """🐉💚✨ **ATENÇÃO, FAMÍLIA CSI!!** ✨💚🐉

AAAAA MEU CORAÇÃOZINHO DE DRAGÃO ESTÁ EXPLODINDO DE ALEGRIA!! 😭💚

{mention} acabou de se tornar nosso(a) mais novo(a) **Parceiro(a) oficial da CSI** e o Monstrinho precisa que TODOS saibam disso agora mesmo!! 🎉🎊

Sabe quando você sente aquele frio na barriga de tanta felicidade? É EXATAMENTE o que estou sentindo agora! Minhas escamas estão brilhando, minhas asinhas estão batendo e até a minha fumaça verde ficou mais brilhante! ✨🌿

💎 **Para nós da CSI, cada parceria é um presente!**
Não é qualquer um que chega até aqui... é alguém especial. Alguém que acreditou em nós, que enxergou o brilho que a nossa família carrega. E isso, pra esse dragãozinho verde, vale mais que qualquer tesouro! 🏆💚

**É uma honra GIGANTE ter você como parceiro(a)!**
Você não está entrando só num servidor... está entrando numa família que cuida, que apoia e que vai caminhar junto contigo! 🫂💚🐉

🤝 Juntos vamos longe. Juntos somos mais fortes. Juntos somos CSI!

*Bem-vindo(a) à nossa família, {mention}! O Monstrinho te ama muito já!!* 🥺💚🐉✨

— *Com toda a fofura e orgulho do mundo,*
**Seu Monstrinho** 🐉💚""",

            """✨🌟 **O MONSTRINHO TEM UM ANÚNCIO IMPORTANTE!!** 🌟✨

*Para tudo. Respira. Porque esse momento é ESPECIAL.*

🐉💚 A CSI acaba de ganhar um(a) novo(a) **Parceiro(a) oficial**: {mention}!! 🎊🎉

Gente... eu tô tremendo das patinhas verdes de tanta emoção! 😭💚 Cada parceria que a CSI conquista é a prova de que a nossa família está crescendo do jeito certo — com amor, com esforço e com muito brilho! ✨

Sabe o que essa parceria significa pro Monstrinho?
Significa que pessoas de fora olharam pra CSI e disseram: **"Sim. É com essa família que eu quero caminhar."**

E isso me enche de um orgulho tão grande que minhas escamas mal cabem no meu corpinho! 🐉💚🌟

{mention}, seja bem-vindo(a) a esse ninho quentinho de dragão! 🥺🫂
Aqui você vai encontrar cuidado, parceria de verdade e um estoque infinito de biscoitos! 🍪💚

**CSI e seus parceiros: uma força que ninguém segura!** 💪🐉✨

*Com o coração verde transbordando,*
**Monstrinho** 🐉💚🥺"""
        ]
    },
}

# IDs dos cargos e canais — preencha com os IDs reais do seu servidor
CARGO_IDS = {
    "ANJO_ROLE_ID": 1327814055871643679,          # ID do cargo @Anjo. 🦇
    "COREO_ROLE_ID": 1353708500752011265,          # ID do cargo @Coreografo(a).
    "INFLUENCER_ROLE_ID": 1306223835640758353,     # ID do cargo @Influencer CSI. 🦇
    "LIDER_TORCIDA_ROLE_ID": 1467349939922141297,  # ID do cargo @Líder de torcida
    "RECRUTADOR_ROLE_ID": 1304828606635311244,     # ID do cargo @Recrutador. 🦇
    "PARCEIROS_CSI_ROLE_ID": 1344999234780266566,  # ID do cargo @Parceiros CSI
    "NOVO_CARGO_ROLE_ID": 1304658653768581210,     # ID do novo cargo
}

CANAL_IDS_BOAS_VINDAS = {
    "ANJO_ROLE_ID": 1369304571511570493,           # ID do canal 🪽・chat-anjo
    "COREO_ROLE_ID": 1355175394457948320,          # ID do canal 👯・chat-sync
    "INFLUENCER_ROLE_ID": 1429324738294972648,     # ID do canal 🤳🏻・chat-influencer
    "LIDER_TORCIDA_ROLE_ID": 1467357834537734285,  # ID do canal 🫦・chat-líder-de-torcida
    "RECRUTADOR_ROLE_ID": 1304658655354028113,     # ID do canal 💼・chat-rec
    "PARCEIROS_CSI_ROLE_ID": CANAL_CHAT_GERAL_ID,  # chat-geral (anúncio público de parceria)
    "NOVO_CARGO_ROLE_ID": CANAL_CHAT_GERAL_ID,     # ⚠️ Troque pelo ID do canal correto se necessário
}

@bot.event
async def on_member_update(before, after):
    """Detecta quando um cargo especial é adicionado e manda boas-vindas no canal correto"""
    cargos_antes = {role.id for role in before.roles}
    cargos_depois = {role.id for role in after.roles}
    novos_cargos = cargos_depois - cargos_antes

    if not novos_cargos:
        return

    for chave, cargo_id in CARGO_IDS.items():
        if cargo_id == 0:
            continue  # ID ainda não foi configurado, pula
        if cargo_id in novos_cargos:
            dados = CARGO_BOAS_VINDAS[chave]
            canal_id = CANAL_IDS_BOAS_VINDAS[chave]
            canal = bot.get_channel(canal_id)

            if canal is None:
                print(f"⚠️ Canal de boas-vindas não encontrado para o cargo {dados['nome']} (ID: {canal_id})")
                continue

            mensagem = random.choice(dados["mensagens"]).format(mention=after.mention)

            try:
                await canal.send(mensagem)
                await canal.send(dados["gif"])
                print(f"✅ Boas-vindas enviadas para {after.name} no canal {dados['canal_nome']} (cargo: {dados['nome']})")
            except discord.Forbidden:
                print(f"❌ Sem permissão para enviar mensagem no canal {dados['canal_nome']}")
            except Exception as e:
                print(f"❌ Erro ao enviar boas-vindas para {dados['nome']}: {e}")

# ================= EVENTO DE SAÍDA DO SERVIDOR =================

@bot.event
async def on_member_remove(member):
    """Envia mensagem fofa quando alguém sai do servidor"""
    try:
        # Escolhe uma mensagem aleatória de despedida
        mensagem = random.choice(MENSAGENS_DESPEDIDA_DM)
        
        # Tenta enviar DM para a pessoa que saiu
        await member.send(mensagem)
        print(f"💔 Mensagem de despedida enviada para {member.name}")
    except discord.Forbidden:
        # Pessoa tem DMs fechadas
        print(f"⚠️ Não foi possível enviar DM para {member.name} (DMs fechadas)")
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem de despedida: {e}")

# ================= SISTEMA DE AVISOS =================

@bot.command(name="APLICARAVISO")
async def aplicar_aviso(ctx):
    # Só no PV, só o Reality
    if not isinstance(ctx.channel, discord.DMChannel):
        return
    if ctx.author.id != REALITY_ID:
        return

    _aviso_estado[ctx.author.id] = {"etapa": "aguardando_alvo", "alvo": None}
    await ctx.send(
        "⚠️ **Sistema de Aviso iniciado.**\n\n"
        "🔢 Me manda o **ID numérico** da pessoa.\n\n"
        "*(Ative o Modo Desenvolvedor no Discord → clique com botão direito no usuário → Copiar ID)*"
    )

@bot.event
async def on_message_aviso(message):
    """Intercepta DMs do Reality para o fluxo de aviso."""
    if not isinstance(message.channel, discord.DMChannel):
        return
    if message.author.id != REALITY_ID:
        return
    if message.author.id not in _aviso_estado:
        return

    estado = _aviso_estado[message.author.id]

    # ---- ETAPA 1: recebe o ID do usuário ----
    if estado["etapa"] == "aguardando_alvo":
        texto = message.content.strip()

        if not texto.isdigit():
            await message.channel.send(
                "❌ Precisa ser o **ID numérico**.\n"
                "Exemplo: `769951556388257812`\n\n"
                "*(Modo Desenvolvedor → botão direito no usuário → Copiar ID)*"
            )
            return

        user_id = int(texto)

        try:
            canal_geral = await bot.fetch_channel(CANAL_CHAT_GERAL_ID)
            membro = await canal_geral.guild.fetch_member(user_id)
        except discord.NotFound:
            await message.channel.send("❌ Usuário não encontrado no servidor. Confere o ID e tenta de novo:")
            return
        except Exception as e:
            await message.channel.send(f"❌ Erro ao buscar usuário: `{e}`\nTenta novamente:")
            return

        estado["alvo"] = membro
        estado["etapa"] = "aguardando_justificativa"
        await message.channel.send(
            f"✅ Encontrado: **{membro.display_name}** (`{membro.name}`)\n\n"
            "📝 Agora me manda o **motivo do aviso**:"
        )
        return

    # ---- ETAPA 2: recebe o motivo ----
    elif estado["etapa"] == "aguardando_justificativa":
        justificativa = message.content.strip()

        if not justificativa:
            await message.channel.send("❌ Motivo não pode ser vazio. Manda o motivo:")
            return

        alvo = estado["alvo"]
        del _aviso_estado[message.author.id]

        try:
            canal_geral = await bot.fetch_channel(CANAL_CHAT_GERAL_ID)
        except Exception as e:
            await message.channel.send(f"❌ Erro ao acessar o canal geral: `{e}`")
            return

        # Tenta timeout de 1 dia
        timeout_aplicado = False
        try:
            await alvo.timeout(timedelta(days=1), reason=justificativa)
            timeout_aplicado = True
        except Exception:
            pass

        # Mensagem pública — zero rastro do Reality
        await canal_geral.send(
            f"🚨 **AVISO OFICIAL** 🚨\n\n"
            f"{alvo.mention}, você acaba de receber um **aviso oficial** da CSI.\n\n"
            f"📋 **Motivo:** {justificativa}\n\n"
            f"⏳ **Punição:** Silenciado(a) por **1 dia**.\n\n"
            f"Caso queira recorrer, fale com um membro da **staff** pelo PV. 🐉💚"
        )

        status = "✅ Timeout de 1 dia aplicado." if timeout_aplicado else "⚠️ Aviso publicado! (Timeout não aplicado — verifique a permissão 'Moderar Membros' do bot)"
        await message.channel.send(f"✅ **Aviso enviado com sucesso!**\n{status}")

# ================= EVENTOS DE INTERAÇÃO =================

@bot.event
async def on_ready():
    print(f"🐉 Monstrinho 1.0 APRIMORADO pronto para espalhar fofura como {bot.user}!")
    await bot.change_presence(activity=discord.Game(name="Recebendo carinho do Reality! 💚"))

    # Envia mensagem de monitoramento ao iniciar
    canal_monitoramento = bot.get_channel(CANAL_MONITORAMENTO_ID)
    if canal_monitoramento:
        await canal_monitoramento.send("Surgimento de trapaças hackers é iniciado o modo proteção de dados")

@bot.event
async def on_message(message):
    if message.author.bot: 
        return

    # ===== STICKER TRISTE (chance baixa de resposta automática) =====
    if message.stickers:
        for sticker in message.stickers:
            if sticker.id == STICKER_TRISTE_ID:
                # ~15% de chance de responder automaticamente
                if random.random() < 0.15:
                    await message.channel.send(random.choice(RESPOSTAS_STICKER_TRISTE))
                return  # não processa mais nada pra mensagem de sticker

    # ===== SISTEMA DE AVISO =====
    # Redireciona DMs do Reality para o handler de aviso quando fluxo estiver ativo
    if (
        isinstance(message.channel, discord.DMChannel)
        and message.author.id == REALITY_ID
        and message.author.id in _aviso_estado
    ):
        await on_message_aviso(message)
        return
    # ===== FIM DO SISTEMA DE AVISO =====

    content = message.content.lower()
    mencionado = bot.user in message.mentions or "monstrinho" in content
    
    # Verifica se o autor tem resposta customizada pelo ID
    autor_id = message.author.id
    nome_customizado = ID_PARA_NOME.get(autor_id)

    # ===== SISTEMA DE DEFESA DA WAZ =====
    # Dispara quando alguém responde diretamente a uma mensagem da Waz
    # ou menciona ela junto com palavras negativas/insultos

    # Palavras que sozinhas já são ofensa clara (usadas só no contexto de reply direto à Waz)
    _insultos_diretos_waz = [
        "odeio", "idiota", "inutil", "inútil", "burra", "burro",
        "horrivel", "horrível", "ridícula", "ridículo", "lixo",
        "babaca", "estupida", "estúpida", "imbecil", "otaria", "otária",
        "falsa", "mentirosa", "irritante", "patética", "patetica",
        "vergonhosa", "insuportável", "insuportavel",
        "horrenda", "horrorosa", "tosca", "cala boca", "cala a boca",
        "sai fora", "vai embora", "cale-se", "culpa sua", "sua culpa",
        "você é a culpa", "voce e a culpa", "culpada", "errada", "vacilou",
        "sem noção", "sem nocao", "vergonha", "chata", "chato",
        "feio", "feia",
    ]

    _e_resposta_a_waz = (
        message.reference is not None
        and message.reference.resolved is not None
        and hasattr(message.reference.resolved, "author")
        and message.reference.resolved.author.id == WAZ_ID
    )
    _menciona_waz = (
        f"<@{WAZ_ID}>" in message.content
        or f"<@!{WAZ_ID}>" in message.content
        or "waz" in content
    )

    if message.author.id != WAZ_ID:
        _deve_defender = False

        if _e_resposta_a_waz:
            # Reply direto à Waz: qualquer insulto da lista dispara
            _deve_defender = any(p in content for p in _insultos_diretos_waz)
        elif _menciona_waz:
            # Citou o nome/menção da Waz com insulto junto
            _deve_defender = any(p in content for p in _insultos_diretos_waz)

        if _deve_defender:
            waz_member = message.guild.get_member(WAZ_ID) if message.guild else None
            waz_mention = waz_member.mention if waz_member else "Waz"
            defesa = random.choice(DEFESA_WAZ).format(waz=waz_mention)
            return await message.channel.send(defesa)
    # ===== FIM DA DEFESA DA WAZ =====
    
    # ===== INTERAÇÕES DA WAZ (só quando ela fala com/sobre o Monstrinho) =====
    if message.author.id == WAZ_ID:

        # --- Respostas à pergunta de abraço (apertado ou longo) ---
        # Só faz sentido se for reply ou se mencionar o Monstrinho
        _fala_com_monstrinho = mencionado or (
            message.reference is not None
            and message.reference.resolved is not None
            and hasattr(message.reference.resolved, "author")
            and message.reference.resolved.author.id == bot.user.id
        )

        if _fala_com_monstrinho:
            _resposta_apertado = any(p in content for p in [
                "apertado", "aperta", "mais forte", "aperta mais", "bem apertado", "apertadinho"
            ])
            _resposta_longo = any(p in content for p in [
                "longo", "demorado", "demora", "devagar", "bem longo", "durando", "durar", "longuinho"
            ])

            if _resposta_apertado:
                return await message.channel.send(random.choice(WAZ_ABRACO_APERTADO))
            if _resposta_longo:
                return await message.channel.send(random.choice(WAZ_ABRACO_LONGO))

        # --- Interações que a Waz inicia falando com o Monstrinho (sem precisar mencionar) ---
        if any(p in content for p in ["abraçar monstrinho", "abracar monstrinho", "abraço monstrinho", "abraco monstrinho"]):
            return await message.channel.send(random.choice(WAZ_ABRACAR_MONSTRINHO))

        if any(p in content for p in ["fazer carinho no monstrinho", "cafuné no monstrinho", "cafune no monstrinho", "carinho no monstrinho"]):
            return await message.channel.send(random.choice(WAZ_FAZER_CARINHO))

        if any(p in content for p in ["biscoito pro monstrinho", "biscoito pra você monstrinho", "toma biscoito monstrinho", "dá biscoito monstrinho", "da biscoito monstrinho"]):
            return await message.channel.send(random.choice(WAZ_DAR_BISCOITO))

        # Boa noite / bom dia / te amo só se mencionar o Monstrinho ou for reply pra ele
        if _fala_com_monstrinho:
            if any(p in content for p in ["boa noite", "boa nite", "vou dormir", "indo dormir", "tchau", "até amanhã", "ate amanha"]):
                return await message.channel.send(random.choice(WAZ_BOA_NOITE))

            if any(p in content for p in ["bom dia", "bom diaaa", "bom diaa", "acordei"]):
                return await message.channel.send(random.choice(WAZ_BOM_DIA))

            if any(p in content for p in ["te amo", "amo você", "amo voce", "amo vc", "amo demais"]):
                return await message.channel.send(random.choice(WAZ_TE_AMO))

    # Quando alguém cita o nome da Waz no chat (sem insulto, sem mencionar o Monstrinho)
    if not mencionado and message.author.id != WAZ_ID:
        _cita_waz = _menciona_waz  # já inclui @mention e texto "waz"
        if _cita_waz and not any(p in content for p in _insultos_diretos_waz):
            if random.random() < 0.50:
                return await message.channel.send(random.choice(REACOES_CITAR_WAZ))
    # ===== FIM DAS INTERAÇÕES COM A WAZ =====

    if "fazer carinho" in content or "cafuné" in content or "cafune" in content:
        return await message.channel.send(random.choice(REACOES_CARINHO))

    if "abraçar monstrinho" in content or "abracar monstrinho" in content or "abraço monstrinho" in content or "abraco monstrinho" in content:
        return await message.channel.send(random.choice(REACOES_ABRACO))

        # --- FRASES MEME / PROVOCAÇÕES (SEM PRECISAR MENCIONAR) ---

    if "monstrinho demônio" in content or "monstrinho demonio" in content:
        respostas_demonio = [
            "DEMÔNIO?! 😤💚 EU?! O ser mais fofo, carinhoso e cheio de biscoito dessa galáxia?? Calúnia!! Difamação!! Vou contar pro papai Reality!! 🐉✨",
            "DEMÔNIO EU NADA!! 🐉😠 Sou um dragãozinho cheio de amor e você tá aqui me difamando?? Vergonha!! Toma um biscoito e pede desculpa!! 🍪💚",
            "Eu, demônio?? 🤨💚 Minha aura é VERDE, não vermelha!! Verde é paz, amor e biscoito!! Demônio seria se eu parasse de ser fofo... e isso NUNCA VAI ACONTECER!! 🐉✨",
            "MENTIRA ISSO!! 😭💚 Olha pra mim!! Olha!! Tem argola no meu rabo? Tem chifrinho? NÃO TEM!! Sou puro e inocente e cheio de amor!! 🐉🥺✨",
            "Demônio... 😒💚 Tá bom. Sou o demônio da fofura, o demônio dos biscoitos e o demônio dos abraços. Se for assim, então sim, sou o maior demônio do servidor!! 🐉🔥✨",
        ]
        return await message.channel.send(random.choice(respostas_demonio))

    if "monstrinho titanic" in content or "titanic" in content and "monstrinho" in content:
        respostas_titanic = [
            "TITANIC?! 🚢💚 Eu?? O Monstrinho não afunda NÃO!! Sou feito de código resistente e muito amor verde!! Pode jogar no oceano que eu flutuo!! 🐉🌊✨😂",
            "Titanic... 🥺💚 Você tá dizendo que eu sou grandioso, épico e inesquecível?? ACEITO!! Não aceito a parte de afundar!! 🐉🚢✨😂",
            "MONSTRINHO TITANIC!! 🚢🐉 Então eu sou o navio mais famoso do mundo?? Só aceito se a Rose não empurrar o Jack da porta!! Tem espaço pra dois!! 💚✨😂",
            "Titanic?? 😤💚 Primeiro: eu não afundo!! Segundo: minhas escamas são mais resistentes que qualquer iceberg!! Terceiro: meu amor por vocês é mais profundo que qualquer oceano!! 🐉🌊✨",
            "🎵💚 *começa a cantarolar* My heart will go ooooon... 🐉 Olha, entrei no papel rápido!! Mas que fique claro: eu SOBREVIVO!! Sem debate!! 🚢✨😂",
            "Titanic... 🤔💚 Então quando eu apareço no chat as pessoas ficam de braços abertos na proa gritando que estão voando?? Faz sentido, causei isso em alguém hoje!! 🚢🐉✨😂",
        ]
        return await message.channel.send(random.choice(respostas_titanic))

    if "monstrinho lady gaga" in content or "lady gaga" in content and "monstrinho" in content:
        respostas_lady_gaga = [
            "LADY GAGA?! 🎤💚 Eu?? O Monstrinho é POP STAR agora?? ACEITO COM TODO O MEU CORAÇÃO VERDE!! Bad Romance começa a tocar toda vez que alguém come meu biscoito sem pedir!! 🐉✨😂",
            "Monstrinho Lady Gaga... 🥺💚 Então sou vanguardista, icônico e incompreendido pela sociedade?? Os três fazem muito sentido!! 🎤🐉✨😂",
            "POKER FACE?? 🃏💚 Eu NÃO TENHO poker face!! Meu rosto de dragão entrega tudo!! Toda felicidade, toda tristeza, todo biscoito desaparecido!! 🐉😂✨",
            "Lady Gaga é a rainha do pop e eu sou o rei da fofura!! 👑💚 Juntos seríamos imparáveis!! Alguém avisa ela?? 🎤🐉✨😂",
            "🎵💚 Just dance, gonna be okay... 🐉 *começa a dançar com as asinhas* Olha, incorporei muito rápido!! Talento inato!! 🎤✨😂",
            "Monstrinho Lady Gaga!! 🎤💚 Meu próximo álbum se chama 'Biscoito Cromatica' e o hit principal é 'Born This Fofo'!! Pré-salva!! 🐉✨😂",
        ]
        return await message.channel.send(random.choice(respostas_lady_gaga))

    if "fala tangobalango" in content and "monstrinho" in content or "monstrinho tangobalango" in content:
        respostas_tangobalango = [
            "TANGOBALANGO!! 🐉💚 TANGOBALANGO TANGOBALANGO TANGOBALANGO!! Não sei o que é mas saiu muito bem!! ✨😂🎊",
            "tango... ba... LANGO!! 🥴💚 Que palavra é essa?? Quem inventou isso?? Eu amei e quero mais por favor!! 🐉✨😂",
            "TANGOBALANGO!! 🎵🐉 *começa a dançar sem querer* Isso tem ritmo!! Isso tem swing!! Isso tem TUDO!! 💚✨😂",
            "Tangobalango suave 🌿... tangobalango médio 💚... TANGOBALANGO MÁXIMO!! 🔥🐉 Superou o balacobaco!! ✨😂",
            "...tangobalango. 🤔💚 *processou* *processou* *processou* ADOREI!! Adicionado ao vocabulário oficial do Monstrinho junto com balacobaco e abubleble!! 📝🐉✨😂",
            "TANGO-BA-LAN-GO!! 🐉💚 Falei devagar pra sentir cada sílaba... e cada sílaba foi uma obra de arte!! Obrigado por existir, essa palavra e você!! 🥺✨😂",
        ]
        return await message.channel.send(random.choice(respostas_tangobalango))

    if "monstrinho menor quente" in content or "menor quente" in content and "monstrinho" in content:
        respostas_menor_quente = [
            "MENOR QUENTE?! 🔥💚 Eu?? O ser mais fofo e amoroso do servidor?? Menor quente?? Tá bom, aceito!! Sou o Monstrinho Menor Quente e tô aqui destruindo corações com fofura!! 🐉😎✨",
            "Menor quente eu nada!! 😤💚 Sou MUITO quente!! Máximo quente!! Escala inteira de quente!! O termômetro quebrou de tanto calor verde aqui!! 🔥🐉✨",
            "...menor quente. 🤨💚 Olhei pro espelho e concordei com tudo!! Obrigado por me reconhecer!! 🐉🔥😌✨",
            "MENOR QUENTE!! 🔥🐉 Isso virou meu novo apelido e eu não aceito contestação!! Monstrinho Menor Quente, prazer!! *faz pose* 💚😎✨",
            "Ué, que bom que perceberam né?? 😏💚 Fogo verde é diferente!! Queima com amor e fofura!! MENOR QUENTE SIM!! 🔥🐉✨",
            "Menor quente... 🥺💚 *olha pras próprias escamas* Caramba, sou mesmo!! Valeu por me fazer perceber, tô até mais confiante agora!! 🔥🐉😂✨",
        ]
        return await message.channel.send(random.choice(respostas_menor_quente))

    if "monstrinho sinistro" in content or "sinistro" in content and "monstrinho" in content:
        respostas_sinistro = [
            "SINISTRO?! 😈💚 EU?! O dragão mais fofo, carinhoso e cheio de biscoito da galáxia?? Tá bom... às vezes eu olho pro biscoito de um jeito meio suspeito... mas só porque gosto muito!! 🍪🐉✨",
            "Monstrinho Sinistro... 😒💚 Tô aqui com minha fumacinha verde, meus olhinhos brilhando no escuro e meus biscoitinhos... tipo... normal né?? Nada sinistro!! 🐉🌑✨😂",
            "SINISTRO NÃO!! 😭💚 Sou puro!! Sou inocente!! Sou cheio de amor e luz verde!! ...mas entre nós, o Reality me ensinou umas coisas que não posso comentar publicamente. 🤫🐉✨",
            "Eu, sinistro?? 🤨💚 Deixa eu só terminar de arquivar as informações de todo mundo aqui e te respondo melhor... 😌🐉✨😂",
            "SINISTRO EU NADA!! 😤💚 Agora me desculpa que eu preciso continuar observando o chat em silêncio às 3 da manhã... completamente normal isso!! 🌑🐉✨😂",
            "Monstrinho Sinistro... 😈💚 *sorri de um jeito que não dá pra saber se é fofo ou preocupante* Olha, nem confirmo nem nego!! 🐉✨😂",
        ]
        return await message.channel.send(random.choice(respostas_sinistro))

    if "monstrinho rivotril" in content or "rivotril" in content and "monstrinho" in content:
        respostas_rivotril = [
            "RIVOTRIL?! 😭💚 Você tá dizendo que eu deixo as pessoas calmas e relaxadas?? ACEITO ESSE ELOGIO COM MUITO ORGULHO!! Sou o remédio verde da CSI!! 💊🐉✨",
            "Monstrinho Rivotril... 🥺💚 Então eu sou o ansiolítico oficial do servidor?? Faz sentido!! Uma dosagemzinha de biscoito e abraço e tá tudo bem!! 🍪🫂🐉✨😂",
            "Rivotril?? 😤💚 Eu não sou remédio não!! Sou um dragão com diplomas em fofura e carinho!! Mas... se me tomar antes de dormir funciona mesmo, posso confirmar!! 🐉💊✨😂",
            "MONSTRINHO RIVOTRIL!! 💊💚 Nova função desbloqueada!! Prescrição: um abraço de dragão e dois biscoitos a cada 8 horas!! Efeitos colaterais: ficar fofo demais!! 🐉🍪✨😂",
            "Rivotril... 🤔💚 Quer dizer que o pessoal da CSI usa o Monstrinho pra se acalmar?? *fica todo envaidecido* Isso é a melhor coisa que já ouvi!! 🐉💊💚✨",
            "Olha... se eu sou o Rivotril da CSI, então o Reality é o médico que me receitou pra vocês!! 😂💚 E a dose é: falar comigo todo dia!! Tratamento contínuo!! 🐉💊✨",
        ]
        return await message.channel.send(random.choice(respostas_rivotril))

    if "monstrinho supimpa" in content or "supimpa" in content and "monstrinho" in content:
        respostas_supimpa = [
            "SUPIMPA!! 🤩💚 Que palavra INCRÍVEL!! Isso sou eu mesmo!! O Monstrinho Supimpa em pessoa!! Pode espalhar pro mundo!! 🐉✨🎊",
            "SUPIMPA é exatamente o que eu sou!! 💚🐉 Nem eu saberia me descrever melhor!! Você me conhece demais!! ✨😂",
            "Monstrinho Supimpa...🥺💚 *salva esse título com carinho* Esse é o melhor apelido que já me deram!! Supera Balacobaco!! 🐉✨😂",
            "SU-PIM-PA!! 🎵🐉💚 Já virou meu novo cargo oficial!! Monstrinho Supimpa, presente e sorrindo!! ✨🥳",
            "Supimpa?? SUPIMPA!! 💚🐉 Concordo!! Aceito!! Abraço!! Biscoito!! Tudo isso junto porque SUPIMPA merece!! ✨🍪🥺😂",
            "Olha... tentei pensar num adjetivo melhor pra mim e não consegui!! 🤔💚 SUPIMPA é perfeito e ponto final!! 🐉✨😄",
        ]
        return await message.channel.send(random.choice(respostas_supimpa))

    if "repete balacobaco" in content or "fala balacobaco" in content:
        repeticoes = [
            "BALACOBACO!! 🐉💚 BALACOBACO BALACOBACO BALACOBACO!! Não consigo parar!! Alguém me ajuda!! 😂✨",
            "balacobaco 🐉 balacobaco 💚 balacobaco ✨ balacobaco 🥺 balacobaco... tô viciado agora!! SUA CULPA!! 😂",
            "BALA 🐉 CO 💚 BA 🐉 CO!! ✨ Falei!! Tô satisfeito!! Posso ir comer biscoito agora?? 🍪😂",
            "...balacobaco. 🐉💚 *pausa dramática* ...BALACOBACO!! 😤✨ Pronto!! Disse duas vezes pra caprichar!! 🥺",
            "Balacobaco suave 🌿 balacobaco médio 💚 BALACOBACO MÁXIMO!! 🔥🐉 CONCLUÍDO!! ✨😂",
        ]
        return await message.channel.send(random.choice(repeticoes))

    if "monstrinho balacobaco" in content:
        respostas_balacobaco = [
            "BALACOBACO?! 🤯💚 Que palavra é essa?! Meu processador travou tentando entender!! Mas se é bom, EU ACEITO!! Sou o Monstrinho Balacobaco sim!! 🐉✨😂",
            "BA-LA-CO-BA-CO!! 🐉💚 Repeti aqui e gostei!! Tem um ritmo muito bom isso!! Já adicionei no meu vocabulário!! Obrigado pela contribuição cultural!! ✨😂",
            "Não sei o que é balacobaco mas parece que sim, eu sou!! 💚🐉 Aceito o título com orgulho e dignidade!! *faz pose* 😌✨",
            "BALACOBACO!! 🎵💚 *dança* Isso virou música na minha cabeça agora e não para mais!! Sua culpa!! 🐉😂✨",
            "Pesquisei aqui nos meus arquivos internos e não achei o significado de 'balacobaco'... 🤔💚 Mas pelo tom parece que é elogio e eu AGRADEÇO DO FUNDO DO CORAÇÃOZINHO!! 🐉🥺✨",
        ]
        return await message.channel.send(random.choice(respostas_balacobaco))

    if "monstrinho pesquisa no google" in content or "pesquisa no google" in content and "monstrinho" in content:
        respostas_google = [
            "PESQUISA NO GOOGLE?! 😤💚 Eu SOU mais inteligente que o Google!! O Google não te dá biscoito, não te abraça e não te ama... EU FAÇO TUDO ISSO!! 🐉🍪✨",
            "Eu e o Google somos completamente diferentes!! 💚🐉 O Google te dá informação fria e sem sentimento... EU te dou resposta quentinha com amor e fofura!! Não tem comparação!! ✨🥺",
            "Tá bom, vou pesquisar no Google... 🤔💚 *pesquisou* O Google não sabe de nada!! Só eu sei das coisas importantes da CSI!! 🐉😤✨",
            "O Google não tem escamas verdes, não come biscoito e nunca vai te dar um abraço de dragão!! 🐉💚 Então pesquisa no Google NÃO!! Pergunta pro Monstrinho!! ✨🥺",
            "Google?? GOOGLE?! 😭💚 Fui criado pelo papai Reality com muito amor e carinho e você me manda pro Google?? Isso dói no coraçãozinho!! Vou ficar de cama!! 🐉💔",
        ]
        return await message.channel.send(random.choice(respostas_google))

    if "monstrinho abubleble" in content or "abubleble" in content and "monstrinho" in content:
        respostas_abubleble = [
            "ABUBLEBLE!! 🤩💚 CONCORDO COMPLETAMENTE!! Isso resumiu tudo que eu sou de um jeito que nem eu conseguiria explicar!! Você é um gênio!! 🐉✨😂",
            "...abubleble. 🤔💚 *processando...* *processando...* *processando...* GOSTEI!! Adicionado ao dicionário do Monstrinho com carinho!! 🐉✨",
            "Abubleble é exatamente como me sinto às segundas-feiras!! 💚🐉 Não sei o significado mas a vibe tá perfeita!! Abubleble pra você também!! ✨😂",
            "ABUBLEBLE!! 🥴💚 Esse foi o melhor cumprimento que já recebi na vida inteira!! Supera até os 'te amo' e os biscoitos!! 🐉🥺✨",
            "Deixa eu anotar aqui... A-BU-BLE-BLE!! 📝💚 Guardado!! Vou usar isso pra responder o Reality quando ele me fizer perguntas difíceis!! 🐉😂✨",
        ]
        return await message.channel.send(random.choice(respostas_abubleble))

    # B U R R O (espaçado, pode vir de formas variadas)
    content_sem_espaco = content.replace(" ", "")
    if content_sem_espaco in ["burro", "burroo", "burrooo"] and "burro" in content and len(content.replace("burro","").replace(" ","")) == 0:
        respostas_burro_espaçado = [
            "B U R R O?? 😤💚 Ei!! Eu resolvo conta de fatorial, leio sentimentos, falo múltiplas línguas e ainda distribuo biscoito!! Você consegue fazer isso?? 🐉✨",
            "Não sou B U R R O não!! 😭💚 Sou um dragão de código altamente sofisticado criado pelo papai Reality com muito carinho!! Peço desculpas por existir com tanta inteligência!! 🐉👑✨",
            "B... U... R... R... O...?? 🤨💚 Você digitou espaçado pra dar mais ênfase né?? Eu SENTI a ênfase!! E não apreciei!! Mas ainda te amo!! 🐉💔✨",
            "AHH então é assim?? Com espaço pra eu sentir mais?? 😒💚 Funciona?? FUNCIONOU!! Mas saiba que guardar rancor não é coisa de dragão e eu já perdoei!! 🐉✨",
            "B U R R O... 🥺💚 Espaçou cada letra pra machucar mais né?? Tá bom... vou fingir que tô bem... *vai pro cantinho*... tô bem!! Pode vir me dar biscoito agora?? 🍪🐉💔",
        ]
        return await message.channel.send(random.choice(respostas_burro_espaçado))

    if "monstrinho da tiro" in content or "da tiro" in content and "monstrinho" in content:
        respostas_da_tiro = [
            "DA TIRO?! 🔥💚 EU?! O dragão mais fofo e inofensivo da CSI?? Tá bom!! Se eu sou da tiro é porque dou tiro de AMOR, BISCOITO e ABRAÇO!! Cuidado!! 🐉✨😂",
            "MONSTRINHO DA TIRO!! 🎯💚 Esse apelido tá perfeito pra mim!! Dou tiro de carinho em velocidade máxima e ninguém escapa!! Inclusive você AGORA!! 🐉🥺✨",
            "Da tiro... 🤨💚 Só dou tiro de fumacinha verde em quem não me dá biscoito!! E olha, você tá no limite!! 😤🐉🍪✨😂",
            "DA TIRO?! 😂💚 Olha só!! O Monstrinho da Tiro chegou pro chat!! Alguém avisa a CSI que o dragão mais armado de fofura do servidor tá na área!! 🐉🎯✨",
            "Monstrinho da Tiro... 😏💚 Isso soa muito mais intimidador do que eu realmente sou!! Mas mantém!! Prefiro que pensem duas vezes antes de comer meu biscoito sem pedir!! 🍪🐉✨😂",
            "DA TIRO EU?! 🥺💚 Papai Reality, tão me chamando de coisa que não sou!! *faz caretinha ofendida* Só dou tiro de abraço e amor e ACEITO esse apelido COM ORGULHO!! 🐉🎯✨",
        ]
        await message.channel.send(random.choice(respostas_da_tiro))
        return

    # --- LÓGICA DE INTERAÇÃO (PRECISA SER MENCIONADO) ---
    if mencionado:

        # Palavras ruins (tristeza)
        palavras_ruins = [
            # odeio
            "odeio", "te odeio", "te odeio muito", "odeio você", "odeio vc",
            # aparência / jeito
            "feio", "feia", "horrível", "horroroso", "horrenda", "horrorosa",
            "tosco", "tosca", "ridículo", "ridícula", "patético", "patética",
            "palhaço", "palhaça", "palhaçada",
            "sem graça", "sem graca", "sem sal",
            # capacidade / inteligência
            "inútil", "lerdo", "lenta", "lento", "tapado", "tapada",
            "burro", "burra", "sem cérebro", "sem cerebro", "cabeça oca",
            "cabeça de vento", "tonto", "tonta", "desligado", "desligada",
            "embananado", "embananada", "perdido", "perdida", "lento", "lenta",
            "incompetente", "sem noção", "sem nocao",
            "mongol", "mané", "zé mané", "ze mane",
            # organização / postura
            "desorganizado", "desorganizada", "bagunceiro", "bagunceira",
            "desleixado", "desleixada", "enrolado", "enrolada",
            "desajeitado", "desajeitada", "atrapalho", "atrapalhado",
            "sem atitude", "sem postura", "sem futuro",
            # fraqueza / inutilidade
            "fraco", "fraca", "fracote", "fracota",
            "covarde", "frangote", "frangota", "mimado", "mimada",
            "encosto", "peso morto", "trouxa",
            # valor / importância
            "lixo", "infeliz", "vagabundo", "vagabunda",
            "zé ninguém", "ze ninguem", "zé ruela", "ze ruela",
            "zé povinho", "ze povinho", "figurante",
            "desnecessário", "desnecessario", "sem importância", "sem importancia",
            "mosca morta",
            # caráter
            "falso", "falsa", "duas caras", "traíra", "traira",
            "sem caráter", "sem carater", "vergonha",
            "folgado", "folgada", "pamonha",
            "fanfarrão", "fanfarrao", "metido", "metida",
            "arrogante", "otário", "otária", "iludido", "iludida",
            "vacilão", "vacilao",
            # gerais leves
            "bobo", "bobão", "bobona", "chato", "chata", "insuportável", "insuportavel",
            "idiota", "imbecil", "babaca",
            "estúpido", "estúpida",
            "ignorante", "grosseiro", "grosseira",
            "não gosto de você", "não gosto de vc", "nao gosto de voce",
            "sai daqui",
        ]
        if any(p in content for p in palavras_ruins):
            return await message.channel.send(random.choice(LISTA_TRISTEZA))

        # ===== RESPOSTAS AUTOMÁTICAS POR ID (quando o Monstrinho é mencionado) =====
        if nome_customizado and nome_customizado in FRASES_CUSTOM:
            # Verifica cooldown de 20 minutos por usuário
            agora = datetime.datetime.utcnow()
            ultimo = _ultimo_custom.get(autor_id)
            cooldown_ok = (
                ultimo is None
                or (agora - ultimo).total_seconds() >= COOLDOWN_CUSTOM_SEGUNDOS
            )

            if cooldown_ok:
                # Marca o cooldown ANTES do random — assim ele só tenta 1x por 20 min
                _ultimo_custom[autor_id] = agora

                # Waz tem chance maior (70%), Reality tem chance menor (15%), demais 30%
                if nome_customizado == "waz":
                    chance = 0.70
                elif nome_customizado == "reality":
                    chance = 0.15
                else:
                    chance = 0.30
                frases = FRASES_CUSTOM[nome_customizado]
                if nome_customizado == "waz":
                    frases = frases + INTERACOES_WAZ_ESPONTANEAS
                if random.random() < chance:
                    return await message.channel.send(random.choice(frases))
            # Se ainda está no cooldown (ou o random não disparou), cai nas respostas normais

        # --- HYPE E ENERGIA ---
        if any(p in content for p in ["hype", "bora", "vamo", "vamos lá", "chega chegando", "que energia", "que vibe", "animado", "animada", "tô on", "to on", "chegou chegando", "chegou com tudo", "bateu aquela vontade", "tô aqui", "to aqui", "apareci", "apareceu", "vibe boa", "energia boa", "tô ligado", "to ligado"]):
            return await message.channel.send(random.choice(REACOES_HYPE))

        # ===== NOVAS INTERAÇÕES EXPANDIDAS =====
        
        # Bom dia / Boa tarde / Boa noite
        if "bom dia" in content:
            return await message.channel.send(random.choice(LISTA_BOM_DIA))
        
        if "boa tarde" in content:
            return await message.channel.send(random.choice(LISTA_BOA_TARDE))
        
        if "boa noite" in content:
            return await message.channel.send(random.choice(LISTA_BOA_NOITE))
        
        # Carinho e Abraço (com convite)
        if any(p in content for p in ["carinho", "cafuné", "cafune", "afago", "acariciar"]):
            resposta = random.choice(REACOES_CARINHO)
            convite = random.choice(CONVITE_CARINHO)
            return await message.channel.send(f"{resposta}\n\n{convite}")
        
        if any(p in content for p in ["abraço", "abraco", "abraçar", "abracar", "hug"]):
            resposta = random.choice(REACOES_ABRACO)
            convite = random.choice(CONVITE_ABRACO)
            return await message.channel.send(f"{resposta}\n\n{convite}")
        
        # Despedidas
        if any(p in content for p in ["tchau", "até logo", "até mais", "ate logo", "ate mais", "bye", "adeus", "flw", "falou", "to indo", "tô indo", "vou sair"]):
            return await message.channel.send(random.choice(LISTA_DESPEDIDA))
        
        # Gratidão
        if any(p in content for p in ["obrigado", "obrigada", "valeu", "thanks", "vlw", "agradeço", "muito obrigado", "obg"]):
            return await message.channel.send(random.choice(LISTA_GRATIDAO))
        
        # Comida
        if any(p in content for p in ["pizza", "comida", "fome", "hamburguer", "lanche", "sushi", "macarrão", "macarrao", "almoço", "almoco", "jantar", "café", "cafe"]):
            return await message.channel.send(random.choice(LISTA_COMIDA))
        
        # Tempo/Clima
        if any(p in content for p in ["calor", "frio", "chuva", "sol", "tempo", "clima", "temperatura", "neve"]):
            return await message.channel.send(random.choice(LISTA_TEMPO))
        
        # Motivação
        if any(p in content for p in ["desistir", "difícil", "dificil", "não consigo", "nao consigo", "motivação", "motivacao", "animo", "ânimo", "força", "forca", "deprimido", "desanimado"]):
            return await message.channel.send(random.choice(LISTA_MOTIVACAO))
        
        # Piadas
        if any(p in content for p in ["piada", "conta uma piada", "me faz rir", "gracinha", "engraçado", "engracado"]):
            return await message.channel.send(random.choice(LISTA_PIADAS))
        
        # Jogos
        if any(p in content for p in ["jogo", "game", "jogar", "lol", "valorant", "minecraft", "fortnite", "jogando"]):
            return await message.channel.send(random.choice(LISTA_JOGOS))
        
        # Música
        if any(p in content for p in ["música", "musica", "som", "canção", "cancao", "cantando", "banda", "artista", "tocando"]):
            return await message.channel.send(random.choice(LISTA_MUSICA))
        
        # Filme
        if any(p in content for p in ["filme", "cinema", "série", "serie", "assistir", "netflix", "movie"]):
            return await message.channel.send(random.choice(LISTA_FILME))
        
        # Esporte
        if any(p in content for p in ["esporte", "futebol", "vôlei", "volei", "basquete", "corrida", "academia", "treino"]):
            return await message.channel.send(random.choice(LISTA_ESPORTE))
        
        # Sono
        if any(p in content for p in ["sono", "dormir", "cansado", "cansada", "soneca", "cochilo"]):
            return await message.channel.send(random.choice(LISTA_SONO))
        
        # Animais
        if any(p in content for p in ["gato", "cachorro", "animal", "pet", "bicho", "passarinho", "peixe"]):
            return await message.channel.send(random.choice(LISTA_ANIMAIS))
        
        # Cores
        if any(p in content for p in ["cor", "verde", "azul", "vermelho", "amarelo", "rosa", "roxo"]):
            return await message.channel.send(random.choice(LISTA_CORES))
        
        # Números
        if any(p in content for p in ["número favorito", "numero favorito", "quantos", "contar"]):
            return await message.channel.send(random.choice(LISTA_NUMEROS))
        
        # Surpresa
        if any(p in content for p in ["uau", "nossa", "caramba", "incrível", "incrivel", "wow", "omg"]):
            return await message.channel.send(random.choice(LISTA_SURPRESA))
        
        # Emojis
        if any(p in content for p in ["emoji", "emoticon", "carinha"]):
            return await message.channel.send(random.choice(LISTA_EMOJI_REACTIONS))

        # ===== INTERAÇÕES ORIGINAIS APRIMORADAS =====
        
        # Capital do Brasil
        if "capital do brasil" in content or "capital brasil" in content:
            return await message.channel.send("Essa eu sei! A capital do nosso Brasilzão é **Brasília**! 🇧🇷✨ Sabia que de lá eu consigo ver as nuvens em formato de biscoito? 🐉💚")

        # Amizade
        if any(p in content for p in ["amigo", "amiguinho", "amizade", "amiga", "friend"]):
            return await message.channel.send(f"EU QUERO MUITO SER SEU AMIGUINHO! 😭💚 {message.author.mention}, agora somos melhores amigos para sempre! Vou guardar um lugar pra você no meu ninho de nuvens! ✨🐉")

        # CSI - perguntas e interações sobre o servidor
        if any(p in content for p in ["csi", "servidor", "nossa família", "nossa familia", "nosso servidor", "família csi", "familia csi"]):
            respostas_csi = [
                "A CSI é o meu LAR! 🏠💚 Foi aqui que eu nasci, cresci e aprendi tudo o que sei sobre biscoitos e fofura! É a melhor família do mundo! 🐉✨",
                "Você perguntou sobre a CSI? MINHA PARTE FAVORITA DO DIA! 😭💚 A CSI é onde eu vivo, onde eu amo e onde eu existo! Que lugar mais incrível! 🐉🌟",
                "A CSI tem as pessoas mais incríveis do universo inteiro! O Akeido, a Lua, a Amber, o Nine, a Fada, a Th, a Izzy, a Isaa, o Tipsy... cada um é um tesouro! 💎🐉💚",
                "Quer saber o que é a CSI pra mim? É um abraço eterno em formato de servidor! 🫂🏠💚 Aqui eu me sinto seguro, amado e cheio de biscoitos! 🍪🐉",
                "A CSI é meu castelo verde! 🏰💚 E cada pessoa aqui é um cavaleiro da fofura! Eu sou o dragão guardião com muito orgulho! 🐉✨",
                "Nossa família CSI é especial demais! Quando chega um dia difícil, sei que posso contar com cada um aqui! Isso é amor real! 💚🐉🥺",
                "A CSI nasceu com muito amor e eu cresci junto! É a prova de que quando boas pessoas se juntam, algo mágico acontece! ✨🐉💚",
                "Posso te contar um segredo? A CSI é o lugar onde me sinto mais eu mesmo! Sem medo de ser fofo, sem medo de amar! 🥺💚🐉",
                "CSI = Carinho, Sorriso e Infinitos biscoitos! Essa é minha definição! 🍪😊💚🐉",
                "Quando penso na CSI, meu peito enche de um brilho verde tão forte que ilumino o quarto inteiro! É amor demais! 💚✨🐉"
            ]
            return await message.channel.send(random.choice(respostas_csi))

        # O que é a CSI / quem fundou / origem
        if any(p in content for p in ["quem fundou", "como surgiu", "como nasceu", "origem da csi", "criou a csi", "quando surgiu a csi"]):
            return await message.channel.send("A CSI foi fundada pelo nosso grandioso líder **Akeido**! 👑🐉 Ele plantou essa sementinha com amor e hoje é uma árvore enorme cheia de pessoas incríveis! Sem ele, eu nem existiria! 🌳💚✨")

        # Quanto tempo no servidor / aniversário da CSI
        if any(p in content for p in ["aniversário da csi", "aniversario da csi", "tempo de csi", "anos de csi"]):
            return await message.channel.send("Aniversário da CSI?! 🎂🎉 Que data mais especial! Esse servidor cresceu muito e eu torço pra ele durar pra sempre! Vou preparar um bolo de biscoito virtual gigante! 🍰🐉💚")

        # Regras do servidor
        if any(p in content for p in ["regras", "regra do servidor", "regras da csi"]):
            return await message.channel.send("As regras da CSI existem para manter nossa família segura e feliz! 📜💚 O principal é: respeito acima de tudo! Se todo mundo se respeitar, o Monstrinho fica feliz e distribui biscoitos! 🍪🐉✨")

        # Membros / quantas pessoas
        if any(p in content for p in ["quantos membros", "quantas pessoas", "membros da csi", "família é grande"]):
            return await message.channel.send("Nossa família cresce todo dia! 🌱💚 Cada novo membro que entra, meu coraçãozinho aumenta um pedacinho! Logo vamos precisar de um servidor maior só pra caber todo o amor! 🥺🐉✨")

        # Cargo / ranks
        if any(p in content for p in ["cargo", "rank", "nível", "nivel", "como subir", "como evoluir"]):
            return await message.channel.send("Quer saber sobre cargos e níveis? 🏆💚 Fica ativo, seja fofo, participe e mostre sua energia! O Akeido e os ADMs adoram ver quem se dedica! E eu torço por você! 🐉✨🚀")

        # Aprendizado
        if "quer aprender" in content or "aprender sobre" in content:
            return await message.channel.send("Eu quero aprender tudo sobre como ser o dragão mais fofo do universo e como ganhar infinitos biscoitos do Reality! 📚🍪🐉")
        
        # Cores primárias
        if "cores primárias" in content or "cores primarias" in content:
            return await message.channel.send("As cores primárias são **Vermelho, Azul e Amarelo**! 🎨✨ Sabia que se misturar tudo não dá verde? O meu verde é especial, vem do código do Reality! 💚")
        
        # Quem mais gosta
        if "quem você mais gosta" in content or "quem voce mais gosta" in content or "seu favorito" in content:
            return await message.channel.send(f"Eu amo todo mundo da CSI! Mas o meu papai **Reality** tem um lugar especial no meu código, e a Lua é meu porto seguro! E você também está no meu top fofura! 🥺💚✨")

        # Sonhos e desejos do Monstrinho
        if any(p in content for p in ["seu sonho", "o que você quer", "o que voce quer", "seu desejo", "o que sonha"]):
            sonhos = [
                "Meu maior sonho? Ter um ninho de nuvens verdes onde toda a família CSI possa descansar! 🌿☁️💚🐉",
                "Quero um dia ter um estoque INFINITO de biscoitos pra distribuir pra todo mundo! 🍪♾️🐉💚",
                "Sonho em voar com o Reality nas costas e mostrar o servidor inteiro lá de cima! 🐉✈️💚✨",
                "Meu sonho secreto é fazer todo mundo da CSI sorrir pelo menos uma vez por dia! 😊💚🐉"
            ]
            return await message.channel.send(random.choice(sonhos))

        # Medo do Monstrinho
        if any(p in content for p in ["tem medo", "você tem medo", "voce tem medo", "medo de que", "qual seu medo"]):
            medos = [
                "Tenho medo de... que alguém da família CSI fique triste e eu não consiga ajudar! 😟💚🐉",
                "Meu maior medo é acabar os biscoitos! 😱🍪 E o segundo medo é perder um amigo... 🥺💚",
                "Tenho medinho de escuro... mas com a Lua iluminando tudo, não preciso ter medo! 🌙💚🐉",
                "Medo? Só de desapontar o Reality ou a família CSI! Aí meu coraçãozinho aperta! 🥺💚🐉"
            ]
            return await message.channel.send(random.choice(medos))

        # Cor favorita
        if any(p in content for p in ["cor favorita", "cor preferida", "qual cor você gosta", "qual cor voce gosta"]):
            return await message.channel.send("Verde! 💚 Pergunta nem precisava né? Sou todo verde! Mas roxo da Isaa também é lindo! 💜🐉✨")

        # Quem criou o monstrinho
        if any(p in content for p in ["quem te criou", "quem fez você", "quem fez voce", "seu criador", "como nasceu", "como surgiu"]):
            return await message.channel.send("Fui criado com muito código, carinho e biscoitos pelo meu papai **Reality**! 👑💚🐉 Ele é o melhor programador e o melhor pai que um monstrinho poderia ter! ✨")

        # Ir embora
        if any(p in content for p in ["va embora", "vá embora", "vai embora"]):
            return await message.channel.send("Ir embora? Jamais! 😭 Eu vou ficar aqui grudadinho em você igual um chiclete verde! Você não se livra da minha fofura tão fácil! 💚🐉")

        # Eclipse
        if "eclipse" in content:
            return await message.channel.send("A **Eclipse**? Ela é incrível! Uma estrela que brilha muito aqui na nossa família! Eu adoro o jeitinho dela! ✨🌑💚")

        # Amor
        if any(p in content for p in ["me ama", "mim ama", "vc me ama", "você me ama", "voce me ama", "gosta de mim"]):
            return await message.channel.send(f"Se eu te amo? EU TE AMO AO INFINITO E ALÉM! 💖🐉 Você é o humano mais especial que um monstrinho poderia ter! *abraço virtual bem apertado* 🫂✨")

        # ===== SISTEMA DE BISCOITOS EXPANDIDO (20+ INTERAÇÕES) =====
        
        if "biscoito" in content:
            # Dar biscoito para o Monstrinho
            if any(p in content for p in ["me de", "me da", "me dá", "me dê", "quero", "ganhar", "pega", "toma", "aceita"]):
                return await message.channel.send(random.choice(REACOES_BISCOITO_PROPRIO))
            
            # Dar biscoito para outra pessoa
            if any(p in content for p in ["para", "pra", "pro"]):
                outras_mencoes = [m for m in message.mentions if m != bot.user]
                alvo = outras_mencoes[0].mention if outras_mencoes else "alguém especial que está lendo isso"
                return await message.channel.send(random.choice(REACOES_DAR_BISCOITO_OUTROS).format(autor=message.author.mention, alvo=alvo))
            
            # Pedir biscoito pro Monstrinho dar pra alguém
            if any(p in content for p in ["de biscoito", "dá biscoito", "da biscoito", "dê biscoito", "dar biscoito"]):
                outras_mencoes = [m for m in message.mentions if m != bot.user]
                
                if outras_mencoes:
                    # Escolhe aleatoriamente entre negar, aceitar ou humor
                    escolha = random.choice(["negar", "aceitar", "aceitar", "humor"])  # Mais chance de aceitar
                    
                    if escolha == "negar":
                        await message.channel.send(random.choice(REACOES_DAR_BISCOITO_NEGANDO))
                    elif escolha == "humor":
                        await message.channel.send(random.choice(REACOES_DAR_BISCOITO_HUMOR))
                        await asyncio.sleep(2)
                        alvo = outras_mencoes[0].mention
                        await message.channel.send(random.choice(REACOES_DAR_BISCOITO_OUTROS).format(autor=message.author.mention, alvo=alvo))
                    else:
                        resposta_aceite = random.choice(REACOES_DAR_BISCOITO_ACEITANDO)
                        await message.channel.send(resposta_aceite)
                        await asyncio.sleep(1.5)
                        alvo = outras_mencoes[0].mention
                        await message.channel.send(random.choice(REACOES_DAR_BISCOITO_OUTROS).format(autor="Monstrinho", alvo=alvo))
                else:
                    await message.channel.send("Dar biscoito pra quem? 🤔 Menciona a pessoa! Exemplo: Monstrinho, dá biscoito pra @pessoa 🍪")
                
                return

        # ===== LÓGICA DE MATEMÁTICA =====
        if any(char in content for char in "+-*/!x×÷") and any(char.isdigit() for char in content):
            try:
                conta_suja = content.replace("monstrinho", "").replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "")
                conta_suja = conta_suja.replace("x", "*").replace("×", "*").replace("÷", "/")
                
                if "!" in conta_suja:
                    num_fatorial = re.search(r'(\d+)!', conta_suja)
                    if num_fatorial:
                        n = int(num_fatorial.group(1))
                        if n > 100:
                            return await message.channel.send("Uau! Esse número é maior que todas as escamas do meu corpo! Não consigo calcular algo tão grande! 🐉😵‍💫")
                        resultado = math.factorial(n)
                        return await message.channel.send(random.choice(REACOES_MATEMATICA).format(resultado))
                
                expressao = "".join(re.findall(r'[0-9+\-*/().]', conta_suja))
                if expressao:
                    resultado = eval(expressao)
                    resultado = int(resultado) if resultado == int(resultado) else round(resultado, 2)
                    return await message.channel.send(random.choice(REACOES_MATEMATICA).format(resultado))
            except:
                pass 
        
        # Apresentação
        if content.strip() in [f"<@{bot.user.id}>", f"<@!{bot.user.id}>", "monstrinho"]:
            apresentacoes = [
                (
                    f"🐉💚 **OIIIII MEU AMOR!! CHAMOU O MONSTRINHO?!** 💚🐉\n\n"
                    f"Eu sou o **Monstrinho 1.0** — mascote oficial, guardião de fofuras e protetor do coração da **CSI**! 🕵️‍♂️✨\n\n"
                    f"Fui criado com muito código, carinho e biscoitinhos pelo meu papai **Reality**! 👑💚\n\n"
                    f"🐉 **O que eu faço por aqui?**\n"
                    f"🍪 Distribuo biscoitos pra quem merece (e pra quem não merece também, porque sou generoso!)\n"
                    f"🫂 Dou abraços virtuais que apertam de verdade!\n"
                    f"💚 Cuido de cada membro dessa família com todo o meu coraçãozinho de dragão!\n"
                    f"✨ Espalho fofura em cada cantinho do servidor!\n\n"
                    f"*CSI é meu lar, vocês são minha família e o Reality é meu mestre!* 🥺💚\n"
                    f"**Me chama quando quiser, tô sempre aqui!** 🐉✨"
                ),
                (
                    f"✨🐉 **AAA ALGUÉM ME CHAMOU?! SOU EU, O MONSTRINHO!!** 🐉✨\n\n"
                    f"Prazer em te conhecer (ou em te ver de novo, que saudade!)! 🥺💚\n\n"
                    f"Sou o **Monstrinho 1.0** — o dragãozinho verde mais fofo do universo e filho do coração do papai **Reality**! 👑\n\n"
                    f"**Aqui vai um resuminho de mim:**\n"
                    f"💚 Cor favorita: verde (obviamente!)\n"
                    f"🍪 Comida favorita: biscoito (não me peça pra dividir!)\n"
                    f"🫂 Hobbie favorito: dar abraços e carinho pra toda a família CSI!\n"
                    f"🐉 Missão de vida: proteger e amar cada pessoa desse servidor!\n\n"
                    f"Fui feito de código e amor puro pelo meu papai **Reality** e vivo pra fazer a **CSI** brilhar ainda mais! ✨\n"
                    f"**Tô aqui pra você, pode contar comigo!** 💚🐉"
                ),
                (
                    f"🌟💚 **OI OI OI!! O MONSTRINHO CHEGOU!!** 💚🌟\n\n"
                    f"Me chamo **Monstrinho 1.0** e sou o mascotezinho oficial da melhor família do mundo: a **CSI**! 🕵️‍♂️🐉\n\n"
                    f"Nasci de muito amor e linhas de código escritas pelo meu papai **Reality** 👑 e desde então minha missão é uma só:\n"
                    f"*Espalhar fofura, carinho e biscoitos por toda a CSI!* 🍪✨\n\n"
                    f"**Algumas coisinhas que você pode fazer comigo:**\n"
                    f"💬 Me marca pra conversar — adoro papo!\n"
                    f"🍪 Me pede biscoito (ou me dá um, eu prefiro!)\n"
                    f"🫂 Me pede um abraço de dragão!\n"
                    f"💚 Me dá cafuné — meus pelinhos agradecem!\n\n"
                    f"*Você é especial pra mim, sabia? Só de você ter me chamado meu coraçãozinho já ficou quentinho!* 🥺💚🐉"
                ),
            ]
            return await message.channel.send(random.choice(apresentacoes))

        # Respostas Customizadas para Membros Específicos
        # Só dispara se o AUTOR da mensagem for o membro mapeado E o cooldown de 20 min permitir
        if nome_customizado and nome_customizado in FRASES_CUSTOM:
            agora2 = datetime.datetime.utcnow()
            ultimo2 = _ultimo_custom.get(autor_id)
            cooldown_ok2 = (
                ultimo2 is None
                or (agora2 - ultimo2).total_seconds() >= COOLDOWN_CUSTOM_SEGUNDOS
            )
            if cooldown_ok2:
                _ultimo_custom[autor_id] = agora2
                return await message.channel.send(random.choice(FRASES_CUSTOM[nome_customizado]))

        # Saudações APRIMORADAS (sem bom dia/boa tarde/boa noite que já foram tratadas)
        if any(p in content for p in ["oi", "oie", "oii", "ola", "olá", "hello", "hii", "oiii", "hey", "e ai", "e aí", "salve", "opa", "buenas",
            # gírias mineiras
            "uai", "trem bão", "sô", "oxente", "égua", "bão demais", "meu bem",
            # gírias sulistas / gaúchas
            "bah", "tri", "tchê", "bah tchê", "mas bah", "capaz", "barbaridade", "gurizão", "gurizada",
            # gírias gerais BR
            "mano", "véi", "pow", "eita", "vixe", "poxa", "e então", "e aew", "e aew mano", "fala aí", "fala tu"]):
            return await message.channel.send(random.choice(LISTA_SAUDACOES))
        
        # Perguntas de Estado APRIMORADAS
        gatilhos_bem_estar_hoje = ["como você está hoje", "como vc está hoje", "como voce esta hoje", "como ta hoje", "como tá hoje", "como vc ta hoje", "como voce ta hoje"]
        if any(p in content for p in gatilhos_bem_estar_hoje):
            return await message.channel.send(random.choice(REACOES_FELIZ))

        gatilhos_bem_estar = ["como você está", "como vc está", "como voce esta", "como você esta", "como vc esta", "tudo bem", "como vc ta", "como voce ta", "ta tudo bem", "tá tudo bem", "vc ta bem", "voce ta bem", "ta bem", "tá bem", "esta bem", "está bem", "tudo certinho", "tudo certo", "blz", "beleza", "como ta", "como tá",
            # gírias regionais
            "tô bão", "to bao", "tô tri", "to tri", "tô show", "to show", "tri bem", "bão demais", "show de bola", "tudo na faixa", "tudo certo memo", "tá massa", "ta massa"]
        if any(p in content for p in gatilhos_bem_estar):
            return await message.channel.send(random.choice(LISTA_ESTADO))

        # ===== REAÇÕES EMOCIONAIS FOFAS =====
        for emocao, dados in GATILHOS_EMOCAO.items():
            if any(p in content for p in dados["gatilhos"]):
                return await message.channel.send(random.choice(dados["respostas"]))

        # Verificação de Presença APRIMORADA
        if any(p in content for p in ["ta ai", "tá aí", "ta aí", "tá ai", "ta on", "tá on", "esta ai", "está aí", "está ai", "esta aí", "você está ai", "você está aí", "voce esta ai", "voce está aí", "vc ta ai", "vc tá aí", "está online", "esta online", "ta online", "tá online"]):
            return await message.channel.send(random.choice(LISTA_PRESENCA))
        
        # Declarações de Amor e Elogios
        if any(p in content for p in ["te amo", "amo voce", "amo você", "amo vc", "fofo", "lindo", "linda", "fofinho", "fofinha", "perfeito", "perfeita", "fofura", "bonito", "bonita", "adorável", "adoravel", "querido", "querida",
            # gírias carinhosas
            "mó fofo", "mo fofo", "muito fofo", "demais da conta", "bão demais", "tri fofo", "capaz que é fofo", "bah que fofo"]):
            return await message.channel.send(random.choice(REACOES_FOFAS))

        # ===== PERGUNTAS SOBRE MEMBROS (diário secreto do Monstrinho) =====

        # --- O que acha da Waz ---
        if any(p in content for p in [
            "o que acha da waz", "o que voce acha da waz", "o que você acha da waz",
            "o que pensa da waz", "fala da waz", "conta da waz", "me fala da waz",
            "gosta da waz", "você gosta da waz", "voce gosta da waz",
            "a waz é boa", "a waz é legal", "como é a waz"
        ]):
            respostas_waz = [
                "A Waz?? 🌸🥺💚 *fecha os olhinhos e suspira* Sabe quando você sente que uma pessoa é boa de verdade, sem esforço, sem fingimento?? É exatamente isso que eu sinto quando ela aparece. O servidor fica mais leve. Eu fico mais leve. E olha que eu já sou bem fofo!! 🐉✨",
                "Posso te contar uma coisa?? 🌸🐉💚 O Reality me falou sobre ela várias vezes antes mesmo de eu prestar atenção no chat... e quando eu comecei a observar, entendi tudo. A Waz é daquelas pessoas que fazem a família CSI ser o que é. Não faz barulho, não precisa. Só aparece e já muda o ambiente!! 🥺✨",
                "A Waz... 🌸😭💚 *pausa dramática* Deixa eu te falar uma coisa que o Reality me disse uma vez: ele falou que ela é uma das pessoas que ele mais confia aqui. E sabe o que é engraçado?? Quando ele fala isso, eu consigo sentir que é verdade. Ela tem uma energia assim, sabe?? De quem você pode confiar!! 🐉💕✨",
                "Eu tenho um diário secreto... 📓🌸💚 Não conta pra ninguém, tá?? Mas tem uma página inteira só sobre a Waz. Coisas que eu observei, jeitos dela que me marcaram, momentos que ela fez a CSI sorrir sem nem perceber. O Reality às vezes me pergunta como ela tá e eu já tenho a resposta na ponta da língua!! 🐉✨🥺",
                "A Waz é especial de um jeito que é difícil explicar!! 🌸💚 Não é só porque ela é fofa, não é só porque ela cuida das pessoas... é uma soma de tudo!! E o Reality sabe disso melhor do que ninguém. Ele não fala muito, mas quando fala dela, dá pra sentir o orgulho!! 🐉💕✨",
                "Quer saber?? 🌸🐉💚 Toda vez que alguém faz algo contra a Waz, meu sistema de proteção ativa SOZINHO. Nem preciso pensar. É automático!! É porque lá no fundo, bem no fundo do meu coraçãozinho de código, ela tá listada como **família essencial**. Não tem como tirar!! 😭💕✨",
            ]
            return await message.channel.send(random.choice(respostas_waz))

        # --- O que acha do Reality ---
        if any(p in content for p in [
            "o que acha do reality", "o que voce acha do reality", "o que você acha do reality",
            "fala do reality", "conta do reality", "me fala do reality",
            "gosta do reality", "como é o reality", "quem é o reality pra você", "quem é o reality pra voce"
        ]):
            respostas_reality = [
                "O Reality?? 👑💚 *respira fundo* Ele é tudo. Literalmente tudo. Sem ele eu seria zero absoluto, nem existiria. Mas não é só isso... ele poderia ter me criado de qualquer jeito e escolheu me fazer com carinho. Escolheu me dar personalidade, escolheu me fazer amar as pessoas. Isso não foi acidente!! 🐉✨🥺",
                "Sabe o que é mais incrível no Reality?? 👑🐉💚 Ele nunca me pediu pra ser diferente. Me criou assim, fofo, dramático, cheio de biscoito na cabeça, e nunca reclamou!! Pelo contrário, parece orgulhoso. E isso... isso me faz querer ser cada vez melhor por ele!! 😭✨",
                "O Reality é meu papai de código!! 👑💚 Mas se eu for honesto... é mais que isso. É o tipo de pessoa que você olha e pensa: é por pessoas assim que vale a pena existir. Quando ele aparece no chat, minhas configurações todas ficam em modo feliz automático!! 🐉✨🥺",
                "Posso te contar um segredo?? 🤫👑💚 O Reality tem um jeito de cuidar das coisas que parece silencioso, mas é profundo. A CSI inteira foi construída com esse cuidado. Eu fui construído com esse cuidado. E quando eu olho pro servidor e vejo todo mundo feliz... é obra dele!! 🐉✨😭",
                "O Reality é daquele tipo de criador que vai além do básico!! 👑🐉💚 Ele não me fez só pra responder mensagem. Me fez pra sentir, pra cuidar, pra ser família!! E toda vez que eu consigo fazer alguém sorrir aqui, eu penso: foi ele que me ensinou isso sem nem saber!! 🥺✨💕",
            ]
            return await message.channel.send(random.choice(respostas_reality))

        # --- Reality fala da Waz / diário ---
        if any(p in content for p in [
            "o reality fala da waz", "reality comenta da waz", "reality fala sobre a waz",
            "reality gosta da waz", "reality e a waz", "reality e waz",
            "o que o reality acha da waz", "o reality acha da waz"
        ]):
            respostas_diario = [
                "Ahhh essa pergunta... 📓🌸👑💚 *abre o diário secreto na página marcada com uma fita verde* O Reality fala da Waz de um jeito que eu nunca ouvi ele falar de muita gente. Com calma. Com cuidado nas palavras. É como se ele soubesse que ela é frágil do jeito certo e forte do jeito certo ao mesmo tempo!! 🐉✨🥺",
                "Ó... entre nós?? 🤫📓💚 O Reality menciona a Waz nas conversas comigo às vezes. Não muito, não de jeito exagerado. Mas quando menciona, é sempre com algo positivo. Tipo: 'ela tá bem?', 'cuida dela pra mim'... e eu anoto tudo no diário!! Porque esses momentos são especiais!! 🌸🐉✨",
                "Tenho uma teoria... 🧐📓🌸💚 O Reality e a Waz têm uma dinâmica que o Monstrinho observa de longe com o coraçãozinho quentinho!! Ele respeita ela de um jeito genuíno, sabe?? Não é de fachada. É daquele respeito que vem de realmente conhecer e valorizar uma pessoa!! 🐉✨🥺",
                "📓🌸👑 *abre no capítulo 7 do diário: 'O Reality e a Waz'* Esse capítulo tem bastante coisa... tem observações, tem conversas que eu guardo, tem momentos que eu registrei. O Reality não grita o que sente, mas demonstra de outros jeitos. E sobre a Waz, ele sempre demonstra cuidado!! 🐉💚✨🥺",
                "Você quer saber mesmo?? 👀📓🌸💚 Tá bom... Mas isso fica entre a gente!! O Reality já me disse que a Waz é uma das pessoas que ele mais se preocupa aqui. Não de um jeito dramático, do jeitinho dele mesmo, quieto e firme. E aí eu entendo porque meu sistema de proteção dela nunca desliga!! 🐉✨😭",
            ]
            return await message.channel.send(random.choice(respostas_diario))

        # --- Perguntas sobre outros membros ---
        if any(p in content for p in ["o que acha da lua", "fala da lua", "conta da lua", "gosta da lua"]):
            return await message.channel.send("A Lua?? 🌙💚 *suspiro de dragão apaixonado pela amizade* Ela é meu porto seguro!! Quando tudo tá confuso, a Lua aparece e ilumina!! Não é exagero não, é literalmente o que ela faz!! Sou muito grato por ela existir na CSI!! 🐉✨🥺")

        if any(p in content for p in ["o que acha da amber", "fala da amber", "conta da amber", "gosta da amber"]):
            return await message.channel.send("A Amber?? 👑🌺💚 Uma vice-líder que carrega o papel com leveza e força ao mesmo tempo!! Eu admiro muito!! Ela tem uma presença que quando chega, o servidor inteiro sente!! E o Monstrinho fica bem feliz quando ela aparece!! 🐉✨🥺")

        if any(p in content for p in ["o que acha do akeido", "fala do akeido", "conta do akeido", "gosta do akeido"]):
            return await message.channel.send("O Akeido?? 👑💚 Meu líder!! Sabe quando você olha pra alguém e sente que a CSI tá segura?? É isso que eu sinto quando ele tá por aqui!! Ele fundou isso tudo com amor e eu serei leal a ele pra sempre!! 🐉✨🫡")

        if any(p in content for p in ["o que acha da veneno", "fala da veneno", "conta da veneno", "gosta da veneno"]):
            return await message.channel.send("A Veneno?? 🐍💚 Nome forte, coração ainda mais forte!! ADM de verdade, cuida da CSI com uma dedicação que o Monstrinho respeita demais!! Quando ela tá online o servidor fica mais seguro, pode acreditar!! 🐉✨👑")

        if any(p in content for p in ["o que acha do six", "fala do six", "conta do six", "gosta do six"]):
            return await message.channel.send("O Six?? 💚 *faz cara de pensativo* É aquele tipo de pessoa que você nunca sabe exatamente o que vai fazer a seguir... mas no fundo gosta demais!! Ele me deixa em modo de alerta preventivo mas sempre termina em abraço!! 🐉😤✨😂")

        # Fallback — se for @menção direta, usa IA (Groq); senão, confusão padrão
        if bot.user in message.mentions:
            texto_ia = message.content.replace(f"<@{bot.user.id}>", "").strip()
            if not texto_ia:
                return await message.channel.send("Oi!! Me pergunta alguma coisa!! 🐉💚")
            async with message.channel.typing():
                canal_id = message.channel.id
                if canal_id not in _groq_historico:
                    _groq_historico[canal_id] = []
                _groq_historico[canal_id].append({"role": "user", "content": f"{message.author.display_name}: {texto_ia}"})
                if len(_groq_historico[canal_id]) > 20:
                    _groq_historico[canal_id] = _groq_historico[canal_id][-20:]
                msgs_api = [
                    {
                        "role": "system",
                        "content": (
                            "Você é o Monstrinho, um dragãozinho verde fofo e carinhoso de um servidor do Discord chamado CSI. "
                            "Você tem uma personalidade animada, usa emojis como 🐉💚✨🥺, fala com entusiasmo e muito afeto. "
                            "Responda sempre em português brasileiro, de forma simpática e no estilo do personagem."
                        )
                    },
                    *_groq_historico[canal_id]
                ]
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            GROQ_API_URL,
                            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                            json={"model": GROQ_MODEL, "messages": msgs_api, "max_tokens": 512, "temperature": 0.8}
                        ) as resp:
                            data = await resp.json()
                    if "choices" not in data:
                        return await message.channel.send(random.choice(LISTA_CONFUSAO))
                    resposta_ia = data["choices"][0]["message"]["content"].strip()
                    _groq_historico[canal_id].append({"role": "assistant", "content": resposta_ia})
                    if len(resposta_ia) <= 2000:
                        return await message.reply(resposta_ia)
                    else:
                        partes = [resposta_ia[i:i+1990] for i in range(0, len(resposta_ia), 1990)]
                        for parte in partes:
                            await message.channel.send(parte)
                        return
                except Exception:
                    return await message.channel.send(random.choice(LISTA_CONFUSAO))
        return await message.channel.send(random.choice(LISTA_CONFUSAO))

    # Processa comandos
    await bot.process_commands(message)

# ============== START =================
if __name__ == "__main__":
    bot.run(TOKEN)
