from __future__ import annotations

from pathlib import Path

from flask import Flask, current_app, g
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from .models import Base, Game, Question
from .services.prizes import prize_for_correct_answers


STARTER_QUESTIONS = [
    ("¿De qué color es el cielo en un día despejado?", "Verde", "Azul", "Rojo", "Amarillo", "B"),
    ("¿Cuántos días tiene una semana?", "Cinco", "Seis", "Siete", "Ocho", "C"),
    ("¿Qué animal dice «miau»?", "Perro", "Gato", "Vaca", "Pato", "B"),
    ("¿Cuántas patas tiene un gato?", "Dos", "Tres", "Cuatro", "Cinco", "C"),
    ("¿Qué bebida se obtiene de la vaca?", "Agua", "Jugo", "Leche", "Café", "C"),
    ("¿Cuántos meses tiene un año?", "Diez", "Once", "Doce", "Trece", "C"),
    ("¿De qué color es la nieve?", "Blanco", "Negro", "Verde", "Azul", "A"),
    ("¿Qué usamos para saber la hora?", "Un libro", "Un reloj", "Una silla", "Una taza", "B"),
    ("¿Cuántas horas tiene un día?", "Doce", "Dieciocho", "Veinticuatro", "Treinta", "C"),
    ("¿De qué color es la hierba?", "Verde", "Roja", "Azul", "Morada", "A"),
    ("¿Qué fruta es amarilla y les encanta a los monos?", "Manzana", "Pera", "Banano", "Uva", "C"),
    ("¿En qué planeta vivimos?", "Marte", "Júpiter", "Venus", "La Tierra", "D"),
    ("¿Qué estación del año es la más calurosa?", "Invierno", "Verano", "Otoño", "Primavera", "B"),
    ("¿Cuántos dedos tiene una mano?", "Cuatro", "Cinco", "Seis", "Siete", "B"),
    ("¿De qué color es el sol?", "Amarillo", "Morado", "Verde", "Azul", "A"),
    ("¿Qué insecto produce miel?", "Mosca", "Hormiga", "Abeja", "Araña", "C"),
    ("¿Qué animal tiene una trompa larga?", "León", "Tigre", "Elefante", "Jirafa", "C"),
    ("¿Con qué escribimos en un papel?", "Lápiz", "Tenedor", "Cuchara", "Peine", "A"),
    ("¿Qué usamos para lavarnos las manos?", "Arena", "Jabón", "Azúcar", "Sal", "B"),
    ("¿Cuántas ruedas tiene una bicicleta?", "Una", "Dos", "Tres", "Cuatro", "B"),
    ("¿Quién pintó «La noche estrellada»?", "Vincent van Gogh", "Claude Monet", "Salvador Dalí", "Rembrandt", "A"),
    ("¿En qué ciudad se encuentra el Coliseo?", "Atenas", "Roma", "Estambul", "Madrid", "B"),
    ("¿Qué instrumento tocaba principalmente Jimi Hendrix?", "Batería", "Piano", "Guitarra eléctrica", "Saxofón", "C"),
    ("¿En qué país se originó la pizza?", "Francia", "Grecia", "Estados Unidos", "Italia", "D"),
    ("¿Cuál es el idioma con más hablantes nativos del mundo?", "Chino mandarín", "Español", "Inglés", "Hindi", "A"),
    ("¿Qué superhéroe es conocido como «el hombre murciélago»?", "Superman", "Batman", "Spider-Man", "Flash", "B"),
    ("¿Qué ave es el símbolo más conocido de la paz?", "El cóndor", "El águila", "La paloma blanca", "El búho", "C"),
    ("¿En qué país se encuentra la Gran Muralla?", "Japón", "India", "Corea del Sur", "China", "D"),
    ("¿Qué celebración mexicana honra a los difuntos el 1 y 2 de noviembre?", "Día de Muertos", "Carnaval", "Semana Santa", "Día de la Independencia", "A"),
    ("¿Cuál es el plato típico japonés hecho con arroz y pescado crudo?", "Paella", "Sushi", "Tacos", "Curry", "B"),
    ("¿Cuántas cuerdas tiene una guitarra clásica estándar?", "4", "5", "6", "8", "C"),
    ("¿Qué princesa de Disney pierde una zapatilla de cristal?", "Blancanieves", "Ariel", "Aurora", "Cenicienta", "D"),
    ("¿En qué ciudad está la Estatua de la Libertad?", "Nueva York", "Chicago", "Washington", "Boston", "A"),
    ("¿Qué planeta lleva el nombre del dios romano de la guerra?", "Júpiter", "Marte", "Saturno", "Mercurio", "B"),
    ("¿En qué país está la Torre inclinada de Pisa?", "España", "Grecia", "Italia", "Francia", "C"),
    ("¿Cómo se conoce popularmente la famosa torre del reloj de Londres?", "Torre de Londres", "Tower Bridge", "London Eye", "Big Ben", "D"),
    ("¿De qué país es originario el flamenco?", "España", "Argentina", "México", "Cuba", "A"),
    ("¿Cuál es el libro sagrado del islam?", "La Biblia", "El Corán", "La Torá", "Los Vedas", "B"),
    ("¿Qué animal es uno de los símbolos más conocidos de Australia?", "León", "Oso panda", "Canguro", "Tigre", "C"),
    ("¿En qué deporte se hizo famoso Michael Jordan?", "Fútbol", "Tenis", "Béisbol", "Baloncesto", "D"),
    ("¿Qué cantante colombiana interpretó «Hips Don't Lie»?", "Shakira", "Karol G", "Selena Gomez", "Thalía", "A"),
    ("¿Cuál es la moneda oficial del Reino Unido?", "Euro", "Libra esterlina", "Dólar", "Franco", "B"),
    ("¿Qué ritmo musical tradicional nació en la costa caribe de Colombia?", "Samba", "Tango", "Cumbia", "Flamenco", "C"),
    ("¿Quién escribió «Romeo y Julieta»?", "Charles Dickens", "Jane Austen", "Oscar Wilde", "William Shakespeare", "D"),
    ("¿En qué país se encuentra el Taj Mahal?", "India", "Pakistán", "Irán", "Egipto", "A"),
    ("¿De qué color es el círculo central de la bandera de Japón?", "Azul", "Rojo", "Amarillo", "Negro", "B"),
    ("¿Qué río atraviesa París?", "Támesis", "Danubio", "Sena", "Rin", "C"),
    ("¿Qué fiesta se celebra el 31 de octubre en muchos países?", "Navidad", "San Valentín", "Pascua", "Halloween", "D"),
    ("¿Qué personaje animado vive en una piña debajo del mar?", "Bob Esponja", "Patricio Estrella", "Calamardo", "Don Cangrejo", "A"),
    ("¿Qué inventor es conocido por desarrollar la bombilla eléctrica comercial?", "Alexander Graham Bell", "Thomas Edison", "Isaac Newton", "Galileo Galilei", "B"),
    ("¿De qué país es la bebida tradicional llamada tequila?", "España", "Cuba", "México", "Perú", "C"),
    ("¿Cuántos jugadores de cada equipo están en la cancha en un partido de baloncesto?", "11", "6", "7", "5", "D"),
    ("¿Qué monumento de Río de Janeiro es una gran estatua con los brazos abiertos?", "Cristo Redentor", "Pan de Azúcar", "Maracaná", "Copacabana", "A"),
    ("¿Qué compositor austriaco escribió la ópera «La flauta mágica»?", "Ludwig van Beethoven", "Wolfgang Amadeus Mozart", "Joseph Haydn", "Franz Schubert", "B"),
    ("¿En qué museo de Madrid se exhibe el «Guernica» de Picasso?", "Museo del Prado", "Museo Thyssen", "Museo Reina Sofía", "Museo Sorolla", "C"),
    ("¿Qué civilización precolombina construyó la ciudad de Chichén Itzá?", "Inca", "Muisca", "Azteca", "Maya", "D"),
    ("¿A quién se le atribuye «La Odisea»?", "Homero", "Virgilio", "Sófocles", "Platón", "A"),
    ("¿Qué pintor español es famoso por sus relojes derretidos?", "Joan Miró", "Salvador Dalí", "Francisco de Goya", "Diego Velázquez", "B"),
    ("¿En qué país se celebra el Oktoberfest original?", "Austria", "Suiza", "Alemania", "Bélgica", "C"),
    ("¿Quién es el dios del trueno en la mitología nórdica?", "Odín", "Balder", "Loki", "Thor", "D"),
    ("¿Quién escribió «La metamorfosis», donde Gregorio Samsa se convierte en insecto?", "Franz Kafka", "Albert Camus", "Hermann Hesse", "Thomas Mann", "A"),
    ("¿Qué ciudad es conocida como la «Ciudad Eterna»?", "París", "Roma", "Jerusalén", "Atenas", "B"),
    ("¿Qué arquitecto diseñó la Sagrada Familia de Barcelona?", "Frank Lloyd Wright", "Le Corbusier", "Antoni Gaudí", "Oscar Niemeyer", "C"),
    ("¿Qué banda británica grabó el álbum «Abbey Road»?", "The Rolling Stones", "Pink Floyd", "Queen", "The Beatles", "D"),
    ("¿Qué instrumento tocaba el músico de jazz Louis Armstrong?", "Trompeta", "Saxofón", "Piano", "Contrabajo", "A"),
    ("¿En qué país nació el poeta Pablo Neruda?", "Argentina", "Chile", "Perú", "Uruguay", "B"),
    ("¿Qué artista pintó la bóveda de la Capilla Sixtina?", "Rafael", "Leonardo da Vinci", "Miguel Ángel", "Sandro Botticelli", "C"),
    ("¿Qué dios griego es el rey del Olimpo?", "Ares", "Apolo", "Hades", "Zeus", "D"),
    ("¿Qué país regaló la Estatua de la Libertad a Estados Unidos?", "Francia", "Reino Unido", "España", "Italia", "A"),
    ("¿Quién dirigió la película «Parque Jurásico» (1993)?", "James Cameron", "Steven Spielberg", "George Lucas", "Ridley Scott", "B"),
    ("¿Qué científica fue la primera persona en ganar dos premios Nobel?", "Rosalind Franklin", "Ada Lovelace", "Marie Curie", "Lise Meitner", "C"),
    ("¿En qué ciudad española se encuentra la Alhambra?", "Sevilla", "Toledo", "Córdoba", "Granada", "D"),
    ("¿Qué novela de George Orwell presenta al «Gran Hermano»?", "1984", "Rebelión en la granja", "Un mundo feliz", "Fahrenheit 451", "A"),
    ("¿Qué pintora mexicana es famosa por sus autorretratos?", "Remedios Varo", "Frida Kahlo", "Leonora Carrington", "María Izquierdo", "B"),
    ("¿Qué ciudad fue sede de los primeros Juegos Olímpicos modernos en 1896?", "París", "Londres", "Atenas", "Roma", "C"),
    ("¿Qué instrumento es típico de la música vallenata colombiana?", "Trompeta", "Violín", "Arpa", "Acordeón", "D"),
    ("¿Qué filósofo griego fue maestro de Alejandro Magno?", "Aristóteles", "Platón", "Sócrates", "Pitágoras", "A"),
    ("¿En qué país está la antigua ciudad de Petra, tallada en roca?", "Egipto", "Jordania", "Siria", "Turquía", "B"),
    ("¿Cómo se llama el gran museo de arte de San Petersburgo, en Rusia?", "Museo Pushkin", "Galería Tretiakov", "Museo del Hermitage", "Museo del Kremlin", "C"),
    ("¿Qué escritor argentino escribió el libro de cuentos «El Aleph»?", "Julio Cortázar", "Adolfo Bioy Casares", "Ernesto Sabato", "Jorge Luis Borges", "D"),
    ("¿Qué religión fundó Siddhartha Gautama?", "Budismo", "Hinduismo", "Jainismo", "Sijismo", "A"),
    ("¿Qué cantante es conocido como el «Rey del Pop»?", "Elvis Presley", "Michael Jackson", "Prince", "Freddie Mercury", "B"),
    ("¿Qué ópera de Georges Bizet está ambientada en Sevilla y tiene una protagonista gitana?", "Aida", "Tosca", "Carmen", "La Traviata", "C"),
    ("¿Qué imperio construyó la red de caminos llamada Qhapaq Ñan?", "Azteca", "Romano", "Maya", "Inca", "D"),
    ("¿En qué ciudad se encuentra el Museo del Prado?", "Madrid", "Barcelona", "Sevilla", "Valencia", "A"),
    ("¿Qué escritor colombiano escribió la novela «María» (1867)?", "José Asunción Silva", "Jorge Isaacs", "Rafael Pombo", "Tomás Carrasquilla", "B"),
    ("¿Qué personaje de Nintendo es un fontanero con gorra roja?", "Sonic", "Link", "Mario", "Pac-Man", "C"),
    ("¿Cuántos días tiene un año bisiesto?", "364", "365", "367", "366", "D"),
    ("¿Qué animal es conocido como el «rey de la selva»?", "León", "Tigre", "Elefante", "Gorila", "A"),
    ("Según un refrán en inglés, ¿qué fruta al día mantiene alejado al médico?", "Banano", "Manzana", "Naranja", "Pera", "B"),
    ("¿Cuál es el deporte más popular de Colombia?", "Béisbol", "Ciclismo", "Fútbol", "Tenis", "C"),
    ("¿En qué país se celebra el famoso Carnaval de Río?", "Argentina", "Colombia", "Uruguay", "Brasil", "D"),
    ("¿Qué personaje de «Toy Story» dice «¡Hasta el infinito y más allá!»?", "Buzz Lightyear", "Woody", "Rex", "Sr. Cara de Papa", "A"),
    ("¿Qué mar baña la costa norte de Colombia?", "Mar Mediterráneo", "Mar Caribe", "Mar Rojo", "Mar Negro", "B"),
    ("¿Qué ciudad colombiana es conocida como la «capital mundial de la salsa»?", "Pasto", "Bogotá", "Cali", "Tunja", "C"),
    ("¿En qué ciudad colombiana se celebra la Feria de las Flores?", "Bogotá", "Cartagena", "Cali", "Medellín", "D"),
    ("¿Por qué producto agrícola es famosa Colombia en todo el mundo?", "Café", "Trigo", "Arroz", "Soya", "A"),
    ("¿Qué fiesta celebra el nacimiento de Jesús?", "Pascua", "Navidad", "Carnaval", "Año Nuevo", "B"),
    ("¿Cuántos colores tiene la bandera de Colombia?", "2", "4", "3", "5", "C"),
    ("¿Qué superhéroe usa un escudo redondo con una estrella?", "Iron Man", "Hulk", "Thor", "Capitán América", "D"),
    ("¿A qué personaje le crece la nariz cuando dice mentiras?", "Pinocho", "Peter Pan", "Aladino", "Hansel", "A"),
    ("¿Qué famoso ratón es la mascota de Disney?", "Jerry", "Mickey Mouse", "Speedy González", "Stuart Little", "B"),
    ("¿Qué país de Sudamérica tiene forma de una franja larga y delgada?", "Bolivia", "Perú", "Chile", "Paraguay", "C"),
    ("¿Cuál es el país más poblado de América del Sur?", "Argentina", "Perú", "Colombia", "Brasil", "D"),
    ("¿En qué deporte se usa un balón ovalado y se anotan «tries»?", "Rugby", "Béisbol", "Hockey", "Golf", "A"),
    ("¿Qué banda británica tenía como cantante a Freddie Mercury?", "The Beatles", "Queen", "The Rolling Stones", "Oasis", "B"),
    ("En «Star Wars», ¿quién es el padre de Luke Skywalker?", "Obi-Wan Kenobi", "Yoda", "Darth Vader", "Han Solo", "C"),
    ("¿Qué juego de mesa tiene reyes, reinas, alfiles y torres?", "Damas", "Dominó", "Parqués", "Ajedrez", "D"),
    ("¿Qué juego de mesa colombiano se juega con dados y fichas de colores?", "Parqués", "Monopolio", "Ajedrez", "Dominó", "A"),
    ("¿Cuántos minutos dura un partido de fútbol sin contar la reposición?", "60", "90", "80", "120", "B"),
    ("¿Qué ciudad es conocida como «la Gran Manzana»?", "Los Ángeles", "Chicago", "Nueva York", "Miami", "C"),
    ("¿Qué villano enemigo de Batman tiene cara de payaso?", "Thanos", "Lex Luthor", "El Duende Verde", "El Joker", "D"),
    ("¿Qué princesa de Disney tiene una larguísima cabellera y vive en una torre?", "Rapunzel", "Mulán", "Bella", "Jazmín", "A"),
    ("Además de Colombia, ¿en qué país son típicas las arepas?", "Chile", "Venezuela", "Argentina", "España", "B"),
    ("¿Qué día se celebra San Valentín en muchos países?", "1 de mayo", "25 de diciembre", "14 de febrero", "31 de octubre", "C"),
    ("¿Qué ogro verde vive en un pantano en una película animada?", "Yoda", "Hulk", "El Grinch", "Shrek", "D"),
    ("¿Cuál es el planeta más grande del sistema solar?", "Júpiter", "Saturno", "Neptuno", "La Tierra", "A"),
    ("¿Qué cantante colombiano popularizó en 1993 el vallenato «La gota fría»?", "Juanes", "Carlos Vives", "J Balvin", "Maluma", "B"),
    ("¿Qué cantante colombiano es famoso por la canción «La camisa negra»?", "Carlos Vives", "Fonseca", "Juanes", "Silvestre Dangond", "C"),
    ("¿Qué red social es famosa por sus videos cortos y retos de baile?", "LinkedIn", "Gmail", "Wikipedia", "TikTok", "D"),
]


