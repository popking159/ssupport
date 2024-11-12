#!/bin/sh
##setup command=wget -q "--no-check-certificate" https://github.com/popking159/ssupport/raw/main/subssupportpy2-install.sh -O - | /bin/sh

echo ''
echo '************************************************************'
echo "**                       STARTED                          **"
echo '************************************************************'
echo "**                  Uploaded by: MNASR                    **"
echo "************************************************************"
echo "**               SubsSupport v1.7.0 r1 py2                **"
echo "************************************************************"
echo "** support py2                                            **"
echo "************************************************************"
if [ -d /usr/lib/enigma2/python/Plugins/Extensions/SubsSupport ]; then
echo "> removing package please wait..."
rm -rf /usr/lib/enigma2/python/Plugins/Extensions/SubsSupport > /dev/null 2>&1
fi

status='/var/lib/opkg/status'
package='enigma2-plugin-extensions-subssupport'

if grep -q $package $status; then
opkg remove $package > /dev/null 2>&1
fi



echo "downloading SubsSupport..."
wget -O  /var/volatile/tmp/SubsSupportpy2.tar.gz https://github.com/popking159/ssupport/raw/main/SubsSupportpy2.tar.gz
echo "Installing SubsSupport..."
tar -xzf /var/volatile/tmp/SubsSupportpy2.tar.gz -C /
rm -rf /var/volatile/tmp/SubsSupportpy2.tar.gz > /dev/null 2>&1
echo "#########################################################"
echo "#########################################################"
echo "Installing dependency files"
opkg install python-codecs python-compression python-core python-difflib python-json python-requests python-xmlrpc unrar python-beautifulsoup4 python-futures python-six


# ============================================================================================================

sync
echo "==================================================================="
echo "===                          FINISHED                           ==="
echo "===                      Modded by MNASR                        ==="
echo "==================================================================="

echo "==================================================================="
echo "===                        Restarting                           ==="
echo "==================================================================="

killall -9 enigma2

exit 0
