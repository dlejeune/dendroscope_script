import sys
import importlib.util

if sys.prefix == sys.base_prefix:
    print(
        "You need to run this tool in a virtual environment. You can do this by first installing the virtualenv package with 'pip install virtualenv' and then running 'virtualenv venv' to create a virtual environment. You can then activate the virtual environment by running 'source venv/bin/activate' on Mac/Linux or 'venv\\Scripts\\activate' on Windows. Once you have activated the virtual environment, you can run this tool."
    )
    sys.exit(1)

try:
    import dendro_interface as dendroscope
    import process_colours as preprocessing
    from pathlib import Path
    import colour
    import typer
    import re
    from typing_extensions import Annotated
    from typing import Optional
    import glob
    import json
    import subprocess
    import logging
    from ete3 import Tree


except ImportError as imp_err:

    print(imp_err)

    print(
        "You are missing some dependencies. You should run 'pip install typer rich typing-extensions colour ete3 matplotlib' before trying again."
    )

    sys.exit(1)


app = typer.Typer(pretty_exceptions_enable=True)
DENDRO_PATH = "/home/dlejeune/dendroscope/Dendroscope"


def run_dendro_command(
    cap_id: str, output_directory: Path, dendro_path: str = DENDRO_PATH
):
    dendro_command_file = output_directory / "tmp" / f"CAP{cap_id}.dendrocmd.txt"
    error_log_file = output_directory / "logs" / f"CAP{cap_id}.dendro.log"

    command = f"{dendro_path} -g --commandFile {str(dendro_command_file)}"
    # command = f"xvfb-run --auto-servernum --server-num=1 {dendro_path} +g --commandFile {str(dendro_command_file)} 2>&1 | tee -a {error_log_file}"
    subprocess.call(command, shell=True)


def construct_dendro_command(
    cap_id: str, tree_fp: Path, patient_dict: dict, output_directory: Path
):
    main_output_file = output_directory / f"CAP{cap_id}.dendrotree.png"
    linear_output_file = output_directory / f"CAP{cap_id}.linear.dendrotree.png"
    nexus_output_file = output_directory / f"CAP{cap_id}.dendro_nexus.nexus"

    logging.info("Building the dendroscope command", extra={"patient_id": cap_id})
    dendro_command = dendroscope.build_dendro_command(
        tree_fp, patient_dict, main_output_file, linear_output_file, nexus_output_file
    )

    dendro_out_cmd_file = output_directory / "tmp" / f"CAP{cap_id}.dendrocmd.txt"

    with open(dendro_out_cmd_file, "w") as output_file:
        output_file.write(dendro_command)

    logging.info(
        f"Wrote the dendroscope command to {dendro_out_cmd_file}",
        extra={"patient_id": cap_id},
    )


def get_patients_dict(lookup_fp: Path) -> dict:
    patients_dict = preprocessing.lookup_to_dict(lookup_fp)
    patients_dict = preprocessing.assign_colours_to_patients(patients_dict)

    return patients_dict


def do_setup(output_directory: Path):
    temp_dir: Path = output_directory / "tmp"
    temp_dir.mkdir(exist_ok=True, parents=True)

    log_dir = output_directory / "logs"

    log_dir.mkdir(exist_ok=True, parents=True)


def optimise_patient_dict(patient_dict: dict, tree_file: Path) -> dict:

    tree_obj = Tree(str(tree_file))

    wpis_in_tree = []

    new_dict = dict(patient_dict)

    for leaf in tree_obj.get_tree_root().get_leaves():
        leaf_wpi = int(leaf.name.split("_")[2].replace("WPI", ""))

        if leaf_wpi and (leaf_wpi not in wpis_in_tree) and (leaf_wpi != 0):
            wpis_in_tree.append(leaf_wpi)

    for visit_id, visit in patient_dict.items():
        if visit["WPI"] not in wpis_in_tree:
            new_dict.pop(visit_id)

    return new_dict


def workflow(
    tree_file: Path,
    cap_id: str,
    patient_dict: dict,
    output_directory: Path,
    create_separate_output_folders: bool = False,
    create_intermediary_files: bool = False,
    dendro_path: str = DENDRO_PATH,
):

    patient_dict = optimise_patient_dict(patient_dict, tree_file)

    logging.info("Starting the dendro build command", extra={"patient_id": cap_id})
    construct_dendro_command(cap_id, tree_file, patient_dict, output_directory)

    logging.info(f"Running dendroscope for {cap_id}", extra={"patient_id": cap_id})
    run_dendro_command(cap_id, output_directory, dendro_path)

    logging.info(f"Finished with patient {cap_id}", extra={"patient_id": cap_id})


@app.command("process-dir")
def cli_process_directory(
    tree_directory: Annotated[Path, typer.Option(help="The directory")],
    lookup_file: Annotated[Path, typer.Option()],
    output_directory: Annotated[Path, typer.Option()],
    dendroscope_bin: Annotated[str, typer.Option()] = DENDRO_PATH,
):

    do_setup(output_directory)
    patients_dict = get_patients_dict(lookup_file)

    files = tree_directory.glob("*.nwk")

    for file in files:
        file_cap_id = file.stem.split("_")[0]

        if file_cap_id in patients_dict:
            patient_dict = patients_dict[file_cap_id]

            workflow(
                file,
                file_cap_id,
                patient_dict,
                output_directory,
                dendro_path=str(dendroscope_bin),
            )
        else:
            logging.error(
                f"Failed to find the CAP_ID {file_cap_id} in the provided lookup table"
            )


@app.command("process-file")
def cli_process_file(
    tree_file: Annotated[Path, typer.Option(help="The directory")],
    lookup_file: Annotated[Path, typer.Option()],
    output_directory: Annotated[Path, typer.Option()],
    dendroscope_bin: Annotated[str, typer.Option()] = DENDRO_PATH,
):

    do_setup(output_directory)
    patients_dict = get_patients_dict(lookup_file)
    json.dump(
        patients_dict, open(output_directory / "tmp" / "patients.json", "w"), indent=4
    )

    file_cap_id = tree_file.stem.split("_")[0]

    if file_cap_id in patients_dict:

        patient_dict = patients_dict[file_cap_id]

        workflow(
            tree_file,
            file_cap_id,
            patient_dict,
            output_directory,
            dendro_path=str(dendroscope_bin),
        )

    else:
        logging.error(
            f"Failed to find the CAP_ID {file_cap_id} in the provided lookup table"
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app()
