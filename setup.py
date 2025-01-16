from setuptools import setup, find_packages

requires = [
    'flask',
    'spotipy',
    'html5lib',
    'requests',
    'requests_html',
    'beautifulsoup4',
    'pathlib',
    'pandas'
]

setup(
    name='SpotifyCalendar',
    version='1.0',
    description='An application to display your top Spotify daily and monthly listening in a calendar format',
    author = 'Matthias Takele',
    packages = find_packages(),
    include_package_data=True,
    install_requires = requires
)