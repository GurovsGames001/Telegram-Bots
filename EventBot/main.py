import psycopg2

import asyncio

from telebot import asyncio_filters
from telebot.async_telebot import AsyncTeleBot
from telebot import types

from telebot.asyncio_storage import StateMemoryStorage

from telebot.asyncio_handler_backends import State, StatesGroup

bot = AsyncTeleBot('6677750545:AAFPsP5TFk-jLH40WuOXpWErYiv9xApHepo', state_storage=StateMemoryStorage())


class MyStates(StatesGroup):
    mainMenu = State()
    inputLastName = State()
    inputFirstName = State()
    inputPatronymic = State()
    inputEmail = State()
    choiceRegistration = State()
    payEventTicket = State()

    inputPasswordOrg = State()
    orgMenu = State()
    inputNameEvent = State()
    inputIsFreeEvent = State()
    inputPriceEvent = State()
    inputPaymentDetails = State()
    inputDateEvent = State()
    inputTimeEvent = State()
    inputTimeClose = State()
    inputPlaceEvent = State()
    inputInfoEvent = State()
    choiceCreationEvent = State()


conn = psycopg2.connect(dbname='events_bot_database', user='gurov.aa',
                        password='12345', host='localhost')
cursor = conn.cursor()


@bot.message_handler(commands=['start'])
async def start_ex(message):
    await bot.send_message(message.chat.id, "Привет!")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("Список мероприятий")
    button2 = types.KeyboardButton("Мои заявки")
    markup.add(button1, button2)

    await bot.set_state(message.from_user.id, MyStates.mainMenu, message.chat.id)
    await bot.send_message(message.chat.id, 'Что вы хотите увидеть?', reply_markup=markup)


# *********************************** КЛИЕНТ ***********************************

@bot.message_handler(state=MyStates.mainMenu)
async def run_main_menu(message):
    if message.text == "Список мероприятий":

        cursor.execute('''SELECT id, name,
                            isfree,
                            to_char(price, \'FM9999999999\'),
                            to_char(date_event, \'dd.mm.yyyy\'),
                            to_char(time_event, \'hh24:mi\'),
                            to_char(time_close, \'hh24:mi\'),
                            place_event, info
                            FROM events''')

        if cursor.rowcount == 0:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button1 = types.KeyboardButton("Вернуться в главное меню")
            markup.add(button1)

            await bot.send_message(message.chat.id, 'Нет доступных мероприятий', reply_markup=markup)

        else:
            for event in cursor:
                event_message = ""
                if event[1][-1] == "\"":
                    event_message += "Название: \"" + str(event[1]) + "\n"
                else:
                    event_message += "Название: \"" + str(event[1]) + "\"\n"
                if event[2]:
                    event_message += "Стоимость: Бесплатно\n"
                else:
                    event_message += "Стоимость: " + str(event[3]) + " рублей\n"
                event_message += "Дата: " + str(event[4]) + "\n"
                event_message += "Время начала: " + str(event[5]) + "\n"
                event_message += "Время окончания: " + str(event[6]) + "\n"
                event_message += "Место проведения: " + str(event[7]) + "\n"
                event_message += "Информация:\n" + str(event[8]) + "\n"

                markup = types.InlineKeyboardMarkup(row_width=1)
                button1 = types.InlineKeyboardButton(text="Забронировать билет",
                                                     callback_data="chooseEvent_" + str(event[0]))
                markup.add(button1)

                await bot.send_message(message.chat.id, str(event_message), reply_markup=markup)

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button1 = types.KeyboardButton("Вернуться в главное меню")
            markup.add(button1)

            await bot.send_message(message.chat.id, 'Выберите мероприятие', reply_markup=markup)

    elif message.text == "Мои заявки":
        user_id = message.from_user.id
        cursor.execute(f'''SELECT applications.id, events.name,
                                    to_char(events.date_event, \'dd.mm.yyyy\'),
                                    to_char(events.time_event, \'hh24:mi\'),
                                    to_char(events.time_close, \'hh24:mi\'),
                                    events.place_event, applications.is_confirmed, applications.is_rejected
                                    FROM applications JOIN events ON applications.event_id = events.id 
                                    WHERE client_telegram_id = {user_id}''')

        if cursor.rowcount == 0:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button1 = types.KeyboardButton("Вернуться в главное меню")
            markup.add(button1)

            await bot.send_message(message.chat.id, 'У вас нет заявок на мероприятия', reply_markup=markup)

        else:
            for application in cursor:
                application_message = ""
                if application[7]:
                    application_message += "❌ ОТКЛОНЕНА ❌\n"
                else:
                    if application[6]:
                        application_message += "✅ ПОДТВЕРЖДЕНА ✅\n"
                    else:
                        application_message += "🕓 ОЖИДАЕТ РАССМОТРЕНИЯ 🕓\n"
                if application[1][-1] == "\"":
                    application_message += "Название: \"" + str(application[1]) + "\n"
                else:
                    application_message += "Название: \"" + str(application[1]) + "\"\n"
                application_message += "Дата: " + str(application[2]) + "\n"
                application_message += "Время начала: " + str(application[3]) + "\n"
                application_message += "Время окончания: " + str(application[4]) + "\n"
                application_message += "Место проведения: " + str(application[5]) + "\n"

                markup = types.InlineKeyboardMarkup(row_width=1)
                button1 = types.InlineKeyboardButton(text="Удалить заявку",
                                                     callback_data="deleteApplication_" + str(application[0]))
                markup.add(button1)

                await bot.send_message(message.chat.id, str(application_message), reply_markup=markup)

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button1 = types.KeyboardButton("Вернуться в главное меню")
            markup.add(button1)

            await bot.send_message(message.chat.id, 'Выберите заявку', reply_markup=markup)

    elif message.text == "Вернуться в главное меню":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Список мероприятий")
        button2 = types.KeyboardButton("Мои заявки")
        markup.add(button1, button2)

        await bot.set_state(message.from_user.id, MyStates.mainMenu, message.chat.id)
        await bot.send_message(message.chat.id, 'Что вы хотите увидеть?', reply_markup=markup)

    elif message.text == "org":
        await bot.send_message(message.chat.id, 'Введите пароль')
        await bot.set_state(message.from_user.id, MyStates.inputPasswordOrg, message.chat.id)

    else:
        await bot.send_message(message.chat.id, 'Пожалуйста, вбейте ответ через кнопку в интерфейсе')


