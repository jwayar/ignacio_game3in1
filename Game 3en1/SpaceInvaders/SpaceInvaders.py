import pygame
import random
import sys
import os
import time
import json
from datetime import datetime

player_email_global = ""
player_email = ""

# Permitir recibir el email desde menu.py (por sys.argv o variable)
if len(sys.argv) > 1:
    player_email = sys.argv[1].strip()
    print(f"DEBUG: Email recibido -> {player_email}")
else:
    player_email = player_email_global

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SOUND_DIR = os.path.join(SCRIPT_DIR, "sonidos")
IMAGE_DIR = os.path.join(SCRIPT_DIR, "imagenes")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from notificaciones.email_notifier import send_email_notification
except ModuleNotFoundError as e:
    print(f"Error importando notificaciones: {e}")
    send_email_notification = None

print("DEBUG: __file__ =", __file__)
print("DEBUG: SpaceInvaders BASE_DIR =", BASE_DIR)
print("DEBUG: sys.path[0:5] =", sys.path[0:5])


GLOBAL_SCORES_PATH = os.path.join(BASE_DIR, "data", "global_scores.json")
GAME_IDENTIFIER = "SPACEINVADERS"
# Crear la carpeta "data" si no existe
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)

player_email = ""
# Permitir recibir el email desde menu.py (por sys.argv o variable)
if len(sys.argv) > 1:
    player_email = sys.argv[1].strip()
    print(f"DEBUG: Email recibido -> {player_email}")


