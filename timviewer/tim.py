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
        self.paint(self.selected)



    def paint(self, palette):
        dc = wx.PaintDC(self.panel)
        dc.Clear()
        x = 0
        print "selected palette:" +str(palette)
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
        while byte != "":
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

    # Reading header 8 bytes: for all types
    magic = unpack4bytes(fmemory[0:4])
    tim_type = unpack4bytes(fmemory[4:8])
    if magic != MAGIC:
        print "file is not a .tim image file"
        return [],0,0

    print "magic:\t%s\ntype:\t%d" % (hex(magic), tim_type)

    if tim_type == TYPE_24BPP:
        return process_24bpp(fmemory)

    elif tim_type == TYPE_16BPP:
        return process_16bpp(fmemory)

    # Reading header 12 bytes: for types with palettes
    end_of_clut = unpack4bytes(fmemory[8:12])+8     # offset to end of clut
    vramx      = unpack2bytes(fmemory[12:14])      # psx specific(optional)
    vramy      = unpack2bytes(fmemory[14:16])      # psx specific(optional)
    clut_size  = unpack2bytes(fmemory[16:18])     # size of each clut
    clut_nb     = unpack2bytes(fmemory[18:20])    # number of cluts

    print "end of clut:\t%s\nclut size:\t%d\number of cluts:\t%d\n" % (hex(end_of_clut), clut_size, clut_nb)

    if tim_type == TYPE_8BPP:
        return process_8bpp(fmemory, clut_size, clut_nb, end_of_clut)
    elif tim_type == TYPE_4BPP:
        return process_4bpp(fmemory, clut_size, clut_nb, end_of_clut)
    else:
        print "Unrecognized .tim file type"


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



def process_24bpp(fmemory,):

    data_size = unpack4bytes(fmemory[8:12])-0x14+8   # total size of image data
    image_width = int(unpack2bytes(fmemory[16:18]))  # width of the image
    image_width = image_width*2/3                    # for 24bpp width has to be devided by 1.5
    image_height = unpack2bytes(fmemory[18:20])      # height of the image

    print "size of data:\t%s\nimage width:\t%d\nimage height:\t%d\n"\
      % (data_size, image_width, image_height)

    # create array to hold pixels
    pixels =  [[None for _ in range(image_height * image_width)]]
    print "total number of pixels:" +str(image_height * image_width)

    x = 0
    y = 0
    # Pixel data starts after the header which is always 20 bytes
    color_data = fmemory[0x14:]
    print image_width*image_height

    # every pixel consists of R G and B each 1 byte : 3 bytes in total
    while(y < data_size):

        # save
        pixels[0][x] = (color_data[y],color_data[y+1],color_data[y+2],0)
        x = x + 1
        y = y + 3
        #print y

    return pixels, image_width, image_height


def process_16bpp(fmemory):

    offset = 8
    data_size = unpack2bytes(fmemory[offset:offset + 2])-0x14+8   # total size of image data - the offset
    image_width = unpack2bytes(fmemory[offset + 8:offset + 10])    # width of the image:
    image_height = unpack2bytes(fmemory[offset + 10:offset + 12])  # height of the image

    print "size of data:\t%s\nimage width:\t%d\nimage height:\t%d\n"\
      % (data_size, image_width, image_height)

    # create array to hold pixels
    pixels =  [[None for _ in range(image_height * image_width)]]
    print "total number of pixels:" +str(image_height * image_width)
    x = 0

    # color data follows the header which is always 20 bytes
    color_data=fmemory[0x14:]

    # each pixel consists of 2 bytes TBGR
    while(x*2 < data_size):

        pixels[0][x] = getpixeldata(color_data, x)
        x = x + 1

    return pixels, image_width, image_height


