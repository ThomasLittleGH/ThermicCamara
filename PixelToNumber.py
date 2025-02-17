threshold = 150  # average of pixels must pass this number to be considered white (true)

values = {
    (True, True, True, False, True, True, True): 0,
    (False, False, True, False, False, True, False): 1,
    (True, False, True, True, True, False, True): 2,
    (True, False, True, True, False, True, True): 3,
    (False, True, True, True, False, True, False): 4,
    (True, True, False, True, False, True, True): 5,
    (True, True, False, True, True, True, True): 6,
    (True, False, True, False, False, True, False): 7,
    (True, True, True, True, True, True, True): 8,
    (True, True, True, True, False, True, False): 9
}


def GetBoolValues(PixelList: list[tuple[int, int, int]]):
    # """ Converts a list of (R, G, B) tuples into boolean values based on threshold """
    return [(sum(pixel) / 3) > threshold for pixel in PixelList]


def ReturnSingleNumber(BoolTable: list[bool]) -> int:
    # """ Maps a boolean list to a digit or returns -1 if not found """
    return values.get(tuple(BoolTable), -1)


def GetNumber(numbers: list[list[tuple[int, int, int]]]) -> float:
    # """ Converts multiple lists of pixel values into a numerical float """
    FinalNumber = []
    for number in numbers:
        BoolValues = GetBoolValues(number)
        ResultNumber = ReturnSingleNumber(BoolValues)
        if ResultNumber == -1:
            raise ValueError("Value not found!!!!!")
        FinalNumber.append(str(ResultNumber))
    return float("".join(FinalNumber))


# Testing with a valid pixel input
test_pixels = [
    [(255, 255, 255), (0, 0, 0), (255, 255, 255), (255, 255, 255), (0, 0, 0), (255, 255, 255), (255, 255, 255)]
    # Example pixel values
]
print(GetNumber(test_pixels))  # Adjust pixels as per the required pattern
