from tracker.adapters.base import Adapter
from tracker.adapters.generic_pdf import GenericPdfResultsAdapter
from tracker.adapters.swim_ontario import SwimOntarioAdapter


def build_adapters() -> list[Adapter]:
    return [SwimOntarioAdapter(), GenericPdfResultsAdapter()]
