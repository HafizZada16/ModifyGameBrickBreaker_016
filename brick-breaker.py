import tkinter as tk
import random
import json


class GameObject(object):
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)


class Ball(GameObject):
    def __init__(self, canvas, x, y, game):
        self.game = game
        self.radius = 10
        self.direction = [1, -1]
        # increase the below value to increase the speed of ball
        self.speed = 5
        item = canvas.create_oval(x-self.radius, y-self.radius,
                                  x+self.radius, y+self.radius,
                                  fill='white')
        super(Ball, self).__init__(canvas, item)

    def update(self):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] <= 0 or coords[2] >= width:
            self.direction[0] *= -1
        if coords[1] <= 0:
            self.direction[1] *= -1
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

    def collide(self, game_objects):
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5
        hit_brick = False  # Menandai apakah bola mengenai brick

        for game_object in game_objects:
            if isinstance(game_object, Brick):
                hit_brick = True  # Menandai bahwa bola mengenai brick
                game_object.hit()  # Menghantam brick
                self.game.update_score(10)  # Memanggil metode update_score dari Game

        if hit_brick:
            self.direction[1] *= -1  # Membalik arah vertikal jika mengenai brick
            self.speed += 0.1  # Menambah kecepatan bola setiap kali memantul
            return  # Keluar dari metode setelah menangani brick

        if len(game_objects) == 1:
            game_object = game_objects[0]
            if isinstance(game_object, Paddle):  # Pastikan hanya mempengaruhi Paddle
                coords = game_object.get_position()
                # Menyesuaikan arah bola berdasarkan posisi mendarat pada paddle
                paddle_center = (coords[0] + coords[2]) * 0.5
                offset = x - paddle_center
                normalized_offset = offset / (game_object.width / 2)  # Normalisasi offset
                self.direction[0] = normalized_offset  # Mengubah arah horizontal
                self.direction[1] *= -1  # Membalik arah vertikal


class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 80
        self.height = 10
        self.ball = None
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill='#F96E2A')
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def move(self, offset):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] + offset >= 0 and coords[2] + offset <= width:
            super(Paddle, self).move(offset, 0)
            if self.ball is not None:
                self.ball.move(offset, 0)


class Brick(GameObject):
    COLORS = {1: '#F95454', 2: '#0D92F4', 3: '#00FF9C', 4: '#117554'} # Menambah 1 step lagi diatas step 3

    def __init__(self, canvas, x, y, hits):
        self.width = 75
        self.height = 20
        self.hits = hits
        color = Brick.COLORS[hits]
        item = canvas.create_rectangle(x - self.width / 2,
                                       y - self.height / 2,
                                       x + self.width / 2,
                                       y + self.height / 2,
                                       fill=color, tags='brick')
        super(Brick, self).__init__(canvas, item)

    def hit(self):
        self.hits -= 1
        if self.hits == 0:
            self.explode()  # Panggil efek ledakan
        else:
            self.canvas.itemconfig(self.item,
                                   fill=Brick.COLORS[self.hits])

    def explode(self):
        # Menentukan titik tengah untuk partikel
        center_x = (self.get_position()[0] + self.get_position()[2]) / 2
        center_y = (self.get_position()[1] + self.get_position()[3]) / 2

        # Membuat partikel ledakan
        for _ in range(30):  # Jumlah partikel
            x_offset = random.randint(-30, 30)  # Offset acak untuk menyebar
            y_offset = random.randint(-15, 15)
            particle = self.canvas.create_oval(
                center_x + x_offset - 5, 
                center_y + y_offset - 5,
                center_x + x_offset + 5, 
                center_y + y_offset + 5,
                fill='yellow', outline='orange', tags='explosion'
            )
            # Hapus partikel setelah 100ms
            self.canvas.after(100, lambda p=particle: self.canvas.delete(p))  

        self.delete()  # Hapus brick setelah efek ledakan


