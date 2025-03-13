from flask import Flask, render_template, request, jsonify
import requests
import os
import json
import re
import unicodedata
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# Hugging Face API configuration
HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")
hf_client = InferenceClient(token=HUGGINGFACE_API_KEY)

# TMDb API configuration
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"

# Función para normalizar texto (eliminar acentos y convertir a minúsculas)
def normalize_text(text):
    # Convertir a minúsculas
    text = text.lower()
    # Eliminar acentos
    text = ''.join(c for c in unicodedata.normalize('NFD', text)
                  if unicodedata.category(c) != 'Mn')
    return text

# Genre ID mapping for TMDb
GENRE_MAP = {
    # Géneros en inglés
    "action": 28, "adventure": 12, "animation": 16, "comedy": 35,
    "crime": 80, "documentary": 99, "drama": 18, "family": 10751,
    "fantasy": 14, "history": 36, "horror": 27, "music": 10402,
    "mystery": 9648, "romance": 10749, "science fiction": 878, "sci-fi": 878,
    "tv movie": 10770, "thriller": 53, "war": 10752, "western": 37,
    # Géneros en español con acentos
    "acción": 28, "aventura": 12, "animación": 16, "comedia": 35,
    "crimen": 80, "documental": 99, "drama": 18, "familiar": 10751,
    "fantasía": 14, "historia": 36, "terror": 27, "música": 10402,
    "misterio": 9648, "romance": 10749, "ciencia ficción": 878, 
    "película de tv": 10770, "suspenso": 53, "guerra": 10752, "oeste": 37,
    # Géneros en español sin acentos
    "accion": 28, "animacion": 16, "fantasia": 14, "musica": 10402,
    "pelicula de tv": 10770
}

# Palabras clave normalizadas (sin acentos)
ERA_KEYWORDS = {
    "recent": ["reciente", "nueva", "ultimo", "moderna", "actual", "nuevas", "ultimos", "modernas", "actuales"],
    "classic": ["clasica", "vieja", "antigua", "retro", "vintage", "clasicas", "viejas", "antiguas"]
}

POPULARITY_KEYWORDS = {
    "popular": ["popular", "famosa", "conocida", "taquillera", "populares", "famosas", "conocidas", "taquilleras"],
    "hidden_gems": ["oculta", "desconocida", "indie", "independiente", "joya", "ocultas", "desconocidas", "indies", "independientes", "joyas"]
}

# Palabras clave para respuestas afirmativas/negativas
AFFIRMATIVE_KEYWORDS = ["si", "sí", "claro", "por supuesto", "dale", "ok", "okay", "vale", "bueno", "genial", "perfecto"]
NEGATIVE_KEYWORDS = ["no", "nope", "negativo", "paso", "mejor no", "ahora no", "en otro momento"]

# Respuestas de respaldo en caso de que la API falle
FALLBACK_RESPONSES = {
    "welcome": "¡Hola! ¿Qué tipo de película te gustaría ver hoy? Puedes mencionar géneros, directores, actores o años.",
    "genre_followup": {
        "action": "¡Genial! ¿Prefieres películas de acción con superhéroes, espías o artes marciales?",
        "comedy": "¡Buena elección! ¿Te gustan más las comedias románticas, las comedias de situación o el humor negro?",
        "horror": "¡Interesante! ¿Prefieres el terror psicológico, el gore o las películas de fantasmas?",
        "sci-fi": "¡Excelente! ¿Te interesan más las películas de ciencia ficción sobre el espacio, viajes en el tiempo o distopías?",
        "drama": "¡Buena elección! ¿Prefieres dramas históricos, familiares o románticos?",
        "default": "¡Buena elección! ¿Hay algún actor o director que te guste especialmente?"
    },
    "era_question": "¿Prefieres películas recientes o clásicas?",
    "popularity_question": "¿Te interesan más las películas populares o prefieres descubrir joyas ocultas?",
    "recommendation_prompt": "Basado en tus preferencias, creo que puedo recomendarte algunas películas interesantes. ¿Quieres ver mis recomendaciones?",
    "no_preferences": "Parece que no he entendido bien tus preferencias. ¿Podrías decirme qué género de películas te gusta? (Acción, Comedia, Terror, etc.)",
    "fallback": "Lo siento, no entendí eso. ¿Podrías reformular tu pregunta o decirme qué tipo de películas te gustan?"
}

