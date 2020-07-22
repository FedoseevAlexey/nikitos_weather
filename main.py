import telebot
import requests
import os
import matplotlib.pyplot as plt

token = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(token)

hello_list = ["привет", "здаров", "ку", "здарова", "здравствуйте", "hello", "hey", "шалом", "салам", "прив", "здрасьте"]
flag = False
current_city = 'крым'
current_weather = {}


def get_weather(city):
    """
        Функция принимает название города,
        переводит название в координаты (ширина и долгота)
        и возвращает json с параметрами погоды данных координат.
    """
    URL_geocoder = 'https://geocode-maps.yandex.ru/1.x'
#     KEY_geocoder = os.environ.get('KEY_GEO')
    KEY_geocoder = 'c9f03f5f-1832-4d23-b829-9ed2d2939857'
    URL_weather = 'https://api.weather.yandex.ru/v2/forecast'
#     KEY_weather = os.environ.get('KEY_WEATHER')
    KEY_weather = '30b3a1e1-af9d-430f-a9ef-3c2d91cbc427'

    params = {
        'apikey': KEY_geocoder,
        'lang': 'ru_RU',
        'format': 'json',
        'geocode': city
    }

    response = requests.get(URL_geocoder, params=params)
    response = response.json()['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point'][
        'pos'].split()
    lat = response[1]
    lon = response[0]

    params = {'lat': lat,
              'lon': lon,
              'lang': 'ru_RU',
              'limit': '3',
              'hours': 'true'}

    answer = requests.get(URL_weather, params=params, headers={'X-Yandex-API-Key': KEY_weather})
    return answer.json()


def get_temp_graph(current_weather, day_number):
    """
        Получает на вход данные прогноза погоды.
        Сохраняет график почасового прогноза температуры в папку с проектом.
    """

    day_weather = current_weather['forecasts'][day_number]['hours']
    temp_list = []
    for day in day_weather:
        temp_list.append(int(day['temp']))

    hours_list = [i for i in range(24)]
    current_date = current_weather['forecasts'][day_number]['date']
    current_date = f'{current_date[-2]}{current_date[-1]}.{current_date[-5]}{current_date[-4]}'

    # Построение графика температуры
    plt.figure(figsize=(25, 10))
    plt.title(f'График температуры на {current_date}', fontsize=30, pad=30, weight='semibold')
    plt.xlabel('Время, часы', fontsize=20, labelpad=20, color='#838383')
    plt.ylabel('Температура, °C', fontsize=20, labelpad=20, color='#838383')
    plt.xticks(hours_list, fontsize=20)
    plt.yticks(temp_list, fontsize=20)
    plt.ylim(ymin=min(temp_list) - 1, ymax=max(temp_list) + 1)
    plt.grid(axis='y')
    plt.bar(hours_list, temp_list, width=0.9, color='#FFB037')
    plt.savefig('plot.png', format='png')
    temp_graph = open('plot.png', 'rb')
    return temp_graph


def get_rain_graph(current_weather, day_number):
    """
        Получает на вход данные прогноза погоды.
        Сохраняет график почасового прогноза дождя в папку с проектом.
    """

    day_weather = current_weather['forecasts'][day_number]['hours']
    rain_list = []
    for hour in day_weather:
        rain_list.append(int(hour['prec_prob']))
    hours_list = [i for i in range(24)]
    current_date = current_weather['forecasts'][day_number]['date']
    current_date = f'{current_date[-2]}{current_date[-1]}.{current_date[-5]}{current_date[-4]}'

    # Построение графика дождя
    plt.figure(figsize=(25, 10))
    plt.title(f'Вероятность дождя {current_date}', fontsize=30, pad=30, weight='semibold')
    plt.xlabel('Время, часы', fontsize=20, labelpad=20, color='#838383')
    plt.ylabel('Вероятность, %', fontsize=20, labelpad=20, color='#838383')
    plt.ylim(ymin=0, ymax=100)

    plt.xticks(hours_list, fontsize=20)
    plt.yticks(rain_list, fontsize=20)
    plt.grid(axis='y')
    plt.bar(hours_list, rain_list, width=0.9, color='#4169E1')
    plt.savefig('rain.png', format='png')
    temp_graph = open('rain.png', 'rb')
    return temp_graph


