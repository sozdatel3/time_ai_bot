from texts import publications

"""
Simple text localization system.
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
        # "publication_5_text": publications.PUBLICATION_5["en"],
        "publications_url_text": "Open TimeAI",
        "time_video": """
<b>Human & Interior</b> <i><u>in the style of Cubism.</u></i>

TimeAI explores how a person’s inner world transforms into a cubist interior. The protagonist, with their own rhythm, character and dreams, becomes the focal point of the space, while the neural network acts as a subtle co-author, bringing together the person and the home into a single visual story.

Here, Cubism is the language of multidimensional thinking: fractured planes, the rhythm of lines, textures and light as a director create a space with no sense of «someone else’s house». The interior genuinely belongs to its owner and articulates their essence."
        """,
        "time_video_button": "Person & Interior",
        "time_stat_button": "Article on Dsgners",
    },
    "ru": {
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
        "publication_1_button": "Творчество без границ",
        "publication_2_button": "Важность нюансов",
        "publication_3_button": "Живой штрих с AI",
        "publication_4_button": "Сквозь призму искусства",
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
