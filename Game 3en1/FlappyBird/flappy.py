import pygame
import random
import sys
import os
import math
import json
from itertools import cycle
from pygame.locals import *
from datetime import datetime


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from notificaciones.email_notifier import send_email_notification
except ModuleNotFoundError as e:
    print(f"Error importando notificaciones: {e}")
    send_email_notification = None


print("DEBUG: __file__ =", __file__)
print("DEBUG: snake BASE_DIR =", BASE_DIR)
import sys
print("DEBUG: sys.path[0:5] =", sys.path[0:5])

GLOBAL_SCORES_PATH = os.path.join(BASE_DIR, "data", "global_scores.json")
GAME_IDENTIFIER = "FLAPPY"

player_email = ""
if len(sys.argv) > 1:
    player_email = sys.argv[1]


# Sistema de datos
class DataManager:
    def __init__(self, scores_path=GLOBAL_SCORES_PATH, game_id=GAME_IDENTIFIER):
        self.scores_path = scores_path
        self.game_id = game_id

    def _read_all_data(self):
        if not os.path.exists(self.scores_path):
            return {}

        with open(self.scores_path, 'r', encoding='utf-8') as file:
            try:
                data = json.load(file)
                if not isinstance(data, dict):
                    return {}
                return data
            except json.JSONDecodeError:
                return {}

    def _save_all_data(self, all_data):
        #Guarda todos los datos en el JSON
        with open(self.scores_path, 'w', encoding='utf-8') as file:
            json.dump(all_data, file, indent=4)

    # Lectura de puntajes (score)
    def load_game_scores(self):
        #Carga y retorna los puntajes del juego actual ordenados
        all_data = self._read_all_data()
        game_scores = all_data.get(self.game_id, [])
        game_scores.sort(key=lambda x: x['score'], reverse=True)
        return game_scores[:10]  # Solo los 10 primeros

    # Actualiza el puntaje
    def update_score(self, name, email, score):

        if not email or "@" not in email:
            print("INFO: Puntaje no guardado. Email no válido.")
            return False, 0

        all_data = self._read_all_data()
        if self.game_id not in all_data:
            all_data[self.game_id] = []

        game_scores = all_data[self.game_id]

        # Guardar Top 1 previo antes de actualizar
        prev_top = game_scores[0].copy() if game_scores else None

        # Buscar jugador
        record_found = False
        old_score = 0

        for player in game_scores:
            if player.get("email") == email:
                record_found = True
                old_score = player["score"]

                if score > old_score:
                    player["score"] = score
                    player["name"] = name
                    player["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                else:
                    return False, old_score
                break

        # Nuevo jugador si no existe
        if not record_found:
            game_scores.append({
                "name": name,
                "email": email,
                "score": score,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        # Ordenar y limitar a top 10
        game_scores.sort(key=lambda x: x['score'], reverse=True)
        all_data[self.game_id] = game_scores[:10]

        # Guardar todo
        self._save_all_data(all_data)

        # Nuevo Top 1 tras guardar
        new_top = game_scores[0] if game_scores else None

        # Notificación: si hay nuevo top o mejora del mismo jugador
        if new_top and new_top["score"] > 0:
            prev_score = prev_top["score"] if prev_top else 0
            prev_email = prev_top["email"] if prev_top else None

            if new_top["score"] > prev_score or new_top["email"] != prev_email:
                try:
                    if send_email_notification:
                        send_email_notification(
                            recipient_email=new_top["email"],
                            game_name=self.game_id,
                            score=new_top["score"],
                            player_name=new_top["name"]
                        )
                        print(f"Notificación enviada a {new_top['email']} (nuevo récord: {new_top['score']})")
                    else:
                        print("No se pudo enviar notificación (función no disponible).")
                except Exception as e:
                    print(f"Error al enviar notificación: {e}")

        return True, old_score

    # Obtener puntajes
    def get_top_scores(self):
        #Devuelve los puntajes del juego actual (máx. 10)
        return self.load_game_scores()


data_manager = DataManager()


# Configuración del juego
FPS = 30
SCREENWIDTH = 576  # Duplicado de 288 a 576
SCREENHEIGHT = 768  # Incrementado de 512 a 768
PIPEGAPSIZE = 150  # Incrementado de 100 a 150 para más espacio entre tuberías
BASEY = SCREENHEIGHT * 0.79

# Configuración de pantalla
FULLSCREEN = False  # Cambiar a True para pantalla completa

# Diccionarios para almacenar imágenes, sonidos y máscaras de colisión
IMAGES, SOUNDS, HITMASKS = {}, {}, {}

# Colores para las imágenes generadas
COLORS = {
    'day_sky': (135, 206, 235),  # Azul cielo diurno
    'night_sky': (25, 25, 112),  # Azul cielo nocturno
    'ground': (222, 184, 135),   # Marrón arena
    'pipe_green': (0, 128, 0),   # Verde
    'pipe_red': (220, 20, 60),   # Rojo
    'red_box': (220, 20, 60),    # Rojo
    'blue_box': (30, 144, 255),  # Azul
    'yellow_box': (255, 215, 0), # Amarillo
    'white': (255, 255, 255),    # Blanco
    'black': (0, 0, 0),          # Negro
    'text': (255, 255, 255),     # Blanco para texto
    'button': (100, 100, 200),   # Azul para botones
    'clear_button': (200, 50, 50), # Rojizo para botón de borrar
}

# Lista de jugadores (cada uno con 3 posiciones de aleteo)
PLAYERS_LIST = (
    # caja roja
    ('redbox-upflap', 'redbox-midflap', 'redbox-downflap'),
    # caja azul
    ('bluebox-upflap', 'bluebox-midflap', 'bluebox-downflap'),
    # caja amarilla
    ('yellowbox-upflap', 'yellowbox-midflap', 'yellowbox-downflap'),
)

# Lista de fondos
BACKGROUNDS_LIST = (
    'background-day',
    'background-night',
)

# Lista de tuberías
PIPES_LIST = (
    'pipe-green',
    'pipe-red',
)

# Archivos para guardar puntuaciones
SCORES_FILE = "flappy_pobre_scores.json"
CURRENT_SCORE_FILE = "flappy_pobre_current_score.json"

try:
    xrange
except NameError:
    xrange = range

def load_high_scores():
    """Carga las puntuaciones más altas desde global_scores.json"""
    try:
        # (DataManager)
        scores = data_manager.get_top_scores()
        return scores

        # Sistema antiguo (comentado, ya no se usa)
        """
        if os.path.exists(SCORES_FILE):
            with open(SCORES_FILE, 'r') as f:
                scores = json.load(f)
                if scores and isinstance(scores[0], int):
                    return [{'name': 'Jugador', 'score': score} for score in scores]
                return scores
        return []
        """
    except:
        return []


def save_high_scores(scores):
    """Guarda las puntuaciones más altas usando DataManager"""
    try:
        for entry in scores:
            data_manager.update_score(
                name=entry.get('name', 'Jugador'),
                email=f"{entry.get('name', 'Jugador').lower()}@anonimo",
                score=entry.get('score', 0)
            )
        return True

        # Sistema antiguo:
        """
        with open(SCORES_FILE, 'w') as f:
            json.dump(scores, f)
        """
    except Exception as e:
        print("ERROR al guardar puntuaciones:", e)
        return False


def clear_high_scores():
    """Borra todas las puntuaciones del juego actual en global_scores.json"""
    try:
        all_data = data_manager._read_all_data()
        # Filtramos los que NO son del juego actual
        remaining = [x for x in all_data if x.get('game') != GAME_IDENTIFIER]
        data_manager._save_all_data(remaining)

        # Sistema antiguo:
        """
        if os.path.exists(SCORES_FILE):
            os.remove(SCORES_FILE)
        save_current_score(0, "")
        """
        return True
    except Exception as e:
        print("ERROR al limpiar puntuaciones:", e)
        return False


def load_current_score():
    """Obtiene la puntuación actual del jugador desde global_scores.json"""
    try:
        # Intentar obtener el email global si está disponible
        email = player_email if player_email else ""
        scores = data_manager.get_top_scores()
        if email:
            for s in scores:
                if s.get('email') == email:
                    return s.get('score', 0), s.get('name', '')
        return 0, ''

        # Antiguo sistema:
        """
        if os.path.exists(CURRENT_SCORE_FILE):
            with open(CURRENT_SCORE_FILE, 'r') as f:
                data = json.load(f)
                return data.get('score', 0), data.get('name', '')
        return 0, ''
        """
    except Exception as e:
        print("ERROR al cargar puntuación actual:", e)
        return 0, ''


def save_current_score(score, name):
    """Guarda la puntuación actual en global_scores.json"""
    try:
        email = player_email if player_email else f"{name.lower()}@anonimo"
        data_manager.update_score(name, email, score)
        return True

        #
        """
        with open(CURRENT_SCORE_FILE, 'w') as f:
            json.dump({'score': score, 'name': name}, f)
        """
    except Exception as e:
        print("ERROR al guardar puntuación actual:", e)
        return False


def update_high_scores(new_score, name):
    """Actualiza la tabla de puntuaciones en global_scores.json"""
    try:
        email = player_email if player_email else f"{name.lower()}@anonimo"
        data_manager.update_score(name, email, new_score)
        return data_manager.get_top_scores()

        # Sistema antiguo:
        """
        scores = load_high_scores()
        ...
        """
    except Exception as e:
        print("ERROR al actualizar puntuaciones:", e)
        return []


def get_player_name():
    """Pide al jugador que ingrese su nombre (máx. 5 caracteres, sugerido desde el email)"""
    input_active = True

    # Obtener sugerencia desde el email global si existe
    suggested_name = ""
    global player_email
    if player_email and "@" in player_email:
        suggested_name = player_email.split("@")[0][:5].upper()  # Parte local, máx. 5 chars
    player_name = suggested_name  # ← Se muestra como texto inicial editable

    input_box = pygame.Rect(SCREENWIDTH//2 - 150, SCREENHEIGHT//2, 300, 50)

    # Fondo semitransparente
    name_bg = pygame.Surface((400, 300), pygame.SRCALPHA)
    pygame.draw.rect(name_bg, (0, 0, 0, 200), (0, 0, 400, 300))
    pygame.draw.rect(name_bg, COLORS['white'], (0, 0, 400, 300), 3)

    # Fondo de pantalla
    temp_bg = pygame.Surface((SCREENWIDTH, SCREENHEIGHT))
    temp_bg.fill(COLORS['day_sky'])

    while input_active:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == K_RETURN:
                    if player_name.strip():
                        input_active = False
                elif event.key == K_BACKSPACE:
                    player_name = player_name[:-1]
                else:
                    # Limitar el nombre a 5 caracteres
                    if len(player_name) < 5:
                        if event.unicode.isalnum():
                            player_name += event.unicode.upper()

        # Dibujar fondo
        SCREEN.blit(temp_bg, (0, 0))

        # Caja de entrada
        name_x = (SCREENWIDTH - name_bg.get_width()) // 2
        name_y = (SCREENHEIGHT - name_bg.get_height()) // 2
        SCREEN.blit(name_bg, (name_x, name_y))

        # Título
        title_font = pygame.font.SysFont('Arial', 30, bold=True)
        title_text = title_font.render("Ingresa tu nombre", True, COLORS['white'])
        title_rect = title_text.get_rect(center=(SCREENWIDTH//2, name_y + 50))
        SCREEN.blit(title_text, title_rect)

        # Campo de texto
        pygame.draw.rect(SCREEN, COLORS['white'], input_box, 2)

        # Texto ingresado (o sugerido)
        font = pygame.font.SysFont('Arial', 28, bold=True)
        text_surface = font.render(player_name, True, COLORS['white'])
        SCREEN.blit(text_surface, (input_box.x + 10, input_box.y + 10))

        # Indicaciones
        inst_font = pygame.font.SysFont('Arial', 18)
        inst_text = inst_font.render("Máx. 5 caracteres — ENTER para continuar", True, COLORS['white'])
        inst_rect = inst_text.get_rect(center=(SCREENWIDTH//2, name_y + 230))
        SCREEN.blit(inst_text, inst_rect)

        # Mostrar sugerencia si no se ha escrito nada
        if not player_name and suggested_name:
            hint_font = pygame.font.SysFont('Arial', 20, italic=True)
            hint_surface = hint_font.render(f"Sugerido: {suggested_name}", True, (180, 180, 180))
            SCREEN.blit(hint_surface, (input_box.x + 10, input_box.y + 10))

        pygame.display.update()
        FPSCLOCK.tick(FPS)

    # Límite de seguridad
    return player_name.strip()[:5]



def generate_images():
    """Genera todas las imágenes necesarias para el juego"""

    # Generar fondos
    # Fondo diurno
    day_bg = pygame.Surface((SCREENWIDTH, SCREENHEIGHT))
    day_bg.fill(COLORS['day_sky'])
    # Añadir nubes
    for _ in range(10):  # Más nubes para pantalla más grande
        x = random.randint(0, SCREENWIDTH)
        y = random.randint(50, SCREENHEIGHT // 2)
        radius = random.randint(20, 40)
        pygame.draw.circle(day_bg, COLORS['white'], (x, y), radius)
        pygame.draw.circle(day_bg, COLORS['white'], (x + radius, y), radius)
        pygame.draw.circle(day_bg, COLORS['white'], (x - radius, y), radius)
    IMAGES['background-day'] = day_bg

    # Fondo nocturno
    night_bg = pygame.Surface((SCREENWIDTH, SCREENHEIGHT))
    night_bg.fill(COLORS['night_sky'])
    # Añadir estrellas
    for _ in range(100):  # Más estrellas para pantalla más grande
        x = random.randint(0, SCREENWIDTH)
        y = random.randint(0, SCREENHEIGHT // 2)
        pygame.draw.circle(night_bg, COLORS['white'], (x, y), 1)
    IMAGES['background-night'] = night_bg

    # Generar base (suelo)
    base_height = SCREENHEIGHT - BASEY
    base = pygame.Surface((SCREENWIDTH * 2, base_height))
    base.fill(COLORS['ground'])
    # Añadir textura al suelo
    for x in range(0, SCREENWIDTH * 2, 20):
        pygame.draw.line(base, (200, 164, 115), (x, 0), (x, base_height), 2)
    IMAGES['base'] = base

    # Generar tuberías (más grandes para pantalla más grande)
    pipe_width = 104  # Duplicado de 52 a 104
    pipe_height = 640  # Duplicado de 320 a 640

    # Tubería verde
    pipe_green = pygame.Surface((pipe_width, pipe_height), pygame.SRCALPHA)
    pygame.draw.rect(pipe_green, COLORS['pipe_green'], (0, 0, pipe_width, pipe_height))
    pygame.draw.rect(pipe_green, (0, 100, 0), (0, 0, pipe_width, pipe_height), 3)
    # Añadir borde superior
    pygame.draw.rect(pipe_green, (0, 100, 0), (0, 0, pipe_width, 60))  # Duplicado de 30 a 60
    pygame.draw.rect(pipe_green, (0, 100, 0), (0, 0, pipe_width, 60), 3)
    IMAGES['pipe-green'] = pipe_green

    # Tubería roja
    pipe_red = pygame.Surface((pipe_width, pipe_height), pygame.SRCALPHA)
    pygame.draw.rect(pipe_red, COLORS['pipe_red'], (0, 0, pipe_width, pipe_height))
    pygame.draw.rect(pipe_red, (139, 0, 0), (0, 0, pipe_width, pipe_height), 3)
    # Añadir borde superior
    pygame.draw.rect(pipe_red, (139, 0, 0), (0, 0, pipe_width, 60))  # Duplicado de 30 a 60
    pygame.draw.rect(pipe_red, (139, 0, 0), (0, 0, pipe_width, 60), 3)
    IMAGES['pipe-red'] = pipe_red

    # Generar cajas (jugadores)
    # Caja roja - más pequeña que las otras
    redbox_size = 40  # Tamaño más pequeño para la caja roja
    redbox_collision_size = 25  # Tamaño de colisión más pequeño

    for flap, offset in [('upflap', -6), ('midflap', 0), ('downflap', 6)]:  # Ajustado para tamaño más pequeño
        redbox = pygame.Surface((redbox_size, redbox_size), pygame.SRCALPHA)
        pygame.draw.rect(redbox, COLORS['red_box'], (0, 0, redbox_size, redbox_size))
        pygame.draw.rect(redbox, (139, 0, 0), (0, 0, redbox_size, redbox_size), 2)
        # Añadir ala
        wing_y = redbox_size // 2 + offset
        pygame.draw.ellipse(redbox, (180, 0, 0), (redbox_size-12, wing_y-6, 18, 12))  # Ajustado para tamaño más pequeño
        IMAGES[f'redbox-{flap}'] = redbox

    # Caja azul - tamaño normal
    bluebox_size = 68  # Tamaño normal

    for flap, offset in [('upflap', -10), ('midflap', 0), ('downflap', 10)]:
        bluebox = pygame.Surface((bluebox_size, bluebox_size), pygame.SRCALPHA)
        pygame.draw.rect(bluebox, COLORS['blue_box'], (0, 0, bluebox_size, bluebox_size))
        pygame.draw.rect(bluebox, (0, 0, 139), (0, 0, bluebox_size, bluebox_size), 2)
        # Añadir ala
        wing_y = bluebox_size // 2 + offset
        pygame.draw.ellipse(bluebox, (0, 0, 180), (bluebox_size-20, wing_y-10, 30, 20))
        IMAGES[f'bluebox-{flap}'] = bluebox

    # Caja amarilla - tamaño normal
    yellowbox_size = 68  # Tamaño normal

    for flap, offset in [('upflap', -10), ('midflap', 0), ('downflap', 10)]:
        yellowbox = pygame.Surface((yellowbox_size, yellowbox_size), pygame.SRCALPHA)
        pygame.draw.rect(yellowbox, COLORS['yellow_box'], (0, 0, yellowbox_size, yellowbox_size))
        pygame.draw.rect(yellowbox, (184, 134, 0), (0, 0, yellowbox_size, yellowbox_size), 2)
        # Añadir ala
        wing_y = yellowbox_size // 2 + offset
        pygame.draw.ellipse(yellowbox, (218, 165, 32), (yellowbox_size-20, wing_y-10, 30, 20))
        IMAGES[f'yellowbox-{flap}'] = yellowbox

    # Generar números para el marcador (más grandes)
    font = pygame.font.SysFont('Arial', 60, bold=True)  # Duplicado de 30 a 60
    for i in range(10):
        num_surface = font.render(str(i), True, COLORS['white'])
        IMAGES[str(i)] = num_surface

    # Generar mensaje de bienvenida (más grande)
    message = pygame.Surface((368, 534), pygame.SRCALPHA)  # Duplicado de 184,267 a 368,534
    pygame.draw.rect(message, (0, 0, 0, 128), (0, 0, 368, 534))
    pygame.draw.rect(message, COLORS['white'], (0, 0, 368, 534), 2)

    # Título "Flappy Pobre" - Cambiado de "Flappy Box"
    title_font = pygame.font.SysFont('Arial', 55, bold=True)  # Duplicado de 30 a 60
    title_text = title_font.render("Flappy Pobre", True, COLORS['text'])  # Cambiado de "Flappy Box" a "Flappy Pobre"
    title_rect = title_text.get_rect(center=(184, 100))  # Duplicado de 92,50 a 184,100
    message.blit(title_text, title_rect)

    # Instrucciones
    inst_font = pygame.font.SysFont('Arial', 30)  # Duplicado de 15 a 30
    inst_text = inst_font.render("Presiona ESPACIO", True, COLORS['text'])
    inst_rect = inst_text.get_rect(center=(184, 300))  # Duplicado de 92,150 a 184,300
    message.blit(inst_text, inst_rect)

    inst_text2 = inst_font.render("para empezar", True, COLORS['text'])
    inst_rect2 = inst_text2.get_rect(center=(184, 340))  # Duplicado de 92,170 a 184,340
    message.blit(inst_text2, inst_rect2)

    IMAGES['message'] = message

    # Generar pantalla de Game Over (más grande)
    gameover = pygame.Surface((376, 120), pygame.SRCALPHA)  # Duplicado de 188,60 a 376,120
    pygame.draw.rect(gameover, (0, 0, 0, 128), (0, 0, 376, 100))
    pygame.draw.rect(gameover, COLORS['white'], (0, 0, 376, 120), 2)

    go_font = pygame.font.SysFont('Arial', 80, bold=True)  # Duplicado de 40 a 80
    go_text = go_font.render("Game Over", True, COLORS['text'])
    go_rect = go_text.get_rect(center=(188, 60))  # Duplicado de 94,30 a 188,60
    gameover.blit(go_text, go_rect)

    IMAGES['gameover'] = gameover

    # Generar botón de tabla de puntuaciones
    button_width, button_height = 150, 50
    button = pygame.Surface((button_width, button_height), pygame.SRCALPHA)
    pygame.draw.rect(button, COLORS['button'], (0, 0, button_width, button_height))
    pygame.draw.rect(button, COLORS['white'], (0, 0, button_width, button_height), 2)

    button_font = pygame.font.SysFont('Arial', 30, bold=True)
    button_text = button_font.render("Tabla", True, COLORS['white'])
    button_text_rect = button_text.get_rect(center=(button_width//2, button_height//2))
    button.blit(button_text, button_text_rect)

    IMAGES['button'] = button

    # Generar botón de borrar puntuaciones - más pequeño
    clear_button_width, clear_button_height = 100, 35  # Reducido de 120,40 a 100,35
    clear_button = pygame.Surface((clear_button_width, clear_button_height), pygame.SRCALPHA)
    pygame.draw.rect(clear_button, COLORS['clear_button'], (0, 0, clear_button_width, clear_button_height))
    pygame.draw.rect(clear_button, COLORS['white'], (0, 0, clear_button_width, clear_button_height), 2)

    clear_button_font = pygame.font.SysFont('Arial', 20, bold=True)  # Reducido de 24 a 20
    clear_button_text = clear_button_font.render("Borrar", True, COLORS['white'])
    clear_button_text_rect = clear_button_text.get_rect(center=(clear_button_width//2, clear_button_height//2))
    clear_button.blit(clear_button_text, clear_button_text_rect)

    IMAGES['clear_button'] = clear_button

    # Generar pantalla de tabla de puntuaciones
    scores_bg = pygame.Surface((400, 500), pygame.SRCALPHA)
    pygame.draw.rect(scores_bg, (0, 0, 0, 200), (0, 0, 400, 500))
    pygame.draw.rect(scores_bg, COLORS['white'], (0, 0, 400, 500), 3)

    # Título "Tabla de Puntuaciones" - Tamaño más pequeño
    title_font = pygame.font.SysFont('Arial', 28, bold=True)  # Reducido de 40 a 28
    title_text = title_font.render("Tabla de Puntuaciones", True, COLORS['white'])
    title_rect = title_text.get_rect(center=(200, 40))
    scores_bg.blit(title_text, title_rect)

    IMAGES['scores_bg'] = scores_bg

def generate_sounds():
    """Genera sonidos simples para el juego"""
    try:
        # Sonido de aleteo
        SOUNDS['wing'] = pygame.mixer.Sound(buffer=create_sine_wave(440, 100))

        # Sonido de punto
        SOUNDS['point'] = pygame.mixer.Sound(buffer=create_sine_wave(880, 150))

        # Sonido de golpe
        SOUNDS['hit'] = pygame.mixer.Sound(buffer=create_noise(200))

        # Sonido de muerte
        SOUNDS['die'] = pygame.mixer.Sound(buffer=create_noise(500))
    except:
        print("No se pudieron generar los sonidos. El juego continuará sin sonido.")

def create_sine_wave(frequency, duration):
    """Crea una onda sinusoidal para generar sonidos simples"""
    sample_rate = 22050
    samples = int(sample_rate * duration / 1000)
    waves = [int(32767.0 * math.sin(2.0 * math.pi * frequency * i / sample_rate)) for i in range(samples)]

    # Convertir a bytes
    sound_data = bytearray()
    for sample in waves:
        sound_data.extend([sample & 0xFF, (sample >> 8) & 0xFF])

    return bytes(sound_data)

def create_noise(duration):
    """Crea ruido para sonidos de impacto"""
    sample_rate = 22050
    samples = int(sample_rate * duration / 1000)
    noise = [random.randint(-32767, 32767) for _ in range(samples)]

    # Convertir a bytes
    sound_data = bytearray()
    for sample in noise:
        sound_data.extend([sample & 0xFF, (sample >> 8) & 0xFF])

    return bytes(sound_data)

MENU_MUSIC_FILE = os.path.join("musica", "sky_stage.mp3")
MENU_MUSIC_VOLUME = 0.4  # volumen base

def play_menu_music(file=MENU_MUSIC_FILE, volume=MENU_MUSIC_VOLUME, loop=True, fade_ms=800):
    """Reproduce música de fondo del menú con un fade suave"""
    try:
        pygame.mixer.music.stop()
        pygame.mixer.music.load(file)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(-1 if loop else 0, fade_ms=fade_ms)
        print(f"[DEBUG] Reproduciendo música del menú: {file}")
    except Exception as e:
        print(f"[ERROR] No se pudo reproducir la música del menú: {e}")


def stop_music(fade_ms=800):
    """Detiene la música suavemente."""
    try:
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.fadeout(fade_ms)
    except Exception:
        pass


def main():
    global SCREEN, FPSCLOCK
    pygame.init()
    FPSCLOCK = pygame.time.Clock()

    SCREEN = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
    pygame.display.set_caption('Flappy Pobre')

    # Variables del jugador
    player_name = "Invitado"
    print(f"DEBUG: Email recibido -> {player_email}")

    #play_menu_music()

    generate_images()
    generate_sounds()

    player_name = get_player_name()
    play_menu_music()
    while True:
        # Seleccionar fondo aleatorio
        randBg = random.randint(0, len(BACKGROUNDS_LIST) - 1)
        IMAGES['background'] = IMAGES[BACKGROUNDS_LIST[randBg]]

        # Seleccionar jugador aleatorio
        randPlayer = random.randint(0, len(PLAYERS_LIST) - 1)
        IMAGES['player'] = (
            IMAGES[PLAYERS_LIST[randPlayer][0]],
            IMAGES[PLAYERS_LIST[randPlayer][1]],
            IMAGES[PLAYERS_LIST[randPlayer][2]],
        )

        # Seleccionar tuberías aleatorias
        pipeindex = random.randint(0, len(PIPES_LIST) - 1)
        pipe_key = PIPES_LIST[pipeindex]
        IMAGES['pipe'] = (
            pygame.transform.flip(IMAGES[pipe_key], False, True),
            IMAGES[pipe_key],
        )

        # Generar máscaras de colisión
        HITMASKS['pipe'] = (
            getHitmask(IMAGES['pipe'][0]),
            getHitmask(IMAGES['pipe'][1]),
        )
        HITMASKS['player'] = (
            getReducedHitmask(IMAGES['player'][0]),
            getReducedHitmask(IMAGES['player'][1]),
            getReducedHitmask(IMAGES['player'][2]),
        )

        #
        movementInfo = showWelcomeAnimation(player_name)

        # Ejecutar juego
        crashInfo = mainGame(movementInfo, player_name)

        # Pantalla de Game Over
        resultado = showGameOverScreen(crashInfo, player_name)


        if resultado == "retry":
            continue
        elif resultado == "inicio":
            player_name = get_player_name()
            play_menu_music()
            continue
        elif resultado == "menu":

            try:
                import __main__  # comprobamos si el script principal es flappy.py
                if "__file__" in dir(__main__) and "flappy.py" in __main__.__file__.lower():
                    pygame.quit()
                    sys.exit()
                else:
                    return
            except Exception:
                pygame.quit()
                sys.exit()


def showWelcomeAnimation(player_name):
    """Muestra la animación de bienvenida"""
    play_menu_music()
    # Índice del jugador para mostrar en pantalla
    playerIndex = 0
    playerIndexGen = cycle([0, 1, 2, 1])
    # Iterador usado para cambiar playerIndex después de cada 5ª iteración
    loopIter = 0

    playerx = int(SCREENWIDTH * 0.2)
    playery = int((SCREENHEIGHT - IMAGES['player'][0].get_height()) / 2)


    messagex = int((SCREENWIDTH - IMAGES['message'].get_width()) / 2)
    messagey = int(SCREENHEIGHT * 0.12)

    # Posición del botón de tabla
    buttonx = int((SCREENWIDTH - IMAGES['button'].get_width()) / 2)
    buttony = int(SCREENHEIGHT * 0.7)

    basex = 0
    # Cantidad máxima que la base puede desplazarse a la izquierda
    baseShift = IMAGES['base'].get_width() - IMAGES['background'].get_width()

    # Movimiento del jugador para el movimiento arriba-abajo en la pantalla de bienvenida
    playerShmVals = {'val': 0, 'dir': 1}

    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP) or event.type == MOUSEBUTTONDOWN:
                # Verificar si se hizo clic en el botón de tabla
                if event.type == MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    button_rect = pygame.Rect(buttonx, buttony, IMAGES['button'].get_width(), IMAGES['button'].get_height())
                    if button_rect.collidepoint(mouse_pos):
                        showScoresTable()  # Mostrar tabla de puntuaciones
                    else:
                        stop_music()
                        # Reproducir primer sonido de aleteo y devolver valores para mainGame
                        if 'wing' in SOUNDS:
                            SOUNDS['wing'].play()
                        return {
                            'playery': playery + playerShmVals['val'],
                            'basex': basex,
                            'playerIndexGen': playerIndexGen,
                        }
                else:  # Si es un evento de teclado
                    # Reproducir primer sonido de aleteo y devolver valores para mainGame
                    if 'wing' in SOUNDS:
                        SOUNDS['wing'].play()
                    return {
                        'playery': playery + playerShmVals['val'],
                        'basex': basex,
                        'playerIndexGen': playerIndexGen,
                    }

        # Ajustar playery, playerIndex, basex
        if (loopIter + 1) % 5 == 0:
            playerIndex = next(playerIndexGen)
        loopIter = (loopIter + 1) % 30
        basex = -((-basex + 4) % baseShift)
        playerShm(playerShmVals)

        # Dibujar sprites
        SCREEN.blit(IMAGES['background'], (0, 0))
        SCREEN.blit(IMAGES['player'][playerIndex], (playerx, playery + playerShmVals['val']))
        SCREEN.blit(IMAGES['message'], (messagex, messagey))
        SCREEN.blit(IMAGES['base'], (basex, BASEY))

        # Mostrar botón de tabla
        SCREEN.blit(IMAGES['button'], (buttonx, buttony))

        # Mostrar nombre del jugador
        font = pygame.font.SysFont(None, 32)
        name_text = font.render(f"Jugador: {player_name}", True, (255, 255, 255))
        name_rect = name_text.get_rect(center=(SCREENWIDTH/2, 30))
        SCREEN.blit(name_text, name_rect)

        # Instrucciones en pantalla (texto más pequeño)
        text = font.render("Presiona ESPACIO o haz clic para jugar", True, (255, 255, 255))
        text_rect = text.get_rect(center=(SCREENWIDTH/2, SCREENHEIGHT - 80))  # Ajustado de 100 a 80
        SCREEN.blit(text, text_rect)

        text_quit = font.render("Presiona ESC para salir", True, (255, 255, 255))
        text_quit_rect = text_quit.get_rect(center=(SCREENWIDTH/2, SCREENHEIGHT - 50))  # Ajustado de 50 a 50
        SCREEN.blit(text_quit, text_quit_rect)

        pygame.display.update()
        FPSCLOCK.tick(FPS)

def showScoresTable():
    GOLD = (255, 215, 0)
    SILVER = (192, 192, 192)
    BRONZE = (205, 127, 50)

    title_font = pygame.font.Font(None, 48)
    top_font = pygame.font.Font(None, 40)
    regular_font = pygame.font.Font(None, 32)


    # Posición de la tabla en la pantalla
    scores_x = (SCREENWIDTH - IMAGES['scores_bg'].get_width()) // 2
    scores_y = (SCREENHEIGHT - IMAGES['scores_bg'].get_height()) // 2

    # Posición del botón de borrar - Centrado sobre el texto "haz clic fuera para cerrar"
    clear_button_x = scores_x + 150  # Centrado en la tabla (400/2 - 100/2 = 150)
    clear_button_y = scores_y + 410  # Posición sobre el texto

    # Área para cerrar (fuera de la tabla)
    close_area = pygame.Rect(scores_x - 10, scores_y - 10,
                           IMAGES['scores_bg'].get_width() + 20,
                           IMAGES['scores_bg'].get_height() + 20)

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                return  # Cerrar la tabla con ESC

            if event.type == MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()

                # Verificar si se hizo clic en el botón de borrar
                #clear_button_rect = pygame.Rect(clear_button_x, clear_button_y,
                                             #IMAGES['clear_button'].get_width(),
                                             #IMAGES['clear_button'].get_height())
                #if clear_button_rect.collidepoint(mouse_pos):
                    #clear_high_scores()  # Borrar puntuaciones

                # Verificar si se hizo clic fuera de la tabla para cerrar
                if not close_area.collidepoint(mouse_pos):
                    return  # Cerrar la tabla

        # Dibujar la tabla de puntuaciones
        scores_surface = IMAGES['scores_bg'].copy()

        # Cargar puntuaciones
        scores = data_manager.get_top_scores()

        # Mostrar las 10 mejores puntuaciones con fuente más pequeña
        font = pygame.font.SysFont('Arial', 14)  # Reducido de 18 a 14
        y_offset = 100

        if not scores:
            no_scores_text = font.render("No hay puntuaciones guardadas", True, COLORS['white'])
            no_scores_rect = no_scores_text.get_rect(center=(200, 250))
            scores_surface.blit(no_scores_text, no_scores_rect)
        else:
            # Encabezados de la tabla
            headers = ["Pos", "Nombre", "Tuberías"]
            header_x_positions = [80, 150, 280]

            for i, header in enumerate(headers):
                header_text = font.render(header, True, (255, 255, 0))  # Amarillo para encabezados
                header_rect = header_text.get_rect(center=(header_x_positions[i], y_offset))
                scores_surface.blit(header_text, header_rect)

            y_offset += 25  # Espacio después de los encabezados

            # Mostrar las puntuaciones
            cell_height = 31
            for i, score_data in enumerate(scores[:10]):
                rank = i + 1
                name = score_data['name']
                score = score_data['score']

    # Determinar estilo según posición
                if rank == 1:
                    color = GOLD
                    font_used = top_font
                    bg_color = (50, 50, 0)  # fondo dorado oscuro
                elif rank == 2:
                    color = SILVER
                    font_used = top_font
                    bg_color = (60, 60, 60)  # fondo plateado oscuro
                elif rank == 3:
                    color = BRONZE
                    font_used = top_font
                    bg_color = (70, 40, 20)  # fondo bronce oscuro
                else:
                    color = COLORS['white']
                    font_used = font
                    bg_color = None

    # Fondo de celda para top 3
                if rank <= 3:
                    pygame.draw.rect(scores_surface, bg_color, (30, y_offset - 10, 340, 30), border_radius=6)

                center_y = y_offset + cell_height // 5
    # Posición
                pos_text = font_used.render(f"{rank}", True, color)
                pos_rect = pos_text.get_rect(center=(header_x_positions[0], center_y))
                scores_surface.blit(pos_text, pos_rect)

                display_name = name if len(name) <= 5 else name[:5]
                name_text = font_used.render(display_name, True, color)
                name_rect = name_text.get_rect(center=(header_x_positions[1], center_y))
                scores_surface.blit(name_text, name_rect)

                score_text = font_used.render(str(score), True, color)
                score_rect = score_text.get_rect(center=(header_x_positions[2], center_y))
                scores_surface.blit(score_text, score_rect)

                y_offset += cell_height

                # Separación visual después del top 3
                if rank == 3:
                    y_offset += 10  # espacio extra
                    pygame.draw.line(scores_surface, (100, 100, 100), (60, y_offset), (340, y_offset), 1)
                    y_offset += 10



        # Mostrar puntuación actual si existe
        current_score, current_name = load_current_score()
        if current_score > 0:
            current_text = font.render(f"Progreso actual de {current_name}: {current_score} tuberías", True, (255, 255, 0))
            current_rect = current_text.get_rect(center=(200, y_offset + 30))
            scores_surface.blit(current_text, current_rect)

        # Instrucción para cerrar
        close_font = pygame.font.SysFont('Arial', 14)
        close_text = close_font.render("Haz clic fuera para cerrar", True, COLORS['white'])
        close_rect = close_text.get_rect(center=(200, 460))
        scores_surface.blit(close_text, close_rect)

        # Dibujar la tabla en la pantalla
        SCREEN.blit(IMAGES['background'], (0, 0))  # Redibujar fondo
        SCREEN.blit(scores_surface, (scores_x, scores_y))

        # Dibujar el botón de borrar en la nueva posición centrada
        #SCREEN.blit(IMAGES['clear_button'], (clear_button_x, clear_button_y))

        pygame.display.update()
        FPSCLOCK.tick(FPS)

def mainGame(movementInfo, player_name):
    try:
        if os.path.exists('flappy_pobre_current_score.json'):
            os.remove('flappy_pobre_current_score.json')
            print("DEBUG: progreso temporal eliminado al iniciar partida.")
    except Exception as e:
        print(f"ERROR al limpiar progreso anterior: {e}")

    score = 0

    playerIndex = loopIter = 0
    playerIndexGen = movementInfo['playerIndexGen']
    playerx, playery = int(SCREENWIDTH * 0.2), movementInfo['playery']

    basex = movementInfo['basex']
    baseShift = IMAGES['base'].get_width() - IMAGES['background'].get_width()

    newPipe1 = getRandomPipe()
    newPipe2 = getRandomPipe()

    upperPipes = [
        {'x': SCREENWIDTH + 200, 'y': newPipe1[0]['y']},
        {'x': SCREENWIDTH + 200 + (SCREENWIDTH / 2), 'y': newPipe2[0]['y']},
    ]
    lowerPipes = [
        {'x': SCREENWIDTH + 200, 'y': newPipe1[1]['y']},
        {'x': SCREENWIDTH + 200 + (SCREENWIDTH / 2), 'y': newPipe2[1]['y']},
    ]

    pipeVelX = -4

    # Parámetros del jugador
    playerVelY = -9
    playerMaxVelY = 10
    playerMinVelY = -8
    playerAccY = 1
    playerRot = 45
    playerVelRot = 3
    playerRotThr = 20
    playerFlapAcc = -9
    playerFlapped = False


    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()

            if event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP) or event.type == MOUSEBUTTONDOWN:
                if playery > -2 * IMAGES['player'][0].get_height():
                    playerVelY = playerFlapAcc
                    playerFlapped = True
                    if 'wing' in SOUNDS:
                        SOUNDS['wing'].play()

        # Comprobar colisión
        crashTest = checkCrash({'x': playerx, 'y': playery, 'index': playerIndex}, upperPipes, lowerPipes)
        if crashTest[0]:
            try:
                if os.path.exists('flappy_pobre_current_score.json'):
                    os.remove('flappy_pobre_current_score.json')
                    print("DEBUG: progreso temporal eliminado tras colisión.")
            except:
                pass

            return {
                'y': playery,
                'groundCrash': crashTest[1],
                'basex': basex,
                'upperPipes': upperPipes,
                'lowerPipes': lowerPipes,
                'score': score,
                'playerVelY': playerVelY,
                'playerRot': playerRot
            }

        # Comprobar puntuación
        playerMidPos = playerx + IMAGES['player'][0].get_width() / 2
        for pipe in upperPipes:
            pipeMidPos = pipe['x'] + IMAGES['pipe'][0].get_width() / 2
            if pipeMidPos <= playerMidPos < pipeMidPos + 4:
                score += 1
                if 'point' in SOUNDS:
                    SOUNDS['point'].play()


        # Actualizar lógica del juego (rotación, gravedad, etc.)
        if (loopIter + 1) % 3 == 0:
            playerIndex = next(playerIndexGen)
        loopIter = (loopIter + 1) % 30
        basex = -((-basex + 100) % baseShift)

        if playerRot > -90:
            playerRot -= playerVelRot
        if playerVelY < playerMaxVelY and not playerFlapped:
            playerVelY += playerAccY
        if playerFlapped:
            playerFlapped = False
            playerRot = 45

        playerHeight = IMAGES['player'][playerIndex].get_height()
        playery += min(playerVelY, BASEY - playery - playerHeight)

        # Mover tuberías
        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            uPipe['x'] += pipeVelX
            lPipe['x'] += pipeVelX

        if len(upperPipes) > 0 and 0 < upperPipes[0]['x'] < 5:
            newPipe = getRandomPipe()
            upperPipes.append(newPipe[0])
            lowerPipes.append(newPipe[1])

        if len(upperPipes) > 0 and upperPipes[0]['x'] < -IMAGES['pipe'][0].get_width():
            upperPipes.pop(0)
            lowerPipes.pop(0)

        # Dibujar sprites y score
        SCREEN.blit(IMAGES['background'], (0, 0))
        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            SCREEN.blit(IMAGES['pipe'][0], (uPipe['x'], uPipe['y']))
            SCREEN.blit(IMAGES['pipe'][1], (lPipe['x'], lPipe['y']))

        SCREEN.blit(IMAGES['base'], (basex, BASEY))
        showScore(score)

        font = pygame.font.SysFont(None, 24)
        name_text = font.render(f"Jugador: {player_name}", True, (255, 255, 255))
        name_rect = name_text.get_rect(center=(SCREENWIDTH / 2, 30))
        SCREEN.blit(name_text, name_rect)

        visibleRot = playerRotThr if playerRot > playerRotThr else playerRot
        playerSurface = pygame.transform.rotate(IMAGES['player'][playerIndex], visibleRot)
        SCREEN.blit(playerSurface, (playerx, playery))

        pygame.display.update()
        FPSCLOCK.tick(FPS)


def showGameOverScreen(crashInfo, player_name):
    stop_music()
    score = crashInfo['score']
    playerx = SCREENWIDTH * 0.2
    playery = crashInfo['y']
    playerHeight = IMAGES['player'][0].get_height()
    playerVelY = crashInfo['playerVelY']
    playerAccY = 2
    playerRot = crashInfo['playerRot']
    playerVelRot = 7
    basex = crashInfo['basex']
    upperPipes, lowerPipes = crashInfo['upperPipes'], crashInfo['lowerPipes']

    final_name = player_name.strip() or "Invitado"

    # Validar email antes de guardar
    global player_email
    player_email = player_email.strip()

    if not player_email or "@" not in player_email:
        player_email = f"{final_name.lower()}@anonimo"

    data_manager.update_score(final_name, player_email, score)


    if 'hit' in SOUNDS:
        SOUNDS['hit'].play()
    if not crashInfo['groundCrash'] and 'die' in SOUNDS:
        SOUNDS['die'].play()

    # Botones
    button_width, button_height = 200, 50
    spacing = 20
    buttons = [
        {"label": "Volver a jugar", "action": "retry"},
        {"label": "Ir a inicio", "action": "inicio"},
        {"label": "Menú principal", "action": "menu"}
    ]
    button_rects = []
    for i, btn in enumerate(buttons):
        x = (SCREENWIDTH - button_width) // 2
        y = 400 + i * (button_height + spacing)
        rect = pygame.Rect(x, y, button_width, button_height)
        button_rects.append((rect, btn["action"]))

    while True:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                for rect, action in button_rects:
                    if rect.collidepoint(mouse_pos):
                        return action

        # Animación de caída del jugador
        if playery + playerHeight < BASEY - 1:
            playery += min(playerVelY, BASEY - playery - playerHeight)
            if playerVelY < 15:
                playerVelY += playerAccY
            if not crashInfo['groundCrash']:
                if playerRot > -90:
                    playerRot -= playerVelRot


        # Fondo y elementos
        # Fondo y elementos del escenario
        SCREEN.blit(IMAGES['background'], (0, 0))
        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            SCREEN.blit(IMAGES['pipe'][0], (uPipe['x'], uPipe['y']))
            SCREEN.blit(IMAGES['pipe'][1], (lPipe['x'], lPipe['y']))
        SCREEN.blit(IMAGES['base'], (basex, BASEY))

        # 🕹️ Dibujar jugador primero (quedará detrás del panel)
        playerSurface = pygame.transform.rotate(IMAGES['player'][1], playerRot)
        SCREEN.blit(playerSurface, (playerx, playery))

        # 🔳 Panel semitransparente (encima del jugador)
        overlay_width = 350
        overlay_height = 380
        overlay_surf = pygame.Surface((overlay_width, overlay_height), pygame.SRCALPHA)

        # Fondo semitransparente negro, igual que tabla de puntuaciones
        panel_color = (0, 0, 0, 200)  # Más opaco para resaltar
        border_color = (255, 255, 255)
        border_radius = 12  # Esquinas redondeadas suaves

        # Relleno
        pygame.draw.rect(
            overlay_surf,
            panel_color,
            (0, 0, overlay_width, overlay_height),
            border_radius=border_radius
        )

        # Borde blanco
        pygame.draw.rect(
            overlay_surf,
            border_color,
            (0, 0, overlay_width, overlay_height),
            width=3,
            border_radius=border_radius
        )

        # Posicionar el panel en el centro de la pantalla
        overlay_x = (SCREENWIDTH - overlay_width) // 2
        overlay_y = 250
        SCREEN.blit(overlay_surf, (overlay_x, overlay_y))


        # 🏁 Título "GAME OVER"
        font_title = pygame.font.SysFont(None, 72)
        title_text = font_title.render("GAME OVER", True, (255, 255, 255))
        title_rect = title_text.get_rect(center=(SCREENWIDTH // 2, 310))
        SCREEN.blit(title_text, title_rect)

        # 🧮 Texto "Tuberías superadas"
        font_info = pygame.font.SysFont(None, 36)
        info_text = font_info.render(f"Tuberías superadas: {score}", True, (255, 255, 255))
        info_rect = info_text.get_rect(center=(SCREENWIDTH // 2, title_rect.bottom + 30))
        SCREEN.blit(info_text, info_rect)

        # 🎯 Score visual (sigue arriba)
        showScore(score)

        # 🔘 Botones sobre todo lo anterior
        for i, (rect, action) in enumerate(button_rects):
            pygame.draw.rect(SCREEN, (100, 100, 200), rect)
            pygame.draw.rect(SCREEN, (255, 255, 255), rect, 2)
            btn_font = pygame.font.SysFont(None, 28)
            text = btn_font.render(buttons[i]["label"], True, (255, 255, 255))
            text_rect = text.get_rect(center=rect.center)
            SCREEN.blit(text, text_rect)


        pygame.display.update()
        FPSCLOCK.tick(FPS)

def playerShm(playerShm):
    """Oscila el valor de playerShm['val'] entre 8 y -8"""
    if abs(playerShm['val']) == 8:
        playerShm['dir'] *= -1

    if playerShm['dir'] == 1:
        playerShm['val'] += 1
    else:
        playerShm['val'] -= 1

def getRandomPipe():
    gapY = random.randrange(0, int(BASEY * 0.6 - PIPEGAPSIZE))
    gapY += int(BASEY * 0.2)
    pipeHeight = IMAGES['pipe'][0].get_height()
    pipeX = SCREENWIDTH + 10

    return [
        {'x': pipeX, 'y': gapY - pipeHeight},  # tubería superior
        {'x': pipeX, 'y': gapY + PIPEGAPSIZE},  # tubería inferior
    ]

def showScore(score):
    """Muestra el puntaje actual con fondo semitransparente"""
    score_digits = list(str(score))
    total_width = sum(IMAGES[d].get_width() for d in score_digits)
    x_offset = (SCREENWIDTH - total_width) / 2
    y_offset = SCREENHEIGHT * 0.1

    # Fondo oscuro translúcido
    bg_width = total_width + 40
    bg_height = IMAGES['0'].get_height() + 20
    bg_rect = pygame.Surface((bg_width, bg_height), pygame.SRCALPHA)
    bg_rect.fill((0, 0, 0, 120))  # negro con transparencia

    SCREEN.blit(bg_rect, (x_offset - 20, y_offset - 10))

    for d in score_digits:
        SCREEN.blit(IMAGES[d], (x_offset, y_offset))
        x_offset += IMAGES[d].get_width()


def checkCrash(player, upperPipes, lowerPipes):
    """Devuelve True si el jugador colisiona con la base o las tuberías."""
    pi = player['index']
    player['w'] = IMAGES['player'][0].get_width()
    player['h'] = IMAGES['player'][0].get_height()

    # Si el jugador choca contra el suelo
    if player['y'] + player['h'] >= BASEY - 1:
        return [True, True]
    else:
        # Determinar el tamaño de colisión según el tipo de jugador
        if 'redbox' in PLAYERS_LIST[pi][0]:  # Si es el bloque rojo
            collision_size = 25  # Área de colisión más pequeña para el bloque rojo
        else:
            collision_size = 40  # Área de colisión normal para otros bloques

        # Crear un rectángulo de colisión más pequeño que el visual
        collision_offset = (player['w'] - collision_size) / 2
        playerRect = pygame.Rect(
            player['x'] + collision_offset,
            player['y'] + collision_offset,
            collision_size, collision_size
        )
        pipeW = IMAGES['pipe'][0].get_width()
        pipeH = IMAGES['pipe'][0].get_height()

        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            # Rectángulos de tubería superior e inferior
            uPipeRect = pygame.Rect(uPipe['x'], uPipe['y'], pipeW, pipeH)
            lPipeRect = pygame.Rect(lPipe['x'], lPipe['y'], pipeW, pipeH)

            # Máscaras de colisión del jugador y tuberías superior/inferior
            pHitMask = HITMASKS['player'][pi]
            uHitmask = HITMASKS['pipe'][0]
            lHitmask = HITMASKS['pipe'][1]

            # Si el jugador colisiona con tubería superior o inferior
            uCollide = pixelCollision(playerRect, uPipeRect, pHitMask, uHitmask)
            lCollide = pixelCollision(playerRect, lPipeRect, pHitMask, lHitmask)

            if uCollide or lCollide:
                return [True, False]

    return [False, False]

def pixelCollision(rect1, rect2, hitmask1, hitmask2):
    """Comprueba si dos objetos colisionan y no solo sus rectángulos"""
    rect = rect1.clip(rect2)

    if rect.width == 0 or rect.height == 0:
        return False

    x1, y1 = rect.x - rect1.x, rect.y - rect1.y
    x2, y2 = rect.x - rect2.x, rect.y - rect2.y

    for x in xrange(rect.width):
        for y in xrange(rect.height):
            if hitmask1[x1 + x][y1 + y] and hitmask2[x2 + x][y2 + y]:
                return True
    return False

def getHitmask(image):
    """Devuelve una máscara de colisión usando el alfa de una imagen."""
    mask = []
    for x in xrange(image.get_width()):
        mask.append([])
        for y in xrange(image.get_height()):
            mask[x].append(bool(image.get_at((x, y))[3]))
    return mask

def getReducedHitmask(image):
    """Devuelve una máscara de colisión reducida para el jugador."""
    # Obtener dimensiones de la imagen
    width, height = image.get_width(), image.get_height()

    # Determinar el tamaño de colisión según el tipo de imagen
    if 'redbox' in str(image):  # Si es el bloque rojo
        collision_size = 25  # Tamaño de colisión más pequeño para el bloque rojo
    else:
        collision_size = 40  # Tamaño de colisión normal para otros bloques

    # Crear una máscara más pequeña (centrada)
    offset_x = (width - collision_size) // 2
    offset_y = (height - collision_size) // 2

    mask = []
    for x in xrange(width):
        mask.append([])
        for y in xrange(height):
            # Solo considerar píxeles dentro del área de colisión reducida
            if offset_x <= x < offset_x + collision_size and offset_y <= y < offset_y + collision_size:
                mask[x].append(bool(image.get_at((x, y))[3]))
            else:
                mask[x].append(False)  # Fuera del área de colisión

    return mask

def main(player_email=""):
    """Función principal para ejecutar Flappy Bird desde el menú"""
    print(f"Jugando Flappy Bird con email: {player_email}")

if __name__ == "__main__":
    # Si se ejecuta directamente, obtener email de argumentos
    email_from_args = sys.argv[1] if len(sys.argv) > 1 else ""
    main(email_from_args)