@bot.callback_query_handler(func=lambda call: call.data.startswith('chooseEvent_'))
async def choose_event(call):
    event_id = int(call.data.split('_')[1])
    cursor.execute(f'SELECT name FROM events WHERE id = {event_id} LIMIT 1')
    await bot.send_message(call.message.chat.id, 'Выбранное мероприятие: ' + cursor.fetchone()[0])

    user_id = call.from_user.id
    cursor.execute(f'SELECT * FROM clients WHERE telegram_id = {user_id} LIMIT 1')
    if cursor.rowcount == 0:
        await bot.send_message(call.message.chat.id, 'Вы не зарегистрированы в системе')
        cursor.execute(f'INSERT INTO clients(telegram_id) VALUES ({user_id})')
        cursor.execute(f'INSERT INTO applications(event_id, client_telegram_id, is_confirmed, is_rejected) VALUES ({event_id}, {user_id}, false, false) RETURNING id')
        application_id = cursor.fetchone()[0]
        cursor.execute(f'UPDATE clients SET last_application_id = {application_id} WHERE telegram_id = {user_id}')

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Отменить заявку")
        markup.add(button1)

        await bot.send_message(call.message.chat.id, 'Введите вашу фамилию', reply_markup=markup)
        await bot.set_state(call.from_user.id, MyStates.inputLastName, call.message.chat.id)
    else:
        user = cursor.fetchone()
        user_message = "Вы уже зарегистрированы в системе. Пожалуйста, проверьте свои данные.\n\n"
        user_message += f"1) ФИО: {user[1]} {user[2]} {user[3]}\n"
        user_message += f"2) Email: {user[4]}\n\n"
        user_message += "Хотите изменить данные?"

        cursor.execute(f'INSERT INTO applications(event_id, client_telegram_id, is_confirmed, is_rejected) VALUES ({event_id}, {user_id}, false, false) RETURNING id')
        application_id = cursor.fetchone()[0]
        cursor.execute(f'UPDATE clients SET last_application_id = {application_id} WHERE telegram_id = {user_id}')

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Да")
        button2 = types.KeyboardButton("Нет")
        button3 = types.KeyboardButton("Отменить заявку")
        markup.add(button1, button2, button3)

        await bot.set_state(call.from_user.id, MyStates.choiceRegistration, call.message.chat.id)
        await bot.send_message(call.message.chat.id, user_message, reply_markup=markup)


