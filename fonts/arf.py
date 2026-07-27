import sys
from PIL import ImageFont
from PIL import BdfFontFile

with open(sys.argv[1],"rb") as bdf_file:
    font_file=BdfFontFile.BdfFontFile(bdf_file)

font_file.save("oledfont.pil")
