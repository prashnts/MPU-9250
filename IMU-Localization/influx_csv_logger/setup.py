"""
Logs CSV data into Influx DB.
"""
from setuptools import find_packages, setup

dependencies = ['click']

setup(
    name='influx_csv_logger',
    version='0.0.1',
    url='https://github.com/prashnts/influx_csv_logger',
    license='MIT',
    author='Prashant Sinha',
    author_email='prashantsinha@outlook.com',
    description='Logs CSV data into Influx DB.',
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=dependencies,
    entry_points={
        'console_scripts': [
            'influxcsvlogger = influx_csv_logger.cli:main',
        ],
    },
    #scripts=['influx_csv_logger/cli.py'],
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        # 'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        'Development Status :: 3 - Alpha',
        # 'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Operating System :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
