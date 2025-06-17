import os
import subprocess
import shutil
import glob
import argparse
import sys

# a personal build script by Pigeon Nation
# can run on a macbook m1 or later i think
# compiles c/c++ to windows x86, macos aarch/x86, linux x86

FNAME_OUT = "main"
SRC_DIR = "src"
BUILD_DIR = "build"
MACOS_BUILD_DIR = os.path.join(BUILD_DIR, "macos")
WINDOWS_BUILD_DIR = os.path.join(BUILD_DIR, "windows")
LINUX_BUILD_DIR = os.path.join(BUILD_DIR, "linux")

MACOS_CXX = "clang++"
MACOS_C = "clang"
MACOS_ARCH_FLAGS = ["-arch", "arm64", "-arch", "x86_64"]

# windows: Requires mingw-w64 cross-compiler installed via Homebrew
WINDOWS_TOOLCHAIN_PREFIX = "/opt/homebrew/bin/x86_64-w64-mingw32"
WINDOWS_CXX = f"{WINDOWS_TOOLCHAIN_PREFIX}-g++"
WINDOWS_C = f"{WINDOWS_TOOLCHAIN_PREFIX}-gcc"
# WINDOWS_DLL_COPY_PATH = f"{WINDOWS_TOOLCHAIN_PREFIX}-g++/../../lib" # Path to MinGW DLLs, adjust if needed

# requires a Linux x86_64 cross-compiler.
# install using Homebrew:
# 1. brew tap messense/macos-cross-toolchains
# 2. brew install x86_64-unknown-linux-gnu
LINUX_TOOLCHAIN_PREFIX = "/opt/homebrew/bin" # m1 mac hb path
LINUX_CXX = f"{LINUX_TOOLCHAIN_PREFIX}/x86_64-unknown-linux-gnu-g++"
LINUX_C = f"{LINUX_TOOLCHAIN_PREFIX}/x86_64-unknown-linux-gnu-gcc"

# c/++ flags
COMMON_CXX_FLAGS = ["-std=c++17", "-Wall", "-Wextra"]
COMMON_C_FLAGS = ["-std=c11", "-Wall", "-Wextra"]