@bot.message_handler(content_types=['text'])
def get_text_message(message):
    global flag, current_city, current_weather
    if flag:
        flag = False
        # Создаеми добавляем кнопки.
        keyboard = telebot.types.InlineKeyboardMarkup()
        current_button = telebot.types.InlineKeyboardButton(text='Сейчас', callback_data='current_data')
        today_button = telebot.types.InlineKeyboardButton(text='Сегодня', callback_data='today_data')
        tomorrow_button = telebot.types.InlineKeyboardButton(text='Завтра', callback_data='tomorrow_data')
        keyboard.add(current_button)
        keyboard.add(today_button)
        keyboard.add(tomorrow_button)
        bot.send_message(message.from_user.id, "Выберите время:", reply_markup=keyboard)
        current_city = message.text
        try:
            current_weather = get_weather('крым')
        except Exception:
            bot.send_message(message.from_user.id, 'Проверь корректность написания населенного пункта и повтори '
                                                   'попытку - /w.')

    else:
        if message.text.lower() in hello_list:
            bot.send_message(message.from_user.id,
                             'Приветос, я погодный бот Никитос!\nЯ умею предсказывать погоду.\n'
                             '/w - получить прогноз погоды по заданному местоположению.')
        elif message.text.lower() == '/w':
            bot.send_message(message.from_user.id, "Отправь мне название населенного пункта:")
            flag = True
        else:
            bot.send_message(message.from_user.id,
                             "Таких команд я еще не знаю.\n"
                             "/w - получить прогноз погоды по заданному местоположению.")


def get_condition_and_wind(current_condition, current_wind_dir):
    """Перевод погодного описания."""
    # Расшифровка погодного описания.
    condition = {
        'clear': 'Ясно',
        'partly-cloudy': 'Малооблачно',
        'cloudy': 'Облачно с прояснениями',
        'overcast': 'Пасмурно',
        'drizzle': 'Морось',
        'light-rain': 'Небольшой дождь',
        'rain': 'Дождь',
        'moderate-rain': 'Умеренно сильный дождь',
        'heavy-rain': 'Сильный дождь',
        'continuous-heavy-rain': 'Длительный сильный дождь',
        'showers': 'Ливень',
        'wet-snow': 'Дождь со снегом',
        'light-snow': 'Небольшой снег',
        'snow': 'Снег',
        'snow-showers': 'Снегопад',
        'hail': 'Град',
        'thunderstorm': 'Гроза',
        'thunderstorm-with-rain': 'Дождь с грозой',
        'thunderstorm-with-hail': 'Гроза с градом',
    }

    # Расшифровка направления ветра.
    wind_dir = {
        'nw': 'северо-западный',
        'n': 'северный',
        'ne': 'северо-восточный',
        'e': 'восточный',
        'se': 'юго-восточный',
        's': 'южный',
        'sw': 'юго-западный',
        'w': 'западный',
        'c': 'штиль',
    }

    return [condition[current_condition], wind_dir[current_wind_dir]]


def get_current_weather_message():
    """Получение значений текущих погодных данных и составление сообщения пользователю."""

    # Расшифровка температуры.
    current_temperature = current_weather['fact']['temp']
    current_feels_like = current_weather['fact']['feels_like']

    # Расшифровка направления и скорости ветра.
    current_wind_dir = current_weather['fact']['wind_dir']
    current_wind_speed = current_weather['fact']['wind_speed']

    # Расшифровка погодного описания.
    current_condition = current_weather['fact']['condition']
    current_condition_and_wind = get_condition_and_wind(current_condition, current_wind_dir)

    # Расшифровка давления.
    current_pressure = current_weather['fact']['pressure_mm']
    current_uv_index = current_weather['fact']['uv_index']
    current_weather_message = f'''
    Текущая погода:
● На улице сейчас {current_condition_and_wind[0].lower()};
● Температура - {current_temperature}°C (ощущается, как {current_feels_like}°C);
● Ветер {current_condition_and_wind[1]} {current_wind_speed} м/c;
● УФ-индекс {current_uv_index};
● Давление {current_pressure} мм рт. ст.'''
    return current_weather_message