@bot.message_handler(state=MyStates.choiceRegistration)
async def choice_registration(message):
    if message.text == 'Да':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Отменить заявку")
        markup.add(button1)

        await bot.send_message(message.chat.id, 'Введите вашу фамилию', reply_markup=markup)
        await bot.set_state(message.from_user.id, MyStates.inputLastName, message.chat.id)
    elif message.text == 'Нет':
        user_id = message.from_user.id
        cursor.execute(f'''SELECT events.isfree, events.payment_details FROM applications JOIN events ON 
            applications.event_id = events.id WHERE applications.id = (SELECT last_application_id FROM clients WHERE telegram_id = 
            {user_id} LIMIT 1)''')
        event_payment_details = cursor.fetchone()
        if not event_payment_details[0]:
            conn.commit()
            payment_message = '''Вы создали заявку на платное мероприятие.\nДля того, чтобы организатор подтвердил её, вам нужно оплатить стоимость билета по следующим реквизитам:\n\n''' + event_payment_details[1]

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button1 = types.KeyboardButton("Оплачено")
            button2 = types.KeyboardButton("Отменить заявку")
            markup.add(button1, button2)

            await bot.set_state(message.from_user.id, MyStates.payEventTicket, message.chat.id)
            await bot.send_message(message.chat.id, payment_message, reply_markup=markup)
        else:
            cursor.execute(f'''UPDATE applications SET is_confirmed = true WHERE id = (SELECT last_application_id 
            FROM clients WHERE telegram_id = {user_id} LIMIT 1)''')
            conn.commit()
            await bot.send_message(message.chat.id, 'Вы успешно забронировали билет!')

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button1 = types.KeyboardButton("Список мероприятий")
            button2 = types.KeyboardButton("Мои заявки")
            markup.add(button1, button2)

            await bot.set_state(message.from_user.id, MyStates.mainMenu, message.chat.id)
            await bot.send_message(message.chat.id, 'Что вы хотите увидеть?', reply_markup=markup)
    elif message.text == 'Отменить заявку':
        await cancel_creation_application(message)
    else:
        await bot.send_message(message.chat.id, 'Пожалуйста, вбейте ответ через кнопку в интерфейсе')


@bot.message_handler(state=MyStates.payEventTicket)
async def pay_event_ticket(message):
    if message.text == 'Отменить заявку':
        await cancel_creation_application(message)

    elif message.text == 'Оплачено':
        await bot.send_message(message.chat.id, 'Ожидайте подтверждение заявки от организатора')

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Список мероприятий")
        button2 = types.KeyboardButton("Мои заявки")
        markup.add(button1, button2)

        await bot.set_state(message.from_user.id, MyStates.mainMenu, message.chat.id)
        await bot.send_message(message.chat.id, 'Что вы хотите увидеть?', reply_markup=markup)

    else:
        await bot.send_message(message.chat.id, 'Пожалуйста, вбейте ответ через кнопку в интерфейсе')


@bot.message_handler(state=MyStates.inputLastName)
async def input_last_name(message):
    if message.text == 'Отменить заявку':
        await cancel_creation_application(message)

    else:
        user_id = message.from_user.id
        cursor.execute(f'UPDATE clients SET last_name = \'{message.text}\' WHERE telegram_id = {user_id}')

        await bot.send_message(message.chat.id, 'Введите ваше имя')
        await bot.set_state(message.from_user.id, MyStates.inputFirstName, message.chat.id)


@bot.message_handler(state=MyStates.inputFirstName)
async def input_first_name(message):
    if message.text == 'Отменить заявку':
        await cancel_creation_application(message)

    else:
        user_id = message.from_user.id
        cursor.execute(f'UPDATE clients SET first_name = \'{message.text}\' WHERE telegram_id = {user_id}')

        await bot.send_message(message.chat.id, 'Введите ваше отчество')
        await bot.set_state(message.from_user.id, MyStates.inputPatronymic, message.chat.id)


@bot.message_handler(state=MyStates.inputPatronymic)
async def input_patronymic(message):
    if message.text == 'Отменить заявку':
        await cancel_creation_application(message)

    else:
        user_id = message.from_user.id
        cursor.execute(f'UPDATE clients SET patronymic = \'{message.text}\' WHERE telegram_id = {user_id}')

        await bot.send_message(message.chat.id, 'Введите вашу электронную почту')
        await bot.set_state(message.from_user.id, MyStates.inputEmail, message.chat.id)


@bot.message_handler(state=MyStates.inputEmail)
async def input_email(message):
    if message.text == 'Отменить заявку':
        await cancel_creation_application(message)

    else:
        user_id = message.from_user.id
        cursor.execute(f'UPDATE clients SET email = \'{message.text}\' WHERE telegram_id = {user_id}')
        conn.commit()

        cursor.execute(f'SELECT * FROM clients WHERE telegram_id = {user_id} LIMIT 1')
        user = cursor.fetchone()
        user_message = "Вы зарегистрированы в системе. Пожалуйста, проверьте свои данные.\n\n"
        user_message += f"1) ФИО: {user[1]} {user[2]} {user[3]}\n"
        user_message += f"2) Email: {user[4]}\n\n"
        user_message += "Хотите изменить данные?"

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Да")
        button2 = types.KeyboardButton("Нет")
        button3 = types.KeyboardButton("Отменить заявку")
        markup.add(button1, button2, button3)

        await bot.set_state(message.from_user.id, MyStates.choiceRegistration, message.chat.id)
        await bot.send_message(message.chat.id, user_message, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('deleteApplication_'))
