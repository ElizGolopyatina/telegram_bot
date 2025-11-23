import asyncio
import random
from pathlib import Path

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ChatMemberHandler,
    filters,
)

# ==== ВСТАВЬ СВОЙ ТОКЕН ====
BOT_TOKEN = "8309572422:AAHqWM0LomhwfPNKTZ1-Qjy7jaGBu2h7GC4"
# ============================

IMAGES_DIR = Path(__file__).parent / "images"


def get_random_image_path() -> Path:
    """Выбирает случайный файл из папки images."""
    files = [f for f in IMAGES_DIR.iterdir() if f.is_file()]
    if not files:
        raise RuntimeError("В папке images нет файлов!")
    return random.choice(files)


# --- наша постоянная клавиатура ---
PREDICTION_BUTTON_TEXT = "🔮 Получить предсказание"

def prediction_keyboard() -> ReplyKeyboardMarkup:
    # одна кнопка в одной строке
    keyboard = [[PREDICTION_BUTTON_TEXT]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def send_prediction(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    files = list(IMAGES_DIR.iterdir())

    # оставляем только допустимые картинки
    allowed_ext = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    files = [f for f in files if f.suffix.lower() in allowed_ext]

    print("Файлы в images:", [f.name for f in files])

    if not files:
        await context.bot.send_message(chat_id, "Нет доступных картинок 🙈")
        return

    # перемешиваем, чтобы выбор был случайным
    random.shuffle(files)

    # пробуем отправлять по одной, пока не найдём рабочую
    for img_path in files:
        print("Пробую отправить:", img_path.name)
        try:
            with open(img_path, "rb") as f:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=f,
                    has_spoiler=True,
                )
            print("Успешно отправлена:", img_path.name)
            return  # успех — выходим
        except Exception as e:
            print(f"Ошибка при отправке {img_path.name}: {e}")

    # если ни одна картинка не отправилась
    await context.bot.send_message(
        chat_id,
        "😢 Не удалось отправить ни одну картинку. Возможно, файлы повреждены.",
        reply_markup=prediction_keyboard()
    )


# --- /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Нажми кнопку, чтобы получить предсказание 🔮",
        reply_markup=prediction_keyboard(),
    )


# --- когда пользователь впервые заходит к боту ---
async def on_chat_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = update.my_chat_member
    if not chat_member:
        return

    # когда пользователь становится "member" — он активировал бота
    if chat_member.new_chat_member.status == "member":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Привет! Нажми кнопку, чтобы получить предсказание 🔮",
            reply_markup=prediction_keyboard(),
        )


# --- обработка нажатий на кнопку (как обычный текст) ---
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()

    if text == PREDICTION_BUTTON_TEXT:
        await send_prediction(update.message.chat_id, context)
    else:
        # на любой другой текст можем просто ещё раз показать кнопку
        await update.message.reply_text(
            "Нажми кнопку ниже, чтобы получить предсказание 🔮",
            reply_markup=prediction_keyboard(),
        )


async def main():
    if not IMAGES_DIR.exists():
        print("Папка images не найдена!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # хендлеры
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(ChatMemberHandler(on_chat_join, ChatMemberHandler.MY_CHAT_MEMBER))

    print("Бот запущен. Нажми Ctrl+C для остановки.")

    # ручной жизненный цикл (чтобы не ругался event loop в Python 3.14)
    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    stop = asyncio.Event()
    try:
        await stop.wait()
    except KeyboardInterrupt:
        print("Остановка...")
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


if __name__ == "__main__":

    asyncio.run(main())

