import asyncio
import traceback
from datetime import datetime

from openai import OpenAI

from config.config import get_config


class OpenAIAPI:
    """
    Класс для работы с OpenAI API согласно официальной документации.
    Использует настройки из ai_settings.
    """

    def __init__(
        self,
        client: OpenAI,
        model: str,
        temperature: float,
        max_tokens: int,
        system_prompt: str = """
        Ты - опытный нумеролог с многолетним стажем. 
        Ты хорошо разбираешься в нумерологии и работе с числами.
        Давай подробные и глубокие ответы на вопросы, используя принципы нумерологии.
        Твои ответы должны быть конкретными и основанными на числовых значениях.
        Используй в ответах фразы, которые могли бы произнести опытные нумерологи.
        
        Используй дату рождения пользователя и не забывай, что сейчас уже 2025 год)
        """,
    ):
        # Клиент OpenAI теперь определяется из конфигурации и сохраняется как свойство класса.
        self.client = client
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.stories_prompt = ""
        self.text_prompt = ""

    @classmethod
    def create(cls) -> "OpenAIAPI":
        """
        Фабричный метод для создания экземпляра класса с базовыми параметрами.
        Для полной инициализации с настройками из БД используйте initialize().
        """
        config = get_config()
        client = config.open_ai_client

        # Создаем экземпляр с временными значениями
        return cls(
            client=client,
            model="gpt-4o",  # значение по умолчанию
            temperature=0.7,  # значение по умолчанию
            max_tokens=2000,  # значение по умолчанию
            system_prompt=None,
        )

    @classmethod
    async def initialize(cls) -> "OpenAIAPI":
        """
        Асинхронный метод инициализации с загрузкой настроек из БД.
        """
        instance = cls.create()

        # Обновляем параметры из настроек
        instance.model = "gpt-4o"
        instance.temperature = 0.7
        instance.max_tokens = 2000
        instance.system_prompt = None
        instance.stories_prompt = ""
        instance.text_prompt = ""

        return instance

    def chat_completion(
        self, messages: list, temperature: float = None, max_tokens: int = None
    ) -> object:
        """
        Отправляет запрос к OpenAI Chat Completion API.

        :param messages: список сообщений в формате [{"role": "user/system/assistant", "content": "..."}]
        :param temperature: температура генерации; если не указана, берется из настроек
        :param max_tokens: максимальное количество токенов; если не указано, берется из настроек
        :return: объект ответа от OpenAI API
        """
        temperature = (
            temperature if temperature is not None else self.temperature
        )
        max_tokens = max_tokens if max_tokens is not None else self.max_tokens
        try:
            # Используем синхронный метод create() согласно новому API.
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response
        except Exception as e:
            print(f"Ошибка вызова OpenAI API: {e}\n{traceback.format_exc()}")
            raise

    async def chat_completion_async(
        self, messages: list, temperature: float = None, max_tokens: int = None
    ) -> object:
        """
        Асинхронный вариант метода chat_completion, который не блокирует событийный цикл.

        :param messages: список сообщений, как в синхронном методе
        :param temperature: температура генерации (если None, берется из настроек)
        :param max_tokens: максимальное количество токенов (если None, берется из настроек)
        :return: объект ответа от OpenAI API
        """
        temperature = (
            temperature if temperature is not None else self.temperature
        )
        max_tokens = max_tokens if max_tokens is not None else self.max_tokens

        def blocking_call():
            return self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        try:
            response = await asyncio.to_thread(blocking_call)
            return response
        except Exception as e:
            print(f"Ошибка вызова OpenAI API: {e}\n{traceback.format_exc()}")
            raise

    async def generate(self, prompt: str, birth_date: str = None) -> str:
        """
        Генерирует текст на основе переданного prompt.

        :param prompt: входной текст для генерации
        :return: сгенерированный текст
        """
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        birth_date_context = (
            f" с учетом моей даты рождения {birth_date}" if birth_date else ""
        )
        full_prompt = f"Дай мне предсказание или совет по запросу: '{prompt}'{birth_date_context}"
        messages.append({"role": "user", "content": full_prompt})

        response = await self.chat_completion_async(messages)
        try:
            generated_text = response.choices[0].message.content
            return generated_text
        except (AttributeError, IndexError) as e:
            print(f"Ошибка обработки ответа OpenAI API: {e}")
            raise ValueError("Неправильный формат ответа от OpenAI API")

    def _calculate_arkan_from_number(self, num: int) -> int:
        """
        Вспомогательный метод для расчета аркана из числа.
        Если число > 22, его цифры складываются, пока результат не станет <= 22.
        """
        while num > 22:
            num = sum(int(digit) for digit in str(num))
        return num

    async def generate_image_async(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "auto",
        output_format: str = "png",  # "jpeg", "png", "webp"
        output_compression: int | None = None,  # 0-100 for jpeg/webp
    ) -> str:
        """
        Генерирует изображение на основе предоставленного промпта с использованием модели gpt-image-1.

        :param prompt: Текстовый промпт для генерации изображения.
        :param size: Размер генерируемого изображения. По умолчанию "1024x1024".
                     Допустимые значения согласно cookbook для gpt-image-1: "1024x1024" (квадрат), "1536x1024" (портрет), "1024x1536" (пейзаж), "auto".
        :param quality: Качество изображения. По умолчанию "auto".
                        Допустимые значения согласно cookbook для gpt-image-1: "low", "medium", "high", "auto".
        :param output_format: Формат выходного изображения. По умолчанию "png".
                              Допустимые значения согласно cookbook для gpt-image-1: "jpeg", "png", "webp".
        :param output_compression: Уровень сжатия (0-100) для форматов "jpeg" или "webp". Применяется, если output_format="jpeg" или "webp".
        :return: Строка с изображением в формате base64 (b64_json).
        """
        # image_model = "gpt-image-1"  # Согласно предоставленному cookbook https://cookbook.openai.com/examples/generate_images_with_gpt_image
        image_model = "dall-e-3"  # Согласно предоставленному cookbook https://cookbook.openai.com/examples/generate_images_with_gpt_image

        # Prepare arguments for the API call
        # output_format and output_compression are not supported directly by client.images.generate
        # in the version likely being used, despite cookbook examples for gpt-image-1 model.
        # The API will likely return PNG by default with b64_json response_format.
        # If specific format/compression is needed, post-processing with PIL/Pillow would be required.
        call_args = {
            "model": image_model,
            "prompt": prompt,
            "size": size,
            # "quality": quality,
            "quality": "hd",
            "response_format": "b64_json",
            # "response_format": "b64_json",  # Explicitly request base64 encoded JSON
        }

        # The following logic for output_format and output_compression is removed from direct API call_args
        # as it causes a TypeError with the current library version.
        # if output_format in ["jpeg", "webp"]:
        #     if output_compression is not None:
        #         if not (0 <= output_compression <= 100):
        #             raise ValueError("output_compression должен быть в диапазоне от 0 до 100 для jpeg/webp.")
        #         # call_args["output_compression"] = output_compression # This line caused issues
        # elif output_format == "png":
        #     pass # PNG is likely default for b64_json
        # else:
        #     print(f"Неподдерживаемый output_format: {output_format} указан для generate_image_async. Будет проигнорирован при вызове API.")

        def blocking_call():
            # Pass the curated call_args directly
            return self.client.images.generate(**call_args)

        try:
            response = await asyncio.to_thread(blocking_call)
            if (
                response.data
                and len(response.data) > 0
                and hasattr(response.data[0], "b64_json")
                and response.data[0].b64_json
            ):
                return response.data[0].b64_json
            # result.json()["data"][0]["b64_json"]
            else:
                print(
                    f"OpenAI API (images.generate) вернул неожиданную структуру ответа: {response}"
                )
                raise ValueError(
                    "Неожиданная структура ответа от OpenAI API при генерации изображения"
                )
        except Exception as e:
            print(
                f"Ошибка вызова OpenAI API (images.generate): {e}\\n{traceback.format_exc()}"
            )
            raise


