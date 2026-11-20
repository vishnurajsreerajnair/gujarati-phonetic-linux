#!/bin/sh
# Install the Gujarati phonetic keyboard for the Linux apps of a ChromeOS
# Linux container (Debian), and make it the keyboard of those apps.
# Run from the repository: sh packaging/install.sh
set -eu

here=$(cd "$(dirname "$0")/.." && pwd)
prefix=/usr/lib/gujarati-phonetic-linux
# One IBus daemon at a fixed address for every app and display. By default
# IBus finds its daemon by display name, and ChromeOS runs several displays
# (X :0, X :1, Wayland), so apps would look for different daemons.
address="unix:path=/run/user/$(id -u)/ibus-gujarati-phonetic"
marker="# gujarati-phonetic-linux"

# IBus, its Python bindings and setxkbmap (IBus sets the key layout with it).
sudo apt-get install -y ibus ibus-gtk3 python3-gi gir1.2-ibus-1.0 x11-xkb-utils

# The engine and its IBus component.
sudo rm -rf "$prefix"
sudo mkdir -p "$prefix"
sudo cp -r "$here/src/gujarati_phonetic" "$prefix/"
sudo install -m 755 "$here/packaging/gujarati-phonetic-engine" "$prefix/"
sudo install -m 755 "$here/packaging/gujarati-phonetic-check" "$prefix/"
sudo ln -sf "$prefix/gujarati-phonetic-check" /usr/local/bin/gujarati-phonetic-check
sudo install -m 644 "$here/packaging/gujarati-phonetic.xml" /usr/share/ibus/component/

# Linux apps talk to IBus at the fixed address (and no longer to fcitx5).
mkdir -p "$HOME/.config/environment.d"
rm -f "$HOME/.config/environment.d/fcitx5.conf"
cat > "$HOME/.config/environment.d/ibus.conf" <<CONF
GTK_IM_MODULE=ibus
QT_IM_MODULE=ibus
XMODIFIERS=@im=ibus
SDL_IM_MODULE=ibus
IBUS_ADDRESS=$address
CONF

# The Terminal too, for gujarati-phonetic-check.
touch "$HOME/.bashrc"
sed -i "/$marker/d" "$HOME/.bashrc"
echo "export IBUS_ADDRESS=$address $marker" >> "$HOME/.bashrc"

# No start from ~/.sommelierrc: it runs once per display.
touch "$HOME/.sommelierrc"
sed -i '/fcitx5/d;/ibus-daemon/d;/ibus engine/d' "$HOME/.sommelierrc"

# Start IBus with the Gujarati keyboard when Linux starts.
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/gujarati-phonetic-ibus.service" <<UNIT
[Unit]
Description=IBus with the Gujarati phonetic keyboard

[Service]
Environment=IBUS_ADDRESS=$address
ExecStart=/usr/bin/ibus-daemon --replace --panel=disable --address=$address
ExecStartPost=/bin/sh -c "sleep 3; /usr/bin/ibus engine gujarati-phonetic"
Restart=on-failure

[Install]
WantedBy=default.target
UNIT
systemctl --user daemon-reload
systemctl --user enable gujarati-phonetic-ibus.service
gsettings set org.freedesktop.ibus.general preload-engines "['gujarati-phonetic']" 2>/dev/null || true

echo "Installed. Restart Linux (right-click the Terminal icon, Shut down Linux),"
echo "then open LibreOffice and type: kem Cho"
