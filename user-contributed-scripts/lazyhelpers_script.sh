#!/bin/bash
# lazyhelpers.sh - Fetch and install genfstab from Arch install scripts
# Minimal installation of just the essentials

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default settings
DEFAULT_PREFIX="/mnt/gentoo/usr"
REPO_URL="https://gitlab.archlinux.org/archlinux/arch-install-scripts/-/archive/master/arch-install-scripts-master.tar.gz"
TEMP_DIR=$(mktemp -d)
INSTALL_DOCS=false
INSTALL_COMPLETIONS=false
INSTALL_UPDATE_GRUB=false

# Cleanup function
cleanup() {
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Fetch and install genfstab utility from Arch install scripts
Optionally install Debian-style update-grub wrapper for Gentoo

OPTIONS:
    -p, --prefix PATH    Installation prefix (default: $DEFAULT_PREFIX)
    -d, --docs          Install documentation (man pages)
    -c, --completions   Install bash/zsh completions
    -g, --grub          Install update-grub wrapper (Debian-style for Gentoo)
    -h, --help          Show this help message

EXAMPLES:
    $0                           # Install to default prefix with minimal files
    $0 -p /usr/local            # Install to /usr/local
    $0 -d -c                    # Install with docs and completions
    $0 -g                       # Install with update-grub wrapper
    $0 -p /opt/tools -d -c -g   # Custom prefix with all extras

EOF
}

get_prefix() {
    local prefix="$1"
    
    if [[ -z "$prefix" ]]; then
        echo
        print_info "Installation prefix options:"
        echo "  1) Default: $DEFAULT_PREFIX (Gentoo chroot)"
        echo "  2) Custom path"
        echo
        read -p "Use default prefix? [Y/n]: " choice
        
        case "$choice" in
            [nN]|[nN][oO])
                read -p "Enter custom prefix path: " prefix
                if [[ -z "$prefix" ]]; then
                    print_error "Empty prefix not allowed"
                    exit 1
                fi
                ;;
            *)
                prefix="$DEFAULT_PREFIX"
                ;;
        esac
    fi
    
    echo "$prefix"
}

check_dependencies() {
    local deps=("curl" "tar" "make" "m4")
    local missing=()
    
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            missing+=("$dep")
        fi
    done
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        print_error "Missing dependencies: ${missing[*]}"
        print_info "Please install: ${missing[*]}"
        exit 1
    fi
}

fetch_sources() {
    print_info "Fetching Arch install scripts..."
    cd "$TEMP_DIR"
    
    if ! curl -sL "$REPO_URL" | tar -xz; then
        print_error "Failed to fetch and extract sources"
        exit 1
    fi
    
    cd arch-install-scripts-master
    print_success "Sources fetched successfully"
}

build_genfstab() {
    print_info "Building genfstab..."
    
    # Create minimal Makefile for just genfstab
    cat > Makefile.minimal << 'EOF'
PREFIX ?= /usr/local
VER = 26

# Core files needed
BINPROGS = genfstab
CORE_FILES = genfstab.in fstab-helpers common

# Optional files
MANS = doc/genfstab.8
ZSHCOMP = completion/zsh/_genfstab
BASHCOMP = completion/bash/genfstab

# Build variables
V_GEN = @echo "  GEN     " $@;
edit = $(V_GEN) m4 -P $@.in >$@ && chmod go-w,+x $@

# Main targets
all: $(BINPROGS)

genfstab: genfstab.in fstab-helpers common
	$(edit)

# Documentation (optional)
man: $(MANS)
doc/genfstab.8: doc/genfstab.asciidoc doc/asciidoc.conf
	$(V_GEN) a2x --no-xmllint --asciidoc-opts="-f doc/asciidoc.conf" -d manpage -f manpage -D doc $<

# Installation
install-core: $(BINPROGS)
	install -d $(DESTDIR)$(PREFIX)/bin
	install -m 0755 $(BINPROGS) $(DESTDIR)$(PREFIX)/bin

install-docs: man
	install -d $(DESTDIR)$(PREFIX)/share/man/man8
	install -m 0644 $(MANS) $(DESTDIR)$(PREFIX)/share/man/man8

install-completions:
	install -d $(DESTDIR)$(PREFIX)/share/zsh/site-functions
	install -m 0644 $(ZSHCOMP) $(DESTDIR)$(PREFIX)/share/zsh/site-functions
	install -d $(DESTDIR)$(PREFIX)/share/bash-completion/completions
	install -m 0644 $(BASHCOMP) $(DESTDIR)$(PREFIX)/share/bash-completion/completions

clean:
	$(RM) $(BINPROGS) $(MANS)

.PHONY: all man install-core install-docs install-completions clean
EOF

    # Build the core utility
    if ! make -f Makefile.minimal all; then
        print_error "Failed to build genfstab"
        exit 1
    fi
    
    print_success "genfstab built successfully"
}

