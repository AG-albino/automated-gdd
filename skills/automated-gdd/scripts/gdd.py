#!/usr/bin/env python3
"""Portable GDD checks and views. Python 3.9+, standard library only."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import sys

START = '<!-- automated-gdd:start -->'
END = '<!-- automated-gdd:end -->'
STATUSES = {'accepted', 'proposed', 'unknown'}
ID = re.compile(r'^[a-z0-9][a-z0-9._-]*$')


def load_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    def invalid(value):
        raise ValueError('Non-finite JSON number: ' + value)
    return json.loads(Path(path).read_text(encoding='utf-8-sig'),
                      object_pairs_hook=unique, parse_constant=invalid)


def number(value):
    return type(value) in (int, float) and (type(value) is int or math.isfinite(value))


def pointer_get(data, pointer):
    if not isinstance(pointer, str) or (pointer and not pointer.startswith('/')):
        raise ValueError('JSON pointer must be empty or start with /')
    if not pointer:
        return data
    for part in pointer[1:].split('/'):
        if re.search(r'~(?![01])', part):
            raise ValueError('Invalid JSON pointer escape')
        part = part.replace('~1', '/').replace('~0', '~')
        if isinstance(data, list):
            if not re.fullmatch(r'0|[1-9][0-9]*', part):
                raise ValueError('Invalid JSON array index: ' + part)
            data = data[int(part)]
        elif isinstance(data, dict):
            data = data[part]
        else:
            raise ValueError('JSON pointer traverses a scalar')
    return data


def project_file(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError('Binding path must be project-relative')
    target = (root / relative).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError('Binding path resolves outside project: ' + relative)
    return target


def records(systems, parameters, errors, warnings):
    indexed = {}
    for system in systems:
        if not isinstance(system, dict):
            errors.append('System must be an object')
            continue
        key = system.get('id')
        if not isinstance(key, str) or not ID.fullmatch(key) or key in indexed:
            errors.append('Invalid/duplicate system id: ' + str(key))
            continue
        indexed[key] = system
        if not isinstance(system.get('summary'), str) or not system['summary'].strip():
            errors.append(key + ': summary is required')
        if system.get('status') not in STATUSES:
            errors.append(key + ': invalid design status')
        if not isinstance(system.get('rules'), list):
            errors.append(key + ': rules must be an array')
        else:
            rule_ids = set()
            for rule in system['rules']:
                if not isinstance(rule, dict) or not isinstance(rule.get('id'), str):
                    errors.append(key + ': rule requires an id')
                    continue
                if rule['id'] in rule_ids or not ID.fullmatch(rule['id']):
                    errors.append(key + ': invalid/duplicate rule id ' + rule['id'])
                rule_ids.add(rule['id'])
                if rule.get('status') not in STATUSES or not isinstance(rule.get('text'), str):
                    errors.append(key + ': rule requires text and status')
                if not rule.get('source'):
                    warnings.append(key + ': rule has no decision source')
    for key, system in indexed.items():
        deps = system.get('depends_on')
        if not isinstance(deps, list) or any(not isinstance(x, str) for x in deps):
            errors.append(key + ': system depends_on must contain IDs')
        else:
            for dep in deps:
                if dep not in indexed:
                    errors.append(key + ': missing system dependency ' + dep)
    graph = {}
    for key, param in parameters.items():
        if not isinstance(key, str) or not ID.fullmatch(key) or key in indexed:
            errors.append('Invalid/colliding parameter id: ' + str(key))
        if not isinstance(param, dict):
            errors.append(str(key) + ': parameter must be an object')
            continue
        if param.get('system') not in indexed:
            errors.append(key + ': missing owning system')
        if 'value' not in param or (param['value'] is not None and not number(param['value'])):
            errors.append(key + ': value must be a finite number or null')
        elif param['value'] is None:
            warnings.append(key + ': numeric value is unknown')
        if not isinstance(param.get('unit'), str) or not param['unit'].strip():
            errors.append(key + ': explicit unit is required')
        if param.get('status') not in STATUSES:
            errors.append(key + ': invalid design status')
        if not param.get('source'):
            warnings.append(key + ': no provenance/source')
        if not isinstance(param.get('bindings'), list):
            errors.append(key + ': bindings must be an array')
        deps = param.get('depends_on')
        if not isinstance(deps, list) or any(not isinstance(x, str) for x in deps):
            errors.append(key + ': parameter depends_on must contain IDs')
        else:
            graph[key] = deps
            for dep in deps:
                if dep not in parameters:
                    errors.append(key + ': missing parameter dependency ' + dep)
    visited, active = set(), set()
    def visit(key):
        if key in active:
            errors.append('Parameter dependency cycle at ' + key)
            return
        if key in visited:
            return
        active.add(key)
        for dep in graph.get(key, []):
            visit(dep)
        active.remove(key)
        visited.add(key)
    for key in graph:
        visit(key)
    return indexed


def experiment_records(root, data, errors):
    result = {}
    for path in sorted((root / 'design' / 'experiments').glob('*.json')):
        try:
            exp = load_json(path)
            if not isinstance(exp, dict) or exp.get('id') != path.stem or not ID.fullmatch(path.stem):
                raise ValueError('experiment id must match its filename')
            if exp['id'] in result:
                raise ValueError('duplicate experiment id')
            if type(exp.get('base_revision')) is not int or not 1 <= exp['base_revision'] <= data['revision']:
                raise ValueError('invalid/future base_revision')
            if exp.get('status') not in {'active', 'paused', 'evaluated', 'adopted', 'rejected'}:
                raise ValueError('invalid experiment status')
            for key in ('hypothesis',):
                if not isinstance(exp.get(key), str) or not exp[key].strip():
                    raise ValueError(key + ' is required')
            for key in ('affects', 'systems', 'trial_rules', 'observations'):
                if not isinstance(exp.get(key), list):
                    raise ValueError(key + ' must be an array')
            for key in ('base_values', 'overrides', 'new_parameters', 'decision'):
                if not isinstance(exp.get(key), dict):
                    raise ValueError(key + ' must be an object')
            decision = exp['decision']
            if decision.get('outcome') not in {'undecided', 'adopt', 'reject'}:
                raise ValueError('invalid decision outcome')
            if exp['status'] in {'adopted', 'rejected'}:
                expected = 'adopt' if exp['status'] == 'adopted' else 'reject'
                if decision.get('outcome') != expected or not decision.get('source'):
                    raise ValueError('closed experiment requires matching decision and source')
            elif decision.get('outcome') != 'undecided':
                raise ValueError('an adoption/rejection decision must close the experiment')
            if set(exp['overrides']) != set(exp['base_values']):
                raise ValueError('base_values must cover exactly the overridden parameters')
            for value in list(exp['overrides'].values()) + list(exp['base_values'].values()):
                if value is not None and not number(value):
                    raise ValueError('trial/base values must be finite numbers or null')
            if any(value is None for value in exp['overrides'].values()):
                raise ValueError('an active numeric override needs a number')
            binding_overrides = exp.get('binding_overrides', {})
            if not isinstance(binding_overrides, dict):
                raise ValueError('binding_overrides must be an object')
            for key, bindings in binding_overrides.items():
                if key not in exp['overrides'] or not isinstance(bindings, list) or not bindings:
                    raise ValueError('binding_overrides must target an overridden parameter with a nonempty binding array')
            result[exp['id']] = exp
        except (ValueError, KeyError, TypeError, OSError) as exc:
            errors.append(path.name + ': ' + str(exc))
    return result


def effective(data, experiments, selected, errors):
    view = copy.deepcopy(data)
    if selected is None:
        return view
    exp = experiments.get(selected)
    if not exp or exp.get('status') != 'active':
        errors.append(str(selected) + ': select an existing active experiment')
        return view
    for key, value in exp['overrides'].items():
        if key not in view['parameters']:
            errors.append(selected + ': unknown override ' + key)
            continue
        if view['parameters'][key]['value'] != exp['base_values'][key]:
            errors.append(selected + ': changed baseline for ' + key + '; reconcile before resuming')
        view['parameters'][key]['value'] = value
        if key in exp.get('binding_overrides', {}):
            view['parameters'][key]['bindings'] = exp['binding_overrides'][key]
    for key, value in exp['new_parameters'].items():
        if key in view['parameters']:
            errors.append(selected + ': new parameter collides with canonical id ' + key)
        else:
            view['parameters'][key] = value
    view['systems'].extend(exp['systems'])
    known_systems = {s.get('id') for s in view['systems'] if isinstance(s, dict)}
    if any(not isinstance(s, str) or s not in known_systems for s in exp['affects']):
        errors.append(selected + ': affects contains an unknown system')
    for key in set(exp['overrides']) | set(exp['new_parameters']):
        param = view['parameters'].get(key)
        if isinstance(param, dict) and param.get('system') not in exp['affects']:
            errors.append(selected + ': parameter owner is outside experiment scope: ' + key)
    view['_experiment'] = exp
    return view


def check_binding(root, key, expected, binding, errors, warnings):
    try:
        if not isinstance(binding, dict):
            raise ValueError('binding must be an object')
        path = project_file(root, binding.get('path'))
        if binding.get('format') == 'json':
            actual = pointer_get(load_json(path), binding.get('pointer'))
        elif binding.get('format') == 'manual':
            evidence = binding.get('verification', {})
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if not evidence.get('evidence') or evidence.get('file_sha256') != digest:
                raise ValueError('manual verification missing or stale for ' + str(binding.get('path')))
            actual = evidence.get('value')
            warnings.append(key + ': manual evidence matches file hash; value not independently parsed')
        else:
            raise ValueError('unsupported binding format; use json or real manual/adapter evidence')
        if not number(actual) or actual != expected:
            raise ValueError('numeric mismatch: expected ' + str(expected) + ', observed ' + str(actual))
    except (OSError, ValueError, KeyError, IndexError, TypeError) as exc:
        errors.append(key + ': ' + str(exc))


def validate(data, root, experiment=None, strict=False, schema_only=False):
    root = Path(root).resolve()
    errors, warnings = [], []
    if not isinstance(data, dict):
        return ['GDD must be an object'], []
    if type(data.get('schema_version')) is not int or data['schema_version'] != 1:
        errors.append('Unsupported schema_version (expected 1)')
    if type(data.get('revision')) is not int or data.get('revision', 0) < 1:
        errors.append('revision must be a positive integer')
    for key, kind in (('project', dict), ('workflow', dict), ('systems', list),
                      ('parameters', dict), ('open_questions', list), ('decisions', list), ('coverage', dict)):
        if not isinstance(data.get(key), kind):
            errors.append(key + ': missing or invalid top-level field')
    if errors:
        return errors, warnings
    if data['workflow'].get('steward') not in {'main', 'subagent'}:
        errors.append('workflow.steward must be main or subagent')
    if data['workflow'].get('numeric_mode') not in {'canonical', 'mirrored'}:
        errors.append('workflow.numeric_mode must be canonical or mirrored')
    if not data['project'].get('title'):
        warnings.append('Game title is unknown')
    coverage = data['coverage']
    if coverage.get('status') not in {'partial', 'reviewed'}:
        errors.append('coverage.status must be partial or reviewed')
    if not isinstance(coverage.get('reviewed_paths'), list) or not isinstance(coverage.get('unregistered'), list):
        errors.append('coverage requires reviewed_paths and unregistered arrays')
    if coverage.get('status') != 'reviewed' or coverage.get('unregistered'):
        warnings.append('Numeric coverage is partial or has unregistered values')
    system_index = records(data['systems'], data['parameters'], errors, warnings)
    known = set(system_index) | set(data['parameters'])
    for system in system_index.values():
        known.update(r['id'] for r in system.get('rules', []) if isinstance(r, dict) and isinstance(r.get('id'), str))
    decision_ids = {d['id'] for d in data['decisions'] if isinstance(d, dict) and isinstance(d.get('id'), str)}
    for collection, label in (('open_questions', 'question'), ('decisions', 'decision')):
        seen = set()
        for item in data[collection]:
            if not isinstance(item, dict) or not isinstance(item.get('id'), str) or not ID.fullmatch(item['id']):
                errors.append(label + ': record requires a stable id')
                continue
            if item['id'] in seen:
                errors.append(label + ': duplicate id ' + item['id'])
            seen.add(item['id'])
            text_key = 'text' if label == 'question' else 'summary'
            if not isinstance(item.get(text_key), str) or not item[text_key].strip():
                errors.append(label + ': missing ' + text_key)
            if label == 'question':
                affects = item.get('affects')
                if (not isinstance(affects, list) or
                        any(not isinstance(k, str) or k not in known for k in affects) or
                        type(item.get('blocking')) is not bool):
                    errors.append('question: invalid affects references or blocking flag')
            elif (item.get('status') not in {'current', 'superseded'} or not item.get('source') or
                  (item.get('superseded_by') is not None and item['superseded_by'] not in decision_ids)):
                errors.append('decision: invalid status, source, or replacement reference')
    if errors:
        return errors, warnings
    experiments = experiment_records(root, data, errors)
    for key in experiments:
        if experiments[key]['status'] == 'active':
            trial_errors = []
            trial = effective(data, experiments, key, trial_errors)
            records(trial['systems'], trial['parameters'], trial_errors, [])
            for issue in trial_errors:
                if key != experiment and 'changed baseline' in issue:
                    warnings.append(issue)
                else:
                    errors.append(issue)
    view = effective(data, experiments, experiment, errors)
    if errors:
        return errors, warnings
    if not schema_only:
        for key, param in view['parameters'].items():
            selected_new = experiment and key in experiments[experiment]['new_parameters']
            if param['status'] != 'accepted' and not selected_new:
                continue
            if param['value'] is None:
                continue
            if not param['bindings']:
                warnings.append(key + ': game binding is unresolved')
            for binding in param['bindings']:
                check_binding(root, key, param['value'], binding, errors, warnings)
        md = root / 'design' / 'GDD.md'
        if not md.exists() or md.read_text(encoding='utf-8') != render_markdown(data):
            warnings.append('Generated Markdown is missing/stale; run render')
    if strict:
        errors.extend('Readiness: ' + warning for warning in warnings)
    return errors, warnings


def compact(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def cell(value):
    text = value if isinstance(value, str) else compact(value)
    return text.replace('|', '\\|').replace('\r', '').replace('\n', '<br>')


def render_markdown(data):
    digest = hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()
    lines = ['<!-- automated-gdd:generated; source=game.json; sha256=' + digest + ' -->',
             '# ' + (data['project'].get('title') or 'Game Design'), '',
             'Revision: ' + str(data['revision']), '',
             '> Generated from game.json. Edit the source, then render again. Experiments are separate.',
             '', '## Project', '']
    for key, value in data['project'].items():
        lines.append('- **' + key + ':** ' + cell(value))
    lines += ['', '## Workflow', '', '```json', json.dumps(data['workflow'], indent=2, ensure_ascii=False), '```', '', '## Systems', '']
    for system in data['systems']:
        lines += ['### ' + system['id'] + ' [' + system['status'] + ']', '', system['summary'], '',
                  'Dependencies: ' + ', '.join(system['depends_on']), '']
        for rule in system['rules']:
            lines.append('- **' + rule['id'] + '** [' + rule['status'] + ']: ' + rule['text'] + ' (source: ' + str(rule.get('source')) + ')')
        extras = {k: v for k, v in system.items() if k not in {'id', 'status', 'summary', 'rules', 'depends_on'}}
        if extras:
            lines += ['', '```json', json.dumps(extras, ensure_ascii=False, indent=2), '```']
        lines.append('')
    lines += ['## Numeric parameters', '', '| ID | Value | Unit | System | Status | Depends on |',
              '|---|---|---|---|---|---|']
    for key, param in data['parameters'].items():
        lines.append('| ' + ' | '.join(cell(v) for v in
                     (key, param['value'], param['unit'], param['system'], param['status'], param['depends_on'])) + ' |')
    for key, param in data['parameters'].items():
        details = {k: v for k, v in param.items() if k not in {'value', 'unit', 'system', 'status', 'depends_on'}}
        lines += ['', '### ' + key, '', '```json', json.dumps(details, ensure_ascii=False, indent=2), '```']
    for title, key in (('Open questions', 'open_questions'), ('Decisions', 'decisions'), ('Coverage', 'coverage')):
        lines += ['', '## ' + title, '', '```json', json.dumps(data[key], ensure_ascii=False, indent=2), '```']
    extras = {k: v for k, v in data.items() if k not in {'schema_version', 'revision', 'project', 'workflow', 'systems', 'parameters', 'open_questions', 'decisions', 'coverage'}}
    if extras:
        lines += ['', '## Additional design data', '', '```json', json.dumps(extras, ensure_ascii=False, indent=2), '```']
    return '\n'.join(lines) + '\n'


def merge_instructions(content):
    if content.count(START) != content.count(END) or content.count(START) > 1:
        raise ValueError('Ambiguous/incomplete managed GDD block; reconcile it before writing')
    newline = '\r\n' if '\r\n' in content else '\n'
    block = '\n'.join([START, '## Automated game design',
        '- Read `design/WORKFLOW.md` and relevant `design/game.json` records before gameplay changes.',
        '- An explicit request changes its targeted old rule; inspect effects on other systems and resolve material choices.',
        '- Keep all configurable game numbers, dependencies and game bindings synchronized; verify affected values before completion.',
        '- Keep trials in `design/experiments/`; apply only the selected scope, never adopt from code/tests alone.',
        '- All agents read directly. Follow saved steward preference; use one writer and verify its work.',
        '- Update canonical JSON and regenerate `design/GDD.md`; preserve current decisions and report unresolved gaps.',
        '- Run `python design/tools/gdd.py validate --root .` (add `--experiment <id>` for a trial).', END]).replace('\n', newline)
    if START in content:
        start, end = content.index(START), content.index(END)
        if end < start:
            raise ValueError('Managed GDD markers are reversed')
        return content[:start] + block + content[end + len(END):]
    return content + ('' if not content or content.endswith(newline * 2) else newline if content.endswith(newline) else newline * 2) + block + newline


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as handle:
        handle.write(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['validate', 'render', 'show', 'install-rules'])
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--id')
    parser.add_argument('--experiment')
    parser.add_argument('--strict', action='store_true')
    parser.add_argument('--schema-only', action='store_true')
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if not root.is_dir():
            raise ValueError('Project root must already exist')
        if args.command == 'install-rules':
            target = root / 'AGENTS.md'
            original = ''
            if target.exists():
                with target.open(encoding='utf-8-sig', newline='') as handle:
                    original = handle.read()
            merged = merge_instructions(original)
            workflow = root / 'design' / 'WORKFLOW.md'
            if not workflow.exists():
                source = Path(__file__).resolve().parent.parent / 'assets' / 'project-workflow.md'
                if not source.exists():
                    raise ValueError('Copy the skill project-workflow.md asset to design/WORKFLOW.md first')
                write_text(workflow, source.read_text(encoding='utf-8'))
            write_text(target, merged)
            print('Merged one GDD block; preserved unrelated project instructions.')
            return 0
        data = load_json(root / 'design' / 'game.json')
        errors, warnings = validate(data, root, args.experiment,
                                    args.strict if args.command == 'validate' else False,
                                    args.schema_only or args.command in {'render', 'show'})
        if errors:
            for error in errors:
                print('ERROR: ' + error, file=sys.stderr)
            return 1
        if args.command == 'render':
            write_text(root / 'design' / 'GDD.md', render_markdown(data))
            print('Rendered design/GDD.md from canonical JSON; experiments excluded.')
        elif args.command == 'show':
            exps = experiment_records(root, data, [])
            view = effective(data, exps, args.experiment, [])
            key = args.id
            if key is None:
                result = {'revision': data['revision'], 'project': data['project'], 'workflow': data['workflow'],
                          'systems': [{'id': s['id'], 'summary': s['summary'], 'status': s['status']} for s in view['systems']],
                          'parameter_ids': list(view['parameters']),
                          'active_experiments': [k for k, v in exps.items() if v['status'] == 'active'],
                          'coverage': data['coverage']}
            elif key in view['parameters']:
                result = {'id': key, **view['parameters'][key],
                          'used_by_parameters': [k for k, v in view['parameters'].items() if key in v['depends_on']]}
            elif key in {s['id'] for s in view['systems']}:
                result = {'system': next(s for s in view['systems'] if s['id'] == key),
                          'used_by_systems': [s['id'] for s in view['systems'] if key in s['depends_on']],
                          'parameters': {k: v for k, v in view['parameters'].items() if v['system'] == key}}
            elif key in exps:
                result = exps[key]
            else:
                raise ValueError('Unknown system/parameter/experiment id: ' + key)
            if args.experiment:
                result = {'effective_experiment': args.experiment, 'trial_rules': exps[args.experiment]['trial_rules'], 'record': result}
            print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))
        else:
            for warning in warnings:
                print('WARNING: ' + warning)
            print('Valid registered data' + (' (schema only; game bindings NOT checked).' if args.schema_only else '; inspect warnings for verification limits.'))
        return 0
    except (OSError, ValueError, KeyError, TypeError, IndexError) as exc:
        print('ERROR: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    raise SystemExit(main())
