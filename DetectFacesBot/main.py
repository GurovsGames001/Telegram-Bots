import cv2

import telebot
from telebot import types

from telebot import custom_filters
from telebot.handler_backends import State, StatesGroup

from telebot.storage import StateMemoryStorage

import os

# Бот
bot = telebot.TeleBot('6635050658:AAGHzRrt0aAc64mn_cBt_wxqazxmVC5-sAk', state_storage=StateMemoryStorage())


# Создание состояний
class MyStates(StatesGroup):
    mainMenu = State()
    photoFile = State()


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Приветствую!")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Обработать новый файл")
    markup.add(item1)

    bot.set_state(message.from_user.id, MyStates.mainMenu, message.chat.id)
    bot.send_message(message.chat.id, "Наш бот позволяет обнаруживать лица на фотографии.\nЕсли вам, например, нужно убедиться, что ваши друзья являются людьми, а не смешариками, то наш бот сможет вам помочь :)", reply_markup=markup)


@bot.message_handler(state=MyStates.mainMenu)
def runMainMenu(message):
    if message.text == "Обработать новый файл":
        bot.send_message(message.chat.id, "Инструкция:\n1) Отправьте фото.\n3) Получите результат :)")
        # Переход к загрузке первого файла
        bot.set_state(message.from_user.id, MyStates.photoFile, message.chat.id)
        bot.send_message(message.chat.id, 'Отправьте фото: ', reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(state=MyStates.photoFile, content_types=['photo'])
def message1(message):
    # Получение информации о файле
    photo_file_info = bot.get_file(message.photo[-1].file_id)
    # Скачивание файла
    downloaded_photo_file = bot.download_file(photo_file_info.file_path)
    # Сохранение файла
    photo_file_path_1 = "photo.jpg"
    with open(photo_file_path_1, 'wb') as f:
        f.write(downloaded_photo_file)

    # Получение изображения для дальнейшей его обработки средствами OpenCV
    image = cv2.imread(photo_file_path_1)

    # Создание переменной с файлом модели
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # Обесцвечивание изображения
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Процесс обнаруживания лиц на изображении
    faces = face_cascade.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=5)

    # Обрисовка лиц на фото прямоугольниками
    for (x, y, w, h) in faces:
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)

    # Сохранение результата
    cv2.imwrite('result.jpg', image)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Обработать новый файл")
    markup.add(item1)

    # Отправка результата пользователю
    bot.send_message(message.chat.id, 'Наслаждайтесь результатом!', reply_markup=markup)
    bot.send_photo(message.chat.id, open('result.jpg', 'rb'))

    # Удаление временных файлов
    os.remove("photo.jpg")
    os.remove("result.jpg")

    bot.delete_state(message.from_user.id, message.chat.id)
    bot.set_state(message.from_user.id, MyStates.mainMenu, message.chat.id)


# Добавление фильтра для распознавания состояний
bot.add_custom_filter(custom_filters.StateFilter(bot))

bot.infinity_polling(skip_pending=True)