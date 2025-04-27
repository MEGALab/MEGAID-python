from setuptools import setup, find_packages

setup(
    name='megaid',
    version='1.0.0',
    description='Ultra-light Snowflake + JWT Compound ID Generator.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='MEGALab',
    author_email='shawn@megalab.io',
    url='https://github.com/MEGALab/MEGAID-python',
    packages=find_packages(),
    install_requires=[
        'PyJWT>=2.8.0'
    ],
    classifiers=[
        'License :: OSI Approved :: GNU Affero General Public License v3',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
)
