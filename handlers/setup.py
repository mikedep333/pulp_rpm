from setuptools import setup, find_packages

setup(
    name='pulp_rpm_handlers',
    version='2.10c6',
    license='GPLv2+',
    packages=find_packages(exclude=['test', 'test.*']),
    author='Pulp Team',
    author_email='pulp-list@redhat.com',
)
