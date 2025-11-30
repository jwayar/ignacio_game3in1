import sys
import os
import pygame
import random
import json
import math
from pygame.math import Vector2
from datetime import datetime
from pytmx.util_pygame import load_pygame 

# CONFIGURACIÓN DE RUTA DE ARCHIVOS
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

try:
    from notificaciones.email_notifier import send_email_notification
except ModuleNotFoundError:
    print("Error importando notificaciones. La función de email no estará disponible.")
    send_email_notification = None

pygame.init()
try:
    pygame.mixer.init()
except Exception:
    print("Advertencia: pygame.mixer no pudo inicializarse completamente.")

cell_size = 25                
number_of_cells = 25          
BOARD_PIXELS = cell_size * number_of_cells  

OFFSET = 60

ANCHO = 2 * OFFSET + BOARD_PIXELS
ALTO = OFFSET + BOARD_PIXELS + 80

# COLORES
GRID_LIGHT = (140, 160, 70)
GRID_DARK = (110, 130, 50)
DARK_GREEN = (43, 51, 24)
GREEN_LIGHT_HOVER = (173, 204, 96)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
ORANGE_RED = (255, 69, 0)
WALL_COLOR_DARK_GREY = (60, 60, 60)
FOOD_COLOR_APPLE_RED = (200, 0, 0)
GRAY = (150, 150, 150)
GOLD = (255, 215, 0)
SILVER = (192, 192, 192)
BRONZE = (205, 127, 50)
SKY_BLUE_LIGHT = (135, 206, 250)
KEY_TUTORIAL_ALPHA = 200 

SNAKE_COLORS = [(0, 100, 255)]

# RUTAS
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FONTS_DIR = os.path.join(SCRIPT_DIR, "fuentes")
GRAPHICS_DIR = os.path.join(SCRIPT_DIR, "graficos")
SOUNDS_DIR = os.path.join(SCRIPT_DIR, "sonidos")
TILESETS_DIR = os.path.join(SCRIPT_DIR, "tilesets")
TMJ_MAP_PATH = os.path.join(TILESETS_DIR, "tablero.tmj") 

# Fuentes
FONT_SNAKE_CHAN_PATH = os.path.join(FONTS_DIR, "snakechan.ttf")
FONT_SNAKEWAY_PATH = os.path.join(FONTS_DIR, "snake.ttf")
MENU_MUSIC_PATH = os.path.join(SOUNDS_DIR, "menu.mp3")

def load_font(path, size):
    try:
        return pygame.font.Font(path, size)
    except Exception:
        return pygame.font.SysFont("consolas", size)

title_font = load_font(FONT_SNAKE_CHAN_PATH, 80)
leaderboard_title_font = load_font(FONT_SNAKE_CHAN_PATH, 45)
menu_font = load_font(FONT_SNAKEWAY_PATH, 25)
score_font = load_font(FONT_SNAKEWAY_PATH, 25)
input_font = load_font(FONT_SNAKEWAY_PATH, 25)
top3_font = load_font(FONT_SNAKEWAY_PATH, 25)
top3_score_font = load_font(FONT_SNAKEWAY_PATH, 25)
standard_font_score = pygame.font.Font(None, 45)
standard_font_leaderboard = pygame.font.Font(None, 45)

# SPRITE MAP
SPRITE_MAP = {
    (0, -1): "head_up.png",
    (0, 1): "head_down.png",
    (1, 0): "head_right.png",
    (-1, 0): "head_left.png",
    "TAIL_UP": "tail_up.png",
    "TAIL_DOWN": "tail_down.png",
    "TAIL_RIGHT": "tail_right.png",
    "TAIL_LEFT": "tail_left.png",
    "BODY_VERTICAL": "body_vertical.png",
    "BODY_HORIZONTAL": "body_horizontal.png",
    "CORNER_BL": "body_bottomleft.png",
    "CORNER_BR": "body_bottomright.png",
    "CORNER_TL": "body_topleft.png",
    "CORNER_TR": "body_topright.png",
    "FOOD": "apple.png",
    "SPEED": "speed.png",
    "KEY_W": "sprite-68-4.png", 
    "KEY_A": "sprite-68-3.png", 
    "KEY_S": "sprite-68-2.png", 
    "KEY_D": "sprite-68-1.png"  
}

screen = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Retro Snake Plus - Spicy Edition")

# SPRITE MANAGER
class SpriteManager:
    def __init__(self, cell_size):
        self.cell_size = cell_size
        self.sprites = {}
        self.food_sprite = None
        self.speed_sprite = None 
        self.trap_sprite = None 
        self.key_sprites = {} 
        self.load_all()

    def load_image(self, filename, custom_size=None):
        path = os.path.join(GRAPHICS_DIR, filename)
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                if custom_size:
                    img = pygame.transform.scale(img, custom_size)
                else:
                    img = pygame.transform.scale(img, (self.cell_size, self.cell_size))
                return img
            except Exception as e:
                print(f"Advertencia: no se pudo cargar imagen {path}: {e}")
                return None
        else:
            return None

    def load_all(self):
        for key, filename in SPRITE_MAP.items():
            if not filename: continue
            
            if key == "SPEED":
                self.speed_sprite = self.load_image(filename, custom_size=(30, 30))
            elif isinstance(key, str) and key.startswith("KEY_"):
                self.key_sprites[key] = self.load_image(filename, custom_size=(40, 40))
            elif key == "FOOD":
                self.food_sprite = self.load_image(filename)
            else:
                self.sprites[key] = self.load_image(filename)

        self.trap_sprite = self.load_image("trap.png")

sprite_manager = SpriteManager(cell_size)

