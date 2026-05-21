import pygame
import sys
import random
import math
import os

pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("The Peephole - Entity Edition")
clock = pygame.time.Clock()

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (180, 0, 0)
GREEN = (0, 255, 0)
GREY = (40, 40, 40)
DARK_GREY = (60, 60, 60)
GOLD = (255, 215, 0)

font_menu = pygame.font.SysFont("courier new", 30, bold=True)
font_small = pygame.font.SysFont("courier new", 16, bold=True)
font_clock = pygame.font.SysFont("courier new", 40, bold=True)

comp_x, comp_y = 115, 260
door_rect = pygame.Rect(600, 180, 110, 280)
MINUTE_DURATION = 1000

def load_data():
    if os.path.exists("data.txt"):
        with open("data.txt", "r") as f:
            try:
                return [int(x) for x in f.read().split(",")]
            except:
                return [0, 0, 0, 0, 0]
    return [0, 0, 0, 0, 0]

def save_data(data):
    with open("data.txt", "w") as f:
        f.write(",".join(str(x) for x in data))

game_data = load_data()

def load_image(path, size=None):
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.smoothscale(img, size) if size else img
        except Exception:
            return None
    return None

def load_sound(path):
    return pygame.mixer.Sound(path) if os.path.exists(path) else None

img_menu_bg = load_image("assets/bakgrund.png", (WIDTH, HEIGHT))
img_p1_raw = load_image("assets/Neighbours/Person1.png")
img_p2_raw = load_image("assets/Neighbours/Person2.png")
img_p1_peephole = load_image("assets/Neighbours/Person1.png", (150, 250))
img_p2_peephole = load_image("assets/Neighbours/Person2.png", (180, 280))
img_granne = load_image("assets/Neighbours/granne.png")
img_p3_raw = load_image("assets/Neighbours/Person3.png")
img_p3_window = load_image("assets/Neighbours/Person3.png", (120, 160))
img_computer = load_image("assets/computer.png", (220, 160))
img_corridor = load_image("assets/corridor.png", (110, 280)) 

snd_knock_calm = load_sound("assets/sfx/Calm knock.mp3")
snd_knock_loud = load_sound("assets/sfx/Banging.mp3")
snd_jumpscare1 = load_sound("assets/sfx/Jumpscare1.mp3")
snd_jumpscare2 = load_sound("assets/sfx/Jumpscare2.mp3")
snd_jumpscare3 = load_sound("assets/sfx/Jumpscare3.mp3")
snd_alarm = load_sound("assets/sfx/Larm.mp3")

path_music_menu = "assets/sfx/Meny.mp3"
path_music_game = "assets/sfx/Lägenheten.mp3"
current_playing_track = None

def update_music(current_scene):
    global current_playing_track
    target_track = path_music_menu if current_scene in ["menu", "achievements", "settings"] else path_music_game
    if target_track and target_track != current_playing_track:
        if os.path.exists(target_track):
            pygame.mixer.music.load(target_track)
            pygame.mixer.music.play(-1)
            current_playing_track = target_track

class GameState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.scene = "menu"
        self.game_state = "playing"
        self.power_level = 100.0
        self.flashlight_on = False
        
        self.door_open = False
        self.walking_in = False
        self.walker_x = 600
        
        self.visitor_outside = False
        self.visitor_type = 1
        self.visitor_timer = 0
        self.stare_timer = 0

        self.window_visitor_active = False
        self.window_visitor_timer = 0
        self.window_flash_duration = 0
        
        self.jumpscare_played = False
        self.death_time_start = 0
        self.death_reason = ""
        self.charge_flash = 0
        
        self.alarm_active = False
        self.alarm_timer_start = 0
        self.alarm_circles = []
        self.alarm_clicks_needed = 0
        self.alarm_failures = 0
        
        self.game_hour = 9
        self.game_minute = 0
        self.game_period = "PM"
        self.last_minute_tick = pygame.time.get_ticks()

    def spawn_alarm_circle(self):
        radius = 35
        x = random.randint(radius, WIDTH - radius)
        y = random.randint(radius, HEIGHT - radius)
        self.alarm_circles.append(pygame.Rect(x - radius, y - radius, radius * 2, radius * 2))

    def get_total_minutes(self):
        hours_passed = (self.game_hour - 9) if self.game_period == "PM" else (12 - 9)
        return hours_passed * 60 + self.game_minute

    def trigger_loss(self, reason, current_time):
        self.game_state = "lost"
        self.death_time_start = current_time
        self.death_reason = reason
        game_data[1] += 1
        save_data(game_data)
        pygame.mixer.music.stop()

    def trigger_win(self):
        self.game_period = "AM"
        self.game_hour = 12
        self.scene = "win"
        game_data[0] += 1
        save_data(game_data)
        pygame.mixer.music.stop()

