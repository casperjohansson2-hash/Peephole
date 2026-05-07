import pygame
import sys
import random
import math
import os

pygame.init()
pygame.mixer.init()

# --- SETTINGS ---
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("The Peephole - Entity Edition")
clock = pygame.time.Clock()

# --- DATA HANTERING ---
def load_data():
    if os.path.exists("data.txt"):
        with open("data.txt", "r") as f:
            try: return [int(x) for x in f.read().split(",")]
            except: return [0, 0, 0, 0, 0]
    return [0, 0, 0, 0, 0]

def save_data(data):
    with open("data.txt", "w") as f:
        f.write(",".join(str(x) for x in data))

game_data = load_data()

# --- ASSET LOADING ---
def load_image(path, size=None):
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            if size:
                return pygame.transform.smoothscale(img, size)
            return img
        except: return None
    return None

def load_sound(path):
    return pygame.mixer.Sound(path) if os.path.exists(path) else None

# Ladda bakgrund för menyn
img_menu_bg = load_image("assets/bakgrund.png", (WIDTH, HEIGHT))

# Ladda personer
img_p1_raw = load_image("assets/Neighbours/Person1.png")
img_p2_raw = load_image("assets/Neighbours/Person2.png")

# För kikhålet
img_p1_peephole = load_image("assets/Neighbours/Person1.png", (150, 250))
img_p2_peephole = load_image("assets/Neighbours/Person2.png", (180, 280))

# Datorn ligger direkt i assets-mappen
img_computer = load_image("assets/computer.png", (220, 160))

# SFX
snd_knock_calm = load_sound("assets/sfx/Calm knock.mp3")
snd_knock_loud = load_sound("assets/sfx/Banging.mp3")
snd_jumpscare1 = load_sound("assets/sfx/Jumpscare1.mp3")
snd_jumpscare2 = load_sound("assets/sfx/Jumpscare2.mp3")

# --- FÄRGER & FONTER ---
BLACK, WHITE, RED, GREEN, GREY = (0,0,0), (255,255,255), (180,0,0), (0,255,0), (40,40,40)
DARK_GREY, LIGHT_GREY, GOLD = (60, 60, 60), (150, 150, 150), (255, 215, 0)

font_menu = pygame.font.SysFont("courier new", 30, bold=True)
font_small = pygame.font.SysFont("courier new", 16, bold=True)
font_clock = pygame.font.SysFont("courier new", 40, bold=True)

# --- SPELVARIABLER ---
scene = "menu"
power_level = 100.0
visitor_outside = False
visitor_type, visitor_timer, stare_timer = 1, 0, 0
game_state, jumpscare_played = "playing", False
death_time_start, death_reason = 0, ""
charge_flash = 0

game_hour, game_minute = 12, 0
last_minute_tick = 0 
MINUTE_DURATION = 1000 

comp_x, comp_y = 115, 260
charge_btn_rect = pygame.Rect(comp_x + 75, comp_y + 45, 70, 25)

def reset_game():
    global power_level, visitor_outside, visitor_timer, stare_timer, game_state, jumpscare_played, scene, death_reason, game_hour, game_minute, last_minute_tick
    power_level, visitor_outside, visitor_timer, stare_timer = 100.0, False, 0, 0
    game_state, jumpscare_played, scene, death_reason = "playing", False, "room", ""
    game_hour, game_minute = 12, 0
    last_minute_tick = pygame.time.get_ticks()

