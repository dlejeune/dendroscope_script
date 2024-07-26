import colour
from process_colours import colour_lookup_hex


years = [2, 3, 4]

for year in years:
    current_colour = colour.Color(colour_lookup_hex[year])

    current_hsl = current_colour.hsl

    for visit in range(4):
        new_colour = colour.Color(
            hsl=(current_hsl[0] + visit / 100, current_hsl[1], current_hsl[2])
        )
        print(new_colour.hsl)
