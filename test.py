import pygame
import sys
import random

# Import the new BossEnemy class
from player import Player, Projectile, Enemy, ShooterEnemy, JumperEnemy, EnemyProjectile, Particle, AirstrikeEvent, \
    BossEnemy

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
ROOMS_CLEARED_TOTAL = 0  # Global Variable
DIFFICULTY_LEVEL = 1  # Global Variable
BASE_ENEMIES = 3
ENEMY_HEALTH_SCALE = 1.2
BOSS_INTERVAL = 2  # Rooms cleared before a boss appears (for quick testing)


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
        self.is_boss_room = False
        self.create_walls_with_doors()

    def create_walls_with_doors(self):
        """
        Creates outer walls and door blocks to seal the room.
        Door blocks are now guaranteed to meet the permanent walls.
        """
        wall_thickness = 40
        door_width = 100
        door_block_thickness = 10
        door_start_h = WIDTH // 2 - door_width // 2
        door_end_h = WIDTH // 2 + door_width // 2
        door_start_v = HEIGHT // 2 - door_width // 2
        door_end_v = HEIGHT // 2 + door_width // 2

        # --- Permanent Base Walls (creating the door gap) ---
        self.walls.add(Wall(0, 0, door_start_h, wall_thickness))
        self.walls.add(Wall(door_end_h, 0, WIDTH - door_end_h, wall_thickness))
        self.walls.add(Wall(0, HEIGHT - wall_thickness, door_start_h, wall_thickness))
        self.walls.add(Wall(door_end_h, HEIGHT - wall_thickness, WIDTH - door_end_h, wall_thickness))
        self.walls.add(Wall(0, 0, wall_thickness, door_start_v))
        self.walls.add(Wall(0, door_end_v, wall_thickness, HEIGHT - door_end_v))
        self.walls.add(Wall(WIDTH - wall_thickness, 0, wall_thickness, door_start_v))
        self.walls.add(Wall(WIDTH - wall_thickness, door_end_v, wall_thickness, HEIGHT - door_end_v))

        # --- Door Blocks (Fill the gap when locked) ---
        top_block = Wall(door_start_h, 0, door_width, door_block_thickness)
        self.walls.add(top_block)
        self.door_walls.add(top_block)
        bottom_block = Wall(door_start_h, HEIGHT - door_block_thickness, door_width, door_block_thickness)
        self.walls.add(bottom_block)
        self.door_walls.add(bottom_block)
        left_block = Wall(0, door_start_v, door_block_thickness, door_width)
        self.walls.add(left_block)
        self.door_walls.add(left_block)
        right_block = Wall(WIDTH - door_block_thickness, door_start_v, door_block_thickness, door_width)
        self.walls.add(right_block)
        self.door_walls.add(right_block)

    def spawn_enemies(self, player):
        # Determine if this room should spawn a boss
        if ROOMS_CLEARED_TOTAL > 0 and (ROOMS_CLEARED_TOTAL + 1) % BOSS_INTERVAL == 0:
            self.is_boss_room = True

            # Spawn a single boss in the center
            boss = BossEnemy(WIDTH // 2, HEIGHT // 2, DIFFICULTY_LEVEL)
            self.enemies.add(boss)
            print(f"BOSS SPAWNED: Health {boss.max_health}")
        else:
            # Spawn regular enemies
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
            wall.kill()

        self.doors_locked = False

        # Increase cleared room count and scale difficulty
        ROOMS_CLEARED_TOTAL += 1
        DIFFICULTY_LEVEL = (ROOMS_CLEARED_TOTAL // 3) + 1

    def update(self, player, particle_group, projectile_group):
        # events (like airstrike)
        for event in list(self.events):
            event.update(screen, player, self.enemies, particle_group)
            if not event.active:
                self.events.remove(event)

        # enemy AI
        for enemy in list(self.enemies):
            result = enemy.update(player)
            if result is not None:
                if isinstance(result, pygame.sprite.Sprite):
                    self.enemy_projectiles.add(result)
                elif isinstance(result, list):
                    # Handle multiple projectiles from BossEnemy
                    self.enemy_projectiles.add(*result)

        # check clear
        if not self.cleared and not self.enemies:
            self.cleared = True
            self.unlock_doors()
            # drop powerup chance
            if random.random() < 0.75 or self.is_boss_room:
                self.powerups.add(PowerUp(WIDTH // 2, HEIGHT // 2))

            # If it was a boss room, drop an extra guaranteed powerup
            if self.is_boss_room:
                self.powerups.add(PowerUp(WIDTH // 2 + 50, HEIGHT // 2 + 50))

            # Chance to trigger an Airstrike
            if random.random() < 0.2:
                airstrike = AirstrikeEvent(
                    WIDTH, HEIGHT,
                    player.rect.centerx,
                    player.rect.centery,
                    pygame
                )
                self.events.append(airstrike)


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
PLAYER_MAX_HEALTH = player.PLAYER_MAX_HEALTH
player_group = pygame.sprite.GroupSingle(player)
projectile_group = pygame.sprite.Group()
particle_group = pygame.sprite.Group() #

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
                # --- Restart Logic ---
                ROOMS_CLEARED_TOTAL, DIFFICULTY_LEVEL

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
                player.invul_timer = 0
                projectile_group.empty()
                particle_group.empty()
                player.pos_x, player.pos_y = WIDTH // 2, HEIGHT // 2
                player.rect.center = (WIDTH // 2, HEIGHT // 2)
                score = 0
                game_over = False
                # -------------------------

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

        # Enemy collisions (now uses player.take_damage for i-frames/knockback)
        for enemy in list(room.enemies):
            if player.rect.colliderect(enemy.rect):
                player.take_damage(enemy.rect.centerx, enemy.rect.centery)

        # Projectile hits (unchanged - applies damage to enemies)
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

        # Enemy projectiles (now uses player.take_damage for i-frames/knockback)
        for ep in list(room.enemy_projectiles):
            if player.rect.colliderect(ep.rect):
                ep.kill()
                player.take_damage(ep.rect.centerx, ep.rect.centery)

        # Powerups
        collected = pygame.sprite.spritecollide(player, room.powerups, True)
        for pu in collected:
            if pu.type == "health":
                player.health = min(PLAYER_MAX_HEALTH, player.health + 2)
            elif pu.type == "multi":
                if player.multi_shot_level == 1:
                    player.multi_shot_level = 3
                else:
                    player.multi_shot_level += 2
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

    # Player is drawn via player_group.draw(screen) below

    projectile_group.draw(screen)
    room.enemies.draw(screen)

    for enemy in room.enemies.sprites():
        enemy.draw_health_bar(screen)

    room.enemy_projectiles.draw(screen)
    particle_group.draw(screen)
    room.powerups.draw(screen)

    # Draw player (handles flashing logic inside Player.update)
    player_group.draw(screen)

    # Draw Airstrike Events
    for event in room.events:
        event.update(screen, player, room.enemies, particle_group)

    # HUD
    pygame.draw.rect(screen, HEALTH_BAR_BG_COLOR, (10, 10, 150, 20))
    health_width = int(150 * (player.health / PLAYER_MAX_HEALTH))
    pygame.draw.rect(screen, HEALTH_BAR_COLOR, (10, 10, health_width, 20))

    score_text = font.render(f"Score: {score}", True, (0, 0, 0))
    room_text = font.render(f"Room: {room.coords}", True, (0, 0, 0))
    difficulty_text = font.render(f"Level: {DIFFICULTY_LEVEL}", True, (0, 0, 0))

    # Boss health warning
    if room.is_boss_room and room.enemies:
        boss = room.enemies.sprites()[0]
        boss_health_text = font.render(f"BOSS HP: {boss.health}/{boss.max_health}", True, (255, 0, 0))
        screen.blit(boss_health_text, (WIDTH - boss_health_text.get_width() - 10, 10))

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
        f"Damage: {player.piercing_level}",
        f"Explosive: {player.explosive_level}"
    ]
    for line in hud_lines:
        text_surf = hud_font.render(line, True, (255, 255, 255))
        screen.blit(text_surf, (10, y_offset))
        y_offset += 20

    pygame.display.flip()
    clock.tick(FPS)