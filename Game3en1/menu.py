import pygame
import sys
import os
import subprocess
import random
import json
from pygame.locals import *

# Ruta base del script actual. Se usa para construir todas las demás rutas relativas
BASE_PATH = os.path.dirname(os.path.abspath(__file__))

# Ruta a la carpeta de recursos del menu
MENU_PATH = os.path.join(BASE_PATH, "menu")
SCREENWIDTH = 800
SCREENHEIGHT = 600
FPS = 30
GAME_TITLE = "J . A . L"
IS_MUSIC_ON = True

# Ruta de fuentes
FONT_FOLDER = os.path.join(MENU_PATH, "fuentes")

# Diccionario para describir el uso de cada fuente
FONT_CONFIG = {
    'menu': "StayPixelRegular-EaOxl.ttf",  # para menú, botones, notas, toggles
    'title': "PixelEmulator-xq08.ttf",     # para el titulo principal
    'input': "Invasion2000.ttf",           # fuente para el input de email
}

# Ruta de musica
MUSIC_FILE = os.path.join(MENU_PATH, "musica", "Retro_Theme.mp3") # musica
# Ruta del archivo de configuración donde se almacena el email del jugador
EMAIL_FILE = os.path.join(MENU_PATH, "current_email.txt") # archivo para guardar el email ingresado

# Importar los juegos como módulos
try:
    print(f"[DEBUG] Intentando importar juegos...")
    print(f"[DEBUG] BASE_PATH: {BASE_PATH}")

    # Agregar las carpetas de juegos al path de Python
    sys.path.insert(0, os.path.join(BASE_PATH, "Snake"))
    sys.path.insert(0, os.path.join(BASE_PATH, "FlappyBird"))
    sys.path.insert(0, os.path.join(BASE_PATH, "SpaceInvaders"))

    from snake import main as snake_main
    print("[DEBUG] Snake importado OK")

    from flappy import main as flappy_main
    print("[DEBUG] Flappy Bird importado OK")

    from SpaceInvaders import main as space_invaders_main
    print("[DEBUG] Space Invaders importado OK")

    GAMES_AVAILABLE = True
    print("[DEBUG] Todos los juegos importados correctamente")

except ImportError as e:
    print(f"[DEBUG] Error importing games: {e}")
    import traceback
    traceback.print_exc()
    GAMES_AVAILABLE = False
except Exception as e:
    print(f"[DEBUG] Otro error: {e}")
    import traceback
    traceback.print_exc()
    GAMES_AVAILABLE = False

# Data store
DATA_PATH = os.path.join(BASE_PATH, "data") # carpeta para almacenar los puntajes
GLOBAL_SCORES_PATH = os.path.join(DATA_PATH, "global_scores.json") # aqui se registran los puntajes de los 3 juegos

# COLORES
COLORS = {
    'dark_bg': (40, 30, 60),
    'text': (255, 170, 0),
    'button_grey': (180, 180, 180),
    'button_hover': (255, 120, 0),
    'input_box': (50, 50, 80),
    'red_alert': (200, 50, 50),
    'toggle_on': (0, 180, 0),
    'toggle_off': (180, 0, 0),
    'toggle_bg': (200, 200, 200),
    'star_light': (200, 200, 255),
    'gradient_edge': (200, 200, 255),
    'credits_bg': (20, 15, 30),
}

# Función para manejar rutas en PyInstaller
def resource_path(relative_path):
    """Obtiene la ruta absoluta al recurso, funciona para dev y para PyInstaller"""
    try:
        # PyInstaller crea una carpeta temporal y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

#Verifica la existencia de la carpeta 'data' y el archivo 'global_scores.json' (si existen omite la creacion)
def initialize_data_storage():
    print("\n--- Verificando Almacenamiento de Datos ---")
    if not os.path.exists(DATA_PATH):
        try:
            os.makedirs(DATA_PATH, exist_ok=True)
            print(f"[DEBUG] Carpeta 'data' creada en: {DATA_PATH}")
        except OSError as e:
            print(f"ERROR: No se pudo crear la carpeta '{DATA_PATH}'. Verifica los permisos: {e}")
            sys.exit(1)
    if not os.path.exists(GLOBAL_SCORES_PATH):
        try:
            with open(GLOBAL_SCORES_PATH, "w", encoding="utf-8") as f:
                json.dump([], f, indent=4)
            print(f"[DEBUG] Archivo JSON creado en: {GLOBAL_SCORES_PATH}")
        except Exception as e:
            print(f"ERROR: No se pudo crear el archivo JSON. Verifica permisos: {e}")
            sys.exit(1)
    else:
        print("[DEBUG] El archivo 'global_scores.json' ya existe.")
    print("------------------------------------------\n")

