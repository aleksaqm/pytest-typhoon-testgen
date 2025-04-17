from setuptools import setup, find_packages

setup(
    name='pytest-typhoon-specgen',
    version='0.1.0',
    author = "Aleksa Perovic",
    author_email="aleksa.perovic@typhoon-hil.com",
    url="https://github.com/aleksaqm/pytest-typhoon-specgen",
    description="Test generator based on requirements.",
    packages=find_packages(),
    python_requires='>=3.6',
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # Replace with your license
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'typhoon_specgen = specgen.plugin:main'
        ]
    }
)