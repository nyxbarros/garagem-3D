import pyglet
pyglet.options['shadow_window'] = False
pyglet.window.Window(visible=False)

import os
os.environ['PYOPENGL_PLATFORM'] = 'x11'
os.environ['SDL_VIDEODRIVER'] = 'x11'

import math
import pygame

from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from PIL import Image
from pywavefront import Wavefront


# =========================================================
# CAMERA
# =========================================================

class Camera:

    def __init__(self):
        self.x = 0
        self.y = 0
        self.z = -5

        self.yaw = 0
        self.pitch = 0

        self.sensitivity = 0.2
        self.speed = 0.2

    def update_mouse(self):

        dx, dy = pygame.mouse.get_rel()

        self.yaw += dx * self.sensitivity
        self.pitch += dy * self.sensitivity

    def get_direction(self):

        rad_yaw = math.radians(self.yaw)
        rad_pitch = math.radians(self.pitch)

        dir_x = math.cos(rad_pitch) * math.sin(rad_yaw)
        dir_y = math.sin(rad_pitch)
        dir_z = math.cos(rad_pitch) * math.cos(rad_yaw)

        return dir_x, dir_y, dir_z

    def move(self, keys):

        dir_x, dir_y, dir_z = self.get_direction()

        if keys[K_w]:
            self.x += dir_x * self.speed
            self.y += dir_y * self.speed
            self.z += dir_z * self.speed

        if keys[K_s]:
            self.x -= dir_x * self.speed
            self.y -= dir_y * self.speed
            self.z -= dir_z * self.speed

        if keys[K_a]:
            self.x += dir_z * self.speed
            self.z -= dir_x * self.speed

        if keys[K_d]:
            self.x -= dir_z * self.speed
            self.z += dir_x * self.speed

        if keys[K_PAGEUP]:
            self.y += self.speed

        if keys[K_PAGEDOWN]:
            self.y -= self.speed

    def apply(self):

        dir_x, dir_y, dir_z = self.get_direction()

        gluLookAt(
            self.x, self.y, self.z,
            self.x + dir_x,
            self.y + dir_y,
            self.z + dir_z,
            0, 1, 0
        )


# =========================================================
# TEXTURE LOADER
# =========================================================

class TextureLoader:

    @staticmethod
    def load(filename):

        img = Image.open(filename)
        img = img.transpose(Image.FLIP_TOP_BOTTOM)

        img_data = img.convert("RGBA").tobytes()

        width, height = img.size

        tex_id = glGenTextures(1)

        glBindTexture(GL_TEXTURE_2D, tex_id)

        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            width,
            height,
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            img_data
        )

        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

        return tex_id


# =========================================================
# CUBE
# =========================================================

class Cube:

    vertices = [
        (-1, -1, -1),
        (1, -1, -1),
        (1, 1, -1),
        (-1, 1, -1),

        (-1, -1, 1),
        (1, -1, 1),
        (1, 1, 1),
        (-1, 1, 1)
    ]

    faces = [
        (0, 1, 2, 3),
        (4, 5, 6, 7),
        (0, 1, 5, 4),
        (2, 3, 7, 6),
        (1, 2, 6, 5),
        (0, 3, 7, 4)
    ]

    texcoords = [
        (0, 0),
        (1, 0),
        (1, 1),
        (0, 1)
    ]

    def __init__(self, texture):

        self.texture = texture

    def draw(self):

        glBindTexture(GL_TEXTURE_2D, self.texture)

        glBegin(GL_QUADS)

        for face in self.faces:

            for i, vertex_index in enumerate(face):

                glTexCoord2fv(self.texcoords[i])
                glVertex3fv(self.vertices[vertex_index])

        glEnd()


# =========================================================
# OBJ MODEL
# =========================================================

class OBJModel:

    def __init__(self, obj_path, texture_path):

        self.scene = Wavefront(
            obj_path,
            collect_faces=True,
            parse=True
        )

        self.texture = TextureLoader.load(texture_path)

    def draw(self):

        glEnable(GL_TEXTURE_2D)

        glBindTexture(GL_TEXTURE_2D, self.texture)

        for mat in self.scene.materials.values():

            verts = mat.vertices
            count = len(verts) // 8

            array_type = (GLfloat * len(verts))(*verts)

            glEnableClientState(GL_VERTEX_ARRAY)
            glEnableClientState(GL_NORMAL_ARRAY)
            glEnableClientState(GL_TEXTURE_COORD_ARRAY)

            glInterleavedArrays(
                GL_T2F_N3F_V3F,
                0,
                array_type
            )

            glDrawArrays(GL_TRIANGLES, 0, count)

            glDisableClientState(GL_TEXTURE_COORD_ARRAY)
            glDisableClientState(GL_NORMAL_ARRAY)
            glDisableClientState(GL_VERTEX_ARRAY)

# =========================================================
# OPENGL APPLICATION
# =========================================================

