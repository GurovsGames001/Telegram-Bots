import sqlite3
from telebot import asyncio_filters
from telebot.async_telebot import AsyncTeleBot
from telebot import types

# list of storages, you can use any storage
from telebot.asyncio_storage import StateMemoryStorage

# new feature for states.
from telebot.asyncio_handler_backends import State, StatesGroup

# default state storage is statememorystorage
bot = AsyncTeleBot('6237729033:AAGfs1b5O7atv3JdpPfjIGXDwGTSewQUxy8', state_storage=StateMemoryStorage())


# Just create different statesgroup
class MyStates(StatesGroup):
    mainMenu = State()
    maxStone = State()  # statesgroup should contain states
    startStone = State()
    numberGame = State()


# set_state -> sets a new state
# delete_state -> delets state if exists
# get_state -> returns state if exists


@bot.message_handler(commands=['start'])
async def start_ex(message):
    await bot.send_message(message.chat.id, "Привет!")

    connect = sqlite3.connect('games.db')
    cursor = connect.cursor()

    cursor.execute("""CREATE TABLE IF NOT EXISTS game(id INTEGER PRIMARY KEY AUTOINCREMENT, 
        nStone INTEGER, maxStone INTEGER, 
        player1_id INTEGER, player2_id INTEGER, winner_id INTEGER, isDelete BOOLEAN)""")
    connect.commit()
    connect.execute('pragma journal_mode=wal')
    connect.commit()

    cursor.close()
    connect.close()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Игра в камни")
    markup.add(item1)

    await bot.set_state(message.from_user.id, MyStates.mainMenu, message.chat.id)
    await bot.send_message(message.chat.id, 'Выберите игру', reply_markup=markup)


@bot.message_handler(state="*", commands='cancel')
async def any_state(message):
    """
    Cancel state
    """
    await bot.send_message(message.chat.id, "Your state was cancelled.")
    await bot.delete_state(message.from_user.id, message.chat.id)


