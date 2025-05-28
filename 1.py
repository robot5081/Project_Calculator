import pandas as pd
import matplotlib.pyplot as plt
import telebot
from telebot import types
import re
from mendeleev import get_all_elements


# Генерация файла elements.csv
def create_elements_file():
    elements = []
    for elem in get_all_elements():
        # Обработка атомной массы (удаление квадратных скобок для радиоактивных элементов)
        mass = elem.atomic_weight
        if isinstance(mass, str) and mass.startswith('['):
            mass = mass.strip('[]')

        elements.append({
            'Symbol': elem.symbol,
            'Name': elem.name,
            'MolarMass': float(mass) if mass else None
        })

    df = pd.DataFrame(elements)
    df.dropna(subset=['MolarMass'], inplace=True)  # Удаляем элементы без массы
    df.to_csv('elements.csv', index=False)


# Создаем файл перед запуском бота
create_elements_file()

# Инициализация бота
bot = telebot.TeleBot('токен бота')
elements_df = pd.read_csv('elements.csv')


def parse_formula(formula):
    pattern = re.compile(r'([A-Z][a-z]*)(\d*)')
    elements = pattern.findall(formula)
    return [(elem[0], int(elem[1]) if elem[1] else 1) for elem in elements]


def calculate_molar_mass(formula):
    try:
        elements = parse_formula(formula)
        total_mass = 0
        molar_data = []

        for symbol, count in elements:
            element = elements_df[elements_df['Symbol'] == symbol]
            if element.empty:
                return None, f"Элемент {symbol} не найден"

            molar_mass = element['MolarMass'].values[0]
            element_mass = round(molar_mass * count)
            total_mass += element_mass
            molar_data.append((symbol, element_mass))

        return total_mass, molar_data
    except Exception as e:
        return None, str(e)


def create_mass_chart(molar_data):
    df = pd.DataFrame(molar_data, columns=['Element', 'Mass'])
    plt.figure(figsize=(10, 5))
    plt.bar(df['Element'], df['Mass'])
    plt.title('Вклад элементов в молярную массу')
    plt.xlabel('Элементы')
    plt.ylabel('Масса (г/моль)')
    plt.savefig('molar_chart.png')
    plt.close()


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    help_text = """
📚 *Бот для расчета молярной массы* 
Отправьте химическую формулу (например: H2O, C2H5OH, CaCO3)
"""
    bot.reply_to(message, help_text, parse_mode='Markdown')


@bot.message_handler(func=lambda message: True)
def process_formula(message):
    formula = message.text.strip()
    mass, data_or_error = calculate_molar_mass(formula)

    if mass is None:
        bot.reply_to(message, f"❌ Ошибка: {data_or_error}")
        return

    create_mass_chart(data_or_error)

    response = f"🔬 Молярная масса {formula}: {mass} г/моль\n\n"
    response += "\n".join([f"{elem[0]}: {elem[1]} г/моль" for elem in data_or_error])

    with open('molar_chart.png', 'rb') as photo:
        bot.send_photo(message.chat.id, photo, caption=response)


if __name__ == '__main__':
    print("Бот запущен!")
    bot.polling()