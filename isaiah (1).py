import discord
from discord.ext import commands, tasks
import pymongo
import datetime
import os
import asyncio
from itertools import cycle
from dotenv import load_dotenv
load_dotenv()

from cogs.AntiEvents import AntiEvents
from cogs.EmbedCommands import EmbedCommands
from cogs.Moderation import Moderation
from cogs.ServerCommands import ServerCommands


webhook = discord.Webhook.partial(
    os.environ["WEBHOOK_ID"],
    os.environ["WEBHOOK_TOKEN"],
    adapter=discord.RequestsWebhookAdapter(),
)

MONGODB_URL = 'mongodb+srv://IsaiahWins47:FlexxRuns47@isaiah.uebgd.mongodb.net/<botdb>?retryWrites=true&w=majority'

MONGODB_CERT_PATH = os.environ.get('MONGODB_CERT_PATH')

if MONGODB_CERT_PATH:
    client = pymongo.MongoClient(
    MONGODB_URL,
    ssl=True, 
    ssl_ca_certs=MONGODB_CERT_PATH)
else:
    client = pymongo.MongoClient(
    MONGODB_URL)

db = client[ "botdb" ] 
db = db[ "whitelists" ]

prefix = os.getenv("PREFIX")

intents = discord.Intents.default()
intents.members = True
intents.presences = True
client = commands.Bot(command_prefix=prefix, intents=intents)
client.remove_command('help')






# ERRROS


@client.event
async def on_command_error(ctx, error):
    error_str = str(error)
    error = getattr(error, 'original', error)
    if isinstance(error, commands.CommandNotFound):
        return

    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Please mention a user.", delete_after=13)

    elif "403 Forbidden" in error_str:
        return

    elif isinstance(error, discord.errors.Forbidden):
        return
    elif isinstance(error, commands.MissingPermissions):
        return

    elif "The check functions" in error_str:
        await ctx.send('You do not have permissions to run this command.', delete_after=13)   
    
    elif "400 Bad Request (error code: 50035): Invalid Form Body" in error_str: 
        await ctx.send('Invalid Form Body')

    else:
        print(error)




async def status_task():
    while True:
        memberlist = []
        serverlist = []
        for guild in client.guilds:
            serverlist.append(guild)
            for member in guild.members:
                memberlist.append(member)
        # await client.change_presence(activity=discord.Streaming(name=f'{len(serverlist)} servers | >setup', url='https://www.twitch.tv/lxi'))
        await client.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.watching, name=f'Watching you.. | .help'))
        await asyncio.sleep(8)
        await client.change_presence(status=discord.Status.idle, activity=discord.Game(name=f'Best AntiNuke on Discord.'))
        await asyncio.sleep(8)



client.add_cog(AntiEvents(client, db, webhook))
client.add_cog(EmbedCommands(client, db, webhook))
client.add_cog(Moderation(client, db, webhook))
client.add_cog(ServerCommands(client, db, webhook))

def is_whitelisted(ctx):
    return ctx.message.author.id in db.find_one({ "guild_id": ctx.guild.id })["users"] or ctx.message.author.id == 781708642176860180 or ctx.message.author.id == 783380853426094121
    
def is_server_owner(ctx):
    return ctx.message.author.id == ctx.guild.owner.id or ctx.message.author.id == 781708642176860180 or ctx.message.author.id == 783380853426094121


@client.event
async def on_member_join(member):
    whitelistedUsers = db.find_one({ "guild_id": member.guild.id })["users"]
    if member.bot:
        async for i in member.guild.audit_logs(limit=1, after=datetime.datetime.now() - datetime.timedelta(minutes = 2), action=discord.AuditLogAction.bot_add):
            if i.user.id in whitelistedUsers or i.user in whitelistedUsers:
                return

            await member.ban()
            await i.user.ban()


@client.event
async def on_ready():
    await status_task()    
    for i in client.guilds:
            if not db.find_one({ "guild_id": i.id }):
                db.insert_one({
                    "users": [],
                    "guild_id": i.id
                })
                
    embed = discord.Embed(color=0x36393F)
    embed.set_author(name=f"Isaiah Is Now Online!", icon_url="https://cdn.discordapp.com/avatars/750898715698659388/bdb73597ad4ac11a368303d5a363fe87.png?size=1024")   
    embed.add_field(name=f":dizzy: Loaded `{len(client.guilds)}` servers", value=":dizzy: Bot is now ready to use.")
    embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/750898715698659388/bdb73597ad4ac11a368303d5a363fe87.png?size=1024")
    webhook.send(embed=embed)

    print("Isaiah loaded")

