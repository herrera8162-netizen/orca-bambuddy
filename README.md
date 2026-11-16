# orca-bambuddy

Installs the newest [Orca Slicer](https://github.com/OrcaSlicer/OrcaSlicer) for macOS, patched so that prints sent to a Bambu Lab printer (or to [Bambuddy](https://github.com/maziggy/bambuddy)) still contain the 3D model.

## Why

When Orca sends a print to a Bambu printer, the `.gcode.3mf` it uploads holds only the toolpath and a thumbnail. Tools that archive or reprint jobs, such as Bambuddy, then have no model to show or reuse.

The patch changes one value in the app: the options Orca uses when it saves the file it sends. It still sends the toolpath, and now writes the model meshes into the file as well, the same way a normal project save does.

## Install

Needs macOS with `curl`, `jq` and `python3`. It works on both Intel and Apple Silicon Macs.

```sh
git clone https://github.com/herrera8162-netizen/orca-bambuddy
cd orca-bambuddy
./orca-bambuddy            # newest release, including betas
./orca-bambuddy --stable   # newest stable release only
./orca-bambuddy --force    # reinstall even if already up to date
```

The script:

1. downloads the official release;
2. patches it;
3. re-signs it for your Mac only;
4. removes the "downloaded from the internet" quarantine flag;
5. replaces `/Applications/OrcaSlicer.app`, quitting Orca first if it's running.

Run it again whenever Orca releases a new version.

## Notes

- **No developer certificate:** the app is re-signed for your Mac only, so macOS may ask for Local Network permission again after each update.
- **Fails safely:** the patch finds its target by the function's name and checks the original bytes before changing them. If a future Orca version changes that code, it stops with an error and leaves your installed app alone.
- **Unofficial:** this isn't affiliated with Orca Slicer or Bambu Lab.
