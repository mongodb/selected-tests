"""Utilities for dependency injection support."""
import inspect

from typing import Any

import inject


def remap_for_injection(func):
    """Remaps a function such that it takes configured dependencies from inject regardless of order."""
    specs = inspect.getfullargspec(func)
    arg_map = {arg_name: specs.annotations.get(arg_name, Any) for arg_name in specs.args}

    def partial(*args, **kwargs):
        args = list(reversed(args))
        new_args = []
        injector = inject.get_injector_or_die()
        for arg_name, anno in arg_map.items():
            if anno in injector._bindings:
                new_args.append(injector.get_instance(anno))
            else:
                new_args.append(args.pop())
        return func(*new_args, **kwargs)

    return partial
