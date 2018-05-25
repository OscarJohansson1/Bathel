import pygame
import logging
import sys
import math
import random

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SCREEN_SIZE = (600, 600)

class Controller():

    PRESTART = 1
    RUNNING = 2
    GAMEOVER = 3

    def __init__(self):
        self.events = {}
        self.keymap = {}

        pygame.init()
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        pygame.display.set_caption('Bathel')
        self.clock = pygame.time.Clock()

        self.register_eventhandler(pygame.QUIT, self.quit)
        self.register_key(pygame.K_ESCAPE, self.quit)


        self.world = World(self)
        self.rocket = Rocket(self)
        self.bullets = []
        self.stones = []

        self.game_state = Controller.PRESTART

        self.fps = 60
        self.count = 0
        self.level = 0

    def run(self):
        while True:
            # -- Handle all events -------------------------------------------
            for event in pygame.event.get():
                logger.debug('Handling event {}'.format(event))

                # Handle events
                for event_type, callbacks in self.events.items():
                    if event.type == event_type:
                        for callback in callbacks:
                            callback(event)

                # Handle keypresses
                if event.type == pygame.KEYDOWN:
                    for key in self.keymap.keys():
                        if event.key == key:
                            for callback in self.keymap[key]:
                                callback(event)
                        if event.key == pygame.K_r:
                            self.game_state = Controller.PRESTART


            self.rocket.update_degree()
            self.rocket.update()
            for bullet in self.bullets:
                bullet.update()
            for stone in self.stones:
                stone.update()

            for stone in self.stones:
                pyth_x = abs(self.rocket.x - stone.x)
                pyth_y = abs(self.rocket.y - stone.y)

                if (((pyth_x - self.rocket.half_side + 2) ** 2) +
                   ((pyth_y - self.rocket.half_side + 2) ** 2) <
                   stone.radius ** 2 + self.rocket.half_side):
                    self.game_state = Controller.GAMEOVER
                if (pyth_y < (stone.radius + self.rocket.half_side) and
                    (self.rocket.x - self.rocket.half_side) < stone.x <
                    (self.rocket.x + self.rocket.half_side)):
                    self.game_state = Controller.GAMEOVER
                if (pyth_x < (stone.radius + self.rocket.half_side) and
                    (self.rocket.y - self.rocket.half_side) < stone.y <
                    (self.rocket.y + self.rocket.half_side)):
                    self.game_state = Controller.GAMEOVER

            for stone in self.stones:
                for bullet in self.bullets:
                    pyth_x = abs(bullet.x - stone.x)
                    pyth_y = abs(bullet.y - stone.y)

                    if (pyth_x ** 2 + pyth_y ** 2) < (bullet.radius + stone.radius) ** 2:
                        self.bullets.remove(bullet)
                        stone.radius -= 3
                        if stone.radius < 20:
                            self.stones.remove(stone)
                        break

            if len(self.stones) == 0:
                self.level += 1
                for x in range(self.level):
                    self.stones.append(Stone(self))




            while len(self.bullets) > 20:
                self.bullets.pop(0)

            if self.game_state == Controller.PRESTART:
                logger.debug('restarting...')
                self.stones = []
                self.level = 0

                self.game_state = Controller.RUNNING

            if self.game_state == Controller.RUNNING:
                self.world.draw()
                self.rocket.draw()
                for bullet in self.bullets:
                    bullet.draw()
                for stone in self.stones:
                    stone.draw()



            white = (238, 238, 238)
            gameover_message = 'Gameover!'
            font_gameover = pygame.font.Font('Fonts/SpaceMono.ttf', 50)
            text_gameover = font_gameover.render(gameover_message, 1, white)


            if self.game_state == Controller.GAMEOVER:
                self.screen.blit(text_gameover, (SCREEN_SIZE[0] / 2 - 125, SCREEN_SIZE[1] / 2 - 25))

            # -- Display -----------------------------------------------------
            pygame.display.flip()

            # -- Updates per second ------------------------------------------
            self.clock.tick(self.fps)

    def quit(self, event):
        logger.info('Quitting...')
        pygame.quit()
        sys.exit()

    def register_eventhandler(self, event_type, callback):
        logger.debug('Registering event handler ({}, {})'.format(event_type, callback))
        if self.events.get(event_type):
            self.events[event_type].append(callback)
        else:
            self.events[event_type] = [callback]

    def register_key(self, key, callback):
        logger.debug('Binding key {} to {}.'.format(key, callback))
        if self.keymap.get(key):
            self.keymap[key].append(callback)
        else:
            self.keymap[key] = [callback]