# Palabras clave para detectar solicitudes de recomendación (normalizadas)
RECOMMENDATION_KEYWORDS = [
    "recomienda", "recomendame", "recomiendame", "recomendaciones", 
    "muestra", "busca", "dame", "quiero", "ver", "peliculas", "film"
]

# Directores y actores famosos para detectar preferencias
FAMOUS_PEOPLE = {
    "tarantino": {"genre": "crime", "director": "Quentin Tarantino"},
    "spielberg": {"genre": "adventure", "director": "Steven Spielberg"},
    "nolan": {"genre": "sci-fi", "director": "Christopher Nolan"},
    "scorsese": {"genre": "crime", "director": "Martin Scorsese"},
    "kubrick": {"genre": "drama", "director": "Stanley Kubrick"},
    "hitchcock": {"genre": "thriller", "director": "Alfred Hitchcock"},
    "dicaprio": {"genre": "drama", "actor": "Leonardo DiCaprio"},
    "pitt": {"genre": "drama", "actor": "Brad Pitt"},
    "hanks": {"genre": "drama", "actor": "Tom Hanks"},
    "johansson": {"genre": "action", "actor": "Scarlett Johansson"},
    "lawrence": {"genre": "drama", "actor": "Jennifer Lawrence"},
    "depp": {"genre": "fantasy", "actor": "Johnny Depp"},
    "almodovar": {"genre": "drama", "director": "Pedro Almodóvar"},
    "banderas": {"genre": "drama", "actor": "Antonio Banderas"},
    "penelope cruz": {"genre": "drama", "actor": "Penélope Cruz"},
    "bardem": {"genre": "drama", "actor": "Javier Bardem"},
    "del toro": {"genre": "fantasy", "director": "Guillermo del Toro"},
    "cuaron": {"genre": "drama", "director": "Alfonso Cuarón"},
    "iñarritu": {"genre": "drama", "director": "Alejandro González Iñárritu"},
    "darin": {"genre": "drama", "actor": "Ricardo Darín"}
}

# Décadas para detectar preferencias de época
DECADES = {
    "50s": {"start_year": "1950", "end_year": "1959"},
    "60s": {"start_year": "1960", "end_year": "1969"},
    "70s": {"start_year": "1970", "end_year": "1979"},
    "80s": {"start_year": "1980", "end_year": "1989"},
    "90s": {"start_year": "1990", "end_year": "1999"},
    "2000s": {"start_year": "2000", "end_year": "2009"},
    "2010s": {"start_year": "2010", "end_year": "2019"},
    "2020s": {"start_year": "2020", "end_year": "2029"}
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '').strip()
    chat_history = data.get('history', [])

    if not user_message:
        return jsonify({"error": "El mensaje no puede estar vacío"}), 400

    chat_history.append({"role": "user", "content": user_message})
    
    # Normalizar el mensaje del usuario para comparaciones
    user_message_normalized = normalize_text(user_message)
    
    # Verificar si es una respuesta afirmativa a una pregunta de recomendación
    if is_affirmative_response(user_message_normalized) and should_recommend_based_on_context(chat_history):
        # Extraer preferencias del historial de chat
        preferences = extract_preferences(chat_history)
        
        # Obtener recomendaciones de películas
        movies = get_movie_recommendations(preferences)
        
        if movies:
            response = format_movie_recommendations(movies)
        else:
            response = "No encontré películas que coincidan con tus preferencias. ¿Te gustaría intentar con otros géneros?"
    
    # Verificar si es una respuesta negativa a una pregunta de recomendación
    elif is_negative_response(user_message_normalized) and should_recommend_based_on_context(chat_history):
        response = "Entiendo. ¿Hay algún otro tipo de película que te interese? Puedes mencionar géneros, directores, actores o años específicos."
    
    # Verificar si se mencionó a un director, actor o década específica
    elif has_specific_criteria(user_message_normalized):
        # Extraer preferencias específicas
        preferences = extract_specific_preferences(user_message_normalized)
        
        # Confirmar las preferencias detectadas
        response = confirm_preferences(preferences)
    
    # Verificar si se requieren recomendaciones de películas explícitamente
    elif any(kw in user_message_normalized for kw in RECOMMENDATION_KEYWORDS):
        # Extraer preferencias del historial de chat
        preferences = extract_preferences(chat_history)
        
        # Obtener recomendaciones de películas
        movies = get_movie_recommendations(preferences)
        
        if movies:
            response = format_movie_recommendations(movies)
        else:
            response = "No encontré películas que coincidan con tus preferencias. ¿Te gustaría intentar con otros géneros?"
    else:
        # Verificar si el mensaje es una respuesta a una pregunta sobre era
        if is_era_response(user_message_normalized):
            response = FALLBACK_RESPONSES["popularity_question"]
        # Verificar si el mensaje es una respuesta a una pregunta sobre popularidad
        elif is_popularity_response(user_message_normalized):
            response = FALLBACK_RESPONSES["recommendation_prompt"]
        else:
            # Generar respuesta conversacional
            response = generate_ai_response(chat_history)
            
            # Verificar si la respuesta está truncada y arreglarla
            if len(response) > 10 and not response.endswith((".", "!", "?")):
                # La respuesta parece estar truncada, usar una respuesta más corta y controlada
                response = generate_fallback_response(chat_history)

    chat_history.append({"role": "assistant", "content": response})
    
    return jsonify({"response": response, "history": chat_history})

