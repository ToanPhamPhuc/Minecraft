import sys
import os
import math
import msvcrt  # Windows-specific keyboard input module

Y_PIXELS = 180
X_PIXELS = 900
Z_BLOCKS = 10
Y_BLOCKS = 20
X_BLOCKS = 20
EYE_HEIGHT = 1.5
VIEW_HEIGHT = 0.7
VIEW_WIDTH = 1.0
BLOCK_BORDER_SIZE = 0.05

keystate = [0] * 256

def process_input():
    global keystate
    keystate = [0] * 256
    while msvcrt.kbhit():
        key = msvcrt.getch()
        if len(key) == 1:
            keystate[ord(key.decode('utf-8'))] = 1

def is_key_pressed(key):
    return keystate[ord(key)]

def init_picture():
    return [[[' ' for _ in range(X_BLOCKS)] for _ in range(Y_BLOCKS)] for _ in range(Z_BLOCKS)]

class Vector:
    def __init__(self, x=0, y=0, z=0):
        self.x, self.y, self.z = x, y, z

class Vector2:
    def __init__(self, psi=0, phi=0):
        self.psi, self.phi = psi, phi

class Player:
    def __init__(self):
        self.pos = Vector(5, 5, 4 + EYE_HEIGHT)
        self.view = Vector2(0, 0)

def angles_to_vect(angles):
    x = math.cos(angles.psi) * math.cos(angles.phi)
    y = math.cos(angles.psi) * math.sin(angles.phi)
    z = math.sin(angles.psi)
    return Vector(x, y, z)

def vect_add(v1, v2):
    return Vector(v1.x + v2.x, v1.y + v2.y, v1.z + v2.z)

def vect_sub(v1, v2):
    return Vector(v1.x - v2.x, v1.y - v2.y, v1.z - v2.z)

def vect_scale(s, v):
    return Vector(s * v.x, s * v.y, s * v.z)

def vect_normalize(v):
    length = math.sqrt(v.x ** 2 + v.y ** 2 + v.z ** 2)
    return Vector(v.x/length, v.y/length, v.z/length)

def init_directions(view):
    view_down = Vector2(view.psi - VIEW_HEIGHT / 2.0, view.phi)
    screen_down = angles_to_vect(view_down)

    view_up = Vector2(view.psi + VIEW_HEIGHT / 2.0, view.phi)
    screen_up = angles_to_vect(view_up)

    view_left = Vector2(view.psi, view.phi - VIEW_WIDTH / 2.0)
    screen_left = angles_to_vect(view_left)

    view_right = Vector2(view.psi, view.phi + VIEW_WIDTH / 2.0)
    screen_right = angles_to_vect(view_right)

    screen_mid_vert = vect_scale(0.5, vect_add(screen_up, screen_down))
    screen_mid_hor = vect_scale(0.5, vect_add(screen_left, screen_right))
    mid_to_left = vect_sub(screen_left, screen_mid_hor)
    mid_to_up = vect_sub(screen_up, screen_mid_vert)

    dir_grid = [[None for _ in range(X_PIXELS)] for _ in range(Y_PIXELS)]

    for y_pix in range(Y_PIXELS):
        for x_pix in range(X_PIXELS):
            tmp = vect_add(screen_mid_hor, mid_to_left)
            tmp = vect_add(tmp, mid_to_up)
            tmp = vect_sub(tmp, vect_scale((x_pix / (X_PIXELS - 1)) * 2, mid_to_left))
            tmp = vect_sub(tmp, vect_scale((y_pix / (Y_PIXELS - 1)) * 2, mid_to_up))
            dir_grid[y_pix][x_pix] = vect_normalize(tmp)

    return dir_grid

def ray_outside(pos):
    return not (0 <= pos.x < X_BLOCKS and 0 <= pos.y < Y_BLOCKS and 0 <= pos.z < Z_BLOCKS)

def on_block_border(pos):
    cnt = 0
    if abs(pos.x - round(pos.x)) < BLOCK_BORDER_SIZE: cnt += 1
    if abs(pos.y - round(pos.y)) < BLOCK_BORDER_SIZE: cnt += 1
    if abs(pos.z - round(pos.z)) < BLOCK_BORDER_SIZE: cnt += 1
    return cnt >= 2

def raytrace(pos, dir, blocks):
    eps = 0.01
    while not ray_outside(pos):
        block = blocks[int(pos.z)][int(pos.y)][int(pos.x)]
        if block != ' ':
            return '-' if on_block_border(pos) else block
        dist = 2
        if dir.x > eps:
            dist = min(dist, ((int(pos.x) + 1 - pos.x) / dir.x))
        elif dir.x < -eps:
            dist = min(dist, ((int(pos.x) - pos.x) / dir.x))
        if dir.y > eps:
            dist = min(dist, ((int(pos.y) + 1 - pos.y) / dir.y))
        elif dir.y < -eps:
            dist = min(dist, ((int(pos.y) - pos.y) / dir.y))
        if dir.z > eps:
            dist = min(dist, ((int(pos.z) + 1 - pos.z) / dir.z))
        elif dir.z < -eps:
            dist = min(dist, ((int(pos.z) - pos.z) / dir.z))
        pos = vect_add(pos, vect_scale(dist + eps, dir))
    return ' '

def get_picture(picture, posview, blocks):
    directions = init_directions(posview.view)
    for y in range(Y_PIXELS):
        for x in range(X_PIXELS):
            picture[y][x] = raytrace(posview.pos, directions[y][x], blocks)

def draw_ascii(picture):
    sys.stdout.flush()
    os.system("cls")  # Windows clear screen
    for row in picture:
        current_color = 0
        for char in row:
            if char == 'o' and current_color != 32:
                print("\033[32m", end="")
                current_color = 32
            elif char != '0' and current_color != 0:
                print("\033[0m", end="")
                current_color = 0
            print(char, end="")
        print("\033[0m")

def update_pos_view(posview, blocks):
    move_eps = 0.3
    tilt_eps = 0.1
    x, y = int(posview.pos.x), int(posview.pos.y)
    z = int(posview.pos.z - EYE_HEIGHT + 0.01)
    if blocks[z][y][x] != ' ':
        posview.pos.z += 1
    z = int(posview.pos.z - EYE_HEIGHT - 0.01)
    if blocks[z][y][x] == ' ':
        posview.pos.z -= 1

    if is_key_pressed('w'):
        posview.view.psi += tilt_eps
    if is_key_pressed('s'):
        posview.view.psi -= tilt_eps
    if is_key_pressed('a'):
        posview.view.phi -= tilt_eps
    if is_key_pressed('d'):
        posview.view.phi += tilt_eps
