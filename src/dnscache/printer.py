from typing import Callable, Generator

from dnscache.enums import Output
from dnscache.mappings import Mappings


def print(mappings: Mappings, outputs: tuple[Output, ...]) -> str:
    """Return the mappings object as a string based on the desired output.

    Args:
        mappings: The mappings object.
        output: The output to print.

    Returns:
        str: the output string.

    """
    funcs: Generator[Callable[[Mappings], str]] = (
        OUTPUT_VS_FUNC[output] for output in outputs
    )
    return "\n".join(func(mappings) for func in funcs)


def _print_ips(mappings: Mappings) -> str:
    return "\n".join(mappings.ips)


def _print_domains(mappings: Mappings) -> str:
    return str(mappings.domains)


def _print_ipset(mappings: Mappings) -> str:
    return ""


OUTPUT_VS_FUNC: dict[Output, Callable[[Mappings], str]] = {
    Output.IP: _print_ips,
    Output.DOMAIN: _print_domains,
    Output.MAPPING: str,
    Output.IPSET: _print_ipset,
}
