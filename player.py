# player.py  (UPDATED with boss abilities)
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
    PLAYER_MAX_HEALTH = 20

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

        # Slow effect (applied by bosses like Frost King)
        self.slow_timer = 0
        self.slow_factor = 1.0
    def apply_slow(self, duration_frames, factor):
        """Apply a slow (factor < 1.0) for duration_frames."""
        # If stronger slow incoming, overwrite
        if self.slow_timer <= 0 or factor < self.slow_factor:
            self.slow_factor = factor
            self.slow_timer = duration_frames

    def update(self, walls, keys):
        # Handle slow timer
        if self.slow_timer > 0:
            self.slow_timer -= 1
            if self.slow_timer <= 0:
                self.slow_factor = 1.0

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
        spd = (PLAYER_SPEED + self.speed_level) * self.slow_factor
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

    def take_damage(self, source_center_x=None, source_center_y=None, damage=1):
        """Processes damage, applying i-frames and knockback."""
        if self.invul_timer > 0:
            return

        # Subtract damage (variable)
        self.health -= damage
        self.invul_timer = INVULNERABILITY_FRAMES  # Start i-frames

        # Apply Knockback if source position is provided
        # if source_center_x is not None and source_center_y is not None:
        #     dx = self.rect.centerx - source_center_x
        #     dy = self.rect.centery - source_center_y
        #     dist = max(1, (dx ** 2 + dy ** 2) ** 0.5)
        #     # Knockback force scales with damage (so heavy hits shove more)
        #     knockback_force = 20 * (1 + damage * 0.4)
        #     self.pos_x += knockback_force * dx / dist
        #     self.pos_y += knockback_force * dy / dist
        #     self.rect.centerx = int(self.pos_x)
        #     self.rect.centery = int(self.pos_y)


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
        random_integer = random.randint(1, 10)
        random_integer2 = random.randint(1, 10)

        if direction == "up":
            base_angle = -90.0 + (random_integer) - (random_integer2)
        elif direction == "down":
            base_angle = 90.0 + (random_integer) - (random_integer2)
        elif direction == "left":
            base_angle = 180.0 + (random_integer) - (random_integer2)
        else:
            base_angle = 0.0 + (random_integer) - (random_integer2)

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

        # contact damage (touch)
        self.contact_damage = 1

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


