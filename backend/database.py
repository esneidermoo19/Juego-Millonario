from __future__ import annotations

from pathlib import Path

from flask import Flask, current_app, g
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from .models import Base, Game, Question
from .services.prizes import prize_for_correct_answers


STARTER_QUESTIONS = [
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
    ("¿Qué movimiento artístico fundó André Breton con su manifiesto de 1924?", "Cubismo", "Dadaísmo", "Surrealismo", "Futurismo", "C"),
    ("¿Quién escribió «En busca del tiempo perdido»?", "Gustave Flaubert", "Émile Zola", "Victor Hugo", "Marcel Proust", "D"),
    ("¿Qué pintor neerlandés pintó «La joven de la perla»?", "Johannes Vermeer", "Rembrandt", "Frans Hals", "Vincent van Gogh", "A"),
    ("¿Qué compositor ruso escribió el ballet «El lago de los cisnes»?", "Ígor Stravinski", "Piotr Ilich Chaikovski", "Serguéi Rajmáninov", "Serguéi Prokófiev", "B"),
    ("¿En qué año cayó Constantinopla en manos del Imperio otomano?", "1204", "1492", "1453", "1517", "C"),
    ("¿Qué dios egipcio, con cabeza de chacal, se asociaba con los muertos y la momificación?", "Ra", "Osiris", "Horus", "Anubis", "D"),
    ("¿Quién pintó «El jardín de las delicias»?", "El Bosco", "Pieter Brueghel el Viejo", "Alberto Durero", "Tiziano", "A"),
    ("¿Qué escritor ruso escribió «Crimen y castigo»?", "León Tolstói", "Fiódor Dostoievski", "Antón Chéjov", "Nikolái Gógol", "B"),
    ("¿Qué arquitecto brasileño diseñó gran parte de los edificios de Brasilia?", "Paulo Mendes da Rocha", "Lina Bo Bardi", "Oscar Niemeyer", "Roberto Burle Marx", "C"),
    ("¿Qué poeta nicaragüense es considerado el padre del modernismo literario?", "Leopoldo Lugones", "José Martí", "Amado Nervo", "Rubén Darío", "D"),
    ("Además del inglés, ¿cuál es la lengua oficial más hablada en la India?", "Hindi", "Bengalí", "Tamil", "Urdu", "A"),
    ("¿Qué civilización creó la escritura cuneiforme?", "Egipcia", "Sumeria", "Fenicia", "China", "B"),
    ("¿Qué pintor impresionista pintó la serie de «Los nenúfares»?", "Edgar Degas", "Édouard Manet", "Claude Monet", "Pierre-Auguste Renoir", "C"),
    ("¿Quién escribió «La divina comedia»?", "Francesco Petrarca", "Nicolás Maquiavelo", "Giovanni Boccaccio", "Dante Alighieri", "D"),
    ("¿Qué tratado de 1494 repartió las tierras del Nuevo Mundo entre España y Portugal?", "Tratado de Tordesillas", "Tratado de Utrecht", "Tratado de Versalles", "Paz de Westfalia", "A"),
    ("¿Qué compositor escribió «Las cuatro estaciones»?", "Johann Sebastian Bach", "Antonio Vivaldi", "Georg Friedrich Händel", "Claudio Monteverdi", "B"),
    ("¿Qué escultor creó «El pensador»?", "Miguel Ángel", "Donatello", "Auguste Rodin", "Gian Lorenzo Bernini", "C"),
    ("¿En qué ciudad se firmó la Declaración de Independencia de Estados Unidos?", "Boston", "Washington", "Nueva York", "Filadelfia", "D"),
    ("¿Durante qué dinastía china se construyó la mayor parte de la Gran Muralla que se conserva hoy?", "Ming", "Han", "Qing", "Tang", "A"),
    ("¿Qué escritora británica escribió «Orgullo y prejuicio»?", "Charlotte Brontë", "Jane Austen", "Virginia Woolf", "Mary Shelley", "B"),
    ("¿Qué cineasta japonés dirigió «Los siete samuráis»?", "Hayao Miyazaki", "Yasujirō Ozu", "Akira Kurosawa", "Takeshi Kitano", "C"),
    ("¿Qué familia de banqueros fue la gran mecenas del Renacimiento en Florencia?", "Borgia", "Este", "Sforza", "Médici", "D"),
    ("¿Qué pueblo indígena colombiano dio origen a la leyenda de El Dorado?", "Muisca", "Tairona", "Zenú", "Quimbaya", "A"),
    ("¿Quién escribió la novela «Pedro Páramo»?", "Carlos Fuentes", "Juan Rulfo", "Octavio Paz", "Juan José Arreola", "B"),
    ("¿Qué artista colombiano es famoso por sus figuras de formas voluminosas?", "Omar Rayo", "Alejandro Obregón", "Fernando Botero", "Débora Arango", "C"),
    ("¿Qué compositor alemán escribió el ciclo de óperas «El anillo del nibelungo»?", "Felix Mendelssohn", "Richard Strauss", "Johannes Brahms", "Richard Wagner", "D"),
    ("¿En qué país se encuentra el templo de Angkor Wat?", "Camboya", "Tailandia", "Vietnam", "Laos", "A"),
    ("¿Qué escritor portugués ganó el Premio Nobel de Literatura en 1998?", "Fernando Pessoa", "José Saramago", "Eça de Queirós", "António Lobo Antunes", "B"),
    ("¿Qué filósofo escribió «Así habló Zaratustra»?", "Immanuel Kant", "Arthur Schopenhauer", "Friedrich Nietzsche", "Søren Kierkegaard", "C"),
    ("¿Qué maravilla del mundo antiguo se encontraba en Alejandría?", "El Coloso", "El Mausoleo", "Los Jardines Colgantes", "El Faro", "D"),
    ("¿Qué pintor español pintó «Las meninas»?", "Diego Velázquez", "Francisco de Goya", "El Greco", "Bartolomé Esteban Murillo", "A"),
    ("¿Qué poeta chilena fue la primera persona latinoamericana en ganar el Nobel de Literatura?", "Isabel Allende", "Gabriela Mistral", "Alfonsina Storni", "Juana de Ibarbourou", "B"),
    ("¿En qué ciudad está la famosa ópera diseñada por Jørn Utzon con techos en forma de velas?", "Melbourne", "Auckland", "Sídney", "Ciudad del Cabo", "C"),
    ("¿Qué escritor francés escribió «Los miserables»?", "Alexandre Dumas", "Stendhal", "Honoré de Balzac", "Victor Hugo", "D"),
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
        event.listen(engine, "connect", _enable_sqlite_foreign_keys)

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


def _enable_sqlite_foreign_keys(
    dbapi_connection: object, connection_record: object
) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
