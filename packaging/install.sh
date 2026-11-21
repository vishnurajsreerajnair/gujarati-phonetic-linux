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
socket="/run/user/$(id -u)/ibus-gujarati-phonetic"
address="unix:path=$socket"
marker="# gujarati-phonetic-linux"

# IBus, its Python bindings, setxkbmap (IBus sets the key layout with it) and
# python3-xlib (key presses for ONLYOFFICE, which drops the text of IBus).
sudo apt-get install -y ibus ibus-gtk3 python3-gi gir1.2-ibus-1.0 x11-xkb-utils \
    python3-xlib

# The engine and its IBus component.
sudo rm -rf "$prefix"
sudo mkdir -p "$prefix"
sudo cp -r "$here/src/gujarati_phonetic" "$prefix/"
sudo install -m 755 "$here/packaging/gujarati-phonetic-engine" "$prefix/"
sudo install -m 755 "$here/packaging/gujarati-phonetic-check" "$prefix/"
sudo install -m 755 "$here/packaging/gujarati-phonetic-toggle" "$prefix/"
sudo ln -sf "$prefix/gujarati-phonetic-check" /usr/local/bin/gujarati-phonetic-check
sudo ln -sf "$prefix/gujarati-phonetic-toggle" /usr/local/bin/gujarati-phonetic-toggle
sudo install -m 644 "$here/packaging/gujarati-phonetic.xml" /usr/share/ibus/component/

# The shelf toggle: an app that switches between Gujarati and English and shows
# the language in a notification. Pin it to the shelf from the launcher.
sudo install -m 644 "$here/packaging/gujarati-phonetic-toggle.desktop" \
    /usr/share/applications/
sudo install -D -m 644 "$here/packaging/gujarati-phonetic.svg" \
    /usr/share/icons/hicolor/scalable/apps/gujarati-phonetic.svg

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
# A socket left by a stopped daemon blocks the address: remove it first.
ExecStartPre=/bin/rm -f $socket
ExecStart=/usr/bin/ibus-daemon --replace --panel=disable --address=$address
# Select the keyboard; "-" keeps the daemon running if this step fails.
ExecStartPost=-/bin/sh -c "sleep 3; /usr/bin/ibus engine gujarati-phonetic"
Restart=on-failure

[Install]
WantedBy=default.target
UNIT
systemctl --user daemon-reload
systemctl --user enable gujarati-phonetic-ibus.service
gsettings set org.freedesktop.ibus.general preload-engines "['gujarati-phonetic']" 2>/dev/null || true

echo "Installed. Restart Linux (right-click the Terminal icon, Shut down Linux),"
echo "then open LibreOffice and type: kem Cho. Pin the app 'ગુજરાતી / English'"
echo "to the shelf: it switches between Gujarati and English."
