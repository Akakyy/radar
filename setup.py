from setuptools import setup, find_packages
import radar

setup(
    name='radar',
    version="0.0.1",
    description="Game",
    long_description='Game',
    author="akakiy_akakievich",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'radar = radar.__main__:main'
        ],
    },
    extras_require={},
    install_requires=open('requirements.txt', 'r').readlines(),
    tests_require=open('requirements.txt', 'r').readlines(),
    classifiers=[
        'Programming Language :: Python',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'Topic :: Utilities'
    ],
    include_package_data=True,
    #package_data={
    #    'radar': [
    #        'binary_files/halstead.jar',
    #        'binary_files/model.dat']
    #},
)