import re
from langdetect import detect
from nltk.corpus import stopwords
import spacy
import unicodedata

# Descargar modelos si no están cargados
try:
    nlp_en = spacy.load("en_core_web_sm")
except:
    spacy.cli.download("en_core_web_sm")
    nlp_en = spacy.load("en_core_web_sm")

try:
    nlp_es = spacy.load("es_core_news_sm")
except:
    spacy.cli.download("es_core_news_sm")
    nlp_es = spacy.load("es_core_news_sm")

# Cargar stopwords
stopwords_en = set(stopwords.words('english'))
stopwords_es = set(stopwords.words('spanish'))

def detect_language(text: str) -> str:
    """Detecta el idioma del texto (en o es)."""
    try:
        lang = detect(text)
        if lang not in ['es', 'en']:
            return 'en'  # fallback en caso de no reconocer el lenguaje
        return lang
    except:
        return 'en'

def preprocess_text(text: str) -> str:
    """Preprocesa texto en inglés o español para embeddings."""
    lang = detect_language(text)
    nlp = nlp_en if lang == 'en' else nlp_es
    stops = stopwords_en if lang == 'en' else stopwords_es

    # Limpieza básica
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)  # quitar puntuación
    text = re.sub(r'\s+', ' ', text).strip()

    # Procesamiento NLP
    doc = nlp(text)
    tokens = [
        token.lemma_ for token in doc
        if token.lemma_ not in stops and not token.is_punct and not token.is_space
    ]

    return ' '.join(tokens)

def preprocess_bulk(texts: list[str]) -> list[str]:
    """Preprocesa una lista de textos."""
    return [preprocess_text(t) for t in texts]

def normalize(name):
    # Quitar tildes, pasar a minúsculas, reemplazar espacios y otros caracteres
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("utf-8")
    return name.strip().lower().replace(" ", "_").replace("-", "_").replace(".", "").replace("/", "_")