state = GameState()

class Button:
    def __init__(self, x, y, width, height, text, font, base_color, hover_color, text_color=WHITE):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.base_color = base_color
        self.hover_color = hover_color
        self.text_color = text_color

    def draw(self, surface, mouse_pos):
        current_color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.base_color
        pygame.draw.rect(surface, current_color, self.rect, border_radius=5)
        
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

class Slider:
    def __init__(self, x, y, width, height, start_val=0.5):
        self.rect = pygame.Rect(x, y, width, height)
        self.val = start_val
        self.is_dragging = False

    def draw(self, surface):
        pygame.draw.rect(surface, GREY, self.rect, border_radius=5)
        fill_width = int(self.rect.width * self.val)
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, fill_width, self.rect.height)
        pygame.draw.rect(surface, GREEN, fill_rect, border_radius=5)
        knob_x = self.rect.x + fill_width
        pygame.draw.circle(surface, WHITE, (knob_x, self.rect.centery), int(self.rect.height * 0.8))

    def update(self, mouse_pos, mouse_pressed):
        if self.rect.collidepoint(mouse_pos) and mouse_pressed[0]:
            self.is_dragging = True
            
        if not mouse_pressed[0]:
            self.is_dragging = False

        if self.is_dragging:
            rel_x = mouse_pos[0] - self.rect.x
            self.val = max(0.0, min(1.0, rel_x / self.rect.width))
            pygame.mixer.music.set_volume(self.val)