async def delete_application(call):
    application_id = int(call.data.split('_')[1])
    cursor.execute(f'DELETE FROM applications WHERE id = {application_id}')
    conn.commit()
    await bot.send_message(call.message.chat.id, 'Заявка успешно удалена!')

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("Список мероприятий")
    button2 = types.KeyboardButton("Мои заявки")
    markup.add(button1, button2)

    await bot.set_state(call.from_user.id, MyStates.mainMenu, call.message.chat.id)
    await bot.send_message(call.message.chat.id, 'Что вы хотите увидеть?', reply_markup=markup)


async def cancel_creation_application(message):
    user_id = message.from_user.id
    cursor.execute(
        f'DELETE FROM applications WHERE id = (SELECT last_application_id FROM clients WHERE telegram_id = {user_id} LIMIT 1)')
    conn.commit()
    await bot.send_message(message.chat.id, 'Создание заявки отменено')

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("Список мероприятий")
    button2 = types.KeyboardButton("Мои заявки")
    markup.add(button1, button2)

    await bot.set_state(message.from_user.id, MyStates.mainMenu, message.chat.id)
    await bot.send_message(message.chat.id, 'Что вы хотите увидеть?', reply_markup=markup)


# *********************************** ОРГАНИЗАТОР ***********************************

@bot.message_handler(state=MyStates.inputPasswordOrg)
async def input_password_org(message):
    password = message.text

    cursor.execute(f'SELECT * FROM organizers WHERE password = \'{password}\' LIMIT 1')

    if cursor.rowcount == 0:
        await bot.send_message(message.chat.id, 'Неверный пароль')

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Список мероприятий")
        button2 = types.KeyboardButton("Мои заявки")
        markup.add(button1, button2)

        await bot.set_state(message.from_user.id, MyStates.mainMenu, message.chat.id)
        await bot.send_message(message.chat.id, 'Что вы хотите увидеть?', reply_markup=markup)
    else:
        user_id = message.from_user.id
        cursor.execute(f'SELECT * FROM org_sessions WHERE telegram_id = {user_id} LIMIT 1')
        if cursor.rowcount == 0:
            cursor.execute(f'''INSERT INTO org_sessions(telegram_id, organizer_id) 
            VALUES ({user_id}, (SELECT id FROM organizers WHERE password = \'{password}\' LIMIT 1))''')
            conn.commit()
        else:
            cursor.execute(f'''UPDATE org_sessions SET organizer_id = 
                    (SELECT id FROM organizers WHERE password = \'{password}\' LIMIT 1) WHERE telegram_id = {user_id}''')
            conn.commit()

        await bot.send_message(message.chat.id, 'Добро пожаловать в меню организатора!')

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Добавить мероприятие")
        button2 = types.KeyboardButton("Список моих мероприятий")
        button3 = types.KeyboardButton("Список заявок на мои мероприятия")
        button4 = types.KeyboardButton("Вернуться в главное меню")
        markup.add(button1, button2, button3, button4)

        await bot.set_state(message.from_user.id, MyStates.orgMenu, message.chat.id)
        await bot.send_message(message.chat.id, 'Что вы хотите увидеть или сделать?', reply_markup=markup)


