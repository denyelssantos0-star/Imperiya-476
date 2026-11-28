import os
import random
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
INICIALIZADO = False


NOME_CANAL_ENLISTMENT = "enlistment"
CARGO_ALISTAMENTO = 1562426482897461278
MODELO_ENLISTMENT = (
    "@everyone\n\n"
    "Nome:\n"
    "ID:\n"
    "Plataforma:\n"
    "Print info:"
)

@bot.event
async def on_ready():
    global INICIALIZADO
    if INICIALIZADO:
        return
    try:
        synced = await bot.tree.sync()

        print(f"✅ {len(synced)} comandos / sincronizados.")

        for comando in synced:
            print(f"➡️ /{comando.name}")

        # Prepara automaticamente o canal de logs.
        await preparar_canal_logs()

        # Sincroniza o contador ao iniciar (inclusive após reinicializações).
        for guild in bot.guilds:
            await atualizar_contador(guild)

        # Garante que o #alistamento tenha um formulário limpo no início.
        for guild in bot.guilds:
            canal_alistamento = discord.utils.get(
                guild.text_channels, name=NOME_CANAL_ENLISTMENT
            )
            if canal_alistamento is not None:
                mensagens_recentes = [
                    mensagem async for mensagem in canal_alistamento.history(limit=30)
                    if mensagem.author == bot.user
                ]
                # Remove formulários antigos que ainda mencionavam o cargo específico.
                mention_cargo_antigo = f"<@&{CARGO_ALISTAMENTO}>"
                for mensagem in mensagens_recentes:
                    if mention_cargo_antigo in mensagem.content:
                        try:
                            await mensagem.delete()
                            print("🗑️ Formulário antigo com menção de cargo removido.")
                        except discord.Forbidden:
                            print("❌ Sem permissão para apagar o formulário antigo.")
                        except discord.HTTPException as erro:
                            print(f"❌ Não consegui remover o formulário antigo: {erro}")

                mensagens_recentes = [m for m in mensagens_recentes if m.content.strip() != ""]
                if not any(m.content.strip() == MODELO_ENLISTMENT.strip() for m in mensagens_recentes):
                    await enviar_formulario_enlistment(canal_alistamento)

        INICIALIZADO = True
    except Exception as erro:
        print(f"❌ Erro ao sincronizar: {erro}")


@bot.tree.command(name="ping", description="Mostra a latência do bot.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"🏓 Pong! `{round(bot.latency * 1000)}ms`"
    )


@bot.tree.command(name="avatar", description="Mostra o avatar de um usuário.")
@app_commands.describe(usuario="Usuário que você deseja visualizar")
async def avatar(
    interaction: discord.Interaction,
    usuario: discord.Member = None
):
    usuario = usuario or interaction.user

    embed = discord.Embed(
        title=f"🖼️ Avatar de {usuario.display_name}",
        color=discord.Color(0x000000)
    )

    embed.set_image(url=usuario.display_avatar.url)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="serverinfo", description="Mostra informações do servidor.")
async def serverinfo(interaction: discord.Interaction):

    guild = interaction.guild

    embed = discord.Embed(
        title=f"📊 {guild.name}",
        color=discord.Color(0x000000)
    )

    embed.add_field(
        name="👥 Membros",
        value=guild.member_count,
        inline=True
    )

    embed.add_field(
        name="👑 Dono",
        value=guild.owner.mention if guild.owner else "Desconhecido",
        inline=True
    )

    embed.add_field(
        name="🆔 ID",
        value=guild.id,
        inline=False
    )

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    await interaction.response.send_message(embed=embed)


# =========================
# BOAS-VINDAS
# =========================

CANAL_BOAS_VINDAS = 1574325988752363540
CANAL_CONTADOR = 1575044479000518676

