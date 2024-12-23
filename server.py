import socket
import threading
import pygame, sys
import random
import math

"""
Uses TCP instead of UDP (which would be the better choice when it comes to more intense games) but too troublesome
Approximately 360 lines of code including both client and server scripts
There are many ways to improve the overall program, like killing the thread when the socket disconnects.
"""

# Root program for the person hosting the game
class Player:
    def __init__(self, game, address):
        self.ADDRESS = address
        self.PLAYER_SIZE = 30
        self.USERNAME = "Player " + str(random.randint(0, 100))

        self.game = game

        self.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

        random_x = random.randint(0, game.display.get_width() - self.PLAYER_SIZE)
        random_y = random.randint(0, game.display.get_height() - self.PLAYER_SIZE)
        self.position = pygame.Vector2(random_x, random_y)
        self.velocity = pygame.Vector2(0, 0)

        self.left = False
        self.right = False
        self.up = False
        self.down = False

        self.SPEED = 5
        self.rect = pygame.Rect(self.position.x, self.position.y, self.PLAYER_SIZE, self.PLAYER_SIZE)

        self.last_fired = 0
        self.health = 100
        self.kills = 0


    def update(self):
        if self.left:
            self.velocity.x = -self.SPEED

        if self.right:
            self.velocity.x = self.SPEED

        if not self.right and not self.left:
            self.velocity.x = 0
        
        if self.up:
            self.velocity.y = -self.SPEED
        
        if self.down:
            self.velocity.y = self.SPEED

        if not self.up and not self.down:
            self.velocity.y = 0

        touching_left = self.position.x <= 0
        touching_right = self.position.x + self.PLAYER_SIZE >= self.game.display.get_width()
        touching_top = self.position.y <= 0
        touching_bottom = self.position.y + self.PLAYER_SIZE >= self.game.display.get_height()

        if self.velocity.length() > 0:
            if touching_left and self.velocity.x < 0:
                self.left = False
                self.position.x = 0
            elif touching_right and self.velocity.x > 0:
                self.right = False
                self.position.x = self.game.display.get_width() - self.PLAYER_SIZE
            elif touching_top and self.velocity.y < 0:
                self.up = False
                self.position.y = 0
            elif touching_bottom and self.velocity.y > 0:
                self.down = False
                self.position.y = self.game.display.get_height() - self.PLAYER_SIZE

            self.position += self.velocity.normalize() * self.SPEED


    def render(self):
        top_rect = pygame.Rect(self.position.x, self.position.y, self.PLAYER_SIZE, self.PLAYER_SIZE * .3)
        bottom_rect = pygame.Rect(self.position.x, self.position.y + top_rect.size[1], self.PLAYER_SIZE, self.PLAYER_SIZE * .7)
        bottom_color = (self.color[0] + ((255 - self.color[0]) * .3), self.color[1] + ((255 - self.color[1]) * .3), self.color[2] + ((255 - self.color[2]) * .3))

        if self.velocity.length() > 0:
            stretch_factor = 3
            bounce_interval = 120

            dy = math.sin(pygame.time.get_ticks()/bounce_interval) * stretch_factor

            top_rect.height += dy
            top_rect.width -= dy

            if dy < 0:
                top_rect.y += abs(dy * 2.5)

            bottom_rect.height += dy
            bottom_rect.width -= dy

        self.rect = pygame.Rect(top_rect.x, top_rect.y, top_rect.height + bottom_rect.height, top_rect.width)
        pygame.draw.rect(self.game.display, bottom_color, bottom_rect)
        pygame.draw.rect(self.game.display, self.color, top_rect)

        my_text = self.game.FONT.render(f"""
{self.USERNAME}
{self.health}%
{self.kills} kills
""",    True, (0, 0, 0))

        diff = self.rect.x + (self.rect.size[0]/2) - (my_text.get_width()/2)
        self.game.display.blit(my_text, (diff, self.rect.y - my_text.get_height()))


