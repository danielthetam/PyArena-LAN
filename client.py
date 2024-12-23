import pygame, sys
import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_ip = input("Enter server IP: ")
server_port = int(input("Enter server port: "))

LOCAL_IP = socket.gethostbyname(socket.gethostname())

s.connect((server_ip, server_port))

username = input("Enter username: ")
s.send(f"${username}".encode())

class Client:
    def __init__(self):
        pygame.init()
        self.display = pygame.display.set_mode((200, 200))

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_a:
                        s.send("a;".encode())

                    elif event.key == pygame.K_d:
                        s.send("d;".encode())

                    elif event.key == pygame.K_w:
                        s.send("w;".encode())

                    elif event.key == pygame.K_s:
                        s.send("s;".encode())

                    if event.key == pygame.K_i:
                        s.send("i;".encode())

                    elif event.key == pygame.K_k:
                        s.send("k;".encode())

                    elif event.key == pygame.K_j:
                        s.send("j;".encode())

                    elif event.key == pygame.K_l:
                        s.send("l;".encode())

                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_a:
                        s.send("upa;".encode())

                    elif event.key == pygame.K_d:
                        s.send("upd;".encode())

                    elif event.key == pygame.K_w:
                        s.send("upw;".encode())

                    elif event.key == pygame.K_s:
                        s.send("ups;".encode())

                elif event.type == pygame.QUIT:
                    s.close()
                    pygame.quit()
                    sys.exit()

            self.display.fill((0, 0, 0)) 
            pygame.display.update()

client = Client()
client.run()