def run_command(command, cwd=None):
    print(f"Executing: {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        if result.stdout:
            print("STDOUT:\n", result.stdout)
        if result.stderr:
            print("STDERR:\n", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Command failed with exit code {e.returncode}")
        print("STDOUT:\n", e.stdout)
        print("STDERR:\n", e.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"ERROR: Command '{command[0]}' not found. "
              f"Please ensure it's installed and in your PATH, or correct the toolchain prefix.")
        sys.exit(1)

def get_source_files(base_dir):
    # find c/c++ files
    cpp_files = glob.glob(os.path.join(base_dir, "**", "*.cpp"), recursive=True)
    c_files = glob.glob(os.path.join(base_dir, "**", "*.c"), recursive=True)
    return cpp_files + c_files

def ensure_dir(path): # ensure a dir exists
    os.makedirs(path, exist_ok=True)

def build_macos():
    print("\n--- Building for macOS (Universal Binary) ---")
    ensure_dir(MACOS_BUILD_DIR)
    
    source_files = get_source_files(SRC_DIR)
    if not source_files:
        print(f"No source files found in {SRC_DIR}.")
        return

    object_files = []
    
    # source file -> object file
    for src_file in source_files:
        base_name = os.path.basename(src_file)
        obj_file = os.path.join(MACOS_BUILD_DIR, base_name + ".o")
        object_files.append(obj_file)
        
        if src_file.endswith(".cpp"):
            compiler = MACOS_CXX
            flags = COMMON_CXX_FLAGS
        elif src_file.endswith(".c"):
            compiler = MACOS_C
            flags = COMMON_C_FLAGS
        else:
            print(f"Skipping unknown file type: {src_file}")
            continue

        compile_command = [
            compiler,
            *flags,
            *MACOS_ARCH_FLAGS,
            "-c", # compile not link
            src_file,
            "-o", obj_file
        ]

        compile_command = [arg for arg in compile_command if arg]
        
        if not run_command(compile_command):
            print(f"Failed to compile {src_file}")
            return

    output_executable = os.path.join(MACOS_BUILD_DIR, FNAME_OUT)
    
    # link
    link_command = [
        MACOS_CXX,
        *object_files,
        *MACOS_ARCH_FLAGS,
        "-o", output_executable
    ]
    link_command = [arg for arg in link_command if arg]

    if run_command(link_command):
        print(f"Successfully built macOS executable: {output_executable}")

def build_windows():
    print("\n--- Building for Windows (x86_64) ---")
    ensure_dir(WINDOWS_BUILD_DIR)

    source_files = get_source_files(SRC_DIR)
    if not source_files:
        print(f"No source files found in {SRC_DIR}.")
        return

    object_files = []

    # obj file creation
    for src_file in source_files:
        base_name = os.path.basename(src_file)
        obj_file = os.path.join(WINDOWS_BUILD_DIR, base_name + ".o")
        object_files.append(obj_file)

        if src_file.endswith(".cpp"):
            compiler = WINDOWS_CXX
            flags = COMMON_CXX_FLAGS
        elif src_file.endswith(".c"):
            compiler = WINDOWS_C
            flags = COMMON_C_FLAGS
        else:
            print(f"Skipping unknown file type: {src_file}")
            continue

        compile_command = [
            compiler,
            *flags,
            "-c",
            src_file,
            "-o", obj_file
        ]
        compile_command = [arg for arg in compile_command if arg]
        
        if not run_command(compile_command):
            print(f"Failed to compile {src_file}")
            return

    output_executable = os.path.join(WINDOWS_BUILD_DIR, FNAME_OUT + ".exe")

    # link
    link_command = [
        WINDOWS_CXX,
        *object_files,
        "-static-libstdc++",
        "-static-libgcc",
        "-o", output_executable
    ]
    link_command = [arg for arg in link_command if arg]

    if run_command(link_command):
        print(f"Successfully built Windows executable: {output_executable}")

        ###### TOCHECK ######

        '''dll_source_path = os.path.join(WINDOWS_DLL_COPY_PATH, "libwinpthread-1.dll")
        if os.path.exists(dll_source_path):
            shutil.copy(dll_source_path, WINDOWS_BUILD_DIR)
            print(f"Copied {os.path.basename(dll_source_path)} to {WINDOWS_BUILD_DIR}")
        else:
            print(f"Warning: Could not find {dll_source_path} to copy. Your .exe might need it.")'''

def build_linux():
    print("\n--- Building for Linux (x86_64) ---")
    ensure_dir(LINUX_BUILD_DIR)

    source_files = get_source_files(SRC_DIR)
    if not source_files:
        print(f"No source files found in {SRC_DIR}.")
        return

    object_files = []

    # compile
    for src_file in source_files:
        base_name = os.path.basename(src_file)
        obj_file = os.path.join(LINUX_BUILD_DIR, base_name + ".o")
        object_files.append(obj_file)

        if src_file.endswith(".cpp"):
            compiler = LINUX_CXX
            flags = COMMON_CXX_FLAGS
        elif src_file.endswith(".c"):
            compiler = LINUX_C
            flags = COMMON_C_FLAGS
        else:
            print(f"Skipping unknown file type: {src_file}")
            continue

        compile_command = [
            compiler,
            *flags,
            "-c",
            src_file,
            "-o", obj_file
        ]
        compile_command = [arg for arg in compile_command if arg]
        
        if not run_command(compile_command):
            print(f"Failed to compile {src_file}")
            return

    output_executable = os.path.join(LINUX_BUILD_DIR, FNAME_OUT)

    # link
    link_command = [
        LINUX_CXX,
        *object_files,
        *COMMON_CXX_FLAGS,
        "-o", output_executable
    ]
    link_command = [arg for arg in link_command if arg]

    if run_command(link_command):
        print(f"Successfully built Linux executable: {output_executable}")

def build_all():
    print("--- Starting full project build ---")
    ensure_dir(BUILD_DIR)

    build_macos()
    build_windows()
    build_linux()

    print("\n--- All builds completed! ---")
    print(f"Executables can be found in: {BUILD_DIR}/")

def clean_all():
    print("--- Cleaning all build artifacts ---")
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
        print(f"Removed directory: {BUILD_DIR}")
    else:
        print(f"Build directory not found: {BUILD_DIR}")
    print("--- All cleaned! ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A simple C/C++ build system for macOS, Windows, and Linux."
    )
    parser.add_argument(
        "command",
        choices=["build", "clean"],
        help="Command to execute: 'build' to compile all platforms, 'clean' to remove build artifacts."
    )

    args = parser.parse_args()

    # ensure root

    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"Working directory: {os.getcwd()}")

    if args.command == "build":
        build_all()
    elif args.command == "clean":
        clean_all()