def is_affirmative_response(normalized_message):
    """Detecta si el mensaje es una respuesta afirmativa."""
    return any(keyword == normalized_message or keyword in normalized_message.split() for keyword in AFFIRMATIVE_KEYWORDS)

def is_negative_response(normalized_message):
    """Detecta si el mensaje es una respuesta negativa."""
    return any(keyword == normalized_message or keyword in normalized_message.split() for keyword in NEGATIVE_KEYWORDS)

def should_recommend_based_on_context(chat_history):
    """Determina si el contexto de la conversación sugiere que se deben mostrar recomendaciones."""
    if len(chat_history) < 2:
        return False
    
    # Verificar si el último mensaje del asistente sugiere recomendaciones
    last_assistant_messages = [msg["content"] for msg in chat_history if msg["role"] == "assistant"]
    if not last_assistant_messages:
        return False
    
    last_assistant_message = normalize_text(last_assistant_messages[-1])
    
    # Buscar frases que sugieran que el asistente está listo para recomendar
    recommendation_phrases = [
        "quieres ver mis recomendaciones",
        "te muestro algunas opciones",
        "te recomiendo",
        "puedo recomendarte",
        "te gustaria ver"
    ]
    
    return any(phrase in last_assistant_message for phrase in recommendation_phrases)

def has_specific_criteria(normalized_message):
    """Detecta si el mensaje contiene criterios específicos como director, actor o década."""
    # Verificar si se menciona a un director o actor
    for person in FAMOUS_PEOPLE.keys():
        if person in normalized_message:
            return True
    
    # Verificar si se menciona una década
    for decade in DECADES.keys():
        if decade in normalized_message:
            return True
    
    # Verificar si se menciona un año específico (formato: 4 dígitos)
    year_pattern = r'\b(19\d{2}|20\d{2})\b'
    if re.search(year_pattern, normalized_message):
        return True
    
    return False

def extract_specific_preferences(normalized_message):
    """Extrae preferencias específicas del mensaje del usuario."""
    preferences = {
        "genre": None,
        "director": None,
        "actor": None,
        "year_from": None,
        "year_to": None
    }
    
    # Detectar director o actor
    for person, info in FAMOUS_PEOPLE.items():
        if person in normalized_message:
            if "director" in info:
                preferences["director"] = info["director"]
            elif "actor" in info:
                preferences["actor"] = info["actor"]
            
            # También asignar el género asociado
            preferences["genre"] = info.get("genre")
            break
    
    # Detectar década
    for decade, years in DECADES.items():
        if decade in normalized_message:
            preferences["year_from"] = years["start_year"]
            preferences["year_to"] = years["end_year"]
            break
    
    # Detectar año específico
    year_pattern = r'\b(19\d{2}|20\d{2})\b'
    year_match = re.search(year_pattern, normalized_message)
    if year_match:
        specific_year = year_match.group(1)
        preferences["year_from"] = specific_year
        preferences["year_to"] = specific_year
    
    # Detectar género
    if not preferences["genre"]:
        for genre in GENRE_MAP.keys():
            normalized_genre = normalize_text(genre)
            if normalized_genre in normalized_message:
                preferences["genre"] = genre
                break
    
    return preferences

