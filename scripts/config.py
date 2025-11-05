import os
import sys
import subprocess
from typing import List, Dict, Any, Optional
# Assuming protection.py exists and handles the initial safety check
# import protection # No need to import if we trust the calling script handles it

# --- Helper functions (would be in a utilities file in a real project) ---

def die_trace(exit_code: int, message: str):
    """Prints an error message to stderr and exits."""
    # Simplified error handling. In the real script, this would include a stack trace.
    print(f"\033[1;31m * FATAL ERROR:\033[m {message}", file=sys.stderr)
    sys.exit(exit_code)

def load_or_generate_uuid(base64_id: str) -> str:
    """Placeholder for function that loads or generates a UUID."""
    # In a real Gentoo installer, this would check /tmp/uuids/ and generate if needed.
    # For simplicity, we just return a stub UUID here.
    return f"STUB-UUID-{base64_id[:4]}"

def uuid_to_mduuid(uuid: str) -> str:
    """Placeholder for function that converts a standard UUID to an MDADM UUID format."""
    return uuid.replace('-', '') # Simplified conversion

def create_resolve_entry(new_id: str, resolve_type: str, resolve_value: str):
    """Placeholder for registering a device ID to a resolvable string (e.g., PARTUUID, LUKS name)."""
    # This information is typically used later by the mounting process.
    print(f"DEBUG: Registered {new_id} -> {resolve_type}={resolve_value}")

def create_resolve_entry_device(new_id: str, device: str):
    """Placeholder for registering a device ID to a physical device path."""
    print(f"DEBUG: Registered {new_id} -> device={device}")

# --- Argument Parsing (Complex Bash logic replaced by a simple Dict) ---

# In a real Python project, argument parsing would use argparse or be handled by the caller.
# Here, we simulate the results of the Bash 'parse_arguments' function.
def parse_arguments_python(arg_list: List[str]) -> tuple[Dict[str, str], List[str]]:
    """Simulates the Bash argument parsing to separate named arguments from positional ones."""
    arguments = {}
    extra_arguments = []
    for arg in arg_list:
        if '=' in arg:
            key, value = arg.split('=', 1)
            arguments[key] = value
        else:
            extra_arguments.append(arg)
    return arguments, extra_arguments


# --- The Main Configurator Class ---