async def atualizar_contador(guild):
    # Primeiro procura no cache; se necessário, consulta o Discord pela API.
    canal = guild.get_channel(CANAL_CONTADOR)

    if canal is None:
        try:
            canal = await bot.fetch_channel(CANAL_CONTADOR)
        except discord.NotFound:
            print(f"❌ Canal do contador {CANAL_CONTADOR} não encontrado. Confira o ID.")
            return
        except discord.Forbidden:
            print("❌ O bot não tem acesso ao canal do contador.")
            return
        except discord.HTTPException as erro:
            print(f"❌ Não foi possível buscar o canal do contador: {erro}")
            return

    if not hasattr(canal, "edit") or not hasattr(canal, "name"):
        print("❌ O ID do contador não corresponde a um canal editável.")
        return

    quantidade = guild.member_count
    if quantidade is None:
        try:
            quantidade = (await guild.fetch_member_count())
        except (AttributeError, discord.HTTPException):
            print("❌ Não foi possível obter a quantidade atual de membros.")
            return

    novo_nome = f"👥 Membros: {quantidade}"

    try:
        if canal.name != novo_nome:
            await canal.edit(name=novo_nome, reason="Atualização automática do contador de membros")
            print(f"✅ Contador atualizado: {novo_nome}")
    except discord.Forbidden:
        print("❌ O bot não tem permissão para editar o canal do contador. Verifique Gerenciar canais.")
    except discord.HTTPException as erro:
        print(f"❌ Erro ao atualizar o contador: {erro}")

@bot.event
async def on_member_join(member):
    await atualizar_contador(member.guild)
        # 🎭 Cargo automático
    cargo = member.guild.get_role(1562426482897461278)


    if cargo:
        try:
            await member.add_roles(
                cargo,
                reason="Cargo automático ao entrar no servidor"
            )
            print(f"✅ Cargo automático dado para {member}")
        except discord.Forbidden:
            print("❌ O bot não tem permissão para dar o cargo.")
        except Exception as erro:
            print(f"❌ Erro no autorole: {erro}")
    else:
        print("❌ Cargo do autorole não encontrado.") 
    
    # Busca o canal pelo ID; se não estiver no cache, tenta buscar pela API.
    canal = bot.get_channel(CANAL_BOAS_VINDAS)
    if canal is None:
        try:
            canal = await bot.fetch_channel(CANAL_BOAS_VINDAS)
        except discord.NotFound:
            print(f"❌ Canal de boas-vindas {CANAL_BOAS_VINDAS} não encontrado. Confira o ID.")
            return
        except discord.Forbidden:
            print("❌ O bot não tem acesso ao canal de boas-vindas.")
            return
        except discord.HTTPException as erro:
            print(f"❌ Não foi possível buscar o canal de boas-vindas: {erro}")
            return

    if not hasattr(canal, "send"):
        print("❌ O ID configurado para boas-vindas não é um canal que aceita mensagens.")
        return
    mensagens_boas_vindas = [
    f"Seja muito bem-vindo(a)!!",
    f"Opa, chegou!",
    f"Bem-vindo(a) ao servidor!",
    f"Mais um por aqui.",
    f"Chega mais, fique à vontade.",
    f"Salve, seja bem-vindo!",
    f"Que bom que chegou, {member.mention}.",
    f"Bem-vindo(a), aproveite!",
    f"A casa agora tem mais alguém.",
    f"Opa, tudo certo? Bem-vindo!",
    f"  Seja bem-vindo(a)!",
    f"Mais um rosto novo por aqui.",
    f"Bem-vindo à nossa comunidade.",
    f"Chegou agora? Seja bem-vindo.",
    f"Fique à vontade por aqui.",
    f"Pode entrar, a casa é sua.",
    f"Sua chegada foi notada, {member.mention}.",
    f"Bem-vindo(a), divirta-se.",
    f"Chegou chegando!",
    f"Mais um para a coleção.",
    f"Seja bem-vindo, sem cerimônia.",
    f"  chegou mais um...",
    f"Bem-vindo(a), sinta-se em casa.",
    f"Finalmente apareceu alguém novo.",
    f"Oi, seja bem-vindo!",
    f"Que sua estadia seja boa.",
    f"A comunidade te recebe de braços abertos.",
    f"Mais um integrante desbloqueado.",
    f"  bem-vindo ao nosso cantinho.",
    f"O servidor ficou um pouquinho maior.",
    f"Seja bem-vindo(a), {member.mention}!",
    f"Chegou, entrou, agora faz parte.",
    f"Novo membro na área!",
    f"Bem-vindo(a), esperamos que goste.",
    f"Olha só quem chegou!",
    f"Seja bem-vindo(a) à família.",
    f"Mais alguém para fazer história.",
    f"  que bom ter você aqui.",
    f"Um novo membro chegou.",
    f"Bem-vindo, aproveite o momento.",
    f"Seja bem-vindo ao caos.",
    f"Chegou mais um, hein.",
    f"  bem-vindo por aqui.",
    f"Opa, fique à vontade.",
    f"Um prazer ter você aqui.",
    f"Bem-vindo(a), não fique de fora.",
    f"A porta está aberta, entre.",
    f"Mais um nome por aqui.",
    f"  chegou para somar.",
    f"Bem-vindo(a), bora aproveitar!",
    f"Chega mais, recém-chegado.",
    f"Bem-vindo ao nosso pequeno mundo.",
    f"  mais um entre nós.",
    f"Opa, seja muito bem-vindo.",
    f"Novo membro na área!",
    f"Que sua chegada seja incrível.",
    f"Bem-vindo(a), aproveite a companhia.",
    f"  tudo começa por aqui.",
    f"Apareceu! Seja bem-vindo(a).",
    f"Chega mais, a casa é sua.",
    f"Bem-vindo(a), divirta-se.",
    f"Mais um na família.",
    f"  fique à vontade :)",
    f"Bem-vindo(a) à comunidade.",
    f"Chegou no lugar certo, {member.mention}.",
    f"Salve! Aproveita o servidor.",
    f"  mais um por aqui.",
    f"Chega junto!",
    f"Bem-vindo(a), sem pressão.",
    f"Que bom que veio, {member.mention}.",
    f"Mais um aventureiro chegou.",
    f"  boas-vindas a você.",
    f"Bem-vindo(a) ao servidor, aproveite!",
    f"Novo rosto, boas histórias.",
    f"Chega mais e aproveita!",
    f"  pode chegar.",
    f"Bem-vindo(a), fique tranquilo.",
    f"A casa é sua.",
    f"  chegou, seja bem-vindo.",
    f"Bem-vindo(a), divirta-se por aqui.",
    f"Mais um chegando para movimentar as coisas.",
    f"  Opa, tudo bem?",
    f"Seja bem-vindo(a), {member.mention}.",
    f"Mais alguém chegou para ficar.",
    f"Entre e aproveite o que temos por aqui.",
    f"  mais um novo rosto.",
    f"Bem-vindo(a), pode ficar à vontade.",
    f"Servidor ganhou mais um integrante!",
]
    mensagem = random.choice(mensagens_boas_vindas)
    try:
        await canal.send(mensagem)
        print(f"✅ Boas-vindas enviada para {member} no canal #{canal.name}.")
    except discord.Forbidden:
        print("❌ Sem permissão para enviar mensagens no canal de boas-vindas. Confira Ver canal e Enviar mensagens.")
    except discord.HTTPException as erro:
        print(f"❌ Erro ao enviar boas-vindas: {erro}")
