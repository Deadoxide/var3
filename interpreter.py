# interpreter.py
import argparse
from pathlib import Path
import sys

from uvm_memory import UVMMemory, OPCODE_NAMES, dump_memory_to_xml


def decode_instruction(instruction_bytes: bytes):
    """
    Декодирует 5 байт в (cmd_name, B).

    Формат:
        value = int.from_bytes(5 байт, 'little')
        A = value & 0x7F
        B = value >> 7
    """
    if len(instruction_bytes) != 5:
        raise ValueError(f"Ожидалось 5 байт инструкции, получено {len(instruction_bytes)}")

    value = int.from_bytes(instruction_bytes, byteorder="little")
    a = value & 0x7F
    b = value >> 7

    cmd_name = OPCODE_NAMES.get(a)
    if cmd_name is None:
        raise ValueError(f"Неизвестный opcode (поле A): {a}")
    return cmd_name, b


def run_program(bytecode: bytes, memory: UVMMemory) -> str:
    """
    Реализует основной цикл интерпретатора.
    Возвращает лог выполнения в виде строки.

    Команды:
      - load_const (A=14, B=константа):
          ACC = B
      - read_value (A=11, B=адрес):
          ACC = MEM[B]
      - write_value (A=94, B=адрес):
          MEM[B] = ACC
      - less (A=69, B=адрес):
          lhs = MEM[B]
          rhs = ACC
          MEM[B] = 1 если lhs < rhs, иначе 0
    """

    # Разбиваем байт-код по 5 байт
    instructions = [bytecode[i:i + 5] for i in range(0, len(bytecode), 5)]
    log_messages = []

    log_messages.append(f"[INFO] Запуск программы. Всего инструкций: {len(instructions)}")

    while memory.ip < len(instructions):
        instruction_bytes = instructions[memory.ip]
        current_ip = memory.ip

        try:
            cmd, operand = decode_instruction(instruction_bytes)
        except Exception as e:
            log_messages.append(f"[RUNTIME ERROR] На адресе {memory.ip}: {e}")
            break

        log_messages.append(
            f"[{current_ip:03d}] Выполняется: {cmd:<12} | B (операнд): {operand} | ACC={memory.acc}"
        )

        new_ip = current_ip + 1

        # --- ВЫПОЛНЕНИЕ КОМАНД ---

        if cmd == "load_const":
            memory.acc = operand

        elif cmd == "read_value":
            value = memory.read_data(operand)
            memory.acc = value

        elif cmd == "write_value":
            memory.write_data(operand, memory.acc)

        elif cmd == "less":
            lhs = memory.read_data(operand)
            rhs = memory.acc
            result = 1 if lhs < rhs else 0
            memory.write_data(operand, result)

        else:
            log_messages.append(f"[RUNTIME ERROR] Неизвестная команда: {cmd}")
            break

        memory.ip = new_ip

    log_messages.append(f"\n--- Выполнение программы завершено на IP={memory.ip} ---")
    log_messages.append(f"Финальный ACC: {memory.acc}")
    log_messages.append(f"Память (первые 16 ячеек): {memory.data[:16]}")

    return "\n".join(log_messages)


# --- CLI-оболочка (для запуска из консоли) ---

def parse_args():
    """Обрабатывает аргументы командной строки."""
    parser = argparse.ArgumentParser(description="UVM Interpreter (Emulator)")
    parser.add_argument("program", help="Путь к бинарному файлу с ассемблированной программой.")
    parser.add_argument("dump_file", help="Путь к файлу-результату для дампа памяти (XML).")
    parser.add_argument(
        "dump_range",
        help="Диапазон адресов памяти для дампа (например, 0:10).",
        type=str
    )
    return parser.parse_args()


def main():
    try:
        args = parse_args()
        program_path = Path(args.program)
        dump_file = args.dump_file

        # Парсинг диапазона дампа
        if ":" not in args.dump_range:
            raise ValueError("Диапазон дампа должен быть в формате START:END.")
        start_str, end_str = args.dump_range.split(":")
        start_addr = int(start_str)
        end_addr = int(end_str)

        with open(program_path, "rb") as f:
            bytecode = f.read()

        memory = UVMMemory()

        # Запуск и вывод лога в консоль
        log = run_program(bytecode, memory)
        print(log)

        # Дамп памяти после выполнения
        dump_memory_to_xml(memory, start_addr, end_addr, dump_file)

    except FileNotFoundError:
        print(f"[ERROR] Файл программы не найден: {args.program}")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Произошла ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Для GUI/WEB основной вход через core_runner / index.html
    pass