def get_weather_message(day):
    """Получение значений погодных данных на любой день,
        где day - порядковый номер дня (0 - сегодня, 1 - завтра и т.д.)
        Составление сообщения пользователю."""

    # Получение прогноза на утро.
    morning_condition = current_weather['forecasts'][day]['parts']['morning']['condition']
    morning_temperature_min = current_weather['forecasts'][day]['parts']['morning']['temp_min']
    morning_temperature_max = current_weather['forecasts'][day]['parts']['morning']['temp_max']
    morning_wind_speed = current_weather['forecasts'][day]['parts']['morning']['wind_speed']
    morning_wind_dir = current_weather['forecasts'][day]['parts']['morning']['wind_dir']
    morning_uv_index = current_weather['forecasts'][day]['parts']['morning']['uv_index']
    morning_pressure_mm = current_weather['forecasts'][day]['parts']['morning']['pressure_mm']
    morning_condition_and_wind = get_condition_and_wind(morning_condition, morning_wind_dir)

    # Получение прогноза на день.
    day_condition = current_weather['forecasts'][day]['parts']['day']['condition']
    day_temperature_min = current_weather['forecasts'][day]['parts']['day']['temp_min']
    day_temperature_max = current_weather['forecasts'][day]['parts']['day']['temp_max']
    day_wind_speed = current_weather['forecasts'][day]['parts']['day']['wind_speed']
    day_wind_dir = current_weather['forecasts'][day]['parts']['day']['wind_dir']
    day_uv_index = current_weather['forecasts'][day]['parts']['day']['uv_index']
    day_pressure_mm = current_weather['forecasts'][day]['parts']['day']['pressure_mm']
    day_condition_and_wind = get_condition_and_wind(day_condition, day_wind_dir)

    # Получение прогноза на вечер.
    evening_condition = current_weather['forecasts'][day]['parts']['evening']['condition']
    evening_temperature_min = current_weather['forecasts'][day]['parts']['evening']['temp_min']
    evening_temperature_max = current_weather['forecasts'][day]['parts']['evening']['temp_max']
    evening_wind_speed = current_weather['forecasts'][day]['parts']['evening']['wind_speed']
    evening_wind_dir = current_weather['forecasts'][day]['parts']['evening']['wind_dir']
    evening_uv_index = current_weather['forecasts'][day]['parts']['evening']['uv_index']
    evening_pressure_mm = current_weather['forecasts'][day]['parts']['evening']['pressure_mm']
    evening_condition_and_wind = get_condition_and_wind(evening_condition, evening_wind_dir)
    tomorrow_date = current_weather['forecasts'][day]['date']
    new_tomorrow_date = f'{tomorrow_date[-2]}{tomorrow_date[-1]}.{tomorrow_date[-5]}{tomorrow_date[-4]}'

    tomorrow_weather_message = f"""
~~~~ Прогноз на {new_tomorrow_date} ~~~~

Утро:
● +{morning_temperature_min}...{morning_temperature_max}°C ;
● {morning_condition_and_wind[0]};
● Ветер {morning_condition_and_wind[1]} {morning_wind_speed} м/c;
● УФ-индекс {morning_uv_index};
● Давление {morning_pressure_mm} мм рт. ст.

День:
● +{day_temperature_min}...{day_temperature_max}°C ;
● {day_condition_and_wind[0]};
● Ветер {day_condition_and_wind[1]} {day_wind_speed} м/c;
● УФ-индекс {day_uv_index};
● Давление {day_pressure_mm} мм рт. ст.

Вечер:
● +{evening_temperature_min}...{evening_temperature_max}°C ;
● {evening_condition_and_wind[0]};
● Ветер {evening_condition_and_wind[1]} {evening_wind_speed} м/c;
● УФ-индекс {evening_uv_index};
● Давление {evening_pressure_mm} мм рт. ст.
    """
    return tomorrow_weather_message


