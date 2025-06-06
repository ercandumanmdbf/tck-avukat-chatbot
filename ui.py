# ui.py

import pygame
import threading
import sys
import textwrap
import time

from chatbot import get_bot_response
from pygame.locals import *

# Pygame ayarları
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("TCK Avukat Chatbot")
font = pygame.font.SysFont(None, 24)
big_font = pygame.font.SysFont(None, 36)
clock = pygame.time.Clock()

# Görsel yükleme
lawyer_img = pygame.image.load("lawyer.png")
lawyer_img = pygame.transform.scale(lawyer_img, (120, 150))

# Global durum
messages = []
input_text = ""
chat_started = False
cursor_visible = True
cursor_counter = 0
scroll_y = 0
line_height = 25
bot_thinking = False
closing = False
auto_scroll = True
scroll_dragging = False
scrollbar_rect = pygame.Rect(780, 25, 8, 480)
scrollbar_click_offset = 0
running = True
pending_input = None

def draw_ui():
    global cursor_counter, cursor_visible, scroll_y

    screen.fill((240, 240, 240))

    if not chat_started:
        screen.blit(lawyer_img, (340, 80))
        title = big_font.render("TCK Avukat Chatbot", True, (0, 0, 0))
        screen.blit(title, (270, 20))
        intro = font.render("Avukat bot ile görüşmeye başlamak için Enter'a basın.", True, (0, 0, 0))
        screen.blit(intro, (230, 300))
        return

    screen.blit(lawyer_img, (20, 10))

    if bot_thinking:
        glow = font.render("Düşünüyor...", True, (100, 100, 255))
        screen.blit(glow, (25, 170))

    chat_rect = pygame.Rect(160, 20, 620, 500)
    pygame.draw.rect(screen, (255, 255, 255), chat_rect)
    pygame.draw.rect(screen, (0, 0, 0), chat_rect, 2)

    clip_rect = pygame.Rect(165, 25, 610, 490)
    screen.set_clip(clip_rect)

    rendered_lines = []
    total_height = 0
    for sender, msg in messages:
        wrapped = textwrap.wrap(msg, width=70)
        for line in wrapped:
            rendered_lines.append((sender, line))
            total_height += line_height

    min_scroll = min(0, 480 - total_height)
    scroll_y = min(0, scroll_y)
    scroll_y = max(scroll_y, min_scroll)

    y = 30 + scroll_y
    for i, (sender, line) in enumerate(rendered_lines):
        if sender == "Siz":
            color = (0, 0, 200)
            prefix = "Siz: " if i == 0 or rendered_lines[i - 1][0] != sender else ""
        elif sender == "Bot Avukat":
            color = (200, 0, 0)
            prefix = "Bot Avukat: " if i == 0 or rendered_lines[i - 1][0] != sender else ""
        else:
            color = (0, 0, 0)
            prefix = f"{sender}: " if i == 0 or rendered_lines[i - 1][0] != sender else ""

        rendered_msg = font.render(f"{prefix}{line}", True, color)
        screen.blit(rendered_msg, (170, y))
        y += line_height

    screen.set_clip(None)

    if total_height > 480:
        scrollbar_height = max(40, 480 * 480 // total_height)
        scroll_pos = int((abs(scroll_y) / (total_height - 480)) * (480 - scrollbar_height))
        scrollbar_rect.update(780, 25 + scroll_pos, 8, scrollbar_height)
        pygame.draw.rect(screen, (200, 200, 200), (780, 25, 8, 480))
        pygame.draw.rect(screen, (100, 100, 100), scrollbar_rect)

    pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(190, 550, 580, 30))
    pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(190, 550, 580, 30), 2)
    label_surface = font.render("Siz:", True, (0, 0, 0))
    screen.blit(label_surface, (150, 555))

    cursor_counter += 1
    if cursor_counter >= 30:
        cursor_visible = not cursor_visible
        cursor_counter = 0

    display_text = input_text + ("|" if cursor_visible else "")
    input_surface = font.render(display_text, True, (0, 0, 0))
    screen.blit(input_surface, (200, 555))

def run_app():
    global input_text, chat_started, running, pending_input
    global bot_thinking, closing, scroll_y, scroll_dragging, scrollbar_click_offset, auto_scroll

    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if chat_started:
                    if event.key == K_RETURN and input_text.strip():
                        messages.append(("Siz", input_text))
                        pending_input = input_text
                        input_text = ""
                    elif event.key == K_BACKSPACE:
                        input_text = input_text[:-1]
                    elif event.key == K_UP:
                        scroll_y += line_height
                        auto_scroll = False
                    elif event.key == K_DOWN:
                        scroll_y -= line_height
                        auto_scroll = False
                    else:
                        input_text += event.unicode
                else:
                    if event.key == K_RETURN:
                        chat_started = True
                        messages.append(("Sistem", "Görüşme başladı. Sorunuzu yazabilirsiniz."))
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 4:
                    scroll_y += line_height
                    auto_scroll = False
                elif event.button == 5:
                    scroll_y -= line_height
                    auto_scroll = False
                elif event.button == 1:
                    if scrollbar_rect.collidepoint(event.pos):
                        scroll_dragging = True
                        scrollbar_click_offset = event.pos[1] - scrollbar_rect.y
                        auto_scroll = False
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    scroll_dragging = False
            elif event.type == MOUSEMOTION and scroll_dragging:
                mouse_y = event.pos[1]
                scroll_area_height = 480
                total_height = len(messages) * line_height * 2
                scrollbar_height = max(40, scroll_area_height * scroll_area_height // max(1, total_height))
                max_scroll = total_height - scroll_area_height
                new_y = mouse_y - scrollbar_click_offset
                new_y = max(25, min(505 - scrollbar_height, new_y))
                scroll_ratio = (new_y - 25) / (480 - scrollbar_height)
                scroll_y = -int(scroll_ratio * max_scroll)

        if pending_input:
            def bot_thread(user_msg):
                global closing
                global bot_thinking, closing, auto_scroll
                bot_thinking = True
                reply, end = get_bot_response(user_msg, messages)
                messages.append(("Bot Avukat", reply))
                bot_thinking = False
                auto_scroll = True
                if end:

                    closing = True

            threading.Thread(target=bot_thread, args=(pending_input,)).start()
            pending_input = None

        draw_ui()
        pygame.display.flip()
        clock.tick(30)

        if closing:
            pygame.time.wait(5000)
            pygame.quit()
            sys.exit()
