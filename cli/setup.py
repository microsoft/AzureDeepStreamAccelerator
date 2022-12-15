from setuptools import setup

setup(
    name='deepstreamcli',
    version='0.1',
    py_modules=['deepstreamcli'],
    install_requires=[
        'Typer>=0.6.1',
        "typing-extensions>=4.0.1"
    ],
    entry_points='''
        [console_scripts]
        azdacli=deepstreamcli:app
    ''',
)
