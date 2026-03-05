from importlib import import_module

modules = []
for name in ["workflow", "execution", "tools", "files", "nodes"]:
    try:
        mod = import_module(f"app.api.{name}")
        globals()[name] = mod
        modules.append(name)
    except Exception:
        pass

__all__ = modules
