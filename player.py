import pygame
import math
import random

# --- Constants used by main.py ---
PLAYER_SPEED = 4
PLAYER_RADIUS = 20
PROJECTILE_SPEED = 8
SHOOT_COOLDOWN = 300  # ms

BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

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
        # Powerup pickup should multiply this by 3: 1 -> 3 -> 9 -> ...
        self.multi_shot_level = 1

        # New stacked power-up levels (integers)
        self.speed_level = 0     # +1 movement speed per stack
        self.rapid_level = 0     # each stack multiplies cooldown by 0.8
        self.piercing_level = 0  # +1 extra enemy hit per stack
        self.explosive_level = 0 # explosive radius/damage per stack

    def can_attack(self):
        # cooldown reduced multiplicatively by rapid_level stacks
        cooldown = SHOOT_COOLDOWN * (0.8 ** self.rapid_level) if self.rapid_level > 0 else SHOOT_COOLDOWN
        cooldown = max(50, int(cooldown))
        return pygame.time.get_ticks() - self.last_shot_time > cooldown

    def attack(self, direction):
        """
        Returns a list of Projectile objects (Projectile defined in main.py).
        direction: 'up','down','left','right'
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

         # local import to avoid circular issues when running as separate module
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
        if walls and pygame.sprite.spritecollide(self, walls, False):
            self.pos_x -= dx
            self.rect.centerx = int(self.pos_x)

        self.pos_y += dy
        self.rect.centery = int(self.pos_y)
        if walls and pygame.sprite.spritecollide(self, walls, False):
            self.pos_y -= dy
            self.rect.centery = int(self.pos_y)
    def teleport_to(self, x, y):
        """Place the player at a new position (used when entering a new room)."""
        self.rect.centerx = int(x)
        self.rect.centery = int(y)
        self.pos_x = float(self.rect.centerx)
        self.pos_y = float(self.rect.centery)
