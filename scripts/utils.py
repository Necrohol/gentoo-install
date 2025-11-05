import os
import sys
import subprocess
import time
import re
from typing import List, Dict, Callable, Any, Optional

# --- Configuration & Environment (Assumed from other converted scripts) ---
# Assuming these global variables are managed by the main application
GENTOO_INSTALL_REPO_SCRIPT_PID = os.environ.get("GENTOO_INSTALL_REPO_SCRIPT_PID")
GENTOO_INSTALL_REPO_DIR = os.environ.get("GENTOO_INSTALL_REPO_DIR")
UUID_STORAGE_DIR = "/tmp/gentoo-install/uuids"  # Hardcoded from config.sh
DISK_ID_TO_RESOLVABLE: Dict[str, str] = {} # Assumed global from config.py

# Global cache for lsblk output
CACHED_LSBLK_OUTPUT: Optional[str] = None

# ANSI color codes for logging (Equivalent to Bash escapes)
_RED = "\033[1;31m"
_YELLOW = "\033[1;33m"
_BOLD = "\033[1m"
_RESET = "\033[0m"

# --- Error and Logging Functions (Replacing Bash functions) ---

def elog(*args):
    """Prints a standard log message: [+][...]"""
    print(f"[{_BOLD}+" f"{_RESET}]", *args)

def einfo(*args):
    """Prints an info message in bold yellow: [+]."""
    print(f"[{_BOLD}+" f"{_RESET}]", f"{_BOLD}{_YELLOW}{' '.join(map(str, args))}" f"{_RESET}")

def ewarn(*args):
    """Prints a warning message to stderr in bold yellow: [!]."""
    print(f"[{_RED}!" f"{_RESET}]", f"{_BOLD}{_YELLOW}{' '.join(map(str, args))}" f"{_RESET}", file=sys.stderr)

def eerror(*args):
    """Prints a general error message to stderr."""
    print(f"{_RED}error:" f"{_RESET}", *args, file=sys.stderr)

def die(message: str):
    """Equivalent to Bash 'die'. Prints error and exits."""
    eerror(message)
    # Check if PID is set and is not the current process, then kill the parent script
    if GENTOO_INSTALL_REPO_SCRIPT_PID and os.getpid() != int(GENTOO_INSTALL_REPO_SCRIPT_PID):
        try:
            os.kill(int(GENTOO_INSTALL_REPO_SCRIPT_PID), 9) # SIGKILL
        except OSError:
            pass # Process may already be dead
    sys.exit(1)

def die_trace(idx: int, message: str):
    """
    Equivalent to Bash 'die_trace'. 
    In Python, we use the traceback module for true tracing, 
    but here we replicate the Bash file:line:function output structure 
    using the inspect module if available, or simplified.
    """
    try:
        import inspect
        # Get frame of the caller of the caller (idx=1 in Bash is the calling function)
        frame = inspect.stack()[idx + 1] 
        msg = f"{_BOLD}{frame.filename}:{frame.lineno}: " \
              f"{_RED}error:{_RESET} {frame.function}: {message}"
        print(msg, file=sys.stderr)
    except Exception:
        # Fallback if inspect fails or is not desired
        eerror(f"FATAL ERROR (Trace Level {idx}): {message}")
    sys.exit(1)

# --- I/O and Control Flow Functions ---

def for_line_in(filename: str, func: Callable[[str], None]):
    """Equivalent to 'for_line_in file func'"""
    try:
        with open(filename, 'r') as f:
            for line in f:
                # Bash's read -r leaves the trailing newline, 
                # but Python's iteration gives us the whole line including \n.
                func(line.rstrip('\n')) 
    except FileNotFoundError:
        die(f"File not found: {filename}")
    except Exception as e:
        die(f"Error reading file {filename}: {e}")

def flush_stdin():
    """Equivalent to 'flush_stdin'. Tries to clear any pending input."""
    # In Python, this requires non-portable libraries (like termios), 
    # or relying on `read -t 0.01` behavior, which is usually skipped 
    # in favor of simply reading the input fully. We keep it as a no-op 
    # to maintain the original script's flow logic.
    pass

def ask(prompt: str) -> bool:
    """Equivalent to 'ask prompt (Y/n)'. Prompts user for yes/no input."""
    while True:
        flush_stdin()
        try:
            response = input(f"{prompt} (Y/n) ").strip().lower()
        except EOFError:
            die("Error in reading input (EOF)")
        
        if response in ('', 'y', 'yes'):
            return True
        elif response in ('n', 'no'):
            return False
        else:
            continue