def confirm_preferences(preferences):
    """Genera un mensaje de confirmación basado en las preferencias detectadas."""
    confirmation = "Entiendo que te interesan "
    
    criteria = []
    
    if preferences["genre"]:
        criteria.append(f"películas de {preferences['genre']}")
    
    if preferences["director"]:
        criteria.append(f"dirigidas por {preferences['director']}")
    
    if preferences["actor"]:
        criteria.append(f"protagonizadas por {preferences['actor']}")
    
    if preferences["year_from"] and preferences["year_to"]:
        if preferences["year_from"] == preferences["year_to"]:
            criteria.append(f"del año {preferences['year_from']}")
        else:
            criteria.append(f"entre {preferences['year_from']} y {preferences['year_to']}")
    
    if not criteria:
        return FALLBACK_RESPONSES["no_preferences"]
    
    confirmation += ", ".join(criteria[:-1])
    if len(criteria) > 1:
        confirmation += f" y {criteria[-1]}"
    else:
        confirmation += criteria[0]
    
    confirmation += ". ¿Quieres ver algunas recomendaciones basadas en estos criterios?"
    
    return confirmation

def is_era_response(normalized_message):
    """Detecta si el mensaje es una respuesta sobre la era de las películas."""
    for era, keywords in ERA_KEYWORDS.items():
        if any(keyword in normalized_message for keyword in keywords):
            return True
    return False

def is_popularity_response(normalized_message):
    """Detecta si el mensaje es una respuesta sobre la popularidad de las películas."""
    for popularity, keywords in POPULARITY_KEYWORDS.items():
        if any(keyword in normalized_message for keyword in keywords):
            return True
    return False

def extract_preferences(chat_history):
    """Extract movie preferences from chat history."""
    # Método de respaldo para extraer preferencias
    preferences = {
        "genre": None,
        "director": None,
        "actor": None,
        "year_from": None,
        "year_to": None,
        "era": "any",
        "popularity": "any"
    }
    
    # Combinar todos los mensajes del usuario y normalizar
    user_messages = " ".join(msg["content"] for msg in chat_history if msg["role"] == "user")
    user_messages_normalized = normalize_text(user_messages)
    
    # Detectar menciones de personas famosas
    for person, info in FAMOUS_PEOPLE.items():
        if person in user_messages_normalized:
            if "director" in info:
                preferences["director"] = info["director"]
            elif "actor" in info:
                preferences["actor"] = info["actor"]
            
            # También asignar el género asociado
            preferences["genre"] = info.get("genre")
            break
    
    # Detectar década o año específico
    for decade, years in DECADES.items():
        if decade in user_messages_normalized:
            preferences["year_from"] = years["start_year"]
            preferences["year_to"] = years["end_year"]
            break
    
    # Detectar año específico
    year_pattern = r'\b(19\d{2}|20\d{2})\b'
    year_matches = re.findall(year_pattern, user_messages_normalized)
    if year_matches:
        # Si hay múltiples años, usar el rango
        if len(year_matches) > 1:
            years = sorted([int(y) for y in year_matches])
            preferences["year_from"] = str(years[0])
            preferences["year_to"] = str(years[-1])
        else:
            specific_year = year_matches[0]
            preferences["year_from"] = specific_year
            preferences["year_to"] = specific_year
    
    # Detectar género
    if not preferences["genre"]:
        for genre, genre_id in GENRE_MAP.items():
            normalized_genre = normalize_text(genre)
            if normalized_genre in user_messages_normalized:
                preferences["genre"] = genre
                break
    
    # Si no se detectó ningún género, usar "action" como predeterminado
    if not preferences["genre"]:
        preferences["genre"] = "action"
    
    # Detectar era
    for era, keywords in ERA_KEYWORDS.items():
        if any(keyword in user_messages_normalized for keyword in keywords):
            preferences["era"] = era
            break
    
    # Detectar popularidad
    for popularity, keywords in POPULARITY_KEYWORDS.items():
        if any(keyword in user_messages_normalized for keyword in keywords):
            preferences["popularity"] = popularity
            break
    
    return preferences