# Расшифровка УФ-индекса.
uv_index_decryption_message = """
Значение индекса и рекомендуемые меры безопасности:

☀ 1-2 (низкий) - солнцезащитные очки и крема не нужны.

☀ 3-5 (умеренный) - крем 𝐒𝐏𝐅 𝟏𝟓.

☀ 6-7 (высокий) - крем 𝐒𝐏𝐅 𝟑𝟎.

☀ 8-10 (очень высокий) - крем 𝐒𝐏𝐅 𝟑𝟎.

☀ 11 (экстремальный) - крем 𝐒𝐏𝐅 𝟓𝟎. 
"""


# Создаем обработчик нажатий на кнопки.

@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    if current_city:
        if call.data == 'current_data':
            keyboard = telebot.types.InlineKeyboardMarkup()
            uv_index_button = telebot.types.InlineKeyboardButton("Расшифровка УФ-индекса", callback_data='uv_index_data')
            keyboard.add(uv_index_button)
            bot.send_message(call.message.chat.id, get_current_weather_message(), reply_markup=keyboard)
        elif call.data == 'today_data':
            # Создаем и добавляем кнопку побробного прогноза.
            keyboard = telebot.types.InlineKeyboardMarkup()
            more_button = telebot.types.InlineKeyboardButton("Подробный прогноз", callback_data='today_more_data')
            uv_index_button = telebot.types.InlineKeyboardButton("Расшифровка УФ-индекса", callback_data='uv_index_data')
            keyboard.add(more_button)
            keyboard.add(uv_index_button)
            # Отправляем пользователю прогноз погоды на сегодня.
            bot.send_message(call.message.chat.id, get_weather_message(0), reply_markup=keyboard)
        elif call.data == 'tomorrow_data':
            keyboard = telebot.types.InlineKeyboardMarkup()
            more_button = telebot.types.InlineKeyboardButton("Подробный прогноз", callback_data='tomorrow_more_data')
            uv_index_button = telebot.types.InlineKeyboardButton("Расшифровка УФ-индекса", callback_data='uv_index_data')
            keyboard.add(more_button)
            keyboard.add(uv_index_button)
            bot.send_message(call.message.chat.id, get_weather_message(1), reply_markup=keyboard)
        elif call.data == 'today_more_data':
            # Добавляем информацию о восходе и закате солнца.
            sunrise = current_weather['forecasts'][0]['sunrise']
            sunset = current_weather['forecasts'][0]['sunset']
            bot.send_message(call.message.chat.id, f'Восход в {sunrise};\nЗакат в {sunset}.')

            bot.send_photo(call.message.chat.id, get_temp_graph(current_weather, 0))
            # Удаление графика прогноза температуры.
            path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'plot.png')
            os.remove(path)
            # Добавление графика дождя.

            bot.send_photo(call.message.chat.id, get_rain_graph(current_weather, 0))
            # Удаление графика прогноза температуры.
            path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'rain.png')
            os.remove(path)

        elif call.data == 'tomorrow_more_data':
            # Добавление информации о восходе и закате солнца.
            sunrise = current_weather['forecasts'][1]['sunrise']
            sunset = current_weather['forecasts'][1]['sunset']
            bot.send_message(call.message.chat.id, f'Восход в {sunrise};\nЗакат в {sunset}.')
            # Добавление графика температуры.
            bot.send_photo(call.message.chat.id, get_temp_graph(current_weather, 1))
            # Удаление графика прогноза температуры.
            path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'plot.png')
            os.remove(path)

            # Добавление графика дождя.
            bot.send_photo(call.message.chat.id, get_rain_graph(current_weather, 1))
            # Удаление графика прогноза температуры.
            path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'rain.png')
            os.remove(path)
        elif call.data == 'uv_index_data':
            bot.send_message(call.message.chat.id, uv_index_decryption_message)
    else:
        bot.send_message(call.message.chat.id, "Сначала введите название города - /w")


bot.polling(none_stop=True)
