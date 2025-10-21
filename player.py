import pygame
import math
import random

pygame.init()
# --- Constants ---
PLAYER_SPEED = 4
PLAYER_RADIUS = 20

PROJECTILE_SPEED = 8
SHOOT_COOLDOWN = 300  # ms

ENEMY_SIZE = 30
ENEMY_COLOR = (255, 0, 0)
ENEMY_SPEED = 2

# --- Colors ---
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
STUCK_ARROW_COLOR = (180, 180, 60)


class Player(pygame.sprite.Sprite):
    PLAYER_MAX_HEALTH = 5

    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((PLAYER_RADIUS * 2, PLAYER_RADIUS * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, BLUE, (PLAYER_RADIUS, PLAYER_RADIUS), PLAYER_RADIUS)
        self.rect = self.image.get_rect(center=(x, y))

        # floating pos for smooth movement of any sub-pixels
        self.pos_x = float(self.rect.centerx)
        self.pos_y = float(self.rect.centery)

        self.last_shot_time = 0
        self.health = self.PLAYER_MAX_HEALTH

        # MULTISHOT: pellet count; start at 1 (single pellet)
        self.multi_shot_level = 1

        # New stacked power-up levels (integers)
        self.speed_level = 0  # +1 movement speed per stack
        self.rapid_level = 0  # each stack multiplies cooldown by 0.8
        self.piercing_level = 0  # +1 extra enemy hit per stack
        self.explosive_level = 0  # explosive radius/damage per stack

    def update(self, walls, keys):
        dx, dy = 0, 0
        spd = PLAYER_SPEED + self.speed_level
        if keys[pygame.K_w]:
            dy = -spd
        if keys[pygame.K_s]:
            dy = spd
        if keys[pygame.K_a]:
            dx = -spd
        if keys[pygame.K_d]:
            dx = spd

        # move and collide with walls
        self.pos_x += dx
        self.rect.centerx = int(self.pos_x)
        if pygame.sprite.spritecollide(self, walls, False):
            self.pos_x -= dx
            self.rect.centerx = int(self.pos_x)

        self.pos_y += dy
        self.rect.centery = int(self.pos_y)
        if pygame.sprite.spritecollide(self, walls, False):
            self.pos_y -= dy
            self.rect.centery = int(self.pos_y)

    def can_attack(self):
        # cooldown reduced multiplicatively by rapid_level stacks
        cooldown = SHOOT_COOLDOWN * (0.8 ** self.rapid_level) if self.rapid_level > 0 else SHOOT_COOLDOWN
        cooldown = max(50, int(cooldown))
        return pygame.time.get_ticks() - self.last_shot_time > cooldown

    def attack(self, direction):
        """
        Returns a list of Projectile objects.
        direction: 'up','down','left','right'
        multi_shot_level stores the pellet count (1, 3, 5, 7, ...).
        """
        self.last_shot_time = pygame.time.get_ticks()

        if direction == "up":
            base_angle = -90.0
        elif direction == "down":
            base_angle = 90.0
        elif direction == "left":
            base_angle = 180.0
        else:
            base_angle = 0.0

        num_shots = int(self.multi_shot_level)
        projectiles = []
        cone_degrees = 30 + (self.multi_shot_level * 5)  # tight shotgun cone

        if num_shots <= 1:
            projectiles.append(Projectile(
                self.rect.centerx, self.rect.centery, base_angle,
                piercing=self.piercing_level, explosive=self.explosive_level
            ))
        else:
            start = base_angle - (cone_degrees / 2.0)
            step = cone_degrees / (num_shots - 1) if num_shots > 1 else 0
            for i in range(num_shots):
                angle = start + step * i
                projectiles.append(Projectile(
                    self.rect.centerx, self.rect.centery, angle,
                    piercing=self.piercing_level, explosive=self.explosive_level
                ))

        return projectiles


class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, angle_degrees, piercing=0, explosive=0):
        super().__init__()
        self.piercing = piercing
        self.explosive = explosive
        # hits_left: how many enemies it can damage before disappearing
        self.hits_left = max(1, piercing + 1)

        # Make explosive bolts visually bigger and chunkier depending on explosive level
        base_w = 14 + 4 * explosive
        base_h = 4 + 2 * explosive
        base = pygame.Surface((base_w, base_h), pygame.SRCALPHA)
        # explosive-looking tint if explosive > 0
        if explosive > 0:
            tint = (255, 180, 60)
            pygame.draw.rect(base, tint, (0, 0, base_w, base_h))
        else:
            pygame.draw.rect(base, YELLOW, (0, 0, base_w, base_h))
        self.image = pygame.transform.rotate(base, -angle_degrees)
        self.rect = self.image.get_rect(center=(x, y))

        self.pos_x = float(self.rect.centerx)
        self.pos_y = float(self.rect.centery)

        rad = math.radians(angle_degrees)
        self.dx = PROJECTILE_SPEED * math.cos(rad)
        self.dy = PROJECTILE_SPEED * math.sin(rad)

        self.age = 0
        self.fly_time = 45  # explosive bolts fly a bit longer

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


