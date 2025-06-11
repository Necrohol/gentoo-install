#!/bin/bash

#riscv-stage-helper.sh

# Set base URL
BASE_URL="https://gentoo.osuosl.org/releases/riscv/autobuilds/"

# Fetch available Stage 3 tarballs
STAGE3_TARBALLS=$(curl -s "$BASE_URL/latest-stage3.txt" | grep -oE '[0-9T]+/stage3-rv64-[^ ]+.tar.xz')

# Validate results
if [[ -z "$STAGE3_TARBALLS" ]]; then
    echo "Failed to retrieve the latest Stage 3 tarballs."
    exit 1
fi

# Present choices to the user
echo "Available Stage 3 tarballs:"
i=1
declare -A TARBALL_MAP
for tarball in $STAGE3_TARBALLS; do
    echo "$i) $tarball"
    TARBALL_MAP[$i]="$tarball"
    ((i++))
done

read -p "Enter the number of the tarball you want to download: " CHOICE

# Check if the choice is valid
if [[ -n "${TARBALL_MAP[$CHOICE]}" ]]; then
    echo "Downloading: $BASE_URL/${TARBALL_MAP[$CHOICE]}"
    wget "$BASE_URL/${TARBALL_MAP[$CHOICE]}" -O stage3-rv64-selected.tar.xz
    echo "Download complete!"
else
    echo "Invalid choice. Exiting."
    exit 1
fi