class World():
    def __init__(self, controller):
        self.controller = controller
        self.screen = controller.screen

    # -- Draw world function -------------------------------------------------
    def draw(self):
        surface = pygame.Surface(SCREEN_SIZE)
        surface.fill(pygame.Color('#EEEEEE'), (0, 0, SCREEN_SIZE[0], SCREEN_SIZE[1]))
        surface.fill(pygame.Color('#111111'), (5, 5, SCREEN_SIZE[0] - 10, SCREEN_SIZE[1] - 10))

        self.screen.blit(surface, (0, 0))

class Rocket():
    def __init__(self, controller):
        self.controller = controller
        self.screen = controller.screen

        self.controller.register_eventhandler(pygame.KEYDOWN, self.keydown)
        self.controller.register_eventhandler(pygame.KEYUP, self.keyup)

        self.color = pygame.Color('#166BCC')

        self.correction = 3

        self.half_side = 10
        self.full_side = 2 * self.half_side
        self.placements = 2 + self.half_side / 2

        self.degree = 0

        self.length = 10000000
        self.s_length = 10
        self.start_x = 0
        self.start_y = 0
        self.end_x = 0
        self.end_y = 0

        self.firekey = False
        self.bullets = []
        self.count = 0

        self.restart()

    # -- Draw the rocket -----------------------------------------------------
    def draw(self):
        surface = pygame.Surface((self.full_side, self.full_side),
                                flags=pygame.SRCALPHA)
        pygame.draw.polygon(surface, self.color, (
                            (0, self.full_side), (self.full_side, self.full_side),
                            (self.half_side, 0)))
        surface = pygame.transform.rotate(surface, self.degree)

        self.screen.blit(surface, (self.x - self.half_side, self.y - self.half_side))

        surface2 = pygame.Surface((SCREEN_SIZE), flags=pygame.SRCALPHA)
        if self.main_booster == "boost_down":
            pygame.draw.line(surface2, self.color, (self.x, self.y),
                                (self.end_x, self.end_y))

            self.screen.blit(surface2, (0, 0))


    # -- Rocket-movement -----------------------------------------------------
    def update_degree(self):
        if self.main_booster == "boost_up":
            if self.right_booster:
                self.degree -= 4
            if self.left_booster:
                self.degree += 4
        elif self.main_booster == "boost_down":
            if self.right_booster:
                self.degree -= 0.5
            if self.left_booster:
                self.degree += 0.5
        else:
            if self.right_booster:
                self.degree -= 8
            if self.left_booster:
                self.degree += 8
        if self.degree < 0:
            self.degree = 360 + (self.degree % 360)
        if self.degree >= 360:
            self.degree = self.degree % 360


    def update(self):
        # -- Calculate new speed and direction -------------------------------
        if self.main_booster == "boost_up":
            self.x_speed = math.cos(math.radians(90 + self.degree)) * self.acceleration
            self.y_speed = -math.sin(math.radians(90 + self.degree)) * self.acceleration
        if self.main_booster == "boost_down":
            self.end_x = math.cos(math.radians(90 + self.degree)) * self.length
            self.end_y = -math.sin(math.radians(90 + self.degree)) * self.length
            self.start_x = self.x + math.cos(math.radians(90 + self.degree)) * self.s_length
            self.start_y = self.y - math.sin(math.radians(90 + self.degree)) * self.s_length
        if not self.main_booster == "boost_up":
            self.y_speed = self.y_speed / self.deceleration
            self.x_speed = self.x_speed / self.deceleration

        # -- Building walls --------------------------------------------------
        if self.x < self.half_side + self.correction:
            self.x = self.half_side + self.correction
            self.x_speed = 0

        elif self.x > SCREEN_SIZE[0] - self.half_side - 2 * self.correction:
            self.x = SCREEN_SIZE[0] - self.half_side - 2 * self.correction
            self.x_speed = 0

        if self.y < self.half_side + self.correction:
            self.y = self.half_side + self.correction
            self.y_speed = 0

        elif self.y > SCREEN_SIZE[1] - self.half_side - 2 * self.correction:
            self.y = SCREEN_SIZE[1] - self.half_side - 2 * self.correction
            self.y_speed = 0

        # -- Calculate new position ------------------------------------------
        self.y = self.y + self.y_speed
        self.x = self.x + self.x_speed

        # -- Update all bullets ----------------------------------------------
        self.count += 1
        if self.firekey == False:
            self.count = 0

        if self.firekey:
            if self.count % 10 == 1:
                logger.debug('{}, {}, {}'.format(self.degree, self.x, self.y))
                self.controller.bullets.append(Bullet(self, self.degree, (self.x, self.y)))

    # -- Setting the rocket back to startstate -------------------------------
    def restart(self):
        self.x = SCREEN_SIZE[0] / 2
        self.y = SCREEN_SIZE[1] / 4 * 3
        self.x_speed = 0
        self.y_speed = 0
        self.acceleration = 5
        self.deceleration = 1.05
        self.main_booster = False
        self.right_booster = False
        self.left_booster = False

    # -- Keys for controlling the rocket -------------------------------------
    def keydown(self, event):
        if event.key == pygame.K_UP or event.key == pygame.K_w:
            self.main_booster = "boost_up"

        if event.key == pygame.K_DOWN or event.key == pygame.K_s:
            self.main_booster = "boost_down"

        if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
            self.right_booster = True

        if event.key == pygame.K_LEFT or event.key == pygame.K_a:
            self.left_booster = True

        if event.key == pygame.K_SPACE:
            self.firekey = True

    # -- Keys for controlling the rocket -------------------------------------
    def keyup(self, event):
        if event.key == pygame.K_UP or event.key == pygame.K_w:
            self.main_booster = False

        if event.key == pygame.K_DOWN or event.key == pygame.K_s:
            self.main_booster = False

        if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
            self.right_booster = False

        if event.key == pygame.K_LEFT or event.key == pygame.K_a:
            self.left_booster = False

        if event.key == pygame.K_SPACE:
            self.firekey = False

