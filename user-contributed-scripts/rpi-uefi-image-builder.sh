#!/bin/bash
rpi-uefi-image-builder.sh 

# Set base URL
BASE_URL="https://gentoo.osuosl.org/releases/arm64/autobuilds"

# Fetch latest ISO filename
LATEST_ISO=$(curl -s "$BASE_URL/latest-iso.txt" | grep -oE '[0-9T]+/install-arm64-minimal-[0-9T]+.iso')

# Fetch available Stage 3 tarballs
STAGE3_TARBALLS=$(curl -s "$BASE_URL/latest-stage3.txt" | grep -oE '[0-9T]+/stage3-arm64-[^ ]+.tar.xz')

# Validate results
if [[ -z "$LATEST_ISO" || -z "$STAGE3_TARBALLS" ]]; then
    echo "Error: Failed to retrieve latest ISO or Stage 3 tarballs."
    exit 1
fi

# Present choices to user
echo "Latest Gentoo ARM64 Minimal Install ISO: $LATEST_ISO"
echo "Available Stage 3 tarballs:"
i=1
declare -A TARBALL_MAP
for tarball in $STAGE3_TARBALLS; do
    echo "$i) $tarball"
    TARBALL_MAP[$i]="$tarball"
    ((i++))
done

# User selection
echo -e "\nChoose an option:"
echo "1) Download latest ISO"
echo "2) Download a Stage 3 tarball"
echo "3) Download both ISO and a Stage 3 tarball"
read -p "Enter choice (1/2/3): " CHOICE

case "$CHOICE" in
    1) wget "$BASE_URL/$LATEST_ISO" -O install-arm64-minimal.iso ;;
    2)  
        read -p "Enter number of the tarball: " TAR_CHOICE
        if [[ -n "${TARBALL_MAP[$TAR_CHOICE]}" ]]; then
            wget "$BASE_URL/${TARBALL_MAP[$TAR_CHOICE]}" -O stage3-arm64-selected.tar.xz
        else
            echo "Invalid selection, exiting."
            exit 1
        fi
        ;;
    3)  
        wget "$BASE_URL/$LATEST_ISO" -O install-arm64-minimal.iso
        read -p "Enter number of the tarball: " TAR_CHOICE
        if [[ -n "${TARBALL_MAP[$TAR_CHOICE]}" ]]; then
            wget "$BASE_URL/${TARBALL_MAP[$TAR_CHOICE]}" -O stage3-arm64-selected.tar.xz
        else
            echo "Invalid selection, exiting."
            exit 1
        fi
        ;;
    *) echo "Invalid choice, exiting." ;;
esac
echo "Download complete!"

# Check if ISO contains squashfs
ISO_MOUNT_DIR="/mnt/iso"
mkdir -p "$ISO_MOUNT_DIR"
sudo mount -o loop install-arm64-minimal.iso "$ISO_MOUNT_DIR"

SQUASHFS_FILE=$(find "$ISO_MOUNT_DIR" -name "*.squashfs")

if [[ -n "$SQUASHFS_FILE" ]]; then
    echo "Extracting squashfs from ISO..."
    sudo unsquashfs -d /mnt/gentoo "$SQUASHFS_FILE"
else
    echo "No squashfs found, falling back to Stage 3 tarball..."
    tar xpvf stage3-arm64-selected.tar.xz --xattrs-include='*.*' --numeric-owner -C /mnt/gentoo
fi

sudo umount "$ISO_MOUNT_DIR"

#### rpi5,4,3 UEFI firmware add to diskimage 
# Prompt user for sourcing rpi-firmware-helper.sh
echo "Would you like to source rpi-firmware-helper.sh before continuing? (y/n)"
read -r SOURCE_HELPER

if [[ "$SOURCE_HELPER" == "y" ]]; then
    if [[ -f "./rpi-firmware-helper.sh" ]]; then
        echo "Sourcing rpi-firmware-helper.sh..."
        source ./rpi-firmware-helper.sh
    else
        echo "Error: rpi-firmware-helper.sh not found!"
        exit 1
    fi
else
    echo "Skipping firmware helper sourcing..."
fi

# Continue with the rest of the script...



#### **Disk Image Creation**
IMAGE_FILE="gentoo-arm64-disk.img"
IMAGE_SIZE="15G"
BIOS_GRUB_SIZE="20M"
EFI_SIZE="120M"
BOOT_SIZE="550M"
BTRFS_SIZE="growable"

# Create necessary directories if they don’t exist
mkdir -p /mnt/gentoo
mkdir -p /tmp/squashfs-extracted

# Extract squashfs if applicable
if [[ -f "./image.squashfs" ]]; then
    echo "Extracting squashfs..."
    sudo unsquashfs -d /mnt/gentoo ./image.squashfs
fi

# Create sparse disk image file
echo "Creating disk image: $IMAGE_FILE ($IMAGE_SIZE)..."
truncate -s ${IMAGE_SIZE} ${IMAGE_FILE}

# Associate image with loop device
LOOP_DEVICE=$(sudo losetup -f -P --show ${IMAGE_FILE})
if [[ -z "$LOOP_DEVICE" ]]; then
    echo "Error: Failed to create loop device."
    exit 1
fi
echo "Loop device created: ${LOOP_DEVICE}"

# Partition disk image with GPT
echo "Partitioning disk image..."
sudo parted ${LOOP_DEVICE} mklabel gpt

# BIOS Boot Partition (20MiB)
echo "Creating 20MiB BIOS Boot partition..."
sudo parted ${LOOP_DEVICE} mkpart primary 1MiB ${BIOS_GRUB_SIZE}
sudo parted ${LOOP_DEVICE} set 1 bios_grub on

# EFI System Partition (120MiB)
echo "Creating 120MiB EFI System partition..."
sudo parted ${LOOP_DEVICE} mkpart primary ${BIOS_GRUB_SIZE} ${EFI_SIZE}
sudo parted ${LOOP_DEVICE} set 2 esp on

# ext4 /boot partition (550MiB)
echo "Creating 550MiB ext4 /boot partition..."
sudo parted ${LOOP_DEVICE} mkpart primary ${EFI_SIZE} ${BOOT_SIZE}
sudo mkfs.ext4 ${LOOP_DEVICE}p3

# Btrfs main partition (remaining space)
echo "Creating main growable Btrfs partition..."
sudo parted ${LOOP_DEVICE} mkpart primary ${BOOT_SIZE} 100%
sudo mkfs.btrfs ${LOOP_DEVICE}p4

# Mount partitions
sudo mount ${LOOP_DEVICE}p4 /mnt
mkdir -p /mnt/boot/efi /mnt/boot/firmware
ln -sf /mnt/boot/efi /mnt/boot/firmware

# Create Btrfs subvolume for swap
btrfs subvolume create /mnt/@swap
sudo chattr +C /mnt/@swap
sudo btrfs property set /mnt/@swap compression none
sudo fallocate -l 8G /mnt/@swap/swap.img

# Detach loop device
echo "Detaching loop device..."
sudo losetup -d ${LOOP_DEVICE}

echo "Disk image creation complete: $IMAGE_FILE"