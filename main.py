import pygame
import sys
import random
import os

pygame.init()
pygame.mixer.init()

# Load and play background music
pygame.mixer.music.load(os.path.join('sounds', 'background.mp3'))
pygame.mixer.music.set_volume(0.5)
pygame.mixer.music.play(-1)  # Loop forever

# Load attack sound
attack_sound = pygame.mixer.Sound(os.path.join('sounds', 'attack.mp3'))
attack_sound.set_volume(0.7)

# Load enemy attack sound
enemy_attack_sound = pygame.mixer.Sound(os.path.join('sounds', 'enemy.mp3'))
enemy_attack_sound.set_volume(0.7)

# Game settings
CELL_SIZE = 32
GRID_WIDTH = 30
GRID_HEIGHT = 22
WINDOW_WIDTH = CELL_SIZE * GRID_WIDTH
WINDOW_HEIGHT = CELL_SIZE * GRID_HEIGHT + 40  # Extra space for UI
UI_FONT_SIZE = 24

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
PLAYER_COLOR = (255, 255, 0)   # Yellow
WALL_COLOR = (80, 80, 80)      # Dark gray
FLOOR_COLOR = (180, 180, 180)  # Light gray
STAIRS_DOWN_COLOR = (0, 200, 255)  # Cyan
STAIRS_UP_COLOR = (255, 100, 255)  # Magenta
ENEMY_COLOR = (255, 50, 50)    # Red
ENEMY2_COLOR = (150, 0, 150)  # Purple
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Map symbols
PLAYER = '@'
WALL = '#'
FLOOR = '.'
STAIRS_DOWN = '>'
STAIRS_UP = '<'
ENEMY = 'E'
ENEMY2 = 'F'
BOSS = 'B'

# Dungeon generation parameters
NUM_ROOMS = 8
ROOM_MIN_SIZE = 4
ROOM_MAX_SIZE = 8
ENEMIES_PER_FLOOR = 3

# Combat settings
PLAYER_MAX_HP = 100
PLAYER_ATTACK_MIN = 15
PLAYER_ATTACK_MAX = 25
ENEMY_ATTACK_MIN = 10
ENEMY_ATTACK_MAX = 20
ENEMY2_ATTACK_MIN = 15
ENEMY2_ATTACK_MAX = 30
ENEMY_MAX_HP = 60
ENEMY2_MAX_HP = 80
BOSS_ATTACK_MIN = 25
BOSS_ATTACK_MAX =40
BOSS_MAX_HP = 200

TILE_IMAGE_FILES = {
    PLAYER: 'player.png',
    WALL: 'wall.png',
    FLOOR: 'floor.png',
    ENEMY: 'enemy.png',
    ENEMY2:'enemy2.png',   
    BOSS: 'boss.png',
    STAIRS_UP: 'stairs_up.png',
    STAIRS_DOWN: 'stairs_down.png',
    'combat_bg': 'combat_bg.png',  # Combat background texture
    'player_combat': 'player_combat.png',  # Detailed player sprite for combat
    'enemy_combat': 'enemy_combat.png',    # Detailed enemy sprite for combat
    'enemy2_combat': 'enemy2_combat.png',  # Detailed enemy2 sprite for combat
}

def load_tile_images():
    tile_images = {}
    tile_folder = os.path.join(os.path.dirname(__file__), 'tiles')
    for key, filename in TILE_IMAGE_FILES.items():
        path = os.path.join(tile_folder, filename)
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            if key == 'combat_bg':
                # Scale combat background to window size
                img = pygame.transform.scale(img, (WINDOW_WIDTH, WINDOW_HEIGHT))
            elif key in ['player_combat', 'enemy_combat', 'enemy2_combat']:
                # Scale combat sprites to reasonable size (e.g., 128x128)
                img = pygame.transform.scale(img, (128, 128))
            else:
                img = pygame.transform.scale(img, (CELL_SIZE, CELL_SIZE))
            tile_images[key] = img
    return tile_images