class Bullet():
    def __init__(self, controller, direction, position):
        self.controller = controller
        self.screen = controller.screen

        self.color = pygame.Color('#2DBA52')
        self.diameter = 10
        self.radius = 5
        self.mid_of_circle = (self.radius, self.radius)

        self.acceleration = 7

        self.degree = direction

        self.x_direction = 0
        self.y_direction = 0
        self.bullet_direction()

        self.x, self.y = position


    def draw(self):
        surface = pygame.Surface((self.diameter, self.diameter),
                                    flags = (pygame.SRCALPHA))
        pygame.draw.circle(surface, self.color, (self.mid_of_circle), self.radius)
        self.screen.blit(surface, (self.x - self.radius, self.y - self.radius))


    def bullet_direction(self):
        self.x_direction = math.cos(math.radians(90 + self.degree))
        self.y_direction = -math.sin(math.radians(90 + self.degree))


    def update(self):
        # -- Calculate new speed and direction -------------------------------
        old_x = self.x
        old_y = self.y

        self.x = self.x + self.x_direction * self.acceleration
        self.y = self.y + self.y_direction * self.acceleration
        dist = ((old_x - self.x) ** 2 + (old_y - self.y) ** 2) ** (1/2)
        logger.debug('Bullet travelled distance {}'.format(dist))


    def __repr__(self):
        return '<Bullet: {:x}>'.format(id(self))

class Stone():
    def __init__(self, controller):
        self.controller = controller
        self.screen = controller.screen

        self.color = pygame.Color('#BA1215')

        self.radius = 38

        self.mid_of_circle = (self.radius, self.radius)
        self.diameter = self.radius * 2

        self.low_roll = -100
        self.high_roll = 100
        self.total = 300 / 100

        self.x = random.randint(self.radius, SCREEN_SIZE[0] - self.radius)
        self.y = random.randint(self.radius, SCREEN_SIZE[1] - self.radius)

        rocket = self.controller.rocket
        if rocket.x - rocket.half_side < self.x < rocket.x + rocket.half_side + 50:
            if rocket.y - rocket.half_side < self.y < rocket.y + rocket.half_side + 50:
                self.x = random.randint(self.radius, SCREEN_SIZE[0] - self.radius)
                self.y = random.randint(self.radius, SCREEN_SIZE[1] - self.radius)

        self.y_speed = random.randint(self.low_roll, self.high_roll) / 100
        self.x_speed = self.total - self.y_speed

    # -- Draw stone function -------------------------------------------------
    def draw(self):
        surface = pygame.Surface((self.diameter, self.diameter),
                                    flags = (pygame.SRCALPHA))
        pygame.draw.circle(surface, self.color, (self.mid_of_circle), self.radius)
        self.screen.blit(surface, (self.x - self.radius, self.y - self.radius))

    # -- Stone movement ------------------------------------------------------
    def update(self):
        self.y = self.y + self.y_speed
        self.x = self.x + self.x_speed

        if self.x < self.radius:
            self.x_speed = -self.x_speed
        if self.x > SCREEN_SIZE[0] - self.radius:
            self.x_speed = -self.x_speed
        if self.y < self.radius:
            self.y_speed = -self.y_speed
        if self.y > SCREEN_SIZE[1] - self.radius:
            self.y_speed = -self.y_speed


if __name__ == "__main__":
    c = Controller()
    c.run()
