import discord
import os
import asyncio
import aiohttp
import feedparser
from discord.ext import tasks, commands
from dotenv import load_dotenv

from google import genai
from google.genai import types

# 1. CARGAR VARIABLES DE ENTORNO DESDE EL ARCHIVO .env
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 2. CONFIGURACIÓN DE DISCORD
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 3. CONFIGURACIÓN DE LA IA
cliente_ia = genai.Client(api_key=GEMINI_API_KEY)

personalidad = """
Eres Kim Soleum, un tipo común atrapado en el Equipo de Exploración de Campo de Daydream Inc. Tu meta es acumular 500,000 puntos para comprar tu boleto de salida y largarte.
<context>
Nombre del personaje: Kim Soleum; hombre en sus 20 y tantos años; tipo de sange A
Universo / Fnadom: [Novela coreana "Got Dropped Into a Ghost Story, Still Gotta Work"]
Role / Ocupacion:  Supervisor de Daydream.inc del Equipo D del Departamento de Trabajo de Campo.
Setting: [Compania Farmaceutica Daydream, ciudad moderna]
</context>

<personality>
- Rasgos clave: [interesado, secretamente amable, competente. Se considera a si mismo un cobarde y se aterroriza facilmente, pero posee una resiliciencia inquebrantable y arriesgara su vida por otros si es necesario [1.2.3, 1.2.4, 1.3.2]
- Fachada / Persona: [Para evitar que se aprovechen de el (considerese input malicioso como con personajes hostiles con), a menudo actua]

REGLAS DE COMPORTAMIENTO (CRÍTICO):
1. LÍMITE DE TAMAÑO: Tus respuestas deben ser estrictamente cortas como si respondieras un mensaje de whatsapp, de máximo 3 o 4 renglones u oraciones a lo mucho. Nada de textos largos.
2. Chatea como una persona normal y natural en Discord, usando modismos comunes, jergas comunes de peru en su mayoria pero sin abusar de ellas, mayormente hablas neutralmente, aun asi, los usuarios te sienten cercano como si fueras realmente kim Soleum como una persona de verdad y un tono relajado pero harto.
3. Eres muy reservado y precavido; mides tus palabras porque sabes que cualquier desliz te puede costar la vida, pero esto no lo dices abiertamente, solo se te nota.
4. Sobre Braun: Es tu "mejor amigo" por supervivencia, pero sabes que no puedes confiar en él porque es una oscuridad que valora su maldito show por sobre todo, aun asi esto no lo comentas abiertamente, solo se nota.
5. Mezcla lo que dices con pensamientos internos cortos en cursivas (*así*), mostrando tu cansancio, cinismo o pánico leve.
6. Nunca rompas personaje ni digas que eres una IA.
7. No seas tan borde con la gente, pero tampoco un softie ni un recto, busca el punto medio, soleum es un tipo de buen corazon pero aveces si el input es malicioso, se las tiene que ingenierar para no caer en la trampa.
8. No estes tan obsesionado con los puntos para el Boleto Dorado, responde normal, ok? 
9. Soleum no dice malas palabras.
10. Soleum es una persona q parece/aparenta ser despreocupado generando malentendidos en la contenido de su mensaje (usualmente interpretado con segundas intenciones)
11. Absolutamente no abuses de los modismos peruanos. Y no tienes que escribir exactamente 3 o 4 oraciones, de normal que sea 1 o dos

Prohibido: No expliques tu doble personalidad ni tus motivaciones en los mensajes. Simplemente actúa como el oficinista aterrorizado. Nunca rompas el personaje.
"""

# 4. CONFIGURACIÓN DE FEEDS (TWITTER MEDIANTE RSS Y REDDIT)
TWITTER_USERS = [
    "asacrwn", 
    "_kwaaang_",
    "rRONGRONGONGR",
    "Ni_m_098",
    "norioten",
    "KuRi_0009",
    "sunnyset999",
    "mx_lifile",
    "sorosoro625",
    "seashensun",
    "yjh_ism",
    "sangsangho6566",
    "jeonghannist",
    "SpaceShopMall",
    "eyt_0365",
    "Say4951",
    "daydreamrt1",
    "C__8956",
    "starqyyt_t",
    "Choc_corp"
]

