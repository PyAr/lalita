from setuptools import setup, find_packages
setup(
    # metadata
    name='lalita',
    version='0.1',

    # content
    package_dir={'': 'src'},
    packages=['lalita', 'lalita.core',
              'lalita.plugins', 'lalita.plugins.randomer_utils'],
    package_data={'lalita.plugins.randomer_utils': ['#pyar.log']},

)