@bot.message_handler(state=MyStates.mainMenu)
async def message_reply(message):
    if message.text=="Игра в камни":
        await bot.send_message(message.chat.id, "Начинаю игру...")
        await bot.send_message(message.chat.id, "Правила игры: \n"
                         + "1) Перед игроками лежит куча камней.\n"
                         + "2) Игрокам доступны заранее определенные действия с этой кучей: добавить 1 камень или увеличить количество камней в 2 раза.\n"
                         + "3) Игроки ходят строго по очереди. Первым ходит создатель игровой сессии.\n"
                         + "4) Цель игры — достичь максимального количества камней в куче.")


        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Создать игру")
        item2 = types.KeyboardButton("Присоединиться к игре")
        markup.add(item1, item2)
        await bot.send_message(message.chat.id, 'Выберите действие: ', reply_markup=markup)


    elif message.text == "Создать игру":
        connect = sqlite3.connect('games.db')
        cursor = connect.cursor()

        person_id = message.chat.id
        cursor.execute(
            "INSERT INTO game (nStone, maxStone, player1_id, player2_id, winner_id, isDelete) VALUES(?, ?, ?, ?, ?, ?);",
            (0, 0, person_id, 0, 0, False))
        connect.commit()

        cursor.execute("SELECT id FROM game WHERE player1_id = ?", (person_id,))
        db = cursor.fetchone()
        numberGame = db[0]

        connect.close()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Возврат в главное меню")
        markup.add(item1)

        await bot.set_state(message.from_user.id, MyStates.maxStone, message.chat.id)
        await bot.send_message(message.chat.id, 'Введите максимальное количество камней в куче: ',
                         reply_markup=markup)


    elif message.text == "Присоединиться к игре":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Возврат в главное меню")
        markup.add(item1)

        await bot.set_state(message.from_user.id, MyStates.numberGame, message.chat.id)
        await bot.send_message(message.chat.id, 'Введите номер игровой сессии: ',
                               reply_markup=markup)


    elif message.text == "Добавить 1 камень":
        connect = sqlite3.connect('games.db')
        cursor = connect.cursor()

        person_id = message.chat.id
        cursor.execute("SELECT id FROM game WHERE player1_id = ? OR player2_id = ?", (person_id, person_id,))
        db1 = cursor.fetchone()
        numberGame = db1[0]

        cursor.execute("UPDATE game SET nStone=nStone+1 WHERE id = ?", (numberGame,))
        connect.commit()

        cursor.execute("SELECT nStone FROM game WHERE id = ?", (numberGame,))
        db2 = cursor.fetchone()
        cursor.execute("SELECT maxStone FROM game WHERE id = ?", (numberGame,))
        maxStone = cursor.fetchone()

        nStone = db2[0]
        await bot.send_message(message.chat.id, 'Количество камней в куче: ' + str(nStone))
        if nStone >= maxStone[0]:
            cursor.execute("UPDATE game SET winner_id = ? WHERE id = ?", (person_id, numberGame,))
            connect.commit()

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item1 = types.KeyboardButton("Завершить игру")
            markup.add(item1)
            await bot.send_message(message.chat.id, 'Вы выиграли!', reply_markup=markup)
        else:
            markup2 = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item1 = types.KeyboardButton("Завершить игру")
            markup2.add(item1)
            await bot.send_message(message.chat.id, 'Ожидание хода другого игрока...', reply_markup=markup2)

            cursor.execute("SELECT nStone, isDelete FROM game WHERE id = ?", (numberGame,))
            newNStone = cursor.fetchone()
            while newNStone[0] == nStone:
                cursor.execute("SELECT nStone, isDelete FROM game WHERE id = ?", (numberGame,))
                newNStone = cursor.fetchone()
                if newNStone[1]:
                    await bot.send_message(message.chat.id, 'Игра была завершена раньше времени кем-то из игроков :(')
                    #bot.register_next_step_handler(message, message_reply)
                    break
                elif newNStone[0] != nStone:
                    break
                else:
                    await asyncio.sleep(0)
            if newNStone[1] == False:
                if newNStone[0] >= maxStone[0]:
                    await bot.send_message(message.chat.id, 'Выиграл другой игрок!')
                else:
                    await bot.send_message(message.chat.id, 'Количество камней в куче: ' + str(newNStone[0]))
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    item1 = types.KeyboardButton("Добавить 1 камень")
                    item2 = types.KeyboardButton("Увеличить количество камней в 2 раза")
                    item3 = types.KeyboardButton("Завершить игру")
                    markup.add(item1, item2, item3)
                    await bot.send_message(message.chat.id, 'Ваш ход:', reply_markup=markup)
        connect.close()

    elif message.text == "Увеличить количество камней в 2 раза":
        connect = sqlite3.connect('games.db')
        cursor = connect.cursor()

        person_id = message.chat.id
        cursor.execute("SELECT id FROM game WHERE player1_id = ? OR player2_id = ?", (person_id, person_id,))
        db1 = cursor.fetchone()
        numberGame = db1[0]

        cursor.execute("UPDATE game SET nStone=nStone*2 WHERE id = ?", (numberGame,))
        connect.commit()

        cursor.execute("SELECT nStone FROM game WHERE id = ?", (numberGame,))
        db2 = cursor.fetchone()
        cursor.execute("SELECT maxStone FROM game WHERE id = ?", (numberGame,))
        maxStone = cursor.fetchone()
        cursor.execute("SELECT isDelete FROM game WHERE id = ?", (numberGame,))
        isDelete = cursor.fetchone()

        nStone = db2[0]
        await bot.send_message(message.chat.id, 'Количество камней в куче: ' + str(nStone))

        if nStone >= maxStone[0]:
            cursor.execute("UPDATE game SET winner_id = ? WHERE id = ?", (person_id, numberGame,))
            connect.commit()

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item1 = types.KeyboardButton("Завершить игру")
            markup.add(item1)
            await bot.send_message(message.chat.id, 'Вы выиграли!', reply_markup=markup)
        else:
            markup2 = types.ReplyKeyboardMarkup(resize_keyboard=True)
            item1 = types.KeyboardButton("Завершить игру")
            markup2.add(item1)
            await bot.send_message(message.chat.id, 'Ожидание хода другого игрока...', reply_markup=markup2)

            cursor.execute("SELECT nStone, isDelete FROM game WHERE id = ?", (numberGame,))
            newNStone = cursor.fetchone()
            while newNStone[0] == nStone:
                cursor.execute("SELECT nStone, isDelete FROM game WHERE id = ?", (numberGame,))
                newNStone = cursor.fetchone()
                if newNStone[1]:
                    await bot.send_message(message.chat.id, 'Игра была завершена раньше времени кем-то из игроков :(')
                    #bot.register_next_step_handler(message, message_reply)
                    break
                elif newNStone[0] != nStone:
                    break
                else:
                    await asyncio.sleep(0)
            if newNStone[1] == False:
                if newNStone[0] >= maxStone[0]:
                    await bot.send_message(message.chat.id, 'Выиграл другой игрок!')
                else:
                    await bot.send_message(message.chat.id, 'Количество камней в куче: ' + str(newNStone[0]))
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    item1 = types.KeyboardButton("Добавить 1 камень")
                    item2 = types.KeyboardButton("Увеличить количество камней в 2 раза")
                    item3 = types.KeyboardButton("Завершить игру")
                    markup.add(item1, item2, item3)
                    await bot.send_message(message.chat.id, 'Ваш ход:', reply_markup=markup)
        connect.close()


    elif message.text == "Завершить игру":
        await bot.send_message(message.chat.id, 'Конец игры!')

        person_id = message.chat.id
        connect = sqlite3.connect('games.db')
        cursor = connect.cursor()

        cursor.execute("SELECT player2_id, isDelete FROM game WHERE player1_id = ? OR player2_id = ?",
                       (person_id, person_id,))
        db = cursor.fetchone()

        if (db[1]) or (db[0] == 0):
            cursor.execute("DELETE FROM game WHERE player1_id = ? OR player2_id = ?", (person_id, person_id,))
            connect.commit()
        else:
            cursor.execute("UPDATE game SET isDelete=true WHERE player1_id = ? OR player2_id = ?",
                           (person_id, person_id,))
            connect.commit()
        connect.close()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Игра в камни")
        markup.add(item1)
        await bot.send_message(message.chat.id, 'Выберите игру', reply_markup=markup)