def init_database(app: Flask) -> None:
    database_url = app.config["DATABASE_URL"]
    if database_url.startswith("sqlite:///") and ":memory:" not in database_url:
        database_path = Path(database_url.removeprefix("sqlite:///"))
        database_path.parent.mkdir(parents=True, exist_ok=True)

    connect_args = (
        {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    )
    engine = create_engine(database_url, connect_args=connect_args)

    if database_url.startswith("sqlite"):
        event.listen(engine, "connect", _configure_sqlite_connection)
        # WAL permite lecturas y escrituras concurrentes (imprescindible con varios workers).
        with engine.connect() as conn:
            conn.exec_driver_sql("PRAGMA journal_mode=WAL")

    app.extensions["database_engine"] = engine
    app.extensions["database_session_factory"] = sessionmaker(
        bind=engine, expire_on_commit=False
    )
    Base.metadata.create_all(engine)
    # Repair completed games written by the previous safe-level payout logic.
    factory = app.extensions["database_session_factory"]
    with factory() as session:
        repaired = False
        completed_games = session.query(Game).filter(
            Game.status == "completed",
            Game.current_question_number > 0,
        )
        for game in completed_games:
            earned_prize = prize_for_correct_answers(game.current_question_number)
            if game.score < earned_prize:
                game.score = earned_prize
                repaired = True
        if repaired:
            session.commit()

    # La base de datos local del juego queda lista para usar desde la primera ejecución.
    # Cada dificultad 1-100 corresponde a una pregunta del banco (y a su traducción al inglés),
    # así que si el banco cambia se actualiza la pregunta de esa dificultad en lugar de duplicarla.
    if database_url == "sqlite:///backend/instance/millionaire.db":
        with factory() as session:
            by_difficulty = {
                question.difficulty: question
                for question in session.query(Question).filter(
                    Question.difficulty.between(1, len(STARTER_QUESTIONS))
                )
            }
            for difficulty, (text, a, b, c, d, answer) in enumerate(STARTER_QUESTIONS, 1):
                values = dict(text=text, option_a=a, option_b=b, option_c=c, option_d=d,
                              correct_option=answer, difficulty=difficulty)
                question = by_difficulty.get(difficulty)
                if question is None:
                    session.add(Question(**values))
                else:
                    for field, value in values.items():
                        setattr(question, field, value)
            session.commit()
    app.teardown_appcontext(_close_session)


def get_session() -> Session:
    if "database_session" not in g:
        g.database_session = current_app.extensions["database_session_factory"]()
    return g.database_session


def _close_session(exception: BaseException | None = None) -> None:
    session = g.pop("database_session", None)
    if session is not None:
        if exception is not None:
            session.rollback()
        session.close()


def _configure_sqlite_connection(
    dbapi_connection: object, connection_record: object
) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()