@bot.event
async def on_member_remove(member):
    await atualizar_contador(member.guild)

# ==========================================
# 🛡️ SISTEMA DE MODERAÇÃO - OS ORIGINAIS
# ==========================================

from datetime import timedelta


# /clear
@bot.tree.command(name="clear", description="Apaga mensagens do canal.")
@app_commands.describe(quantidade="Quantidade de mensagens para apagar")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, quantidade: int):

    if quantidade < 1 or quantidade > 100:
        await interaction.response.send_message(
            "❌ Escolha uma quantidade entre 1 e 100.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    try:
        apagadas = await interaction.channel.purge(
            limit=quantidade
        )
        await enviar_log_moderacao(
    titulo="🧹 Mensagens apagadas",
    moderador=interaction.user,
    detalhes=(
        f"📍 Canal: {interaction.channel.mention}\n"
        f"🗑️ Quantidade: {len(apagadas)}"
    )
)

        await interaction.followup.send(
            f"🧹 **{len(apagadas)} mensagens foram apagadas!**",
            ephemeral=True
        )

    except discord.Forbidden:
        await interaction.followup.send(
            "❌ Eu não tenho permissão para apagar mensagens neste canal.",
            ephemeral=True
        )

    except Exception as erro:
        print(f"❌ ERRO NO /CLEAR: {erro}")

        await interaction.followup.send(
            "❌ Ocorreu um erro ao apagar as mensagens. Veja o CMD.",
            ephemeral=True
        )


# /kick
@bot.tree.command(name="kick", description="Expulsa um membro do servidor.")
@app_commands.describe(
    membro="Membro que será expulso",
    motivo="Motivo da expulsão"
)
@app_commands.checks.has_permissions(kick_members=True)
async def kick(
    interaction: discord.Interaction,
    membro: discord.Member,
    motivo: str = "Nenhum motivo informado"
):
    if membro == interaction.user:
        await interaction.response.send_message(
            "❌ Você não pode expulsar você mesmo.",
            ephemeral=True
        )
        return

    try:
        await membro.kick(reason=motivo)
        await enviar_log_moderacao(
    titulo="👢 Membro expulso",
    moderador=interaction.user,
    usuario=membro,
    motivo=motivo
)

        embed = discord.Embed(
            title="👢 Membro expulso",
            color=discord.Color(0x000000)
        )

        embed.add_field(
            name="👤 Usuário",
            value=f"{membro} (`{membro.id}`)",
            inline=False
        )

        embed.add_field(
            name="🛡️ Moderador",
            value=interaction.user.mention,
            inline=False
        )

        embed.add_field(
            name="📝 Motivo",
            value=motivo,
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ Não tenho permissão para expulsar esse membro.",
            ephemeral=True
        )


# /ban
@bot.tree.command(name="ban", description="Bane um membro do servidor.")
@app_commands.describe(
    membro="Membro que será banido",
    motivo="Motivo do banimento"
)
@app_commands.checks.has_permissions(ban_members=True)
async def ban(
    interaction: discord.Interaction,
    membro: discord.Member,
    motivo: str = "Nenhum motivo informado"
):
    if membro == interaction.user:
        await interaction.response.send_message(
            "❌ Você não pode banir você mesmo.",
            ephemeral=True
        )
        return

    try:
        await membro.ban(reason=motivo)
        await enviar_log_moderacao(
    titulo="🔨 Membro banido",
    moderador=interaction.user,
    usuario=membro,
    motivo=motivo
)

        embed = discord.Embed(
            title="🔨 Membro banido",
            color=discord.Color(0x000000)
        )

        embed.add_field(
            name="👤 Usuário",
            value=f"{membro} (`{membro.id}`)",
            inline=False
        )

        embed.add_field(
            name="🛡️ Moderador",
            value=interaction.user.mention,
            inline=False
        )

        embed.add_field(
            name="📝 Motivo",
            value=motivo,
            inline=False
        )

        await interaction.response.send_message(embed=embed)

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ Não tenho permissão para banir esse membro.",
            ephemeral=True
        )


