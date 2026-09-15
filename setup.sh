#!/usr/bin/env bash
# Автоматическая установка YouTube Content Factory (Mac/Linux)
# Запуск:  chmod +x setup.sh && ./setup.sh
set -e

echo "🎬 Установка YouTube Content Factory..."
echo ""

# 1. Проверяем Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден. Установи его: https://www.python.org/downloads/"
    exit 1
fi
echo "✅ Python найден: $(python3 --version)"

# 2. Создаём виртуальное окружение, если его ещё нет
if [ ! -d "venv" ]; then
    echo "📦 Создаю виртуальное окружение..."
    python3 -m venv venv
fi

# 3. Активируем venv и ставим зависимости
echo "📦 Устанавливаю зависимости (может занять пару минут)..."
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✅ Зависимости установлены"

# 4. Создаём .env, если его нет
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "📝 Создан файл .env"
fi

# 5. Просим ключ Gemini, если он ещё не вписан
if ! grep -q "^GEMINI_API_KEY=.\+" .env 2>/dev/null; then
    echo ""
    echo "🔑 Нужен бесплатный ключ Gemini API."
    echo "   Получи его тут: https://aistudio.google.com/app/apikey"
    read -p "   Вставь ключ сюда (или нажми Enter, чтобы добавить позже): " key
    if [ -n "$key" ]; then
        if grep -q "^GEMINI_API_KEY=" .env; then
            # заменяем строку с ключом
            tmp=$(mktemp)
            sed "s|^GEMINI_API_KEY=.*|GEMINI_API_KEY=$key|" .env > "$tmp" && mv "$tmp" .env
        else
            echo "GEMINI_API_KEY=$key" >> .env
        fi
        echo "✅ Ключ сохранён в .env"
    else
        echo "⚠️ Ключ не задан — впиши его в .env позже (без него будут только шаблонные сценарии)"
    fi
fi

echo ""
echo "🎉 Установка завершена!"
echo ""
echo "Дальше запускай через:  ./start.sh"
