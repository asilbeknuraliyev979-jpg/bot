import os
import math
import random
import string
import qrcode
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from pathlib import Path
from config.config import Config

def generate_certificate_id() -> str:
    # Generate a unique certificate ID, e.g. EMB-2026-00521
    year = datetime.now().year
    num = "".join(random.choices(string.digits, k=5))
    return f"EMB-{year}-{num}"

def create_certificate(full_name: str, class_name: str, subject: str, test_code: str, correct: int, total: int, percentage: float) -> dict:
    """
    Generates a premium education-style certificate matching the requested template exactly.
    Returns a dictionary with 'cert_id', 'image_path', and 'pdf_path'.
    """
    cert_id = generate_certificate_id()
    
    # 1. Create a base high-definition canvas (1280 x 960) with premium light cream linen background
    width, height = 1280, 960
    background_color = "#FDFBF7"  # Elegant off-white/cream
    image = Image.new("RGB", (width, height), background_color)
    draw = ImageDraw.Draw(image)
    
    # Color Palette
    navy_blue = "#083262"  # Premium dark navy blue
    gold = "#D2AC67"       # Sleek gold color
    dark_gray = "#333333"  # Text color
    
    # 2. Draw Elegant Repeating star watermarks for premium certificate paper look
    for wx in range(100, width, 180):
        for wy in range(100, height, 180):
            draw.polygon([
                (wx, wy - 6), (wx + 2, wy - 2), (wx + 6, wy - 2), (wx + 3, wy),
                (wx + 4, wy + 4), (wx, wy + 2), (wx - 4, wy + 4), (wx - 3, wy),
                (wx - 6, wy - 2), (wx - 2, wy - 2)
            ], fill="#FAF5EB")
            
    # Draw Subtle Wavy Abstract Silk Curves Across Canvas
    for offset in range(0, 200, 20):
        draw.arc([30 - offset, height - 450 - offset, 650 - offset, height - 30 - offset], 90, 180, fill="#F2E6D5", width=1)
        draw.arc([width - 650 + offset, 30 + offset, width - 30 + offset, 450 + offset], 270, 360, fill="#F2E6D5", width=1)
    
    # 3. Draw Premium Geometric Polygonal Overlays in corners with Gold Borders
    # Top-Right Corner
    draw.polygon([(width - 380, 40), (width - 40, 40), (width - 40, 380)], fill=navy_blue)
    draw.polygon([(width - 430, 40), (width - 380, 40), (width - 40, 380), (width - 40, 430)], fill=gold)
    
    # Bottom-Left Corner
    draw.polygon([(40, height - 380), (40, height - 40), (380, height - 40)], fill=navy_blue)
    draw.polygon([(40, height - 430), (40, height - 380), (380, height - 40), (430, height - 40)], fill=gold)
    
    # Bottom-Right Corner
    draw.polygon([(width - 480, height - 40), (width - 40, height - 480), (width - 40, height - 40)], fill=navy_blue)
    draw.polygon([(width - 530, height - 40), (width - 480, height - 40), (width - 40, height - 480), (width - 40, height - 530)], fill=gold)

    # 4. Draw Premium Double Gold and Navy Inner Borders
    # Primary gold outer border
    draw.rectangle([40, 40, width - 40, height - 40], outline=gold, width=3)
    # Secondary thin gold inner rim
    draw.rectangle([46, 46, width - 46, height - 46], outline=gold, width=1)
    # Inner navy blue frame
    draw.rectangle([50, 50, width - 50, height - 50], outline=navy_blue, width=2)
    
    # 5. Load System Fonts
    try:
        title_font = ImageFont.truetype("georgiab.ttf", 66)       # Georgia Bold
        subtitle_font = ImageFont.truetype("georgiai.ttf", 22)    # Georgia Italic
        cursive_font = ImageFont.truetype("gabriola.ttf", 75)      # Gabriola Cursive
        bold_serif = ImageFont.truetype("georgiab.ttf", 26)       # Georgia Bold small
        sans_bold = ImageFont.truetype("arialbd.ttf", 20)         # Arial Bold
        sans_regular = ImageFont.truetype("arial.ttf", 18)        # Arial Regular
        caption_font = ImageFont.truetype("arial.ttf", 14)        # Arial Caption
    except IOError:
        # Fallbacks
        title_font = ImageFont.load_default(50)
        subtitle_font = ImageFont.load_default(18)
        cursive_font = ImageFont.load_default(36)
        bold_serif = ImageFont.load_default(20)
        sans_bold = ImageFont.load_default(16)
        sans_regular = ImageFont.load_default(14)
        caption_font = ImageFont.load_default(12)
        
    # 6. Top-Left Premium Ribbed Golden Seal (Top-Left of Certificate)
    seal_cx, seal_cy = 160, 220
    
    # Draw ribbons hanging from seal
    draw.polygon([(seal_cx - 30, seal_cy + 10), (seal_cx - 50, seal_cy + 140), (seal_cx - 20, seal_cy + 115), (seal_cx - 5, seal_cy + 10)], fill=navy_blue)
    draw.polygon([(seal_cx - 30, seal_cy + 10), (seal_cx - 50, seal_cy + 140), (seal_cx - 20, seal_cy + 115), (seal_cx - 5, seal_cy + 10)], outline=gold, width=2)
    
    draw.polygon([(seal_cx + 5, seal_cy + 10), (seal_cx + 20, seal_cy + 115), (seal_cx + 50, seal_cy + 140), (seal_cx + 30, seal_cy + 10)], fill=navy_blue)
    draw.polygon([(seal_cx + 5, seal_cy + 10), (seal_cx + 20, seal_cy + 115), (seal_cx + 50, seal_cy + 140), (seal_cx + 30, seal_cy + 10)], outline=gold, width=2)
    
    # Generate jagged golden teeth for the outer seal ring
    teeth_points = []
    num_teeth = 40
    for i in range(2 * num_teeth):
        angle = i * math.pi / num_teeth
        r = 85 if i % 2 == 0 else 73
        x = seal_cx + r * math.cos(angle)
        y = seal_cy + r * math.sin(angle)
        teeth_points.append((x, y))
    draw.polygon(teeth_points, fill=gold)
    
    # Inner navy blue ring
    draw.ellipse([seal_cx - 62, seal_cy - 62, seal_cx + 62, seal_cy + 62], fill=navy_blue)
    # Inner gold border ring
    draw.ellipse([seal_cx - 55, seal_cy - 55, seal_cx + 55, seal_cy + 55], outline=gold, width=2)
    
    # Draw perfect programmatic gold star in seal center (instead of 🏆 emoji)
    star_pts = []
    for i in range(10):
        angle = i * math.pi / 5 - math.pi / 2
        r = 30 if i % 2 == 0 else 14
        star_pts.append((seal_cx + r * math.cos(angle), seal_cy + r * math.sin(angle)))
    draw.polygon(star_pts, fill=gold)
    
    # 7. Draw Top-Center Header with Programmatic graduation cap shape (instead of 🎓 emoji)
    cap_cx, cap_cy = width // 2, 105
    # Diamond top
    draw.polygon([(cap_cx, cap_cy - 12), (cap_cx + 24, cap_cy), (cap_cx, cap_cy + 12), (cap_cx - 24, cap_cy)], fill=navy_blue)
    draw.polygon([(cap_cx, cap_cy - 12), (cap_cx + 24, cap_cy), (cap_cx, cap_cy + 12), (cap_cx - 24, cap_cy)], outline=gold, width=2)
    # Base skull arch
    draw.chord([cap_cx - 12, cap_cy, cap_cx + 12, cap_cy + 16], 0, 180, fill=navy_blue)
    # Tassel
    draw.line([(cap_cx, cap_cy), (cap_cx - 16, cap_cy + 6)], fill=gold, width=2)
    draw.ellipse([cap_cx - 18, cap_cy + 5, cap_cx - 14, cap_cy + 9], fill=gold)
    
    draw.text((width // 2, 160), "EDU MASTER BOT", font=bold_serif, fill=navy_blue, anchor="mm")
    draw.text((width // 2, 190), "BILIM – KELAJAK KALITI!", font=caption_font, fill=gold, anchor="mm")
    
    # 8. Draw "S E R T I F I K A T" Title
    draw.text((width // 2, 280), "S E R T I F I K A T", font=title_font, fill=navy_blue, anchor="mm")
    
    # 9. Draw "Ushbu sertifikat" Gold Banner Ribbon
    banner_left, banner_top = width // 2 - 180, 335
    banner_right, banner_bottom = width // 2 + 180, 375
    draw.rectangle([banner_left, banner_top, banner_right, banner_bottom], fill=gold)
    draw.polygon([(banner_left, banner_top), (banner_left - 15, banner_top + 20), (banner_left, banner_bottom)], fill=gold)
    draw.polygon([(banner_right, banner_top), (banner_right + 15, banner_top + 20), (banner_right, banner_bottom)], fill=gold)
    draw.text((width // 2, 355), "Ushbu sertifikat", font=sans_bold, fill="#FFFFFF", anchor="mm")
    
    # 10. Draw Student Full Name in beautiful calligraphy style
    draw.text((width // 2, 445), full_name, font=cursive_font, fill=navy_blue, anchor="mm")
    
    # Elegant custom gold flourishes flanking the student name
    # Left flourish
    draw.arc([width // 2 - 290, 428, width // 2 - 240, 458], 0, 360, fill=gold, width=2)
    draw.line([(width // 2 - 250, 443), (width // 2 - 180, 443)], fill=gold, width=2)
    # Right flourish
    draw.arc([width // 2 + 240, 428, width // 2 + 290, 458], 0, 360, fill=gold, width=2)
    draw.line([(width // 2 + 180, 443), (width // 2 + 250, 443)], fill=gold, width=2)
    
    # Vintage thin ornament/divider line under name
    draw.line([(width // 2 - 200, 485), (width // 2 + 200, 485)], fill=gold, width=1)
    draw.polygon([(width // 2, 480), (width // 2 + 8, 485), (width // 2, 490), (width // 2 - 8, 485)], fill=gold)
    
    # 11. Draw Description Text
    desc_text = "Edu Master Bot da o'tkazilgan testda yuqori natija ko'rsatgani uchun\nushbu sertifikat bilan taqdirlanadi."
    draw.text((width // 2, 535), desc_text, font=subtitle_font, fill=dark_gray, anchor="mm", align="center")
    
    # 12. Draw 5-Column Statistics with Circular Badges containing CUSTOM VECTOR ICONS (No emojis!)
    col_y = 650
    col_width_span = 960
    start_x = 160
    col_gap = col_width_span // 4
    
    for idx in range(5):
        cx = start_x + (idx * col_gap)
        
        # Draw dark navy circle badge
        draw.ellipse([cx - 28, col_y - 28, cx + 28, col_y + 28], fill=navy_blue, outline=gold, width=2)
        
        # Draw programmatic vector graphics inside circle depending on column
        if idx == 0:  # FAN (Book icon)
            draw.rectangle([cx - 12, col_y - 8, cx - 2, col_y + 8], fill="#FFFFFF")
            draw.rectangle([cx + 2, col_y - 8, cx + 12, col_y + 8], fill="#FFFFFF")
            draw.line([(cx - 9, col_y - 4), (cx - 5, col_y - 4)], fill=navy_blue, width=1)
            draw.line([(cx - 9, col_y), (cx - 5, col_y)], fill=navy_blue, width=1)
            draw.line([(cx - 9, col_y + 4), (cx - 5, col_y + 4)], fill=navy_blue, width=1)
            draw.line([(cx + 5, col_y - 4), (cx + 9, col_y - 4)], fill=navy_blue, width=1)
            draw.line([(cx + 5, col_y), (cx + 9, col_y)], fill=navy_blue, width=1)
            draw.line([(cx + 5, col_y + 4), (cx + 9, col_y + 4)], fill=navy_blue, width=1)
            title = "FAN"
            val = subject
        elif idx == 1:  # TEST KODI (Tag shape)
            draw.polygon([(cx - 12, col_y - 6), (cx + 4, col_y - 6), (cx + 12, col_y + 2), (cx + 4, col_y + 10), (cx - 12, col_y + 10)], fill="#FFFFFF")
            draw.ellipse([cx - 7, col_y - 1, cx - 3, col_y + 3], fill=navy_blue)
            title = "TEST KODI"
            val = test_code
        elif idx == 2:  # NATIJA (Award star medal)
            m_pts = []
            for i in range(10):
                angle = i * math.pi / 5 - math.pi / 2
                r = 12 if i % 2 == 0 else 6
                m_pts.append((cx + r * math.cos(angle), col_y - 2 + r * math.sin(angle)))
            draw.polygon(m_pts, fill=gold)
            draw.polygon([(cx - 5, col_y + 4), (cx - 9, col_y + 13), (cx - 1, col_y + 10)], fill="#FFFFFF")
            draw.polygon([(cx + 5, col_y + 4), (cx + 9, col_y + 13), (cx + 1, col_y + 10)], fill="#FFFFFF")
            title = "NATIJA"
            val = f"{percentage}%"
        elif idx == 3:  # TO'G'RI JAVOBLAR (Bullseye Target)
            draw.ellipse([cx - 12, col_y - 12, cx + 12, col_y + 12], outline="#FFFFFF", width=2)
            draw.ellipse([cx - 7, col_y - 7, cx + 7, col_y + 7], outline="#FFFFFF", width=1)
            draw.ellipse([cx - 3, col_y - 3, cx + 3, col_y + 3], fill=gold)
            title = "TO'G'RI JAVOBLAR"
            val = f"{correct} / {total}"
        else:  # SINF (Graduation Cap)
            draw.polygon([(cx, col_y - 8), (cx + 12, col_y - 2), (cx, col_y + 4), (cx - 12, col_y - 2)], fill="#FFFFFF")
            draw.chord([cx - 6, col_y, cx + 6, col_y + 10], 0, 180, fill="#FFFFFF")
            title = "SINF"
            val = class_name
            
        # Column Title (e.g. FAN)
        draw.text((cx, col_y + 48), title, font=sans_bold, fill=gold, anchor="mm")
        # Column Value (e.g. Matematika)
        draw.text((cx, col_y + 72), val, font=sans_bold, fill=navy_blue, anchor="mm")
        
    # 13. Bottom Section: Signature (Left), Seal/QR (Center), Date (Right)
    bottom_y = 835
    
    # A. Signature (Left) with elegant flowing calligraphy pen lines
    sig_points = []
    for t in range(50):
        x_sig = 120 + t * 4
        y_sig = bottom_y - 35 + 8 * math.sin(t * 0.3) - 4 * math.cos(t * 0.1)
        sig_points.append((x_sig, y_sig))
    draw.line(sig_points, fill=navy_blue, width=2)
    
    draw.line([(120, bottom_y - 10), (320, bottom_y - 10)], fill=dark_gray, width=1)
    draw.text((220, bottom_y + 10), "Bot Admini", font=sans_bold, fill=dark_gray, anchor="mm")
    draw.text((220, bottom_y + 28), "Edu Master Bot", font=caption_font, fill=navy_blue, anchor="mm")
    
    # B. Circular Stamp Logo (Middle-Left)
    stamp_cx, stamp_cy = 440, bottom_y - 10
    draw.ellipse([stamp_cx - 45, stamp_cy - 45, stamp_cx + 45, stamp_cy + 45], outline=navy_blue, width=2)
    draw.ellipse([stamp_cx - 40, stamp_cy - 40, stamp_cx + 40, stamp_cy + 40], outline=gold, width=1)
    draw.text((stamp_cx, stamp_cy - 12), "EDU MASTER", font=caption_font, fill=navy_blue, anchor="mm")
    
    # Draw stamp cap
    draw.polygon([(stamp_cx, stamp_cy - 2), (stamp_cx + 8, stamp_cy + 3), (stamp_cx, stamp_cy + 8), (stamp_cx - 8, stamp_cy + 3)], fill=navy_blue)
    draw.chord([stamp_cx - 4, stamp_cy + 4, stamp_cx + 4, stamp_cy + 12], 0, 180, fill=navy_blue)
    
    draw.text((stamp_cx, stamp_cy + 22), "KAFOLATLANGAN", font=caption_font, fill=navy_blue, anchor="mm")
    
    # C. QR Code inside a gold Wheat/Laurel Wreath border (Middle)
    qr_cx, qr_cy = 640, bottom_y - 15
    qr_data = f"Edu Master Bot\nSertifikat: {cert_id}\nIsm: {full_name}\nSinf: {class_name}\nFan: {subject}\nNatija: {percentage}%\nSana: {datetime.now().strftime('%d-%b-%Y')}"
    qr = qrcode.QRCode(version=1, box_size=3, border=1)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color=navy_blue, back_color=background_color).convert("RGB")
    qr_img = qr_img.resize((90, 90))
    image.paste(qr_img, (qr_cx - 45, qr_cy - 45))
    
    # Programmatic golden Laurel Wreath arcs flanking the QR code
    draw.arc([qr_cx - 80, qr_cy - 45, qr_cx - 45, qr_cy + 45], 90, 270, fill=gold, width=2)
    draw.arc([qr_cx + 45, qr_cy - 45, qr_cx + 80, qr_cy + 45], 270, 90, fill=gold, width=2)
    for a in range(-40, 45, 20):
        lx = qr_cx - 62 + 8 * math.sin(a * math.pi / 180)
        ly = qr_cy + 35 * math.cos(a * math.pi / 180)
        draw.ellipse([lx - 3, ly - 3, lx + 3, ly + 3], fill=gold)
        
        rx = qr_cx + 62 - 8 * math.sin(a * math.pi / 180)
        ry = qr_cy + 35 * math.cos(a * math.pi / 180)
        draw.ellipse([rx - 3, ry - 3, rx + 3, ry + 3], fill=gold)
        
    draw.text((qr_cx, qr_cy + 65), f"Sertifikat ID: {cert_id}", font=sans_bold, fill=navy_blue, anchor="mm")
    
    # D. Calendar/Date (Right)
    sana_cx = 980
    # Programmatic grid calendar icon
    draw.rectangle([sana_cx - 16, bottom_y - 45, sana_cx + 16, bottom_y - 15], outline=navy_blue, width=2)
    draw.rectangle([sana_cx - 10, bottom_y - 49, sana_cx - 6, bottom_y - 43], fill=gold)
    draw.rectangle([sana_cx + 6, bottom_y - 49, sana_cx + 10, bottom_y - 43], fill=gold)
    draw.rectangle([sana_cx - 15, bottom_y - 44, sana_cx + 15, bottom_y - 36], fill=gold)
    for dx in [-8, 0, 8]:
        for dy in [-28, -20]:
            draw.rectangle([sana_cx + dx - 2, bottom_y + dy - 2, sana_cx + dx + 2, bottom_y + dy + 2], fill=navy_blue)
            
    draw.text((sana_cx, bottom_y + 5), "Sana", font=sans_bold, fill=gold, anchor="mm")
    current_date = datetime.now().strftime("%d-%b-%Y")
    draw.text((sana_cx, bottom_y + 25), current_date, font=sans_bold, fill=navy_blue, anchor="mm")
    
    # 14. Save Files securely
    Config.ensure_dirs()
    image_filename = f"cert_{cert_id.replace('-', '_')}.png"
    pdf_filename = f"cert_{cert_id.replace('-', '_')}.pdf"
    
    image_path = Config.CERTIFICATE_DIR / image_filename
    pdf_path = Config.CERTIFICATE_DIR / pdf_filename
    
    # Save Image
    image.save(image_path, "PNG")
    # Save PDF
    image.save(pdf_path, "PDF")
    
    return {
        "cert_id": cert_id,
        "image_path": str(image_path),
        "pdf_path": str(pdf_path)
    }
