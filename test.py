import pygame
import sys
import random
from player import Player, Projectile, Enemy, ShooterEnemy, JumperEnemy, EnemyProjectile, Particle

# --- Settings ---
WIDTH, HEIGHT = 800, 600
FPS = 60

# --- Colors ---
GREY = (146, 142, 133)
DARK_GREY = (59, 59, 59)
HEALTH_BAR_COLOR = (255, 0, 0)
HEALTH_BAR_BG_COLOR = (100, 0, 0)
WHITE = (255, 255, 255)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dungeon Shooter")
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 36)
pause_font = pygame.font.SysFont(None, 72)

# --- Difficulty Scaling ---
ROOMS_CLEARED_TOTAL = 0
DIFFICULTY_LEVEL = 1
BASE_ENEMIES = 3
ENEMY_HEALTH_SCALE = 1.2


# --- Wall Class ---
class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__()
        self.image = pygame.Surface((w, h))
        self.image.fill(DARK_GREY)
        self.rect = self.image.get_rect(topleft=(x, y))


# --- PowerUp ---
class PowerUp(pygame.sprite.Sprite):
    TYPES = ["health", "multi", "speed", "rapid", "pierce", "explosive"]

    def __init__(self, x, y, kind=None):
        super().__init__()
        self.type = kind if kind else random.choice(PowerUp.TYPES)
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
        self.timer = 20 * FPS

    def update(self):
        self.timer -= 1
        if self.timer <= 0:
            self.kill()


# --- Enemy Spawning ---
def spawn_enemy_type():
    r = random.random()
    if r < 0.6:
        return Enemy
    elif r < 0.85:
        return ShooterEnemy
    else:
        return JumperEnemy


def spawn_enemy_far_from_player(player):
    for _ in range(200):
        x = random.randint(150, WIDTH - 150)
        y = random.randint(150, HEIGHT - 150)
        dist = ((x - player.rect.centerx) ** 2 + (y - player.rect.centery) ** 2) ** 0.5
        if dist > 200:
            return spawn_enemy_type()(x, y)
    return spawn_enemy_type()(150, 150)


