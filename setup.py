import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()
requires = ["flake8 > 3.0.0", "attrs > 19.0.0"]

setuptools.setup(
    name="flake8-click",
    license="MIT",
    version="0.1.0",
    description="flake8 extension for click",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="r2c",
    author_email="flake8@r2c.dev",
    url="https://github.com/returntocorp/click-best-practices",
    py_modules=["flake8_click"],
    install_requires=requires,
    entry_points={
        "flake8.extension": [
            "CLC = flake8_click:ClickOptionHelpChecker",
            "CLC1 = flake8_click:ClickOptionFunctionArgumentChecker",
        ]
    },
    classifiers=[
        "Framework :: Flake8",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
    ],
)
