"""
Taken from https://github.com/Benjamin-Dobell/s3tc-dxt-decompression/blob/master/s3tc.cpp
"""
def dxt1(data: bytes, width: int, height: int) -> bytearray:
    "dxt1 to raw"
    print(width, height)
    width = max(4, width)
    height = max(4, height)
    final = bytearray(width*height*3)

    pointer = 0
    for y in range(height//4):
        for x in range(width//4):
            color0 = int.from_bytes(data[pointer:pointer+2], 'little')
            color1 = int.from_bytes(data[pointer+2:pointer+4], 'little')
            
            temp = (color0 >> 11) * 255 + 16
            r0 = ((temp//32 + temp)//32) % 256
            temp = ((color0 & 0x07E0) >> 5) * 255 + 32
            g0 = ((temp//64 + temp)//64) % 256
            temp = (color0 & 0x001F) * 255 + 16
            b0 = ((temp//32 + temp)//32) % 256     

            temp = (color1 >> 11) * 255 + 16
            r1 = ((temp//32 + temp)//32) % 256
            temp = ((color1 & 0x07E0) >> 5) * 255 + 32
            g1 = ((temp//64 + temp)//64) % 256
            temp = (color1 & 0x001F) * 255 + 16
            b1 = ((temp//32 + temp)//32) % 256             

            code = int.from_bytes(data[pointer+4:pointer+8], 'little')

            for j in range(4):
                for i in range(4):
                    positionCode = (code >> 2*(4*j+i)) & 0x03
                    if color0 > color1:
                        if positionCode == 0:
                            finalColor = (r0, g0, b0)
                        elif positionCode == 1:
                            finalColor = (r1, g1, b1)
                        elif positionCode == 2:
                            finalColor = ((2*r0+r1)//3, (2*g0+g1)//3, (2*b0+b1)//3)
                        elif positionCode == 3:
                            finalColor = ((r0+2*r1)//3, (g0+2*g1)//3, (b0+2*b1)//3)
                    else:
                        if positionCode == 0:
                            finalColor = (r0, g0, b0)
                        elif positionCode == 1:
                            finalColor = (r1, g1, b1)
                        elif positionCode == 2:
                            finalColor = ((r0+r1)//2, (g0+g1)//2, (b0+b1)//2)
                        elif positionCode == 3:
                            finalColor = (0, 0, 0)
                    
                    final[((y*4 + j) * width + (x*4 + i))*3] = finalColor[0]
                    final[((y*4 + j) * width + (x*4 + i))*3+1] = finalColor[1]
                    final[((y*4 + j) * width + (x*4 + i))*3+2] = finalColor[2]
            pointer += 8  
    print('dxt1')
    return final   


def DecompressBlockDXT5(x: int, y: int, width: int, blockStorage: bytes, image: bytearray):
    print("dxt5")
    """
    // unsigned long x:                     x-coordinate of the first pixel in the block.
    // unsigned long y:                     y-coordinate of the first pixel in the block.
    // unsigned long width:                 width of the texture being decompressed.
    // unsigned long height:                height of the texture being decompressed.
    // const unsigned char *blockStorage:   pointer to the block to decompress.
    // unsigned long *image:                pointer to image where the decompressed pixel data should be stored.
    """
    blockStorage_index = 0
    alpha0 = blockStorage[blockStorage_index]
    alpha1 = blockStorage[blockStorage_index+1]

    bits = blockStorage[blockStorage_index+2:blockStorage_index+8]
    alphaCode1 = bits[2] | (bits[3] << 8) | (bits[4] << 16) | (bits[5] << 24)
    alphaCode2 = bits[0] | (bits[1] << 8)

    color0 = int.from_bytes(blockStorage[blockStorage_index+8:blockStorage_index+10], "little")
    color1 = int.from_bytes(blockStorage[blockStorage_index+10:blockStorage_index+12], "little")
    used: list[tuple] = []

    temp = (color0 >> 11) * 255 + 16
    r0 = ((temp//32 + temp)//32) % 256
    temp = ((color0 & 0x07E0) >> 5) * 255 + 32
    g0 = ((temp//64 + temp)//64)
    temp = (color0 & 0x001F) * 255 + 16
    b0 = ((temp//32 + temp)//32)

    temp = (color1 >> 11) * 255 + 16
    r1 = ((temp//32 + temp)//32) % 256
    temp = ((color1 & 0x07E0) >> 5) * 255 + 32
    g1 = ((temp//64 + temp)//64) % 256
    temp = (color1 & 0x001F) * 255 + 16
    b1 = ((temp//32 + temp)//32) % 256

    code = int.from_bytes(blockStorage[blockStorage_index+12:blockStorage_index+16], "little")

    for j in range(4):
        for i in range(4):
            alphaCodeIndex = 3*(4*j+i)

            if alphaCodeIndex <= 12:
                alphaCode = (alphaCode2 >> alphaCodeIndex) & 0x07
            elif alphaCodeIndex == 15:
                alphaCode = (alphaCode2 >> 15) | ((alphaCode1 << 1) & 0x06)
            else:
                alphaCode = (alphaCode1 >> (alphaCodeIndex - 16)) & 0x07

            if alphaCode == 0:
                finalAlpha = alpha0
            elif alphaCode == 1:
                finalAlpha = alpha1
            else:
                if alpha0 > alpha1:
                    finalAlpha = ((8-alphaCode)*alpha0 + (alphaCode-1)*alpha1)//7
                else:
                    if alphaCode == 6:
                        finalAlpha = 0
                    elif alphaCode == 7:
                        finalAlpha = 255
                    else:
                        finalAlpha = ((6-alphaCode)*alpha0 + (alphaCode-1)*alpha1)//5

            colorCode = (code >> 2*(4*j+i)) & 0x03

            if colorCode == 0:
                finalColor = (r0, g0, b0, finalAlpha)
            elif colorCode == 1:
                finalColor = (r1, g1, b1, finalAlpha)
            elif colorCode == 2:
                finalColor = ((2*r0+r1)//3, (2*g0+g1)//3, (2*b0+b1)//3, finalAlpha)
            elif colorCode == 3:
                finalColor = ((r0+2*r1)//3, (g0+2*g1)//3, (b0+2*b1)//3, finalAlpha)

            # print(finalColor)
            if x + i < width:
                if (x+i, y+j) in used:
                    print('used')
                used.append((x+i, y+j))
                # print(x, y, finalColor)
                image[((y + j) * width + (x + i))*4] = finalColor[0]
                image[((y + j) * width + (x + i))*4+1] = finalColor[1]
                image[((y + j) * width + (x + i))*4+2] = finalColor[2]
                image[((y + j) * width + (x + i))*4+3] = 255

def block_decompress_image_dxt5(width: int, height: int, blockStorage: bytes) -> bytearray:
    blockCountX = (width + 3) // 4
    blockCountY = (height + 3) // 4
    decompressed_width = max(width, 4)
    decompressed_height = max(height, 4)
    image = bytearray(decompressed_width*decompressed_height*4)

    for j in range(blockCountY):
        for i in range(blockCountX):
            DecompressBlockDXT5(i*4, j*4, width, blockStorage[j*blockCountY + i * 16:], image)

    print("xuy2", len(image))
    return image

def main():
    with open(r"C:\Users\megaz\Downloads\tracks_wood1688954074.dxt5", "rb") as file:
        compressed = file.read()

    width = 1024

    image = block_decompress_image_dxt5(width, width, compressed)
    from PIL import Image
    im = Image.frombuffer('RGBA', (width, width), image)
    im.show()

if __name__ == "__main__":
    main()