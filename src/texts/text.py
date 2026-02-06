from texts import prompts, publications

"""
Simple text localization system.
ᛞᛜᚠᛃᚱᚷ
"""

# PUBLICATIONS = [
#     {

#     },
#     {

#     },
# ]

DEFAULT_LANGUAGE = "ru"

# Default texts in different languages
TEXTS = {
    "en": {
        "main_menu_title": publications.PUBLICATION_1["en"],
        "publications_button": """Important: articles and publications""",
        # "publications_text": """ТЕКСТ ПУБЛИКАЦИЙ""",
        "publications_text": """<i>Greetings!

My name is Zhanna Vidmayer, and I am the author and visionary behind the «TimeAI — Universe of Creativity» project.

Our project is created specifically for architects and designers who seek not just tools, but innovative solutions to bring the boldest ideas in interior design to life.

With TimeAI, you gain access to cutting-edge generative design technologies and neural network tools. These solutions help realize the trends of the future: biophilic design, Japanese minimalism and craft, retro-fusion with a modern accent, the atmosphere of dopamine interiors, as well as flexible personalization and current design trends.

We share and support your aspiration to create unique spaces, combining technology and artistic approach in the rhythm of time.

Welcome to TimeAI — a space where next-generation design is born!</i>""",
        "back_button_to_main_menu": """←""",
        "back_button_to_publications": """←""",
        "publication_1_button": "Creativity without borders",
        "publication_2_button": "Importance of details",
        "publication_3_button": "Live AI sketch",
        "publication_4_button": "Through the prism of art",
        "publication_1_text": publications.PUBLICATION_2["en"],
        "publication_2_text": publications.PUBLICATION_3["en"],
        "publication_3_text": publications.PUBLICATION_4["en"],
        "publication_4_text": publications.PUBLICATION_5["en"],
        "prompt_1_button": prompts.ALL_PROMPTS_list_en[0],
        "prompt_2_button": prompts.ALL_PROMPTS_list_en[1],
        "prompt_3_button": prompts.ALL_PROMPTS_list_en[2],
        "prompt_4_button": prompts.ALL_PROMPTS_list_en[3],
        "prompt_5_button": prompts.ALL_PROMPTS_list_en[4],
        "prompt_6_button": prompts.ALL_PROMPTS_list_en[5],
        "prompt_1_text": prompts.PROMPT_1["en"],
        "prompt_2_text": prompts.PROMPT_2["en"],
        "prompt_3_text": prompts.PROMPT_3["en"],
        "prompt_4_text": prompts.PROMPT_4["en"],
        "prompt_5_text": prompts.PROMPT_5["en"],
        "prompt_6_text": prompts.PROMPT_6["en"],
        # "publication_5_text": publications.PUBLICATION_5["en"],
        "publications_url_text": "Open TimeAI",
        # ᛞᛜᚠᛃᚱᚷ
        "time_video": """
<b>Human & Interior</b> <i><u>in the style of Cubism.</u></i>
TimeAI explores how a person’s inner world transforms into a cubist interior. The protagonist, with their own rhythm, character and dreams, becomes the focal point of the space, while the neural network acts as a subtle co-author, bringing together the person and the home into a single visual story.

Here, Cubism is the language of multidimensional thinking: fractured planes, the rhythm of lines, textures and light as a director create a space with no sense of «someone else’s house». The interior genuinely belongs to its owner and articulates their essence.
        """,
        "time_video_button": "Person & Interior",
        "time_stat_button": "Article on Dsgners",
        "prepared_prompts_button": "Ready to use prompts 2026",
        "prompt_main_text": """<b>Ready-to-use prompts 2026:</b> <i><u>trending interior styles without any prompt engineering skills.</u></i>

Hey everyone!

We're excited to share some inspiration and exclusive prompts for instant generation of trending interiors: soft minimalism, art-deco, biophilia 2.0, japandi, plus unique RU-CN fusion styles from TimeAI!

AI creates harmonious spaces through the lens of «Human & Interior» philosophy — tailored to your personality and needs, in just seconds.

Save hours on routine work — boost your creativity!

Subscribe to timeai.ai — get free access to generations first!

Share your style ideas — we'll create a custom prompt for you!""",
        "back_button_to_prompts": """←""",
        "share_idea_button": "Share idea",
        "minimal_button": "Purity of Minimalism",
        "minimal_text": """<b>TimeAI Vision | Minimalism: </b><i><u>the art of seeing more clearly.</u></i>

Minimalism is the language of space. A clean canvas in an age of digital noise, where lines breathe, form gains clarity, and silence fills the space with meaning and air.

It is freedom, light, and inner breath. Today, minimalism is once again at its peak — when simplicity and depth meet within a single frame, freeing space and consciousness from the unnecessary. Sometimes the silence of an interior speaks louder than words, becoming an aesthetic of calm and functionality.

How do you create a space where air becomes décor, and every detail is a source of harmony?

Read about the philosophy of minimalism and the inspiration of a new generation with TimeAI, and subscribe at www.timeai.ai to be the first.
Launching soon!""",
        "minimal_designers": "Article on Dsgners",
        "minimal_dzen": "Article on Dzen",
    },
    "ru": {
        "minimal_button": "Чистота минимализма",
        "vintaaj_button": "Винтаж эпох.",
        "minimal_text": """<b>TimeAI Vision | Минимализм:</b> <i><u>искусство видеть чище.</u></i>

Минимализм — язык пространства. Чистый холст в эпоху цифрового шума, где линии дышат, форма обретает ясность, а тишина наполняет смыслом и воздухом.

Это свобода, свет и внутреннее дыхание. Сегодня минимализм снова на пике — когда простота и глубина сходятся в одном кадре, освобождая пространство и сознание от лишнего. Иногда тишина интерьера звучит громче слов, становясь эстетикой покоя и функциональности.

Как создать пространство, где воздух становится декором, а каждая деталь — источником гармонии?  

Читайте о философии минимализма и вдохновении нового поколения с TimeAI и подписывайтесь на сайте www.timeai.ai, чтобы быть первыми.
Скоро старт!""",
        "vintaaj_text": """<b>Винтаж</b> — <i><u>симбиоз не забытых эпох.</u></i>

Винтажный стиль — вечное искусство аутентичности: состаренный дуб, латунь, кружевной текстиль, эффект патины. Нейтральный фон стен оживает акцентами — антикварные комоды, граммофоны 1940-х, хрупкий фарфор, венские стулья Тонета, лепнина, гобелены…

Как выдержанное вино из старинного погреба, оно набирает аромат ностальгии: тёплой, чуть грустной, полной историй прошлого. 

Винтаж переживает тренды, сливается с современностью, добавляя уют блошиных находок и превращая дом в персональный нарратив.

TimeAI виртуозно генерирует патинированные текстуры и фьюжн: от бюджетных сокровищ до симбиоза эпох ваш интерьер обретёт узнаваемый почерк.

Скоро запуск TimeAI.
Присоединяйтесь к симбиозу винтажного творчества в современном его прочтении!""",
        "share_idea_button": "Поделиться идеей",
        "prepared_prompts_button": "Промпты 2026 — бери и твори",
        "prompt_main_text": """<b>Готовые промпты 2026:</b> <i><u>трендовые стили интерьера без навыков prompt engineering.</u></i>

Друзья!

Спешим поделиться вдохновением и эксклюзивными промптами для мгновенной генерации трендовых интерьеров: мягкий минимализм, арт-деко, биофилия 2.0, джапанди, а также уникальные RU-CN фьюжн-стили от TimeAI!

AI создаёт гармоничные пространства через призму философии «Человек & Интерьер» — под ваш характер и запрос, за секунды.

Экономьте часы на рутине — усиливайте креатив!

Подписывайтесь на timeai.ai — получите бесплатный доступ к генерациям первыми!

Делитесь идеями стилей — сделаем персональный промпт!""",
        "main_menu_title": publications.PUBLICATION_1["ru"],
        "publications_button": """О важном: статьи и публикации""",
        "publications_text": """<i>Приветствую вас!

Меня зовут Жанна Видмайер, я автор и вдохновитель проекта «TimeAI — Вселенная креатива».

Наш проект создан специально для архитекторов и дизайнеров, которые ищут не просто инструменты, а инновационные решения для воплощения самых смелых идей в интерьерном дизайне.

С TimeAI вы получаете доступ к передовым технологиям генеративного дизайна и нейросетевым инструментам. Эти решения помогут реализовать тренды будущего: биофильный дизайн, японский минимализм и крафт, ретро-фьюжн с современным акцентом, атмосферу дофаминового интерьера, а также гибкую персонализацию и актуальные тенденции дизайна.

Мы разделяем и поддерживаем ваше стремление создавать уникальные пространства, сочетая технологию и художественный подход в ритме времени.

Добро пожаловать в TimeAI — пространство, где рождается дизайн нового поколения!</i>""",
        "back_button_to_main_menu": """←""",
        "back_button_to_publications": """←""",
        "back_button_to_prompts": """←""",
        "publication_1_button": "Творчество без границ",
        "publication_2_button": "Важность нюансов",
        "publication_3_button": "Живой штрих с AI",
        "publication_4_button": "Сквозь призму искусства",
        "prompt_1_button": prompts.ALL_PROMPTS_list_ru[0],
        "prompt_2_button": prompts.ALL_PROMPTS_list_ru[1],
        "prompt_3_button": prompts.ALL_PROMPTS_list_ru[2],
        "prompt_4_button": prompts.ALL_PROMPTS_list_ru[3],
        "prompt_5_button": prompts.ALL_PROMPTS_list_ru[4],
        "prompt_6_button": prompts.ALL_PROMPTS_list_ru[5],
        "prompt_1_text": prompts.PROMPT_1["ru"],
        "prompt_2_text": prompts.PROMPT_2["ru"],
        "prompt_3_text": prompts.PROMPT_3["ru"],
        "prompt_4_text": prompts.PROMPT_4["ru"],
        "prompt_5_text": prompts.PROMPT_5["ru"],
        "prompt_6_text": prompts.PROMPT_6["ru"],
        "publication_1_text": publications.PUBLICATION_2["ru"],
        "publication_2_text": publications.PUBLICATION_3["ru"],
        "publication_3_text": publications.PUBLICATION_4["ru"],
        "publication_4_text": publications.PUBLICATION_5["ru"],
        # "publication_5_text": publications.PUBLICATION_5["ru"],
        "publications_url_text": "Открой TimeAI",
        "time_video": """
<b>Человек & Интерьер</b> <i><u>в стиле Кубизм.</u></i>

TimeAI исследует, как внутренний мир человека превращается в кубистичный интерьер. Герой со своим ритмом, характером и мечтами становится центром пространства, а нейросеть выступает тонким соавтором, собирающим личность и дом в единую визуальную историю.

Кубизм здесь — язык многогранного мышления: ломаные плоскости, ритм линий, фактуры и свет-режиссёр создают пространство, в котором нет «чужого дома». Интерьер честно принадлежит своему владельцу и формулирует его суть.

        """,
        #         TimeAI переводит человека и его внутренний мир в язык пространства. В центре всегда герой: его ритм, характер, мечты и грани, собранные в стилевом коде. Нейросеть здесь не «замена» дизайнера, а соавтор, который помогает соединить личность и дом в единую визуальную историю.
        # Представим мужчину, чей дом одновременно рационален и эмоционален, смел и сдержан, современен и укоренён в культуре. Человек & Интерьер в стиле «Кубизм» — это многогранная личность: Человек-Кубизм мыслит объёмно, видит несколько вариантов сразу, собирает смысл из деталей и ценит структуру и честность.
        # Язык его интерьера — ломаные плоскости, ритм линий, фактура материалов, свет как режиссёр и искусство как точка сборки. Здесь нет «просто дивана» или «просто стены» — есть композиции и плоскости, которые держат напряжение. Поэтому кубизм в интерьере звучит премиально: он формулирует суть.
        # Как сказал Билли Болдуин: «Самое худшее, что любой декоратор может сделать, — это дать клиенту ощущение, что он гуляет в чужом доме. Интерьеры должны принадлежать владельцу, а не быть отражением декоратора».
        # TimeAI — инструмент, который переводит человека и его внутренний мир в язык пространства. Мы выбираем героя, его ритм, характер, мечты и грани и пропускаем всё это через стилевой код: нейросеть становится не «заменой» дизайнера, а тонким соавтором, собирающим личность и дом в единую визуальную историю.
        # Представим мужчину: его дом отражает рациональное и эмоциональное, смелое и сдержанное, современное и укоренённое в культуре.
        # Человек & Интерьер в стиле «Кубизм» — это личность, которую нельзя свести к одной фразе. Кубизм показывает правду, не ломая форму: Человек-Кубизм состоит из граней, ракурсов и противоречий, которые меняют его ежесекундно. Он мыслит объёмно, видит несколько вариантов сразу, собирает смысл из деталей, ценит структуру и честность.
        # Язык его интерьера — ломаные плоскости, ритм линий, фактура материалов, свет как режиссёр и искусство как точка сборки. В таком пространстве нет «просто дивана» или «просто стены» — есть композиции и плоскости, которые держат напряжение. Поэтому кубизм в интерьере звучит премиально: он формулирует суть.
        # Как сказал Билли Болдуин, легендарный декоратор: «Самое худшее, что любой декоратор может сделать, — это дать клиенту ощущение, что он гуляет в чужом доме. Интерьеры должны принадлежать владельцу, а не быть отражением декоратора».
        "time_video_button": "Человек & Интерьер",
        "time_stat_button": "Статья на Dsgners",
        "minimal_designers": "Статья на Dsgners",
        "minimal_dzen": "Статья на Dzen",
    },
}


