from flask import Flask, render_template, request, jsonify, url_for
import base64
import hashlib
import io
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

load_dotenv()

app = Flask(__name__)

# Yandex Cloud credentials. Store them only in .env, not in code.
API_KEY = os.getenv("YANDEX_API_KEY", "").strip()
FOLDER_ID = os.getenv("FOLDER_ID", "").strip()
DEMO_MODE = os.getenv("DEMO_MODE", "auto").strip().lower()

STATIC_DIR = Path(app.root_path) / "static"
GENERATED_DIR = STATIC_DIR / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)

# Prepared logo style presets. The selected value is added to the final prompt.
PRESET_STYLES = {
    "minimalist": "минималистичный логотип, чистый дизайн, простые геометрические формы, много воздуха",
    "modern": "современный логотип, яркие акценты, динамичная композиция, цифровой стиль",
    "geometric": "геометрический логотип, четкие линии, абстрактный знак, строгая симметрия",
    "vintage": "винтажный логотип, ретро-эстетика, декоративная рамка, премиальный вид",
    "tech": "технологичный логотип, AI-эстетика, нейронные линии, футуристический знак",
    "corporate": "корпоративный логотип, профессиональный вид, строгий стиль, доверие и надежность",
    "creative": "креативный логотип, художественный стиль, необычная форма, запоминающийся знак",
    "elegant": "элегантный логотип, утонченные формы, премиальный стиль, аккуратная типографика",
}

LOGO_FORMS = {
    "badge": "квадратная иконка/бейдж 1:1, подходящий для сайта и соцсетей",
    "circle": "круглая эмблема с центральным знаком",
    "wordmark": "логотип с названием компании как главным элементом",
    "icon_text": "комбинация иконки и текстового названия компании",
}

STYLE_COLORS = {
    "minimalist": (31, 41, 55, 20, 184, 166),
    "modern": (79, 70, 229, 236, 72, 153),
    "geometric": (15, 23, 42, 99, 102, 241),
    "vintage": (79, 70, 54, 180, 83, 9),
    "tech": (2, 132, 199, 16, 185, 129),
    "corporate": (30, 64, 175, 14, 165, 233),
    "creative": (124, 58, 237, 245, 158, 11),
    "elegant": (17, 24, 39, 168, 85, 247),
}


def has_yandex_credentials() -> bool:
    return bool(API_KEY and FOLDER_ID and API_KEY != "YOUR_API_KEY_HERE" and FOLDER_ID != "b1g...")


def should_use_demo_mode() -> bool:
    if DEMO_MODE in {"1", "true", "yes", "on"}:
        return True
    if DEMO_MODE in {"0", "false", "no", "off"}:
        return False
    return not has_yandex_credentials()


def build_prompt(company_name: str, style_key: str, custom_prompt: str, logo_form: str) -> str:
    prompt = (
        f'Создай профессиональный логотип для компании "{company_name}". '
        "Изображение должно быть квадратным 1:1, чистым, без лишнего фона, пригодным для сайта, презентации и соцсетей. "
    )

    if logo_form in LOGO_FORMS:
        prompt += f"Форма: {LOGO_FORMS[logo_form]}. "

    if style_key in PRESET_STYLES:
        prompt += f"Стиль: {PRESET_STYLES[style_key]}. "

    if custom_prompt:
        prompt += f"Дополнительные пожелания: {custom_prompt}. "

    return prompt.strip()


def stable_seed(*parts: str) -> int:
    raw = "|".join(str(part) for part in parts if part is not None)
    return int(hashlib.sha256(raw.encode("utf-8")).hexdigest()[:8], 16)


def get_font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def draw_centered_text(draw: ImageDraw.ImageDraw, text: str, y: int, font, fill, max_width: int):
    if not text:
        return

    current = text
    while len(current) > 1 and draw.textbbox((0, 0), current, font=font)[2] > max_width:
        current = current[:-1]
    if current != text:
        current = current[:-1] + "…"

    bbox = draw.textbbox((0, 0), current, font=font)
    x = (1024 - (bbox[2] - bbox[0])) // 2
    draw.text((x, y), current, font=font, fill=fill)