# Sistema de datos
class DataManager:
    """Gestiona la carga y guardado de puntajes en el archivo JSON global."""
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
        with open(self.scores_path, 'w', encoding='utf-8') as file:
            json.dump(all_data, file, indent=4)

    def load_game_scores(self):
        all_data = self._read_all_data()
        game_scores = all_data.get(self.game_id, [])
        game_scores.sort(key=lambda x: x['score'], reverse=True)
        return game_scores[:10]

    def update_score(self, name, email, score):
        if not email or "@" not in email:
            return False, 0

        all_data = self._read_all_data()
        if self.game_id not in all_data:
            all_data[self.game_id] = []

        game_scores = all_data[self.game_id]
        prev_top = game_scores[0].copy() if game_scores else None
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

        if not record_found:
            game_scores.append({
                "name": name,
                "email": email,
                "score": score,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        game_scores.sort(key=lambda x: x['score'], reverse=True)
        all_data[self.game_id] = game_scores[:10]
        self._save_all_data(all_data)

        new_top = game_scores[0] if game_scores else None

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
                except Exception as e:
                    print(f"Error al enviar notificación: {e}")

        return True, old_score

    def get_top_scores(self):
        return self.load_game_scores()


data_manager = DataManager()

# Inicializacion de Pygame
pygame.init()
try:
    # Inicialización del mixer
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
except Exception as e:
    print("Advertencia: no se pudo inicializar el mixer:", e)

# Configuracion de la pantalla
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders")
clock = pygame.time.Clock()
FPS = 60

# Configuracion de los colores
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 220, 0)
RED = (220, 60, 60)
YELLOW = (230, 230, 80)
BLUE = (100, 150, 255)
GRAY = (60, 60, 60)
HIGHLIGHT = (180, 180, 180)

# fuentes de texto
font_small = pygame.font.SysFont("consolas", 18)
font_med = pygame.font.SysFont("consolas", 26)
font_big = pygame.font.SysFont("consolas", 48)

# RUTA BASE PARA ARCHIVOS DE SONIDO
SOUND_DIR = os.path.join(SCRIPT_DIR, "sonidos")

# Archivos de música (.mp3)
menu_music_file = "menu.mp3"
# game_music_file = "game.mp3" <--- ELIMINADO para evitar confusiones en las funciones

# Volúmenes predederminados
menu_volume = 0.3
game_volume = 0.6 # Este volumen controlará los efectos de sonido en el juego

# ******************************************************************************
# ********************** SECCIÓN DE CARGA DE SONIDOS (.wav) *********************
# ******************************************************************************

# Variables globales para almacenar los objetos Sound de Pygame
SOUNDS = {}
def load_sounds():
    """Carga todos los archivos .wav como objetos pygame.mixer.Sound."""
    global SOUNDS

    # Lista de archivos WAV a cargar (SOLO EFECTOS DE JUEGO)
    sound_files = [
        "0.wav", "1.wav", "2.wav", "3.wav",
        "invaderkilled.wav", "shipexplosion.wav",
        "shoot.wav", "shoot2.wav"
    ]

    for filename in sound_files:
        path = os.path.join(SOUND_DIR, filename)
        key = filename.split('.')[0] # Usar el nombre sin extensión como clave (ej: "shoot")
        if os.path.exists(path):
            try:
                SOUNDS[key] = pygame.mixer.Sound(path)
                # Establece el volumen inicial para los efectos
                SOUNDS[key].set_volume(game_volume)
            except pygame.error as e:
                print(f"Advertencia: No se pudo cargar el sonido {filename}: {e}")
        else:
            print(f"Advertencia: No se encontró el archivo de sonido: {path}")

# Llama a la función de carga
load_sounds()

# Función de conveniencia para reproducir un efecto de sonido
def play_sound(sound_key):
    """Reproduce el sonido asociado a la clave (ej: 'shoot', 'invaderkilled', '1')."""
    if sound_key in SOUNDS:
        try:
            SOUNDS[sound_key].play()
        except pygame.error as e:
            pass

# ------------------- Reproducción de música (.mp3) -------------------
def play_music_with_fade(file, volume=0.6, loop=True, fade_ms=800):
    """Carga y reproduce música con fade-out/fade-in. Ignora 'game.mp3'."""
    # SÓLO se permite reproducir si es la música del menú
    if file != menu_music_file:
        stop_music() # Asegura que si se llama con 'game.mp3' se detiene todo
        return

    path = os.path.join(SOUND_DIR, file)
    if os.path.exists(path):
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.fadeout(fade_ms)
                pygame.time.delay(fade_ms)
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(-1 if loop else 0, fade_ms=fade_ms)
        except Exception as e:
            print("Error al reproducir música:", e)
    else:
        print(f"No se encontró {file} en {path}")

def play_music_instant(file, volume=0.6, loop=True):
    """Reproduce inmediatamente (sin fade). Ignora 'game.mp3'."""
    if file != menu_music_file:
        stop_music()
        return

    path = os.path.join(SOUND_DIR, file)
    if os.path.exists(path):
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(-1 if loop else 0)
        except Exception as e:
            print("Error al reproducir música (instant):", e)
    else:
        print(f"No se encontró {file} en {path}")

def stop_music(fade_ms=0):
    try:
        if pygame.mixer.music.get_busy() and fade_ms > 0:
            pygame.mixer.music.fadeout(fade_ms)
        else:
            pygame.mixer.music.stop()
    except Exception:
        pass

# ******************************************************************************
# ********************** SECCIÓN DE CARGA DE GRÁFICOS ********************
# ******************************************************************************

# RUTA BASE PARA ARCHIVOS DE GRÁFICOS (carpeta 'graficos')
GRAPHICS_DIR = os.path.join(SCRIPT_DIR, "graficos")
GRAPHICS = {}

def load_graphics():
    """Carga todos los archivos .png como objetos pygame.Surface."""
    global GRAPHICS

    image_files = [
        "enemy1_1.png", "enemy1_2.png",
        "enemy2_1.png", "enemy2_2.png",
        "enemy3_1.png", "enemy3_2.png",
        "enemylaser.png",
        "explosionblue.png",
        "explosiongreen.png",
        "explosionpurple.png",
        "laser.png", "ship.png"
    ]

    for filename in image_files:
        path = os.path.join(GRAPHICS_DIR, filename)
        key = filename.split('.')[0]
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                GRAPHICS[key] = img
            except pygame.error as e:
                print(f"Advertencia: No se pudo cargar la imagen {filename}: {e}")
        # else:
            # print(f"Advertencia: No se encontró el archivo de imagen: {path}") # Desactivado por defecto


# Llama a la función de carga de gráficos
load_graphics()

# ------------------- Fondo de estrellas -------------------
stars = [[random.randint(0, WIDTH), random.randint(0, HEIGHT)] for _ in range(70)]

def update_stars():
    for s in stars:
        s[1] += 1
        if s[1] > HEIGHT:
            s[0] = random.randint(0, WIDTH)
            s[1] = 0

def draw_background():
    screen.fill(BLACK)
    for s in stars:
        pygame.draw.circle(screen, WHITE, (s[0], s[1]), 1)

# ------------------- Utilidades de texto -------------------
def draw_text_center(text, font_obj, color, x, y):
    surf = font_obj.render(text, True, color)
    rect = surf.get_rect(center=(x, y))
    screen.blit(surf, rect)
    return rect

def draw_text_left(text, font_obj, color, x, y):
    surf = font_obj.render(text, True, color)
    rect = surf.get_rect(topleft=(x, y))
    screen.blit(surf, rect)
    return rect

# ------------------- Enemigos -------------------
def create_enemies(rows=5, cols=10):
    enemies = []

    # Redimensionamiento de Sprites (Solo se hace una vez)
    SCALE_FACTOR = 0.25
    enemy_width = 12
    enemy_height = 12

    if "enemy1_1" in GRAPHICS:
        enemy_width = int(GRAPHICS["enemy1_1"].get_width() * SCALE_FACTOR)
        enemy_height = int(GRAPHICS["enemy1_1"].get_height() * SCALE_FACTOR)

        GRAPHICS["enemy1_1_SCALED"] = pygame.transform.scale(GRAPHICS["enemy1_1"], (enemy_width, enemy_height))
        GRAPHICS["enemy1_2_SCALED"] = pygame.transform.scale(GRAPHICS["enemy1_2"], (enemy_width, enemy_height))

        GRAPHICS["enemy2_1_SCALED"] = pygame.transform.scale(GRAPHICS["enemy2_1"], (enemy_width, enemy_height))
        GRAPHICS["enemy2_2_SCALED"] = pygame.transform.scale(GRAPHICS["enemy2_2"], (enemy_width, enemy_height))

        GRAPHICS["enemy3_1_SCALED"] = pygame.transform.scale(GRAPHICS["enemy3_1"], (enemy_width, enemy_height))
        GRAPHICS["enemy3_2_SCALED"] = pygame.transform.scale(GRAPHICS["enemy3_2"], (enemy_width, enemy_height))

        GRAPHICS["explosionpurple_SCALED"] = pygame.transform.scale(GRAPHICS["explosionpurple"], (enemy_width, enemy_height))
        GRAPHICS["explosionblue_SCALED"] = pygame.transform.scale(GRAPHICS["explosionblue"], (enemy_width, enemy_height))
        GRAPHICS["explosiongreen_SCALED"] = pygame.transform.scale(GRAPHICS["explosiongreen"], (enemy_width, enemy_height))

    spacing_factor = 10
    row_spacing = 12

    total_block_width = (cols * enemy_width) + ((cols - 1) * spacing_factor)
    start_x = (WIDTH - total_block_width) // 2
    start_y = 50

    for r in range(rows):
        for c in range(cols):
            x = start_x + c * (enemy_width + spacing_factor)
            y = start_y + r * (enemy_height + row_spacing)

            enemies.append({
                "rect": pygame.Rect(x, y, enemy_width, enemy_height),
                "row_index": r,
                "exploding": False,
                "explosion_timer": 0
            })

    return enemies

# ------------------- Pantalla de carga y fade -------------------
def loading_screen(seconds=1.0):
    t0 = time.time()
    while time.time() - t0 < seconds:
        clock.tick(FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        update_stars()
        draw_background()
        draw_text_center("CARGANDO...", font_big, WHITE, WIDTH//2, HEIGHT//2 - 20)
        frac = (time.time() - t0) / seconds
        if frac > 1: frac = 1
        bw = 400; bh = 16
        bx = WIDTH//2 - bw//2; by = HEIGHT//2 + 20
        pygame.draw.rect(screen, GRAY, (bx, by, bw, bh), border_radius=6)
        pygame.draw.rect(screen, GREEN, (bx, by, int(bw * frac), bh), border_radius=6)
        pygame.display.flip()

def fade_out_screen(duration_ms=350):
    fade = pygame.Surface((WIDTH, HEIGHT))
    fade.fill(BLACK)
    steps = 20
    delay = max(1, duration_ms // steps)
    for i in range(steps+1):
        alpha = int((i/steps) * 255)
        fade.set_alpha(alpha)
        update_stars()
        draw_background()
        screen.blit(fade, (0, 0))
        pygame.display.flip()
        pygame.time.delay(delay)

# ------------------- Ajuste de volumen (TAB + flechas) -------------------
def adjust_volumes():
    global menu_volume, game_volume
    selected = 0
    # SINCRONIZACIÓN: Carga instantánea de menu.mp3 para probar volumen
    # Usamos un archivo dummy para simular el volumen del juego (que ahora son los efectos)
    test_file = menu_music_file if selected == 0 else menu_music_file # Usamos menu.mp3 para simular ambos, pero solo si estamos en el menú
    play_music_instant(test_file, menu_volume)

    adjusting = True
    while adjusting:
        clock.tick(FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_TAB:
                    selected = 1 - selected
                    # SINCRONIZACIÓN: Carga instantánea de la música para probar volumen
                    if selected == 0:
                        # Si cambiamos a menú, cargamos la música
                        play_music_instant(menu_music_file, menu_volume)
                    else:
                        # Si cambiamos a juego, detenemos la música (solo controlamos efectos)
                        stop_music()
                        # Opcional: Probar un efecto de sonido para el volumen del juego
                        # play_sound("shoot")

                elif ev.key == pygame.K_LEFT:
                    if selected == 0:
                        menu_volume = max(0.0, round(menu_volume - 0.05, 2))
                        pygame.mixer.music.set_volume(menu_volume)
                    else:
                        game_volume = max(0.0, round(game_volume - 0.05, 2))
                        # Aplicar el cambio de volumen a los efectos de sonido
                        for s in SOUNDS.values(): s.set_volume(game_volume)

                elif ev.key == pygame.K_RIGHT:
                    if selected == 0:
                        menu_volume = min(1.0, round(menu_volume + 0.05, 2))
                        pygame.mixer.music.set_volume(menu_volume)
                    else:
                        game_volume = min(1.0, round(game_volume + 0.05, 2))
                        # Aplicar el cambio de volumen a los efectos de sonido
                        for s in SOUNDS.values(): s.set_volume(game_volume)

                elif ev.key == pygame.K_ESCAPE:
                    # Al salir, asegurar que la música del menú se esté reproduciendo
                    play_music_with_fade(menu_music_file, menu_volume, fade_ms=400)
                    adjusting = False

        update_stars()
        draw_background()
        draw_text_center("AJUSTAR VOLUMEN", font_big, YELLOW, WIDTH//2, HEIGHT//6)
        draw_text_center("TAB = cambiar MENÚ/EFECTOS | ← / → = ajustar | ESC = volver", font_small, BLUE, WIDTH//2, HEIGHT//6 + 40)
        draw_text_center(f"{'MENÚ' if selected == 0 else 'EFECTOS'}: {int((menu_volume if selected==0 else game_volume)*100)}%", font_med, WHITE, WIDTH//2, HEIGHT//2)
        pygame.display.flip()

# - Tabla de puntajes
def show_scores_screen():
    play_music_with_fade(menu_music_file, menu_volume, fade_ms=400)
    scores = data_manager.load_game_scores()
    showing = True

    while showing:
        clock.tick(FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                showing = False

        update_stars()
        draw_background()

        draw_text_center("TABLA DE PUNTAJES", font_big, YELLOW, WIDTH // 2, 60)
        draw_text_center(" TOP 3 JUGADORES", font_med, YELLOW, WIDTH // 2, 120)

        start_y = 160
        for i, it in enumerate(scores[:3]):
            rank = i + 1
            line = f"{rank:02d}. {it['name']} — {it['score']}"

            if rank == 1: color = (255, 215, 0)
            elif rank == 2: color = (192, 192, 192)
            elif rank == 3: color = (205, 127, 50)

            rect_width = 400; rect_height = 45
            rect_x = WIDTH // 2 - rect_width // 2
            rect_y = start_y + i * (rect_height + 10)
            pygame.draw.rect(screen, (30, 30, 30), (rect_x, rect_y, rect_width, rect_height), border_radius=8)
            pygame.draw.rect(screen, color, (rect_x, rect_y, rect_width, rect_height), 2, border_radius=8)

            font_top = pygame.font.SysFont("consolas", 32, bold=True)
            draw_text_center(line, font_top, color, WIDTH // 2, rect_y + rect_height // 2)

        start_y += 3 * 55 + 20
        draw_text_center("OTROS JUGADORES", font_med, WHITE, WIDTH // 2, start_y)

        for i, it in enumerate(scores[3:10]):
            rank = i + 4
            line = f"{rank:02d}. {it['name']} — {it['score']}"
            color = WHITE
            draw_text_center(line, font_small, color, WIDTH // 2, start_y + 40 + i * 25)

        draw_text_center("Clic o tecla para volver", font_small, BLUE, WIDTH // 2, HEIGHT - 40)

        pygame.display.flip()


# Game Over pantalla
def game_over_screen_with_input(score):
    global player_email
    stop_music() # Detiene cualquier música (solo menu.mp3 si se está reproduciendo)
    name = ""
    entering_name = True
    prompt = "ESCRIBÍ TU NOMBRE (ENTER para guardar):"

    while entering_name:
        clock.tick(FPS)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN:
                    if name.strip() != "":
                        final_name = name.strip()[:5]
                        global player_email
                        player_email = player_email.strip()

                        if not player_email or "@anonimo" in player_email:
                            pass
                        elif score > 0:
                            data_manager.update_score(final_name, player_email, score)

                        entering_name = False

                elif ev.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                else:
                    if len(name) < 5 and ev.unicode.isalnum():
                        name += ev.unicode.upper()


        update_stars()
        draw_background()
        draw_text_center("GAME OVER", font_big, RED, WIDTH//2, HEIGHT//2 - 140)
        draw_text_center(f"Puntos: {score}", font_med, WHITE, WIDTH//2, HEIGHT//2 - 90)
        draw_text_center(prompt, font_small, YELLOW, WIDTH//2, HEIGHT//2 - 40)

        box_rect = pygame.Rect(WIDTH//2 - 220, HEIGHT//2 - 20, 440, 40)
        pygame.draw.rect(screen, WHITE, box_rect, border_radius=6)

        txt_surf = font_med.render(name, True, BLACK)
        screen.blit(txt_surf, (box_rect.x + 8, box_rect.y + 4))
        draw_text_center("", font_small, GRAY, WIDTH//2, HEIGHT//2 + 40)
        pygame.display.flip()

    buttons = [
        {"label": "Jugar de nuevo", "rect": pygame.Rect(WIDTH//2 - 160, HEIGHT//2 + 60, 320, 54), "color": GREEN, "action": "retry"},
        {"label": "Volver al menú", "rect": pygame.Rect(WIDTH//2 - 160, HEIGHT//2 + 130, 320, 54), "color": BLUE, "action": "menu"},
        {"label": "Menú principal", "rect": pygame.Rect(WIDTH//2 - 160, HEIGHT//2 + 200, 320, 54), "color": RED, "action": "main_menu"}
    ]

    showing = True
    while showing:
        clock.tick(FPS)
        mx, my = pygame.mouse.get_pos()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN:
                for b in buttons:
                    if b["rect"].collidepoint(ev.pos):
                        if b["action"] == "main_menu":
                            stop_music()
                            pygame.quit()
                            sys.exit()

                        if b["action"] != "retry":
                             # Al volver al menú, SÍ queremos la música del menú
                             play_music_with_fade(menu_music_file, menu_volume, fade_ms=400)
                        return b["action"]

        update_stars()
        draw_background()
        draw_text_center("GAME OVER", font_big, RED, WIDTH//2, HEIGHT//2 - 120)
        draw_text_center(f"Puntos guardados: {score}", font_med, WHITE, WIDTH//2, HEIGHT//2 - 60)

        for b in buttons:
            color = b["color"]
            if b["rect"].collidepoint(mx, my):
                color = (min(color[0]+40,255), min(color[1]+40,255), min(color[2]+40,255))
            pygame.draw.rect(screen, color, b["rect"], border_radius=8)
            draw_text_center(b["label"], font_med, BLACK, b["rect"].centerx, b["rect"].centery)

        pygame.display.flip()

# ***********************************************************************************
# ************* VARIABLES GLOBALES DE CONTROL DE OLEADA DE PROYECTO BETA ************
# ***********************************************************************************
# Variables Globales del Proyecto Beta para la Sincronización de Oleada
moveTime = 0        # Índice del sonido de movimiento actual (0 a 3)
moveTimeCurrent = 25 # Retardo inicial en frames entre movimientos
moveTimeBase = 25    # Retardo inicial (se usa para resetear moveTimeCurrent)

# juego principal
def main_game():
    """
    Función principal del juego (minijuego).
    Lógica de oleadas, aceleración y sonido sincronizado (Proyecto Beta).
    """

    global moveTime, moveTimeCurrent, moveTimeBase

    fade_out_screen(200)
    loading_screen()
    # SINCRONIZACIÓN: Música del juego - AHORA SOLO SE DETIENE LA MÚSICA
    stop_music(fade_ms=400)

    # Inicialización de objetos
    if "ship" in GRAPHICS:
        ship_width = GRAPHICS["ship"].get_width()
        ship_height = GRAPHICS["ship"].get_height()
    else:
        ship_width = 50
        ship_height = 20

    player = pygame.Rect(WIDTH//2 - ship_width//2, HEIGHT - 60, ship_width, ship_height)
    bullets = []
    enemy_bullets = []
    enemies = create_enemies(cols=10)
    direction = 1
    score = 0
    player_lives = 3
    running = True

    # Lógica de Animación
    animation_counter = 0
    animation_speed = 30
    EXPLOSION_DURATION = 15

    # Variables de Disparo del Jugador
    player_can_shoot = True
    player_shot_delay = 0
    PLAYER_SHOT_DELAY_MAX = 30

    # Variables de Disparo del Enemigo (Cadencia dinámica)
    ENEMY_SHOT_DELAY_MIN = 20
    ENEMY_SHOT_DELAY_MAX = 120
    enemy_shot_timer = 0

    # Variables de Parpadeo de Invulnerabilidad
    hit_time = 0
    RESPAWN_DELAY = 1200  # ms de invulnerabilidad tras ser golpeado
    last_move_time = pygame.time.get_ticks()

    while running:
        clock.tick(FPS)
        now = pygame.time.get_ticks()

        # --- Lógica de Oleada (Basada en moveTime) ---
        active_enemies = [en_obj for en_obj in enemies if not en_obj["exploding"]]

        # 1. Aceleración Automática (update_speed)
        if active_enemies:
            remaining_ratio = len(active_enemies) / (10 * 5) # 50 enemigos iniciales
            moveTimeCurrent = max(1, int(moveTimeBase * remaining_ratio))

        # 2. Control de la Sincronización Musical y Movimiento
        target_move_ms = moveTimeCurrent * (1000/FPS)

        if now - last_move_time > target_move_ms:
            last_move_time = now

            # Mover enemigos y actualizar el sonido
            if active_enemies:
                # SINCRONIZACIÓN: Toca el sonido de movimiento '0', '1', '2', '3'
                play_sound(str(moveTime))
                moveTime = (moveTime + 1) % 4

                # Movimiento lateral
                move_down_pending = False
                for en_obj in active_enemies:
                    en = en_obj["rect"]
                    # Paso lateral de 6 píxeles (corregido)
                    en.x += 6 * direction
                    if en.right >= WIDTH - 10 or en.left <= 10:
                        move_down_pending = True

                # Movimiento hacia abajo
                if move_down_pending:
                    direction *= -1
                    for en_obj in active_enemies:
                        en_obj["rect"].y += 10

        # Actualizar Contadores de Animación
        animation_counter += 1
        if animation_counter >= animation_speed:
            animation_counter = 0

        animation_frame = 0
        if animation_counter >= animation_speed // 2:
            animation_frame = 1

        # Eventos
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()

        # Movimiento del Jugador
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player.left > 0:
            player.x -= 7
        if keys[pygame.K_RIGHT] and player.right < WIDTH:
            player.x += 7

        # Control de Disparo del Jugador
        if not player_can_shoot:
            player_shot_delay += 1
            if player_shot_delay >= PLAYER_SHOT_DELAY_MAX:
                player_can_shoot = True
                player_shot_delay = 0

        if keys[pygame.K_SPACE] and len(bullets) < 5 and player_can_shoot:
            if "laser" in GRAPHICS:
                laser_width = GRAPHICS["laser"].get_width()
                laser_height = GRAPHICS["laser"].get_height()
            else:
                laser_width = 4
                laser_height = 10

            bullets.append(pygame.Rect(player.centerx - laser_width//2, player.top, laser_width, laser_height))
            play_sound("shoot")
            player_can_shoot = False

        # --- Disparo de los enemigos (Cadencia dinámica) ---
        if active_enemies:
            # Cadencia de disparo dinámica
            remaining_ratio = len(active_enemies) / max(1, 10 * 5)
            dynamic_delay = int(ENEMY_SHOT_DELAY_MIN + (ENEMY_SHOT_DELAY_MAX - ENEMY_SHOT_DELAY_MIN) * remaining_ratio)

            enemy_shot_timer += 1
            if enemy_shot_timer >= dynamic_delay:
                shooter_obj = random.choice(active_enemies)
                shooter = shooter_obj["rect"]

                if "enemylaser" in GRAPHICS:
                    e_laser_width = GRAPHICS["enemylaser"].get_width()
                    e_laser_height = GRAPHICS["enemylaser"].get_height()
                else:
                    e_laser_width = 4
                    e_laser_height = 10

                enemy_bullets.append(pygame.Rect(shooter.centerx - e_laser_width//2, shooter.bottom, e_laser_width, e_laser_height))
                play_sound("shoot2")
                enemy_shot_timer = 0 # Reinicia el temporizador

        # Colisión de balas del jugador y enemigos
        for b in bullets[:]:
            b.y -= 8
            if b.bottom < 0:
                bullets.remove(b)
                continue

            hit_enemy_obj = None
            for i, en_obj in enumerate(enemies):
                if not en_obj["exploding"] and b.colliderect(en_obj["rect"]):
                    hit_enemy_obj = en_obj
                    break

            if hit_enemy_obj:
                bullets.remove(b)
                score += 10
                play_sound("invaderkilled")

                hit_enemy_obj["exploding"] = True
                hit_enemy_obj["explosion_timer"] = EXPLOSION_DURATION

                continue

        # Actualización de la explosión y eliminación de enemigos
        for en_obj in enemies[:]:
            if en_obj["exploding"]:
                en_obj["explosion_timer"] -= 1
                if en_obj["explosion_timer"] <= 0:
                    enemies.remove(en_obj)

        # Colisión de balas enemigas y jugador (con parpadeo)
        is_invulnerable = (now - hit_time) < RESPAWN_DELAY

        for eb in enemy_bullets[:]:
            eb.y += 6
            if eb.top > HEIGHT:
                try: enemy_bullets.remove(eb)
                except ValueError: pass
                continue

            if eb.colliderect(player) and not is_invulnerable:
                try: enemy_bullets.remove(eb)
                except ValueError: pass

                player_lives -= 1
                play_sound("shipexplosion")

                # Activar parpadeo
                hit_time = now
                is_invulnerable = True
                player.x = WIDTH // 2 - player.width // 2 # Reposicionar nave
                player.y = HEIGHT - 60

                if player_lives <= 0:
                    running = False
                    break

        # Enemigos llegan abajo
        for en_obj in active_enemies:
            if en_obj["rect"].bottom >= player.top:
                player_lives = 0
                running = False
                break

        # Generar nueva oleada
        if not active_enemies:
            enemies = create_enemies(cols=10)
            # Reiniciar velocidad al inicio de la nueva oleada
            moveTimeCurrent = moveTimeBase

        # Diseño y Renderizado
        update_stars()
        draw_background()

        # --- Lógica de Parpadeo de la Nave ---
        blink = True

        if is_invulnerable:
            blink = (now // 120) % 2 == 0

        if blink or not is_invulnerable:
            if "ship" in GRAPHICS: screen.blit(GRAPHICS["ship"], player.topleft)
            else: pygame.draw.rect(screen, GREEN, player)

        # Dibujo de Balas
        if "laser" in GRAPHICS:
            laser_img = GRAPHICS["laser"]
            for b in bullets: screen.blit(laser_img, b.topleft)
        else:
            for b in bullets: pygame.draw.rect(screen, WHITE, b)

        if "enemylaser" in GRAPHICS:
            e_laser_img = GRAPHICS["enemylaser"]
            for eb in enemy_bullets: screen.blit(e_laser_img, eb.topleft)
        else:
            for eb in enemy_bullets: pygame.draw.rect(screen, BLUE, eb)


        # Dibujar enemigos / explosiones
        sprite_keys_type1 = ["enemy1_1_SCALED", "enemy1_2_SCALED"]
        sprite_keys_type2 = ["enemy2_1_SCALED", "enemy2_2_SCALED"]
        sprite_keys_type3 = ["enemy3_1_SCALED", "enemy3_2_SCALED"]

        for en_obj in enemies:
            e = en_obj["rect"]
            current_row = en_obj["row_index"]

            if en_obj["exploding"]:
                if current_row < 2: explosion_img = GRAPHICS.get("explosionpurple_SCALED")
                elif current_row < 4: explosion_img = GRAPHICS.get("explosionblue_SCALED")
                else: explosion_img = GRAPHICS.get("explosiongreen_SCALED")

                if explosion_img: screen.blit(explosion_img, e.topleft)
                else: pygame.draw.rect(screen, (255, 0, 255) if current_row < 2 else (0, 0, 255), e)
                continue

            if current_row < 2:
                sprite_keys = sprite_keys_type1; color_fallback = RED
            elif current_row < 4:
                sprite_keys = sprite_keys_type2; color_fallback = GREEN
            else:
                sprite_keys = sprite_keys_type3; color_fallback = YELLOW

            sprite_key = sprite_keys[animation_frame]

            if sprite_key in GRAPHICS:
                enemy_img = GRAPHICS[sprite_key]
                screen.blit(enemy_img, e.topleft)
            else:
                pygame.draw.rect(screen, color_fallback, e)

        # HUD
        draw_text_left(f"Puntos: {score}", font_small, WHITE, 10, 10)
        life_text = f"Vida: {player_lives}"
        draw_text_left(life_text, font_small, WHITE, WIDTH - 160, 10)

        max_lives = 3
        bar_w = 100
        bar_h = 12
        bx = WIDTH - 160
        by = 30
        pygame.draw.rect(screen, RED, (bx, by, bar_w, bar_h))
        if player_lives > 0:
            fill_w = int((player_lives / max_lives) * bar_w)
            pygame.draw.rect(screen, GREEN, (bx, by, fill_w, bar_h))

        pygame.display.flip()

    # Pantalla Game Over
    stop_music(fade_ms=400)
    result = game_over_screen_with_input(score)

    if result == "retry":
        main_game()
    elif result == "menu":
        return


# ***************** Menu principal ****************
def main_menu():
    # SINCRONIZACIÓN: Música del menú (menu.mp3)
    play_music_with_fade(menu_music_file, menu_volume, fade_ms=400)
    loading_screen()

    buttons = [
        ("JUGAR", HEIGHT//2 - 60, GREEN),
        ("PUNTUACIONES", HEIGHT//2, YELLOW),
        ("AJUSTAR VOLUMEN", HEIGHT//2 + 60, BLUE),
        ("SALIR", HEIGHT//2 + 120, RED),
    ]

    running = True
    while running:
        clock.tick(FPS)
        mx, my = pygame.mouse.get_pos()
        click = False
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                stop_music()
                pygame.quit(); sys.exit()
            if ev.type == pygame.MOUSEBUTTONDOWN:
                click = True

        update_stars()
        draw_background()
        draw_text_center("SPACE INVADERS", font_big, GREEN, WIDTH//2, HEIGHT//4)

        for text, y, base_color in buttons:
            rect = pygame.Rect(WIDTH//2 - 140, y - 22, 280, 48)
            color = base_color
            if rect.collidepoint(mx, my):
                color = (min(base_color[0] + 40, 255), min(base_color[1] + 40, 255), min(base_color[2] + 40, 255))
            pygame.draw.rect(screen, color, rect, border_radius=8)
            draw_text_center(text, font_med, BLACK, rect.centerx, rect.centery)

        pygame.display.flip()

        if click:
            for text, y, base_color in buttons:
                rect = pygame.Rect(WIDTH//2 - 140, y - 22, 280, 48)
                if rect.collidepoint(mx, my):
                    if text == "JUGAR":
                        main_game()
                        # Al volver, la música del menú se cargará desde game_over_screen_with_input o main_menu
                    elif text == "PUNTUACIONES":
                        show_scores_screen()
                        # La música se mantiene
                    elif text == "AJUSTAR VOLUMEN":
                        adjust_volumes()
                        # La música se mantiene
                    elif text == "SALIR":
                        stop_music()
                        pygame.quit()
                        sys.exit()

# ejecucion
def main(player_email=""):
    """Función principal para ejecutar Space Invaders desde el menú"""
    global player_email_global
    player_email_global = player_email
    main_menu()

# ejecucion
if __name__ == "__main__":
    main()