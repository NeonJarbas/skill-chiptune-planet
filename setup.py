#!/usr/bin/env python3
from setuptools import setup

# skill_id=package_name:SkillClass
PLUGIN_ENTRY_POINT = 'skill-chiptune-planet.jarbasai=skill_chiptune_planet:ChiptunePlanetSkill'

setup(
    # this is the package name that goes on pip
    name='ovos-skill-chiptune-planet',
    version='0.0.1',
    description='ovos chip tune 8 bit music skill plugin',
    url='https://github.com/JarbasSkills/skill-chiptune-planet',
    author='JarbasAi',
    author_email='jarbasai@mailfence.com',
    license='Apache-2.0',
    package_dir={"skill_chiptune_planet": ""},
    package_data={'skill_chiptune_planet': ['locale/*', 'res/*', 'res/*']},
    packages=['skill_chiptune_planet'],
    include_package_data=True,
    install_requires=["ovos_workshop~=0.0.5a1"],
    keywords='ovos skill plugin',
    entry_points={'ovos.plugin.skill': PLUGIN_ENTRY_POINT}
)
