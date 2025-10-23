import pygame
import math
import random

pygame.init()
# --- Constants ---
PLAYER_SPEED = 4
PLAYER_RADIUS = 20
INVULNERABILITY_FRAMES = 30  # 0.5 seconds at 60 FPS

PROJECTILE_SPEED = 8
SHOOT_COOLDOWN = 300  # ms

ENEMY_SIZE = 30
ENEMY_COLOR = (255, 0, 0)
ENEMY_SPEED = 2

# --- Colors ---
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
STUCK_ARROW_COLOR = (180, 180, 60)
WARNING_LINE_COLOR = (255, 0, 0)


class Player(pygame.sprite.Sprite):
    PLAYER_MAX_HEALTH = 5

    def __init__(self, x, y):
        super().__init__()
        # Create a base image for drawing and flashing
        self.original_image = pygame.Surface((PLAYER_RADIUS * 2, PLAYER_RADIUS * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.original_image, BLUE, (PLAYER_RADIUS, PLAYER_RADIUS), PLAYER_RADIUS)

        self.image = self.original_image.copy()
        self.rect = self.image.get_rect(center=(x, y))

        # floating pos for smooth movement of any sub-pixels
        self.pos_x = float(self.rect.centerx)
        self.pos_y = float(self.rect.centery)

        self.last_shot_time = 0
        self.health = self.PLAYER_MAX_HEALTH

        # --- I-Frame Attributes ---
        self.invul_timer = 0
        self.is_flashing = False
        self.flash_interval = 5  # Flash every 5 frames
        # -----------------------------

        # MULTISHOT: pellet count; start at 1 (single pellet)
        self.multi_shot_level = 1

        # New stacked power-up levels (integers)
        self.speed_level = 0
        self.rapid_level = 0
        self.piercing_level = 0
        self.explosive_level = 0

    def update(self, walls, keys):
        # --- I-Frame Logic ---
        if self.invul_timer > 0:
            self.invul_timer -= 1
            # Visual flashing
            if self.invul_timer % self.flash_interval == 0:
                self.is_flashing = not self.is_flashing

            if self.is_flashing:
                # Use a transparent image during the flash
                self.image = pygame.Surface((PLAYER_RADIUS * 2, PLAYER_RADIUS * 2), pygame.SRCALPHA)
            else:
                self.image = self.original_image.copy()
        else:
            self.image = self.original_image.copy()
            self.is_flashing = False

        # --- Movement Logic ---
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

    def take_damage(self, source_center_x=None, source_center_y=None):
        """Processes damage, applying i-frames and knockback."""
        if self.invul_timer > 0:
            return

        self.health -= 1
        self.invul_timer = INVULNERABILITY_FRAMES  # Start i-frames

        # Apply Knockback if source position is provided
        if source_center_x is not None and source_center_y is not None:
            dx = self.rect.centerx - source_center_x
            dy = self.rect.centery - source_center_y
            dist = max(1, (dx ** 2 + dy ** 2) ** 0.5)
            # Apply a significant knockback force
            knockback_force = 40
            self.pos_x += knockback_force * dx / dist
            self.pos_y += knockback_force * dy / dist
            self.rect.centerx = int(self.pos_x)
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


# --- BOSS ENEMY CLASS ---
class BossEnemy(Enemy):
    def __init__(self, x, y, difficulty_level):
        BOSS_SIZE = ENEMY_SIZE * 2.5
        super().__init__(x, y)

        # Override properties
        self.image = pygame.Surface((BOSS_SIZE, BOSS_SIZE))
        self.original_color = (150, 0, 150)  # Purple
        self.flash_color = (255, 255, 255)  # White flash
        self.image.fill(self.original_color)
        self.rect = self.image.get_rect(center=(x, y))

        # Scale health based on difficulty level
        base_boss_health = 50
        self.max_health = int(base_boss_health * (1.5 ** difficulty_level))
        self.health = self.max_health

        # New movement logic (minimal drift)
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.drift_factor = 0.5
        self.center_x = x
        self.center_y = y

        # Shooting mechanics
        self.shoot_cooldown = 60 - (difficulty_level * 5)  # Faster attacks with difficulty
        self.shoot_cooldown = max(15, self.shoot_cooldown)
        self.timer = 0
        self.shot_count = 3 + (difficulty_level // 2) * 2  # More bullets with difficulty
        self.shot_spread = 60  # degrees

    def update(self, player):
        if self.flash_timer > 0:
            self.flash_timer -= 1
            if self.flash_timer == 0:
                self.image.fill(self.original_color)

        # --- Movement Logic (Drift around center, but don't actively chase) ---
        dx = self.center_x - self.pos_x
        dy = self.center_y - self.pos_y
        dist = max(1.0, math.hypot(dx, dy))

        # Apply slow drift
        self.pos_x += self.drift_factor * dx / dist * 0.5
        self.pos_y += self.drift_factor * dy / dist * 0.5

        # Add a tiny random perturbation for subtle, non-root movement
        self.pos_x += random.uniform(-0.1, 0.1)
        self.pos_y += random.uniform(-0.1, 0.1)

        self.rect.centerx = int(self.pos_x)
        self.rect.centery = int(self.pos_y)

        # --- Attack Logic ---
        self.timer += 1
        if self.timer >= self.shoot_cooldown:
            self.timer = 0

            # Fire multiple projectiles at the player
            projectiles = []

            # Base angle towards the player
            angle_to_player = math.degrees(math.atan2(player.rect.centery - self.rect.centery,
                                                      player.rect.centerx - self.rect.centerx))

            start_angle = angle_to_player - (self.shot_spread / 2.0)
            step = self.shot_spread / (self.shot_count - 1) if self.shot_count > 1 else 0

            for i in range(self.shot_count):
                angle = start_angle + step * i
                projectiles.append(EnemyProjectile(self.rect.centerx, self.rect.centery, player, angle=angle))

            # Return the list of projectiles to be added to the game group
            return projectiles

        return None


class GameEvent:
    """Base class for time-limited game events."""

    def __init__(self):
        self.active = True

    def update(self, screen, player, enemy_group, particle_group):
        raise NotImplementedError("Must be implemented by subclass")


class AirstrikeEvent(GameEvent):
    # Takes pygame as an argument for image loading (passed from test.py)
    def __init__(self, width, height, player_x, player_y, pygame_instance, duration=300):
        super().__init__()
        self.width = width
        self.height = height
        self.duration = duration  # Total frames for the event
        self.warning_frames = 60  # 1 second warning
        self.frame = 0
        self.started_flight = False

        # --- PATH CALCULATION (Targeting Player) ---
        self.start_x = -150
        self.start_y = -50
        self.target_x = player_x
        self.target_y = player_y

        dx = self.target_x - self.start_x
        dy = self.target_y - self.start_y
        magnitude = math.hypot(dx, dy)

        if magnitude > 0:
            self.dx = dx / magnitude
            self.dy = dy / magnitude
        else:
            self.dx = 1.0
            self.dy = 0.0

        self.speed = 10  # pixels per frame
        self.angle_degrees = math.degrees(math.atan2(self.dy, self.dx))
        projection_factor = max(self.width, self.height) * 1.5
        self.end_x = self.start_x + self.dx * projection_factor
        self.end_y = self.start_y + self.dy * projection_factor

        # --- IMAGE LOADING WITH ROTATION ---
        try:
            self.base_image = pygame_instance.image.load("plane.png").convert_alpha()
            self.base_image = pygame_instance.transform.scale(self.base_image, (100, 50))
        except pygame_instance.error:
            self.base_image = pygame_instance.Surface((100, 50))
            self.base_image.fill((100, 100, 100))

        self.rotated_image = pygame_instance.transform.rotate(self.base_image, -self.angle_degrees)

        # Bomb properties
        self.bomb_radius = 30
        self.bomb_interval = 50  # drop every N pixels of travel
        self.bomb_timer = 0
        self.bombs = []

    def draw_dotted_line(self, screen, color, start_pos, end_pos, dash_length=10, gap_length=5):
        """Draws a dotted line between two points."""
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        distance = math.hypot(dx, dy)

        if distance == 0:
            return

        unit_dx = dx / distance
        unit_dy = dy / distance

        current_pos = list(start_pos)

        while True:
            dash_end_x = current_pos[0] + unit_dx * dash_length
            dash_end_y = current_pos[1] + unit_dy * dash_length

            current_dist = math.hypot(current_pos[0] - start_pos[0], current_pos[1] - start_pos[1])
            dist_to_dash_end = math.hypot(dash_end_x - start_pos[0], dash_end_y - start_pos[1])

            if current_dist >= distance:
                break

            if dist_to_dash_end > distance:
                pygame.draw.line(screen, color, (int(current_pos[0]), int(current_pos[1])), end_pos, 2)
                break
            else:
                pygame.draw.line(screen, color, (int(current_pos[0]), int(current_pos[1])),
                                 (int(dash_end_x), int(dash_end_y)), 2)

            current_pos[0] = dash_end_x + unit_dx * gap_length
            current_pos[1] = dash_end_y + unit_dy * gap_length


    def update(self, screen, player, enemy_group, particle_group):
        if self.frame >= self.duration:
            self.active = False
            return

        self.frame += 1

        # --- WARNING PHASE ---
        if self.frame <= self.warning_frames:
            self.draw_dotted_line(
                screen,
                WARNING_LINE_COLOR,
                (self.start_x, self.start_y),
                (int(self.end_x), int(self.end_y))
            )
            return

        # --- FLIGHT PHASE ---
        self.started_flight = True
        flight_frame = self.frame - self.warning_frames

        x = self.start_x + flight_frame * self.speed * self.dx
        y = self.start_y + flight_frame * self.speed * self.dy

        plane_rect = self.rotated_image.get_rect(center=(int(x), int(y)))
        screen.blit(self.rotated_image, plane_rect)

        # Drop bombs
        self.bomb_timer += self.speed
        if self.bomb_timer >= self.bomb_interval:
            self.bomb_timer = 0
            self.bombs.append({
                "x": x,
                "y": y,
                "r": self.bomb_radius,
                "timer": 40  # Explosion delay
            })

        # Update bombs
        for bomb in list(self.bombs):
            bomb["timer"] -= 1

            # Draw falling bomb
            if bomb["timer"] > 10:
                pygame.draw.circle(
                    screen,
                    (255, 200, 0),
                    (int(bomb["x"]), int(bomb["y"])),
                    6
                )

            # Draw warning circle
            if bomb["timer"] > 0 and bomb["timer"] <= 30:
                warning_radius = int(bomb["r"] * (30 - bomb["timer"]) / 30)
                pygame.draw.circle(
                    screen,
                    (255, 100, 100),
                    (int(bomb["x"]), int(bomb["y"])),
                    warning_radius,
                    1
                )

            # Explosion
            if bomb["timer"] <= 0:
                bx, by = bomb["x"], bomb["y"]

                # Explosion visual
                pygame.draw.circle(
                    screen,
                    (255, 100, 0),
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

                # Damage player - USE take_damage
                px, py = player.rect.center
                if ((bx - px) ** 2 + (by - py) ** 2) ** 0.5 <= bomb["r"]:
                    player.take_damage(source_center_x=bx, source_center_y=by)

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
    def __init__(self, x, y, player, angle=None):
        super().__init__()
        self.image = pygame.Surface((8, 8))
        self.image.fill((255, 150, 0))
        self.rect = self.image.get_rect(center=(x, y))

        self.pos_x = float(self.rect.centerx)
        self.pos_y = float(self.rect.centery)

        speed = 5.0

        if angle is not None:
            rad = math.radians(angle)
            self.dx = speed * math.cos(rad)
            self.dy = speed * math.sin(rad)
        else:
            dx = player.rect.centerx - x
            dy = player.rect.centery - y
            dist = max(1.0, math.hypot(dx, dy))
            self.dx = speed * dx / dist
            self.dy = speed * dy / dist

    def update(self, walls=None):
        self.pos_x += self.dx
        self.pos_y += self.dy
        self.rect.centerx = int(self.pos_x)
        self.rect.centery = int(self.pos_y)
        if walls and pygame.sprite.spritecollideany(self, walls):
            self.kill()