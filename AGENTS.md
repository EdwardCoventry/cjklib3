# Agent Notes for cjklib3

## Purpose

This fork tracks practical compatibility fixes for modern Python tooling while keeping cjklib runtime behavior stable for downstream projects (including kiku).

## Preferred local workflow

From repo root:

```powershell
python -m compileall .
python -c "from cjklib import characterlookup; cjk=characterlookup.CharacterLookup('J'); print(type(cjk).__name__)"
```

For broad import validation:

```powershell
python -c "import pkgutil, importlib, cjklib; [importlib.import_module(m.name) for m in pkgutil.walk_packages(cjklib.__path__, prefix='cjklib.')]"
```

## Compatibility expectations

- Keep SQLAlchemy compatibility logic inside this repo (not downstream monkeypatches).
- Favor small, targeted patches for Python-version compatibility.
- Preserve default DB discovery behavior on Linux/macOS and Windows.

## Notes for downstream consumers

- kiku uses this repo as editable local dependency during development.
- Changes here should be validated with both direct cjklib imports and downstream import flows.
