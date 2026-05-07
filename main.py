import pygame
import sys
import random
import math
import os

pygame.init()
pygame.mixer.init()

WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("The Peephole - Entity Edition")
clock = pygame.time.Clock()

# --- DATA HANTERING ---
def load_data():
    if os.path.exists("data.txt"):
        with open("data.txt", "r") as f:
            try:
                values = f.read().split(",")
                return [int(x) for x in values]
            except:
                return [0, 0, 0, 0, 0]
    return [0, 0, 0, 0, 0]

def save_data(data):
    with open("data.txt", "w") as f:
        data_string = ",".join(str(x) for x in data)
        f.write(data_string)

game_data = load_data()

# --- RESURS HANTERING ---
def load_image(path, size=None):
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            if size:
                return pygame.transform.smoothscale(img, size)
            return img
        except:
            return None
    return None

def load_sound(path):
    if os.path.exists(path):
        return pygame.mixer.Sound(path)
    return None

img_menu_bg = load_image("assets/bakgrund.png", (WIDTH, HEIGHT))
img_p1_raw = load_image("assets/Neighbours/Person1.png")
img_p2_raw = load_image("assets/Neighbours/Person2.png")
img_p1_peephole = load_image("assets/Neighbours/Person1.png", (150, 250))
img_p2_peephole = load_image("assets/Neighbours/Person2.png", (180, 280))
img_computer = load_image("assets/computer.png", (220, 160))

snd_knock_calm = load_sound("assets/sfx/Calm knock.mp3")
snd_knock_loud = load_sound("assets/sfx/Banging.mp3")
snd_jumpscare1 = load_sound("assets/sfx/Jumpscare1.mp3")
snd_jumpscare2 = load_sound("assets/sfx/Jumpscare2.mp3")

# --- FÄRGER OCH FONTER ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (180, 0, 0)
GREEN = (0, 255, 0)
GREY = (40, 40, 40)
DARK_GREY = (60, 60, 60)
LIGHT_GREY = (150, 150, 150)
GOLD = (255, 215, 0)
YELLOW = (255, 255, 200)

font_menu = pygame.font.SysFont("courier new", 30, bold=True)
font_small = pygame.font.SysFont("courier new", 16, bold=True)
font_clock = pygame.font.SysFont("courier new", 40, bold=True)

# --- SPELVARIABLER ---
scene = "menu"
power_level = 100.0
visitor_outside = False
visitor_type = 1
visitor_timer = 0
stare_timer = 0
game_state = "playing"
jumpscare_played = False
death_time_start = 0
death_reason = ""
charge_flash = 0

game_hour = 9
game_minute = 0
game_period = "PM"
last_minute_tick = 0 
MINUTE_DURATION = 1000 

comp_x = 115
comp_y = 260
charge_btn_rect = pygame.Rect(comp_x + 75, comp_y + 45, 70, 25)

def reset_game():
    global power_level, visitor_outside, visitor_timer, stare_timer, game_state
    global jumpscare_played, scene, death_reason, game_hour, game_minute, last_minute_tick, game_period
    power_level = 100.0
    visitor_outside = False
    visitor_timer = 0
    stare_timer = 0
    game_state = "playing"
    jumpscare_played = False
    scene = "room"
    death_reason = ""
    game_hour = 9
    game_minute = 0
    game_period = "PM"
    last_minute_tick = pygame.time.get_ticks()

def get_total_minutes():
    # Räknar minuter passerade sedan kl 21:00
    if game_period == "PM":
        return (game_hour - 9) * 60 + game_minute
    else: # För 12:00 AM (Midnatt)
        return (12 - 9) * 60 + game_minute

