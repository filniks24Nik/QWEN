#!/usr/bin/env bash
# Запуск фабрики (Mac/Linux). Требует, чтобы ./setup.sh уже был выполнен один раз.
set -e
if [ ! -d "venv" ]; then
    echo "❌ Похоже, установка ещё не выполнена. Сначала запусти:  ./setup.sh"
    exit 1
fi
source venv/bin/activate
python main.py "$@"
