RelativeDistance = {
    "RELATIVE_DISTANCE_NONE": 0,
    "VerySmall": 1,
    "Small": 2,
    "Medium": 3,
    "Large": 4,
    "VeryLarge": 5,
}


RelativeDirection = {
    "East": 1,
    "NorthEast": 2,
    "North": 3,
    "NorthWest": 4,
    "West": 5,
    "SouthWest": 6,
    "South": 7,
    "SouthEast": 8,
}

DirectionAngles = {
    1: 0,
    2: 45,
    3: 90,
    4: 135,
    5: 180,
    6: 225,
    7: 270,
    8: 315,
}

name2sub_type = {
    'treasure': 1,
    'buff': 2,
    'start': 3,
    'end': 4
}
sub_type2name = {v: k for k, v in name2sub_type.items()}

if __name__ == '__main__':
    print(name2sub_type)
    print(sub_type2name)