@bot.message_handler(state=MyStates.orgMenu)
async def run_org_menu(message):
    if message.text == "Добавить мероприятие":
        user_id = message.from_user.id
        cursor.execute(f'INSERT INTO events(organizer_id) VALUES ((SELECT organizer_id FROM org_sessions WHERE telegram_id = {user_id} LIMIT 1)) RETURNING id')
        event_id = cursor.fetchone()[0]
        cursor.execute(f'UPDATE org_sessions SET last_event_id = {event_id} WHERE telegram_id = {user_id}')
        conn.commit()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Отменить создание мероприятия")
        markup.add(button1)

        await bot.set_state(message.from_user.id, MyStates.inputNameEvent, message.chat.id)
        await bot.send_message(message.chat.id, 'Введите название мероприятия', reply_markup=markup)

    elif message.text == "Список моих мероприятий":
        user_id = message.from_user.id
        cursor.execute(f'''SELECT id, name, isfree,
                                    to_char(price, \'FM9999999999\'),
                                    to_char(date_event, \'dd.mm.yyyy\'),
                                    to_char(time_event, \'hh24:mi\'),
                                    to_char(time_close, \'hh24:mi\'),
                                    place_event, info
                                    FROM events WHERE organizer_id = 
                                    (SELECT organizer_id FROM org_sessions WHERE telegram_id = {user_id} LIMIT 1)''')

        if cursor.rowcount == 0:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button1 = types.KeyboardButton("Вернуться в меню организатора")
            markup.add(button1)

            await bot.send_message(message.chat.id, 'У вас нет созданных мероприятий', reply_markup=markup)

        else:
            for event in cursor:
                event_message = ""
                if event[1][-1] == "\"":
                    event_message += "Название: \"" + str(event[1]) + "\n"
                else:
                    event_message += "Название: \"" + str(event[1]) + "\"\n"
                if event[2]:
                    event_message += "Стоимость: Бесплатно\n"
                else:
                    event_message += "Стоимость: " + str(event[3]) + " рублей\n"
                event_message += "Дата: " + str(event[4]) + "\n"
                event_message += "Время начала: " + str(event[5]) + "\n"
                event_message += "Время окончания: " + str(event[6]) + "\n"
                event_message += "Место проведения: " + str(event[7]) + "\n"
                event_message += "Информация:\n" + str(event[8]) + "\n"

                markup = types.InlineKeyboardMarkup(row_width=1)
                # button1 = types.InlineKeyboardButton(text="Изменить данные",
                #                                      callback_data="changeEvent_" + str(event[0]))
                button2 = types.InlineKeyboardButton(text="Удалить мероприятие",
                                                     callback_data="deleteEvent_" + str(event[0]))
                markup.add(button2)

                await bot.send_message(message.chat.id, str(event_message), reply_markup=markup)

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button1 = types.KeyboardButton("Вернуться в меню организатора")
            markup.add(button1)

            await bot.send_message(message.chat.id, 'Выберите мероприятие', reply_markup=markup)

    elif message.text == "Вернуться в меню организатора":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Добавить мероприятие")
        button2 = types.KeyboardButton("Список моих мероприятий")
        button3 = types.KeyboardButton("Список заявок на мои мероприятия")
        button4 = types.KeyboardButton("Вернуться в главное меню")
        markup.add(button1, button2, button3, button4)

        await bot.set_state(message.from_user.id, MyStates.orgMenu, message.chat.id)
        await bot.send_message(message.chat.id, 'Что вы хотите увидеть или сделать?', reply_markup=markup)

    elif message.text == "Список заявок на мои мероприятия":
        user_id = message.from_user.id
        cursor.execute(f'''SELECT applications.id, events.name, events.isfree,
                        to_char(events.price, \'FM9999999999\'),
                        to_char(events.date_event, \'dd.mm.yyyy\'), 
                        clients.last_name, clients.first_name, 
                        clients.patronymic, clients.email,
                        applications.is_confirmed
                        FROM applications
                        JOIN events ON applications.event_id = events.id
                        JOIN clients ON applications.client_telegram_id = clients.telegram_id
                        WHERE events.organizer_id = (SELECT org_sessions.organizer_id FROM org_sessions 
                        WHERE org_sessions.telegram_id = {user_id})''')

        if cursor.rowcount == 0:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button1 = types.KeyboardButton("Вернуться в меню организатора")
            markup.add(button1)

            await bot.send_message(message.chat.id, 'На ваши мероприятия нет заявок', reply_markup=markup)

        else:
            for application in cursor:
                application_message = ""
                if application[1][-1] == "\"":
                    application_message += "Название: \"" + str(application[1]) + "\n"
                else:
                    application_message += "Название: \"" + str(application[1]) + "\"\n"
                if application[2]:
                    application_message += "Стоимость: Бесплатно\n"
                else:
                    application_message += "Стоимость: " + str(application[3]) + " рублей\n"
                application_message += "Дата: " + str(application[4]) + "\n"
                application_message += f"ФИО клиента: {application[5]} {application[6]} {application[7]}\n"
                application_message += "Email клиента: " + str(application[8]) + "\n"

                if application[9]:
                    await bot.send_message(message.chat.id, str(application_message))
                else:
                    markup = types.InlineKeyboardMarkup(row_width=1)
                    button1 = types.InlineKeyboardButton(text="Подтвердить",
                                                         callback_data="confirmApplication_" + str(application[0]) + "_1")
                    button2 = types.InlineKeyboardButton(text="Отклонить",
                                                         callback_data="confirmApplication_" + str(application[0]) + "_0")
                    markup.add(button1, button2)

                    await bot.send_message(message.chat.id, str(application_message), reply_markup=markup)

            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            button1 = types.KeyboardButton("Вернуться в меню организатора")
            markup.add(button1)

            await bot.send_message(message.chat.id, 'Подтвердите/отклоните заявки', reply_markup=markup)

    elif message.text == "Вернуться в главное меню":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Список мероприятий")
        button2 = types.KeyboardButton("Мои заявки")
        markup.add(button1, button2)

        await bot.set_state(message.from_user.id, MyStates.mainMenu, message.chat.id)
        await bot.send_message(message.chat.id, 'Что вы хотите увидеть?', reply_markup=markup)

    else:
        await bot.send_message(message.chat.id, 'Пожалуйста, вбейте ответ через кнопку в интерфейсе')


