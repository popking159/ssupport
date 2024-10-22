#!/bin/sh
##setup command=wget -q "--no-check-certificate" https://github.com/popking159/ssupport/raw/main/subssupport-install.sh -O - | /bin/sh

echo ''
echo '************************************************************'
echo "**                       STARTED                          **"
echo '************************************************************'
echo "**                  Uploaded by: MNASR                    **"
echo "************************************************************"
echo "**                 SubsSupport v1.7.0 r7                  **"
echo "************************************************************"
echo ' add subdl.com                                              '
echo ' add elsubtitle " still need some adjustment "              '
echo "************************************************************"
sleep 3s

if [ -d /usr/lib/enigma2/python/Plugins/Extensions/SubsSupport ]; then
echo "> removing package please wait..."
sleep 3s 
rm -rf /usr/lib/enigma2/python/Plugins/Extensions/SubsSupport > /dev/null 2>&1
fi

status='/var/lib/opkg/status'
package='enigma2-plugin-extensions-subssupport'

if grep -q $package $status; then
opkg remove $package > /dev/null 2>&1
fi

sleep 3s

echo "downloading SubsSupport..."
wget -O  /var/volatile/tmp/SubsSupport.tar.gz https://github.com/popking159/ssupport/raw/main/SubsSupport.tar.gz
echo "Installing SubsSupport..."
tar -xzf /var/volatile/tmp/SubsSupport.tar.gz -C /
rm -rf /var/volatile/tmp/SubsSupport.tar.gz
sync
echo "#########################################################"
echo "#########################################################"
echo "Installing dependency files"
opkg install python3-codecs python3-compression python3-core python3-difflib python3-json python3-requests python3-xmlrpc unrar python3-beautifulsoup4

SETTINGS="/etc/enigma2/settings"
echo "Adding new settings for subssupport..."
echo ""
echo ">>>>>>>>>     RESTARTING     <<<<<<<<<"
echo ""
init 4
sleep 3
sed -i "/subtitlesSupport/d" $SETTINGS
{
    echo "config.plugins.subtitlesSupport.encodingsGroup=Arabic"
	echo "config.plugins.subtitlesSupport.external.font.size=52"
	echo "config.plugins.subtitlesSupport.search.lang1=ar"
	echo "config.plugins.subtitlesSupport.search.lang2=ar"
	echo "config.plugins.subtitlesSupport.search.lang3=ar"
	echo "config.plugins.subtitlesSupport.search.opensbutitles_com.enabled=False"
	echo "config.plugins.subtitlesSupport.search.opensubtitles.enabled=False"
	echo "config.plugins.subtitlesSupport.search.podnapisi.enabled=False"
	echo "config.plugins.subtitlesSupport.search.prijevodionline.enabled=False"
 	echo "config.plugins.subtitlesSupport.search.subdl_com.enabled=False"
	echo "config.plugins.subtitlesSupport.search.titlovi.enabled=False"
	echo "config.plugins.subtitlesSupport.search.titulky_com.enabled=False"
	
} >> $SETTINGS

# ============================================================================================================
sleep 2
sync
init 3
echo "==================================================================="
echo "===                          FINISHED                           ==="
echo "                         Modded by MNASR                        ==="
echo "==================================================================="
sleep 2
exit 0
