import os
import qrcode
from PIL import Image, ImageDraw, ImageFont
from typing import List
from app.core.config import settings
from app.models.textbook import Textbook


def create_qr_codes_directory():
    """Создание директории для QR кодов если не существует"""
    os.makedirs(settings.QR_CODES_DIR, exist_ok=True)


def generate_qr_code(textbook: Textbook) -> str:
    """
    Генерация QR кода для учебника
    Возвращает путь к сохраненному файлу
    """
    # Создаем данные для QR кода
    qr_data = f"ID:{textbook.id}|SUBJ:{textbook.subject}|TITLE:{textbook.title}|YEAR:{textbook.year}"
    
    # Создаем QR код
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # Создаем изображение
    img = qr.make_image(fill_color="black", back_color="white")
    img = img.resize((settings.QR_CODE_SIZE, settings.QR_CODE_SIZE))
    
    # Сохраняем файл
    filename = f"textbook_{textbook.id}.png"
    filepath = os.path.join(settings.QR_CODES_DIR, filename)
    img.save(filepath)
    
    return filepath


def generate_qr_batch(textbooks: List[Textbook]) -> List[str]:
    """
    Генерация QR кодов для списка учебников
    Возвращает список путей к файлам
    """
    create_qr_codes_directory()
    filepaths = []
    
    for textbook in textbooks:
        filepath = generate_qr_code(textbook)
        filepaths.append(filepath)
    
    return filepaths


def create_print_sheet(textbooks: List[Textbook]) -> str:
    """
    Создание листа для печати с QR кодами (3x7 наклеек)
    Возвращает путь к файлу листа
    """
    create_qr_codes_directory()
    
    # Размеры для печати (A4 примерно 2480x3508 пикселей при 300 DPI)
    sheet_width = 2480
    sheet_height = 3508
    
    # Размер одной наклейки
    sticker_width = sheet_width // settings.QR_CODES_PER_ROW
    sticker_height = sheet_height // settings.QR_CODES_PER_COLUMN
    
    # Создаем пустой лист
    sheet = Image.new('RGB', (sheet_width, sheet_height), 'white')
    
    # Генерируем QR коды и размещаем их на листе
    for i, textbook in enumerate(textbooks[:21]):  # Максимум 21 код (3x7)
        # Генерируем QR код
        qr_path = generate_qr_code(textbook)
        qr_img = Image.open(qr_path)
        
        # Масштабируем QR код под размер наклейки
        qr_size = min(sticker_width, sticker_height) - 40  # Отступы
        qr_img = qr_img.resize((qr_size, qr_size))
        
        # Вычисляем позицию
        row = i // settings.QR_CODES_PER_ROW
        col = i % settings.QR_CODES_PER_ROW
        
        x = col * sticker_width + (sticker_width - qr_size) // 2
        y = row * sticker_height + (sticker_height - qr_size) // 2
        
        # Вставляем QR код на лист
        sheet.paste(qr_img, (x, y))
        
        # Добавляем текст с информацией об учебнике
        draw = ImageDraw.Draw(sheet)
        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()
        
        # Текст под QR кодом
        text = f"{textbook.subject[:20]}\n{textbook.title[:30]}"
        text_x = col * sticker_width + 20
        text_y = y + qr_size + 10
        
        draw.text((text_x, text_y), text, fill="black", font=font)
    
    # Сохраняем лист
    sheet_filename = f"qr_sheet_{len(textbooks)}.png"
    sheet_path = os.path.join(settings.QR_CODES_DIR, sheet_filename)
    sheet.save(sheet_path)
    
    return sheet_path