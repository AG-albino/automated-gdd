import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE_PATH = Path(__file__).with_name('gdd.py')
if MODULE_PATH.exists():
    spec = importlib.util.spec_from_file_location('gdd', MODULE_PATH)
    gdd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gdd)
else:
    gdd = None


class GDDTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(gdd, 'The GDD helper has not been implemented')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'design' / 'experiments').mkdir(parents=True)
        self.data = {
            'schema_version': 1, 'revision': 1,
            'project': {'title': 'Test game', 'phase': 'prototype'},
            'workflow': {'steward': 'main', 'numeric_mode': 'mirrored'},
            'systems': [{'id': 'player', 'summary': 'Move and survive',
                         'status': 'accepted', 'rules': [], 'depends_on': []}],
            'parameters': {'player.health': {
                'system': 'player', 'value': 100, 'unit': 'hp',
                'status': 'accepted', 'source': 'User request',
                'depends_on': [], 'bindings': [
                    {'path': 'data/player.json', 'format': 'json',
                     'pointer': '/max_health'}]}},
            'open_questions': [], 'decisions': [],
            'coverage': {'status': 'partial', 'reviewed_paths': [], 'unregistered': []}
        }
        self.engine(100)

    def engine(self, value):
        (self.root / 'data').mkdir(exist_ok=True)
        (self.root / 'data' / 'player.json').write_text(
            json.dumps({'max_health': value}), encoding='utf-8')

    def errors(self, data=None, experiment=None, strict=False):
        return gdd.validate(data or self.data, self.root, experiment, strict)[0]

    def experiment(self, **updates):
        data = {'id': 'exp-health', 'base_revision': 1, 'status': 'active',
                'hypothesis': 'Less health raises tension', 'affects': ['player'],
                'base_values': {'player.health': 100},
                'overrides': {'player.health': 80}, 'new_parameters': {},
                'systems': [], 'trial_rules': [], 'observations': [],
                'decision': {'outcome': 'undecided', 'source': None}}
        data.update(updates)
        (self.root / 'design' / 'experiments' / 'exp-health.json').write_text(
            json.dumps(data), encoding='utf-8')
        return data

    def test_valid_binding_and_input_is_not_mutated(self):
        original = copy.deepcopy(self.data)
        self.assertEqual([], self.errors())
        self.assertEqual(original, self.data)

    def test_numeric_mismatch_is_a_failure(self):
        self.engine(80)
        self.assertTrue(any('player.health' in e and 'mismatch' in e for e in self.errors()))

    def test_unknown_units_pending_bindings_and_partial_coverage_fail_strict(self):
        p = self.data['parameters']['player.health']
        p['value'] = None
        p['bindings'] = []
        self.assertEqual([], self.errors())
        self.assertTrue(self.errors(strict=True))

    def test_dependency_cycles_and_missing_references_are_rejected(self):
        self.data['systems'][0]['depends_on'] = ['missing']
        self.assertTrue(any('missing' in e for e in self.errors()))
        self.data['systems'][0]['depends_on'] = []
        self.data['parameters']['player.health']['depends_on'] = ['player.health']
        self.assertTrue(any('cycle' in e for e in self.errors()))

    def test_explicit_experiment_overrides_engine_check_without_adoption(self):
        self.experiment()
        self.engine(80)
        before = copy.deepcopy(self.data)
        self.assertTrue(self.errors())
        self.assertEqual([], self.errors(experiment='exp-health'))
        self.assertEqual(before, self.data)

    def test_changed_experiment_baseline_is_rejected(self):
        self.experiment()
        self.data['parameters']['player.health']['value'] = 90
        self.assertTrue(any('baseline' in e for e in self.errors(experiment='exp-health')))

    def test_unselected_stale_trial_does_not_block_unrelated_work(self):
        self.experiment()
        self.data['parameters']['player.health']['value'] = 90
        self.engine(90)
        errors, warnings = gdd.validate(self.data, self.root)
        self.assertEqual([], errors)
        self.assertTrue(any('baseline' in w for w in warnings))

    def test_trial_scene_bindings_do_not_replace_canonical_bindings(self):
        self.experiment(binding_overrides={'player.health': [
            {'path': 'data/arena.json', 'format': 'json', 'pointer': '/max_health'}]})
        (self.root / 'data' / 'arena.json').write_text('{"max_health":80}', encoding='utf-8')
        original = copy.deepcopy(self.data)
        self.assertEqual([], self.errors())
        self.assertEqual([], self.errors(experiment='exp-health'))
        self.assertEqual(original, self.data)

    def test_trial_binding_override_must_target_a_trial_parameter(self):
        self.experiment(binding_overrides={'missing': []})
        self.assertTrue(any('binding_overrides' in e for e in self.errors(experiment='exp-health')))

    def test_rules_questions_and_decisions_keep_meaningful_structure(self):
        self.data['open_questions'] = [{'id': 'q-health', 'text': 'Which health?',
                                      'affects': ['missing'], 'blocking': False}]
        self.assertTrue(any('question' in e for e in self.errors()))
        self.data['open_questions'] = []
        self.data['decisions'] = [{'id': 'd-health', 'summary': 'Use current health',
                                  'source': 'User request', 'status': 'superseded',
                                  'superseded_by': 'missing'}]
        self.assertTrue(any('decision' in e for e in self.errors()))

    def test_numeric_trial_requires_affected_owner_in_scope(self):
        self.experiment(affects=[])
        self.assertTrue(any('scope' in e for e in self.errors(experiment='exp-health')))

    def test_experiment_cannot_be_adopted_without_decision_source(self):
        self.experiment(status='adopted', decision={'outcome': 'adopt', 'source': None})
        self.assertTrue(any('decision' in e for e in self.errors()))

    def test_closed_experiment_cannot_be_selected(self):
        self.experiment(status='rejected', decision={'outcome': 'reject', 'source': 'User: remove it'})
        self.assertTrue(any('active' in e for e in self.errors(experiment='exp-health')))

    def test_experiment_can_have_new_system_and_parameter(self):
        new_p = copy.deepcopy(self.data['parameters']['player.health'])
        new_p.update(system='jump', value=2, unit='m', bindings=[])
        self.experiment(overrides={}, base_values={},
                        systems=[{'id': 'jump', 'summary': 'Trial jump', 'status': 'proposed',
                                  'rules': [], 'depends_on': ['player']}],
                        affects=['player', 'jump'], new_parameters={'jump.height': new_p})
        self.assertEqual([], self.errors(experiment='exp-health'))

    def test_json_pointer_escaping_and_arrays(self):
        self.assertEqual(7, gdd.pointer_get({'a/b': [{'~k': 7}]}, '/a~1b/0/~0k'))
        with self.assertRaises(ValueError):
            gdd.pointer_get({}, 'bad')

    def test_numbers_must_be_finite_and_not_booleans(self):
        for invalid in (True, float('nan'), float('inf'), '100'):
            self.data['parameters']['player.health']['value'] = invalid
            self.assertTrue(self.errors())

    def test_bound_files_cannot_escape_project(self):
        self.data['parameters']['player.health']['bindings'][0]['path'] = '../other.json'
        self.assertTrue(any('outside' in e for e in self.errors()))

    def test_duplicate_keys_are_rejected(self):
        bad = self.root / 'duplicate.json'
        bad.write_text('{"value": 1, "value": 2}', encoding='utf-8')
        with self.assertRaises(ValueError):
            gdd.load_json(bad)

    def test_generated_markdown_changes_when_value_changes(self):
        first = gdd.render_markdown(self.data)
        self.data['parameters']['player.health']['value'] = 80
        second = gdd.render_markdown(self.data)
        self.assertNotEqual(first, second)
        self.assertIn('80', second)

    def test_strict_validation_detects_stale_view_after_synced_numeric_edit(self):
        self.data['coverage']['status'] = 'reviewed'
        (self.root / 'design' / 'GDD.md').write_text(gdd.render_markdown(self.data), encoding='utf-8')
        self.assertEqual([], self.errors(strict=True))
        self.data['parameters']['player.health']['value'] = 80
        self.data['revision'] = 2
        self.engine(80)
        self.assertTrue(any('Markdown' in e for e in self.errors(strict=True)))

    def test_instruction_install_preserves_existing_rules_and_is_idempotent(self):
        content = '# Existing instructions\r\n\r\nKeep Russian text: правила.\r\n'
        merged = gdd.merge_instructions(content)
        self.assertTrue(merged.startswith(content))
        self.assertEqual(merged, gdd.merge_instructions(merged))
        with self.assertRaises(ValueError):
            gdd.merge_instructions('<!-- automated-gdd:start -->\ntruncated')

    def test_non_json_verification_is_bound_to_file_content(self):
        import hashlib
        resource = self.root / 'player.tres'
        resource.write_text('health = 100\n', encoding='utf-8')
        binding = {'path': 'player.tres', 'format': 'manual',
                   'verification': {'value': 100, 'file_sha256': hashlib.sha256(resource.read_bytes()).hexdigest(),
                                    'evidence': 'Engine inspector read max_health=100'}}
        self.data['parameters']['player.health']['bindings'] = [binding]
        self.assertEqual([], self.errors())
        resource.write_text('health = 80\n', encoding='utf-8')
        self.assertTrue(any('verification' in e for e in self.errors()))


if __name__ == '__main__':
    unittest.main()