@bot.message_handler(state=MyStates.inputNameEvent)
async def input_name_event(message):
    if message.text == 'Отменить создание мероприятия':
        await cancel_creation_event(message)

    else:
        user_id = message.from_user.id
        cursor.execute(f'UPDATE events SET name = \'{message.text}\' WHERE id = (SELECT last_event_id FROM org_sessions WHERE telegram_id = {user_id} LIMIT 1)')
        conn.commit()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Да")
        button2 = types.KeyboardButton("Нет")
        button3 = types.KeyboardButton("Отменить создание мероприятия")
        markup.add(button1, button2, button3)

        await bot.set_state(message.from_user.id, MyStates.inputIsFreeEvent, message.chat.id)
        await bot.send_message(message.chat.id, 'Мероприятие бесплатное?', reply_markup=markup)


@bot.message_handler(state=MyStates.inputIsFreeEvent)
async def input_is_free_event(message):
    if message.text == 'Отменить создание мероприятия':
        await cancel_creation_event(message)

    elif message.text == 'Да':
        user_id = message.from_user.id
        cursor.execute(f'UPDATE events SET isfree = true WHERE id = (SELECT last_event_id FROM org_sessions WHERE telegram_id = {user_id} LIMIT 1)')
        conn.commit()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Отменить создание мероприятия")
        markup.add(button1)

        await bot.set_state(message.from_user.id, MyStates.inputDateEvent, message.chat.id)
        await bot.send_message(message.chat.id, 'Введите дату проведения мероприятия', reply_markup=markup)

    elif message.text == 'Нет':
        user_id = message.from_user.id
        cursor.execute(f'UPDATE events SET isfree = false WHERE id = (SELECT last_event_id FROM org_sessions WHERE telegram_id = {user_id} LIMIT 1)')
        conn.commit()

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Отменить создание мероприятия")
        markup.add(button1)

        await bot.set_state(message.from_user.id, MyStates.inputPriceEvent, message.chat.id)
        await bot.send_message(message.chat.id, 'Введите стоимость билета', reply_markup=markup)

    else:
        await bot.send_message(message.chat.id, 'Пожалуйста, вбейте ответ через кнопку в интерфейсе')


@bot.message_handler(state=MyStates.inputPriceEvent)
async def input_price_event(message):
    if message.text == 'Отменить создание мероприятия':
        await cancel_creation_event(message)

    else:
        try:
            user_id = message.from_user.id
            cursor.execute(
                f'UPDATE events SET price = {message.text} WHERE id = (SELECT last_event_id FROM org_sessions WHERE telegram_id = {user_id} LIMIT 1)')
            conn.commit()

            await bot.set_state(message.from_user.id, MyStates.inputPaymentDetails, message.chat.id)
            await bot.send_message(message.chat.id, 'Введите реквизиты для оплаты билета на мероприятие')
        except Exception:
            conn.rollback()
            await bot.send_message(message.chat.id, 'Неверный формат данных. Введите стоимость билета')


@bot.message_handler(state=MyStates.inputPaymentDetails)
async def input_payment_details(message):
    if message.text == 'Отменить создание мероприятия':
        await cancel_creation_event(message)

    else:
        try:
            user_id = message.from_user.id
            cursor.execute(
                f'UPDATE events SET payment_details = \'{message.text}\' WHERE id = (SELECT last_event_id FROM org_sessions WHERE telegram_id = {user_id} LIMIT 1)')
            conn.commit()

            await bot.set_state(message.from_user.id, MyStates.inputDateEvent, message.chat.id)
            await bot.send_message(message.chat.id, 'Введите дату проведения мероприятия')
        except Exception:
            conn.rollback()
            await bot.send_message(message.chat.id, 'Неверный формат данных. Введите реквизиты для оплаты билета на мероприятие')