class Game(tk.Frame):
    def __init__(self, master):
        super(Game, self).__init__(master)
        self.lives = 3
        self.width = 610
        self.height = 400
        self.score = 0
        self.canvas = tk.Canvas(self, bg='#C9E6F0',
                                width=self.width,
                                height=self.height,)
        self.canvas.pack()
        self.pack()

        self.items = {}
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width/2, 326)
        self.items[self.paddle.item] = self.paddle
        # adding brick with different hit capacities - 4,3,2 and 1
        for x in range(5, self.width - 5, 75):
            self.add_brick(x + 37.5, 50, 4)
            self.add_brick(x + 37.5, 70, 3)
            self.add_brick(x + 37.5, 90, 2)
            self.add_brick(x + 37.5, 110, 1)

        self.hud = None
        self.score_text = self.draw_text(self.width - 50, 20, 'Score: 0', 15)  # Menampilkan skor di pojok kanan atas
        self.setup_game()
        self.canvas.focus_set()
        self.canvas.bind('<Left>',
                         lambda _: self.paddle.move(-10))
        self.canvas.bind('<Right>',
                         lambda _: self.paddle.move(10))
        self.canvas.bind('<Motion>', self.move_paddle_with_mouse)  # Mengikat gerakan mouse

    def setup_game(self):
        self.add_ball()
        self.update_lives_text()
        self.text = self.draw_text(300, 200, 'Press Space to start')
        self.canvas.bind('<space>', lambda _: self.start_game())
        self.draw_spikes()

    def draw_spikes(self):
        spike_height = 20  # Tinggi jarum
        spike_width = 8   # Lebar jarum
        for x in range(0, self.width, 12):  # Menggambar jarum setiap 30 piksel
            self.canvas.create_polygon(
                x, self.height - 12,  # Mengangkat jarum lebih tinggi dari dasar
                x - spike_width, self.height + spike_height - 10,  # Mengubah posisi y untuk jarum
                x + spike_width, self.height + spike_height - 10,  # Mengubah posisi y untuk jarum
                fill='black', outline='black'
            )

    def add_ball(self):
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        self.ball = Ball(self.canvas,x, 310, self)
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def draw_text(self, x, y, text, size='30'):
        font = ('Fixedsys', size)
        return self.canvas.create_text(x, y, text=text,
                                       font=font)

    def update_lives_text(self):
        text = 'Lives: %s' % self.lives
        if self.hud is None:
            self.hud = self.draw_text(50, 20, text, 15)
        else:
            self.canvas.itemconfig(self.hud, text=text)

    def start_game(self):
        self.canvas.unbind('<space>')
        self.canvas.delete(self.text)
        self.paddle.ball = None
        self.game_loop()

    def game_loop(self):
        self.check_collisions()
        num_bricks = len(self.canvas.find_withtag('brick'))
        if num_bricks == 0: 
            self.ball.speed = None
            self.draw_text(300, 200, 'You win! You the Breaker of Bricks.')
        elif self.ball.get_position()[3] >= self.height: 
            self.ball.speed = None
            self.ball.canvas.itemconfig(self.ball.item, fill='red')  # Mengubah warna bola menjadi merah
            self.lives -= 1
            if self.lives < 0:
                self.draw_text(300, 200, 'You Lose! Game Over!')
            else:
                self.after(1000, self.setup_game)
        else:
            self.ball.update()
            self.after(50, self.game_loop)

    def check_collisions(self):
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]
        self.ball.collide(objects)

    def move_paddle_with_mouse(self, event):
        # Menggerakkan paddle berdasarkan posisi mouse
        paddle_coords = self.paddle.get_position()
        new_x = event.x
        width = self.canvas.winfo_width()
        if new_x >= self.paddle.width / 2 and new_x <= width - self.paddle.width / 2:
            self.paddle.move(new_x - paddle_coords[0] - self.paddle.width / 2)

    def update_score(self, points):
        self.score += points
        self.canvas.itemconfig(self.score_text, text='Score: %s' % self.score)  # Memperbarui teks skor


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Break those Bricks!')
    game = Game(root)
    game.mainloop()