# /timeout
@bot.tree.command(name="timeout", description="Coloca um membro de castigo.")
@app_commands.describe(
    membro="Membro que receberá timeout",
    minutos="Duração em minutos",
    motivo="Motivo do timeout"
)
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(
    interaction: discord.Interaction,
    membro: discord.Member,
    minutos: int,
    motivo: str = "Nenhum motivo informado"
):
    if minutos < 1 or minutos > 40320:
        await interaction.response.send_message(
            "❌ Escolha entre 1 e 40320 minutos.",
            ephemeral=True
        )
        return

    if membro == interaction.user:
        await interaction.response.send_message(
            "❌ Você não pode aplicar timeout em você mesmo.",
            ephemeral=True
        )
        return

    try:
        await membro.timeout(
            timedelta(minutes=minutos),
            reason=motivo
        )

        # Envia para o canal de logs
        await enviar_log_moderacao(
            titulo="🔇 Timeout aplicado",
            moderador=interaction.user,
            usuario=membro,
            motivo=motivo,
            detalhes=f"⏱️ Duração: {minutos} minutos"
        )

        # Resposta do comando
        embed = discord.Embed(
            title="🔇 Timeout aplicado",
            color=discord.Color(0x000000)
        )

        embed.add_field(
            name="👤 Usuário",
            value=membro.mention,
            inline=True
        )

        embed.add_field(
            name="⏱️ Tempo",
            value=f"{minutos} minutos",
            inline=True
        )

        embed.add_field(
            name="📝 Motivo",
            value=motivo,
            inline=False
        )

        embed.set_footer(
            text=f"Aplicado por {interaction.user}"
        )

        await interaction.response.send_message(embed=embed)

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ Não tenho permissão para dar timeout nesse membro.",
            ephemeral=True
        )

    except Exception as erro:
        print(f"❌ ERRO NO /TIMEOUT: {erro}")

        if not interaction.response.is_done():
            await interaction.response.send_message(
                "❌ Ocorreu um erro ao aplicar o timeout.",
                ephemeral=True
            )