def try_command(*cmd: str) -> bool:
    """
    Equivalent to 'try'. Executes a command and offers retry/abort/continue options on failure.
    Returns True if the command succeeded or if the user chose to continue.
    """
    cmd_list = list(cmd)
    prompt_parens = f"({_BOLD}S{_RESET}hell/{_BOLD}r{_RESET}etry/{_BOLD}a{_RESET}bort/{_BOLD}c{_RESET}ontinue/{_BOLD}p{_RESET}rint)"

    # Outer loop allows retrying the command
    while True:
        try:
            # Execute command with stderr/stdout captured for cleaner output
            result = subprocess.run(cmd_list, check=False, capture_output=False)
            cmd_status = result.returncode
        except FileNotFoundError:
            cmd_status = 127
        except Exception as e:
            cmd_status = 1
            eerror(f"Execution error: {e}")

        if cmd_status != 0:
            print(f"{_RED} * Command failed: {_YELLOW}${_RESET} {' '.join(cmd_list)}")
            print(f"Last command failed with exit code {cmd_status}")

            # Prompt until input is valid
            while True:
                response = input(f"Specify next action {prompt_parens} ").strip().lower()
                
                if response in ('', 's', 'shell'):
                    print("You will be prompted for action again after exiting this shell.")
                    # Drop into an interactive shell
                    subprocess.run(["/bin/bash"], check=False)
                    break # Break inner loop, returns to command retry loop
                elif response in ('r', 'retry'):
                    break # Break inner loop, returns to command retry loop
                elif response in ('a', 'abort'):
                    die("Installation aborted")
                elif response in ('c', 'continue'):
                    return True # Command failed, but user wants to continue
                elif response in ('p', 'print'):
                    print(f"{_YELLOW}${_RESET} {' '.join(cmd_list)}")
                else:
                    continue
        else:
            return True # Command succeeded

def countdown(message: str, seconds: int):
    """Equivalent to 'countdown message seconds'."""
    sys.stderr.write(message)
    sys.stderr.flush()
    for i in range(seconds, 0, -1):
        sys.stderr.write(f"{_RED}{i}{_RESET} ")
        sys.stderr.flush()
        time.sleep(1)
    sys.stderr.write("\n")

# --- Download Functions ---