def generate_demo_image(company_name: str, style_key: str, custom_prompt: str, logo_form: str, seed=None):
    """Local deterministic logo generator for homework/testing when Yandex credentials are absent."""
    if seed is None:
        seed = stable_seed(company_name, style_key, custom_prompt, logo_form)
    else:
        seed = int(seed)

    c1r, c1g, c1b, c2r, c2g, c2b = STYLE_COLORS.get(style_key, STYLE_COLORS["tech"])
    accent = (c2r, c2g, c2b)
    main = (c1r, c1g, c1b)
    dark = (15, 23, 42)

    img = Image.new("RGB", (1024, 1024), "white")
    draw = ImageDraw.Draw(img)

    for i in range(1024):
        ratio = i / 1023
        r = int(248 * (1 - ratio) + 238 * ratio)
        g = int(250 * (1 - ratio) + 242 * ratio)
        b = int(252 * (1 - ratio) + 255 * ratio)
        draw.line((0, i, 1024, i), fill=(r, g, b))

    for i in range(-300, 1200, 120):
        draw.line((i, 0, i + 560, 1024), fill=(235, 240, 255), width=18)

    if logo_form == "circle":
        draw.ellipse((190, 140, 834, 784), fill=(255, 255, 255), outline=accent, width=14)
        draw.ellipse((250, 200, 774, 724), outline=(226, 232, 240), width=6)
    elif logo_form == "wordmark":
        draw.rounded_rectangle((150, 245, 874, 690), radius=80, fill=(255, 255, 255), outline=(226, 232, 240), width=6)
    else:
        draw.rounded_rectangle((190, 130, 834, 784), radius=120, fill=(255, 255, 255), outline=(226, 232, 240), width=6)

    center = (512, 430)
    draw.ellipse((384, 302, 640, 558), outline=main, width=18)
    draw.arc((328, 246, 696, 614), start=24, end=336, fill=accent, width=14)
    draw.arc((360, 278, 664, 582), start=205, end=520, fill=(148, 163, 184), width=8)

    nodes = [(512, 282), (650, 430), (512, 578), (374, 430), (592, 350), (450, 506)]
    for idx, (x, y) in enumerate(nodes):
        radius = 22 if idx < 4 else 15
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=accent if idx % 2 else main)
        draw.line((center[0], center[1], x, y), fill=(203, 213, 225), width=5)

    points = [(340, 630), (425, 590), (500, 615), (610, 535), (690, 562)]
    draw.line(points, fill=accent, width=18, joint="curve")
    draw.polygon([(690, 562), (650, 540), (662, 596)], fill=accent)

    font_title = get_font(88 if len(company_name) <= 12 else 70, bold=True)
    font_sub = get_font(30, bold=False)
    clean_name = company_name.strip() or "AI MarketLab"
    draw_centered_text(draw, clean_name.upper(), 790, font_title, dark, 820)
    draw_centered_text(draw, "AI • DIGITAL • MARKETING", 890, font_sub, (71, 85, 105), 760)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG", optimize=True)
    image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return {"success": True, "image": image_base64, "seed": seed, "mode": "demo"}


def save_generated_image(image_base64: str, company_name: str, seed: int) -> str:
    safe_name = "".join(ch.lower() if ch.isalnum() else "-" for ch in company_name).strip("-") or "logo"
    file_name = f"{safe_name}-{seed}.png"
    file_path = GENERATED_DIR / file_name
    file_path.write_bytes(base64.b64decode(image_base64))
    return f"generated/{file_name}"