def generate_ai_response(chat_history):
    """Generate a conversational response using Hugging Face."""
    try:
        # Obtener el último mensaje del usuario y normalizarlo
        user_message = chat_history[-1]["content"]
        user_message_normalized = normalize_text(user_message)
        
        # Detectar género mencionado
        detected_genre = None
        for genre in GENRE_MAP.keys():
            normalized_genre = normalize_text(genre)
            if normalized_genre in user_message_normalized:
                detected_genre = genre
                break
        
        # Si se detectó un género, usar respuesta predefinida
        if detected_genre:
            # Buscar el género en las respuestas predefinidas
            for key in FALLBACK_RESPONSES["genre_followup"].keys():
                if normalize_text(key) == normalize_text(detected_genre):
                    return FALLBACK_RESPONSES["genre_followup"][key]
            
            # Si no se encuentra una respuesta específica, usar la respuesta predeterminada
            return FALLBACK_RESPONSES["genre_followup"]["default"]
        
        # Verificar si es una respuesta sobre era
        if is_era_response(user_message_normalized):
            return FALLBACK_RESPONSES["popularity_question"]
        
        # Verificar si es una respuesta sobre popularidad
        if is_popularity_response(user_message_normalized):
            return FALLBACK_RESPONSES["recommendation_prompt"]
        
        # Si el mensaje es corto y simple, usar respuestas predefinidas
        if len(user_message.split()) <= 3:
            return generate_fallback_response(chat_history)
        
        # Para mensajes más complejos, usar Hugging Face
        formatted_chat = []
        for msg in chat_history[-3:]:  # Usar solo los últimos 3 mensajes para mantener el contexto manejable
            role = "user" if msg["role"] == "user" else "assistant"
            formatted_chat.append(f"<{role}>: {msg['content']}")
        
        system_prompt = """
        Eres un asistente de recomendación de películas amigable y conversacional.
        Tu objetivo es ayudar al usuario a encontrar películas que le gusten haciendo preguntas sobre sus preferencias.
        
        Puedes preguntar sobre géneros, directores, actores, años o décadas específicas.
        Mantén un tono amigable y conversacional. Usa español en todo momento.
        Mantén tus respuestas breves y concisas, no más de 2-3 oraciones.
        
        Cuando tengas suficiente información, pregunta al usuario si quiere ver recomendaciones.
        No le pidas que escriba "recomiéndame películas", simplemente pregúntale si quiere ver tus recomendaciones.
        """
        
        prompt = f"{system_prompt}\n\n{''.join(formatted_chat)}\n<assistant>:"
        
        # Generar respuesta con Hugging Face
        response = hf_client.text_generation(
            prompt,
            model="mistralai/Mistral-7B-Instruct-v0.2",
            max_new_tokens=100,  # Limitar la longitud para evitar respuestas truncadas
            temperature=0.7,
            repetition_penalty=1.2
        )
        
        # Limpiar la respuesta
        response = response.strip()
        if response.startswith("<assistant>:"):
            response = response[len("<assistant>:"):].strip()
        
        # Asegurarse de que la respuesta termine con un signo de puntuación
        if response and not response[-1] in ['.', '!', '?']:
            # Buscar el último signo de puntuación y cortar ahí
            last_period = max(response.rfind('.'), response.rfind('!'), response.rfind('?'))
            if last_period > len(response) // 2:  # Solo cortar si el signo está en la segunda mitad
                response = response[:last_period+1]
            else:
                response += "."
        
        return response
    
    except Exception as e:
        print(f"Error generating response with Hugging Face: {e}")
        return generate_fallback_response(chat_history)

def generate_fallback_response(chat_history):
    """Generar respuesta de respaldo cuando la API falla."""
    user_message = chat_history[-1]["content"]
    user_message_normalized = normalize_text(user_message)
    
    # Si es el primer mensaje del usuario
    if len(chat_history) <= 1:
        return FALLBACK_RESPONSES["welcome"]
    
    # Detectar género mencionado
    detected_genre = None
    for genre in GENRE_MAP.keys():
        normalized_genre = normalize_text(genre)
        if normalized_genre in user_message_normalized:
            detected_genre = genre
            break
    
    # Si se detectó un género
    if detected_genre:
        # Buscar el género en las respuestas predefinidas
        for key in FALLBACK_RESPONSES["genre_followup"].keys():
            if normalize_text(key) == normalize_text(detected_genre):
                return FALLBACK_RESPONSES["genre_followup"][key]
        
        # Si no se encuentra una respuesta específica, usar la respuesta predeterminada
        return FALLBACK_RESPONSES["genre_followup"]["default"]
    
    # Verificar si es una respuesta sobre era
    if is_era_response(user_message_normalized):
        return FALLBACK_RESPONSES["popularity_question"]
    
    # Verificar si es una respuesta sobre popularidad
    if is_popularity_response(user_message_normalized):
        return FALLBACK_RESPONSES["recommendation_prompt"]
    
    # Si no se entiende la respuesta
    return FALLBACK_RESPONSES["fallback"]