# --- Enemies ---
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((ENEMY_SIZE, ENEMY_SIZE))
        self.original_color = ENEMY_COLOR
        self.flash_color = (255, 255, 0)
        self.image.fill(self.original_color)
        self.rect = self.image.get_rect(center=(x, y))

        self.max_health = 2
        self.health = self.max_health
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

    def draw_health_bar(self, screen):
        # Health bar dimensions and position
        bar_width = self.rect.width
        bar_height = 5
        bar_x = self.rect.x
        bar_y = self.rect.y - 10

        # Background (empty health)
        pygame.draw.rect(screen, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))

        # Current health
        health_ratio = self.health / self.max_health
        current_width = int(bar_width * health_ratio)
        pygame.draw.rect(screen, (0, 255, 0), (bar_x, bar_y, current_width, bar_height))


class GameEvent:
    """Base class for time-limited game events."""

    def __init__(self):
        self.active = True

    def update(self, screen, player, enemy_group, particle_group):
        raise NotImplementedError("Must be implemented by subclass")


class AirstrikeEvent(GameEvent):
    # Takes pygame as an argument for image loading (passed from test.py)
    def __init__(self, width, height, player_x, player_y, pygame_instance, duration=180):
        super().__init__()
        self.width = width
        self.height = height
        self.duration = duration  # total frames
        self.frame = 0

        # --- AIRSTRIKE FLIGHT PATH LOGIC ---
        # Fixed diagonal path (Top-Left to Bottom-Right)
        self.dx = 1.0
        self.dy = 0.5
        magnitude = math.sqrt(self.dx ** 2 + self.dy ** 2)
        self.dx /= magnitude
        self.dy /= magnitude

        # Start position off-screen top-left
        self.start_x = -150
        self.start_y = 50
        self.speed = 10  # pixels per frame
        # -----------------------------------

        # Bomb properties
        self.bomb_radius = 30
        self.bomb_interval = 50  # drop every N pixels
        self.bomb_timer = 0
        self.bombs = []

        # --- IMAGE LOADING WITH FALLBACK (Placeholder) ---
        try:
            # Note: This will likely fail if no 'plane.png' exists, but that's expected
            self.image = pygame_instance.image.load("plane.png").convert_alpha()
            # Scale it down to a reasonable size
            self.image = pygame_instance.transform.scale(self.image, (100, 50))
        except pygame_instance.error:
            # Placeholder surface if image is missing
            self.image = pygame_instance.Surface((100, 50))
            self.image.fill((100, 100, 100))  # Grey placeholder
            # print("Warning: plane.png not found. Using placeholder for Airstrike.")

    def update(self, screen, player, enemy_group, particle_group):
        if self.frame >= self.duration:
            self.active = False
            return

        self.frame += 1

        # Plane current position
        x = self.start_x + self.frame * self.speed * self.dx
        y = self.start_y + self.frame * self.speed * self.dy

        screen.blit(self.image, (int(x), int(y)))  # Must cast to int

        # Drop bombs at intervals based on travel distance
        self.bomb_timer += self.speed
        if self.bomb_timer >= self.bomb_interval:
            self.bomb_timer = 0
            self.bombs.append({
                "x": x,
                "y": y,
                "r": self.bomb_radius,
                "timer": 100  # Explosion delay
            })

        # Update bombs
        for bomb in list(self.bombs):
            bomb["timer"] -= 1

            # Draw falling bomb
            pygame.draw.circle(
                screen,
                (255, 200, 0),  # Yellow-orange
                (int(bomb["x"]), int(bomb["y"])),
                6
            )

            # Explosion
            if bomb["timer"] <= 0:
                bx, by = bomb["x"], bomb["y"]

                # Explosion visual (drawn for one frame)
                pygame.draw.circle(
                    screen,
                    (255, 100, 0),  # Orange-red
                    (int(bx), int(by)),
                    bomb["r"],
                    2
                )

                # Add particles
                for _ in range(10):
                    particle_group.add(Particle(int(bx), int(by)))

                # Damage enemies
                for enemy in list(enemy_group):
                    ex, ey = enemy.rect.center
                    if ((bx - ex) ** 2 + (by - ey) ** 2) ** 0.5 <= bomb["r"]:
                        if enemy.take_hit():
                            enemy.kill()

                # Damage player
                px, py = player.rect.center
                if ((bx - px) ** 2 + (by - py) ** 2) ** 0.5 <= bomb["r"]:
                    player.health -= 1

                # Remove bomb after explosion
                self.bombs.remove(bomb)


class ShooterEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image.fill((200, 50, 200))
        self.shoot_cooldown = 90
        self.timer = 0
        self.max_health = 3
        self.health = self.max_health

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
        self.max_health = 2
        self.health = self.max_health

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