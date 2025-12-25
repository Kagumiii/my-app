from PIL import Image
from colorthief import ColorThief
import colorsys


def get_dominant_color(image_path):
    """Получить доминирующий цвет из изображения"""
    try:
        color_thief = ColorThief(image_path)
        dominant_color = color_thief.get_color(quality=1)
        return dominant_color
    except Exception as e:
        print(f"Ошибка при извлечении цвета: {e}")
        return (59, 130, 246)  # синий по умолчанию (#3b82f6)


def rgb_to_hex(rgb):
    """Конвертировать RGB в HEX"""
    return '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])


def get_color_scheme(rgb):
    """Сгенерировать цветовую схему на основе основного цвета"""
    r, g, b = [x / 255.0 for x in rgb]
    h, l, s = colorsys.rgb_to_hls(r, g, b)

    # Более темный вариант
    dark_rgb = colorsys.hls_to_rgb(h, max(0.1, l * 0.4), s)
    dark_color = tuple(int(x * 255) for x in dark_rgb)

    # Более светлый вариант
    light_rgb = colorsys.hls_to_rgb(h, min(0.95, l * 1.6), max(0.3, s * 0.7))
    light_color = tuple(int(x * 255) for x in light_rgb)

    # Акцентный цвет (комплиментарный)
    h_complement = (h + 0.5) % 1.0
    accent_rgb = colorsys.hls_to_rgb(h_complement, l, s)
    accent_color = tuple(int(x * 255) for x in accent_rgb)

    return {
        'primary': rgb,
        'primary_hex': rgb_to_hex(rgb),
        'dark': dark_color,
        'dark_hex': rgb_to_hex(dark_color),
        'light': light_color,
        'light_hex': rgb_to_hex(light_color),
        'accent': accent_color,
        'accent_hex': rgb_to_hex(accent_color)
    }