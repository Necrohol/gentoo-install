 #!/bin/bash
# refind-helper.sh -
# https://efi.akeo.ie/downloads/efifs-1.11/x64/  amd64 efi drivers 
# https://efi.akeo.ie/downloads/efifs-1.11/aa64/ arm64 efi drivers
# https://efi.akeo.ie/downloads/efifs-1.11/riscv64/ 
 test -d /sys/firmware/efi/ && echo efi || echo bios 
 ##### probulation .... 
  # ? lsblk -o +PARTTYPE | grep C12A7328-F81F-11D2-BA4B-00A0C93EC93B
detect {$WIN_ESP} & Windows MSR # Do installs hear for dualboot Windows
detect Bootmgfw.efi Winload.efi: {$WIN_ESP}/EFI/Microsoft/Boot
### pray users dont have installed on same pysical drives 
### less hell to as windows and Gentoo will fight.. 
detect {$Linux_ESP} porbe {$Linux_ESP}/EFI/Gentoo/grubx64.efi etc. files 

|die 
echo "wont Install on AMD64  Gentoo Linux/Linux partion with Grub Found, not always a good idea." 
#  arm64? http://ftp.us.debian.org/debian/pool/main/r/refind/refind_0.13.2-1+b1_arm64.deb > |app-arch/deb2targz 


 
 cat /var/lib/portage/world | grep sys-boot/refind 
if not exitst ; USE="ext2 ext4 iso9690 btrfs doc hfs ntfs reiserfs secureboot " emerge -bavgk sys-boot/refind
if not exitst ; echo "sys-boot/refind ext2 ext4 iso9690 btrfs doc hfs ntfs reiserfs secureboot" >> /etc/portage/package.use/refind 

refind-install --usedefault {$WIN_ESP}/EFI/refind/ 
refind-install --shim /usr/share/shim-signed/shimx64.efi
refind-install --preloader /usr/share/preloader-signed/PreLoader.efi
 
 
  mkdir {$WIN_ESP}/EFI/refind/tools
 cp /usr/share/shim/mmx64.efi {$WIN_ESP}/EFI/refind/mmx64.efi
 cp /usr/share/efitools/efi/KeyTool.efi {$WIN_ESP}/EFI/refind/tools/KeyTool.efi
 
 if https://boot.netboot.xyz/ipxe/netboot.xyz-snp.efi 
 else arm64? https://boot.netboot.xyz/ipxe/netboot.xyz-arm64-snp.efi
 if amd64? wget -o {$WIN_ESP}/EFI/refind/tools/netboot.xyz-snp.efi 
  else arm64? wget -o {$WIN_ESP}/EFI/refind/tools/netboot.xyz-arm64-snp.efi 
  https://boot.ipxe.org/ipxe.efi
  https://boot.ipxe.org/snponly.efi
  
 arm64? https://boot.ipxe.org/arm64-efi/ipxe.efi snponly.efi
  # 
 amd64? https://www.memtest.org/download/v7.20/mt86plus_7.20.binaries.zip memtest32.efi memtest64.efi > {$WIN_ESP}/EFI/refind/tools/