btn_start = Button(WIDTH//2 - 125, 200, 250, 50, "START", font_menu, GREY, (100, 0, 0))
btn_achievements = Button(WIDTH//2 - 125, 270, 250, 50, "ACHIEVEMENTS", font_menu, GREY, (100, 0, 0))
btn_settings = Button(WIDTH//2 - 125, 340, 250, 50, "SETTINGS", font_menu, GREY, (100, 0, 0))
btn_close = Button(WIDTH//2 - 125, 410, 250, 50, "CLOSE", font_menu, GREY, (100, 0, 0))
btn_charge = Button(comp_x + 75, comp_y + 45, 70, 25, "CHARGE", font_small, DARK_GREY, GREEN)
btn_continue = Button(WIDTH - 180, HEIGHT - 70, 160, 50, "CONTINUE", font_small, GREY, (100, 0, 0))
volume_slider = Slider(WIDTH//2 - 100, 250, 200, 20, start_val=0.5)

def draw_clock():
    time_str = f"{state.game_hour:02}:{state.game_minute:02} {state.game_period}"
    screen.blit(font_clock.render(time_str, True, WHITE), (WIDTH - 220, 30))

def draw_room(mouse_pos):
    bg_brightness = max(5, int(state.power_level / 5))
    screen.fill((bg_brightness, bg_brightness, bg_brightness + 10))

    win_x, win_y, win_w, win_h = 50, 100, 120, 160
    total_mins = state.get_total_minutes()
    lerp = min(1.0, total_mins / 180)
    sky_color = (int(100 * (1 - lerp) + 5 * lerp), int(150 * (1 - lerp) + 5 * lerp), int(255 * (1 - lerp) + 15 * lerp))
    
    sky_surface = pygame.Surface((win_w, win_h))
    sky_surface.fill(sky_color)

    sun_a = math.pi * (0.4 + lerp * 0.5)
    pygame.draw.circle(sky_surface, (255, 255, 100), (int(win_w//2 + (win_h-10) * math.cos(sun_a)), int((win_h+30) - (win_h-10) * math.sin(sun_a))), 15)
    
    moon_f = max(0.0, (total_mins - 180 * 0.3) / (180 * 0.7))
    moon_a = math.pi * (0.1 - moon_f * 0.4)
    mx, my = int(win_w//2 + (win_h-10) * math.cos(moon_a)), int((win_h+30) - (win_h-10) * math.sin(moon_a))
    pygame.draw.circle(sky_surface, (220, 220, 255), (mx, my), 12)
    pygame.draw.circle(sky_surface, sky_color, (mx + 8, my), 12)

    screen.blit(sky_surface, (win_x, win_y))

    if state.window_visitor_active and img_p3_window:
        screen.blit(img_p3_window, (win_x, win_y))

    pygame.draw.rect(screen, (40, 40, 45), (win_x, win_y, win_w, win_h), 5)
    
    pygame.draw.line(screen, (40, 40, 45), (win_x + 60, win_y), (win_x + 60, win_y + win_h), 4)
    pygame.draw.line(screen, (40, 40, 45), (win_x, win_y + 80), (win_x + win_w, win_y + 80), 4)
    
    pygame.draw.rect(screen, (15, 15, 15), (0, 450, WIDTH, 150)) 
    
    if state.door_open:
        if img_corridor: screen.blit(img_corridor, (door_rect.x, door_rect.y))
        else: pygame.draw.rect(screen, (10, 10, 10), door_rect)
            
        if state.visitor_outside:
            v_img = img_p1_raw if state.visitor_type == 1 else img_p2_raw
            if v_img:
                screen.blit(pygame.transform.smoothscale(v_img, (90, 250)), (door_rect.x + 10, door_rect.y + 30))
                
        open_door_rect = pygame.Rect(710, 180, 50, 280)
        pygame.draw.rect(screen, (20, 10, 5), open_door_rect) 
        pygame.draw.circle(screen, (120, 110, 0), (720, 320), 12) 
        
        close_txt = font_small.render("CLOSE", True, WHITE)
        screen.blit(close_txt, (720 - close_txt.get_width()//2, 340))
        
    else:
        pygame.draw.rect(screen, (30, 15, 5), door_rect)
        pygame.draw.circle(screen, (120, 110, 0), (620, 320), 12) 

    pygame.draw.rect(screen, (35, 25, 20), (100, 420, 250, 30)) 
    pygame.draw.rect(screen, (25, 15, 10), (120, 450, 15, 50))  
    pygame.draw.rect(screen, (25, 15, 10), (315, 450, 15, 50))  
    if img_computer: screen.blit(img_computer, (comp_x, comp_y))
    
    btn_charge.base_color = GREEN if state.charge_flash > 0 else DARK_GREY
    if state.charge_flash > 0: state.charge_flash -= 1
    btn_charge.draw(screen, mouse_pos)
    
    pygame.draw.rect(screen, BLACK, (btn_charge.rect.x, btn_charge.rect.bottom + 5, 70, 10))
    pygame.draw.rect(screen, GREEN if state.power_level > 30 else RED, (btn_charge.rect.x, btn_charge.rect.bottom + 5, int(70 * (state.power_level/100)), 10))

    if state.walking_in and img_p2_raw:
        scaled_walk = pygame.transform.smoothscale(img_p2_raw, (130, 350))
        screen.blit(scaled_walk, (state.walker_x, 150))

    if state.flashlight_on and state.power_level > 0:
        mouse_x, mouse_y = mouse_pos
        for i in range(8):
            gr = 40 + (i * 15)
            ga = max(0, 80 - (i * 10)) 
            surf = pygame.Surface((gr * 2, gr * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 255, 220, ga), (gr, gr), gr)
            screen.blit(surf, (mouse_x - gr, mouse_y - gr))

    if state.alarm_active:
        if (pygame.time.get_ticks() // 250) % 2 == 0:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((200, 0, 0, 50))
            screen.blit(overlay, (0, 0))
            
        time_left = max(0, 5000 - (pygame.time.get_ticks() - state.alarm_timer_start)) / 1000
        alarm_text = font_menu.render(f"LARM WENT OFF! CLICK THE CIRCLES! {time_left:.1f}s", True, RED)
        screen.blit(alarm_text, (WIDTH//2 - alarm_text.get_width()//2 - 10, 50))
        
        for circle in state.alarm_circles:
            pygame.draw.circle(screen, RED, circle.center, circle.width // 2)
            pygame.draw.circle(screen, WHITE, circle.center, circle.width // 2, 3)

    draw_clock()

def draw_peephole():
    screen.fill(BLACK)
    pygame.draw.circle(screen, (35, 35, 40), (WIDTH//2, HEIGHT//2), 200)
    
    if state.visitor_outside:
        img = img_p1_peephole if state.visitor_type == 1 else img_p2_peephole
        if img: screen.blit(img, (WIDTH//2 - img.get_width()//2, HEIGHT//2 - img.get_height()//2))
            
    for i in range(200, 500, 10): 
        pygame.draw.circle(screen, BLACK, (WIDTH//2, HEIGHT//2), i, 15)
        
    draw_clock()

def draw_menu(mouse_pos):
    if img_menu_bg: screen.blit(img_menu_bg, (0, 0))
    else: screen.fill(BLACK)
    screen.blit(font_menu.render(f"THE PEEPHOLE", True, DARK_GREY), (WIDTH//2 - 105, 102))
    screen.blit(font_menu.render(f"THE PEEPHOLE", True, RED), (WIDTH//2 - 105, 100))
    btn_start.draw(screen, mouse_pos)
    btn_achievements.draw(screen, mouse_pos)
    btn_settings.draw(screen, mouse_pos)
    btn_close.draw(screen, mouse_pos)

def draw_achievements():
    screen.fill(BLACK)
    at = font_menu.render("ACHIEVEMENTS", True, GOLD)
    screen.blit(at, (WIDTH//2 - at.get_width()//2, 100))
    screen.blit(font_small.render(f"WINS: {game_data[0]}", True, WHITE), (WIDTH//2 - 50, 250))
    screen.blit(font_small.render(f"DEATHS: {game_data[1]}", True, WHITE), (WIDTH//2 - 50, 280))

def draw_settings(mouse_pos, mouse_pressed):
    screen.fill(BLACK)
    at = font_menu.render("SETTINGS", True, GOLD)
    screen.blit(at, (WIDTH//2 - at.get_width()//2, 100))
    vol_text = font_small.render(f"VOLUME: {int(volume_slider.val * 100)}%", True, WHITE)
    screen.blit(vol_text, (WIDTH//2 - 100, 220))
    
    volume_slider.update(mouse_pos, mouse_pressed)
    volume_slider.draw(screen)

def draw_lost(current_time):
    elapsed = current_time - state.death_time_start
    if elapsed < 2500:
        if not state.jumpscare_played:
            if "3" in state.death_reason:
                s = snd_jumpscare3
            else:
                s = snd_jumpscare1 if ("1" in state.death_reason or "power" in state.death_reason) else snd_jumpscare2
                
            if s: s.play()
            state.jumpscare_played = True
            
        shake_x, shake_y = random.randint(-15, 15), random.randint(-15, 15)
        screen.fill((random.randint(0,20), 0, 0)) 
        
        if state.death_reason == "granne":
            img = img_granne
        elif "3" in state.death_reason:
            img = img_p3_raw
        else:
            img = img_p1_raw if ("1" in state.death_reason or "power" in state.death_reason) else img_p2_raw
            
        if img: 
            screen.blit(pygame.transform.smoothscale(img, (WIDTH + 40, HEIGHT + 40)), (-20 + shake_x, -20 + shake_y))
            
        if state.death_reason == "granne":
            granne_text = font_menu.render("Neighbour threw you out", True, RED)
            screen.blit(granne_text, (WIDTH//2 - granne_text.get_width()//2, HEIGHT - 80))
            
    elif elapsed < 5500:
        screen.fill(BLACK)
    else: 
        state.scene = "menu"
        state.game_state = "playing"

def draw_screen(mouse_pos, current_time, mouse_pressed):
    if state.scene == "menu":
        draw_menu(mouse_pos)
    elif state.scene == "achievements":
        draw_achievements()
    elif state.scene == "settings":
        draw_settings(mouse_pos, mouse_pressed)
    elif state.scene == "win":
        screen.fill(BLACK)
        t = font_menu.render("MIDNIGHT - YOU SURVIVED", True, GREEN)
        screen.blit(t, (WIDTH//2 - t.get_width()//2, HEIGHT//2))
        btn_continue.draw(screen, mouse_pos)
    elif state.game_state == "playing":
        if state.scene == "room": draw_room(mouse_pos)
        else: draw_peephole()
    elif state.game_state == "lost":
        draw_lost(current_time)

while True:
    current_time = pygame.time.get_ticks()
    mouse_pos = pygame.mouse.get_pos()
    mouse_x, mouse_y = mouse_pos
    
    update_music(state.scene)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit(); sys.exit()
            
        if event.type == pygame.MOUSEBUTTONDOWN:
            if state.scene == "menu":
                if btn_start.is_clicked(mouse_pos): 
                    state.reset()
                    state.scene = "room"
                elif btn_achievements.is_clicked(mouse_pos): 
                    state.scene = "achievements"
                elif btn_settings.is_clicked(mouse_pos): 
                    state.scene = "settings"
                elif btn_close.is_clicked(mouse_pos): 
                    pygame.quit(); sys.exit()
                    
            elif state.scene == "room" and state.game_state == "playing":
                if state.alarm_active:
                    for circle in state.alarm_circles[:]:
                        if circle.collidepoint(mouse_x, mouse_y):
                            state.alarm_circles.remove(circle)
                            state.alarm_clicks_needed -= 1
                            if state.alarm_clicks_needed > 0:
                                state.spawn_alarm_circle()
                            else:
                                state.alarm_active = False
                                if snd_alarm: snd_alarm.stop()
                            break
                            
                else:
                    if btn_charge.is_clicked(mouse_pos):
                        state.power_level = min(100, state.power_level + 10)
                        state.charge_flash = 5
                        
                        if random.randint(1, 100) == 1:
                            state.alarm_active = True
                            if snd_alarm: snd_alarm.play(-1)
                            state.alarm_timer_start = current_time
                            state.alarm_clicks_needed = 3
                            state.alarm_circles = []
                            state.spawn_alarm_circle()
                            
                        elif not state.visitor_outside and random.random() < 0.05:
                            state.visitor_outside = True
                            state.visitor_type = random.choice([1, 2])
                            state.visitor_timer = 0
                            state.stare_timer = 0
                            s = snd_knock_calm if state.visitor_type == 1 else snd_knock_loud
                            if s: s.play()
                    
                    current_knob_rect = pygame.Rect(695, 295, 50, 50) if state.door_open else pygame.Rect(595, 295, 50, 50)
                    if current_knob_rect.collidepoint(mouse_x, mouse_y) and not state.walking_in:
                        state.door_open = not state.door_open
                        if state.door_open and state.visitor_outside:
                            if state.visitor_type == 1:
                                state.trigger_loss("monster1", current_time)
                            elif state.visitor_type == 2:
                                state.visitor_outside = False
                                state.walking_in = True
                                state.walker_x = door_rect.x - 20 

                    elif door_rect.collidepoint(mouse_x, mouse_y) and not state.door_open and not state.walking_in:
                        state.scene = "peephole"
                    
            elif state.scene == "win":
                if btn_continue.is_clicked(mouse_pos):
                    state.scene = "menu"
                    
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if state.scene == "peephole": state.scene = "room"
                elif state.scene in ["achievements", "win", "settings"]: state.scene = "menu"
            
            if event.key == pygame.K_f and state.scene == "room" and state.game_state == "playing":
                state.flashlight_on = not state.flashlight_on

    if state.scene not in ["menu", "achievements", "win"] and state.game_state == "playing":
        if state.alarm_active:
            if current_time - state.alarm_timer_start > 5000:
                state.alarm_active = False
                if snd_alarm: snd_alarm.stop()
        
                state.alarm_failures += 1
                if state.alarm_failures >= 2:
                    state.trigger_loss("granne", current_time)

        if not state.window_visitor_active and random.random() < 0.001:
            state.window_visitor_active = True
            state.window_visitor_timer = current_time
            state.window_flash_duration = 0

        if state.window_visitor_active:
            window_rect = pygame.Rect(50, 100, 120, 160)
            
            if state.scene == "room" and state.flashlight_on and window_rect.collidepoint(mouse_x, mouse_y):
                state.window_flash_duration += clock.get_time()
                
                if state.window_flash_duration >= 3000:
                    state.window_visitor_active = False
            else:
                state.window_flash_duration = 0

            if current_time - state.window_visitor_timer > 7000:
                state.window_visitor_active = False
                state.trigger_loss("monster3", current_time)

        state.power_level -= 0.20 if (state.scene == "room" and state.flashlight_on) else 0.05
        if state.power_level <= 0: 
            state.trigger_loss("power", current_time)

        if current_time - state.last_minute_tick >= MINUTE_DURATION:
            state.game_minute += 1
            state.last_minute_tick = current_time
            if state.game_minute >= 60:
                state.game_minute = 0
                if state.game_hour == 11:
                    state.trigger_win()
                else:
                    state.game_hour = 1 if state.game_hour == 12 else state.game_hour + 1

        if state.walking_in:
            state.walker_x -= 3 
            if state.walker_x < -150: 
                state.walking_in = False
                state.door_open = False 

        if state.visitor_outside:
            if state.scene == "peephole":
                if state.visitor_type == 1:
                    state.stare_timer += 1
                    if state.stare_timer >= 120: state.visitor_outside = False
                else: 
                    state.trigger_loss("monster2", current_time)
            else:
                state.visitor_timer += 1
            
            if state.visitor_timer > 550: 
                state.trigger_loss(f"monster{state.visitor_type}", current_time)

    mouse_pressed = pygame.mouse.get_pressed()
    draw_screen(mouse_pos, current_time, mouse_pressed)

    pygame.display.flip()
    clock.tick(60)