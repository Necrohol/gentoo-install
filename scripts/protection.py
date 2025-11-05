import os
import sys

# Equivalent to: [[ "$GENTOO_INSTALL_REPO_SCRIPT_ACTIVE" != "true" ]]; then ...

if os.environ.get("GENTOO_INSTALL_REPO_SCRIPT_ACTIVE") != "true":
    # Equivalent to: echo "..." >&2; exit 1
    # \033[1;31m and \033[0m are the standard ANSI codes for bold red text.
    print("\033[1;31m * ERROR:\033[m This script must not be executed directly!", file=sys.stderr)
    sys.exit(1)

# If the check passes, the rest of the Python script would continue here.
