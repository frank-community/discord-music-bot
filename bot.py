import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
import nest_asyncio
nest_asyncio.apply()
# bot設定
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "quiet": True,
    "extract_flat": "in_playlist"
}

FFMPEG_OPTIONS = {
    "options": "-vn"
}

ytdl = YoutubeDL(YTDL_OPTIONS)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get("title")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or discord.utils.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if "entries" in data:
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS), data=data)

@bot.command()
async def join(ctx):
    if not ctx.author.voice:
        return await ctx.send("VCに接続してから実行してください。")
    channel = ctx.author.voice.channel
    voice = await channel.connect(timeout=10, reconnect=True)

    await channel.connect()

@bot.command()
async def play(ctx, *, url: str):
    voice = ctx.voice_client or await ctx.author.voice.channel.connect()
    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        voice.play(player, after=lambda e: print(f"再生終了: {e}") if e else None)
    await ctx.send(f"再生開始: **{player.title}**")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("VCから切断しました。")
    else:
        await ctx.send("BotはVCに接続していません。")

bot.run("")
