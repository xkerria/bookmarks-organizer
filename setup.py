from setuptools import setup, find_packages

setup(
    name="bookmarks-organizer",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'beautifulsoup4',
        'openai',
        'python-dotenv',
        'httpx[socks]',
        'qianfan',
        'pyyaml'
    ],
    entry_points={
        'console_scripts': [
            'organize-bookmarks=src.main:main',
        ],
    },
    python_requires='>=3.8',
) 