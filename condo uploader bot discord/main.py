# main.py - MULTI COOKIE + AUTO RETRY

import os
import json
import time
import requests
from dotenv import load_dotenv
import discord
from discord.ext import commands
from unblacklister import uniqueId, referentt, assetId
from ad import advertise
from keep_alive import keep_alive

load_dotenv()

TOKEN= os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="-", intents=intents)


# ==========================================
#       ĐỌC DANH SÁCH COOKIE
# ==========================================
def load_cookie_list():
    with open("cookies.txt", "r") as f:
        cookies = [line.strip() for line in f.readlines() if line.strip()]
    return cookies


# ==========================================
#       LẤY CSRF TOKEN
# ==========================================
def get_csrf(cookie):
    try:
        r = requests.post(
            "https://auth.roblox.com/v2/logout",
            cookies={".ROBLOSECURITY": cookie}
        )
        return r.headers.get("x-csrf-token", None)
    except:
        return None


# ==========================================
#       UPLOAD 1 GAME (ONE ATTEMPT)
# ==========================================
def attempt_upload(cookie):
    token = get_csrf(cookie)
    if not token:
        return None, "Cookie die"

    try:
        auth = requests.get(
            "https://users.roblox.com/v1/users/authenticated",
            headers={"x-csrf-token": token},
            cookies={".ROBLOSECURITY": cookie}
        ).json()

        userId = auth["id"]
    except:
        return None, "Token/Authentication lỗi"

    # Lấy GameID
    try:
        inv = requests.get(
            f"https://inventory.roblox.com/v2/users/{userId}/inventory/9?limit=10&sortOrder=Asc",
            headers={"x-csrf-token": token},
            cookies={".ROBLOSECURITY": cookie}
        ).json()

        gameId = inv["data"][0]["assetId"]
    except:
        return None, "Không lấy được GameID"

    # Lấy UniverseID
    try:
        univ = requests.get(
            f"https://apis.roblox.com/universes/v1/places/{gameId}"
        ).json()
        univId = univ["universeId"]
    except:
        return None, "Không lấy được UniverseID"

    # Upload file
    myfile = open("file.rbxlx", "rb").read()
    upload = requests.post(
        f"https://data.roblox.com/Data/Upload.ashx?assetid={gameId}",
        headers={
            "Content-Type": "application/xml",
            "x-csrf-token": token,
            "User-Agent": "Roblox"
        },
        cookies={".ROBLOSECURITY": cookie},
        data=myfile
    )

    if upload.status_code != 200:
        return None, f"Upload thất bại: {upload.status_code}"


    avatartype = "MorphToR6"
    allowprivateservers = True
    playercount = 5
    # Update config
    cfg = {
        "name": "Mr Beast in North Korea",
        "description": " Created by Capybara ",
        "universeAvatarType": avatartype,
        "universeAnimationType": "Standard",
        "maxPlayerCount": playercount,
        "allowPrivateServers": allowprivateservers,
        "privateServerPrice": 0,
        "permissions": {
            "IsThirdPartyTeleportAllowed": True,
            "IsThirdPartyPurchaseAllowed": True
    }

    requests.patch(
        f"https://develop.roblox.com/v2/universes/{univId}/configuration",
        headers={
            "Content-Type": "application/json",
            "x-csrf-token": token
        },
        cookies={".ROBLOSECURITY": cookie},
        data=json.dumps(cfg)
    )

    return gameId, "SUCCESS"


# ==========================================
#   MULTI-COOKIE UPLOAD + AUTO RETRY
# ==========================================
def upload_with_retry():
    cookies = load_cookie_list()

    for index, cookie in enumerate(cookies):

        print(f"\n▶ Đang dùng Cookie ({index+1}/{len(cookies)}): {cookie[:20]}...")

        # Retry 5 lần cho mỗi cookie
        for retry in range(1, 6):
            print(f"   🔄 Attempt {retry}/5...")

            gameId, status = attempt_upload(cookie)

            if gameId:
                print("   ✔ Thành công!")
                return gameId, cookie

            print(f"   ❌ Lỗi: {status}")
            time.sleep(3)

        print("   ⚠ Cookie này không thành công → chuyển cookie khác")

    return None, None



# ==========================================
#          DISCORD UPLOAD COMMAND
# ==========================================
@bot.command()
async def upload(ctx):
    await ctx.send("⏳ Đang upload bằng nhiều cookie... Hãy đợi 10–30s")

    gameId, used_cookie = upload_with_retry()

    if not gameId:
        return await ctx.send("❌ Tất cả cookie đều thất bại!")

    embed = discord.Embed(
        title="🎉 Upload thành công!",
        description="Game đã được upload thành công bằng hệ thống Multi-Cookie",
        color=0x00ff99
    )
    embed.add_field(
        name="Link Game",
        value=f"[Click để chơi](https://www.roblox.com/games/{gameId})",
        inline=False
    )
    embed.add_field(
        name="Cookie sử dụng",
        value=f"```{used_cookie[:60]}...```",
        inline=False
    )

    await ctx.send(embed=embed)

    # Hỏi quảng cáo
    await ctx.send("📢 Quảng cáo game? (Y/N)")

    res = await bot.wait_for(
        "message",
        check=lambda m: m.author == ctx.author
    )

    if res.content.lower().startswith("y"):
        advertise(gameId)
        await ctx.send("📢 Đã quảng cáo!")
    else:
        await ctx.send("🔒 Không quảng cáo.")




keep_alive()
bot.run(TOKEN)
