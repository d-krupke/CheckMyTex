import typing

import proselint.tools

from checkmytex.latex_document import LatexDocument

from .abstract_checker import Checker
from .problem import Problem

_proselint_config = {
    "max_errors": 5000,
    "checks": {
        "airlinese.misc": True,
        "annotations.misc": True,
        "archaism.misc": True,
        "cliches.hell": True,
        "cliches.misc": True,
        "consistency.spacing": False,  # LaTeX does not care about spacing.
        "consistency.spelling": True,
        "corporate_speak.misc": True,
        "cursing.filth": True,
        "cursing.nfl": False,
        "cursing.nword": True,
        "dates_times.am_pm": True,
        "dates_times.dates": True,
        "hedging.misc": True,
        "hyperbole.misc": True,
        "jargon.misc": True,
        "lexical_illusions.misc": True,
        "lgbtq.offensive_terms": True,
        "lgbtq.terms": True,
        "links.broken": False,
        "malapropisms.misc": True,
        "misc.apologizing": True,
        "misc.back_formations": True,
        "misc.bureaucratese": True,
        "misc.but": True,
        "misc.capitalization": True,
        "misc.chatspeak": True,
        "misc.commercialese": True,
        "misc.composition": True,
        "misc.currency": True,
        "misc.debased": True,
        "misc.false_plurals": True,
        "misc.illogic": True,
        "misc.inferior_superior": True,
        "misc.institution_name": True,
        "misc.latin": True,
        "misc.many_a": True,
        "misc.metaconcepts": True,
        "misc.metadiscourse": True,
        "misc.narcissism": True,
        "misc.not_guilty": True,
        "misc.phrasal_adjectives": True,
        "misc.preferred_forms": True,
        "misc.pretension": True,
        "misc.professions": True,
        "misc.punctuation": True,
        "misc.scare_quotes": True,
        "misc.suddenly": True,
        "misc.tense_present": True,
        "misc.waxed": True,
        "misc.whence": True,
        "mixed_metaphors.misc": True,
        "mondegreens.misc": True,
        "needless_variants.misc": True,
        "nonwords.misc": True,
        "oxymorons.misc": True,
        "psychology.misc": True,
        "redundancy.misc": True,
        "redundancy.ras_syndrome": True,
        "skunked_terms.misc": True,
        "spelling.able_atable": True,
        "spelling.able_ible": True,
        "spelling.athletes": True,
        "spelling.em_im_en_in": True,
        "spelling.er_or": True,
        "spelling.in_un": True,
        "spelling.misc": True,
        "security.credit_card": True,
        "security.password": True,
        "sexism.misc": True,
        "terms.animal_adjectives": True,
        "terms.denizen_labels": True,
        "terms.eponymous_adjectives": True,
        "terms.venery": True,
        "typography.diacritical_marks": True,
        "typography.exclamation": True,
        "typography.symbols": True,
        "uncomparables.misc": True,
        "weasel_words.misc": True,
        "weasel_words.very": True,
    },
}


class Proselint(Checker):
    def check(self, document: LatexDocument) -> typing.Iterable[Problem]:
        self.log("Running proselint...")
        text = document.get_text()
        suggestions = proselint.tools.lint(text, config=_proselint_config)
        for suggestion in suggestions:
            rule = suggestion[0]
            message = suggestion[1]
            origin = document.get_simplified_origin_of_text(
                suggestion[4], suggestion[4] + suggestion[6]
            )
            context = document.get_source_context(origin)
            severity = suggestion[7]
            replacements = suggestion[8]
            yield Problem(
                origin,
                f"{severity}: {message} Suggestion: {replacements}",
                context=context,
                long_id=f"{rule}: {context}",
                rule=rule,
                tool="Proselint",
            )

    def is_available(self) -> bool:
        return True
