from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from sqlalchemy.orm import sessionmaker
from song_database_setup import engine, Song

import re

ALLOWED_PATTERN = re.compile(r"^[1-9a-zA-Zа-яА-Я _-]+$")

def is_valid_song_text(text: str) -> bool:
    return bool(ALLOWED_PATTERN.fullmatch(text))


TOKEN = "8369625560:AAGuHIkFsmPzj6wkfRjEZqn7OVXDuAHi2cY"
CHANNEL_ID = "-1003394233404"  # ID of the target Telegram channel to receive new song submissions

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
👋 В этом боте вы Вы можете предложить песню для новогодней дискотеки. На каждого человека есть по 2 песни.
    
Песни должны быть с с отсутствием (или минимальным количеством) мата (всю грязь обрежем и запикаем).
Без упоминания запрещенных законодательством РФ тем.
    
❗️ Если вы предложите песню, нарушающую правила, вы просто потеряете один выбор.
    
Для предложения песни используйте: <code>/song [автор и название песни]</code>""", parse_mode="HTML")


async def song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: <code>/song [автор и название песни]</code>", parse_mode="HTML")
        return

    query = " ".join(context.args).strip()

    if not is_valid_song_text(query):
        await update.message.reply_text(
            "❌ Недопустимые символы.\n\n"
            "Разрешены только:\n"
            "• буквы (a–z, а–я)\n"
            "• цифры (1–9)\n"
            "• пробел\n"
            "• символы - _"
        )
        return

    # Prepare DB session
    SessionLocal = sessionmaker(bind=engine)
    user_id = update.effective_user.id if update.effective_user else None

    if user_id is None:
        await update.message.reply_text("Не удалось определить ваш ID пользователя Telegram. Попробуйте ещё раз позже.")
        return

    session = SessionLocal()
    try:
        # Check how many songs this user has already submitted
        existing_count = session.query(Song).filter(Song.user_id == user_id).count()
        if existing_count >= 2:
            await update.message.reply_text("😔 Вы уже предложили две песни.")
            return

        # Create and persist the song record
        new_song = Song(user_id=user_id, song_title=query)
        session.add(new_song)
        session.commit()

        await update.message.reply_text(
            f"✅ Песня предложена: <code>{query}</code>",
            parse_mode="HTML",
        )

        # Try to notify the channel about the new submission (non-blocking for user flow)
        try:
            user = update.effective_user
            user_mention = user.mention_html() if user else f"ID: {user_id}"
            channel_text = (
                f"🎵 Новая песня\n"
                f"Песня: <code>{query}</code>\n"
                f"От: {user_mention} (ID: <code>{user_id}</code>)"
            )
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=channel_text,
                parse_mode="HTML",
                disable_web_page_preview=True,
            )
        except Exception as notify_err:
            # Do not affect user flow if the channel notification fails
            print(f"Failed to send notification to channel {CHANNEL_ID}: {notify_err}")
    except Exception as e:
        session.rollback()
        # Log error to console for maintainers
        print(f"Error while saving song to DB: {e}")
        await update.message.reply_text(
            "⚠️ Что-то пошло не так. Попробуйте ещё раз")
    finally:
        session.close()

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("song", song))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
