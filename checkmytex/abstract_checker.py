import abc
import subprocess
import typing

from .latex_document import LatexDocument
from .problem import Problem


class Checker(abc.ABC):
    @abc.abstractmethod
    def check(self, document: LatexDocument) -> typing.Iterable[Problem]:
        pass

    @abc.abstractmethod
    def is_available(self) -> bool:
        pass

    def _run(self, cmd, input=None) -> typing.Tuple[str, str, int]:
        with subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE) as proc:
            if input:
                out, err = proc.communicate(str(input).replace("\t", " ").encode())
            else:
                out, err = proc.communicate()
            return out.decode() if out else None, err.decode() if err else None, proc.wait()

    def needs_detex(self):
        return False