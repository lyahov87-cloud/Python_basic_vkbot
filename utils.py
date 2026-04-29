from vk_api.keyboard import VkKeyboard, VkKeyboardColor

def create_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('🎲 Случайный фильм', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('🔎 Поиск', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('🔝 ТОП-10 по годам', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('/history', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('/help', color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()

def create_year_keyboard():
    keyboard = VkKeyboard(one_time=True)
    for year in ['2024', '2023', '2022']:
        keyboard.add_button(year, color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('2021', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('2020', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Назад', color=VkKeyboardColor.SECONDARY)
    return keyboard.get_keyboard()
