from dataclasses import dataclass

from bs4 import BeautifulSoup
import json

codex_fb2_path = "/home/sb/projects/civil_codex_gc/garant_grajdansky_kodeks_rf.fb2"
codex_name = "Гражданский кодекс Российской Федерации"
paths_rus = {
    "нуля": 0,
    "первая": 1,
    "вторая": 2,
    "третья": 3,
    "четвертая": 4,
}
max_chunk_size: int = 8192
"""
Кодекс
Часть
Раздел
Подраздел
Глава
Статья 
Пункт
"""


def roman_to_int(roman_numeral):
    """Римские цифра в нормальный инт."""
    roman_dict = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    result = 0
    prev_value = 0

    for numeral in roman_numeral[::-1]:
        value = roman_dict[numeral]

        if value < prev_value:
            result -= value
        else:
            result += value

        prev_value = value

    return result


def get_point_num(s: str):
    """Попытаемся получить номер пункта."""
    try:
        dot = str(s).index(".")
    except ValueError:
        return None
    point_str = str(s[:dot]).strip()

    try:
        return int(point_str)
    except ValueError:
        return None


def remove_point_num(s: str, point_num: int):
    """Удаляем номер пункта из строки."""
    s = s.replace(str(point_num) + ". ", "")
    s = s.strip()
    return s


def get_full_article_text(section) -> str:
    """Получить полную статью из секции."""
    s = ""
    for p in section.find_all("p"):
        if p is None:
            continue
        if p.text.startswith("Статья "):
            # Может попасть title
            continue
        s = s + str(p.text).strip()
    return s


def get_article_by_point(section) -> list:
    """Слишком большая статья. Берем по пунктам."""
    """
                        item["Point"],
                    item["Text"],
                    
                    """
    result: list = []
    Point: int = 0
    Text: str = ""
    text_len: int = 0
    for p in section.find_all("p"):
        if p is None:
            continue
        if p.text.startswith("Статья"):
            # Может попасть title
            continue
        paragraf_text = str(p.text).strip()
        Text = Text + str(p.text)
        text_len = len(Text)
        paragraf_text_len = len(paragraf_text)
        if (text_len + paragraf_text_len) > max_chunk_size:
            obj = {
                "Point": Point,
                "Text": Text,
            }
            Text = ""
            result.append(obj)

    return result


@dataclass(init=True, frozen=True)
class CodexRecord:
    CodexName: str
    Part: int
    Section: int
    SectionTitle: str
    Subsection: int
    SubsectionTitle: str
    Chapter: float
    ChapterTitle: str
    Article: int
    ArticleTitle: str
    Point: int
    Text: str

    def __str__(self):
        return (
            f"{self.CodexName};{self.Part};{self.Section};{self.SectionTitle};"
            f"{self.Subsection};{self.SubsectionTitle};{self.Chapter};{self.ChapterTitle};"
            f"{self.Article};{self.ArticleTitle};{self.Point};{self.Text}"
        )

    def __dict__(self):
        return {
            "codex_name": f"{self.CodexName}",
            "part": f"{self.Part}",
            "section": f"{self.Section}",
            "section_title": f"{self.SectionTitle}",
            "subsection": f"{self.Subsection}",
            "subsection_title": f"{self.SubsectionTitle}",
            "chapter": f"{self.Chapter}",
            "chapter_title": f"{self.ChapterTitle}",
            "article": f"{self.Article}",
            "article_title": f"{self.ArticleTitle}",
            "point": f"{self.Point}",
            "text": f"{self.Text}",
        }


def search_for_dot(text) -> int | None:
    """Получение номера статьи."""
    try:
        dot = text.index(". ")
        offset_dot = 2
        return dot, offset_dot
    except ValueError:
        pass
    try:
        dot = str(text).index("-1.")
        offset_dot = 3
        return dot, offset_dot
    except ValueError:
        pass
    try:
        dot = str(text).index("-2.")
        offset_dot = 3
        return dot, offset_dot
    except ValueError:
        pass
    try:
        dot = str(text).index("-3.")
        offset_dot = 3
        return dot, offset_dot
    except ValueError:
        pass
    try:
        dot = str(text).index("-4.")
        offset_dot = 3
        return dot, offset_dot
    except ValueError:
        pass
    try:
        dot = str(text).index(".")
        offset_dot = 1
        return dot, offset_dot
    except ValueError:
        pass
    return None


