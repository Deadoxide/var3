# uvm_asm.py
import pprint
import sys

# ------------------------------------------------------------
# Кодирование инструкции по спецификации:
#   Биты 0–6: поле A (opcode)
#   Биты 7–32: поле B (операнд)
# Размер команды: 5 байт, порядок little-endian.
# ------------------------------------------------------------

def pack_instruction(a: int, b: int) -> bytes:
    """
    Упаковывает A и B в 5 байт по спецификации:
        value = A | (B << 7)
    """
    if a < 0 or a >= (1 << 7):
        raise ValueError(f"Поле A (opcode) должно помещаться в 7 бит: 0..127, получено {a}")
    if b < 0 or b >= (1 << 26):
        raise ValueError(f"Поле B (операнд) должно помещаться в 26 бит: 0..(2^26-1), получено {b}")

    value = a | (b << 7)
    return value.to_bytes(5, "little")


# --- Коды операций согласно спецификации УВМ (поле A, биты 0–6) ---

OP_LOAD_CONST = 14  # Загрузка константы
OP_READ       = 11  # Чтение значения из памяти
OP_WRITE      = 94  # Запись значения в память
OP_LESS       = 69  # Бинарная операция "<"


# --- Функции генерации байт-кода под новую спецификацию ---

def asm_load_const(const: int) -> bytes:
    """
    Загрузка константы.
    A = 14, B = const.
    Тест (A=14, B=381):
        0x8E, 0xBE, 0x00, 0x00, 0x00
    """
    return pack_instruction(OP_LOAD_CONST, const)


def asm_read_value(address: int) -> bytes:
    """
    Чтение значения из памяти.
    A = 11, B = address.
    Тест (A=11, B=435):
        0x8B, 0xD9, 0x00, 0x00, 0x00
    """
    return pack_instruction(OP_READ, address)


def asm_write_value(address: int) -> bytes:
    """
    Запись значения в память.
    A = 94, B = address.
    Тест (A=94, B=308):
        0x5E, 0x9A, 0x00, 0x00, 0x00
    """
    return pack_instruction(OP_WRITE, address)


def asm_less(address: int) -> bytes:
    """
    Бинарная операция "<".
    A = 69, B = address.
    По спецификации:
      - первый операнд: значение в памяти по адресу B,
      - второй операнд: регистр-аккумулятор,
      - результат: записывается по адресу B.
    Тест (A=69, B=989):
        0xC5, 0xEE, 0x01, 0x00, 0x00
    """
    return pack_instruction(OP_LESS, address)


# --- Главная функция трансляции IR в байт-код ---

def asm(IR: list) -> bytes:
    """
    Транслирует промежуточное представление (IR) в последовательность байт-кода.
    IR — список кортежей вида:
        ('load_const', value)
        ('read_value', address)
        ('write_value', address)
        ('less', address)
    """
    bytecode = bytes()
    for op, *arg in IR:
        if op == "load_const":
            bytecode += asm_load_const(arg[0])
        elif op == "read_value":
            bytecode += asm_read_value(arg[0])
        elif op == "write_value":
            bytecode += asm_write_value(arg[0])
        elif op == "less":
            bytecode += asm_less(arg[0])
        else:
            raise ValueError(f"Неизвестная команда ассемблера: {op}")
    return bytecode


# --- Парсер исходного текста ASM в IR и байт-код ---

def full_asm(text: str) -> tuple[bytes, list]:
    """
    Читает текст программы, преобразует его в байт-код и IR.
    Формат строки: "команда; аргумент"
        load_const; 381
        read_value; 435
        write_value; 308
        less; 989
    Комментарии после '#' игнорируются.
    """
    text = text.strip()
    IR = []

    for line in text.splitlines():
        line = line.strip()

        # 1. Удаляем хвостовой комментарий
        if "#" in line:
            line = line.split("#")[0].strip()

        # 2. Пустые строки игнорируем
        if not line:
            continue

        # 3. Парсинг "cmd; arg"
        parts = line.split(";")
        cmd = parts[0].strip()

        if len(parts) > 1 and parts[1].strip():
            arg = parts[1].strip()
            IR.append((cmd, int(arg)))
        else:
            raise ValueError(f"Команда '{cmd}' требует аргумент (формат: '{cmd}; число').")

    # Генерируем байт-код
    bytecode = asm(IR)
    return bytecode, IR


# --- Тестовый вывод IR и байт-кода (для режима тестирования/отладки) ---

def print_ir_test_mode(IR: list, bytecode: bytes):
    """Выводит IR и байт-код, а также разбор по инструкциям (5 байт на команду)."""
    print("\n--- Промежуточное представление (IR) ---")
    pprint.pprint(IR)

    print("\n--- Сгенерированный байт-код (в байтовом формате) ---")
    print(*(f"0x{b:02X}" for b in bytecode))

    print("\n--- Представление по инструкциям (5 байт на команду) ---")
    current_byte_index = 0
    for i, (op, *arg) in enumerate(IR):
        instruction_bytes = bytecode[current_byte_index: current_byte_index + 5]
        current_byte_index += 5

        opcode_hex = " ".join(f"{b:02X}" for b in instruction_bytes)
        arg_value = arg[0] if arg else "N/A"

        print(f"[{i:02d}] Команда: {op:<12} | Bytes: {opcode_hex} | IR аргумент: {arg_value}")


# --- Встроенные тесты по спецификации ---

def test_asm_functions():
    """Проверяет, что функции ассемблирования генерируют байты точно как в задании."""
    try:
        # Загрузка константы (A=14, B=381):
        assert list(asm_load_const(381)) == [0x8E, 0xBE, 0x00, 0x00, 0x00], "Test load_const failed"
        # Чтение значения из памяти (A=11, B=435):
        assert list(asm_read_value(435)) == [0x8B, 0xD9, 0x00, 0x00, 0x00], "Test read_value failed"
        # Запись значения в память (A=94, B=308):
        assert list(asm_write_value(308)) == [0x5E, 0x9A, 0x00, 0x00, 0x00], "Test write_value failed"
        # Бинарная операция "<" (A=69, B=989):
        assert list(asm_less(989)) == [0xC5, 0xEE, 0x01, 0x00, 0x00], "Test less failed"

        print("[INFO] Встроенные тесты asm_функций пройдены успешно.")
    except AssertionError as e:
        print(f"[ERROR] Тест не пройден: {e}")
        sys.exit(1)


if __name__ == "__main__":
    test_asm_functions()
