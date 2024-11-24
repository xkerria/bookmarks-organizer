from setuptools import setup, find_packages

setup(
    name="bookmarks-organizer",
    version="0.1.0",
    description="A tool for organizing browser bookmarks using AI",
    author="Kerria Kerria",
    packages=find_packages(),
    install_requires=[
        'beautifulsoup4>=4.12.0',
        'openai>=1.0.0',
        'python-dotenv>=1.0.0',
        'httpx[socks]>=0.24.0',
        'qianfan>=0.0.3',
        'pyyaml>=6.0.0',
        'fasttext>=0.9.2'
    ],
    python_requires='>=3.8',
)