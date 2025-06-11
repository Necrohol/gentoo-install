#!/bin/bash

# refind-helper.sh - Enhanced dual-boot detection and rEFInd setup
# Detects multiple ESP partitions and configures rEFInd for Windows/Linux dual-boot
### adds tools netboot.xyz.efi etc great for interwebs rescue cd without needing a phyical rescue cd. or anything else including gentoo live over interwebs. should the worst happen. 
# mkdir esp/EFI/refind/drivers_x64
# cp /usr/share/refind/drivers_x64/drivername_x64.efi esp/EFI/refind/drivers_x64/ 
# https://efi.akeo.ie/   has varrious drivers in efi. 
### Normally I have done this step by hand with Pentoo Linux (aka) Gentoo with Pentatation Testing and cybersecurity tools baked into ISO. 
### pentoo Installer has a few irks and quirks (not using the automatic cause intaller to die.), 
### and or adding tools once the box comes up. https://github.com/oddlama/gentoo-install for more repeatable automation 

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
        exit 1
    fi
}

# Check if system is EFI
check_efi() {
    if [[ -d /sys/firmware/efi/ ]]; then
        log "EFI system detected"
        return 0
    else
        error "BIOS system detected - EFI required for rEFInd"
        exit 1
    fi
}

# Detect architecture
detect_arch() {
    local arch=$(uname -m)
    case $arch in
        x86_64)
            echo "amd64"
            ;;
        aarch64)
            echo "arm64"
            ;;
        riscv64)
            echo "riscv64"
            ;;
        *)
            error "Unsupported architecture: $arch"
            exit 1
            ;;
    esac
}

# Find all ESP partitions
find_esp_partitions() {
    local esp_partitions=()
    
    # Method 1: Using lsblk to find EFI System Partition type
    log "Searching for ESP partitions..."
    
    while read -r line; do
        if [[ -n "$line" ]]; then
            esp_partitions+=("$line")
        fi
    done < <(lsblk -no PATH,PARTTYPE | grep -i "C12A7328-F81F-11D2-BA4B-00A0C93EC93B" | awk '{print $1}')
    
    # Method 2: Check mounted ESP partitions
    while read -r line; do
        local mountpoint=$(echo "$line" | awk '{print $2}')
        local device=$(echo "$line" | awk '{print $1}')
        if [[ "$mountpoint" == "/boot/efi" ]] || [[ "$mountpoint" == "/efi" ]]; then
            if [[ ! " ${esp_partitions[*]} " =~ " ${device} " ]]; then
                esp_partitions+=("$device")
            fi
        fi
    done < <(mount | grep -E "(vfat|fat32)" | grep -v tmpfs)
    
    printf '%s\n' "${esp_partitions[@]}"
}

# Mount ESP partition if not mounted
mount_esp() {
    local esp_device="$1"
    local mount_point="/tmp/esp_$(basename "$esp_device")"
    
    if mountpoint -q "$mount_point" 2>/dev/null; then
        echo "$mount_point"
        return 0
    fi
    
    mkdir -p "$mount_point"
    if mount "$esp_device" "$mount_point"; then
        echo "$mount_point"
        return 0
    else
        error "Failed to mount $esp_device"
        return 1
    fi
}

# Detect Windows ESP
detect_windows_esp() {
    local esp_partitions=("$@")
    local windows_esp=""
    
    for esp in "${esp_partitions[@]}"; do
        local mount_point=$(mount_esp "$esp")
        if [[ -n "$mount_point" ]]; then
            # Check for Windows Boot Manager
            if [[ -f "$mount_point/EFI/Microsoft/Boot/bootmgfw.efi" ]] || \
               [[ -f "$mount_point/EFI/Microsoft/Boot/winload.efi" ]]; then
                windows_esp="$mount_point"
                log "Windows ESP found: $esp -> $mount_point"
                break
            fi
        fi
    done
    
    echo "$windows_esp"
}