install_update_grub() {
    local prefix="$1"
    local grub_script="$prefix/bin/update-grub"
    local chroot_base=""
    
    print_info "Installing Debian-style update-grub wrapper..."
    
    # Detect if we're installing to a chroot
    if [[ "$prefix" == *"/mnt/gentoo"* ]]; then
        chroot_base="/mnt/gentoo"
        print_info "Detected Gentoo chroot installation"
    fi
    
    # Create the update-grub script
    mkdir -p "$prefix/bin"
    
    cat > "$grub_script" << 'EOF'
#!/bin/sh
# update-grub - Debian-style GRUB configuration updater
# Shamelessly filched from Debian for Gentoo convenience
set -e

# Detect if we're in a chroot environment
if [ -n "$CHROOT_BASE" ] && [ -d "$CHROOT_BASE" ]; then
    echo "Running grub-mkconfig in chroot environment..."
    chroot "$CHROOT_BASE" grub-mkconfig -o /boot/grub/grub.cfg "$@"
else
    echo "Running grub-mkconfig..."
    exec grub-mkconfig -o /boot/grub/grub.cfg "$@"
fi

# Disable memtest86+ if it exists (common Debian annoyance)
if [ -f /etc/grub.d/20_memtest86+ ]; then
    echo "Disabling memtest86+ GRUB entry..."
    chmod -x /etc/grub.d/20_memtest86+ 2>/dev/null || true
fi
EOF
    
    # Make it executable
    chmod +x "$grub_script"
    
    # If installing to a chroot, create a wrapper that knows about the chroot
    if [[ -n "$chroot_base" ]]; then
        cat > "$grub_script" << EOF
#!/bin/sh
# update-grub - Debian-style GRUB configuration updater for Gentoo chroot
# Shamelessly filched from Debian and adapted for chroot
set -e

CHROOT_BASE="$chroot_base"

echo "Running grub-mkconfig in Gentoo chroot..."
if [ -d "\$CHROOT_BASE" ]; then
    chroot "\$CHROOT_BASE" grub-mkconfig -o /boot/grub/grub.cfg "\$@"
    
    # Disable memtest86+ if it exists in chroot
    if [ -f "\$CHROOT_BASE/etc/grub.d/20_memtest86+" ]; then
        echo "Disabling memtest86+ GRUB entry in chroot..."
        chmod -x "\$CHROOT_BASE/etc/grub.d/20_memtest86+" 2>/dev/null || true
    fi
else
    echo "Error: Chroot base \$CHROOT_BASE not found!"
    exit 1
fi

echo "GRUB configuration updated successfully!"
EOF
        chmod +x "$grub_script"
    fi
    
    print_success "update-grub installed successfully"
}

install_files() {
    local prefix="$1"
    local install_targets=("install-core")
    
    print_info "Installing to: $prefix"
    
    # Create destination directory
    mkdir -p "$prefix"
    
    # Add optional targets
    if [[ "$INSTALL_DOCS" == true ]]; then
        if command -v a2x &> /dev/null; then
            install_targets+=("install-docs")
            print_info "Will install documentation"
        else
            print_warning "a2x not found, skipping documentation"
        fi
    fi
    
    if [[ "$INSTALL_COMPLETIONS" == true ]]; then
        install_targets+=("install-completions")
        print_info "Will install completions"
    fi
    
    # Install selected components
    for target in "${install_targets[@]}"; do
        if ! make -f Makefile.minimal "PREFIX=$prefix" "$target"; then
            print_error "Failed to install $target"
            exit 1
        fi
    done
    
    # Install update-grub wrapper if requested
    if [[ "$INSTALL_UPDATE_GRUB" == true ]]; then
        install_update_grub "$prefix"
    fi
    
    print_success "Installation completed!"
}

show_summary() {
    local prefix="$1"
    
    echo
    print_success "=== Installation Summary ==="
    echo "Prefix: $prefix"
    echo "Installed:"
    echo "  - genfstab utility: $prefix/bin/genfstab"
    
    if [[ "$INSTALL_UPDATE_GRUB" == true ]]; then
        echo "  - update-grub wrapper: $prefix/bin/update-grub"
    fi
    
    if [[ "$INSTALL_DOCS" == true ]] && command -v a2x &> /dev/null; then
        echo "  - Manual page: $prefix/share/man/man8/genfstab.8"
    fi
    
    if [[ "$INSTALL_COMPLETIONS" == true ]]; then
        echo "  - Bash completion: $prefix/share/bash-completion/completions/genfstab"
        echo "  - Zsh completion: $prefix/share/zsh/site-functions/_genfstab"
    fi
    
    echo
    print_info "Usage Examples:"
    print_info "  genfstab: $prefix/bin/genfstab -U /mnt >> /mnt/etc/fstab"
    
    if [[ "$INSTALL_UPDATE_GRUB" == true ]]; then
        print_info "  update-grub: $prefix/bin/update-grub"
        if [[ "$prefix" == *"/mnt/gentoo"* ]]; then
            print_info "  (Chroot-aware: will run grub-mkconfig inside /mnt/gentoo)"
        fi
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--prefix)
            PREFIX="$2"
            shift 2
            ;;
        -d|--docs)
            INSTALL_DOCS=true
            shift
            ;;
        -c|--completions)
            INSTALL_COMPLETIONS=true
            shift
            ;;
        -g|--grub)
            INSTALL_UPDATE_GRUB=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    print_info "Arch Install Scripts Lazy Helper"
    echo
    
    # Get installation prefix
    PREFIX=$(get_prefix "$PREFIX")
    
    # Check system dependencies
    check_dependencies
    
    # Fetch and build
    fetch_sources
    build_genfstab
    install_files "$PREFIX"
    
    # Show summary
    show_summary "$PREFIX"
}

# Run main function
main