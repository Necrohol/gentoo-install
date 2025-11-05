import os
import sys
import subprocess
import re
from typing import List, Dict, Any, Optional

# --- Assume this check is performed by the caller or by a sourced protection.py ---
# import protection # Assuming protection.py handles the initial safety check
# if os.environ.get("GENTOO_INSTALL_REPO_SCRIPT_ACTIVE") != "true":
#     ... exit 1 ...


# --- PLACEHOLDER UTILITIES (from other scripts like error.sh or uuid.sh) ---

def die_trace(exit_code: int, message: str, trace_level: int = 1):
    """
    Equivalent to the Bash 'die_trace' function. 
    Prints error and exits. In the full project, this includes a stack trace.
    """
    print(f"\033[1;31m * FATAL ERROR:\033[m {message}", file=sys.stderr)
    sys.exit(exit_code)

def parse_arguments_python(arg_list: List[str]) -> Dict[str, str]:
    """
    Simplified Python equivalent of 'parse_arguments'.
    In Bash, this function handles '+key' (required) and '?key' (optional). 
    In Python, we just parse all 'key=value' pairs.
    """
    arguments = {}
    for arg in arg_list:
        if '=' in arg:
            key, value = arg.split('=', 1)
            # Remove + or ? prefixes if they were preserved from the Bash call
            key = key.lstrip('+?') 
            arguments[key] = value
    return arguments

def load_or_generate_uuid(base64_id: str) -> str:
    """Stub for the UUID generation logic."""
    return f"PY-STUB-UUID-{base64_id[:4]}-{os.getpid()}"


# --- The Main Utility Class ---

class GentooInstallerUtils:
    """
    Utility class to encapsulate functions.sh logic.
    """
    
    def __init__(self, gentoo_install_repo_dir: str):
        # Equivalent to Bash global variable
        self.GENTOO_INSTALL_REPO_DIR = gentoo_install_repo_dir
        
        # Dictionary to store arguments parsed from Bash-style functions
        self.arguments: Dict[str, str] = {}
        self.extra_arguments: List[str] = []

    # --- Utility Functions (direct conversion) ---

    def safe_source(self, script_path: str):
        """
        Bash 'source' equivalent for executing other Python scripts.
        In Python, this is done via 'import' or by executing a subprocess.
        This is typically avoided in favor of direct function calls.
        """
        if not os.path.exists(script_path):
            die_trace(1, f"Required script not found: {script_path}")
        # For Python, we would rely on the main installer to handle imports.
        # If executing a Bash script, we'd use subprocess.run:
        # subprocess.run(["bash", "-c", f"source {script_path}"], check=True)
        print(f"DEBUG: Attempted to 'source' (import) {script_path}. Relying on Python module system.")


    def create_resolve_entry(self, new_id: str, resolve_type: str, resolve_value: str):
        """
        Registers a device ID to a resolvable string (e.g., PARTUUID, LUKS name).
        This would update the global DISK_ID_TO_RESOLVABLE dictionary in config.py.
        """
        # Assuming the state is managed in a separate Config object or passed in
        # For now, just logging the action.
        print(f"DEBUG: Registered RESOLVE {new_id} -> {resolve_type}={resolve_value}")

    def create_resolve_entry_device(self, new_id: str, device: str):
        """Registers a device ID to a physical device path."""
        # Assuming the state is managed in a separate Config object or passed in
        print(f"DEBUG: Registered RESOLVE {new_id} -> device={device}")

    def uuid_to_mduuid(self, uuid: str) -> str:
        """Converts a standard UUID to an MDADM UUID format (used in create_raid)."""
        # Bash: uuid_to_mduuid "$uuid"
        return uuid.replace('-', '')

    # --- Conditional/Logic Functions ---

    def only_one_of(self, arguments: Dict[str, str], keys: List[str]):
        """Checks that only one of the provided keys exists in the arguments dictionary."""
        present_keys = [key for key in keys if key in arguments]
        if len(present_keys) > 1:
            die_trace(2, f"Only one of the arguments ({', '.join(keys)}) can be given")

    # The rest of the validation and configuration functions (create_new_id, 
    # verify_existing_id, verify_option, etc.) would be methods on this class
    # or the DiskConfigurator class, as shown in the config.py conversion.
    
    # --- File System Operations ---
    
    def check_exists_or_die(self, path: str):
        """Checks if a file/directory exists, otherwise calls die_trace."""
        if not os.path.exists(path):
            die_trace(1, f"Path does not exist: {path}")

    def check_is_dir_or_die(self, path: str):
        """Checks if a path is a directory, otherwise calls die_trace."""
        if not os.path.isdir(path):
            die_trace(1, f"Path is not a directory: {path}")

    def check_is_file_or_die(self, path: str):
        """Checks if a path is a regular file, otherwise calls die_trace."""
        if not os.path.isfile(path):
            die_trace(1, f"Path is not a file: {path}")
            
    # --- Mount/Unmount Functions ---
    
    def mount(self, source: str, target: str, fstype: Optional[str] = None, options: Optional[str] = None):
        """Wrapper for the 'mount' command."""
        cmd = ["mount"]
        if fstype:
            cmd.extend(["-t", fstype])
        if options:
            cmd.extend(["-o", options])
        cmd.extend([source, target])
        
        try:
            subprocess.run(cmd, check=True)
            print(f"Mounted {source} to {target}")
        except subprocess.CalledProcessError as e:
            die_trace(1, f"Failed to mount {source} to {target}: {e}")
            
    # The 'umount', 'chroot_exec', 'bind_mount' and 'is_mounted' functions 
    # would be implemented similarly using 'subprocess.run'.


# --- Example Usage ---

if __name__ == "__main__":
    # The 'protection.py' guard would run here or be called by the parent script.
    
    # Example initialization:
    utils = GentooInstallerUtils(gentoo_install_repo_dir="/path/to/repo")
    
    # Example usage:
    # utils.mount("proc", "/mnt/gentoo/proc", fstype="proc")
    
    print("\nGentooInstallerUtils class successfully defined.")