def draw_room():
    global charge_flash
    bg_brightness = max(5, int(power_level / 5))
    screen.fill((bg_brightness, bg_brightness, bg_brightness + 10))
    
    # Golv
    pygame.draw.rect(screen, (15, 15, 15), (0, 450, WIDTH, 150))
    
    # Fönster
    pygame.draw.rect(screen, (5, 5, 15), (50, 100, 120, 160))
    pygame.draw.rect(screen, (40, 40, 45), (50, 100, 120, 160), 5) 
    
    # --- DÖRR ---
    door_rect = pygame.Rect(600, 180, 110, 280)
    pygame.draw.rect(screen, (30, 15, 5), door_rect) # Dörren
    pygame.draw.circle(screen, (120, 110, 0), (615, 320), 6) # Handtag
    
    # (Här togs koden för siluetten bort)

    # SKRIVBORD
    pygame.draw.rect(screen, (35, 25, 20), (100, 420, 250, 30)) 
    pygame.draw.rect(screen, (25, 15, 10), (120, 450, 15, 50)) 
    pygame.draw.rect(screen, (25, 15, 10), (315, 450, 15, 50)) 
    
    # DATOR
    if img_computer:
        screen.blit(img_computer, (comp_x, comp_y))
    else:
        pygame.draw.rect(screen, (20, 20, 20), (comp_x + 20, comp_y, 180, 130))
    
    # SKÄRMLJUS
    screen_glow = max(0, min(255, int(power_level * 2.5)))
    pygame.draw.rect(screen, (0, screen_glow // 4, screen_glow // 2), (comp_x + 35, comp_y + 15, 150, 95))
    
    # CHARGE KNAPP
    btn_col = GREEN if charge_flash > 0 else DARK_GREY
    if charge_flash > 0: charge_flash -= 1
    pygame.draw.rect(screen, btn_col, charge_btn_rect, border_radius=3)
    btn_txt = font_small.render("CHARGE", True, WHITE)
    screen.blit(btn_txt, (charge_btn_rect.centerx - btn_txt.get_width()//2, charge_btn_rect.centery - btn_txt.get_height()//2))
    
    # Batteri
    p_color = GREEN if power_level > 30 else RED
    pygame.draw.rect(screen, BLACK, (charge_btn_rect.x, charge_btn_rect.bottom + 5, 70, 10))
    pygame.draw.rect(screen, p_color, (charge_btn_rect.x, charge_btn_rect.bottom + 5, int(70 * (power_level/100)), 10))

    # KLOCKA
    time_str = f"{game_hour:02}:{game_minute:02} AM"
    clock_txt = font_clock.render(time_str, True, WHITE)
    screen.blit(clock_txt, (WIDTH - 220, 30))

def draw_peephole():
    screen.fill(BLACK)
    pygame.draw.circle(screen, (35, 35, 40), (WIDTH//2, HEIGHT//2), 200)
    
    # --- RITA PERSONEN I KIKHÅLET ---
    if visitor_outside:
        img = img_p1_peephole if visitor_type == 1 else img_p2_peephole
        if img:
            screen.blit(img, (WIDTH//2 - img.get_width()//2, HEIGHT//2 - img.get_height()//2))
        else:
            pygame.draw.circle(screen, RED if visitor_type == 2 else WHITE, (WIDTH//2, HEIGHT//2), 50)
            
    # Maskning (svarta ringar runt kikhålet)
    for i in range(200, 500, 10): 
        pygame.draw.circle(screen, BLACK, (WIDTH//2, HEIGHT//2), i, 15)
        
    clock_txt = font_clock.render(f"{game_hour:02}:{game_minute:02} AM", True, WHITE)
    screen.blit(clock_txt, (WIDTH - 220, 30))

# --- MAIN LOOP ---
while True:
    current_time = pygame.time.get_ticks()
    mx, my = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
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
                        visitor_outside, visitor_type, visitor_timer, stare_timer = True, random.choice([1, 2]), 0, 0
                        s = snd_knock_calm if visitor_type == 1 else snd_knock_loud
                        if s: s.play()
                
                # Klicka på dörren för att se i kikhålet
                if 600 < mx < 710 and 180 < my < 460: scene = "peephole"
                
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if scene == "peephole": scene = "room"
            elif scene in ["achievements", "win"]: scene = "menu"

    # --- LOGIK ---
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
                game_hour = 1 if game_hour == 12 else game_hour + 1
            if game_hour == 6:
                scene = "win"
                game_data[0] += 1; game_data[2] = 1; save_data(game_data)

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

    # --- RENDERING ---
    if scene == "menu":
        if img_menu_bg:
            screen.blit(img_menu_bg, (0, 0))
        else:
            screen.fill(BLACK) # Fallback om bilden inte hittas
            
        for i, text in enumerate(["START", "ACHIEVEMENTS", "CLOSE"]):
            rect = pygame.Rect(WIDTH//2 - 125, 200 + i*70, 250, 50)
            # Vi gör knapparna lite genomskinliga eller behåller färgen
            pygame.draw.rect(screen, (100,0,0) if rect.collidepoint(mx, my) else GREY, rect, border_radius=5)
            t = font_menu.render(text, True, WHITE)
            screen.blit(t, (rect.centerx - t.get_width()//2, rect.centery - t.get_height()//2))
    
    elif scene == "achievements":
        screen.fill(BLACK)
        # ... 
            
    elif scene == "win":
        screen.fill(BLACK)
        t = font_menu.render("06:00 AM - SURVIVED", True, GREEN)
        screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2))
        
    elif game_state == "playing":
        draw_room() if scene == "room" else draw_peephole()
        
    elif game_state == "lost":
        # --- JUMPSCARE RENDERING ---
        elapsed = current_time - death_time_start
        if elapsed < 2500:
            if not jumpscare_played:
                s = snd_jumpscare1 if "1" in death_reason or "power" in death_reason else snd_jumpscare2
                if s: s.play(); jumpscare_played = True
            
            shake_x = random.randint(-15, 15)
            shake_y = random.randint(-15, 15)
            screen.fill((random.randint(0,20), 0, 0)) 
            
            img = img_p1_raw if ("1" in death_reason or "power" in death_reason) else img_p2_raw
            if img: 
                jumpscare_img = pygame.transform.smoothscale(img, (WIDTH + 40, HEIGHT + 40))
                screen.blit(jumpscare_img, (-20 + shake_x, -20 + shake_y))
            else:
                txt = font_menu.render("YOU DIED", True, RED)
                screen.blit(txt, (WIDTH//2 - txt.get_width()//2 + shake_x, HEIGHT//2 + shake_y))
        else: 
            scene, game_state = "menu", "playing"

    pygame.display.flip()
    clock.tick(60)