#!/usr/bin/env python3
"""
Gentoo Repository Configuration Manager
Manages both official and unofficial repositories for gentoo-install
"""

import os
import sys
import json
import subprocess
import tarfile
from pathlib import Path
from datetime import datetime

class GentooRepoManager:
    def __init__(self):
        self.config_file = "gentoo-install-add-repos.conf"
        self.main_config = "gentoo.config"
        self.repos_data = {
            "official_repos": [],
            "unofficial_repos": [],
            "timestamp": None
        }
    
    def load_config(self):
        """Load existing configuration if it exists"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.repos_data = json.load(f)
                print(f"Loaded existing config from {self.config_file}")
            except Exception as e:
                print(f"Error loading config: {e}")
                print("Starting with empty configuration")
    
    def save_config(self):
        """Save configuration to file"""
        self.repos_data["timestamp"] = datetime.now().isoformat()
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.repos_data, f, indent=2)
            print(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def add_official_repos(self):
        """Add official repositories from comma-separated input"""
        print("\n=== Add Official Repositories ===")
        print("Enter repository names separated by commas (or press Enter to skip)")
        print("Example: guru,science,steam-overlay")
        
        current_repos = ", ".join(self.repos_data["official_repos"])
        if current_repos:
            print(f"Current repos: {current_repos}")
        
        user_input = input("Repositories: ").strip()
        if not user_input:
            return
        
        # Parse comma-separated list
        new_repos = [repo.strip() for repo in user_input.split(',') if repo.strip()]
        
        # Add to existing repos (avoid duplicates)
        for repo in new_repos:
            if repo not in self.repos_data["official_repos"]:
                self.repos_data["official_repos"].append(repo)
        
        print(f"Added repositories: {', '.join(new_repos)}")
    
    def add_unofficial_repo(self):
        """Add an unofficial repository with custom sync settings"""
        print("\n=== Add Unofficial Repository ===")
        print("Format: <name> <sync-type> <sync-uri>")
        print("Example: my-overlay git https://github.com/user/overlay.git")
        
        name = input("Repository name: ").strip()
        if not name:
            return
        
        sync_type = input("Sync type (git/rsync/etc): ").strip()
        if not sync_type:
            return
        
        sync_uri = input("Sync URI: ").strip()
        if not sync_uri:
            return
        
        repo_config = {
            "name": name,
            "sync_type": sync_type,
            "sync_uri": sync_uri
        }
        
        # Check for duplicates
        for existing in self.repos_data["unofficial_repos"]:
            if existing["name"] == name:
                print(f"Repository '{name}' already exists. Updating...")
                existing.update(repo_config)
                return
        
        self.repos_data["unofficial_repos"].append(repo_config)
        print(f"Added unofficial repository: {name}")
    
    def show_current_config(self):
        """Display current repository configuration"""
        print("\n=== Current Configuration ===")
        
        if self.repos_data["official_repos"]:
            print("Official repositories:")
            for repo in self.repos_data["official_repos"]:
                print(f"  - {repo}")
        else:
            print("No official repositories configured")
        
        if self.repos_data["unofficial_repos"]:
            print("\nUnofficial repositories:")
            for repo in self.repos_data["unofficial_repos"]:
                print(f"  - {repo['name']} ({repo['sync_type']}) -> {repo['sync_uri']}")
        else:
            print("No unofficial repositories configured")
        
        if self.repos_data.get("timestamp"):
            print(f"\nLast updated: {self.repos_data['timestamp']}")
    
    def generate_eselect_commands(self):
        """Generate eselect repository commands"""
        commands = []
        
        # Official repos - use eselect repository enable
        for repo in self.repos_data["official_repos"]:
            commands.append(f"eselect repository enable {repo}")
        
        # Unofficial repos - use eselect repository add
        for repo in self.repos_data["unofficial_repos"]:
            cmd = f"eselect repository add {repo['name']} {repo['sync_type']} {repo['sync_uri']}"
            commands.append(cmd)
        
        return commands
    
    def export_commands(self):
        """Export eselect commands to a shell script"""
        commands = self.generate_eselect_commands()
        if not commands:
            print("No repositories configured to export")
            return
        
        script_name = "setup-repositories.sh"
        try:
            with open(script_name, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write("# Generated by Gentoo Repository Manager\n")
                f.write("# Compatible with oddlama/gentoo-install for repeatable installs\n")
                f.write(f"# Created: {datetime.now().isoformat()}\n\n")
                
                f.write("set -euo pipefail\n\n")
                f.write("echo 'Setting up Gentoo repositories...'\n\n")
                
                # Add error handling for each command
                for cmd in commands:
                    f.write(f"echo 'Running: {cmd}'\n")
                    f.write(f"if ! {cmd}; then\n")
                    f.write(f"    echo 'Warning: Failed to execute: {cmd}'\n")
                    f.write(f"    echo 'Continuing with next command...'\n")
                    f.write(f"fi\n\n")
                
                f.write("echo 'Repository setup complete!'\n")
                f.write("echo 'Run: emerge --sync to synchronize all repositories'\n")
                f.write("echo 'Use: eselect repository list to verify setup'\n")
            
            os.chmod(script_name, 0o755)
            print(f"Commands exported to {script_name}")
            print("Script includes error handling for robust execution")
            
            # Also display commands
            print("\nGenerated commands:")
            for cmd in commands:
                print(f"  {cmd}")
                
        except Exception as e:
            print(f"Error exporting commands: {e}")
    
    def create_backup_archive(self):
        """Create a tarball with all configuration files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"gentoo-install-config_{timestamp}.tgz"
        
        # Generate setup script first if we have repos configured
        if self.repos_data["official_repos"] or self.repos_data["unofficial_repos"]:
            self.export_commands()
        
        files_to_backup = [
            self.config_file,
            self.main_config,
            "setup-repositories.sh",
            "gentoo.conf",  # Common gentoo-install config name
            "gentoo.conf.example"  # If present
        ]
        
        files_added = 0
        try:
            with tarfile.open(archive_name, "w:gz") as tar:
                for file_path in files_to_backup:
                    if os.path.exists(file_path):
                        tar.add(file_path)
                        print(f"Added {file_path} to archive")
                        files_added += 1
                    else:
                        print(f"Skipped {file_path} (not found)")
            
            if files_added > 0:
                print(f"\nBackup archive created: {archive_name}")
                print(f"Contains {files_added} files for repeatable gentoo installations")
                return archive_name
            else:
                print("No files found to backup")
                os.remove(archive_name)
                return None
        except Exception as e:
            print(f"Error creating archive: {e}")
            return None
    
    def interactive_menu(self):
        """Main interactive menu"""
        self.load_config()
        
        while True:
            print("\n" + "="*50)
            print("Gentoo Repository Configuration Manager")
            print("="*50)
            print("1. Add official repositories (comma-separated)")
            print("2. Add unofficial repository")
            print("3. Show current configuration")
            print("4. Export eselect commands")
            print("5. Create backup archive (includes setup-repositories.sh)")
            print("6. Integration with gentoo-install")
            print("6. Integration with gentoo-install")
            print("7. Save and exit")
            print("8. Exit without saving")
            
            choice = input("\nSelect option (1-8): ").strip()
            
            if choice == "1":
                self.add_official_repos()
            elif choice == "2":
                self.add_unofficial_repo()
            elif choice == "3":
                self.show_current_config()
            elif choice == "4":
                self.export_commands()
            elif choice == "5":
                if self.save_config():
                    self.create_backup_archive()
            elif choice == "6":
                self.gentoo_install_integration()
            elif choice == "7":
                if self.save_config():
                    print("Configuration saved. Goodbye!")
                break
            elif choice == "8":
                print("Exiting without saving...")
                break
            else:
                print("Invalid option. Please try again.")
    
    def gentoo_install_integration(self):
        """Integration helpers for gentoo-install workflow"""
        print("\n=== gentoo-install Integration ===")
        print("This helps integrate repository setup with oddlama/gentoo-install")
        print()
        print("1. Generate post-install script")
        print("2. Show integration instructions")
        print("3. Create complete install package")
        print("4. Back to main menu")
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == "1":
            self.generate_post_install_script()
        elif choice == "2":
            self.show_integration_instructions()
        elif choice == "3":
            self.create_install_package()
        elif choice == "4":
            return
        else:
            print("Invalid option")
    
    def generate_post_install_script(self):
        """Generate a post-install script for gentoo-install"""
        if not (self.repos_data["official_repos"] or self.repos_data["unofficial_repos"]):
            print("No repositories configured. Add some repositories first.")
            return
        
        script_name = "post-install-repos.sh"
        commands = self.generate_eselect_commands()
        
        try:
            with open(script_name, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write("# Post-install repository setup for gentoo-install\n")
                f.write("# Run this after gentoo-install completes\n")
                f.write(f"# Generated: {datetime.now().isoformat()}\n\n")
                
                f.write("set -euo pipefail\n\n")
                f.write("echo '=== Post-Install Repository Setup ==='\n\n")
                
                # Check if we're in a chroot or live system
                f.write("if [ -f /etc/gentoo-release ]; then\n")
                f.write("    echo 'Setting up repositories in installed system...'\n")
                f.write("else\n")
                f.write("    echo 'Error: This should be run in the installed Gentoo system'\n")
                f.write("    exit 1\n")
                f.write("fi\n\n")
                
                for cmd in commands:
                    f.write(f"echo 'Executing: {cmd}'\n")
                    f.write(f"{cmd} || echo 'Warning: {cmd} failed'\n")
                
                f.write("\necho 'Syncing repositories...'\n")
                f.write("emerge --sync || echo 'Warning: sync failed, try manually later'\n")
                f.write("echo 'Repository setup complete!'\n")
            
            os.chmod(script_name, 0o755)
            print(f"Post-install script created: {script_name}")
            
        except Exception as e:
            print(f"Error creating post-install script: {e}")
    
    def show_integration_instructions(self):
        """Show instructions for integrating with gentoo-install"""
        print("\n=== Integration Instructions ===")
        print()
        print("To use this with gentoo-install:")
        print()
        print("1. Configure gentoo-install normally:")
        print("   cd gentoo-install")
        print("   ./configure")
        print("   # Save as gentoo.conf")
        print()
        print("2. Run this repository manager:")
        print("   python3 gentoo-repo-manager.py")
        print("   # Configure your repositories")
        print("   # Create backup archive (option 5)")
        print()
        print("3. Extract your config archive after gentoo-install:")
        print("   tar -xzf gentoo-install-config_TIMESTAMP.tgz")
        print("   chmod +x setup-repositories.sh")
        print("   ./setup-repositories.sh")
        print()
        print("4. Or use the post-install script approach:")
        print("   # Copy post-install-repos.sh to your new system")
        print("   # Run it after first boot")
        print()
        print("This enables repeatable Gentoo installs with custom repositories!")
    
    def create_install_package(self):
        """Create a complete package for gentoo-install integration"""
        print("\n=== Creating Complete Install Package ===")
        
        # Save current config
        if not self.save_config():
            print("Failed to save configuration")
            return
        
        # Generate all scripts
        self.export_commands()
        self.generate_post_install_script()
        
        # Create comprehensive archive
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        package_name = f"gentoo-complete-install_{timestamp}.tgz"
        
        files_to_package = [
            self.config_file,
            "gentoo.conf",
            "gentoo.conf.example", 
            "setup-repositories.sh",
            "post-install-repos.sh",
            "README-repos.txt"
        ]
        
        # Create README
        try:
            with open("README-repos.txt", 'w') as f:
                f.write("Gentoo Repository Setup Package\n")
                f.write("=" * 35 + "\n\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n\n")
                f.write("Files included:\n")
                f.write("- gentoo-install-add-repos.conf: Repository configuration\n")
                f.write("- setup-repositories.sh: Repository setup script\n")
                f.write("- post-install-repos.sh: Post-install script for new system\n")
                f.write("- gentoo.conf: gentoo-install configuration (if present)\n\n")
                f.write("Usage:\n")
                f.write("1. Run gentoo-install with gentoo.conf\n")
                f.write("2. After installation, run setup-repositories.sh\n")
                f.write("3. Or copy post-install-repos.sh to new system and run there\n\n")
                f.write("Configured repositories:\n")
                if self.repos_data["official_repos"]:
                    f.write("Official: " + ", ".join(self.repos_data["official_repos"]) + "\n")
                for repo in self.repos_data["unofficial_repos"]:
                    f.write(f"Unofficial: {repo['name']} ({repo['sync_type']}) -> {repo['sync_uri']}\n")
        except Exception as e:
            print(f"Warning: Could not create README: {e}")
        
        # Create package
        files_added = 0
        try:
            with tarfile.open(package_name, "w:gz") as tar:
                for file_path in files_to_package:
                    if os.path.exists(file_path):
                        tar.add(file_path)
                        print(f"Added {file_path}")
                        files_added += 1
            
            if files_added > 0:
                print(f"\nComplete install package created: {package_name}")
                print("This package contains everything for repeatable Gentoo installs!")
            else:
                print("No files to package")
                
        except Exception as e:
            print(f"Error creating package: {e}")

def main():
    """Main entry point"""
    manager = GentooRepoManager()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--export":
            manager.load_config()
            manager.export_commands()
        elif sys.argv[1] == "--backup":
            manager.load_config()
            manager.create_backup_archive()
        elif sys.argv[1] == "--show":
            manager.load_config()
            manager.show_current_config()
        else:
            print("Usage:")
            print("  python3 gentoo-repo-manager.py           # Interactive mode")
            print("  python3 gentoo-repo-manager.py --export  # Export commands")
            print("  python3 gentoo-repo-manager.py --backup  # Create backup")
            print("  python3 gentoo-repo-manager.py --show    # Show config")
    else:
        manager.interactive_menu()

if __name__ == "__main__":
    main()