def create_empty_grid():
    return [[WALL for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

def place_room(grid, x, y, w, h):
    for i in range(y, y + h):
        for j in range(x, x + w):
            if 0 < i < GRID_HEIGHT-1 and 0 < j < GRID_WIDTH-1:
                grid[i][j] = FLOOR

def create_dungeon(seed, floor, place_up_stairs=True, place_down_stairs=True):
    # Check if this is the boss floor
    is_boss_floor = (floor == 5)
    random.seed((seed, floor))  # Use tuple for unique per-floor
    grid = create_empty_grid()
    rooms = []
    for _ in range(NUM_ROOMS):
        w = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        h = random.randint(ROOM_MIN_SIZE, ROOM_MAX_SIZE)
        x = random.randint(1, GRID_WIDTH - w - 1)
        y = random.randint(1, GRID_HEIGHT - h - 1)
        new_room = (x, y, w, h)
        # Check for overlap
        failed = False
        for other in rooms:
            ox, oy, ow, oh = other
            if (x < ox + ow and x + w > ox and y < oy + oh and y + h > oy):
                failed = True
                break
        if not failed:
            place_room(grid, x, y, w, h)
            if rooms:
                # Connect to previous room with a corridor
                prev_x, prev_y, prev_w, prev_h = rooms[-1]
                prev_cx = prev_x + prev_w // 2
                prev_cy = prev_y + prev_h // 2
                new_cx = x + w // 2
                new_cy = y + h // 2
                if random.choice([True, False]):
                    # Horizontal then vertical
                    for j in range(min(prev_cx, new_cx), max(prev_cx, new_cx) + 1):
                        if 0 < j < GRID_WIDTH-1 and 0 < prev_cy < GRID_HEIGHT-1:
                            grid[prev_cy][j] = FLOOR
                    for i in range(min(prev_cy, new_cy), max(prev_cy, new_cy) + 1):
                        if 0 < new_cx < GRID_WIDTH-1 and 0 < i < GRID_HEIGHT-1:
                            grid[i][new_cx] = FLOOR
                else:
                    # Vertical then horizontal
                    for i in range(min(prev_cy, new_cy), max(prev_cy, new_cy) + 1):
                        if 0 < prev_cx < GRID_WIDTH-1 and 0 < i < GRID_HEIGHT-1:
                            grid[i][prev_cx] = FLOOR
                    for j in range(min(prev_cx, new_cx), max(prev_cx, new_cx) + 1):
                        if 0 < j < GRID_WIDTH-1 and 0 < new_cy < GRID_HEIGHT-1:
                            grid[new_cy][j] = FLOOR
            rooms.append(new_room)
    # Place stairs
    stairs_up_pos = None
    stairs_down_pos = None
    if rooms:
        # Place stairs in different rooms
        first_room = rooms[0]
        last_room = rooms[-1]
        if place_up_stairs:
            up_x = first_room[0] + first_room[2] // 2
            up_y = first_room[1] + first_room[3] // 2
            stairs_up_pos = (up_x, up_y)
        if place_down_stairs and floor != 5:
            # Try to place stairs down in a different room than stairs up
            down_room = last_room
            if place_up_stairs and len(rooms) > 1:
                # Find a room that is not the first room
                for room in reversed(rooms):
                    rx, ry, rw, rh = room
                    candidate = (rx + rw // 2, ry + rh // 2)
                    if candidate != stairs_up_pos:
                        down_room = room
                        break
            down_x = down_room[0] + down_room[2] // 2
            down_y = down_room[1] + down_room[3] // 2
            stairs_down_pos = (down_x, down_y)
        # Place tiles
        if stairs_up_pos:
            grid[stairs_up_pos[1]][stairs_up_pos[0]] = STAIRS_UP
        if stairs_down_pos:
            grid[stairs_down_pos[1]][stairs_down_pos[0]] = STAIRS_DOWN
    # Player starts at up stairs (or down stairs if no up stairs)
    if stairs_up_pos:
        player_start = stairs_up_pos
    elif stairs_down_pos:
        player_start = stairs_down_pos
    else:
        player_start = (1, 1)
    # Place enemies
    enemies = []
    attempts = 0
    while len(enemies) < ENEMIES_PER_FLOOR and attempts < 100:
        ex = random.randint(1, GRID_WIDTH - 2)
        ey = random.randint(1, GRID_HEIGHT - 2)
        if (grid[ey][ex] == FLOOR and
            (ex, ey) != player_start and
            (stairs_up_pos is None or (ex, ey) != stairs_up_pos) and
            (stairs_down_pos is None or (ex, ey) != stairs_down_pos) and
            (ex, ey) not in enemies):
            enemies.append((ex, ey))
        attempts += 1

    # Place enemy2 (one per floor)
    enemy2 = None
    attempts = 0
    while enemy2 is None and attempts < 100:
        ex = random.randint(1, GRID_WIDTH - 2)
        ey = random.randint(1, GRID_HEIGHT - 2)
        if (grid[ey][ex] == FLOOR and
            (ex, ey) != player_start and
            (stairs_up_pos is None or (ex, ey) != stairs_up_pos) and
            (stairs_down_pos is None or (ex, ey) != stairs_down_pos) and
            (ex, ey) not in enemies):
            enemy2 = (ex, ey)
        attempts += 1

    # Place boss on floor 5
    boss_pos = None
    if is_boss_floor:
        # Find a room with enough space for 2x2s
        for room in rooms:
            rx, ry, rw, rh = room
            # Check if room is big enough for boss (needs 2x2 space)
            if rw >= 2 and rh >= 2:
                # Try to place boss in center of room
                boss_x = rx + (rw //2 - 1)  # Center, but ensure 2x2 fits
                boss_y = ry + (rh // 2) - 1
                
                # Check if 2x2 area is all floor tiles
                can_place = True
                for dx in range(2):
                    for dy in range(2):
                        nx, ny = boss_x + dx, boss_y + dy
                        if (nx < 0 or nx >= GRID_WIDTH or ny < 0 or ny >= GRID_HEIGHT or
                            grid[ny][nx] != FLOOR or
                            (nx, ny) == player_start or
                            (nx, ny) in enemies or
                            (enemy2 is not None and (nx, ny) == enemy2)):
                            can_place = False
                            break
                    if not can_place:
                        break
                
                if can_place:
                    boss_pos = (boss_x, boss_y)
                    break
        
        # If no suitable room found, try placing in any available22ce
        if boss_pos is None:
            for y in range(1, GRID_HEIGHT - 2):
                for x in range(1, GRID_WIDTH - 2):
                    # Check if 2x2 area is available
                    can_place = True
                    for dx in range(2):
                        for dy in range(2):
                            nx, ny = x + dx, y + dy
                            if (grid[ny][nx] != FLOOR or
                                (nx, ny) == player_start or
                                (nx, ny) in enemies or
                                (enemy2 is not None and (nx, ny) == enemy2)):
                                can_place = False
                                break
                        if not can_place:
                            break
                    
                    if can_place:
                        boss_pos = (x, y)
                        break
                if boss_pos:
                    break

    return grid, player_start, stairs_up_pos, stairs_down_pos, enemies, enemy2, boss_pos



def draw_grid(screen, grid, player_x, player_y, enemies, enemy2, tile_images, boss_pos=None):
    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE + 40, CELL_SIZE, CELL_SIZE)
            # Draw base tile (floor or wall)
            if cell == WALL:
                if WALL in tile_images:
                    screen.blit(tile_images[WALL], rect)
                else:
                    pygame.draw.rect(screen, WALL_COLOR, rect)
            elif cell == FLOOR:
                if FLOOR in tile_images:
                    screen.blit(tile_images[FLOOR], rect)
                else:
                    pygame.draw.rect(screen, FLOOR_COLOR, rect)
            elif cell == STAIRS_DOWN:
                if STAIRS_DOWN in tile_images:
                    screen.blit(tile_images[STAIRS_DOWN], rect)
                else:
                    pygame.draw.rect(screen, STAIRS_DOWN_COLOR, rect)
            elif cell == STAIRS_UP:
                if STAIRS_UP in tile_images:
                    screen.blit(tile_images[STAIRS_UP], rect)
                else:
                    pygame.draw.rect(screen, STAIRS_UP_COLOR, rect)
            # Draw enemy or player on top
            if (x, y) in enemies:
                if ENEMY in tile_images:
                    screen.blit(tile_images[ENEMY], rect)
                else:
                    pygame.draw.rect(screen, ENEMY_COLOR, rect)
            if enemy2 and (x, y) == enemy2:
                if ENEMY2 in tile_images:
                    screen.blit(tile_images[ENEMY2], rect)
                else:
                    pygame.draw.rect(screen, ENEMY2_COLOR, rect)
            # Draw boss (32x32 like other enemies)
            if boss_pos and (x, y) == boss_pos:
                if BOSS in tile_images:
                    screen.blit(tile_images[BOSS], rect)
                else:
                    pygame.draw.rect(screen, (255, 0, 0), rect)
            if x == player_x and y == player_y:
                if PLAYER in tile_images:
                    screen.blit(tile_images[PLAYER], rect)
                else:
                    pygame.draw.rect(screen, PLAYER_COLOR, rect)

def can_move(grid, x, y, enemies=None, enemy2=None):
    if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
        if grid[y][x] == WALL:
            return False
        # Removed enemy collision - player can now pass through enemies
        return True
    return False

def draw_health_bar(surface, x, y, width, height, current_hp, max_hp, color):
    # Background
    pygame.draw.rect(surface, (50, 50, 50), (x, y, width, height))
    # Health bar
    health_width = int((current_hp / max_hp) * width)
    pygame.draw.rect(surface, color, (x, y, health_width, height))
    # Border
    pygame.draw.rect(surface, WHITE, (x, y, width, height), 2)

def draw_combat_ui(screen, ui_font, enemy_type, tile_images, player_hp, enemy_hp, player_max_hp, enemy_max_hp, combat_state, damage_dealt=None):
    # Combat popup dimensions and position
    combat_width = 600
    combat_height = 400
    combat_x = (WINDOW_WIDTH - combat_width) // 2
    combat_y = (WINDOW_HEIGHT - combat_height) // 2
    
    # Create combat popup surface
    combat_surface = pygame.Surface((combat_width, combat_height))
    combat_surface.fill(BLACK)
    
    # Draw combat background if available, otherwise use solid color
    if 'combat_bg' in tile_images:
        # Scale background to fit combat popup
        scaled_bg = pygame.transform.scale(tile_images['combat_bg'], (combat_width, combat_height))
        combat_surface.blit(scaled_bg, (0, 0))
    else:
        # Use a dark background as fallback
        combat_surface.fill((40, 40, 40))
    
    # Draw player sprite (left side of combat popup)
    if 'player_combat' in tile_images:
        player_sprite = tile_images['player_combat']
        # Scale sprite to fit combat popup (make it larger)
        scaled_player = pygame.transform.scale(player_sprite, (150, 150))
        player_x = 100
        player_y = combat_height // 2 - 20  # Move lower
        combat_surface.blit(scaled_player, (player_x, player_y))
    
    # Draw enemy sprite (right side of combat popup)
    if enemy_type == "boss":
        if BOSS in tile_images:
            enemy_sprite = pygame.transform.scale(tile_images[BOSS], (180, 180))
            enemy_x = combat_width - 100 - enemy_sprite.get_width()
            enemy_y = combat_height // 2 - 40
            combat_surface.blit(enemy_sprite, (enemy_x, enemy_y))
        else:
            enemy_x = combat_width - 180
            enemy_y = combat_height // 2 - 40
            pygame.draw.rect(combat_surface, (255, 0, 0), (enemy_x, enemy_y, 180, 180))
    else:
        enemy_sprite_key = 'enemy2_combat' if enemy_type == "enemy2" else 'enemy_combat'
        if enemy_sprite_key in tile_images:
            enemy_sprite = tile_images[enemy_sprite_key]
            scaled_enemy = pygame.transform.scale(enemy_sprite, (150, 150))
            enemy_x = combat_width - 100 - scaled_enemy.get_width()
            enemy_y = combat_height // 2 - 20
            combat_surface.blit(scaled_enemy, (enemy_x, enemy_y))
    
    # Combat title
    title = ui_font.render("EN GARDE!", True, WHITE)
    title_rect = title.get_rect(center=(combat_width // 2, 30))
    combat_surface.blit(title, title_rect)
    
    # Health bars - moved higher
    # Player health bar
    draw_health_bar(combat_surface, 100, 120, 150, 20, player_hp, player_max_hp, GREEN)
    player_hp_text = ui_font.render(f"HP: {max(0, player_hp)}/{player_max_hp}", True, WHITE)
    combat_surface.blit(player_hp_text, (100, 145))
    
    # Enemy health bar
    if enemy_type == "boss":
        enemy_hp_color = (255, 0, 0)
    else:
        enemy_hp_color = ENEMY2_COLOR if enemy_type == "enemy2" else ENEMY_COLOR
    draw_health_bar(combat_surface, 350, 120, 150, 20, enemy_hp, enemy_max_hp, enemy_hp_color)
    enemy_hp_text = ui_font.render(f"HP: {max(0, enemy_hp)}/{enemy_max_hp}", True, WHITE)
    combat_surface.blit(enemy_hp_text, (350, 145))
    
    # Create smaller font for instructions
    small_font = pygame.font.SysFont("monospace", 14)
    
    # Combat info consolidated to bottom left
    info_x = 10
    info_y = combat_height - 40
    line_height = 18
    
    # Damage display
    if damage_dealt is not None:
        damage_text = small_font.render(f"Damage: {damage_dealt}", True, RED)
        combat_surface.blit(damage_text, (info_x, info_y))
        info_y += line_height
    
    # Combat state and instructions
    if combat_state == "player_turn":
        # All options on one line
        options_text = small_font.render("A: Attack | D: Defend | F: Flee", True, WHITE)
        combat_surface.blit(options_text, (info_x, info_y))
    elif combat_state == "enemy_turn":
        instructions = small_font.render("Enemy attacks!", True, WHITE)
        combat_surface.blit(instructions, (info_x, info_y))
    elif combat_state == "victory":   # Large victory message in center
        victory_font = pygame.font.SysFont("monospace", 48)
        victory_text = victory_font.render("VICTORY!", True, GREEN)
        victory_rect = victory_text.get_rect(center=(combat_width // 2, combat_height // 2))
        combat_surface.blit(victory_text, victory_rect)
        # Small instruction below
        instructions2 = small_font.render("Press any key", True, WHITE)
        instructions2_rect = instructions2.get_rect(center=(combat_width // 2, combat_height // 2 + 60))
        combat_surface.blit(instructions2, instructions2_rect)
    elif combat_state == "fled":
        instructions = small_font.render("You fled! Press Any Key to Continue", True, WHITE)
        combat_surface.blit(instructions, (info_x, info_y))
        info_y += line_height
       
    
    # Draw combat popup on main screen
    screen.blit(combat_surface, (combat_x, combat_y))

def draw_game_over_screen(screen, ui_font):
    # Create a semi-transparent overlay
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    overlay.set_alpha(128)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))
    
    # Large game over text
    game_over_font = pygame.font.SysFont("monospace",72)
    game_over_text = game_over_font.render("GAME OVER", True, RED)
    game_over_rect = game_over_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
    screen.blit(game_over_text, game_over_rect)
    
    # Instructions
    instruction_text = ui_font.render("Press SPACE to start a new game", True, WHITE)
    instruction_rect = instruction_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
    screen.blit(instruction_text, instruction_rect)

def calculate_damage(min_damage, max_damage, is_defending=False):
    base_damage = random.randint(min_damage, max_damage)
    if is_defending:
        base_damage = max(1, base_damage // 2)  # Defending reduces damage by half
    return base_damage




def draw_ui(screen, ui_font, seed, seed_input_mode, seed_input, floor):
    if seed_input_mode:
        msg = f"Enter new seed: {seed_input}"  # Show what user is typing
        color = GRAY
    else:
        msg = f"Seed: {seed} (press 'S' to change)" if floor == 1 else f"Seed: {seed} (locked)"
        color = WHITE
    text = ui_font.render(msg, True, color)
    screen.blit(text, (10, 5))
    floor_msg = f"Floor: {floor}"
    floor_text = ui_font.render(floor_msg, True, WHITE)
    screen.blit(floor_text, (WINDOW_WIDTH - 120, 5))

def find_adjacent_floor(grid, x, y):
    # Try to find a neighboring floor tile (up, down, left, right)
    for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
        nx, ny = x + dx, y + dy
        if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
            if grid[ny][nx] == FLOOR:
                return nx, ny
    return x, y  # No adjacent floor found, stay in place

def move_enemies(grid, enemies, enemy2, player_pos):
    new_enemies = []
    for (ex, ey) in enemies:
        possible_moves = []
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = ex + dx, ey + dy
            if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                if grid[ny][nx] == FLOOR and (nx, ny) != player_pos and (nx, ny) not in enemies and (enemy2 is None or (nx, ny) != enemy2):
                    possible_moves.append((nx, ny))
        if possible_moves:
            new_pos = random.choice(possible_moves)
            new_enemies.append(new_pos)
        else:
            new_enemies.append((ex, ey))
    
    # Move enemy2
    new_enemy2 = enemy2
    if enemy2:
        ex, ey = enemy2
        possible_moves = []
        for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
            nx, ny = ex + dx, ey + dy
            if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                if grid[ny][nx] == FLOOR and (nx, ny) != player_pos and (nx, ny) not in enemies and (nx, ny) != enemy2:
                    possible_moves.append((nx, ny))
        if possible_moves:
            new_enemy2 = random.choice(possible_moves)
    
    return new_enemies, new_enemy2

def main():
    seed = 42
    floor = 1
    grid, (player_x, player_y), stairs_up_pos, stairs_down_pos, enemies, enemy2, boss_pos = create_dungeon(seed, floor, place_up_stairs=True, place_down_stairs=True)
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    tile_images = load_tile_images()
    pygame.display.set_caption("ASCII Roguelike")
    ui_font = pygame.font.SysFont("monospace", UI_FONT_SIZE)
    clock = pygame.time.Clock()
    seed_input_mode = False
    seed_input = ""
    enemy_move_counter = 0
    ENEMY_MOVE_DELAY = 50  # Move enemies every 15 frames
    
    # Combat state
    in_combat = False
    combat_enemy_type = None
    combat_enemy_pos = None
    player_hp = PLAYER_MAX_HP
    player_max_hp = PLAYER_MAX_HP
    enemy_hp = 0
    enemy_max_hp = 0
    combat_state = "player_turn"  # player_turn, enemy_turn, victory, defeat, fled
    damage_dealt = None
    player_defending = False
    enemy_turn_delay = 0  # Counter for enemy turn delay
    
    # Game over state
    game_over = False
    game_won = False

    title_screen = True
    while True:
        if title_screen:
            fade_alpha = 0
            fade_in_done = False
            # Prepare title and prompt surfaces
            title_font = pygame.font.SysFont("monospace", 72)
            title_text = title_font.render("ENTER THE DUNGEON", True, (255, 0, 0))
            title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
            prompt_font = pygame.font.SysFont("monospace", 32)
            prompt_text = prompt_font.render("Press SPACE to start", True, (255, 255, 255))
            prompt_rect = prompt_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
            # Create a surface for fade-in
            fade_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            while title_screen:
                screen.fill((0, 0, 0))
                fade_surface.fill((0, 0, 0, 0))
                fade_surface.blit(title_text, title_rect)
                fade_surface.blit(prompt_text, prompt_rect)
                if not fade_in_done:
                    fade_surface.set_alpha(fade_alpha)
                    fade_alpha += 5  # Increase for faster/slower fade
                    if fade_alpha >= 255:
                        fade_alpha = 255
                        fade_in_done = True
                else:
                    fade_surface.set_alpha(255)
                screen.blit(fade_surface, (0, 0))
                pygame.display.flip()
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    elif fade_in_done and event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                        title_screen = False
                pygame.time.Clock().tick(30)
            continue

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if game_won:
                    if event.key == pygame.K_SPACE:
                        # Start new game
                        game_won = False
                        game_over = False
                        floor = 1
                        grid, (player_x, player_y), stairs_up_pos, stairs_down_pos, enemies, enemy2, boss_pos = create_dungeon(seed, floor, place_up_stairs=True, place_down_stairs=True)
                        player_hp = PLAYER_MAX_HP
                        in_combat = False
                        combat_enemy_type = None
                        combat_enemy_pos = None
                        combat_state = "player_turn"
                        damage_dealt = None
                        player_defending = False
                elif game_over:
                    if event.key == pygame.K_SPACE:
                        # Start new game
                        game_over = False
                        floor = 1
                        grid, (player_x, player_y), stairs_up_pos, stairs_down_pos, enemies, enemy2, boss_pos = create_dungeon(seed, floor, place_up_stairs=True, place_down_stairs=True)
                        player_hp = PLAYER_MAX_HP
                        in_combat = False
                        combat_enemy_type = None
                        combat_enemy_pos = None
                        combat_state = "player_turn"
                        damage_dealt = None
                        player_defending = False
                elif in_combat:
                    if combat_state == "player_turn":
                        if event.key == pygame.K_a:  # Attack
                            attack_sound.play()
                            damage = calculate_damage(PLAYER_ATTACK_MIN, PLAYER_ATTACK_MAX)
                            enemy_hp -= damage
                            damage_dealt = damage
                            combat_state = "enemy_turn"
                            player_defending = False
                            enemy_turn_delay = 30  # 1 second delay at 30 FPS
                        elif event.key == pygame.K_d:  # Defend
                            player_defending = True
                            combat_state = "enemy_turn"
                            enemy_turn_delay = 30  # 1 second delay at 30 FPS
                        elif event.key == pygame.K_f:  # Flee
                            if random.random() < 0.7:  # 70% chance to flee
                                combat_state = "fled"
                                for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                                    nx, ny = player_x + dx, player_y + dy
                                    if (0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT and
                                        grid[ny][nx] == FLOOR and
                                        (nx, ny) not in enemies and
                                        (enemy2 is None or (nx, ny) != enemy2) and
                                        (boss_pos is None or (nx, ny) != boss_pos)):
                                        player_x, player_y = nx, ny
                                        break
                            else:
                                combat_state = "enemy_turn"
                                enemy_turn_delay = 30  # 1 second delay at 30 FPS
                    elif combat_state in ["enemy_turn", "victory", "defeat", "fled"]:
                        if combat_state == "enemy_turn":
                            # Enemy attacks
                            if enemy_hp > 0:
                                if combat_enemy_type == "boss":
                                    min_dmg = BOSS_ATTACK_MIN
                                    max_dmg = BOSS_ATTACK_MAX
                                elif combat_enemy_type == "enemy2":
                                    min_dmg = ENEMY2_ATTACK_MIN
                                    max_dmg = ENEMY2_ATTACK_MAX
                                else:
                                    min_dmg = ENEMY_ATTACK_MIN
                                    max_dmg = ENEMY_ATTACK_MAX
                                damage = calculate_damage(min_dmg, max_dmg, player_defending)
                                player_hp -= damage
                                damage_dealt = damage
                                enemy_attack_sound.play() # Play enemy attack sound
                            
                            # Check combat result
                            if enemy_hp <= 0:
                                combat_state = "victory"
                            elif player_hp <= 0:
                                # Go straight to game over, skip defeat message
                                game_over = True
                                if combat_enemy_type == "enemy":
                                    if combat_enemy_pos in enemies:
                                        enemies.remove(combat_enemy_pos)
                                elif combat_enemy_type == "enemy2":
                                    enemy2 = None
                                in_combat = False
                                combat_enemy_type = None
                                combat_enemy_pos = None
                                combat_state = "player_turn"
                                damage_dealt = None
                                player_defending = False
                            else:
                                combat_state = "player_turn"
                        else:
                            # Combat ended, return to game
                            if combat_state == "victory":
                                # Check if boss was defeated
                                if combat_enemy_type == "boss":
                                    game_won = True
                                else:
                                    # Remove defeated enemy
                                    if combat_enemy_type == "enemy":
                                        if combat_enemy_pos in enemies:
                                            enemies.remove(combat_enemy_pos)
                                    elif combat_enemy_type == "enemy2":
                                        enemy2 = None
                            elif combat_state == "defeat":
                                # Game over when player is defeated
                                game_over = True
                                if combat_enemy_type == "enemy":
                                    if combat_enemy_pos in enemies:
                                        enemies.remove(combat_enemy_pos)
                                elif combat_enemy_type == "enemy2":
                                    enemy2 = None
                            
                            in_combat = False
                            combat_enemy_type = None
                            combat_enemy_pos = None
                            combat_state = "player_turn"
                            damage_dealt = None
                            player_defending = False
                elif seed_input_mode:
                    if event.key == pygame.K_RETURN:
                        # Try to set new seed
                        try:
                            new_seed = int(seed_input)
                            seed = new_seed
                            floor = 1
                            grid, (player_x, player_y), stairs_up_pos, stairs_down_pos, enemies, enemy2, boss_pos = create_dungeon(seed, floor, place_up_stairs=True, place_down_stairs=True)
                            player_hp = PLAYER_MAX_HP
                        except ValueError:
                            pass  # Ignore invalid input
                        seed_input_mode = False
                        seed_input = ""
                    elif event.key == pygame.K_BACKSPACE:
                        seed_input = seed_input[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        seed_input_mode = False
                        seed_input = ""
                    else:
                        if event.unicode.isdigit() or (event.unicode == '-' and len(seed_input) == 0):
                            seed_input += event.unicode
                else:
                    dx, dy = 0, 0
                    if event.key == pygame.K_UP:
                        dy = -1
                    elif event.key == pygame.K_DOWN:
                        dy = 1
                    elif event.key == pygame.K_LEFT:
                        dx = -1
                    elif event.key == pygame.K_RIGHT:
                        dx = 1
                    elif event.key == pygame.K_s and floor == 1:
                        seed_input_mode = True
                        seed_input = ""
                    if not seed_input_mode and can_move(grid, player_x + dx, player_y + dy, enemies, enemy2):
                        player_x += dx
                        player_y += dy
        
        # Handle automatic enemy turn
        if in_combat and combat_state == "enemy_turn":
            if enemy_turn_delay > 0:
                enemy_turn_delay -= 1
            else:
                # Enemy attacks
                if enemy_hp > 0:
                    if combat_enemy_type == "boss":
                        min_dmg = BOSS_ATTACK_MIN
                        max_dmg = BOSS_ATTACK_MAX
                    elif combat_enemy_type == "enemy2":
                        min_dmg = ENEMY2_ATTACK_MIN
                        max_dmg = ENEMY2_ATTACK_MAX
                    else:
                        min_dmg = ENEMY_ATTACK_MIN
                        max_dmg = ENEMY_ATTACK_MAX
                    damage = calculate_damage(min_dmg, max_dmg, player_defending)
                    player_hp -= damage
                    damage_dealt = damage
                    enemy_attack_sound.play() # Play enemy attack sound
                
                # Check combat result
                if enemy_hp <= 0:
                    combat_state = "victory"
                elif player_hp <= 0:
                    # Go straight to game over, skip defeat message
                    game_over = True
                    if combat_enemy_type == "enemy":
                        if combat_enemy_pos in enemies:
                            enemies.remove(combat_enemy_pos)
                    elif combat_enemy_type == "enemy2":
                        enemy2 = None
                    in_combat = False
                    combat_enemy_type = None
                    combat_enemy_pos = None
                    combat_state = "player_turn"
                    damage_dealt = None
                    player_defending = False
                else:
                    combat_state = "player_turn"
        
        # Handle stairs and move off stairs if needed
        transitioned = False
        if not seed_input_mode and not in_combat:
            if (player_x, player_y) == stairs_down_pos:
                floor += 1
                grid, _, stairs_up_pos, stairs_down_pos, enemies, enemy2, boss_pos = create_dungeon(seed, floor, place_up_stairs=True, place_down_stairs=True)
                player_x, player_y = stairs_up_pos if stairs_up_pos else (1, 1)
                transitioned = True
            elif (player_x, player_y) == stairs_up_pos and floor > 1:
                floor -= 1
                grid, _, stairs_up_pos, stairs_down_pos, enemies, enemy2, boss_pos = create_dungeon(seed, floor, place_up_stairs=(floor > 1), place_down_stairs=True)
                player_x, player_y = stairs_down_pos if stairs_down_pos else (1, 1)
                transitioned = True
        # Move off stairs if needed
        if transitioned and grid[player_y][player_x] in (STAIRS_UP, STAIRS_DOWN):
            new_x, new_y = find_adjacent_floor(grid, player_x, player_y)
            player_x, player_y = new_x, new_y
        # Check for combat
        if not in_combat and not seed_input_mode:
            if (player_x, player_y) in enemies:
                in_combat = True
                combat_enemy_type = "enemy"
                combat_enemy_pos = (player_x, player_y)
                enemy_hp = ENEMY_MAX_HP
                enemy_max_hp = ENEMY_MAX_HP
                combat_state = "player_turn"
            elif enemy2 and (player_x, player_y) == enemy2:
                in_combat = True
                combat_enemy_type = "enemy2"
                combat_enemy_pos = (player_x, player_y)
                enemy_hp = ENEMY2_MAX_HP
                enemy_max_hp = ENEMY2_MAX_HP
                combat_state = "player_turn"
            # Boss combat
            elif boss_pos and (player_x, player_y) == boss_pos and floor == 5:
                in_combat = True
                combat_enemy_type = "boss"
                combat_enemy_pos = boss_pos
                enemy_hp = BOSS_MAX_HP
                enemy_max_hp = BOSS_MAX_HP
                combat_state = "player_turn"
        # Move enemies every ENEMY_MOVE_DELAY frames
        if not in_combat:
            enemy_move_counter += 1
            if enemy_move_counter >= ENEMY_MOVE_DELAY:
                enemies, enemy2 = move_enemies(grid, enemies, enemy2, (player_x, player_y))
                enemy_move_counter = 0
        
        # Draw everything
        screen.fill(BLACK)
        draw_ui(screen, ui_font, seed, seed_input_mode, seed_input, floor)
        draw_grid(screen, grid, player_x, player_y, enemies, enemy2, tile_images, boss_pos)
        if not game_over and not game_won:
            if in_combat:
                draw_combat_ui(screen, ui_font, combat_enemy_type, tile_images, player_hp, enemy_hp, player_max_hp, enemy_max_hp, combat_state, damage_dealt)
        if game_over:
            draw_game_over_screen(screen, ui_font)
        if game_won:
            draw_game_win_screen(screen, ui_font)
        pygame.display.flip()
        clock.tick(30)



def draw_game_win_screen(screen, ui_font):
    overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    overlay.set_alpha(180)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))
    win_font = pygame.font.SysFont("monospace", 72)
    win_text = win_font.render("YOU WIN!", True, (0, 255, 0))
    win_rect = win_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
    screen.blit(win_text, win_rect)
    instruction_text = ui_font.render("Press SPACE to play again", True, WHITE)
    instruction_rect = instruction_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
    screen.blit(instruction_text, instruction_rect)

if __name__ == "__main__":
    main() 