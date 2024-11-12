import pygame

# Инициализация Pygame
pygame.init()

# Размер экрана
screen = pygame.display.set_mode((600, 400))
pygame.display.set_caption("Text Input Example")

# Цвета, шрифты
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
FONT = pygame.font.Font(None, 36)

# Параметры текстового поля
input_box = pygame.Rect(200, 150, 200, 50)  # Размеры поля
text = ""  # Хранение введенного текста
active = False  # Активно поле или нет (когда юзер тыкнул мышкой)

# Главный цикл
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Проверка, тыкнул ли юзер на текстовое поле
            if input_box.collidepoint(event.pos):
                active = not active
            else:
                active = False
        elif event.type == pygame.KEYDOWN:
            if active:  # Только если поле активно
                if event.key == pygame.K_RETURN:  # Нажал Enter — выходим
                    print("Введенный текст:", text)
                    text = ""  # Очистить текст
                elif event.key == pygame.K_BACKSPACE:  # Удалить символ
                    text = text[:-1]
                else:
                    text += event.unicode  # Добавляем символ

    # Рисуем поле и текст
    screen.fill(WHITE)
    pygame.draw.rect(screen, BLACK, input_box, 2)
    text_surface = FONT.render(text, True, BLACK)
    screen.blit(text_surface, (input_box.x + 5, input_box.y + 10))

    pygame.display.flip()

pygame.quit()
