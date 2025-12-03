# core_runner.py

"""
Общая точка входа для запуска УВМ из GUI (tkinter) или других оболочек.
"""

from typing import Tuple

from uvm_asm import full_asm
from uvm_memory import UVMMemory, dump_memory_to_xml_str
from interpreter import run_program


def assemble_source(source: str) -> Tuple[bytes, list]:
    """Ассемблирует текст программы в (bytecode, IR)."""
    bytecode, IR = full_asm(source)
    return bytecode, IR


def run_uvm_source(source: str) -> str:
    """
    Принимает текст программы на ассемблере,
    ассемблирует, запускает интерпретатор и возвращает
    строку с:
      - сгенерированным байт-кодом (в hex),
      - логом выполнения,
      - дампом памяти (XML, адреса 0..31).
    """

    source = source.strip()
    if not source:
        return "[WARN] Исходный текст пуст — нечего выполнять."

    # 1. Ассемблирование
    try:
        bytecode, IR = assemble_source(source)
    except Exception as e:
        return f"[ASM ERROR] {type(e).__name__}: {e}"

    # Строка с байтами в 16-ричном виде
    hex_bytes = " ".join(f"0x{b:02X}" for b in bytecode)

    # 2. Память
    memory = UVMMemory()

    # 3. Запуск интерпретатора
    try:
        log_text = run_program(bytecode, memory)
    except Exception as e:
        log_text = f"[RUNTIME ERROR] {type(e).__name__}: {e}"

    # 4. Дамп памяти (первые 32 ячейки)
    try:
        xml_dump = dump_memory_to_xml_str(memory, 0, 31)
    except Exception as e:
        xml_dump = f"[DUMP ERROR] {type(e).__name__}: {e}"

    # 5. Собираем всё вместе
    parts = []
    parts.append("--- Сгенерированный байт-код ---")
    parts.append(hex_bytes)
    parts.append("\n--- Лог выполнения ---")
    parts.append(log_text)
    parts.append("\n--- Дамп памяти (XML, адреса 0..31) ---")
    parts.append(xml_dump)

    return "\n".join(parts)
