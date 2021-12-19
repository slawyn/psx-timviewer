import wx
import struct
import sys
from array import array

MAGIC = 0x10
TYPE_24BPP = 0x03
TYPE_16BPP = 0x02
TYPE_8BPP = 0x09
TYPE_4BPP = 0x08


class Frame(wx.Frame):

    def __init__(self, pixels, imgwidth, imgheight):
        wx.Frame.__init__(self, None, -1, 'Title', style=wx.SYSTEM_MENU | wx.CAPTION | wx.CLOSE_BOX)

        self.imgwidth = imgwidth
        self.imgheight = imgheight
        self.wimgwidth = imgwidth if imgwidth>200 else 200
        self.wimgheight = imgheight if imgheight >200 else 200
        self.offset = 40
        self.SetClientSize((self.wimgwidth, self.wimgheight+self.offset))

        self.panel =wx.Panel(self, size=self.GetSize())
        self.panel.Bind(wx.EVT_PAINT, self.on_paint)
        self.pixels = pixels
        self.selected = 0
        dd_list=[]
        sample=[]
        for i in range(len(pixels)):
            dd_list.append(str(i))

        self.dropdown_box= wx.ComboBox(self.panel, size=wx.DefaultSize, choices=sample)
        self.create_dropdown(self.dropdown_box, dd_list)
        self.dropdown_box.SetSelection(self.selected)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.dropdown_box, 0, wx.ALL, len(pixels))
        self.panel.SetSizer(sizer)

    def create_dropdown(self, widget, items):
        for item in items:
            widget.Append(item)
        widget.Bind(wx.EVT_COMBOBOX, self.on_select)


    def on_select(self, event):
        self.selected = int(self.dropdown_box.GetValue())
        self.Refresh()



    def paint(self, palette):
        dc = wx.PaintDC(self.panel)
        dc.Clear()
        x = 0
        print("selected palette:" +str(palette))
        for i in range(self.imgheight):
            for j in range(self.imgwidth):

                dc.SetPen(
                wx.Pen(wx.Colour(self.pixels[palette][x][0], self.pixels[palette][x][1], self.pixels[palette][x][2], self.pixels[palette][x][3])))
                dc.DrawPoint(j, i + self.offset )
                x = x + 1


    def on_paint(self, event=None):
        self.paint(self.selected)


#--------------------------------------------

# Read file into fmemory
# Input: name of the file
# Output: pointer to memory containing the file
def open_and_read_File(filename):
    f = open(filename, "rb")
    fmemory = []
    try:
        byte = f.read(1)
        while byte != b"":
            fmemory.append(ord(byte))
            byte = f.read(1)
    finally:
        f.close()

    return fmemory



# Change to little endian and convert 4 bytes to integer
# Input: list of 4 bytes
# Output: integer
def unpack4bytes(list1):
    bytes = array('B', list1)
    return struct.unpack('<I', bytes)[0]

# Change to little endian and convert 2 bytes to integer
# Input: list of 2 bytes
# Output: integer
def unpack2bytes(list1):
    bytes = array('B', list1)
    return struct.unpack('<h', bytes)[0]


# Read header and select appropriate function for the corresponding function
# Input: pointer to file memory
# Output: pixels, image width, image height
def process_file(fmemory):
    return process_image(fmemory)




# Convert 15 bit TBGR to 24-bit RGBA
def getpixeldata(datatable, position):
    value = datatable[position*2 :position*2 + 2]
    color = unpack2bytes(value)
    mask = 0b011111
    red = color & mask
    green = (color >> 5) & mask
    blue = (color >> 10) & mask

    # the transparent bit is on:
    if blue >= 0b100000:
        return (0, 0, 0, 255)
    return (red * 8, green * 8, blue * 8, 0)



def process_image(fmemory,):


    data_size = len(fmemory)#image_width*image_height
    image_width = 100
    image_height = 400

    print("size of data:\t%s\nimage width:\t%d\nimage height:\t%d\n"\
      % (data_size, image_width, image_height))

    # create array to hold pixels
    pixels =  [[None for _ in range(data_size)]]
    print("total number of pixels:" +str(image_height * image_width))

    x = 0
    y = 1
    # Pixel data starts after the header which is always 20 bytes
    color_data = fmemory[:]
    print(image_width*image_height)

    # every pixel consists of R G and B each 1 byte : 3 bytes in total
    
    try:
        while(y < data_size):

            # save
            pixels[0][x] = (color_data[y],color_data[y+1],color_data[y+2], 0)
            x = x + 1
            y = y + 3
            #print(y)
    except:
        print(y)
    return pixels, image_width, image_height




def main():
    print("Usage: python tim.py <name of the file>")
    filename=sys.argv[1]
    fmemory = open_and_read_File(filename)
    pixels, width, height = process_file(fmemory)

    app = wx.App(False)
    frame = Frame(pixels, width, height)

    frame.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()
