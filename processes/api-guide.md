# Руководство по Claude Vision API

## Обзор

Для реального анализа монет используется Claude Vision API (модель `claude-sonnet-4-6`). Пользователь загружает фото — оно кодируется в base64 и отправляется в API вместе со структурированным промптом. API возвращает JSON с грейдом, ценой, дефектами и историей.

---

## Требования

- Аккаунт Anthropic: https://console.anthropic.com
- API-ключ: `Settings → API Keys → Create Key`
- Тарифный план с доступом к `claude-sonnet-4-6`
- Node.js ≥ 18 или Python ≥ 3.10 для бэкенда

---

## Установка SDK

### Node.js
```bash
npm install @anthropic-ai/sdk
```

### Python
```bash
pip install anthropic
```

---

## Промпт для анализа монеты

Это системный промпт — передаётся один раз как `system`. Пользовательское сообщение содержит изображение и короткую инструкцию.

### System prompt
```
Ты — опытный нумизмат с 20-летним стажем и доступом к актуальным каталогам монет (Краузе, Конрос, NGC Price Guide).

Твоя задача: проанализировать фотографию монеты и вернуть структурированный JSON-ответ.

Правила:
1. Отвечай ТОЛЬКО валидным JSON без markdown-обёртки, без комментариев.
2. Если монету невозможно идентифицировать — верни поле "identified": false и укажи причину в "error".
3. Грейд определяй по стандарту Шелдона (Poor P-1 … UNC MS-70).
4. Диапазон цен указывай в рублях для российских монет, в USD для иностранных.
5. Дефекты делити на "major" (влияют на грейд) и "minor" (косметические).
6. Историческую справку пиши на том же языке, что и запрос пользователя.
```

### User message (с изображением)
```
Определи монету на фотографии. Верни результат строго в формате JSON согласно системному промпту.
Язык ответа: русский.
```

---

## Формат JSON-ответа

```json
{
  "identified": true,
  "confidence": 0.94,

  "coin": {
    "name": "1 Рубль СССР",
    "year": 1961,
    "denomination": "1 рубль",
    "country": "СССР",
    "mint": "Ленинградский монетный двор (ЛМД)",
    "composition": "Медно-никелевый сплав (CuNi)",
    "diameter_mm": 27,
    "weight_g": 7.5,
    "mintage": 400000000,
    "catalog_reference": "Краузе Y#134a"
  },

  "grade": {
    "code": "VF-30",
    "name": "Very Fine",
    "name_ru": "Очень хорошее",
    "sheldon_points": 30,
    "scale_position": 0.55
  },

  "price": {
    "currency": "RUB",
    "low": 350,
    "high": 850,
    "note": "Диапазон зависит от торговой площадки и актуальности спроса"
  },

  "defects": {
    "major": [
      {
        "type": "wear",
        "location": "reverse",
        "description": "Потёртость реверса на выступающих деталях"
      }
    ],
    "minor": [
      {
        "type": "scratches",
        "description": "Незначительные царапины в поле"
      },
      {
        "type": "patina",
        "description": "Естественная равномерная патина"
      }
    ]
  },

  "history": "Рубль образца 1961 года введён в ходе денежной реформы СССР, деноминировавшей рубль в соотношении 10:1. Чеканился на Ленинградском монетном дворе из медно-никелевого сплава. Выпускался до 1991 года и стал символом позднесоветской эпохи.",

  "error": null
}
```

### Ответ при неудачной идентификации
```json
{
  "identified": false,
  "confidence": 0,
  "error": "Фотография не содержит монеты или качество изображения недостаточно для идентификации. Рекомендации: хорошее равномерное освещение, монета в фокусе, нейтральный фон.",
  "coin": null,
  "grade": null,
  "price": null,
  "defects": null,
  "history": null
}
```

---

## Реализация — Node.js

```javascript
import Anthropic from '@anthropic-ai/sdk';
import fs from 'fs';

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

const SYSTEM_PROMPT = `Ты — опытный нумизмат с 20-летним стажем и доступом к актуальным каталогам монет (Краузе, Конрос, NGC Price Guide).

Твоя задача: проанализировать фотографию монеты и вернуть структурированный JSON-ответ.