#Carga la fuente designada para el menú, botones y texto general
def get_font(size):
    try:
        font_path = resource_path(os.path.join(FONT_FOLDER, FONT_CONFIG['menu']))
        return pygame.font.Font(font_path, size)
    except:
        return pygame.font.SysFont('Arial', size)

#Carga la fuente para el título principal del juego
def get_main_title_font(size):
    try:
        font_path = resource_path(os.path.join(FONT_FOLDER, FONT_CONFIG['title']))
        return pygame.font.Font(font_path, size)
    except:
        return pygame.font.SysFont('Arial', size)

#Carga la fuente para el campo de entrada del email (input box)
def get_input_font(size):
    try:
        font_path = resource_path(os.path.join(FONT_FOLDER, FONT_CONFIG['input']))
        return pygame.font.Font(font_path, size)
    except:
        return pygame.font.SysFont('Arial', size)

#Aplica un efecto de contorno al texto
def render_text_with_outline(font, text, main_color, outline_color, position, screen, outline_size=2):
    outline_surface = font.render(text, True, outline_color)
    for dx in range(-outline_size, outline_size + 1):
        for dy in range(-outline_size, outline_size + 1):
            if dx != 0 or dy != 0:
                screen.blit(outline_surface, (position[0] + dx, position[1] + dy))
    main_surface = font.render(text, True, main_color)
    screen.blit(main_surface, position)

# Dibuja una franja en la parte superior del fondo del menú
def draw_subtle_gradient(screen, rect_y, rect_height, color_start, color_end):
    width = screen.get_width()

    # Calcular las diferencias de color para el cambio gradual
    dr = (color_end[0] - color_start[0]) / rect_height
    dg = (color_end[1] - color_start[1]) / rect_height
    db = (color_end[2] - color_start[2]) / rect_height

    for y in range(rect_height):
        r = int(color_start[0] + dr * y)
        g = int(color_start[1] + dg * y)
        b = int(color_start[2] + db * y)
        pygame.draw.line(screen, (r, g, b), (0, rect_y + y), (width, rect_y + y))

# Carga y reproduce la musica de fondo en bucle
def play_music():
    if IS_MUSIC_ON:
        try:
            music_path = resource_path(MUSIC_FILE)
            if os.path.exists(music_path):
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.play(-1) #lo mantiene en bucle
        except Exception as e:
            print(f"Error loading music: {e}")

#Alterna el estado de la musica (on/off)
def toggle_music():
    global IS_MUSIC_ON
    IS_MUSIC_ON = not IS_MUSIC_ON
    if IS_MUSIC_ON:
        play_music()
    else:
        pygame.mixer.music.stop()

