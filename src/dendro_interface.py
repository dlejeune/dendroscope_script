from pathlib import Path


class GroupStyle:

    def __init__(
        self,
        selector: str,
        colour: str = None,
        shape: str = None,
        size: str = None,
        font: str = None,
        fillcolour: str = None,
    ):

        self.selector = selector

        self.colour: str | None = colour
        self.shape: str | None = shape
        self.size: str | None = size
        self.font: str | None = font
        self.fillcolour: str | None = fillcolour

    def to_dendro_string(self) -> str:
        output_string = f"find searchtext='{self.selector}' target=Nodes regex=true;"

        if self.colour:
            output_string += f"set labelcolor={self.colour} 255;\n"

        if self.size:
            output_string += f"set nodesize={self.size};\n"

        if self.shape:
            output_string += f"set nodeshape={self.shape};\n"

        if self.font:
            output_string += f"set font={self.font};\n"

        if self.fillcolour:
            output_string += f"set fillcolor={self.fillcolour} 150;\n"

        output_string += "deselect all;\n"

        return output_string


# This class will generate the dendro command. It should operate on a single file with its entrypoint returning a string for one tree

# It should only be aware of the single CAP patient dict and generate regex selectors for each WPI


def generate_dendro_preamble(
    tree_file: str,
    width: int = 1920,
    height: int = 1080,
    drawer: str = "CircularPhylogram",
    zoom: str = "expand",
    radial_labels: bool = True,
    ladderize: str = "right",
    sparse_labels: bool = False,
) -> str:

    return f"""
        open file='{str(tree_file)}';
        set window width={width} height={height};
        set drawer={drawer};
        zoom what={zoom};
        set radiallabels={str(radial_labels).lower()};
        ladderize={ladderize};
        set sparselabels={str(sparse_labels).lower()};
        """


def generate_dendro_export_command(
    main_output_file: Path, linear_output_file: Path, nexus_output_file: Path
) -> str:
    return f"""
        exportimage file='{str(main_output_file)}' format=PNG replace=true;
        set drawer=RectangularPhylogram;
        exportimage file='{str(linear_output_file)}' format=PNG replace=true;
        save format=NeXML file={str(nexus_output_file)}
        quit;"""


def create_wpi_group_styles(patient_visits: dict) -> list:
    styles = []

    for visit in patient_visits.values():

        padded_wpi = str(visit["WPI"]).rjust(3, "0")
        regex_selector = f"(.*({padded_wpi}WPI))(.*(NGS)).*"
        colour = visit["colour"]

        style = GroupStyle(
            regex_selector,
            colour=f"{colour[0]} {colour[1]} {colour[2]}",
            font="arial-italic-8",
        )

        styles.append(style)

    return styles


def create_other_styles() -> list:
    # This ain't great but whatever
    ogv_style = GroupStyle(
        "OGV",
        colour="255 61 240",
        shape="rectangle",
        size="20",
        font="arial-bold-16",
        fillcolour="255 61 240",
    )

    styles = [
        ogv_style,
    ]

    return styles


def generate_dendro_styling_command(patient_visits) -> str:

    styles = create_wpi_group_styles(patient_visits)
    styles.extend(create_other_styles())
    output_str = ""

    for style in styles:
        output_str += style.to_dendro_string()

    return output_str


def build_dendro_command(
    input_tree_file: Path,
    patient_visits: dict,
    main_output_file: Path,
    linear_output_file: Path,
    nexus_output_file: Path,
) -> str:

    output_str = generate_dendro_preamble(str(input_tree_file))
    output_str += generate_dendro_styling_command(patient_visits)
    output_str += generate_dendro_export_command(
        main_output_file, linear_output_file, nexus_output_file
    )

    return output_str
