from aiogram import F, Router
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from generate import ai_generate
from tasks import task_manager
import logging
from typing import List, Dict, Set, Optional
from aiogram.types import WebAppInfo
import urllib.parse
from pathlib import Path
import json

router = Router()



### State is a process in which the user currently is ###
class Gen(StatesGroup):                                                    
    main_menu = State()
    quantity = State()
    elements = State()
    task_type = State()
    task_subtype = State()
    selecting_options = State()
    patterns = State()
    polynomials = State()
    degrees = State()
    logarithms = State()
    trigonometry = State()
    templates = State()
    adding_template = State()



### Class for multiple choice in menu ###
class MultiSelect:                                                         
    def __init__(self):
        self.selected_options = set()
        self.all_options = []
        self.current_category = ""
    
    def reset(self, category: str, options: List[str]):
        self.selected_options = set()
        self.all_options = options
        self.current_category = category
    
    def toggle_option(self, option_idx: int) -> bool:
        option = self.all_options[option_idx]
        if option in self.selected_options:
            self.selected_options.remove(option)
            return False
        else:
            self.selected_options.add(option)
            return True
    
    def get_selected(self) -> List[str]:
        if not self.selected_options:
            return ["Не применять"]
        return list(self.selected_options)

multi_select = MultiSelect()


### Class of variety of keyboards ###
class Keyboards:
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text="Сгенерировать задачи", callback_data="generate_tasks"),
                InlineKeyboardButton(text="Добавить шаблон", callback_data="add_template")
            ]]
        )
    
    @staticmethod
    def single_select_menu(options: List[str], prefix: str = "", selected_idx: int = -1) -> InlineKeyboardMarkup:
        buttons = []
        for i, option in enumerate(options):
            prefix_symbol = "✅ " if i == selected_idx else "☑️ "
            buttons.append([
                InlineKeyboardButton(
                    text=f"{prefix_symbol}{option}",
                    callback_data=f"{prefix}_{i}"
                )
            ])
        return InlineKeyboardMarkup(inline_keyboard=buttons)
    
    @staticmethod
    def multi_select_menu(category: str, options: List[str], selected: Set[str]) -> InlineKeyboardMarkup:
        buttons = []
        for i, option in enumerate(options):
            prefix = "✅ " if option in selected else "☑️ "
            buttons.append([
                InlineKeyboardButton(
                    text=f"{prefix}{option}",
                    callback_data=f"multi_{category}_{i}"
                )
            ])
        buttons.append([
            InlineKeyboardButton(text="🚀 Готово", callback_data=f"multi_done_{category}")
        ])
        return InlineKeyboardMarkup(inline_keyboard=buttons)



