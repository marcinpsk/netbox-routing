import ast
import importlib
import re
from pathlib import Path

from django.apps import apps
from django.test import SimpleTestCase

__all__ = ('MigrationDependencyTestCase',)

_MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / 'migrations'


def _declared_dependencies():
    """Yield (migration_file, app_label, node_name) for every cross-app dependency we declare."""
    for path in sorted(_MIGRATIONS_DIR.glob('0*.py')):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            if not any(getattr(t, 'id', None) == 'dependencies' for t in node.targets):
                continue
            for element in getattr(node.value, 'elts', []):
                try:
                    app_label, name = ast.literal_eval(element)
                except (ValueError, TypeError):
                    continue  # swappable_dependency() and friends resolve at runtime
                if app_label != 'netbox_routing':
                    yield path.name, app_label, name


def _migration_names(app_label):
    """The migration names present on disk for *app_label*, or None if the app has none.

    Resolved through the app registry: an app's label is not its module path
    (`contenttypes` lives at `django.contrib.contenttypes`).
    """
    try:
        app_config = apps.get_app_config(app_label)
    except LookupError:
        return None
    try:
        package = importlib.import_module(f'{app_config.name}.migrations')
    except ModuleNotFoundError:
        return None
    directory = Path(package.__file__).parent
    return {p.stem for p in directory.glob('*.py') if p.stem != '__init__'}


class MigrationDependencyTestCase(SimpleTestCase):
    """Guard against depending on core migrations that no longer exist.

    NetBox squashes its core migrations. `migrate` still resolves a dependency on a
    squashed-away node through the squash's `replaces`, so the suite, test-database
    creation and `makemigrations --check` all stay green — but any caller that builds
    the graph with `replace_migrations=False`, `sqlmigrate` among them, fails with
    NodeNotFoundError. The reference also breaks outright once a squash is itself
    squashed and the `replaces` entry goes away.
    """

    def test_no_dependency_on_a_missing_migration(self):
        # Reported together rather than raised one at a time: the graph error names only the
        # first dangling node, so fixing it just reveals the next.
        missing = []
        for migration, app_label, name in _declared_dependencies():
            if name.startswith('__'):
                continue  # __first__ / __latest__ are resolved by Django, not by filename
            names = _migration_names(app_label)
            if names is None:
                missing.append(f'{migration}: app {app_label!r} has no migrations package')
            elif name not in names:
                missing.append(f'{migration}: {app_label}.{name} is not on disk')

        self.assertEqual(missing, [], 'Dependencies on migrations that do not exist:\n' + '\n'.join(missing))

    def test_initial_still_orders_after_the_apps_it_references(self):
        # The FK targets in 0001_initial are created by those apps, so dropping the
        # dependencies (the right fix elsewhere) would leave this migration unordered.
        initial = (_MIGRATIONS_DIR / '0001_initial.py').read_text()
        referenced = {target.split('.')[0] for target in re.findall(r"to='([a-z]+\.\w+)'", initial)}
        depended_on = {
            app for migration, app, _ in _declared_dependencies() if migration == '0001_initial.py'
        }

        for app_label in referenced - {'netbox_routing'}:
            self.assertIn(
                app_label,
                depended_on,
                f'0001_initial has foreign keys into {app_label} but does not depend on it',
            )
