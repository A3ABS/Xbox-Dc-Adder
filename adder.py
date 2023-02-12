import urllib.request
import urllib.error
import discord
import json

with open('credentials.json', 'r') as f:
    data = json.load(f)

auth_token = data['authorization']
self_xuid = data['self_xuid']
discord_bot_token = data['discord_bot_token']

client = discord.Client(intents=discord.Intents.all())

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    global xuid
    if message.author == client.user:
        return
    
    if message.content.startswith('!add'):
        xuid = message.content.split(" ")[1]
        response = make_requests(xuid)
        await message.channel.send(response)

def make_requests(xuid):
	response = [None]

	if(request_social_xboxlive_com(response, xuid)):
		response[0].close()
		if response[0].code == 204:
			return "Successfully or already added xuid to friends list"
		else:
			return "Failed to add xuid to friends list"
	else:
		return "Failed to make request to Xbox Live servers"

def request_social_xboxlive_com(response, xuid):
    response[0] = None

    try:
        req = urllib.request.Request(f"https://social.xboxlive.com/users/xuid({self_xuid})/people/xuids?method=add")

        req.add_header("Authorization", auth_token)
        req.add_header("Accept-Charset", "UTF-8")
        req.add_header("x-xbl-contract-version", "2")
        req.add_header("Accept", "application/json")
        req.add_header("Content-Type", "application/json")
        req.add_header("Expect", "100-continue")

        body = "{{\"xuids\":[\"{}\"]}}".format(xuid)
        print("Payload:")
        print(body)

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

