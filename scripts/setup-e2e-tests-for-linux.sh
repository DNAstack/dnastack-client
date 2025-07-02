#!/bin/bash
set -ex

uname -a

# This is designed to be invoked on Debian GNU/Linux.

apt-get update
# Install dependencies, excluding problematic Python packages
DEBIAN_FRONTEND=noninteractive apt-get install -qqy \
  curl \
  unzip \
  libglib2.0-bin \
  libnss3 \
  libxcb1 \
  gcc \
  libffi-dev \
  npm

# Install chromium but mark the problematic Python packages as hold to prevent their installation
apt-mark hold python3-dbus python3-cupshelpers system-config-printer-common system-config-printer-udev system-config-printer || true
DEBIAN_FRONTEND=noninteractive apt-get install -qqy chromium || true

# NOTE: We install chromium to get its dependencies but we will use Chrome for Testing.
apt-get remove -y chromium || true

# Unhold the packages
apt-mark unhold python3-dbus python3-cupshelpers system-config-printer-common system-config-printer-udev system-config-printer || true

# Install uv if not already installed
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install Python packages using uv
uv pip install --system google-cloud-secret-manager \
               google-crc32c \
               pandas \
               python-dotenv

mkdir -p /root/.config/chromium/Crash\ Reports/pending/

npm i -qgy @puppeteer/browsers

#########################
# Install Chrome Driver #
#########################
export HELPER_TOOLS_PATH=/opt/helpers
npx @puppeteer/browsers install --path=${HELPER_TOOLS_PATH} chromedriver@stable
export CHROMEDRIVER_BIN_PATH=/usr/local/bin/chromedriver
echo '#!/bin/bash' > ${CHROMEDRIVER_BIN_PATH}
echo "\$(find ${HELPER_TOOLS_PATH}/chromedriver/* -name chromedriver) \$@" >> ${CHROMEDRIVER_BIN_PATH}
chmod a+x ${CHROMEDRIVER_BIN_PATH}

##############################
# Install Chrome for Testing #
##############################
npx @puppeteer/browsers install --path=${HELPER_TOOLS_PATH} chrome@stable
export CHROME_BIN_PATH=/usr/local/bin/chrome
echo '#!/bin/bash' > ${CHROME_BIN_PATH}
echo "\$(find ${HELPER_TOOLS_PATH}/chrome/* -name chrome) \$@" >> ${CHROME_BIN_PATH}
chmod a+x ${CHROME_BIN_PATH}

set +e
