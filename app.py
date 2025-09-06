from flask import Flask
import requests

app = Flask(__name__)

# Функция для получения курсов валют с API
def get_exchange_rates(base='USD'):
    url = f"https://api.exchangerate-api.com/v4/latest/{base}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['rates']
    else:
        return None

@app.route('/')
def home():
    rates = get_exchange_rates()
    if rates is None:
        return "<h1>Ошибка: Не удалось получить данные о курсах валют.</h1>"

    # Простой HTML для отображения
    html = """
    <html>
    <head>
        <title>Курсы валют</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            table { border-collapse: collapse; width: 50%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <h1>Курсы валют относительно USD</h1>
        <p>Данные обновляются при перезагрузке страницы.</p>
        <table>
            <tr><th>Валюта</th><th>Курс к 1 USD</th></tr>
    """

    # Добавляем несколько популярных валют (можно расширить)
    currencies = ['EUR', 'RUB', 'GBP', 'JPY', 'CNY', 'BTC']  # Примеры
    for currency in currencies:
        if currency in rates:
            html += f"<tr><td>{currency}</td><td>{rates[currency]:.4f}</td></tr>"

    html += """
        </table>
    </body>
    </html>
    """

    return html

if __name__ == '__main__':
       # Render требует, чтобы приложение слушало PORT из переменной окружения
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)