# --- Room ---
class Room:
    def __init__(self, x, y):
        self.coords = (x, y)
        self.enemies = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.enemy_projectiles = pygame.sprite.Group()
        self.events = []
        self.walls = pygame.sprite.Group()
        self.door_walls = pygame.sprite.Group()  # Group for the door blocks
        self.cleared = False
        self.doors_locked = True
        self.create_walls_with_doors()

    def create_walls_with_doors(self):
        """
        Creates four full outer walls with a central gap, and uses a thin block
        to fill the gap when the door is locked.
        """
        wall_thickness = 40
        door_width = 100
        # NEW: Thin thickness for the temporary door barrier
        door_block_thickness = 8

        # Calculate the center position of the door blocks for a clean look
        center_thickness = wall_thickness // 2
        door_y_offset = center_thickness - door_block_thickness // 2
        door_x_offset = center_thickness - door_block_thickness // 2

        # --- Create Top Wall (and its door segment) ---
        # Top Wall (main segments)
        self.walls.add(Wall(0, 0, WIDTH // 2 - door_width // 2, wall_thickness))
        self.walls.add(Wall(WIDTH // 2 + door_width // 2, 0, WIDTH // 2 - door_width // 2, wall_thickness))
        # Door block: Thin, spans the gap
        top_door_block = Wall(WIDTH // 2 - door_width // 2, 0, door_width, door_block_thickness+15)
        self.walls.add(top_door_block)
        self.door_walls.add(top_door_block)

        # --- Create Bottom Wall (and its door segment) ---
        # Bottom Wall (main segments)
        self.walls.add(Wall(0, HEIGHT - wall_thickness, WIDTH // 2 - door_width // 2, wall_thickness))
        self.walls.add(
            Wall(WIDTH // 2 + door_width // 2, HEIGHT - wall_thickness, WIDTH // 2 - door_width // 2, wall_thickness))
        # Door block: Thin, spans the gap
        bottom_door_block = Wall(WIDTH // 2 - door_width // 2, HEIGHT - wall_thickness + door_y_offset, door_width,
                                 door_block_thickness + 20)
        self.walls.add(bottom_door_block)
        self.door_walls.add(bottom_door_block)

        # --- Create Left Wall (and its door segment) ---
        # Left Wall (main segments)
        self.walls.add(Wall(0, 0, wall_thickness, HEIGHT // 2 - door_width // 2))
        self.walls.add(Wall(0, HEIGHT // 2 + door_width // 2, wall_thickness, HEIGHT // 2 - door_width // 2))
        # Door block: Thin, spans the gap
        left_door_block = Wall(door_x_offset-15, HEIGHT // 2 - door_width // 2 , door_block_thickness+15, door_width)
        self.walls.add(left_door_block)
        self.door_walls.add(left_door_block)

        # --- Create Right Wall (and its door segment) ---
        # Right Wall (main segments)
        self.walls.add(Wall(WIDTH - wall_thickness, 0, wall_thickness, HEIGHT // 2 - door_width // 2))
        self.walls.add(
            Wall(WIDTH - wall_thickness, HEIGHT // 2 + door_width // 2, wall_thickness, HEIGHT // 2 - door_width // 2))
        # Door block: Thin, spans the gap
        right_door_block = Wall(WIDTH - wall_thickness + door_x_offset, HEIGHT // 2 - door_width // 2,
                                door_block_thickness + 15, door_width)
        self.walls.add(right_door_block)
        self.door_walls.add(right_door_block)

    def spawn_enemies(self, player):
        num_enemies = int(BASE_ENEMIES + DIFFICULTY_LEVEL * 0.5)

        for _ in range(random.randint(num_enemies, num_enemies + 2)):
            e = spawn_enemy_far_from_player(player)
            # Scale enemy health
            e.max_health = int(e.max_health * (ENEMY_HEALTH_SCALE ** (DIFFICULTY_LEVEL - 1)))
            e.health = e.max_health
            self.enemies.add(e)

    def unlock_doors(self):
        # REQUIRED to modify top-level variables
        global ROOMS_CLEARED_TOTAL, DIFFICULTY_LEVEL

        # Remove all door blocks, opening the path
        for wall in list(self.door_walls):
            wall.kill()  # Removes the wall sprite from ALL groups it belongs to (self.walls and self.door_walls)

        self.doors_locked = False

        # Increase cleared room count and scale difficulty
        ROOMS_CLEARED_TOTAL += 1
        DIFFICULTY_LEVEL = (ROOMS_CLEARED_TOTAL // 3) + 1

    def update(self, player, particle_group, projectile_group):
        # enemy AI
        for enemy in list(self.enemies):
            result = enemy.update(player)
            if isinstance(result, pygame.sprite.Sprite):
                self.enemy_projectiles.add(result)

        # check clear
        if not self.cleared and not self.enemies:
            self.cleared = True
            self.unlock_doors()
            # drop powerup chance
            if random.random() < 0.5:
                self.powerups.add(PowerUp(WIDTH // 2, HEIGHT // 2))


# --- Dungeon ---
class Dungeon:
    def __init__(self):
        self.rooms = {}
        self.current = (0, 0)
        self.load_room(0, 0)

    def load_room(self, x, y):
        if (x, y) not in self.rooms:
            room = Room(x, y)
            room.spawn_enemies(player)
            self.rooms[(x, y)] = room
        self.current = (x, y)

    def get_room(self):
        return self.rooms[self.current]

    def move(self, direction):
        x, y = self.current
        if direction == "up":
            y -= 1
        elif direction == "down":
            y += 1
        elif direction == "left":
            x -= 1
        elif direction == "right":
            x += 1
        self.load_room(x, y)


# --- Transition Check ---
def check_room_transition(player, dungeon):
    margin = 10
    px, py = player.rect.center

    # Check only if doors are unlocked, relying on wall collision otherwise
    if dungeon.get_room().doors_locked:
        return

    if py < margin:  # top
        dungeon.move("up")
        player.pos_y = HEIGHT - 100
    elif py > HEIGHT - margin:
        dungeon.move("down")
        player.pos_y = 100
    elif px < margin:
        dungeon.move("left")
        player.pos_x = WIDTH - 120
    elif px > WIDTH - margin:
        dungeon.move("right")
        player.pos_x = 120

    player.rect.centerx = int(player.pos_x)
    player.rect.centery = int(player.pos_y)


# --- Create Player and Groups ---
player = Player(WIDTH // 2, HEIGHT // 2)
PLAYER_MAX_HEALTH = player.PLAYER_MAX_HEALTH  # For clean HUD access
player_group = pygame.sprite.GroupSingle(player)
projectile_group = pygame.sprite.Group()
particle_group = pygame.sprite.Group()

dungeon = Dungeon()

score = 0
paused = False
game_over = False

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
                # Reset Global Variables on Restart
                # The 'global' keyword is omitted here because we are in the top-level script scope.

                ROOMS_CLEARED_TOTAL = 0
                DIFFICULTY_LEVEL = 1

                dungeon = Dungeon()
                player.health = PLAYER_MAX_HEALTH
                player.multi_shot_level = 1
                player.speed_level = 0
                player.rapid_level = 0
                player.piercing_level = 0
                player.explosive_level = 0
                player.last_shot_time = 0
                projectile_group.empty()
                particle_group.empty()
                player.pos_x, player.pos_y = WIDTH // 2, HEIGHT // 2
                player.rect.center = (WIDTH // 2, HEIGHT // 2)
                score = 0
                game_over = False

    if not paused and not game_over:
        keys = pygame.key.get_pressed()

        # Player shooting
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
                for p in player.attack(direction):
                    projectile_group.add(p)

        room = dungeon.get_room()
        player_group.update(room.walls, keys)
        projectile_group.update(room.walls)
        particle_group.update()
        room.powerups.update()
        room.enemy_projectiles.update(room.walls)

        room.update(player, particle_group, projectile_group)
        check_room_transition(player, dungeon)

        # Enemy collisions
        for enemy in list(room.enemies):
            if player.rect.colliderect(enemy.rect):
                player.health -= 1
                dx = player.rect.centerx - enemy.rect.centerx
                dy = player.rect.centery - enemy.rect.centery
                dist = max(1, (dx ** 2 + dy ** 2) ** 0.5)
                player.pos_x += 20 * dx / dist
                player.pos_y += 20 * dy / dist

        # Projectile hits
        for proj in list(projectile_group):
            hits = pygame.sprite.spritecollide(proj, room.enemies, False)
            if hits:
                if getattr(proj, "explosive", 0) > 0:
                    cx, cy = proj.rect.center
                    radius = 50 + proj.explosive * 20
                    for enemy in list(room.enemies):
                        ex, ey = enemy.rect.center
                        if ((ex - cx) ** 2 + (ey - cy) ** 2) ** 0.5 <= radius:
                            for _ in range(1 + proj.explosive):
                                if enemy.take_hit():
                                    enemy.kill()
                                    score += 1
                                    for _ in range(6):
                                        particle_group.add(Particle(ex, ey))
                    proj.kill()
                else:
                    for enemy in hits:
                        if proj.hits_left > 0:
                            if enemy.take_hit():
                                enemy.kill()
                                score += 1
                                for _ in range(6):
                                    particle_group.add(Particle(enemy.rect.centerx, enemy.rect.centery))
                            proj.hits_left -= 1
                        if proj.hits_left <= 0:
                            proj.kill()
                            break

        # Enemy projectiles
        for ep in list(room.enemy_projectiles):
            if player.rect.colliderect(ep.rect):
                ep.kill()
                player.health -= 1

        # Powerups
        collected = pygame.sprite.spritecollide(player, room.powerups, True)
        for pu in collected:
            if pu.type == "health":
                player.health = min(PLAYER_MAX_HEALTH, player.health + 2)
            elif pu.type == "multi":
                player.multi_shot_level *= 3
            elif pu.type == "speed":
                player.speed_level += 1
            elif pu.type == "rapid":
                player.rapid_level += 1
            elif pu.type == "pierce":
                player.piercing_level += 1
            elif pu.type == "explosive":
                player.explosive_level += 1

        if player.health <= 0:
            game_over = True

    # --- Draw ---
    screen.fill(GREY)
    room = dungeon.get_room()
    room.walls.draw(screen)
    player_group.draw(screen)
    projectile_group.draw(screen)
    room.enemies.draw(screen)

    # Draw enemy health bars (Fixed to safely iterate over the group's current sprites)
    for enemy in room.enemies.sprites():
        enemy.draw_health_bar(screen)

    room.enemy_projectiles.draw(screen)
    particle_group.draw(screen)
    room.powerups.draw(screen)

    # HUD
    pygame.draw.rect(screen, HEALTH_BAR_BG_COLOR, (10, 10, 150, 20))
    health_width = int(150 * (player.health / PLAYER_MAX_HEALTH))
    pygame.draw.rect(screen, HEALTH_BAR_COLOR, (10, 10, health_width, 20))

    score_text = font.render(f"Score: {score}", True, (0, 0, 0))
    room_text = font.render(f"Room: {room.coords}", True, (0, 0, 0))
    difficulty_text = font.render(f"Level: {DIFFICULTY_LEVEL}", True, (0, 0, 0))
    screen.blit(score_text, (10, 40))
    screen.blit(room_text, (10, 70))
    screen.blit(difficulty_text, (10, 100))

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

    # Powerup stats
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

    pygame.display.flip()
    clock.tick(FPS)