#!/usr/bin/env python3
"""
Скрипт для быстрого обновления токенов в .env файле
"""
import os
import re

def update_env_token(key, value):
    """Обновляет значение переменной в .env файле"""
    env_path = '.env'
    
    if not os.path.exists(env_path):
        print(f"❌ Файл {env_path} не найден!")
        return False
    
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Ищем строку с ключом
    pattern = f'^{key}=.*$'
    replacement = f'{key}={value}'
    
    if re.search(pattern, content, re.MULTILINE):
        # Заменяем существующее значение
        new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"✅ {key} обновлен")
        return True
    else:
        print(f"❌ Ключ {key} не найден в .env")
        return False

def main():
    print("=" * 70)
    print("🔐 ОБНОВЛЕНИЕ ТОКЕНОВ VFS GLOBAL")
    print("=" * 70)
    print()
    print("Откройте сайт https://services.vfsglobal.by/")
    print("Нажмите F12 -> Network -> выполните запрос CheckIsSlotAvailable")
    print("Скопируйте заголовки и вставьте ниже:")
    print()
    
    # Запрашиваем новые токены
    print("-" * 70)
    print("1️⃣  AUTHORIZE:")
    print("   (Найдите в Request Headers -> authorize)")
    authorize = input("   Вставьте: ").strip()
    
    print()
    print("-" * 70)
    print("2️⃣  CLIENTSOURCE:")
    print("   (Найдите в Request Headers -> clientsource)")
    clientsource = input("   Вставьте: ").strip()
    
    print()
    print("-" * 70)
    print("3️⃣  COOKIES:")
    print("   (Найдите в Request Headers -> cookie)")
    cookies = input("   Вставьте: ").strip()
    
    print()
    print("=" * 70)
    print("📝 Обновляю .env файл...")
    print("=" * 70)
    
    success = True
    if authorize:
        success &= update_env_token('AUTHORIZE', authorize)
    
    if clientsource:
        success &= update_env_token('CLIENTSOURCE', clientsource)
    
    if cookies:
        success &= update_env_token('COOKIES', cookies)
    
    print()
    if success:
        print("🎉 Токены успешно обновлены!")
        print()
        print("Теперь запустите бота:")
        print("  source venv/bin/activate")
        print("  python main.py")
    else:
        print("⚠️  Произошли ошибки при обновлении")
    
    print("=" * 70)

if __name__ == "__main__":
    main()