def draw_room():
    global charge_flash
    bg_brightness = max(5, int(power_level / 5))
    screen.fill((bg_brightness, bg_brightness, bg_brightness + 10))

    # --- FÖNSTER ---
    win_x, win_y, win_w, win_h = 50, 100, 120, 160
    total_mins = get_total_minutes()
    
    # Natthimmel
    sky_r, sky_g, sky_b = 5, 5, 15
    pygame.draw.rect(screen, (sky_r, sky_g, sky_b), (win_x, win_y, win_w, win_h))

    # Månen (Startar synligt och rör sig sakta)
    moon_x = win_x + 35 + (total_mins * 0.15)
    moon_y = (win_y + 70) - (total_mins * 0.1)
    
    # Rita månen om den är inom ramarna
    if win_x + 5 < moon_x < win_x + win_w - 5:
        pygame.draw.circle(screen, (220, 220, 255), (int(moon_x), int(moon_y)), 12)
        pygame.draw.circle(screen, (sky_r, sky_g, sky_b), (int(moon_x + 8), int(moon_y)), 12)

    # Fönsterkarm
    pygame.draw.rect(screen, (40, 40, 45), (win_x, win_y, win_w, win_h), 5)
    pygame.draw.line(screen, (40, 40, 45), (win_x + 60, win_y), (win_x + 60, win_y + win_h), 2)
    pygame.draw.line(screen, (40, 40, 45), (win_x, win_y + 80), (win_x + win_w, win_y + 80), 2)

    # --- LAMPA OCH LJUS ---
    lamp_x, lamp_y = WIDTH // 2, 40
    if power_level > 0:
        glow_intensity = max(0, int(power_level * 0.8))
        for i in range(10):
            glow_radius = 150 + (i * 20)
            glow_alpha = max(0, (glow_intensity // 10) - (i * 2))
            glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 255, 150, glow_alpha), (glow_radius, glow_radius), glow_radius)
            screen.blit(glow_surf, (lamp_x - glow_radius, lamp_y - glow_radius))
        pygame.draw.rect(screen, GREY, (lamp_x - 5, 0, 10, 30))
        pygame.draw.circle(screen, YELLOW, (lamp_x, lamp_y), 15)
    
    # Inredning
    pygame.draw.rect(screen, (15, 15, 15), (0, 450, WIDTH, 150)) # Golv
    door_rect = pygame.Rect(600, 180, 110, 280)
    pygame.draw.rect(screen, (30, 15, 5), door_rect)
    pygame.draw.circle(screen, (120, 110, 0), (615, 320), 6)
    
    pygame.draw.rect(screen, (35, 25, 20), (100, 420, 250, 30)) # Bord
    pygame.draw.rect(screen, (25, 15, 10), (120, 450, 15, 50)) 
    pygame.draw.rect(screen, (315, 450, 15, 50)) 
    
    if img_computer:
        screen.blit(img_computer, (comp_x, comp_y))
    else:
        pygame.draw.rect(screen, (20, 20, 20), (comp_x + 20, comp_y, 180, 130))
    
    # Knapp och batteri
    btn_col = GREEN if charge_flash > 0 else DARK_GREY
    if charge_flash > 0: charge_flash -= 1
    pygame.draw.rect(screen, btn_col, charge_btn_rect, border_radius=3)
    btn_txt = font_small.render("CHARGE", True, WHITE)
    screen.blit(btn_txt, (charge_btn_rect.centerx - btn_txt.get_width()//2, charge_btn_rect.centery - btn_txt.get_height()//2))
    
    p_color = GREEN if power_level > 30 else RED
    pygame.draw.rect(screen, BLACK, (charge_btn_rect.x, charge_btn_rect.bottom + 5, 70, 10))
    pygame.draw.rect(screen, p_color, (charge_btn_rect.x, charge_btn_rect.bottom + 5, int(70 * (power_level/100)), 10))

    # Klocka
    time_str = f"{game_hour:02}:{game_minute:02} {game_period}"
    clock_txt = font_clock.render(time_str, True, WHITE)
    screen.blit(clock_txt, (WIDTH - 220, 30))

def draw_peephole():
    screen.fill(BLACK)
    pygame.draw.circle(screen, (35, 35, 40), (WIDTH//2, HEIGHT//2), 200)
    if visitor_outside:
        img = img_p1_peephole if visitor_type == 1 else img_p2_peephole
        if img: screen.blit(img, (WIDTH//2 - img.get_width()//2, HEIGHT//2 - img.get_height()//2))
    for i in range(200, 500, 10): 
        pygame.draw.circle(screen, BLACK, (WIDTH//2, HEIGHT//2), i, 15)
    time_str = f"{game_hour:02}:{game_minute:02} {game_period}"
    clock_txt = font_clock.render(time_str, True, WHITE)
    screen.blit(clock_txt, (WIDTH - 220, 30))

# --- HUVUDLOOP ---
while True:
    current_time = pygame.time.get_ticks()
    mx, my = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            if scene == "menu":
                if pygame.Rect(WIDTH//2-125, 200, 250, 50).collidepoint(mx, my): reset_game()
                if pygame.Rect(WIDTH//2-125, 270, 250, 50).collidepoint(mx, my): scene = "achievements"
                if pygame.Rect(WIDTH//2-125, 340, 250, 50).collidepoint(mx, my): pygame.quit(); sys.exit()
            elif scene == "room" and game_state == "playing":
                if charge_btn_rect.collidepoint(mx, my):
                    power_level = min(100, power_level + 10)
                    charge_flash = 5
                    if not visitor_outside and random.random() < 0.05:
                        visitor_outside, visitor_type = True, random.choice([1, 2])
                        visitor_timer, stare_timer = 0, 0
                        s = snd_knock_calm if visitor_type == 1 else snd_knock_loud
                        if s: s.play()
                if 600 < mx < 710 and 180 < my < 460: scene = "peephole"
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if scene == "peephole": scene = "room"
            elif scene in ["achievements", "win"]: scene = "menu"

    if scene not in ["menu", "achievements", "win"] and game_state == "playing":
        power_level -= 0.08 
        if power_level <= 0: 
            game_state, death_time_start, death_reason = "lost", current_time, "power"
            game_data[1] += 1; save_data(game_data)

        if current_time - last_minute_tick >= MINUTE_DURATION:
            game_minute += 1
            last_minute_tick = current_time
            if game_minute >= 60:
                game_minute = 0
                if game_hour == 11:
                    game_period = "AM"
                    game_hour = 12
                    # VINST VID MIDNATT
                    scene = "win"
                    game_data[0] += 1; game_data[2] = 1; save_data(game_data)
                elif game_hour == 12:
                    game_hour = 1
                else:
                    game_hour += 1

        if visitor_outside:
            if scene == "peephole":
                if visitor_type == 1:
                    stare_timer += 1
                    if stare_timer >= 120: visitor_outside = False
                else: 
                    game_state, death_time_start, death_reason = "lost", current_time, "monster2"
                    game_data[1] += 1; save_data(game_data)
            else:
                visitor_timer += 1
                if visitor_type == 2 and visitor_timer > 400: visitor_outside = False
            if visitor_timer > 550: 
                game_state, death_time_start, death_reason = "lost", current_time, f"monster{visitor_type}"
                game_data[1] += 1; save_data(game_data)

    # Rendering
    if scene == "menu":
        if img_menu_bg: screen.blit(img_menu_bg, (0, 0))
        else: screen.fill(BLACK)
        for i, text in enumerate(["START", "ACHIEVEMENTS", "CLOSE"]):
            rect = pygame.Rect(WIDTH//2 - 125, 200 + i*70, 250, 50)
            pygame.draw.rect(screen, (100, 0, 0) if rect.collidepoint(mx, my) else GREY, rect, border_radius=5)
            t = font_menu.render(text, True, WHITE)
            screen.blit(t, (rect.centerx - t.get_width()//2, rect.centery - t.get_height()//2))
    elif scene == "win":
        screen.fill(BLACK)
        t = font_menu.render("MIDNIGHT - YOU SURVIVED", True, GREEN)
        screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2))
    elif game_state == "playing":
        draw_room() if scene == "room" else draw_peephole()
    elif game_state == "lost":
        elapsed = current_time - death_time_start
        if elapsed < 2500:
            if not jumpscare_played:
                s = snd_jumpscare1 if "1" in death_reason or "power" in death_reason else snd_jumpscare2
                if s: s.play(); jumpscare_played = True
            shake_x, shake_y = random.randint(-15, 15), random.randint(-15, 15)
            screen.fill((random.randint(0,20), 0, 0)) 
            img = img_p1_raw if ("1" in death_reason or "power" in death_reason) else img_p2_raw
            if img: screen.blit(pygame.transform.smoothscale(img, (WIDTH + 40, HEIGHT + 40)), (-20 + shake_x, -20 + shake_y))
        else: scene, game_state = "menu", "playing"

    pygame.display.flip()
    clock.tick(60)