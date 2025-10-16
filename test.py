import pygame
import sys
import random
import math
from player import Player  # uses the player.py file provided above

# --- Settings ---
WIDTH, HEIGHT = 800, 600
FPS = 60
GRID_SIZE = 12  # 12x12 rooms
START_CELL = (GRID_SIZE // 2, GRID_SIZE // 2)  # start in center

# --- Colors ---
Grey = (146, 142, 133)
Dark_Grey = (59, 59, 59)
HEALTH_BAR_COLOR = (255, 0, 0)
HEALTH_BAR_BG_COLOR = (100, 0, 0)
WHITE = (255, 255, 255)
DOOR_CLOSED = (180, 50, 50)
DOOR_OPEN = (50, 180, 50)
DOOR_BORDER = (30, 30, 30)

# --- Init ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Crossbow — Rooms")
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 36)
pause_font = pygame.font.SysFont(None, 72)

# --- Utility surfaces (procedural textures) ---
def make_stone_tile(seed, tile_size=32):
    """Create a stone tile surface with some scratches and moss variation based on seed."""
    rnd = random.Random(seed)
    surf = pygame.Surface((tile_size, tile_size))
    # base stone color varies slightly
    base = (120 + rnd.randint(-10, 10), 120 + rnd.randint(-10, 10), 115 + rnd.randint(-10, 10))
    surf.fill(base)
    # draw grout lines
    grout = (80 + rnd.randint(-5, 5), 75 + rnd.randint(-5, 5), 70 + rnd.randint(-5, 5))
    pygame.draw.line(surf, grout, (0, tile_size//2), (tile_size, tile_size//2), 1)
    pygame.draw.line(surf, grout, (tile_size//2, 0), (tile_size//2, tile_size), 1)
    # add some moss spots
    for _ in range(rnd.randint(1, 4)):
        mx = rnd.randint(0, tile_size-6)
        my = rnd.randint(0, tile_size-6)
        size = rnd.randint(2, 6)
        moss = (50 + rnd.randint(-10, 30), 80 + rnd.randint(-20, 20), 40 + rnd.randint(-10, 10))
        pygame.draw.ellipse(surf, moss, (mx, my, size, size))
    # subtle scratches
    for _ in range(rnd.randint(2, 5)):
        x1 = rnd.randint(0, tile_size)
        y1 = rnd.randint(0, tile_size)
        x2 = min(tile_size, x1 + rnd.randint(-6, 6))
        y2 = min(tile_size, y1 + rnd.randint(-6, 6))
        pygame.draw.line(surf, (200, 200, 200, 40), (x1, y1), (x2, y2), 1)
    return surf

def make_brick_tile(seed, tile_w=32, tile_h=16):
    rnd = random.Random(seed)
    surf = pygame.Surface((tile_w, tile_h))
    base = (140 + rnd.randint(-10, 10), 110 + rnd.randint(-10,10), 100 + rnd.randint(-10,10))
    surf.fill(base)
    # draw mortar lines
    mortar = (100 + rnd.randint(-5,5), 90 + rnd.randint(-5,5), 85 + rnd.randint(-5,5))
    pygame.draw.line(surf, mortar, (0, tile_h-2), (tile_w, tile_h-2), 2)
    # subtle darker edges
    pygame.draw.rect(surf, (base[0]-10, base[1]-10, base[2]-10), (0, 0, tile_w, tile_h), 1)
    # a small moss smear
    if rnd.random() < 0.4:
        mx = rnd.randint(0, tile_w-8)
        my = rnd.randint(0, tile_h-6)
        pygame.draw.ellipse(surf, (60,90,50), (mx, my, rnd.randint(4,8), rnd.randint(2,6)))
    return surf

# --- Wall Class ---
class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, color=Dark_Grey, image=None):
        super().__init__()
        if image:
            # tile the image into the wall rect
            surf = pygame.Surface((w, h))
            for ix in range(0, w, image.get_width()):
                for iy in range(0, h, image.get_height()):
                    surf.blit(image, (ix, iy))
            self.image = surf
        else:
            self.image = pygame.Surface((w, h))
            self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))

# --- Particle Class ---
class Particle(pygame.sprite.Sprite):
    def __init__(self, x, y, color=(255, 200, 100)):
        super().__init__()
        self.image = pygame.Surface((4, 4))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.dx = random.uniform(-2, 2)
        self.dy = random.uniform(-2, 2)
        self.lifetime = random.randint(10, 20)

    def update(self):
        self.rect.x += int(self.dx)
        self.rect.y += int(self.dy)
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()

# --- PowerUp ---
class PowerUp(pygame.sprite.Sprite):
    TYPES = ["health", "multi", "speed", "rapid", "pierce", "explosive"]

    def __init__(self, x, y, kind=None):
        super().__init__()
        self.type = kind if kind is not None else random.choice(PowerUp.TYPES)
        self.image = pygame.Surface((20, 20))
        cmap = {
            "health": (0, 255, 0),
            "multi": (0, 200, 255),
            "speed": (0, 0, 255),
            "rapid": (255, 255, 0),
            "pierce": (255, 100, 0),
            "explosive": (200, 0, 200)
        }
        self.image.fill(cmap.get(self.type, (255, 255, 255)))
        self.rect = self.image.get_rect(center=(x, y))
        self.timer = 15 * FPS

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            self.kill()

# --- Projectile & constants reused from player.py ---
PROJECTILE_SPEED = 8
SHOOT_COOLDOWN = 300  # ms

ENEMY_SIZE = 30
ENEMY_COLOR = (255, 0, 0)
ENEMY_SPEED = 2

YELLOW = (255, 255, 0)

def update(self, walls=None):
        self.age += 1
        self.pos_x += self.dx
        self.pos_y += self.dy
        self.rect.centerx = int(self.pos_x)
        self.rect.centery = int(self.pos_y)

        # collide with walls -> vanish
        if walls and pygame.sprite.spritecollideany(self, walls):
            self.kill()
            return

        if self.age >= self.fly_time:
            self.kill()

# --- Enemy classes (kept from your original) ---
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((ENEMY_SIZE, ENEMY_SIZE))
        self.original_color = ENEMY_COLOR
        self.flash_color = (255, 255, 0)
        self.image.fill(self.original_color)
        self.rect = self.image.get_rect(center=(x, y))
        self.health = 2
        self.flash_timer = 0

    def update(self, player):
        if self.flash_timer > 0:
            self.flash_timer -= 1
            if self.flash_timer == 0:
                self.image.fill(self.original_color)

        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = max(1.0, math.hypot(dx, dy))
        self.rect.x += int(ENEMY_SPEED * dx / dist)
        self.rect.y += int(ENEMY_SPEED * dy / dist)
        return None

    def take_hit(self):
        self.health -= 1
        self.image.fill(self.flash_color)
        self.flash_timer = 15
        return self.health <= 0

class ShooterEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image.fill((200, 50, 200))
        self.shoot_cooldown = 90
        self.timer = 0

    def update(self, player):
        super().update(player)
        self.timer += 1
        if self.timer >= self.shoot_cooldown:
            self.timer = 0
            return EnemyProjectile(self.rect.centerx, self.rect.centery, player)
        return None

class JumperEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image.fill((50, 200, 50))
        self.jump_cooldown = random.randint(120, 180)
        self.timer = 0
        self.target = None

    def update(self, player):
        if self.flash_timer > 0:
            self.flash_timer -= 1
            if self.flash_timer == 0:
                self.image.fill((50, 200, 50))

        self.timer += 1
        if self.timer >= self.jump_cooldown:
            self.timer = 0
            self.jump_cooldown = random.randint(120, 180)
            self.target = player.rect.center

        if self.target:
            dx = self.target[0] - self.rect.centerx
            dy = self.target[1] - self.rect.centery
            dist = max(1.0, math.hypot(dx, dy))
            speed = 6
            self.rect.x += int(speed * dx / dist)
            self.rect.y += int(speed * dy / dist)
            if abs(dx) < 10 and abs(dy) < 10:
                self.target = None
        return None

class EnemyProjectile(pygame.sprite.Sprite):
    def __init__(self, x, y, player):
        super().__init__()
        self.image = pygame.Surface((8, 8))
        self.image.fill((255, 150, 0))
        self.rect = self.image.get_rect(center=(x, y))

        self.pos_x = float(self.rect.centerx)
        self.pos_y = float(self.rect.centery)

        dx = player.rect.centerx - x
        dy = player.rect.centery - y
        dist = max(1.0, math.hypot(dx, dy))
        speed = 5.0
        self.dx = speed * dx / dist
        self.dy = speed * dy / dist

    def update(self, walls=None):
        self.pos_x += self.dx
        self.pos_y += self.dy
        self.rect.centerx = int(self.pos_x)
        self.rect.centery = int(self.pos_y)
        if walls and pygame.sprite.spritecollideany(self, walls):
            self.kill()

# --- Enemy spawn utilities ---
def spawn_enemy_type():
    r = random.random()
    if r < 0.6:
        return Enemy
    elif r < 0.85:
        return ShooterEnemy
    else:
        return JumperEnemy

def random_spawn_point_away_from(rect, margin=120):
    """Return x,y inside the room bounds but away from rect center by margin pixels."""
    for _ in range(300):
        x = random.randint(120, WIDTH - 120)
        y = random.randint(120, HEIGHT - 120)
        dist = math.hypot(x - rect.centerx, y - rect.centery)
        if dist > margin:
            return x, y
    return WIDTH // 2, HEIGHT // 2

# --- Doors and Room classes ---
class Door(pygame.sprite.Sprite):
    SIZE = 80  # door width (for top/bottom) or height (for left/right)
    THICK = 12  # door thickness in wall

    def __init__(self, direction, room_rect, is_open=False):
        super().__init__()
        self.direction = direction  # 'up','down','left','right'
        self.is_open = is_open
        if direction in ("up", "down"):
            w = Door.SIZE
            h = Door.THICK
            self.image = pygame.Surface((w, h))
        else:
            w = Door.THICK
            h = Door.SIZE
            self.image = pygame.Surface((w, h))
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        cx, cy = room_rect.center
        if direction == "up":
            self.rect.centerx = cx
            self.rect.top = room_rect.top
        elif direction == "down":
            self.rect.centerx = cx
            self.rect.bottom = room_rect.bottom
        elif direction == "left":
            self.rect.left = room_rect.left
            self.rect.centery = cy
        elif direction == "right":
            self.rect.right = room_rect.right
            self.rect.centery = cy

    def draw(self, surface):
        color = DOOR_OPEN if self.is_open else DOOR_CLOSED
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, DOOR_BORDER, self.rect, 2)

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False