class Server:
    def __init__(self, PORT, MAX_PLAYERS, RESOLUTION):
        pygame.init()
        pygame.font.init()
        self.FONT = pygame.font.Font(None, 20)
        self.display = pygame.display.set_mode((RESOLUTION))
        pygame.display.set_caption("Little Fun Game")

        self.clock = pygame.time.Clock()

        self.players = {}
        self.bullets = []
        self.BULLET_SIZE = 10
        self.BULLET_SPEED = 8
        self.FIRE_COOLDOWN = 600  # In miliseconds

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Creating our listener socket
        self.hostname = (socket.gethostbyname(socket.gethostname()), PORT)

        try:
            self.sock.bind(("", PORT))  # Binds our socket to the given address

        except Exception as e:  # Would likely be due to the port being in use
            print("Trouble binding to the selected address. Trying another port may help.") 
            print(e)
 
        self.sock.listen(MAX_PLAYERS)
        print(f"Hosted on {self.hostname[0]}:{self.hostname[1]}")

        # Listener thread for the 'listen_conn' function
        listener = threading.Thread(target=self.listen_conn, daemon=True)
        listener.start()


    def packet_handler(self, connection : socket.socket):  # Handles incoming packets for each connection
        while True:
            data = connection.recv(1024).decode()
            
            if len(data) <= 0:  # Happens when the socket disconnects, so we handle the out of range error
                continue 

            if data[0] == '$':  # Usernames are prefixed with a $, so this is a check for that, refer to client.py
                self.players[connection].USERNAME = data[1:]
                print(f"New User Connected: {self.players[connection].USERNAME}")

            else:
                instructions = data.split(';')
                instructions.remove(instructions[-1])

                for data in instructions:
                    player = self.players[connection]

                    if data == 'a':
                        player.left = True

                    elif data == 'd':
                        player.right = True

                    elif data == 'w':
                        player.up = True

                    elif data == 's':
                        player.down = True
                    
                    elif data == 'upa':
                        player.left = False

                    elif data == 'upd':
                        player.right = False

                    elif data == 'upw':
                        player.up = False

                    elif data == 'ups':
                        player.down = False

                    if data in ['i', 'k', 'j', 'l'] and (player.last_fired + self.FIRE_COOLDOWN) < pygame.time.get_ticks():
                        player_center = pygame.Vector2(player.position.x + (player.PLAYER_SIZE/2), player.position.y + (player.PLAYER_SIZE/2))
                        bullet_vel = pygame.Vector2(0, 0)
                        player.last_fired = pygame.time.get_ticks()

                        if data == 'i':
                            bullet_vel = pygame.Vector2(0, -1)

                        elif data == 'k':
                            bullet_vel = pygame.Vector2(0, 1)

                        elif data == 'j':
                            bullet_vel = pygame.Vector2(-1, 0)

                        elif data == 'l':
                            bullet_vel = pygame.Vector2(1, 0)

                        self.bullets.append([pygame.Rect(player_center.x, player_center.y, self.BULLET_SIZE, self.BULLET_SIZE), bullet_vel, player])


    def exit(self):
        for sock in self.players:
            sock.close() 

        self.sock.close()
        pygame.quit()
        sys.exit()


    def listen_conn(self):  # Handles new connections
        while True:
            connection, address = self.sock.accept()

            print(f"New Connection Accepted: {connection}, {address}")

            self.players[connection] = Player(self, address)
            threading.Thread(target=self.packet_handler, args=(connection,), daemon=True).start()

        
    def render(self):
        self.display.fill((255, 255, 255))

        for player_conn in self.players:
            player = self.players[player_conn]
            player.render()

        for bullet in self.bullets:
            pygame.draw.rect(self.display, (40, 40, 40), bullet[0])

        pygame.display.update()


    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.exit()

            elif event.type == pygame.KEYUP:
                pass
            

    def update(self):
        for player_conn in self.players:
            player = self.players[player_conn]
            player.update()
        
        for bullet in self.bullets:
            bullet_rect : pygame.Rect = bullet[0]
            bullet_vel : pygame.Vector2 = bullet[1]

            bullet[0] = bullet_rect.move(bullet_vel.x * self.BULLET_SPEED, bullet_vel.y * self.BULLET_SPEED)

            if bullet_rect.x + self.BULLET_SIZE <= 0 or bullet_rect.x >= self.display.get_width():
                self.bullets.remove(bullet)
            elif bullet_rect.y + self.BULLET_SIZE <= 0 or bullet_rect.y >= self.display.get_height():
                self.bullets.remove(bullet)


            player_rects = [self.players[player_conn].rect for player_conn in self.players if self.players[player_conn] != bullet[2]]
            player_conns = [x for x in self.players if self.players[x] != bullet[2]]

            collisions = bullet_rect.collidelist(player_rects)  # Returns an index of the first collision
            if collisions != -1:  # Index of -1 represents no collision
                BULLET_DAMAGE = 20

                hit_player_conn = player_conns[collisions]
                self.players[hit_player_conn].health -= BULLET_DAMAGE

                if self.players[hit_player_conn].health <= 0:
                    self.players.pop(hit_player_conn)
                    bullet[2].kills += 1

                self.bullets.remove(bullet)
            


    def run(self):
        self.handle_input()
        self.render()
        self.update()
        self.clock.tick(60)


if __name__ == "__main__":
    port = int(input("Enter a server port: "))
    max_players = int(input("Enter maximum players: "))
    dimension_x = int(input("Enter map width: "))
    dimension_y = int(input("Enter map height: "))

    server = Server(port, max_players, (dimension_x, dimension_y))

    while True:
        server.run()