# SUPERFICIE MAPA
def render_tmj_map_json(tmj_path, target_cells, cell_size):
    try:
        if not os.path.exists(tmj_path): return None
        with open(tmj_path, "r", encoding="utf-8") as f: data = json.load(f)

        width = data.get("width")
        height = data.get("height")
        tilewidth = data.get("tilewidth")
        tileheight = data.get("tileheight")
        layers = data.get("layers", [])
        tilesets = data.get("tilesets", [])

        if width is None or height is None or tilewidth is None or tileheight is None: return None
        map_surface = pygame.Surface((target_cells * cell_size, target_cells * cell_size), pygame.SRCALPHA)

        if not tilesets: return None
        tileset = tilesets[0]
        tileset_image_source = tileset.get("image")
        if not tileset_image_source: return None

        tileset_image_path = os.path.join(os.path.dirname(tmj_path), tileset_image_source)
        if not os.path.exists(tileset_image_path): return None

        tileset_image = pygame.image.load(tileset_image_path).convert_alpha()
        columns = tileset.get("columns")
        tilecount = tileset.get("tilecount")
        
        tiles = []
        for i in range(tilecount):
            tx = (i % columns) * tilewidth
            ty = (i // columns) * tileheight
            tile_surf = tileset_image.subsurface((tx, ty, tilewidth, tileheight)).copy()
            if tilewidth != cell_size or tileheight != cell_size:
                tile_surf = pygame.transform.scale(tile_surf, (cell_size, cell_size))
            tiles.append(tile_surf)

        for layer in layers:
            if layer.get("type") != "tilelayer" or not layer.get("visible", True): continue
            data_layer = layer.get("data", [])
            layer_width = layer.get("width", width)
            layer_height = layer.get("height", height)
            for y in range(min(layer_height, target_cells)):
                for x in range(min(layer_width, target_cells)):
                    idx = y * layer_width + x
                    if idx < 0 or idx >= len(data_layer): continue
                    gid = data_layer[idx]
                    if not gid: continue
                    gid_clean = gid & 0x1FFFFFFF
                    tile_index = gid_clean - 1
                    if 0 <= tile_index < len(tiles):
                        map_surface.blit(tiles[tile_index], (x * cell_size, y * cell_size))
        return map_surface
    except Exception as e:
        print(f"Error mapa: {e}")
        return None

TMX_BACKGROUND_SURFACE = render_tmj_map_json(TMJ_MAP_PATH, number_of_cells, cell_size)

# SONIDOS
eat_sound = None
wall_hit_sound = None
chile_sound = None 

try:
    eat_path = os.path.join(SOUNDS_DIR, "eat.mp3")
    if os.path.exists(eat_path): eat_sound = pygame.mixer.Sound(eat_path)
    wall_path = os.path.join(SOUNDS_DIR, "wall.mp3")
    if os.path.exists(wall_path): wall_hit_sound = pygame.mixer.Sound(wall_path)
    chile_path = os.path.join(SOUNDS_DIR, "chile.ogg")
    if os.path.exists(chile_path):
        chile_sound = pygame.mixer.Sound(chile_path)
        chile_sound.set_volume(0.6)
except Exception as e:
    print(f"Advertencia: no se pudieron cargar sonidos: {e}")

try:
    move_sounds = {}
    for name in ("up", "down", "left", "right"):
        p = os.path.join(SOUNDS_DIR, f"{name}.mp3")
        if os.path.exists(p):
            move_sounds[name] = pygame.mixer.Sound(p)
            move_sounds[name].set_volume(0.4)
except Exception: move_sounds = {}

def load_menu_music():
    if not pygame.mixer or not pygame.mixer.get_init(): return
    if not pygame.mixer.music.get_busy():
        if os.path.exists(MENU_MUSIC_PATH):
            try:
                pygame.mixer.music.load(MENU_MUSIC_PATH)
                pygame.mixer.music.play(-1)
            except Exception: pass

def stop_music():
    try:
        if pygame.mixer.music.get_busy(): pygame.mixer.music.stop()
    except Exception: pass

class DataManager:
    def __init__(self, scores_path=os.path.join(BASE_DIR, "data", "global_scores.json"), game_id="SNAKE"):
        self.scores_path = scores_path
        self.game_id = game_id

    def _read_all_data(self):
        if not os.path.exists(self.scores_path): return {}
        with open(self.scores_path, 'r', encoding='utf-8') as file:
            try:
                data = json.load(file)
                if not isinstance(data, dict): return {}
                return data
            except json.JSONDecodeError: return {}

    def _save_all_data(self, all_data):
        os.makedirs(os.path.dirname(self.scores_path), exist_ok=True)
        with open(self.scores_path, 'w', encoding='utf-8') as file:
            json.dump(all_data, file, indent=4)

    def load_game_scores(self):
        all_data = self._read_all_data()
        game_scores = all_data.get(self.game_id, [])
        game_scores.sort(key=lambda x: x['score'], reverse=True)
        return game_scores[:10]

    def update_score(self, name, email, score):
        if not email or "@" not in email: return False, 0
        all_data = self._read_all_data()
        if self.game_id not in all_data: all_data[self.game_id] = []
        game_scores = all_data[self.game_id]
        
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
                else: return False, old_score
                break
        
        if not record_found:
            game_scores.append({"name": name, "email": email, "score": score, "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        
        game_scores.sort(key=lambda x: x['score'], reverse=True)
        all_data[self.game_id] = game_scores[:10]
        self._save_all_data(all_data)
        
        new_top = game_scores[0] if game_scores else None
        if new_top and new_top["score"] > 0 and send_email_notification:
             if new_top["score"] == score: 
                try:
                    send_email_notification(new_top["email"], self.game_id, new_top["score"], new_top["name"])
                except: pass
        return True, old_score

    def get_top_scores(self): return self.load_game_scores()

# ------------------ CLASES DE JUEGO

class Wall:
    def __init__(self, snake_body, food_positions, num_traps=17): 
        self.positions = []
        self.num_traps = num_traps
        self.generate_initial_pos(snake_body, food_positions)

    def draw(self):
        for position in self.positions:
            wall_rect = pygame.Rect(OFFSET + position.x * cell_size, OFFSET + position.y * cell_size, cell_size, cell_size)
            if sprite_manager.trap_sprite: screen.blit(sprite_manager.trap_sprite, wall_rect)
            else: pygame.draw.rect(screen, WALL_COLOR_DARK_GREY, wall_rect, 0, 4)

    def generate_random_cell(self):
        return Vector2(random.randint(0, number_of_cells-1), random.randint(0, number_of_cells-1))

    def is_adjacent_any(self, pos, others):
        for o in others:
            if abs(int(o.x) - int(pos.x)) <= 1 and abs(int(o.y) - int(pos.y)) <= 1: return True
        return False

    def generate_initial_pos(self, snake_body, food_positions):
        self.positions = []
        excluded = set((int(v.x), int(v.y)) for v in snake_body)
        excluded |= set((int(p.x), int(p.y)) for p in food_positions)

        attempts = 0
        while len(self.positions) < self.num_traps and attempts < 5000:
            attempts += 1
            cand = self.generate_random_cell()
            cx, cy = int(cand.x), int(cand.y)
            if cx < 2 or cx >= number_of_cells - 2: continue
            if cy < 2 or cy >= number_of_cells: continue 
            if (cx, cy) in excluded: continue
            
            dist_to_snake = min(abs(cx - int(sv.x)) + abs(cy - int(sv.y)) for sv in snake_body)
            if dist_to_snake <= 3: continue
            if self.is_adjacent_any(cand, self.positions): continue

            self.positions.append(cand)
            excluded.add((cx, cy))

    def regenerate_all_pos(self, snake_body, food_positions):
        self.generate_initial_pos(snake_body, food_positions)

class Food:
    def __init__(self, snake_body, num_foods=4):
        self.positions = []
        self.num_foods = num_foods
        self.wall_positions = []
        self.generate_initial_pos(snake_body)

    def draw(self):
        offset_y = math.sin(pygame.time.get_ticks() * 0.005) * 3 
        
        if sprite_manager.food_sprite:
            for position in self.positions:
                rect_pos = pygame.Rect(OFFSET + position.x * cell_size, 
                                       OFFSET + position.y * cell_size + offset_y, 
                                       cell_size, cell_size)
                screen.blit(sprite_manager.food_sprite, rect_pos)
        else:
            for position in self.positions:
                pygame.draw.rect(screen, FOOD_COLOR_APPLE_RED,
                                 (OFFSET + position.x * cell_size, OFFSET + position.y * cell_size + offset_y, cell_size, cell_size), 0, 4)

    def generate_random_cell(self):
        return Vector2(random.randint(0, number_of_cells-1), random.randint(0, number_of_cells-1))

    def generate_initial_pos(self, snake_body):
        self.positions = []
        excluded = set((int(v.x), int(v.y)) for v in snake_body)
        excluded |= set((int(w.x), int(w.y)) for w in getattr(self, "wall_positions", []))

        attempts = 0
        while len(self.positions) < self.num_foods and attempts < 5000:
            attempts += 1
            pos = self.generate_random_cell()
            px, py = int(pos.x), int(pos.y)
            if px < 2 or px >= number_of_cells - 2: continue
            if py < 2: continue 
            if (px, py) in excluded: continue
            self.positions.append(pos)
            excluded.add((px, py))

    def regenerate_single_pos(self, snake_body):
        excluded = set((int(v.x), int(v.y)) for v in snake_body)
        excluded |= set((int(p.x), int(p.y)) for p in self.positions)
        excluded |= set((int(w.x), int(w.y)) for w in getattr(self, "wall_positions", []))
        pos = self.generate_random_cell()
        attempts = 0
        while (int(pos.x), int(pos.y)) in excluded and attempts < 2000:
            pos = self.generate_random_cell()
            attempts += 1
        self.positions.append(pos)

class Chili:
    def __init__(self):
        self.position = Vector2(-1, -1)
        self.active = False
        self.spawn_timer = 0
        self.last_spawn_score = 0
    
    def spawn(self, snake_body, food_positions, wall_positions):
        self.active = True
        excluded = set((int(v.x), int(v.y)) for v in snake_body)
        excluded |= set((int(p.x), int(p.y)) for p in food_positions)
        excluded |= set((int(w.x), int(w.y)) for w in wall_positions)
        
        attempts = 0
        while attempts < 1000:
            pos = Vector2(random.randint(0, number_of_cells-1), random.randint(0, number_of_cells-1))
            px, py = int(pos.x), int(pos.y)
            if px < 2 or px >= number_of_cells - 2: continue
            if py < 2: continue
            if (px, py) not in excluded:
                self.position = pos
                return
            attempts += 1
        self.active = False 

    def draw(self):
        if not self.active: return
        offset_y = math.sin(pygame.time.get_ticks() * 0.005) * 3 
        
        x_pos = OFFSET + self.position.x * cell_size
        y_pos = OFFSET + self.position.y * cell_size + offset_y
        
        center_x = x_pos + cell_size // 2
        center_y = y_pos + cell_size // 2
        
        if sprite_manager.speed_sprite:
            sprite = sprite_manager.speed_sprite
            rect = sprite.get_rect(center=(center_x, center_y))
            screen.blit(sprite, rect)
        else:
            rect = pygame.Rect(x_pos, y_pos, cell_size, cell_size)
            pygame.draw.rect(screen, RED, rect, 0, 4) 
            pygame.draw.rect(screen, (0, 255, 0), (x_pos + 10, y_pos - 5, 5, 5))

    def reset(self):
        self.active = False
        self.position = Vector2(-1, -1)

class Snake:
    def __init__(self):
        self.body = [Vector2(6, 9), Vector2(5, 9), Vector2(4, 9)]
        self.direction = Vector2(1, 0)
        self.add_segment = False
        self.eat_sound = eat_sound
        self.wall_hit_sound = wall_hit_sound
        self.can_change_direction = True
        self.is_moving = False 
        
        if hasattr(sprite_manager, "sprites"): self.sprites = sprite_manager.sprites
        else: self.sprites = {}

    def draw(self):
        for index, block in enumerate(self.body):
            x_pos = int(OFFSET + block.x * cell_size)
            y_pos = int(OFFSET + block.y * cell_size)
            block_rect = pygame.Rect(x_pos, y_pos, cell_size, cell_size)

            if index == 0:
                if len(self.body) > 1:
                    direction = self.body[0] - self.body[1]
                    head_sprite = self.sprites.get((int(direction.x), int(direction.y)))
                    if head_sprite: screen.blit(head_sprite, block_rect)
                    else: pygame.draw.rect(screen, SNAKE_COLORS[0], block_rect, 0, 7)
                else: pygame.draw.rect(screen, SNAKE_COLORS[0], block_rect, 0, 7)

            elif index == len(self.body) - 1:
                direction = self.body[-2] - self.body[-1]
                tail_sprite = None
                if direction.x == 1: tail_sprite = self.sprites.get("TAIL_LEFT")
                elif direction.x == -1: tail_sprite = self.sprites.get("TAIL_RIGHT")
                elif direction.y == 1: tail_sprite = self.sprites.get("TAIL_UP")
                else: tail_sprite = self.sprites.get("TAIL_DOWN")
                if tail_sprite: screen.blit(tail_sprite, block_rect)
                else: pygame.draw.rect(screen, SNAKE_COLORS[0], block_rect, 0, 7)

            else:
                prev_block = self.body[index + 1] - block
                next_block = self.body[index - 1] - block
                body_sprite = None
                if prev_block.x == next_block.x: body_sprite = self.sprites.get("BODY_VERTICAL")
                elif prev_block.y == next_block.y: body_sprite = self.sprites.get("BODY_HORIZONTAL")
                else:
                    if (prev_block.x == -1 and next_block.y == -1) or (next_block.x == -1 and prev_block.y == -1): body_sprite = self.sprites.get("CORNER_TL")
                    elif (prev_block.x == -1 and next_block.y == 1) or (next_block.x == -1 and prev_block.y == 1): body_sprite = self.sprites.get("CORNER_BL")
                    elif (prev_block.x == 1 and next_block.y == -1) or (next_block.x == 1 and prev_block.y == -1): body_sprite = self.sprites.get("CORNER_TR")
                    elif (prev_block.x == 1 and next_block.y == 1) or (next_block.x == 1 and prev_block.y == 1): body_sprite = self.sprites.get("CORNER_BR")
                if body_sprite: screen.blit(body_sprite, block_rect)
                else: pygame.draw.rect(screen, SNAKE_COLORS[0], block_rect, 0, 7)

    def update(self):
        if not self.is_moving: return 
        
        self.body.insert(0, self.body[0] + self.direction)
        if not self.add_segment: self.body = self.body[:-1]
        else: self.add_segment = False
        self.can_change_direction = True

    def change_direction(self, new_direction):
        # Al presionar cualquier tecla válida, comenzamos el movimiento
        if not self.is_moving:
            if new_direction == Vector2(-1, 0): return 
            self.is_moving = True

        if self.can_change_direction and new_direction != -self.direction:
            if new_direction != self.direction:
                if new_direction == Vector2(0, -1) and "up" in move_sounds: move_sounds["up"].play()
                elif new_direction == Vector2(0, 1) and "down" in move_sounds: move_sounds["down"].play()
                elif new_direction == Vector2(-1, 0) and "left" in move_sounds: move_sounds["left"].play()
                elif new_direction == Vector2(1, 0) and "right" in move_sounds: move_sounds["right"].play()
            self.direction = new_direction
            self.can_change_direction = False

    def reset(self):
        self.body = [Vector2(6, 9), Vector2(5, 9), Vector2(4, 9)]
        self.direction = Vector2(1, 0)
        self.can_change_direction = True
        self.add_segment = False
        self.is_moving = False # Reset al estado quieto

class Game:
    def __init__(self):
        self.snake = Snake()
        self.food = Food(self.snake.body, num_foods=4)
        self.wall = Wall(self.snake.body, self.food.positions, num_traps=17) 
        self.food.wall_positions = self.wall.positions
        self.chili = Chili() 
        self.score = 0
        self.initial_speed_ms = 150
        self.current_speed_ms = self.initial_speed_ms
        self.speed_level = 0 
        self.max_speed_level = 5
        # Velocidad máxima 3.5 
        self.min_speed_ms = int(self.initial_speed_ms / 3.5) 
        self.last_chili_spawn_time = pygame.time.get_ticks()
        self.last_score_for_chili = 0

    def draw(self):
        self.food.draw()
        self.chili.draw() 
        self.wall.draw()
        self.snake.draw()
        
        if not self.snake.is_moving:
            self.draw_wasd_tutorial()

    def draw_wasd_tutorial(self):
        center_x = ANCHO // 2
        center_y = ALTO // 2 + 50 
        
        keys = sprite_manager.key_sprites
        if not keys: return
        
        spacing = 45 
        
        w_pos = (center_x - 20, center_y - spacing) 
        a_pos = (center_x - 20 - spacing, center_y) 
        s_pos = (center_x - 20, center_y)           
        d_pos = (center_x - 20 + spacing, center_y) 
        
        # Efecto de presión para la tecla D
        current_time = pygame.time.get_ticks()
        press_offset_y = 0
        is_pressed = (current_time // 500) % 2 == 0 # Alternar cada medio segundo
        
        d_pos_draw = list(d_pos)
        d_alpha = KEY_TUTORIAL_ALPHA
        if is_pressed:
            d_pos_draw[1] += 4
            d_alpha = 255 # Hacemos que brille un poco más cuando se "presiona"

        def blit_alpha(source, location, opacity):
            x = location[0]
            y = location[1]
            temp = pygame.Surface((source.get_width(), source.get_height())).convert()
            temp.blit(screen, (-x, -y))
            temp.blit(source, (0, 0))
            temp.set_alpha(opacity)
            screen.blit(temp, location)

        if "KEY_W" in keys: blit_alpha(keys["KEY_W"], w_pos, KEY_TUTORIAL_ALPHA)
        if "KEY_A" in keys: blit_alpha(keys["KEY_A"], a_pos, KEY_TUTORIAL_ALPHA)
        if "KEY_S" in keys: blit_alpha(keys["KEY_S"], s_pos, KEY_TUTORIAL_ALPHA)
        
        # Dibujamos D con su posible efecto
        if "KEY_D" in keys: blit_alpha(keys["KEY_D"], tuple(d_pos_draw), d_alpha)
        
        if is_pressed:
            txt = menu_font.render("¡MUÉVETE!", True, WHITE)
            screen.blit(txt, txt.get_rect(center=(center_x, center_y + 60)))


    def update(self):
        self.snake.update()
        self.check_collision_with_food()
        self.check_collision_with_chili() 
        self.check_collision_with_edges()
        self.check_collision_with_tail()
        self.check_collision_with_walls()
        self.handle_chili_spawning() 
        
    def handle_chili_spawning(self):
        if not self.chili.active:
            current_time = pygame.time.get_ticks()
            time_condition = (current_time - self.last_chili_spawn_time) >= 15000
            score_condition = (self.score - self.last_score_for_chili) >= 10
            if time_condition or score_condition:
                self.chili.spawn(self.snake.body, self.food.positions, self.wall.positions)
                self.last_chili_spawn_time = current_time
                self.last_score_for_chili = self.score

    def check_collision_with_food(self):
        head = self.snake.body[0]
        for idx, pos in enumerate(self.food.positions):
            if head == pos:
                self.food.positions.pop(idx)
                self.snake.add_segment = True
                self.score += 1
                if self.snake.eat_sound:
                    try: self.snake.eat_sound.play()
                    except Exception: pass
                self.food.regenerate_single_pos(self.snake.body)
                return

    def check_collision_with_chili(self):
        if self.chili.active and self.snake.body[0] == self.chili.position:
            if chile_sound: chile_sound.play()
            self.snake.add_segment = True 
            self.chili.reset()
            self.last_chili_spawn_time = pygame.time.get_ticks()
            self.last_score_for_chili = self.score 
            if self.speed_level < self.max_speed_level:
                self.speed_level += 1
                self.recalculate_speed()
            else:
                self.score += 5

    def recalculate_speed(self):
        if self.speed_level == 0:
            self.current_speed_ms = self.initial_speed_ms
        else:
            step = (self.initial_speed_ms - self.min_speed_ms) / self.max_speed_level
            self.current_speed_ms = int(self.initial_speed_ms - (step * self.speed_level))
        pygame.time.set_timer(SNAKE_UPDATE, self.current_speed_ms)

    def check_collision_with_walls(self):
        head = self.snake.body[0]
        for p in self.wall.positions:
            if head == p:
                self.game_over()
                return

    def check_collision_with_edges(self):
        head = self.snake.body[0]
        if head.x >= number_of_cells or head.x < 0 or head.y >= number_of_cells or head.y < 0:
            self.game_over()

    def check_collision_with_tail(self):
        if self.snake.body[0] in self.snake.body[1:]:
            self.game_over()

    def game_over(self):
        global game_state, last_score, current_player_name, current_player_email
        last_score = self.score
        if self.snake.wall_hit_sound:
            try: self.snake.wall_hit_sound.play()
            except Exception: pass

        final_name = current_player_name.strip()
        if final_name == "Invitado" or not final_name:
            final_name = current_player_email.split('@')[0] if "@" in current_player_email else "Invitado"
        if last_score > 0:
            data_manager.update_score(final_name[:5], current_player_email, last_score)

        self.snake.reset()
        self.food.generate_initial_pos(self.snake.body)
        self.wall.regenerate_all_pos(self.snake.body, self.food.positions)
        self.food.wall_positions = self.wall.positions
        self.chili.reset()
        self.score = 0
        self.speed_level = 0
        self.current_speed_ms = self.initial_speed_ms
        self.last_chili_spawn_time = pygame.time.get_ticks()
        self.last_score_for_chili = 0
        
        game_state = "GAME_OVER"
        stop_music()
        pygame.time.set_timer(SNAKE_UPDATE, self.current_speed_ms)


# BOTONES Y PANTALLAS
class Button:
    def __init__(self, text, rect, base_color, hover_color, text_color=WHITE, font=menu_font):
        self.text = text
        self.rect = rect
        self.base_color = base_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font = font

    def draw(self, surface, mouse_pos):
        current_color = self.base_color
        if self.rect.collidepoint(mouse_pos):
            current_color = self.hover_color

        pygame.draw.rect(surface, current_color, self.rect, 0, 10)
        pygame.draw.rect(surface, self.text_color, self.rect, 3, 10)
        text_surf = self.font.render(self.text, True, self.text_color)
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))

def draw_menu():
    global boton_rects
    screen.fill(SKY_BLUE_LIGHT)
    mouse_pos = pygame.mouse.get_pos()
    title_surf = title_font.render("RETRO SNAKE", True, DARK_GREEN)
    screen.blit(title_surf, title_surf.get_rect(center=(ANCHO // 2, ALTO // 4)))
    button_y_start = ALTO // 2 - 50
    button_width = 300
    spacing = 80
    buttons_data = [("JUGAR", button_y_start), ("CLASIFICACIONES", button_y_start + spacing), ("SALIR DEL JUEGO", button_y_start + 2 * spacing)]
    boton_rects = {}
    for text, y in buttons_data:
        rect = pygame.Rect(ANCHO // 2 - button_width // 2, y, button_width, 60)
        Button(text, rect, DARK_GREEN, GREEN_LIGHT_HOVER, WHITE, menu_font).draw(screen, mouse_pos)
        boton_rects[text] = rect
    display_name = current_player_name if current_player_name != "Invitado" else "Invitado (Sin registro)"
    user_surf = score_font.render(f"Jugador: {display_name}", True, DARK_GREEN)
    screen.blit(user_surf, (OFFSET, ALTO - 50))
    load_menu_music()
    return boton_rects

def draw_game_over():
    global game_over_rects
    mouse_pos = pygame.mouse.get_pos()
    overlay = pygame.Surface((ANCHO, ALTO))
    overlay.set_alpha(200)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))
    title_surf = title_font.render("GAME OVER", True, RED)
    score_display = int(last_score)
    prefix_surf = menu_font.render("Puntaje: ", True, WHITE)
    score_num_surf = standard_font_leaderboard.render(str(score_display), True, WHITE)
    total_width = prefix_surf.get_width() + score_num_surf.get_width()
    x_start = ANCHO // 2 - total_width // 2
    y_score = ALTO // 3 + 80
    screen.blit(title_surf, title_surf.get_rect(center=(ANCHO // 2, ALTO // 3)))
    screen.blit(prefix_surf, (x_start, y_score - prefix_surf.get_height() // 2))
    screen.blit(score_num_surf, (x_start + prefix_surf.get_width(), y_score - score_num_surf.get_height() // 2))
    save_msg = score_font.render("Intenta conseguir un puntaje mayor a 0.", True, GRAY) if score_display <= 0 else score_font.render(f"Puntaje de {current_player_name} registrado.", True, GRAY)
    screen.blit(save_msg, save_msg.get_rect(center=(ANCHO // 2, ALTO // 3 + 120)))
    button_y_start = ALTO // 2 + 100
    button_width = 250
    spacing = 70
    boton_play_again = Button("Volver a Jugar", pygame.Rect(ANCHO // 2 - button_width // 2, button_y_start, button_width, 50), DARK_GREEN, GREEN_LIGHT_HOVER, WHITE, menu_font)
    boton_menu = Button("Ir a Inicio", pygame.Rect(ANCHO // 2 - button_width // 2, button_y_start + spacing, button_width, 50), DARK_GREEN, GREEN_LIGHT_HOVER, WHITE, menu_font)
    boton_main_menu = Button("Menú Principal", pygame.Rect(ANCHO // 2 - button_width // 2, button_y_start + 2 * spacing, button_width, 50), DARK_GREEN, GREEN_LIGHT_HOVER, WHITE, menu_font)
    boton_play_again.draw(screen, mouse_pos)
    boton_menu.draw(screen, mouse_pos)
    boton_main_menu.draw(screen, mouse_pos)
    game_over_rects = {"PLAY_AGAIN": boton_play_again.rect, "MENU": boton_menu.rect, "MAIN_MENU": boton_main_menu.rect}

def draw_pause_menu():
    global pause_rects
    mouse_pos = pygame.mouse.get_pos()
    overlay = pygame.Surface((ANCHO, ALTO))
    overlay.set_alpha(180)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))
    title_surf = title_font.render("PAUSA", True, WHITE)
    screen.blit(title_surf, title_surf.get_rect(center=(ANCHO // 2, ALTO // 3)))
    button_width = 250
    spacing = 70
    button_y_start = ALTO // 2 - 30
    btn_resume = Button("Reanudar", pygame.Rect(ANCHO // 2 - button_width // 2, button_y_start, button_width, 50), DARK_GREEN, GREEN_LIGHT_HOVER, WHITE, menu_font)
    btn_menu = Button("Ir al Menú", pygame.Rect(ANCHO // 2 - button_width // 2, button_y_start + spacing, button_width, 50), DARK_GREEN, GREEN_LIGHT_HOVER, WHITE, menu_font)
    btn_exit = Button("Salir del Juego", pygame.Rect(ANCHO // 2 - button_width // 2, button_y_start + 2 * spacing, button_width, 50), DARK_GREEN, GREEN_LIGHT_HOVER, WHITE, menu_font)
    btn_resume.draw(screen, mouse_pos)
    btn_menu.draw(screen, mouse_pos)
    btn_exit.draw(screen, mouse_pos)
    pause_rects = {"RESUME": btn_resume.rect, "MENU": btn_menu.rect, "EXIT": btn_exit.rect}

def draw_name_input_screen():
    global name_input_text, input_box_rect, continue_button_rect, is_input_active
    mouse_pos = pygame.mouse.get_pos()
    box_width = 400
    box_height = 250
    box_rect = pygame.Rect(ANCHO // 2 - box_width // 2, ALTO // 2 - box_height // 2, box_width, box_height)
    draw_menu()
    overlay = pygame.Surface((ANCHO, ALTO))
    overlay.set_alpha(150)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))
    pygame.draw.rect(screen, DARK_GREEN, box_rect, 0, 10)
    pygame.draw.rect(screen, DARK_GREEN, box_rect, 5, 10)
    title_surf = menu_font.render("¡INGRESA TU NOMBRE!", True, WHITE)
    screen.blit(title_surf, title_surf.get_rect(center=(ANCHO // 2, box_rect.y + 40)))
    input_box_rect = pygame.Rect(ANCHO // 2 - 150, box_rect.y + 90, 300, 40)
    pygame.draw.rect(screen, WHITE, input_box_rect, 0, 5)
    pygame.draw.rect(screen, DARK_GREEN, input_box_rect, 2, 5)
    display_text = name_input_text if name_input_text else "Tu nombre (Máx 5)"
    text_color = BLACK if name_input_text else GRAY
    text_surf = input_font.render(display_text, True, text_color)
    screen.blit(text_surf, (input_box_rect.x + 10, input_box_rect.y + 8))
    if is_input_active and pygame.time.get_ticks() % 1000 < 500:
        cursor_x = input_box_rect.x + 10 + input_font.size(name_input_text)[0]
        pygame.draw.line(screen, BLACK, (cursor_x, input_box_rect.y + 8), (cursor_x, input_box_rect.y + 32), 2)
    continue_button = Button("CONTINUAR", pygame.Rect(ANCHO // 2 - 100, box_rect.y + 160, 200, 50), DARK_GREEN, GREEN_LIGHT_HOVER, WHITE, menu_font)
    continue_button.draw(screen, mouse_pos)
    continue_button_rect = continue_button.rect
    return input_box_rect, continue_button_rect

def draw_leaderboard():
    global leaderboard_rects
    screen.fill(SKY_BLUE_LIGHT)
    mouse_pos = pygame.mouse.get_pos()
    title_surf = leaderboard_title_font.render("CLASIFICACIONES TOP 10", True, DARK_GREEN)
    screen.blit(title_surf, title_surf.get_rect(center=(ANCHO // 2, 40)))
    top_scores = data_manager.get_top_scores()
    displayed_scores = top_scores[:10]
    if not displayed_scores:
        no_scores_surf = menu_font.render("¡Sé el primero en el ranking!", True, DARK_GREEN)
        screen.blit(no_scores_surf, no_scores_surf.get_rect(center=(ANCHO // 2, ALTO // 2)))
    MEDALS = [GOLD, SILVER, BRONZE]
    rank_y_start = 120
    rank_height = 80
    for i in range(min(3, len(displayed_scores))):
        player = displayed_scores[i]
        rank_rect = pygame.Rect(OFFSET + 10, rank_y_start + i * rank_height, ANCHO - 2 * OFFSET - 20, rank_height - 10)
        pygame.draw.rect(screen, MEDALS[i], rank_rect, 0, 8)
        pygame.draw.rect(screen, DARK_GREEN, rank_rect, 3, 8)
        rank_text = top3_font.render(f"{i + 1}°", True, DARK_GREEN)
        screen.blit(rank_text, (OFFSET + 30, rank_rect.centery - rank_text.get_height() // 2))
        name_text = top3_score_font.render(player['name'][:5], True, DARK_GREEN)
        screen.blit(name_text, (OFFSET + 120, rank_rect.centery - name_text.get_height() // 2))
        score_text = standard_font_leaderboard.render(str(player['score']), True, DARK_GREEN)
        screen.blit(score_text, (ANCHO - OFFSET - score_text.get_width() - 30, rank_rect.centery - score_text.get_height() // 2))
    table_y_start = rank_y_start + min(3, len(displayed_scores)) * rank_height + 10
    if len(displayed_scores) > 3:
        header_font = menu_font
        row_font = score_font
        col_x = [OFFSET + 20, OFFSET + 120, ANCHO - OFFSET - 150]
        screen.blit(header_font.render("Puesto", True, DARK_GREEN), (col_x[0], table_y_start))
        screen.blit(header_font.render("Nombre", True, DARK_GREEN), (col_x[1], table_y_start))
        screen.blit(header_font.render("Puntaje", True, DARK_GREEN), (col_x[2], table_y_start))
        for i, player in enumerate(displayed_scores[3:]):
            rank = i + 4
            y = table_y_start + 40 + i * 35
            screen.blit(row_font.render(f"{rank}°", True, DARK_GREEN), (col_x[0], y))
            screen.blit(row_font.render(player['name'][:5], True, DARK_GREEN), (col_x[1], y))
            screen.blit(standard_font_score.render(str(player['score']), True, DARK_GREEN), (col_x[2], y))
    button_width = 200
    btn_y = ALTO - 60
    menu_btn = Button("Menú", pygame.Rect((ANCHO - button_width) // 2, btn_y, button_width, 50), DARK_GREEN, GREEN_LIGHT_HOVER, WHITE, menu_font)
    menu_btn.draw(screen, mouse_pos)
    leaderboard_rects = {"MENU": menu_btn.rect}

# LOOP PRINCIPAL
SNAKE_UPDATE = pygame.USEREVENT
input_box_rect = pygame.Rect(0, 0, 0, 0)
continue_button_rect = pygame.Rect(0, 0, 0, 0)
is_input_active = False

GLOBAL_SCORES_PATH = os.path.join(BASE_DIR, "data", "global_scores.json")
GAME_IDENTIFIER = "SNAKE"
game_state = "MENU"
is_paused = False
current_player_name = "Invitado"
current_player_email = ""
last_score = 0
name_input_text = ""

clock = pygame.time.Clock()
data_manager = None
game = None
pause_rects = {}

def start_game_loop(player_name_arg, player_email_arg):
    global data_manager, game, current_player_name, current_player_email, game_state
    global last_score, name_input_text, is_input_active, input_box_rect, continue_button_rect
    global is_paused, pause_rects

    data_manager = DataManager()
    game = Game()
    current_player_name = player_name_arg
    current_player_email = player_email_arg
    pygame.time.set_timer(SNAKE_UPDATE, game.current_speed_ms)

    if current_player_name != "Invitado":
        name_input_text = current_player_name[:5]
    if current_player_email and "@" in current_player_email:
        game_state = "NAME_INPUT_MENU"
    load_menu_music()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if game_state == "NAME_INPUT_MENU":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = event.pos
                    if input_box_rect.collidepoint(mouse_pos): is_input_active = True
                    else: is_input_active = False
                    if continue_button_rect.collidepoint(mouse_pos):
                        if name_input_text.strip(): current_player_name = name_input_text.strip()[:5]
                        else: current_player_name = (current_player_email.split('@')[0] if "@" in current_player_email else "Invitado")[:5]
                        game_state = "RUNNING"
                        stop_music()
                elif event.type == pygame.KEYDOWN and is_input_active:
                    if event.key == pygame.K_RETURN:
                        if name_input_text.strip(): current_player_name = name_input_text.strip()[:5]
                        else: current_player_name = (current_player_email.split('@')[0] if "@" in current_player_email else "Invitado")[:5]
                        game_state = "RUNNING"
                        stop_music()
                    elif event.key == pygame.K_BACKSPACE: name_input_text = name_input_text[:-1]
                    else:
                        if len(name_input_text) < 5 and (event.unicode.isalnum() or event.unicode.isspace()): name_input_text += event.unicode
                continue

            if game_state == "RUNNING":
                if event.type == SNAKE_UPDATE and not is_paused:
                    game.update()
                if event.type == pygame.KEYDOWN:
                    if not is_paused:
                        # Movimiento básico
                        if event.key == pygame.K_UP: game.snake.change_direction(Vector2(0, -1))
                        if event.key == pygame.K_DOWN: game.snake.change_direction(Vector2(0, 1))
                        if event.key == pygame.K_LEFT: game.snake.change_direction(Vector2(-1, 0))
                        if event.key == pygame.K_RIGHT: game.snake.change_direction(Vector2(1, 0))
                        
                        # Soporte WASD
                        if event.key == pygame.K_w: game.snake.change_direction(Vector2(0, -1))
                        if event.key == pygame.K_s: game.snake.change_direction(Vector2(0, 1))
                        if event.key == pygame.K_a: game.snake.change_direction(Vector2(-1, 0))
                        if event.key == pygame.K_d: game.snake.change_direction(Vector2(1, 0))

                    if event.key == pygame.K_p:
                        is_paused = not is_paused
                        if is_paused: stop_music()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                if game_state == "RUNNING" and is_paused:
                    if pause_rects.get("RESUME") and pause_rects["RESUME"].collidepoint(mouse_pos): is_paused = False
                    elif pause_rects.get("MENU") and pause_rects["MENU"].collidepoint(mouse_pos):
                        is_paused = False
                        game_state = "MENU"
                        load_menu_music()
                    elif pause_rects.get("EXIT") and pause_rects["EXIT"].collidepoint(mouse_pos):
                        pygame.quit()
                        sys.exit()
                if game_state == "MENU":
                    if boton_rects.get("JUGAR") and boton_rects["JUGAR"].collidepoint(mouse_pos):
                        if current_player_email and "@" in current_player_email: game_state = "NAME_INPUT_MENU"
                        else: game_state = "RUNNING"
                        stop_music()
                    elif boton_rects.get("CLASIFICACIONES") and boton_rects["CLASIFICACIONES"].collidepoint(mouse_pos): game_state = "LEADERBOARD"
                    elif boton_rects.get("SALIR DEL JUEGO") and boton_rects["SALIR DEL JUEGO"].collidepoint(mouse_pos):
                        pygame.quit()
                        sys.exit()
                elif game_state == "GAME_OVER":
                    if game_over_rects["PLAY_AGAIN"].collidepoint(mouse_pos):
                        if current_player_email and "@" in current_player_email: game_state = "NAME_INPUT_MENU"
                        else: game_state = "RUNNING"
                        stop_music()
                    elif game_over_rects["MENU"].collidepoint(mouse_pos):
                        game_state = "MENU"
                        load_menu_music()
                    elif game_over_rects["MAIN_MENU"].collidepoint(mouse_pos):
                        pygame.quit()
                        sys.exit()
                elif game_state == "LEADERBOARD":
                    if leaderboard_rects["MENU"].collidepoint(mouse_pos):
                        game_state = "MENU"
                        load_menu_music()

        if game_state == "MENU": draw_menu()
        elif game_state == "NAME_INPUT_MENU": input_box_rect, continue_button_rect = draw_name_input_screen()
        elif game_state in ("RUNNING", "GAME_OVER"):
            screen.fill(DARK_GREEN)
            
            # HUD
            hud_h = 48
            hud_rect = pygame.Rect(0, 0, ANCHO, hud_h)
            pygame.draw.rect(screen, BLACK, hud_rect)
            
            display_name = current_player_name if current_player_name != "Invitado" else "Invitado"
            name_surf = score_font.render(f"Jugador: {display_name}", True, WHITE)
            screen.blit(name_surf, (OFFSET, (hud_h - name_surf.get_height()) // 2))
            
            # BARRA VELOCIDAD
            bar_width = 150
            bar_height = 15
            bar_x = ANCHO // 2 - bar_width // 2
            bar_y = (hud_h - bar_height) // 2
            
            pygame.draw.rect(screen, WALL_COLOR_DARK_GREY, (bar_x, bar_y, bar_width, bar_height), 0, 3)
            pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 1, 3)
            
            segments = 5
            segment_w = (bar_width - 4) / segments
            for i in range(game.speed_level):
                seg_x = bar_x + 2 + i * segment_w
                pygame.draw.rect(screen, ORANGE_RED, (seg_x, bar_y + 2, segment_w - 2, bar_height - 4))

            if sprite_manager.speed_sprite:
                chili_icon = pygame.transform.scale(sprite_manager.speed_sprite, (24, 24))
                screen.blit(chili_icon, (bar_x - 30, bar_y - 4))
            else:
                 pygame.draw.rect(screen, RED, (bar_x - 25, bar_y, 15, 15))

            # HUD Score
            apple_icon = sprite_manager.food_sprite
            if apple_icon:
                apple_icon_scaled = pygame.transform.scale(apple_icon, (30, 30))
                apple_x = ANCHO - OFFSET - 100
                apple_y = (hud_h - 30) // 2
                screen.blit(apple_icon_scaled, (apple_x, apple_y))
            else:
                pygame.draw.rect(screen, FOOD_COLOR_APPLE_RED, (ANCHO - OFFSET - 100, (hud_h - 30)//2, 30, 30), 0, 5)
            score_surf = standard_font_score.render(str(game.score), True, WHITE)
            
            # EJE X (Izquierda <-> Derecha)
            score_x = ANCHO - OFFSET - 60
            
            # EJE Y (Arriba <-> Abajo)
            score_y = (hud_h - score_surf.get_height()) // 2 + 4
            
            screen.blit(score_surf, (score_x, score_y))

            if TMX_BACKGROUND_SURFACE:
                screen.blit(TMX_BACKGROUND_SURFACE, (OFFSET, OFFSET))
            else:
                for fila in range(number_of_cells):
                    for col in range(number_of_cells):
                        cell_color = GRID_DARK if (fila + col) % 2 == 0 else GRID_LIGHT
                        pygame.draw.rect(screen, cell_color, (OFFSET + col * cell_size, OFFSET + fila * cell_size, cell_size, cell_size))

            game.draw()
            if is_paused: draw_pause_menu()
            if game_state == "GAME_OVER": draw_game_over()

        elif game_state == "LEADERBOARD": draw_leaderboard()

        pygame.display.update()
        clock.tick(60)

if __name__ == '__main__':
    initial_email = sys.argv[1] if len(sys.argv) > 1 else ""
    player_name = initial_email.split('@')[0] if initial_email and "@" in initial_email else "Invitado"
    font_dirs = [os.path.dirname(FONT_SNAKE_CHAN_PATH), os.path.dirname(FONT_SNAKEWAY_PATH)]
    for f_dir in font_dirs:
        if f_dir and f_dir not in sys.path: sys.path.insert(0, f_dir)
    start_game_loop(player_name, initial_email)