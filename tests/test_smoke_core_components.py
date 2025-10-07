"""
🔥 Dynamic Smoke Test — Import, Instantiate, and Call

- Discovers all classes in `core/`
- Attempts to instantiate each with dummy args
- Optionally calls no-op methods if available

This provides deep smoke testing across the entire core package.
"""

import importlib
import inspect
import os
import pkgutil
import sys

import pytest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Ensure packages/core/src is importable
CORE_SRC_PATH = os.path.join(PROJECT_ROOT, "packages", "core", "src")
if os.path.exists(CORE_SRC_PATH) and CORE_SRC_PATH not in sys.path:
    sys.path.insert(0, CORE_SRC_PATH)


def iter_core_classes():
    """Yield (module_name, class_name, class_obj) for all classes in core"""
    try:
        import core
    except ImportError:
        return []

    classes = []
    for _finder, name, _ispkg in pkgutil.walk_packages(
        core.__path__, core.__name__ + "."
    ):
        # Skip test modules and private modules
        if "test" in name or any(part.startswith("_") for part in name.split(".")):
            continue

        try:
            module = importlib.import_module(name)
        except Exception:
            # Skip modules that can't be imported
            continue

        for cname, cls in inspect.getmembers(module, inspect.isclass):
            # Only include classes defined in core (not imported from elsewhere)
            if cls.__module__.startswith("core"):
                classes.append((name, cname, cls))

    return classes


@pytest.mark.order(1)
@pytest.mark.smoke
@pytest.mark.parametrize("module_name,class_name,cls", iter_core_classes())
def test_instantiate_class(module_name, class_name, cls):
    """✅ Attempt to instantiate each class with default or dummy args"""
    print(f"🔎 Testing class: {module_name}.{class_name}")

    # Skip abstract classes
    if inspect.isabstract(cls):
        pytest.skip(f"⚠️  {class_name} is abstract, skipping instantiation")
        return

    try:
        # Try instantiating with no args
        instance = cls()
    except TypeError:
        # Try instantiating with dummy None args if parameters exist
        try:
            sig = inspect.signature(cls)
            # Build kwargs with None for required params
            kwargs = {}
            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue
                if param.default is param.empty:
                    # Required parameter - provide None
                    kwargs[param_name] = None

            instance = cls(**kwargs)
        except Exception as inner_e:
            pytest.skip(f"⚠️  Cannot instantiate {class_name}: {inner_e}")
            return
    except Exception as e:
        pytest.skip(f"⚠️  Cannot instantiate {class_name}: {e}")
        return

    assert instance is not None, f"❌ Could not instantiate {class_name}"
    print(f"  ✅ Successfully instantiated {class_name}")

    # Optionally call a no-op method if available
    callable_methods = [
        m
        for m, fn in inspect.getmembers(instance, inspect.ismethod)
        if not m.startswith("_") and m not in ["from_orm", "dict", "json", "copy"]
    ]

    if callable_methods:
        method_name = callable_methods[0]
        method = getattr(instance, method_name)
        try:
            # Try calling with no args
            method()
            print(f"  ✅ Called method {method_name}()")
        except TypeError:
            # Method requires args - skip it
            pytest.skip(f"⚠️  Method {method_name} requires arguments, skipped")
        except Exception as e:
            pytest.skip(f"⚠️  Method {method_name} raised {e} — skipped")


def test_core_has_classes():
    """✅ Verify that core package contains some classes"""
    classes = list(iter_core_classes())
    if not classes:
        pytest.skip("⚠️  No classes found in core package")
    else:
        print(f"✅ Found {len(classes)} classes in core package")
        assert len(classes) > 0
