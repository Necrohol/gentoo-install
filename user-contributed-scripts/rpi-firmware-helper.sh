#!/bin/bash

### rpi-firmware-helper [UEFI & GRUB] with embedded U-Boot/UEFI module ###
### odlama-gentoo-Installer ###

# Define firmware URLs
declare -A RPI_FIRMWARE
RPI_FIRMWARE["RPI5"]="https://github.com/worproject/rpi5-uefi/releases/download/v0.3/RPi5_UEFI_Release_v0.3.zip"
RPI_FIRMWARE["RPI4"]="https://github.com/pftf/RPi4/releases/download/v1.42/RPi4_UEFI_Firmware_v1.42.zip"
RPI_FIRMWARE["RPI3"]="https://github.com/pftf/RPi3/releases/download/v1.39/RPi3_UEFI_Firmware_v1.39.zip"

# Function to find all ESP partitions
find_esp_partitions() {
    local esp_partitions=()

    echo "Searching for ESP partitions..."

    # Method 1: Using lsblk for EFI System Partition type detection
    while read -r line; do
        if [[ -n "$line" ]]; then
            esp_partitions+=("$line")
        fi
    done < <(lsblk -no PATH,PARTTYPE | grep -i "C12A7328-F81F-11D2-BA4B-00A0C93EC93B" | awk '{print $1}')

    # Method 2: Using blkid to locate FAT32 ESP partitions
    if [[ ${#esp_partitions[@]} -eq 0 ]]; then
        echo "No ESP partitions found using lsblk. Trying blkid..."
        while read -r line; do
            esp_partitions+=("$line")
        done < <(blkid -t TYPE=vfat -o device)
    fi

    # Display results
    if [[ ${#esp_partitions[@]} -eq 0 ]]; then
        echo "No EFI System Partitions detected."
        return 1
    else
        echo "Found ESP partitions:"
        printf '%s\n' "${esp_partitions[@]}"
        return 0
    fi
}

# Detect chroot environment
detect_chroot() {
    if [[ -d "/mnt/gentoo/boot/efi" ]]; then
        echo "Chroot environment detected at /mnt/gentoo/boot/efi."
        EFI_PATH="/mnt/gentoo/boot/efi"
    else
        EFI_PATH="/boot/efi"
    fi
}

# Prompt user for board selection
echo "Select your Raspberry Pi model:"
echo "1) RPI5"
echo "2) RPI4"
echo "3) RPI3"
read -p "Enter choice (1/2/3): " CHOICE

# Determine board type
case "$CHOICE" in
    1) BOARD="RPI5" ;;
    2) BOARD="RPI4" ;;
    3) BOARD="RPI3" ;;
    *) echo "Invalid choice. Exiting."; exit 1 ;;
esac

# Ensure ESP partition exists
detect_chroot
find_esp_partitions || { echo "No valid EFI partition found. Exiting."; exit 1; }

# Download firmware
echo "Downloading firmware for $BOARD..."
wget "${RPI_FIRMWARE[$BOARD]}" -O firmware.zip

# Unpack firmware
echo "Extracting firmware to $EFI_PATH..."
mkdir -p "$EFI_PATH"
unzip firmware.zip -d "$EFI_PATH"

# Backup and update config.txt
CONFIG_FILE="/boot/.rpi/config.txt"
if [[ -f "$CONFIG_FILE" ]]; then
    echo "Backing up config.txt..."
    mv "$CONFIG_FILE" "/boot/.rpi/config.txt.old"
fi

# Create symlink
echo "Creating symlink: $EFI_PATH -> /boot/firmware"
ln -sf "$EFI_PATH" /boot/firmware

echo "Setup complete!"
echo "Warning: config.txt has fewer options under UEFI, so take due care when editing it or using Raspberry Pi tools. Backup before modifications!"