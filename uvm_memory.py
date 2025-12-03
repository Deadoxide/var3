# uvm_memory.py
import xml.etree.ElementTree as ET
import io

# --- Opcode-to-Name Mapping (по полю A) ---
OPCODE_NAMES = {
    14: "load_const",   # A=14
    11: "read_value",   # A=11
    94: "write_value",  # A=94
    69: "less",         # A=69
}


class UVMMemory:
    """Модель памяти, регистра-аккумулятора и IP для УВМ."""

    def __init__(self, data_size=2048):
        self.data = [0] * data_size
        self.stack = []       # оставляем на будущее
        self.ip = 0           # instruction pointer
        self.acc = 0          # регистр-аккумулятор

    def push(self, value):
        self.stack.append(value)

    def pop(self):
        if not self.stack:
            raise IndexError("Стек пуст при выполнении POP.")
        return self.stack.pop()

    def read_data(self, address: int) -> int:
        """Чтение из памяти данных."""
        if 0 <= address < len(self.data):
            return self.data[address]
        raise IndexError(f"Недопустимый адрес для чтения: {address}")

    def write_data(self, address: int, value: int):
        """Запись в память данных."""
        if 0 <= address < len(self.data):
            self.data[address] = value
        else:
            raise IndexError(f"Недопустимый адрес для записи: {address}")


def dump_memory_to_xml_str(memory: UVMMemory, start_addr: int, end_addr: int) -> str:
    """Генерирует дамп памяти в XML формате и возвращает его как строку (для GUI/CLI)."""

    root = ET.Element("memory_dump")

    # 1. Стек
    stack_elem = ET.SubElement(root, "stack")
    stack_elem.text = ", ".join(map(str, memory.stack))

    # 2. Регистры (IP, ACC)
    regs_elem = ET.SubElement(root, "registers")
    ET.SubElement(regs_elem, "ip").text = str(memory.ip)
    ET.SubElement(regs_elem, "acc").text = str(memory.acc)

    # 3. Память данных
    data_elem = ET.SubElement(root, "data_memory")
    start = max(0, start_addr)
    end = min(end_addr + 1, len(memory.data))

    for addr in range(start, end):
        cell = ET.SubElement(data_elem, "cell", address=str(addr))
        cell.text = str(memory.data[addr])

    # Создание XML-строки
    tree = ET.ElementTree(root)
    xml_buffer = io.BytesIO()
    tree.write(xml_buffer, encoding="utf-8", xml_declaration=True)
    return xml_buffer.getvalue().decode("utf-8")


def dump_memory_to_xml(memory: UVMMemory, start_addr: int, end_addr: int, filename: str):
    """Сохраняет дамп памяти в XML формате в файл."""
    xml_str = dump_memory_to_xml_str(memory, start_addr, end_addr)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(xml_str)
    print(f"\n[INFO] Дамп памяти сохранен в файл: {filename}")
