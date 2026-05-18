import logging
from aiogram import Bot

logger = logging.getLogger("EduMasterBot.subscription")

async def is_subscribed(bot: Bot, channel_username: str, user_id: int) -> bool:
    # Ensure channel username starts with @ if it's not a numeric ID
    if not channel_username.startswith("@") and not channel_username.startswith("-"):
        channel_username = f"@{channel_username}"
        
    try:
        # Check if the channel is public and accessible
        member = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
        # Allowed states
        if member.status in ["creator", "administrator", "member"]:
            return True
    except Exception as e:
        logger.error(f"Error checking subscription for user {user_id} in {channel_username}: {e}")
        # In case the bot is not an administrator in the channel or cannot find it, return True to not lock out users,
        # or return False if strict subscription is required.
        # But wait, since mandatory subscription is specified: "MANDATORY CHANNEL SUBSCRIPTION"
        # We should assume strict checking. If there's an error (e.g. user not found), return False.
        # However, to be friendly during local tests if the channel doesn't exist, we can return True or False.
        # Let's return False for strict correctness, but we'll print a friendly instruction.
        return False
    return False