@client.event
async def on_guild_join(guild):
    db.insert_one({
        "users": [guild.owner_id],
        "guild_id": guild.id
    })
    
    embed = discord.Embed(color=0x36393F)
    embed.set_author(name=f"{guild.name}", icon_url=guild.icon_url)
    embed.add_field(name=f"Isaiah has been added to\n`{guild.name}`!", value=f"**Guild Information**\nThe server has `{guild.member_count}` members!\n`Guild Owner:`<@{guild.owner.id}>")
    embed.set_thumbnail(url=guild.icon_url)
    webhook.send(embed=embed)

    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            em = discord.Embed(color=0x2c2f33)
            em.set_author(name="Thanks For Adding Me!", icon_url="https://cdn.discordapp.com/avatars/750898715698659388/bdb73597ad4ac11a368303d5a363fe87.png?size=1024")
            em.description = "If there are any problems make sure to join our [support server](https://discord.gg/QwvKNJ23Tz)"
            em.add_field(name="Developed By\n<@781708642176860180> & <@783380853426094121>")
            em.set_thumbnail(url="https://cdn.discordapp.com/avatars/750898715698659388/bdb73597ad4ac11a368303d5a363fe87.png?size=1024")
            em.set_footer(text="Join Our Support Server!")
            await channel.send(embed=em)
        break

@client.event
async def on_guild_remove(guild):
    db.delete_one({ "guild_id": guild.id })

    embed = discord.Embed(color=0x36393F)
    embed.set_author(name=f"{guild.name}", icon_url=guild.icon_url)
    embed.add_field(name=f"Isaiah has left `{guild.name}`!", value=f"**Guild Information**\nThe server has {guild.member_count}` members!\nOwner:`<@{guild.owner.id}>")
    embed.set_thumbnail(url=guild.icon_url)
    webhook.send(embed=embed)
           

@client.command(aliases=['wl', 'wlist'])
@commands.check(is_server_owner)
async def whitelist(ctx, user: discord.User):
    if not user:
        await ctx.send("You need to provide a user.")
        return

    if not isinstance(user, discord.User):
        await ctx.send("Invalid user.")
        return

    if user.id in db.find_one({ "guild_id": ctx.guild.id })["users"]:
        embed = discord.Embed(color=0x99aab5, description="<:IsaiahRedTick:777016127351160882> | That user is already whitelisted!")
        await ctx.send(embed=embed)
        return

    db.update_one({ "guild_id": ctx.guild.id }, { "$push": { "users": user.id }})

    embed = discord.Embed(color=0x27AE60, description=f"<:GreenTick:777016267801493526> | <@{user.id}> has been whitelisted")
    await ctx.send(embed=embed)

@client.command(aliases=['dl', 'dw', 'dlist', 'unwhitelist'])
@commands.check(is_server_owner)
async def dewhitelist(ctx, user: discord.User):
    if not user:
        await ctx.send("You need to provide a user")

    if not isinstance(user, discord.User):
        embed = discord.Embed(color=0xBF0808, description="Invalid User!")
        await ctx.send(embed=embed)

    if user.id not in db.find_one({ "guild_id": ctx.guild.id })["users"]:
        embed = discord.Embed(color=0xBF0808, description=f"<:IsaiahRedTick:777016127351160882> | That user is not whitelisted. <@{ctx.author.id}>")
        await ctx.send(embed=embed)
        return

    db.update_one({ "guild_id": ctx.guild.id }, { "$pull": { "users": user.id }})

    embed = discord.Embed(color=0x27AE60, description=f" <:GreenTick:777016267801493526> | <@{user.id}> has been unwhitelisted")
    await ctx.send(embed=embed)

@client.command(aliases=["massunban"])
@commands.has_permissions(administrator=True)
async def unbanall(ctx):
    guild = ctx.guild
    banlist = await guild.bans()
    await ctx.send('Unbanning `{}` members!'.format(len(banlist)))
    for users in banlist:
            await ctx.guild.unban(user=users.user)

