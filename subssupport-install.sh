#!/bin/sh
##setup command=wget -q "--no-check-certificate" https://github.com/popking159/ssupport/raw/main/installer.sh -O - | /bin/sh

rm -r /usr/lib/enigma2/python/Plugins/Extensions/SubsSupport
echo "downloading SubsSupport..."
wget -O  /var/volatile/tmp/SubsSupport.tar.gz https://github.com/popking159/ssupport/raw/main/SubsSupport.tar.gz
echo "Installing SubsSupport..."
tar -xzf /var/volatile/tmp/SubsSupport.tar.gz -C /
rm -rf /var/volatile/tmp/SubsSupport.tar.gz
sync
echo "#########################################################"
echo "#########################################################"
echo "Installing dependency files"
opkg install perl-module-io-zlib python3-codecs python3-compression python3-core python3-difflib python3-json python3-requests python3-xmlrpc unrar

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
	echo "config.plugins.subtitlesSupport.external.font.size=50"
	echo "config.plugins.subtitlesSupport.search.archive_org.enabled=False"
	echo "config.plugins.subtitlesSupport.search.edna_cz.enabled=False"
	echo "config.plugins.subtitlesSupport.search.itasa.enabled=False"
	echo "config.plugins.subtitlesSupport.search.indexsubtitle.enabled=False"
	echo "config.plugins.subtitlesSupport.search.itasa.enabled=False"
	echo "config.plugins.subtitlesSupport.search.lang1=ar"
	echo "config.plugins.subtitlesSupport.search.lang2=ar"
	echo "config.plugins.subtitlesSupport.search.lang3=ar"
	echo "config.plugins.subtitlesSupport.search.moviesubtitles.enabled=False"
	echo "config.plugins.subtitlesSupport.search.moviesubtitles2.enabled=False"
	echo "config.plugins.subtitlesSupport.search.mysubs.enabled=False"
	echo "config.plugins.subtitlesSupport.search.opensubtitles.enabled=False"
	echo "config.plugins.subtitlesSupport.search.opensubtitles_com.enabled=False"
	echo "config.plugins.subtitlesSupport.search.podnapisi.enabled=False"
	echo "config.plugins.subtitlesSupport.search.prijevodionline.enabled=False"
	echo "config.plugins.subtitlesSupport.search.serialzone_cz.enabled=False"
	echo "config.plugins.subtitlesSupport.search.subdl_com.enabled=False"
	echo "config.plugins.subtitlesSupport.search.subscene.enabled=False"
	echo "config.plugins.subtitlesSupport.search.subtitlecat_com.enabled=False"
	echo "config.plugins.subtitlesSupport.search.subtitles_gr.enabled=False"
	echo "config.plugins.subtitlesSupport.search.subtitlist.enabled=False"
	echo "config.plugins.subtitlesSupport.search.syt-subs_com.enabled=False"
	echo "config.plugins.subtitlesSupport.search.titlovi.enabled=False"
	echo "config.plugins.subtitlesSupport.search.titlovi_com.enabled=False"
	echo "config.plugins.subtitlesSupport.search.titulky_com.enabled=False"
	
} >> $SETTINGS

# ============================================================================================================
sleep 2
sync
init 3
echo "==================================================================="
echo "===                          FINISHED                           ==="
echo "==================================================================="
exit 0