@bot.message_handler(state=MyStates.inputDateEvent)
async def input_date_event(message):
    if message.text == 'Отменить создание мероприятия':
        await cancel_creation_event(message)

    else:
        try:
            user_id = message.from_user.id
            cursor.execute(f'UPDATE events SET date_event = \'{message.text}\' WHERE id = (SELECT last_event_id FROM org_sessions WHERE telegram_id = {user_id} LIMIT 1)')
            conn.commit()

            await bot.set_state(message.from_user.id, MyStates.inputTimeEvent, message.chat.id)
            await bot.send_message(message.chat.id, 'Введите время начала мероприятия')
        except Exception:
            conn.rollback()
            await bot.send_message(message.chat.id, 'Неверный формат данных. Введите дату проведения мероприятия')


@bot.message_handler(state=MyStates.inputTimeEvent)
async def input_time_event(message):
    if message.text == 'Отменить создание мероприятия':
        await cancel_creation_event(message)

    else:
        try:
            user_id = message.from_user.id
            cursor.execute(
                f'UPDATE events SET time_event = \'{message.text}\' WHERE id = (SELECT last_event_id FROM org_sessions WHERE telegram_id = {user_id} LIMIT 1)')
            conn.commit()

            await bot.set_state(message.from_user.id, MyStates.inputTimeClose, message.chat.id)
            await bot.send_message(message.chat.id, 'Введите время окончания мероприятия')
        except Exception:
            conn.rollback()
            await bot.send_message(message.chat.id, 'Неверный формат данных. Введите время начала мероприятия')


@bot.message_handler(state=MyStates.inputTimeClose)
async def input_time_event(message):
    if message.text == 'Отменить создание мероприятия':
        await cancel_creation_event(message)

    else:
        try:
            user_id = message.from_user.id
            cursor.execute(
                f'UPDATE events SET time_close = \'{message.text}\' WHERE id = (SELECT last_event_id FROM org_sessions WHERE telegram_id = {user_id} LIMIT 1)')

            await bot.set_state(message.from_user.id, MyStates.inputPlaceEvent, message.chat.id)
            await bot.send_message(message.chat.id, 'Введите место проведения мероприятия')
        except Exception:
            conn.rollback()
            await bot.send_message(message.chat.id, 'Неверный формат данных. Введите время окончания мероприятия')


@bot.message_handler(state=MyStates.inputPlaceEvent)
async def input_place_event(message):
    if message.text == 'Отменить создание мероприятия':
        await cancel_creation_event(message)

    else:
        user_id = message.from_user.id
        cursor.execute(f'UPDATE events SET place_event = \'{message.text}\' WHERE id = (SELECT last_event_id FROM org_sessions WHERE telegram_id = {user_id} LIMIT 1)')

        await bot.set_state(message.from_user.id, MyStates.inputInfoEvent, message.chat.id)
        await bot.send_message(message.chat.id, 'Введите описание мероприятия и прочую необходимую информацию о нём')


@bot.message_handler(state=MyStates.inputInfoEvent)
async def input_info_event(message):
    if message.text == 'Отменить создание мероприятия':
        await cancel_creation_event(message)

    else:
        user_id = message.from_user.id
        cursor.execute(f'UPDATE events SET info = \'{message.text}\' WHERE id = (SELECT last_event_id FROM org_sessions WHERE telegram_id = {user_id} LIMIT 1)')
        conn.commit()

        cursor.execute(f'''SELECT name, isfree,
                                to_char(price, \'FM9999999999\'),
                                to_char(date_event, \'dd.mm.yyyy\'),
                                to_char(time_event, \'hh24:mi\'),
                                to_char(time_close, \'hh24:mi\'),
                                place_event, info
                                FROM events WHERE id = 
                                (SELECT last_event_id FROM org_sessions WHERE telegram_id = {user_id} LIMIT 1)''')
        event = cursor.fetchone()
        event_message = "Вы создали мероприятие. Пожалуйста, проверьте данные о нём.\n\n"
        if event[0][-1] == "\"":
            event_message += "Название: \"" + str(event[0]) + "\n"
        else:
            event_message += "Название: \"" + str(event[0]) + "\"\n"
        if event[1]:
            event_message += "Стоимость: Бесплатно\n"
        else:
            event_message += "Стоимость: " + str(event[2]) + " рублей\n"
        event_message += "Дата: " + str(event[3]) + "\n"
        event_message += "Время начала: " + str(event[4]) + "\n"
        event_message += "Время окончания: " + str(event[5]) + "\n"
        event_message += "Место проведения: " + str(event[6]) + "\n"
        event_message += "Информация:\n" + str(event[7]) + "\n\n"
        event_message += "Хотите изменить данные?"

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Да")
        button2 = types.KeyboardButton("Нет")
        button3 = types.KeyboardButton("Отменить создание мероприятия")
        markup.add(button1, button2, button3)

        await bot.set_state(message.from_user.id, MyStates.choiceCreationEvent, message.chat.id)
        await bot.send_message(message.chat.id, event_message, reply_markup=markup)


