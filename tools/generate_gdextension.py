"""
GDExtension File Generator

Generates the .gdextension file with proper platform configurations.
Can be used standalone or as part of the build pipeline.
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional
from tools.base_tool import BaseTool


def detect_platform() -> str:
    """Detect the current platform."""
    import platform
    system = platform.system().lower()
    
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    else:
        raise ValueError(f"Unsupported platform: {system}")


def get_library_extension(platform: str) -> str:
    """Get the library file extension for a platform."""
    extensions = {
        "windows": "dll",
        "linux": "so",
        "macos": "dylib"
    }
    return extensions.get(platform, "so")


def get_library_prefix(platform: str) -> str:
    """Get the library file prefix for a platform."""
    if platform == "windows":
        return ""
    return "lib"


def generate_library_path(platform: str, target: str, arch: str) -> str:
    """
    Generate the library path for a specific platform/target/arch.
    
    Args:
        platform: Platform name (windows, linux, macos)
        target: Target name (editor, template_debug, template_release)
        arch: Architecture (x86_64, arm64, universal, etc.)
        
    Returns:
        Library path string
    """
    prefix = get_library_prefix(platform)
    ext = get_library_extension(platform)
    
    # Build the filename
    parts = [prefix + "gdai", platform, target]
    
    # Add arch if not universal or if platform is not macOS
    if arch != "universal" or platform != "macos":
        parts.append(arch)
    
    filename = ".".join(parts) + f".{ext}"
    
    return f"res://addons/gdai/bin/{platform}/{filename}"


def generate_gdextension_content(
    platforms: Optional[List[str]] = None,
    targets: Optional[List[str]] = None,
    architectures: Optional[Dict[str, List[str]]] = None,
    godot_version: str = "4.4",
    entry_symbol: str = "gdai_library_init"
) -> str:
    """
    Generate the content of a .gdextension file.
    
    Args:
        platforms: List of platforms to include (None = all)
        targets: List of targets to include (None = editor only)
        architectures: Dict of platform -> list of architectures
        godot_version: Minimum Godot version
        entry_symbol: Entry point symbol name
        
    Returns:
        Complete .gdextension file content
    """
    
    # Default values
    if platforms is None:
        platforms = ["windows", "linux", "macos"]
    
    if targets is None:
        targets = ["editor"]
    
    if architectures is None:
        architectures = {
            "windows": ["x86_64"],
            "linux": ["x86_64"],
            "macos": ["universal"]
        }
    
    # Start building content
    lines = [
        "[configuration]",
        f'entry_symbol = "{entry_symbol}"',
        f'compatibility_minimum = "{godot_version}"',
        "reloadable = true",
        "",
        "[libraries]"
    ]
    
    # Generate library entries for each platform/target/arch combination
    for platform in platforms:
        lines.append(f"# {platform.title()}")
        
        for target in targets:
            for arch in architectures.get(platform, ["x86_64"]):
                lib_path = generate_library_path(platform, target, arch)
                
                # Generate the key
                key_parts = [platform, target]
                if arch != "universal" or platform != "macos":
                    key_parts.append(arch)
                key = ".".join(key_parts)
                
                lines.append(f'{key} = "{lib_path}"')
        
        lines.append("")  # Blank line between platforms
    
    return "\n".join(lines)


def write_gdextension_file(output_path: Path, content: str) -> None:
    """Write the gdextension content to a file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content)
    print(f"✅ Generated: {output_path}")


def main():
    """CLI entry point for standalone usage."""
    parser = argparse.ArgumentParser(
        description="Generate .gdextension file for GodotAI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("plugin/gdai.gdextension"),
        help="Output file path (default: plugin/gdai.gdextension)"
    )
    
    parser.add_argument(
        "--platform", "-p",
        choices=["windows", "linux", "macos"],
        help="Generate for specific platform only"
    )
    
    parser.add_argument(
        "--all-platforms",
        action="store_true",
        help="Generate for all platforms (default)"
    )
    
    parser.add_argument(
        "--target", "-t",
        choices=["editor", "template_debug", "template_release"],
        action="append",
        help="Target(s) to include (can be specified multiple times)"
    )
    
    parser.add_argument(
        "--godot-version",
        default="4.4",
        help="Minimum Godot version (default: 4.4)"
    )
    
    parser.add_argument(
        "--entry-symbol",
        default="gdai_library_init",
        help="Entry point symbol (default: gdai_library_init)"
    )
    
    args = parser.parse_args()
    
    # Determine platforms
    if args.platform:
        platforms = [args.platform]
    else:
        platforms = ["windows", "linux", "macos"]
    
    # Determine targets
    targets = args.target if args.target else ["editor"]
    
    # Standard architectures
    architectures = {
        "windows": ["x86_64"],
        "linux": ["x86_64"],
        "macos": ["universal"]
    }
    
    # Generate content
    content = generate_gdextension_content(
        platforms=platforms,
        targets=targets,
        architectures=architectures,
        godot_version=args.godot_version,
        entry_symbol=args.entry_symbol
    )
    
    # Write file
    try:
        write_gdextension_file(args.output, content)
        print(f"\n📄 Generated .gdextension file with:")
        print(f"   Platforms: {', '.join(platforms)}")
        print(f"   Targets: {', '.join(targets)}")
        print(f"   Godot: {args.godot_version}+")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return 1

# Add this to the END of tools/generate_gdextension.py

from typing import Dict, Any
from tools.base_tool import BaseTool


class GenerateGDExtensionTool(BaseTool):
    """Generate gdextension file based on built libraries."""
    
    @property
    def name(self) -> str:
        return "generate-gdextension"
    
    @property
    def description(self) -> str:
        return "Generate gdai.gdextension file from built libraries"
    
    @property
    def category(self) -> str:
        return "build"
    
    @property
    def visible(self) -> bool:
        return False  # Hidden from menu, called by build-plugin
    
    def execute(self, args: Dict[str, Any]) -> int:
        """Execute generation for current platform."""
        root_dir = self.get_root_dir()
        output_path = root_dir / "plugin" / "gdai.gdextension"
        
        try:
            # Detect current platform
            current_platform = detect_platform()
            
            # Get architecture from args or use default
            arch = args.get("architecture", "x86_64")
            if arch == "universal":
                arch = "universal"
            
            print(f"Generating gdextension for {current_platform} {arch}...")
            
            # Generate for current platform only (for dev builds)
            content = generate_gdextension_content(
                platforms=[current_platform],
                targets=["editor"],
                architectures={
                    current_platform: [arch]
                }
            )
            
            write_gdextension_file(output_path, content)
            print(f"✅ Generated: {output_path}")
            print(f"   Platform: {current_platform}.editor.{arch}")
            
            return 0
            
        except Exception as e:
            print(f"❌ Error generating gdextension: {e}")
            import traceback
            traceback.print_exc()
            return 1

if __name__ == "__main__":
    sys.exit(main())