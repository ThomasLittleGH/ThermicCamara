import renderImageToWindow
import time

data = [[0]*100] * 100
while True:
    for y in range(100):
        for x in range(100):
            #Take pic, send to array, send array to image.
            # Send array to update image window.
            data[y][x] = 100 # place holder

            renderImageToWindow.render(data)
            print("Current line (x,y): " + str(x) + " " + str(y))

            time.sleep(100)