# async def get_publication_photo(id: str, bot: Bot):
#     print(f"!!!!misk/publication/{id}.png")
#     return


def get_text(
    key: str,
    language: str = DEFAULT_LANGUAGE,
    default_text: str = None,
    **kwargs,
) -> str:
    """
    Get text by key and language.

    Args:
        key: Text key
        language: Language code (en, ru, ar)
        kwargs: Format parameters for the text

    Returns:
        Localized text or key if text not found
    """
    # Get language dictionary, fallback to default language if not found
    lang_dict = TEXTS.get(language, TEXTS.get(DEFAULT_LANGUAGE, {}))

    # Get text by key, fallback to default language if not found
    text = lang_dict.get(key)
    if text is None and language != DEFAULT_LANGUAGE:
        text = TEXTS.get(DEFAULT_LANGUAGE, {}).get(key, key)

    # Format text with provided parameters if any
    if text and kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass  # If formatting fails, return the original text

    return text or default_text or key


def get_publications_buttons(language: str = DEFAULT_LANGUAGE):
    return [
        {
            "id": "publication_1_button",
            "name": get_text("publication_1_button", language),
        },
        {
            "id": "publication_2_button",
            "name": get_text("publication_2_button", language),
        },
        {
            "id": "publication_3_button",
            "name": get_text("publication_3_button", language),
        },
        {
            "id": "publication_4_button",
            "name": get_text("publication_4_button", language),
        },
        # {
        #     "id": "publication_5_button",
        #     "name": get_text("publication_5_button", language),
        # },
    ]


