import argparse
import subprocess
import sys
import os
import platform
import shutil


def RED(text):
    return "\033[91m" + text + "\033[0m"


def GREEN(text):
    return "\033[92m" + text + "\033[0m"


def YELLOW(text):
    return "\033[93m" + text + "\033[0m"


def CYAN(text):
    return "\033[96m" + text + "\033[0m"


# === BEGIN: Platform-specific code ===
# To deploy to a CircuitPython board masquerading as a USB drive with a certain name,
# we must be able to find all the mounted USB drives on the system and check their names.
# How this is done depends on the OS on which the script is running. For any OS, the
# `find_mount_points_with_names` function must be implemented for the script to work.
# The function should return a list of tuples, where the first item in each tuple is a
# string which can be supplied to `os.listdir` to find the contents of the root of a USB
# drive. The second item in each tuple should be a string giving the name of the USB
# drive. A tuple should be returned for every USB drive plugged into the system.

# To implement the function for a new platform, simply add a clause to the `if` chain
# below which defines the `find_mount_points_with_names` function.

if os.name == "nt":

    def find_mount_points_with_names():
        drives = []
        drive_list_proc = subprocess.run(
            ["fsutil", "fsinfo", "drives"], stdout=subprocess.PIPE
        )
        for drive in drive_list_proc.stdout.decode().split(" "):
            if len(drive) == 3 and drive[1] == ":" and drive[2] == "\\":
                drive_deets_proc = subprocess.run(
                    ["fsutil", "fsinfo", "volumeInfo", drive[:2]],
                    stdout=subprocess.PIPE,
                )
                drive_name = None
                for drive_kv in drive_deets_proc.stdout.decode().splitlines():
                    if drive_kv.startswith("Volume Name :"):
                        assert drive_name is None
                        drive_name = drive_kv.split(":")[1].strip()
                drives.append((drive, drive_name))
        return drives

elif platform.system() == "Darwin":

    def find_mount_points_with_names():
        drives = []
        mount_proc = subprocess.run(["mount"], stdout=subprocess.PIPE)
        for mount_line in mount_proc.stdout.decode().splitlines():
            if mount_line.startswith("/"):
                mount_parts = mount_line.split(" ")
                mount_point = mount_parts[2]
                if mount_point.startswith("/Volumes"):
                    drives.append((mount_point, mount_point.removeprefix("/Volumes/")))
        return drives

else:
    print(
        RED(
            f"ERROR: Platform-specific functions are not available on your system, which is detected as {os.name}"
        ),
        file=sys.stderr,
    )
    print(
        RED("ERROR: Implement the required platform-specific functions to proceed."),
        file=sys.stderr,
    )
    exit()

# === END: Platform-specific code ===

# The rest of the program is implemented using cross-platform functions from the
# Python library, and should work on any system so long as the platform-specific
# functions are implemented with the appropriate contracts.


parser = argparse.ArgumentParser(
    description="Run this script to find a USB drive with a certain name, wipe its "
    + "current contents, and move the appropriate files to the drive so that it runs "
    + "the updated software. Automatically expands through symbolic links and merges "
    + "general lib folders with board-specific lib folders. The program must be run "
    + "from the root directory of a properly-structured spacecraft software project."
)
parser.add_argument("deploy_type")
deploy_target = parser.add_mutually_exclusive_group(required=True)
deploy_target.add_argument("--target_drive", nargs="?", default="CIRCUITPY")
deploy_target.add_argument("--tmp_folder", action="store_true")
args = parser.parse_args()
if args.target_drive is None:
    args.target_drive = "CIRCUITPY"

if args.tmp_folder:
    print(CYAN(f"Starting deploy type {args.deploy_type} to temporary folder..."))
else:
    print(
        CYAN(
            f"Starting deploy type {args.deploy_type} to CircuitPython board with name {args.target_drive}..."
        )
    )

deploy_types = os.listdir(os.path.join(".", "applications"))
if args.deploy_type not in deploy_types:
    print(
        RED(f"ERROR: No software found for target {args.deploy_type}"),
        file=sys.stderr,
    )
    deploy_types_string = filter(
        (lambda x: (len(x) < 8) or (x[-8:] != "_testapp")), deploy_types
    )
    deploy_types_string = list(map((lambda x: YELLOW(x)), deploy_types_string))
    deploy_types_string = (
        ", ".join(deploy_types_string[:-1]) + ", and " + deploy_types_string[-1]
    )
    print(f"Available deploy types are {deploy_types_string}", file=sys.stderr)
    exit()

if args.tmp_folder:
    import tempfile

    deploy_path = os.path.join(tempfile.gettempdir(), "CIRCUITPY")
    os.makedirs(deploy_path, exist_ok=True)
else:
    target_drives = [
        mp[0]
        for mp in filter(
            (lambda mp: mp[1] == args.target_drive), find_mount_points_with_names()
        )
    ]
    if len(target_drives) != 1:
        print(
            RED(
                f"ERROR: There must be exactly one drive named {args.target_drive} but {len(target_drives)} were found."
            ),
            file=sys.stderr,
        )
        print(
            RED(
                "ERROR: Exited without deploying the software. "
                + "Rename a drive, or target a drive name that is unique and exists."
            ),
            file=sys.stderr,
        )
        exit()
    deploy_path = target_drives[0]

print(
    f"Configuration complete! Loading software for {args.deploy_type} to {deploy_path}"
)

print("Wiping existing software on device...")
for item in os.listdir(deploy_path):
    item_path = os.path.join(deploy_path, item)
    if os.path.isdir(item_path):
        shutil.rmtree(item_path)
    else:
        os.remove(item_path)

print("Programming shared libraries to device...")
for item in os.listdir(os.path.join(".", "shared")):
    src_item_path = os.path.join(".", "shared", item)
    dst_item_path = os.path.join(deploy_path, item)
    if os.path.isdir(src_item_path):
        shutil.copytree(
            src_item_path, dst_item_path, symlinks=False, dirs_exist_ok=True
        )
    else:
        shutil.copyfile(src_item_path, dst_item_path, follow_symlinks=True)

print("Programming target-specific software to device...")
for item in os.listdir(os.path.join(".", "applications", args.deploy_type)):
    src_item_path = os.path.join(".", "applications", args.deploy_type, item)
    dst_item_path = os.path.join(deploy_path, item)
    if os.path.isdir(src_item_path):
        shutil.copytree(
            src_item_path, dst_item_path, symlinks=False, dirs_exist_ok=True
        )
    else:
        shutil.copyfile(src_item_path, dst_item_path, follow_symlinks=True)

print("Removing any generated __pycache__ directories copied to device...")
for tree in os.walk(deploy_path, followlinks=True):
    if "__pycache__" in tree[1]:
        shutil.rmtree(os.path.join(tree[0], "__pycache__"))

print(GREEN(f"Device programming complete for target {args.deploy_type}!"))
