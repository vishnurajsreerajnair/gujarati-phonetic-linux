#!/bin/sh
# Remove the Gujarati phonetic keyboard and its start-up settings.
# Run from the repository: sh packaging/uninstall.sh
set -eu

systemctl --user disable --now gujarati-phonetic-ibus.service 2>/dev/null || true
rm -f "$HOME/.config/systemd/user/gujarati-phonetic-ibus.service"
systemctl --user daemon-reload
sudo rm -rf /usr/lib/gujarati-phonetic-linux
sudo rm -f /usr/local/bin/gujarati-phonetic-check
sudo rm -f /usr/share/ibus/component/gujarati-phonetic.xml
rm -f "$HOME/.config/environment.d/ibus.conf"
if [ -f "$HOME/.bashrc" ]; then
    sed -i '/# gujarati-phonetic-linux/d' "$HOME/.bashrc"
fi
if [ -f "$HOME/.sommelierrc" ]; then
    sed -i '/ibus-daemon/d;/ibus engine/d' "$HOME/.sommelierrc"
fi
echo "Removed. Restart Linux to finish."