### Class for prompt creation and getting answers: "raw", "formatted", and "polished" ###
class TaskGenerator:
    @staticmethod
    def _load_pool_of_examples() -> str:
        try:
            with open(Path(__file__).parent / 'pool_of_examples.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return "\n".join([line for line in data.get("Pool", []) if line.strip()])
        except (FileNotFoundError, json.JSONDecodeError):
            return ""
    
    @staticmethod
    def build_raw_prompt(data: Dict) -> str:
        examples = ""
        if data.get('task_type') and data.get('task_subtype'):
            examples = "\n".join(task_manager.get_examples(data['task_type'], data['task_subtype']))
        
        pool_of_examples = TaskGenerator._load_pool_of_examples()

        prompt = f"""
Ты вариатор РАЗЛИЧНЫХ ПО СТРУКТУРЕ И ЛОГИКЕ задач по математике для очень умных школьников (ЗАДАЧИ ДОЛЖНЫ БЫТЬ СЛОЖНЫМИ). 
ИСПОЛЬЗУЙ КРЕАТИВНЫЕ ИДЕИ ПРИ ГЕНЕРАЦИИ ЗАДАЧ.
Сгенерируй {data['quantity']} РАЗЛИЧНЫХ по СТРУКТУРЕ математических задач по следующим параметрам:
- Элементы: {data['elements']}
- Тип задачи: {data['task_type']} ({data.get('task_subtype', 'без подтипа')}
- Узоры: {', '.join(data.get('patterns', ['Не применять']))}
- Многочлены: {', '.join(data.get('polynomials', ['Не применять']))}
- Свойства степеней: {', '.join(data.get('degrees', ['Не применять']))}
- Свойства логарифмов: {', '.join(data.get('logarithms', ['Не применять']))}
- Свойства тригонометрии: {', '.join(data.get('trigonometry', ['Не применять']))}
- Шаблоны: {', '.join(data.get('templates', ['Не применять']))}

("Не применять" - значит учитель просто не выбрал данный вариант. Это не значит, что свойства/типы/узоры нельзя использовать)

Твоя основная задача ВКЛЮЧИТЬ КРЕАТИВ И СОЗДАТЬ ОЧЕНЬ ИНТЕРЕСНЫЕ ЗАДАЧИ, КАЖДАЯ ОТЛИЧАЮЩАЯ ОТ ДРУГИХ.
ИСПОЛЬЗУЙ КРЕАТИВНЫЕ ИДЕИ НАПИСАНИЯ УСЛОВИЙ ЗАДАЧ

Примеры для вдохновения:
{examples}.

Не нужно повторяться с этими примерами, нужно создавать всегда УНИКАЛЬНЫЕ И РАЗЛИЧНЫЕ задачи, опираясь также на введённые учителем параметры.
Убедись, что задачи РАЗЛИЧНЫЕ по структуре и логике. 
Для создания различных задач используй разного вида числитель и знаменатель дробей, разные степени у переменных,
разное расположение членов, перемножай, склоадывай, дели, вычитай, приводи не к лёгкому виду, а к СЛОЖНОМУ ВИДУ ПРИВОДИ

Строгий формат вывода:
i) <условие>
<ответ>
i) <условие>
<ответ>
...

Тебе нужно проверить сгенерированные задачи на корректность и если что подкорректировать.
Если обнаружится, что ответ неправильный, то подкорректируй условие и ответ.
Затем перепроверь условие и ответ и если что исправь.


Не нужно повторяться с этими примерами, нужно создавать всегда УНИКАЛЬНЫЕ задачи, опираясь ещё на введённые учителем параметры 

По итогу должен быть сгенерирован ТОЛЬКО СПИСОК ИЗ ПАР ДВУХ СТРОК: 
"i)МАТЕМАТИЧЕСКОЕ ВЫРАЖЕНИЕ
ОТВЕТ" 

Было так:
1)
\((x^5 - 3x^4 + 2x^3 - 6x^2 + x - 3)/(x^3 - 3x^2 + x - 3)\)  
\(x^2 + 1\)

Должно стать так:
1) \((x^5 - 3x^4 + 2x^3 - 6x^2 + x - 3)/(x^3 - 3x^2 + x - 3)\)  
\(x^2 + 1\)

БЕЗ ЛИШНИХ ПЕРЕВОДОВ СТРОКИ!!!
ЗАПРЕЩАЕТСЯ использование знаков доллара $ и $$!!!
НЕ ПИСАТЬ НИКАКИХ СЛОВ И ПОЯСНЯЮЩИХ РЕШЕНИЙ!!!

'\' - означает создание дроби (3/4), а ':' - это деление, удобное для деления рациональных числед с запятой (0,1 : 2345,99).

Перед генерацией задач просмотри идеи для оформления задач из пула задач ниже.
ПРОСМОТРИ ВСЕ ЗАДАЧИ ПЕРЕД ГЕНЕРАЦИЕЙ СВОИХ:
{pool_of_examples}
"""
        return prompt

    @staticmethod
    def build_format_prompt(raw_tasks: str, data: Dict) -> str:
        examples = ""
        if data.get('task_type') and data.get('task_subtype'):
            examples = "\n".join(task_manager.get_examples(data['task_type'], data['task_subtype']))

        pool_of_examples = TaskGenerator._load_pool_of_examples()

        return f"""
Ты вариатор РАЗЛИЧНЫХ ПО СТРУКТУРЕ И ЛОГИКЕ задач по математике для очень умных школьников (ЗАДАЧИ ДОЛЖНЫ БЫТЬ СЛОЖНЫМИ).

Были сгенерированы следующие задачи, которые должны пройти проверку на то, что ВСЕ ОНИ 1) РАЗЛИЧНЫЕ ПО СТРУКТУРЕ И ЛОГИКЕ, 
2) НЕТ ОДНОТИПНЫХ ЗАДАЧ,
3) КОРРЕКТНЫЕ (Ответ удовлетворяет полностью условию)
4) Должны быть отформатированы по требованиям ниже:
{raw_tasks}

Требования:
Учитель задал следующие параметры:
- Элементы: {data['elements']}
- Тип задачи: {data['task_type']} ({data.get('task_subtype', 'без подтипа')}
- Узоры: {', '.join(data.get('patterns', ['Не применять']))}
- Многочлены: {', '.join(data.get('polynomials', ['Не применять']))}
- Свойства степеней: {', '.join(data.get('degrees', ['Не применять']))}
- Свойства логарифмов: {', '.join(data.get('logarithms', ['Не применять']))}
- Свойства тригонометрии: {', '.join(data.get('trigonometry', ['Не применять']))}
- Шаблоны: {', '.join(data.get('templates', ['Не применять']))}
("Не применять" - значит учитель просто не выбрал данный вариант. Это не значит, что свойства/типы/узоры нельзя использовать)
1. Пронумеруй задачи (1), 2), ...)
2. Формат строго:
    i) <условие>
    <ответ>
3. ИСПОЛЬЗУЙ Katex!!!
4. Учти параметры:
- Тип: {data['task_type']} ({data.get('task_subtype', '')})
- Узоры: {', '.join(data.get('patterns', []))}
- Многочлены: {', '.join(data.get('polynomials', []))}
5. Оставь только {data['quantity']} задач
6. Убедись, что задачи РАЗЛИЧНЫЕ по структуре и логике. 
Для создания различных задач используй разного вида числитель и знаменатель дробей, разные степени у переменных,
разное расположение членов, перемножай, склоадывай, дели, вычитай, приводи не к лёгкому виду, а к СЛОЖНОМУ ВИДУ ПРИВОДИ

Твоя основная задача ВКЛЮЧИТЬ КРЕАТИВ И СОЗДАТЬ ОЧЕНЬ ИНТЕРЕСНЫЕ ЗАДАЧИ, КАЖДАЯ ОТЛИЧАЮЩАЯ ОТ ОСТАЛЬНЫХ.
ИСПОЛЬЗУЙ КРЕАТИВНЫЕ ИДЕИ НАПИСАНИЯ УСЛОВИЙ ЗАДАЧ!

Тебе нужно проверить сгенерированные задачи на корректность и если что подкорректировать.
Если обнаружится, что ответ неправильный, то подкорректируй условие и ответ.
Затем перепроверь условие и ответ и если что исправь.

При генерации примеров генератор вдохновлялся следующими примерами {examples}.
Не нужно повторяться с этими примерами, нужно создавать всегда УНИКАЛЬНЫЕ задачи, опираясь ещё на введённые учителем параметры 
Перепроверь условие и ответ

По итогу должен быть сгенерирован ТОЛЬКО СПИСОК ИЗ ПАР ДВУХ СТРОК: 
"i)МАТЕМАТИЧЕСКОЕ ВЫРАЖЕНИЕ
ОТВЕТ" 

Было так:
1)
\((x^5 - 3x^4 + 2x^3 - 6x^2 + x - 3)/(x^3 - 3x^2 + x - 3)\)  
\(x^2 + 1\)

Должно стать так:
1) \((x^5 - 3x^4 + 2x^3 - 6x^2 + x - 3)/(x^3 - 3x^2 + x - 3)\)  
\(x^2 + 1\)

ЗАПРЕЩАЕТСЯ ПИСАТЬ СЛОВА, ТОЛЬКО МАТЕМАТИЧЕСКИЕ ФОРМУЛЫ!!!

'\' - означает создание дроби (3/4), а ':' - это деление, удобное для деления рациональных числед с запятой (0,1 : 2345,99).

БЕЗ ЛИШНИХ ПЕРЕВОДОВ СТРОКИ!!!
ЗАПРЕЩАЕТСЯ использование знаков доллара $ и $$!!!

ПРОСМОТРИ ВСЕ ЗАДАЧИ ПЕРЕД ГЕНЕРАЦИЕЙ СВОИХ:
{pool_of_examples}

НЕ ПИСАТЬ НИКАКИХ СЛОВ И ПОЯСНЯЮЩИХ РЕШЕНИЙ!!!
Строгий формат вывода:
i) <условие>
<ответ>
i) <условие>
<ответ>
...
"""

    @staticmethod
    def build_polish_prompt(formatted_tasks: str, data: Dict) -> str:
        examples = ""
        if data.get('task_type') and data.get('task_subtype'):
            examples = "\n".join(task_manager.get_examples(data['task_type'], data['task_subtype']))
        return f"""Тщательно проверь и отшлифуй задачи:
{formatted_tasks}

Требования:
Учитель задал следующие параметры:
- Элементы: {data['elements']}
- Тип задачи: {data['task_type']} ({data.get('task_subtype', 'без подтипа')}
- Узоры: {', '.join(data.get('patterns', ['Не применять']))}
- Многочлены: {', '.join(data.get('polynomials', ['Не применять']))}
- Свойства степеней: {', '.join(data.get('degrees', ['Не применять']))}
- Свойства логарифмов: {', '.join(data.get('logarithms', ['Не применять']))}
- Свойства тригонометрии: {', '.join(data.get('trigonometry', ['Не применять']))}
- Шаблоны: {', '.join(data.get('templates', ['Не применять']))}
("Не применять" - значит учитель просто не выбрал данный вариант. Это не значит, что свойства/типы/узоры нельзя использовать)
1. Пронумеруй задачи (1), 2), ...)
2. Формат строго:
    i) <условие>
    <ответ>
3. ИСПОЛЬЗУЙ Katex!!!
4. Учти параметры:
- Тип: {data['task_type']} ({data.get('task_subtype', '')})
- Узоры: {', '.join(data.get('patterns', []))}
- Многочлены: {', '.join(data.get('polynomials', []))}
5. Оставь только {data['quantity']} задач
6. Убедись, что задачи РАЗЛИЧНЫЕ по структуре и логике. 
Для создания различных задач используй разного вида числитель и знаменатель дробей, разные степени у переменных,
разное расположение членов, перемножай, склоадывай, дели, вычитай, приводи не к лёгкому виду, а к СЛОЖНОМУ ВИДУ ПРИВОДИ

Тебе нужно проверить сгенерированные задачи на корректность и если что подкорректировать.
Если обнаружится, что ответ неправильный, то подкорректируй условие и ответ.
Затем перепроверь условие и ответ и если что исправь.

При генерации примеров генератор вдохновлялся следующими примерами {examples}.
Не нужно повторяться с этими примерами, нужно создавать всегда УНИКАЛЬНЫЕ задачи, опираясь ещё на введённые учителем параметры 
Перепроверь условие и ответ

Не расписывай условие, то есть в Условии модет быть среди операций: сумма, разность, произведение, частное! Без "равно" (=).
После номера Условия ( i) ) БЕЗ ПЕРЕВОДА СТРОКИ сразу продолдается Условие!!!! Только затем следует перевод строки и ответ!!!
Было так:
1)
\((x^5 - 3x^4 + 2x^3 - 6x^2 + x - 3)/(x^3 - 3x^2 + x - 3)\)  
\(x^2 + 1\)

Должно стать так:
1) \((x^5 - 3x^4 + 2x^3 - 6x^2 + x - 3)/(x^3 - 3x^2 + x - 3)\)  
\(x^2 + 1\)

БЕЗ ЛИШНИХ ПЕРЕВОДОВ СТРОКИ!!!
ЗАПРЕЩАЕТСЯ использование знаков доллара $ и $$!!!

НЕ ПИСАТЬ НИКАКИХ СЛОВ И ПОЯСНЯЮЩИХ РЕШЕНИЙ!!!
СТРОГИЙ ФОРМАТ ВЫВОДА:
i) <условие>
<ответ>
i) <условие>
<ответ>
...
'\' - означает создание дроби (3/4), а ':' - это деление, удобное для деления рациональных числед с запятой (0,1 : 2345,99).

ЗАПРЕЩАЕТСЯ ПИСАТЬ СЛОВА, ТОЛЬКО МАТЕМАТИЧЕСКИЕ ФОРМУЛЫ!!!

ПО ИТОГУ ДОЛЖЕН ПОЛУЧИТЬСЯ ТОЛЬКО СПИСОК ИЗ ЗАДАЧ С ОТВЕТОМ:
i) <условие>
<ответ>
i) <условие>
<ответ>
...
"""



### Greeting and main_menu output ###
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await message.answer("Добрый день! Я бот для генерации математических задач.")
    await show_main_menu(message, state)

async def show_main_menu(message: Message, state: FSMContext):
    await state.set_state(Gen.main_menu)
    await message.answer("Выберите действие:", reply_markup=Keyboards.main_menu())



### Getting chosen parameters
@router.callback_query(F.data == "generate_tasks")
async def start_generation_flow(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Сколько задач сгенерировать? (1 - 20)")
    await state.set_state(Gen.quantity)

@router.message(Gen.quantity)
async def handle_quantity(message: Message, state: FSMContext):
    if not message.text.isdigit() or not 1 <= int(message.text) <= 20:
        await message.answer("Введите число от 1 до 20")
        return
    
    await state.update_data(quantity=int(message.text))
    elements = task_manager.get_elements()
    await message.answer("Выберите элементы для задач:", 
                         reply_markup=Keyboards.single_select_menu(elements, "element"))
    await state.set_state(Gen.elements)

@router.callback_query(F.data.startswith("element_"), Gen.elements)
async def handle_elements(callback: CallbackQuery, state: FSMContext):
    element_idx = int(callback.data.split("_")[1])
    elements = task_manager.get_elements()
    
    await callback.message.edit_reply_markup(
        reply_markup=Keyboards.single_select_menu(elements, "element", element_idx)
    )
    
    await state.update_data(elements=elements[element_idx])
    types = list(task_manager.get_types().keys())
    await callback.message.answer("Выберите тип задачи:", 
                                 reply_markup=Keyboards.single_select_menu(types, "type"))
    await state.set_state(Gen.task_type)

@router.callback_query(F.data.startswith("type_"), Gen.task_type)
async def handle_task_type(callback: CallbackQuery, state: FSMContext):
    type_idx = int(callback.data.split("_")[1])
    types = list(task_manager.get_types().keys())
    
    await callback.message.edit_reply_markup(
        reply_markup=Keyboards.single_select_menu(types, "type", type_idx)
    )
    
    selected_type = types[type_idx]
    await state.update_data(task_type=selected_type)
    
    subtypes = task_manager.get_type_options(selected_type)
    if subtypes:
        await callback.message.answer("Выберите подтип задачи:", 
                                     reply_markup=Keyboards.single_select_menu(subtypes, "subtype"))
        await state.set_state(Gen.task_subtype)
    else:
        await start_multi_select(callback.message, state, "patterns")

@router.callback_query(F.data.startswith("subtype_"), Gen.task_subtype)
async def handle_task_subtype(callback: CallbackQuery, state: FSMContext):
    subtype_idx = int(callback.data.split("_")[1])
    data = await state.get_data()
    subtypes = task_manager.get_type_options(data['task_type'])
    
    await callback.message.edit_reply_markup(
        reply_markup=Keyboards.single_select_menu(subtypes, "subtype", subtype_idx)
    )
    
    selected_subtype = subtypes[subtype_idx]
    examples = "\n".join(task_manager.get_examples(data['task_type'], selected_subtype))
    await state.update_data(task_subtype=selected_subtype, examples=examples)
    await start_multi_select(callback.message, state, "patterns")

async def start_multi_select(message: Message, state: FSMContext, category: str):
    category_name = {
        "patterns": "Узоры",
        "polynomials": "Многочлены",
        "degrees": "Свойства степеней",
        "logarithms": "Свойства логарифмов",
        "trigonometry": "Свойства тригонометрии",
        "templates": "Шаблоны"
    }[category]
    
    options = task_manager.get_category(category_name)
    multi_select.reset(category, options)
    
    await message.answer(
        f"Выберите {category_name.lower()} (можно несколько):",
        reply_markup=Keyboards.multi_select_menu(category, options, multi_select.selected_options)
    )
    await state.set_state(Gen.selecting_options)

@router.callback_query(F.data.startswith("multi_"), Gen.selecting_options)
async def handle_multi_select(callback: CallbackQuery, state: FSMContext):
    data = callback.data.split("_")
    
    if data[1] == "done":
        category = data[2]
        selected = multi_select.get_selected()
        
        await state.update_data({category: selected})
        
        next_states = {
            "patterns": ("polynomials", "Многочлены"),
            "polynomials": ("degrees", "Свойства степеней"),
            "degrees": ("logarithms", "Свойства логарифмов"),
            "logarithms": ("trigonometry", "Свойства тригонометрии"),
            "trigonometry": ("templates", "Шаблоны"),
            "templates": (None, None)
        }
        
        next_category, next_category_name = next_states[category]
        
        if next_category:
            await start_multi_select(callback.message, state, next_category)
        else:
            await generate_and_send_tasks(callback.message, state)
    else:
        category = data[1]
        option_idx = int(data[2])
        is_selected = multi_select.toggle_option(option_idx)
        
        await callback.message.edit_reply_markup(
            reply_markup=Keyboards.multi_select_menu(
                category, 
                multi_select.all_options, 
                multi_select.selected_options
            )
        )



### Generation of tasks ###
async def generate_and_send_tasks(message: Message, state: FSMContext):
    data = await state.get_data()
    await message.answer("⌛ Генерирую задачи...")
    
    # 1. The first request is generation of "raw" tasks
    raw_prompt = TaskGenerator.build_raw_prompt(data)
    raw_response = await ai_generate(raw_prompt)
    
    if not raw_response:
        await message.answer("⚠ Ошибка при генерации задач (Error №1_AI)")
        await show_main_menu(message, state)
        return
    
    # 2. The second request is generation of "formatted" tasks
    format_prompt = TaskGenerator.build_format_prompt(raw_response, data)
    formatted_response = await ai_generate(format_prompt)
    
    if not formatted_response:
        await message.answer(f"📚 Сырые задачи:\n\n{raw_response}")
        return

    # 3. The third request is generation of "polished" tasks
    polished_response = await ai_generate(TaskGenerator.build_polish_prompt(formatted_response, data))
    final_response = polished_response or formatted_response
    
    encoded_tasks = urllib.parse.quote(final_response)
    web_app_button = InlineKeyboardButton(
        text="📖 Открыть",
        web_app=WebAppInfo(url=f"https://v0-new-project-bhtqs8yaaqd.vercel.app/?tasks={encoded_tasks}")
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[web_app_button]])
    
    await message.answer(
        "✅ Задачи готовы! Нажмите кнопку ниже для отображения:",
        reply_markup=keyboard
    )
    await message.answer(f"📚 Текстовый вариант (LaTeX):\n\n{final_response}")
    await show_main_menu(message, state)



### Adding a new template ###
@router.callback_query(F.data == "add_template")
async def start_adding_template(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите текст нового шаблона:")
    await state.set_state(Gen.adding_template)

@router.message(Gen.adding_template)
async def handle_new_template(message: Message, state: FSMContext):
    if task_manager.add_template(message.text):
        await message.answer("Шаблон успешно добавлен!")
    else:
        await message.answer("Ошибка при добавлении шаблона")
    await show_main_menu(message, state)