# Detect Linux ESP
detect_linux_esp() {
    local esp_partitions=("$@")
    local linux_esp=""
    
    for esp in "${esp_partitions[@]}"; do
        local mount_point=$(mount_esp "$esp")
        if [[ -n "$mount_point" ]]; then
            # Check for common Linux bootloaders
            if [[ -f "$mount_point/EFI/GRUB/grubx64.efi" ]] || \
               [[ -f "$mount_point/EFI/Gentoo/grubx64.efi" ]] || \
               [[ -f "$mount_point/EFI/systemd/systemd-bootx64.efi" ]] || \
               [[ -f "$mount_point/EFI/BOOT/bootx64.efi" ]]; then
                linux_esp="$mount_point"
                log "Linux ESP found: $esp -> $mount_point"
                break
            fi
        fi
    done
    
    echo "$linux_esp"
}

# Install rEFInd package if not present
install_refind_package() {
    local arch="$1"
    
    case "$arch" in
        arm64)
            # ARM64 workaround - use Debian package due to Gentoo ebuild issues
            if [[ ! -d "/usr/share/refind" ]] && [[ ! -f "/tmp/refind_installed" ]]; then
                warn "ARM64 detected - using Debian package workaround for rEFInd"
                warn "Gentoo ebuild has symlink issues in fakeroot"
                
                local temp_dir=$(mktemp -d)
                cd "$temp_dir"
                
                # Download Debian package
                wget -q "http://ftp.us.debian.org/debian/pool/main/r/refind/refind_0.13.2-1+b1_arm64.deb" || {
                    error "Failed to download rEFInd ARM64 Debian package"
                    exit 1
                }
                
                # Extract using deb2targz if available, otherwise use ar/tar
                if command -v deb2targz >/dev/null 2>&1; then
                    deb2targz refind_0.13.2-1+b1_arm64.deb
                    tar -xf refind_0.13.2-1+b1_arm64.tar.gz
                else
                    # Manual extraction
                    ar x refind_0.13.2-1+b1_arm64.deb
                    tar -xf data.tar.xz
                fi
                
                # Install files manually
                cp -r usr/share/refind /usr/share/ 2>/dev/null || true
                cp -r usr/bin/* /usr/bin/ 2>/dev/null || true
                
                # Mark as installed
                touch /tmp/refind_installed
                
                cd - >/dev/null
                rm -rf "$temp_dir"
                
                log "rEFInd ARM64 installed via Debian package workaround"
            else
                log "rEFInd already available for ARM64"
            fi
            ;;
        riscv64)
            error "RISC-V is not supported by rEFInd yet"
            error "Consider using systemd-boot or GRUB for RISC-V systems"
            exit 1
            ;;
        amd64)
            # Standard Gentoo installation for AMD64
            if ! grep -q "sys-boot/refind" /var/lib/portage/world 2>/dev/null; then
                log "Installing rEFInd package for AMD64..."
                
                # Add USE flags
                local use_flags="ext2 ext4 iso9660 btrfs doc hfs ntfs reiserfs secureboot"
                echo "sys-boot/refind $use_flags" >> /etc/portage/package.use/refind
                
                # Install package
                USE="$use_flags" emerge -avqk sys-boot/refind || {
                    error "Failed to install rEFInd package"
                    exit 1
                }
            else
                log "rEFInd package already installed"
            fi
            ;;
    esac
}

# Setup rEFInd
setup_refind() {
    local win_esp="$1"
    local arch="$2"
    
    log "Setting up rEFInd in Windows ESP: $win_esp"
    
    case "$arch" in
        arm64)
            # ARM64 manual installation due to Gentoo ebuild issuese that cause builds to die.
            log "ARM64: Manual rEFInd installation"
            mkdir -p "$win_esp/EFI/refind"
            
            if [[ -d "/usr/share/refind" ]]; then
                cp -r /usr/share/refind/* "$win_esp/EFI/refind/"
                
                # Fix potential symlink issues from Gentoo ebuild that cause builds to die.
                find "$win_esp/EFI/refind" -type l -exec rm {} \;
                
                # Copy ARM64 specific binaries
                if [[ -f "/usr/share/refind/refind_aa64.efi" ]]; then
                    cp /usr/share/refind/refind_aa64.efi "$win_esp/EFI/refind/refind_aa64.efi"
                    # Create bootaa64.efi as fallback
                    cp /usr/share/refind/refind_aa64.efi "$win_esp/EFI/BOOT/bootaa64.efi" 2>/dev/null || true
                fi
            else
                error "rEFInd files not found - installation may have failed"
                exit 1
            fi
            ;;
        amd64)
            # Standard installation for AMD64
            refind-install --usedefault "$win_esp/EFI/refind/" --shim /usr/share/shim-signed/shimx64.efi || {
                warn "Standard rEFInd install failed, trying manual method"
                mkdir -p "$win_esp/EFI/refind"
                cp -r /usr/share/refind/* "$win_esp/EFI/refind/"
            }
            ;;
    esac
    
    # Create tools directory
    mkdir -p "$win_esp/EFI/refind/tools"
    
    # Copy security tools if available (mainly for AMD64)
    if [[ "$arch" == "amd64" ]]; then
        if [[ -f "/usr/share/shim/mmx64.efi" ]]; then
            cp /usr/share/shim/mmx64.efi "$win_esp/EFI/refind/mmx64.efi"
        fi
        
        if [[ -f "/usr/share/efitools/efi/KeyTool.efi" ]]; then
            cp /usr/share/efitools/efi/KeyTool.efi "$win_esp/EFI/refind/tools/KeyTool.efi"
        fi
    fi
}

# Download additional tools
download_tools() {
    local win_esp="$1"
    local arch="$2"
    local tools_dir="$win_esp/EFI/refind/tools"
    
    log "Downloading additional tools for $arch..."
    
    case "$arch" in
        amd64)
            # Download netboot.xyz 
            wget -q -O "$tools_dir/netboot.xyz.efi" \
                "https://boot.netboot.xyz/ipxe/netboot.xyz.efi" || warn "Failed to download netboot.xyz" 
            # Download netboot.xyz 
            wget -q -O "$tools_dir/netboot.xyz-snp.efi" \
                "https://boot.netboot.xyz/ipxe/netboot.xyz-snp.efi" || warn "Failed to download netboot.xyz.snp" 				
            
            # Download iPXE
            wget -q -O "$tools_dir/ipxe.efi" \
                "https://boot.ipxe.org/ipxe.efi" || warn "Failed to download iPXE"
            
            # Download memtest86+ (requires extraction)
            local memtest_url="https://www.memtest.org/download/v7.20/mt86plus_7.20.binaries.zip"
            local temp_dir=$(mktemp -d)
            if wget -q -O "$temp_dir/memtest.zip" "$memtest_url"; then
                cd "$temp_dir"
                unzip -q memtest.zip
                if [[ -f "memtest64.efi" ]]; then
                    cp memtest64.efi "$tools_dir/memtest64.efi"
                fi
                if [[ -f "memtest32.efi" ]]; then
                    cp memtest32.efi "$tools_dir/memtest32.efi"
                fi
                rm -rf "$temp_dir"
            else
                warn "Failed to download memtest86+"
            fi
            ;;
        arm64)
            # Download ARM64 specific tools
            wget -q -O "$tools_dir/netboot.xyz-arm64.efi" \
                "https://boot.netboot.xyz/ipxe/netboot.xyz-arm64.efi" || warn "Failed to download netboot.xyz ARM64"
				            wget -q -O "$tools_dir/netboot.xyz-arm64-snp.efi" \
                "https://boot.netboot.xyz/ipxe/netboot.xyz-arm64-snp.efi" || warn "Failed to download netboot.snp.xyz ARM64"
            
            wget -q -O "$tools_dir/ipxe-arm64.efi" \
                "https://boot.ipxe.org/arm64-efi/ipxe.efi" || warn "Failed to download iPXE ARM64"
            ;;
    esac
}

# Create rEFInd configuration
create_refind_config() {
    local win_esp="$1"
    local linux_esp="$2"
    local config_file="$win_esp/EFI/refind/refind.conf"
    
    log "Creating rEFInd configuration..."
    
    cat > "$config_file" << EOF
# rEFInd configuration file
# Auto-generated by refind-helper.sh

timeout 20
use_graphics_for osx,linux
scanfor manual,external,optical,netboot
also_scan_dirs EFI/Microsoft/Boot,EFI/GRUB,EFI/Gentoo,EFI/systemd

# Default selection
default_selection "+,bzImage,vmlinuz"

# Hide unwanted entries
dont_scan_files shim.efi,MokManager.efi,fbx64.efi,mmx64.efi

# Windows entry
menuentry "Windows" {
    loader /EFI/Microsoft/Boot/bootmgfw.efi
    icon /EFI/refind/icons/os_win.png
    ostype Windows
}

# Linux entry (if separate ESP)
EOF

    if [[ -n "$linux_esp" ]] && [[ "$linux_esp" != "$win_esp" ]]; then
        cat >> "$config_file" << EOF
menuentry "Linux" {
    loader /EFI/GRUB/grubx64.efi
    icon /EFI/refind/icons/os_linux.png
    ostype Linux
}
EOF
    fi

    cat >> "$config_file" << EOF

# Tools submenu
showtools memtest, gdisk, gptsync, netboot, shell, KeyTool ,netboot.xyz,ipxe
EOF
}

# Main function
main() {
    check_root
    check_efi
    
    local arch=$(detect_arch)
    log "Detected architecture: $arch"
    
    # Find ESP partitions
    local esp_partitions=($(find_esp_partitions))
    
    if [[ ${#esp_partitions[@]} -eq 0 ]]; then
        error "No ESP partitions found"
        exit 1
    fi
    
    log "Found ${#esp_partitions[@]} ESP partition(s): ${esp_partitions[*]}"
    
# Check drive separation for stability
check_drive_separation() {
    local esp_partitions=("$@")
    local drives=()
    
    # Extract unique drives from ESP partitions
    for esp in "${esp_partitions[@]}"; do
        local drive=$(lsblk -no PKNAME "$esp" | head -1)
        if [[ ! " ${drives[*]} " =~ " ${drive} " ]]; then
            drives+=("$drive")
        fi
    done
    
    log "Found ESP partitions on ${#drives[@]} drive(s): ${drives[*]}"
    
    if [[ ${#drives[@]} -eq 1 ]]; then
        warn "All ESP partitions are on the same physical drive: ${drives[0]}"
        warn "This breaks the generally preferred rule of separate drives for Windows/Linux stability"
        
        # Extra warning for ARM64
        if [[ "$(detect_arch)" == "arm64" ]]; then
            warn "ARM64 dual-boot setup is inherently more risky"
            warn "Windows 11 ARM64 + Linux on same drive increases instability risk"
            echo -e "${RED}WARNING: Proceeding with ARM64 same-drive dual-boot setup${NC}"
            echo -e "${RED}Consider using separate drives for better stability${NC}"
            
            read -p "Continue anyway? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log "Aborting setup for safety"
                exit 0
            fi
        else
            warn "Recommend using separate physical drives for Windows and Linux"
            read -p "Continue with same-drive setup? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log "Aborting setup - consider separate drives"
                exit 0
            fi
        fi
    else
        log "Good: ESP partitions are on separate drives (preferred for stability)"
    fi
}
    
    if [[ -z "$WIN_ESP" ]]; then
        error "Windows ESP not found"
        exit 1
    fi
    
    if [[ -z "$LINUX_ESP" ]]; then
        warn "Linux ESP not found - assuming single ESP setup"
        LINUX_ESP="$WIN_ESP"
    fi
    
    if [[ "$WIN_ESP" == "$LINUX_ESP" ]]; then
        warn "Windows and Linux share the same ESP - this may cause conflicts"
    fi
    
    # Install rEFInd package
    install_refind_package "$arch"
    
    # Setup rEFInd
    setup_refind "$WIN_ESP" "$arch"
    
    # Download additional tools
    download_tools "$WIN_ESP" "$arch"
    
    # Create configuration
    create_refind_config "$WIN_ESP" "$LINUX_ESP"
    
    log "rEFInd setup completed successfully!"
    log "Windows ESP: $WIN_ESP"
    log "Linux ESP: $LINUX_ESP"
    log "Reboot and select rEFInd from your UEFI firmware to test"
    
    # Cleanup - unmount temporary mount points
    for esp in "${esp_partitions[@]}"; do
        local mount_point="/tmp/esp_$(basename "$esp")"
        if mountpoint -q "$mount_point" 2>/dev/null; then
            umount "$mount_point" 2>/dev/null || true
            rmdir "$mount_point" 2>/dev/null || true
        fi
    done
}

# Run main function
main "$@"