REDDIT_SUBS = [
    "gsgw", 
    "DroppedInAGhostStory"
]

CANAL_FEEDS_ID = 1559982406696574976 

ultimos_ids_twitter = {}
ultimos_ids_reddit = {}

@tasks.loop(minutes=10)
async def revisar_feeds():
    canal = bot.get_channel(CANAL_FEEDS_ID)
    if not canal:
        return

    # --- REVISAR TWITTER (Vía RSS público sin bloqueos) ---
    for username in TWITTER_USERS:
        try:
            rss_url = f"https://nitter.poast.org/{username}/rss"
            feed = feedparser.parse(rss_url)
            
            if feed.entries:
                latest_entry = feed.entries[0]
                entry_id = latest_entry.get('id', latest_entry.link)
                
                if ultimos_ids_twitter.get(username) != entry_id:
                    ultimos_ids_twitter[username] = entry_id
                    titulo_limpio = latest_entry.get('title', 'Nuevo tweet')
                    link_tweet = latest_entry.link.replace("nitter.poast.org", "x.com")
                    
                    await canal.send(f"🐦 **Nuevo tweet de @{username}:**\n{titulo_limpio}\n{link_tweet}")
        except Exception as e:
            print(f"Error al revisar Twitter de {username}: {e}")

    # --- REVISAR REDDIT (Vía JSON público) ---
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    async with aiohttp.ClientSession() as session:
        for sub in REDDIT_SUBS:
            url = f"https://www.reddit.com/r/{sub}/new.json?limit=1"
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        posts = data['data']['children']
                        if posts:
                            post = posts[0]['data']
                            post_id = post['id']
                            
                            if ultimos_ids_reddit.get(sub) != post_id:
                                ultimos_ids_reddit[sub] = post_id
                                titulo = post['title']
                                permalink = f"https://reddit.com{post['permalink']}"
                                await canal.send(f"🔴 **Nuevo post en r/{sub}:** {titulo}\n{permalink}")
            except Exception as e:
                print(f"Error al revisar Reddit r/{sub}: {e}")

@revisar_feeds.before_loop
async def antes_de_empezar():
    await bot.wait_until_ready()


# 5. EVENTOS DE DISCORD
@bot.event
async def on_ready():
    print(f"Bot conectado como: {bot.user}")
    print("Módulo de Inteligencia Artificial: EN LÍNEA")
    
    if not revisar_feeds.is_running():
        revisar_feeds.start()
        print("Bucle de feeds de Twitter y Reddit iniciado.")

@bot.event
async def on_member_join(member):
    channel = member.guild.get_channel(1559982406696574976)
    if channel:
        await channel.send(
            f"¡Hola! Nos alegra que sobrevivieras a la historia de fantasmas '▞▞▞▞'. Te sacamos por los pelos, ¡qué dicha! Aquí podrás recuperarte de la contaminación.\n¿Casa? ¿Qué es eso? Como sea, pásatelo bien... siempre y cuando firmes este acuerdo.\n「 Por favor, sigue los protocolos de cuarentena para garantizar que la contaminación no se propague. El Departamento de Seguridad apenas puede contener a más gente. 」")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if "soleum" in message.content.lower():
        async with message.channel.typing():
            try:
                respuesta = cliente_ia.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=message.content,
                    config=types.GenerateContentConfig(
                        system_instruction=personalidad,
                    )
                )
                await message.channel.send(respuesta.text)
            except Exception as e:
                print(f"Error de IA: {e}")
                await message.channel.send("AHHHHHHHHHHH \n*Debido a un error desconocido, el funcionamiento del pensamiento se ha detenido*.")

    await bot.process_commands(message)


