from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

long_description = (here / 'README.md').read_text(encoding='utf-8')

setup(
    name='mementoizer',
    version='0.0.1',
    description='Memento-ize a video',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/ryanfox/mementoizer',
    author='Ryan Fox',
    author_email='ryan@foxrow.com',
    keywords='video, image processing, computer vision',
    packages=find_packages(where='mementoizer'),
    python_requires='>=3.8, <4',
    install_requires=['moviepy>=1.0.3'],
    entry_points={
        'console_scripts': [
            'mementoize=mementoizer:cli',
        ],
    },
    project_urls={
        'Source': 'https://github.com/ryanfox/mementoizer/',
    },
)
