from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from anonclient.client import AnonChatAsync
from aiogram.bot import Bot
from aiogram.dispatcher import Dispatcher
from aiogram import types, executor
from anonclient.payload_pb2 import Message, Action, TextMessage
import asyncio
from dotenv import load_dotenv, dotenv_values


load_dotenv()
bot = Bot(token=dotenv_values()['TELEGRAM_APIKEY'])
dp = Dispatcher(bot)

class Chat(AnonChatAsync):
    def __init__(self, url, token):
        super().__init__(url, token)
        self.connected_id = []
    async def on_paired(self, id):
        self.connected_id.append(id)
        await bot.send_message(int(id), 'Anda telah terhubung dgn seseorang')
    async def on_message(self, message: Message, from_me: bool):
        if not from_me:
            await bot.send_message(message.id, message.textMessage.text)
    async def on_close(self, id, ws_partner_closed, from_me):
        self.connected_id.remove(id)
        await bot.send_message(int(id), 'chat berhasil diputuskan' if from_me else 'teman chat anda telah memutuskan anda')
    async def on_action(self, id, action_id):
        if action_id == Action.TIMEOUT:
            await bot.send_message(int(id), 'Waktu Habis')
        elif action_id == Action.DUPLICATE:
            await bot.reply('Anda masih dalam chat')
    async def on_connected(self):
        print('connected')

async def main():
    chat = await Chat(dotenv_values()['ANONCHAT_SERVER'],dotenv_values()['ANONCHAT_APIKEY'])
    @dp.message_handler(commands=['start'])
    async def start(msg: types.Message):
        await msg.reply('started')
    @dp.message_handler(commands=['search'])
    async def search(msg: types.Message):
        await chat.send_payload(Action(name=Action.PAIR, id=msg.from_user.id.__str__()))
        await msg.reply('Sedang Melakukan Pencarian')
    @dp.message_handler()
    async def forwarder(msg: types.Message):
        if msg.from_user.id.__str__() in chat.connected_id:
            await chat.send_payload(Message(id=msg.from_user.id.__str__(), textMessage=TextMessage(text=msg.text)))
        else:
            await msg.reply('ketik /search untuk melakukan pencarian')
    await chat.ws.wait_closed()

loop = asyncio.get_event_loop()
asyncio.run_coroutine_threadsafe(main(), loop)
executor.start_polling(dp, skip_updates=True)