@bot.message_handler(state=MyStates.maxStone, is_digit=True)
async def inputMaxStone(message):
    maxStone = message.text
    maxStone = int(maxStone)
    if maxStone < 0:
        await bot.send_message(message.chat.id, 'Количество камней не может быть отрицательным числом')
        await bot.send_message(message.chat.id, 'Введите максимальное количество камней в куче: ')
    else:
        person_id = message.chat.id
        connect = sqlite3.connect('games.db')
        cursor = connect.cursor()
        cursor.execute("SELECT id FROM game WHERE player1_id = ?", (person_id,))
        db = cursor.fetchone()
        numberGame = db[0]
        cursor.execute("UPDATE game SET maxStone = ? WHERE id = ?", (maxStone, numberGame,))
        connect.commit()
        connect.close()

        await bot.set_state(message.from_user.id, MyStates.startStone, message.chat.id)
        await bot.send_message(message.chat.id, 'Введите начальное количество камней в куче: ')


@bot.message_handler(state=MyStates.maxStone, is_digit=False)
async def inputMaxStoneWithError(message):
    if message.text == "Возврат в главное меню":
        person_id = message.chat.id
        connect = sqlite3.connect('games.db')
        cursor = connect.cursor()

        cursor.execute("DELETE FROM game WHERE player1_id = ?", (person_id,))
        connect.commit()
        connect.close()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Игра в камни")
        markup.add(item1)

        await bot.set_state(message.from_user.id, MyStates.mainMenu, message.chat.id)
        await bot.send_message(message.chat.id, 'Выберите игру', reply_markup=markup)
    else:
        await bot.send_message(message.chat.id,'Неверный формат данных')
        await bot.send_message(message.chat.id, 'Введите максимальное количество камней в куче: ')


