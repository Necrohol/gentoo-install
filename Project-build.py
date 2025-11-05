#!/usr/bin/env python3
"""
gentoo-install Project Builder + Cross-Build Hints
---------------------------------------------------
Creates a structured working directory for gentoo-install projects,
saves configuration files, repo definitions, and reference links.

Supports Laptop, Desktop, and Embedded systems (e.g., RPi, RISC-V).

If run on a non-Gentoo host, automatically includes Proot/QEMU
cross-build suggestions for easier setup.

Author: Necrohol Community Contributor
"""

import os
import datetime
import argparse
import tarfile
import subprocess
from pathlib import Path
from pyshortcuts import make_shortcut


class GentooInstallProject:
    def __init__(self, name, system_type, base_dir="projects"):
        self.name = name
        self.system_type = system_type.lower()
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.project_dir = Path(base_dir) / f"{self.name}-{self.system_type}-{self.timestamp}"
        self.config_file = "gentoo.conf"
        self.repo_file = "gentoo-install-add-repos.conf"
        self.hints_file = "hints.toml"
        self.references_file = "references.toml"
        self.project_log = "Project-log.md"

    # --- Directory creation and base files ---
    def create_structure(self):
        print(f"[+] Creating project directory: {self.project_dir}")
        self.project_dir.mkdir(parents=True, exist_ok=True)

        for sub in ["repos", "overlay", "stage3", "logs", "references"]:
            (self.project_dir / sub).mkdir(exist_ok=True)
            print(f"  ├── Created {sub}/")

        (self.project_dir / self.config_file).write_text(
            f"# gentoo.conf generated {self.timestamp}\n# Add your installation options here.\n"
        )
        (self.project_dir / self.repo_file).write_text(
            f"# gentoo-install-add-repos.conf generated {self.timestamp}\n# Example:\n# [repos]\n# guru = /var/db/repos/guru\n"
        )
        (self.project_dir / self.hints_file).write_text(
            "# hints.toml\n# Example: suggest=app-misc/openrgb or app-portage/carnage for overlay lookup\n"
        )
        (self.project_dir / self.project_log).write_text(
            f"# Project Log for {self.name}-{self.system_type}\n\nCreated: {self.timestamp}\n\n"
            "## Tasks\n- [ ] Configure gentoo.conf\n- [ ] Add custom overlays\n"
            "- [ ] Run gentoo-install (TUI)\n\n## Notes\n"
        )

        self._add_references()
        self._append_host_environment_hints()

    # --- Add references to useful wiki/gentoo resources ---
    def _add_references(self):
        (self.project_dir / self.references_file).write_text(
            """# references.toml
# Useful links for this project

[general]
gentoo_wiki = "https://wiki.gentoo.org/"
gentoo_install = "https://github.com/Necrohol/gentoo-install"
carnage_repo = "https://github.com/dsafxP/carnage"
openrgb = "https://wiki.gentoo.org/wiki/OpenRGB"

[embedded]
rpi_overlay = "https://github.com/GenPi64/genpi64-overlay"
rpi_tools_conf = "https://github.com/GenPi64/genpi-tools/blob/master/genpi-tools.conf"
riscv_overlay = "https://github.com/gentoo/riscv"

[cross_build]
proot = "https://wiki.gentoo.org/wiki/Project:Prefix/Portability"
crossdev = "https://wiki.gentoo.org/wiki/Crossdev"
qemu_user = "https://wiki.gentoo.org/wiki/QEMU/User_mode_emulation"
"""
        )

    # --- Detect if we're running on Gentoo or not ---
    def _is_gentoo_host(self):
        try:
            with open("/etc/os-release") as f:
                data = f.read().lower()
                return "gentoo" in data
        except FileNotFoundError:
            return False

    # --- Append host hints for cross-builds ---
    def _append_host_environment_hints(self):
        gentoo_host = self._is_gentoo_host()
        log_path = self.project_dir / self.project_log
        with open(log_path, "a") as f:
            if gentoo_host:
                f.write("\n## Host Detected\nGentoo Linux host detected. Native emerge and chroot usable.\n")
            else:
                f.write("\n## Host Detected\nNon-Gentoo host detected.\n")
                f.write("Consider using `proot` or `qemu-user` to run Gentoo stage3 environments.\n\n")
                f.write("### Suggested Tools\n")
                f.write("- app-emulation/qemu-user-static\n")
                f.write("- proot (for unprivileged chroot)\n")
                f.write("- binfmt_misc support for ARM/RISC-V images\n\n")
                f.write("### Example Setup\n")
                f.write("```\n# Example: run a Gentoo ARM64 stage3 in Proot\n"
                        "proot -R ./stage3-arm64 /bin/bash\n```\n\n")
                f.write("Refer to `references.toml` → [cross_build] for official guides.\n")

    # --- Optional clone of gentoo-install repo ---
    def clone_gentoo_install(self):
        print("[+] Cloning gentoo-install repository...")
        subprocess.run(
            ["git", "clone", "--depth=1", "https://github.com/Necrohol/gentoo-install.git",
             str(self.project_dir / "gentoo-install")],
            check=False
        )

    # --- Optional Carnage install (overlay manager) ---
    def install_carnage(self):
        print("[+] Installing app-portage/carnage from guru overlay...")
        subprocess.run(["emerge", "--ask", "app-portage/carnage"], check=False)

    # --- Make reference shortcuts for GUI users ---
    def make_reference_shortcuts(self):
        print("[+] Creating reference shortcuts (inside project/references)...")
        ref_dir = self.project_dir / "references"
        shortcuts = {
            "Gentoo Wiki": "https://wiki.gentoo.org/",
            "GenPi64 Overlay": "https://github.com/GenPi64/genpi64-overlay",
            "Gentoo RISC-V": "https://github.com/gentoo/riscv",
            "Proot Info": "https://wiki.gentoo.org/wiki/Project:Prefix/Portability"
        }
        for name, url in shortcuts.items():
            make_shortcut(script=url, name=name, folder=str(ref_dir))

    # --- Archive project for sharing ---
    def archive_project(self, fmt="xz"):
        print(f"[+] Creating compressed archive ({fmt})...")
        archive_name = f"{self.project_dir}.tar.{fmt}"
        mode = f"w:{fmt}"
        with tarfile.open(archive_name, mode) as tar:
            tar.add(self.project_dir, arcname=self.project_dir.name)
        print(f"  └── Created archive: {archive_name}")

    # --- Print summary ---
    def summarize(self):
        print("\n[Project Summary]")
        print(f" Name:       {self.name}")
        print(f" Type:       {self.system_type}")
        print(f" Directory:  {self.project_dir}")
        print(f" Timestamp:  {self.timestamp}")
        print(f" Configs:    {self.config_file}, {self.repo_file}")
        print("-----------------------------------------------------------")
        print("For cross-builds, review Project-log.md → 'Host Detected' section.\n")


def main():
    parser = argparse.ArgumentParser(description="Gentoo-install Project Builder & Organizer (with cross-build hints)")
    parser.add_argument("name", help="Project name (e.g. rpi5, tower, thinkpad)")
    parser.add_argument("type", choices=["laptop", "desktop", "embedded"], help="System type")
    parser.add_argument("--clone", action="store_true", help="Clone gentoo-install repo into project")
    parser.add_argument("--carnage", action="store_true", help="Install Carnage overlay tool")
    parser.add_argument("--archive", action="store_true", help="Create tar.xz archive after setup")
    args = parser.parse_args()

    proj = GentooInstallProject(args.name, args.type)
    proj.create_structure()

    if args.clone:
        proj.clone_gentoo_install()
    if args.carnage:
        proj.install_carnage()

    proj.make_reference_shortcuts()

    if args.archive:
        proj.archive_project(fmt="xz")

    proj.summarize()


if __name__ == "__main__":
    main()