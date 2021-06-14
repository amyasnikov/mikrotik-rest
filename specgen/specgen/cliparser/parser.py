import re
from dataclasses import dataclass
from typing import Callable, Iterator, Dict, List, Set


@dataclass
class Parser:

    regexp: re.Pattern
    find_func: Callable[[str, re.Pattern], Iterator[Dict[str, str]]]

    def finditer(self, output_str: str) -> Iterator[Dict[str, str]]:
        yield from self.find_func(output_str, self.regexp)

    @staticmethod
    def find_leaves(output_str: str, regexp: re.Pattern) -> Iterator[Dict[str, str]]:
        def trim_n_strip(finds: List[str]) -> Set[str]:
            bad_chars = ('\x1b[m', '\r')
            items = set()
            for entry in finds:
                for bad_char in bad_chars:
                    entry = entry.replace(bad_char, '')
                entry = entry.replace('\n', ' ')

                items.update(entry.split(' '))
            try:
                items.remove('')
            except KeyError:
                pass
            return items

        search_res = regexp.findall(output_str)
        yield from map(lambda leaf_name: {'name': leaf_name},
                       trim_n_strip(search_res))

    @staticmethod
    def find_params(output_str: str, regexp: re.Pattern) -> Iterator[Dict[str, str]]:
        def get_clinode(match: re.Match) -> Dict[str, str]:
            name = match.group(1)
            if name == '<numbers>':
                name = '.id'
            return {'name': name, 'description': match.group(2)}

        bad_chars = ('\x1b[m\x1b[33m', '\x1b[m\x1b[32m', '\x1b[m')
        for char in bad_chars:
            output_str = output_str.replace(char, '')
        yield from map(get_clinode, regexp.finditer(output_str))

    @staticmethod
    def find_param_type(output_str: str, regexp: re.Pattern) -> Iterator[Dict[str, str]]:
        types = {
            'yes\x1b[m\x1b[33m | \x1b[mno' : 'boolean',
            '(integer number)' : 'integer'
        }
        if output_str.count('::=') == 1:
            param_line = regexp.findall(output_str)[0]
            for type_ in types:
                if type_ in param_line:
                    yield {'param_type': types[type_]}
                    break
            else:
                yield {'param_type': ''}
        else:
            yield {'param_type': ''}