@bot.message_handler(state=MyStates.startStone, is_digit=True)
async def inputStartStone(message):
    startStone = message.text
    startStone = int(startStone)
    if startStone < 0:
        await bot.send_message(message.chat.id, 'Количество камней не может быть отрицательным числом')
        await bot.send_message(message.chat.id, 'Введите начальное количество камней в куче: ')
    else:
        person_id = message.chat.id
        connect = sqlite3.connect('games.db')
        cursor = connect.cursor()
        cursor.execute("SELECT id FROM game WHERE player1_id = ?", (person_id,))
        db = cursor.fetchone()
        numberGame = db[0]
        cursor.execute("UPDATE game SET nStone = ? WHERE id = ?", (startStone, numberGame,))
        connect.commit()

        await bot.send_message(message.chat.id, 'Игра создана!\nНомер игровой сессии: ' + str(numberGame))
        markup2 = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Завершить игру")
        markup2.add(item1)
        await bot.send_message(message.chat.id, 'Ожидание второго игрока...', reply_markup=markup2)

        cursor.execute("SELECT player2_id FROM game WHERE id = ?", (numberGame,))
        idPlayer2 = cursor.fetchone()
        newIdPlayer2 = idPlayer2
        while newIdPlayer2[0] == 0:
            cursor.execute("SELECT player2_id FROM game WHERE id = ?", (numberGame,))
            newIdPlayer2 = cursor.fetchone()
            if newIdPlayer2[0] != 0:
                break
            else:
                await asyncio.sleep(0)

        cursor.execute("SELECT* FROM game WHERE id = ?", (numberGame,))
        db = cursor.fetchone()
        await bot.send_message(message.chat.id, 'Второй игрок присоединился!\nНачальное количество камней в куче: '
                        + str(db[1]) + '\nМаксимальное количество камней в куче: ' + str(db[2]))
        connect.close()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Добавить 1 камень")
        item2 = types.KeyboardButton("Увеличить количество камней в 2 раза")
        item3 = types.KeyboardButton("Завершить игру")
        markup.add(item1, item2, item3)

        await bot.set_state(message.from_user.id, MyStates.mainMenu, message.chat.id)
        await bot.send_message(message.chat.id, 'Ваш ход:', reply_markup=markup)


@bot.message_handler(state=MyStates.startStone, is_digit=False)
async def inputStartStoneWithError(message):
    if message.text == "Возврат в главное меню":
        person_id = message.chat.id
        connect = sqlite3.connect('games.db')
        cursor = connect.cursor()

        cursor.execute("DELETE FROM game WHERE player1_id = ?", (person_id,))
        connect.commit()
        connect.close()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Игра в камни")
        markup.add(item1)

        await bot.set_state(message.from_user.id, MyStates.mainMenu, message.chat.id)
        await bot.send_message(message.chat.id, 'Выберите игру', reply_markup=markup)
    elif message.text == "Завершить игру":
        await bot.send_message(message.chat.id, 'Конец игры!')

        person_id = message.chat.id
        connect = sqlite3.connect('games.db')
        cursor = connect.cursor()

        cursor.execute("SELECT player2_id, isDelete FROM game WHERE player1_id = ? OR player2_id = ?",
                       (person_id, person_id,))
        db = cursor.fetchone()

        if (db[1]) or (db[0] == 0):
            cursor.execute("DELETE FROM game WHERE player1_id = ? OR player2_id = ?", (person_id, person_id,))
            connect.commit()
        else:
            cursor.execute("UPDATE game SET isDelete=true WHERE player1_id = ? OR player2_id = ?",
                           (person_id, person_id,))
            connect.commit()
        connect.close()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Игра в камни")
        markup.add(item1)
        await bot.set_state(message.from_user.id, MyStates.mainMenu, message.chat.id)
        await bot.send_message(message.chat.id, 'Выберите игру', reply_markup=markup)
    else:
        await bot.send_message(message.chat.id,'Неверный формат данных')
        await bot.send_message(message.chat.id, 'Введите начальное количество камней в куче: ')


