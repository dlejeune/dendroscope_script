# 1) Read all the trees in the directory
# 2) Update node information such that their names better identify their contents
#     a) this means we annotate each one with WPI and Weeks Pre Treatment (which we pull from the file?)
#     no wait. we can use the csv file to pre-allocate colours. Then we determine commonalities within the things.


# Okay new strategy:

# 1) Parse the CSV file with all the CAP numbers, WPIs and WPA.
#     a) We can use this information to assign colours across all the participants, such that colours are comparable?
#     b) The colour is:
#         i) red for all samples in year one
#         ii) shades of blue for all the samples in year pre-therapy
#         iii) For each year between 1 and n-1, assign that year a colour and assign shades to the varying samples in that year

import csv
import json
from pathlib import Path
from operator import itemgetter
import colour
import matplotlib.pyplot as plt
import matplotlib.patches as patches

WEEKS_IN_YEAR = 52

YEAR_ONE = "#ff0000"  # RED
YEAR_N_MINUS_ONE = "#0000ff"  # Blue
colour_lookup = {
    2: (255, 115, 0),  # Orange
    3: (255, 255, 0),  # Yellow
    4: (0, 255, 0),  # Green
    5: (0, 255, 183),  # Teal
    6: (0, 0, 255),  # Light Blue
}

colour_lookup_hex = {
    2: "#ff7300",  # Orange
    3: "#ffea00",  # Yellow
    4: "#00ff00",  # Green
    5: "#00ffb7",  # Teal
    6: "#87CEEB",  # Light Blue
}


def rgbfloat2rgbint(rgb):
    """
    Convert rgb float values (0.0-1.0) to rgb integer values (0-255).

    Args:
        rgb (tuple): Tuple of float values from 0.0 to 1.0

    Returns:
        tuple: Tuple of integer values from 0 to 255
    """
    return tuple([int(255 * i) for i in rgb])


def lookup_to_dict(lookup_path: Path) -> dict:
    patient_dict = {}

    with open(lookup_path, "r") as lookup_fh:
        reader = csv.DictReader(lookup_fh)

        for line in reader:
            if line["PID"] not in patient_dict:
                patient_dict[line["PID"]] = {}

            weeks_post_inf = int(line["Weeks post infection"])
            weeks_pre_art = int(line["Weeks pre-ART"])
            year_of_infection = (weeks_post_inf // WEEKS_IN_YEAR) + 1
            years_pre_art = weeks_pre_art // WEEKS_IN_YEAR

            visit_colour = None

            if year_of_infection == 1:
                visit_colour = rgbfloat2rgbint(colour.Color("red").rgb)
            elif years_pre_art == 0:
                visit_colour = rgbfloat2rgbint(colour.Color("blue").rgb)

            patient_dict[line["PID"]][int(line["Visit Code"])] = {
                "code": int(line["Visit Code"]),
                "CAP": line["PID"],
                "WPI": weeks_post_inf,
                "YOI": year_of_infection,
                "WPA": weeks_pre_art,
                "YPA": years_pre_art,
                "colour": visit_colour,
            }

    return patient_dict


def assign_colours_to_patients(patient_dict: dict) -> dict:
    year_dict = {}
    n_minus_one_visits = []

    for patient_id, visits in patient_dict.items():
        for visit in visits.values():
            if visit["YOI"] != 1 and visit["YPA"] != 0:
                visit_yoi = visit["YOI"]

                if visit_yoi not in year_dict:
                    year_dict[visit_yoi] = []

                year_dict[visit_yoi].append(visit)

            elif visit["YOI"] != 1 and visit["YPA"] == 0:
                n_minus_one_visits.append(visit)

    num_years = len(year_dict)

    # colours = [
    #     colour
    #     for colour in colour.Color("red").range_to(colour.Color("blue"), num_years + 2)
    # ]
    # colours = colours[1:]

    current_colour_idx = 0

    for year in year_dict:
        # current_colour = colours[current_colour_idx]
        # next_colour = colours[current_colour_idx + 1]

        # year_base_colour = colour.Color(colour_lookup[year])
        year_base_colour = colour.Color(colour_lookup_hex[year])

        year_base_hsl = year_base_colour.hsl

        # year_colours = [
        #     colour
        #     for colour in current_colour.range_to(next_colour, len(year_dict[year]))
        # ]

        sorted_visits = sorted(year_dict[year], key=itemgetter("WPI"))

        year_dict[year] = sorted_visits

        for idx, visit in enumerate(year_dict[year]):
            visit_cap = visit["CAP"]
            visit_id = visit["code"]

            if visit_id in patient_dict[visit_cap]:
                new_colour = colour.Color(
                    hsl=(
                        year_base_hsl[0] + idx * (0.001),
                        year_base_hsl[1],
                        year_base_hsl[2],
                    )
                )

                patient_dict[visit_cap][visit_id]["colour"] = rgbfloat2rgbint(
                    new_colour.rgb
                )

    year_base_colour = colour.Color(YEAR_N_MINUS_ONE)
    year_base_hsl = year_base_colour.hsl

    for visit in n_minus_one_visits:
        visit_cap = visit["CAP"]
        visit_id = visit["code"]

        new_colour = colour.Color(
            hsl=(
                year_base_hsl[0] - idx * (0.001),
                year_base_hsl[1],
                year_base_hsl[2],
            )
        )

        patient_dict[visit_cap][visit_id]["colour"] = rgbfloat2rgbint(new_colour.rgb)

    return patient_dict
