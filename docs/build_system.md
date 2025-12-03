# Building GodotAI

## Prerequisites

### Required Tools

1. **CMake 3.13+**
   - Windows: [Download installer](https://cmake.org/download/)
   - Linux: `sudo apt install cmake`
   - macOS: `brew install cmake`

2. **C++ Compiler**
   - Windows: Visual Studio 2022 with C++ Desktop Development workload
   - Linux: GCC 7+ or Clang 6+
   - macOS: Xcode Command Line Tools

3. **Python 3.6+** (for build tools)

4. **Git** (for cloning and submodule management)

## Quick Build

```bash
# Clone the repository
git clone https://github.com/RectangleEquals/godotai.git
cd godotai

# Run the build system
python setup.py
```

Select tools in this order:
1. **init** - Initialize git submodules (godot-cpp, libgit2, libhv)
2. **build-libgit2** - Build git operations library
3. **build-libhv** - Build HTTP networking library
4. **build** - Build the GodotAI GDExtension

The final library will be in `plugin/bin/`.

## Build System Architecture

GodotAI uses a modular Python-based build system with CMake:

```
setup.py                      # Main entry point (interactive menu)
├── tools/
│   ├── init.py              # Initialize submodules
│   ├── build_cmake.py       # Build GodotAI with CMake
│   ├── build_libgit2.py     # Build libgit2 dependency
│   ├── build_libhv.py       # Build libhv dependency
│   ├── clean.py             # Clean build artifacts
│   └── ...
└── CMakeLists.txt           # CMake configuration for GodotAI
```

### Why CMake?

We migrated from the originally planned SCons system to CMake because:
- **godot-cpp provides excellent CMake support** with comprehensive platform handling
- **Avoids Python 3.13+ compatibility issues** that affect SCons
- **Consistency with dependencies** - libgit2 and libhv already use CMake
- **Better IDE integration** - Native support in Visual Studio, CLion, VS Code

## Configuration

The build system stores configuration in `.buildconfig.json`:

```json
{
  "godot_version": "4.4",
  "platform": "windows",
  "target": "template_release",
  "architecture": "x86_64",
  "precision": "single",
  "jobs": 4
}
```

You can modify this file or override settings when running the build tool.

## Build Options

### Build Targets

- **template_debug** - Debug builds with symbols, slower but easier to debug
- **template_release** - Optimized release builds (default)
- **editor** - Editor builds with additional editor-specific features

### Floating-Point Precision

- **single** - Single precision (default, matches Godot)
- **double** - Double precision (for high-precision applications)

### Architecture

- **x86_64** - 64-bit Intel/AMD (default)
- **x86_32** - 32-bit Intel/AMD
- **arm64** - ARM 64-bit (Apple Silicon, ARM servers)
- **universal** - macOS universal binary (x86_64 + arm64)

## Platform-Specific Notes

### Windows

- Requires Visual Studio 2022 (Community edition is free)
- Builds use the Visual Studio 17 2022 generator
- Output: `libgodotai.windows.template_release.x86_64.dll`

### Linux

- Requires GCC 7+ or Clang 6+
- Install build essentials: `sudo apt install build-essential cmake`
- Output: `libgodotai.linux.template_release.x86_64.so`

### macOS

- Requires Xcode Command Line Tools: `xcode-select --install`
- Supports universal binaries (x86_64 + arm64)
- Output: `libgodotai.macos.template_release.universal.dylib`

## Advanced Usage

### Using CMake Directly

If you prefer direct CMake usage:

```bash
# Configure
cmake -S . -B build/cmake -DGODOTAI_BUILD_TYPE=template_release

# Build
cmake --build build/cmake --config Release --parallel

# Install to plugin/bin
cmake --install build/cmake --config Release
```

### Available CMake Options

```cmake
GODOTAI_BUILD_TYPE=template_release  # template_debug|template_release|editor
GODOTAI_PRECISION=single             # single|double
GODOTAI_USE_HOT_RELOAD=ON            # ON|OFF
GODOTAI_DEV_BUILD=OFF                # ON|OFF
GODOTAI_ENABLE_TESTING=OFF           # ON|OFF
```

### IDE Integration

**Visual Studio Code:**
1. Install CMake Tools extension
2. Open folder, select kit
3. Use CMake sidebar to build

**Visual Studio 2022:**
1. File → Open → Folder
2. Visual Studio detects CMakeLists.txt automatically
3. Build → Build All

**CLion:**
1. Open folder
2. CLion configures CMake automatically
3. Run → Build

## Build Output

```
godotai/
├── build/
│   ├── cmake/              # CMake build artifacts
│   │   └── bin/            # Compiled libraries
│   └── ...
├── build_ext_libs/         # Built dependencies
│   ├── git2.lib           # libgit2 (Windows)
│   ├── libgit2.a          # libgit2 (Unix)
│   ├── hv_static.lib      # libhv (Windows)
│   └── libhv_static.a     # libhv (Unix)
└── plugin/
    ├── bin/                # Final GDExtension libraries
    │   └── libgodotai.*   # → Copy to Godot project
    ├── godotai.gdextension # GDExtension manifest
    └── ...
```

## Library Naming

Built libraries follow godot-cpp's naming convention:

```
libgodotai.<platform>.<target>[.dev][.double].<arch>.<ext>
```

Examples:
- `libgodotai.windows.template_release.x86_64.dll`
- `libgodotai.linux.template_debug.dev.x86_64.so`
- `libgodotai.macos.template_release.universal.dylib`

## Troubleshooting

### CMake not found
```bash
# Windows: Download from cmake.org
# Linux: sudo apt install cmake
# macOS: brew install cmake
```

### godot-cpp not found
```bash
python setup.py
# Select: init
```

### Missing dependencies
```bash
# Build libgit2
python setup.py
# Select: build-libgit2

# Build libhv
python setup.py
# Select: build-libhv
```

### Compiler errors
- Ensure compiler meets minimum version requirements
- Try a clean build: `python setup.py` → `clean` → `build`
- Check that all submodules are initialized

### Build fails on Windows
- Install Visual Studio 2022 with C++ Desktop Development
- Or modify `tools/build_cmake.py` to use VS 2019: `"Visual Studio 16 2019"`

## Clean Build

To start fresh:

```bash
python setup.py
# Select: clean
# Options: all (cleans everything including dependencies)
```

Or manually:
```bash
rm -rf build/ build_ext_libs/ plugin/bin/
```

## Performance Tips

1. **Parallel builds**: Use multiple CPU cores
   - Set `jobs` parameter to your CPU core count
   - Or let CMake auto-detect: `jobs: 0`

2. **Incremental builds**: Only clean when necessary
   - Cleaning forces a full rebuild
   - Incremental builds are much faster

3. **Release builds**: Use `template_release` for production
   - Debug builds include symbols and are much larger
   - Release builds are optimized

4. **Hot reload**: Enable for development, disable for production
   - Allows code changes without restarting Godot
   - Adds overhead, disable for final builds

## Next Steps

After building:

1. **Copy to Godot project**:
   ```bash
   cp -r plugin/ /path/to/godot-project/addons/godotai/
   ```

2. **Enable in Godot**:
   - Open your Godot project
   - Project → Project Settings → Plugins
   - Enable "GodotAI"

3. **Verify installation**:
   - Check for GodotAI menu in Godot editor
   - Open Output panel to see initialization messages

## Further Reading

- [CMAKE_MIGRATION.md](CMAKE_MIGRATION.md) - Detailed migration guide
- [godot-cpp CMake docs](https://github.com/godotengine/godot-cpp)
- [GDExtension tutorial](https://docs.godotengine.org/en/latest/tutorials/scripting/gdextension/)