def get_movie_recommendations(preferences):
    """Get movie recommendations from TMDb based on preferences."""
    if not TMDB_API_KEY:
        return []

    # Parámetros base para la API
    params = {
        "api_key": TMDB_API_KEY,
        "language": "es-ES",
        "sort_by": "popularity.desc",
        "include_adult": "false",
        "page": 1
    }

    # Añadir filtro de género si está disponible
    if preferences.get("genre"):
        genre = preferences["genre"].lower()
        genre_id = None
        for g, gid in GENRE_MAP.items():
            if normalize_text(g) == normalize_text(genre):
                genre_id = gid
                break
        
        if genre_id:
            params["with_genres"] = genre_id
    
    # Añadir filtro de año si está disponible
    if preferences.get("year_from") and preferences.get("year_to"):
        params["primary_release_date.gte"] = f"{preferences['year_from']}-01-01"
        params["primary_release_date.lte"] = f"{preferences['year_to']}-12-31"
    elif preferences.get("era") == "recent":
        params["primary_release_date.gte"] = "2015-01-01"
    elif preferences.get("era") == "classic":
        params["primary_release_date.lte"] = "2000-12-31"
    
    # Ajustar ordenamiento según popularidad
    if preferences.get("popularity") == "hidden_gems":
        params.update({
            "sort_by": "vote_average.desc",
            "vote_count.gte": "50",
            "vote_count.lte": "1000",
            "vote_average.gte": "7"
        })
    
    # Buscar por director o actor si está disponible
    person_id = None
    if preferences.get("director"):
        person_info = get_person_id(preferences["director"])
        if person_info:
            person_id = person_info["id"]
    elif preferences.get("actor"):
        person_info = get_person_id(preferences["actor"])
        if person_info:
            person_id = person_info["id"]
    
    if person_id:
        params["with_people"] = person_id

    try:
        # Realizar la búsqueda
        response = requests.get(f"{TMDB_BASE_URL}/discover/movie", params=params)
        response.raise_for_status()
        results = response.json().get("results", [])
        
        # Si no hay resultados, intentar una búsqueda más amplia
        if not results and "with_genres" in params:
            del params["with_genres"]
            response = requests.get(f"{TMDB_BASE_URL}/discover/movie", params=params)
            response.raise_for_status()
            results = response.json().get("results", [])
        
        # Si aún no hay resultados y hay filtro de persona, intentar sin él
        if not results and "with_people" in params:
            del params["with_people"]
            response = requests.get(f"{TMDB_BASE_URL}/discover/movie", params=params)
            response.raise_for_status()
            results = response.json().get("results", [])
        
        return results[:3]  # Devolver solo las 3 primeras películas
    except requests.RequestException as e:
        print(f"Error fetching movie recommendations: {e}")
        return []

def get_person_id(name):
    """Get person ID from TMDb API."""
    if not TMDB_API_KEY:
        return None
    
    try:
        params = {
            "api_key": TMDB_API_KEY,
            "language": "es-ES",
            "query": name
        }
        
        response = requests.get(f"{TMDB_BASE_URL}/search/person", params=params)
        response.raise_for_status()
        results = response.json().get("results", [])
        
        if results:
            return results[0]
        
        return None
    except Exception as e:
        print(f"Error searching for person: {e}")
        return None

def format_movie_recommendations(movies):
    """Format movie recommendations for display in chat."""
    if not movies:
        return "No encontré películas que coincidan con tus preferencias."

    response = "Aquí tienes algunas recomendaciones:\n\n"

    for i, movie in enumerate(movies, 1):
        title = movie.get("title", "Sin título")
        year = movie.get("release_date", "")[:4] if movie.get("release_date") else "Año desconocido"
        overview = movie.get("overview", "Sin descripción disponible.")
        movie_id = movie.get("id")

        tmdb_url = f"https://www.themoviedb.org/movie/{movie_id}" if movie_id else ""

        response += f"**{i}. {title} ({year})**\n{overview}\n"
        if tmdb_url:
            response += f"[Más información]({tmdb_url})\n"
        response += "\n"

    response += "¿Te gustaría ver más recomendaciones o prefieres buscar otro tipo de películas?"
    
    return response

if __name__ == '__main__':
    app.run(debug=True)