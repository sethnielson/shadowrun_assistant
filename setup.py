from setuptools import setup, find_packages

setup(
    name='shadownexus',
    version='0.1',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
        'Django>=4.0,<5.0',
    ],
    entry_points={
        'console_scripts': [
            'shadowrun-web=shadownexus.manage:main',
        ],
    },
)
