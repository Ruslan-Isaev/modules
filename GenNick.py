"""gennick module for hikka userbot
    Copyright (C) 2025 Ruslan Isaev
    
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see https://www.gnu.org/licenses/."""

# meta developer: @RUIS_VlP
# при поддержке @hikka_mods

__version__ = (1, 0, 0)

from .. import loader, utils
import random
import string
from typing import List, Optional, Literal
import re

class NicknameGenerator:
    """Генератор произносимых и стильных никнеймов."""
    
    DEFAULT_SYLLABLES = [
        'ka', 'shi', 'mi', 'zo', 'ren', 'ti', 'ne', 'su', 'vo', 'dai',
        'xan', 'ri', 'fu', 'pu', 'ko', 'me', 'el', 'tra', 'qua', 'gen',
        'lor', 'vik', 'nyx', 'zel', 'thor', 'syn', 'try', 'pho', 'lux', 'ry',
        'kor', 'vex', 'ji', 'al', 'bis', 'war', 'tex', 'yon', 'ga', 'dra',
        'fi', 'na', 'to', 'va', 'qu', 'ex', 'ja', 'ki', 'lu', 'ma'
    ]
    
    SPECIAL_CHARS = ['_', '-', '.', '!', '~']
    
    def __init__(self):
        self.syllables = self.DEFAULT_SYLLABLES.copy()
    
    def generate(
        self,
        length: int = 8,
        *,
        phonemic_alternation: bool = True,
        add_number: bool = False,
        add_special_char: bool = False,
        syllables: Optional[List[str]] = None,
        capital_style: Literal['first', 'all', 'random', 'camel'] = 'first',
        min_syllable_length: int = 1,
        max_syllable_length: int = 3
    ) -> str:
        """
        Генерирует произносимый никнейм с заданными параметрами.
        
        Параметры:
            length: Длина никнейма
            phonemic_alternation: Чередовать гласные/согласные для лучшей произносимости
            add_number: Добавить случайное число в конец
            add_special_char: Добавить специальный символ
            syllables: Кастомный список слогов
            capital_style: Стиль капитализации
            min_syllable_length: Минимальная длина слога
            max_syllable_length: Максимальная длина слога
        """
        # Инициализация слогов
        syllables = syllables or self.syllables
        syllables = [s for s in syllables if min_syllable_length <= len(s) <= max_syllable_length]
        
        # Проверка параметров
        if not syllables:
            raise ValueError("Нет подходящих слогов для генерации")
        
        # Выделение места для дополнительных символов
        extra_length = 0
        if add_number:
            extra_length += random.randint(1, 2)
        if add_special_char:
            extra_length += 1
        
        if extra_length >= length:
            raise ValueError("Запрошенная длина слишком мала для добавления дополнительных символов")
        
        nickname = []
        remaining = length - extra_length
        last_type = None
        
        # Генерация основной части
        while remaining > 0:
            # Фильтрация слогов по длине
            possible = [s for s in syllables if len(s) <= remaining]
            
            # Фильтрация по фонетическому чередованию
            if phonemic_alternation and last_type is not None and len(possible) > 1:
                possible = self._filter_by_phonetics(possible, last_type)
            
            if not possible:
                # Если нет подходящих слогов, добавляем случайную букву
                char = random.choice(string.ascii_lowercase)
                nickname.append(char)
                remaining -= 1
                last_type = self._get_char_type(char)
                continue
            
            syllable = random.choice(possible)
            nickname.append(syllable)
            remaining -= len(syllable)
            last_type = self._get_char_type(syllable[0])
        
        # Добавление дополнительных символов
        if add_number:
            num_length = min(2, length - len(''.join(nickname)))
            if num_length > 0:
                min_num = 10 ** (num_length - 1)
                max_num = (10 ** num_length) - 1
                nickname.append(str(random.randint(min_num, max_num)))
        
        if add_special_char:
            special_char = random.choice(self.SPECIAL_CHARS)
            insert_pos = random.choice([len(nickname) - 1,  # Перед числом
                random.randint(1, len(nickname) - 1),  # В середине
                0  # В начале
            ])
            nickname.insert(insert_pos, special_char)
        
        # Сборка финальной строки
        nickname_str = ''.join(nickname)[:length]
        
        # Применение стиля капитализации
        nickname_str = self._apply_capital_style(nickname_str, capital_style)
        
        return nickname_str
    
    def _filter_by_phonetics(self, syllables: List[str], last_type: str) -> List[str]:
        """Фильтрует слоги по фонетическому чередованию."""
        filtered = []
        for s in syllables:
            first_char = s[0].lower()
            current_type = self._get_char_type(first_char)
            if last_type != current_type:
                filtered.append(s)
        return filtered or syllables
    
    @staticmethod
    def _get_char_type(char: str) -> str:
        """Определяет тип символа (гласный/согласный)."""
        vowels = {'a', 'e', 'i', 'o', 'u', 'y'}
        return 'vowel' if char.lower() in vowels else 'consonant'
    
    @staticmethod
    def _apply_capital_style(nickname: str, style: str) -> str:
        """Применяет выбранный стиль капитализации."""
        if style == 'first':
            return nickname.capitalize()
        elif style == 'all':
            return nickname.upper()
        elif style == 'random':
            return ''.join(random.choice([c.upper(), c.lower()]) for c in nickname)
        elif style == 'camel':
            parts = []
            for i, part in enumerate(re.split('([^a-zA-Z0-9]+)', nickname)):
                if i % 2 == 0 and part:
                    parts.append(part.capitalize())
                else:
                    parts.append(part)
            return ''.join(parts)
        return nickname

@loader.tds
class GenNickMod(loader.Module):
    """Простой генератор ников"""

    strings = {
        "name": "GenNick",
    }

    @loader.command()
    async def GenNick(self, message):
        """Генерирует стандартный ник"""
        generator = NicknameGenerator()
        await utils.answer(message, f"<b>Ваш новый ник</b>: <code>{generator.generate()}</code>")    
        
    @loader.command()
    async def GenIntNick(self, message):
        """Генерирует ник с цифрами"""
        generator = NicknameGenerator()
        await utils.answer(message, f"<b>Ваш новый ник</b>: <code>{generator.generate(add_number=True)}</code>")    