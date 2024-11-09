from pydub import AudioSegment

import telebot
from telebot import types

from telebot import custom_filters
from telebot.handler_backends import State, StatesGroup

from telebot.storage import StateMemoryStorage

import os

# Бот
bot = telebot.TeleBot('6267222781:AAE_BRbGHF5CxLVBwZS0ulSoj49-61iiP_Y', state_storage=StateMemoryStorage())


# Создание состояний
class MyStates(StatesGroup):
    mainMenu = State()
    firstFile = State()
    secondFile = State()


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Приветствую!")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Создать новый файл")
    markup.add(item1)

    bot.set_state(message.from_user.id, MyStates.mainMenu, message.chat.id)
    bot.send_message(message.chat.id, "Наш бот позволяет наложить один аудиофайл на другой, создав единую аудиодорожку.\nЭто может быть полезно, если вам нужно, например, соединить вокал с минусовкой.", reply_markup=markup)


@bot.message_handler(state=MyStates.mainMenu)
def runMainMenu(message):
    if message.text == "Создать новый файл":
        bot.send_message(message.chat.id, "Инструкция:\n1) Отправьте первый аудиофайл в формате mp3.\n2) Отправьте второй аудиофайл в формате mp3.\n3) Получите результат :)")
        # Переход к загрузке первого файла
        bot.set_state(message.from_user.id, MyStates.firstFile, message.chat.id)
        bot.send_message(message.chat.id, 'Отправьте первый файл: ', reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(state=MyStates.firstFile, content_types=['audio'])
def message1(message):
    # Получение информации о файле
    audio_file_info = bot.get_file(message.audio.file_id)
    # Скачивание файла
    downloaded_audio_file = bot.download_file(audio_file_info.file_path)
    # Сохранение файла
    audio_file_path_1 = "m1.mp3"
    with open(audio_file_path_1, 'wb') as f:
        f.write(downloaded_audio_file)

    # Переход к загрузке второго файла
    bot.set_state(message.from_user.id, MyStates.secondFile, message.chat.id)
    bot.send_message(message.chat.id, 'Отправьте второй файл: ')


@bot.message_handler(state=MyStates.secondFile, content_types=['audio'])
def message2(message):
    # Получение информации о файле
    audio_file_info = bot.get_file(message.audio.file_id)
    # Скачивание файла
    downloaded_audio_file = bot.download_file(audio_file_info.file_path)
    # Сохранение файла
    audio_file_path_2 = "m2.mp3"
    with open(audio_file_path_2, 'wb') as f:
        f.write(downloaded_audio_file)

    # Создание аудиосегмента для каждого загруженного файла
    bot.send_message(message.chat.id, 'Наложение...')
    sound1 = AudioSegment.from_file("m1.mp3")
    sound2 = AudioSegment.from_file("m2.mp3")

    # Процесс наложения
    combined = sound1.overlay(sound2)

    # Сохранение файла с результатом наложения
    combined.export("result.mp3", format='mp3')

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Создать новый файл")
    markup.add(item1)

    # Отправка результата пользователю
    bot.send_message(message.chat.id, 'Наслаждайтесь результатом!', reply_markup=markup)
    with open("result.mp3", 'rb') as audio_file:
        bot.send_audio(message.chat.id, audio_file)

    # Удаление временных файлов
    os.remove("m1.mp3")
    os.remove("m2.mp3")
    os.remove("result.mp3")

    bot.delete_state(message.from_user.id, message.chat.id)
    bot.set_state(message.from_user.id, MyStates.mainMenu, message.chat.id)

# Добавление фильтра для распознавания состояний
bot.add_custom_filter(custom_filters.StateFilter(bot))

bot.infinity_polling(skip_pending=True)