Правила:
1. Отвечай ТОЛЬКО валидным JSON без markdown-обёртки, без комментариев.
2. Если монету невозможно идентифицировать — верни поле "identified": false и укажи причину в "error".
3. Грейд определяй по стандарту Шелдона (Poor P-1 … UNC MS-70).
4. Диапазон цен указывай в рублях для российских монет, в USD для иностранных.
5. Дефекты дели на "major" (влияют на грейд) и "minor" (косметические).
6. Историческую справку пиши на том же языке, что и запрос пользователя.`;

async function analyzeCoin(imagePath) {
  // Читаем файл и кодируем в base64
  const imageBuffer = fs.readFileSync(imagePath);
  const base64Image = imageBuffer.toString('base64');
  const mediaType = 'image/jpeg'; // или image/png, image/webp

  const response = await client.messages.create({
    model: 'claude-sonnet-4-6',
    max_tokens: 1024,
    system: SYSTEM_PROMPT,
    messages: [
      {
        role: 'user',
        content: [
          {
            type: 'image',
            source: {
              type: 'base64',
              media_type: mediaType,
              data: base64Image,
            },
          },
          {
            type: 'text',
            text: 'Определи монету на фотографии. Верни результат строго в формате JSON. Язык ответа: русский.',
          },
        ],
      },
    ],
  });

  // Парсим JSON из ответа
  const rawText = response.content[0].text;
  return JSON.parse(rawText);
}

// Пример использования
const result = await analyzeCoin('./coin.jpg');
console.log(result);
```

---

## Реализация — Python

```python
import anthropic
import base64
import json

client = anthropic.Anthropic()  # читает ANTHROPIC_API_KEY из окружения

SYSTEM_PROMPT = """Ты — опытный нумизмат с 20-летним стажем и доступом к актуальным каталогам монет.

Твоя задача: проанализировать фотографию монеты и вернуть структурированный JSON-ответ.

Правила:
1. Отвечай ТОЛЬКО валидным JSON без markdown-обёртки, без комментариев.
2. Если монету невозможно идентифицировать — верни "identified": false и причину в "error".
3. Грейд — по стандарту Шелдона (Poor P-1 … UNC MS-70).
4. Цены в рублях для РФ/СССР, в USD для иностранных монет.
5. Дефекты: "major" (влияют на грейд) и "minor" (косметические)."""

def analyze_coin(image_path: str) -> dict:
    with open(image_path, "rb") as f:
        image_data = base64.standard_b64encode(f.read()).decode("utf-8")

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Определи монету. Верни JSON. Язык ответа: русский.",
                    },
                ],
            }
        ],
    )

    return json.loads(message.content[0].text)

# Пример
result = analyze_coin("coin.jpg")
print(result)
```

---

## HTTP API (для фронтенда)

Если бэкенд реализован на Express / FastAPI, фронтенд отправляет:

### POST /api/analyze

**Request**
```http
POST /api/analyze
Content-Type: multipart/form-data

image: <binary file>
lang: "ru"  | "en"
```

**Response 200**
```json
{ ...структура JSON-ответа выше... }
```

**Response 400**
```json
{ "error": "Файл не является изображением или превышает 10 МБ" }
```

**Response 500**
```json
{ "error": "Ошибка анализа. Попробуйте позже." }
```

---

## Интеграция в index.html

Заменить демо-задержку в `analyzeBtn` на реальный fetch:

```javascript
analyzeBtn.addEventListener('click', async () => {
  analyzeBtn.classList.add('loading');
  analyzeBtn.disabled = true;

  try {
    const formData = new FormData();
    formData.append('image', currentFile); // хранить файл глобально при загрузке
    formData.append('lang', currentLang);

    const res = await fetch('/api/analyze', { method: 'POST', body: formData });
    if (!res.ok) throw new Error('API error');

    const data = await res.json();

    if (!data.identified) {
      showError(data.error);
      return;
    }

    populateResultCard(data); // функция заполняет DOM из JSON
    resultCard.classList.add('visible');
    resultCard.scrollIntoView({ behavior: 'smooth', block: 'start' });

  } catch (err) {
    showError('Не удалось выполнить анализ. Проверьте подключение.');
  } finally {
    analyzeBtn.classList.remove('loading');
    analyzeBtn.disabled = false;
  }
});
```

---

## Стоимость и лимиты

| Параметр | Значение |
|---|---|
| Модель | `claude-sonnet-4-6` |
| Input tokens (фото ~1000px) | ~1 500–2 000 |
| Output tokens (JSON ответ) | ~400–600 |
| Стоимость за запрос | ~$0.008–0.015 |
| Rate limit (по умолчанию) | 50 RPM |
| Максимальный размер изображения | 5 МБ (после кодирования base64) |
| Поддерживаемые форматы | JPEG, PNG, GIF, WEBP |

---

## Переменные окружения

```bash
# .env (не коммитить в git!)
ANTHROPIC_API_KEY=sk-ant-...

# Node.js: загрузить через dotenv
# Python: загружается автоматически из окружения
```

Добавить `.env` в `.gitignore`:
```
.env
.env.local
```
