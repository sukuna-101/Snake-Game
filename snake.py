"""
Snake Game - 100% Python (Pygame)
Recursos: Pontuação, Game Over, Níveis de dificuldade, High Score salvo em arquivo

Requisitos:
    pip install pygame

Como jogar:
    python snake.py

Controles:
    Setas ou WASD -> mover
    P             -> pausar
    R             -> reiniciar (na tela de game over)
    ESC           -> sair
"""

import os
import sys
import json
import random
from dataclasses import dataclass

try:
    import pygame
except ImportError:
    print("Pygame nao esta instalado. Instale com: pip install pygame")
    sys.exit(1)


# ---------- Configuracoes ----------
CELL = 24
COLS, ROWS = 28, 22
HUD_H = 60
WIDTH, HEIGHT = COLS * CELL, ROWS * CELL + HUD_H
FPS_BASE = 10

BG1 = (18, 22, 30)
BG2 = (24, 28, 38)
HUD_BG = (12, 15, 22)
TEXT = (230, 235, 245)
MUTED = (140, 150, 170)
ACCENT = (255, 196, 61)
SNAKE_HEAD = (90, 230, 160)
SNAKE_BODY = (60, 190, 130)
FOOD = (235, 90, 100)
BONUS = (180, 120, 255)
GRID_LINE = (28, 34, 46)

HIGHSCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snake_highscore.json")

DIFFICULTIES = {
    "Facil":   {"speed": 8,  "wall": False},
    "Normal":  {"speed": 12, "wall": False},
    "Dificil": {"speed": 17, "wall": True},
}
DIFF_ORDER = ["Facil", "Normal", "Dificil"]