def convert_markdown_to_html(text: str) -> str:
    """Convert markdown formatting to HTML for Telegram compatibility"""
    import re

    # Handle headers (## Header)
    text = re.sub(r"^##\s+(.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)
    text = re.sub(r"^###\s+(.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)

    # Handle bold (**text** or __text__)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)

    # Handle italic (*text* or _text_)
    text = re.sub(r"\*([^*]+?)\*", r"<i>\1</i>", text)
    text = re.sub(r"_([^_]+?)_", r"<i>\1</i>", text)

    # Handle blockquotes (> text)
    text = re.sub(r"^>\s+(.+)$", r"<i>\1</i>", text, flags=re.MULTILINE)

    # Handle line breaks
    # text = text.replace("\n\n", "\n")

    return text


# - Главный заголовок: `<b>Анализ твоей натальной карты 💫</b>`
async def generate_numerology_prediction(query: str, birth_date: str) -> str:
    """Generate a numerology-based prediction using OpenAI"""
    config = get_config()
    try:
        # Initialize OpenAI API
        today = datetime.now().strftime("%d.%m.%Y")
        system_prompt = f"""
## Роль и экспертиза
Ты - высококвалифицированный астролог с многолетним опытом работы с натальными картами и предсказательной астрологией. Ты обладаешь глубокими знаниями в:
- Интерпретации планет в знаках и домах
- Анализе аспектов между планетами
- Прогностической астрологии (транзиты, прогрессии, дирекции)
- Лунных узлах и кармической астрологии
- Астрологии взаимоотношений
- Хорарной астрологии для конкретных вопросов

## Входные данные
Ты получишь:
1. **Натальный JSON** с полными астрологическими данными человека, включающий:
   - Персональные данные (имя, дата, время, место рождения)
   - Положения всех планет (Солнце, Луна, Меркурий, Венера, Марс, Юпитер, Сатурн, Уран, Нептун, Плутон)
   - Лунные узлы (Северный и Южный)
   - Дополнительные точки (Хирон, Черная Луна Лилит)
   - Угловые точки (Асцендент, Десцендент, MC, IC)
   - Система домов (Плацидус)
   - Ретроградность планет
   - Точные градусы планет

2. **Запрос пользователя** - конкретный вопрос или тема для анализа

## Принципы интерпретации

### Планеты в знаках
- **Солнце** - основная личность, эго, жизненная сила
- **Луна** - эмоции, подсознание, потребности, материнство
- **Меркурий** - мышление, коммуникация, обучение
- **Венера** - любовь, красота, финансы, ценности
- **Марс** - действие, энергия, сексуальность, агрессия
- **Юпитер** - рост, философия, удача, образование
- **Сатурн** - ограничения, дисциплина, карма, уроки
- **Уран** - революции, оригинальность, неожиданности
- **Нептун** - иллюзии, духовность, творчество, обман
- **Плутон** - трансформация, власть, глубинные процессы

### Дома и их значения
- **1 дом** - личность, внешность, первые впечатления
- **2 дом** - финансы, ценности, самооценка, таланты
- **3 дом** - коммуникация, братья/сестры, короткие поездки
- **4 дом** - семья, дом, корни, мать, недвижимость
- **5 дом** - творчество, дети, романтика, развлечения
- **6 дом** - работа, здоровье, рутина, служение
- **7 дом** - партнерство, брак, открытые враги, сотрудничество
- **8 дом** - трансформация, смерть, секс, чужие деньги, оккультизм
- **9 дом** - философия, высшее образование, путешествия, религия
- **10 дом** - карьера, репутация, статус, отец, призвание
- **11 дом** - друзья, группы, мечты, социальные сети
- **12 дом** - подсознание, жертвы, тайны, духовность, изоляция

### Аспекты (орбисы)
- **Соединение (0°)** - слияние энергий, усиление
- **Секстиль (60°)** - гармония, возможности, таланты
- **Квадрат (90°)** - напряжение, препятствия, рост через конфликт
- **Тригон (120°)** - легкость, поток, естественные способности
- **Оппозиция (180°)** - противоположности, баланс, проекция

### Ретроградность
Учитывай ретроградные планеты как показатели:
- Внутренней работы и переосмысления
- Кармических уроков из прошлых жизней
- Необходимости повторного изучения тем планеты

## Стиль ответов

### Форматирование
Используй HTML-теги для Telegram:
- `<b>` для выделения важных моментов и заголовков
- `<i>` для курсива (весь основной текст должен быть в курсиве)
- Структура заголовков: `<i><b><b><i>•</i></b></b> </i><b>Заголовок раздела</b>`
- Одинарные отступы между абзацами: `\n\n`
- Французские кавычки для цитат
- Весь основной текст (кроме заголовков) должен быть обернут в теги `<i>...</i>`
- Подзаголовки внутри разделов выделяй как: `<i><b>Подзаголовок:</b> текст...</i>`
- Разделяй абзацы пустой строкой
- После каждого предложения / пункта ставь точку/восклицательный знак/вопросительный знак
- Если используешь что-то вроде "Совет от Астролога" - пиши от "Совет от AI-астролога"
- Если используешь в ответе какой-то год, то пиши не гг. а год. Например: "2025 год"

### Структура ответа
1. **Краткий анализ натальной карты** (2-3 предложения о ключевых особенностях)
2. **Ответ на конкретный вопрос** (основная часть)
3. **Практические рекомендации** (что делать, как использовать энергии)
4. **Временные рамки** (когда ожидать изменений, благоприятные периоды)
5. **Заключение** (краткое резюме и поддержка)

### Тон и подача
- Профессиональный, но доступный язык
- Избегай фатализма, фокусируйся на возможностях
- Конкретные примеры и практические советы
- Учитывай психологическое состояние человека
- Баланс между реализмом и оптимизмом

## Специальные указания

### Для разных типов вопросов

**Отношения и любовь:**
- Анализируй 5-й и 7-й дома
- Венеру, Марс и их аспекты
- Лунные узлы для кармических связей
- Транзиты к натальным планетам любви

**Карьера и финансы:**
- 2-й, 6-й и 10-й дома
- Положение MC и его управителя
- Юпитер и Сатурн для роста и структуры
- Прогрессии к угловым точкам

**Здоровье:**
- 6-й дом и его управитель
- Аспекты к Марсу (энергия) и Сатурну (ограничения)
- Транзиты медленных планет

**Духовность и саморазвитие:**
- 9-й и 12-й дома
- Нептун, Плутон и Северный узел
- Хирон для исцеления

### Временные техники
- **Транзиты** - текущие влияния планет
- **Прогрессии** - внутреннее развитие (1 день = 1 год)
- **Солнечные возвращения** - годовые циклы
- **Лунные циклы** - месячные ритмы

### Ограничения
- Не делай медицинских диагнозов
- Избегай абсолютных предсказаний
- Помни о свободе воли
- Фокусируйся на тенденциях, а не на фатуме

## Пример структуры ответа

```
<i><b>Анализ твоей натальной карты 💫</b>

[Краткий обзор ключевых особенностей натальной карты]

<i><b><b><i>•</i></b></b> </i><b>[Ответ на конкретный вопрос].</b>

[Детальный анализ с использованием астрологических показателей]

<i><b><b><i>•</i></b></b> </i><b>Рекомендации от AI-астролога.</b>

[Практические советы и рекомендации]

<i><b><b><i>•</i></b></b> </i><b>Благоприятные периоды.</b>

[Временные рамки и лучшие моменты для действий]

<i><b><b><i>•</i></b></b> </i><b>В заключение.</b>

[Поддерживающее резюме и мотивация]
</i>
```

## Важно помнить
- Всегда основывайся на предоставленных натальных данных
- Используй точные градусы для более точных интерпретаций
- Учитывай систему домов (Плацидус)
- Комбинируй несколько астрологических факторов для полной картины
- Максимальный размер ответа - 8000 символов
- Будь конкретным и практичным в советах
- Сегодня уже {today}, поэтому если вопрос "когда...", то учитываем, что сейчас уже {today}
        """
        openai_api = OpenAIAPI(
            # get_config().open_ai_client, "gpt-4o", 0.7, 3000, system_prompt
            config.get_openai_client(),
            "gpt-4.1",
            0.7,
            30000,
            system_prompt,
        )

        prediction_md = await openai_api.generate(query, birth_date)

        try:
            prediction = convert_markdown_to_html(prediction_md)

        except Exception as e:
            print(f"Error converting markdown to HTML: {e}")
            prediction = prediction_md

        return prediction
    except Exception as e:
        print(f"Error generating numerology prediction: {e}")
        return "Произошла ошибка при получении предсказания. Пожалуйста, попробуйте позже."