class Room:
    PADDING = 100  # wall thickness area

    def __init__(self, gx, gy, seed=None):
        self.gx = gx
        self.gy = gy
        self.key = (gx, gy)
        self.seed = seed or (gx * 1000 + gy)
        self.rnd = random.Random(self.seed)

        # groups
        self.walls = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.enemy_projectiles = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.particles = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.active_events = []

        # define room rectangle (play area inside walls)
        self.room_rect = pygame.Rect(0, 0, WIDTH, HEIGHT)
        # Doors placeholders (some may be None)
        self.doors = {"up": None, "down": None, "left": None, "right": None}
        # Connectivity
        self.connections = {"up": False, "down": False, "left": False, "right": False}
        # cleared flag
        self.cleared = False
        # tracks whether room has been initialized (so we only spawn once)
        self.generated = False

        # textures for this room
        self.floor_tile = make_stone_tile(self.seed)
        self.wall_tile = make_brick_tile(self.seed + 999)

        # Build walls and (doors will be added if connections set)
        self._build_basic_walls()

        # do initial generation of enemies/powerups only when player first enters
        # but create a small placeholder so check_cleared works
        # (actual spawn will be done in generate_contents)
        # self._spawn_enemies_initial()
        # occasionally pre-place a powerup
        if self.rnd.random() < 0.12:
            px = self.rnd.randint(120, WIDTH - 120)
            py = self.rnd.randint(120, HEIGHT - 120)
            self.powerups.add(PowerUp(px, py))

    def _build_basic_walls(self):
        # Outer walls: top, bottom, left, right thick blocks tiled with wall texture
        top = Wall(0, 0, WIDTH, Room.PADDING, image=self.wall_tile)
        bottom = Wall(0, HEIGHT - Room.PADDING, WIDTH, Room.PADDING, image=self.wall_tile)
        left = Wall(0, 0, Room.PADDING, HEIGHT, image=self.wall_tile)
        right = Wall(WIDTH - Room.PADDING, 0, Room.PADDING, HEIGHT, image=self.wall_tile)
        self.walls.add(top, bottom, left, right)

    def generate_contents(self, player_rect):
        """Populate room with enemies/powerups the first time it's entered."""
        if self.generated:
            return
        self.generated = True

        cnt = self.rnd.randint(1, 4)
        for _ in range(cnt):
            cls = spawn_enemy_type()
            x, y = random_spawn_point_away_from(player_rect, 120)
            e = cls(x, y)
            self.enemies.add(e)

        # small extra chance for an airstrike event (keeps old event system)
        #Rif self.rnd.random() < 0.08:
            #self.active_events.append(AirstrikeEvent(WIDTH, HEIGHT, player_rect.centerx, player_rect.centery))

        # small chance of a powerup
        if self.rnd.random() < 0.25:
            px, py = random_spawn_point_away_from(player_rect, 150)
            self.powerups.add(PowerUp(px, py))

    def ensure_connection(self, direction, exists=True):
        if direction not in self.connections:
            return
        self.connections[direction] = exists
        if exists and self.doors[direction] is None:
            d = Door(direction, self.room_rect, is_open=False)
            self.doors[direction] = d
            block = Wall(d.rect.left, d.rect.top, d.rect.width, d.rect.height, image=None)
            block.door_block = True
            d.block = block
            self.walls.add(block)
        elif not exists and self.doors[direction] is not None:
            d = self.doors[direction]
            if hasattr(d, "block"):
                d.block.kill()
            self.doors[direction] = None
            self.connections[direction] = False

    def open_doors_if_cleared(self):
        if self.cleared:
            for dir_name, d in self.doors.items():
                if d and not d.is_open:
                    d.open()
                    if hasattr(d, "block"):
                        try:
                            d.block.kill()
                        except Exception:
                            pass

    def check_cleared(self):
        # if no enemies (or all dead), mark cleared and open doors
        if not self.enemies:
            if not self.cleared:
                self.cleared = True
            self.open_doors_if_cleared()

    def spawn_more(self, amount=1, player_rect=None):
        for _ in range(amount):
            cls = spawn_enemy_type()
            if player_rect:
                x, y = random_spawn_point_away_from(player_rect, 120)
            else:
                x = self.rnd.randint(self.room_rect.left + 120, self.room_rect.right - 120)
                y = self.rnd.randint(self.room_rect.top + 120, self.room_rect.bottom - 120)
            e = cls(x, y)
            self.enemies.add(e)

    def draw_floor(self, surface):
        # tile floor using floor_tile
        tile = self.floor_tile
        for ix in range(0, WIDTH, tile.get_width()):
            for iy in range(0, HEIGHT, tile.get_height()):
                surface.blit(tile, (ix, iy))

    def draw_doors(self, surface):
        for d in self.doors.values():
            if d:
                d.draw(surface)

    def update_events(self):
        for ev in list(self.active_events):
            ev.update(screen, player, self.enemies, self.particles)
            if not ev.active:
                self.active_events.remove(ev)

