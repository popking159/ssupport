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
sleep 3

if [ -d /usr/lib/enigma2/python/Plugins/Extensions/SubsSupport ]; then
echo "> removing package please wait..."
sleep 2
rm -rf /usr/lib/enigma2/python/Plugins/Extensions/SubsSupport > /dev/null 2>&1
fi

status='/var/lib/opkg/status'
package='enigma2-plugin-extensions-subssupport'

if grep -q $package $status; then
opkg remove $package > /dev/null 2>&1
fi

sleep 2

echo "downloading SubsSupport..."
wget -O  /var/volatile/tmp/SubsSupportpy2.tar.gz https://github.com/popking159/ssupport/raw/main/SubsSupportpy2.tar.gz
echo "Installing SubsSupport..."
tar -xzf /var/volatile/tmp/SubsSupportpy2.tar.gz -C /
rm -rf /var/volatile/tmp/SubsSupportpy2.tar.gz > /dev/null 2>&1

sleep 2
# cd /tmp 
# if [ -d /usr/lib/enigma2/python/Plugins/SystemPlugins/NewVirtualKeyBoard ]; then
# echo "adjust SubsSupport with NewVirtualKeyBoard..."
# wget "https://github.com/popking159/ssupport/raw/main/subtitles.py"
# rm -f /usr/lib/enigma2/python/Plugins/Extensions/SubsSupport/subtitles.py > /dev/null 2>&1
# mv subtitles.py /usr/lib/enigma2/python/Plugins/Extensions/SubsSupport  > /dev/null 2>&1
# fi
# cd ..
# sync
echo "#########################################################"
echo "#########################################################"
echo "Installing dependency files"
opkg install python-codecs python-compression python-core python-difflib python-json python-requests python-xmlrpc unrar python-beautifulsoup4 python-futures python-six


# ============================================================================================================
sleep 
sync
echo "==================================================================="
echo "===                          FINISHED                           ==="
echo "===                      Modded by MNASR                        ==="
echo "==================================================================="
sleep 2
echo "==================================================================="
echo "===                        Restarting                           ==="
echo "==================================================================="

killall -9 enigma2
exit 0
