"""Simple Space Invaders clone using pygame.

Run the game with::

    python main.py
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List

import pygame

# Game configuration constants
WIDTH = 800
HEIGHT = 600
FPS = 60
PLAYER_SPEED = 5
BULLET_SPEED = 8
ENEMY_ROWS = 4
ENEMY_COLS = 8
ENEMY_HORIZONTAL_PADDING = 60
ENEMY_VERTICAL_PADDING = 50
ENEMY_HORIZONTAL_SPACING = 60
ENEMY_VERTICAL_SPACING = 50
ENEMY_VERTICAL_STEP = 20
ENEMY_SPEED = 1
ENEMY_DROP_SPEED_MULTIPLIER = 1.1
PLAYER_LIVES = 3
FONT_NAME = "arial"
ENEMY_WIDTH = 40
ENEMY_HEIGHT = 30


@dataclass
class Bullet:
    rect: pygame.Rect
    speed: int
    active: bool = True

    def update(self) -> None:
        self.rect.y -= self.speed
        if self.rect.bottom < 0:
            self.active = False

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, (255, 255, 0), self.rect)


@dataclass
class Enemy:
    rect: pygame.Rect
    speed: int

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, (0, 255, 0), self.rect, border_radius=4)


class Player:
    def __init__(self) -> None:
        self.rect = pygame.Rect(WIDTH // 2 - 25, HEIGHT - 60, 50, 30)
        self.lives = PLAYER_LIVES
        self.cooldown = 0

    def move(self, dx: int) -> None:
        self.rect.x += dx * PLAYER_SPEED
        self.rect.x = max(0, min(WIDTH - self.rect.width, self.rect.x))

    def update(self) -> None:
        if self.cooldown > 0:
            self.cooldown -= 1

    def shoot(self) -> Bullet | None:
        if self.cooldown == 0:
            bullet_rect = pygame.Rect(
                self.rect.centerx - 3, self.rect.top - 10, 6, 12
            )
            self.cooldown = FPS // 4
            return Bullet(bullet_rect, BULLET_SPEED)
        return None

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, (0, 191, 255), self.rect, border_radius=4)


class SpaceInvaders:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Space Invaders")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(FONT_NAME, 24)

        self.player = Player()
        self.bullets: List[Bullet] = []
        self.enemies: List[Enemy] = []
        self.enemy_direction = 1
        self.level = 1
        self.score = 0
        self.running = True

        self._spawn_enemies()

    def _spawn_enemies(self) -> None:
        self.enemies.clear()
        self.enemy_direction = 1
        total_width = (ENEMY_COLS - 1) * ENEMY_HORIZONTAL_SPACING + ENEMY_WIDTH
        start_x = max(ENEMY_HORIZONTAL_PADDING, (WIDTH - total_width) // 2)
        for row in range(ENEMY_ROWS):
            for col in range(ENEMY_COLS):
                x = start_x + col * ENEMY_HORIZONTAL_SPACING
                y = ENEMY_VERTICAL_PADDING + row * ENEMY_VERTICAL_SPACING
                rect = pygame.Rect(x, y, ENEMY_WIDTH, ENEMY_HEIGHT)
                self.enemies.append(Enemy(rect, ENEMY_SPEED + self.level - 1))

    def run(self) -> None:
        while self.running:
            self.clock.tick(FPS)
            self._handle_events()
            self._update()
            self._draw()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False

        keys = pygame.key.get_pressed()
        move_left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        move_right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        dx = int(move_right) - int(move_left)
        if dx:
            self.player.move(dx)

        if keys[pygame.K_SPACE]:
            bullet = self.player.shoot()
            if bullet:
                self.bullets.append(bullet)

    def _update(self) -> None:
        self.player.update()
        for bullet in self.bullets:
            bullet.update()
        self.bullets = [bullet for bullet in self.bullets if bullet.active]

        if not self.enemies:
            self.level += 1
            self._spawn_enemies()

        move_down = False
        leftmost = min((enemy.rect.left for enemy in self.enemies), default=0)
        rightmost = max((enemy.rect.right for enemy in self.enemies), default=WIDTH)
        if leftmost <= 10 and self.enemy_direction < 0:
            move_down = True
            self.enemy_direction = 1
        elif rightmost >= WIDTH - 10 and self.enemy_direction > 0:
            move_down = True
            self.enemy_direction = -1

        for enemy in self.enemies:
            enemy.rect.x += enemy.speed * self.enemy_direction
        if move_down:
            for enemy in self.enemies:
                enemy.rect.y += ENEMY_VERTICAL_STEP
                enemy.speed = math.ceil(enemy.speed * ENEMY_DROP_SPEED_MULTIPLIER)

        self._handle_collisions()

    def _handle_collisions(self) -> None:
        for bullet in list(self.bullets):
            for enemy in list(self.enemies):
                if bullet.rect.colliderect(enemy.rect):
                    self.score += 10
                    self.enemies.remove(enemy)
                    bullet.active = False
                    break

        for enemy in list(self.enemies):
            if enemy.rect.colliderect(self.player.rect):
                self._lose_life()
                break
            if enemy.rect.bottom >= HEIGHT - 80:
                self._lose_life()
                break

    def _lose_life(self) -> None:
        self.player.lives -= 1
        if self.player.lives <= 0:
            self._game_over()
        else:
            self.player.rect.centerx = WIDTH // 2
            self.player.cooldown = FPS // 2
            self.bullets.clear()
            self._spawn_enemies()

    def _game_over(self) -> None:
        self._display_message("Game Over", "Press Enter or Esc to quit")
        self.running = False

    def _display_message(self, title: str, subtitle: str | None = None) -> None:
        title_font = pygame.font.SysFont(FONT_NAME, 48)
        subtitle_font = pygame.font.SysFont(FONT_NAME, 28)

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key in (
                    pygame.K_RETURN,
                    pygame.K_SPACE,
                    pygame.K_ESCAPE,
                ):
                    waiting = False

            self.screen.fill((10, 10, 30))
            title_surface = title_font.render(title, True, (255, 255, 255))
            self.screen.blit(
                title_surface,
                title_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)),
            )

            if subtitle:
                subtitle_surface = subtitle_font.render(subtitle, True, (200, 200, 200))
                self.screen.blit(
                    subtitle_surface,
                    subtitle_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20)),
                )

            score_surface = subtitle_font.render(
                f"Final Score: {self.score}", True, (255, 215, 0)
            )
            self.screen.blit(
                score_surface,
                score_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70)),
            )

            pygame.display.flip()
            self.clock.tick(FPS // 2)

    def _draw(self) -> None:
        self.screen.fill((10, 10, 30))

        for enemy in self.enemies:
            enemy.draw(self.screen)
        for bullet in self.bullets:
            bullet.draw(self.screen)
        self.player.draw(self.screen)

        score_surface = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
        lives_surface = self.font.render(f"Lives: {self.player.lives}", True, (255, 255, 255))
        level_surface = self.font.render(f"Level: {self.level}", True, (255, 255, 255))

        self.screen.blit(score_surface, (10, 10))
        self.screen.blit(lives_surface, (10, 40))
        self.screen.blit(level_surface, (WIDTH - 120, 10))

        pygame.display.flip()


if __name__ == "__main__":
    game = SpaceInvaders()
    game.run()
    pygame.quit()
