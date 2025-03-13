Recomendador de Películas con Chatbot
Una aplicación web interactiva que recomienda películas a los usuarios mediante un chatbot conversacional.

Características
Interfaz de chat moderna y responsive con TailwindCSS
Integración con la API de TMDb para obtener datos de películas
Chatbot conversacional potenciado por Hugging Face
Recomendaciones personalizadas basadas en múltiples criterios:

Géneros de películas
Directores
Actores
Años o décadas específicas
Popularidad (películas populares o joyas ocultas)
Soporte para interacciones en español
Manejo de errores y respuestas de respaldo
Diseño adaptable para dispositivos móviles y de escritorio
Requisitos
Python 3.8+
API key de TMDb (The Movie Database)
API key de Hugging Face (opcional, para mejorar las respuestas del chatbot)
Instalación
1. Clonar el repositorio
git clone https://github.com/tu-usuario/movies-with-ia.git
cd movies-with-ia
2. Crear un entorno virtual
En Windows:
python -m venv venv
venv\Scripts\activate
En macOS/Linux:
python3 -m venv venv
source venv/bin/activate
3. Instalar dependencias
pip install -r requirements.txt
4. Configurar variables de entorno
Crea un archivo .env en la raíz del proyecto con el siguiente contenido:

TMDB_API_KEY=tu_tmdb_api_key
HUGGINGFACE_API_KEY=tu_huggingface_api_key
Obtención de API Keys
TMDb API Key
Regístrate en The Movie Database
Ve a tu perfil > Configuración > API
Solicita una API key para uso personal
Copia la API key (v3 auth) en tu archivo .env
Hugging Face API Key
Regístrate en Hugging Face
Ve a tu perfil > Settings > Access Tokens
Crea un nuevo token
Copia el token en tu archivo .env
Uso
Iniciar la aplicación
python app.py
La aplicación estará disponible en http://127.0.0.1:5000/

Interacción con el chatbot
Abre la aplicación en tu navegador
El chatbot te saludará y te preguntará por tus preferencias
Puedes mencionar:

Géneros: "Me gustan las películas de acción"
Directores: "Me gustan las películas de Tarantino"
Actores: "Me gustan las películas con Leonardo DiCaprio"
Años/Décadas: "Quiero ver películas de los 90s"
Cuando el chatbot te pregunte si quieres ver recomendaciones, simplemente responde "sí"
El chatbot te mostrará tres películas que coincidan con tus preferencias
Estructura del proyecto
movies-with-ia/
├── app.py                 # Aplicación principal de Flask
├── requirements.txt       # Dependencias del proyecto
├── .env                   # Variables de entorno (no incluido en el repositorio)
├── .env.example           # Ejemplo de variables de entorno
├── .gitignore             # Archivos ignorados por Git
├── README.md              # Documentación del proyecto
├── static/                # Archivos estáticos
│   ├── css/               # Hojas de estilo
│   │   └── custom.css     # Estilos personalizados
│   └── js/                # JavaScript
│       └── chat.js        # Lógica del chat
└── templates/             # Plantillas HTML
    └── index.html         # Página principal
Tecnologías utilizadas
Backend: Flask (Python)
Frontend: HTML, CSS, JavaScript
Estilos: TailwindCSS
APIs:

TMDb API para datos de películas
Hugging Face para procesamiento de lenguaje natural
Otras librerías:

Requests para llamadas HTTP
python-dotenv para variables de entorno
Personalización
Añadir más géneros
Puedes añadir más géneros al diccionario GENRE_MAP en app.py.

Añadir más directores/actores
Puedes añadir más personas famosas al diccionario FAMOUS_PEOPLE en app.py.

Modificar el estilo
Puedes personalizar la apariencia editando templates/index.html y static/css/custom.css.

Contribuciones
Las contribuciones son bienvenidas. Por favor, abre un issue para discutir los cambios importantes antes de enviar un pull request.

