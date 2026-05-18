from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from src.infrastructure.config.settings import settings
from src.infrastructure.config.database import get_db_session, init_db
from src.infrastructure.security.jwt_handler import init_jwt

from src.infrastructure.adapters.output.persistence.sqlalchemy_usuario_repo import SQLAlchemyUsuarioRepo
from src.infrastructure.adapters.output.persistence.sqlalchemy_itinerario_repo import SQLAlchemyItinerarioRepo
from src.infrastructure.adapters.output.external.api_colombia_adapter import ApiColombiaAdapter

from src.application.services.auth_service import AuthService, TOKEN_BLACKLIST
from src.application.services.itinerario_service import ItinerarioService
from src.application.services.aeropuerto_cache_service import AeropuertoCacheService

from src.infrastructure.adapters.input.web.auth_controller import create_auth_blueprint
from src.infrastructure.adapters.input.web.itinerario_controller import create_itinerario_blueprint
from src.infrastructure.adapters.input.web.aeropuerto_controller import create_aeropuerto_blueprint


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder="../../presentation/templates",
        static_folder="../../presentation/static",
    )

    app.config["JWT_SECRET_KEY"] = settings.jwt_secret_key
    app.config["SECRET_KEY"] = settings.jwt_secret_key
    app.config["DEBUG"] = settings.flask_debug

    CORS(app, resources={r"/api/*": {"origins": "*"}, r"/auth/*": {"origins": "*"}})

    jwt: JWTManager = init_jwt(app)

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        return jwt_payload.get("jti") in TOKEN_BLACKLIST

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        from flask import jsonify
        return jsonify({"error": "Token revocado. Inicia sesión nuevamente."}), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        from flask import jsonify
        return jsonify({"error": "Token expirado. Inicia sesión nuevamente."}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        from flask import jsonify
        return jsonify({"error": "Token de autenticación requerido."}), 401

    init_db()

    db_session = get_db_session()

    usuario_repo = SQLAlchemyUsuarioRepo(db_session)
    itinerario_repo = SQLAlchemyItinerarioRepo(db_session)
    aeropuerto_client = ApiColombiaAdapter()
    cache_service = AeropuertoCacheService(db_session)

    _seed_aeropuertos(cache_service)

    auth_service = AuthService(usuario_repo)
    itinerario_service = ItinerarioService(itinerario_repo, aeropuerto_client, cache_service)

    app.register_blueprint(create_auth_blueprint(auth_service))
    app.register_blueprint(create_itinerario_blueprint(itinerario_service))
    app.register_blueprint(create_aeropuerto_blueprint(aeropuerto_client, cache_service))

    _register_frontend_routes(app)

    return app


def _seed_aeropuertos(cache_service) -> None:
    import json, os
    from src.application.dtos.aeropuerto_dto import AeropuertoDTO

    data_path = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', 'data', 'airports.json')
    )
    try:
        with open(data_path, encoding='utf-8') as f:
            aeropuertos_raw = json.load(f)
        aeropuertos = [
            AeropuertoDTO(iata=r[0], nombre=r[1], ciudad=r[2], pais=r[3],
                          latitud=r[4], longitud=r[5])
            for r in aeropuertos_raw
        ]
    except Exception:
        aeropuertos = []

    # fallback: lista mínima embebida por si el archivo JSON falla
    if not aeropuertos:
        aeropuertos = [
        # ── Colombia ─────────────────────────────────────────────────────────
        AeropuertoDTO("BOG", "Aeropuerto Internacional El Dorado",              "Bogotá",          "Colombia",     4.7016,   -74.1469),
        AeropuertoDTO("MDE", "Aeropuerto Internacional José María Córdova",     "Medellín",        "Colombia",     6.1645,   -75.4234),
        AeropuertoDTO("CLO", "Aeropuerto Internacional Alfonso Bonilla Aragón", "Cali",            "Colombia",     3.5432,   -76.3816),
        AeropuertoDTO("BAQ", "Aeropuerto Internacional Ernesto Cortissoz",      "Barranquilla",    "Colombia",    10.8896,   -74.7808),
        AeropuertoDTO("CTG", "Aeropuerto Internacional Rafael Núñez",           "Cartagena",       "Colombia",    10.4424,   -75.5130),
        AeropuertoDTO("BGA", "Aeropuerto Internacional Palonegro",              "Bucaramanga",     "Colombia",     7.1265,   -73.1848),
        AeropuertoDTO("PEI", "Aeropuerto Internacional Matecaña",               "Pereira",         "Colombia",     4.8127,   -75.7395),
        AeropuertoDTO("SMR", "Aeropuerto Internacional Simón Bolívar",          "Santa Marta",     "Colombia",    11.1196,   -74.2306),
        AeropuertoDTO("ADZ", "Aeropuerto Internacional Gustavo Rojas Pinilla",  "San Andrés",      "Colombia",    12.5836,   -81.7112),
        AeropuertoDTO("MTR", "Aeropuerto Internacional Los Garzones",           "Montería",        "Colombia",     8.8237,   -75.8258),
        AeropuertoDTO("NVA", "Aeropuerto Benito Salas",                         "Neiva",           "Colombia",     2.9500,   -75.2940),
        AeropuertoDTO("VVC", "Aeropuerto La Vanguardia",                        "Villavicencio",   "Colombia",     4.1678,   -73.6138),
        AeropuertoDTO("IBE", "Aeropuerto Perales",                              "Ibagué",          "Colombia",     4.4216,   -75.1333),
        AeropuertoDTO("PST", "Aeropuerto Antonio Nariño",                       "Pasto",           "Colombia",     1.3963,   -77.2955),
        AeropuertoDTO("UIB", "Aeropuerto El Caraño",                            "Quibdó",          "Colombia",     5.6958,   -76.6412),
        # ── América del Norte ────────────────────────────────────────────────
        AeropuertoDTO("JFK", "John F. Kennedy International Airport",           "Nueva York",      "USA",         40.6413,   -73.7781),
        AeropuertoDTO("LAX", "Los Angeles International Airport",               "Los Ángeles",     "USA",         33.9416,  -118.4085),
        AeropuertoDTO("ORD", "O'Hare International Airport",                    "Chicago",         "USA",         41.9742,   -87.9073),
        AeropuertoDTO("MIA", "Miami International Airport",                     "Miami",           "USA",         25.7959,   -80.2870),
        AeropuertoDTO("YYZ", "Toronto Pearson International Airport",           "Toronto",         "Canadá",      43.6777,   -79.6248),
        AeropuertoDTO("MEX", "Aeropuerto Internacional Benito Juárez",          "Ciudad de México","México",      19.4363,   -99.0721),
        AeropuertoDTO("CUN", "Aeropuerto Internacional de Cancún",              "Cancún",          "México",      21.0365,   -86.8771),
        # ── América del Sur ──────────────────────────────────────────────────
        AeropuertoDTO("GRU", "Aeropuerto Internacional de São Paulo-Guarulhos", "São Paulo",       "Brasil",      -23.4356,  -46.4731),
        AeropuertoDTO("EZE", "Aeropuerto Internacional Ministro Pistarini",     "Buenos Aires",    "Argentina",   -34.8222,  -58.5358),
        AeropuertoDTO("SCL", "Aeropuerto Internacional Arturo Merino Benítez",  "Santiago",        "Chile",       -33.3930,  -70.7858),
        AeropuertoDTO("LIM", "Aeropuerto Internacional Jorge Chávez",           "Lima",            "Perú",        -12.0219,  -77.1143),
        AeropuertoDTO("UIO", "Aeropuerto Internacional Mariscal Sucre",         "Quito",           "Ecuador",     -0.1292,   -78.3575),
        AeropuertoDTO("GYE", "Aeropuerto Internacional José Joaquín de Olmedo", "Guayaquil",       "Ecuador",     -2.1574,   -79.8836),
        AeropuertoDTO("PTY", "Aeropuerto Internacional de Tocumen",             "Ciudad de Panamá","Panamá",       9.0714,   -79.3835),
        AeropuertoDTO("VVI", "Aeropuerto Internacional Viru Viru",              "Santa Cruz",      "Bolivia",    -17.6448,  -63.1354),
        # ── Europa ───────────────────────────────────────────────────────────
        AeropuertoDTO("LHR", "Heathrow Airport",                                "Londres",         "Reino Unido", 51.4775,    -0.4614),
        AeropuertoDTO("CDG", "Aéroport de Paris-Charles de Gaulle",             "París",           "Francia",     49.0097,     2.5479),
        AeropuertoDTO("MAD", "Aeropuerto Adolfo Suárez Madrid-Barajas",         "Madrid",          "España",      40.4936,    -3.5668),
        AeropuertoDTO("BCN", "Aeropuerto de Barcelona-El Prat",                 "Barcelona",       "España",      41.2971,     2.0785),
        AeropuertoDTO("FRA", "Frankfurt Airport",                               "Fráncfort",       "Alemania",    50.0379,     8.5622),
        AeropuertoDTO("AMS", "Amsterdam Airport Schiphol",                      "Ámsterdam",       "Países Bajos",52.3086,     4.7639),
        AeropuertoDTO("FCO", "Aeroporto di Roma-Fiumicino",                     "Roma",            "Italia",      41.8003,    12.2389),
        AeropuertoDTO("IST", "Istanbul Airport",                                "Estambul",        "Turquía",     41.2753,    28.7519),
        # ── Asia y Oceanía ───────────────────────────────────────────────────
        AeropuertoDTO("DXB", "Dubai International Airport",                     "Dubái",           "EAU",         25.2532,    55.3657),
        AeropuertoDTO("SIN", "Singapore Changi Airport",                        "Singapur",        "Singapur",     1.3644,   103.9915),
        AeropuertoDTO("HND", "Tokyo Haneda Airport",                            "Tokio",           "Japón",       35.5494,   139.7798),
        AeropuertoDTO("PEK", "Beijing Capital International Airport",           "Pekín",           "China",       40.0799,   116.6031),
        AeropuertoDTO("SYD", "Sydney Kingsford Smith Airport",                  "Sídney",          "Australia",  -33.9399,   151.1753),
        AeropuertoDTO("GRU", "Aeropuerto Internacional de São Paulo-Guarulhos", "São Paulo",       "Brasil",      -23.4356,  -46.4731),
        # ── África ───────────────────────────────────────────────────────────
        AeropuertoDTO("JNB", "O. R. Tambo International Airport",               "Johannesburgo",   "Sudáfrica",   -26.1367,   28.2411),
        AeropuertoDTO("CAI", "Cairo International Airport",                     "El Cairo",        "Egipto",       30.1219,   31.4056),
        AeropuertoDTO("NBO", "Jomo Kenyatta International Airport",             "Nairobi",         "Kenia",        -1.3192,   36.9275),
        AeropuertoDTO("CMN", "Aéroport Mohammed V",                             "Casablanca",      "Marruecos",    33.3675,   -7.5897),
        AeropuertoDTO("LOS", "Murtala Muhammed International Airport",          "Lagos",           "Nigeria",       6.5774,    3.3214),
        AeropuertoDTO("ADD", "Bole International Airport",                      "Adís Abeba",      "Etiopía",       8.9779,   38.7993),
        # ── América del Sur adicionales ──────────────────────────────────────
        AeropuertoDTO("BSB", "Aeropuerto Internacional de Brasilia",            "Brasilia",        "Brasil",      -15.8711,  -47.9186),
        AeropuertoDTO("RIO", "Aeropuerto Internacional Galeão",                 "Río de Janeiro",  "Brasil",      -22.8099,  -43.2505),
        AeropuertoDTO("CWB", "Aeropuerto Internacional Afonso Pena",            "Curitiba",        "Brasil",      -25.5285,  -49.1758),
        AeropuertoDTO("MVD", "Aeropuerto Internacional de Carrasco",            "Montevideo",      "Uruguay",     -34.8384,  -56.0308),
        AeropuertoDTO("ASU", "Aeropuerto Internacional Silvio Pettirossi",      "Asunción",        "Paraguay",    -25.2398,  -57.5198),
        AeropuertoDTO("CCS", "Aeropuerto Internacional Simón Bolívar",          "Caracas",         "Venezuela",    10.6031,  -66.9913),
        AeropuertoDTO("HAV", "Aeropuerto Internacional José Martí",             "La Habana",       "Cuba",         22.9892,  -82.4091),
        AeropuertoDTO("SDQ", "Aeropuerto Internacional Las Américas",           "Santo Domingo",   "Rep. Dom.",    18.4297,  -69.6689),
        AeropuertoDTO("SJO", "Aeropuerto Internacional Juan Santamaría",        "San José",        "Costa Rica",    9.9938,  -84.2088),
        AeropuertoDTO("GUA", "Aeropuerto Internacional La Aurora",              "Ciudad de Guatemala","Guatemala",  14.5833,  -90.5275),
        AeropuertoDTO("SAL", "Aeropuerto Internacional Óscar Arnulfo Romero",   "San Salvador",    "El Salvador",  13.4409,  -89.0557),
        AeropuertoDTO("MGA", "Aeropuerto Internacional Augusto Sandino",        "Managua",         "Nicaragua",    12.1415,  -86.1682),
        AeropuertoDTO("TGU", "Aeropuerto Internacional Toncontín",              "Tegucigalpa",     "Honduras",     14.0608,  -87.2172),
        AeropuertoDTO("BZE", "Aeropuerto Internacional Philip S. W. Goldson",   "Belmopán",        "Belice",       17.5391,  -88.3082),
        # ── Norteamérica adicionales ─────────────────────────────────────────
        AeropuertoDTO("SFO", "San Francisco International Airport",             "San Francisco",   "USA",          37.6213, -122.3790),
        AeropuertoDTO("DFW", "Dallas/Fort Worth International Airport",         "Dallas",          "USA",          32.8998,  -97.0403),
        AeropuertoDTO("ATL", "Hartsfield-Jackson Atlanta International Airport","Atlanta",         "USA",          33.6407,  -84.4277),
        AeropuertoDTO("SEA", "Seattle-Tacoma International Airport",            "Seattle",         "USA",          47.4502, -122.3088),
        AeropuertoDTO("BOS", "Boston Logan International Airport",              "Boston",          "USA",          42.3656,  -71.0096),
        AeropuertoDTO("IAH", "George Bush Intercontinental Airport",            "Houston",         "USA",          29.9902,  -95.3368),
        AeropuertoDTO("LAS", "Harry Reid International Airport",                "Las Vegas",       "USA",          36.0840, -115.1537),
        AeropuertoDTO("DEN", "Denver International Airport",                    "Denver",          "USA",          39.8561, -104.6737),
        AeropuertoDTO("YVR", "Vancouver International Airport",                 "Vancouver",       "Canadá",       49.1967, -123.1815),
        AeropuertoDTO("YUL", "Aéroport international Pierre-Elliott-Trudeau",   "Montreal",        "Canadá",       45.4706,  -73.7408),
        # ── Europa adicionales ───────────────────────────────────────────────
        AeropuertoDTO("MUC", "Munich Airport",                                  "Múnich",          "Alemania",     48.3537,   11.7750),
        AeropuertoDTO("ZRH", "Zurich Airport",                                  "Zúrich",          "Suiza",        47.4647,    8.5492),
        AeropuertoDTO("VIE", "Vienna International Airport",                    "Viena",           "Austria",      48.1102,   16.5697),
        AeropuertoDTO("BRU", "Brussels Airport",                                "Bruselas",        "Bélgica",      50.9014,    4.4844),
        AeropuertoDTO("CPH", "Copenhagen Airport",                              "Copenhague",      "Dinamarca",    55.6180,   12.6561),
        AeropuertoDTO("ARN", "Stockholm Arlanda Airport",                       "Estocolmo",       "Suecia",       59.6519,   17.9186),
        AeropuertoDTO("OSL", "Oslo Gardermoen Airport",                         "Oslo",            "Noruega",      60.1939,   11.1004),
        AeropuertoDTO("HEL", "Helsinki-Vantaa Airport",                         "Helsinki",        "Finlandia",    60.3172,   24.9633),
        AeropuertoDTO("LIS", "Aeroporto Humberto Delgado",                      "Lisboa",          "Portugal",     38.7742,   -9.1342),
        AeropuertoDTO("MXP", "Aeroporto di Milano Malpensa",                    "Milán",           "Italia",       45.6306,    8.7281),
        AeropuertoDTO("ATH", "Athens International Airport Eleftherios Venizelos","Atenas",        "Grecia",       37.9364,   23.9445),
        AeropuertoDTO("WAW", "Warsaw Chopin Airport",                           "Varsovia",        "Polonia",      52.1657,   20.9671),
        AeropuertoDTO("PRG", "Václav Havel Airport Prague",                     "Praga",           "Rep. Checa",   50.1008,   14.2600),
        AeropuertoDTO("BUD", "Budapest Ferenc Liszt International Airport",     "Budapest",        "Hungría",      47.4298,   19.2611),
        # ── Asia adicionales ─────────────────────────────────────────────────
        AeropuertoDTO("ICN", "Incheon International Airport",                   "Seúl",            "Corea del Sur",37.4602,  126.4407),
        AeropuertoDTO("HKG", "Hong Kong International Airport",                 "Hong Kong",       "China",        22.3080,  113.9185),
        AeropuertoDTO("BKK", "Suvarnabhumi Airport",                            "Bangkok",         "Tailandia",    13.6900,  100.7501),
        AeropuertoDTO("KUL", "Kuala Lumpur International Airport",              "Kuala Lumpur",    "Malasia",       2.7456,  101.7099),
        AeropuertoDTO("CGK", "Soekarno-Hatta International Airport",            "Yakarta",         "Indonesia",    -6.1256,  106.6559),
        AeropuertoDTO("MNL", "Ninoy Aquino International Airport",              "Manila",          "Filipinas",    14.5086,  121.0196),
        AeropuertoDTO("DEL", "Indira Gandhi International Airport",             "Nueva Delhi",     "India",        28.5665,   77.1031),
        AeropuertoDTO("BOM", "Chhatrapati Shivaji Maharaj International Airport","Bombay",         "India",        19.0896,   72.8656),
        AeropuertoDTO("DOH", "Hamad International Airport",                     "Doha",            "Catar",        25.2609,   51.6138),
        AeropuertoDTO("AUH", "Abu Dhabi International Airport",                 "Abu Dabi",        "EAU",          24.4330,   54.6511),
        AeropuertoDTO("TLV", "Ben Gurion International Airport",                "Tel Aviv",        "Israel",       32.0055,   34.8854),
        AeropuertoDTO("NRT", "Narita International Airport",                    "Tokio",           "Japón",        35.7647,  140.3864),
        AeropuertoDTO("PVG", "Shanghai Pudong International Airport",           "Shanghái",        "China",        31.1443,  121.8083),
        # ── Oceanía adicionales ──────────────────────────────────────────────
        AeropuertoDTO("MEL", "Melbourne Airport",                               "Melbourne",       "Australia",   -37.6690,  144.8410),
        AeropuertoDTO("AKL", "Auckland Airport",                                "Auckland",        "Nueva Zelanda",-37.0082, 174.7917),
        ]  # fin fallback

    for a in aeropuertos:
        try:
            cache_service.guardar_o_actualizar(a)
        except Exception:
            pass


def _register_frontend_routes(app: Flask):
    from flask import render_template, redirect, url_for

    @app.get("/")
    def index():
        return redirect(url_for("frontend_login"))

    @app.get("/login")
    def frontend_login():
        return render_template("auth/login.html")

    @app.get("/register")
    def frontend_register():
        return render_template("auth/register.html")

    @app.get("/itinerarios")
    def frontend_lista():
        return render_template("itinerarios/lista.html")

    @app.get("/itinerarios/nuevo")
    def frontend_nuevo():
        return render_template("itinerarios/formulario.html")

    @app.get("/itinerarios/<string:id>/editar")
    def frontend_editar(id):
        return render_template("itinerarios/formulario.html", itinerario_id=id)

    @app.get("/itinerarios/<string:id>")
    def frontend_detalle(id):
        return render_template("itinerarios/detalle.html", itinerario_id=id)
