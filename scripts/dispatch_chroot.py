#!/usr/bin/env python3
import os
import subprocess
import sys
from typing import List

def get_nproc() -> str:
    """Determine the number of available processing units (CPU cores)."""
    try:
        # Use Python's standard library function
        nproc_int = os.cpu_count() or 2
    except NotImplementedError:
        # Fallback in case os.cpu_count() fails or is not implemented
        try:
            nproc_result = subprocess.run(
                ["nproc"], capture_output=True, text=True, check=True, timeout=5
            )
            nproc_int = int(nproc_result.stdout.strip())
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError, subprocess.TimeoutExpired):
            print("Warning: Could not determine processor count, defaulting to 2.", file=sys.stderr)
            nproc_int = 2
            
    return str(nproc_int)

def setup_chroot_environment(nproc: str):
    """Set critical environment variables for compilation and package management."""
    
    # Set safe umask (Equivalent to: umask 0077)
    # The octal format 0o077 is used for umask in Python.
    os.umask(0o077)
    
    NPROC_INT = int(nproc)
    NPROC_ONE = str(NPROC_INT + 1)
    
    # Export variables (Equivalent to: export NPROC=..., NPROC_ONE=...)
    os.environ["NPROC"] = nproc
    os.environ["NPROC_ONE"] = NPROC_ONE
    
    # Set default makeflags (Equivalent to: export MAKEFLAGS="-j$NPROC")
    os.environ["MAKEFLAGS"] = f"-j{nproc}"
    
    # Set emerge flags for parallel emerges 
    # (Equivalent to: export EMERGE_DEFAULT_OPTS="...")
    # NOTE: These variables are highly specific to Gentoo's tools.
    os.environ["EMERGE_DEFAULT_OPTS"] = f"--jobs={NPROC_ONE} --load-average={nproc}"
    
    # Unset critical variables (Equivalent to: unset key)
    if "key" in os.environ:
        del os.environ["key"]

def dispatch_command(args: List[str]):
    """Execute the requested command, replacing the current process."""
    if not args:
        print("Error: No command provided for dispatch.", file=sys.stderr)
        sys.exit(1)
        
    command = args[0]
    
    # os.execvp replaces the current Python process with the new program.
    # This is the direct equivalent of the 'exec' shell command, ensuring 
    # the new program inherits the newly set environment variables.
    try:
        print(f"Executing command with new environment: {command} {' '.join(args[1:])}")
        os.execvp(command, args)
    except FileNotFoundError:
        print(f"Error: Command not found or could not be executed: {command}", file=sys.stderr)
        sys.exit(127) # Standard exit code for command not found

def main():
    # --- 1. Initial Safety Check ---
    # Equivalent to: [[ $EXECUTED_IN_CHROOT != "true" ]] && { ... }
    if os.environ.get("EXECUTED_IN_CHROOT") != "true":
        print("This script must be executed in a prepared chroot environment!", file=sys.stderr)
        # We exit with a different code than the command exit codes
        sys.exit(99) 

    # --- 2. Setup Environment ---
    processor_count = get_nproc()
    setup_chroot_environment(processor_count)
    
    # --- 3. Dispatch Command ---
    # sys.argv[0] is the script name itself, so we pass sys.argv[1:]
    dispatch_command(sys.argv[1:])

if __name__ == "__main__":
    # Note: Unlike Bash, sourcing /etc/profile is generally not done here. 
    # The Gentoo build process relies on the calling process (the installer) 
    # to have set up the chroot and necessary paths already.
    main()
