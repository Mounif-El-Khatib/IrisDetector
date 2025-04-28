# Iris Detector

### Installation

Create a virtual environment by running `python3 -m venv venv`.

Activate the virtual environment by running `source venv/bin/activate`.

Start by installing the required python dependencies by running `pip install -r requirements.txt`.

At this point, buildozer should be installed; Buildozer is the tool that packages Python code into an Android apk. You can check its documentation [here](https://buildozer.readthedocs.io/en/latest/installation.html).

The `buildozer.spec` file already exists inside the project. It contains configurations for the app, where you specify things like which Android API to use, what dependencies and permissions are required...

### Building the app

In order to package the Python code into an apk, simply run `buildozer android debug`. 

When running for the first time, it will download an Android SDK, NDK, and other dependencies that are required. This may take a long time depending on bandwidth and your computer speed.

After the build is finished, an Android APK will be created under `bin/`.

You can then use `adb install bin/{apk_name}` to install it to an Android device.

