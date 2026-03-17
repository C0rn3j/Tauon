from pythonforandroid.recipe import Recipe
from pythonforandroid.toolchain import current_directory
import os
import shlex
from pathlib import Path

import sh


class PhazorRecipe(Recipe):
    version = "0.1"
    url = None
    depends = ["python3"]
    call_hostpython_via_targetpython = False
    name = "phazor"
    built_libraries = {
        "libphazor.so": ".",
    }

    def get_project_dir(self) -> str:
        return str(Path(__file__).resolve().parents[4])

    def get_deps_prefix(self, arch) -> Path:
        override = os.environ.get("PHAZOR_ANDROID_DEPS_PREFIX")
        if override:
            return Path(override) / arch.arch
        return Path(self.get_project_dir()) / "android-deps" / arch.arch

    def validate_deps_prefix(self, prefix: Path) -> None:
        include_dir = prefix / "include"
        lib_dir = prefix / "lib"
        expected_headers = [
            include_dir / "FLAC/stream_decoder.h",
            include_dir / "opus/opusfile.h",
            include_dir / "vorbis/vorbisfile.h",
            include_dir / "wavpack/wavpack.h",
            include_dir / "libopenmpt/libopenmpt.h",
            include_dir / "gme/gme.h",
            include_dir / "samplerate.h",
            include_dir / "mpg123.h",
        ]
        expected_libs = [
            lib_dir / "libFLAC.so",
            lib_dir / "libopusfile.so",
            lib_dir / "libvorbisfile.so",
            lib_dir / "libwavpack.so",
            lib_dir / "libopenmpt.so",
            lib_dir / "libgme.so",
            lib_dir / "libsamplerate.so",
            lib_dir / "libmpg123.so",
        ]

        missing = [str(path) for path in [include_dir, lib_dir, *expected_headers, *expected_libs] if not path.exists()]
        if missing:
            raise FileNotFoundError(
                "Missing Android native dependencies for Phazor.\n"
                f"Expected prefix: {prefix}\n"
                "Set PHAZOR_ANDROID_DEPS_PREFIX to the parent directory containing ABI subdirs if needed.\n"
                "Missing paths:\n - " + "\n - ".join(missing)
            )

    def get_build_dir(self, arch):
        # Keep the build output in the project root so built_libraries can pick it up.
        return self.get_project_dir()

    def build_arch(self, arch):
        env = self.get_recipe_env(arch)
        project_dir = self.get_project_dir()

        python_root = os.path.join(
            project_dir,
            ".buildozer", "android", "platform",
            f"build-{arch.arch}",
            "build", "other_builds", "python3",
            f"{arch.arch}__ndk_target_24",
            "python3"
        )

        python_include = os.path.join(python_root, "Include")
        python_lib_dir = os.path.join(python_root, "android-build")

        prefix = self.get_deps_prefix(arch)
        self.validate_deps_prefix(prefix)
        outfile = os.path.join(project_dir, "libphazor.so")
        cc = shlex.split(env["CC"])

        with current_directory(project_dir):
            sh.Command(cc[0])(
                *cc[1:],
                "-std=c17",
                "-shared", "-Wall", "-O3", "-g",
                "-Isrc",
                f"-I{prefix / 'include'}",
                f"-I{python_include}",
                "src/phazor/kissfft/kiss_fftr.c",
                "src/phazor/kissfft/kiss_fft.c",
                "src/phazor/phazor.c",
                f"-L{prefix / 'lib'}",
                f"-L{python_lib_dir}",
                "-lpython3.14",
                "-lsamplerate",
                "-lwavpack",
                "-lopusfile",
                "-lvorbisfile",
                "-lmpg123",
                "-lFLAC",
                "-lopenmpt",
                "-lgme",
                "-llog",
                "-o", outfile,
                _env=env
            )

        print(f"Built {outfile}")


recipe = PhazorRecipe()
