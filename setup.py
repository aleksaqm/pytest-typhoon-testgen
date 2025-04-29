from setuptools import setup, find_packages

setup(
    name='pytest-typhoon-testgen',
    version='0.1.0',
    author = "Aleksa Perovic",
    author_email="aleksa.perovic@typhoon-hil.com",
    url="https://github.com/aleksaqm/pytest-typhoon-testgen",
    description="Test generator based on requirements.",
    packages=find_packages(),
    python_requires='>=3.6',
    install_requires=["jinja2>=3.0"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'typhoon_testgen = testgen.plugin:main'
        ]
    }
)