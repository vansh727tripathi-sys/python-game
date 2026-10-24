"""
Ultra-Vibrant Arcade Snake in Python
High-performance graphics using Python's native Tkinter Canvas.
Zero pip dependencies required!
"""

import tkinter as tk
import random
import math
import time
import colorsys
import threading
import sys

# Platform-specific audio (Windows winsound)
try:
    import winsound
    SOUND_AVAILABLE = True
except ImportError:
    SOUND_AVAILABLE = False


def play_sound(sound_type: str, combo: int = 1, sound_enabled: bool = True):
    """Plays non-blocking 8-bit sound effects in a daemon thread."""
    if not SOUND_AVAILABLE or not sound_enabled:
        return

    def _worker():
        try:
            if sound_type == "eat":
                freq = min(1800, 520 + combo * 90)
                winsound.Beep(freq, 45)
            elif sound_type == "star":
                winsound.Beep(1100, 60)
                winsound.Beep(1450, 75)
            elif sound_type == "gem":
                winsound.Beep(1350, 50)
                winsound.Beep(1800, 90)
            elif sound_type == "game_over":
                winsound.Beep(450, 100)
                winsound.Beep(320, 140)
                winsound.Beep(220, 260)
            elif sound_type == "theme":
                winsound.Beep(850, 40)
        except Exception:
            pass

    threading.Thread(target=_worker, daemon=True).start()


def hsv_to_hex(h: float, s: float, v: float) -> str:
    """Converts normalized HSV (0.0-1.0) into a hex color string."""
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


# Color palettes for visual themes
THEMES = {
    "Rainbow Galaxy": {
        "bg": "#0B0C1A",
        "grid": "#151833",
        "border_outer": "#7C3AED",
        "border_inner": "#06B6D4",
        "hud_bg": "#12142B",
        "hud_border": "#282C5E",
        "star_color": "#E2E8F0",
        "mode": "rainbow",
    },
    "Cyberpunk 2099": {
        "bg": "#0B0B14",
        "grid": "#1D122E",
        "border_outer": "#EC4899",
        "border_inner": "#06B6D4",
        "hud_bg": "#151128",
        "hud_border": "#3B1B54",
        "star_color": "#F472B6",
        "mode": "cyber",
        "head_color": "#06B6D4",
        "colors": ["#EC4899", "#D946EF", "#8B5CF6", "#3B82F6", "#06B6D4"],
    },
    "Candy Kingdom": {
        "bg": "#181024",
        "grid": "#2D1B40",
        "border_outer": "#FB7185",
        "border_inner": "#34D399",
        "hud_bg": "#221333",
        "hud_border": "#4C266E",
        "star_color": "#FDE047",
        "mode": "candy",
        "head_color": "#FB7185",
        "colors": ["#F472B6", "#FB923C", "#FBBF24", "#34D399", "#38BDF8", "#A78BFA"],
    },
    "Emerald Matrix": {
        "bg": "#040D07",
        "grid": "#0B2614",
        "border_outer": "#10B981",
        "border_inner": "#4ADE80",
        "hud_bg": "#07170C",
        "hud_border": "#134221",
        "star_color": "#86EFAC",
        "mode": "matrix",
        "head_color": "#4ADE80",
        "colors": ["#86EFAC", "#4ADE80", "#22C55E", "#16A34A", "#15803D", "#14532D"],
    },
}


class Particle:
    """Animated explosion particle."""
    def __init__(self, x: float, y: float, color: str, p_type: str = "spark"):
        self.x = x
        self.y = y
        self.color = color
        self.p_type = p_type
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1.8, 6.5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.radius = random.uniform(2.5, 5.0)
        self.life = random.randint(18, 30)
        self.max_life = self.life

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.93
        self.vy *= 0.93
        self.radius = max(0.6, self.radius * 0.94)
        self.life -= 1


class FloatingText:
    """Floating score / combo pop-up animation."""
    def __init__(self, text: str, x: float, y: float, color: str, size: int = 12):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.life = 28

    def update(self):
        self.y -= 1.6
        self.life -= 1


