import random
from telethon import functions
from telethon.tl.types import Message
from .. import loader, utils

def replace_text(input_text):
    # Задаем соответствия для замен
    upper_mapping = {
        'Q': 'ᵠ', 'W': 'ᵂ', 'E': 'ᴱ', 'R': 'ᴿ', 'T': 'ᵀ', 
        'Y': 'ʸ', 'U': 'ᵁ', 'I': 'ᴵ', 'O': 'ᴼ', 'P': 'ᴾ', 
        'A': 'ᴬ', 'S': 'ˢ', 'D': 'ᴰ', 'F': 'ᶠ', 'G': 'ᴳ',
        'H': 'ᴴ', 'J': 'ᴶ', 'K': 'ᴷ', 'L': 'ᴸ', 'Z': 'ᶻ',
        'X': 'ˣ', 'C': 'ᶜ', 'V': 'ⱽ', 'B': 'ᴮ', 'N': 'ᴺ', 
        'M': 'ᴹ'
    }
    
    lower_mapping = {
        'q': 'ᵠ', 'w': 'ʷ', 'e': 'ᵉ', 'r': 'ʳ', 't': 'ᵗ',
        'y': 'ʸ', 'u': 'ᵘ', 'i': 'ᶦ', 'o': 'ᵒ', 'p': 'ᵖ',
        'a': 'ᵃ', 's': 'ˢ', 'd': 'ᵈ', 'f': 'ᶠ', 'g': 'ᵍ',
        'h': 'ʰ', 'j': 'ʲ', 'k': 'ᵏ', 'l': 'ˡ', 'z': 'ᶻ',
        'x': 'ˣ', 'c': 'ᶜ', 'v': 'ᵛ', 'b': 'ᵇ', 'n': 'ⁿ',
        'm': 'ᵐ'
    }
    
    digit_mapping = {
        '0': '⁰', 
        '1': '¹', 
        '2': '²', 
        '3': '³',
        '4': '⁴',
        '5': '⁵',
        '6': '⁶',
        '7': '⁷',
        '8': '⁸',
        '9': '⁹'
    }
    
    special_mapping = {
        '+': '⁺',
        '=': '⁼',
        '!': 'ᵎ',
        '(' :  '⁽',
        ')' :  '⁾',
        '-' :  '⁻',
        ' ' : ' '
    }

    # Инициализируем переменную для результата
    result = ""

    # Проходим по каждому символу входного текста
    for char in input_text:
        if char in upper_mapping:
            result += upper_mapping[char]
        elif char in lower_mapping:
            result += lower_mapping[char]
        elif char in digit_mapping:
            result += digit_mapping[char]
        elif char in special_mapping:
            result += special_mapping[char]
    
    # Проверяем, не пустой ли результат
    if not result:
        return "Ошибка!"
    
    return result

@loader.tds
class НадстрочкаMod(loader.Module):
    """Делает надстрочный текст"""

    strings = {
        "name": "Надстрочка",
    }

    def init(self):
        self.name = self.strings["name"]

    @loader.command()
    async def upcmd(self, message: Message):
        """<text> - сделать верхний шрифт"""
        mt = message.text[4:]
        mt = replace_text(mt)
        await utils.answer(message, f"<code>{mt}</code>")