class OpenGLApp:

    def __init__(self):

        pygame.init()

        self.display = (800, 600)

        pygame.display.set_mode(
            self.display,
            DOUBLEBUF | OPENGL
        )

        pygame.event.set_grab(True)
        pygame.mouse.set_visible(False)

        self.clock = pygame.time.Clock()

        self.camera = Camera()

        self.rot_x = 0
        self.rot_y = 0

        self.init_opengl()

        self.chao = Cube(TextureLoader.load("chao.jpg"))

        self.paredes=[
            Cube(TextureLoader.load("parede.png")),
            Cube(TextureLoader.load("parede.png")),
            Cube(TextureLoader.load("parede.png"))
        ]

        self.teto = Cube(TextureLoader.load("chao.jpg"))

        self.carro = OBJModel(
            "OBJS/Car/nissan_gtr_32_EXP.obj",
            "OBJS/Car/textures/Main_Atlas.png"
        )

        self.cabinet = OBJModel(
            "OBJS/Cabinet/Cabinet_.obj",
            "OBJS/Cabinet/textures/Wood067_1K-JPG_Color.jpg"
        )

        self.box = OBJModel(
            "OBJS/Box/p_kardus.obj",
            "OBJS/Box/textures/kardus_albedo.png"
        )

    def init_opengl(self):

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)

        # =========================
        # ILUMINAÇÃO
        # =========================

        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)

        # Permite usar cores/texturas junto da luz
        glEnable(GL_COLOR_MATERIAL)

        glColorMaterial(
            GL_FRONT_AND_BACK,
            GL_AMBIENT_AND_DIFFUSE
        )

        # Luz ambiente global
        glLightModelfv(
            GL_LIGHT_MODEL_AMBIENT,
            (0.6, 0.6, 0.6, 1.0)
        )

        # Posição da luz
        glLightfv(
            GL_LIGHT0,
            GL_POSITION,
            (2, 5, 5, 1)
        )

        # Intensidade da luz
        glLightfv(
            GL_LIGHT0,
            GL_DIFFUSE,
            (2.0, 2.0, 2.0, 1.0)
        )

        # Brilho/reflexo
        glLightfv(
            GL_LIGHT0,
            GL_SPECULAR,
            (1.0, 1.0, 1.0, 1.0)
        )

        # Material do objeto
        glMaterialfv(
            GL_FRONT_AND_BACK,
            GL_SPECULAR,
            (1.0, 1.0, 1.0, 1.0)
        )

        glMaterialf(
            GL_FRONT_AND_BACK,
            GL_SHININESS,
            64
        )

        # =========================
        # PROJEÇÃO
        # =========================

        glMatrixMode(GL_PROJECTION)

        gluPerspective(
            45,
            self.display[0] / self.display[1],
            0.1,
            100.0
        )

        glMatrixMode(GL_MODELVIEW)
    def process_input(self):

        for event in pygame.event.get():

            if event.type == QUIT:
                return False

            if event.type == KEYDOWN:

                if event.key == K_ESCAPE:
                    return False

        self.camera.update_mouse()

        keys = pygame.key.get_pressed()

        self.camera.move(keys)

        if keys[K_q]:
            self.rot_y -= 1

        if keys[K_e]:
            self.rot_y += 1

        if keys[K_r]:
            self.rot_x -= 1

        if keys[K_f]:
            self.rot_x += 1

        return True
    def draw_model(
            self,
            model,
            position=(0, 0, 0),
            rotation=(0, 0, 0),
            scale=(1, 1, 1)
    ):

        glPushMatrix()

        # posição
        glTranslatef(*position)

        # rotação
        glRotatef(rotation[0], 1, 0, 0)
        glRotatef(rotation[1], 0, 1, 0)
        glRotatef(rotation[2], 0, 0, 1)

        # escala
        glScalef(*scale)

        model.draw()

        glPopMatrix()

    def render(self):

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glLoadIdentity()

        self.camera.apply()

        glRotatef(self.rot_x, 1, 0, 0)
        glRotatef(self.rot_y, 0, 1, 0)

        # =================================
        # CHAO
        # =================================

        self.draw_model(
            self.chao,
            position=(0, -2, 0),
            scale=(3, 0.01, 3)
        )

        # =================================
        # PAREDES
        # =================================

        self.draw_model(
            self.paredes[0],
            position=(0, 0, 3),
            scale=(3, 3, 0.1)
        )

        self.draw_model(
            self.paredes[1],
            position=(3, 0, 0),
            scale=(0.1, 3, 3)
        )

        self.draw_model(
            self.paredes[2],
            position=(-3, 0, 0),
            scale=(0.1, 3, 3)
        )

        # =================================
        # TETO
        # =================================

        self.draw_model(
            self.teto,
            position=(0, 2, 0),
            scale=(3, 0.01, 3)
        )

        # =================================
        # CARRO
        # =================================

        self.draw_model(
            self.carro,
            position=(0.3, -1.6, 0)
        )

        # =================================
        # Armário
        # =================================

        self.draw_model(
            self.cabinet,
            position=(-2, -1.6, 0),
            scale=(0.3,0.2,0.3)
        )

        # =================================
        # CAIXA
        # =================================

        self.draw_model(
            self.box,
            scale=(0.3, 0.3, 0.3),
            position=(1.8, -1.8, 1.8),
            rotation=(0, 180, 0)
        )

        pygame.display.flip()

    def run(self):

        running = True

        while running:

            self.clock.tick(60)

            running = self.process_input()

            self.render()

        pygame.quit()


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    app = OpenGLApp()

    app.run()