def process_8bpp(fmemory, clut_size, clut_nb, end_of_clut):


    data_size = unpack4bytes(fmemory[end_of_clut:end_of_clut +4])  # total size of image data
    image_orgx = unpack2bytes(fmemory[end_of_clut + 4:end_of_clut + 6]) #not important
    image_orgy = unpack2bytes(fmemory[end_of_clut + 6:end_of_clut + 8]) #not important

    image_width = unpack2bytes(
        fmemory[end_of_clut + 8:end_of_clut + 10]) *2  # width of the image: should be multiplied by 2 for 8bpp
    image_height = unpack2bytes(
        fmemory[end_of_clut + 10:end_of_clut + 12])    # height of the image

    print "size of data + 0x0C:\t%s\nimage orgX:\t%d\nimage orgY:\t%d\nimage width:\t%d\nimage height:\t%d\n"\
          % (hex(data_size), image_orgx, image_orgy, image_width, image_height)

    # Clut is starting right after the header and contains 2 bytes per pixel
    # 512 bytes per clut in 8bpp
    # There can more than one clut
    clut_memory=fmemory[20:end_of_clut]
    clut = [[clut_memory[clut_size * 2 *_2  + _1] for _1 in range(clut_size * 2)] for _2 in range(clut_nb)]

    # indices following the cluts
    offset = end_of_clut + 12
    indices=fmemory[offset:]

    # array to hold all the pixels
    pixels =  [[None for _ in range(image_height * image_width)] for _ in range(len(clut))]



    for x in range(len(clut)):
        for i in range(image_height * image_width):
            position = indices[i]
            pixels[x][i] = getpixeldata(clut[x], position)


    print "number of palettes is:" + str(len(pixels))
    return pixels,image_width, image_height


def process_4bpp(fmemory, clut_size, clut_nb, end_of_clut):

    # Read the rest of the header
    data_size = unpack4bytes(fmemory[end_of_clut:end_of_clut +4])  # total size of image data
    image_orgx = unpack2bytes(fmemory[end_of_clut + 4:end_of_clut + 6]) # not important
    image_orgy = unpack2bytes(fmemory[end_of_clut + 6:end_of_clut + 8]) # not important

    image_width = unpack2bytes(
        fmemory[end_of_clut + 8:end_of_clut + 10]) *4  # width of the image: should be multiplied by  4 for 4bpp
    image_height = unpack2bytes(
        fmemory[end_of_clut + 10:end_of_clut + 12])   # height of the image

    print "size of data + 0x0C:\t%s\nimage orgX:\t%d\nimage orgY:\t%d\nimage width:\t%d\nimage height:\t%d\n"\
          % (hex(data_size), image_orgx, image_orgy, image_width, image_height)

    # Clut is starting right after the header and contains 2 bytes per color
    # 32 bytes per clut in 4bpp
    # There can more than one clut
    clut_memory=fmemory[20:end_of_clut]
    clut = [[clut_memory[clut_size * 2 *_2  + _1] for _1 in range(clut_size * 2)] for _2 in range(clut_nb)]

    # indices following the cluts
    offset = end_of_clut + 12
    indices=fmemory[offset:]

    # total amount of pixels
    total = image_height * image_width


    # array to hold pixels
    pixels =  [[None for _ in range(total)] for _ in range(len(clut))]


    for x in range(len(clut)):
        i=0
        j=0
        while(j!= total/2):

            position = indices[j]
            # two nibbles in 1 byte of position contain information about 2 pixels
            # the second nibble about the first pixel the first nibble about the second pixel
            pixels[x][i] = getpixeldata(clut[x], position & 0b00001111)
            pixels[x][i+1] = getpixeldata(clut[x], position >> 4)
            i=i+2
            j=j+1


    print "number of palettes is:" + str(len(pixels))

    return pixels, image_width, image_height


def main():
    print "Usage: python tim.py <name of the file>"
    filename=sys.argv[1]
    fmemory = open_and_read_File(filename)
    pixels, width, height = process_file(fmemory)

    app = wx.App(False)
    frame = Frame(pixels, width, height)

    frame.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()
