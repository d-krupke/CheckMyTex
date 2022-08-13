import os
import re
import typing

import flachtex
from checkmytex.latex_document.latex_document import Detex
from flachtex import FileFinder, TraceableString
from flachtex.command_substitution import NewCommandSubstitution, find_new_commands
from flachtex.rules import TodonotesRule, ChangesRule
from flachtex.rules.skip_rules import RegexSkipRule
from flachtex.utils import Range

from checkmytex import LatexDocument

class _IgnoreRule(RegexSkipRule):
    """
    A skip rule for flachtex to remove parts delimited by `%%PAUSE-CHECKING`
    and `%%CONTINUE-CHECKING`.
    """

    def __init__(self):
        super().__init__(
            r"((^\s*%%PAUSE-CHECKING)"
            r"(?P<skipped_part>.*?)"
            r"(^\s*%%CONTINUE-CHECKING))"
        )

    def determine_skip(self, match: re.Match):
        span_to_be_skipped = Range(
            match.start("skipped_part"), match.end("skipped_part")
        )
        return span_to_be_skipped

class LatexParser:
    def __init__(
            self,
            file_finder: typing.Optional[FileFinder] = None,
            yalafi_opts: typing.Optional[typing.Dict] = None,
    ):
        self._ff = file_finder
        self.file_finder = FileFinder() if not file_finder else file_finder
        self._yalafi_opts = yalafi_opts

    def newcommand(self, name: int, num_parameters: int, definition: str):
        pass

    def _get_source(
            self, path: str
    ) -> typing.Tuple[TraceableString, typing.Dict[str, typing.Dict]]:
        preprocessor = flachtex.Preprocessor(os.path.dirname(path))
        preprocessor.file_finder = self.file_finder
        preprocessor.skip_rules.append(TodonotesRule())
        preprocessor.skip_rules.append(_IgnoreRule())
        preprocessor.substitution_rules.append(ChangesRule())
        preprocessor.substitution_rules.append(ChangesRule(True))
        preprocessor.substitution_rules.append(
            self._find_command_definitions(path, self.file_finder)
        )
        flat_source = preprocessor.expand_file(path)
        return flachtex.remove_comments(flat_source), preprocessor.structure

    def _find_command_definitions(self, path, file_finder) -> NewCommandSubstitution:
        """
        Parse the document once independently to extract new commands.
        :param path:
        :return:
        """
        preprocessor = flachtex.Preprocessor(os.path.dirname(path))
        if file_finder:
            preprocessor.file_finder = file_finder
        doc = preprocessor.expand_file(path)
        cmds = find_new_commands(doc)
        ncs = NewCommandSubstitution()
        for cmd in cmds:
            ncs.new_command(cmd)
        return ncs

    def parse(
            self, path: str, project_root: typing.Optional[str] = None
    ) -> LatexDocument:
        if project_root:
            self.file_finder.set_root(project_root)
        else:
            self.file_finder.set_root(os.path.dirname(path))
        source, files = self._get_source(path)
        return LatexDocument(source, files, Detex(str(source),self._yalafi_opts))
