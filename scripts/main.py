import os
import sys
import subprocess
import re
from typing import List, Dict, Optional, Callable

# --- Protection Guard ---
# This line replaces:
# # shellcheck source=./scripts/protection.sh
# source "$GENTOO_INSTALL_REPO_DIR/scripts/protection.sh" || exit 1
import protection 
# By importing 'protection', the 'run_protection_guard()' function inside 
# protection.py executes immediately, checking environment variables and 
# exiting the script if the safety guard conditions are not met.
# ------------------------

# Import necessary functions/classes from converted utilities and configuration
from utils import elog, einfo, ewarn, eerror, die, die_trace, try_command, ask, \
                  get_blkid_uuid_for_id, resolve_device_by_id, countdown, download, \
                  GENTOO_INSTALL_REPO_DIR, DISK_ID_TO_RESOLVABLE, UUID_STORAGE_DIR

# Placeholder for functions that would be in 'system.py' or 'mount.py'
def prepare_installation_environment(): elog("Preparation environment stub.")
def apply_disk_configuration(): elog("Applying disk configuration stub.")
def download_stage3(): elog("Downloading stage3 stub.")
def extract_stage3(): elog("Extracting stage3 stub.")
def mount_efivars(): elog("Mounting efivars stub.")
def mount_by_id(id_val: str, mountpoint: str): elog(f"Mounting {id_val} to {mountpoint} stub.")
def enable_service(service: str): elog(f"Enabling service {service} stub.")
def env_update(): elog("Running env-update stub.")
def mkdir_or_die(mode: int, path: str): os.makedirs(path, mode=mode, exist_ok=True)
def touch_or_die(mode: int, path: str): open(path, 'a').close()
def gentoo_umount(): elog("Unmounting old system mounts stub.")
def gentoo_chroot(root_mountpoint: str, bind_path: str, function_name: str): 
    elog(f"Entering chroot at {root_mountpoint} to execute {function_name} stub.")
    if function_name == "__install_gentoo_in_chroot":
        return GentooInstaller().main_install_gentoo_in_chroot()
    return 0
def getuto(): elog("Running getuto stub.")


# --- Main Installer Class ---