# ---------- Persistencia ----------
def load_highscores():
    if not os.path.exists(HIGHSCORE_FILE):
        return {k: 0 for k in DIFF_ORDER}
    try:
        with open(HIGHSCORE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {k: int(data.get(k, 0)) for k in DIFF_ORDER}
    except Exception:
        return {k: 0 for k in DIFF_ORDER}


def save_highscores(scores):
    try:
        with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
            json.dump(scores, f)
    except Exception:
        pass


# ---------- Jogo ----------
@dataclass
class Food:
    pos: tuple
    bonus: bool = False
    ttl: int = 0  # frames restantes se bonus


class SnakeGame:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Snake - Python")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.SysFont("consolas", 44, bold=True)
        self.font_mid = pygame.font.SysFont("consolas", 24, bold=True)
        self.font_sm = pygame.font.SysFont("consolas", 18)
        self.highscores = load_highscores()
        self.difficulty = "Normal"
        self.state = "menu"  # menu | playing | paused | gameover
        self.reset()

    # ---------- Estado ----------
    def reset(self):
        cx, cy = COLS // 2, ROWS // 2
        self.snake = [(cx - 2, cy), (cx - 1, cy), (cx, cy)]
        self.direction = (1, 0)
        self.pending_dir = (1, 0)
        self.score = 0
        self.level = 1
        self.food = self._spawn_food(bonus=False)
        self.bonus = None
        self.bonus_timer = 0
        self.frame = 0

    def _spawn_food(self, bonus=False):
        occupied = set(self.snake)
        bonus_pos = getattr(self, "bonus", None)
        bonus_pos = bonus_pos.pos if bonus_pos else None
        while True:
            pos = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
            if pos not in occupied and pos != bonus_pos:
                return Food(pos=pos, bonus=bonus, ttl=90 if bonus else 0)

    def _current_speed(self):
        base = DIFFICULTIES[self.difficulty]["speed"]
        return min(base + (self.level - 1), 30)

    # ---------- Loop ----------
    def run(self):
        while True:
            self._handle_events()
            if self.state == "playing":
                self._update()
            self._draw()
            self.clock.tick(self._current_speed() if self.state == "playing" else 30)

    def _handle_events(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                save_highscores(self.highscores)
                pygame.quit()
                sys.exit(0)
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    save_highscores(self.highscores)
                    pygame.quit()
                    sys.exit(0)

                if self.state == "menu":
                    if e.key in (pygame.K_UP, pygame.K_w):
                        i = DIFF_ORDER.index(self.difficulty)
                        self.difficulty = DIFF_ORDER[(i - 1) % len(DIFF_ORDER)]
                    elif e.key in (pygame.K_DOWN, pygame.K_s):
                        i = DIFF_ORDER.index(self.difficulty)
                        self.difficulty = DIFF_ORDER[(i + 1) % len(DIFF_ORDER)]
                    elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.reset()
                        self.state = "playing"

                elif self.state == "playing":
                    if e.key in (pygame.K_UP, pygame.K_w) and self.direction != (0, 1):
                        self.pending_dir = (0, -1)
                    elif e.key in (pygame.K_DOWN, pygame.K_s) and self.direction != (0, -1):
                        self.pending_dir = (0, 1)
                    elif e.key in (pygame.K_LEFT, pygame.K_a) and self.direction != (1, 0):
                        self.pending_dir = (-1, 0)
                    elif e.key in (pygame.K_RIGHT, pygame.K_d) and self.direction != (-1, 0):
                        self.pending_dir = (1, 0)
                    elif e.key == pygame.K_p:
                        self.state = "paused"

                elif self.state == "paused":
                    if e.key == pygame.K_p or e.key == pygame.K_RETURN:
                        self.state = "playing"

                elif self.state == "gameover":
                    if e.key == pygame.K_r:
                        self.reset()
                        self.state = "playing"
                    elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self.state = "menu"

    def _update(self):
        self.direction = self.pending_dir
        hx, hy = self.snake[-1]
        dx, dy = self.direction
        nx, ny = hx + dx, hy + dy

        wall = DIFFICULTIES[self.difficulty]["wall"]
        if wall:
            if nx < 0 or nx >= COLS or ny < 0 or ny >= ROWS:
                self._die()
                return
        else:
            nx %= COLS
            ny %= ROWS

        new_head = (nx, ny)
        if new_head in self.snake:
            self._die()
            return

        self.snake.append(new_head)

        ate = False
        if new_head == self.food.pos:
            self.score += 10
            ate = True
            self.food = self._spawn_food(bonus=False)
            if self.score > 0 and self.score % 50 == 0:
                self.level += 1
            if self.bonus is None and random.random() < 0.20:
                self.bonus = self._spawn_food(bonus=True)

        if self.bonus and new_head == self.bonus.pos:
            self.score += 50
            self.bonus = None
            ate = True

        if not ate:
            self.snake.pop(0)

        if self.bonus:
            self.bonus.ttl -= 1
            if self.bonus.ttl <= 0:
                self.bonus = None

        self.frame += 1

    def _die(self):
        if self.score > self.highscores[self.difficulty]:
            self.highscores[self.difficulty] = self.score
            save_highscores(self.highscores)
        self.state = "gameover"

    # ---------- Render ----------
    def _draw(self):
        self.screen.fill(BG1)
        self._draw_board()
        self._draw_hud()

        if self.state == "menu":
            self._draw_menu()
        elif self.state == "playing":
            self._draw_food()
            self._draw_snake()
        elif self.state == "paused":
            self._draw_food()
            self._draw_snake()
            self._overlay("PAUSADO", "Pressione P para continuar")
        elif self.state == "gameover":
            self._draw_food()
            self._draw_snake()
            self._overlay(
                "GAME OVER",
                f"Pontos: {self.score}   R = reiniciar   ENTER = menu",
            )

        pygame.display.flip()

    def _draw_board(self):
        for y in range(ROWS):
            for x in range(COLS):
                r = pygame.Rect(x * CELL, HUD_H + y * CELL, CELL, CELL)
                pygame.draw.rect(self.screen, BG1 if (x + y) % 2 == 0 else BG2, r)

    def _draw_hud(self):
        pygame.draw.rect(self.screen, HUD_BG, (0, 0, WIDTH, HUD_H))
        pygame.draw.line(self.screen, GRID_LINE, (0, HUD_H), (WIDTH, HUD_H), 2)

        score_s = self.font_mid.render(f"Score {self.score:04d}", True, TEXT)
        self.screen.blit(score_s, (16, 10))

        lvl_s = self.font_sm.render(f"Nivel {self.level}", True, MUTED)
        self.screen.blit(lvl_s, (16, 36))

        diff_s = self.font_mid.render(self.difficulty.upper(), True, ACCENT)
        self.screen.blit(diff_s, (WIDTH // 2 - diff_s.get_width() // 2, 10))
        wall_txt = "Paredes: ON" if DIFFICULTIES[self.difficulty]["wall"] else "Paredes: OFF"
        wall_s = self.font_sm.render(wall_txt, True, MUTED)
        self.screen.blit(wall_s, (WIDTH // 2 - wall_s.get_width() // 2, 36))

        hs = self.highscores[self.difficulty]
        hs_s = self.font_mid.render(f"Best {hs:04d}", True, TEXT)
        self.screen.blit(hs_s, (WIDTH - hs_s.get_width() - 16, 10))
        hint_s = self.font_sm.render("P pausa  ESC sair", True, MUTED)
        self.screen.blit(hint_s, (WIDTH - hint_s.get_width() - 16, 36))

    def _draw_snake(self):
        for i, (x, y) in enumerate(self.snake):
            r = pygame.Rect(x * CELL + 1, HUD_H + y * CELL + 1, CELL - 2, CELL - 2)
            color = SNAKE_HEAD if i == len(self.snake) - 1 else SNAKE_BODY
            pygame.draw.rect(self.screen, color, r, border_radius=6)
            if i == len(self.snake) - 1:
                # olhos
                dx, dy = self.direction
                cx = x * CELL + CELL // 2
                cy = HUD_H + y * CELL + CELL // 2
                ox, oy = dy * 4, -dx * 4  # perpendicular
                for sx, sy in ((ox, oy), (-ox, -oy)):
                    pygame.draw.circle(self.screen, (20, 20, 30), (cx + dx * 4 + sx, cy + dy * 4 + sy), 3)

    def _draw_food(self):
        if self.food:
            x, y = self.food.pos
            cx = x * CELL + CELL // 2
            cy = HUD_H + y * CELL + CELL // 2
            pygame.draw.circle(self.screen, FOOD, (cx, cy), CELL // 2 - 3)
        if self.bonus:
            x, y = self.bonus.pos
            r = pygame.Rect(x * CELL + 3, HUD_H + y * CELL + 3, CELL - 6, CELL - 6)
            # pisca conforme ttl
            if self.bonus.ttl > 20 or (self.frame // 4) % 2 == 0:
                pygame.draw.rect(self.screen, BONUS, r, border_radius=4)

    def _draw_menu(self):
        title = self.font_big.render("SNAKE", True, ACCENT)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, HUD_H + 40))

        sub = self.font_sm.render("100% Python  -  use SETAS / WASD", True, MUTED)
        self.screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, HUD_H + 100))

        base_y = HUD_H + 170
        header = self.font_mid.render("Dificuldade", True, TEXT)
        self.screen.blit(header, (WIDTH // 2 - header.get_width() // 2, base_y))

        for i, d in enumerate(DIFF_ORDER):
            selected = d == self.difficulty
            label = f"> {d} <" if selected else f"  {d}  "
            color = ACCENT if selected else MUTED
            surf = self.font_mid.render(label, True, color)
            self.screen.blit(surf, (WIDTH // 2 - surf.get_width() // 2, base_y + 40 + i * 34))
            hs = self.highscores[d]
            hs_surf = self.font_sm.render(f"best {hs}", True, MUTED)
            self.screen.blit(hs_surf, (WIDTH // 2 + 90, base_y + 46 + i * 34))

        tip = self.font_sm.render("ENTER para iniciar    UP/DOWN muda dificuldade", True, TEXT)
        self.screen.blit(tip, (WIDTH // 2 - tip.get_width() // 2, HEIGHT - 40))

    def _overlay(self, title, subtitle):
        s = pygame.Surface((WIDTH, HEIGHT - HUD_H), pygame.SRCALPHA)
        s.fill((0, 0, 0, 160))
        self.screen.blit(s, (0, HUD_H))
        t = self.font_big.render(title, True, ACCENT)
        self.screen.blit(t, (WIDTH // 2 - t.get_width() // 2, HEIGHT // 2 - 40))
        sub = self.font_sm.render(subtitle, True, TEXT)
        self.screen.blit(sub, (WIDTH // 2 - sub.get_width() // 2, HEIGHT // 2 + 20))


def main():
    SnakeGame().run()


if __name__ == "__main__":
    main()
