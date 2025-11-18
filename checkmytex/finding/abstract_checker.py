import abc
import subprocess
import typing

from checkmytex.latex_document import LatexDocument

from .problem import Problem


class Checker(abc.ABC):
    def __init__(self, log: typing.Callable = print):
        self.log = log

    @abc.abstractmethod
    def check(self, document: LatexDocument) -> typing.Iterable[Problem]:
        pass

    @abc.abstractmethod
    def is_available(self) -> bool:
        pass

    def _run(
        self, cmd: str, input: str | None = None, timeout: float = 300
    ) -> tuple[str, str, int]:
        """
        Execute a shell command.

        NOTE: This method uses shell=True which can be a security risk if cmd
        contains untrusted input. All commands should be constructed from
        trusted sources only. Future work should migrate to list-based commands.

        Args:
            cmd: Command string to execute
            input: Optional stdin input

        Returns:
            Tuple of (stdout, stderr, exit_code)

        Raises:
            subprocess.SubprocessError: If command execution fails
            UnicodeDecodeError: If output cannot be decoded as UTF-8
        """
        self.log("EXEC:", cmd)
        try:
            with subprocess.Popen(
                cmd,
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # Capture stderr properly
            ) as proc:
                input_bytes = None
                if input:
                    input_bytes = str(input).replace("\t", " ").encode("utf-8")

                try:
                    out, err = proc.communicate(input=input_bytes, timeout=timeout)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    out, err = proc.communicate()
                    msg = f"Command timed out after {timeout} seconds: {cmd}"
                    raise subprocess.SubprocessError(msg) from None

                return (
                    out.decode("utf-8") if out else "",
                    err.decode("utf-8") if err else "",
                    proc.returncode,
                )
        except (OSError, ValueError) as e:
            msg = f"Failed to execute command '{cmd}': {e}"
            raise subprocess.SubprocessError(msg) from e

    def needs_detex(self):
        return False

    def __str__(self):
        return self.__class__.__name__

    def installation_guide(self) -> str:
        return "No installation guide available yet."
