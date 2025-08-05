import os
import logging
import asyncio
from dotenv import load_dotenv
import tempfile
from pathlib import Path
from uuid import uuid4
import torch

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.types import Message

from llm_api import LLMService

load_dotenv()
TOKEN = os.getenv("SUPER_BOT_KEY")

bot = Bot(token=TOKEN)
dp = Dispatcher()

llm_service = LLMService(model="gpt-4.1-mini")


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Привет, я бот, у которого можно спросить про магистратуру ИТМО!!!"
    )

@dp.message(F.text)
async def handle_text(message: Message):
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    user_query = message.text
    user_id = str(message.from_user.id)
    try:
        llm_answer = llm_service.generate(user_query)
    except Exception as e:
        logging.error(f"Ошибка генерации ответа LLM: {e}", exc_info=True)
        await message.answer("Произошла ошибка при генерации ответа. Попробуйте позже.")
    await message.answer(llm_answer)


@dp.message(~(F.content_type.in_({"text"})))
async def handle_other(message: Message):
    await message.answer("Извините, я понимаю только текст.")


async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())