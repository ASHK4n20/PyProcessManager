from setuptools import setup, find_packages

setup(
    name="pypm",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'psutil==5.9.0',
        'PyYAML==6.0',
        'click==8.1.3',
        'rich==13.3.1',
        'watchdog==2.1.9',
    ],
    entry_points={
        'console_scripts': [
            'pypm=cli:cli',
        ],
    },
)