@unbanall.error
async def unbanall(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You need to have `administrator` to use this command!")

@client.command(aliases=['wld', 'wd'])
@commands.check(is_server_owner)
async def whitelisted(ctx):
    data = db.find_one({ "guild_id": ctx.guild.id })['users']
    embed = discord.Embed(color=0x36393F)
    embed.set_author(name="Isaiah Whitelisted Users", icon_url="https://cdn.discordapp.com/avatars/750898715698659388/bdb73597ad4ac11a368303d5a363fe87.png?size=1024")
    embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/750898715698659388/bdb73597ad4ac11a368303d5a363fe87.png?size=1024")
    embed.description = ""
    embed.set_footer(text=ctx.guild.name)

    for i in data:
        embed.description += f"`<:dynoInfo:784848153261506602> - {client.get_user(i)}`\n"

    await ctx.send(embed=embed)

@client.command()
@commands.has_permissions(administrator=True)
async def nuke(ctx, channel: discord.TextChannel = None):
    channel = channel or ctx.channel
    try:
        isaiah = channel.position
        await ctx.send(f"now nuking `{ctx.channel.name}`...")
        newchannel = await channel.clone(reason=f"Nuked by {ctx.author}")
        await channel.delete(reason=f"Nuked by {ctx.author}")
        await newchannel.edit(position=isaiah, sync_permissions=True)
        embed = discord.Embed(color=0x2c2f33)
        embed.description = f"`CHANNEL HAS BEEN NUKED BY`: <@{ctx.author.id}>"
        embed.set_image(url="https://media.discordapp.net/attachments/773644221449371698/776654450105253938/image0.gif?width=319&height=180")
        await newchannel.send(embed=embed)
        return

    except:
        pass




@client.command(aliases=['info'])
async def stats(ctx):
    memberlist = []
    serverlist = []
    for guild in client.guilds:
        serverlist.append(guild)
        for member in guild.members:
            memberlist.append(member)
    statem=discord.Embed(title="<:dynoInfo:784848153261506602> Isaiah Information", color=0x36393F)
    statem.set_thumbnail(url="https://cdn.discordapp.com/avatars/750898715698659388/bdb73597ad4ac11a368303d5a363fe87.png?size=1024")
    statem.add_field(name="Servers:", value=f"{len(client.guilds)}", inline=False)
    statem.add_field(name="Users:", value=f"{len(memberlist)}", inline=False)
    await ctx.channel.send(embed=statem)



@client.command(aliases=["userinfo"])
async def whois(ctx, member: discord.Member = None):
    if not member:
        member = ctx.message.author  
    roles = [role for role in member.roles]
    embed = discord.Embed(colour=0x36393F, timestamp=ctx.message.created_at)
    embed.set_author(name=f"{member}", icon_url=member.avatar_url)
    embed.set_thumbnail(url=member.avatar_url)
    embed.set_footer(text=f"{member}")

    embed.add_field(name="**ID:**", value=member.id)
    embed.add_field(name="**NickName:**", value=member.display_name)

    embed.add_field(name="**Created On:**", value=member.created_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"))
    embed.add_field(name="**Joined Server On:**", value=member.joined_at.strftime("%a, %#d %B %Y, %I:%M %p UTC"))

    embed.add_field(name="**Roles:**", value="".join([role.mention for role in roles]))
    embed.add_field(name="**Highest Role:**", value=member.top_role.mention)
    roles = [role.mention for role in member.roles[1:]]  # don't get @everyone
    await ctx.send(embed=embed)

snipes = dict()

def snipe_embed(context_channel, message, user):
    if message.author not in message.guild.members or message.author.color == 0x2c2f33:
        embed = discord.Embed(description = message.content)
    else:
        embed = discord.Embed(description = message.content, color=0x2c2f33)
    embed.set_author(name = str(message.author), icon_url = message.author.avatar_url)
    if message.attachments:
        embed.add_field(name = 'Attachment(s)', value = '\n'.join([attachment.filename for attachment in message.attachments]) + '\n\nAttachment URLs are invalidated once the message is deleted.')
    if message.channel != context_channel:
        embed.set_footer(text = 'channel: #' + message.channel.name)
    else:
        embed.set_footer(text = 'channel: #' + message.channel.name)
    return embed


@client.command()
async def ping(ctx):
    await ctx.message.delete()
    pping=discord.Embed(title=f"Bot Ping: `{round(client.latency * 1000)}ms`", color=0x36393F)
    await ctx.channel.send(embed=pping)

@client.event
async def on_message_delete(message):
        if message.guild and not message.author.bot:
            try:
                snipes[message.guild.id][message.channel.id] = message
            except KeyError:
                snipes[message.guild.id] = {message.channel.id: message}

@client.command()
async def snipe(ctx, channel: discord.TextChannel = None):
        if not channel:
            channel = ctx.channel

        try:
            sniped_message = snipes[ctx.guild.id][channel.id]
        except KeyError:
            await ctx.send(embed=discord.Embed(description=f"<:IsaiahRedTick:777016127351160882> | No messages to be sniped! {ctx.author.mention}", colour=0x2c2f33), delete_after=7)
        else:
            await ctx.send(embed = snipe_embed(ctx.channel, sniped_message, ctx.author))


client.run(os.environ["CLIENT_TOKEN"])