def generate_yandex_image(prompt, seed=None):
    """Generate image via Yandex Art API."""
    if not has_yandex_credentials():
        return {"error": "YANDEX_API_KEY или FOLDER_ID не настроены. Заполните .env или включите DEMO_MODE=true."}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Api-Key {API_KEY}",
    }

    if seed is None:
        seed = int(time.time())
    else:
        seed = int(seed)

    payload = {
        "modelUri": f"art://{FOLDER_ID}/yandex-art/latest",
        "generationOptions": {
            "seed": seed,
            "aspectRatio": {"widthRatio": "1", "heightRatio": "1"},
        },
        "messages": [{"weight": "1", "text": prompt}],
    }

    try:
        create_response = requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/imageGenerationAsync",
            headers=headers,
            json=payload,
            timeout=30,
        )
        if create_response.status_code != 200:
            return {"error": f"Ошибка создания запроса: {create_response.text}"}

        operation_id = create_response.json().get("id")
        if not operation_id:
            return {"error": "Не получен ID операции"}

        for _ in range(60):
            time.sleep(2)
            status_response = requests.get(
                f"https://llm.api.cloud.yandex.net:443/operations/{operation_id}",
                headers={"Authorization": f"Api-Key {API_KEY}"},
                timeout=30,
            )
            if status_response.status_code != 200:
                return {"error": f"Ошибка проверки статуса: {status_response.text}"}

            result = status_response.json()
            if result.get("done"):
                if "error" in result:
                    return {"error": f"Ошибка генерации: {result['error']}"}
                image_base64 = result.get("response", {}).get("image")
                if image_base64:
                    return {"success": True, "image": image_base64, "seed": seed, "mode": "yandex-art"}
                return {"error": "Изображение не найдено в ответе"}

        return {"error": "Превышено время ожидания генерации"}
    except requests.exceptions.Timeout:
        return {"error": "Превышено время ожидания запроса"}
    except Exception as exc:
        return {"error": f"Ошибка: {exc}"}


def generate_image(prompt, company_name, style_key, custom_prompt, logo_form, seed=None):
    if should_use_demo_mode():
        return generate_demo_image(company_name, style_key, custom_prompt, logo_form, seed=seed)
    return generate_yandex_image(prompt, seed=seed)


@app.route("/")
def index():
    return render_template(
        "index.html",
        styles=PRESET_STYLES,
        forms=LOGO_FORMS,
        demo_mode=should_use_demo_mode(),
    )


@app.route("/health")
def health():
    return jsonify({"status": "ok", "demo_mode": should_use_demo_mode(), "yandex_credentials": has_yandex_credentials()})


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}

    company_name = data.get("company_name", "").strip()
    custom_prompt = data.get("custom_prompt", "").strip()
    style = data.get("style", "minimalist")
    logo_form = data.get("logo_form", "badge")

    if not company_name:
        return jsonify({"error": "Введите название компании"}), 400

    prompt = build_prompt(company_name, style, custom_prompt, logo_form)
    result = generate_image(prompt, company_name, style, custom_prompt, logo_form)

    if "error" in result:
        return jsonify(result), 500

    image_path = save_generated_image(result["image"], company_name, result["seed"])
    image_url = url_for("static", filename=image_path)

    return jsonify(
        {
            "success": True,
            "image": result["image"],
            "image_url": image_url,
            "download_url": image_url,
            "prompt": prompt,
            "seed": result["seed"],
            "mode": result.get("mode", "yandex-art"),
        }
    )


@app.route("/refine", methods=["POST"])
def refine():
    data = request.get_json(silent=True) or {}

    original_prompt = data.get("original_prompt", "").strip()
    refinement = data.get("refinement", "").strip()
    original_seed = data.get("seed")
    company_name = data.get("company_name", "AI MarketLab").strip() or "AI MarketLab"
    style = data.get("style", "minimalist")
    logo_form = data.get("logo_form", "badge")

    if not original_prompt or not refinement:
        return jsonify({"error": "Необходимы оригинальный промпт и текст доработки"}), 400

    new_prompt = f"{original_prompt} Доработка: {refinement}. Сохрани основную структуру и визуальную идею."
    result = generate_image(new_prompt, company_name, style, refinement, logo_form, seed=original_seed)

    if "error" in result:
        return jsonify(result), 500

    image_path = save_generated_image(result["image"], company_name, result["seed"])
    image_url = url_for("static", filename=image_path)

    return jsonify(
        {
            "success": True,
            "image": result["image"],
            "image_url": image_url,
            "download_url": image_url,
            "prompt": new_prompt,
            "seed": result["seed"],
            "mode": result.get("mode", "yandex-art"),
        }
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
