'''
Скрипты терминала:
    python main.py                 # Интерактивный интерфейс на паузе
    python main.py --auto          # Интерфейс с обновлением в 0.6 сек
    python main.py --headless 100  # Вычисляет 100 шагов симуляции и выводит итог
'''

from greenhouse_pkg import main

if __name__ == "__main__":
    main()