class DiskConfigurator:
    """
    Holds the configuration and logic for defining the disk layout 
    of the Gentoo installation.
    """
    
    def __init__(self, base_dir: str):
        # Base temporary directory
        self.TMP_DIR = base_dir
        
        # --- System Configuration Variables ---
        self.ROOT_MOUNTPOINT = os.path.join(self.TMP_DIR, "root")
        self.GENTOO_INSTALL_REPO_BIND = os.path.join(self.TMP_DIR, "bind")
        self.UUID_STORAGE_DIR = os.path.join(self.TMP_DIR, "uuids")
        self.LUKS_HEADER_BACKUP_DIR = os.path.join(self.TMP_DIR, "luks-headers")

        # --- Feature Flags (Equivalent to Bash flags) ---
        self.USED_RAID = False
        self.USED_LUKS = False
        self.USED_ZFS = False
        self.USED_BTRFS = False
        self.USED_ENCRYPTION = False
        self.NO_PARTITIONING_OR_FORMATTING = False

        # --- Disk Configuration Data Structures ---
        # Equivalent to Bash array DISK_ACTIONS
        self.DISK_ACTIONS: List[str] = []
        # Equivalent to Bash array DISK_DRACUT_CMDLINE
        self.DISK_DRACUT_CMDLINE: List[str] = []
        # Equivalent to Bash associative arrays
        self.DISK_ID_TO_RESOLVABLE: Dict[str, str] = {}
        self.DISK_ID_PART_TO_GPT_ID: Dict[str, str] = {}
        self.DISK_ID_TO_UUID: Dict[str, str] = {}
        self.DISK_GPT_HAD_SIZE_REMAINING: Dict[str, bool] = {}

        # --- Final Mountpoint IDs (set by layout functions) ---
        self.DISK_ID_EFI: Optional[str] = None
        self.DISK_ID_BIOS: Optional[str] = None
        self.DISK_ID_SWAP: Optional[str] = None
        self.DISK_ID_ROOT: Optional[str] = None
        self.DISK_ID_ROOT_TYPE: Optional[str] = None
        self.DISK_ID_ROOT_MOUNT_OPTS: Optional[str] = None

    # --- Utility Methods (Bash functions transformed into class methods) ---

    def only_one_of(self, arguments: Dict[str, str], *keys: str):
        """Checks that only one of the provided keys exists in the arguments dictionary."""
        present_keys = [key for key in keys if key in arguments]
        if len(present_keys) > 1:
            die_trace(2, f"Only one of the arguments ({', '.join(keys)}) can be given")

    def create_new_id(self, arguments: Dict[str, str], arg_name: str):
        """Creates a new unique ID and registers it with a UUID."""
        id_val = arguments.get(arg_name)
        if not id_val:
            die_trace(2, f"Argument '{arg_name}' is required for ID creation.")
        
        if ';' in id_val:
            die_trace(2, "Identifier contains invalid character ';'")
        if id_val in self.DISK_ID_TO_UUID:
            die_trace(2, f"Identifier '{id_val}' already exists")
        
        # Base64 encoding for UUID generation (simplified)
        base64_id = id_val.encode('utf-8').hex() # Simple hex representation for uniqueness
        self.DISK_ID_TO_UUID[id_val] = load_or_generate_uuid(base64_id)

    def verify_existing_id(self, arguments: Dict[str, str], arg_name: str):
        """Checks if an ID provided in arguments already exists."""
        id_val = arguments.get(arg_name)
        if id_val not in self.DISK_ID_TO_UUID:
            die_trace(2, f"Identifier {arg_name}='{id_val}' not found")

    def verify_option(self, arguments: Dict[str, str], opt: str, *valid_options: str):
        """Checks if the value of an argument is one of the valid options."""
        arg_val = arguments.get(opt)
        if arg_val not in valid_options:
            die_trace(2, f"Invalid option {opt}='{arg_val}', must be one of ({', '.join(valid_options)})")

    def verify_existing_unique_ids(self, arguments: Dict[str, str], arg: str):
        """Checks for multiple existing, unique, and non-empty IDs in a semicolon-separated string."""
        ids_str = arguments.get(arg, "")
        ids = [i.strip() for i in ids_str.split(';') if i.strip()]

        if not ids:
            die_trace(2, f"{arg}=... must contain at least one entry")
        
        if len(ids) != len(set(ids)):
            die_trace(2, f"{arg}=... contains duplicate identifiers")

        for id_val in ids:
            if id_val not in self.DISK_ID_TO_UUID:
                die_trace(2, f"{arg}=... contains unknown identifier '{id_val}'")

    # --- Disk Action Methods (The core DSL) ---
    # Note: Bash's dynamic argument handling is replaced by explicit unpacking here.

    def register_existing(self, new_id: str, device: str):
        """Registers an existing device or partition."""
        arguments = {'new_id': new_id, 'device': device}
        self.create_new_id(arguments, 'new_id')
        
        create_resolve_entry_device(new_id, device)
        self.DISK_ACTIONS.append(f"action=existing new_id={new_id} device={device};")

    def create_gpt(self, new_id: str, device: Optional[str] = None, id_val: Optional[str] = None):
        """Creates a new GPT disk label."""
        arguments = {'new_id': new_id}
        if device: arguments['device'] = device
        if id_val: arguments['id'] = id_val

        self.only_one_of(arguments, 'device', 'id')
        self.create_new_id(arguments, 'new_id')
        if id_val: self.verify_existing_id(arguments, 'id')

        uuid = self.DISK_ID_TO_UUID[new_id]
        create_resolve_entry(new_id, "ptuuid", uuid)
        
        # Simplified action string assembly
        action = f"action=create_gpt new_id={new_id}"
        if device: action += f" device={device}"
        if id_val: action += f" id={id_val}"
        self.DISK_ACTIONS.append(action + ";")

    def create_partition(self, new_id: str, id_val: str, size: str, type: str):
        """Creates a new partition on a GPT table."""
        arguments = {'new_id': new_id, 'id': id_val, 'size': size, 'type': type}
        
        self.create_new_id(arguments, 'new_id')
        self.verify_existing_id(arguments, 'id')
        self.verify_option(arguments, 'type', 'bios', 'efi', 'swap', 'raid', 'luks', 'linux')

        if self.DISK_GPT_HAD_SIZE_REMAINING.get(id_val):
             die_trace(1, f"Cannot add another partition to table ({id_val}) after size=remaining was used")

        if size == "remaining":
            self.DISK_GPT_HAD_SIZE_REMAINING[id_val] = True

        self.DISK_ID_PART_TO_GPT_ID[new_id] = id_val
        uuid = self.DISK_ID_TO_UUID[new_id]
        create_resolve_entry(new_id, "partuuid", uuid)
        
        self.DISK_ACTIONS.append(f"action=create_partition new_id={new_id} id={id_val} size={size} type={type};")

    # --- Other DSL methods (create_raid, create_luks, format, etc.) would follow a similar structure ---

    # For brevity, only implementing the final layout function from the original Bash script:
    def create_classic_single_disk_layout(self, device: str, swap: str, type: str = 'efi', luks: str = 'false', root_fs: str = 'ext4'):
        """Single disk, 3 partitions (efi, swap, root)."""
        
        use_luks = luks == "true"
        
        self.create_gpt(new_id='gpt', device=device)
        self.create_partition(new_id=f"part_{type}", id_val='gpt', size='1GiB', type=type)
        if swap != "false":
            self.create_partition(new_id='part_swap', id_val='gpt', size=swap, type='swap')
        self.create_partition(new_id='part_root', id_val='gpt', size='remaining', type='linux')

        root_id = "part_root"
        if use_luks:
            self.USED_LUKS = True
            self.USED_ENCRYPTION = True
            # Simplified luks creation call
            self.DISK_ACTIONS.append(f"action=create_luks new_id=part_luks_root name=root id=part_root;")
            self.DISK_DRACUT_CMDLINE.append(f"rd.luks.uuid={self.DISK_ID_TO_UUID['part_luks_root']}")
            root_id = "part_luks_root"

        # Simplified format calls
        self.DISK_ACTIONS.append(f"action=format id=part_{type} type={type} label={type};")
        if swap != "false":
            self.DISK_ACTIONS.append(f"action=format id=part_swap type=swap label=swap;")
        self.DISK_ACTIONS.append(f"action=format id={root_id} type={root_fs} label=root;")

        # Set final mountpoint IDs
        if type == "efi":
            self.DISK_ID_EFI = f"part_{type}"
        else:
            self.DISK_ID_BIOS = f"part_{type}"

        if swap != "false":
            self.DISK_ID_SWAP = 'part_swap'
            
        self.DISK_ID_ROOT = root_id
        self.DISK_ID_ROOT_TYPE = root_fs

        if root_fs == "btrfs":
            self.DISK_ID_ROOT_MOUNT_OPTS = "defaults,noatime,compress-force=zstd,subvol=/root"
        elif root_fs == "ext4":
            self.DISK_ID_ROOT_MOUNT_OPTS = "defaults,noatime,errors=remount-ro,discard"
        else:
            die_trace(1, "Unsupported root filesystem type")