class GentooInstaller:
    """
    Orchestrates the Gentoo installation process, running complex steps 
    within the chroot environment. (Configuration attributes omitted for brevity)
    """
    
    # --- Configuration Variables (Placeholders) ---
    def __init__(self):
        # ... (Configuration loading remains the same as previous response) ...
        self.MUSL = os.environ.get("MUSL", "false") == "true"
        self.SYSTEMD = os.environ.get("SYSTEMD", "false") == "true"
        self.LOCALES = os.environ.get("LOCALES", "en_US.UTF-8 UTF-8")
        self.HOSTNAME = os.environ.get("HOSTNAME", "gentoo-host")
        self.KEYMAP = os.environ.get("KEYMAP", "us")
        self.LOCALE = os.environ.get("LOCALE", "en_US.UTF-8")
        self.TIMEZONE = os.environ.get("TIMEZONE", "America/New_York")
        self.SELECT_MIRRORS = os.environ.get("SELECT_MIRRORS", "false") == "true"
        self.SELECT_MIRRORS_LARGE_FILE = os.environ.get("SELECT_MIRRORS_LARGE_FILE", "false") == "true"
        self.ENABLE_BINPKG = os.environ.get("ENABLE_BINPKG", "false") == "true"
        self.ROOT_SSH_AUTHORIZED_KEYS = os.environ.get("ROOT_SSH_AUTHORIZED_KEYS", "")
        self.SYSTEMD_INITRAMFS_SSHD = os.environ.get("SYSTEMD_INITRAMFS_SSHD", "false") == "true"
        self.USED_RAID = os.environ.get("USED_RAID", "false") == "true"
        self.USED_LUKS = os.environ.get("USED_LUKS", "false") == "true"
        self.USED_BTRFS = os.environ.get("USED_BTRFS", "false") == "true"
        self.USED_ZFS = os.environ.get("USED_ZFS", "false") == "true"
        self.IS_EFI = os.environ.get("IS_EFI", "true") == "true"
        self.KEYMAP_INITRAMFS = os.environ.get("KEYMAP_INITRAMFS", "us")
        self.PORTAGE_SYNC_TYPE = os.environ.get("PORTAGE_SYNC_TYPE", "rsync")
        self.PORTAGE_GIT_MIRROR = os.environ.get("PORTAGE_GIT_MIRROR", "https://anongit.gentoo.org/repo/sync/gentoo.git")
        self.PORTAGE_GIT_FULL_HISTORY = os.environ.get("PORTAGE_GIT_FULL_HISTORY", "false") == "true"
        self.SYSTEMD_NETWORKD = os.environ.get("SYSTEMD_NETWORKD", "false") == "true"
        self.SYSTEMD_NETWORKD_DHCP = os.environ.get("SYSTEMD_NETWORKD_DHCP", "true") == "true"
        self.SYSTEMD_NETWORKD_INTERFACE_NAME = os.environ.get("SYSTEMD_NETWORKD_INTERFACE_NAME", "enp1s0")
        self.SYSTEMD_NETWORKD_ADDRESSES = os.environ.get("SYSTEMD_NETWORKD_ADDRESSES", "").split()
        self.SYSTEMD_NETWORKD_GATEWAY = os.environ.get("SYSTEMD_NETWORKD_GATEWAY", "")
        self.ENABLE_SSHD = os.environ.get("ENABLE_SSHD", "false") == "true"
        self.ADDITIONAL_PACKAGES = os.environ.get("ADDITIONAL_PACKAGES", "").split()
        self.USE_PORTAGE_TESTING = os.environ.get("USE_PORTAGE_TESTING", "false") == "true"
        self.GENTOO_ARCH = os.environ.get("GENTOO_ARCH", "amd64")
        self.LUKS_HEADER_BACKUP_DIR = "/tmp/gentoo-install/luks-headers"
        self.DISK_ID_ROOT = os.environ.get("DISK_ID_ROOT", "part_root")
        self.DISK_ID_ROOT_TYPE = os.environ.get("DISK_ID_ROOT_TYPE", "ext4")
        self.DISK_ID_ROOT_MOUNT_OPTS = os.environ.get("DISK_ID_ROOT_MOUNT_OPTS", "defaults")
        self.DISK_ID_EFI = os.environ.get("DISK_ID_EFI", "part_efi")
        self.DISK_ID_BIOS = os.environ.get("DISK_ID_BIOS", "part_bios")
        self.DISK_ID_SWAP = os.environ.get("DISK_ID_SWAP")
        self.DISK_DRACUT_CMDLINE: List[str] = []
        self.DISK_ID_PART_TO_GPT_ID: Dict[str, str] = {'part_efi': 'gpt', 'part_root': 'gpt'}
        
    # --- Installation Step Methods (All methods from the previous conversion are kept) ---

    def install_stage3(self):
        prepare_installation_environment()
        apply_disk_configuration()
        download_stage3()
        extract_stage3()

    def configure_base_system(self):
        # ... (Implementation remains the same) ...
        # 1. Locales
        if self.MUSL:
            einfo("Installing musl-locales")
            try_command("emerge", "--verbose", "sys-apps/musl-locales")
            with open("/etc/env.d/00local", "a") as f:
                f.write('MUSL_LOCPATH="/usr/share/i18n/locales/musl"\n')
        else:
            einfo("Generating locales")
            with open("/etc/locale.gen", "w") as f:
                f.write(self.LOCALES)
            try_command("locale-gen")
        
        # 2. Hostname, Keymap, Locale, Timezone (Systemd vs OpenRC)
        if self.SYSTEMD:
            einfo("Setting machine-id")
            try_command("systemd-machine-id-setup")
            
            einfo("Selecting hostname")
            with open("/etc/hostname", "w") as f: f.write(self.HOSTNAME)
            
            einfo("Selecting keymap")
            with open("/etc/vconsole.conf", "w") as f: f.write(f"KEYMAP={self.KEYMAP}\n")
            
            einfo("Selecting locale")
            with open("/etc/locale.conf", "w") as f: f.write(f"LANG={self.LOCALE}\n")

            einfo("Selecting timezone")
            os.symlink(f"../usr/share/zoneinfo/{self.TIMEZONE}", "/etc/localtime", follow_symlinks=False)

        else: # OpenRC/Standard
            einfo("Selecting hostname")
            try_command("sed", "-i", f"/hostname=/c\\hostname=\"{self.HOSTNAME}\"", "/etc/conf.d/hostname")
            
            # Timezone
            if self.MUSL:
                try_command("emerge", "-v", "sys-libs/timezone-data")
                einfo("Selecting timezone")
                with open("/etc/env.d/00local", "a") as f: f.write(f"TZ=\"{self.TIMEZONE}\"\n")
            else:
                einfo("Selecting timezone")
                with open("/etc/timezone", "w") as f: f.write(self.TIMEZONE)
                os.chmod("/etc/timezone", 0o644)
                try_command("emerge", "-v", "--config", "sys-libs/timezone-data")
            
            # Keymap
            einfo("Selecting keymap")
            try_command("sed", "-i", f"/keymap=/c\\keymap=\"{self.KEYMAP}\"", "/etc/conf.d/keymaps")

            # Locale
            einfo("Selecting locale")
            try_command("eselect", "locale", "set", self.LOCALE)
            
        env_update()

    def configure_portage(self):
        # ... (Implementation remains the same) ...
        mkdir_or_die(0o755, "/etc/portage/package.use")
        touch_or_die(0o644, "/etc/portage/package.use/zz-autounmask")
        mkdir_or_die(0o755, "/etc/portage/package.keywords")
        touch_or_die(0o644, "/etc/portage/package.keywords/zz-autounmask")
        touch_or_die(0o644, "/etc/portage/package.license")

        if self.SELECT_MIRRORS:
            einfo("Temporarily installing mirrorselect")
            try_command("emerge", "--verbose", "--oneshot", "app-portage/mirrorselect")
            einfo("Selecting fastest portage mirrors")
            mirrorselect_params = ["-s", "4", "-b", "10"]
            if self.SELECT_MIRRORS_LARGE_FILE:
                mirrorselect_params.append("-D")
            try_command("mirrorselect", *mirrorselect_params)
        
        with open("/etc/portage/make.conf", "a") as f:
            if self.ENABLE_BINPKG:
                f.write('FEATURES="getbinpkg binpkg-request-signature"\n')
                getuto()
                os.chmod("/etc/portage/gnupg/pubring.kbx", 0o644)

        os.chmod("/etc/portage/make.conf", 0o644)

    def enable_sshd(self):
        # ... (Implementation remains the same) ...
        einfo("Installing and enabling sshd")
        sshd_config_path = os.path.join(GENTOO_INSTALL_REPO_DIR, "contrib/sshd_config")
        try:
            subprocess.run(["install", "-m0600", "-o", "root", "-g", "root", sshd_config_path, "/etc/ssh/sshd_config"], check=True)
        except subprocess.CalledProcessError:
            die("Could not install /etc/ssh/sshd_config")
        enable_service("sshd")

    def install_authorized_keys(self):
        # ... (Implementation remains the same) ...
        mkdir_or_die(0o700, "/root/")
        mkdir_or_die(0o700, "/root/.ssh")

        if self.ROOT_SSH_AUTHORIZED_KEYS:
            einfo("Adding authorized keys for root")
            auth_keys_path = "/root/.ssh/authorized_keys"
            touch_or_die(0o600, auth_keys_path)
            with open(auth_keys_path, "w") as f:
                f.write(self.ROOT_SSH_AUTHORIZED_KEYS)
    
    # ... (generate_initramfs, get_cmdline, install_kernel_efi, generate_syslinux_cfg,
    #      install_kernel_bios, install_kernel, add_fstab_entry, generate_fstab implementations
    #      are identical to the previous conversion) ...

    def generate_initramfs(self, output: str):
        # ... (omitted for brevity, assume implementation is correct) ...
        pass
    
    def get_cmdline(self) -> str:
        # ... (omitted for brevity, assume implementation is correct) ...
        return ""

    def install_kernel_efi(self):
        # ... (omitted for brevity, assume implementation is correct) ...
        pass

    def generate_syslinux_cfg(self) -> str:
        # ... (omitted for brevity, assume implementation is correct) ...
        return ""

    def install_kernel_bios(self):
        # ... (omitted for brevity, assume implementation is correct) ...
        pass

    def install_kernel(self):
        # ... (omitted for brevity, assume implementation is correct) ...
        pass

    def add_fstab_entry(self, spec: str, file: str, vfstype: str, opt: str, pass_val: str):
        # ... (omitted for brevity, assume implementation is correct) ...
        pass

    def generate_fstab(self):
        # ... (omitted for brevity, assume implementation is correct) ...
        pass

    def main_install_gentoo_in_chroot(self):
        """The main installation routine executed inside the chroot."""
        # ... (Implementation remains the same) ...
        getattr(self, 'before_install', lambda: None)()

        einfo("Clearing root password")
        try_command("passwd", "-d", "root")

        einfo("Syncing portage tree")
        try_command("emerge-webrsync")

        # Mount EFI/BIOS partitions
        if self.IS_EFI:
            mount_efivars()
            einfo("Mounting efi partition")
            mount_by_id(self.DISK_ID_EFI, "/boot/efi")
        else:
            einfo("Mounting bios partition")
            mount_by_id(self.DISK_ID_BIOS, "/boot/bios")

        # Configure base system
        getattr(self, 'before_configure_base_system', lambda: None)()
        self.configure_base_system()
        getattr(self, 'after_configure_base_system', lambda: None)()

        # Configure portage
        getattr(self, 'before_configure_portage', lambda: None)()
        self.configure_portage()
        
        # Install git for portage sync
        einfo("Installing git")
        try_command("emerge", "--verbose", "dev-vcs/git")

        # Configure git sync for portage
        if self.PORTAGE_SYNC_TYPE == "git":
            mkdir_or_die(0o755, "/etc/portage/repos.conf")
            sync_depth = "0" if self.PORTAGE_GIT_FULL_HISTORY else "1"
            repo_conf = f"""[DEFAULT]
main-repo = gentoo

[gentoo]
location = /var/db/repos/gentoo
sync-type = git
sync-uri = {self.PORTAGE_GIT_MIRROR}
auto-sync = yes
sync-depth = {sync_depth}
sync-git-verify-commit-signature = yes
sync-openpgp-key-path = /usr/share/openpgp-keys/gentoo-release.asc
"""
            with open("/etc/portage/repos.conf/gentoo.conf", "w") as f: f.write(repo_conf)
            os.chmod("/etc/portage/repos.conf/gentoo.conf", 0o644)
            try_command("rm", "-rf", "/var/db/repos/gentoo")
            try_command("emerge", "--sync")
            
        getattr(self, 'after_configure_portage', lambda: None)()

        einfo("Generating ssh host keys")
        try_command("ssh-keygen", "-A")

        self.install_authorized_keys()

        einfo("Enabling dracut USE flag on sys-kernel/installkernel")
        with open("/etc/portage/package.use/installkernel", "w") as f: f.write("sys-kernel/installkernel dracut\n")

        # Install core kernel tools
        try_command("emerge", "--verbose", "sys-kernel/dracut", "sys-kernel/gentoo-kernel-bin", "app-arch/zstd")

        # Install conditional packages (LUKS, BTRFS, ZFS)
        if self.USED_LUKS:
            einfo("Installing cryptsetup")
            try_command("emerge", "--verbose", "sys-fs/cryptsetup")
            if self.SYSTEMD:
                einfo("Enabling cryptsetup USE flag on sys-apps/systemd")
                with open("/etc/portage/package.use/systemd", "w") as f: f.write("sys-apps/systemd cryptsetup\n")
                einfo("Rebuilding systemd with changed USE flag")
                try_command("emerge", "--verbose", "--changed-use", "--oneshot", "sys-apps/systemd")

        if self.USED_BTRFS:
            einfo("Installing btrfs-progs")
            try_command("emerge", "--verbose", "sys-fs/btrfs-progs")
            
        if self.USED_ZFS:
            einfo("Installing zfs")
            try_command("emerge", "--verbose", "sys-fs/zfs", "sys-fs/zfs-kmod")
            einfo("Enabling zfs services")
            if self.SYSTEMD:
                for svc in ["zfs.target", "zfs-import-cache", "zfs-mount", "zfs-import.target"]:
                    try_command("systemctl", "enable", svc)
            else:
                for svc in ["zfs-import", "zfs-mount"]:
                    try_command("rc-update", "add", svc, "boot")


        # Install kernel and initramfs
        getattr(self, 'before_install_kernel', lambda: None)()
        self.install_kernel()
        getattr(self, 'after_install_kernel', lambda: None)()

        self.generate_fstab()

        einfo("Installing gentoolkit")
        try_command("emerge", "--verbose", "app-portage/gentoolkit")

        # Configure Networking
        if self.SYSTEMD and self.SYSTEMD_NETWORKD:
            enable_service("systemd-networkd")
            enable_service("systemd-resolved")
            network_config = f"[Match]\nName={self.SYSTEMD_NETWORKD_INTERFACE_NAME}\n\n[Network]\n"
            if self.SYSTEMD_NETWORKD_DHCP:
                network_config += "DHCP=yes\n"
            else:
                addresses_str = "".join([f"Address={addr}\n" for addr in self.SYSTEMD_NETWORKD_ADDRESSES])
                network_config += addresses_str
                network_config += f"Gateway={self.SYSTEMD_NETWORKD_GATEWAY}\n"
            
            config_path = "/etc/systemd/network/20-wired.network"
            with open(config_path, "w") as f: f.write(network_config)
            
            try_command("chown", "root:systemd-network", config_path)
            os.chmod(config_path, 0o640)

        elif not self.SYSTEMD:
            einfo("Installing dhcpcd")
            try_command("emerge", "--verbose", "net-misc/dhcpcd")
            enable_service("dhcpcd")

        if self.ENABLE_SSHD:
            self.enable_sshd()

        # Install additional packages
        if self.ADDITIONAL_PACKAGES:
            einfo("Installing additional packages")
            try_command("emerge", "--verbose", "--autounmask-continue=y", *self.ADDITIONAL_PACKAGES)

        # Root password setup
        if ask("Do you want to assign a root password now?"):
            try_command("passwd", "root")
            einfo("Root password assigned")
        else:
            try_command("passwd", "-d", "root")
            ewarn("Root password cleared, set one as soon as possible!")

        # Enable testing repository
        if self.USE_PORTAGE_TESTING:
            einfo(f"Adding ~{self.GENTOO_ARCH} to ACCEPT_KEYWORDS")
            with open("/etc/portage/make.conf", "a") as f:
                f.write(f"ACCEPT_KEYWORDS=\"~{self.GENTOO_ARCH}\"\n")

        getattr(self, 'after_install', lambda: None)()

        einfo("Gentoo installation complete.")
        # ... (Final messages) ...

    # --- Top-Level Execution Functions ---
    
    def main_install(self, root_mountpoint: str, gentoo_install_repo_bind: str):
        """The main entry point for the installation process (outside chroot)."""
        gentoo_umount()
        self.install_stage3()

        if self.IS_EFI:
            mount_efivars()
        
        # Execute main_install_gentoo_in_chroot inside the chroot
        gentoo_chroot(root_mountpoint, gentoo_install_repo_bind, "__install_gentoo_in_chroot")


    def main_chroot(self, mountpoint: str, *args):
        """The entry point for manually chrooting into a mounted system."""
        if not subprocess.run(["mountpoint", "-q", "--", mountpoint], check=False).returncode == 0:
            die(f"'{mountpoint}' is not a mountpoint")

        gentoo_chroot(mountpoint, *args)


# --- Execution Block ---

if __name__ == "__main__":
    # The 'import protection' above handles the safety guard.
    
    print("Main installation logic converted to GentooInstaller class with Python protection guard.")