#Carga el último email guardado
def load_email():
    try:
        email_path = resource_path(EMAIL_FILE)
        if os.path.exists(email_path):
            with open(email_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
    except:
        pass
    return ""

#Guarda el email del jugador
def save_email(email):
    try:
        email_path = resource_path(EMAIL_FILE)
        with open(email_path, 'w', encoding='utf-8') as f:
            f.write(email.strip())
    except:
        pass

def get_char_index_from_pos(font, text, x_pos, start_x):
    current_x = start_x
    if x_pos < start_x:
        return 0

    for i, char in enumerate(text):
        char_width, _ = font.size(char)

        if x_pos < current_x + char_width // 2:
            return i
        current_x += char_width

    return len(text)

def input_box_logic_retro(screen, rect, text, active, cursor_pos, default_text="Ingresa tu email", clear_font_name=None):
    mouse_pos = pygame.mouse.get_pos()
    color = COLORS['text'] if active else COLORS['button_grey']
    # Dibujar caja de entrada (input box)
    pygame.draw.rect(screen, COLORS['input_box'], rect)
    pygame.draw.rect(screen, color, rect, 3)

    # Tipográfica y márgenes
    font = get_input_font(16)
    padding = 10
    button_margin = 8
    button_size = rect.height
    max_text_width = rect.width - (2 * padding)

    # Texto mostrado (placeholder)
    if not text and not active:
        display_text = default_text
        display_color = (160, 160, 160)
    else:
        display_text = text
        display_color = COLORS['text']

    text_surface = font.render(display_text, True, display_color)
    text_width = text_surface.get_width()
    cursor_pixel = font.size(display_text[:cursor_pos])[0]

    # Posicionamiento del texto
    if text_width <= max_text_width:
        text_x = rect.centerx - text_width // 2
        scroll_offset = 0
    else:
        scroll_offset = max(0, cursor_pixel - max_text_width + 20)
        text_x = rect.x + padding - scroll_offset

    text_y = rect.y + (rect.height - text_surface.get_height()) // 2

    # Evita que el texto se dibuje fuera de la caja del input del email
    prev_clip = screen.get_clip()
    clip_rect = pygame.Rect(rect.x + padding, rect.y, max_text_width, rect.height)
    screen.set_clip(clip_rect)
    screen.blit(text_surface, (text_x, text_y))
    screen.set_clip(prev_clip)

    # --- Cursor parpadeante ---
    if active and pygame.time.get_ticks() % 1000 < 500:
        cursor_x = text_x + cursor_pixel - scroll_offset
        pygame.draw.line(screen, COLORS['text'], (cursor_x, text_y), (cursor_x, text_y + text_surface.get_height()), 2)

    # Botón 'X' (para limpiar texto en el input del email)
    clear_rect = pygame.Rect(rect.right + button_margin, rect.y, button_size, button_size)
    is_hover = clear_rect.collidepoint(mouse_pos)

    # Colores del boton 'X'
    base_color = (180, 30, 30) if not is_hover else (255, 60, 60)
    border_color = (255, 255, 255)
    shadow_color = (60, 0, 0)

    # Dibujar boton 'X'
    pygame.draw.rect(screen, shadow_color, clear_rect.move(2, 2))
    pygame.draw.rect(screen, base_color, clear_rect)
    pygame.draw.rect(screen, border_color, clear_rect, 2)

    # Fuente para el boton 'X'
    if clear_font_name:
        try:
            clear_font_path = resource_path(clear_font_name)
            x_font = pygame.font.Font(clear_font_path, 20)
        except:
            x_font = get_font(20)
    else:
        x_font = get_font(20)
    # Centrado en el boton 'X'
    x_surface = x_font.render("X", True, (255, 255, 255))
    x_rect = x_surface.get_rect(center=clear_rect.center)
    screen.blit(x_surface, x_rect)

    return clear_rect, is_hover

# Ejecuta los juegos como módulos en lugar de procesos separados
def run_game(game_function, player_email):
    try:
        pygame.mixer.music.stop()
        save_email(player_email)
        print(f"[DEBUG] Ejecutando juego con email: {player_email}")
        # Pasar el email como argumento a la función del juego
        game_function(player_email)
    except Exception as e:
        print(f"[DEBUG] Error ejecutando el juego: {e}")
        import traceback
        traceback.print_exc()

        # Mostrar mensaje de error en pantalla
        show_error_message(f"Error al abrir el juego: {str(e)}")
    finally:
        if IS_MUSIC_ON:
            play_music()

def show_error_message(error_text):
    """Muestra un mensaje de error temporal"""
    error_font = get_font(20)
    error_surface = error_font.render(error_text, True, COLORS['red_alert'])
    error_rect = error_surface.get_rect(center=(SCREENWIDTH//2, SCREENHEIGHT//2))

    # Guardar pantalla actual
    temp_surface = SCREEN.copy()

    # Dibujar mensaje de error
    SCREEN.fill(COLORS['dark_bg'])
    pygame.draw.rect(SCREEN, (80, 40, 40), error_rect.inflate(20, 20))
    SCREEN.blit(error_surface, error_rect)

    # Mensaje para continuar
    continue_font = get_font(16)
    continue_text = continue_font.render("Presiona cualquier tecla para continuar...", True, COLORS['text'])
    continue_rect = continue_text.get_rect(center=(SCREENWIDTH//2, SCREENHEIGHT//2 + 50))
    SCREEN.blit(continue_text, continue_rect)

    pygame.display.update()

    # Esperar tecla
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN or event.type == MOUSEBUTTONDOWN:
                waiting = False

    # Restaurar pantalla
    SCREEN.blit(temp_surface, (0, 0))
    pygame.display.update()

#Dibuja un interruptor para los estados de pantalla y musica (on/off)
def draw_toggle_switch(screen, x, y, is_on, width=50, height=25):
    radius = height // 2
    rect_bg = pygame.Rect(x, y, width, height)
    color = COLORS['toggle_on'] if is_on else COLORS['toggle_off']
    pygame.draw.rect(screen, color, rect_bg, border_radius=radius)
    circle_x = x + width - radius if is_on else x + radius
    pygame.draw.circle(screen, COLORS['toggle_bg'], (circle_x, y + radius), radius - 3)

# Dibuja un efecto de líneas de escaneo (simular una pantalla CRT)
def draw_scanlines(screen):
    scanline_surface = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
    scanline_color = (0, 0, 0, 50)
    for y in range(0, screen.get_height(), 2):
        pygame.draw.line(scanline_surface, scanline_color, (0, y), (screen.get_width(), y))
    screen.blit(scanline_surface, (0, 0))

# Genera una lista de estrellas
def create_stars(num_stars, speed_factor, size, screen_width, screen_height):
    stars = []
    for _ in range(num_stars):
        stars.append([
            random.randint(0, screen_width),
            random.randint(0, screen_height),
            speed_factor,
            size
        ])
    return stars

# Actualiza y dibuja las estrellas en pantalla (para simular un fondo animado)
def draw_and_move_stars(screen, stars, color):
    for star in stars:
        star[0] -= star[2]
        if star[0] < 0:
            star[0] = screen.get_width()
            star[1] = random.randint(0, screen.get_height())
        pygame.draw.rect(screen, color, (star[0], star[1], star[3], star[3]))

# PANTALLA DE CRÉDITOS
def credits_screen(screen, fps_clock):
    credits_data = [
        " CREDITS ",
        "",
        "-Space Invaders-",
        "Hecho por: Ignacio Janco",
        "Música del menú: TRYZ",
        "Música del juego: Desconocida",
        "Playtesters: Lionel y Alan",
        "",
        " -Flappy Bird Pobre-",
        "Hecho por: Alan Chaparro",
        "Música: No utilizada",
        "Origen de efectos: Desconocido",
        "Playtesters: Ignacio y Alan",
        "",
        "-Snake-",
        "Hecho por: Lionel Belén",
        "Música: No utilizada",
        "Origen de efectos: Desconocido",
        "Playtesters: Ignacio y Alan",
        "",
        "🧰 Programas usados:",
        "Python, Thonny, Visual Studio Code, Pygame",
        "",
        "💬 Agradecimientos:",
        "A todos los profes de la especialidad y a nuestras familias ❤️",
        "__INSERT_MEME_HERE__", # <--- Marcador para la posición de la imagen
        "-------------------  Gracias  ---------------------",
        "",
        "Presiona ESC, RETORNO o haz click para volver...",
    ]

    # Fuentes
    title_font = get_main_title_font(48)
    text_font = get_font(24)
    note_font = get_font(18)

    # cargar imagen
    meme_img = None
    try:
        meme_path = resource_path("meme.jpg")
        if os.path.exists(meme_path):
            meme_img = pygame.image.load(meme_path).convert_alpha()
            meme_img = pygame.transform.scale(meme_img, (350, 350))
            print(f"[DEBUG] Imagen 'meme.jpg' cargada")
        else:
            print(f"[DEBUG] Imagen 'meme.jpg' no esta en la carpeta.")
    except pygame.error as e:
        print(f"ERROR: No se pudo cargar la imagen 'meme.jpg': {e}")
        meme_img = None

    meme_height = meme_img.get_height() if meme_img else 0

    # Calcular la altura total de los créditos para el desplazamiento
    total_credits_height = 0
    line_spacing = 30 # Espaciado entre líneas

    for i, line in enumerate(credits_data):
        current_font = text_font
        if "CREDITS" in line or "Gracias" in line:
            current_font = title_font
        elif "Presiona ESC" in line:
            current_font = note_font

        if line == "__INSERT_MEME_HERE__":
            total_credits_height += meme_height + line_spacing # Altura de la imagen + espacio extra
        else:
            total_credits_height += current_font.size(line)[1]
        total_credits_height += line_spacing

    scroll_offset = SCREENHEIGHT
    scroll_speed = 0.05 # Velocidad de desplazamiento

    running = True
    credits_finished_scrolling = False

    while running:
        dt = fps_clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key in (K_ESCAPE, K_RETURN):
                    running = False
            if event.type == MOUSEBUTTONDOWN:
                running = False # Permitir click para salir

        # Desplazamiento (scroll)
        if not credits_finished_scrolling:
            scroll_offset -= scroll_speed * dt

            # Lógica de detención del scroll
            target_y_for_last_line = SCREENHEIGHT - 30

            if scroll_offset <= (target_y_for_last_line - (total_credits_height - line_spacing)):
                 credits_finished_scrolling = True
                 scroll_offset = (target_y_for_last_line - (total_credits_height - line_spacing))

        # DIBUJO --
        screen.fill(COLORS['credits_bg']) # Fondo oscuro para créditos

        # Contenido de los créditos
        y_pos = scroll_offset
        for i, line in enumerate(credits_data):
            current_font = text_font
            color = COLORS['text']
            outline = (0, 0, 0)

            if "CREDITS" in line or "Gracias" in line:
                current_font = title_font
            elif "Presiona ESC" in line:
                current_font = note_font
                color = COLORS['button_hover']

            if line == "__INSERT_MEME_HERE__" and meme_img:
                img_rect = meme_img.get_rect(center=(SCREENWIDTH // 2, y_pos + meme_img.get_height() // 2))
                if -meme_img.get_height() < img_rect.y < SCREENHEIGHT:
                    screen.blit(meme_img, img_rect)
                y_pos += meme_height + line_spacing # Avance después de la imagen
            else: # Dibujar texto normal
                line_surface = current_font.render(line, True, color)
                line_rect = line_surface.get_rect(center=(SCREENWIDTH // 2, y_pos + line_surface.get_height() // 2))

                # Solo dibujar si está en pantalla
                if -line_surface.get_height() < line_rect.y < SCREENHEIGHT:
                    if "Presiona ESC" not in line and "CREDITS" not in line and "Gracias" not in line:
                        render_text_with_outline(current_font, line, color, outline, (line_rect.x, line_rect.y), screen, outline_size=1)
                    else:
                        screen.blit(line_surface, line_rect)
                y_pos += line_surface.get_height() + line_spacing

        draw_scanlines(screen)
        pygame.display.update()

#Función principal del menú del juego
def main():
    global SCREEN, FPSCLOCK, IS_MUSIC_ON
    pygame.init()
    pygame.mixer.init()
    SCREEN = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
    pygame.display.set_caption(GAME_TITLE)
    FPSCLOCK = pygame.time.Clock()
    play_music()

    # Fondo estelar en capas (parallax)
    stars_layer1 = create_stars(50, 0.5, 1, SCREENWIDTH, SCREENHEIGHT)
    stars_layer2 = create_stars(20, 1.5, 2, SCREENWIDTH, SCREENHEIGHT)
    stars_layer3 = create_stars(5, 3.0, 3, SCREENWIDTH, SCREENHEIGHT)

    # Caja de entrada para email
    email_text = load_email()
    email_active = False
    INPUT_BOX_Y = 200
    input_box = pygame.Rect(SCREENWIDTH // 2 - 150, INPUT_BOX_Y, 300, 40)
    cursor_pos = len(email_text)

    # Elementos del menu - ahora usamos las funciones importadas
    menu_items = [
        {"text": "SNAKE", "action": lambda: run_game(snake_main, email_text)},
        {"text": "SPACE INVADERS", "action": lambda: run_game(space_invaders_main, email_text)},
        {"text": "FLAPPY BIRD", "action": lambda: run_game(flappy_main, email_text)},
        {"text": "SALIR", "action": lambda: sys.exit()}
    ]

    # Si los juegos no están disponibles, mostrar mensaje
    if not GAMES_AVAILABLE:
        menu_items = [
            {"text": "JUEGOS NO DISPONIBLES", "action": lambda: None},
            {"text": "SALIR", "action": lambda: sys.exit()}
        ]

    selected_index = 0
    blink_timer = 0
    blink_state = True # Esta variable controla el parpadeo del título y el menú

    # Bucle principal
    while True:
        dt = FPSCLOCK.tick(FPS)
        blink_timer += dt
        if blink_timer >= 700:
            blink_state = not blink_state
            blink_timer = 0

        mouse_pos = pygame.mouse.get_pos()

        # Botón de Créditos (Superior Derecha)
        credits_font = get_font(20)
        credits_text = "CREDITOS"
        credits_surf = credits_font.render(credits_text, True, COLORS['text'])
        credits_padding = 10
        credits_rect = pygame.Rect(
            SCREENWIDTH - credits_surf.get_width() - (credits_padding * 2) - 10,
            10,
            credits_surf.get_width() + (credits_padding * 2),
            credits_surf.get_height() + (credits_padding * 2)
        )
        is_credits_hover = credits_rect.collidepoint(mouse_pos)

        # EVENTOS
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == MOUSEBUTTONDOWN:
                # Activación de input box
                if input_box.collidepoint(event.pos):
                    email_active = True
                    text_x_start = input_box.x + 10
                    font = get_input_font(20)
                    cursor_pos = get_char_index_from_pos(font, email_text, event.pos[0], text_x_start)
                else:
                    email_active = False

                # Boton X para limpiar email
                if 'clear_rect' in locals() and clear_rect.collidepoint(event.pos):
                    email_text = ""
                    cursor_pos = 0

                # Interruptores musica
                music_toggle_rect = pygame.Rect(140, SCREENHEIGHT - 60, 50, 25)

                if music_toggle_rect.collidepoint(event.pos):
                    toggle_music()

                # NUEVO: Botón de Créditos
                if credits_rect.collidepoint(event.pos):
                    credits_screen(SCREEN, FPSCLOCK) # Llamar a la nueva pantalla de créditos

            elif event.type == KEYDOWN:
                if email_active:
                    #Edicion de texto en el input box
                    if event.key == K_RETURN:
                        email_active = False
                    elif event.key == K_BACKSPACE and cursor_pos > 0:
                        email_text = email_text[:cursor_pos - 1] + email_text[cursor_pos:]
                        cursor_pos = max(0, cursor_pos - 1)
                    elif event.key == K_DELETE and cursor_pos < len(email_text):
                        email_text = email_text[:cursor_pos] + email_text[cursor_pos + 1:]
                        cursor_pos = min(len(email_text), cursor_pos)
                    elif event.key == K_LEFT:
                        cursor_pos = max(0, cursor_pos - 1)
                    elif event.key == K_RIGHT:
                        cursor_pos = min(len(email_text), cursor_pos + 1)
                    elif len(email_text) < 40 and event.unicode and not event.unicode.isspace():
                        email_text = email_text[:cursor_pos] + event.unicode + email_text[cursor_pos:]
                        cursor_pos += 1
                else:
                    # Navegación del menú (wasd) (flechas)
                    if event.key in (K_w, K_UP):
                        selected_index = (selected_index - 1) % len(menu_items)
                    elif event.key in (K_s, K_DOWN):
                        selected_index = (selected_index + 1) % len(menu_items)
                    elif event.key == K_m:
                        toggle_music()
                    elif event.key == K_c: # NUEVO: Acceso rápido a créditos con 'C'
                        credits_screen(SCREEN, FPSCLOCK)
                    elif event.key == K_RETURN:
                        menu_items[selected_index]["action"]()

        # -DIBUJO-
        SCREEN.fill(COLORS['dark_bg']) # Fondo
        draw_subtle_gradient(SCREEN, 0, 50, COLORS['gradient_edge'], COLORS['dark_bg'])
        draw_and_move_stars(SCREEN, stars_layer1, COLORS['star_light'])
        draw_and_move_stars(SCREEN, stars_layer2, COLORS['star_light'])
        draw_and_move_stars(SCREEN, stars_layer3, COLORS['star_light'])

        # Titulo y efectos aplicados
        title_font = get_main_title_font(72)
        title_text = GAME_TITLE
        title_width, title_height = title_font.size(title_text)
        title_x = SCREENWIDTH // 2 - title_width // 2
        title_y = 90

        main_title_color = (255, 255, 255)
        outline_title_color = COLORS['button_grey']

        current_title_color = main_title_color if blink_state else (200, 200, 200)
        current_outline_color = outline_title_color if blink_state else main_title_color

        render_text_with_outline(
            title_font,
            title_text,
            current_title_color,
            current_outline_color,
            (title_x, title_y),
            SCREEN,
            outline_size=3
        )

        # NUEVO: Dibujar el botón de Créditos
        button_color = COLORS['button_hover'] if is_credits_hover else COLORS['button_grey']
        pygame.draw.rect(SCREEN, COLORS['input_box'], credits_rect)
        pygame.draw.rect(SCREEN, button_color, credits_rect, 3)
        credits_text_color = COLORS['text'] if is_credits_hover else COLORS['button_grey']
        credits_surf = credits_font.render(credits_text, True, credits_text_color)
        credits_text_rect = credits_surf.get_rect(center=credits_rect.center)
        render_text_with_outline(credits_font, credits_text, credits_text_color, (0, 0, 0), (credits_text_rect.x, credits_text_rect.y), SCREEN, 1)

        # Caja de entrada con su botón 'X'
        clear_rect, hovering_clear = input_box_logic_retro(
            SCREEN,
            input_box,
            email_text,
            email_active,
            cursor_pos,
            "ejemplo@dominio.com",
            clear_font_name=os.path.join(FONT_FOLDER, FONT_CONFIG['menu'])
        )

        # Mensaje de aviso (email inválido)
        if email_text and not ("@" in email_text and "." in email_text):
            warning_font = get_font(20)
            warning_surface = warning_font.render("Email no válido. Jugarás como Invitado.", True, COLORS['red_alert'])
            SCREEN.blit(warning_surface, (input_box.x, input_box.y + 50))

        # Menú
        menu_font = get_font(36)
        menu_start_y = 285
        for i, item in enumerate(menu_items):
            text = item['text']
            text_w, text_h = menu_font.size(text)
            pos = (SCREENWIDTH // 2 - text_w // 2, menu_start_y + i * 50)
            render_text_with_outline(menu_font, text, COLORS['text'], (255, 255, 255), pos, SCREEN, 1)
            #Indicadores de selección (efecto de parpadeo) > elemento del menu <
            if i == selected_index and blink_state:
                cursor_open = menu_font.render(">", True, COLORS['text'])
                cursor_close = menu_font.render("<", True, COLORS['text'])
                SCREEN.blit(cursor_open, (pos[1] - 30, pos[1]))
                SCREEN.blit(cursor_close, (pos[0] + text_w + 15, pos[1]))

        # Controles inferiores (instrucciones e interruptores)
        note_font = get_font(16)
        SCREEN.blit(
            note_font.render("PRESIONA 'M' PARA SILENCIAR Y 'C' PARA CRÉDITOS", True, COLORS['button_hover']),
            note_font.render("PRESIONA 'M' PARA SILENCIAR Y 'C' PARA CRÉDITOS", True, COLORS['button_hover']).get_rect(center=(SCREENWIDTH // 2, SCREENHEIGHT - 10))
        )

        # Dibuja el interruptor del estado de la musica (musica activada por defecto)
        fs_font = get_font(24)
        SCREEN.blit(fs_font.render("MÚSICA", True, COLORS['text']), (20, SCREENHEIGHT - 60))
        draw_toggle_switch(SCREEN, 140, SCREENHEIGHT - 60, IS_MUSIC_ON)

        draw_scanlines(SCREEN)
        pygame.display.update()

if __name__ == '__main__':
    initialize_data_storage()
    main()