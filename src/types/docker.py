import os
import re
import shlex
import socket
import string
import subprocess
import sys

from src.utils.path_util import PathUtil
from config import APP_NAME_FIREFOX, APP_NAME_DESKTOP, APP_NAME_VSCODE, APP_NAME_ZETTLR, APP_NAME_GODOT, \
    APP_NAME_JABREF, APP_OWNER_NAME_GODOT, APP_OWNER_NAME_JABREF
from PIL import Image
import io, base64, numpy as np, time
import uuid


class DockerImageBuilder:

    BASE_ENV_TAG = 'base-env'

    @staticmethod
    def docker_image_exists(image_name: str) -> bool:
        image_name = image_name.strip()
        # repo, tag = image_name.split(":", 1)
        result = subprocess.run(
            [
                "docker",
                "images",
                "--format",
                "{{.Repository}}:{{.Tag}}",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

        images = {line.strip() for line in result.stdout.splitlines()}
        return image_name in images

    @staticmethod
    def build_base_image(
        reponame: str,
        dockerfile_name: str = "DockerfileBase",
        platform: str | None = None,
        tag: str = BASE_ENV_TAG,
    ) -> str:
        """
        Build a base environment image.

        :return: image name, e.g. zettlr:base-env
        """
        dockerfile = PathUtil.get_docker_file_filepath(
            reponame=reponame,
            filename=dockerfile_name,
        ).resolve()

        if not dockerfile.exists():
            raise FileNotFoundError(dockerfile)

        context_dir = dockerfile.parent
        image_name = f"{reponame.lower()}:{tag}"

        cmd = [
            "docker", "build",
            "-t", image_name,
            "-f", str(dockerfile),
        ]

        if platform:
            cmd.extend(["--platform", platform])

        cmd.append(str(context_dir))

        print(f"[+] Building base env image: {image_name}")
        subprocess.run(cmd, check=True)
        print(f"[✓] Base env ready: {image_name}")

        return image_name

    @staticmethod
    def build_diff_image(
        reponame: str,
        before_commit: str,
        after_commit: str,
        dockerfile_name: str = "DockerfileDiff",
        platform: str | None = None,
    ) -> str:
        """
        Build a single image that contains:
          - /before : build at before_commit
          - /after  : build at after_commit
        """

        image_name = (
            f"{reponame.lower()}:diff-"
            f"{before_commit[:8]}-"
            f"{after_commit[:8]}"
        )

        if DockerImageBuilder.docker_image_exists(image_name):
            print(f"[=] Image exists, skip build: {image_name}")
            return image_name

        dockerfile = PathUtil.get_docker_file_filepath(
            reponame=reponame,
            filename=dockerfile_name,
        ).resolve()

        if not dockerfile.exists():
            raise FileNotFoundError(dockerfile)

        context_dir = dockerfile.parent

        cmd = [
            "docker", "build",
            "-t", image_name,
            "--build-arg", f"BEFORE_COMMIT={before_commit}",
            "--build-arg", f"AFTER_COMMIT={after_commit}",
            "-f", str(dockerfile),
        ]

        if platform:
            cmd.extend(["--platform", platform])

        cmd.append(str(context_dir))

        print(f"[+] Building diff image: {image_name}")
        subprocess.run(cmd, check=True)
        print(f"[✓] Diff image ready: {image_name}")

        return image_name

    @staticmethod
    def ensure_diff_image(
        reponame: str,
        before_commit: str,
        after_commit: str,
        *,
        base_dockerfile: str = "DockerfileBase",
        diff_dockerfile: str = "DockerfileDiff",
        base_tag: str = BASE_ENV_TAG,
        platform: str | None = None,
    ) -> str:
        """
        Ensure that:
          1) base image exists (build if missing)
          2) diff image exists (build if missing)

        Return diff image name.
        """

        base_image = f"{reponame.lower()}:{base_tag}"

        # ---- Step 1: ensure base image ----
        if not DockerImageBuilder.docker_image_exists(base_image):
            print(f"[!] Base image missing, building: {base_image}")
            DockerImageBuilder.build_base_image(
                reponame=reponame,
                dockerfile_name=base_dockerfile,
                platform=platform,
                tag=base_tag,
            )
        else:
            print(f"[✓] Base image exists: {base_image}")

        # ---- Step 2: ensure diff image ----
        diff_image = (
            f"{reponame.lower()}:diff-"
            f"{before_commit[:8]}-"
            f"{after_commit[:8]}"
        )

        if DockerImageBuilder.docker_image_exists(diff_image):
            print(f"[✓] Diff image exists: {diff_image}")
            return diff_image

        print(f"[!] Diff image missing, building: {diff_image}")
        return DockerImageBuilder.build_diff_image(
            reponame=reponame,
            before_commit=before_commit,
            after_commit=after_commit,
            dockerfile_name=diff_dockerfile,
            platform=platform,
        )


class DockerComputer:
    environment = "linux"
    dimensions = (1280, 720)  # Default fallback; will be updated in __enter__.

    def __init__(
        self,
        container_name="cua-image",
        image="cua-image:latest",  ## <-- Use your local image name
        display=":99",
        port_mapping="5900:5900",
    ):
        self.container_name = container_name
        self.image = image
        self.display = display
        self.port_mapping = port_mapping

    @staticmethod
    def stop_and_remove(name: str) -> None:
        """
        Stop and remove a container if it exists.
        Safe to call even if container does not exist.
        """
        subprocess.run(
            ["docker", "rm", "-f", name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    @classmethod
    def run_from_image(
            cls,
            image: str,
            *,
            name: str | None = None,
            display=":99",
            port_mapping="5900:5900",
            detach: bool = True,
            auto_remove: bool = False,
    ) -> "DockerComputer":

        container_name = name or "docker-computer"

        # 👇 stop and remove the previous
        cls.stop_and_remove(container_name)

        cmd = [
            "docker", "run",
            "--name", container_name,
            "-e", f"DISPLAY={display}",
            "-p", port_mapping,
        ]

        if detach:
            cmd.append("-d")

        if auto_remove:
            cmd.append("--rm")

        cmd.append(image)

        subprocess.run(cmd, check=True)

        print(f"[+] Container started: {container_name}")

        return cls(
            container_name=container_name,
            image=image,
            display=display,
            port_mapping=port_mapping,
        )

    @staticmethod
    def _wait_for_port(host: str, port: int, timeout: float = 20.0) -> bool:
        """
        Wait until TCP port is connectable.
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                with socket.create_connection((host, port), timeout=1):
                    return True
            except OSError:
                time.sleep(0.5)
        return False

    @staticmethod
    def open_vnc_gui(
            host: str = "localhost",
            port: int = 5900,
            password: str = "secret",
    ) -> None:
        """
        Open VNC GUI on the host machine.

        macOS:
          - Uses Finder / Screen Sharing via `open vnc://...`
          - Waits until VNC is READY to avoid black screen

        Other platforms:
          - Print instructions only
        """

        vnc_url = f"vnc://{host}:{port}"

        print("[GUI] Waiting for VNC server to be ready …")
        if not DockerComputer._wait_for_port(host, port, timeout=20):
            print("[GUI] ❌ VNC port not ready after timeout")
            return

        # 🔑 Extra grace time for XFCE session attach (IMPORTANT for macOS)
        time.sleep(3)

        if sys.platform == "darwin":
            print("[GUI] Opening macOS Screen Sharing …")
            print("[GUI] If you see a black screen, close and retry once.")
            print(f"[GUI] Password: {password}")
            subprocess.run(["open", vnc_url], check=False)
            time.sleep(3)
            return
        elif sys.platform.startswith("linux"):
            print("[GUI] VNC available at:")
            print(f"      vncviewer {vnc_url}")
            if password:
                print(f"      Password: {password}")
            return
        else:
            raise RuntimeError(f"Unsupported platform: {sys.platform}")

    def __enter__(self):
        # Check if the container is running
        result = subprocess.run(
            ["docker", "ps", "-q", "-f", f"name={self.container_name}"],
            capture_output=True,
            text=True,
        )

        if not result.stdout.strip():
            # raise RuntimeError(
            #     f"Container {self.container_name} is not running. Build and run with:\n"
            #     f"docker build -t {self.container_name} .\n"
            #     f"docker run --rm -it --name {self.container_name} "
            #     f"-p {self.port_mapping} -e DISPLAY={self.display} {self.container_name}"
            # )
            raise RuntimeError(
                f"Container {self.container_name} is not running. Build and run with:\n"
                f"docker build --platform=linux/amd64 -t {self.container_name} .\n"
                f"docker run --platform=linux/amd64 --rm -it --name {self.container_name} "
                f"-p {self.port_mapping} -e DISPLAY={self.display} {self.container_name}"
            )

        # Fetch display geometry
        geometry = self._exec(
            f"DISPLAY={self.display} xdotool getdisplaygeometry"
        ).strip()
        if geometry:
            w, h = geometry.split()
            self.dimensions = (int(w), int(h))
        # print("Starting Docker container...")
        # # Run the container detached, removing it automatically when it stops
        # subprocess.check_call(
        #     [
        #         "docker",
        #         "run",
        #         "-d",
        #         "--rm",
        #         "--name",
        #         self.container_name,
        #         "-p",
        #         self.port_mapping,
        #         self.image,
        #     ]
        # )
        # # Give the container a moment to start
        # time.sleep(3)
        # print("Entering DockerComputer context")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # print("Stopping Docker container...")
        # subprocess.check_call(["docker", "stop", self.container_name])
        # print("Exiting DockerComputer context")
        pass

    # def _exec(self, cmd: str) -> str:
    #     """
    #     Run 'cmd' in the container.
    #     We wrap cmd in double quotes and escape any double quotes inside it,
    #     so spaces or quotes don't break the shell call.
    #     """
    #     # Escape any existing double quotes in cmd
    #     safe_cmd = cmd.replace('"', '\\"')
    #
    #     # Then wrap the entire cmd in double quotes for `sh -c`
    #     docker_cmd = f'docker exec {self.container_name} sh -c "{safe_cmd}"'
    #
    #     return subprocess.check_output(docker_cmd, shell=True).decode(
    #         "utf-8", errors="ignore"
    #     )

    # def _exec(self, cmd: str, *, detach: bool = False) -> str | None:
    #     # @todo if it affects the other part or firefox
    #     # @todo major issue to fix
    #     # safe_cmd = cmd.replace('"', '\\"')
    #     # docker_cmd = (
    #     #     f'docker exec -d {self.container_name} sh -c "{safe_cmd}"'  # 后台
    #     #     if detach
    #     #     else f'docker exec {self.container_name} sh -c "{safe_cmd}"'
    #     # )
    #     full_cmd = f'source ~/.nvm/nvm.sh && {cmd}'
    #     docker_cmd = (
    #         f'docker exec -d {self.container_name} bash -lc "{full_cmd}"'
    #         if detach
    #         else f'docker exec {self.container_name} bash -lc "{full_cmd}"'
    #     )
    #
    #     if detach:
    #         subprocess.run(docker_cmd, shell=True, check=True)
    #         return None
    #     else:
    #         return subprocess.check_output(docker_cmd, shell=True).decode(
    #             "utf-8", errors="ignore"
    #         )

    def _exec(self, cmd: str, *, detach: bool = False) -> str | None:
        """
        Execute a command inside the container, optionally in detached mode.

        - bash -lc loads ~/.bashrc, so NVM is usually available.
        - Fallback ensures node/nvm works even if bashrc didn't load.
        - Safe quoting ensures commands with double quotes won't break.
        """

        # Escape double quotes inside the command
        safe_cmd = cmd.replace('"', r'\"')

        # Fallback: if node is not available, source NVM manually
        wrapped_cmd = (
            'type node >/dev/null 2>&1 || source ~/.nvm/nvm.sh; '
            f'{safe_cmd}'
        )

        docker_cmd = (
            f'docker exec -d {self.container_name} bash -lc "{wrapped_cmd}"'
            if detach
            else f'docker exec {self.container_name} bash -lc "{wrapped_cmd}"'
        )

        if detach:
            subprocess.run(docker_cmd, shell=True, check=True)
            return None
        else:
            return subprocess.check_output(
                docker_cmd, shell=True
            ).decode("utf-8", errors="ignore")

    def screenshot(self) -> str:
        """
        Takes a screenshot with ImageMagick (import), returning base64-encoded PNG.
        Requires 'import'.
        """
        # cmd = (
        #     f"export DISPLAY={self.display} && "
        #     "import -window root /tmp/screenshot.png && "
        #     "base64 /tmp/screenshot.png"
        # )
        cmd = (
            f"export DISPLAY={self.display} && "
            "import -window root png:- | base64 -w 0"
        )

        return self._exec(cmd)

    def click(self, x: int, y: int, button: str = "left") -> None:
        button_map = {"left": 1, "middle": 2, "right": 3}
        b = button_map.get(button, 1)
        self._exec(f"DISPLAY={self.display} xdotool mousemove {x} {y} click {b}")

    def right_click(self, x: int, y: int) -> None:
        self.click(x, y, button="right")

    def middle_click(self, x: int, y: int) -> None:
        self.click(x, y, button="middle")

    def long_click(self, x: int, y: int, duration: float = 1.0, button: str = "left") -> None:
        """
        Simulate a long click: press and hold the mouse button at (x, y), wait, then release.
        Default is a 1-second left-button long press.
        """
        button_map = {"left": 1, "middle": 2, "right": 3}
        b = button_map.get(button, 1)
        self._exec(f"DISPLAY={self.display} xdotool mousemove {x} {y} mousedown {b}")
        time.sleep(duration)
        self._exec(f"DISPLAY={self.display} xdotool mouseup {b}")

    def double_click(self, x: int, y: int) -> None:
        self._exec(
            f"DISPLAY={self.display} xdotool mousemove {x} {y} click --repeat 2 1"
        )

    def triple_click(self, x: int, y: int) -> None:
        """
        Simulate a triple-click at (x, y).
        Commonly used for selecting a full line or paragraph in text editors.
        """
        self._exec(
            f"DISPLAY={self.display} xdotool mousemove {x} {y} click --repeat 3 1"
        )

    def scroll(self, x: int, y: int, scroll_x: int, scroll_y: int) -> None:
        """
        For simple vertical scrolling: xdotool click 4 (scroll up) or 5 (scroll down).
        """
        self._exec(f"DISPLAY={self.display} xdotool mousemove {x} {y}")
        clicks = abs(scroll_y)
        button = 4 if scroll_y < 0 else 5
        for _ in range(clicks):
            self._exec(f"DISPLAY={self.display} xdotool click {button}")

    # def type(self, text: str) -> None:
    #     """
    #     Type the given text via xdotool, preserving spaces and quotes.
    #     """
    #     # # Escape single quotes in the user text: ' -> '\'\''
    #     # safe_text = text.replace("'", "'\\''")
    #     # # Then wrap everything in single quotes for xdotool
    #     # cmd = f"DISPLAY={self.display} xdotool type -- '{safe_text}'"
    #
    #     """
    #         Type the given text via xdotool, preserving spaces and special characters.
    #     """
    #     # 用 shlex.quote 包一层，避免 ! $ 空格 引号 被外层 shell 误解释
    #     safe_text = shlex.quote(text)
    #     cmd = f"DISPLAY={self.display} xdotool type -- {safe_text}"
    #     self._exec(cmd)

    def type(self, text: str) -> None:
        cmd = [
            "docker", "exec",
            "-i",  # ⭐ must：allow stdin
            self.container_name,
            "bash", "-lc",
            "xdotool type --clearmodifiers --delay 1 --file -"
        ]

        env = os.environ.copy()
        env["DISPLAY"] = self.display

        subprocess.run(
            cmd,
            input=text,
            text=True,
            env=env,
            check=False,
        )

    def wait(self, ms: int = 1000) -> None:
        time.sleep(ms / 1000)

    def move(self, x: int, y: int) -> None:
        self._exec(f"DISPLAY={self.display} xdotool mousemove {x} {y}")

    def keypress(self, keys: list[str]) -> None:
        mapping = {
            # Modifier and function keys
            "ENTER": "Return",
            "LEFT": "Left",
            "RIGHT": "Right",
            "UP": "Up",
            "DOWN": "Down",
            "ESC": "Escape",
            "SPACE": "space",
            "BACKSPACE": "BackSpace",
            "TAB": "Tab",
            "CTRL": "ctrl",
            "ALT": "alt",
            "SHIFT": "shift",

            # Punctuation keys (important!)
            ",": "comma",
            ".": "period",
            "/": "slash",
            ";": "semicolon",
            "'": "apostrophe",
            "[": "bracketleft",
            "]": "bracketright",
        }

        mapped_keys = [mapping.get(key.upper(), mapping.get(key, key)) for key in keys]
        combo = "+".join(mapped_keys)
        self._exec(f"DISPLAY={self.display} xdotool key {combo}")

    def drag(self, path: list[dict[str, int]]) -> None:
        if not path:
            return
        start_x = path[0]["x"]
        start_y = path[0]["y"]
        self._exec(
            f"DISPLAY={self.display} xdotool mousemove {start_x} {start_y} mousedown 1"
        )
        for point in path[1:]:
            self._exec(f"DISPLAY={self.display} xdotool mousemove {point['x']} {point['y']}")
        self._exec(f"DISPLAY={self.display} xdotool mouseup 1")

    def run_single_build(
            self,
            commit_id: str | None = None,
            build_id: str | None = None,
            app: str = "firefox",
            wait_sec: int = 60,
            poll_int: int = 1,
            gui_grace: float = 5.0  # ← Set gui_grace (e.g., 1.0) if you need an extra pause after the app process is detected, allowing the GUI a second or two to finish rendering.

    ) -> bool:
        if app == APP_NAME_FIREFOX:
            return self.run_single_build_for_firefox(commit_id=commit_id, build_id=build_id, app=app,
                                              wait_sec=wait_sec, poll_int=poll_int,
                                              gui_grace=gui_grace)
        elif app == APP_NAME_DESKTOP:
            return self.run_single_build_for_desktop(commit_id=commit_id, app=app,
                                              wait_sec=wait_sec, poll_int=poll_int, gui_grace=gui_grace)
        elif app == APP_NAME_VSCODE:
            return self.run_single_build_for_vscode(commit_id=commit_id, app=app,
                                                    wait_sec=wait_sec, poll_int=poll_int, gui_grace=gui_grace)
        elif app == APP_NAME_ZETTLR:
            return self.run_single_build_for_zettlr(commit_id=commit_id, app=app,
                                                    wait_sec=wait_sec, poll_int=poll_int, gui_grace=gui_grace)
        elif app == APP_NAME_GODOT:
            return self.run_single_build_for_godot(commit_id=commit_id, app=app,
                                                    wait_sec=wait_sec, poll_int=poll_int, gui_grace=gui_grace)

        elif app == APP_NAME_JABREF:
            return self.run_single_build_for_jabref(commit_id=commit_id, app=app,
                                                    wait_sec=wait_sec, poll_int=poll_int, gui_grace=gui_grace)


    def run_single_build_for_firefox(
            self,
            commit_id: str | None = None,
            build_id: str | None = None,
            app: str = APP_NAME_FIREFOX,  # ← 仅此一处默认值，可随意传入
            wait_sec: int = 60,
            poll_int: int = 1,
            gui_grace: float = 3.0  # ← Set gui_grace (e.g., 1.0) if you need an extra pause after the app process is detected, allowing the GUI a second or two to finish rendering.

    ) -> bool:
        if not commit_id and not build_id:
            raise ValueError("Must provide either commit_id or build_id")

        # ── small helper ────────────────────────────────────────────
        def _pgrep_pattern(proc: str) -> str:
            """
            Return '[f]irefox'‑style pattern that never matches the pgrep command itself.
            E.g. 'firefox' → '[f]irefox',  'thunderbird' → '[t]hunderbird'
            """
            return f"[{proc[0]}]{proc[1:]}" if proc else proc

        grep_pat = _pgrep_pattern(app)

        # ── 0. 尝试杀掉旧实例 ─────────────────────────────────────
        try:
            self._exec(f"pkill -f {app}")
        except subprocess.CalledProcessError:
            pass

        # ── 1. 启动 + 同步等待函数 ────────────────────────────────
        def _start_and_wait(rev: str, tag: str) -> bool:
            print(f"[INFO] Trying {tag}: {rev}")

            # ① 后台启动并回显 PID（\$! 防外层展开）
            pid_cmd = (
                f"nohup mozregression --launch {rev} --app {app} "
                f">/tmp/mozreg.log 2>&1 & echo \\$!"
            )
            moz_pid = self._exec(pid_cmd).strip()
            if not re.fullmatch(r"\d+", moz_pid):
                # print(f"[⚠️] {tag}: invalid PID '{moz_pid}'")
                return False

            # ② 轮询：成功=子进程里出现 {app}; 失败=mozregression 提前退出
            t0 = time.time()
            while time.time() - t0 < wait_sec:
                try:
                    self._exec(f"pgrep -P {moz_pid} -f '{grep_pat}'")
                    # elapsed = int(time.time() - t0)
                    # print(f"[✅] {app} appeared after {elapsed}s (parent {moz_pid})")
                    return True
                except subprocess.CalledProcessError:
                    try:
                        self._exec(f"kill -0 {moz_pid}")  # still alive?
                    except subprocess.CalledProcessError:
                        # print(f"[❌] {tag}: mozregression exited early — see /tmp/mozreg.log")
                        return False
                    time.sleep(poll_int)

            # print(f"[❌] {tag}: timeout ({wait_sec}s) — see /tmp/mozreg.log")
            return False

        # ── 2. commit_id → build_id 回退逻辑 ──────────────────────
        # ← If the code resumes 1‑2 seconds before the app’s window is fully drawn,
        #    pass gui_grace=1.0 (or any number of seconds) to wait a little longer
        #    after the GUI process is detected.
        if commit_id and _start_and_wait(commit_id, "commit_id"):
            if gui_grace:
                time.sleep(gui_grace)
            return True
        if build_id and _start_and_wait(build_id, "build_id"):
            if gui_grace:
                time.sleep(gui_grace)
            return True

        print("[❌] Both commit_id and build_id failed.")
        return False

    def _diff_ratio_b64(self, b64_a: str, b64_b: str, ignore_top: int = 0) -> float:
        """Return % of pixels that changed between two base64 PNGs."""
        img_a = Image.open(io.BytesIO(base64.b64decode(b64_a))).convert("RGB")
        img_b = Image.open(io.BytesIO(base64.b64decode(b64_b))).convert("RGB")
        arr_a, arr_b = np.array(img_a), np.array(img_b)

        # 可选：忽略顶部时钟区域
        if ignore_top > 0:
            arr_a = arr_a[ignore_top:, :, :]
            arr_b = arr_b[ignore_top:, :, :]

        diff = np.abs(arr_a.astype(int) - arr_b.astype(int))
        diff_pixels = np.count_nonzero(np.sum(diff, axis=2))  # 任何通道变化都算差异
        total_pixels = arr_a.shape[0] * arr_a.shape[1]
        return diff_pixels / total_pixels * 100.0

    def run_single_build_for_desktop(
            self,
            commit_id: str,
            app: str = APP_NAME_DESKTOP,
            repo_url="https://github.com/desktop/desktop.git",
            wait_sec: int = 120,
            poll_int: int = 1,
            gui_grace: float = 3.0,
            project_dir: str = f"/home/myuser/{APP_NAME_DESKTOP}",  # Path inside container
    ) -> bool:
        """
        Run a desktop app build (inside Docker) for a given commit ID.

        If the repo doesn't exist under project_dir, it will be cloned automatically.

        Steps:
        1. Check whether the repo exists; clone if missing.
        2. Checkout development branch and pull latest updates.
        3. Checkout the target commit.
        4. Install dependencies with Yarn.
        5. Build the app using yarn build:dev.
        6. Start the app and wait until GUI process is detected.
        """
        print(f"[INFO] Starting desktop build for commit {commit_id}")

        # ---- Step 0: Ensure repository exists ----
        try:
            repo_check = self._exec(f"test -d {project_dir}/.git && echo OK || echo MISSING").strip()
            if repo_check != "OK":
                print(f"[INFO] Repo not found under {project_dir}, cloning from {repo_url} ...")
                self._exec(f"mkdir -p {project_dir} && git clone {repo_url} {project_dir}")
            else:
                print(f"[INFO] Repository already exists in {project_dir}.")
        except subprocess.CalledProcessError as e:
            print(f"[❌] Repository check/clone failed: {e}")
            return False

        # ---- Step 1: Clean up any old app processes ----
        try:
            self._exec(f"pkill -f {app}")
        except subprocess.CalledProcessError:
            pass  # Ignore if no process found

        # ---- Step 2: Switch to the development branch and checkout commit ----
        try:
            self._exec(f"cd {project_dir} && git fetch --all")
            self._exec(f"cd {project_dir} && git checkout development && git pull")
            self._exec(f"cd {project_dir} && git checkout {commit_id}")
        except subprocess.CalledProcessError as e:
            print(f"[❌] Git checkout failed: {e}")
            return False

        # ---- Step 3: Install dependencies and build ----
        try:
            self._exec(f"cd {project_dir} && yarn")
            self._exec(f"cd {project_dir} && yarn build:dev")
            # self._exec(f"cd {project_dir} && yarn start")
        except subprocess.CalledProcessError as e:
            print(f"[❌] Build failed: {e}")
            return False

        # ---- Step 4: start app + wait for GUI diff ----
        print("[INFO] Capturing baseline screenshot before launching app ...")
        baseline_b64 = self.screenshot()

        pid_file = "/tmp/app_pid.txt"
        start_cmd = f"cd {project_dir} && nohup yarn start >/tmp/app_run.log 2>&1 & echo $! > {pid_file}"
        self._exec(start_cmd)

        print(f"[INFO] Waiting up to {wait_sec}s for {app} GUI to appear (visual diff)...")
        start_time = time.time()
        threshold_pct = 0.5  # 0.5% 像素变化阈值
        ignore_top_px = 60  # 忽略顶部 60px（时钟/系统栏）

        while time.time() - start_time < wait_sec:
            curr_b64 = self.screenshot()
            pct = self._diff_ratio_b64(baseline_b64, curr_b64, ignore_top=ignore_top_px)

            if pct >= threshold_pct:
                elapsed = int(time.time() - start_time)
                print(f"[✅] Visual change {pct:.3f}% (> {threshold_pct}%) after {elapsed}s — GUI visible.")
                print(f"[INFO] Waiting {gui_grace}s for stabilization ...")
                time.sleep(gui_grace)
                print("[✅] Desktop build and GUI launch completed successfully.")
                return True

            time.sleep(poll_int)

        print(f"[❌] Timeout ({wait_sec}s): visual diff never exceeded {threshold_pct}%.")
        return False

    def run_single_build_for_vscode(
            self,
            commit_id: str,
            app: str = APP_NAME_VSCODE,
            repo_url="https://github.com/microsoft/vscode.git",
            wait_sec: int = 120,
            poll_int: int = 1,
            gui_grace: float = 3.0,
            project_dir: str = f"/home/myuser/{APP_NAME_VSCODE}",  # Path inside container
    ) -> bool:
        """
        Run a VSCode build (inside Docker) for a given commit ID.

        If the built folder for the commit already exists, skip build steps and directly run GUI test.

        Steps:
        1. Ensure repo exists (clone if missing).
        2. Checkout main branch and target commit.
        3. Install dependencies with npm ci.
        4. Build VSCode via gulp (vscode-linux-x64).
        5. Rename output folder to include commit ID.
        6. Optionally start and check GUI via visual diff.
        """
        arch = self._exec("uname -m").strip()

        if arch == "x86_64":
            platform_target = "vscode-linux-x64"
        elif arch in ("aarch64", "arm64"):
            platform_target = "vscode-linux-arm64"
        else:
            raise RuntimeError(f"Unsupported architecture: {arch}")
        print(f"[INFO] Starting VSCode build for commit {commit_id}")
        build_dst = f"{project_dir}/../VSCode-{commit_id}"
        # build_dst = f"{project_dir}/../VSCode-linux-x64-{commit_id}"

        # ---- Step 0: Clean up any old app processes ----
        try:
            self._exec(f"pkill -f code-oss")
        except subprocess.CalledProcessError:
            pass  # Ignore if no process found

        # ---- Step 1: If already built, skip directly to Step 5 ----
        try:
            exists_check = self._exec(f"test -d {build_dst} && echo EXISTS || echo MISSING").strip()
            if exists_check == "EXISTS":
                print(f"[⚡] Build folder already exists: {build_dst}")
                print(f"[INFO] Skipping build steps, proceeding directly to GUI verification ...")
                app = "code-oss"
                return self._run_vscode_gui_check(build_dst, app, wait_sec, poll_int, gui_grace)
        except subprocess.CalledProcessError:
            pass  # if test fails, continue build

        # ---- Step 2: Ensure repository exists ----
        try:
            repo_check = self._exec(f"test -d {project_dir}/.git && echo OK || echo MISSING").strip()
            if repo_check != "OK":
                print(f"[INFO] Repo not found under {project_dir}, cloning from {repo_url} ...")
                self._exec(f"mkdir -p {project_dir} && git clone {repo_url} {project_dir}")
            else:
                print(f"[INFO] Repository already exists in {project_dir}.")
        except subprocess.CalledProcessError as e:
            print(f"[❌] Repository check/clone failed: {e}")
            return False

        # ---- Step 3: Switch branch and checkout target commit ----
        try:
            self._exec(f"cd {project_dir} && git fetch --all")
            self._exec(f"cd {project_dir} && git checkout main && git pull")
            self._exec(f"cd {project_dir} && git checkout {commit_id}")
        except subprocess.CalledProcessError as e:
            print(f"[❌] Git checkout failed: {e}")
            return False

        # ---- Step 4: Install dependencies ----
        try:
            print("[INFO] Installing dependencies with npm ci ...")
            self._exec(f"cd {project_dir} && npm ci")
        except subprocess.CalledProcessError as e:
            print(f"[❌] npm install failed: {e}")
            return False

        # ---- Step 5: Build VSCode ----
        try:
            print("[INFO] Building VSCode (npm run gulp) ...")
            # self._exec(f"cd {project_dir} && npm run gulp vscode-linux-x64")

            print(f"[INFO] Building VSCode for {platform_target} ...")
            self._exec(f"cd {project_dir} && npm run gulp {platform_target}")

            # build_src = f"{project_dir}/../VSCode-linux-x64"
            # Search inside the container for folder matching Zettlr-linux-*
            find_exec_folder_cmd = (
                "find /home/myuser -maxdepth 1 -type d -name VSCode-linux-\\*"
            )
            build_src = self._exec(find_exec_folder_cmd).strip()

            self._exec(f"mv {build_src} {build_dst}")
            print(f"[✅] Build completed and moved to: {build_dst}")
        except subprocess.CalledProcessError as e:
            print(f"[❌] VSCode build failed: {e}")
            return False

        # ---- Step 6: Start and check GUI ----
        app = "code-oss"
        return self._run_vscode_gui_check(build_dst, app, wait_sec, poll_int, gui_grace)

    def run_single_build_for_zettlr(
            self,
            commit_id: str,
            app: str = APP_NAME_ZETTLR,
            repo_url="https://github.com/Zettlr/Zettlr.git",
            wait_sec: int = 120,
            poll_int: int = 1,
            gui_grace: float = 3.0,
            project_dir: str = f"/home/myuser/{APP_NAME_ZETTLR}",  # Path inside container
    ) -> bool:
        """
        git clone https://github.com/Zettlr/Zettlr.git
        cd Zettlr
        yarn install --immutable
        cd source
        yarn install --immutable
        cd ..
        yarn package
        """
        print(f"[INFO] Starting Zettlr build for commit {commit_id}")
        build_dst = f"{project_dir}/out/Zettlr-{commit_id}"

        # ---- Step 0: Clean up any old app processes ----
        try:
            # Attempt to kill the Zettlr process (or Electron/code-oss fallback)
            self._exec(f"pkill -f Zettlr")
            # Delete the main configuration file (config.json)
            # This resets all user settings, window layout, and the workspace list.
            # self._exec("rm -f ~/.config/Zettlr/config.json")
            #
            # # Delete the Zettlr Tutorial folder
            # # When Zettlr cannot find config.json, it recreates this folder. Deleting it
            # # ensures that the folder and its contents are also restored to their initial state.
            # # Note: Use '\' to escape the space in the folder name for shell execution.
            # self._exec("rm -rf ~/Documents/Zettlr\\ Tutorial")

        except subprocess.CalledProcessError:
            pass  # Ignore if no process found

        # ---- Step 1: If already built, skip directly to GUI check ----
        try:
            exists_check = self._exec(f"test -d {build_dst} && echo EXISTS || echo MISSING").strip()
            if exists_check == "EXISTS":
                print(f"[⚡] Build folder already exists: {build_dst}")
                print(f"[INFO] Skipping build steps, proceeding directly to GUI verification ...")
                return self._run_vscode_gui_check(build_dst, app, wait_sec, poll_int, gui_grace)
        except subprocess.CalledProcessError:
            pass  # if test fails, continue build

        # ---- Step 2: Ensure repository exists ----
        try:
            repo_check = self._exec(f"test -d {project_dir}/.git && echo OK || echo MISSING").strip()
            if repo_check != "OK":
                print(f"[INFO] Repo not found under {project_dir}, cloning from {repo_url} ...")
                self._exec(f"mkdir -p {project_dir} && git clone {repo_url} {project_dir}")
            else:
                print(f"[INFO] Repository already exists in {project_dir}.")
        except subprocess.CalledProcessError as e:
            print(f"[❌] Repository check/clone failed: {e}")
            return False

        # ---- Step 3: Switch branch and checkout target commit ----
        try:
            self._exec(f"cd {project_dir} && git fetch --all")
            self._exec(f"cd {project_dir} && git checkout develop && git pull")
            self._exec(f"cd {project_dir} && git checkout {commit_id}")
        except subprocess.CalledProcessError as e:
            print(f"[❌] Git checkout failed: {e}")
            return False

        # ---- Step 4: Install dependencies (Using yarn install --immutable) ----
        try:
            print("[INFO] Installing root dependencies with yarn install --immutable ...")
            # 1. Install root dependencies
            self._exec(f"cd {project_dir} && yarn install --immutable")

            # print("[INFO] Installing source dependencies with yarn install --immutable ...")
            # # 2. Install dependencies for the 'source' directory
            # self._exec(f"cd {project_dir}/source && yarn install --immutable")
            #
            # # 3. CD back to project root for the package step
            # self._exec(f"cd {project_dir}")

        except subprocess.CalledProcessError as e:
            print(f"[❌] yarn install failed: {e}")
            return False

        # ---- Step 5: Build Zettlr (Using yarn package) ----
        try:
            print("[INFO] Building Zettlr (yarn package) ...")
            self._exec(f"cd {project_dir} && yarn package")

            # Search inside the container for folder matching Zettlr-linux-*
            find_exec_folder_cmd = (
                f"bash -lc 'find {project_dir}/out -type d -maxdepth 1 -name \"Zettlr-linux-*\"'"
            )
            build_src = self._exec(find_exec_folder_cmd).strip()

            # The final destination path was defined at the start of the function.
            self._exec(f"mv {build_src} {build_dst}")
            print(f"[✅] Build completed and moved from {build_src} to: {build_dst}")
        except subprocess.CalledProcessError as e:
            print(f"[❌] Zettlr build failed: {e}")
            return False

        # ---- Step 6: Start and check GUI ----
        return self._run_vscode_gui_check(build_dst, app, wait_sec, poll_int, gui_grace)

    def run_single_build_for_godot(
            self,
            commit_id: str,
            app: str = APP_NAME_GODOT,
            repo_url="https://github.com/godotengine/godot.git",
            wait_sec: int = 120,
            poll_int: int = 1,
            gui_grace: float = 3.0,
            project_dir: str = f"/home/myuser/{APP_NAME_GODOT}",  # Path inside container
    ) -> bool:
        """
        git clone https://github.com/godotengine/godot.git
        cd godot
        cd bin
        scons platform=linuxbsd
        """
        print(f"[INFO] Starting {app} build for commit {commit_id}")
        build_dst = f"{project_dir}/{app}-{commit_id}"

        # ---- Step 0: Clean up any old app processes ----
        try:
            # Kill the running process
            self._exec(f"pkill -f {app}")

            # Remove Godot config folder
            # Clear the specific project list file (project_list.cfg) and the 'projects' directory (where Godot 4+ might store project data).
            # clear_config_docker_cmd = (
            #     f"docker exec {self.container_name} bash -c "
            #     "'rm -rf /home/myuser/.local/share/godot'"
            # )
            # subprocess.check_output(clear_config_docker_cmd, shell=True)
            #
            # # After running these commands, you must restart the Godot Project Manager
            # # to see the cleared list.
            # docker_cmd = (
            #     f"docker exec {self.container_name} bash -c '"
            #     'find /home/myuser -type f -name "project.godot" '
            #     '-not -path "/home/myuser/godot/*" '
            #     '-not -path "/home/myuser/.local/share/Trash/*" '
            #     '-print0 | while IFS= read -r -d "" file; do '
            #     'dir=$(dirname "$file"); '
            #     'echo "--- Deleting: $dir ---"; '
            #     'rm -rf "$dir"; '
            #     'done'
            #     "'"
            # )
            # subprocess.check_output(docker_cmd, shell=True).decode("utf-8", errors="ignore")

        except subprocess.CalledProcessError:
            pass  # Ignore if no process found

        # ---- Step 1: If already built, skip directly to GUI check ----
        try:
            exists_check = self._exec(f"test -d {build_dst} && echo EXISTS || echo MISSING").strip()
            if exists_check == "EXISTS":
                print(f"[⚡] Build folder already exists: {build_dst}")
                print(f"[INFO] Skipping build steps, proceeding directly to GUI verification ...")
                return self._run_vscode_gui_check(build_dst, app, wait_sec, poll_int, gui_grace)
        except subprocess.CalledProcessError:
            pass  # if test fails, continue build

        # ---- Step 2: Ensure repository exists ----
        try:
            repo_check = self._exec(f"test -d {project_dir}/.git && echo OK || echo MISSING").strip()
            if repo_check != "OK":
                print(f"[INFO] Repo not found under {project_dir}, cloning from {repo_url} ...")
                self._exec(f"mkdir -p {project_dir} && git clone {repo_url} {project_dir}")
            else:
                print(f"[INFO] Repository already exists in {project_dir}.")
        except subprocess.CalledProcessError as e:
            print(f"[❌] Repository check/clone failed: {e}")
            return False

        # ---- Step 3: Switch branch and checkout target commit ----
        try:
            self._exec(f"cd {project_dir} && git fetch --all")
            self._exec(f"cd {project_dir} && git checkout master && git pull")
            self._exec(f"cd {project_dir} && git checkout {commit_id}")
        except subprocess.CalledProcessError as e:
            print(f"[❌] Git checkout failed: {e}")
            return False

        # ---- Step 4: Compiling
        try:
            print("[INFO] Compiling ...")
            # 1. Install root dependencies
            self._exec(f"cd {project_dir} && scons platform=linuxbsd")

        except subprocess.CalledProcessError as e:
            print(f"[❌] scons platform=linuxbsd failed: {e}")
            return False

        # ---- Step 5: Change name ----
        try:
            find_exec_file_cmd = (
                f"find {project_dir}/bin -maxdepth 1 -type f -name 'godot.linuxbsd.editor.*' -print -quit"
            )
            build_src = self._exec(find_exec_file_cmd).strip()
            self._exec(f"mv {build_src} {project_dir}/bin/godot")
            self._exec(f"mv {project_dir}/bin {build_dst}")
            # The final destination path was defined at the start of the function.
            # self._exec(f"mv {build_src} {build_dst}")
            print(f"[✅] Build completed and moved from {build_src} to: {build_dst}")
        except subprocess.CalledProcessError as e:
            print(f"[❌] godot open failed: {e}")
            return False

        # ---- Step 6: Start and check GUI ----
        return self._run_vscode_gui_check(build_dst, app, wait_sec, poll_int, gui_grace)

    def run_single_build_for_jabref(
            self,
            commit_id: str,
            app: str = APP_NAME_JABREF,
            repo_url="https://github.com/JabRef/jabref.git",
            wait_sec: int = 180,
            poll_int: int = 1,
            gui_grace: float = 3.0,
            project_dir: str = f"/home/myuser/{APP_NAME_JABREF}",  # Path inside container,
            main_branch: str = "main"
    ) -> bool:
        """
        git clone --recurse-submodules (--depth=10) https://github.com/JabRef/jabref
        cd jabref
        ./gradlew :jabgui:jpackage
        """
        print(f"[INFO] Starting {app} build for commit {commit_id}")
        base_path = "jabgui/build/packages"
        build_dst = f"{project_dir}/{base_path}/{app}-{commit_id}"

        # ---- Step 0: Clean up any old app processes ----
        try:
            # Kill the running process
            self._exec(f"pkill -f JabRef")

            # Remove config folder
            # # Clear the specific project list file
            # clear_config_docker_cmd = (
            #     f"docker exec {self.container_name} bash -c "
            #     "'rm -rf ~/.java/.userPrefs/org/jabref'"
            # )
            # subprocess.check_output(clear_config_docker_cmd, shell=True)

        except subprocess.CalledProcessError:
            pass  # Ignore if no process found

        # ---- Step 1: If already built, skip directly to GUI check ----
        try:
            exists_check = self._exec(f"test -d {build_dst} && echo EXISTS || echo MISSING").strip()
            if exists_check == "EXISTS":
                print(f"[⚡] Build folder already exists: {build_dst}")
                print(f"[INFO] Skipping build steps, proceeding directly to GUI verification ...")
                app = APP_OWNER_NAME_JABREF
                build_dst = f"{build_dst}/{app}/bin"
                return self._run_vscode_gui_check(build_dst, app, wait_sec, poll_int, gui_grace)
        except subprocess.CalledProcessError:
            pass  # if test fails, continue build

        # ---- Step 2: Ensure repository exists ----
        try:
            repo_check = self._exec(f"test -d {project_dir}/.git && echo OK || echo MISSING").strip()
            if repo_check != "OK":
                print(f"[INFO] Repo not found under {project_dir}, cloning from {repo_url} ...")
                self._exec(f"mkdir -p {project_dir} && git clone --recurse-submodules {repo_url} {project_dir}")
            else:
                print(f"[INFO] Repository already exists in {project_dir}.")
        except subprocess.CalledProcessError as e:
            print(f"[❌] Repository check/clone failed: {e}")
            return False

        # ---- Step 3: Switch branch and checkout target commit ----
        try:
            self._exec(f"cd {project_dir} && git fetch --all")
            self._exec(f"cd {project_dir} && git checkout {main_branch} && git pull")
            self._exec(f"cd {project_dir} && git checkout {commit_id}")
        except subprocess.CalledProcessError as e:
            print(f"[❌] Git checkout failed: {e}")
            return False

        # ---- Step 4: Compiling
        try:
            print("[INFO] Compiling ...")
            # 1. Install root dependencies
            self._exec(f"cd {project_dir} && ./gradlew :jabgui:jpackage")

        except subprocess.CalledProcessError as e:
            print(f"[❌] {e}")
            return False

        # ---- Step 5: Change name ----
        try:
            build_src = f"{project_dir}/{base_path}/ubuntu-22.04"
            self._exec(f"mv {build_src} {build_dst}")
            print(f"[✅] Build completed and moved from {build_src} to: {build_dst}")
        except subprocess.CalledProcessError as e:
            print(f"[❌] open failed: {e}")
            return False

        # ---- Step 6: Start and check GUI ----
        app = APP_OWNER_NAME_JABREF
        build_dst = f"{build_dst}/{app}/bin"
        return self._run_vscode_gui_check(build_dst, app, wait_sec, poll_int, gui_grace)

    # 🧩 Helper function
    def _run_vscode_gui_check(self, build_dst: str, app: str, wait_sec: int, poll_int: int, gui_grace: float) -> bool:
        """Run visual diff to verify GUI startup."""
        print("[INFO] Capturing baseline screenshot before launch ...")
        baseline_b64 = self.screenshot()

        pid_file = "/tmp/app_pid.txt"

        start_cmd = f"cd {build_dst} && nohup ./{app} >/tmp/app_run.log 2>&1 & echo $! > {pid_file}"
        self._exec(start_cmd)

        print(f"[INFO] Waiting up to {wait_sec}s for {app} GUI to appear (visual diff)...")
        start_time = time.time()
        threshold_pct = 0.5
        ignore_top_px = 60

        while time.time() - start_time < wait_sec:
            curr_b64 = self.screenshot()
            pct = self._diff_ratio_b64(baseline_b64, curr_b64, ignore_top=ignore_top_px)

            if pct >= threshold_pct:
                elapsed = int(time.time() - start_time)
                print(f"[✅] Visual change {pct:.3f}% (> {threshold_pct}%) after {elapsed}s — GUI visible.")
                print(f"[INFO] Waiting {gui_grace}s for stabilization ...")
                time.sleep(gui_grace)
                print(f"[✅] {app} build and GUI launch completed successfully.")
                return True

            time.sleep(poll_int)

        print(f"[❌] Timeout ({wait_sec}s): visual diff never exceeded {threshold_pct}%.")
        return False





