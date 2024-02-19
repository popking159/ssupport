#!/bin/sh
# Command: wget https://raw.githubusercontent.com/popking159/ssupport/main/installer.sh -O - | /bin/sh #
IPKFILE="subssupport_1.7.0_cortexa15hf-neon-vfpv4.ipk"
MAINURL="https://raw.githubusercontent.com/popking159/"
PKGDIR='ssupport/main/'
echo "Downloading subssupport..."
wget -T 2 $MAINURL$PKGDIR$IPKFILE -P "/tmp/"
IPKTMPFILE="/tmp/"$IPKFILE
echo "Installing subssupport..."
opkg install --force-reinstall $IPKTMPFILE
exit 0
