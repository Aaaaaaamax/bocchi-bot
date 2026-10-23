import discord
from discord.ext import commands, tasks
import pytz
from datetime import datetime
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# --- 1. ระบบเว็บเซิร์ฟเวอร์จำลองสำหรับ Render (เพิ่มเข้ามาใหม่ตรงนี้) ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bocchi Bot is running 24/7!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

# รันเว็บเซิร์ฟเวอร์แยกออกไปอีก Thread พร้อมกับบอท
web_thread = threading.Thread(target=run_web_server)
web_thread.daemon = True
web_thread.start()
# -------------------------------------------------------------

# --- 2. โค้ดบอทเดิมของคุณ ---
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

target_channel_id = None
Bangkok_tz = pytz.timezone('Asia/Bangkok')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Slash commands synced successfully!")
    except Exception as e:
        print(e)
    
    # เปิดใช้งานลูปเวลาถ้ายังไม่ได้เริ่ม
    if not scheduled_task.is_running():
        scheduled_task.start()

@bot.tree.command(name="setup", description="ตั้งค่าห้องสำหรับแจ้งเตือนและล็อกห้องอัตโนมัติ")
@discord.app_commands.describe(channel="เลือกห้องแชทที่ต้องการ")
async def setup(interaction: discord.Interaction, channel: discord.TextChannel):
    global target_channel_id
    target_channel_id = channel.id
    
    await interaction.response.send_message(
        f"✅ ตั้งค่าเรียบร้อย! บอทจะล็อกห้อง {channel.mention} ตอน 23:59 และเปิดห้องตอน 06:00",
        ephemeral=False
    )

@bot.tree.command(name="test_lock", description="[ทดสอบ] สั่งล็อกห้องทันทีเพื่อเช็คระบบ")
async def test_lock(interaction: discord.Interaction):
    global target_channel_id
    if target_channel_id is None:
        await interaction.response.send_message("❌ ยังไม่ได้ตั้งค่าห้อง! กรุณาใช้คำสั่ง /setup ก่อน", ephemeral=True)
        return

    channel = bot.get_channel(target_channel_id)
    if channel is None:
        await interaction.response.send_message("❌ ไม่พบห้องแชทที่ตั้งค่าไว้", ephemeral=True)
        return

    guild = channel.guild
    overwrite = channel.overwrites_for(guild.default_role)
    overwrite.send_messages = False
    await channel.set_permissions(guild.default_role, overwrite=overwrite)
    
    await interaction.response.send_message("🔒 **[ทดสอบ] สั่งล็อกห้องเรียบร้อย! (ปิดไม่ให้พิมพ์)**")

@bot.tree.command(name="test_unlock", description="[ทดสอบ] สั่งเปิดห้องทันทีเพื่อเช็คระบบ")
async def test_unlock(interaction: discord.Interaction):
    global target_channel_id
    if target_channel_id is None:
        await interaction.response.send_message("❌ ยังไม่ได้ตั้งค่าห้อง! กรุณาใช้คำสั่ง /setup ก่อน", ephemeral=True)
        return

    channel = bot.get_channel(target_channel_id)
    if channel is None:
        await interaction.response.send_message("❌ ไม่พบห้องแชทที่ตั้งค่าไว้", ephemeral=True)
        return

    guild = channel.guild
    overwrite = channel.overwrites_for(guild.default_role)
    overwrite.send_messages = True
    await channel.set_permissions(guild.default_role, overwrite=overwrite)
    
    await interaction.response.send_message("🔓 **[ทดสอบ] สั่งเปิดห้องเรียบร้อย! (ให้พิมพ์ได้)**")

@tasks.loop(minutes=1)
async def scheduled_task():
    global target_channel_id
    if target_channel_id is None:
        return

    now = datetime.now(Bangkok_tz)
    current_time = now.strftime("%H:%M")
    
    channel = bot.get_channel(target_channel_id)
    if channel is None:
        return

    guild = channel.guild
    overwrite = channel.overwrites_for(guild.default_role)

    if current_time == "06:00":
        overwrite.send_messages = True
        await channel.set_permissions(guild.default_role, overwrite=overwrite)
        await channel.send("🔓 **เปิดให้หาคีย์ได้แล้วนะ**")

    elif current_time == "23:59":
        overwrite.send_messages = False
        await channel.set_permissions(guild.default_role, overwrite=overwrite)
        await channel.send("🔒 **ปิดให้หาคีย์นะครับ**")

# ดึง Token จาก Environment Variable เพื่อความปลอดภัย ป้องกัน GitHub บล็อก
bot.run(os.getenv('DISCORD_TOKEN'))

