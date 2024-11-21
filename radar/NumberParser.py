from natasha import Segmenter, MorphVocab, NewsEmbedding, NewsSyntaxParser, Doc
import pymorphy2

segmenter = Segmenter()
morph_vocab = MorphVocab()
emb = NewsEmbedding()
syntax_parser = NewsSyntaxParser(emb)

morph = pymorphy2.MorphAnalyzer()


NUM_WORDS = {
    "ноль": 0,
    "один": 1, "одна": 1,
    "два": 2, "две": 2,
    "три": 3,
    "четыре": 4,
    "пять": 5,
    "шесть": 6,
    "семь": 7,
    "восемь": 8,
    "девять": 9,
    "десять": 10,
    "одиннадцать": 11,
    "двенадцать": 12,
    "тринадцать": 13,
    "четырнадцать": 14,
    "пятнадцать": 15,
    "шестнадцать": 16,
    "семнадцать": 17,
    "восемнадцать": 18,
    "девятнадцать": 19,
    "двадцать": 20,
    "тридцать": 30,
    "сорок": 40,
    "пятьдесят": 50,
    "шестьдесят": 60,
    "семьдесят": 70,
    "восемьдесят": 80,
    "девяносто": 90,
    "сто": 100,
    "двести": 200,
    "триста": 300,
    "четыреста": 400,
    "пятьсот": 500,
    "шестьсот": 600,
    "семьсот": 700,
    "восемьсот": 800,
    "девятьсот": 900,
    "тысяча": 1000,
    "миллион": 1_000_000,
    "миллиард": 1_000_000_000
}


def words_to_number(words):
    total = 0
    current = 0
    for word in words:
        word = morph.parse(word)[0].normal_form
        if word in NUM_WORDS:
            value = NUM_WORDS[word]
            if value >= 1000:
                current *= value
            elif value >= 100:
                current += value
            else:
                current += value
        elif word == "и":
            continue
        else:
            total += current
            current = 0
    return total + current


def convert_numbers_in_text(text):
    doc = Doc(text)
    doc.segment(segmenter)
    doc.parse_syntax(syntax_parser)

    tokens = [_.text for _ in doc.tokens]
    result_text = text
    current_chunk = []
    chunks = []

    for token in tokens:
        word_normal = morph.parse(token)[0].normal_form
        if word_normal in NUM_WORDS or token.lower() == "и":
            current_chunk.append(token)
        else:
            if current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
    if current_chunk:
        chunks.append(" ".join(current_chunk))

    for chunk in chunks:
        number = words_to_number(chunk.split())
        result_text = result_text.replace(chunk, str(number))

    return result_text