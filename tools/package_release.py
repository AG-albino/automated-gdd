#!/usr/bin/env python3
"""Build a self-contained skill ZIP and verify it in an isolated project."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile


def run(helper, root, command, *options):
    result = subprocess.run([sys.executable, str(helper), command, '--root', str(root), *options],
                            capture_output=True, text=True, encoding='utf-8')
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout


def main():
    root = Path(__file__).resolve().parent.parent
    skill = root / 'skills' / 'automated-gdd'
    dist = root / 'dist'
    dist.mkdir(exist_ok=True)
    archive = dist / 'automated-gdd.zip'
    relative_paths = ('SKILL.md', 'LICENSE', 'VERSION', 'agents/openai.yaml',
                      'assets/game.template.json', 'assets/project-workflow.md',
                      'references/data-contract.md', 'references/onboarding.md',
                      'references/steward.md', 'scripts/gdd.py')
    files = [skill / p for p in relative_paths]
    for path in files:
        text = path.read_text(encoding='utf-8')
        if '\ufffd' in text:
            raise ValueError('Invalid replacement character in ' + str(path))
    readme = (root / 'README.md').read_text(encoding='utf-8')
    expected = ('```text\nUse the skill at https://github.com/AG-albino/automated-gdd '
                'to set up an automated game design document (GDD) in my project.\n```')
    if not readme.startswith('# Automated GDD\n\n[![Checks]'):
        raise ValueError('README must start with the heading and status badges')
    prompt_position = readme.find(expected)
    if prompt_position < 0 or prompt_position > readme.find('![Automated GDD —'):
        raise ValueError('README must include the copyable English prompt before the banner')
    if re.search(r'[\u0400-\u04ff]', readme):
        raise ValueError('README must be entirely English')
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', readme):
        if not target.startswith(('https://', 'http://', '#')) and not (root / target.split('#')[0]).exists():
            raise ValueError('Broken local README link: ' + target)
    frontmatter = (skill / 'SKILL.md').read_text(encoding='utf-8').split('---', 2)[1]
    if not re.search(r'^name: automated-gdd$', frontmatter, re.M):
        raise ValueError('Unexpected skill name')
    if not re.search(r'^description: .+', frontmatter, re.M):
        raise ValueError('Missing skill description')
    version = (skill / 'VERSION').read_text(encoding='utf-8').strip()
    if not re.search(r'^  version: "' + re.escape(version) + r'"$', frontmatter, re.M):
        raise ValueError('Skill metadata and VERSION must agree')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as package:
        for path in sorted(set(files)):
            relative = path.relative_to(skill).as_posix()
            info = zipfile.ZipInfo('automated-gdd/' + relative, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            package.writestr(info, path.read_bytes())
    with tempfile.TemporaryDirectory(prefix='automated-gdd-release-') as temp:
        scratch = Path(temp)
        with zipfile.ZipFile(archive) as package:
            if package.testzip() is not None:
                raise ValueError('Corrupt ZIP member')
            if set(package.namelist()) != {'automated-gdd/' + p for p in relative_paths}:
                raise ValueError('Archive must contain only installable skill files')
            package.extractall(scratch)
        extracted = scratch / 'automated-gdd'
        for path in files:
            if path.read_bytes() != (extracted / path.relative_to(skill)).read_bytes():
                raise ValueError('Archive differs from source: ' + str(path))
        for path in extracted.rglob('*.md'):
            for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
                if not target.startswith(('https://', 'http://', '#')) and not (path.parent / target.split('#')[0]).is_file():
                    raise ValueError('Broken skill link inside release ZIP: ' + target)
        project = scratch / 'test game'
        (project / 'design').mkdir(parents=True)
        original = '# Local rules\n\nKeep these instructions.\n'
        (project / 'AGENTS.md').write_text(original, encoding='utf-8')
        original_bytes = (project / 'AGENTS.md').read_bytes()
        template = json.loads((extracted / 'assets' / 'game.template.json').read_text(encoding='utf-8'))
        (project / 'design' / 'game.json').write_text(json.dumps(template), encoding='utf-8')
        helper = extracted / 'scripts' / 'gdd.py'
        run(helper, project, 'install-rules')
        first = (project / 'AGENTS.md').read_bytes()
        run(helper, project, 'install-rules')
        assert first == (project / 'AGENTS.md').read_bytes(), 'Installation must be idempotent'
        assert first.startswith(original_bytes), 'Existing rules must survive byte-for-byte'
        run(helper, project, 'render')
        run(helper, project, 'validate', '--schema-only')
        overview = json.loads(run(helper, project, 'show'))
        assert overview['revision'] == 1
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    (dist / 'SHA256SUMS').write_text(checksum + '  automated-gdd.zip\n', encoding='utf-8')
    print('Built dist/automated-gdd.zip and dist/SHA256SUMS')
    print('Verified minimal archive contents, source bytes, document links, and extracted CLI setup/render/validation.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
