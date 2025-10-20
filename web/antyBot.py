from PIL import Image, ImageDraw, ImageFont
import random
import base64
from io import BytesIO

def generate_captcha():
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    op = '+'
    question = f"{a} {op} {b}"
    
    answer = a + b

    width, height = 150, 60
    img = Image.new("RGB", (width, height), color=(255,255,255))
    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype("arial.ttf", size=15)
    bbox = draw.textbbox((0, 0), question, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2
    draw.text((text_x, text_y), question, font=font, fill=(0,0,0))

    for _ in range(8):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        line_color = tuple(random.randint(50,200) for _ in range(3))
        draw.line([(x1, y1), (x2, y2)], fill=line_color, width=2)

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    img_bytes = buf.read()
    img_base64 = "data:image/png;base64," + base64.b64encode(img_bytes).decode("utf-8")

    return answer, img_base64