class SnakeGame:
    def __init__(self):
        # Window & Canvas Dimensions
        self.win_width = 720
        self.win_height = 800
        self.hud_height = 80

        # Grid configuration
        self.cell_size = 20
        self.grid_cols = 33
        self.grid_rows = 33
        self.play_left = 30
        self.play_top = self.hud_height + 20
        self.play_width = self.grid_cols * self.cell_size
        self.play_height = self.grid_rows * self.cell_size
        self.play_right = self.play_left + self.play_width
        self.play_bottom = self.play_top + self.play_height

        # Initialize Tkinter Window
        self.root = tk.Tk()
        self.root.title("Neon Cyber Snake - Deluxe Arcade Edition")
        self.root.geometry(f"{self.win_width}x{self.win_height}")
        self.root.resizable(False, False)
        self.root.configure(bg="#0B0C1A")

        # Main Canvas
        self.canvas = tk.Canvas(
            self.root,
            width=self.win_width,
            height=self.win_height,
            bg="#0B0C1A",
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        # Game State
        self.score = 0
        self.high_score = 0
        self.game_over = False
        self.is_paused = False
        self.sound_enabled = True

        # Snake state: list of (col, row) coordinates
        self.snake = []
        self.direction = "RIGHT"
        self.next_direction = "RIGHT"

        # Speed configuration (higher ms = slower, easier starting control)
        self.base_speed = 150  # 150ms starting speed for smooth, relaxed control
        self.speed_ms = self.base_speed

        # Combo & Multiplier System
        self.combo = 0
        self.combo_timer = 0
        self.combo_max_time = 3.5

        # Visual FX & Themes
        self.theme_names = list(THEMES.keys())
        self.theme_index = 0
        self.theme = THEMES[self.theme_names[self.theme_index]]
        self.frame_count = 0
        self.rainbow_hue = 0.0
        self.shake_frames = 0

        # Collectibles
        self.food = (0, 0)
        self.foods_eaten = 0
        self.star_active = False
        self.star_pos = (0, 0)
        self.star_expire_time = 0
        self.gem_active = False
        self.gem_pos = (0, 0)
        self.gem_expire_time = 0

        # FX Systems
        self.particles: list[Particle] = []
        self.float_texts: list[FloatingText] = []

        # Twinkling Background Stars
        self.bg_stars = [
            (
                random.randint(self.play_left + 10, self.play_right - 10),
                random.randint(self.play_top + 10, self.play_bottom - 10),
                random.uniform(0.8, 2.2),
                random.uniform(0, math.pi * 2),
            )
            for _ in range(40)
        ]

        # Key Bindings
        self._bind_keys()
        self.root.protocol("WM_DELETE_WINDOW", self.quit_game)

        # Reset & Start Game Loops
        self.reset_game()
        self.game_tick()     # Snake movement loop (~95ms)
        self.render_loop()   # 60 FPS animation loop (16ms)

    def _bind_keys(self):
        """Set up all keyboard listeners."""
        self.root.bind("<Up>", lambda e: self.set_direction("UP"))
        self.root.bind("<Down>", lambda e: self.set_direction("DOWN"))
        self.root.bind("<Left>", lambda e: self.set_direction("LEFT"))
        self.root.bind("<Right>", lambda e: self.set_direction("RIGHT"))

        self.root.bind("<w>", lambda e: self.set_direction("UP"))
        self.root.bind("<W>", lambda e: self.set_direction("UP"))
        self.root.bind("<s>", lambda e: self.set_direction("DOWN"))
        self.root.bind("<S>", lambda e: self.set_direction("DOWN"))
        self.root.bind("<a>", lambda e: self.set_direction("LEFT"))
        self.root.bind("<A>", lambda e: self.set_direction("LEFT"))
        self.root.bind("<d>", lambda e: self.set_direction("RIGHT"))
        self.root.bind("<D>", lambda e: self.set_direction("RIGHT"))

        self.root.bind("<space>", lambda e: self.toggle_pause())
        self.root.bind("<p>", lambda e: self.toggle_pause())
        self.root.bind("<P>", lambda e: self.toggle_pause())

        self.root.bind("<r>", lambda e: self.reset_game())
        self.root.bind("<R>", lambda e: self.reset_game())

        self.root.bind("<t>", lambda e: self.cycle_theme())
        self.root.bind("<T>", lambda e: self.cycle_theme())

        self.root.bind("<m>", lambda e: self.toggle_sound())
        self.root.bind("<M>", lambda e: self.toggle_sound())

        self.root.bind("<Escape>", lambda e: self.quit_game())
        self.root.bind("<q>", lambda e: self.quit_game())
        self.root.bind("<Q>", lambda e: self.quit_game())

    def set_direction(self, new_dir: str):
        """Changes the snake's direction, preventing 180-degree self-collisions."""
        opposites = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}
        if self.game_over or self.is_paused:
            return
        if opposites.get(new_dir) != self.direction:
            self.next_direction = new_dir

    def toggle_pause(self):
        if not self.game_over:
            self.is_paused = not self.is_paused

    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        state = "ON" if self.sound_enabled else "MUTED"
        self.float_texts.append(
            FloatingText(f"Sound {state}", self.win_width // 2, self.hud_height + 50, "#38BDF8", 14)
        )

    def cycle_theme(self):
        """Switches through vibrant color themes dynamically."""
        self.theme_index = (self.theme_index + 1) % len(self.theme_names)
        self.theme = THEMES[self.theme_names[self.theme_index]]
        self.canvas.configure(bg=self.theme["bg"])
        self.root.configure(bg=self.theme["bg"])
        play_sound("theme", sound_enabled=self.sound_enabled)
        self.float_texts.append(
            FloatingText(
                f"Theme: {self.theme_names[self.theme_index]}",
                self.win_width // 2,
                self.hud_height + 40,
                "#FDE047",
                14,
            )
        )

    def quit_game(self):
        try:
            self.root.destroy()
        except Exception:
            pass
        sys.exit(0)

    def reset_game(self):
        """Initializes or restarts the game state."""
        mid_col = self.grid_cols // 2
        mid_row = self.grid_rows // 2
        self.snake = [
            (mid_col, mid_row),
            (mid_col - 1, mid_row),
            (mid_col - 2, mid_row),
            (mid_col - 3, mid_row),
        ]
        self.direction = "RIGHT"
        self.next_direction = "RIGHT"
        self.score = 0
        self.combo = 0
        self.combo_timer = 0
        self.foods_eaten = 0
        self.speed_ms = self.base_speed
        self.star_active = False
        self.gem_active = False
        self.game_over = False
        self.is_paused = False
        self.particles.clear()
        self.float_texts.clear()
        self.spawn_food()

    def get_empty_cell(self) -> tuple[int, int]:
        """Finds a random unoccupied grid coordinate."""
        occupied = set(self.snake)
        if self.star_active:
            occupied.add(self.star_pos)
        if self.gem_active:
            occupied.add(self.gem_pos)

        while True:
            c = random.randint(0, self.grid_cols - 1)
            r = random.randint(0, self.grid_rows - 1)
            if (c, r) not in occupied:
                return (c, r)

    def spawn_food(self):
        self.food = self.get_empty_cell()

    def spawn_star(self):
        self.star_pos = self.get_empty_cell()
        self.star_active = True
        self.star_expire_time = time.time() + 7.0  # 7 seconds lifetime

    def spawn_gem(self):
        self.gem_pos = self.get_empty_cell()
        self.gem_active = True
        self.gem_expire_time = time.time() + 5.5  # 5.5 seconds lifetime

    def add_particles(self, x: float, y: float, color: str, count: int = 16):
        """Emits particle burst."""
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def colrow_to_pixel(self, col: int, row: int) -> tuple[float, float]:
        """Converts grid cell to center pixel coordinate."""
        x = self.play_left + col * self.cell_size + self.cell_size / 2
        y = self.play_top + row * self.cell_size + self.cell_size / 2
        return x, y

    def game_tick(self):
        """Discrete movement loop for the snake logic."""
        if not self.game_over and not self.is_paused:
            self.direction = self.next_direction
            head_col, head_row = self.snake[0]

            if self.direction == "UP":
                new_head = (head_col, head_row - 1)
            elif self.direction == "DOWN":
                new_head = (head_col, head_row + 1)
            elif self.direction == "LEFT":
                new_head = (head_col - 1, head_row)
            elif self.direction == "RIGHT":
                new_head = (head_col + 1, head_row)
            else:
                new_head = (head_col, head_row)

            # Check Wall Collisions
            col, row = new_head
            if col < 0 or col >= self.grid_cols or row < 0 or row >= self.grid_rows:
                self.trigger_game_over()
                self.root.after(self.speed_ms, self.game_tick)
                return

            # Check Self Collision
            if new_head in self.snake[:-1]:
                self.trigger_game_over()
                self.root.after(self.speed_ms, self.game_tick)
                return

            # Move Snake
            self.snake.insert(0, new_head)
            px, py = self.colrow_to_pixel(col, row)

            # Handle Normal Apple Food Eat
            if new_head == self.food:
                self.foods_eaten += 1
                now = time.time()
                if now - self.combo_timer < self.combo_max_time:
                    self.combo = min(8, self.combo + 1)
                else:
                    self.combo = 1
                self.combo_timer = now

                multiplier = self.combo
                gained = 10 * multiplier
                self.score += gained
                if self.score > self.high_score:
                    self.high_score = self.score

                # Visual & Sound Feedback
                play_sound("eat", combo=multiplier, sound_enabled=self.sound_enabled)
                self.add_particles(px, py, "#FF3366", count=18)
                self.add_particles(px, py, "#FBBF24", count=6)
                combo_text = f"+{gained} (x{multiplier}!)" if multiplier > 1 else f"+{gained}"
                self.float_texts.append(FloatingText(combo_text, px, py - 10, "#4ADE80", 13))

                # Gradual speed increase as score grows
                self.speed_ms = max(60, int(self.base_speed * (0.985 ** min(35, self.foods_eaten))))

                # Spawn new food
                self.spawn_food()

                # Chance to spawn bonus Star (every 4 foods)
                if self.foods_eaten % 4 == 0 and not self.star_active:
                    self.spawn_star()

                # Rare Gem spawn on high combos
                if self.combo >= 3 and not self.gem_active and random.random() < 0.6:
                    self.spawn_gem()

            # Handle Golden Star Eat
            elif self.star_active and new_head == self.star_pos:
                play_sound("star", sound_enabled=self.sound_enabled)
                star_points = 50 * max(1, self.combo)
                self.score += star_points
                if self.score > self.high_score:
                    self.high_score = self.score
                self.add_particles(px, py, "#FDE047", count=28)
                self.add_particles(px, py, "#FFFFFF", count=10)
                self.float_texts.append(FloatingText(f"★ SUPER STAR +{star_points}!", px, py - 15, "#FBBF24", 15))
                self.star_active = False

            # Handle Diamond Gem Eat
            elif self.gem_active and new_head == self.gem_pos:
                play_sound("gem", sound_enabled=self.sound_enabled)
                gem_points = 100
                self.score += gem_points
                if self.score > self.high_score:
                    self.high_score = self.score
                self.add_particles(px, py, "#00F0FF", count=30)
                self.add_particles(px, py, "#38BDF8", count=12)
                self.float_texts.append(FloatingText(f"💎 GEM +{gem_points}!", px, py - 15, "#38BDF8", 16))
                self.gem_active = False

            else:
                # Normal move, remove tail
                self.snake.pop()

        self.root.after(self.speed_ms, self.game_tick)

    def trigger_game_over(self):
        """Visual & audio impact for game over."""
        self.game_over = True
        self.shake_frames = 12
        head_px, head_py = self.colrow_to_pixel(self.snake[0][0], self.snake[0][1])
        self.add_particles(head_px, head_py, "#EF4444", count=35)
        self.add_particles(head_px, head_py, "#F59E0B", count=20)
        self.add_particles(head_px, head_py, "#FFFFFF", count=15)
        play_sound("game_over", sound_enabled=self.sound_enabled)

    # =========================================================================
    # RENDER ENGINE (Smooth 60 FPS)
    # =========================================================================
    def render_loop(self):
        """Continuous high-framerate rendering loop."""
        self.frame_count += 1
        self.rainbow_hue = (self.rainbow_hue + 0.008) % 1.0

        # Expire Star / Gem if time ran out
        now = time.time()
        if self.star_active and now > self.star_expire_time:
            self.star_active = False
        if self.gem_active and now > self.gem_expire_time:
            self.gem_active = False

        # Clear Canvas
        self.canvas.delete("all")

        # Screen Shake calculation
        shake_dx, shake_dy = 0, 0
        if self.shake_frames > 0:
            shake_dx = random.randint(-4, 4)
            shake_dy = random.randint(-4, 4)
            self.shake_frames -= 1

        # Draw Layers
        self._draw_background(shake_dx, shake_dy)
        self._draw_grid_and_border(shake_dx, shake_dy)
        self._draw_collectibles(shake_dx, shake_dy)
        self._draw_snake(shake_dx, shake_dy)
        self._draw_particles(shake_dx, shake_dy)
        self._draw_floating_text(shake_dx, shake_dy)
        self._draw_hud()

        if self.is_paused:
            self._draw_overlay("PAUSED", "Press [SPACE] or [P] to Resume", "#FBBF24")
        elif self.game_over:
            self._draw_overlay("GAME OVER", "Press [R] to Restart  |  [T] to Switch Theme", "#EF4444")

        # 60 FPS update (16 milliseconds)
        self.root.after(16, self.render_loop)

    def _draw_background(self, dx: int, dy: int):
        """Draws starry background with pulsating cosmic dust."""
        # Twinkling stars
        for sx, sy, radius, phase in self.bg_stars:
            pulse = (math.sin(self.frame_count * 0.08 + phase) + 1) / 2
            r = radius * (0.6 + 0.6 * pulse)
            c = self.theme["star_color"]
            self.canvas.create_oval(
                sx + dx - r, sy + dy - r, sx + dx + r, sy + dy + r,
                fill=c, outline=""
            )

    def _draw_grid_and_border(self, dx: int, dy: int):
        """Draws retro cyberpunk neon grid and double glowing borders."""
        grid_col = self.theme["grid"]
        # Subtle Grid Lines
        for c in range(0, self.grid_cols + 1, 2):
            x = self.play_left + c * self.cell_size + dx
            self.canvas.create_line(x, self.play_top + dy, x, self.play_bottom + dy, fill=grid_col, width=1)
        for r in range(0, self.grid_rows + 1, 2):
            y = self.play_top + r * self.cell_size + dy
            self.canvas.create_line(self.play_left + dx, y, self.play_right + dx, y, fill=grid_col, width=1)

        # Outer Neon Glow Border
        b_out = self.theme["border_outer"]
        b_in = self.theme["border_inner"]
        self.canvas.create_rectangle(
            self.play_left - 4 + dx, self.play_top - 4 + dy,
            self.play_right + 4 + dx, self.play_bottom + 4 + dy,
            outline=b_out, width=4
        )
        self.canvas.create_rectangle(
            self.play_left - 1 + dx, self.play_top - 1 + dy,
            self.play_right + 1 + dx, self.play_bottom + 1 + dy,
            outline=b_in, width=2
        )

        # Glowing corner accent markers
        accent_len = 16
        pts = [
            (self.play_left + dx, self.play_top + dy, 1, 1),
            (self.play_right + dx, self.play_top + dy, -1, 1),
            (self.play_left + dx, self.play_bottom + dy, 1, -1),
            (self.play_right + dx, self.play_bottom + dy, -1, -1),
        ]
        for cx, cy, dir_x, dir_y in pts:
            self.canvas.create_line(cx, cy, cx + dir_x * accent_len, cy, fill="#FFFFFF", width=3)
            self.canvas.create_line(cx, cy, cx, cy + dir_y * accent_len, fill="#FFFFFF", width=3)

    def _draw_collectibles(self, dx: int, dy: int):
        """Renders rich vector food items (Apple, Star, Gem)."""
        pulse = math.sin(self.frame_count * 0.16)

        # 1. 🍎 DELUXE RED APPLE
        fx, fy = self.colrow_to_pixel(self.food[0], self.food[1])
        fx += dx
        fy += dy

        # Glow halo
        glow_r = 13 + pulse * 2.5
        self.canvas.create_oval(
            fx - glow_r, fy - glow_r, fx + glow_r, fy + glow_r,
            outline="#F43F5E", width=1
        )
        # Apple Body
        self.canvas.create_oval(fx - 8, fy - 6, fx + 8, fy + 9, fill="#FF1E56", outline="#E11D48", width=1.5)
        # White Shine Reflection
        self.canvas.create_oval(fx - 5, fy - 4, fx - 1, fy, fill="#FFA8BE", outline="")
        # Wooden Stem
        self.canvas.create_line(fx, fy - 6, fx + 2, fy - 12, fill="#78350F", width=2)
        # Vibrant Green Leaf
        self.canvas.create_polygon(
            [fx + 2, fy - 11, fx + 8, fy - 13, fx + 6, fy - 8],
            fill="#22C55E", outline=""
        )

        # 2. ⭐ SUPER GOLDEN STAR
        if self.star_active:
            sx, sy = self.colrow_to_pixel(self.star_pos[0], self.star_pos[1])
            sx += dx
            sy += dy
            star_rot = self.frame_count * 0.05
            r_out = 12 + pulse * 2
            r_in = 5 + pulse * 1

            # Outer aura ring
            self.canvas.create_oval(
                sx - r_out - 4, sy - r_out - 4, sx + r_out + 4, sy + r_out + 4,
                outline="#FBBF24", width=1
            )

            # Star 5-point polygon
            pts = []
            for i in range(10):
                angle = -math.pi / 2 + i * (math.pi / 5) + star_rot
                r = r_out if i % 2 == 0 else r_in
                pts.extend([sx + r * math.cos(angle), sy + r * math.sin(angle)])
            self.canvas.create_polygon(pts, fill="#FDE047", outline="#F59E0B", width=2)
            # Center bright spark
            self.canvas.create_oval(sx - 3, sy - 3, sx + 3, sy + 3, fill="#FFFFFF", outline="")

            # Remaining timer ring indicator
            remaining = max(0, self.star_expire_time - time.time())
            arc_extent = (remaining / 7.0) * 359
            self.canvas.create_arc(
                sx - 16, sy - 16, sx + 16, sy + 16,
                start=90, extent=arc_extent, outline="#FBBF24", width=2, style="arc"
            )

        # 3. 💎 CYAN CRYSTAL GEM
        if self.gem_active:
            gx, gy = self.colrow_to_pixel(self.gem_pos[0], self.gem_pos[1])
            gx += dx
            gy += dy
            gem_r = 10 + pulse * 1.5
            # Faceted Diamond Polygon
            diamond = [gx, gy - gem_r - 2, gx + gem_r, gy, gx, gy + gem_r + 2, gx - gem_r, gy]
            self.canvas.create_polygon(diamond, fill="#00F0FF", outline="#0284C7", width=2)
            # Inner Facet Highlights
            self.canvas.create_line(gx - gem_r, gy, gx + gem_r, gy, fill="#E0F2FE", width=1.5)
            self.canvas.create_line(gx, gy - gem_r - 2, gx, gy + gem_r + 2, fill="#E0F2FE", width=1.5)
            self.canvas.create_oval(gx - 2, gy - 2, gx + 2, gy + 2, fill="#FFFFFF", outline="")

    def _draw_snake(self, dx: int, dy: int):
        """Renders snake with dynamic rainbow gradients, 3D highlights, expressive eyes, and animated tongue."""
        mode = self.theme["mode"]

        # Draw Body Segments (from tail to neck)
        n = len(self.snake)
        for i in range(n - 1, 0, -1):
            col, row = self.snake[i]
            cx, cy = self.colrow_to_pixel(col, row)
            cx += dx
            cy += dy

            # Determine Segment Color
            if mode == "rainbow":
                # Fluid rainbow wave along snake body
                seg_hue = (self.rainbow_hue + i * 0.035) % 1.0
                seg_col = hsv_to_hex(seg_hue, 0.88, 1.0)
            elif mode == "cyber":
                palette = self.theme["colors"]
                seg_col = palette[i % len(palette)]
            elif mode == "candy":
                palette = self.theme["colors"]
                seg_col = palette[i % len(palette)]
            elif mode == "matrix":
                palette = self.theme["colors"]
                seg_col = palette[i % len(palette)]
            else:
                seg_col = "#22C55E"

            # Segment Radius (slight tapering near tail for sleek look)
            seg_r = 8.5
            if i > n - 4:
                seg_r = max(5.0, seg_r - (i - (n - 4)) * 1.0)

            # Draw outer segment with border
            self.canvas.create_oval(
                cx - seg_r, cy - seg_r, cx + seg_r, cy + seg_r,
                fill=seg_col, outline="#FFFFFF", width=1 if i % 2 == 0 else 0
            )
            # 3D Gloss / Shine Bubble (creates glassy, candy-like depth)
            self.canvas.create_oval(
                cx - seg_r * 0.55, cy - seg_r * 0.55,
                cx - seg_r * 0.1, cy - seg_r * 0.1,
                fill="#FFFFFF", outline=""
            )

        # Draw Head
        h_col, h_row = self.snake[0]
        hx, hy = self.colrow_to_pixel(h_col, h_row)
        hx += dx
        hy += dy

        head_color = self.theme.get("head_color", "#00F0FF" if mode == "rainbow" else "#4ADE80")
        if mode == "rainbow":
            head_color = hsv_to_hex(self.rainbow_hue, 0.95, 1.0)

        # Head Body
        hr = 10.5
        self.canvas.create_oval(
            hx - hr, hy - hr, hx + hr, hy + hr,
            fill=head_color, outline="#FFFFFF", width=1.5
        )

        # Expressive Eyes & Directional Pupils
        eye_offset = 5.0
        pupil_offset = 2.0
        eye_r = 3.8
        pupil_r = 2.0

        if self.direction == "RIGHT":
            eye1 = (hx + 3, hy - eye_offset)
            eye2 = (hx + 3, hy + eye_offset)
            p_shift = (pupil_offset, 0)
            tongue_base = (hx + hr, hy)
            tongue_tip = (hx + hr + 8, hy)
            fork1 = (hx + hr + 11, hy - 3)
            fork2 = (hx + hr + 11, hy + 3)
        elif self.direction == "LEFT":
            eye1 = (hx - 3, hy - eye_offset)
            eye2 = (hx - 3, hy + eye_offset)
            p_shift = (-pupil_offset, 0)
            tongue_base = (hx - hr, hy)
            tongue_tip = (hx - hr - 8, hy)
            fork1 = (hx - hr - 11, hy - 3)
            fork2 = (hx - hr - 11, hy + 3)
        elif self.direction == "UP":
            eye1 = (hx - eye_offset, hy - 3)
            eye2 = (hx + eye_offset, hy - 3)
            p_shift = (0, -pupil_offset)
            tongue_base = (hx, hy - hr)
            tongue_tip = (hx, hy - hr - 8)
            fork1 = (hx - 3, hy - hr - 11)
            fork2 = (hx + 3, hy - hr - 11)
        else:  # DOWN
            eye1 = (hx - eye_offset, hy + 3)
            eye2 = (hx + eye_offset, hy + 3)
            p_shift = (0, pupil_offset)
            tongue_base = (hx, hy + hr)
            tongue_tip = (hx, hy + hr + 8)
            fork1 = (hx - 3, hy + hr + 11)
            fork2 = (hx + 3, hy + hr + 11)

        # Animated Flicking Tongue (pokes out every few frames)
        if (self.frame_count // 4) % 6 == 0 and not self.game_over:
            self.canvas.create_line(tongue_base[0], tongue_base[1], tongue_tip[0], tongue_tip[1], fill="#EF4444", width=2)
            self.canvas.create_line(tongue_tip[0], tongue_tip[1], fork1[0], fork1[1], fill="#EF4444", width=2)
            self.canvas.create_line(tongue_tip[0], tongue_tip[1], fork2[0], fork2[1], fill="#EF4444", width=2)

        # Draw Sclera (White of the eyes)
        for ex, ey in [eye1, eye2]:
            self.canvas.create_oval(ex - eye_r, ey - eye_r, ex + eye_r, ey + eye_r, fill="#FFFFFF", outline="#000000", width=1)
            # Black Pupils tracking direction
            px = ex + p_shift[0]
            py = ey + p_shift[1]
            self.canvas.create_oval(px - pupil_r, py - pupil_r, px + pupil_r, py + pupil_r, fill="#0F172A", outline="")
            # Glint
            self.canvas.create_oval(px - 1.2, py - 1.2, px, py, fill="#FFFFFF", outline="")

    def _draw_particles(self, dx: int, dy: int):
        """Updates and renders particle physics."""
        alive = []
        for p in self.particles:
            p.update()
            if p.life > 0:
                alive.append(p)
                r = p.radius
                self.canvas.create_oval(
                    p.x + dx - r, p.y + dy - r, p.x + dx + r, p.y + dy + r,
                    fill=p.color, outline=""
                )
        self.particles = alive

    def _draw_floating_text(self, dx: int, dy: int):
        """Updates and renders floating score text popups."""
        alive = []
        for ft in self.float_texts:
            ft.update()
            if ft.life > 0:
                alive.append(ft)
                self.canvas.create_text(
                    ft.x + dx, ft.y + dy,
                    text=ft.text,
                    fill=ft.color,
                    font=("Segoe UI", ft.size, "bold")
                )
        self.float_texts = alive

    def _draw_hud(self):
        """Renders modern glassmorphism arcade scoreboard and combo bar."""
        hb = self.theme["hud_bg"]
        h_border = self.theme["hud_border"]

        # Top HUD Banner Panel
        self.canvas.create_rectangle(0, 0, self.win_width, self.hud_height, fill=hb, outline=h_border, width=2)

        # 🍎 Score Display (Left)
        self.canvas.create_text(
            40, 28, text="SCORE", anchor="w",
            fill="#94A3B8", font=("Consolas", 10, "bold")
        )
        self.canvas.create_text(
            40, 52, text=f"{self.score:05d}", anchor="w",
            fill="#38BDF8", font=("Consolas", 20, "bold")
        )

        # 🔥 Combo & Multiplier (Center)
        now = time.time()
        time_left = max(0.0, self.combo_max_time - (now - self.combo_timer))
        if self.combo > 1 and time_left > 0:
            ratio = time_left / self.combo_max_time
            bar_w = 120
            bar_x = self.win_width // 2 - bar_w // 2
            bar_y = 52
            # Combo text
            self.canvas.create_text(
                self.win_width // 2, 28,
                text=f"🔥 COMBO x{self.combo}!",
                fill="#FBBF24", font=("Segoe UI", 13, "bold")
            )
            # Background meter bar
            self.canvas.create_rectangle(
                bar_x, bar_y, bar_x + bar_w, bar_y + 8,
                fill="#1E293B", outline="#475569"
            )
            # Progress fill
            fill_col = "#F59E0B" if self.combo < 4 else "#EF4444"
            self.canvas.create_rectangle(
                bar_x, bar_y, bar_x + int(bar_w * ratio), bar_y + 8,
                fill=fill_col, outline=""
            )
        else:
            # Level / Length Indicator
            length = len(self.snake)
            speed_lvl = max(1, 1 + (self.base_speed - self.speed_ms) // 10)
            self.canvas.create_text(
                self.win_width // 2, 40,
                text=f"LENGTH: {length}  |  SPEED: Level {speed_lvl}",
                fill="#64748B", font=("Consolas", 11, "bold")
            )

        # 👑 High Score (Right)
        self.canvas.create_text(
            self.win_width - 40, 28, text="HIGH SCORE", anchor="e",
            fill="#94A3B8", font=("Consolas", 10, "bold")
        )
        self.canvas.create_text(
            self.win_width - 40, 52, text=f"{self.high_score:05d}", anchor="e",
            fill="#FBBF24", font=("Consolas", 20, "bold")
        )

        # Controls & Theme Bar at the bottom
        snd_label = "🔊 ON" if self.sound_enabled else "🔇 MUTED"
        theme_name = self.theme_names[self.theme_index]
        self.canvas.create_text(
            self.win_width // 2, self.win_height - 18,
            text=f"[T] Theme: {theme_name}   |   [M] Sound: {snd_label}   |   [P] Pause   |   [R] Restart",
            fill="#64748B", font=("Consolas", 9, "bold")
        )

    def _draw_overlay(self, title: str, subtitle: str, color: str):
        """Draws semi-transparent overlay cards for Pause and Game Over."""
        cx = self.win_width // 2
        cy = self.play_top + self.play_height // 2

        # Card shadow & background
        w, h = 240, 90
        self.canvas.create_rectangle(
            cx - w, cy - h, cx + w, cy + h,
            fill="#090D16", outline=color, width=3
        )
        # Title
        self.canvas.create_text(
            cx, cy - 22, text=title,
            fill=color, font=("Consolas", 26, "bold")
        )
        # Subtitle
        self.canvas.create_text(
            cx, cy + 24, text=subtitle,
            fill="#CBD5E1", font=("Segoe UI", 11, "normal")
        )

    def run(self):
        """Starts the Tkinter GUI main event loop."""
        self.root.mainloop()


if __name__ == "__main__":
    game = SnakeGame()
    game.run()