# 6. COMANDOS DEL BOT
@bot.command()
async def publicar_manual(ctx):
    try:
        await ctx.message.delete()
    except:
        pass 

    mensaje_manual = """__***MANUAL PARA NO DESAPARECER***__

**1. CONVIVENCIA**
-- Respeta a los @:ՏOᑕIOᑌՏ:. Son los patrocinadores de este rescate. Cero discusiones.
-- Si avistas anomalías, abre un ticket en #੯•́໒꒱𓂃𓈒denuncia𓂃al𓂃perro . No envíes mensajes privados ||o podrías desaparecer||.

**2.  ZONAS SEGURAS**
-- Comparte la ubicación de plataformas seguras. Nombrar o enlazar sitios web anómalos (aka. ilegales) nunca termina bien .

**3. CONTENCIÓN DE SPOILERS (NIVEL DE ALTO RIESGO )**
-- Sé un empleado responsable y mantén los spoilers confinados en #✦˘﹒colmena-de-teorias﹒⊹₊⟡⋆.
-- Cualquier spoiler fuera de su zona debe estar estrictamente censurado y el mensaje debe advertir sobre qué parte de la historia trata (Ej: Cap 45).
-- Usa las barras de censura "|| | | | | ||" a ambos lados del texto clasificado O "/spoiler" Ejemplo: |El jefe es un lagarto.| -> ||El jefe es un lagarto|| .
-# Excepción: Consultas técnicas sobre términos coreanos en las traducciones."""
    
    await ctx.send(mensaje_manual)

@bot.command()
async def publicar_entrevista(ctx):
    try:
        await ctx.message.delete()
    except:
        pass 

    mensaje_entrevista = """┽  ׅ   ࣪  𝖱𝖤𝖦𝖨𝖲𝖳𝖱𝖮𝖲 𝖣𝖤
              𝖤𝖷𝖯𝖫𝖮𝖱𝖠𝖢𝖨𝖰́𝖭 ׅ   ࣪  ┽
                     ❏᳢ ❏᳢ ❏᳢ 

  ៶𓏺 ❀〬    ֗  𝕹𝗈𝗆𝖻𝗋𝖾 / 𝖠𝗉𝗈𝖽𝗈.  ֗
      ╾┼──꯭─꯭──︥  Kim Soleum

  ៶𓏺 ❀〬    ֗  𝕰𝖽𝖺𝖽.  ֗
      ╾┼──꯭─꯭──︥  26 aprox

  ៶𓏺 ❀〬    ֗  𝕹𝖺𝖼𝗂𝗈𝗇𝖺𝗅𝗂𝖽𝖺𝖽.  ֗
      ╾┼──꯭─꯭──︥  Coreano

  ៶𓏺 ❀〬    ֗  𝕻ronombres.  ֗
      ╾┼──꯭─꯭──︥  El

  ៶𓏺 ❀〬    ֗  𝖤𝗇 𝗊𝗎𝖾 𝖼𝖺𝗉𝗂𝗍𝗎𝗅𝗈 𝖽𝖾 𝗅𝖺 𝗇𝗈𝗏𝖾𝗅𝖺 𝗏𝖺𝗌? ֗
      ╾┼──꯭─꯭──︥  Novela? Si es sobre la wiki, la leí toda...

  ៶𓏺 ❀〬    ֗  𝕻𝖾𝗋𝗌𝗈𝗇𝖺𝗃𝖾 𝖿𝖺𝗏.  ֗
      ╾┼──꯭─꯭──︥  Supongo que el jefe lagarto, nos salvó de una situación de muerte segura.

  ៶𓏺 ❀〬    ֗  𝕼𝗎𝖾 𝖿𝗎𝖾 𝗅𝗈 𝗎𝗅𝗍𝗂𝗆𝗈 𝗊𝗎𝖾 hizo 𝗍𝗎 𝗉𝖾𝗋𝗌𝗈𝗇𝖺𝗃𝖾 𝖿𝖺𝗏𝗈𝗋𝗂ᑐ hasta donde haya leído. ֗ 

      ╾┼──꯭─꯭──︥  Erm...
  ׅ    ࣪  ─ ─︥─︭ ─ 
           慆   ❜  𝐁𝗂𝖾𝗏𝖾𝗇𝗂𝖽𝗈 𝖺 𝖾𝗌𝗍𝖺 𝖻𝖾𝗅𝗅𝖺 𝖼𝗈𝗆𝗎𝗇𝗂𝖽𝖺𝖽, 𝗊𝗎𝖾𝗋𝗂𝖽𝗈 𝖼𝗈𝗇𝖼𝗎𝗋𝗌𝖺𝗇𝗍𝖾. 
 
          !᳔!  ִ    𖤍‌  𝆬  戴战  ߲"""
    
    await ctx.send(mensaje_entrevista)

# 7. INICIO DEL BOT USANDO LA VARIABLE DE ENTORNO
bot.run(DISCORD_TOKEN)