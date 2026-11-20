#!/bin/sh
# Install the Gujarati phonetic keyboard for the Linux apps of a ChromeOS
# Linux container (Debian), and make it the keyboard of those apps.
# Run from the repository: sh packaging/install.sh
set -eu

here=$(cd "$(dirname "$0")/.." && pwd)
prefix=/usr/lib/gujarati-phonetic-linux

# IBus and its Python bindings.
sudo apt-get install -y ibus ibus-gtk3 python3-gi gir1.2-ibus-1.0

# The engine and its IBus component.
sudo rm -rf "$prefix"
sudo mkdir -p "$prefix"
sudo cp -r "$here/src/gujarati_phonetic" "$prefix/"
sudo install -m 755 "$here/packaging/gujarati-phonetic-engine" "$prefix/"
sudo install -m 755 "$here/packaging/gujarati-phonetic-check" "$prefix/"
sudo ln -sf "$prefix/gujarati-phonetic-check" /usr/local/bin/gujarati-phonetic-check
sudo install -m 644 "$here/packaging/gujarati-phonetic.xml" /usr/share/ibus/component/

# Linux apps talk to IBus (and no longer to fcitx5).
mkdir -p "$HOME/.config/environment.d"
rm -f "$HOME/.config/environment.d/fcitx5.conf"
cat > "$HOME/.config/environment.d/ibus.conf" <<'CONF'
GTK_IM_MODULE=ibus
QT_IM_MODULE=ibus
XMODIFIERS=@im=ibus
SDL_IM_MODULE=ibus
CONF

# Start IBus with the Gujarati keyboard when Linux starts.
touch "$HOME/.sommelierrc"
sed -i '/fcitx5/d;/ibus-daemon/d;/ibus engine/d' "$HOME/.sommelierrc"
cat >> "$HOME/.sommelierrc" <<'RC'
ibus-daemon --daemonize --replace --xim --panel=disable
(sleep 3; ibus engine gujarati-phonetic) &
RC
gsettings set org.freedesktop.ibus.general preload-engines "['gujarati-phonetic']" 2>/dev/null || true

echo "Installed. Restart Linux (right-click the Terminal icon, Shut down Linux),"
echo "then open LibreOffice and type: kem Cho"
