#!/bin/sh

# Define color codes
RED="\e[31m"
GREEN="\e[32m"
BLUE="\e[34m"
YELLOW="\e[33m"
RESET="\e[0m"

# Welcome message with decoration
clear
echo -e "${GREEN}==============================================================${RESET}"
echo -e "${GREEN}===                Welcome to Subtitle Support             ===${RESET}"
echo -e "${GREEN}===                     Script by MNASR                    ===${RESET}"
echo -e "${GREEN}==============================================================${RESET}"
sleep 3  # Pause for 3 seconds

# Check if all arguments are provided
if [ "$#" -ne 5 ]; then
    echo -e "${RED}Usage: $0 <OpenSubtitles_API_KEY> <OpenSubtitles_username> <OpenSubtitles_password> <Subdl_API_KEY> <downloadPath>${RESET}"
    exit 1
fi

# Assign arguments to variables
OpenSubtitles_API_KEY="$1"
OpenSubtitles_username="$2"
OpenSubtitles_password="$3"
Subdl_API_KEY="$4"
downloadPath="$5"

SETTINGS="/etc/enigma2/settings"
BACKUP="$SETTINGS.bak"

echo -e "${YELLOW}Backing up existing settings to $BACKUP...${RESET}"
cp $SETTINGS $BACKUP

echo -e "${YELLOW}Adding subtitles support credentials and default settings...${RESET}"
echo ""

# Stop Enigma2
init 4
sleep 2

# Remove existing subtitle support settings
sed -i "/subtitlesSupport/d" $SETTINGS

# Append new settings
{
    # User-input credentials
    echo "config.plugins.subtitlesSupport.search.opensubtitles_com.OpenSubtitles_API_KEY=$OpenSubtitles_API_KEY"
    echo "config.plugins.subtitlesSupport.search.opensubtitles_com.OpenSubtitles_username=$OpenSubtitles_username"
    echo "config.plugins.subtitlesSupport.search.opensubtitles_com.OpenSubtitles_password=$OpenSubtitles_password"
    echo "config.plugins.subtitlesSupport.search.subdl_com.Subdl_API_KEY=$Subdl_API_KEY"
    echo "config.plugins.subtitlesSupport.search.downloadPath=$downloadPath"

    # Default subtitle settings
    echo "config.plugins.subtitlesSupport.external.background.alpha=00"
    echo "config.plugins.subtitlesSupport.external.background.enabled=True"
    echo "config.plugins.subtitlesSupport.external.background.height=3"
    echo "config.plugins.subtitlesSupport.external.background.type=fixed"
    echo "config.plugins.subtitlesSupport.external.shadow.enabled=False"
    echo "config.plugins.subtitlesSupport.search.archive_org.enabled=False"
    echo "config.plugins.subtitlesSupport.search.elsubtitle.enabled=False"
    echo "config.plugins.subtitlesSupport.search.foursub.enabled=False"
    echo "config.plugins.subtitlesSupport.search.mysubs.enabled=False"
    echo "config.plugins.subtitlesSupport.search.novalermora.enabled=False"
    echo "config.plugins.subtitlesSupport.search.opensubtitles.enabled=False"
    echo "config.plugins.subtitlesSupport.search.opensubtitlesmora.enabled=False"
    echo "config.plugins.subtitlesSupport.search.podnapisi.enabled=False"
    echo "config.plugins.subtitlesSupport.search.prijevodionline.enabled=False"
    echo "config.plugins.subtitlesSupport.search.sub_scene_com.enabled=False"
    echo "config.plugins.subtitlesSupport.search.subscenebest.enabled=False"
    echo "config.plugins.subtitlesSupport.search.subsource.enabled=False"
    echo "config.plugins.subtitlesSupport.search.subtitlecat.enabled=False"
    echo "config.plugins.subtitlesSupport.search.titlovi.enabled=False"
    echo "config.plugins.subtitlesSupport.search.titulky_com.enabled=False"
    echo "config.plugins.subtitlesSupport.search.ytssubs.enabled=False"
} >> $SETTINGS

# Restart Enigma2
echo -e "${YELLOW}>>>>>>>>>     RESTARTING     <<<<<<<<<${RESET}"
sleep 2
sync
init 3

echo -e "${GREEN}===================================================================${RESET}"
echo -e "${GREEN}===                          FINISHED                           ===${RESET}"
echo -e "${GREEN}===                      Script by MNASR                        ===${RESET}"
echo -e "${GREEN}===================================================================${RESET}"
sleep 2
exit 0
