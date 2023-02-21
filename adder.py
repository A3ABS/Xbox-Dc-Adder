import urllib.request
import urllib.error
import discord
import json
import aiohttp


with open('credentials.json', 'r') as f:
    data = json.load(f)

auth_token = data['authorization']
self_xuid = data['self_xuid']
discord_bot_token = data['discord_bot_token']

client = discord.Client(intents=discord.Intents.all())

@client.event
async def on_ready():
    with open('image.png', 'rb') as image:
        await client.user.edit(avatar=image.read())
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if message.content.startswith('!xuid'):
        gamertag = message.content.split(' ', 1)[1]
        try:
            xbl_token, user_hash = await authorize_token(auth_token)
            xuid = await get_xuid(xbl_token, user_hash, gamertag)
            await message.channel.send(f"The XUID for {gamertag} is {xuid}.")
        except Exception as e:
            await message.channel.send(f"Error: {str(e)}")
    elif message.content.startswith('!add'):
        try:
            xuid = message.content.split(" ")[1]
            if not xuid.isnumeric():
                raise ValueError("Invalid xuid")
            
            xbl_token, user_hash = await authorize_token(auth_token)
            response = await make_friends_request(xbl_token, user_hash, xuid)
            await message.channel.send(response)
        except (IndexError, ValueError):
            await message.channel.send("Please provide a valid xuid to add to the friends list.")
        except Exception as e:
            await message.channel.send(f"Error: {str(e)}")

async def get_xuid(xbl_token, user_hash, gamertag) -> str:
    url = f"https://profile.xboxlive.com/users/gt({gamertag})/profile/settings?settings=GameDisplayPicRaw,Gamerscore,Gamertag,AccountTier,XboxOneRep,PreferredColor,RealName,Bio,TenureLevel,Watermarks,Location,IsDeleted,ShowUserAsAvatar"
    hdr = {
        'x-xbl-contract-version': '3',
        'Authorization' : f'XBL3.0 x={user_hash};{xbl_token}'
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=hdr) as response:
            response_data = await response.json()
            xuid = response_data["profileUsers"][0]["id"]
            return xuid

async def authorize_token(auth_token) -> str:
    payload = {
        "RelyingParty": "http://xboxlive.com",
        "TokenType": "JWT",
        "Properties": {
            "UserTokens": [auth_token],
            "SandboxId": "RETAIL"
        }
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("https://xsts.auth.xboxlive.com/xsts/authorize", json=payload) as xsts_request:
            if xsts_request.status in [200, 201, 202, 204]:
                data = await xsts_request.json()

                user_hash = data['DisplayClaims']['xui'][0]['uhs']
                xbl_token = data["Token"]

                print(user_hash, xbl_token)
                return xbl_token, user_hash
            else:
                print("error refreshing token")

async def make_friends_request(xbl_token, user_hash, xuid):
    url = f"https://social.xboxlive.com/users/xuid({self_xuid})/people/xuids?method=add"
    hdr = {
        'x-xbl-contract-version': '2',
        'Authorization' : f'XBL3.0 x={user_hash};{xbl_token}',
        'Accept-Charset': 'UTF-8',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    body = {"xuids": [xuid]}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=hdr, json=body) as response:
            if response.status == 204:
                return "Successfully or already added xuid to friends list"
            else:
                return "Failed to add xuid to friends list"

async def request_social_xboxlive_com(response, xbl_token, user_hash, xuid):
    response[0] = None

    if await make_friends_request(xbl_token, user_hash, xuid):
        try:
            response[0].close()
        except:
            pass

    try:
        req = urllib.request.Request(f"https://social.xboxlive.com/users/xuid({self_xuid})/people/xuids?method=add")

        req.add_header("Authorization", f"XBL3.0 x={user_hash};{xbl_token}")
        req.add_header("Accept-Charset", "UTF-8")
        req.add_header("x-xbl-contract-version", "2")
        req.add_header("Accept", "application/json")
        req.add_header("Content-Type", "application/json")
        req.add_header("Expect", "100-continue")
        body = "{{\"xuids\":[\"{}\"]}}".format
        print("Payload:")
        print(body)
        print(req.headers)

        response[0] = urllib.request.urlopen(req, body.encode("utf-8"))

    except urllib.error.URLError as e:
        if hasattr(e, "code"):
            print("Error code: ", e.code)
        if hasattr(e, "reason"):
            print("Error reason: ", e.reason)
        response[0] = e
        return False
    except Exception as e:
        print("An error occurred:", str(e))
        return False

    return True


client.run(data['discord_bot_token'])