# /lock
@bot.tree.command(name="lock", description="Tranca o canal atual.")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):

    canal = interaction.channel

    overwrite = canal.overwrites_for(
        interaction.guild.default_role
    )

    overwrite.send_messages = False

    await canal.set_permissions(
        interaction.guild.default_role,
        overwrite=overwrite
    )

    await interaction.response.send_message(
        "🔒 **Canal trancado.**"
    )


# /unlock
@bot.tree.command(name="unlock", description="Destranca o canal atual.")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):

    canal = interaction.channel

    overwrite = canal.overwrites_for(
        interaction.guild.default_role
    )

    overwrite.send_messages = None

    await canal.set_permissions(
        interaction.guild.default_role,
        overwrite=overwrite
    )

    await interaction.response.send_message(
        "🔓 **Canal destrancado.**"
    )


# Mensagem para quem tentar usar comando sem permissão
@bot.tree.error
async def erro_comando(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError
):
    if isinstance(error, app_commands.MissingPermissions):
        if interaction.response.is_done():
            await interaction.followup.send(
                "❌ Você não tem permissão para usar esse comando.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ Você não tem permissão para usar esse comando.",
                ephemeral=True
            )
# ...todos os códigos acima...

# ==========================================
# 📋 LOGS - OS ORIGINAIS
# ==========================================

# O bot procura o canal "logs" automaticamente.
# Se ele não existir, tenta criar o canal.
CANAL_LOGS = None
NOME_CANAL_LOGS = "logs"


async def preparar_canal_logs():
    global CANAL_LOGS

    for guild in bot.guilds:
        canal = discord.utils.get(guild.text_channels, name=NOME_CANAL_LOGS)

        if canal is None:
            try:
                canal = await guild.create_text_channel(
                    NOME_CANAL_LOGS,
                    reason="Criação automática do canal de logs do bot"
                )
                print(f"✅ Canal #{NOME_CANAL_LOGS} criado no servidor {guild.name}.")
            except discord.Forbidden:
                print(f"❌ Não tenho permissão para criar o canal #{NOME_CANAL_LOGS} em {guild.name}.")
                continue
            except discord.HTTPException as erro:
                print(f"❌ Erro ao criar o canal #{NOME_CANAL_LOGS}: {erro}")
                continue

        CANAL_LOGS = canal.id
        print(f"✅ Canal de logs configurado: #{canal.name} ({canal.id})")
        return canal

    print("❌ Não foi possível encontrar/criar o canal de logs.")
    return None


def pegar_canal_logs():
    if CANAL_LOGS is None:
        return None
    return bot.get_channel(CANAL_LOGS)


# 🗑️ MENSAGEM APAGADA
@bot.event
async def on_message_delete(message):

    if message.author.bot:
        return

    canal_logs = pegar_canal_logs()

    if canal_logs is None:
        print("❌ Canal de logs não encontrado.")
        return

    conteudo = message.content or "Sem conteúdo de texto."

    # Evita embed gigante
    if len(conteudo) > 1000:
        conteudo = conteudo[:1000] + "..."

    embed = discord.Embed(
        title="🗑️ Mensagem apagada",
        color=discord.Color(0x000000),
        timestamp=discord.utils.utcnow()
    )

    embed.add_field(
        name="👤 Autor",
        value=f"{message.author.mention}\n`{message.author.id}`",
        inline=True
    )

    embed.add_field(
        name="📍 Canal",
        value=message.channel.mention,
        inline=True
    )

    embed.add_field(
        name="💬 Mensagem",
        value=conteudo,
        inline=False
    )

    embed.set_thumbnail(
        url=message.author.display_avatar.url
    )

    embed.set_footer(
        text=f"Mensagem ID: {message.id}"
    )

    await canal_logs.send(embed=embed)