# --- RoomManager ---
class RoomManager:
    def __init__(self, size=GRID_SIZE, start_cell=START_CELL):
        self.size = size
        self.grid = {}  # (gx,gy)->Room
        self.curr = None
        self.curr_pos = start_cell
        self._create_room_at(*start_cell)
        self.ensure_start_connected(*start_cell)
        self.enter_room(*start_cell)

    def _in_bounds(self, gx, gy):
        return 0 <= gx < self.size and 0 <= gy < self.size

    def _create_room_at(self, gx, gy):
        if not self._in_bounds(gx, gy):
            return None
        if (gx, gy) in self.grid:
            return self.grid[(gx, gy)]
        room = Room(gx, gy)
        self.grid[(gx, gy)] = room
        return room

    def ensure_start_connected(self, gx, gy):
        room = self.grid[(gx, gy)]
        possible_dirs = ["up", "down", "left", "right"]
        chosen = random.choice(possible_dirs)
        self._ensure_connection_between(gx, gy, chosen)

    def _ensure_connection_between(self, gx, gy, direction):
        nx, ny = gx, gy
        opp = None
        if direction == "up":
            ny -= 1
            opp = "down"
        elif direction == "down":
            ny += 1
            opp = "up"
        elif direction == "left":
            nx -= 1
            opp = "right"
        elif direction == "right":
            nx += 1
            opp = "left"
        if not self._in_bounds(nx, ny):
            return False
        r = self._create_room_at(gx, gy)
        nr = self._create_room_at(nx, ny)
        exists = True if random.random() < 0.7 else False
        r.ensure_connection(direction, exists)
        nr.ensure_connection(opp, exists)
        return exists

    def discover_neighbors_randomly(self, gx, gy):
        base = self.grid.get((gx, gy))
        if not base:
            return
        for direction in ["up", "down", "left", "right"]:
            if base.connections[direction]:
                continue
            if random.random() < 0.55:
                self._ensure_connection_between(gx, gy, direction)

    def enter_room(self, gx, gy, via=None):
        if not self._in_bounds(gx, gy):
            return False
        if (gx, gy) not in self.grid:
            self._create_room_at(gx, gy)
        room = self.grid[(gx, gy)]
        self.discover_neighbors_randomly(gx, gy)
        self.curr = room
        self.curr_pos = (gx, gy)

        # generate room contents now (first enter)
        room.generate_contents(player.rect)

        # place player depending on via
        if via == "up":
            player.teleport_to(WIDTH//2, HEIGHT - Room.PADDING - 30)
        elif via == "down":
            player.teleport_to(WIDTH//2, Room.PADDING + 30)
        elif via == "left":
            player.teleport_to(WIDTH - Room.PADDING - 30, HEIGHT//2)
        elif via == "right":
            player.teleport_to(Room.PADDING + 30, HEIGHT//2)
        else:
            player.teleport_to(WIDTH//2, HEIGHT//2)

        # close doors until cleared (if door exists)
        for d in room.doors.values():
            if d:
                d.close()
                if hasattr(d, "block") and d.block not in room.walls:
                    room.walls.add(d.block)

        # check cleared immediately if no enemies generated
        room.check_cleared()
        room.open_doors_if_cleared()
        return True

    def try_move_through_door(self, direction):
        gx, gy = self.curr_pos
        if direction not in self.curr.connections or not self.curr.connections[direction]:
            return False
        d = self.curr.doors[direction]
        if not d or not d.is_open:
            return False
        nx, ny = gx, gy
        if direction == "up":
            ny -= 1; opp = "down"
        elif direction == "down":
            ny += 1; opp = "up"
        elif direction == "left":
            nx -= 1; opp = "right"
        elif direction == "right":
            nx += 1; opp = "left"
        if not self._in_bounds(nx, ny):
            return False
        neighbor = self._create_room_at(nx, ny)
        if not neighbor.connections.get(opp):
            neighbor.ensure_connection(opp, True)
        self.enter_room(nx, ny, via=opp)
        return True

# --- Initialize player and manager ---
player = Player(WIDTH // 2, HEIGHT // 2)
player_group = pygame.sprite.GroupSingle(player)

room_manager = RoomManager(size=GRID_SIZE, start_cell=START_CELL)
current_room = room_manager.curr

# Global convenience groups for drawing
projectile_group = pygame.sprite.Group()
enemy_projectiles = pygame.sprite.Group()
particle_group = pygame.sprite.Group()

# Score + state
score = 0
paused = False
game_over = False

# Helper
def spawn_powerup_near_center_in_room(room, min_distance_from_player=150):
    for _ in range(200):
        x = random.randint(120, WIDTH - 120)
        y = random.randint(120, HEIGHT - 120)
        dist = ((x - player.rect.centerx) ** 2 + (y - player.rect.centery) ** 2) ** 0.5
        if dist > min_distance_from_player:
            pu = PowerUp(x, y)
            room.powerups.add(pu)
            return
    pu = PowerUp(WIDTH // 2, HEIGHT // 2)
    room.powerups.add(pu)

# --- Main Loop ---
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE and not game_over:
                paused = not paused

            if game_over and event.key == pygame.K_r:
                score = 0
                game_over = False
                player.health = player.PLAYER_MAX_HEALTH
                player.multi_shot_level = 1
                player.speed_level = 0
                player.rapid_level = 0
                player.piercing_level = 0
                player.explosive_level = 0
                player.last_shot_time = 0
                room_manager = RoomManager(size=GRID_SIZE, start_cell=START_CELL)
                current_room = room_manager.curr
                player.teleport_to(WIDTH//2, HEIGHT//2)

    if not paused and not game_over:
        keys = pygame.key.get_pressed()

        # Shooting
        if player.can_attack():
            direction = None
            if keys[pygame.K_UP]:
                direction = "up"
            elif keys[pygame.K_DOWN]:
                direction = "down"
            elif keys[pygame.K_LEFT]:
                direction = "left"
            elif keys[pygame.K_RIGHT]:
                direction = "right"

            if direction:
                pellets = player.attack(direction)
                for p in pellets:
                    current_room.projectiles.add(p)
                    projectile_group.add(p)

        # Movement
        player_group.update(current_room.walls, keys)

        # Door transition check — instant teleport when player overlaps threshold near edge and door open
        for dir_name, door in current_room.doors.items():
            if door and door.is_open:
                if dir_name == "up" and player.rect.centery <= Room.PADDING // 2:
                    if room_manager.try_move_through_door("up"):
                        current_room = room_manager.curr
                        break
                if dir_name == "down" and player.rect.centery >= HEIGHT - Room.PADDING // 2:
                    if room_manager.try_move_through_door("down"):
                        current_room = room_manager.curr
                        break
                if dir_name == "left" and player.rect.centerx <= Room.PADDING // 2:
                    if room_manager.try_move_through_door("left"):
                        current_room = room_manager.curr
                        break
                if dir_name == "right" and player.rect.centerx >= WIDTH - Room.PADDING // 2:
                    if room_manager.try_move_through_door("right"):
                        current_room = room_manager.curr
                        break

        # Update projectiles and groups (room-local)
        current_room.projectiles.update(current_room.walls)
        projectile_group.update(current_room.walls)
        current_room.enemy_projectiles.update(current_room.walls)
        enemy_projectiles.update(current_room.walls)
        current_room.particles.update()
        particle_group.update()
        current_room.powerups.update()

        # Events
        current_room.update_events()

        # Enemies
        for enemy in list(current_room.enemies):
            result = enemy.update(player)
            if isinstance(result, pygame.sprite.Sprite):
                current_room.enemy_projectiles.add(result)
                enemy_projectiles.add(result)

        # Collisions: player <-> enemies
        for enemy in list(current_room.enemies):
            if player.rect.colliderect(enemy.rect):
                if player.health > 0:
                    player.health -= 1
                dx = player.rect.centerx - enemy.rect.centerx
                dy = player.rect.centery - enemy.rect.centery
                dist = max(1.0, (dx ** 2 + dy ** 2) ** 0.5)
                player.pos_x += 20 * dx / dist
                player.pos_y += 20 * dy / dist
                player.rect.centerx = int(player.pos_x)
                player.rect.centery = int(player.pos_y)

        # Projectile hits enemies
        for proj in list(current_room.projectiles):
            hits = pygame.sprite.spritecollide(proj, current_room.enemies, False)
            if hits:
                if getattr(proj, "explosive", 0) and proj.explosive > 0:
                    base_radius = 50
                    radius = base_radius + 20 * proj.explosive
                    cx, cy = proj.rect.center
                    for enemy in list(current_room.enemies):
                        ex, ey = enemy.rect.center
                        if ((ex - cx) ** 2 + (ey - cy) ** 2) ** 0.5 <= radius:
                            died = False
                            for _ in range(1 + proj.explosive):
                                if enemy.take_hit():
                                    died = True
                                    break
                            if died:
                                enemy.kill()
                                score += 1
                                for _ in range(8):
                                    current_room.particles.add(Particle(enemy.rect.centerx, enemy.rect.centery))
                                    particle_group.add(Particle(enemy.rect.centerx, enemy.rect.centery))
                    for _ in range(20 + 6 * proj.explosive):
                        current_room.particles.add(Particle(cx, cy, color=(255, 180, 50)))
                        particle_group.add(Particle(cx, cy, color=(255, 180, 50)))
                    proj.kill()
                    continue

                for enemy in hits:
                    if getattr(proj, "hits_left", 1) > 0:
                        if enemy.take_hit():
                            enemy.kill()
                            score += 1
                            for _ in range(6):
                                current_room.particles.add(Particle(enemy.rect.centerx, enemy.rect.centery))
                                particle_group.add(Particle(enemy.rect.centerx, enemy.rect.centery))
                        proj.hits_left -= 1
                    if proj.hits_left <= 0:
                        proj.kill()
                        break

        # Enemy projectiles hit player
        for ep in list(current_room.enemy_projectiles):
            if player.rect.colliderect(ep.rect):
                ep.kill()
                if player.health > 0:
                    player.health -= 1

        # Power-up pickup
        collected = pygame.sprite.spritecollide(player, current_room.powerups, True)
        for pu in collected:
            if pu.type == "health":
                player.health = min(player.PLAYER_MAX_HEALTH, player.health + 2)
            elif pu.type == "multi":
                player.multi_shot_level = max(1, int(player.multi_shot_level * 3))
            elif pu.type == "speed":
                player.speed_level += 1
            elif pu.type == "rapid":
                player.rapid_level += 1
            elif pu.type == "pierce":
                player.piercing_level += 1
            elif pu.type == "explosive":
                player.explosive_level += 1

        # Check cleared
        current_room.check_cleared()

        # spawn a small chance powerup after clearing
        if current_room.cleared and random.random() < 0.01:
            spawn_powerup_near_center_in_room(current_room)

        # player death
        if player.health <= 0:
            game_over = True

    # --- Drawing ---
    screen.fill(Grey)

    # draw floor texture for current room
    current_room.draw_floor(screen)

    # draw walls
    current_room.walls.draw(screen)

    # draw doors
    current_room.draw_doors(screen)

    # draw groups
    current_room.enemies.draw(screen)
    current_room.projectiles.draw(screen)
    projectile_group.draw(screen)
    current_room.enemy_projectiles.draw(screen)
    enemy_projectiles.draw(screen)
    current_room.particles.draw(screen)
    particle_group.draw(screen)
    current_room.powerups.draw(screen)

    # draw player
    player_group.draw(screen)

    # HUD / bars
    bar_x, bar_y = 10, 10
    bar_width, bar_height = 150, 20
    pygame.draw.rect(screen, HEALTH_BAR_BG_COLOR, (bar_x, bar_y, bar_width, bar_height))
    health_width = int(bar_width * (player.health / player.PLAYER_MAX_HEALTH))
    pygame.draw.rect(screen, HEALTH_BAR_COLOR, (bar_x, bar_y, health_width, bar_height))

    score_text = font.render(f"Score: {score}", True, (0, 0, 0))
    room_text = font.render(f"Room: {room_manager.curr_pos[0]},{room_manager.curr_pos[1]}", True, (0, 0, 0))
    hp_text = font.render(f"HP: {player.health}", True, (0, 0, 0))
    screen.blit(score_text, (10, 40))
    screen.blit(room_text, (10, 70))
    screen.blit(hp_text, (10, 100))

    hud_font = pygame.font.SysFont(None, 24)
    y_offset = 130
    hud_lines = [
        f"Multishot: {player.multi_shot_level}",
        f"Speed: {player.speed_level}",
        f"Rapid: {player.rapid_level}",
        f"Piercing: {player.piercing_level}",
        f"Explosive: {player.explosive_level}"
    ]
    for line in hud_lines:
        text_surf = hud_font.render(line, True, (255, 255, 255))
        screen.blit(text_surf, (10, y_offset))
        y_offset += 20

    if paused and not game_over:
        pause_text = pause_font.render("PAUSED", True, WHITE)
        rect = pause_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        screen.blit(pause_text, rect)

    if game_over:
        over_text = pause_font.render("GAME OVER", True, (255, 0, 0))
        rect = over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40))
        screen.blit(over_text, rect)
        instr_text = font.render("Press R to Restart", True, WHITE)
        rect2 = instr_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20))
        screen.blit(instr_text, rect2)

    pygame.display.flip()
    clock.tick(FPS)
