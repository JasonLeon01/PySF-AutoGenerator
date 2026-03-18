import os
import re
import sys
import platform
import subprocess


def scan_hpp_files(hpp_root, repo_root, parse_folders):
    hpp_folders = {}
    for folder in parse_folders:
        folder_path = os.path.join(hpp_root, repo_root, folder)
        if not os.path.isdir(folder_path):
            print(f"Warning: {folder_path} is not a valid directory, skipping.")
            continue

        hpp_files = []
        for dirpath, _, filenames in os.walk(folder_path):
            for filename in filenames:
                if filename.endswith(".hpp"):
                    hpp_files.append(filename)
        hpp_folders[folder] = sorted(list(set(hpp_files)))
    return hpp_folders


def normalize_type(type_str):
    result = re.sub(r"\bconst\b|\bvolatile\b", "", type_str)
    result = re.sub(r"\s+", " ", result).strip()
    return result


def resolve_macos_sdk_path():
    if sys.platform != "darwin":
        return None

    sdkroot = os.environ.get("SDKROOT")
    if sdkroot and os.path.exists(sdkroot):
        return sdkroot

    try:
        sdk_path = (
            subprocess.check_output(
                ["xcrun", "--sdk", "macosx", "--show-sdk-path"],
                stderr=subprocess.DEVNULL,
                text=True,
            )
            .strip()
        )
        if sdk_path and os.path.exists(sdk_path):
            return sdk_path
    except Exception:
        return None
    return None


def resolve_libclang_prefix():
    libclang_path = os.environ.get("PYSF_LIBCLANG_PATH") or os.environ.get("LIBCLANG_PATH")
    if not libclang_path:
        return None

    prefix = os.path.dirname(os.path.dirname(libclang_path))
    if prefix and os.path.isdir(prefix):
        return prefix
    return None


def resolve_clang_resource_dir():
    if sys.platform != "darwin":
        return None

    resource_dir = os.environ.get("CLANG_RESOURCE_DIR")
    if resource_dir and os.path.isdir(resource_dir):
        return resource_dir

    prefix = resolve_libclang_prefix()
    if not prefix:
        return None

    clang_bin = os.path.join(prefix, "bin", "clang")
    if os.path.exists(clang_bin):
        try:
            resource_dir = (
                subprocess.check_output(
                    [clang_bin, "--print-resource-dir"],
                    stderr=subprocess.DEVNULL,
                    text=True,
                )
                .strip()
            )
            if resource_dir and os.path.isdir(resource_dir):
                return resource_dir
        except Exception:
            pass

    clang_lib_dir = os.path.join(prefix, "lib", "clang")
    if not os.path.isdir(clang_lib_dir):
        return None

    try:
        versions = sorted(os.listdir(clang_lib_dir), reverse=True)
        for version in versions:
            candidate = os.path.join(clang_lib_dir, version)
            if os.path.isdir(candidate):
                return candidate
    except Exception:
        return None

    return None


def get_macos_clang_args(macos_min_version="12.0"):
    if sys.platform != "darwin":
        return []

    args = []

    arch = platform.machine().lower()
    if arch == "aarch64":
        arch = "arm64"
    if arch in {"arm64", "x86_64"}:
        args.extend(["-target", f"{arch}-apple-macosx{macos_min_version}"])
        args.append(f"-mmacosx-version-min={macos_min_version}")

    llvm_prefix = resolve_libclang_prefix()
    if llvm_prefix:
        libcpp_include = os.path.join(llvm_prefix, "include", "c++", "v1")
        if os.path.isdir(libcpp_include):
            args.extend(["-isystem", libcpp_include])

    resource_dir = resolve_clang_resource_dir()
    if resource_dir:
        resource_include = os.path.join(resource_dir, "include")
        if os.path.isdir(resource_include):
            args.extend(["-isystem", resource_include])

    sdk_path = resolve_macos_sdk_path()
    if sdk_path:
        args.extend(["-isysroot", sdk_path])

        sdk_usr_include = os.path.join(sdk_path, "usr", "include")
        if os.path.isdir(sdk_usr_include):
            args.extend(["-isystem", sdk_usr_include])

        frameworks = os.path.join(sdk_path, "System/Library/Frameworks")
        private_frameworks = os.path.join(sdk_path, "System/Library/PrivateFrameworks")
        if os.path.isdir(frameworks):
            args.extend(["-iframework", frameworks])
        if os.path.isdir(private_frameworks):
            args.extend(["-iframework", private_frameworks])

    if resource_dir:
        args.extend(["-resource-dir", resource_dir])

    return args