# --- BOSS BASE CLASS ---
class BossEnemy(Enemy):
    """
    Generic boss base. Subclasses should override visuals and behavior.
    Subclasses should return:
        - None (no action)
        - EnemyProjectile instance
        - Projectile-like instance
        - Enemy instance (to spawn minions)
        - list of the above
    Room.update in main.py handles different result types.
    """

    def __init__(self, x, y, difficulty_level):
        # Use a larger default and override in subclass
        super().__init__(x, y)
        self.original_color = (150, 0, 150)
        self.image = pygame.Surface((int(ENEMY_SIZE * 2.5), int(ENEMY_SIZE * 2.5)))
        self.image.fill(self.original_color)
        self.rect = self.image.get_rect(center=(x, y))

        # Boss stats scale with difficulty (difficulty_level starting at 1)
        base_hp = 30
        self.max_health = int(base_hp * (difficulty_level))
        self.health = self.max_health

        # movement
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.center_x = x
        self.center_y = y
        self.drift_factor = 0.5

        # attack timing
        self.timer = 0
        self.shoot_cooldown = max(20, 80 - difficulty_level * 5)

        # contact/projectile damage defaults (will be scaled by stage)
        self.contact_damage = 2
        self.projectile_damage = 1

        # display name default (subclasses should override)
        self.display_name = self.__class__.__name__

    def take_hit(self):
        # re-use Enemy.take_hit behavior
        return super().take_hit()

    def draw_health_bar(self, screen):
        # draw bigger healthbar above boss (we will normally hide this when top-bar UI is used)
        bar_width = self.rect.width
        bar_height = 8
        bar_x = self.rect.x
        bar_y = self.rect.y - 12
        pygame.draw.rect(screen, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        health_ratio = self.health / self.max_health
        current_width = int(bar_width * health_ratio)
        pygame.draw.rect(screen, (255, 200, 0), (bar_x, bar_y, current_width, bar_height))

    def apply_stage_scaling(self, boss_stage, difficulty_level):
        """
        boss_stage: integer counting how many bosses the player has faced previously (0-based).
        This method increases HP, damage, firing rate, and movement characteristics
        to make bosses progressively more punishing while keeping their identity.
        """
        # Strength multiplier: starts ~3x, grows ~1.2^stage
        strength_multiplier = 3.0 * (1.2 ** boss_stage)

        # Increase max health multiplicatively
        old_hp = self.max_health
        self.max_health = max(1, int(self.max_health * strength_multiplier))
        # keep current health proportional (so boss spawns full health)
        self.health = self.max_health

        # Increase contact and projectile damage more moderately
        self.contact_damage = max(1, int(self.contact_damage * (1.15 ** boss_stage) * (1 + (difficulty_level - 1) * 0.08)))
        self.projectile_damage = max(1, int(self.projectile_damage * (1.2 ** boss_stage) * (1 + (difficulty_level - 1) * 0.05)))

        # Reduce shoot cooldown (make more frequent) but clamp
        if hasattr(self, "shoot_cooldown"):
            self.shoot_cooldown = max(6, int(self.shoot_cooldown * max(0.4, 1.0 - boss_stage * 0.04)))

        # Boost movement/behavior if they have movement attributes
        if hasattr(self, "speed"):
            self.speed *= (1.0 + boss_stage * 0.03)
        if hasattr(self, "patrol_speed"):
            self.patrol_speed *= (1.0 + boss_stage * 0.03)
        if hasattr(self, "dash_speed"):
            self.dash_speed *= (1.0 + boss_stage * 0.03)
        # make certain bosses spawn more minions at higher stages
        if hasattr(self, "num_orbiters"):
            self.num_orbiters = min(8, self.num_orbiters + boss_stage // 3)
        if hasattr(self, "spawn_cooldown"):
            # shorter spawn cooldown to spawn more minions
            self.spawn_cooldown = max(20, int(self.spawn_cooldown * max(0.45, 1.0 - boss_stage * 0.03)))

        # store stage for reference
        self.boss_stage = boss_stage
        self.scaled = True


# --- 20 Boss Subclasses ---
# Each boss overrides __init__ to change visuals & stats, and update() for behavior.

# Helper small function to create small orbiters (visual only) for some bosses
def _make_orbiter_image(radius, color):
    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.circle(surf, color, (radius, radius), radius)
    return surf


class Boss01_Core(BossEnemy):
    """Mini Core - small, slow, shoots single projectiles"""
    def __init__(self, x, y, difficulty_level):
        super().__init__(x, y, difficulty_level)
        size = int(ENEMY_SIZE * 1.2)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (120, 120, 120), (size // 2, size // 2), size // 2)
        self.rect = self.image.get_rect(center=(x, y))
        self.max_health = int(8 * (1.15 ** difficulty_level))
        self.health = self.max_health
        self.shoot_cooldown = max(40, 90 - difficulty_level * 4)
        self.timer = 0
        self.speed = 0.6 + difficulty_level * 0.02
        self.display_name = "Mini Core"
        self.projectile_damage = 1

    def update(self, player):
        # slowly track and periodically fire a direct projectile at player
        self.timer += 1
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        dist = max(1.0, math.hypot(dx, dy))
        self.rect.x += int(self.speed * dx / dist)
        self.rect.y += int(self.speed * dy / dist)

        if self.timer >= self.shoot_cooldown:
            self.timer = 0
            return EnemyProjectile(self.rect.centerx, self.rect.centery, player, damage=self.projectile_damage)
        return None


class Boss02_Blades(BossEnemy):
    """Dual Blades - silhouette with two rotating blades, performs dashes"""
    def __init__(self, x, y, difficulty_level):
        super().__init__(x, y, difficulty_level)
        w = int(ENEMY_SIZE * 2.0)
        h = int(ENEMY_SIZE * 1.6)
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (200, 120, 120), (0, h // 4, w, h // 2), border_radius=6)
        self.rect = self.image.get_rect(center=(x, y))
        self.max_health = int(20 * (1.25 ** difficulty_level))
        self.health = self.max_health
        self.dash_cooldown = max(60, 160 - difficulty_level * 6)
        self.dash_timer = 0
        self.dash_speed = 10 + difficulty_level * 0.6
        self.dashing = False
        self.dash_dir = (0, 0)
        self.dash_duration = 18
        self.dash_tick = 0
        self.display_name = "Dual Blades"
        self.projectile_damage = 1

    def update(self, player):
        self.dash_timer += 1
        if self.dashing:
            self.dash_tick += 1
            self.rect.x += int(self.dash_dir[0] * self.dash_speed)
            self.rect.y += int(self.dash_dir[1] * self.dash_speed)
            if self.dash_tick >= self.dash_duration:
                self.dashing = False
                self.dash_tick = 0
            # No projectile; relies on high-contact damage
            return None
        else:
            # small repositioning
            dx = player.rect.centerx - self.rect.centerx
            dy = player.rect.centery - self.rect.centery
            dist = max(1.0, math.hypot(dx, dy))
            self.rect.x += int(1 * dx / dist)
            self.rect.y += int(1 * dy / dist)

        if self.dash_timer >= self.dash_cooldown:
            # start dash towards player
            self.dash_timer = 0
            dx = player.rect.centerx - self.rect.centerx
            dy = player.rect.centery - self.rect.centery
            mag = max(1.0, math.hypot(dx, dy))
            self.dash_dir = (dx / mag, dy / mag)
            self.dashing = True
            self.dash_tick = 0
        return None


class Boss03_Burster(BossEnemy):
    """Burster - medium round, fires spread shots"""
    def __init__(self, x, y, difficulty_level):
        super().__init__(x, y, difficulty_level)
        size = int(ENEMY_SIZE * 2.2)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (220, 50, 50), (size // 2, size // 2), size // 2)
        self.rect = self.image.get_rect(center=(x, y))
        self.max_health = int(18 * (1.2 ** difficulty_level))
        self.health = self.max_health
        self.shoot_cooldown = max(30, 85 - difficulty_level * 3)
        self.shots = 5 + difficulty_level // 2
        self.timer = 0
        self.display_name = "Burster"
        self.projectile_damage = 1

    def update(self, player):
        self.timer += 1
        if self.timer >= self.shoot_cooldown:
            self.timer = 0
            # create a spread of projectiles aimed near the player
            base_dx = player.rect.centerx - self.rect.centerx
            base_dy = player.rect.centery - self.rect.centery
            base_angle = math.degrees(math.atan2(base_dy, base_dx))
            spread = 40  # degrees
            shots = []
            if self.shots <= 1:
                shots.append(EnemyProjectile(self.rect.centerx, self.rect.centery, player, damage=self.projectile_damage))
            else:
                start = base_angle - spread / 2
                step = spread / max(1, self.shots - 1)
                for i in range(self.shots):
                    angle = start + step * i
                    shots.append(EnemyProjectile(self.rect.centerx, self.rect.centery, player, angle=angle, damage=self.projectile_damage))
            return shots
        # small wander
        return None


class Boss04_Crawler(BossEnemy):
    """Crawler - long horizontal shape, moves along ground only and emits shockwave"""
    def __init__(self, x, y, difficulty_level):
        super().__init__(x, y, difficulty_level)
        w = int(ENEMY_SIZE * 3.2)
        h = int(ENEMY_SIZE * 0.9)
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (100, 200, 100), (0, 0, w, h), border_radius=6)
        self.rect = self.image.get_rect(center=(x, y + 100))
        self.pos_x = float(self.rect.centerx)
        self.pos_y = float(self.rect.centery)
        self.max_health = int(22 * (1.18 ** difficulty_level))
        self.health = self.max_health
        self.patrol_dir = 1
        self.patrol_speed = 2 + difficulty_level * 0.1
        self.shoot_cooldown = 120 - difficulty_level * 2
        self.timer = 0
        self.display_name = "Crawler"
        self.projectile_damage = 1

    def update(self, player):
        # patrol left-right
        self.rect.x += int(self.patrol_speed * self.patrol_dir)
        if self.rect.left < 60 or self.rect.right > 740:
            self.patrol_dir *= -1

        # occasionally do a ground shockwave: a few slow heavy projectiles toward player
        self.timer += 1
        if self.timer >= self.shoot_cooldown:
            self.timer = 0
            projectiles = []
            # 3 heavy, slow projectiles aimed at player with small spread
            base_dx = player.rect.centerx - self.rect.centerx
            base_dy = player.rect.centery - self.rect.centery
            base_angle = math.degrees(math.atan2(base_dy, base_dx))
            for a in (-10, 0, 10):
                projectiles.append(EnemyProjectile(self.rect.centerx, self.rect.centery, player, angle=base_angle + a, damage=self.projectile_damage + 1))
            return projectiles
        return None


class Boss05_Sentinel(BossEnemy):
    """Sentinel - large square that shoots homing bullets"""
    def __init__(self, x, y, difficulty_level):
        super().__init__(x, y, difficulty_level)
        size = int(ENEMY_SIZE * 2.6)
        self.image = pygame.Surface((size, size))
        self.image.fill((180, 180, 220))
        self.rect = self.image.get_rect(center=(x, y))
        self.max_health = int(28 * (1.22 ** difficulty_level))
        self.health = self.max_health
        self.shoot_cooldown = max(25, 70 - difficulty_level * 2)
        self.timer = 0
        self.display_name = "Sentinel"
        self.projectile_damage = 1

    def update(self, player):
        self.timer += 1
        # slightly hover around center
        self.rect.x += int(math.sin(pygame.time.get_ticks() * 0.001) * 1.2)
        self.rect.y += int(math.cos(pygame.time.get_ticks() * 0.001) * 1.0)

        if self.timer >= self.shoot_cooldown:
            self.timer = 0
            # spawn several homing shots (they always target the player)
            shots = []
            for _ in range(2 + (self.boss_stage // 3 if hasattr(self, "boss_stage") else 0)):
                shots.append(EnemyProjectile(self.rect.centerx, self.rect.centery, player, damage=self.projectile_damage))
            return shots
        return None


class Boss06_Orbweaver(BossEnemy):
    """Orbweaver - has orbiting little orbs that fire too"""
    def __init__(self, x, y, difficulty_level):
        super().__init__(x, y, difficulty_level)
        size = int(ENEMY_SIZE * 2.2)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (140, 80, 200), (size // 2, size // 2), size // 2)
        self.rect = self.image.get_rect(center=(x, y))
        self.orbiters = []
        self.num_orbiters = 3 + (difficulty_level // 4)
        for i in range(self.num_orbiters):
            angle = i * (360 / self.num_orbiters)
            self.orbiters.append({"angle": angle, "dist": 40 + i * 10})
        self.timer = 0
        self.shoot_cooldown = max(40, 90 - difficulty_level * 3)
        self.max_health = int(24 * (1.2 ** difficulty_level))
        self.health = self.max_health
        self.display_name = "Orbweaver"
        self.projectile_damage = 1

    def update(self, player):
        # rotate orbiters (visual only) and occasionally fire radial bursts
        self.timer += 1
        for i, orb in enumerate(self.orbiters):
            orb["angle"] = (orb["angle"] + 2 + i) % 360

        if self.timer >= self.shoot_cooldown:
            self.timer = 0
            shots = []
            # radial burst
            count = 6 + (self.num_orbiters)
            for i in range(count):
                angle = i * (360 / count)
                shots.append(EnemyProjectile(self.rect.centerx, self.rect.centery, player, angle=angle, damage=self.projectile_damage))
            return shots
        return None


class Boss07_Sprinter(BossEnemy):
    """Sprinter - fast triangle that charges repeatedly"""
    def __init__(self, x, y, difficulty_level):
        super().__init__(x, y, difficulty_level)
        size = int(ENEMY_SIZE * 1.8)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, (230, 130, 30), [(size // 2, 0), (0, size), (size, size)])
        self.rect = self.image.get_rect(center=(x, y))
        self.charge_cooldown = max(40, 140 - difficulty_level * 5)
        self.charge_timer = 0
        self.charging = False
        self.charge_speed = 12 + difficulty_level * 0.6
        self.charge_duration = 16
        self.charge_tick = 0
        self.max_health = int(16 * (1.18 ** difficulty_level))
        self.health = self.max_health
        self.display_name = "Sprinter"
        self.projectile_damage = 1

    def update(self, player):
        self.charge_timer += 1
        if self.charging:
            self.charge_tick += 1
            self.rect.x += int(self.charge_dir[0] * self.charge_speed)
            self.rect.y += int(self.charge_dir[1] * self.charge_speed)
            if self.charge_tick >= self.charge_duration:
                self.charging = False
                self.charge_tick = 0
        else:
            # small hops around center
            self.rect.x += int(math.sin(pygame.time.get_ticks() * 0.002) * 1.0)

        if self.charge_timer >= self.charge_cooldown:
            self.charge_timer = 0
            dx = player.rect.centerx - self.rect.centerx
            dy = player.rect.centery - self.rect.centery
            mag = max(1.0, math.hypot(dx, dy))
            self.charge_dir = (dx / mag, dy / mag)
            self.charging = True
            self.charge_tick = 0
        return None


class Boss08_Warden(BossEnemy):
    """Warden - shielded boss that becomes invulnerable briefly and shoots"""
    def __init__(self, x, y, difficulty_level):
        super().__init__(x, y, difficulty_level)
        size = int(ENEMY_SIZE * 2.8)
        self.image = pygame.Surface((size, size))
        self.image.fill((90, 140, 180))
        self.rect = self.image.get_rect(center=(x, y))
        self.shield_timer = 0
        self.shield_duration = 60
        self.shield_cooldown = max(120, 300 - difficulty_level * 10)
        self.timer = 0
        self.max_health = int(32 * (1.25 ** difficulty_level))
        self.health = self.max_health
        self.display_name = "Warden"
        self.projectile_damage = 1

    def take_hit(self):
        # invulnerable during shield
        if self.shield_timer > 0:
            # flash but don't take damage
            self.image.fill((150, 180, 200))
            self.flash_timer = 6
            return False
        return super().take_hit()

    def update(self, player):
        self.timer += 1
        if self.shield_timer > 0:
            self.shield_timer -= 1
            # while shielded, do small radial bullets
            if self.timer % 8 == 0:
                # shoot outward in 6 directions
                shots = []
                for a in range(6):
                    angle = a * (360 / 6)
                    shots.append(EnemyProjectile(self.rect.centerx, self.rect.centery, player, angle=angle, damage=self.projectile_damage))
                return shots
        else:
            # normal attack: single targeted projectile occasionally
            if self.timer >= self.shield_cooldown:
                self.timer = 0
                self.shield_timer = self.shield_duration
                return None

            if self.timer % 50 == 0:
                return EnemyProjectile(self.rect.centerx, self.rect.centery, player, damage=self.projectile_damage)
        return None


class Boss09_Bomber(BossEnemy):
    """Bomber - cross-shaped, drops explosive projectiles"""
    def __init__(self, x, y, difficulty_level):
        super().__init__(x, y, difficulty_level)
        size = int(ENEMY_SIZE * 2.4)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (200, 80, 40), (size // 4, 0, size // 2, size))
        pygame.draw.rect(self.image, (200, 80, 40), (0, size // 4, size, size // 2))
        self.rect = self.image.get_rect(center=(x, y))
        self.drop_cooldown = max(40, 140 - difficulty_level * 4)
        self.timer = 0
        self.max_health = int(26 * (1.2 ** difficulty_level))
        self.health = self.max_health
        self.display_name = "Bomber"
        self.projectile_damage = 2

    def update(self, player):
        # drop slow-moving bombs downward (projectiles with angle ~90)
        self.timer += 1
        if self.timer >= self.drop_cooldown:
            self.timer = 0
            # bombs fall downwards: spawn a projectile with angle ~90 +/- 10 deg and higher damage
            angle = 90 + random.uniform(-10, 10)
            return EnemyProjectile(self.rect.centerx + random.randint(-20, 20), self.rect.centery, player, angle=angle, damage=self.projectile_damage + 1)
        return None


class Boss10_PhaseWalker(BossEnemy):
    """Phase Walker - teleports intermittently and fires on teleport"""
    def __init__(self, x, y, difficulty_level):
        super().__init__(x, y, difficulty_level)
        size = int(ENEMY_SIZE * 2.0)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (100, 150, 255), (size // 2, size // 2), size // 2)
        self.rect = self.image.get_rect(center=(x, y))
        self.tp_cooldown = max(60, 150 - difficulty_level * 4)
        self.tp_timer = 0
        self.tp_burst = 3
        self.max_health = int(20 * (1.2 ** difficulty_level))
        self.health = self.max_health
        self.display_name = "Phase Walker"
        self.projectile_damage = 1

    def update(self, player):
        self.tp_timer += 1
        if self.tp_timer >= self.tp_cooldown:
            self.tp_timer = 0
            # teleport to random on-screen location then fire a burst
            nx = random.randint(100, 700)
            ny = random.randint(100, 500)
            self.rect.center = (nx, ny)
            bursts = []
            for i in range(self.tp_burst):
                angle = random.uniform(-20, 20) + math.degrees(math.atan2(player.rect.centery - ny, player.rect.centerx - nx))
                bursts.append(EnemyProjectile(nx, ny, player, angle=angle, damage=self.projectile_damage))
            return bursts
        return None


class Boss11_Cycler(BossEnemy):
    """Cycler - rotating parts, fires while rotating"""
    def __init__(self, x, y, difficulty_level):
        super().__init__(x, y, difficulty_level)
        size = int(ENEMY_SIZE * 2.6)
        self.base_image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.base_image, (160, 100, 240), (size // 2, size // 2), size // 2)
        self.rect = self.base_image.get_rect(center=(x, y))
        self.angle = 0
        self.shoot_cooldown = max(20, 50 - difficulty_level * 2)
        self.timer = 0
        self.max_health = int(30 * (1.2 ** difficulty_level))
        self.health = self.max_health
        self.display_name = "Cycler"
        self.projectile_damage = 1

    def update(self, player):
        self.timer += 1
        self.angle = (self.angle + 6) % 360
        if self.timer >= self.shoot_cooldown:
            self.timer = 0
            # fire rotated volley (angles offset by cycle angle)
            shots = []
            for i in range(6):
                angle = self.angle + i * (360 / 6)
                shots.append(EnemyProjectile(self.rect.centerx, self.rect.centery, player, angle=angle, damage=self.projectile_damage))
            return shots
        return None


class Boss12_Shifter(BossEnemy):
    """Shifter - changes forms randomly and fires random attacks"""
    def __init__(self, x, y, difficulty_level):
        super().__init__(x, y, difficulty_level)
        self.forms = [ (180, 60, 60), (60, 180, 60), (60, 60, 180), (180, 180, 60)]
        self.form = 0
        size = int(ENEMY_SIZE * 2.4)
        self.base_image = pygame.Surface((size, size))
        self.base_image.fill(self.forms[self.form])
        self.rect = self.base_image.get_rect(center=(x, y))
        self.change_cooldown = max(80, 200 - difficulty_level * 6)
        self.timer = 0
        self.max_health = int(22 * (1.18 ** difficulty_level))
        self.health = self.max_health
        self.display_name = "Shifter"
        self.projectile_damage = 1

    def update(self, player):
        self.timer += 1
        if self.timer >= self.change_cooldown:
            self.timer = 0
            # pick a new form and immediately fire a pattern based on it
            self.form = random.randrange(len(self.forms))
            self.base_image.fill(self.forms[self.form])
            # form actions:
            if self.form == 0:
                # single strong shot
                return EnemyProjectile(self.rect.centerx, self.rect.centery, player, damage=self.projectile_damage + 1)
            elif self.form == 1:
                # short radial burst
                shots = []
                for a in range(8):
                    angle = a * (360 / 8)
                    shots.append(EnemyProjectile(self.rect.centerx, self.rect.centery, player, angle=angle, damage=self.projectile_damage))
                return shots
            elif self.form == 2:
                # spawn a minion
                return Enemy(self.rect.centerx + random.randint(-30,30), self.rect.centery + random.randint(-30,30))
            else:
                # targeted 3-shot cone
                shots = []
                base_angle = math.degrees(math.atan2(player.rect.centery - self.rect.centery, player.rect.centerx - self.rect.centerx))
                for a in (-10, 0, 10):
                    shots.append(EnemyProjectile(self.rect.centerx, self.rect.centery, player, angle=base_angle + a, damage=self.projectile_damage))
                return shots
        return None


class Boss13_Spawner(BossEnemy):
    """Spawner - periodically spawns regular enemies"""
    def __init__(self, x, y, difficulty_level):
        super().__init__(x, y, difficulty_level)
        size = int(ENEMY_SIZE * 2.4)
        self.image = pygame.Surface((size, size))
        self.image.fill((120, 80, 40))
        self.rect = self.image.get_rect(center=(x, y))
        self.spawn_cooldown = max(60, 160 - difficulty_level * 6)
        self.timer = 0
        self.max_health = int(26 * (1.22 ** difficulty_level))
        self.health = self.max_health
        self.display_name = "Spawner"
        self.projectile_damage = 1

    def update(self, player):
        self.timer += 1
        if self.timer >= self.spawn_cooldown:
            self.timer = 0
            # spawn 1-2 regular enemies near boss
            spawns = []
            count = 1 + (1 if random.random() < 0.4 else 0)
            for _ in range(count):
                nx = self.rect.centerx + random.randint(-60, 60)
                ny = self.rect.centery + random.randint(-60, 60)
                e = Enemy(nx, ny)
                e.max_health = max(1, int(e.max_health * (1 + (self.boss_stage if hasattr(self,'boss_stage') else 0)*0.2)))
                e.health = e.max_health
                spawns.append(e)
            return spawns
        return None


class Boss14_Blazer(BossEnemy):
    """Blazer - constant stream of fiery shots"""
    def __init__(self, x, y, difficulty_level):
        super().__init__(x, y, difficulty_level)
        size = int(ENEMY_SIZE * 2.0)
        self.image = pygame.Surface((size, size))
        self.image.fill((240, 140, 40))
        self.rect = self.image.get_rect(center=(x, y))
        self.stream_rate = max(4, 12 - difficulty_level)
        self.timer = 0
        self.max_health = int(24 * (1.2 ** difficulty_level))
        self.health = self.max_health
        self.display_name = "Blazer"
        self.projectile_damage = 1
        self.stream_active = False
        self.stream_duration = 60
        self.stream_tick = 0

    def update(self, player):
        self.timer += 1
        if not self.stream_active and self.timer >= 120:
            self.stream_active = True
            self.stream_tick = 0
            self.timer = 0
        if self.stream_active:
            self.stream_tick += 1
            # fire small fast projectiles every few frames
            if self.stream_tick % self.stream_rate == 0:
                return EnemyProjectile(self.rect.centerx + random.randint(-10,10), self.rect.centery, player, damage=self.projectile_damage)
            if self.stream_tick >= self.stream_duration:
                self.stream_active = False
        return None


class Boss15_FrostKing(BossEnemy):
    """Frost King - slows player when nearby (visualized only here)"""
    def __init__(self, x, y, difficulty_level):
        super().__init__(x, y, difficulty_level)
        size = int(ENEMY_SIZE * 3.2)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (150, 220, 255), (size // 2, size // 2), size // 2)
        self.rect = self.image.get_rect(center=(x, y))
        self.freeze_radius = 100 + difficulty_level * 5
        self.max_health = int(28 * (1.2 ** difficulty_level))
        self.health = self.max_health
        self.timer = 0
        self.display_name = "Frost King"
        self.projectile_damage = 1

    def update(self, player):
        # aura: if player within radius, apply slow
        px, py = player.rect.center
        bx, by = self.rect.center
        dist = math.hypot(px - bx, py - by)
        if dist <= self.freeze_radius:
            player.apply_slow(40, 0.55)  # ~0.66x speed for 40 frames
        # occasionally fire icy shards
        self.timer += 1
        if self.timer >= 80:
            self.timer = 0
            shots = []
            for a in (-12, 0, 12):
                base_angle = math.degrees(math.atan2(player.rect.centery - by, player.rect.centerx - bx))
                shots.append(EnemyProjectile(bx, by, player, angle=base_angle + a, damage=self.projectile_damage))
            return shots
        return None


class Boss16_Stormer(BossEnemy):
    """Stormer - chain lightning (simulated by multiple close projectiles)"""
    def __init__(self, x, y, difficulty_level):
        super().__init__(x, y, difficulty_level)
        size = int(ENEMY_SIZE * 2.6)
        self.image = pygame.Surface((size, size))
        self.image.fill((230, 230, 80))
        self.rect = self.image.get_rect(center=(x, y))
        self.chain_rate = max(40, 110 - difficulty_level * 4)
        self.timer = 0
        self.max_health = int(26 * (1.22 ** difficulty_level))
        self.health = self.max_health
        self.display_name = "Stormer"
        self.projectile_damage = 1

    def update(self, player):
        self.timer += 1
        if self.timer >= self.chain_rate:
            self.timer = 0
            # quick burst of nearby angled projectiles to simulate chain lightning
            shots = []
            for i in range(6):
                angle = math.degrees(math.atan2(player.rect.centery - self.rect.centery, player.rect.centerx - self.rect.centerx)) + random.uniform(-25,25)
                shots.append(EnemyProjectile(self.rect.centerx + random.randint(-20,20), self.rect.centery + random.randint(-20,20), player, angle=angle, damage=self.projectile_damage))
            return shots
        return None


class Boss17_Titan(BossEnemy):
    """Titan - massive, slow, heavy projectiles"""
    def __init__(self, x, y, difficulty_level):
        super().__init__(x, y, difficulty_level)
        size = int(ENEMY_SIZE * 3.6)
        self.image = pygame.Surface((size, size))
        self.image.fill((160, 30, 30))
        self.rect = self.image.get_rect(center=(x, y))
        self.shoot_cooldown = max(50, 140 - difficulty_level * 3)
        self.timer = 0
        self.max_health = int(45 * (1.28 ** difficulty_level))
        self.health = self.max_health
        self.display_name = "Titan"
        self.projectile_damage = 3

    def update(self, player):
        self.timer += 1
        if self.timer >= self.shoot_cooldown:
            self.timer = 0
            # heavy slow projectile (higher damage)
            return EnemyProjectile(self.rect.centerx, self.rect.centery, player, damage=self.projectile_damage + 2)
        return None


class Boss18_Phantom(BossEnemy):
    """Phantom - fades in/out and phases through bullets (visual only)"""
    def __init__(self, x, y, difficulty_level):
        super().__init__(x, y, difficulty_level)
        size = int(ENEMY_SIZE * 2.4)
        self.base_image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.base_image, (110, 110, 140), (size // 2, size // 2), size // 2)
        self.rect = self.base_image.get_rect(center=(x, y))
        self.alpha = 255
        self.fade_dir = -5
        self.shoot_cooldown = max(30, 80 - difficulty_level * 2)
        self.timer = 0
        self.max_health = int(18 * (1.18 ** difficulty_level))
        self.health = self.max_health
        self.display_name = "Phantom"
        self.projectile_damage = 1
        self.phase = False
        self.phase_timer = 0
        self.phase_duration = 40
        self.phase_cooldown = 120

    def update(self, player):
        self.timer += 1
        # fade alpha and toggle intangible phases
        if self.timer >= self.phase_cooldown:
            self.timer = 0
            self.phase = True
            self.phase_timer = 0
        if self.phase:
            self.phase_timer += 1
            # teleport slightly while phased
            if self.phase_timer % 10 == 0:
                self.rect.centerx += random.randint(-40, 40)
                self.rect.centery += random.randint(-30, 30)
            if self.phase_timer >= self.phase_duration:
                self.phase = False
                self.phase_timer = 0

        if self.timer % self.shoot_cooldown == 0:
            # shoot a pair of slightly offset piercing bolts
            shots = []
            base_angle = math.degrees(math.atan2(player.rect.centery - self.rect.centery, player.rect.centerx - self.rect.centerx))
            shots.append(EnemyProjectile(self.rect.centerx, self.rect.centery, player, angle=base_angle - 6, damage=self.projectile_damage))
            shots.append(EnemyProjectile(self.rect.centerx, self.rect.centery, player, angle=base_angle + 6, damage=self.projectile_damage))
            return shots
        return None


class Boss19_Colossus(BossEnemy):
    """Colossus - multi-phase: changes attack when health below thresholds"""
    def __init__(self, x, y, difficulty_level):
        super().__init__(x, y, difficulty_level)
        size = int(ENEMY_SIZE * 3.2)
        self.image = pygame.Surface((size, size))
        self.image.fill((80, 40, 120))
        self.rect = self.image.get_rect(center=(x, y))
        self.max_health = int(60 * (1.25 ** difficulty_level))
        self.health = self.max_health
        self.phase = 1
        self.timer = 0
        self.display_name = "Colossus"
        self.projectile_damage = 2
        self.phase_changed = False

    def update(self, player):
        self.timer += 1
        # change phase when health crosses thresholds
        ratio = self.health / self.max_health
        if ratio < 0.66 and self.phase == 1:
            self.phase = 2
        if ratio < 0.33 and self.phase == 2:
            self.phase = 3

        if self.phase == 1 and self.timer % 90 == 0:
            # single heavy projectile
            return EnemyProjectile(self.rect.centerx, self.rect.centery, player, damage=self.projectile_damage + 1)
        elif self.phase == 2 and self.timer % 60 == 0:
            # fire three spread shots
            shots = []
            base_angle = math.degrees(math.atan2(player.rect.centery - self.rect.centery, player.rect.centerx - self.rect.centerx))
            for a in (-12, 0, 12):
                shots.append(EnemyProjectile(self.rect.centerx, self.rect.centery, player, angle=base_angle + a, damage=self.projectile_damage + 1))
            return shots
        elif self.phase == 3 and self.timer % 40 == 0:
            # radial slam
            shots = []
            for i in range(12):
                shots.append(EnemyProjectile(self.rect.centerx, self.rect.centery, player, angle=i * (360 / 12), damage=self.projectile_damage + 1))
            return shots
        return None


class Boss20_OmegaCore(BossEnemy):
    """Omega Core - black/purple, combines many behaviors (final)"""
    def __init__(self, x, y, difficulty_level):
        super().__init__(x, y, difficulty_level)
        size = int(ENEMY_SIZE * 3.8)
        self.base_image = pygame.Surface((size, size))
        self.base_image.fill((30, 10, 40))
        self.rect = self.base_image.get_rect(center=(x, y))
        self.timer = 0
        self.max_health = int(80 * (1.3 ** difficulty_level))
        self.health = self.max_health
        self.display_name = "Omega Core"
        self.projectile_damage = 3
        self.phase_timer = 0
        self.phase = 0
        self.attack_cycle = 0

    def update(self, player):
        self.timer += 1
        self.phase_timer += 1
        # Cycle through a set of attack phases: radial -> minions -> targeted storm
        if self.phase_timer >= 120:
            self.phase_timer = 0
            self.phase = (self.phase + 1) % 3

        if self.phase == 0 and self.timer % 40 == 0:
            # radial barrage
            shots = []
            count = 16
            for i in range(count):
                shots.append(EnemyProjectile(self.rect.centerx, self.rect.centery, player, angle=i * (360 / count), damage=self.projectile_damage))
            return shots
        elif self.phase == 1 and self.timer % 90 == 0:
            # spawn multiple mid-health minions (Shooters)
            spawns = []
            for i in range(2 + (self.boss_stage // 3 if hasattr(self,'boss_stage') else 0)):
                sx = self.rect.centerx + random.randint(-80, 80)
                sy = self.rect.centery + random.randint(-80, 80)
                s = ShooterEnemy(sx, sy)
                s.max_health = max(1, int(s.max_health * (1 + (self.boss_stage if hasattr(self,'boss_stage') else 0)*0.2)))
                s.health = s.max_health
                spawns.append(s)
            return spawns
        elif self.phase == 2 and self.timer % 20 == 0:
            # targeted nano-storm: many small shots at player
            shots = []
            for _ in range(3 + (self.boss_stage // 2 if hasattr(self,'boss_stage') else 0)):
                shots.append(EnemyProjectile(self.rect.centerx + random.randint(-20,20), self.rect.centery + random.randint(-20,20), player, damage=self.projectile_damage))
            return shots
        return None


# --- Utility: create boss instance by index (0-based) ---
BOSS_CLASS_LIST = [
    Boss01_Core, Boss02_Blades, Boss03_Burster, Boss04_Crawler, Boss05_Sentinel,
    Boss06_Orbweaver, Boss07_Sprinter, Boss08_Warden, Boss09_Bomber, Boss10_PhaseWalker,
    Boss11_Cycler, Boss12_Shifter, Boss13_Spawner, Boss14_Blazer, Boss15_FrostKing,
    Boss16_Stormer, Boss17_Titan, Boss18_Phantom, Boss19_Colossus, Boss20_OmegaCore
]


def create_boss_by_index(index, x, y, difficulty_level, boss_stage=0):
    """index: 0..19 (wraps if outside). Returns an instance of that boss.
       boss_stage: how many bosses have been faced already (0-based)."""
    idx = index % len(BOSS_CLASS_LIST)
    cls = BOSS_CLASS_LIST[idx]
    boss = cls(x, y, difficulty_level)
    # apply stage scaling that increases HP, damage, and aggression
    boss.apply_stage_scaling(boss_stage, difficulty_level)
    return boss


# --- GameEvent and AirstrikeEvent (unchanged except small bomb damage set) ---
class GameEvent:
    """Base class for time-limited game events."""

    def __init__(self):
        self.active = True

    def update(self, screen, player, enemy_group, particle_group):
        raise NotImplementedError("Must be implemented by subclass")


class AirstrikeEvent(GameEvent):
    # Takes pygame as an argument for image loading (passed from main)
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

                # Damage player - USE take_damage with moderate bomb damage
                px, py = player.rect.center
                if ((bx - px) ** 2 + (by - py) ** 2) ** 0.5 <= bomb["r"]:
                    player.take_damage(source_center_x=bx, source_center_y=by, damage=2)

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
        self.contact_damage = 1
        self.projectile_damage = 1

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
        self.contact_damage = 1

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
    def __init__(self, x, y, player, angle=None, damage=1):
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

        # Damage this projectile does on hit
        self.damage = damage

    def update(self, walls=None):
        self.pos_x += self.dx
        self.pos_y += self.dy
        self.rect.centerx = int(self.pos_x)
        self.rect.centery = int(self.pos_y)
        if walls and pygame.sprite.spritecollideany(self, walls):
            self.kill()
