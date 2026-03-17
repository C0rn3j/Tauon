from pythonforandroid.recipe import Recipe
from pythonforandroid.toolchain import current_directory
import sh
import os


class PhazorRecipe(Recipe):
    version = "0.1"
    url = None
    depends = ["python3"]
    call_hostpython_via_targetpython = False
    name = "phazor"
    built_libraries = {
        "libphazor.so": ".",
        "libphazor-pw.so": ".",
    }

    def get_build_dir(self, arch):
        # Build directly from your project checkout
        return os.path.abspath(os.path.join(self.ctx.root_dir, "..", ".."))

    def build_arch(self, arch):
        env = self.get_recipe_env(arch)

        project_dir = os.path.abspath(".")
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

        prefix = f"/opt/android-deps/{arch.arch}"
        outdir = os.path.join(project_dir, "build", "android", arch.arch)
        outfile = os.path.join(outdir, "libphazor.so")

        os.makedirs(outdir, exist_ok=True)

        with current_directory(project_dir):
            sh.Command(env["CC"])(
                f"--target={env['TARGET']}",
                "-shared", "-fPIC", "-Wall", "-O3", "-g",
                "-Isrc",
                f"-I{prefix}/include",
                f"-I{python_include}",
                "src/phazor/kissfft/kiss_fftr.c",
                "src/phazor/kissfft/kiss_fft.c",
                "src/phazor/phazor.c",
                f"-L{prefix}/lib",
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