# ✏️ MENSAGEM EDITADA
@bot.event
async def on_message_edit(before, after):

    if before.author.bot:
        return

    # Não cria log se o conteúdo não mudou
    if before.content == after.content:
        return

    canal_logs = pegar_canal_logs()

    if canal_logs is None:
        return

    antes = before.content or "Sem conteúdo."
    depois = after.content or "Sem conteúdo."

    if len(antes) > 900:
        antes = antes[:900] + "..."

    if len(depois) > 900:
        depois = depois[:900] + "..."

    embed = discord.Embed(
        title="✏️ Mensagem editada",
        color=discord.Color(0x000000),
        timestamp=discord.utils.utcnow()
    )

    embed.add_field(
        name="👤 Autor",
        value=f"{before.author.mention}\n`{before.author.id}`",
        inline=True
    )

    embed.add_field(
        name="📍 Canal",
        value=before.channel.mention,
        inline=True
    )

    embed.add_field(
        name="📝 Antes",
        value=antes,
        inline=False
    )

    embed.add_field(
        name="📝 Depois",
        value=depois,
        inline=False
    )

    embed.add_field(
        name="🔗 Ir para mensagem",
        value=f"[Clique aqui]({after.jump_url})",
        inline=False
    )

    embed.set_thumbnail(
        url=before.author.display_avatar.url
    )

    await canal_logs.send(embed=embed)

async def enviar_log_moderacao(
    titulo,
    moderador,
    usuario=None,
    motivo=None,
    detalhes=None
):
    canal = bot.get_channel(CANAL_LOGS)

    if canal is None:
        print("❌ Canal de logs não encontrado.")
        return

    embed = discord.Embed(
        title=titulo,
        color=discord.Color(0x000000),
        timestamp=discord.utils.utcnow()
    )

    embed.add_field(
        name="🛡️ Moderador",
        value=f"{moderador.mention}\n`{moderador.id}`",
        inline=True
    )

    if usuario:
        embed.add_field(
            name="👤 Usuário",
            value=f"{usuario.mention}\n`{usuario.id}`",
            inline=True
        )

    if motivo:
        embed.add_field(
            name="📝 Motivo",
            value=motivo,
            inline=False
        )

    if detalhes:
        embed.add_field(
            name="📋 Detalhes",
            value=detalhes,
            inline=False
        )

    embed.set_footer(text="Imperiya • 476 d.C.")

    await canal.send(embed=embed)

# ==========================================
# 📢 SISTEMA DE EMBED - OS ORIGINAIS
# ==========================================

@bot.tree.command(
    name="embed",
    description="Envia uma mensagem personalizada em embed."
)
@app_commands.describe(
    titulo="Título do embed",
    mensagem="Texto principal",
    canal="Canal onde o embed será enviado",
    imagem="Link de uma imagem (opcional)",
    rodape="Texto no final do embed (opcional)",
    miniatura="Link de uma miniatura (opcional)",
cor="Cor do embed: roxo, vermelho, azul, verde, preto..."
)
@app_commands.checks.has_permissions(manage_messages=True)
async def criar_embed(
    interaction: discord.Interaction,
    titulo: str,
    mensagem: str,
    canal: discord.TextChannel,
    imagem: str = None,
    rodape: str = "Imperiya 476 d.C.",
    miniatura: str = None,
    cor: str = "preto"):
    cores = {
        "roxo": discord.Color(0x000000),
        "vermelho": discord.Color(0x000000),
        "azul": discord.Color(0x000000),
        "verde": discord.Color(0x000000),
        "amarelo": discord.Color(0x000000),
        "laranja": discord.Color(0x000000),
        "preto": discord.Color(0x000000),
        "rosa": discord.Color(0x000000),
        "branco": discord.Color(0x000000)
    }

    cor_embed = cores.get(cor.lower(), discord.Color(0x000000))

    try:
        embed = discord.Embed(
            title=titulo,
            description=mensagem,
            color=cor_embed,
            timestamp=discord.utils.utcnow()
        )
        # Mostra quem criou
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url
        )

                # Imagem opcional
        if imagem:
            if imagem.startswith(("http://", "https://")):
                embed.set_image(url=imagem)
                # Miniatura opcional
                
        if miniatura:
            if miniatura.startswith(("http://", "https://")):
                embed.set_thumbnail(url=miniatura)
            else:
                await interaction.response.send_message(
                    "❌ O campo miniatura precisa ser um link começando com http:// ou https://",
                    ephemeral=True
                )
                return
        # Rodapé
        if rodape:
            embed.set_footer(text=rodape)

        # Envia
        await canal.send(embed=embed)

        await interaction.response.send_message(
            f"✅ Embed enviado em {canal.mention}!",
            ephemeral=True
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ Não tenho permissão para enviar mensagens nesse canal.",
            ephemeral=True
        )

    except Exception as erro:
        print(f"❌ ERRO NO /EMBED: {erro}")

        if not interaction.response.is_done():
            await interaction.response.send_message(
                "❌ Ocorreu um erro ao criar o embed.",
                ephemeral=True
            )