@bot.message_handler(state=MyStates.numberGame, is_digit=True)
async def inputNumberGame(message):
    numberGame = message.text
    numberGame = int(numberGame)

    connect = sqlite3.connect('games.db')
    cursor = connect.cursor()
    cursor.execute("SELECT id FROM game WHERE id = ?", (numberGame,))
    data_id = cursor.fetchone()
    if data_id is None:
        connect.close()
        await bot.send_message(message.chat.id, 'Игровой сессии с таким номером не существует')
        await bot.send_message(message.chat.id, 'Введите номер игровой сессии: ')
    else:
        person_id = message.chat.id
        cursor.execute("UPDATE game SET player2_id = ? WHERE id = ?", (person_id, numberGame,))
        connect.commit()

        cursor.execute("SELECT* FROM game WHERE id = ?", (numberGame,))
        db = cursor.fetchone()
        await bot.send_message(message.chat.id, 'Вы присоединились к игре!\nНачальное количество камней в куче: '
                        + str(db[1]) + '\nМаксимальное количество камней в куче: ' + str(db[2]))

        markup2 = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Завершить игру")
        markup2.add(item1)
        await bot.send_message(message.chat.id, 'Ожидание хода первого игрока...', reply_markup=markup2)

        nStone = db[1]
        cursor.execute("SELECT nStone, maxStone, isDelete FROM game WHERE id = ?", (numberGame,))
        newNStone = cursor.fetchone()
        while newNStone[0] == nStone:
            cursor.execute("SELECT nStone, maxStone, isDelete FROM game WHERE id = ?", (numberGame,))
            newNStone = cursor.fetchone()

            if newNStone[2]:
                connect.close()
                await bot.set_state(message.from_user.id, MyStates.mainMenu, message.chat.id)
                await bot.send_message(message.chat.id, 'Игра была завершена раньше времени кем-то из игроков :(')
                break
            elif newNStone[0] != nStone:
                break
            else:
                await asyncio.sleep(0)

        connect.close()
        if newNStone[2] == False:
            if newNStone[0] >= newNStone[1]:
                await bot.send_message(message.chat.id, 'Выиграл другой игрок!')
            else:
                await bot.send_message(message.chat.id, 'Количество камней в куче: ' + str(newNStone[0]))

                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                item1 = types.KeyboardButton("Добавить 1 камень")
                item2 = types.KeyboardButton("Увеличить количество камней в 2 раза")
                item3 = types.KeyboardButton("Завершить игру")
                markup.add(item1, item2, item3)

                await bot.set_state(message.from_user.id, MyStates.mainMenu, message.chat.id)
                await bot.send_message(message.chat.id, 'Ваш ход:', reply_markup=markup)


@bot.message_handler(state=MyStates.numberGame, is_digit=False)
async def inputNumberGameWithError(message):
    if message.text == "Возврат в главное меню":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Игра в камни")
        markup.add(item1)

        await bot.set_state(message.from_user.id, MyStates.mainMenu, message.chat.id)
        await bot.send_message(message.chat.id, 'Выберите игру', reply_markup=markup)
    elif message.text == "Завершить игру":
        await bot.send_message(message.chat.id, 'Конец игры!')

        person_id = message.chat.id
        connect = sqlite3.connect('games.db')
        cursor = connect.cursor()

        cursor.execute("SELECT player2_id, isDelete FROM game WHERE player1_id = ? OR player2_id = ?",
                       (person_id, person_id,))
        db = cursor.fetchone()

        if (db[1]) or (db[0] == 0):
            cursor.execute("DELETE FROM game WHERE player1_id = ? OR player2_id = ?", (person_id, person_id,))
            connect.commit()
        else:
            cursor.execute("UPDATE game SET isDelete=true WHERE player1_id = ? OR player2_id = ?",
                           (person_id, person_id,))
            connect.commit()
        connect.close()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Игра в камни")
        markup.add(item1)
        await bot.set_state(message.from_user.id, MyStates.mainMenu, message.chat.id)
        await bot.send_message(message.chat.id, 'Выберите игру', reply_markup=markup)
    else:
        await bot.send_message(message.chat.id,'Неверный формат данных')
        await bot.send_message(message.chat.id, 'Введите номер игровой сессии: ')


@bot.message_handler(content_types='text')
async def message_reply(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("Игра в камни")
    markup.add(item1)

    await bot.set_state(message.from_user.id, MyStates.mainMenu, message.chat.id)
    await bot.send_message(message.chat.id, 'Выберите игру', reply_markup=markup)


# await bot.delete_state(message.from_user.id, message.chat.id)


# register filters

bot.add_custom_filter(asyncio_filters.StateFilter(bot))
bot.add_custom_filter(asyncio_filters.IsDigitFilter())

import asyncio

asyncio.run(bot.polling())