def download_stdout(url: str) -> str:
    """Equivalent to 'download_stdout url'. Downloads file to stdout."""
    try:
        # wget arguments: quiet, https-only, secure protocol, output to stdout
        result = subprocess.run(
            ["wget", "--quiet", "--https-only", "--secure-protocol=PFS", "-O", "-", "--", url],
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        die(f"Failed to download URL {url}: {e.stderr}")
    except FileNotFoundError:
        die("wget command not found. Please install it.")

def download(url: str, output_path: str):
    """Equivalent to 'download url output_path'. Downloads file to a path."""
    try:
        # wget arguments: quiet, https-only, secure protocol, show progress, output file
        subprocess.run(
            ["wget", "--quiet", "--https-only", "--secure-protocol=PFS", "--show-progress", "-O", output_path, "--", url],
            check=True
        )
    except subprocess.CalledProcessError as e:
        die(f"Failed to download URL {url} to {output_path}: {e}")
    except FileNotFoundError:
        die("wget command not found. Please install it.")

# --- Disk/Device Resolution Functions (Replicating Shell Logic) ---

def _run_blkid_export(device: Optional[str] = None, tag_value: Optional[str] = None) -> str:
    """Helper to run blkid and get the raw export output."""
    # blkid -g -c /dev/null is often for cache clearing/update
    subprocess.run(["blkid", "-g", "-c", "/dev/null"], check=True, capture_output=True)
    
    cmd = ["blkid", "-c", "/dev/null", "-o", "export"]
    if tag_value:
        # -t TAG=VALUE
        cmd.extend(["-t", tag_value])
    if device:
        cmd.append(device)

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        # Note: blkid returns non-zero if no device is found with -t
        if not tag_value:
             die(f"Error while executing blkid for device '{device}': {e.stderr}")
        return "" # Return empty string for not found when searching by tag

def get_blkid_field_by_device(blkid_field: str, device: str) -> str:
    """Gets a single BLKID field value (e.g., 'UUID') for a given device."""
    # Try to run partprobe if available (like the bash script)
    subprocess.run(["partprobe"], check=False, capture_output=True) 

    val_output = _run_blkid_export(device=device)
    
    # Extract the field using regex
    match = re.search(rf"^{re.escape(blkid_field)}=[\"']?([^\"'\n]+)[\"']?", val_output, re.MULTILINE)
    
    if not match:
        die(f"Could not find {blkid_field}=... in blkid output for device '{device}'")
        
    return match.group(1).strip()

def get_device_by_blkid_field(blkid_field: str, field_value: str) -> str:
    """Finds a device by a BLKID tag/value pair (e.g., 'PARTUUID=...')."""
    
    tag_value = f"{blkid_field}={field_value}"
    dev_output = _run_blkid_export(tag_value=tag_value)
    
    # Extract DEVNAME using regex
    match = re.search(r"^DEVNAME=[\"']?([^\"'\n]+)[\"']?", dev_output, re.MULTILINE)
    
    if not match:
        # Bash version dies here.
        die(f"Could not find device by blkid tag '{tag_value}'")
        
    return match.group(1).strip()

def get_device_by_partuuid(partuuid: str) -> str:
    """Resolves a device path using /dev/disk/by-partuuid/ or blkid."""
    by_path = f"/dev/disk/by-partuuid/{partuuid}"
    if os.path.exists(by_path):
        return by_path
    return get_device_by_blkid_field('PARTUUID', partuuid)

def get_device_by_uuid(uuid: str) -> str:
    """Resolves a device path using /dev/disk/by-uuid/ or blkid."""
    by_path = f"/dev/disk/by-uuid/{uuid}"
    if os.path.exists(by_path):
        return by_path
    return get_device_by_blkid_field('UUID', uuid)

def cache_lsblk_output():
    """Caches the output of lsblk for fast lookups."""
    global CACHED_LSBLK_OUTPUT
    try:
        result = subprocess.run(
            ["lsblk", "--all", "--path", "--pairs", "--output", "NAME,PTUUID,PARTUUID"],
            check=True,
            capture_output=True,
            text=True
        )
        CACHED_LSBLK_OUTPUT = result.stdout
    except subprocess.CalledProcessError as e:
        die(f"Error while executing lsblk to cache output: {e.stderr}")
    except FileNotFoundError:
        die("lsblk command not found.")

def get_device_by_ptuuid(ptuuid: str) -> str:
    """Finds a device by its Partition Table UUID (PTUUID)."""
    global CACHED_LSBLK_OUTPUT
    ptuuid = ptuuid.lower()
    
    if CACHED_LSBLK_OUTPUT is None:
        cache_lsblk_output()

    output = CACHED_LSBLK_OUTPUT
    if not output:
        die("lsblk output cache is empty.")

    # Bash logic: grep for ptuuid="..." and partuuid=""
    # This filters for the main disk device, not a partition.
    pattern = rf'name="([^"]+)" ptuuid="{re.escape(ptuuid)}" partuuid=""'
    match = re.search(pattern, output.lower())
    
    if not match:
        die(f"Could not find PTUUID='{ptuuid}' in lsblk output")
    
    return match.group(1) # The NAME field (device path)

def uuid_to_mduuid(uuid: str) -> str:
    """Converts a standard UUID to the MDADM UUID format (e.g., 8:8:8:8)."""
    uuid = uuid.lower().replace('-', '')
    # Bash substring manipulation: :0:8, :8:8, :16:8, :24:8
    return f"{uuid[:8]}:{uuid[8:16]}:{uuid[16:24]}:{uuid[24:32]}"

def get_device_by_mdadm_uuid(uuid: str) -> str:
    """Finds an MDADM device by its UUID."""
    mduuid = uuid_to_mduuid(uuid)
    
    try:
        # mdadm --examine --scan output is used
        result = subprocess.run(
            ["mdadm", "--examine", "--scan"],
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        die(f"Error while executing mdadm to find array with UUID={mduuid}: {e.stderr}")
    except FileNotFoundError:
        die("mdadm command not found.")
        
    # Bash logic: grep for the UUID, then extract the device path
    pattern = rf"array (\S+)\s+uuid={re.escape(mduuid)}"
    match = re.search(pattern, result.stdout.lower(), re.IGNORECASE)
    
    if not match:
        die(f"Could not find UUID='{mduuid}' in mdadm output")

    return match.group(1) # The device path

def get_device_by_luks_name(name: str) -> str:
    """LUKS devices are typically accessed via /dev/mapper/name."""
    return f"/dev/mapper/{name}"

def resolve_device_by_id(id_val: str) -> str:
    """Resolves a configuration ID to a canonical block device path."""
    if id_val not in DISK_ID_TO_RESOLVABLE:
        die(f"Cannot resolve id='{id_val}' to a block device (no table entry)")

    entry = DISK_ID_TO_RESOLVABLE[id_val]
    if ':' not in entry:
        die(f"Invalid resolve entry format: '{entry}'")

    type_val, arg = entry.split(':', 1)
    
    dev: str = ""
    if type_val == 'partuuid':
        dev = get_device_by_partuuid(arg)
    elif type_val == 'ptuuid':
        dev = get_device_by_ptuuid(arg)
    elif type_val == 'uuid':
        dev = get_device_by_uuid(arg)
    elif type_val == 'mdadm':
        dev = get_device_by_mdadm_uuid(arg)
    elif type_val == 'luks':
        dev = get_device_by_luks_name(arg)
    elif type_val == 'device':
        dev = arg
    else:
        die(f"Cannot resolve '{entry}' to device (unknown type)")

    return canonicalize_device(dev)

# --- Filesystem/UUID Management ---

def load_or_generate_uuid(base64_id: str) -> str:
    """Loads a UUID from storage or generates a new one, saving it."""
    uuid_file = os.path.join(UUID_STORAGE_DIR, base64_id)

    if os.path.exists(uuid_file):
        try:
            with open(uuid_file, 'r') as f:
                return f.read().strip()
        except IOError as e:
            die(f"Failed to read UUID file {uuid_file}: {e}")
    else:
        try:
            # Use uuidgen command (common Linux utility)
            result = subprocess.run(["uuidgen", "-r"], check=True, capture_output=True, text=True)
            uuid = result.stdout.strip()
            
            os.makedirs(UUID_STORAGE_DIR, exist_ok=True)
            with open(uuid_file, 'w') as f:
                f.write(uuid)
            
            return uuid
        except subprocess.CalledProcessError as e:
            die(f"Failed to execute uuidgen: {e.stderr}")
        except FileNotFoundError:
            die("uuidgen command not found.")
        except IOError as e:
            die(f"Failed to write UUID file {uuid_file}: {e}")

# --- Device Path Utilities ---

def shorten_device(device_path: str) -> str:
    """Returns the basename of the device if it's from /dev/disk/by-id/."""
    # Bash: ${1#/dev/disk/by-id/}
    if device_path.startswith("/dev/disk/by-id/"):
        return device_path[len("/dev/disk/by-id/"):]
    return device_path

def canonicalize_device(given_dev: str) -> str:
    """
    Returns the /dev/disk/by-id/ path if the device path is a symlink to it, 
    otherwise returns the original path.
    """
    given_dev_realpath = os.path.realpath(given_dev)
    
    for dev_id_path in os.listdir("/dev/disk/by-id"):
        full_path = os.path.join("/dev/disk/by-id", dev_id_path)
        try:
            if os.path.realpath(full_path) == given_dev_realpath:
                return full_path
        except OSError:
            # Handle broken symlinks gracefully
            continue
            
    return given_dev

# --- Program Check Functions ---

def has_program(program: str, checkfile: Optional[str] = None) -> bool:
    """Equivalent to 'has_program program [checkfile]'."""
    if checkfile is None:
        # Check if program exists in PATH
        return bool(os.access(program, os.X_OK) or os.system(f"type {program} >/dev/null 2>&1") == 0)
    elif checkfile.startswith("/"):
        # Check if checkfile (as a full path) exists
        return os.path.exists(checkfile)
    else:
        # Check if checkfile (as a program name) exists in PATH
        return bool(os.access(checkfile, os.X_OK) or os.system(f"type {checkfile} >/dev/null 2>&1") == 0)

# check_wanted_programs is too long and specific to be included here, 
# but it would use 'has_program' and 'ask' and 'subprocess.run' for package manager calls.

def maybe_exec(func_name: str, *args):
    """Executes a function if it exists."""
    # In Python, we check if the function is callable in the current scope.
    if func_name in globals() and callable(globals()[func_name]):
        globals()[func_name](*args)
    elif func_name in locals() and callable(locals()[func_name]):
        locals()[func_name](*args)
    # Note: For methods in a class, you would use getattr(obj, func_name)
    
# --- The original parse_arguments is replaced by a simplified Python version, 
# as the full implementation is part of the DiskConfigurator conversion ---

# Assuming argument parsing from the previous step is used or passed in
# (e.g., 'parse_arguments' from config.py)

if __name__ == "__main__":
    # --- Example Usage ---
    elog("Starting utility checks.")
    
    # Check if this process can call utils (simulating protection.sh)
    if os.environ.get("GENTOO_INSTALL_REPO_SCRIPT_ACTIVE") != "true":
        die("Protection check failed. Must be run by main installer.")

    try:
        # Example logging and I/O
        einfo("Current working directory is:", os.getcwd())
        if has_program("wget"):
            elog("Wget is available.")
        
        # Example UUID management
        test_id = "test-device-1"
        base64_id = test_id.encode('utf-8').hex()
        uuid = load_or_generate_uuid(base64_id)
        elog(f"Resolved/Generated UUID for {test_id}: {uuid}")
        
        # Example device resolution (needs devices to exist)
        # Note: True testing requires a mock filesystem
        # try_command("ls", "-l", "/root") 
        
    except SystemExit:
        print("Script exited.")