# --- Example Usage (How the main installer would call this) ---

if __name__ == "__main__":
    # Simulate the check from protection.sh
    if os.environ.get("GENTOO_INSTALL_REPO_SCRIPT_ACTIVE") != "true":
        print("\033[1;31m * ERROR:\033[m This script must not be executed directly!", file=sys.stderr)
        sys.exit(1)

    # Initialize the configurator
    config = DiskConfigurator(base_dir="/tmp/gentoo-install-python")
    
    # Example call mimicking the Bash script's usage in an installer:
    # Arguments would typically come from an external configuration file or TUI
    try:
        # Example 1: Classic single-disk EFI/LUKS setup
        config.create_classic_single_disk_layout(
            device="/dev/sda", 
            swap="8GiB", 
            type="efi", 
            luks="true", 
            root_fs="ext4"
        )
        
        # Print results for verification
        print("\n--- Final Configuration Summary ---")
        print(f"EFI ID: {config.DISK_ID_EFI}")
        print(f"ROOT ID: {config.DISK_ID_ROOT} ({config.DISK_ID_ROOT_TYPE})")
        print(f"USED LUKS: {config.USED_LUKS}")
        print("\nDISK ACTIONS:")
        for action in config.DISK_ACTIONS:
            print(f"  {action}")
            
    except SystemExit:
        # Catch die_trace calls
        pass
    except Exception as e:
        die_trace(1, f"An unexpected error occurred: {e}")
