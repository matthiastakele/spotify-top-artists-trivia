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
    name='SpotifyTopArtistsTrivia',
    version='1.0',
    description='An application to test your knowledge on your top Spotify artists',
    author = 'Matthias Takele',
    packages = find_packages(),
    include_package_data=True,
    install_requires = requires
)