@bot.message_handler(state=MyStates.choiceCreationEvent)
async def choice_creation_event(message):
    if message.text == 'Отменить создание мероприятия':
        await cancel_creation_event(message)
    elif message.text == 'Да':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Отменить создание мероприятия")
        markup.add(button1)

        await bot.set_state(message.from_user.id, MyStates.inputNameEvent, message.chat.id)
        await bot.send_message(message.chat.id, 'Введите название мероприятия', reply_markup=markup)
    elif message.text == 'Нет':
        await bot.send_message(message.chat.id, 'Вы успешно создали мероприятие!')

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        button1 = types.KeyboardButton("Добавить мероприятие")
        button2 = types.KeyboardButton("Список моих мероприятий")
        button3 = types.KeyboardButton("Список заявок на мои мероприятия")
        button4 = types.KeyboardButton("Вернуться в главное меню")
        markup.add(button1, button2, button3, button4)

        await bot.set_state(message.from_user.id, MyStates.orgMenu, message.chat.id)
        await bot.send_message(message.chat.id, 'Что вы хотите увидеть или сделать?', reply_markup=markup)


# @bot.callback_query_handler(func=lambda call: call.data.startswith('changeEvent_'))
# async def change_event(call):
#     event_id = int(call.data.split('_')[1])
#     user_id = call.from_user.id
#     cursor.execute(f'UPDATE org_sessions SET last_event_id = {event_id} WHERE telegram_id = {user_id}')
#     conn.commit()
#
#     markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
#     button1 = types.KeyboardButton("Отменить создание мероприятия")
#     markup.add(button1)
#
#     await bot.set_state(call.from_user.id, MyStates.inputNameEvent, call.message.chat.id)
#     await bot.send_message(call.message.chat.id, 'Введите название мероприятия', reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('deleteEvent_'))
async def delete_event(call):
    event_id = int(call.data.split('_')[1])
    cursor.execute(f'DELETE FROM events WHERE id = {event_id}')
    conn.commit()
    await bot.send_message(call.message.chat.id, 'Мероприятие успешно удалено!')


@bot.callback_query_handler(func=lambda call: call.data.startswith('confirmApplication_'))
async def confirm_application(call):
    application_id = int(call.data.split('_')[1])
    is_confirmed = bool(int(call.data.split('_')[2]))

    if is_confirmed:
        cursor.execute(f'UPDATE applications SET is_confirmed = true WHERE id = {application_id}')
        conn.commit()
        await bot.send_message(call.message.chat.id, 'Заявка подтверждена')
    else:
        cursor.execute(f'UPDATE applications SET is_rejected = true WHERE id = {application_id}')
        conn.commit()
        await bot.send_message(call.message.chat.id, 'Заявка отклонена')


async def cancel_creation_event(message):
    user_id = message.from_user.id
    cursor.execute(
        f'DELETE FROM events WHERE id = (SELECT last_event_id FROM org_sessions WHERE telegram_id = {user_id} LIMIT 1)')
    conn.commit()
    await bot.send_message(message.chat.id, 'Создание мероприятия отменено')

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("Добавить мероприятие")
    button2 = types.KeyboardButton("Список моих мероприятий")
    button3 = types.KeyboardButton("Список заявок на мои мероприятия")
    button4 = types.KeyboardButton("Вернуться в главное меню")
    markup.add(button1, button2, button3, button4)

    await bot.set_state(message.from_user.id, MyStates.orgMenu, message.chat.id)
    await bot.send_message(message.chat.id, 'Что вы хотите увидеть или сделать?', reply_markup=markup)


@bot.message_handler(content_types='text')
async def send_error_message(message):
    await bot.send_message(message.chat.id, "Произошёл сбой. Соединение восстановлено")

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton("Список мероприятий")
    button2 = types.KeyboardButton("Мои заявки")
    markup.add(button1, button2)

    await bot.set_state(message.from_user.id, MyStates.mainMenu, message.chat.id)
    await bot.send_message(message.chat.id, 'Что вы хотите увидеть?', reply_markup=markup)


bot.add_custom_filter(asyncio_filters.StateFilter(bot))
bot.add_custom_filter(asyncio_filters.IsDigitFilter())


asyncio.run(bot.polling())
