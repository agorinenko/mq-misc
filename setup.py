import setuptools
"""
python -m pip install --upgrade setuptools wheel twine
python setup.py sdist bdist_wheel

python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*
python -m twine upload dist/*
"""
with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()

setuptools.setup(
    name="mq-misc",
    version="0.0.4",
    author="Anton Gorinenko",
    author_email="anton.gorinenko@gmail.com",
    description="Utility package for working with rabbitmq",
    long_description=long_description,
    keywords='python, asyncio, utils, mq, aio_pika, rabbit mq, rabbit',
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(exclude=['tests']),
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "aio_pika>=6.8.0",
        "ConfigArgParse>=1.3"
    ],
    extras_require={
        'test': [
            'pytest',
            'pytest-cov',
            'pytest-asyncio',
            'pytest-mock',
            'pylint',
            'pytest-dotenv',
            'envparse',
            'asynctest',
        ]
    },
    python_requires='>=3.8',
)