def to_acticle_num(ArticleSRC) -> float:
    """
    Преобразование в число с плавающей точкой.
    Проблема в том что в исходном тексте есть странные номера статей типа 123.7-1
    """
    ArticleSRC = ArticleSRC.replace("-", "00")
    return float(ArticleSRC)


def main():
    CodexName: str = ""
    Part = 0
    Section = 0
    SectionTitle = ""
    Subsection = 0
    SubsectionTitle = ""
    Chapter = 0.0
    ChapterTitle = ""
    Article = 0
    ArticleTitle = ""
    Point = 0
    result: list = []
    fp = open(codex_fb2_path)
    soup = BeautifulSoup(fp, 'html.parser')
    body = soup.find("body")
    count = 0
    big_article_count = 0
    should_exit = False
    MaxArticleLen = 0
    MinActicelLen = 0
    for section in body.find_all("section"):
        Text = ""
        # print("--------------------------")
        # print(section)

        title = section.find("title")
        if title is None:
            continue
        text = title.text
        if text.startswith("Часть"):
            Part = paths_rus[text[6:]]
            continue
        if text.startswith("Раздел"):
            dot = str(text).index(".")
            Section = roman_to_int(str(text[7:dot]).strip())
            SectionTitle = str(text[dot + 1:]).strip()
            Subsection = 0
            SubsectionTitle = ""
            continue
        if text.startswith("Подраздел"):
            dot = str(text).index(".")
            Subsection = int(str(text[10:dot]).strip())
            SubsectionTitle = str(text[dot + 1:]).strip()
            continue
        if text.startswith("Глава"): # §
            dot = str(text).index(".")
            Chapter = float(str(text[6:dot]).strip())
            ChapterTitle = str(text[dot + 1:]).strip()
            continue
        if text.startswith("§ "):
            dot = str(text).index(".")
            value = float(str(text[2:dot]).strip()) / 10
            Chapter = Chapter + value
            continue
        if Part == 4 and Section == 7 and Subsection == 2 and Chapter == 77.0:
            break
        if Part < 1 and Section < 1 and Subsection < 1 and Chapter < 1.0:
            continue
        if text.startswith("Статья"):
            dot, offset_dot = search_for_dot(str(text))
            ArticleSRC = str(text[7:dot]).strip()
            Article = to_acticle_num(ArticleSRC)
            ArticleTitle = str(text[dot + offset_dot:]).strip()
            Point = 0
            if ArticleTitle.startswith("1."):
                ArticleTitle = ArticleTitle.replace("1. ", "")
                Point = 0
                # Text: str
        if ArticleTitle.startswith("Утратила силу"):
            continue
        # print(
        #    f"{codex_name};{Part};{Section};{SectionTitle};{Subsection};{SubsectionTitle};"
        #    f"{Chapter};{ChapterTitle};{Article};{ArticleTitle};"
        #    f"{Point};{Text}"
        # )
        count = count + 1
        Text = ""
        Point = 9999
        Text = get_full_article_text(section)
        text_len = len(Text)
        if text_len >= max_chunk_size:
            big_article_count = big_article_count + 1
            points = get_article_by_point(section)
            print(big_article_count,Article, Text[:200], text_len)
            Point = 9999
            for point in points:
                obj = CodexRecord(
                    codex_name,
                    Part,
                    Section,
                    SectionTitle,
                    Subsection,
                    SubsectionTitle,
                    Chapter,
                    ChapterTitle,
                    Article,
                    ArticleTitle,
                    Point,
                    point["Text"],
                )
                result.append(obj.__dict__())
        else:
            obj = CodexRecord(
                codex_name,
                Part,
                Section,
                SectionTitle,
                Subsection,
                SubsectionTitle,
                Chapter,
                ChapterTitle,
                Article,
                ArticleTitle,
                Point,
                Text,
            )
            result.append(obj.__dict__())
        if should_exit:
            break
        text_len = len(Text)
        if MaxArticleLen < text_len:
            MaxArticleLen = text_len
        if MinActicelLen > text_len:
            MinActicelLen = text_len

    fp.close()
    fh = open("result.json", "w", encoding="utf-8")
    json.dump(result, fh, ensure_ascii=False, indent=4)
    fh.close()
    print(f"MinActicelLen:{MinActicelLen} MaxArticleLen:{MaxArticleLen} ")
    print(f"big_article_count:{big_article_count} count: {count}")


if __name__ == '__main__':
    main()