# ==========================================
# 👤 USERINFO
# ==========================================

@bot.tree.command(
    name="userinfo",
    description="Mostra informações de um membro."
)
@app_commands.describe(
    usuario="Membro que você deseja consultar"
)
async def userinfo(
    interaction: discord.Interaction,
    usuario: discord.Member = None
):
    usuario = usuario or interaction.user

    # Cargos, removendo @everyone
    cargos = [
        cargo.mention
        for cargo in usuario.roles
        if cargo != interaction.guild.default_role
    ]

    cargos.reverse()

    if cargos:
        texto_cargos = " ".join(cargos)

        if len(texto_cargos) > 1000:
            texto_cargos = texto_cargos[:1000] + "..."
    else:
        texto_cargos = "Nenhum cargo."

    embed = discord.Embed(
        title=f"👤 Informações de {usuario.display_name}",
        color=discord.Color(0x000000),
        timestamp=discord.utils.utcnow()
    )

    embed.set_thumbnail(
        url=usuario.display_avatar.url
    )

    embed.add_field(
        name="🏷️ Usuário",
        value=usuario.mention,
        inline=True
    )

    embed.add_field(
        name="🆔 ID",
        value=f"`{usuario.id}`",
        inline=True
    )

    embed.add_field(
        name="🤖 É bot?",
        value="Sim" if usuario.bot else "Não",
        inline=True
    )

    embed.add_field(
        name="📅 Conta criada",
        value=discord.utils.format_dt(
            usuario.created_at,
            style="F"
        ),
        inline=False
    )

    if usuario.joined_at:
        embed.add_field(
            name="📥 Entrou no servidor",
            value=discord.utils.format_dt(
                usuario.joined_at,
                style="F"
            ),
            inline=False
        )

    embed.add_field(
        name=f"🎭 Cargos ({len(cargos)})",
        value=texto_cargos,
        inline=False
    )

    embed.set_footer(
        text="Imperiya • info"
    )

    await interaction.response.send_message(
        embed=embed
    )


# ==========================================
# 💬 SAY
# ==========================================

@bot.tree.command(
    name="say",
    description="Faz o bot enviar uma mensagem."
)
@app_commands.describe(
    mensagem="Mensagem que será enviada",
    canal="Canal onde a mensagem será enviada"
)
@app_commands.checks.has_permissions(
    manage_messages=True
)
async def say(
    interaction: discord.Interaction,
    mensagem: str,
    canal: discord.TextChannel
):
    try:
        await canal.send(mensagem)

        await interaction.response.send_message(
            f"✅ Mensagem enviada em {canal.mention}.",
            ephemeral=True
        )

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ Não tenho permissão para enviar mensagens nesse canal.",
            ephemeral=True
        )

    except Exception as erro:
        print(f"❌ ERRO NO /SAY: {erro}")

        if not interaction.response.is_done():
            await interaction.response.send_message(
                "❌ Ocorreu um erro ao enviar a mensagem.",
                ephemeral=True
            )



# ==========================================
# 📋 SISTEMA DE ALISTAMENTO - OS ORIGINAIS
# ==========================================

async def enviar_formulario_enlistment(canal):
    try:
        await canal.send(
            MODELO_ENLISTMENT,
            allowed_mentions=discord.AllowedMentions(
                roles=False, users=False, everyone=True
            )
        )
        print(f"✅ Formulário de enlistment enviado em #{canal.name}.")
    except discord.Forbidden:
        print("❌ Sem permissão para enviar o formulário ou mencionar os cargos no #enlistment.")
    except discord.HTTPException as erro:
        print(f"❌ Erro ao enviar formulário de enlistment: {erro}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if isinstance(message.channel, discord.TextChannel) and message.channel.name == NOME_CANAL_ENLISTMENT:
        texto = message.content.strip()

        # Se a mensagem já for o formulário limpo do bot, não cria outro.
        if texto != MODELO_ENLISTMENT.strip():
            await enviar_formulario_enlistment(message.channel)

    await bot.process_commands(message)


@bot.event
async def on_ready_enlistment():
    pass

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN não foi configurado nas variáveis de ambiente da FadeHost.")

bot.run(TOKEN)