def get_publications_texts(language: str = DEFAULT_LANGUAGE):
    return [
        {
            "id": "publication_1_text",
            "name": publications.PUBLICATION_1[language],
        },
        {
            "id": "publication_2_text",
            "name": publications.PUBLICATION_2[language],
        },
        {
            "id": "publication_3_text",
            "name": publications.PUBLICATION_3[language],
        },
        {
            "id": "publication_4_text",
            "name": publications.PUBLICATION_4[language],
        },
        {
            "id": "publication_5_text",
            "name": publications.PUBLICATION_5[language],
        },
    ]


def get_prompts_buttons(language: str = DEFAULT_LANGUAGE):
    return [
        {
            "id": "prompt_1_button",
            "name": get_text("prompt_1_button", language),
        },
        {
            "id": "prompt_2_button",
            "name": get_text("prompt_2_button", language),
        },
        {
            "id": "prompt_3_button",
            "name": get_text("prompt_3_button", language),
        },
        {
            "id": "prompt_4_button",
            "name": get_text("prompt_4_button", language),
        },
        {
            "id": "prompt_5_button",
            "name": get_text("prompt_5_button", language),
        },
        {
            "id": "prompt_6_button",
            "name": get_text("prompt_6_button", language),
        },
    ]


def get_prompts_texts(language: str = DEFAULT_LANGUAGE):
    return [
        {
            "id": "prompt_1_text",
            "name": prompts.PROMPT_1[language],
        },
        {
            "id": "prompt_2_text",
            "name": prompts.PROMPT_2[language],
        },
        {
            "id": "prompt_3_text",
            "name": prompts.PROMPT_3[language],
        },
        {
            "id": "prompt_4_text",
            "name": prompts.PROMPT_4[language],
        },
        {
            "id": "prompt_5_text",
            "name": prompts.PROMPT_5[language],
        },
        {
            "id": "prompt_6_text",
            "name": prompts.PROMPT_6[language],
        },
    ]
